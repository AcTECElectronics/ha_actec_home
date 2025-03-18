from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
import logging

from homeassistant.components.sensor import (
    RestoreSensor,
    SensorDeviceClass,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import LIGHT_LUX, Platform, UnitOfEnergy, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from . import AcConfigEntry
from .core.const import (
    ACTION_ENERGY,
    ACTION_SENSOR,
    ACTION_TOTAL_ENERGY,
    KEY_PROPERTY,
    PROP_LIGHT_INTENSITY,
    PROP_POWER,
    PROP_TOTAL_ENERGY,
)
from .core.products import PRODUCTS_INFO
from .entity import AcDeviceEntity, AcEntityDescription

SCAN_INTERVAL = timedelta(minutes=1)


_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class AcSensorDescription(AcEntityDescription, SensorEntityDescription):
    """Describes AcTEC sensor."""

    PLATFORM: Platform = Platform.SENSOR
    action: str
    prop: str
    value_fn: Callable[[int], StateType | date | datetime | Decimal]


DESCRIPTIONS = {
    "illuminance": AcSensorDescription(
        key="illuminance",
        translation_key="illuminance",
        device_class=SensorDeviceClass.ILLUMINANCE,
        native_unit_of_measurement=LIGHT_LUX,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        action=ACTION_SENSOR,
        prop=PROP_LIGHT_INTENSITY,
        value_fn=lambda x: x / 100,
    ),
    "power": AcSensorDescription(
        key="power",
        translation_key="power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        action=ACTION_ENERGY,
        prop=PROP_POWER,
        value_fn=lambda x: x / 10,
    ),
    "energy": AcSensorDescription(
        key="energy",
        translation_key="energy",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=3,
        action=ACTION_TOTAL_ENERGY,
        prop=PROP_TOTAL_ENERGY,
        value_fn=lambda x: x / 1000,
    ),
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: AcConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up AcTEC sensors."""

    gateway = config_entry.runtime_data

    entities: list[AcDeviceSensor] = []

    for device in gateway.devices.values():
        if device.product_key in PRODUCTS_INFO:
            for info in PRODUCTS_INFO[device.product_key]:
                if info["platform"] == Platform.SENSOR and info["type"] in DESCRIPTIONS:
                    if info["type"] == "energy":
                        entities.append(
                            AcEnergySensor(
                                device, info["endpoint"], DESCRIPTIONS[info["type"]]
                            )
                        )
                    else:
                        entities.append(
                            AcDeviceSensor(
                                device, info["endpoint"], DESCRIPTIONS[info["type"]]
                            )
                        )

    async_add_entities(entities)


class AcDeviceSensor(AcDeviceEntity, RestoreSensor):
    """Representation of a Sensor."""

    entity_description: AcSensorDescription

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        await super().async_added_to_hass()
        if last_state := await self.async_get_last_sensor_data():
            self._attr_native_value = last_state.native_value
        await self.device.fetch_property(self.endpoint, self.entity_description.action)

    def update_state(self, body: dict) -> None:
        """Update state."""
        prop = body.get(KEY_PROPERTY, {})
        value = prop.get(self.entity_description.prop)
        if value is not None:
            self._attr_native_value = self.entity_description.value_fn(value)


class AcEnergySensor(AcDeviceSensor):
    """Representation of a Sensor for energy."""

    _attr_should_poll = True

    async def async_update(self) -> None:
        """Get the latest energy usage."""
        await self.device.fetch_property(self.endpoint, self.entity_description.action)
