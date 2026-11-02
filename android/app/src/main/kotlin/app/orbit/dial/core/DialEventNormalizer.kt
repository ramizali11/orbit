package app.orbit.dial.core

import kotlin.math.abs

/**
 * Normalized high-level logical dial events.
 */
enum class LogicalDialEventType {
    ROTATE_CW,
    ROTATE_CCW,
    SINGLE_PRESS,
    DOUBLE_PRESS,
    TRIPLE_PRESS,
    LONG_PRESS,
    RAPID_ROTATION,
    CONTINUOUS_ROTATION
}

/**
 * Rich decoded event object for the Action Engine and Live Diagnostics Screen.
 */
data class NormalizedDialEvent(
    val type: LogicalDialEventType,
    val direction: Int,             // +1 (CW), -1 (CCW), 0 (Press/None)
    val rawDelta: Int,              // Original hardware ticks
    val scaledDelta: Int,           // Acceleration-adjusted ticks
    val source: String,             // Device identifier or driver source
    val timestamp: Long,
    val isRapid: Boolean = false,
    val streak: Int = 1
)

/**
 * Normalizes hardware dial inputs into clean, debounced logical events.
 * Handles rate tracking, direction determination, acceleration scaling,
 * and media-volume feedback-loop protection.
 */
class DialEventNormalizer(
    var sensitivity: Float = 1.0f,
    var invertDirection: Boolean = false,
    var enableAcceleration: Boolean = true,
    private val emit: (NormalizedDialEvent) -> Unit
) {
    private var lastEventTime = 0L
    private var lastKind: Kind? = null
    private var lastDirection = 0
    private var currentStreak = 0

    private val spinTracker = SpinTracker()

    companion object {
        const val DEBOUNCE_PRESS_MS = 60L
        const val RAPID_INTERVAL_MS = 380L // CMF rate limit interval
    }

    /**
     * Process an incoming raw DialEvent from any protocol adapter.
     */
    fun process(raw: DialEvent, now: Long = Clock.now()): NormalizedDialEvent? {
        val dt = now - lastEventTime

        // Debounce identical rapid presses
        if (raw.kind != Kind.ROTATE && raw.kind == lastKind && dt < DEBOUNCE_PRESS_MS) {
            return null
        }

        lastEventTime = now
        lastKind = raw.kind

        val normalized = when (raw.kind) {
            Kind.ROTATE -> {
                val baseDir = if (raw.delta > 0) 1 else if (raw.delta < 0) -1 else 0
                val effectiveDir = if (invertDirection) -baseDir else baseDir

                if (effectiveDir == lastDirection && dt < 800) {
                    currentStreak++
                } else {
                    currentStreak = 1
                    lastDirection = effectiveDir
                }

                // Acceleration calculation
                val gain = if (enableAcceleration) {
                    spinTracker.update(raw.delta, now)
                    spinTracker.gain(maxGain = 3.0f)
                } else 1.0f

                val isRapid = dt < RAPID_INTERVAL_MS && currentStreak >= 2
                val magnitude = (abs(raw.delta) * sensitivity * gain).toInt().coerceAtLeast(1)
                val scaledDelta = magnitude * effectiveDir

                val type = if (isRapid) {
                    LogicalDialEventType.RAPID_ROTATION
                } else if (effectiveDir > 0) {
                    LogicalDialEventType.ROTATE_CW
                } else {
                    LogicalDialEventType.ROTATE_CCW
                }

                NormalizedDialEvent(
                    type = type,
                    direction = effectiveDir,
                    rawDelta = raw.delta,
                    scaledDelta = scaledDelta,
                    source = raw.source,
                    timestamp = now,
                    isRapid = isRapid,
                    streak = currentStreak
                )
            }
            Kind.CLICK -> NormalizedDialEvent(
                type = LogicalDialEventType.SINGLE_PRESS,
                direction = 0,
                rawDelta = 0,
                scaledDelta = 0,
                source = raw.source,
                timestamp = now
            )
            Kind.DOUBLE -> NormalizedDialEvent(
                type = LogicalDialEventType.DOUBLE_PRESS,
                direction = 0,
                rawDelta = 0,
                scaledDelta = 0,
                source = raw.source,
                timestamp = now
            )
            Kind.TRIPLE -> NormalizedDialEvent(
                type = LogicalDialEventType.TRIPLE_PRESS,
                direction = 0,
                rawDelta = 0,
                scaledDelta = 0,
                source = raw.source,
                timestamp = now
            )
            Kind.HOLD -> NormalizedDialEvent(
                type = LogicalDialEventType.LONG_PRESS,
                direction = 0,
                rawDelta = 0,
                scaledDelta = 0,
                source = raw.source,
                timestamp = now
            )
            else -> null
        }

        normalized?.let(emit)
        return normalized
    }
}
