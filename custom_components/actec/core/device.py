from __future__ import annotations

from collections.abc import Callable
from functools import cached_property
import logging
from typing import TYPE_CHECKING

from .const import (
    ACTION_CW,
    ACTION_HSV,
    ACTION_LEVEL,
    ACTION_ONOFF,
    ACTION_POSITION,
    KEY_ENDPOINT,
    KEY_PROPERTY,
    PROP_CW,
    PROP_H,
    PROP_LEVEL,
    PROP_ONOFF,
    PROP_POSITION,
    PROP_S,
    PROP_V,
)
from .types import DeviceInfo, ProductMode
from .unit import AcBaseUnit

if TYPE_CHECKING:
    from .gateway import AcGateway


_LOGGER = logging.getLogger(__name__)


class AcDevice(AcBaseUnit):
    def __init__(
        self, gateway: AcGateway, info: DeviceInfo, suggested_area: str | None
    ) -> None:
        super().__init__(gateway, suggested_area)
        self.product_key: str = info["product_key"]
        self.product_mode: ProductMode | None = info.get("product_mode")
        self.device_id: str = info["device_id"]
        self.device_name: str = info["name"]
        self._state_callbacks: dict[int, set[Callable[[dict], None]]] = {}

    @cached_property
    def unique_id(self) -> str:
        return f"{self.device_id}"

    def add_listener(
        self, endpoint: int, update_callback: Callable[[dict], None]
    ) -> Callable[[], None]:
        callbacks = self._state_callbacks.setdefault(endpoint, set())
        callbacks.add(update_callback)
        return lambda: callbacks.discard(update_callback)

    def update_property(self, body: dict) -> None:
        """Update property of the device.

        body (dict):
            device_id: string
            endpoint: int
            action: A
            property: ActionProperty[A]
        """
        endpoint = body.get(KEY_ENDPOINT)
        prop = body.get(KEY_PROPERTY)
        _LOGGER.debug("设备属性上报: %s#%s %s", self.device_id, endpoint, prop)
        if callbacks := self._state_callbacks.get(endpoint):
            for callback in callbacks:
                callback(body)

    async def fetch_property(self, endpoint: int, action: str) -> None:
        """Fetch property of the device.

        Args:
            endpoint (int): Endpoint of the device
            action (str): Action of the device
        Returns:
            dict: Property of the device

        """
        await self.gateway.get_device_property(self.device_id, endpoint, action)
        # _LOGGER.debug("fetch_property: %s", result)
        # return result

    async def set_onoff(self, endpoint: int, on: bool) -> None:
        """Turn on/off the device.

        Args:
            endpoint (int): Endpoint of the device
            on (bool): True for on, False for off

        """
        await self.gateway.set_device_property(
            self.device_id, endpoint, ACTION_ONOFF, {PROP_ONOFF: 1 if on else 0}
        )

    async def set_brightness(self, endpoint: int, brightness: float) -> None:
        """Set brightness of the light.

        Args:
            endpoint (int): Endpoint of the device
            brightness (float): 0.0-100.0

        """
        await self.gateway.set_device_property(
            self.device_id, endpoint, ACTION_LEVEL, {PROP_LEVEL: brightness}
        )

    async def set_color_temp(self, endpoint: int, color_temp: int) -> None:
        """Set color temperature of the light.

        Args:
            endpoint (int): Endpoint of the device
            color_temp (int): 2700-6500

        """
        await self.gateway.set_device_property(
            self.device_id, endpoint, ACTION_CW, {PROP_CW: color_temp}
        )

    async def set_hsv(
        self, endpoint: int, hue: int, saturation: int, value: int
    ) -> None:
        """Set HSV color of the light.

        Args:
            endpoint (int): Endpoint of the device
            hue (float): 0-360
            saturation (float): 0-1000
            value (float): 0-1000

        """
        await self.gateway.set_device_property(
            self.device_id,
            endpoint,
            ACTION_HSV,
            {PROP_H: hue, PROP_S: saturation, PROP_V: value},
        )

    async def set_position(self, endpoint: int, position: int) -> None:
        """Set position of the curtain.

        Args:
            endpoint (int): Endpoint of the device
            position (int): 0-100

        """
        await self.gateway.set_device_property(
            self.device_id, endpoint, ACTION_POSITION, {PROP_POSITION: position}
        )

    def __repr__(self) -> str:
        """Return a string representation of the device."""
        return f"<AcDevice {self.product_key} {self.device_name} {self.device_id} product_mode:{self.product_mode}>"
