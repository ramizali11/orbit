package app.orbit.dial

import android.Manifest
import android.os.Build
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import app.orbit.dial.bluetooth.*

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DeviceManagerScreen(
    onBack: () -> Unit
) {
    val context = LocalContext.current
    val registry = remember { DeviceRegistry.getInstance(context) }
    val savedDevices by registry.devices.collectAsState()
    val activeDeviceId by registry.activeDeviceId.collectAsState()

    val discoveryManager = remember { Orbit.discoveryManager ?: BluetoothDiscoveryManager(context).also { Orbit.discoveryManager = it } }
    val discoveredDevices by discoveryManager.discoveredDevices.collectAsState()
    val isScanning by discoveryManager.isScanning.collectAsState()

    var renamingDevice by remember { mutableStateOf<DeviceFingerprint?>(null) }
    var renameText by remember { mutableStateOf("") }
    var diagnosticDevice by remember { mutableStateOf<DeviceFingerprint?>(null) }

    // Bluetooth permission launcher
    val permLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { permissions ->
        val granted = permissions.values.all { it }
        if (granted) discoveryManager.startDiscovery()
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Device Manager") },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(painterResource(R.drawable.ic_arrow_left), contentDescription = "Back")
                    }
                },
                actions = {
                    if (isScanning) {
                        CircularProgressIndicator(
                            modifier = Modifier.size(24.dp).padding(end = 12.dp),
                            color = MaterialTheme.colorScheme.primary,
                            strokeWidth = 2.dp
                        )
                    }
                    IconButton(onClick = {
                        if (isScanning) {
                            discoveryManager.stopDiscovery()
                        } else {
                            if (discoveryManager.hasPermissions()) {
                                discoveryManager.startDiscovery()
                            } else {
                                val req = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                                    arrayOf(Manifest.permission.BLUETOOTH_SCAN, Manifest.permission.BLUETOOTH_CONNECT)
                                } else {
                                    arrayOf(Manifest.permission.BLUETOOTH, Manifest.permission.ACCESS_FINE_LOCATION)
                                }
                                permLauncher.launch(req)
                            }
                        }
                    }) {
                        Icon(
                            painterResource(if (isScanning) R.drawable.ic_x else R.drawable.ic_search),
                            contentDescription = if (isScanning) "Stop Scan" else "Scan"
                        )
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.surface
                )
            )
        }
    ) { padding ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(horizontal = 16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            item {
                Text(
                    "Manage your Bluetooth rotary dial devices. Tap a device to set it as active, or scan for nearby buds and knobs.",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    modifier = Modifier.padding(vertical = 8.dp)
                )
            }

            // Saved / Paired Devices
            item {
                Text(
                    "Saved Devices (${savedDevices.size})",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold,
                    color = MaterialTheme.colorScheme.primary
                )
            }

            if (savedDevices.isEmpty()) {
                item {
                    Surface(
                        color = MaterialTheme.colorScheme.surfaceContainer,
                        shape = RoundedCornerShape(12.dp),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Text(
                            "No devices saved yet. Tap the search icon to scan.",
                            modifier = Modifier.padding(16.dp),
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }
            } else {
                items(savedDevices) { dev ->
                    DeviceCard(
                        device = dev,
                        isActive = dev.deviceId == activeDeviceId,
                        onSelect = {
                            registry.setActiveDevice(dev.deviceId)
                            Orbit.endpointManager?.bindDevice(dev)
                        },
                        onRename = {
                            renamingDevice = dev
                            renameText = dev.displayName
                        },
                        onForget = { registry.forgetDevice(dev.deviceId) },
                        onProbe = { diagnosticDevice = dev }
                    )
                }
            }

            // Nearby Discovered Devices
            item {
                Spacer(Modifier.height(8.dp))
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        "Discovered Nearby (${discoveredDevices.size})",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold,
                        color = MaterialTheme.colorScheme.primary
                    )
                    if (isScanning) {
                        Text("Scanning...", style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.tertiary)
                    }
                }
            }

            if (discoveredDevices.isEmpty()) {
                item {
                    Surface(
                        color = MaterialTheme.colorScheme.surfaceContainer,
                        shape = RoundedCornerShape(12.dp),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Text(
                            if (isScanning) "Searching for Bluetooth Classic & BLE devices..."
                            else "No scan in progress. Tap the search icon above.",
                            modifier = Modifier.padding(16.dp),
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }
            } else {
                items(discoveredDevices) { item ->
                    DiscoveredDeviceRow(
                        discovered = item,
                        onAdd = {
                            val saved = registry.registerDevice(item.fingerprint)
                            registry.setActiveDevice(saved.deviceId)
                            Orbit.endpointManager?.bindDevice(saved)
                        }
                    )
                }
            }

            item { Spacer(Modifier.height(32.dp)) }
        }
    }

    // Rename Dialog
    renamingDevice?.let { dev ->
        AlertDialog(
            onDismissRequest = { renamingDevice = null },
            title = { Text("Rename Device") },
            text = {
                OutlinedTextField(
                    value = renameText,
                    onValueChange = { renameText = it },
                    label = { Text("Friendly Name") },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth()
                )
            },
            confirmButton = {
                Button(onClick = {
                    registry.renameDevice(dev.deviceId, renameText)
                    renamingDevice = null
                }) { Text("Save") }
            },
            dismissButton = {
                TextButton(onClick = { renamingDevice = null }) { Text("Cancel") }
            }
        )
    }

    // Diagnostic Probe Dialog
    diagnosticDevice?.let { dev ->
        val detector = remember { app.orbit.dial.protocol.ProtocolDetector {} }
        val adapter = remember(dev) { detector.resolveAdapter(dev) }
        val probe = remember(dev) { adapter.runDiagnosticProbe(dev) }

        AlertDialog(
            onDismissRequest = { diagnosticDevice = null },
            title = { Text("Protocol Diagnostic Probe") },
            text = {
                Text(
                    probe,
                    style = MaterialTheme.typography.bodySmall,
                    fontFamily = androidx.compose.ui.text.font.FontFamily.Monospace
                )
            },
            confirmButton = {
                Button(onClick = { diagnosticDevice = null }) { Text("Done") }
            }
        )
    }
}

@Composable
fun DeviceCard(
    device: DeviceFingerprint,
    isActive: Boolean,
    onSelect: () -> Unit,
    onRename: () -> Unit,
    onForget: () -> Unit,
    onProbe: () -> Unit
) {
    Surface(
        color = if (isActive) MaterialTheme.colorScheme.primaryContainer else MaterialTheme.colorScheme.surfaceContainer,
        shape = RoundedCornerShape(16.dp),
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onSelect)
    ) {
        Column(Modifier.padding(16.dp)) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.SpaceBetween,
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(Modifier.weight(1f)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text(
                            device.displayName,
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = FontWeight.Bold,
                            color = if (isActive) MaterialTheme.colorScheme.onPrimaryContainer else MaterialTheme.colorScheme.onSurface
                        )
                        if (isActive) {
                            Spacer(Modifier.width(8.dp))
                            Surface(
                                color = MaterialTheme.colorScheme.primary,
                                shape = RoundedCornerShape(6.dp)
                            ) {
                                Text(
                                    "ACTIVE",
                                    color = MaterialTheme.colorScheme.onPrimary,
                                    fontSize = 10.sp,
                                    fontWeight = FontWeight.Bold,
                                    modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                                )
                            }
                        }
                    }
                    Text(
                        "${device.protocol.name} • ${device.verifiedStatus.name}",
                        style = MaterialTheme.typography.bodySmall,
                        color = if (isActive) MaterialTheme.colorScheme.onPrimaryContainer.copy(alpha = 0.8f) else MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }

            Spacer(Modifier.height(8.dp))
            Row(
                horizontalArrangement = Arrangement.End,
                modifier = Modifier.fillMaxWidth()
            ) {
                TextButton(onClick = onProbe) { Text("Diagnose", fontSize = 12.sp) }
                TextButton(onClick = onRename) { Text("Rename", fontSize = 12.sp) }
                TextButton(onClick = onForget) { Text("Forget", fontSize = 12.sp, color = MaterialTheme.colorScheme.error) }
            }
        }
    }
}

@Composable
fun DiscoveredDeviceRow(
    discovered: DiscoveredDevice,
    onAdd: () -> Unit
) {
    Surface(
        color = MaterialTheme.colorScheme.surfaceContainerLow,
        shape = RoundedCornerShape(12.dp),
        modifier = Modifier.fillMaxWidth()
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(12.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            Column(Modifier.weight(1f)) {
                Text(
                    discovered.fingerprint.displayName,
                    style = MaterialTheme.typography.bodyLarge,
                    fontWeight = FontWeight.Medium
                )
                Text(
                    "${discovered.fingerprint.protocol.name} • RSSI: ${discovered.rssi} dBm",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
            Button(onClick = onAdd) {
                Text("Pair & Use")
            }
        }
    }
}

