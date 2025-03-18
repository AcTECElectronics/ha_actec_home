from collections.abc import Callable
from dataclasses import dataclass
import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import STATE_OFF, STATE_ON, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from . import AcConfigEntry
from .core.const import ACTION_SENSOR, KEY_PROPERTY, PROP_PIR_TRIGGER
from .core.products import PRODUCTS_INFO
from .entity import AcDeviceEntity, AcEntityDescription

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class AcBinarySensorDescription(AcEntityDescription, BinarySensorEntityDescription):
    """Describes AcTEC binary sensor."""

    PLATFORM: Platform = Platform.BINARY_SENSOR
    action: str
    prop: str
    value_fn: Callable[[int], bool | None] = lambda x: bool(x)


DESCRIPTIONS = {
    "motion": AcBinarySensorDescription(
        key="motion",
        translation_key="motion",
        device_class=BinarySensorDeviceClass.MOTION,
        action=ACTION_SENSOR,
        prop=PROP_PIR_TRIGGER,
    ),
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: AcConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up AcTEC binary sensors."""

    gateway = config_entry.runtime_data

    entities: list[AcDeviceBinarySensor] = []

    for device in gateway.devices.values():
        if device.product_key in PRODUCTS_INFO:
            entities.extend(
                [
                    AcDeviceBinarySensor(
                        device, info["endpoint"], DESCRIPTIONS[info["type"]]
                    )
                    for info in PRODUCTS_INFO[device.product_key]
                    if info["platform"] == Platform.BINARY_SENSOR
                    and info["type"] in DESCRIPTIONS
                ]
            )

    async_add_entities(entities)


class AcDeviceBinarySensor(AcDeviceEntity, BinarySensorEntity, RestoreEntity):
    """Representation of a binary sensor."""

    entity_description: AcBinarySensorDescription

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        await super().async_added_to_hass()
        if last_state := await self.async_get_last_state():
            if last_state.state == STATE_ON:
                self._attr_is_on = True
            elif last_state.state == STATE_OFF:
                self._attr_is_on = False
        await self.device.fetch_property(self.endpoint, self.entity_description.action)

    def update_state(self, body: dict) -> None:
        """Update state."""
        prop = body.get(KEY_PROPERTY, {})
        if (value := prop.get(self.entity_description.prop)) is not None:
            self._attr_is_on = self.entity_description.value_fn(value)
