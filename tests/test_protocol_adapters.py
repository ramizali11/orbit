"""Tests for Protocol Adapters and ProtocolDetector."""
import pytest

from orbit.core.device_registry import DeviceFingerprint
from orbit.core.events import Kind
from orbit.protocol.adapters import (
    BleGattDialAdapter, BleHidDialAdapter, CmfAvrcpHfpAdapter,
    GenericAvrcpAdapter, ProtocolDetector, UnknownDeviceAdapter
)


def test_detector_cmf_buds_pro_2():
    fp = DeviceFingerprint(name="CMF Buds Pro 2", address="40:ED:98:AA:BB:CC")
    adapter = ProtocolDetector.detect(fp)
    assert isinstance(adapter, CmfAvrcpHfpAdapter)
    assert adapter.id == "cmf-avrcp-hfp"


def test_detector_surface_dial_hid():
    fp = DeviceFingerprint(name="Surface Dial", service_uuids=["00001812-0000-1000-8000-00805f9b34fb"])
    adapter = ProtocolDetector.detect(fp)
    assert isinstance(adapter, BleHidDialAdapter)
    assert adapter.id == "ble-hid"


def test_detector_generic_earbuds():
    fp = DeviceFingerprint(name="TWS Earbuds Pro", address="11:22:33:44:55:66")
    adapter = ProtocolDetector.detect(fp)
    assert isinstance(adapter, GenericAvrcpAdapter)
    assert adapter.id == "generic-avrcp"


def test_detector_manual_override():
    fp = DeviceFingerprint(name="CMF Buds Pro 2", address="40:ED:98:AA:BB:CC")
    adapter = ProtocolDetector.detect(fp, manual_override="ble-hid")
    assert isinstance(adapter, BleHidDialAdapter)


def test_ble_hid_report_decoding():
    adapter = BleHidDialAdapter("Test Dial")
    # Positive rotation step (+1)
    ev_pos = adapter.decode_report(b"\x01")
    assert ev_pos is not None
    assert ev_pos.kind == Kind.ROTATE
    assert ev_pos.delta == 1

    # Negative rotation step (-1)
    ev_neg = adapter.decode_report(b"\xff")
    assert ev_neg is not None
    assert ev_neg.kind == Kind.ROTATE
    assert ev_neg.delta == -1

    # Zero delta -> None
    assert adapter.decode_report(b"\x00") is None


def test_ble_gatt_notification_decoding():
    adapter = BleGattDialAdapter("Custom BLE")
    # Rotation delta
    ev_rot = adapter.decode_notification(b"\x02\x00")
    assert ev_rot is not None
    assert ev_rot.kind == Kind.ROTATE
    assert ev_rot.delta == 2

    # Button single click
    ev_click = adapter.decode_notification(b"\x00\x01")
    assert ev_click is not None
    assert ev_click.kind == Kind.CLICK

    # Button hold
    ev_hold = adapter.decode_notification(b"\x00\x03")
    assert ev_hold is not None
    assert ev_hold.kind == Kind.HOLD

