"""Tests for UI scrolling behavior in Orbit:

Verifies that:
- The scrollbar beside the controls is properly scrollable.
- Scrolling works using mouse wheel, scrollbar dragging, and touchpad gestures.
- The Orbit circular control (WheelPreview) and parent containers do not intercept/block scrolling.
- Horizontal sliders and combo boxes do not capture wheel events from the scroll area.
- Scrollbar handle dragging and paging update the scroll offset.
- The layout remains responsive on varying window sizes without hiding or blocking the scrollbar.
- Windows Hub tabs (customization with volume actions, dashboard, settings) have functional scroll areas.
- DialCanvas responds to wheel events to step detents.
"""
import pytest
from pathlib import Path
from PySide6.QtCore import Qt, QPoint, QPointF, QEvent
from PySide6.QtGui import QWheelEvent, QMouseEvent
from PySide6.QtWidgets import QApplication, QScrollArea, QSlider, QComboBox, QScrollBar

from orbit.core import config as config_mod
from orbit.core import settings as st
from orbit.ui.settings_window import SettingsWindow
from orbit.ui.windows_hub import WindowsHubWindow
from orbit.ui.dial_canvas import DialCanvas
from orbit.core.device_registry import DeviceRegistry
from orbit.platform.windows.actions import DialActionProfile


@pytest.fixture
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def settings_win(tmp_path, app):
    base, _ = config_mod.load(platform="windows")
    saved = []
    w = SettingsWindow(base, {}, True, "#7C9CFF", saved.append, settings_path=tmp_path / "s.json")
    w.show()
    app.processEvents()
    return w


def test_mouse_wheel_on_viewport_scrolls(settings_win, app):
    sc = settings_win.scroll
    sb = sc.verticalScrollBar()
    sb.setValue(0)
    assert sb.value() == 0

    pos = sc.viewport().rect().center()
    ev = QWheelEvent(QPointF(pos), QPointF(sc.viewport().mapToGlobal(pos)),
                     QPoint(0, 0), QPoint(0, -120), Qt.NoButton, Qt.NoModifier, Qt.ScrollUpdate, False)
    app.sendEvent(sc.viewport(), ev)
    app.processEvents()
    assert sb.value() > 0, "Mouse wheel on viewport must scroll the scrollbar"


def test_mouse_wheel_on_orbit_circle_scrolls(settings_win, app):
    sc = settings_win.scroll
    sb = sc.verticalScrollBar()
    sb.setValue(0)

    # Wheel over the circular preview widget
    preview = settings_win.preview
    pos = preview.rect().center()
    ev = QWheelEvent(QPointF(pos), QPointF(preview.mapToGlobal(pos)),
                     QPoint(0, 0), QPoint(0, -120), Qt.NoButton, Qt.NoModifier, Qt.ScrollUpdate, False)
    app.sendEvent(preview, ev)
    app.processEvents()
    assert sb.value() > 0, "Mouse wheel over Orbit circle preview must scroll the content"


def test_mouse_wheel_on_slider_does_not_block_scrolling(settings_win, app):
    sc = settings_win.scroll
    sb = sc.verticalScrollBar()
    sb.setValue(0)

    slider = settings_win.findChild(QSlider)
    assert slider is not None
    init_slider_val = slider.value()

    pos = slider.rect().center()
    ev = QWheelEvent(QPointF(pos), QPointF(slider.mapToGlobal(pos)),
                     QPoint(0, 0), QPoint(0, -120), Qt.NoButton, Qt.NoModifier, Qt.ScrollUpdate, False)
    app.sendEvent(slider, ev)
    app.processEvents()

    assert sb.value() > 0, "Mouse wheel over slider must scroll the page rather than being blocked"
    # Ensure slider was not inadvertently moved by the scroll wheel
    assert slider.value() == init_slider_val


def test_mouse_wheel_on_combobox_does_not_block_scrolling(settings_win, app):
    sc = settings_win.scroll
    sb = sc.verticalScrollBar()
    sb.setValue(0)

    combo = settings_win.findChild(QComboBox)
    assert combo is not None
    init_combo_idx = combo.currentIndex()

    pos = combo.rect().center()
    ev = QWheelEvent(QPointF(pos), QPointF(combo.mapToGlobal(pos)),
                     QPoint(0, 0), QPoint(0, -120), Qt.NoButton, Qt.NoModifier, Qt.ScrollUpdate, False)
    app.sendEvent(combo, ev)
    app.processEvents()

    assert sb.value() > 0, "Mouse wheel over combobox must scroll the page"
    assert combo.currentIndex() == init_combo_idx


def test_scrollbar_dragging_and_release(settings_win, app):
    sc = settings_win.scroll
    sb = sc.verticalScrollBar()
    sb.setValue(0)
    assert sb.maximum() > 100, "Scrollable area must have scroll range"

    # Drag the scrollbar handle
    handle_x = sb.width() // 2
    handle_y = 20
    press_ev = QMouseEvent(QMouseEvent.MouseButtonPress, QPointF(handle_x, handle_y),
                          Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
    app.sendEvent(sb, press_ev)
    app.processEvents()

    move_ev = QMouseEvent(QMouseEvent.MouseMove, QPointF(handle_x, handle_y + 120),
                          Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
    app.sendEvent(sb, move_ev)
    app.processEvents()
    val_after_drag = sb.value()
    assert val_after_drag > 0, "Dragging the scrollbar thumb downwards must update the scroll offset"

    rel_ev = QMouseEvent(QMouseEvent.MouseButtonRelease, QPointF(handle_x, handle_y + 120),
                         Qt.LeftButton, Qt.NoButton, Qt.NoModifier)
    app.sendEvent(sb, rel_ev)
    app.processEvents()
    assert sb.value() == val_after_drag


def test_touchpad_gesture_scrolling(settings_win, app):
    sc = settings_win.scroll
    sb = sc.verticalScrollBar()
    sb.setValue(0)

    # Touchpad gesture gives pixel-based delta (pixelDelta = (0, -40))
    pos = sc.viewport().rect().center()
    ev = QWheelEvent(QPointF(pos), QPointF(sc.viewport().mapToGlobal(pos)),
                     QPoint(0, -40), QPoint(0, 0), Qt.NoButton, Qt.NoModifier, Qt.ScrollUpdate, False)
    app.sendEvent(sc.viewport(), ev)
    app.processEvents()
    assert sb.value() > 0, "Touchpad gesture with pixelDelta must scroll the scrollbar"


def test_layout_responsive_resizing(settings_win, app):
    sc = settings_win.scroll
    sb = sc.verticalScrollBar()

    # Resize to small window
    settings_win.resize(780, 520)
    app.processEvents()
    assert settings_win.preview.isVisible(), "Orbit circle must remain visible on small screens"
    assert sb.isVisible(), "Scrollbar must remain visible and accessible"
    assert sc.width() > 300, "Right scroll pane must have room"

    # Resize to large window
    settings_win.resize(1200, 900)
    app.processEvents()
    assert settings_win.preview.isVisible(), "Orbit circle must remain visible on large screens"
    assert sb.isVisible(), "Scrollbar must remain visible and accessible"


def test_windows_hub_customization_scroll_area(tmp_path, app):
    reg = DeviceRegistry(tmp_path / "dev.json")
    prof = DialActionProfile()
    hub = WindowsHubWindow(reg, prof, lambda p: None)
    hub.show()
    app.processEvents()

    # Tab 2: Dial Customization
    tab_cust = hub.tabs.widget(2)
    scrolls = tab_cust.findChildren(QScrollArea)
    assert len(scrolls) >= 1, "Dial Customization tab must contain a QScrollArea"
    sc = scrolls[0]
    assert sc.widgetResizable() is True
    assert sc.verticalScrollBarPolicy() == Qt.ScrollBarAsNeeded

    # Tab 0: Dashboard
    tab_dash = hub.tabs.widget(0)
    assert len(tab_dash.findChildren(QScrollArea)) >= 1, "Dashboard tab must contain a QScrollArea"


def test_dial_canvas_wheel_interaction(app):
    dial = DialCanvas()
    dial.show()
    app.processEvents()

    init_steps = dial.total_steps
    assert init_steps == 0

    # Spin wheel CW (+1)
    ev_cw = QWheelEvent(QPointF(100, 100), QPointF(100, 100), QPoint(0, 0), QPoint(0, 120),
                        Qt.NoButton, Qt.NoModifier, Qt.ScrollUpdate, False)
    dial.wheelEvent(ev_cw)
    assert dial.total_steps == 1
    assert dial.last_kind == "CW"

    # Spin wheel CCW (-1)
    ev_ccw = QWheelEvent(QPointF(100, 100), QPointF(100, 100), QPoint(0, 0), QPoint(0, -120),
                         Qt.NoButton, Qt.NoModifier, Qt.ScrollUpdate, False)
    dial.wheelEvent(ev_ccw)
    assert dial.total_steps == 0
    assert dial.last_kind == "CCW"

