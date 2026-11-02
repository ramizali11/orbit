"""Device fingerprinting, registry and duplicate resolution.

Provides persistent device identity across restarts, user custom nicknames,
and adapter affinity, decoupling Orbit from fragile Bluetooth display names.
"""
from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional

log = logging.getLogger("orbit.registry")


@dataclass
class DeviceFingerprint:
    name: str = ""
    address: str = ""
    vendor_id: int = 0
    product_id: int = 0
    service_uuids: list[str] = field(default_factory=list)
    device_class: int = 0
    connection_type: str = "CLASSIC"  # CLASSIC, BLE, BRIDGED, HID

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> DeviceFingerprint:
        return cls(
            name=d.get("name", ""),
            address=d.get("address", "").upper(),
            vendor_id=int(d.get("vendor_id", 0)),
            product_id=int(d.get("product_id", 0)),
            service_uuids=[str(u).lower() for u in d.get("service_uuids", [])],
            device_class=int(d.get("device_class", 0)),
            connection_type=d.get("connection_type", "CLASSIC"),
        )

    def similarity(self, other: DeviceFingerprint) -> float:
        """Returns 0.0 to 1.0 confidence score representing if two devices are identical."""
        if self.address and other.address and self.address.upper() == other.address.upper():
            return 1.0
        score = 0.0
        # Vendor + Product match
        if self.vendor_id and other.vendor_id and self.vendor_id == other.vendor_id:
            score += 0.35
            if self.product_id and other.product_id and self.product_id == other.product_id:
                score += 0.35
        # Service UUID overlap
        s1 = set(u.lower() for u in self.service_uuids)
        s2 = set(u.lower() for u in other.service_uuids)
        if s1 and s2:
            overlap = len(s1 & s2) / float(max(len(s1), len(s2)))
            score += 0.20 * overlap
        # Normalized Name match
        n1 = self.name.strip().lower()
        n2 = other.name.strip().lower()
        if n1 and n2 and n1 == n2:
            score += 0.10
        return round(min(1.0, score), 4)


@dataclass
class DeviceRecord:
    id: str  # Unique persistent ID (MAC address or UUID)
    fingerprint: DeviceFingerprint
    custom_name: str = ""
    adapter_id: str = "auto"
    is_favorite: bool = False
    auto_reconnect: bool = True
    last_connected: float = 0.0
    notes: str = ""

    @property
    def display_name(self) -> str:
        return self.custom_name.strip() or self.fingerprint.name.strip() or f"Device {self.id[:8]}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "fingerprint": self.fingerprint.to_dict(),
            "custom_name": self.custom_name,
            "adapter_id": self.adapter_id,
            "is_favorite": self.is_favorite,
            "auto_reconnect": self.auto_reconnect,
            "last_connected": self.last_connected,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> DeviceRecord:
        fp_dict = d.get("fingerprint", {})
        fp = DeviceFingerprint.from_dict(fp_dict) if fp_dict else DeviceFingerprint(name=d.get("name", ""), address=d.get("id", ""))
        return cls(
            id=d.get("id", "").upper(),
            fingerprint=fp,
            custom_name=d.get("custom_name", ""),
            adapter_id=d.get("adapter_id", "auto"),
            is_favorite=bool(d.get("is_favorite", False)),
            auto_reconnect=bool(d.get("auto_reconnect", True)),
            last_connected=float(d.get("last_connected", 0.0)),
            notes=d.get("notes", ""),
        )


class DeviceRegistry:
    def __init__(self, storage_path: Path):
        self.path = storage_path
        self._devices: dict[str, DeviceRecord] = {}
        self._active_device_id: Optional[str] = None
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            return
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            devs = data.get("devices", {})
            self._devices = {k.upper(): DeviceRecord.from_dict(v) for k, v in devs.items()}
            self._active_device_id = data.get("active_device_id")
            log.info("loaded %d devices from registry", len(self._devices))
        except Exception:
            log.exception("failed to load device registry from %s", self.path)

    def save(self) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "active_device_id": self._active_device_id,
                "devices": {k: v.to_dict() for k, v in self._devices.items()},
            }
            self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception:
            log.exception("failed to save device registry to %s", self.path)

    def get(self, device_id: str) -> Optional[DeviceRecord]:
        return self._devices.get(device_id.upper())

    def get_all(self) -> list[DeviceRecord]:
        return sorted(self._devices.values(), key=lambda d: (not d.is_favorite, -d.last_connected))

    def register_or_update(self, fingerprint: DeviceFingerprint) -> DeviceRecord:
        dev_id = fingerprint.address.upper() or fingerprint.name.upper()
        if not dev_id:
            dev_id = f"UNKNOWN-{fingerprint.vendor_id:04x}:{fingerprint.product_id:04x}"

        existing = self._devices.get(dev_id)
        if existing:
            # Update fingerprint info while preserving user customization
            existing.fingerprint = fingerprint
            self.save()
            return existing

        record = DeviceRecord(id=dev_id, fingerprint=fingerprint)
        self._devices[dev_id] = record
        self.save()
        log.info("registered new device: %s [%s]", record.display_name, dev_id)
        return record

    def set_custom_name(self, device_id: str, name: str) -> bool:
        dev = self._devices.get(device_id.upper())
        if dev:
            dev.custom_name = name.strip()
            self.save()
            return True
        return False

    def set_adapter(self, device_id: str, adapter_id: str) -> bool:
        dev = self._devices.get(device_id.upper())
        if dev:
            dev.adapter_id = adapter_id.strip()
            self.save()
            return True
        return False

    def remove(self, device_id: str) -> bool:
        dev_id = device_id.upper()
        if dev_id in self._devices:
            del self._devices[dev_id]
            if self._active_device_id == dev_id:
                self._active_device_id = None
            self.save()
            return True
        return False

    @property
    def active_device(self) -> Optional[DeviceRecord]:
        if self._active_device_id:
            return self._devices.get(self._active_device_id.upper())
        return None

    def set_active_device(self, device_id: Optional[str]) -> None:
        self._active_device_id = device_id.upper() if device_id else None
        self.save()
