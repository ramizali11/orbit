"""Diagnostic Tool for Windows Dial Input & Low-Level Interception.

Monitors simultaneously:
1. Low-Level Keyboard Hook (WH_KEYBOARD_LL): Captures VK_VOLUME_UP, VK_VOLUME_DOWN, media keys.
2. CoreAudio Endpoint Callbacks: Monitors volume changes on all active and dynamically connected endpoints.
3. Distinguishes hardware vs injected keyboard events.
4. Allows testing suppression (blocking native volume flyout) if keyboard events are generated.

Usage:
    python tools/dial_input_diagnostic.py [--suppress] [--duration SECONDS]
"""
import argparse
import ctypes
from ctypes import wintypes
import datetime
import os
import sys
import threading
import time

# Win32 Constants
WH_KEYBOARD_LL = 13
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_SYSKEYDOWN = 0x0104
WM_SYSKEYUP = 0x0105

VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF
VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_STOP = 0xB2
VK_MEDIA_PLAY_PAUSE = 0xB3

LLKHF_EXTENDED = 0x01
LLKHF_INJECTED = 0x10
LLKHF_ALTDOWN = 0x20
LLKHF_UP = 0x80

VK_NAMES = {
    VK_VOLUME_MUTE: "VK_VOLUME_MUTE (0xAD)",
    VK_VOLUME_DOWN: "VK_VOLUME_DOWN (0xAE)",
    VK_VOLUME_UP: "VK_VOLUME_UP (0xAF)",
    VK_MEDIA_NEXT_TRACK: "VK_MEDIA_NEXT_TRACK (0xB0)",
    VK_MEDIA_PREV_TRACK: "VK_MEDIA_PREV_TRACK (0xB1)",
    VK_MEDIA_STOP: "VK_MEDIA_STOP (0xB2)",
    VK_MEDIA_PLAY_PAUSE: "VK_MEDIA_PLAY_PAUSE (0xB3)",
}

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode", wintypes.DWORD),
        ("scanCode", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_size_t),
    ]

HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_ssize_t, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)

user32.SetWindowsHookExW.argtypes = [ctypes.c_int, HOOKPROC, wintypes.HINSTANCE, wintypes.DWORD]
user32.SetWindowsHookExW.restype = wintypes.HHOOK
user32.CallNextHookEx.argtypes = [wintypes.HHOOK, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM]
user32.CallNextHookEx.restype = ctypes.c_ssize_t
user32.UnhookWindowsHookEx.argtypes = [wintypes.HHOOK]
kernel32.GetModuleHandleW.restype = wintypes.HMODULE
kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]

class DialDiagnostic:
    def __init__(self, suppress: bool = False):
        self.suppress = suppress
        self.hook = None
        self._hook_proc = None
        self.events_log = []
        self.running = True
        self._bound_endpoints = {}

    def log(self, channel: str, msg: str):
        now = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        line = f"[{now}] [{channel:14s}] {msg}"
        print(line, flush=True)
        self.events_log.append(line)

    def _ll_key_callback(self, nCode, wParam, lParam):
        if nCode >= 0:
            kb = KBDLLHOOKSTRUCT.from_address(lParam)
            vk = kb.vkCode
            is_up = bool(kb.flags & LLKHF_UP)
            is_injected = bool(kb.flags & LLKHF_INJECTED)
            is_ext = bool(kb.flags & LLKHF_EXTENDED)
            action = "KEY_UP" if is_up else "KEY_DOWN"
            vk_name = VK_NAMES.get(vk, f"VK_0x{vk:02X}")

            # Highlight volume and media keys
            if vk in (VK_VOLUME_UP, VK_VOLUME_DOWN, VK_VOLUME_MUTE,
                      VK_MEDIA_PLAY_PAUSE, VK_MEDIA_NEXT_TRACK, VK_MEDIA_PREV_TRACK):
                src_desc = "INJECTED (App/Driver)" if is_injected else "PHYSICAL/HARDWARE"
                self.log("KEYBOARD_LL",
                         f"{action:8s} | {vk_name:24s} | Scan={kb.scanCode:02X} | "
                         f"Flags=0x{kb.flags:02X} ({src_desc}) | ExtraInfo={kb.dwExtraInfo}")

                if self.suppress and not is_up:
                    self.log("KEYBOARD_LL", f"--> [SUPPRESSED] {vk_name} (blocked native volume popup)")
                    return 1  # Block event from reaching Windows volume manager

        return user32.CallNextHookEx(self.hook, nCode, wParam, lParam)

    def _bind_all_endpoints(self):
        try:
            from pycaw.pycaw import AudioUtilities
            from pycaw.callbacks import AudioEndpointVolumeCallback

            outer = self
            class VolNotify(AudioEndpointVolumeCallback):
                def __init__(self, dev_id, dev_name):
                    super().__init__()
                    self.dev_id = dev_id
                    self.dev_name = dev_name

                def on_notify(self, new_volume, new_mute, event_context, channels, channel_volumes):
                    outer.log(
                        "COREAUDIO_VOL",
                        f"Endpoint='{self.dev_name}' | Level={new_volume * 100:5.1f}% | "
                        f"Mute={new_mute} | Context={event_context.contents}"
                    )

            enumerator = AudioUtilities.GetDeviceEnumerator()
            coll = enumerator.EnumAudioEndpoints(0, 1)  # eRender, ACTIVE
            for i in range(coll.GetCount()):
                dev = AudioUtilities.CreateDevice(coll.Item(i))
                if dev.id not in self._bound_endpoints:
                    cb = VolNotify(dev.id, dev.FriendlyName)
                    dev.EndpointVolume.RegisterControlChangeNotify(cb)
                    self._bound_endpoints[dev.id] = (dev, cb)
                    self.log("COREAUDIO_INIT", f"Attached callback to active endpoint: '{dev.FriendlyName}'")

        except Exception as e:
            self.log("COREAUDIO_WARN", f"Failed binding endpoints: {e}")

    def run(self, duration_s: float = 0):
        print("=" * 80)
        print("ORBIT WINDOWS — PHYSICAL DIAL INPUT & LOW-LEVEL INTERCEPTION DIAGNOSTIC")
        print("=" * 80)
        print(f"Mode: {'[SUPPRESSION ACTIVE] Intercepting & swallowing volume keys' if self.suppress else '[MONITORING ONLY] Passive logging'}")
        print("Monitors in parallel:")
        print("  [1] WH_KEYBOARD_LL (Windows Low-Level Keyboard Hook: VK_VOLUME_UP/DOWN, Media)")
        print("  [2] CoreAudio IAudioEndpointVolumeCallback (Master Endpoint Volume Events)")
        print("-" * 80)
        print("DIAGNOSTIC TEST PROCEDURE:")
        print("  1. Rotate physical dial CLOCKWISE (several clicks).")
        print("  2. Rotate physical dial COUNTER-CLOCKWISE (several clicks).")
        print("  3. Press physical dial BUTTON (single click, double click).")
        print("  4. Press keyboard Volume Up / Volume Down keys (to compare signature).")
        print("-" * 80)

        self._bind_all_endpoints()

        # Install WH_KEYBOARD_LL hook
        self._hook_proc = HOOKPROC(self._ll_key_callback)
        mod = kernel32.GetModuleHandleW(None)
        self.hook = user32.SetWindowsHookExW(
            WH_KEYBOARD_LL,
            self._hook_proc,
            mod,
            0
        )

        if not self.hook:
            err = ctypes.get_last_error()
            self.log("ERROR", f"Failed to install WH_KEYBOARD_LL (error code: {err})")
            return

        self.log("INIT", f"WH_KEYBOARD_LL hook active (HHOOK=0x{self.hook:X}). Listening for events...")

        start_time = time.time()
        msg = wintypes.MSG()

        try:
            last_rebind = 0
            while self.running:
                # Refresh endpoints every 3 seconds to catch newly connected Bluetooth earbuds
                now = time.time()
                if now - last_rebind > 3.0:
                    last_rebind = now
                    self._bind_all_endpoints()

                # Process Windows message queue
                while user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, 1):  # PM_REMOVE
                    user32.TranslateMessage(ctypes.byref(msg))
                    user32.DispatchMessageW(ctypes.byref(msg))

                time.sleep(0.01)

                if duration_s > 0 and (time.time() - start_time) >= duration_s:
                    break
        except KeyboardInterrupt:
            print("\nDiagnostic stopped by user.")
        finally:
            if self.hook:
                user32.UnhookWindowsHookEx(self.hook)
                self.log("EXIT", "WH_KEYBOARD_LL hook uninstalled.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--suppress", action="store_true", help="Suppress intercepted volume keys (return 1)")
    parser.add_argument("--duration", type=float, default=0, help="Run duration in seconds (0 = forever)")
    args = parser.parse_args()

    diag = DialDiagnostic(suppress=args.suppress)
    diag.run(duration_s=args.duration)
