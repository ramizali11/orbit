package app.orbit.dial.bluetooth

import android.Manifest
import android.annotation.SuppressLint
import android.bluetooth.BluetoothAdapter
import android.bluetooth.BluetoothDevice
import android.bluetooth.BluetoothManager
import android.bluetooth.le.ScanCallback
import android.bluetooth.le.ScanResult
import android.bluetooth.le.ScanSettings
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.content.pm.PackageManager
import android.os.Build
import android.os.Handler
import android.os.Looper
import androidx.core.content.ContextCompat
import app.orbit.dial.Orbit
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

/**
 * Discovered device model containing the live RSSI, connection state, and fingerprint.
 */
data class DiscoveredDevice(
    val fingerprint: DeviceFingerprint,
    val rssi: Int = 0,
    val isConnected: Boolean = false,
    val isBonded: Boolean = false,
    val bluetoothDevice: BluetoothDevice? = null
)

/**
 * Universal Bluetooth Discovery Manager:
 * Coordinates Bluetooth Classic and Bluetooth Low Energy (BLE) scanning,
 * extracts device fingerprints, and delivers a unified list of nearby rotary dial candidates.
 */
class BluetoothDiscoveryManager(private val context: Context) {

    private val mainHandler = Handler(Looper.getMainLooper())
    private val bluetoothManager = context.getSystemService(Context.BLUETOOTH_SERVICE) as? BluetoothManager
    private val bluetoothAdapter: BluetoothAdapter? = bluetoothManager?.adapter

    private val _discoveredDevices = MutableStateFlow<List<DiscoveredDevice>>(emptyList())
    val discoveredDevices: StateFlow<List<DiscoveredDevice>> = _discoveredDevices.asStateFlow()

    private val _isScanning = MutableStateFlow(false)
    val isScanning: StateFlow<Boolean> = _isScanning.asStateFlow()

    private val scanTimeoutRunnable = Runnable { stopDiscovery() }

    // BLE Scan callback
    private val bleScanCallback = object : ScanCallback() {
        override fun onScanResult(callbackType: Int, result: ScanResult) {
            handleScanResult(result)
        }

        override fun onBatchScanResults(results: MutableList<ScanResult>) {
            results.forEach { handleScanResult(it) }
        }

        override fun onScanFailed(errorCode: Int) {
            Orbit.log("BLE scan failed with error code $errorCode")
            _isScanning.value = false
        }
    }

    // Classic Bluetooth discovery receiver
    private val classicReceiver = object : BroadcastReceiver() {
        @SuppressLint("MissingPermission")
        override fun onReceive(c: Context, intent: Intent) {
            when (intent.action) {
                BluetoothDevice.ACTION_FOUND -> {
                    val device: BluetoothDevice? = if (Build.VERSION.SDK_INT >= 33) {
                        intent.getParcelableExtra(BluetoothDevice.EXTRA_DEVICE, BluetoothDevice::class.java)
                    } else {
                        @Suppress("DEPRECATION")
                        intent.getParcelableExtra(BluetoothDevice.EXTRA_DEVICE)
                    }
                    val rssi = intent.getShortExtra(BluetoothDevice.EXTRA_RSSI, Short.MIN_VALUE).toInt()
                    device?.let { handleClassicDevice(it, rssi) }
                }
                BluetoothAdapter.ACTION_DISCOVERY_FINISHED -> {
                    Orbit.log("Bluetooth Classic discovery finished")
                }
            }
        }
    }

    private var classicReceiverRegistered = false

    /**
     * Verify whether the required runtime Bluetooth permissions are granted.
     */
    fun hasPermissions(): Boolean {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            ContextCompat.checkSelfPermission(context, Manifest.permission.BLUETOOTH_SCAN) == PackageManager.PERMISSION_GRANTED &&
            ContextCompat.checkSelfPermission(context, Manifest.permission.BLUETOOTH_CONNECT) == PackageManager.PERMISSION_GRANTED
        } else {
            ContextCompat.checkSelfPermission(context, Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED &&
            ContextCompat.checkSelfPermission(context, Manifest.permission.BLUETOOTH) == PackageManager.PERMISSION_GRANTED
        }
    }

    /**
     * Start universal Bluetooth discovery (Bonded enumeration + Classic discovery + BLE scan).
     * Automatically stops after [timeoutMs] to preserve battery life.
     */
    @SuppressLint("MissingPermission")
    fun startDiscovery(timeoutMs: Long = 12000L) {
        if (!hasPermissions()) {
            Orbit.log("Bluetooth discovery requested but permissions are missing")
            return
        }

        val adapter = bluetoothAdapter
        if (adapter == null || !adapter.isEnabled) {
            Orbit.log("Bluetooth adapter is not available or disabled")
            return
        }

        stopDiscovery()
        _isScanning.value = true

        // 1. Immediately inspect bonded/paired devices
        refreshBondedDevices()

        // 2. Start BLE scanning
        runCatching {
            val scanner = adapter.bluetoothLeScanner
            if (scanner != null) {
                val settings = ScanSettings.Builder()
                    .setScanMode(ScanSettings.SCAN_MODE_LOW_LATENCY)
                    .build()
                scanner.startScan(null, settings, bleScanCallback)
                Orbit.log("Started BLE scanning")
            }
        }.onFailure { Orbit.log("Failed to start BLE scan: ${it.message}") }

        // 3. Start Classic discovery for audio headsets
        runCatching {
            if (!classicReceiverRegistered) {
                val filter = IntentFilter().apply {
                    addAction(BluetoothDevice.ACTION_FOUND)
                    addAction(BluetoothAdapter.ACTION_DISCOVERY_FINISHED)
                }
                context.registerReceiver(classicReceiver, filter)
                classicReceiverRegistered = true
            }
            if (adapter.isDiscovering) {
                adapter.cancelDiscovery()
            }
            adapter.startDiscovery()
            Orbit.log("Started Bluetooth Classic discovery")
        }.onFailure { Orbit.log("Failed to start Classic discovery: ${it.message}") }

        // Schedule timeout
        mainHandler.removeCallbacks(scanTimeoutRunnable)
        mainHandler.postDelayed(scanTimeoutRunnable, timeoutMs)
    }

    /**
     * Stop all active Bluetooth scanning.
     */
    @SuppressLint("MissingPermission")
    fun stopDiscovery() {
        mainHandler.removeCallbacks(scanTimeoutRunnable)
        _isScanning.value = false

        val adapter = bluetoothAdapter
        if (adapter != null && hasPermissions()) {
            runCatching {
                adapter.bluetoothLeScanner?.stopScan(bleScanCallback)
            }
            runCatching {
                if (adapter.isDiscovering) {
                    adapter.cancelDiscovery()
                }
            }
        }

        if (classicReceiverRegistered) {
            runCatching { context.unregisterReceiver(classicReceiver) }
            classicReceiverRegistered = false
        }
        Orbit.log("Bluetooth discovery stopped")
    }

    /**
     * Load already-paired Bluetooth devices into the discovery flow.
     */
    @SuppressLint("MissingPermission")
    fun refreshBondedDevices() {
        val adapter = bluetoothAdapter
        if (!hasPermissions() || adapter == null) return

        val bonded = runCatching { adapter.bondedDevices }.getOrNull() ?: return
        bonded.forEach { device ->
            val name = device.name ?: "Unknown Paired Device"
            val address = device.address
            val (protocol, verified) = DeviceFingerprint.inferProtocol(name, null, emptyList())
            val fingerprint = DeviceFingerprint(
                deviceId = address ?: name,
                name = name,
                hardwareAddress = address,
                deviceClass = device.bluetoothClass?.deviceClass ?: 0,
                isBonded = true,
                protocol = protocol,
                verifiedStatus = verified
            )
            addOrUpdateDevice(fingerprint, rssi = 0, isConnected = false, isBonded = true, device = device)
        }
    }

    @SuppressLint("MissingPermission")
    private fun handleScanResult(result: ScanResult) {
        val record = result.scanRecord
        val device = result.device ?: return
        val name = record?.deviceName ?: (if (hasPermissions()) device.name else null) ?: "Unknown BLE Device"
        val address = device.address

        // Extract Advertised UUIDs
        val uuids = record?.serviceUuids?.map { it.uuid.toString() } ?: emptyList()

        // Extract Manufacturer Data
        val manufacturerData = record?.manufacturerSpecificData
        var manufacturerId: Int? = null
        var manufacturerHex: String? = null
        if (manufacturerData != null && manufacturerData.size() > 0) {
            manufacturerId = manufacturerData.keyAt(0)
            val bytes = manufacturerData.valueAt(0)
            if (bytes != null) {
                manufacturerHex = bytes.joinToString("") { "%02X".format(it) }
            }
        }

        val (protocol, verified) = DeviceFingerprint.inferProtocol(name, manufacturerId, uuids)
        val fingerprint = DeviceFingerprint(
            deviceId = address ?: name,
            name = name,
            hardwareAddress = address,
            deviceClass = if (hasPermissions()) device.bluetoothClass?.deviceClass ?: 0 else 0,
            serviceUuids = uuids,
            manufacturerId = manufacturerId,
            manufacturerDataHex = manufacturerHex,
            isBonded = if (hasPermissions()) device.bondState == BluetoothDevice.BOND_BONDED else false,
            protocol = protocol,
            verifiedStatus = verified
        )

        addOrUpdateDevice(fingerprint, rssi = result.rssi, isConnected = false, isBonded = fingerprint.isBonded, device = device)
    }

    @SuppressLint("MissingPermission")
    private fun handleClassicDevice(device: BluetoothDevice, rssi: Int) {
        val name = (if (hasPermissions()) device.name else null) ?: "Unknown Classic Device"
        val address = device.address
        val devClass = if (hasPermissions()) device.bluetoothClass?.deviceClass ?: 0 else 0
        val isBonded = if (hasPermissions()) device.bondState == BluetoothDevice.BOND_BONDED else false

        val (protocol, verified) = DeviceFingerprint.inferProtocol(name, null, emptyList())
        val fingerprint = DeviceFingerprint(
            deviceId = address ?: name,
            name = name,
            hardwareAddress = address,
            deviceClass = devClass,
            isBonded = isBonded,
            protocol = protocol,
            verifiedStatus = verified
        )

        addOrUpdateDevice(fingerprint, rssi = rssi, isConnected = false, isBonded = isBonded, device = device)
    }

    private fun addOrUpdateDevice(
        fingerprint: DeviceFingerprint,
        rssi: Int,
        isConnected: Boolean,
        isBonded: Boolean,
        device: BluetoothDevice?
    ) {
        val current = _discoveredDevices.value.toMutableList()
        val index = current.indexOfFirst { it.fingerprint.deviceId == fingerprint.deviceId }

        if (index >= 0) {
            val existing = current[index]
            val mergedFingerprint = existing.fingerprint.copy(
                name = if (fingerprint.name.isNotBlank()) fingerprint.name else existing.fingerprint.name,
                hardwareAddress = fingerprint.hardwareAddress ?: existing.fingerprint.hardwareAddress,
                serviceUuids = (existing.fingerprint.serviceUuids + fingerprint.serviceUuids).distinct(),
                manufacturerId = fingerprint.manufacturerId ?: existing.fingerprint.manufacturerId,
                manufacturerDataHex = fingerprint.manufacturerDataHex ?: existing.fingerprint.manufacturerDataHex,
                isBonded = isBonded || existing.isBonded,
                lastSeen = System.currentTimeMillis()
            )
            current[index] = existing.copy(
                fingerprint = mergedFingerprint,
                rssi = if (rssi != 0) rssi else existing.rssi,
                isConnected = isConnected || existing.isConnected,
                isBonded = isBonded || existing.isBonded,
                bluetoothDevice = device ?: existing.bluetoothDevice
            )
        } else {
            current.add(
                DiscoveredDevice(
                    fingerprint = fingerprint,
                    rssi = rssi,
                    isConnected = isConnected,
                    isBonded = isBonded,
                    bluetoothDevice = device
                )
            )
        }
        _discoveredDevices.value = current
    }
}
