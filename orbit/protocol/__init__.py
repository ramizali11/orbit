"""Orbit Protocol Abstraction Layer for Windows & Desktop.

Provides extensible protocol adapters for rotary earbuds cases, BLE HID dials,
and custom GATT encoders.
"""
from __future__ import annotations

from enum import Enum
from typing import Callable, Optional, Set
from orbit.core.events import InputEvent


class ProtocolCapability(str, Enum):
    ROTATE = "rotate"
    CLICK = "click"
    DOUBLE_CLICK = "double_click"
    TRIPLE_CLICK = "triple_click"
    HOLD = "hold"
    BATTERY_QUERY = "battery_query"


class ProtocolAdapter:
    """Base interface for all physical dial communication protocols."""

    id: str = "base"
    display_name: str = "Base Adapter"
    capabilities: Set[ProtocolCapability] = set()

    def __init__(self, target_identifier: str = ""):
        self.target_identifier = target_identifier
        self._emit: Optional[Callable[[InputEvent], None]] = None

    @property
    def is_available(self) -> bool:
        return True

    def start(self, emit: Callable[[InputEvent], None]) -> None:
        self._emit = emit

    def stop(self) -> None:
        self._emit = None

    def set_passthrough(self, enabled: bool) -> None:
        pass

    def set_duck(self, factor: Optional[float]) -> None:
        pass

    def describe(self) -> str:
        return f"{self.display_name} on {self.target_identifier or 'default'}"

