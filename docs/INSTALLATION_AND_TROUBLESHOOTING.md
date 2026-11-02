# Orbit Android: Installation & Troubleshooting Guide

**Application ID:** `app.orbit.dial`  
**Minimum Android Version:** Android 8.0 (API 26)  
**Target Android Version:** Android 16 (API 36)

---

## 1. Installation Instructions

### Method A: Sideload via ADB (Recommended for Development)
1. Enable **Developer Options** and **USB Debugging** on your Android smartphone.
2. Connect your smartphone via USB to your computer.
3. Build the debug APK using Gradle:
   ```bash
   cd android
   ./gradlew assembleDebug
   ```
4. Install to your device:
   ```bash
   adb install -r app/build/outputs/apk/debug/app-debug.apk
   ```

### Method B: Standalone APK Sideload (Direct Download)
1. Download `Orbit-Android.apk` from the GitHub Releases page or build artifact.
2. On your device, tap the downloaded APK in your Files/Downloads app.
3. If prompted, allow your browser/file manager to "Install unknown apps".
4. **Android 13+ "Restricted Settings" Unblock:**
   - On Android 13, 14, 15, and 16, sideloaded applications initially have Accessibility and Notification Listener permissions disabled by Android's security policy.
   - To unblock:
     1. Open phone **Settings** -> **Apps** -> **See all apps** -> **Orbit**.
     2. Tap the **three-dot menu (⋮)** in the top right corner.
     3. Select **"Allow restricted settings"**.
     4. Authenticate using your fingerprint, PIN, or pattern.
     5. Now proceed into Orbit to enable the Accessibility Service.

---

## 2. Hardware Setup: CMF Buds Pro 2

1. Pair your CMF Buds Pro 2 with your phone via Bluetooth.
2. Open the **Nothing X** app (or Settings -> Connected Devices -> CMF Buds Pro 2):
   - Go to **Controls** -> **Smart Dial**.
   - Set the gestures:
     - **Single Press:** `Play / Pause`
     - **Double Press:** `Next Track`
     - **Triple Press:** `Previous Track`
     - **Press & Hold:** `Voice Assistant`
3. Open **Orbit**:
   - The Home Dashboard will show:
     - **Earbuds Endpoint:** `Connected`
     - **Charging Case Dial:** `Active (Bridged)`
   - Open **Diagnostics & Devices** -> **Test Dial Input**:
     - Turn the dial clockwise and counterclockwise. The visual dial will rotate in real time!
     - Press the dial once: verify a Single Press event appears in the live log.

---

## 3. Comprehensive Troubleshooting Guide

### Issue 1: "Wheel won't open when I press or hold the dial"
- **Cause A (HFP Voice Command handler not set):**
  - Android has not set Orbit as the default Voice Command handler.
  - *Fix:* Hold the dial button down for 2 seconds. When the "Open with" chooser dialog appears, select **Orbit** -> **"Always"**. If Google Assistant or Gemini opens automatically, go to phone Settings -> Apps -> Default apps -> Opening links / Digital assistant, find Google, and tap "Clear defaults".
- **Cause B (Earbud gestures not routed to media session):**
  - In Nothing X, check that Single/Double/Triple press are mapped to Play/Pause, Next, and Previous.
- **Cause C (Accessibility Service off):**
  - In phone Settings -> Accessibility, ensure Orbit is enabled.

### Issue 2: "System volume panel appears on screen when I turn the dial"
- **Cause:**
  - CMF Buds Pro 2 communicate rotary turns by sending AVRCP absolute volume changes to the Android Bluetooth stack. The Bluetooth stack calls `AudioManager.setStreamVolume(STREAM_MUSIC, ..., FLAG_SHOW_UI)`.
- **Explanation:**
  - Orbit immediately processes the turn and restores the volume to a comfortable mid-range headroom baseline without playing extra UI sounds.
  - On Samsung devices: Install **SoundAssistant** from the Galaxy Store to set the volume panel to a compact minimal bar or move it to the edge.

### Issue 3: "Phone physical volume keys are triggering dial actions"
- **Status:** **Resolved.**
  - Orbit's `AccessibilityService.onKeyEvent` monitors hardware keycodes `KEYCODE_VOLUME_UP` and `KEYCODE_VOLUME_DOWN`. Any volume change occurring within 600ms of a physical volume keypress is tagged as `phoneKeyRecently()` and ignored by the dial decoder.

### Issue 4: "Battery usage feels high"
- **Status:** **Resolved.**
  - In v0.3.0, `OrbitMediaService` automatically pauses the silent `AudioTrack` when the smartphone screen is locked/turned off, eliminating unnecessary Bluetooth DSP processing while in your pocket.

### Issue 5: "Device Manager doesn't see nearby Bluetooth devices"
- **Fix:**
  - Tap the Search icon in Device Manager. If prompted, grant **Nearby Devices** (Android 12+) or **Location** (Android 8-11) permission. Make sure phone Bluetooth is enabled.

