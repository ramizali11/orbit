"""Interactive 16-step animated Canvas dial widget for Windows.

Draws a virtual rotary encoder with 16 physical detents, rotating indicator needle,
live click flashes, and velocity/direction response matching the physical CMF dial.
"""
from __future__ import annotations

import math
from PySide6.QtCore import QEasingCurve, QPointF, QPropertyAnimation, QRectF, QSize, Qt, Property
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen, QRadialGradient, QWheelEvent
from PySide6.QtWidgets import QWidget

DETENTS = 16
STEP_DEG = 360.0 / DETENTS  # 22.5 degrees per physical step
ACCENT_ORANGE = "#FF5500"
ACCENT_GLOW = "#FF7722"
BG_CHASSIS = "#13161C"
BG_KNOB = "#1C202A"
TICK_DIM = "#323744"
TICK_LIT = "#FF5500"


class DialCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(220, 220)
        self.setMaximumSize(320, 320)
        self._angle = 0.0
        self._target_angle = 0.0
        self._last_delta = 0
        self._total_steps = 0
        self._active_tick = 0
        self._flash_alpha = 0.0
        self._last_event_kind = "IDLE"

        self._anim = QPropertyAnimation(self, b"angle", self)
        self._anim.setDuration(120)
        self._anim.setEasingCurve(QEasingCurve.OutQuad)

    def sizeHint(self) -> QSize:
        return QSize(260, 260)

    def _get_angle(self) -> float:
        return self._angle

    def _set_angle(self, val: float) -> None:
        self._angle = val
        self.update()

    angle = Property(float, _get_angle, _set_angle)

    def on_dial_step(self, delta: int) -> None:
        self._last_delta = delta
        self._total_steps += delta
        self._active_tick = (self._active_tick + delta) % DETENTS
        self._last_event_kind = "CW" if delta > 0 else "CCW"

        self._anim.stop()
        self._anim.setStartValue(self._angle)
        self._target_angle += delta * STEP_DEG
        self._anim.setEndValue(self._target_angle)
        self._anim.start()

    def on_button_event(self, kind: str) -> None:
        self._last_event_kind = kind.upper()
        self._flash_alpha = 1.0
        self.update()

    def reset_counters(self) -> None:
        self._total_steps = 0
        self._last_delta = 0
        self._last_event_kind = "IDLE"
        self._target_angle = 0.0
        self._angle = 0.0
        self.update()

    @property
    def total_steps(self) -> int:
        return self._total_steps

    @property
    def last_kind(self) -> str:
        return self._last_event_kind

    def wheelEvent(self, event: QWheelEvent) -> None:
        delta = 1 if event.angleDelta().y() > 0 else -1
        self.on_dial_step(delta)
        event.accept()

    def paintEvent(self, _) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        cx, cy = w / 2.0, h / 2.0
        radius = min(w, h) / 2.0 - 12.0

        # Outer chassis ring
        p.setPen(QPen(QColor("#242834"), 2.0))
        p.setBrush(QColor(BG_CHASSIS))
        p.drawEllipse(QPointF(cx, cy), radius, radius)

        # Draw 16 detent ticks around perimeter
        tick_len = radius * 0.12
        for i in range(DETENTS):
            deg = i * STEP_DEG - 90.0
            rad = math.radians(deg)
            is_active = (i == self._active_tick)

            x_out = cx + (radius - 6.0) * math.cos(rad)
            y_out = cy + (radius - 6.0) * math.sin(rad)
            x_in = cx + (radius - 6.0 - tick_len) * math.cos(rad)
            y_in = cy + (radius - 6.0 - tick_len) * math.sin(rad)

            if is_active:
                p.setPen(QPen(QColor(TICK_LIT), 3.0))
            else:
                p.setPen(QPen(QColor(TICK_DIM), 1.5))
            p.drawLine(QPointF(x_in, y_in), QPointF(x_out, y_out))

        # Central knob circle
        knob_r = radius * 0.68
        grad = QRadialGradient(cx, cy, knob_r)
        grad.setColorAt(0.0, QColor("#2A2F3D"))
        grad.setColorAt(0.85, QColor(BG_KNOB))
        grad.setColorAt(1.0, QColor("#14171E"))

        p.setPen(QPen(QColor("#3A4050"), 1.5))
        p.setBrush(QBrush(grad))
        p.drawEllipse(QPointF(cx, cy), knob_r, knob_r)

        # Rotating needle indicator
        needle_rad = math.radians(self._angle - 90.0)
        nx_tip = cx + (knob_r - 8.0) * math.cos(needle_rad)
        ny_tip = cy + (knob_r - 8.0) * math.sin(needle_rad)
        nx_base = cx + (knob_r * 0.22) * math.cos(needle_rad)
        ny_base = cy + (knob_r * 0.22) * math.sin(needle_rad)

        p.setPen(QPen(QColor(ACCENT_ORANGE), 3.5, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(QPointF(nx_base, ny_base), QPointF(nx_tip, ny_tip))

        # Center cap
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(ACCENT_ORANGE))
        p.drawEllipse(QPointF(cx, cy), 6.0, 6.0)

        # Event flash effect if button pressed
        if self._flash_alpha > 0.05:
            flash_col = QColor(ACCENT_ORANGE)
            flash_col.setAlphaF(min(1.0, self._flash_alpha * 0.35))
            p.setBrush(flash_col)
            p.drawEllipse(QPointF(cx, cy), knob_r, knob_r)
            self._flash_alpha *= 0.85
            if self._flash_alpha > 0.05:
                self.update()

        # Step count badge at center-bottom
        p.setPen(QColor("#A0A6B5"))
        font = p.font()
        font.setPixelSize(11)
        font.setBold(True)
        p.setFont(font)
        text = f"{self._total_steps:+d}" if self._total_steps != 0 else "0"
        p.drawText(QRectF(cx - 30, cy + knob_r * 0.35, 60, 20), Qt.AlignCenter, f"{text} det")

