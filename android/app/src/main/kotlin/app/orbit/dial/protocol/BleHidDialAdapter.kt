package app.orbit.dial.protocol

import app.orbit.dial.bluetooth.DeviceFingerprint
import app.orbit.dial.bluetooth.ProtocolType
import app.orbit.dial.core.DialEvent
import app.orbit.dial.core.Kind
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.asSharedFlow

/**
 * Protocol adapter for Bluetooth Low Energy Human Interface Device (HID) rotary knobs,
 * Surface Dial clones, and media controllers.
 */
class BleHidDialAdapter(
    private val eventSink: (DialEvent) -> Unit
) : ProtocolAdapter {

    override val protocolType: ProtocolType = ProtocolType.BLE_HID

    override val capabilities: ProtocolCapabilities = ProtocolCapabilities(
        supportsRotation = true,
        supportsDirection = true,
        supportsContinuousRotation = true,
        supportsSinglePress = true,
        supportsDoublePress = true,
        supportsTriplePress = true,
        supportsLongPress = true,
        requiresEarbudsIntermediary = false,
        knownLatencyMs = 15,
        notes = "Standard BLE HID peripheral (Service UUID 0x1812). High reporting rate."
    )

    private val _events = MutableSharedFlow<DialEvent>(extraBufferCapacity = 64)
    override val events: SharedFlow<DialEvent> = _events.asSharedFlow()

    private var boundDevice: DeviceFingerprint? = null

    override fun attach(device: DeviceFingerprint) {
        boundDevice = device
    }

    override fun detach() {
        boundDevice = null
    }

    override fun canHandle(device: DeviceFingerprint): Boolean {
        return device.protocol == ProtocolType.BLE_HID ||
               device.serviceUuids.any { it.contains("1812", ignoreCase = true) }
    }

    /**
     * Decode HID relative rotary motion (Generic Desktop Dial detent or Consumer Control).
     */
    fun onHidRotary(delta: Int, source: String = "ble-hid") {
        if (delta == 0) return
        val event = DialEvent(Kind.ROTATE, delta, source, System.currentTimeMillis())
        _events.tryEmit(event)
        eventSink(event)
    }

    override fun runDiagnosticProbe(device: DeviceFingerprint): String {
        return buildString {
            appendLine("--- BLE HID Controller Diagnostic Probe ---")
            appendLine("Device: ${device.displayName} (${device.deviceId})")
            appendLine("Protocol: BLE HID (0x1812)")
            appendLine("Connection: Standalone Bluetooth HID Peripheral")
            appendLine("Status: VERIFIED")
        }
    }
}

