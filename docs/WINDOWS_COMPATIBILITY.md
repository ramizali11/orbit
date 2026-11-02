# Orbit — Windows Bluetooth & Device Compatibility Matrix

*Last Updated: 2026-11-02*  
*Target Platforms: Windows 10 (Build 19041+) and Windows 11 (21H2, 22H2, 23H2, 24H2+)*

---

## 1. Executive Summary

Orbit turns physical rotary dials on Bluetooth earbuds charging cases and standalone dials into responsive, customizable input controllers on Windows. On Windows 10 and 11, Orbit supports both **Bluetooth Classic (BR/EDR)** and **Bluetooth Low Energy (BLE)** via an extensible multi-protocol adapter architecture.

Windows handles Bluetooth audio and peripherals differently from mobile OSes. This document specifies the exact Windows subsystems, driver stacks, API capabilities, and device compatibility profiles supported by Orbit.

---

## 2. Windows Bluetooth Stack & Dial Input Mechanisms

| Mechanism | Windows Subsystem | Driver / API Layer | Elevation Req. | Dial Capabilities | Latency |
|---|---|---|---|---|---|
| **AVRCP Absolute Volume** | Windows Audio Stack (CoreAudio) | `IAudioEndpointVolumeCallback`, `pycaw`, `comtypes` | No (Standard User) | Rotary Steps (CW / CCW) | 12–25 ms |
| **HFP Hands-Free AT Commands** | Windows Bluetooth Port Driver | ETW (`Microsoft-Windows-BTH-BTHPORT`), `advapi32.dll` | **Yes (Admin)** | Long Press / Dial Hold (`AT+BVRA=1/0`) | 5–15 ms |
| **System Media Transport Controls (SMTC)** | Windows Media Manager | `Windows.Media.Playback`, `winrt` | No (Standard User) | Single Click, Double Click, Triple Click | 10–20 ms |
| **BLE GATT Custom Service** | Windows Runtime BLE Stack | `Windows.Devices.Bluetooth.GenericAttributeProfile` | No (Standard User) | Rotary Deltas, Button Masks | 8–18 ms |
| **BLE HID Over GATT (HOGP)** | Windows HID Class Driver / WinRT | `0x1812` HID Service / Raw Input API | No (Standard User) | Relative Rotary, Dial Clicks | 4–10 ms |

---

## 3. Physical Hardware Topology: Earbuds vs. Charging Case

### 3.1 The Bridged Reality (`INDIRECT_BRIDGED`)
Unlike standalone Bluetooth mice or keyboards, earbuds charging cases (including **CMF Buds Pro 2**) **do not possess an independent Bluetooth radio or distinct MAC address**. 

```
┌────────────────────────────────────────────────────────┐
│                   CMF Buds Pro 2 Case                  │
│  [ Rotary Dial ] ──(Pogo Pins / Sub-GHz Link)──>      │
└──────────────────────────┬─────────────────────────────┘
                           │ Physical Casing
                           ▼
┌────────────────────────────────────────────────────────┐
│                   Active Earbud Radio                  │
│         Single Bluetooth MAC: 40:ED:98:XX:XX:XX         │
│         (Carries A2DP, AVRCP, HFP, BLE Advert)         │
└──────────────────────────┬─────────────────────────────┘
                           │ Bluetooth Classic Link
                           ▼
┌────────────────────────────────────────────────────────┐
│                  Windows 10 / 11 PC                    │
│   • AVRCP Absolute Volume Callback ──> Rotary Turns    │
│   • ETW BTHPORT Sniffer ─────────────> Dial Hold       │
│   • Windows SMTC Hook ───────────────> Button Clicks   │
└────────────────────────────────────────────────────────┘
```

**Hardware Limitation Note:**  
If the earbuds are switched off, placed in a closed non-communicating case, or disconnected from Windows, the charging-case dial cannot send signals to Windows because the physical dial relays its inputs through the earbud's active Bluetooth radio. Orbit exposes this transparently in the UI as **`INDIRECT_BRIDGED`** rather than fabricating an artificial connection.

### 3.2 Dual-Radio Standalone Devices (`DIRECT_DUAL_RADIO`)
For devices with their own dedicated Bluetooth radio (such as Microsoft Surface Dial or standalone rotary dials):
- Connects directly via BLE or Classic Bluetooth.
- Exposes independent MAC address and GATT/HID services.
- Operates regardless of whether audio earbuds are connected.

---

## 4. Device Compatibility Matrix

| Device Brand / Model | Connection Type | Topology | Supported Adapters | Verified Status | Dial Turns | Clicks | Hold |
|---|---|---|---|---|---|---|---|
| **CMF Buds Pro 2 (Genuine)** | Classic BT (A2DP+HFP) | `INDIRECT_BRIDGED` | `CmfAvrcpHfpAdapter` | **VERIFIED (Traces)** | Yes (16-step grid) | Yes | Yes (ETW Admin) |
| **CMF Buds (Standard)** | Classic BT | Earbuds Only | N/A (No Case Dial) | Detected | N/A | Yes | No |
| **CMF Neckband Pro** | Classic BT | Inline Dial | `CmfAvrcpHfpAdapter` | Compatible | Yes | Yes | Yes |
| **CMF Buds Pro 2 Clones / Replicas** | Classic BT | `INDIRECT_BRIDGED` | `GenericAvrcpAdapter` | Compatible | Yes (8–32 step) | Yes | Partial |
| **Third-Party Rotary Case Earbuds** | Classic BT | `INDIRECT_BRIDGED` | `GenericAvrcpAdapter` | Compatible | Yes | Yes | Fallback |
| **Microsoft Surface Dial** | BLE HID | `DIRECT_DUAL_RADIO` | `BleHidDialAdapter` | Compatible | Yes | Yes | Yes |
| **Generic BLE HID Rotary Encoder** | BLE HID | `DIRECT_DUAL_RADIO` | `BleHidDialAdapter` | Compatible | Yes | Yes | Yes |
| **Custom BLE GATT Rotary Knob** | BLE GATT | `DIRECT_DUAL_RADIO` | `BleGattDialAdapter` | Compatible | Yes | Yes | Yes |
| **Unknown Bluetooth Device** | Any | Auto-Detect | `UnknownDeviceAdapter` | Diagnostic Mode | Probe | Probe | Probe |

---

## 5. Protocol Adapters Specification

### 1. `CmfAvrcpHfpAdapter`
- **Target:** Genuine CMF Buds Pro 2.
- **Rotation Channel:** CoreAudio `IAudioEndpointVolumeCallback` with step-detection algorithm (16-step grid, snaps to home level on idle).
- **Hold Channel:** ETW session listening to `Microsoft-Windows-BTH-BTHPORT` GUID `{8a1f9517-3a8c-4a9e-a018-4f17a200f277}` for HCI packets containing `AT+BVRA=1` or `AT+BVRA=0`.
- **Clicks:** SMTC hook for media transport control notifications.

### 2. `GenericAvrcpAdapter`
- **Target:** Third-party rotary earbuds, white-label products, and CMF clones.
- **Rotation Channel:** Adaptive grid auto-detection (scans grid intervals from 8 to 32 steps).
- **Hold Channel:** Timed click hold fallback or ETW when supported.

### 3. `BleHidDialAdapter`
- **Target:** Microsoft Surface Dial, generic BLE volume/rotary knobs.
- **Standard:** HID over GATT Profile (`0x1812`).
- **Reports:** Decodes relative rotary displacement (`Consumer Control: Volume Increment / Decrement` or `Radial Controller`).

### 4. `BleGattDialAdapter`
- **Target:** Microcontroller-based rotary encoders (ESP32, nRF52) or future vendor GATT dials.
- **Protocol:** Characteristic notification parsing signed 8-bit/16-bit deltas and button bitmasks.

### 5. `UnknownDeviceAdapter`
- **Target:** Newly discovered or unprofiled devices.
- **Behavior:** Runs safe non-destructive probes, logs incoming packets to `diagnostics.log`, and suggests the closest matching profile to the user.

---

## 6. Windows OS Compatibility & Requirements

| Windows Edition | Minimum Version | Status | Notes |
|---|---|---|---|
| **Windows 11 (24H2, 23H2, 22H2)** | Build 22621+ | **Fully Supported** | Native modern WinRT Bluetooth and CoreAudio. |
| **Windows 10 (22H2, 21H2, 20H2)** | Build 19041+ | **Fully Supported** | WinRT Bluetooth APIs available. ETW session fully supported. |
| **Windows 10 (1809 and older)** | Build 17763 | **Limited Support** | WinRT BLE API limitations; CoreAudio volume dial functional. |
| **Windows 7 / 8.1** | Any | **Unsupported** | Lacks modern BLE stack and WinRT APIs. |

---

## 7. Security & Privilege Boundaries

- **Standard User Execution:** Orbit operates cleanly under standard user permissions for:
  - Rotary dial actions (Volume, Scroll, Shortcuts, App Switcher, Brightness).
  - Bluetooth device discovery and status monitoring.
  - Media clicks via SMTC.
- **Administrative Elevation (`UAC`):** Required **only** for the ETW kernel trace session (`advapi32!StartTraceW`) needed to capture raw Bluetooth HCI packets (`AT+BVRA=1`) for physical Press-and-Hold. Orbit includes a `--no-elevate` flag to run without elevation when hold is not needed.

