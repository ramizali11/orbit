package app.orbit.dial.bluetooth

/**
 * Connection state of an individual endpoint.
 */
enum class EndpointConnectionState {
    DISCONNECTED,
    CONNECTING,
    CONNECTED,              // Direct active Bluetooth connection
    BRIDGED,                // Dial accessible indirectly through paired earbuds (e.g. CMF Buds Pro 2)
    NOT_INDEPENDENTLY_ACCESSIBLE // Hardware has no independent radio
}

/**
 * Logical connection endpoint representing either the earbuds or the charging case.
 */
sealed class DeviceEndpoint {
    abstract val id: String
    abstract val name: String
    abstract val state: EndpointConnectionState
    abstract val isDialAccessible: Boolean

    /**
     * Earbuds Endpoint: Responsible for Bluetooth Audio (A2DP), Phone calls (HFP),
     * and forwarding dial events when operating in Bridged topology.
     */
    data class Earbuds(
        override val id: String,
        override val name: String,
        override val state: EndpointConnectionState = EndpointConnectionState.DISCONNECTED,
        val isA2dpConnected: Boolean = false,
        val isHfpConnected: Boolean = false,
        val batteryLevel: Int? = null
    ) : DeviceEndpoint() {
        override val isDialAccessible: Boolean = false
    }

    /**
     * Charging Case Endpoint: Represents the physical rotary dial on the case.
     */
    data class ChargingCase(
        override val id: String,
        override val name: String,
        override val state: EndpointConnectionState = EndpointConnectionState.DISCONNECTED,
        val isIndependentRadio: Boolean = false,
        val caseBatteryLevel: Int? = null,
        val lidOpen: Boolean? = null
    ) : DeviceEndpoint() {
        override val isDialAccessible: Boolean
            get() = state == EndpointConnectionState.CONNECTED || state == EndpointConnectionState.BRIDGED
    }
}

/**
 * Overall device topology determining how dial input travels to the smartphone.
 */
enum class DeviceTopology {
    /**
     * Case dial communicates through the earbuds via local bus / pogo pins,
     * and the earbud forwards events to Android via AVRCP/HFP.
     * (Genuine CMF Buds Pro 2 architecture)
     */
    INDIRECT_BRIDGED,

    /**
     * Case has its own independent Bluetooth Low Energy or Classic radio
     * and connects directly to the phone as a distinct Bluetooth peripheral.
     */
    DIRECT_DUAL_RADIO,

    /**
     * Single standalone dial unit (e.g. Surface Dial clone, Bluetooth knob).
     */
    STANDALONE_DIAL,

    /**
     * Topology not yet determined.
     */
    UNKNOWN
}

/**
 * Combined session representing both endpoints of a dial device.
 */
data class UnifiedDeviceSession(
    val deviceFingerprint: DeviceFingerprint,
    val topology: DeviceTopology,
    val earbudsEndpoint: DeviceEndpoint.Earbuds,
    val caseEndpoint: DeviceEndpoint.ChargingCase
) {
    val isReadyForDialEvents: Boolean
        get() = caseEndpoint.isDialAccessible

    val statusSummary: String
        get() = when {
            isReadyForDialEvents && topology == DeviceTopology.INDIRECT_BRIDGED ->
                "Dial Active (Bridged via ${earbudsEndpoint.name})"
            isReadyForDialEvents && topology == DeviceTopology.DIRECT_DUAL_RADIO ->
                "Dial Active (Direct Case Connection)"
            earbudsEndpoint.state == EndpointConnectionState.CONNECTED ->
                "Earbuds Connected • Case Dial Waiting"
            else ->
                "Disconnected"
        }
}

