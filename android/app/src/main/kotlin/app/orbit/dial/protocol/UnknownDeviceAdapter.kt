package app.orbit.dial.protocol

import app.orbit.dial.bluetooth.DeviceFingerprint
import app.orbit.dial.bluetooth.ProtocolType
import app.orbit.dial.core.DialEvent
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.asSharedFlow

/**
 * Diagnostic and safe-testing adapter for unidentified or newly discovered devices.
 * Captures raw GATT packets, Bluetooth broadcasts, or AVRCP events without fabricating support.
 */
class UnknownDeviceAdapter(
    private val eventSink: (DialEvent) -> Unit
) : ProtocolAdapter {

    override val protocolType: ProtocolType = ProtocolType.UNKNOWN

    override val capabilities: ProtocolCapabilities = ProtocolCapabilities(
        supportsRotation = false,
        supportsDirection = false,
        supportsContinuousRotation = false,
        supportsSinglePress = false,
        supportsDoublePress = false,
        supportsTriplePress = false,
        supportsLongPress = false,
        requiresEarbudsIntermediary = false,
        knownLatencyMs = 0,
        notes = "Unknown device under diagnostic investigation. Safe testing mode active."
    )

    private val _events = MutableSharedFlow<DialEvent>(extraBufferCapacity = 64)
    override val events: SharedFlow<DialEvent> = _events.asSharedFlow()

    private var boundDevice: DeviceFingerprint? = null
    private val diagnosticLog = mutableListOf<String>()

    override fun attach(device: DeviceFingerprint) {
        boundDevice = device
        diagnosticLog.clear()
        diagnosticLog.add("Attached to unknown device: ${device.displayName} (${device.deviceId})")
    }

    override fun detach() {
        boundDevice = null
    }

    override fun canHandle(device: DeviceFingerprint): Boolean = true

    fun recordRawPacket(source: String, data: ByteArray) {
        val hex = data.joinToString("") { "%02X".format(it) }
        diagnosticLog.add("[$source] Raw: $hex (${data.size} bytes)")
    }

    override fun runDiagnosticProbe(device: DeviceFingerprint): String {
        return buildString {
            appendLine("=== UNKNOWN DEVICE DIAGNOSTIC PROBE ===")
            appendLine("Device Name: ${device.name}")
            appendLine("Hardware Address: ${device.hardwareAddress ?: "Hidden"}")
            appendLine("Bluetooth Class: 0x${device.deviceClass.toString(16)}")
            appendLine("Manufacturer ID: ${device.manufacturerId?.let { "0x${it.toString(16)}" } ?: "None"}")
            appendLine("Manufacturer Data: ${device.manufacturerDataHex ?: "None"}")
            appendLine("Service UUIDs (${device.serviceUuids.size}):")
            device.serviceUuids.forEach { appendLine("  - $it") }
            appendLine("--- Event Stream History ---")
            if (diagnosticLog.isEmpty()) {
                appendLine("No events received yet. Rotate or press the physical dial to test.")
            } else {
                diagnosticLog.takeLast(10).forEach { appendLine(it) }
            }
        }
    }
}

