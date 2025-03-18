from dataclasses import dataclass
from enum import IntEnum
import logging

from homeassistant.components.event import (
    EventDeviceClass,
    EventEntity,
    EventEntityDescription,
)
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import AcConfigEntry
from .core.const import KEY_PROPERTY, PROP_KEY_EVENT
from .core.products import PRODUCTS_INFO
from .entity import AcDeviceEntity, AcEntityDescription

_LOGGER = logging.getLogger(__name__)


class KeyEventTypes(IntEnum):
    single_press = 0x01
    double_press = 0x02
    long_press_down = 0x10
    long_press_up = 0x11
    long_press_hold = 0x12


@dataclass(frozen=True, kw_only=True)
class AcEventDescription(AcEntityDescription, EventEntityDescription):
    """Describes AcTEC event."""

    PLATFORM: Platform = Platform.EVENT


@dataclass(frozen=True, kw_only=True)
class AcKeyEventDescription(AcEventDescription):
    """Describes AcTEC key event."""

    device_class: EventDeviceClass = EventDeviceClass.BUTTON


DESCRIPTIONS: dict[str, list[AcEventDescription]] = {
    "key_event": [
        AcKeyEventDescription(
            key="single_press",
            translation_key="single_press",
            event_types=[
                "single_press",  # 0x01: 单击
            ],
        ),
        AcKeyEventDescription(
            key="double_press",
            translation_key="double_press",
            event_types=[
                "double_press",  # 0x02: 双击
            ],
        ),
        AcKeyEventDescription(
            key="long_press",
            translation_key="long_press",
            event_types=[
                "long_press_down",  # 0x10: 长按按下
                "long_press_up",  # 0x11: 长按弹起
                "long_press_hold",  # 0x12: 长按过程,每隔1s发送
            ],
        ),
    ],
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: AcConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up AcTEC events."""

    gateway = config_entry.runtime_data

    entities: list[AcKeyEvent] = []

    for device in gateway.devices.values():
        if device.product_key in PRODUCTS_INFO:
            for info in PRODUCTS_INFO[device.product_key]:
                if info["platform"] == Platform.EVENT and info["type"] in DESCRIPTIONS:
                    endpoint = info["endpoint"]
                    entities.extend(
                        [
                            AcKeyEvent(device, endpoint, desc)
                            for desc in DESCRIPTIONS[info["type"]]
                        ]
                    )

    async_add_entities(entities)


class AcKeyEvent(AcDeviceEntity, EventEntity):
    """Representation of an KeyEvent."""

    entity_description: AcEventDescription

    def __init__(self, device, endpoint: int, description: AcEventDescription) -> None:
        super().__init__(device, endpoint, description)
        self._attr_translation_placeholders = {"endpoint": str(endpoint)}

    def update_state(self, body: dict) -> None:
        """Update state."""
        prop = body.get(KEY_PROPERTY, {})
        if (value := prop.get(PROP_KEY_EVENT)) in KeyEventTypes:
            event_type = KeyEventTypes(value)
            self._trigger_event(event_type.name)
            self.async_write_ha_state()
