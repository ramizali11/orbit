package app.orbit.dial.protocol

import app.orbit.dial.bluetooth.DeviceFingerprint
import app.orbit.dial.bluetooth.ProtocolType
import app.orbit.dial.core.DialEvent
import app.orbit.dial.core.Kind
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Test

class ProtocolAdapterTest {

    @Test
    fun detectorResolvesCmfAdapter() {
        val events = mutableListOf<DialEvent>()
        val detector = ProtocolDetector { events += it }

        val cmfDevice = DeviceFingerprint(
            deviceId = "CMF:11:22:33",
            name = "CMF Buds Pro 2",
            protocol = ProtocolType.CMF_AVRCP
        )

        val adapter = detector.resolveAdapter(cmfDevice)
        assertTrue(adapter is CmfAvrcpHfpAdapter)
        assertEquals(ProtocolType.CMF_AVRCP, adapter.protocolType)
        assertTrue(adapter.capabilities.requiresEarbudsIntermediary)

        adapter.attach(cmfDevice)
        val probe = adapter.runDiagnosticProbe(cmfDevice)
        assertTrue(probe.contains("16 steps"))
    }

    @Test
    fun detectorResolvesBleHidAdapter() {
        val events = mutableListOf<DialEvent>()
        val detector = ProtocolDetector { events += it }

        val hidDevice = DeviceFingerprint(
            deviceId = "HID:44:55:66",
            name = "Surface Dial Clone",
            serviceUuids = listOf("00001812-0000-1000-8000-00805f9b34fb")
        )

        val adapter = detector.resolveAdapter(hidDevice)
        assertTrue(adapter is BleHidDialAdapter)
        adapter.attach(hidDevice)

        (adapter as BleHidDialAdapter).onHidRotary(2)
        assertEquals(1, events.size)
        assertEquals(Kind.ROTATE, events[0].kind)
        assertEquals(2, events[0].delta)
    }

    @Test
    fun bleGattPayloadDecoding() {
        val events = mutableListOf<DialEvent>()
        val adapter = BleGattDialAdapter { events += it }

        // Test CW rotation (+1) with no buttons
        adapter.decodeGattPayload(byteArrayOf(0x01, 0x00))
        assertEquals(1, events.size)
        assertEquals(Kind.ROTATE, events[0].kind)
        assertEquals(1, events[0].delta)

        // Test CCW rotation (-1) with Single Click (0x01)
        adapter.decodeGattPayload(byteArrayOf((-1).toByte(), 0x01))
        assertEquals(3, events.size)
        assertEquals(Kind.ROTATE, events[1].kind)
        assertEquals(-1, events[1].delta)
        assertEquals(Kind.CLICK, events[2].kind)
    }

    @Test
    fun unknownDeviceSafeFallback() {
        val events = mutableListOf<DialEvent>()
        val detector = ProtocolDetector { events += it }

        val mysteriousDevice = DeviceFingerprint(
            deviceId = "MYSTERY:AA:BB",
            name = "XYZ Random Widget"
        )

        val adapter = detector.resolveAdapter(mysteriousDevice)
        assertTrue(adapter is UnknownDeviceAdapter)
        val probe = adapter.runDiagnosticProbe(mysteriousDevice)
        assertTrue(probe.contains("UNKNOWN DEVICE DIAGNOSTIC PROBE"))
    }
}

