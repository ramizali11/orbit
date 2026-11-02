# Orbit Universal Dial Controller — Feature & Device Matrix

**Date:** November 2026  
**Version:** 0.3.0-android

---

## 1. Device Support Matrix

| Device Model | Dial Physical Location | Hardware Connectivity | Case Endpoint Independent? | Orbit Protocol Adapter | Support Status | Notes |
|---|---|---|---|---|---|---|
| **CMF Buds Pro 2** | Charging Case (Smart Dial) | Bluetooth Classic (A2DP / AVRCP 1.6 / HFP 1.8) | No (Bridged via active earbud) | `CmfAvrcpHfpAdapter` | **VERIFIED** | Full support for Rotate CW/CCW, Single, Double, Triple press, Hold. |
| **CMF Watch Pro / Pro 2** | Watch Crown / Bezel | BLE Proprietary GATT | Yes (Standalone wearable) | `BleGattDialAdapter` (Planned) | **DISCOVERED** | Requires custom GATT service decoding. |
| **Microsoft Surface Dial** | Standalone Physical Dial | BLE HID (Generic Desktop Dial) | Yes (Standalone device) | `BleHidDialAdapter` | **VERIFIED** | Direct radial wheel and scroll mapping. |
| **Generic Bluetooth Shutter / Knob** | Handheld remote | BLE HID / Media Buttons | Yes (Standalone peripheral) | `BleHidDialAdapter` / `ControlsHub` | **VERIFIED** | Volume and media transport keys mapped as dial detents. |
| **CMF Buds 2 Clone / Replicas** | Charging Case Dial | Emulated AVRCP volume steps | No (Bridged via clone bud) | `CmfAvrcpHfpAdapter` / `GenericAvrcpAdapter` | **PARTIALLY VERIFIED** | Supported via auto grid-learning in `VolumeDial`. |
| **Unknown BLE GATT Dial** | Various | Custom BLE GATT Services | Yes / No | `UnknownDeviceAdapter` | **DISCOVERED** | Inspects GATT services and allows diagnostic event capture. |

---

## 2. Rotary Dial Logical Events

| Logical Event | CMF Buds Pro 2 Mapping | BLE GATT Mapping | BLE HID Mapping | Description |
|---|---|---|---|---|
| **Rotate Clockwise (CW)** | AVRCP Volume +1 step | GATT Characteristic `+1` | HID Dial Report `+detent` | Single notch clockwise rotation |
| **Rotate Counterclockwise (CCW)** | AVRCP Volume -1 step | GATT Characteristic `-1` | HID Dial Report `-detent` | Single notch counterclockwise rotation |
| **Rapid Rotation** | Rate < 400ms interval | Notification frequency > 10Hz | High angular velocity | Triggers acceleration multipliers in tools |
| **Continuous Rotation** | Sustained rotation stream | Sustained stream | Sustained stream | Physics-based glide and momentum |
| **Single Press** | AVRCP `PLAY` or `PAUSE` | Button Char = `0x01` | HID Button 1 | Action click / Wheel item commit |
| **Double Press** | AVRCP `FORWARD` | Button Char = `0x02` | HID Double Click | Secondary action / Next tool |
| **Triple Press** | AVRCP `BACKWARD` | Button Char = `0x03` | HID Triple Click | Tertiary action / Prev tool |
| **Long Press (Hold)** | HFP `AT+BVRA=1` (Voice Command) | Button Char Hold event | HID Button Hold | Open radial menu / Custom shortcut |

---

## 3. Action Catalog

| Category | Action Identifier | Description | Required Android Permission |
|---|---|---|---|
| **Audio & Volume** | `action:volume_up` | Raise music stream volume | None |
| | `action:volume_down` | Lower music stream volume | None |
| | `action:mute_toggle` | Toggle mute / unmute | None |
| | `action:play_pause` | Toggle media playback | Notification Listener (for active session) |
| | `action:next_track` | Skip to next audio track | Notification Listener |
| | `action:prev_track` | Skip to previous audio track | Notification Listener |
| **Screen & Display**| `action:brightness_up` | Increase screen brightness | `WRITE_SETTINGS` |
| | `action:brightness_down` | Decrease screen brightness | `WRITE_SETTINGS` |
| | `action:auto_brightness_toggle` | Toggle adaptive brightness | `WRITE_SETTINGS` |
| | `action:flashlight_toggle` | Toggle LED flashlight | Camera access (No permission needed) |
| **Navigation** | `action:scroll_up` | Smooth vertical scroll up | Accessibility Service (`canPerformGestures`) |
| | `action:scroll_down` | Smooth vertical scroll down | Accessibility Service (`canPerformGestures`) |
| | `action:page_up` | Jump page up / flick gesture | Accessibility Service |
| | `action:page_down` | Jump page down / flick gesture | Accessibility Service |
| | `action:app_switch` | Switch to recent application | Accessibility Service (`GLOBAL_ACTION_RECENTS`) |
| | `action:back` | Go back | Accessibility Service (`GLOBAL_ACTION_BACK`) |
| | `action:home` | Navigate home | Accessibility Service (`GLOBAL_ACTION_HOME`) |
| | `action:notifications` | Pull down notification shade | Accessibility Service (`GLOBAL_ACTION_NOTIFICATIONS`) |
| **Camera** | `action:camera_zoom_in` | Pinch-to-zoom in camera viewfinder | Accessibility Service (Gesture) |
| | `action:camera_zoom_out` | Pinch-to-zoom out camera | Accessibility Service (Gesture) |
| | `action:camera_shutter` | Trigger camera shutter button | `onKeyEvent` volume injection / Accessibility |
| **Productivity** | `action:undo` | Trigger Ctrl+Z in supported editors | Accessibility / Input Injection |
| | `action:redo` | Trigger Ctrl+Y in supported editors | Accessibility / Input Injection |
| | `action:launch_app` | Launch designated application | None (`getLaunchIntentForPackage`) |
| | `action:assistant` | Launch Voice Assistant / Claude | None (`VOICE_COMMAND` / App Intent) |

