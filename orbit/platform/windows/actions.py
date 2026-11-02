"""Windows Dial Action Catalog and Execution Engine.

Provides predefined and customizable actions for rotary dial turns and clicks,
covering system volume, media transport, window management, scrolling, display
brightness, keyboard macros, and application launching.
"""
from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Callable, Optional

log = logging.getLogger("orbit.actions")


class ActionCategory(str, Enum):
    VOLUME = "Volume & Audio"
    MEDIA = "Media Playback"
    NAVIGATION = "Scrolling & Navigation"
    WINDOW = "Window Management"
    DISPLAY = "Display & Screen"
    PRODUCTIVITY = "Shortcuts & Apps"


@dataclass
class ActionItem:
    id: str
    title: str
    category: ActionCategory
    description: str
    default_param: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "category": self.category.value,
            "description": self.description,
            "default_param": self.default_param,
        }


ACTIONS = [
    # Volume
    ActionItem("volume_up", "Volume Up (+2%)", ActionCategory.VOLUME, "Increases master system volume"),
    ActionItem("volume_down", "Volume Down (-2%)", ActionCategory.VOLUME, "Decreases master system volume"),
    ActionItem("mute_toggle", "Mute / Unmute", ActionCategory.VOLUME, "Toggles audio mute"),
    # Media
    ActionItem("media_play_pause", "Play / Pause", ActionCategory.MEDIA, "Toggles playback in active media player"),
    ActionItem("media_next", "Next Track", ActionCategory.MEDIA, "Skips to next media track"),
    ActionItem("media_prev", "Previous Track", ActionCategory.MEDIA, "Rewinds to previous track"),
    ActionItem("media_stop", "Stop Playback", ActionCategory.MEDIA, "Stops media playback"),
    # Navigation
    ActionItem("scroll_up", "Scroll Up", ActionCategory.NAVIGATION, "Scrolls active window upwards"),
    ActionItem("scroll_down", "Scroll Down", ActionCategory.NAVIGATION, "Scrolls active window downwards"),
    ActionItem("page_up", "Page Up", ActionCategory.NAVIGATION, "Sends Page Up key"),
    ActionItem("page_down", "Page Down", ActionCategory.NAVIGATION, "Sends Page Down key"),
    ActionItem("zoom_in", "Zoom In (Ctrl +)", ActionCategory.NAVIGATION, "Zooms in active document / browser"),
    ActionItem("zoom_out", "Zoom Out (Ctrl -)", ActionCategory.NAVIGATION, "Zooms out active document / browser"),
    # Window Management
    ActionItem("app_switch_next", "Next Application (Alt+Tab)", ActionCategory.WINDOW, "Switches to next application"),
    ActionItem("app_switch_prev", "Previous Application (Alt+Shift+Tab)", ActionCategory.WINDOW, "Switches to previous application"),
    ActionItem("task_view", "Task View (Win+Tab)", ActionCategory.WINDOW, "Opens Windows Task View"),
    ActionItem("show_desktop", "Show Desktop (Win+D)", ActionCategory.WINDOW, "Toggles desktop visibility"),
    # Display
    ActionItem("brightness_up", "Brightness Up (+5%)", ActionCategory.DISPLAY, "Increases internal screen brightness"),
    ActionItem("brightness_down", "Brightness Down (-5%)", ActionCategory.DISPLAY, "Decreases internal screen brightness"),
    # Productivity
    ActionItem("undo", "Undo (Ctrl+Z)", ActionCategory.PRODUCTIVITY, "Sends Undo shortcut"),
    ActionItem("redo", "Redo (Ctrl+Y)", ActionCategory.PRODUCTIVITY, "Sends Redo shortcut"),
    ActionItem("open_wheel", "Open Orbit Wheel", ActionCategory.PRODUCTIVITY, "Opens the radial overlay menu"),
    ActionItem("custom_key", "Custom Keyboard Shortcut", ActionCategory.PRODUCTIVITY, "Sends a user-defined key combination", "ctrl+shift+space"),
    ActionItem("launch_app", "Launch Application…", ActionCategory.PRODUCTIVITY, "Opens an application by name or path", "notepad.exe"),
    ActionItem("none", "Do Nothing", ActionCategory.PRODUCTIVITY, "No action assigned"),
]


@dataclass
class DialActionProfile:
    """Configurable action profile for a dial device."""
    cw_action: str = "volume_up"
    ccw_action: str = "volume_down"
    click_action: str = "media_play_pause"
    double_click_action: str = "media_next"
    triple_click_action: str = "media_prev"
    hold_action: str = "open_wheel"
    invert_direction: bool = False
    rate_multiplier: float = 1.0
    cw_param: str = ""
    ccw_param: str = ""
    click_param: str = ""
    double_click_param: str = ""
    triple_click_param: str = ""
    hold_param: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> DialActionProfile:
        return cls(
            cw_action=d.get("cw_action", "volume_up"),
            ccw_action=d.get("ccw_action", "volume_down"),
            click_action=d.get("click_action", "media_play_pause"),
            double_click_action=d.get("double_click_action", "media_next"),
            triple_click_action=d.get("triple_click_action", "media_prev"),
            hold_action=d.get("hold_action", "open_wheel"),
            invert_direction=bool(d.get("invert_direction", False)),
            rate_multiplier=float(d.get("rate_multiplier", 1.0)),
            cw_param=d.get("cw_param", ""),
            ccw_param=d.get("ccw_param", ""),
            click_param=d.get("click_param", ""),
            double_click_param=d.get("double_click_param", ""),
            triple_click_param=d.get("triple_click_param", ""),
            hold_param=d.get("hold_param", ""),
        )


class WindowsActionExecutor:
    """Executes ActionItem commands against native Windows APIs."""

    def __init__(self, output, brightness_backend=None):
        self.output = output
        self.brightness = brightness_backend

    def execute(self, action_id: str, param: str = "", steps: int = 1) -> bool:
        if action_id == "none" or not action_id:
            return True

        try:
            # Volume
            if action_id == "volume_up":
                for _ in range(max(1, steps)):
                    self.output.keys("volumeup")
                return True
            elif action_id == "volume_down":
                for _ in range(max(1, steps)):
                    self.output.keys("volumedown")
                return True
            elif action_id == "mute_toggle":
                self.output.keys("mute")
                return True

            # Media
            elif action_id == "media_play_pause":
                self.output.media("play_pause")
                return True
            elif action_id == "media_next":
                self.output.media("next")
                return True
            elif action_id == "media_prev":
                self.output.media("previous")
                return True
            elif action_id == "media_stop":
                self.output.media("stop")
                return True

            # Scrolling & Zoom
            elif action_id == "scroll_up":
                self.output.scroll(-steps)
                return True
            elif action_id == "scroll_down":
                self.output.scroll(steps)
                return True
            elif action_id == "page_up":
                for _ in range(max(1, steps)):
                    self.output.keys("pageup")
                return True
            elif action_id == "page_down":
                for _ in range(max(1, steps)):
                    self.output.keys("pagedown")
                return True
            elif action_id == "zoom_in":
                for _ in range(max(1, steps)):
                    self.output.keys("ctrl+plus")
                return True
            elif action_id == "zoom_out":
                for _ in range(max(1, steps)):
                    self.output.keys("ctrl+minus")
                return True

            # Window
            elif action_id == "app_switch_next":
                self.output.keys("alt+tab")
                return True
            elif action_id == "app_switch_prev":
                self.output.keys("alt+shift+tab")
                return True
            elif action_id == "task_view":
                self.output.keys("win+tab")
                return True
            elif action_id == "show_desktop":
                self.output.keys("win+d")
                return True

            # Display Brightness
            elif action_id in ("brightness_up", "brightness_down"):
                if self.brightness:
                    cur = self.brightness.get()
                    if cur is not None:
                        delta = 5.0 * steps if action_id == "brightness_up" else -5.0 * steps
                        self.brightness.set(cur + delta)
                        return True
                return False

            # Productivity
            elif action_id == "undo":
                self.output.keys("ctrl+z")
                return True
            elif action_id == "redo":
                self.output.keys("ctrl+y")
                return True
            elif action_id == "custom_key":
                combo = param.strip() or "ctrl+shift+space"
                self.output.keys(combo)
                return True
            elif action_id == "launch_app":
                target = param.strip()
                if target:
                    self.output.launch(target)
                return True

            log.warning("unhandled action: %s", action_id)
            return False
        except Exception:
            log.exception("failed executing action %s", action_id)
            return False

