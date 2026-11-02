package app.orbit.dial.protocol

import app.orbit.dial.bluetooth.DeviceFingerprint
import app.orbit.dial.bluetooth.ProtocolType
import app.orbit.dial.bluetooth.VerificationStatus
import app.orbit.dial.core.DialEvent
import kotlinx.coroutines.flow.SharedFlow

/**
 * Declared capabilities of a Bluetooth rotary dial protocol adapter.
 */
data class ProtocolCapabilities(
    val supportsRotation: Boolean = true,
    val supportsDirection: Boolean = true,
    val supportsContinuousRotation: Boolean = true,
    val supportsSinglePress: Boolean = true,
    val supportsDoublePress: Boolean = false,
    val supportsTriplePress: Boolean = false,
    val supportsLongPress: Boolean = false,
    val requiresEarbudsIntermediary: Boolean = false,
    val knownLatencyMs: Int = 50,
    val notes: String = ""
)

/**
 * Universal interface for all Bluetooth rotary dial communication protocols.
 * Supports CMF AVRCP, direct BLE GATT, BLE HID, and future proprietary encoders.
 */
interface ProtocolAdapter {
    val protocolType: ProtocolType
    val capabilities: ProtocolCapabilities

    /**
     * Observable stream of normalized dial events emitted by this adapter.
     */
    val events: SharedFlow<DialEvent>

    /**
     * Attach to a device using its fingerprint and begin listening for incoming dial events.
     */
    fun attach(device: DeviceFingerprint)

    /**
     * Detach from the active device and release resources.
     */
    fun detach()

    /**
     * Check if this adapter can handle the given device.
     */
    fun canHandle(device: DeviceFingerprint): Boolean

    /**
     * Run safe diagnostic probe on device to test connectivity and event reception.
     */
    fun runDiagnosticProbe(device: DeviceFingerprint): String
}

