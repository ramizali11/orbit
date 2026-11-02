"""Concrete Protocol Adapters for CMF Buds Pro 2, clones, BLE HID and GATT dials."""
from __future__ import annotations

import logging
import re
from typing import Callable, Optional, Set

from orbit.core.device_registry import DeviceFingerprint
from orbit.core.events import Capability, InputEvent, Kind
from orbit.protocol import ProtocolAdapter, ProtocolCapability

log = logging.getLogger("orbit.protocol")


class CmfAvrcpHfpAdapter(ProtocolAdapter):
    """Protocol adapter for genuine CMF Buds Pro 2 and CMF rotary devices.

    Decodes dial turns via AVRCP absolute volume on the audio endpoint and
    sniffs dial press-and-hold via Windows ETW HFP AT+BVRA=1 packets.
    """

    id = "cmf-avrcp-hfp"
    display_name = "CMF Buds Pro 2 (AVRCP + HFP)"
    capabilities: Set[ProtocolCapability] = {
        ProtocolCapability.ROTATE,
        ProtocolCapability.HOLD,
        ProtocolCapability.CLICK,
    }

    def __init__(self, target_identifier: str = "CMF Buds Pro 2"):
        super().__init__(target_identifier)
        self._vol_source = None
        self._bt_source = None

    def start(self, emit: Callable[[InputEvent], None]) -> None:
        super().start(emit)
        from orbit.platform.windows.input_bt import BluetoothPacketSource
        from orbit.platform.windows.input_volume import VolumeRotationSource

        self._vol_source = VolumeRotationSource(self.target_identifier)
        self._bt_source = BluetoothPacketSource()

        try:
            self._vol_source.start(emit)
        except Exception:
            log.exception("failed to start CMF volume rotation source")

        try:
            self._bt_source.start(emit)
        except Exception:
            log.exception("failed to start CMF ETW hold source")

    def stop(self) -> None:
        if self._vol_source:
            self._vol_source.stop()
            self._vol_source = None
        if self._bt_source:
            self._bt_source.stop()
            self._bt_source = None
        super().stop()

    def set_passthrough(self, enabled: bool) -> None:
        if self._vol_source:
            self._vol_source.set_passthrough(enabled)

    def set_duck(self, factor: Optional[float]) -> None:
        if self._vol_source:
            self._vol_source.set_duck(factor)


class GenericAvrcpAdapter(ProtocolAdapter):
    """Generic AVRCP volume step adapter for third-party rotary earbuds and replicas."""

    id = "generic-avrcp"
    display_name = "Generic AVRCP Rotary Adapter"
    capabilities: Set[ProtocolCapability] = {
        ProtocolCapability.ROTATE,
        ProtocolCapability.CLICK,
    }

    def __init__(self, target_identifier: str = ""):
        super().__init__(target_identifier)
        self._vol_source = None

    def start(self, emit: Callable[[InputEvent], None]) -> None:
        super().start(emit)
        from orbit.platform.windows.input_volume import VolumeRotationSource
        self._vol_source = VolumeRotationSource(self.target_identifier)
        try:
            self._vol_source.start(emit)
        except Exception:
            log.exception("failed to start generic AVRCP volume source")

    def stop(self) -> None:
        if self._vol_source:
            self._vol_source.stop()
            self._vol_source = None
        super().stop()

    def set_passthrough(self, enabled: bool) -> None:
        if self._vol_source:
            self._vol_source.set_passthrough(enabled)

    def set_duck(self, factor: Optional[float]) -> None:
        if self._vol_source:
            self._vol_source.set_duck(factor)


class BleHidDialAdapter(ProtocolAdapter):
    """BLE HID dial adapter (e.g. Surface Dial, generic BLE rotary knobs, HID over GATT 0x1812)."""

    id = "ble-hid"
    display_name = "BLE HID Dial (Surface Dial / HOGP)"
    capabilities: Set[ProtocolCapability] = {
        ProtocolCapability.ROTATE,
        ProtocolCapability.CLICK,
        ProtocolCapability.HOLD,
    }

    def decode_report(self, report_bytes: bytes) -> Optional[InputEvent]:
        """Decodes standard relative rotary HID report."""
        if not report_bytes or len(report_bytes) < 1:
            return None
        # Byte 0: signed displacement or button mask
        delta = int.from_bytes(report_bytes[:1], byteorder="little", signed=True)
        if delta != 0:
            return InputEvent(source="ble-hid", kind=Kind.ROTATE, delta=delta)
        return None


class BleGattDialAdapter(ProtocolAdapter):
    """Custom BLE GATT rotary encoder adapter (e.g. ESP32, nRF52 dial implementations)."""

    id = "ble-gatt"
    display_name = "Custom BLE GATT Rotary Dial"
    capabilities: Set[ProtocolCapability] = {
        ProtocolCapability.ROTATE,
        ProtocolCapability.CLICK,
        ProtocolCapability.HOLD,
    }

    def decode_notification(self, payload: bytes) -> Optional[InputEvent]:
        """Decodes signed 8-bit delta or button state from GATT notification."""
        if not payload:
            return None
        # Format: byte 0 = delta (-128..127), byte 1 = button state (0=none, 1=click, 2=double, 3=hold)
        delta = int.from_bytes(payload[:1], byteorder="little", signed=True)
        btn = payload[1] if len(payload) > 1 else 0

        if delta != 0:
            return InputEvent(source="ble-gatt", kind=Kind.ROTATE, delta=delta)
        if btn == 1:
            return InputEvent(source="ble-gatt", kind=Kind.CLICK)
        if btn == 2:
            return InputEvent(source="ble-gatt", kind=Kind.DOUBLE)
        if btn == 3:
            return InputEvent(source="ble-gatt", kind=Kind.HOLD)
        return None


class UnknownDeviceAdapter(ProtocolAdapter):
    """Diagnostic adapter for unrecognized devices, capturing raw telemetry."""

    id = "unknown"
    display_name = "Diagnostic Safe Probe"
    capabilities: Set[ProtocolCapability] = set()

    def __init__(self, target_identifier: str = ""):
        super().__init__(target_identifier)
        self.probed_packets: list[bytes] = []

    def probe_packet(self, data: bytes) -> None:
        self.probed_packets.append(data)
        log.info("unknown device [%s] probe captured %d bytes: %s", self.target_identifier, len(data), data.hex())


class ProtocolDetector:
    """Infers the appropriate protocol adapter for a device based on its fingerprint."""

    _ADAPTER_REGISTRY = [
        BleHidDialAdapter,
        CmfAvrcpHfpAdapter,
        GenericAvrcpAdapter,
        BleGattDialAdapter,
        UnknownDeviceAdapter,
    ]

    @classmethod
    def detect(cls, fp: DeviceFingerprint, manual_override: str = "auto") -> ProtocolAdapter:
        if manual_override and manual_override != "auto":
            for a_cls in cls._ADAPTER_REGISTRY:
                if a_cls.id == manual_override:
                    return a_cls(fp.name or fp.address)

        # 1. Check for BLE HID service UUID 0x1812
        for u in fp.service_uuids:
            if "1812" in u.lower():
                return BleHidDialAdapter(fp.name or fp.address)

        # 2. Check for Genuine CMF / Nothing products
        name_lower = (fp.name or "").lower()
        if any(token in name_lower for token in ("cmf", "buds pro 2", "nothing")):
            return CmfAvrcpHfpAdapter(fp.name or fp.address)

        # 3. Check for generic earbuds / audio devices
        audio_keywords = ("buds", "tws", "dial", "airdopes", "headset", "earbuds", "rotary", "pro")
        if any(token in name_lower for token in audio_keywords) or (fp.device_class & 0x200000) != 0:
            return GenericAvrcpAdapter(fp.name or fp.address)

        # 4. Custom BLE GATT if BLE connection with custom characteristics
        if fp.connection_type == "BLE" and fp.service_uuids:
            return BleGattDialAdapter(fp.name or fp.address)

        # 5. Fallback safe diagnostic probe
        return UnknownDeviceAdapter(fp.name or fp.address)
