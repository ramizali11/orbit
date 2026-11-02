# Orbit Bluetooth Device & Protocol Compatibility Guide

**Date:** November 2026  
**Status:** Living Engineering Document

---

## 1. Physical Architecture: Earbuds vs. Charging-Case Endpoints

A foundational challenge of rotary-dial earbuds is understanding how the physical dial on the charging case connects to the smartphone.

### Topology Comparison

```
TOPOLOGY A: Indirect/Bridged Dial (e.g., Genuine CMF Buds Pro 2)

+------------------------+       Pogo Pins / Local Bus       +------------------------+
|      Charging Case     | --------------------------------> |      Earbuds Unit      |
|  [Physical Rotary Dial]|                                   |  (Master BT Controller)|
+------------------------+                                   +------------------------+
                                                                         |
                                                                         | Standard Bluetooth Classic
                                                                         | (A2DP, AVRCP 1.6, HFP 1.8)
                                                                         v
                                                             +------------------------+
                                                             |       Smartphone       |
                                                             |      [Orbit App]       |
                                                             +------------------------+

TOPOLOGY B: Dual-Endpoint / Independent Case Radio (e.g., Select 3rd-Party & Next-Gen Dials)

+------------------------+       Direct BLE GATT / HID
|      Charging Case     | ==========================================================+
|  [Independent BLE Radio|                                                           |
+------------------------+                                                           |
                                                                                     v
+------------------------+       Bluetooth Audio (A2DP / LE Audio)           +----------------+
|      Earbuds Unit      | ------------------------------------------------> |   Smartphone   |
|   (Audio Playback)     |                                                   |   [Orbit App]  |
+------------------------+                                                   +----------------+
```

### Verified Endpoint Behaviors

| Device Model | Case Advertises Independently? | Case Accepts Direct Pairing? | Earbuds Required for Dial? | Case Accessible while Buds are in Case? | Real Hardware Verification Status |
|---|---|---|---|---|---|
| **CMF Buds Pro 2 (Genuine)** | No (Case has no standalone BT radio; uses earbud RF/bus) | No | Yes (At least one earbud must be out or connected in lid-open state) | Yes, when case lid is open or buds maintain link | **VERIFIED** |
| **CMF Buds / Neckband series** | No dial on case | N/A | N/A | N/A | **UNSUPPORTED** |
| **Generic AVRCP Dial Clones** | No (Emulates CMF A2DP volume behavior) | No | Yes | Depends on clone firmware | **DISCOVERED / PARTIALLY VERIFIED** |
| **BLE HID Rotary Knobs (Surface Dial Clones)** | Yes (Independent BLE HID peripheral) | Yes | N/A (Standalone controller) | N/A | **VERIFIED** |
| **Custom / Unknown BLE GATT Dial** | Yes (Advertises custom GATT Service) | Yes | No | Yes | **DISCOVERED** |

---

## 2. Protocol Discovery and Decoding System

Orbit implements a unified protocol abstraction layer:

### 2.1 AVRCP Absolute Volume Protocol (`CmfAvrcpHfpAdapter`)
- **Device Identification:**
  - Device Name matches `CMF Buds Pro 2`, `Nothing Buds`, or user-specified AVRCP dial device.
  - Bluetooth Class: `Audio/Video Headset` (`0x040404`).
  - Active audio route: `TYPE_BLUETOOTH_A2DP` or `TYPE_BLE_HEADSET`.
- **Event Decoding:**
  - **Rotation:** AVRCP `SetAbsoluteVolume` (0–127) mapped to 16-step grid. Each detent turns volume up/down by 1 step (~6.25%).
  - **Direction:** `delta > 0` => Clockwise; `delta < 0` => Counterclockwise.
  - **Single / Double / Triple Press:** AVRCP Passthrough `PLAY`/`PAUSE` (Single), `FORWARD` (Double), `BACKWARD` (Triple).
  - **Hold:** Hands-Free Profile (HFP) `AT+BVRA=1` triggers `Intent.ACTION_VOICE_COMMAND`.
- **Known Limitations:**
  - System volume overlay displays briefly upon dial rotation unless muted or suppressed.
  - Rate limited by bud firmware to ~3-4 reports/sec (~270-450ms interval).
  - Physical dial volume changes must be disambiguated from phone volume button presses.

### 2.2 Direct BLE GATT Rotary Protocol (`BleGattDialAdapter`)
- **Device Identification:**
  - Advertises standard or proprietary Rotary/Encoder GATT Service UUID.
  - Characteristic with `NOTIFY` or `INDICATE` property.
- **Event Decoding:**
  - Characteristic notification payload: Signed byte (`+1` CW, `-1` CCW) or relative counter.
  - Button state: Bitmask or discrete state characteristic.
- **Advantages:** Low latency (<30ms), does not alter media stream volume, independent of audio playback.

### 2.3 BLE HID Protocol (`BleHidDialAdapter`)
- **Device Identification:**
  - Human Interface Device (HID) Service UUID `0x1812`.
  - Report Map specifies Consumer Control (Volume / Dial / AC Scroll) or Generic Desktop (Dial).
- **Event Decoding:**
  - HID Input Reports received via Android `InputDevice` subsystem (`onKeyEvent` / `onGenericMotionEvent`) or direct GATT HID report notifications.

---

## 3. Duplicate-Device Fingerprinting Matrix

Because multiple genuine or clone devices frequently share identical Bluetooth display names (e.g. "CMF Buds Pro 2"), Orbit constructs a 6-tuple device fingerprint:

$$\text{Fingerprint} = \langle \text{Name}, \text{Address/PseudoID}, \text{DeviceClass}, \text{AdvertisedUUIDs}, \text{ManufacturerData}, \text{ProtocolType} \rangle$$

1. **MAC Address / Identity Address:** Used as primary anchor on Android 8–11; on Android 12+ (where randomized addresses may occur), MAC + Identity Resolving Key (IRK) or bonded device descriptor is preserved.
2. **Manufacturer Specific Data:** Extracts 16-bit Company Identifier (e.g., Nothing Technology, Cambridge Silicon Radio, BES, Realtek) and custom advertising payloads.
3. **Advertised Services:** Set of 16-bit, 32-bit, and 128-bit Service UUIDs.
4. **Bluetooth Profile Mask:** Bitmask representing supported profiles (A2DP Sink/Source, AVRCP Controller/Target, HFP, HID, GATT).
5. **User Alias:** Persistent custom label allowing the user to distinguish between "Living Room Buds" and "Gym Buds".

---

## 4. Verification Classifications

- **VERIFIED:** Physical hardware tested directly; dial rotation, press, and hold operate accurately.
- **PARTIALLY VERIFIED:** Device connects and basic volume/media keys function, but rotary detents or hold latency need physical validation.
- **DISCOVERED:** Device identified via scan or fingerprint matching, but protocol handshake is in testing.
- **UNSUPPORTED:** Device does not expose dial events or uses inaccessible proprietary RF.
- **UNKNOWN:** Insufficient metadata to categorize.

