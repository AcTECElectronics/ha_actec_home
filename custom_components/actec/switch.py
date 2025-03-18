from dataclasses import dataclass
import logging
from typing import Any

from homeassistant.components.switch import (
    SwitchDeviceClass,
    SwitchEntity,
    SwitchEntityDescription,
)
from homeassistant.const import STATE_OFF, STATE_ON, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.typing import UndefinedType

from . import AcConfigEntry
from .core.const import ACTION_ONOFF, KEY_PROPERTY, PROP_ONOFF
from .core.products import PRODUCTS_INFO
from .core.types import GroupType, ProductMode
from .entity import AcDeviceEntity, AcEntityDescription, AcGroupEntity

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class AcSwitchDescription(AcEntityDescription, SwitchEntityDescription):
    """Describes AcTEC switch."""

    PLATFORM: Platform = Platform.SWITCH
    name: str | UndefinedType | None = None


DESCRIPTIONS = {
    "switch": AcSwitchDescription(key="switch", device_class=SwitchDeviceClass.SWITCH),
    "outlet": AcSwitchDescription(key="outlet", device_class=SwitchDeviceClass.OUTLET),
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: AcConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up AcTEC switches."""

    gateway = config_entry.runtime_data

    entities: list[AcDeviceSwitch | AcGroupSwitch] = []

    for device in gateway.devices.values():
        if device.product_key == "768" and device.product_mode == ProductMode.ON_OFF:
            entities.append(AcDeviceSwitch(device, 2, DESCRIPTIONS["switch"]))
            entities.append(AcDeviceSwitch(device, 3, DESCRIPTIONS["switch"]))
        elif device.product_key in PRODUCTS_INFO:
            entities.extend(
                [
                    AcDeviceSwitch(device, info["endpoint"], DESCRIPTIONS[info["type"]])
                    for info in PRODUCTS_INFO[device.product_key]
                    if info["platform"] == Platform.SWITCH
                    and info["type"] in DESCRIPTIONS
                ]
            )
        else:
            _LOGGER.debug("Unsupported device: %s", device)

    entities.extend(
        [
            AcGroupSwitch(group, DESCRIPTIONS["switch"])
            for group in gateway.groups.values()
            if group.group_type == GroupType.ON_OFF
        ]
    )

    async_add_entities(entities)


class AcBaseSwitch(SwitchEntity, RestoreEntity):
    """Base class for AcTEC switch."""

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        await super().async_added_to_hass()
        if last_state := await self.async_get_last_state():
            if last_state.state == STATE_ON:
                self._attr_is_on = True
            elif last_state.state == STATE_OFF:
                self._attr_is_on = False


class AcDeviceSwitch(AcDeviceEntity, AcBaseSwitch):
    """Representation of a Switch."""

    entity_description: AcSwitchDescription

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        await super().async_added_to_hass()
        await self.device.fetch_property(self.endpoint, ACTION_ONOFF)

    def update_state(self, body: dict) -> None:
        """Update state."""
        prop = body.get(KEY_PROPERTY, {})
        if PROP_ONOFF in prop:
            self._attr_is_on = bool(prop[PROP_ONOFF])
            self.async_write_ha_state()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        await self.device.set_onoff(self.endpoint, True)
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        await self.device.set_onoff(self.endpoint, False)
        self._attr_is_on = False
        self.async_write_ha_state()


class AcGroupSwitch(AcGroupEntity, AcBaseSwitch):
    """Representation of a Switch Group."""

    entity_description: AcSwitchDescription

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        await self.group.set_onoff(True)
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        await self.group.set_onoff(False)
        self._attr_is_on = False
        self.async_write_ha_state()
