package app.orbit.dial.protocol

import app.orbit.dial.bluetooth.DeviceFingerprint
import app.orbit.dial.bluetooth.ProtocolType
import app.orbit.dial.core.DialEvent
import app.orbit.dial.core.Kind
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.asSharedFlow

/**
 * Protocol adapter for direct BLE GATT rotary encoders.
 * Listens to characteristic notifications reporting rotary steps (+1/-1) and button events.
 */
class BleGattDialAdapter(
    private val eventSink: (DialEvent) -> Unit
) : ProtocolAdapter {

    override val protocolType: ProtocolType = ProtocolType.BLE_GATT_DIAL

    override val capabilities: ProtocolCapabilities = ProtocolCapabilities(
        supportsRotation = true,
        supportsDirection = true,
        supportsContinuousRotation = true,
        supportsSinglePress = true,
        supportsDoublePress = true,
        supportsTriplePress = false,
        supportsLongPress = true,
        requiresEarbudsIntermediary = false,
        knownLatencyMs = 25,
        notes = "Direct BLE GATT notification stream. Independent case radio or standalone knob."
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
        return device.protocol == ProtocolType.BLE_GATT_DIAL ||
               device.name.lowercase().let { it.contains("dial") || it.contains("knob") || it.contains("encoder") }
    }

    /**
     * Decode a raw GATT characteristic notification payload into a normalized DialEvent.
     */
    fun decodeGattPayload(payload: ByteArray, source: String = "ble-gatt") {
        if (payload.isEmpty()) return
        // Common rotary GATT payload format:
        // Byte 0: Signed delta (-128 to 127), e.g. +1 (CW), -1 (CCW)
        // Byte 1: Button state flags (0x01 = Pressed, 0x02 = Long Press)
        val delta = payload[0].toInt()
        val now = System.currentTimeMillis()

        if (delta != 0) {
            val event = DialEvent(Kind.ROTATE, delta, source, now)
            _events.tryEmit(event)
            eventSink(event)
        }

        if (payload.size > 1) {
            val flags = payload[1].toInt()
            if (flags and 0x01 != 0) {
                val event = DialEvent(Kind.CLICK, 0, source, now)
                _events.tryEmit(event)
                eventSink(event)
            }
            if (flags and 0x02 != 0) {
                val event = DialEvent(Kind.HOLD, 0, source, now)
                _events.tryEmit(event)
                eventSink(event)
            }
        }
    }

    override fun runDiagnosticProbe(device: DeviceFingerprint): String {
        return buildString {
            appendLine("--- BLE GATT Dial Diagnostic Probe ---")
            appendLine("Device: ${device.displayName} (${device.deviceId})")
            appendLine("Protocol: BLE GATT Characteristic Notifications")
            appendLine("Advertised Services: ${device.serviceUuids.joinToString(", ")}")
            appendLine("Status: DISCOVERED")
        }
    }
}

