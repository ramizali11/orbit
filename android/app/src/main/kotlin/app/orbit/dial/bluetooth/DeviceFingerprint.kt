package app.orbit.dial.bluetooth

import org.json.JSONArray
import org.json.JSONObject

/**
 * Verification state of a Bluetooth dial device.
 * Strict rule: Never mark an untested device as VERIFIED.
 */
enum class VerificationStatus {
    VERIFIED,           // Physical dial and actions verified on real hardware
    PARTIALLY_VERIFIED, // Connection works, some events/actions untested
    DISCOVERED,         // Device identified, protocol compatibility in test
    UNSUPPORTED,        // Device confirmed unable to deliver dial input
    UNKNOWN             // Insufficient information
}

/**
 * Communication protocol family used by a rotary dial device.
 */
enum class ProtocolType {
    CMF_AVRCP,          // CMF Buds Pro 2 AVRCP absolute volume + HFP VR
    BLE_GATT_DIAL,      // Direct BLE GATT encoder notifications
    BLE_HID,            // BLE HID consumer control / rotary knob
    GENERIC_AVRCP,      // 3rd party earbuds using volume step rotation
    UNKNOWN             // Protocol yet to be determined
}

/**
 * Role of a logical device endpoint.
 */
enum class EndpointRole {
    EARBUDS,            // Audio receiver & headset controls
    CHARGING_CASE,      // Rotary dial controller
    STANDALONE_DIAL,    // Unified / independent physical dial
    UNKNOWN
}

/**
 * Robust device fingerprint constructed from all available Bluetooth advertising,
 * profile, and hardware metadata to disambiguate devices with identical names.
 */
data class DeviceFingerprint(
    val deviceId: String,
    val name: String,
    val alias: String? = null,
    val hardwareAddress: String? = null,
    val deviceClass: Int = 0,
    val serviceUuids: List<String> = emptyList(),
    val manufacturerId: Int? = null,
    val manufacturerDataHex: String? = null,
    val isBonded: Boolean = false,
    val protocol: ProtocolType = ProtocolType.UNKNOWN,
    val verifiedStatus: VerificationStatus = VerificationStatus.UNKNOWN,
    val lastSeen: Long = System.currentTimeMillis()
) {
    /** Display name: preferred user alias, falling back to hardware name or placeholder */
    val displayName: String
        get() = alias?.takeIf { it.isNotBlank() } ?: name.takeIf { it.isNotBlank() } ?: "Unknown Bluetooth Device"

    /**
     * Determine similarity with another fingerprint to detect duplicates and clones.
     * Returns a score from 0.0 (completely distinct) to 1.0 (identical device).
     */
    fun matchScore(other: DeviceFingerprint): Float {
        if (!hardwareAddress.isNullOrBlank() && hardwareAddress.equals(other.hardwareAddress, ignoreCase = true)) {
            return 1.0f
        }
        var score = 0.0f
        if (name.equals(other.name, ignoreCase = true)) score += 0.4f
        if (manufacturerId != null && manufacturerId == other.manufacturerId) score += 0.3f
        if (deviceClass != 0 && deviceClass == other.deviceClass) score += 0.15f
        val sharedUuids = serviceUuids.intersect(other.serviceUuids.toSet())
        if (sharedUuids.isNotEmpty()) score += 0.15f
        return score.coerceIn(0.0f, 1.0f)
    }

    fun toJson(): JSONObject = JSONObject().apply {
        put("deviceId", deviceId)
        put("name", name)
        put("alias", alias ?: "")
        put("hardwareAddress", hardwareAddress ?: "")
        put("deviceClass", deviceClass)
        put("serviceUuids", JSONArray(serviceUuids))
        if (manufacturerId != null) put("manufacturerId", manufacturerId)
        put("manufacturerDataHex", manufacturerDataHex ?: "")
        put("isBonded", isBonded)
        put("protocol", protocol.name)
        put("verifiedStatus", verifiedStatus.name)
        put("lastSeen", lastSeen)
    }

    companion object {
        fun fromJson(json: JSONObject): DeviceFingerprint {
            val uuidsArray = json.optJSONArray("serviceUuids")
            val uuids = if (uuidsArray != null) {
                (0 until uuidsArray.length()).map { uuidsArray.getString(it) }
            } else emptyList()

            return DeviceFingerprint(
                deviceId = json.getString("deviceId"),
                name = json.optString("name", "Unknown Device"),
                alias = json.optString("alias").ifBlank { null },
                hardwareAddress = json.optString("hardwareAddress").ifBlank { null },
                deviceClass = json.optInt("deviceClass", 0),
                serviceUuids = uuids,
                manufacturerId = if (json.has("manufacturerId")) json.getInt("manufacturerId") else null,
                manufacturerDataHex = json.optString("manufacturerDataHex").ifBlank { null },
                isBonded = json.optBoolean("isBonded", false),
                protocol = runCatching { ProtocolType.valueOf(json.optString("protocol")) }.getOrDefault(ProtocolType.UNKNOWN),
                verifiedStatus = runCatching { VerificationStatus.valueOf(json.optString("verifiedStatus")) }.getOrDefault(VerificationStatus.UNKNOWN),
                lastSeen = json.optLong("lastSeen", System.currentTimeMillis())
            )
        }

        /**
         * Inspect names and identifiers to estimate initial protocol type and verification status.
         */
        fun inferProtocol(name: String, manufacturerId: Int?, serviceUuids: List<String>): Pair<ProtocolType, VerificationStatus> {
            val lower = name.lowercase()
            return when {
                lower.contains("cmf buds pro 2") -> {
                    ProtocolType.CMF_AVRCP to VerificationStatus.VERIFIED
                }
                lower.contains("cmf") || lower.contains("nothing") -> {
                    ProtocolType.CMF_AVRCP to VerificationStatus.PARTIALLY_VERIFIED
                }
                serviceUuids.any { it.contains("1812", ignoreCase = true) } -> {
                    // Standard HID Service UUID 0x1812
                    ProtocolType.BLE_HID to VerificationStatus.PARTIALLY_VERIFIED
                }
                lower.contains("dial") || lower.contains("knob") || lower.contains("rotary") -> {
                    ProtocolType.BLE_GATT_DIAL to VerificationStatus.DISCOVERED
                }
                else -> {
                    ProtocolType.UNKNOWN to VerificationStatus.UNKNOWN
                }
            }
        }
    }
}

