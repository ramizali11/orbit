package app.orbit.dial.protocol

import app.orbit.dial.bluetooth.DeviceFingerprint
import app.orbit.dial.bluetooth.ProtocolType
import app.orbit.dial.core.DialEvent

/**
 * Protocol Detector: Evaluates device fingerprints, declared services, and manufacturer
 * signatures to automatically select the most accurate ProtocolAdapter.
 */
class ProtocolDetector(
    private val eventSink: (DialEvent) -> Unit
) {
    val cmfAdapter = CmfAvrcpHfpAdapter(eventSink)
    val bleHidAdapter = BleHidDialAdapter(eventSink)
    val bleGattAdapter = BleGattDialAdapter(eventSink)
    val genericAvrcpAdapter = GenericAvrcpAdapter(eventSink)
    val unknownAdapter = UnknownDeviceAdapter(eventSink)

    val registeredAdapters: List<ProtocolAdapter> = listOf(
        cmfAdapter,
        bleHidAdapter,
        bleGattAdapter,
        genericAvrcpAdapter,
        unknownAdapter
    )

    /**
     * Resolve the optimal protocol adapter for the given device.
     */
    fun resolveAdapter(device: DeviceFingerprint): ProtocolAdapter {
        // 1. Explicit Protocol Type match
        when (device.protocol) {
            ProtocolType.CMF_AVRCP -> return cmfAdapter
            ProtocolType.BLE_HID -> return bleHidAdapter
            ProtocolType.BLE_GATT_DIAL -> return bleGattAdapter
            ProtocolType.GENERIC_AVRCP -> return genericAvrcpAdapter
            ProtocolType.UNKNOWN -> { /* Fall through to heuristic detection */ }
        }

        // 2. Candidate inspection
        for (adapter in registeredAdapters) {
            if (adapter !== unknownAdapter && adapter.canHandle(device)) {
                return adapter
            }
        }

        return unknownAdapter
    }
}
