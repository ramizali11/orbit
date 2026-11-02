# 🌀 Orbit

### One Input. Infinite Possibilities.

**Turn your earbuds into more than just earbuds.**

Orbit is an open-source project that aims to transform Bluetooth earbuds and rotary controls into customizable controllers for everyday devices.

Why limit a physical dial to adjusting volume when it could scroll pages, control brightness, zoom in and out, navigate content, or trigger your favourite shortcuts?

Orbit explores new ways to make everyday hardware more useful and customizable.

**Android · Windows · Bluetooth · Custom Controls**

---

## 📑 Index

Navigate directly to any section of this README.

| No. | Section |
|---:|---|
| 01 | [Download Orbit](#-download-orbit) |
| 02 | [What is Orbit?](#-what-is-orbit) |
| 03 | [Features & Capabilities](#-features--capabilities) |
| 04 | [Device Compatibility](#-device-compatibility) |
| 05 | [Platform Support](#️-platform-support) |
| 06 | [Technology Stack](#️-technology-stack) |
| 07 | [Project Architecture](#️-project-architecture) |
| 08 | [Contributing](#-contributing) |
| 09 | [Feedback & Contact](#-feedback--contact) |

---

## 📥 Download Orbit

Choose your platform and get started.

| Platform | Download | Version |
|---|---|---|
| 📱 Android | [Download APK](https://github.com/YOUR_USERNAME/orbit/releases/download/v1.0.0/Orbit-Android.apk) | v1.0.0 |
| 💻 Windows | [Download Windows ZIP](https://github.com/YOUR_USERNAME/orbit/releases/download/v1.0.1/Orbit-Windows.zip) | v1.0.1 |

### Android Installation

1. Download the APK.
2. Open the downloaded file.
3. Allow installation from your browser or file manager if prompted.
4. Install and launch Orbit.

### Windows Installation

1. Download the Windows ZIP.
2. Extract the ZIP file.
3. Open the extracted folder.
4. Run `Orbit.exe`.

*Note: These are early releases. Some features are experimental, and device compatibility may vary.*

---

## ✨ What is Orbit?

Orbit is built around a simple idea: physical hardware should be more customizable.

Many Bluetooth devices have physical controls with predefined functions. Orbit explores ways to make those controls more useful by allowing users to assign different actions to supported inputs.

Instead of having one fixed function, a compatible rotary dial could become a versatile controller for your phone or computer.

## 🚀 Features & Capabilities

Orbit focuses on making physical inputs more versatile.

| Feature | Description |
|---|---|
| 🎧 Bluetooth Integration | Connect and work with supported Bluetooth devices. |
| 🎛️ Rotary Controls | Explore customizable rotary dial functionality. |
| 🔊 Volume Control | Control system volume. |
| 📜 Scrolling | Navigate pages and content using supported inputs. |
| 🔍 Zoom Control | Zoom in and out where supported. |
| 💡 Brightness | Control display brightness where supported. |
| ⏯️ Media Controls | Manage media playback. |
| ⌨️ Shortcuts | Trigger supported keyboard shortcuts. |
| 📱 Cross-Platform | Development for Android and Windows. |

*Actual availability depends on the connected hardware, operating system, and implemented platform support.*

## 🎧 Device Compatibility

Orbit primarily focuses on Bluetooth devices with physical rotary controls.

### Primary Target Devices

- CMF Buds Pro 2
- Other compatible CMF devices
- Third-party earbuds with similar rotary functionality
- Other supported Bluetooth input devices

### Compatibility Philosophy

Orbit aims to support more than one specific product.

The goal is to develop an extensible device architecture that makes it easier to investigate and add support for different hardware.

**Important:** A device appearing in Bluetooth discovery does not automatically mean its rotary input can be captured. Compatibility must be verified on actual hardware.

## 🖥️ Platform Support

### Android

The Android application focuses on Bluetooth integration, supported physical inputs, and customizable controls.

### Windows

The Windows application focuses on desktop integration, Bluetooth input handling, and system-level actions.

## 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| Python | Desktop application logic |
| PySide6 | Windows desktop interface |
| Kotlin | Android application development |
| Jetpack Compose | Android user interface |
| Bluetooth APIs | Device communication and discovery |
| Windows APIs | Desktop input handling |
| CoreAudio | Windows audio endpoint monitoring |

## 🏗️ Project Architecture

Orbit aims to separate device communication, input processing, and action execution.

The general architecture consists of:

1. **Device Discovery** – Detect and identify supported devices.
2. **Input Handling** – Receive available physical input events.
3. **Device Integration** – Handle hardware-specific communication.
4. **Control Engine** – Interpret inputs and determine assigned actions.
5. **Action Execution** – Perform the requested operation.
6. **User Interface** – Allow users to configure and manage controls.

## 🤝 Contributing

Orbit is an evolving open-source project, and contributions are welcome.

You can contribute by:

- Improving existing functionality.
- Adding support for compatible devices.
- Fixing bugs.
- Improving performance.
- Suggesting new features.
- Testing hardware compatibility.
- Improving documentation.

### Contribution Steps

1. Fork this repository.
2. Create a new branch.
3. Make your changes.
4. Test your implementation.
5. Submit a pull request.

If you encounter a hardware compatibility issue, include the device model, operating system, and relevant diagnostic logs.

## 💬 Feedback & Contact

Your feedback helps make Orbit better!

Found a bug, facing a compatibility issue, or have an idea for a new feature? Feel free to share it.

### 🐛 Report a Bug

Found something that isn't working as expected? Open an issue with:

- Device model and operating system.
- Description of the problem.
- Steps to reproduce the issue.
- Screenshots or diagnostic logs, if available.

### 💡 Suggest a Feature

Have an idea that could make Orbit more useful? Open a feature request and describe how it could work.

### 📩 Get in Touch

- **GitHub Issues:** [Report bugs or request features](https://github.com/YOUR_USERNAME/orbit/issues)
- **GitHub Repository:** [Explore the source code](https://github.com/YOUR_USERNAME/orbit)
- **Any problem:** Email: ramizsaiyed202@gmail.com

Contributions, suggestions, testing, and constructive feedback are always welcome.

**Connect. Customize. Control.**
