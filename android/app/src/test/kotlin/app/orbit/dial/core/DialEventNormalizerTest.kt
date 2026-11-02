package app.orbit.dial.core

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

class DialEventNormalizerTest {

    private var now = 10_000L
    private val normalized = mutableListOf<NormalizedDialEvent>()
    private lateinit var normalizer: DialEventNormalizer

    @Before
    fun setup() {
        Clock.now = { now }
        normalized.clear()
        normalizer = DialEventNormalizer { normalized += it }
    }

    @Test
    fun rotateClockwiseNormalization() {
        val raw = DialEvent(Kind.ROTATE, delta = 1, source = "cmf-dial", t = now)
        val event = normalizer.process(raw, now)

        assertNotNull(event)
        assertEquals(LogicalDialEventType.ROTATE_CW, event?.type)
        assertEquals(1, event?.direction)
        assertEquals(1, event?.rawDelta)
        assertEquals(1, event?.scaledDelta)
    }

    @Test
    fun rotateCounterclockwiseNormalization() {
        val raw = DialEvent(Kind.ROTATE, delta = -1, source = "cmf-dial", t = now)
        val event = normalizer.process(raw, now)

        assertNotNull(event)
        assertEquals(LogicalDialEventType.ROTATE_CCW, event?.type)
        assertEquals(-1, event?.direction)
        assertEquals(-1, event?.rawDelta)
        assertEquals(-1, event?.scaledDelta)
    }

    @Test
    fun invertDirectionSetting() {
        normalizer.invertDirection = true
        val raw = DialEvent(Kind.ROTATE, delta = 1, source = "cmf-dial", t = now)
        val event = normalizer.process(raw, now)

        assertNotNull(event)
        assertEquals(LogicalDialEventType.ROTATE_CCW, event?.type)
        assertEquals(-1, event?.direction)
    }

    @Test
    fun debounceDuplicatePress() {
        val click1 = DialEvent(Kind.CLICK, 0, "cmf", now)
        assertNotNull(normalizer.process(click1, now))

        // Same press within 30ms: must be debounced
        now += 30
        val click2 = DialEvent(Kind.CLICK, 0, "cmf", now)
        assertNull(normalizer.process(click2, now))

        // Press after debounce gap: must be delivered
        now += 100
        val click3 = DialEvent(Kind.CLICK, 0, "cmf", now)
        assertNotNull(normalizer.process(click3, now))
    }

    @Test
    fun rapidRotationDetection() {
        // First tick
        normalizer.process(DialEvent(Kind.ROTATE, 1, "cmf", now), now)

        // Rapid tick within 200ms
        now += 200
        val second = normalizer.process(DialEvent(Kind.ROTATE, 1, "cmf", now), now)

        assertNotNull(second)
        assertTrue(second!!.isRapid)
        assertEquals(LogicalDialEventType.RAPID_ROTATION, second.type)
        assertEquals(2, second.streak)
    }
}

