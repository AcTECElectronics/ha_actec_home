from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING

from .const import (
    ACTION_CW,
    ACTION_HSV,
    ACTION_LEVEL,
    ACTION_ONOFF,
    ACTION_POSITION,
    PROP_CW,
    PROP_H,
    PROP_LEVEL,
    PROP_ONOFF,
    PROP_POSITION,
    PROP_S,
    PROP_V,
)
from .types import GroupInfo, GroupType
from .unit import AcBaseUnit

if TYPE_CHECKING:
    from .gateway import AcGateway


class AcGroup(AcBaseUnit):
    def __init__(
        self, gateway: AcGateway, info: GroupInfo, suggested_area: str | None
    ) -> None:
        super().__init__(gateway, suggested_area)
        self.group_type: GroupType = info["group_type"]
        self.group_id: int = info["group_id"]
        self.group_name: str = info["name"]

    @cached_property
    def unique_id(self) -> str:
        return f"{self.gateway.mac.replace(':', '')}_group_{self.group_id}"

    async def set_onoff(self, on: bool):
        """Turn on/off the device.

        Args:
            on (bool): True for on, False for off

        """
        await self.gateway.set_group_property(
            self.group_id, ACTION_ONOFF, {PROP_ONOFF: 1 if on else 0}
        )

    async def set_brightness(self, brightness: float):
        """Set brightness of the light.

        Args:
            brightness (float): 0.0-100.0

        """
        await self.gateway.set_group_property(
            self.group_id, ACTION_LEVEL, {PROP_LEVEL: brightness}
        )

    async def set_color_temp(self, color_temp: int):
        """Set color temperature of the light.

        Args:
            color_temp (int): 2700-6500

        """
        await self.gateway.set_group_property(
            self.group_id, ACTION_CW, {PROP_CW: color_temp}
        )

    async def set_hsv(self, hue: float, saturation: float, value: float):
        """Set HSV color of the light.

        Args:
            hue (float): 0.0-360.0
            saturation (float): 0.0-100.0
            value (float): 0.0-100.0

        """
        await self.gateway.set_group_property(
            self.group_id,
            ACTION_HSV,
            {PROP_H: hue, PROP_S: saturation, PROP_V: value},
        )

    async def set_position(self, position: int):
        """Set position of the curtain.

        Args:
            position (int): 0-100

        """
        await self.gateway.set_group_property(
            self.group_id, ACTION_POSITION, {PROP_POSITION: position}
        )
