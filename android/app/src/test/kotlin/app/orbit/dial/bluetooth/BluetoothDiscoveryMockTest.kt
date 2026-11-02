package app.orbit.dial.bluetooth

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class BluetoothDiscoveryMockTest {

    @Test
    fun discoveredDeviceDeduplication() {
        val dev1 = DiscoveredDevice(
            fingerprint = DeviceFingerprint(
                deviceId = "AA:BB:CC:DD:EE:01",
                name = "CMF Buds Pro 2",
                hardwareAddress = "AA:BB:CC:DD:EE:01",
                protocol = ProtocolType.CMF_AVRCP,
                verifiedStatus = VerificationStatus.VERIFIED
            ),
            rssi = -65,
            isBonded = true
        )

        // Same hardware address, updated RSSI
        val dev1Updated = DiscoveredDevice(
            fingerprint = dev1.fingerprint.copy(
                serviceUuids = listOf("0000110b-0000-1000-8000-00805f9b34fb")
            ),
            rssi = -55,
            isBonded = true
        )

        val list = mutableListOf(dev1)
        val index = list.indexOfFirst { it.fingerprint.deviceId == dev1Updated.fingerprint.deviceId }
        assertTrue(index >= 0)
        list[index] = dev1Updated

        assertEquals(1, list.size)
        assertEquals(-55, list[0].rssi)
        assertEquals(1, list[0].fingerprint.serviceUuids.size)
    }

    @Test
    fun duplicateNamesTreatedAsSeparateDevicesByAddress() {
        // Two real cases with identical broadcast name "CMF Buds Pro 2"
        val unitA = DiscoveredDevice(
            fingerprint = DeviceFingerprint(
                deviceId = "11:22:33:44:55:AA",
                name = "CMF Buds Pro 2",
                hardwareAddress = "11:22:33:44:55:AA"
            ),
            rssi = -70
        )

        val unitB = DiscoveredDevice(
            fingerprint = DeviceFingerprint(
                deviceId = "11:22:33:44:55:BB",
                name = "CMF Buds Pro 2",
                hardwareAddress = "11:22:33:44:55:BB"
            ),
            rssi = -82
        )

        val map = mapOf(
            unitA.fingerprint.deviceId to unitA,
            unitB.fingerprint.deviceId to unitB
        )

        assertEquals(2, map.size)
        assertTrue(map.containsKey("11:22:33:44:55:AA"))
        assertTrue(map.containsKey("11:22:33:44:55:BB"))
    }
}

