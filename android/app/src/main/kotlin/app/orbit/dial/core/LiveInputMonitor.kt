package app.orbit.dial.core

import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

/**
 * Diagnostic event state for the Live Input Testing Screen and Dashboard telemetry.
 */
data class LiveInputState(
    val lastEvent: NormalizedDialEvent? = null,
    val deviceName: String = "No Device Active",
    val eventTypeDisplay: String = "Waiting for input...",
    val rotationDirectionDisplay: String = "None",
    val timestampFormatted: String = "--:--:--",
    val rawDeltaDisplay: String = "0",
    val totalRotationTicks: Int = 0,
    val totalPresses: Int = 0,
    val connectionStatus: String = "Disconnected"
)

/**
 * Live Input Monitor: tracks and formats all incoming physical rotary events
 * for instantaneous rendering in the UI.
 */
object LiveInputMonitor {

    private val _state = MutableStateFlow(LiveInputState())
    val state: StateFlow<LiveInputState> = _state.asStateFlow()

    private val fmt = java.text.SimpleDateFormat("HH:mm:ss.SSS", java.util.Locale.US)

    val normalizer = DialEventNormalizer { normalized ->
        recordNormalized(normalized)
    }

    fun onRawEvent(raw: DialEvent) {
        normalizer.process(raw)
    }

    private fun recordNormalized(event: NormalizedDialEvent) {
        val current = _state.value
        val dirDisplay = when (event.direction) {
            1 -> "Clockwise (CW)"
            -1 -> "Counterclockwise (CCW)"
            else -> "None (Press)"
        }

        val typeDisplay = when (event.type) {
            LogicalDialEventType.ROTATE_CW -> "Rotate Clockwise"
            LogicalDialEventType.ROTATE_CCW -> "Rotate Counterclockwise"
            LogicalDialEventType.RAPID_ROTATION -> "Rapid Spin"
            LogicalDialEventType.CONTINUOUS_ROTATION -> "Continuous Spin"
            LogicalDialEventType.SINGLE_PRESS -> "Single Press"
            LogicalDialEventType.DOUBLE_PRESS -> "Double Press"
            LogicalDialEventType.TRIPLE_PRESS -> "Triple Press"
            LogicalDialEventType.LONG_PRESS -> "Long Press (Hold)"
        }

        val newTicks = if (event.direction != 0) current.totalRotationTicks + event.rawDelta else current.totalRotationTicks
        val newPresses = if (event.direction == 0) current.totalPresses + 1 else current.totalPresses

        _state.value = current.copy(
            lastEvent = event,
            deviceName = event.source.ifBlank { "Dial Controller" },
            eventTypeDisplay = typeDisplay,
            rotationDirectionDisplay = dirDisplay,
            timestampFormatted = fmt.format(java.util.Date(event.timestamp)),
            rawDeltaDisplay = if (event.rawDelta != 0) "${if (event.rawDelta > 0) "+" else ""}${event.rawDelta}" else "--",
            totalRotationTicks = newTicks,
            totalPresses = newPresses
        )
    }

    fun updateConnectionStatus(status: String) {
        _state.value = _state.value.copy(connectionStatus = status)
    }

    fun resetStats() {
        _state.value = _state.value.copy(
            totalRotationTicks = 0,
            totalPresses = 0,
            eventTypeDisplay = "Stats Reset"
        )
    }
}

