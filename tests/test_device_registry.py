"""Tests for DeviceFingerprint and DeviceRegistry."""
import pytest
from pathlib import Path

from orbit.core.device_registry import DeviceFingerprint, DeviceRecord, DeviceRegistry


def test_fingerprint_serialization():
    fp = DeviceFingerprint(
        name="CMF Buds Pro 2",
        address="40:ED:98:11:22:33",
        vendor_id=76,
        product_id=1234,
        service_uuids=["00001812-0000-1000-8000-00805F9B34FB"],
        device_class=2360324,
        connection_type="CLASSIC",
    )
    d = fp.to_dict()
    assert d["name"] == "CMF Buds Pro 2"
    assert d["address"] == "40:ED:98:11:22:33"
    assert d["vendor_id"] == 76

    fp2 = DeviceFingerprint.from_dict(d)
    assert fp2.name == fp.name
    assert fp2.address == fp.address
    assert fp2.service_uuids == ["00001812-0000-1000-8000-00805f9b34fb"]


def test_fingerprint_similarity():
    fp1 = DeviceFingerprint(name="CMF Buds Pro 2", address="40:ED:98:11:22:33")
    fp2 = DeviceFingerprint(name="CMF Buds Pro 2", address="40:ed:98:11:22:33")
    assert fp1.similarity(fp2) == 1.0

    # Same vendor and product, randomized address
    fp3 = DeviceFingerprint(name="Buds Pro", vendor_id=100, product_id=200)
    fp4 = DeviceFingerprint(name="Buds Pro", vendor_id=100, product_id=200)
    assert fp3.similarity(fp4) >= 0.80

    # Unrelated
    fp5 = DeviceFingerprint(name="Keyboard", vendor_id=999)
    assert fp1.similarity(fp5) < 0.2


def test_registry_persistence(tmp_path: Path):
    reg_file = tmp_path / "devices.json"
    reg = DeviceRegistry(reg_file)

    fp1 = DeviceFingerprint(name="CMF Buds Pro 2", address="40:ED:98:AA:BB:CC")
    rec1 = reg.register_or_update(fp1)
    assert rec1.id == "40:ED:98:AA:BB:CC"

    reg.set_custom_name("40:ED:98:AA:BB:CC", "My Office Buds")
    reg.set_adapter("40:ED:98:AA:BB:CC", "cmf-avrcp-hfp")
    reg.set_active_device("40:ED:98:AA:BB:CC")

    # Reload from disk
    reg2 = DeviceRegistry(reg_file)
    rec_loaded = reg2.get("40:ED:98:AA:BB:CC")
    assert rec_loaded is not None
    assert rec_loaded.custom_name == "My Office Buds"
    assert rec_loaded.display_name == "My Office Buds"
    assert rec_loaded.adapter_id == "cmf-avrcp-hfp"
    assert reg2.active_device is not None
    assert reg2.active_device.id == "40:ED:98:AA:BB:CC"

