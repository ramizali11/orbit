# Orbit Universal Dial Controller — Implementation Plan

**Target:** Android First  
**Architecture:** Clean Protocol & Extensible Component Architecture  
**Standards:** Kotlin Coroutines/Flow, Jetpack Compose, Android Bluetooth / BLE, AccessibilityService

---

## Milestone Breakdown & Execution Roadmap

```
+---------------------------------------------------------------------------------------+
| MILESTONE 1: Repository Audit & Architecture Understanding (COMPLETED)               |
| - Inspect repository, docs, Python & Android codebases.                               |
| - Document audit, compatibility matrix, and implementation plan.                      |
+---------------------------------------------------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------+
| MILESTONE 2: Universal Bluetooth Discovery & Device Fingerprinting                    |
| - Implement Bluetooth permissions handling (BLUETOOTH_SCAN, CONNECT, FINE_LOCATION).  |
| - Dual-mode discovery (Classic Bluetooth discovery + BLE Scanner).                   |
| - DeviceFingerprint, FingerprintExtractor, and DeviceRegistry for deduplication.      |
| - Unit tests for fingerprinting and duplicate resolution.                             |
+---------------------------------------------------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------+
| MILESTONE 3: Separate Earbud & Charging-Case Endpoints                                |
| - Endpoint model: EarbudsEndpoint, CaseEndpoint, UnifiedDeviceSession.                 |
| - Topology engine: Direct Dual-Radio vs Indirect Bridged Dial (CMF Buds Pro 2 style). |
| - Independent connection state monitoring and live UI status representation.          |
+---------------------------------------------------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------+
| MILESTONE 4: CMF Buds Pro 2 Protocol Integration                                      |
| - Harden CmfAvrcpHfpAdapter: 16-step grid alignment, echo cancellation, fresh-set.   |
| - Phone volume button filter (prevent volume rockers from firing dial actions).       |
| - Audio output device binding (only parse volume when active route is CMF device).    |
+---------------------------------------------------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------+
| MILESTONE 5: Replica & Unknown-Device Discovery Framework                             |
| - ProtocolAdapter interface: CmfAvrcpHfpAdapter, BleGattDialAdapter, BleHidAdapter.   |
| - ProtocolDetector: heuristic and fingerprint-based protocol selection.               |
| - Unknown device diagnostic probe & safe capability interrogation.                    |
+---------------------------------------------------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------+
| MILESTONE 6: Rotary Dial Event Detection & Normalization                              |
| - Logical events: Rotate CW/CCW, Single, Double, Triple, Hold, Continuous, Rapid.     |
| - Debounce, deduplicate, momentum/acceleration curves (SpinTracker).                  |
| - Live Input Diagnostics screen in UI (instant visual feedback on physical turn).     |
+---------------------------------------------------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------+
| MILESTONE 7: Universal & Customizable Action Engine                                   |
| - Expanded Action Catalog: Volume, Brightness, Smooth Scroll, Page Up/Down, App Switch|
|   Camera Zoom/Shutter, Undo/Redo, Media Transport, Custom Shortcuts.                  |
| - Per-profile and per-tool sensitivity/acceleration parameters.                       |
+---------------------------------------------------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------+
| MILESTONE 8: Android Dashboard, Onboarding & Settings UI                              |
| - 12-Step Guided Onboarding Wizard.                                                   |
| - Modern Compose Dashboard with Dual-Endpoint status cards, event monitor & presets.  |
| - Device Manager Screen (Scan, Pair, Rename, Fingerprint Inspection, Forget).         |
+---------------------------------------------------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------+
| MILESTONE 9: Background Services, Permissions & Reliability                           |
| - Robust FGS lifecycle management, automatic reconnect on Bluetooth ACL connect.     |
| - Screen-off low-power mode (suspend silence loop to conserve battery).              |
| - Graceful recovery from audio focus loss or service interruption.                    |
+---------------------------------------------------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------+
| MILESTONE 10: Automated Tests & Validation                                            |
| - Comprehensive test suite for Bluetooth discovery, fingerprinting, protocol decoders.|
| - Simulated mock Bluetooth devices and synthetic AVRCP/BLE event streams.             |
| - Hardware testing checklist for physical CMF Buds Pro 2 verification.                |
+---------------------------------------------------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------+
| MILESTONE 11: APK Generation, Release Documentation & Progress Handover               |
| - Gradle build verification, APK artifact generation.                                 |
| - Complete Release Notes, Troubleshooting Guide, and docs/PROGRESS.md report.         |
+---------------------------------------------------------------------------------------+
```

---

## Technical Risk Mitigation Matrix

| Identified Risk | Impact | Engineering Mitigation Strategy |
|---|---|---|
| Android 12+ Bluetooth runtime permission denials | Scan fails silently | Granular pre-flight checks, informative rationale UI, and fallback to bonded-only device enumeration. |
| System Volume Panel flashing on dial turn | Visual annoyance | Re-center to quiet grid position, minimal delta operations, and documented OEM volume panel styling guidance. |
| Competing VOICE_COMMAND handlers (Google App / Gemini) | Dial hold does not reach Orbit | Direct user to "Open with Orbit -> Always" in onboarding with verification check via `PackageManager.resolveActivity`. |
| Physical phone volume keys misidentified as dial turn | Spurious dial action | Filter keyevents via `AccessibilityService.onKeyEvent` timestamp correlation (<600ms grace window). |
| Battery drain from continuous silent audio playback | Reduced battery life | Suspend silent `AudioTrack` when display is off or when no audio output device is routed to earbuds. |

