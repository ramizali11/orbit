package app.orbit.dial.bluetooth

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class DeviceEndpointTest {

    @Test
    fun bridgedTopologyAccessibility() {
        val fingerprint = DeviceFingerprint(
            deviceId = "CMF:01:02:03",
            name = "CMF Buds Pro 2",
            protocol = ProtocolType.CMF_AVRCP
        )

        val session = UnifiedDeviceSession(
            deviceFingerprint = fingerprint,
            topology = DeviceTopology.INDIRECT_BRIDGED,
            earbudsEndpoint = DeviceEndpoint.Earbuds(
                id = "cmf_buds",
                name = "CMF Buds",
                state = EndpointConnectionState.CONNECTED
            ),
            caseEndpoint = DeviceEndpoint.ChargingCase(
                id = "cmf_case",
                name = "CMF Case Dial",
                state = EndpointConnectionState.BRIDGED,
                isIndependentRadio = false
            )
        )

        assertTrue(session.isReadyForDialEvents)
        assertTrue(session.caseEndpoint.isDialAccessible)
        assertEquals("Dial Active (Bridged via CMF Buds)", session.statusSummary)
    }

    @Test
    fun disconnectedBudsBridgedDialNotAccessible() {
        val fingerprint = DeviceFingerprint(
            deviceId = "CMF:01:02:03",
            name = "CMF Buds Pro 2",
            protocol = ProtocolType.CMF_AVRCP
        )

        val session = UnifiedDeviceSession(
            deviceFingerprint = fingerprint,
            topology = DeviceTopology.INDIRECT_BRIDGED,
            earbudsEndpoint = DeviceEndpoint.Earbuds(
                id = "cmf_buds",
                name = "CMF Buds",
                state = EndpointConnectionState.DISCONNECTED
            ),
            caseEndpoint = DeviceEndpoint.ChargingCase(
                id = "cmf_case",
                name = "CMF Case Dial",
                state = EndpointConnectionState.NOT_INDEPENDENTLY_ACCESSIBLE,
                isIndependentRadio = false
            )
        )

        assertFalse(session.isReadyForDialEvents)
        assertFalse(session.caseEndpoint.isDialAccessible)
        assertEquals("Disconnected", session.statusSummary)
    }

    @Test
    fun directDualRadioAccessibility() {
        val fingerprint = DeviceFingerprint(
            deviceId = "DIAL:99:88:77",
            name = "Custom Rotary Case",
            protocol = ProtocolType.BLE_GATT_DIAL
        )

        val session = UnifiedDeviceSession(
            deviceFingerprint = fingerprint,
            topology = DeviceTopology.DIRECT_DUAL_RADIO,
            earbudsEndpoint = DeviceEndpoint.Earbuds(
                id = "custom_buds",
                name = "Custom Buds",
                state = EndpointConnectionState.DISCONNECTED
            ),
            caseEndpoint = DeviceEndpoint.ChargingCase(
                id = "custom_case",
                name = "Custom Case",
                state = EndpointConnectionState.CONNECTED,
                isIndependentRadio = true
            )
        )

        // Case is direct BLE GATT, so dial is accessible even if earbuds are disconnected!
        assertTrue(session.isReadyForDialEvents)
        assertTrue(session.caseEndpoint.isDialAccessible)
        assertEquals("Dial Active (Direct Case Connection)", session.statusSummary)
    }
}

