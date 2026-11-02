# Orbit — Windows Architecture & Implementation Plan

*Author: Senior Systems & Windows Software Engineer*  
*Target Release: Orbit Universal Dial Controller for Windows 10 & 11*  
*Date: 2026-11-02*

---

## 1. Architectural Blueprint

Orbit for Windows provides a desktop utility experience designed for physical rotary dial interaction. It harmonizes with the existing Android core architecture while utilizing native Windows platform capabilities.

```
┌────────────────────────────────────────────────────────────────────────┐
│                          ORBIT DESKTOP UI                              │
│  ┌───────────────┐ ┌────────────────┐ ┌────────────────┐ ┌──────────┐  │
│  │   Dashboard   │ │ Device Manager │ │ Dial Config    │ │ Live Test│  │
│  └───────────────┘ └────────────────┘ └────────────────┘ └──────────┘  │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │         Live Dial Visualization (16-step animated Canvas)        │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Qt Signal / Bus
┌───────────────────────────────────▼────────────────────────────────────┐
│                         ORBIT CORE ENGINE                              │
│  ┌───────────────────────────────┐  ┌────────────────────────────────┐ │
│  │     DialEventNormalizer       │  │          ActionCatalog         │ │
│  │  (Rate, Direction, Debounce)  │  │ (Volume, Nav, Media, Apps, Key)│ │
│  └───────────────────────────────┘  └────────────────────────────────┘ │
│  ┌───────────────────────────────┐  ┌────────────────────────────────┐ │
│  │       DeviceRegistry          │  │       EndpointManager          │ │
│  │ (Fingerprinting, Nicknames)   │  │(Earbuds vs Case Dual-Endpoint) │ │
│  └───────────────────────────────┘  └────────────────────────────────┘ │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│                    PROTOCOL ADAPTER ABSTRACTION                        │
│  ┌───────────────────────┐  ┌───────────────────┐  ┌─────────────────┐ │
│  │  CmfAvrcpHfpAdapter   │  │ GenericAvrcpAdapter│  │BleHidDialAdapter│ │
│  └───────────────────────┘  └───────────────────┘  └─────────────────┘ │
│  ┌───────────────────────┐  ┌───────────────────┐                      │
│  │  BleGattDialAdapter   │  │UnknownDeviceAdapter│                      │
│  └───────────────────────┘  └───────────────────┘                      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│                      NATIVE WINDOWS SUBSYSTEMS                         │
│  ┌──────────────────┐  ┌─────────────────┐  ┌────────────────────────┐ │
│  │ WinRT Bluetooth  │  │ CoreAudio       │  │ ETW BTHPORT Session    │ │
│  │ (BLE & Discovery)│  │ (AVRCP Volume)  │  │ (HFP AT+BVRA Sniffer)  │ │
│  └──────────────────┘  └─────────────────┘  └────────────────────────┘ │
│  ┌──────────────────┐  ┌─────────────────┐  ┌────────────────────────┐ │
│  │ Windows Media    │  │ SendInput       │  │ WMI Monitor Brightness │ │
│  │ (SMTC Hook)      │  │ (Keys / Mouse)  │  │ (PowerShell Bridge)    │ │
│  └──────────────────┘  └─────────────────┘  └────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Implementation Milestones

### Milestone 1: Windows Architecture & Planning (Complete)
- [x] Audit existing Windows codebase (`orbit/platform/windows/`, `orbit/core/`, `orbit/ui/`).
- [x] Create `docs/WINDOWS_COMPATIBILITY.md`.
- [x] Create `docs/WINDOWS_IMPLEMENTATION_PLAN.md`.

### Milestone 2: Universal Bluetooth Discovery & Device Registry
- [ ] Create `orbit/platform/windows/discovery.py`:
  - Enumerate paired and nearby Bluetooth devices using WinRT `Windows.Devices.Enumeration.DeviceInformation` and Windows CoreAudio endpoints.
  - Query device names, addresses/IDs, connection state, device class, and signal strength (RSSI).
  - Background asynchronous scanning with cancellation.
- [ ] Create `orbit/core/device_registry.py`:
  - 6-tuple device fingerprint: `(name, address, vendor_id, product_id, service_uuids, device_class)`.
  - Disambiguate duplicate device names.
  - Persist known devices, user-assigned custom names, and preferred protocol adapters in `~/.orbit/registry.json`.

### Milestone 3: Dual-Endpoint Architecture
- [ ] Create `orbit/core/endpoints.py`:
  - `EarbudsEndpoint`: Handles audio output state, playback status, volume level.
  - `ChargingCaseEndpoint`: Handles rotary dial status, battery, rotation events.
  - `DeviceSession`: Dual-endpoint controller supporting `INDIRECT_BRIDGED` (CMF Buds Pro 2 topology) and `DIRECT_DUAL_RADIO`.

### Milestone 4: Extensible Protocol Adapters
- [ ] Implement `orbit/protocol/`:
  - `ProtocolAdapter` base interface with capability flags (`ROTATE`, `CLICK`, `HOLD`, `BATTERY`).
  - `CmfAvrcpHfpAdapter`: Bridges AVRCP absolute volume ticks with ETW HFP `AT+BVRA` hold events.
  - `GenericAvrcpAdapter`: Adaptive grid step detection (8–32 steps) for clones and third-party earbuds.
  - `BleHidDialAdapter`: Standard BLE HID Consumer Control / Radial Controller report decoder.
  - `BleGattDialAdapter`: Standard signed byte delta GATT notify subscriber.
  - `UnknownDeviceAdapter`: Safe diagnostic packet sniffer.
  - `ProtocolDetector`: Automatic fingerprint-based detection with manual fallback.

### Milestone 5: Expanded Windows Action Catalog & Execution Engine
- [ ] Create `orbit/platform/windows/actions.py`:
  - System Volume: Volume Up (+2%), Volume Down (-2%), Mute/Unmute.
  - Media: Play/Pause, Next Track, Previous Track, Stop.
  - Navigation & Scrolling: Scroll Up, Scroll Down, Page Up, Page Down, Zoom In, Zoom Out.
  - Window & Task Management: Alt+Tab (Switch Applications), Task View (Win+Tab), Minimize Window, Desktop Toggle (Win+D).
  - Screen Brightness: Brightness Up (+5%), Brightness Down (-5%) via WMI.
  - Custom Shortcuts: Key combinations (e.g., Ctrl+Z, Ctrl+Y, Ctrl+Shift+S).
  - Application Launching: Launch installed applications or custom executables.
  - Rate Scaling & Direction Inversion: Multipliers for fast spins and clockwise/counterclockwise reversal.

### Milestone 6: Polished Native Windows Desktop UI
- [ ] Update / Create `orbit/ui/`:
  - **Dashboard View**: Dual-endpoint status cards (Earbuds + Charging Case), quick ON/OFF switch, current action summary.
  - **Device Manager & Scanner**: Live scanning for nearby devices, paired list, RSSI signal indicators, device renaming, adapter selection.
  - **Dial Configuration**: Direct visual mapping of CW, CCW, Single Click, Double Click, Triple Click, and Hold to Action Catalog items.
  - **Live Input Testing Screen**: Interactive 16-step animated Canvas dial reflecting real-time physical rotations, tick counter, RPM/speed meter, and event log.
  - **Diagnostics View**: Real-time packet and event monitor showing raw AVRCP, ETW, HID, and GATT logs.
  - **Settings**: Windows autostart toggle, system tray behavior, volume flyout suppression, dark theme styling matching Android `#FF5500` accents.

### Milestone 7: Background Operation & Reliability
- [ ] Windows System Tray:
  - Notification icon with animated or status-tinted glyph.
  - Context menu: Orbit ON/OFF toggle, Show Dashboard, Show Wheel, Settings, Device Status, Exit.
- [ ] Windows Autostart:
  - Configure via Registry (`HKCU\Software\Microsoft\Windows\CurrentVersion\Run`).
- [ ] Power & Session Management:
  - Handle system sleep/wake cleanly without dropping ETW sessions or crashing CoreAudio callbacks.

### Milestone 8: Automated Unit Testing & Verification
- [ ] Write pytest unit tests:
  - Fingerprint generation, comparison, and serialization.
  - Protocol adapter event mapping.
  - Rate scaling and direction inversion.
  - Action catalog execution.
  - Windows registry and settings persistence.
- [ ] Execute test suite and verify 100% pass rate.

### Milestone 9: Windows Executable Build & Release
- [ ] Run `packaging/windows/build_exe.py` to build `dist/Orbit/Orbit.exe`.
- [ ] Validate standalone executable startup and smoke tests.
- [ ] Document build and installation instructions in `README.md`.

