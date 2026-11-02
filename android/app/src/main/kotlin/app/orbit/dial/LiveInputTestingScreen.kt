package app.orbit.dial

import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.spring
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import app.orbit.dial.core.LiveInputMonitor
import kotlin.math.cos
import kotlin.math.sin

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun LiveInputTestingScreen(
    onBack: () -> Unit
) {
    val inputState by LiveInputMonitor.state.collectAsState()

    // Interactive dial visual rotation angle
    var dialAngle by remember { mutableFloatStateOf(0f) }

    LaunchedEffect(inputState.lastEvent) {
        val ev = inputState.lastEvent ?: return@LaunchedEffect
        if (ev.direction != 0) {
            dialAngle += (ev.scaledDelta * 22.5f) // 16 steps per full 360 rotation (360/16 = 22.5 deg)
        }
    }

    val animatedAngle by animateFloatAsState(
        targetValue = dialAngle,
        animationSpec = spring(stiffness = 300f),
        label = "dialRotation"
    )

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Input Testing & Diagnostics") },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(painterResource(R.drawable.ic_arrow_left), contentDescription = "Back")
                    }
                },
                actions = {
                    TextButton(onClick = { LiveInputMonitor.resetStats() }) {
                        Text("Reset")
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.surface
                )
            )
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(16.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(
                "Rotate or press your physical charging-case dial to test live event reception.",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.padding(bottom = 16.dp)
            )

            // Animated Rotary Dial Visualization
            Box(
                modifier = Modifier
                    .size(200.dp)
                    .padding(8.dp),
                contentAlignment = Alignment.Center
            ) {
                val primaryColor = MaterialTheme.colorScheme.primary
                val outlineColor = MaterialTheme.colorScheme.outlineVariant
                val tertiaryColor = MaterialTheme.colorScheme.tertiary

                Canvas(modifier = Modifier.fillMaxSize()) {
                    val center = Offset(size.width / 2f, size.height / 2f)
                    val radius = size.minDimension / 2f - 12.dp.toPx()

                    // Background ring
                    drawCircle(
                        color = outlineColor,
                        radius = radius,
                        center = center,
                        style = Stroke(width = 8.dp.toPx())
                    )

                    // 16 detent ticks on the dial
                    for (i in 0 until 16) {
                        val angleRad = Math.toRadians((i * 22.5 + animatedAngle).toDouble())
                        val innerRadius = radius - 16.dp.toPx()
                        val start = Offset(
                            (center.x + innerRadius * cos(angleRad)).toFloat(),
                            (center.y + innerRadius * sin(angleRad)).toFloat()
                        )
                        val end = Offset(
                            (center.x + radius * cos(angleRad)).toFloat(),
                            (center.y + radius * sin(angleRad)).toFloat()
                        )
                        drawElevationLine(start, end, if (i == 0) tertiaryColor else primaryColor, if (i == 0) 4.dp.toPx() else 2.dp.toPx())
                    }
                }

                // Center indicator badge
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Text(
                        inputState.rawDeltaDisplay,
                        style = MaterialTheme.typography.headlineMedium,
                        fontWeight = FontWeight.Bold,
                        color = MaterialTheme.colorScheme.primary
                    )
                    Text(
                        "TICKS",
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }

            Spacer(Modifier.height(24.dp))

            // Diagnostic Telemetry Card
            Surface(
                color = MaterialTheme.colorScheme.surfaceContainer,
                shape = RoundedCornerShape(16.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    TelemetryRow("Last Event", inputState.eventTypeDisplay)
                    TelemetryRow("Direction", inputState.rotationDirectionDisplay)
                    TelemetryRow("Device", inputState.deviceName)
                    TelemetryRow("Timestamp", inputState.timestampFormatted)
                    TelemetryRow("Total Turns", "${inputState.totalRotationTicks} ticks")
                    TelemetryRow("Total Presses", "${inputState.totalPresses} presses")
                }
            }

            Spacer(Modifier.height(16.dp))

            // Quick instruction alert
            Surface(
                color = MaterialTheme.colorScheme.surfaceContainerLow,
                shape = RoundedCornerShape(12.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                Row(
                    modifier = Modifier.padding(12.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Icon(
                        painterResource(R.drawable.ic_settings),
                        contentDescription = null,
                        tint = MaterialTheme.colorScheme.primary,
                        modifier = Modifier.size(24.dp)
                    )
                    Spacer(Modifier.width(12.dp))
                    Text(
                        "CMF Buds Pro 2 Note: In Nothing X app, ensure Dial is set to Play/Pause (1x), Next (2x), Prev (3x), Voice Assistant (Hold).",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }
        }
    }
}

private fun androidx.compose.ui.graphics.drawscope.DrawScope.drawElevationLine(
    start: Offset,
    end: Offset,
    color: Color,
    strokeWidth: Float
) {
    drawLine(
        color = color,
        start = start,
        end = end,
        strokeWidth = strokeWidth,
        cap = StrokeCap.Round
    )
}

@Composable
fun TelemetryRow(label: String, value: String) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(
            label,
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
        Text(
            value,
            style = MaterialTheme.typography.bodyMedium,
            fontWeight = FontWeight.SemiBold,
            fontFamily = FontFamily.Monospace,
            color = MaterialTheme.colorScheme.onSurface
        )
    }
}

