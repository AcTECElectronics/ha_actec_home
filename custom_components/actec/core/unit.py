from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .gateway import AcGateway


class AcBaseUnit:
    def __init__(self, gateway: AcGateway, suggested_area: str | None) -> None:
        self.gateway = gateway
        self.suggested_area = suggested_area
        self._available_callbacks: set[Callable[[bool], None]] = set()

    def add_available_listener(
        self, available_callback: Callable[[bool], None]
    ) -> Callable[[], None]:
        self._available_callbacks.add(available_callback)
        return lambda: self._available_callbacks.discard(available_callback)

    def set_available(self, available: bool) -> None:
        for callback in self._available_callbacks:
            callback(available)
