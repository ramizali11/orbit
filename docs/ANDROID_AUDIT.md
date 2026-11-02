# Orbit Android Repository Audit

**Date:** November 2026  
**Auditor:** Senior Android & Bluetooth Systems Engineer  
**Target:** Orbit Universal Rotary Dial Controller (`app.orbit.dial`)

---

## 1. Executive Summary

Orbit is a multi-platform rotary dial and input controller system designed to turn physical dial hardware—specifically the rotary dial on the **CMF Buds Pro 2** charging case and comparable devices—into a universal input device for smartphones and desktop computers.

The repository contains two distinct implementations sharing architectural principles:
1. **Desktop Implementation (Windows & macOS):** Built in Python 3.11+ using PySide6/Qt, pycaw/CoreAudio, and platform-specific event hooks.
2. **Android Implementation:** Located under `android/`, written in modern Kotlin using Jetpack Compose, Coroutines/Flow, targeting Android 8.0+ (API 26) through Android 16 (compileSdk 36, targetSdk 36).

This audit evaluates the current Android implementation against the master requirements for a production-grade, universal Bluetooth dial controller.

---

## 2. Existing Android Application Architecture

### 2.1 Component Overview

```
                                      +------------------------------------+
                                      |            MainActivity            |
                                      | (Compose UI, Onboarding, Controls) |
                                      +-----------------+------------------+
                                                        |
                                                        v
+-------------------------------+             +--------------------+            +-------------------------------+
|    OrbitMediaService (FGS)    |             |      Orbit.kt      |            |   OrbitAccessibilityService   |
|-------------------------------|             |   (In-Process Hub) |            |-------------------------------|
| - Silent AudioTrack loop      | <---------> | - DialEvent Flow   | <--------> | - TYPE_ACCESSIBILITY_OVERLAY  |
| - MediaSession (always play)  |             | - ControlsHub      |            |   (Compose radial wheel view) |
| - VOLUME_CHANGED_ACTION rx    |             | - VolumeDial proxy |            | - Key interception (onKeyEvent)|
| - 40ms volume poller          |             | - KeyPairing       |            | - Action execution (gestures, |
| - Media button event listener |             | - Activity logs    |            |   brightness, torch, a11y)    |
+-------------------------------+             +--------------------+            +-------------------------------+
                ^                                                                               ^
                |                                                                               |
+-------------------------------+                                               +-------------------------------+
|     HoldTrampolineActivity    |                                               |    OrbitNotificationListener  |
|-------------------------------|                                               |-------------------------------|
| - Catches ACTION_VOICE_COMMAND|                                               | - Reads active MediaSessions  |
|   (Bluetooth HFP AT+BVRA=1)   |                                               | - Forwards playback to music  |
+-------------------------------+                                               +-------------------------------+
```

### 2.2 Core Engine (`app.orbit.dial.core`)
The core directory is a high-fidelity Kotlin port of Orbit's desktop core logic:
- **`Engine.kt`**: State machine managing `State.TOOL` (active tool execution) and `State.WHEEL` (radial selector overlay). Handles selection timeout, tool rotation, and tool activation.
- **`VolumeDial.kt`**: Algorithmic decoder that translates streaming system audio volume levels (`STREAM_MUSIC`) into discrete physical dial clicks. Includes grid-step auto-detection (16-step CMF grid vs OEM 15/25/30 stream steps), echo filtering, in-flight set disambiguation, and idle re-centering to keep the dial within volume headroom.
- **`Controls.kt`**: `ControlsHub` routing engine, `PressRecognizer` for stateful multi-tap/hold detection, and `Trigger`/`Binding` serialization.
- **`Motion.kt`**: `SpinTracker` and `Pace` for momentum estimation, rate calculation, and adaptive acceleration.
- **`Tools.kt`**: Tool catalog implementing Volume, Smooth Scroll, Brightness, Teleprompter, Scrub, Recent Apps, and Camera/Torch.
- **`BackTap.kt`**: Accelerometer-based double/triple back tap detector, chop, and wrist twist gestures.

---

## 3. Existing Bluetooth & Dial Functionality: Findings & Deficiencies

### 3.1 Passive Media / Audio Routing (Current State)
In the current implementation:
- **No Bluetooth APIs are directly called for device management or scanning.**
- The app relies entirely on Android's system Bluetooth stack:
  1. **Dial Rotation:** Detected passively via `VOLUME_CHANGED_ACTION` broadcast and a 40ms polling loop querying `AudioManager.getStreamVolume(STREAM_MUSIC)`.
  2. **Dial Presses:** Detected passively by holding the active `MediaSession` with an `AudioTrack` streaming PCM silence without audio focus.
  3. **Dial Long-Press (Hold):** Detected via an activity intent filter for `android.intent.action.VOICE_COMMAND` triggered by HFP `AT+BVRA=1`.
- **Filtering:** Currently only checks `AudioManager.getDevices(GET_DEVICES_OUTPUTS)` for `TYPE_BLUETOOTH_A2DP` or `TYPE_BLE_HEADSET`.

### 3.2 Critical Deficiencies Identified
1. **Missing Universal Bluetooth Discovery:**
   - No nearby device scanning (Classic `BluetoothAdapter.startDiscovery` or BLE `BluetoothLeScanner`).
   - Missing permissions in `AndroidManifest.xml`: `BLUETOOTH_SCAN`, `BLUETOOTH_CONNECT`, `BLUETOOTH_ADMIN`, `ACCESS_FINE_LOCATION`.
   - Cannot list, pair, inspect, or manage Bluetooth dial devices.
2. **Missing Endpoint Separation (Earbuds vs Case):**
   - No data model or logical separation between Earbuds endpoint and Charging Case endpoint.
   - For CMF Buds Pro 2, the charging case dial communicates through the earbuds to AVRCP/HFP. The app must accurately represent this topology (Case endpoint mediated by Earbuds) while supporting independent BLE/GATT case endpoints for 3rd party/replica devices.
3. **No Protocol Abstraction Layer:**
   - No extensible adapter architecture for BLE GATT dials, HID over GATT rotary knobs, or proprietary RF protocols.
4. **No Device Fingerprinting:**
   - No manufacturer data parsing, service UUID inspection, or hardware duplicate handling.
5. **No Live Input Diagnostic Screen:**
   - Users cannot see real-time incoming Bluetooth packets/events, raw values, or decoded rotary ticks.
6. **Limited Action Catalog:**
   - Media, camera zoom, brightness, and scroll actions exist in rudimentary form, but lack fine-grained sensitivity, acceleration profiles, or productivity action sets.

---

## 4. Android Services & Permissions Audit

| Service / Component | Purpose | Current Status | Issues / Improvements Needed |
|---|---|---|---|
| `OrbitAccessibilityService` | Window overlay (`TYPE_ACCESSIBILITY_OVERLAY`), gesture dispatch, key filter | Functional | Requires explicit onboarding disclosure. Robust gesture queueing needed. |
| `OrbitMediaService` | FGS (`mediaPlayback`), silence generator, volume poller, MediaSession | Functional | Battery drain from continuous silence. Needs sleep when screen is off. |
| `HoldTrampolineActivity` | Intercepts `ACTION_VOICE_COMMAND` for HFP Hold | Functional | Competes with Google Assistant / Gemini. Needs guidance for user assignment. |
| `OrbitNotificationListener` | Forwards media buttons to real players | Functional | Needs clear user opt-in during onboarding. |
| `OrbitTileService` | Quick Settings tile for master toggle | Functional | Clean toggle implementation. |
| `BluetoothDiscoveryService` | BLE & Classic scanning, connection tracking | **MISSING** | **Must be implemented.** |

---

## 5. Reusable Components & Tests

- **`VolumeDial.kt`**: Fully verified mathematical model for AVRCP volume step decoding; highly reusable and covered by `VolumeDialTest.kt`.
- **`Controls.kt` & `PressRecognizer`**: Rock-solid event deduplication and multi-press recognition, covered by `TriggerEdgeTest.kt` and `ControlsTest.kt`.
- **`SpinTracker.kt`**: Excellent motion and flick detection; reusable for acceleration across all protocols.
- **`OverlayUi.kt` & Compose Wheel**: High-quality visual canvas implementation of the radial menu.

---

## 6. Action Items for Transformation

1. Maintain 100% compatibility with existing Python desktop implementations (`orbit/`, `tests/`, `config.toml`).
2. Add Bluetooth permission declarations and runtime permission handling for Android 8 through 16.
3. Implement `app.orbit.dial.bluetooth` package with:
   - `DeviceDiscoveryManager` (Classic + BLE)
   - `DeviceFingerprint` & `DeviceFingerprinter`
   - `DeviceRegistry` (Persistence & Duplicate Handling)
   - `EndpointManager` (Earbuds vs Case logical separation)
   - `ProtocolDetector` & `ProtocolAdapter` framework
4. Enhance `VolumeDial` and create `GattDialDecoder` and `HidDialDecoder`.
5. Upgrade Android UI: Onboarding wizard, Device Manager, Live Input Diagnostics, Settings & Action Mappings.
6. Provide full automated test coverage using mock Bluetooth devices.

