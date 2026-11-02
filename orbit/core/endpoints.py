"""Logical Dual-Endpoint Architecture: Earbuds vs. Charging Case.

Models the physical reality that earbuds and their case dials represent distinct
logical functions with independent states, even when sharing a single bridged radio.
"""
from __future__ import annotations

import enum
import logging
import time
from dataclasses import dataclass, field
from typing import Callable, Optional

log = logging.getLogger("orbit.endpoints")


class EndpointState(str, enum.Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ACTIVE = "active"
    ERROR = "error"


class ConnectionTopology(str, enum.Enum):
    INDIRECT_BRIDGED = "indirect_bridged"  # Case dial events relayed via active earbud (CMF Buds Pro 2)
    DIRECT_DUAL_RADIO = "direct_dual_radio"  # Case or dial has its own independent Bluetooth radio (Surface Dial)
    EARBUDS_ONLY = "earbuds_only"  # Earbuds with no physical case dial


@dataclass
class EarbudsEndpoint:
    name: str = ""
    address: str = ""
    state: EndpointState = EndpointState.DISCONNECTED
    battery_level: Optional[int] = None
    volume_level: Optional[float] = None
    is_playing: bool = False
    last_seen: float = 0.0

    @property
    def is_connected(self) -> bool:
        return self.state in (EndpointState.CONNECTED, EndpointState.ACTIVE)


@dataclass
class ChargingCaseEndpoint:
    name: str = ""
    address: str = ""
    state: EndpointState = EndpointState.DISCONNECTED
    topology: ConnectionTopology = ConnectionTopology.INDIRECT_BRIDGED
    battery_level: Optional[int] = None
    dial_active: bool = False
    last_interaction: float = 0.0

    @property
    def is_available(self) -> bool:
        return self.state in (EndpointState.CONNECTED, EndpointState.ACTIVE)


class UnifiedDeviceSession:
    """Combines earbuds and charging case into a synchronized session."""

    def __init__(self, device_id: str, display_name: str, topology: ConnectionTopology = ConnectionTopology.INDIRECT_BRIDGED):
        self.device_id = device_id
        self.display_name = display_name
        self.topology = topology
        self.earbuds = EarbudsEndpoint(name=display_name, address=device_id)
        self.case = ChargingCaseEndpoint(name=f"{display_name} Case Dial", address=device_id, topology=topology)
        self.listeners: list[Callable[[UnifiedDeviceSession], None]] = []

    def add_listener(self, listener: Callable[[UnifiedDeviceSession], None]) -> None:
        if listener not in self.listeners:
            self.listeners.append(listener)

    def remove_listener(self, listener: Callable[[UnifiedDeviceSession], None]) -> None:
        if listener in self.listeners:
            self.listeners.remove(listener)

    def _notify(self) -> None:
        for l in list(self.listeners):
            try:
                l(self)
            except Exception:
                log.exception("session listener error")

    def update_earbuds(self, state: EndpointState, volume: Optional[float] = None, battery: Optional[int] = None, playing: Optional[bool] = None) -> None:
        self.earbuds.state = state
        self.earbuds.last_seen = time.time()
        if volume is not None:
            self.earbuds.volume_level = volume
        if battery is not None:
            self.earbuds.battery_level = battery
        if playing is not None:
            self.earbuds.is_playing = playing

        # In bridged topology, the case dial availability strictly depends on the earbuds link
        if self.topology == ConnectionTopology.INDIRECT_BRIDGED:
            if self.earbuds.is_connected:
                if self.case.state == EndpointState.DISCONNECTED:
                    self.case.state = EndpointState.CONNECTED
            else:
                self.case.state = EndpointState.DISCONNECTED
                self.case.dial_active = False

        self._notify()

    def update_dial_activity(self) -> None:
        self.case.last_interaction = time.time()
        self.case.dial_active = True
        if self.case.state != EndpointState.ACTIVE:
            self.case.state = EndpointState.ACTIVE
            self._notify()

    def set_dial_idle(self) -> None:
        if self.case.dial_active:
            self.case.dial_active = False
            if self.case.state == EndpointState.ACTIVE:
                self.case.state = EndpointState.CONNECTED
            self._notify()

