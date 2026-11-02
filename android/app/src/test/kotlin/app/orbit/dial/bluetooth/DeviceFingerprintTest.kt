package app.orbit.dial.bluetooth

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Test

class DeviceFingerprintTest {

    @Test
    fun fingerprintSerializationRoundtrip() {
        val original = DeviceFingerprint(
            deviceId = "AA:BB:CC:DD:EE:FF",
            name = "CMF Buds Pro 2",
            alias = "My Dial Buds",
            hardwareAddress = "AA:BB:CC:DD:EE:FF",
            deviceClass = 0x040404,
            serviceUuids = listOf("0000110b-0000-1000-8000-00805f9b34fb"),
            manufacturerId = 0x0B72,
            manufacturerDataHex = "01020304",
            isBonded = true,
            protocol = ProtocolType.CMF_AVRCP,
            verifiedStatus = VerificationStatus.VERIFIED,
            lastSeen = 1700000000000L
        )

        val json = original.toJson()
        val parsed = DeviceFingerprint.fromJson(json)

        assertEquals(original.deviceId, parsed.deviceId)
        assertEquals(original.name, parsed.name)
        assertEquals(original.alias, parsed.alias)
        assertEquals(original.displayName, "My Dial Buds")
        assertEquals(original.hardwareAddress, parsed.hardwareAddress)
        assertEquals(original.deviceClass, parsed.deviceClass)
        assertEquals(original.serviceUuids, parsed.serviceUuids)
        assertEquals(original.manufacturerId, parsed.manufacturerId)
        assertEquals(original.manufacturerDataHex, parsed.manufacturerDataHex)
        assertEquals(original.isBonded, parsed.isBonded)
        assertEquals(original.protocol, parsed.protocol)
        assertEquals(original.verifiedStatus, parsed.verifiedStatus)
        assertEquals(original.lastSeen, parsed.lastSeen)
    }

    @Test
    fun duplicateDetectionWithIdenticalNamesDifferentAddresses() {
        val device1 = DeviceFingerprint(
            deviceId = "11:22:33:44:55:66",
            name = "CMF Buds Pro 2",
            hardwareAddress = "11:22:33:44:55:66",
            manufacturerId = 0x0B72
        )

        val device2 = DeviceFingerprint(
            deviceId = "99:88:77:66:55:44",
            name = "CMF Buds Pro 2",
            hardwareAddress = "99:88:77:66:55:44",
            manufacturerId = 0x0B72
        )

        // Same name and manufacturer, but different MAC addresses
        assertFalse(device1.deviceId == device2.deviceId)
        val score = device1.matchScore(device2)
        assertTrue(score >= 0.7f) // High similarity due to same name & manufacturer ID
        assertTrue(score < 1.0f)  // But not an identical device
    }

    @Test
    fun inferProtocolCMFBudsPro2() {
        val (proto, status) = DeviceFingerprint.inferProtocol("CMF Buds Pro 2", null, emptyList())
        assertEquals(ProtocolType.CMF_AVRCP, proto)
        assertEquals(VerificationStatus.VERIFIED, status)
    }

    @Test
    fun inferProtocolBleHid() {
        val (proto, status) = DeviceFingerprint.inferProtocol("Rotary Knob", null, listOf("00001812-0000-1000-8000-00805f9b34fb"))
        assertEquals(ProtocolType.BLE_HID, proto)
        assertEquals(VerificationStatus.PARTIALLY_VERIFIED, status)
    }

    @Test
    fun inferProtocolUnknown() {
        val (proto, status) = DeviceFingerprint.inferProtocol("Random Speaker", null, emptyList())
        assertEquals(ProtocolType.UNKNOWN, proto)
        assertEquals(VerificationStatus.UNKNOWN, status)
    }
}

