"""Windows Bluetooth discovery and device enumeration.

Combines three native Windows discovery channels:
  1. Registry BTHPORT devices: Instant, reliable inventory of all paired/remembered
     Bluetooth Classic & BLE devices, their MAC addresses, COD, and manufacturer IDs.
  2. CoreAudio render endpoints: Real-time detection of active Bluetooth audio endpoints
     (A2DP / Hands-Free) currently connected to the system.
  3. BluetoothApis.dll: Native Win32 Bluetooth inquiry scanning for newly discoverable
     devices in pairing mode.
"""
from __future__ import annotations

import ctypes
from ctypes import wintypes as wt
import logging
import threading
import time
import winreg
from dataclasses import dataclass
from typing import Callable, Optional

from orbit.core.device_registry import DeviceFingerprint

log = logging.getLogger("orbit.discovery")

# Win32 Bluetooth structures
class BLUETOOTH_DEVICE_SEARCH_PARAMS(ctypes.Structure):
    _fields_ = [
        ("dwSize", wt.DWORD),
        ("fReturnAuthenticated", wt.BOOL),
        ("fReturnRemembered", wt.BOOL),
        ("fReturnUnknown", wt.BOOL),
        ("fReturnConnected", wt.BOOL),
        ("fIssueInquiry", wt.BOOL),
        ("cTimeoutMultiplier", ctypes.c_ubyte),
        ("hRadio", wt.HANDLE),
    ]

class BLUETOOTH_ADDRESS(ctypes.Structure):
    _fields_ = [("ullLong", ctypes.c_uint64)]

class SYSTEMTIME(ctypes.Structure):
    _fields_ = [
        ("wYear", wt.WORD), ("wMonth", wt.WORD), ("wDayOfWeek", wt.WORD),
        ("wDay", wt.WORD), ("wHour", wt.WORD), ("wMinute", wt.WORD),
        ("wSecond", wt.WORD), ("wMilliseconds", wt.WORD),
    ]

class BLUETOOTH_DEVICE_INFO(ctypes.Structure):
    _fields_ = [
        ("dwSize", wt.DWORD),
        ("Address", BLUETOOTH_ADDRESS),
        ("ulClassofDevice", wt.ULONG),
        ("fConnected", wt.BOOL),
        ("fRemembered", wt.BOOL),
        ("fAuthenticated", wt.BOOL),
        ("stLastSeen", SYSTEMTIME),
        ("stLastUsed", SYSTEMTIME),
        ("szName", ctypes.c_wchar * 248),
    ]


@dataclass
class DiscoveredDevice:
    fingerprint: DeviceFingerprint
    is_connected: bool = False
    is_paired: bool = False
    audio_endpoint_name: str = ""
    rssi: Optional[int] = None
    last_seen: float = 0.0

    @property
    def display_name(self) -> str:
        return self.fingerprint.name or f"Device {self.fingerprint.address}"


def _format_mac(raw_hex_or_int) -> str:
    if isinstance(raw_hex_or_int, int):
        return ":".join(f"{(raw_hex_or_int >> (8 * i)) & 0xFF:02X}" for i in reversed(range(6)))
    s = str(raw_hex_or_int).replace(":", "").replace("-", "").upper()
    if len(s) == 12:
        return ":".join(s[i:i + 2] for i in range(0, 12, 2))
    return s


class WindowsBluetoothDiscovery:
    def __init__(self):
        self._lock = threading.Lock()
        self._is_scanning = False
        self._bth_dll = None
        try:
            self._bth_dll = ctypes.WinDLL("BluetoothApis.dll")
        except Exception:
            log.warning("BluetoothApis.dll unavailable on this system")

    @property
    def is_scanning(self) -> bool:
        return self._is_scanning

    def get_paired_devices(self) -> list[DiscoveredDevice]:
        """Reads all paired Bluetooth devices from Windows BTHPORT registry."""
        results: list[DiscoveredDevice] = []
        reg_path = r"SYSTEM\CurrentControlSet\Services\BTHPORT\Parameters\Devices"
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path) as k:
                count, _, _ = winreg.QueryInfoKey(k)
                for i in range(count):
                    addr_hex = winreg.EnumKey(k, i)
                    mac = _format_mac(addr_hex)
                    name = ""
                    cod = 0
                    mfg = 0
                    try:
                        with winreg.OpenKey(k, addr_hex) as sk:
                            try:
                                raw_name, _ = winreg.QueryValueEx(sk, "Name")
                                if isinstance(raw_name, bytes):
                                    name = raw_name.decode("utf-8", errors="replace").rstrip("\x00")
                                elif isinstance(raw_name, str):
                                    name = raw_name.rstrip("\x00")
                            except OSError:
                                pass
                            try:
                                cod, _ = winreg.QueryValueEx(sk, "COD")
                            except OSError:
                                pass
                            try:
                                mfg, _ = winreg.QueryValueEx(sk, "ManufacturerId")
                            except OSError:
                                pass
                    except OSError:
                        pass

                    fp = DeviceFingerprint(
                        name=name or f"Bluetooth Device ({mac[-5:]})",
                        address=mac,
                        vendor_id=mfg,
                        device_class=cod,
                        connection_type="CLASSIC",
                    )
                    results.append(DiscoveredDevice(fingerprint=fp, is_paired=True))
        except Exception:
            log.exception("failed to query registry Bluetooth devices")
        return results

    def get_active_audio_endpoints(self) -> list[dict[str, str]]:
        """Queries CoreAudio for currently active audio render endpoints."""
        endpoints = []
        try:
            from pycaw.pycaw import AudioUtilities
            coll = AudioUtilities.GetDeviceEnumerator().EnumAudioEndpoints(0, 1)  # eRender, ACTIVE
            for i in range(coll.GetCount()):
                dev = AudioUtilities.CreateDevice(coll.Item(i))
                endpoints.append({
                    "name": dev.FriendlyName or "Audio Endpoint",
                    "id": dev.id or "",
                })
        except Exception:
            log.exception("failed to enumerate active audio endpoints")
        return endpoints

    def discover_all(self, issue_inquiry: bool = False, timeout_multiplier: int = 2) -> list[DiscoveredDevice]:
        """Aggregates devices from registry, active audio endpoints, and live inquiry."""
        with self._lock:
            device_map: dict[str, DiscoveredDevice] = {}

            # 1. Paired devices from registry
            for dev in self.get_paired_devices():
                device_map[dev.fingerprint.address.upper()] = dev

            # 2. Check active audio endpoints
            audio_endpoints = self.get_active_audio_endpoints()
            for ep in audio_endpoints:
                ep_name = ep["name"].lower()
                matched = False
                for dev in device_map.values():
                    dev_name = dev.fingerprint.name.lower()
                    if dev_name and (dev_name in ep_name or ep_name in dev_name):
                        dev.is_connected = True
                        dev.audio_endpoint_name = ep["name"]
                        matched = True
                        break
                if not matched:
                    # An active audio endpoint not matched to a known MAC
                    fp = DeviceFingerprint(
                        name=ep["name"],
                        address="AUDIO-ENDPOINT",
                        connection_type="CLASSIC",
                    )
                    device_map[ep["name"].upper()] = DiscoveredDevice(
                        fingerprint=fp,
                        is_connected=True,
                        audio_endpoint_name=ep["name"],
                    )

            # 3. Live Bluetooth inquiry if supported and requested
            if self._bth_dll and issue_inquiry:
                try:
                    params = BLUETOOTH_DEVICE_SEARCH_PARAMS()
                    params.dwSize = ctypes.sizeof(BLUETOOTH_DEVICE_SEARCH_PARAMS)
                    params.fReturnAuthenticated = True
                    params.fReturnRemembered = True
                    params.fReturnUnknown = True
                    params.fReturnConnected = True
                    params.fIssueInquiry = True
                    params.cTimeoutMultiplier = max(1, min(10, timeout_multiplier))
                    params.hRadio = None

                    info = BLUETOOTH_DEVICE_INFO()
                    info.dwSize = ctypes.sizeof(BLUETOOTH_DEVICE_INFO)

                    h_find = self._bth_dll.BluetoothFindFirstDevice(ctypes.byref(params), ctypes.byref(info))
                    if h_find:
                        try:
                            while True:
                                mac = _format_mac(info.Address.ullLong)
                                name = str(info.szName).strip()
                                connected = bool(info.fConnected)
                                remembered = bool(info.fRemembered)

                                if mac in device_map:
                                    device_map[mac].is_connected = device_map[mac].is_connected or connected
                                    device_map[mac].is_paired = device_map[mac].is_paired or remembered
                                    if name and not device_map[mac].fingerprint.name:
                                        device_map[mac].fingerprint.name = name
                                else:
                                    fp = DeviceFingerprint(
                                        name=name or f"BT Device {mac[-5:]}",
                                        address=mac,
                                        device_class=int(info.ulClassofDevice),
                                        connection_type="CLASSIC",
                                    )
                                    device_map[mac] = DiscoveredDevice(
                                        fingerprint=fp,
                                        is_connected=connected,
                                        is_paired=remembered,
                                    )

                                if not self._bth_dll.BluetoothFindNextDevice(h_find, ctypes.byref(info)):
                                    break
                        finally:
                            self._bth_dll.BluetoothFindDeviceClose(h_find)
                except Exception:
                    log.exception("error during Bluetooth inquiry scan")

            return list(device_map.values())

    def start_async_discovery(self, on_result: Callable[[list[DiscoveredDevice]], None], issue_inquiry: bool = False) -> threading.Thread:
        def _worker():
            self._is_scanning = True
            try:
                devs = self.discover_all(issue_inquiry=issue_inquiry)
                on_result(devs)
            finally:
                self._is_scanning = False

        t = threading.Thread(target=_worker, name="bt-async-discovery", daemon=True)
        t.start()
        return t

