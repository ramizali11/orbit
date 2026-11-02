# Orbit Hardware Testing Guide: CMF Buds Pro 2 & Rotary Dials

**Target:** Real Device Validation  
**Primary Target Device:** CMF Buds Pro 2 (Charging Case Smart Dial)

---

## 1. Hardware Architecture Verification

### Understanding the CMF Buds Pro 2 Case Dial:
1. **The Case has no independent Bluetooth MAC address.**
   - The rotary dial is wired via pogo pins to the earbuds inside the case, or linked via internal RF to the master bud when the lid is open.
   - Therefore, the case **cannot** pair directly or independently with a phone or computer without at least one earbud connected.
   - Orbit models this accurately as `INDIRECT_BRIDGED` topology (`DeviceTopology.INDIRECT_BRIDGED`).
2. **Nothing X Dial Gestures Requirement:**
   - In Nothing X (or Phone Settings -> Connected Devices -> CMF Buds Pro 2 -> Controls -> Dial):
     - **Rotate:** Leave enabled (adjusts volume / AVRCP absolute volume).
     - **Single Press:** Set to **Play / Pause**.
     - **Double Press:** Set to **Next Track**.
     - **Triple Press:** Set to **Previous Track**.
     - **Press & Hold:** Set to **Voice Assistant** (triggers HFP `AT+BVRA=1`).

---

## 2. 20-Point Physical Testing Checklist

Execute these tests with real physical hardware:

### A. Pairing & Discovery
- [ ] **1. Bonded Device Detection:** Pair CMF Buds Pro 2 in Android Settings. Open Orbit -> Device Manager. Verify CMF Buds Pro 2 appears with `CMF_AVRCP` badge and `VERIFIED` status.
- [ ] **2. Separate Endpoints Status:** Open Dashboard. Verify **Earbuds Endpoint** shows `Connected` (green dot) and **Charging Case Dial** shows `Active (Bridged)` (green dot).
- [ ] **3. Disconnect Verification:** Put earbuds in case and close lid. Verify Earbuds Endpoint switches to `Disconnected` and Case Dial switches to `Requires Earbuds`.
- [ ] **4. Duplicate Name Resolution:** Connect a second pair of CMF buds (or a clone). Verify Device Manager displays both without collision, distinguishing them by hardware address or custom user alias.

### B. Dial Rotation Testing
- [ ] **5. Slow Clockwise Rotation:** Open "Test Dial Input" screen. Rotate dial slowly 5 clicks clockwise. Verify the visual on-screen dial rotates clockwise with each detent and "TICKS" counter increments by 5.
- [ ] **6. Slow Counterclockwise Rotation:** Rotate dial 5 clicks counterclockwise. Verify visual dial rotates counterclockwise and counter decreases.
- [ ] **7. Fast / Flick Rotation:** Flick the dial rapidly 5+ clicks. Verify `SpinTracker` detects acceleration and reports `Rapid Spin` without locking or crashing.
- [ ] **8. Direction Reversal:** Turn CW 3 clicks, then immediately CCW 3 clicks. Verify no lag or reverse overshoot.
- [ ] **9. System Volume Rocker Disambiguation:** While in Test Dial Input, press the phone's physical hardware volume button (+ and -). Verify that the phone keypress is filtered out and NOT counted as a physical dial turn.

### C. Press & Hold Testing
- [ ] **10. Single Press:** Press the physical dial button once. Verify "Single Press" appears in the live telemetry log and commit action fires.
- [ ] **11. Double Press:** Double-click the dial button. Verify "Double Press" fires and triggers the secondary tool.
- [ ] **12. Triple Press:** Triple-click the dial button. Verify "Triple Press" fires.
- [ ] **13. Long Press (Hold):** Press and hold the dial button for ~1.5s. When Android prompt appears for Voice Command the first time, select **Orbit -> "Always"**. Verify subsequent holds launch the Orbit radial wheel.
- [ ] **14. Rapid Repeat Hold:** Hold once, then hold again within 4 seconds. Note: HFP stack rate-limits `AT+BVRA` to ~5s intervals; verify graceful timeout handling.

### D. Audio & Background Operation
- [ ] **15. Real Music Playback:** Open Spotify or YouTube and start playing music. Rotate dial to drive Orbit tools (e.g. Smooth Scroll). Verify music playback continues without interruption.
- [ ] **16. Media Button Forwarding:** With Orbit on and radial wheel closed, press the dial once. Verify music pauses/resumes via `OrbitNotificationListener`.
- [ ] **17. Screen Locked / Off:** Turn the screen off. Verify battery saver suspends the silent audio track. Turn screen on; verify Orbit immediately resumes ownership.
- [ ] **18. Bluetooth Disconnection & Recovery:** Turn Bluetooth off in phone settings, then back on. Verify `OrbitMediaService` and `EndpointManager` reconnect automatically.
- [ ] **19. Phone Reboot:** Restart smartphone. Verify `OrbitAccessibilityService` starts upon boot and restores wheel overlay capability.
- [ ] **20. 2-Hour Stability Test:** Keep Orbit active in background for 2 hours during normal daily phone use. Check battery stats in Android Settings -> Battery. Verify battery usage remains low (< 2-3%).

