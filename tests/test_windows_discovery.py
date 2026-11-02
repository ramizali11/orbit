"""Tests for Windows Bluetooth Discovery."""
import pytest
from orbit.platform.windows.discovery import WindowsBluetoothDiscovery, _format_mac


def test_format_mac():
    assert _format_mac("40ED98112233") == "40:ED:98:11:22:33"
    assert _format_mac("40:ED:98:11:22:33") == "40:ED:98:11:22:33"
    # Integer address
    val = 0x40ED98112233
    assert _format_mac(val) == "40:ED:98:11:22:33"


def test_discovery_query():
    disc = WindowsBluetoothDiscovery()
    devs = disc.discover_all(issue_inquiry=False)
    # On Windows machine with paired devices, devs will list them
    assert isinstance(devs, list)
    for d in devs:
        assert d.fingerprint.address
        assert d.display_name

