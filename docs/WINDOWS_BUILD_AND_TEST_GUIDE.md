# Orbit — Windows Build & Verification Guide

*Target: Windows 10 (Build 19041+) and Windows 11 (all versions)*

---

## 1. Quick Start

### 1.1 Prerequisites
- Windows 10 (64-bit) or Windows 11.
- Python 3.10 to 3.13 (Python 3.13 recommended).
- Git.

### 1.2 Setup Environment
From the repository root (`c:\Users\mahen\Desktop\all things\orbit\orbit`):

```powershell
# Create dedicated virtual environment
python -m venv .venv

# Install dependencies
.venv\Scripts\pip install -r requirements.txt pytest pyinstaller pillow
```

---

## 2. Running Orbit for Windows

To launch Orbit in development mode:

```powershell
.venv\Scripts\python -m orbit
```

Orbit will:
1. Initialize the CoreAudio volume listener and Windows ETW sniffer.
2. Place an icon in the Windows System Tray (by the taskbar clock).
3. Automatically open the **Orbit Dashboard & Devices Hub**.

---

## 3. Running Automated Tests

Run the full automated test suite (217 tests covering controls, engine, motion, volume dial, device registry, protocol adapters, actions, and Windows discovery):

```powershell
.venv\Scripts\pytest
```

To run only the Windows protocol and device tests:

```powershell
.venv\Scripts\pytest tests/test_device_registry.py tests/test_protocol_adapters.py tests/test_windows_actions.py tests/test_windows_discovery.py -v
```

---

## 4. Building the Standalone Release Executable (`Orbit.exe`)

To compile the standalone Windows executable:

```powershell
.venv\Scripts\python packaging/windows/build_exe.py
```

The compiled binary will be placed at:
```
dist/Orbit/Orbit.exe
```

---

## 5. Hardware Verification Checklist (Physical CMF Buds Pro 2 & Rotary Dials)

| # | Test Case | Action | Expected Result | Pass/Fail |
|---|---|---|---|---|
| 1 | **Bluetooth Audio Pairing** | Pair CMF Buds Pro 2 in Windows Settings > Bluetooth. | Earbuds connect for audio; appears in Device Manager. | [ ] |
| 2 | **Device Detection** | Open Orbit Dashboard. | Device appears as Connected; Topology shows `INDIRECT_BRIDGED`. | [ ] |
| 3 | **Clockwise Turn (CW)** | Rotate charging-case dial right. | Virtual dial needle turns CW; volume increments (+2%). | [ ] |
| 4 | **Counter-Clockwise (CCW)** | Rotate charging-case dial left. | Virtual dial needle turns CCW; volume decrements (-2%). | [ ] |
| 5 | **Direction Inversion** | Enable "Invert Rotary Direction" in Dial Customization. | Dial turns left for Volume Up, right for Volume Down. | [ ] |
| 6 | **Fast Spin Multiplier** | Spin dial rapidly. | Detents scale smoothly; no skipped callbacks. | [ ] |
| 7 | **Single Press (Click)** | Press charging-case button once. | Media Play/Pause triggers in active Windows media player. | [ ] |
| 8 | **Double Press** | Press charging-case button twice. | Next Track triggers. | [ ] |
| 9 | **Triple Press** | Press charging-case button 3 times. | Previous Track triggers. | [ ] |
| 10 | **Dial Hold (Elevated)** | Run Orbit as Administrator and hold case button for 1s. | ETW sniffs `AT+BVRA=1`; Radial Wheel opens on screen. | [ ] |
| 11 | **Scroll Mode** | Set CW to "Scroll Down" and CCW to "Scroll Up". | Rotating dial scrolls active browser / document window. | [ ] |
| 12 | **Window Switcher** | Set CW to "Next Application (Alt+Tab)". | Rotating dial cycles through open Windows applications. | [ ] |
| 13 | **System Tray Minimization** | Close Orbit main window. | Window hides to System Tray; Orbit remains active in background. | [ ] |
| 14 | **Tray Restore** | Double-click or single-click tray icon. | Orbit Dashboard & Devices Hub re-opens instantly. | [ ] |
| 15 | **Power Toggle** | Click "Orbit Active: ON" button. | Changes to "OFF"; physical dial returns to default OS behavior. | [ ] |

