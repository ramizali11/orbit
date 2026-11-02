"""Tests for Windows Action Catalog, Profile and Executor."""
import pytest
from unittest.mock import MagicMock

from orbit.platform.windows.actions import (
    ACTIONS, ActionCategory, DialActionProfile, WindowsActionExecutor
)


def test_action_catalog_sanity():
    assert len(ACTIONS) >= 15
    ids = [a.id for a in ACTIONS]
    assert "volume_up" in ids
    assert "volume_down" in ids
    assert "media_play_pause" in ids
    assert "scroll_up" in ids
    assert "app_switch_next" in ids


def test_dial_action_profile_serialization():
    prof = DialActionProfile(
        cw_action="zoom_in",
        ccw_action="zoom_out",
        click_action="media_next",
        hold_action="mute_toggle",
        invert_direction=True,
        rate_multiplier=2.5,
    )
    d = prof.to_dict()
    assert d["cw_action"] == "zoom_in"
    assert d["invert_direction"] is True
    assert d["rate_multiplier"] == 2.5

    prof2 = DialActionProfile.from_dict(d)
    assert prof2.cw_action == "zoom_in"
    assert prof2.invert_direction is True
    assert prof2.rate_multiplier == 2.5


def test_action_executor_dispatch():
    mock_output = MagicMock()
    mock_brightness = MagicMock()
    mock_brightness.get.return_value = 50.0

    executor = WindowsActionExecutor(mock_output, mock_brightness)

    # Volume up
    assert executor.execute("volume_up", steps=2) is True
    assert mock_output.keys.call_count == 2
    mock_output.keys.assert_called_with("volumeup")

    # Media play/pause
    assert executor.execute("media_play_pause") is True
    mock_output.media.assert_called_with("play_pause")

    # Scroll down
    assert executor.execute("scroll_down", steps=3) is True
    mock_output.scroll.assert_called_with(3)

    # Brightness up
    assert executor.execute("brightness_up", steps=1) is True
    mock_brightness.set.assert_called_with(55.0)

    # App switch next
    assert executor.execute("app_switch_next") is True
    mock_output.keys.assert_called_with("alt+tab")

    # None action
    assert executor.execute("none") is True

