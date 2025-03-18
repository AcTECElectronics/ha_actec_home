from abc import abstractmethod
from dataclasses import dataclass
import logging
from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_MODE,
    ATTR_COLOR_TEMP_KELVIN,
    ATTR_HS_COLOR,
    ColorMode,
    LightEntity,
    LightEntityDescription,
)
from homeassistant.const import STATE_OFF, STATE_ON, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.typing import UndefinedType

from . import AcConfigEntry
from .core.const import (
    ACTION_CW,
    ACTION_HSV,
    ACTION_LEVEL,
    ACTION_ONOFF,
    KEY_ACTION,
    KEY_PROPERTY,
    PROP_CW,
    PROP_H,
    PROP_LEVEL,
    PROP_ONOFF,
    PROP_S,
    PROP_V,
)
from .core.device import AcDevice
from .core.group import AcGroup
from .core.products import PRODUCTS_INFO
from .core.types import GroupType, ProductMode
from .entity import AcDeviceEntity, AcEntityDescription, AcGroupEntity

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class AcLightDescription(AcEntityDescription, LightEntityDescription):
    """Describes AcTEC light."""

    PLATFORM: Platform = Platform.LIGHT
    key: str = "light"
    name: str | UndefinedType | None = None


DESCRIPTIONS = {
    "light": AcLightDescription(key="light"),
    "light_group": AcLightDescription(key="light_group", icon="mdi:lightbulb-group"),
}

COLOR_MODES = {
    "brightness": {ColorMode.BRIGHTNESS},
    "color_temp": {ColorMode.COLOR_TEMP},
    "hs": {ColorMode.HS},
    "hs_color_temp": {ColorMode.HS, ColorMode.COLOR_TEMP},
}


def group_type_to_color_modes(group_type: GroupType) -> set[ColorMode]:
    """Convert group type to supported color modes."""
    if group_type == GroupType.BRIGHTNESS:
        return {ColorMode.BRIGHTNESS}
    if group_type == GroupType.COLOR_TEMP:
        return {ColorMode.COLOR_TEMP}
    if group_type == GroupType.RGB_COLOR_TEMP:
        return {ColorMode.HS, ColorMode.COLOR_TEMP}
    return set()


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: AcConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up AcTEC lights."""

    gateway = config_entry.runtime_data

    entities: list[AcDeviceLight | AcGroupLight] = []

    for device in gateway.devices.values():
        if device.product_key == "5120":
            if device.product_mode == ProductMode.BRIGHTNESS:
                color_modes = COLOR_MODES["brightness"]
                entities.append(AcDeviceLight(device, 2, color_modes))
                entities.append(AcDeviceLight(device, 3, color_modes))
            elif device.product_mode == ProductMode.COLOR_TEMP:
                color_modes = COLOR_MODES["color_temp"]
                entities.append(AcDeviceLight(device, 2, color_modes))
            else:
                _LOGGER.debug("Unsupported product_mode: %s", device)
        elif device.product_key == "5121":
            if device.product_mode == ProductMode.BRIGHTNESS:
                color_modes = COLOR_MODES["brightness"]
                entities.append(AcDeviceLight(device, 2, color_modes))
                entities.append(AcDeviceLight(device, 3, color_modes))
                entities.append(AcDeviceLight(device, 4, color_modes))
                entities.append(AcDeviceLight(device, 5, color_modes))
                entities.append(AcDeviceLight(device, 6, color_modes))
                entities.append(AcDeviceLight(device, 7, color_modes))
                entities.append(AcDeviceLight(device, 8, color_modes))
                entities.append(AcDeviceLight(device, 9, color_modes))
            elif device.product_mode == ProductMode.COLOR_TEMP:
                color_modes = COLOR_MODES["color_temp"]
                entities.append(AcDeviceLight(device, 2, color_modes))
                entities.append(AcDeviceLight(device, 4, color_modes))
                entities.append(AcDeviceLight(device, 6, color_modes))
                entities.append(AcDeviceLight(device, 8, color_modes))
            else:
                _LOGGER.debug("Unsupported product_mode: %s", device)
        elif device.product_key in PRODUCTS_INFO:
            entities.extend(
                [
                    AcDeviceLight(device, info["endpoint"], COLOR_MODES[info["type"]])
                    for info in PRODUCTS_INFO[device.product_key]
                    if info["platform"] == Platform.LIGHT
                    and info["type"] in COLOR_MODES
                ]
            )
        else:
            _LOGGER.debug("Unsupported device: %s", device)

    entities.extend(
        [
            AcGroupLight(group, group_type_to_color_modes(group.group_type))
            for group in gateway.groups.values()
            if group.group_type
            in [GroupType.BRIGHTNESS, GroupType.COLOR_TEMP, GroupType.RGB_COLOR_TEMP]
        ]
    )

    async_add_entities(entities)


class AcBaseLight(LightEntity, RestoreEntity):
    """Base class for AcTEC light entities."""

    _attr_max_color_temp_kelvin: int | None = 6500
    _attr_min_color_temp_kelvin: int | None = 2700

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        await super().async_added_to_hass()
        if last_state := await self.async_get_last_state():
            if last_state.state == STATE_ON:
                self._attr_is_on = True
            elif last_state.state == STATE_OFF:
                self._attr_is_on = False
            last_attributes = last_state.attributes
            # _LOGGER.debug("last_attributes: %s", last_attributes)
            if (brightness := last_attributes.get(ATTR_BRIGHTNESS)) is not None:
                self._attr_brightness = brightness
            if (color_mode := last_attributes.get(ATTR_COLOR_MODE)) is not None:
                self._attr_color_mode = color_mode
            if (
                color_temp_kelvin := last_attributes.get(ATTR_COLOR_TEMP_KELVIN)
            ) is not None:
                self._attr_color_temp_kelvin = color_temp_kelvin
            if (hs_color := last_attributes.get(ATTR_HS_COLOR)) is not None:
                self._attr_hs_color = hs_color

    @abstractmethod
    async def device_set_onoff(self, on: bool) -> None:
        pass

    @abstractmethod
    async def device_set_brightness(self, brightness: int) -> None:
        pass

    @abstractmethod
    async def device_set_cw(self, color_temp_kelvin: int) -> None:
        pass

    @abstractmethod
    async def device_set_hsv(self, h: int, s: int, v: int) -> None:
        pass

    def save_brightness(self, brightness: int) -> None:
        """Save brightness."""
        self._attr_is_on = brightness > 0
        self._attr_brightness = brightness

    def save_cw(self, color_temp_kelvin: int) -> None:
        """Save color temperature."""
        self._attr_color_mode = ColorMode.COLOR_TEMP
        self._attr_color_temp_kelvin = color_temp_kelvin

    def save_hsv(self, hs_color: tuple[float, float], brightness: int) -> None:
        """Save HSV color and brightness."""
        self._attr_color_mode = ColorMode.HS
        self._attr_hs_color = hs_color
        self._attr_brightness = brightness

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        _LOGGER.debug("async_turn_on: %s", kwargs)
        if len(kwargs.keys()) == 0:
            await self.device_set_onoff(True)
            self._attr_is_on = True
            self.async_write_ha_state()
            return

        if ATTR_HS_COLOR in kwargs:
            hs_color = kwargs[ATTR_HS_COLOR]
            if ATTR_BRIGHTNESS in kwargs:
                brightness = kwargs[ATTR_BRIGHTNESS]
            elif self.brightness is not None:
                brightness = self.brightness
            else:
                brightness = 127
            await self.device_set_hsv(
                int(hs_color[0]),
                int(hs_color[1] * 10),
                int(brightness / 255 * 1000),
            )
            self.save_hsv(hs_color, brightness)
            self.async_write_ha_state()
            return

        if ATTR_COLOR_TEMP_KELVIN in kwargs:
            color_temp_kelvin = kwargs[ATTR_COLOR_TEMP_KELVIN]
            await self.device_set_cw(color_temp_kelvin)
            self.save_cw(color_temp_kelvin)
            self.async_write_ha_state()
        if ATTR_BRIGHTNESS in kwargs:
            brightness = kwargs[ATTR_BRIGHTNESS]
            await self.device_set_brightness(brightness / 255 * 100)
            self.save_brightness(brightness)
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        _LOGGER.debug("async_turn_off: %s", kwargs)
        await self.device_set_onoff(False)
        self._attr_is_on = False
        self.async_write_ha_state()


class AcDeviceLight(AcDeviceEntity, AcBaseLight):
    """Representation of a Light."""

    def __init__(
        self,
        device: AcDevice | AcGroup,
        endpoint: int,
        supported_color_modes: set[ColorMode],
    ) -> None:
        super().__init__(device, endpoint, DESCRIPTIONS["light"])
        self._attr_supported_color_modes = supported_color_modes
        self._attr_color_mode = next(iter(supported_color_modes), None)

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        await super().async_added_to_hass()
        actions = {ACTION_ONOFF, ACTION_LEVEL}
        if ColorMode.COLOR_TEMP in self.supported_color_modes:
            actions.add(ACTION_CW)
        if ColorMode.HS in self.supported_color_modes:
            actions.add(ACTION_HSV)
        for action in actions:
            await self.device.fetch_property(self.endpoint, action)

    def update_state(self, body: dict) -> None:
        """Update state."""
        action = body.get(KEY_ACTION)
        prop = body.get(KEY_PROPERTY, {})
        if action == ACTION_ONOFF:
            self._attr_is_on = bool(prop[PROP_ONOFF])
        elif action == ACTION_LEVEL:
            self.save_brightness(round(prop[PROP_LEVEL] / 100 * 255))
        elif action == ACTION_CW:
            self.save_cw(prop[PROP_CW])
        elif action == ACTION_HSV:
            self.save_hsv(
                (prop[PROP_H], prop[PROP_S] / 10), round(prop[PROP_V] / 1000 * 255)
            )
        self.async_write_ha_state()

    async def device_set_onoff(self, on: bool) -> None:
        await self.device.set_onoff(self.endpoint, on)

    async def device_set_brightness(self, brightness: int) -> None:
        await self.device.set_brightness(self.endpoint, brightness)

    async def device_set_cw(self, color_temp_kelvin: int) -> None:
        await self.device.set_color_temp(self.endpoint, color_temp_kelvin)

    async def device_set_hsv(self, h: int, s: int, v: int) -> None:
        await self.device.set_hsv(self.endpoint, h, s, v)


class AcGroupLight(AcGroupEntity, AcBaseLight):
    """Representation of a Light Group."""

    def __init__(
        self,
        group: AcGroup,
        supported_color_modes: set[ColorMode],
    ) -> None:
        super().__init__(group, DESCRIPTIONS["light_group"])
        self._attr_supported_color_modes = supported_color_modes
        self._attr_color_mode = next(iter(supported_color_modes), None)

    async def device_set_onoff(self, on: bool) -> None:
        await self.group.set_onoff(on)

    async def device_set_brightness(self, brightness: int) -> None:
        await self.group.set_brightness(brightness)

    async def device_set_cw(self, color_temp_kelvin: int) -> None:
        await self.group.set_color_temp(color_temp_kelvin)

    async def device_set_hsv(self, h: int, s: int, v: int) -> None:
        await self.group.set_hsv(h, s, v)
