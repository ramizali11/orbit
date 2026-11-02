package app.orbit.dial.bluetooth

import android.bluetooth.BluetoothAdapter
import android.bluetooth.BluetoothDevice
import android.bluetooth.BluetoothManager
import android.bluetooth.BluetoothProfile
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.media.AudioDeviceInfo
import android.media.AudioManager
import android.os.Build
import app.orbit.dial.Orbit
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

/**
 * Manages separate Earbuds and Charging Case endpoints.
 * Accurately determines whether the case has its own Bluetooth radio or transmits
 * dial events through the earbuds as an intermediary (Topology A vs Topology B).
 * Never displays a fake independent connection.
 */
class EndpointManager(private val context: Context) {

    private val audioManager = context.getSystemService(Context.AUDIO_SERVICE) as? AudioManager
    private val bluetoothManager = context.getSystemService(Context.BLUETOOTH_SERVICE) as? BluetoothManager
    private val bluetoothAdapter: BluetoothAdapter? = bluetoothManager?.adapter

    private val _session = MutableStateFlow<UnifiedDeviceSession?>(null)
    val session: StateFlow<UnifiedDeviceSession?> = _session.asStateFlow()

    private var a2dpProfile: BluetoothProfile? = null
    private var headsetProfile: BluetoothProfile? = null

    private val profileListener = object : BluetoothProfile.ServiceListener {
        override fun onServiceConnected(profile: Int, proxy: BluetoothProfile) {
            when (profile) {
                BluetoothProfile.A2DP -> a2dpProfile = proxy
                BluetoothProfile.HEADSET -> headsetProfile = proxy
            }
            updateConnectionStates()
        }

        override fun onServiceDisconnected(profile: Int) {
            when (profile) {
                BluetoothProfile.A2DP -> a2dpProfile = null
                BluetoothProfile.HEADSET -> headsetProfile = null
            }
            updateConnectionStates()
        }
    }

    private val connectionReceiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context, intent: Intent) {
            when (intent.action) {
                BluetoothDevice.ACTION_ACL_CONNECTED,
                BluetoothDevice.ACTION_ACL_DISCONNECTED,
                AudioManager.ACTION_AUDIO_BECOMING_NOISY -> {
                    updateConnectionStates()
                }
            }
        }
    }

    private var isStarted = false

    fun start() {
        if (isStarted) return
        isStarted = true

        bluetoothAdapter?.getProfileProxy(context, profileListener, BluetoothProfile.A2DP)
        bluetoothAdapter?.getProfileProxy(context, profileListener, BluetoothProfile.HEADSET)

        val filter = IntentFilter().apply {
            addAction(BluetoothDevice.ACTION_ACL_CONNECTED)
            addAction(BluetoothDevice.ACTION_ACL_DISCONNECTED)
            addAction(AudioManager.ACTION_AUDIO_BECOMING_NOISY)
        }
        context.registerReceiver(connectionReceiver, filter)
        updateConnectionStates()
        Orbit.log("EndpointManager started")
    }

    fun stop() {
        if (!isStarted) return
        isStarted = false

        runCatching { context.unregisterReceiver(connectionReceiver) }
        a2dpProfile?.let { bluetoothAdapter?.closeProfileProxy(BluetoothProfile.A2DP, it) }
        headsetProfile?.let { bluetoothAdapter?.closeProfileProxy(BluetoothProfile.HEADSET, it) }
        a2dpProfile = null
        headsetProfile = null
        Orbit.log("EndpointManager stopped")
    }

    /**
     * Configure the active device to track.
     */
    fun bindDevice(fingerprint: DeviceFingerprint) {
        val topology = determineTopology(fingerprint)
        val initialSession = UnifiedDeviceSession(
            deviceFingerprint = fingerprint,
            topology = topology,
            earbudsEndpoint = DeviceEndpoint.Earbuds(
                id = "${fingerprint.deviceId}_buds",
                name = "${fingerprint.displayName} Earbuds",
                state = EndpointConnectionState.DISCONNECTED
            ),
            caseEndpoint = DeviceEndpoint.ChargingCase(
                id = "${fingerprint.deviceId}_case",
                name = "${fingerprint.displayName} Charging Case Dial",
                state = if (topology == DeviceTopology.INDIRECT_BRIDGED) {
                    EndpointConnectionState.NOT_INDEPENDENTLY_ACCESSIBLE
                } else {
                    EndpointConnectionState.DISCONNECTED
                },
                isIndependentRadio = topology == DeviceTopology.DIRECT_DUAL_RADIO
            )
        )
        _session.value = initialSession
        updateConnectionStates()
    }

    /**
     * Determine device topology based on fingerprint and known hardware realities.
     */
    fun determineTopology(fingerprint: DeviceFingerprint): DeviceTopology {
        return when (fingerprint.protocol) {
            ProtocolType.CMF_AVRCP, ProtocolType.GENERIC_AVRCP -> {
                // Genuine CMF Buds Pro 2 and clones route dial through active earbud
                DeviceTopology.INDIRECT_BRIDGED
            }
            ProtocolType.BLE_GATT_DIAL -> {
                // Independent BLE GATT dial peripheral
                DeviceTopology.DIRECT_DUAL_RADIO
            }
            ProtocolType.BLE_HID -> {
                DeviceTopology.STANDALONE_DIAL
            }
            ProtocolType.UNKNOWN -> {
                if (fingerprint.name.contains("buds", ignoreCase = true)) {
                    DeviceTopology.INDIRECT_BRIDGED
                } else {
                    DeviceTopology.UNKNOWN
                }
            }
        }
    }

    /**
     * Query active audio devices and Bluetooth profiles to update the session.
     */
    @Synchronized
    fun updateConnectionStates() {
        val currentSession = _session.value ?: return
        val isAudioRouteBt = isBluetoothAudioConnected()

        val budsState: EndpointConnectionState
        val caseState: EndpointConnectionState

        when (currentSession.topology) {
            DeviceTopology.INDIRECT_BRIDGED -> {
                budsState = if (isAudioRouteBt) EndpointConnectionState.CONNECTED else EndpointConnectionState.DISCONNECTED
                // When buds are connected in Bridged topology, the case dial becomes accessible through them
                caseState = if (isAudioRouteBt) EndpointConnectionState.BRIDGED else EndpointConnectionState.NOT_INDEPENDENTLY_ACCESSIBLE
            }
            DeviceTopology.DIRECT_DUAL_RADIO -> {
                budsState = if (isAudioRouteBt) EndpointConnectionState.CONNECTED else EndpointConnectionState.DISCONNECTED
                // Case would connect via dedicated BLE GATT
                caseState = EndpointConnectionState.DISCONNECTED // Will update when BLE GATT attaches
            }
            DeviceTopology.STANDALONE_DIAL -> {
                budsState = EndpointConnectionState.NOT_INDEPENDENTLY_ACCESSIBLE
                caseState = if (isAudioRouteBt) EndpointConnectionState.CONNECTED else EndpointConnectionState.DISCONNECTED
            }
            DeviceTopology.UNKNOWN -> {
                budsState = if (isAudioRouteBt) EndpointConnectionState.CONNECTED else EndpointConnectionState.DISCONNECTED
                caseState = EndpointConnectionState.DISCONNECTED
            }
        }

        val updated = currentSession.copy(
            earbudsEndpoint = currentSession.earbudsEndpoint.copy(
                state = budsState,
                isA2dpConnected = isAudioRouteBt
            ),
            caseEndpoint = currentSession.caseEndpoint.copy(
                state = caseState
            )
        )
        _session.value = updated
        Orbit.log("Endpoints updated: Buds=${budsState.name}, Case=${caseState.name} (Topology=${currentSession.topology})")
    }

    private fun isBluetoothAudioConnected(): Boolean {
        if (audioManager == null) return false
        val outputs = audioManager.getDevices(AudioManager.GET_DEVICES_OUTPUTS)
        return outputs.any { dev ->
            dev.type == AudioDeviceInfo.TYPE_BLUETOOTH_A2DP ||
            (Build.VERSION.SDK_INT >= 31 && (dev.type == AudioDeviceInfo.TYPE_BLE_HEADSET || dev.type == AudioDeviceInfo.TYPE_BLE_SPEAKER))
        }
    }
}

