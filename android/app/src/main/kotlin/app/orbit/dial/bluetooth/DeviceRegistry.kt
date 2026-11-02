package app.orbit.dial.bluetooth

import android.content.Context
import android.content.SharedPreferences
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import org.json.JSONArray
import org.json.JSONObject

/**
 * Persistent registry for discovered, paired, and user-configured rotary dial devices.
 * Handles deduplication, custom user aliases, and protocol settings.
 */
class DeviceRegistry private constructor(private val context: Context) {

    private val prefs: SharedPreferences = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
    private val _devices = MutableStateFlow<List<DeviceFingerprint>>(emptyList())
    val devices: StateFlow<List<DeviceFingerprint>> = _devices.asStateFlow()

    private val _activeDeviceId = MutableStateFlow<String?>(null)
    val activeDeviceId: StateFlow<String?> = _activeDeviceId.asStateFlow()

    init {
        loadFromPrefs()
    }

    @Synchronized
    private fun loadFromPrefs() {
        val raw = prefs.getString(KEY_DEVICES, null)
        val loaded = if (!raw.isNullOrBlank()) {
            runCatching {
                val array = JSONArray(raw)
                (0 until array.length()).map { DeviceFingerprint.fromJson(array.getJSONObject(it)) }
            }.getOrDefault(emptyList())
        } else {
            emptyList()
        }
        _devices.value = loaded
        _activeDeviceId.value = prefs.getString(KEY_ACTIVE_DEVICE_ID, null)
    }

    @Synchronized
    private fun saveToPrefs() {
        val array = JSONArray()
        _devices.value.forEach { array.put(it.toJson()) }
        prefs.edit()
            .putString(KEY_DEVICES, array.toString())
            .putString(KEY_ACTIVE_DEVICE_ID, _activeDeviceId.value)
            .apply()
    }

    /**
     * Register or update a device fingerprint.
     * Merges with existing record if deviceId matches, updating lastSeen and metadata.
     */
    @Synchronized
    fun registerDevice(fingerprint: DeviceFingerprint): DeviceFingerprint {
        val currentList = _devices.value.toMutableList()
        val index = currentList.indexOfFirst { it.deviceId == fingerprint.deviceId }

        val updated = if (index >= 0) {
            val existing = currentList[index]
            // Preserve user-defined alias if new fingerprint has none
            val mergedAlias = fingerprint.alias ?: existing.alias
            // Preserve higher verification status
            val mergedStatus = if (existing.verifiedStatus == VerificationStatus.VERIFIED) {
                VerificationStatus.VERIFIED
            } else {
                fingerprint.verifiedStatus
            }
            existing.copy(
                name = if (fingerprint.name.isNotBlank()) fingerprint.name else existing.name,
                alias = mergedAlias,
                hardwareAddress = fingerprint.hardwareAddress ?: existing.hardwareAddress,
                deviceClass = if (fingerprint.deviceClass != 0) fingerprint.deviceClass else existing.deviceClass,
                serviceUuids = (existing.serviceUuids + fingerprint.serviceUuids).distinct(),
                manufacturerId = fingerprint.manufacturerId ?: existing.manufacturerId,
                manufacturerDataHex = fingerprint.manufacturerDataHex ?: existing.manufacturerDataHex,
                isBonded = fingerprint.isBonded || existing.isBonded,
                protocol = if (fingerprint.protocol != ProtocolType.UNKNOWN) fingerprint.protocol else existing.protocol,
                verifiedStatus = mergedStatus,
                lastSeen = System.currentTimeMillis()
            ).also { currentList[index] = it }
        } else {
            currentList.add(fingerprint)
            fingerprint
        }

        _devices.value = currentList
        if (_activeDeviceId.value == null) {
            _activeDeviceId.value = updated.deviceId
        }
        saveToPrefs()
        return updated
    }

    /**
     * User-facing rename for a device.
     */
    @Synchronized
    fun renameDevice(deviceId: String, newAlias: String) {
        val currentList = _devices.value.toMutableList()
        val index = currentList.indexOfFirst { it.deviceId == deviceId }
        if (index >= 0) {
            val existing = currentList[index]
            currentList[index] = existing.copy(alias = newAlias.trim().ifEmpty { null })
            _devices.value = currentList
            saveToPrefs()
        }
    }

    /**
     * Remove a device from the registry.
     */
    @Synchronized
    fun forgetDevice(deviceId: String) {
        val currentList = _devices.value.toMutableList()
        currentList.removeAll { it.deviceId == deviceId }
        _devices.value = currentList
        if (_activeDeviceId.value == deviceId) {
            _activeDeviceId.value = currentList.firstOrNull()?.deviceId
        }
        saveToPrefs()
    }

    /**
     * Select active device.
     */
    @Synchronized
    fun setActiveDevice(deviceId: String) {
        if (_devices.value.any { it.deviceId == deviceId }) {
            _activeDeviceId.value = deviceId
            saveToPrefs()
        }
    }

    fun getDevice(deviceId: String): DeviceFingerprint? {
        return _devices.value.firstOrNull { it.deviceId == deviceId }
    }

    fun getActiveDevice(): DeviceFingerprint? {
        val id = _activeDeviceId.value ?: return null
        return getDevice(id)
    }

    companion object {
        private const val PREFS_NAME = "orbit_bluetooth_registry"
        private const val KEY_DEVICES = "saved_devices"
        private const val KEY_ACTIVE_DEVICE_ID = "active_device_id"

        @Volatile
        private var instance: DeviceRegistry? = null

        fun getInstance(context: Context): DeviceRegistry {
            return instance ?: synchronized(this) {
                instance ?: DeviceRegistry(context.applicationContext).also { instance = it }
            }
        }
    }
}

