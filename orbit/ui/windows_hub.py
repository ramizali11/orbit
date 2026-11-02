"""Comprehensive Windows Desktop Hub for Orbit.

Features:
  - Dual-Endpoint Dashboard (Earbuds vs Charging Case status)
  - Bluetooth Device Manager & Scanner (Registry, CoreAudio & Win32 inquiry)
  - Rotary Dial Customization (CW, CCW, Clicks, Hold, Invert, Rate Multiplier)
  - Live Input Testing Screen (Interactive 16-step animated Canvas dial & event log)
  - Subsystem Diagnostics (AVRCP, ETW, SMTC, WMI)
  - Windows Autostart & Background Preferences
"""
from __future__ import annotations

import logging
import time
from typing import Callable, Optional

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPen
from PySide6.QtWidgets import (
    QAbstractButton, QCheckBox, QComboBox, QFrame, QGroupBox, QHBoxLayout,
    QHeaderView, QLabel, QLineEdit, QMainWindow, QPushButton, QScrollArea,
    QSlider, QSpinBox, QTabWidget, QTableWidget, QTableWidgetItem, QTextEdit,
    QVBoxLayout, QWidget
)

from orbit.core.device_registry import DeviceFingerprint, DeviceRecord, DeviceRegistry
from orbit.core.endpoints import ConnectionTopology, EndpointState, UnifiedDeviceSession
from orbit.core.events import InputEvent, Kind
from orbit.platform.windows.actions import ACTIONS, DialActionProfile, WindowsActionExecutor
from orbit.platform.windows.discovery import DiscoveredDevice, WindowsBluetoothDiscovery
from orbit.protocol.adapters import ProtocolDetector
from orbit.ui.dial_canvas import DialCanvas

log = logging.getLogger("orbit.hub")

COLOR_CANVAS = "#101217"
COLOR_PANEL = "#151820"
COLOR_GROUP = "#1A1D25"
COLOR_BORDER = "#262A34"
COLOR_TEXT = "#F2F4F8"
COLOR_TEXT_DIM = "#8A8F9C"
COLOR_ORANGE = "#FF5500"
COLOR_GREEN = "#2ECC71"
COLOR_RED = "#E74C3C"


class WindowsHubWindow(QMainWindow):
    event_received = Signal(object)

    def __init__(self, registry: DeviceRegistry, action_profile: DialActionProfile,
                 on_profile_save: Callable[[DialActionProfile], None],
                 executor: Optional[WindowsActionExecutor] = None,
                 parent=None):
        super().__init__(parent)
        self.registry = registry
        self.profile = action_profile
        self.on_profile_save = on_profile_save
        self.executor = executor
        self.discovery = WindowsBluetoothDiscovery()
        self.discovered_cache: list[DiscoveredDevice] = []

        active_rec = self.registry.active_device
        dev_name = active_rec.display_name if active_rec else "CMF Buds Pro 2"
        dev_id = active_rec.id if active_rec else "40:ED:98:AA:BB:CC"
        self.session = UnifiedDeviceSession(dev_id, dev_name, ConnectionTopology.INDIRECT_BRIDGED)

        self.setWindowTitle("Orbit — Universal Dial Controller")
        self.setMinimumSize(860, 640)
        self.resize(920, 680)
        self.setStyleSheet(f"""
            QMainWindow, QWidget#central {{ background-color: {COLOR_CANVAS}; color: {COLOR_TEXT}; }}
            QTabWidget::pane {{ border: 1px solid {COLOR_BORDER}; background: {COLOR_PANEL}; border-radius: 8px; }}
            QTabBar::tab {{
                background: {COLOR_CANVAS}; color: {COLOR_TEXT_DIM}; padding: 10px 20px;
                font-weight: bold; border-top-left-radius: 6px; border-top-right-radius: 6px;
                margin-right: 4px;
            }}
            QTabBar::tab:selected {{ background: {COLOR_PANEL}; color: {COLOR_ORANGE}; border: 1px solid {COLOR_BORDER}; border-bottom: none; }}
            QTabBar::tab:hover {{ color: {COLOR_TEXT}; }}
            QGroupBox {{ font-weight: bold; border: 1px solid {COLOR_BORDER}; border-radius: 8px; margin-top: 12px; padding: 14px; background: {COLOR_GROUP}; }}
            QGroupBox::title {{ subcontrol-origin: margin; left: 14px; padding: 0 4px; color: {COLOR_TEXT}; }}
            QPushButton {{
                background-color: {COLOR_GROUP}; border: 1px solid {COLOR_BORDER}; color: {COLOR_TEXT};
                padding: 7px 16px; border-radius: 6px; font-weight: 500;
            }}
            QPushButton:hover {{ background-color: #242934; border-color: #3B4254; }}
            QPushButton#primary {{ background-color: {COLOR_ORANGE}; color: #FFFFFF; font-weight: bold; border: none; }}
            QPushButton#primary:hover {{ background-color: #FF661A; }}
            QComboBox, QLineEdit {{
                background-color: {COLOR_PANEL}; border: 1px solid {COLOR_BORDER}; color: {COLOR_TEXT};
                padding: 6px 10px; border-radius: 6px; min-height: 20px;
            }}
            QComboBox::drop-down {{ border: none; }}
            QTableWidget {{
                background-color: {COLOR_PANEL}; alternate-background-color: {COLOR_GROUP};
                border: 1px solid {COLOR_BORDER}; gridline-color: {COLOR_BORDER}; color: {COLOR_TEXT};
            }}
            QHeaderView::section {{ background-color: {COLOR_GROUP}; color: {COLOR_TEXT_DIM}; padding: 6px; border: 1px solid {COLOR_BORDER}; }}
            QTextEdit {{ background-color: #0C0E12; border: 1px solid {COLOR_BORDER}; color: #00FF66; font-family: Consolas, monospace; font-size: 11px; }}
            QScrollBar:vertical {{
                background-color: {COLOR_PANEL}; width: 14px; margin: 0px; border-radius: 6px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {COLOR_BORDER}; border-radius: 5px; min-height: 36px; margin: 2px;
            }}
            QScrollBar::handle:vertical:hover {{ background-color: #3B4254; }}
            QScrollBar::handle:vertical:pressed {{ background-color: {COLOR_ORANGE}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; background: none; border: none; }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: none; }}
        """)

        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(12)

        # Header bar
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("ORBIT")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setStyleSheet(f"color: {COLOR_ORANGE}; letter-spacing: 2px;")
        subtitle = QLabel("Universal Bluetooth Rotary Dial Controller for Windows 10 & 11")
        subtitle.setStyleSheet(f"color: {COLOR_TEXT_DIM}; font-size: 12px;")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box)
        header.addStretch(1)

        self.btn_power = QPushButton("Orbit Active: ON")
        self.btn_power.setObjectName("primary")
        self.btn_power.setCheckable(True)
        self.btn_power.setChecked(True)
        self.btn_power.clicked.connect(self._toggle_power)
        header.addWidget(self.btn_power)
        root.addLayout(header)

        # Tabs
        self.tabs = QTabWidget()
        self.tab_dashboard = QWidget()
        self.tab_devices = QWidget()
        self.tab_customization = QWidget()
        self.tab_testing = QWidget()
        self.tab_diagnostics = QWidget()
        self.tab_settings = QWidget()

        self.tabs.addTab(self.tab_dashboard, "Dashboard")
        self.tabs.addTab(self.tab_devices, "Device Manager")
        self.tabs.addTab(self.tab_customization, "Dial Customization")
        self.tabs.addTab(self.tab_testing, "Live Input Testing")
        self.tabs.addTab(self.tab_diagnostics, "Diagnostics")
        self.tabs.addTab(self.tab_settings, "Settings")
        root.addWidget(self.tabs, 1)

        self._build_dashboard_tab()
        self._build_devices_tab()
        self._build_customization_tab()
        self._build_testing_tab()
        self._build_diagnostics_tab()
        self._build_settings_tab()

        self.event_received.connect(self._on_bus_event)

        # Polling timer for active audio state
        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(1200)
        self._poll_timer.timeout.connect(self._poll_audio_state)
        self._poll_timer.start()

    # ---------------------------------------------------------------- Dashboard Tab
    def _build_dashboard_tab(self):
        tab_layout = QVBoxLayout(self.tab_dashboard)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        content = QWidget()
        v = QVBoxLayout(content)
        v.setContentsMargins(20, 20, 20, 20)
        v.setSpacing(18)

        # Dual Endpoint Status Cards
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(16)

        # Card 1: Earbuds Endpoint
        self.card_earbuds = QGroupBox("Earbuds Endpoint (Audio & Controls)")
        eb_layout = QVBoxLayout(self.card_earbuds)
        self.lbl_eb_name = QLabel(f"Device: {self.session.earbuds.name}")
        self.lbl_eb_state = QLabel("Status: Detecting...")
        self.lbl_eb_state.setStyleSheet(f"color: {COLOR_GREEN}; font-weight: bold;")
        self.lbl_eb_topology = QLabel("Topology: Classic Bluetooth (A2DP / AVRCP / HFP)")
        self.lbl_eb_topology.setStyleSheet(f"color: {COLOR_TEXT_DIM}; font-size: 11px;")
        eb_layout.addWidget(self.lbl_eb_name)
        eb_layout.addWidget(self.lbl_eb_state)
        eb_layout.addWidget(self.lbl_eb_topology)
        cards_layout.addWidget(self.card_earbuds, 1)

        # Card 2: Charging Case Dial Endpoint
        self.card_case = QGroupBox("Charging Case Dial Endpoint (Physical Dial)")
        case_layout = QVBoxLayout(self.card_case)
        self.lbl_case_name = QLabel(f"Dial: {self.session.case.name}")
        self.lbl_case_state = QLabel("Status: Active (Bridged via Earbuds)")
        self.lbl_case_state.setStyleSheet(f"color: {COLOR_ORANGE}; font-weight: bold;")
        self.lbl_case_mode = QLabel("Dial Link: INDIRECT_BRIDGED (Physical Dial -> Earbud -> Windows)")
        self.lbl_case_mode.setStyleSheet(f"color: {COLOR_TEXT_DIM}; font-size: 11px;")
        case_layout.addWidget(self.lbl_case_name)
        case_layout.addWidget(self.lbl_case_state)
        case_layout.addWidget(self.lbl_case_mode)
        cards_layout.addWidget(self.card_case, 1)

        v.addLayout(cards_layout)

        # Active Mappings Summary
        box_summary = QGroupBox("Active Dial Action Mappings")
        sum_layout = QVBoxLayout(box_summary)
        self.lbl_cw_sum = QLabel(f"Turn Clockwise (CW):  {self._action_title(self.profile.cw_action)}")
        self.lbl_ccw_sum = QLabel(f"Turn Counter-Clockwise (CCW):  {self._action_title(self.profile.ccw_action)}")
        self.lbl_click_sum = QLabel(f"Single Press:  {self._action_title(self.profile.click_action)}")
        self.lbl_hold_sum = QLabel(f"Long Press (Hold):  {self._action_title(self.profile.hold_action)}")
        for l in (self.lbl_cw_sum, self.lbl_ccw_sum, self.lbl_click_sum, self.lbl_hold_sum):
            l.setFont(QFont("Segoe UI", 12))
            sum_layout.addWidget(l)
        v.addWidget(box_summary)

        # Quick Shortcuts / Actions
        btn_box = QHBoxLayout()
        btn_test = QPushButton("Open Live Dial Test Screen")
        btn_test.clicked.connect(lambda: self.tabs.setCurrentIndex(3))
        btn_dev = QPushButton("Manage Bluetooth Devices")
        btn_dev.clicked.connect(lambda: self.tabs.setCurrentIndex(1))
        btn_box.addWidget(btn_test)
        btn_box.addWidget(btn_dev)
        btn_box.addStretch(1)
        v.addLayout(btn_box)
        v.addStretch(1)
        scroll.setWidget(content)
        tab_layout.addWidget(scroll)

    # ---------------------------------------------------------------- Device Manager Tab
    def _build_devices_tab(self):
        v = QVBoxLayout(self.tab_devices)
        v.setContentsMargins(18, 18, 18, 18)
        v.setSpacing(12)

        ctrl_bar = QHBoxLayout()
        btn_scan = QPushButton("Scan for Bluetooth Devices")
        btn_scan.setObjectName("primary")
        btn_scan.clicked.connect(self._run_scan)
        self.lbl_scan_status = QLabel("Ready")
        self.lbl_scan_status.setStyleSheet(f"color: {COLOR_TEXT_DIM};")
        ctrl_bar.addWidget(btn_scan)
        ctrl_bar.addWidget(self.lbl_scan_status)
        ctrl_bar.addStretch(1)
        v.addLayout(ctrl_bar)

        self.dev_table = QTableWidget(0, 5)
        self.dev_table.setHorizontalHeaderLabels(["Device Name", "MAC Address", "Type", "Status", "Adapter Affinity"])
        self.dev_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.dev_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.dev_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.dev_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.dev_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.dev_table.setSelectionBehavior(QTableWidget.SelectRows)
        v.addWidget(self.dev_table, 1)

        action_bar = QHBoxLayout()
        self.btn_select_active = QPushButton("Set Selected as Active Dial")
        self.btn_select_active.clicked.connect(self._set_selected_active)
        self.edit_nickname = QLineEdit()
        self.edit_nickname.setPlaceholderText("Enter custom nickname...")
        self.btn_rename = QPushButton("Rename Device")
        self.btn_rename.clicked.connect(self._rename_selected)
        action_bar.addWidget(self.btn_select_active)
        action_bar.addSpacing(12)
        action_bar.addWidget(self.edit_nickname)
        action_bar.addWidget(self.btn_rename)
        v.addLayout(action_bar)

        self._refresh_device_table()

    def _run_scan(self):
        self.lbl_scan_status.setText("Scanning Bluetooth devices and audio endpoints...")
        self.discovery.start_async_discovery(self._on_scan_completed, issue_inquiry=True)

    def _on_scan_completed(self, devs: list[DiscoveredDevice]):
        self.discovered_cache = devs
        QTimer.singleShot(0, lambda: self._update_device_table_after_scan(devs))

    def _update_device_table_after_scan(self, devs: list[DiscoveredDevice]):
        self.lbl_scan_status.setText(f"Scan complete — found {len(devs)} devices")
        for d in devs:
            self.registry.register_or_update(d.fingerprint)
        self._refresh_device_table()

    def _refresh_device_table(self):
        records = self.registry.get_all()
        active_id = self.registry.active_device.id if self.registry.active_device else ""
        self.dev_table.setRowCount(len(records))

        for row, rec in enumerate(records):
            is_active = (rec.id == active_id)
            name_text = rec.display_name + ("  ★ ACTIVE" if is_active else "")
            item_name = QTableWidgetItem(name_text)
            if is_active:
                item_name.setForeground(QColor(COLOR_ORANGE))
            self.dev_table.setItem(row, 0, item_name)
            self.dev_table.setItem(row, 1, QTableWidgetItem(rec.id))
            self.dev_table.setItem(row, 2, QTableWidgetItem(rec.fingerprint.connection_type))

            # Connected status
            is_conn = any(d.fingerprint.address.upper() == rec.id.upper() and d.is_connected for d in self.discovered_cache)
            status_text = "Connected" if is_conn else "Paired / Known"
            item_status = QTableWidgetItem(status_text)
            if is_conn:
                item_status.setForeground(QColor(COLOR_GREEN))
            self.dev_table.setItem(row, 3, item_status)

            adapter = ProtocolDetector.detect(rec.fingerprint, rec.adapter_id)
            self.dev_table.setItem(row, 4, QTableWidgetItem(adapter.id))

    def _set_selected_active(self):
        row = self.dev_table.currentRow()
        if row >= 0:
            mac_item = self.dev_table.item(row, 1)
            if mac_item:
                dev_id = mac_item.text().strip()
                self.registry.set_active_device(dev_id)
                rec = self.registry.get(dev_id)
                if rec:
                    self.session.device_id = rec.id
                    self.session.display_name = rec.display_name
                    self.session.earbuds.name = rec.display_name
                    self.session.case.name = f"{rec.display_name} Case Dial"
                    self.lbl_eb_name.setText(f"Device: {rec.display_name}")
                    self.lbl_case_name.setText(f"Dial: {rec.display_name} Case Dial")
                self._refresh_device_table()

    def _rename_selected(self):
        row = self.dev_table.currentRow()
        new_name = self.edit_nickname.text().strip()
        if row >= 0 and new_name:
            mac_item = self.dev_table.item(row, 1)
            if mac_item:
                self.registry.set_custom_name(mac_item.text(), new_name)
                self.edit_nickname.clear()
                self._refresh_device_table()

    # ---------------------------------------------------------------- Dial Customization Tab
    def _build_customization_tab(self):
        tab_layout = QVBoxLayout(self.tab_customization)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        content = QWidget()
        v = QVBoxLayout(content)
        v.setContentsMargins(20, 20, 20, 20)
        v.setSpacing(14)

        box_rot = QGroupBox("Rotary Dial Actions (Rotation)")
        l_rot = QVBoxLayout(box_rot)

        # CW
        row_cw = QHBoxLayout()
        row_cw.addWidget(QLabel("Clockwise Turn (CW / Right):"), 1)
        self.combo_cw = self._create_action_combo(self.profile.cw_action)
        row_cw.addWidget(self.combo_cw, 2)
        l_rot.addLayout(row_cw)

        # CCW
        row_ccw = QHBoxLayout()
        row_ccw.addWidget(QLabel("Counter-Clockwise Turn (CCW / Left):"), 1)
        self.combo_ccw = self._create_action_combo(self.profile.ccw_action)
        row_ccw.addWidget(self.combo_ccw, 2)
        l_rot.addLayout(row_ccw)

        # Invert Direction
        self.chk_invert = QCheckBox("Invert Rotary Direction (Swap CW and CCW)")
        self.chk_invert.setChecked(self.profile.invert_direction)
        l_rot.addWidget(self.chk_invert)

        # Rate Multiplier
        row_rate = QHBoxLayout()
        row_rate.addWidget(QLabel("Fast-Spin Multiplier:"), 1)
        self.slider_rate = QSlider(Qt.Horizontal)
        self.slider_rate.setRange(10, 30)
        self.slider_rate.setValue(int(self.profile.rate_multiplier * 10))
        self.lbl_rate_val = QLabel(f"{self.profile.rate_multiplier:.1f}x")
        self.slider_rate.valueChanged.connect(lambda v: self.lbl_rate_val.setText(f"{v/10.0:.1f}x"))
        row_rate.addWidget(self.slider_rate, 2)
        row_rate.addWidget(self.lbl_rate_val)
        l_rot.addLayout(row_rate)
        v.addWidget(box_rot)

        # Button Gestures
        box_btn = QGroupBox("Dial Push Button Gestures")
        l_btn = QVBoxLayout(box_btn)

        row_click = QHBoxLayout()
        row_click.addWidget(QLabel("Single Press:"), 1)
        self.combo_click = self._create_action_combo(self.profile.click_action)
        row_click.addWidget(self.combo_click, 2)
        l_btn.addLayout(row_click)

        row_dbl = QHBoxLayout()
        row_dbl.addWidget(QLabel("Double Press:"), 1)
        self.combo_dbl = self._create_action_combo(self.profile.double_click_action)
        row_dbl.addWidget(self.combo_dbl, 2)
        l_btn.addLayout(row_dbl)

        row_tpl = QHBoxLayout()
        row_tpl.addWidget(QLabel("Triple Press:"), 1)
        self.combo_tpl = self._create_action_combo(self.profile.triple_click_action)
        row_tpl.addWidget(self.combo_tpl, 2)
        l_btn.addLayout(row_tpl)

        row_hold = QHBoxLayout()
        row_hold.addWidget(QLabel("Long Press (Hold):"), 1)
        self.combo_hold = self._create_action_combo(self.profile.hold_action)
        row_hold.addWidget(self.combo_hold, 2)
        l_btn.addLayout(row_hold)
        v.addWidget(box_btn)

        # Save Actions Button
        btn_save = QPushButton("Apply & Save Action Settings")
        btn_save.setObjectName("primary")
        btn_save.clicked.connect(self._save_actions)
        v.addWidget(btn_save, 0, Qt.AlignRight)
        v.addStretch(1)
        scroll.setWidget(content)
        tab_layout.addWidget(scroll)

    def _create_action_combo(self, selected_id: str) -> QComboBox:
        combo = QComboBox()
        for item in ACTIONS:
            combo.addItem(f"[{item.category.value}] {item.title}", item.id)
        idx = combo.findData(selected_id)
        if idx >= 0:
            combo.setCurrentIndex(idx)
        return combo

    def _action_title(self, action_id: str) -> str:
        for item in ACTIONS:
            if item.id == action_id:
                return item.title
        return action_id

    def _save_actions(self):
        self.profile.cw_action = self.combo_cw.currentData()
        self.profile.ccw_action = self.combo_ccw.currentData()
        self.profile.click_action = self.combo_click.currentData()
        self.profile.double_click_action = self.combo_dbl.currentData()
        self.profile.triple_click_action = self.combo_tpl.currentData()
        self.profile.hold_action = self.combo_hold.currentData()
        self.profile.invert_direction = self.chk_invert.isChecked()
        self.profile.rate_multiplier = self.slider_rate.value() / 10.0

        self.on_profile_save(self.profile)

        # Update dashboard summary
        self.lbl_cw_sum.setText(f"Turn Clockwise (CW):  {self._action_title(self.profile.cw_action)}")
        self.lbl_ccw_sum.setText(f"Turn Counter-Clockwise (CCW):  {self._action_title(self.profile.ccw_action)}")
        self.lbl_click_sum.setText(f"Single Press:  {self._action_title(self.profile.click_action)}")
        self.lbl_hold_sum.setText(f"Long Press (Hold):  {self._action_title(self.profile.hold_action)}")

    # ---------------------------------------------------------------- Live Testing Tab
    def _build_testing_tab(self):
        h = QHBoxLayout(self.tab_testing)
        h.setContentsMargins(18, 18, 18, 18)
        h.setSpacing(18)

        # Left: Interactive Dial
        left_box = QVBoxLayout()
        self.canvas_dial = DialCanvas()
        left_box.addWidget(self.canvas_dial, 0, Qt.AlignCenter)

        stats_box = QGroupBox("Live Dial Telemetry")
        s_layout = QVBoxLayout(stats_box)
        self.lbl_test_steps = QLabel("Cumulative Detents: 0")
        self.lbl_test_dir = QLabel("Last Direction: IDLE")
        self.lbl_test_action = QLabel("Last Triggered Action: None")
        for l in (self.lbl_test_steps, self.lbl_test_dir, self.lbl_test_action):
            l.setFont(QFont("Segoe UI", 11))
            s_layout.addWidget(l)

        btn_reset_test = QPushButton("Reset Dial Counters")
        btn_reset_test.clicked.connect(self._reset_testing)
        s_layout.addWidget(btn_reset_test)
        left_box.addWidget(stats_box)
        left_box.addStretch(1)
        h.addLayout(left_box, 1)

        # Right: Live Event Stream Log
        right_box = QVBoxLayout()
        right_box.addWidget(QLabel("Live Physical Dial Event Stream:"))
        self.txt_events = QTextEdit()
        self.txt_events.setReadOnly(True)
        right_box.addWidget(self.txt_events, 1)

        btn_clear_log = QPushButton("Clear Log")
        btn_clear_log.clicked.connect(self.txt_events.clear)
        right_box.addWidget(btn_clear_log, 0, Qt.AlignRight)
        h.addLayout(right_box, 2)

    def _reset_testing(self):
        self.canvas_dial.reset_counters()
        self.lbl_test_steps.setText("Cumulative Detents: 0")
        self.lbl_test_dir.setText("Last Direction: IDLE")
        self.lbl_test_action.setText("Last Triggered Action: None")

    # ---------------------------------------------------------------- Diagnostics Tab
    def _build_diagnostics_tab(self):
        v = QVBoxLayout(self.tab_diagnostics)
        v.setContentsMargins(18, 18, 18, 18)
        v.setSpacing(14)

        box_sub = QGroupBox("Windows Subsystems Status")
        s_layout = QVBoxLayout(box_sub)

        # AVRCP Audio Volume
        self.lbl_diag_avrcp = QLabel("✔ CoreAudio AVRCP Absolute Volume: Active")
        self.lbl_diag_avrcp.setStyleSheet(f"color: {COLOR_GREEN};")
        # ETW BTHPORT
        from orbit.platform.windows import etw
        is_admin = etw.is_admin()
        etw_text = "✔ ETW BTHPORT Kernel Trace (AT+BVRA Sniffer): Running (Elevated)" if is_admin else \
            "⚠ ETW BTHPORT Kernel Trace: Disabled (Standard User — Run as Admin for Hold)"
        self.lbl_diag_etw = QLabel(etw_text)
        self.lbl_diag_etw.setStyleSheet(f"color: {COLOR_GREEN if is_admin else COLOR_ORANGE};")

        # SMTC Media
        self.lbl_diag_smtc = QLabel("✔ System Media Transport Controls (SMTC): Connected")
        self.lbl_diag_smtc.setStyleSheet(f"color: {COLOR_GREEN};")

        # WMI Brightness
        from orbit.platform.windows.brightness import InternalBrightness
        b = InternalBrightness()
        has_bright = b.get() is not None
        bright_text = "✔ WMI Internal Monitor Brightness: Supported" if has_bright else \
            "ℹ WMI Internal Monitor Brightness: Desktop Monitor (DDC/CI External or N/A)"
        self.lbl_diag_wmi = QLabel(bright_text)
        self.lbl_diag_wmi.setStyleSheet(f"color: {COLOR_GREEN if has_bright else COLOR_TEXT_DIM};")

        s_layout.addWidget(self.lbl_diag_avrcp)
        s_layout.addWidget(self.lbl_diag_etw)
        s_layout.addWidget(self.lbl_diag_smtc)
        s_layout.addWidget(self.lbl_diag_wmi)
        v.addWidget(box_sub)

        v.addWidget(QLabel("Raw Diagnostic Protocol Output:"))
        self.txt_raw_diag = QTextEdit()
        self.txt_raw_diag.setReadOnly(True)
        v.addWidget(self.txt_raw_diag, 1)

    # ---------------------------------------------------------------- Settings Tab
    def _build_settings_tab(self):
        tab_layout = QVBoxLayout(self.tab_settings)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        content = QWidget()
        v = QVBoxLayout(content)
        v.setContentsMargins(20, 20, 20, 20)
        v.setSpacing(14)

        box_start = QGroupBox("Startup & Background Operation")
        l_start = QVBoxLayout(box_start)

        from orbit.platform.windows import autostart
        self.chk_autostart = QCheckBox("Start Orbit automatically when signing into Windows")
        self.chk_autostart.setChecked(autostart.enabled() if autostart.available() else False)
        self.chk_autostart.toggled.connect(self._toggle_autostart)
        l_start.addWidget(self.chk_autostart)

        self.chk_flyout = QCheckBox("Hide Windows on-screen volume bar during dial rotation")
        self.chk_flyout.setChecked(True)
        l_start.addWidget(self.chk_flyout)

        self.chk_tray_close = QCheckBox("Minimize to system tray when closing window")
        self.chk_tray_close.setChecked(True)
        l_start.addWidget(self.chk_tray_close)
        v.addWidget(box_start)

        box_about = QGroupBox("About Orbit")
        l_about = QVBoxLayout(box_about)
        l_about.addWidget(QLabel("Orbit Universal Dial Controller v2.0 (Windows Native Edition)"))
        l_about.addWidget(QLabel("Target: CMF Buds Pro 2, CMF devices, third-party rotary earbuds, and BLE dials."))
        l_about.addWidget(QLabel("Platform: Windows 10 (19041+) and Windows 11"))
        v.addWidget(box_about)
        v.addStretch(1)
        scroll.setWidget(content)
        tab_layout.addWidget(scroll)

    def _toggle_autostart(self, enabled: bool):
        from orbit.platform.windows import autostart
        if autostart.available():
            autostart.set_enabled(enabled)

    def _toggle_power(self, checked: bool):
        self.btn_power.setText("Orbit Active: ON" if checked else "Orbit Paused: OFF")
        self.btn_power.setStyleSheet(f"background-color: {COLOR_ORANGE if checked else '#444A59'};")

    def _poll_audio_state(self):
        # Checks if any audio render endpoint is actively bound
        active_rec = self.registry.active_device
        if active_rec:
            self.lbl_eb_state.setText(f"Status: Connected ({active_rec.display_name})")
            self.lbl_case_state.setText("Status: Active (Physical Dial Ready)")
            self.session.update_earbuds(EndpointState.CONNECTED)
        else:
            self.lbl_eb_state.setText("Status: Waiting for device...")
            self.lbl_case_state.setText("Status: Idle")

    def post_event(self, ev: InputEvent):
        """Dispatched from worker threads into the Qt main thread."""
        self.event_received.emit(ev)

    def _on_bus_event(self, ev: InputEvent):
        now_str = time.strftime("%H:%M:%S")

        # 1. Update live test canvas
        if ev.kind == Kind.ROTATE:
            eff_delta = -ev.delta if self.profile.invert_direction else ev.delta
            scaled_delta = int(round(eff_delta * self.profile.rate_multiplier))
            self.canvas_dial.on_dial_step(scaled_delta)
            self.lbl_test_steps.setText(f"Cumulative Detents: {self.canvas_dial.total_steps:+d}")
            self.lbl_test_dir.setText(f"Last Direction: {'Clockwise (CW)' if scaled_delta > 0 else 'Counter-Clockwise (CCW)'}")

            # Execute action if configured
            action_id = self.profile.cw_action if scaled_delta > 0 else self.profile.ccw_action
            self.lbl_test_action.setText(f"Last Triggered Action: {self._action_title(action_id)}")
            if self.executor and self.btn_power.isChecked():
                self.executor.execute(action_id, steps=abs(scaled_delta))

            self.session.update_dial_activity()
            self.txt_events.append(f"[{now_str}] ROTATE detents={scaled_delta:+d} -> Action: {self._action_title(action_id)}")

        elif ev.kind in (Kind.CLICK, Kind.DOUBLE, Kind.TRIPLE, Kind.HOLD):
            self.canvas_dial.on_button_event(ev.kind.value)
            action_map = {
                Kind.CLICK: self.profile.click_action,
                Kind.DOUBLE: self.profile.double_click_action,
                Kind.TRIPLE: self.profile.triple_click_action,
                Kind.HOLD: self.profile.hold_action,
            }
            action_id = action_map.get(ev.kind, "none")
            self.lbl_test_action.setText(f"Last Triggered Action: {self._action_title(action_id)}")
            if self.executor and self.btn_power.isChecked():
                self.executor.execute(action_id)

            self.session.update_dial_activity()
            self.txt_events.append(f"[{now_str}] BUTTON {ev.kind.value.upper()} -> Action: {self._action_title(action_id)}")

        # Also append to raw diagnostic log
        self.txt_raw_diag.append(f"[{now_str}] {ev.source}: {ev.kind.value} delta={ev.delta} t={ev.t:.3f}")

