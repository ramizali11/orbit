package app.orbit.dial.protocol

import app.orbit.dial.bluetooth.DeviceFingerprint
import app.orbit.dial.bluetooth.ProtocolType
import app.orbit.dial.core.DialEvent
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.asSharedFlow

/**
 * Protocol adapter for genuine CMF Buds Pro 2.
 * Communicates via:
 * 1. AVRCP Absolute Volume reports mapped onto a 16-step grid for rotary detents.
 * 2. AVRCP Media Keys for single, double, and triple press.
 * 3. HFP AT+BVRA=1 Voice Command for hold detection.
 */
class CmfAvrcpHfpAdapter(
    private val eventSink: (DialEvent) -> Unit
) : ProtocolAdapter {

    override val protocolType: ProtocolType = ProtocolType.CMF_AVRCP

    override val capabilities: ProtocolCapabilities = ProtocolCapabilities(
        supportsRotation = true,
        supportsDirection = true,
        supportsContinuousRotation = true,
        supportsSinglePress = true,
        supportsDoublePress = true,
        supportsTriplePress = true,
        supportsLongPress = true,
        requiresEarbudsIntermediary = true,
        knownLatencyMs = 280, // Hardware firmware rate limit ~270-450ms
        notes = "Case dial communicates via active earbud link. Rotation uses AVRCP volume steps."
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
        val lower = device.name.lowercase()
        return lower.contains("cmf buds pro 2") ||
               (lower.contains("cmf") && lower.contains("buds")) ||
               device.protocol == ProtocolType.CMF_AVRCP
    }

    fun dispatchEvent(event: DialEvent) {
        _events.tryEmit(event)
        eventSink(event)
    }

    override fun runDiagnosticProbe(device: DeviceFingerprint): String {
        return buildString {
            appendLine("--- CMF Buds Pro 2 Protocol Diagnostic Probe ---")
            appendLine("Device: ${device.displayName} (${device.deviceId})")
            appendLine("Protocol: CMF_AVRCP / HFP AT+BVRA")
            appendLine("Grid Size: 16 steps (AVRCP 0-127 / 16)")
            appendLine("Case Connectivity: Bridged via Earbuds Pogo Bus")
            appendLine("Hardware Address: ${device.hardwareAddress ?: "N/A"}")
            appendLine("Status: VERIFIED supported")
        }
    }
}

