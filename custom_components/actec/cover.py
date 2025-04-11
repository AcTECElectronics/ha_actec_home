from dataclasses import dataclass
import logging
from typing import Any

from homeassistant.components.cover import (
    ATTR_CURRENT_POSITION,
    ATTR_POSITION,
    CoverDeviceClass,
    CoverEntity,
    CoverEntityDescription,
    CoverEntityFeature,
)
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.typing import UndefinedType

from . import AcConfigEntry
from .core.const import ACTION_POSITION, KEY_PROPERTY, PROP_POSITION
from .core.products import PRODUCTS_INFO
from .core.types import GroupType, ProductMode
from .entity import AcDeviceEntity, AcEntityDescription, AcGroupEntity

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class AcCoverDescription(AcEntityDescription, CoverEntityDescription):
    """Describes AcTEC cover."""

    PLATFORM: Platform = Platform.COVER
    key: str = "cover"
    name: str | UndefinedType | None = None


DESCRIPTIONS = {
    "curtain": AcCoverDescription(device_class=CoverDeviceClass.CURTAIN),
    "roller": AcCoverDescription(device_class=CoverDeviceClass.SHADE),
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: AcConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up AcTEC covers."""

    gateway = config_entry.runtime_data

    entities: list[AcDeviceCover | AcGroupCover] = []

    for device in gateway.devices.values():
        if device.product_key == "768":
            if device.product_mode == ProductMode.CURTAIN:
                entities.append(AcDeviceCover(device, 2, DESCRIPTIONS["curtain"]))
            # else: ignore
        elif device.product_key in PRODUCTS_INFO:
            entities.extend(
                [
                    AcDeviceCover(device, info["endpoint"], DESCRIPTIONS[info["type"]])
                    for info in PRODUCTS_INFO[device.product_key]
                    if info["platform"] == Platform.COVER
                    and info["type"] in DESCRIPTIONS
                ]
            )
        else:
            _LOGGER.debug("Unsupported device: %s", device)

    entities.extend(
        [
            AcGroupCover(group, DESCRIPTIONS["curtain"])
            for group in gateway.groups.values()
            if group.group_type == GroupType.CURTAIN
        ]
    )

    async_add_entities(entities)


class AcBaseCover(CoverEntity, RestoreEntity):
    """Base class for AcTEC cover entities."""

    _attr_supported_features: CoverEntityFeature = (
        CoverEntityFeature.OPEN
        | CoverEntityFeature.CLOSE
        | CoverEntityFeature.SET_POSITION
    )

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        await super().async_added_to_hass()
        if last_state := await self.async_get_last_state():
            if ATTR_CURRENT_POSITION in last_state.attributes:
                position = last_state.attributes[ATTR_CURRENT_POSITION]
                self._attr_current_cover_position = position

    @property
    def is_closed(self) -> bool | None:
        """Return if the cover is closed or not."""
        if (current_position := self.current_cover_position) is not None:
            return current_position <= 1
        return None


class AcDeviceCover(AcDeviceEntity, AcBaseCover):
    """Representation of a Cover Device."""

    entity_description: AcCoverDescription

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        await super().async_added_to_hass()
        await self.device.fetch_property(self.endpoint, ACTION_POSITION)

    def update_state(self, body: dict) -> None:
        """Update state."""
        prop = body.get(KEY_PROPERTY, {})
        if PROP_POSITION in prop:
            self._attr_is_opening = False
            self._attr_is_closing = False
            self._attr_current_cover_position = prop[PROP_POSITION]
            self.async_write_ha_state()

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the cover."""
        self._attr_is_opening = True
        self._attr_is_closing = False
        self.async_write_ha_state()
        await self.device.set_position(self.endpoint, 100)
        # self._attr_current_cover_position = 100
        # self.async_write_ha_state()

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close cover."""
        self._attr_is_opening = False
        self._attr_is_closing = True
        self.async_write_ha_state()
        await self.device.set_position(self.endpoint, 0)
        # self._attr_current_cover_position = 0
        # self.async_write_ha_state()

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        """Move the cover to a specific position."""
        target_position = kwargs[ATTR_POSITION]
        self._attr_is_opening = False
        self._attr_is_closing = False
        if (current_position := self.current_cover_position) is not None:
            if target_position > current_position:
                self._attr_is_opening = True
            elif target_position < current_position:
                self._attr_is_closing = True
        self.async_write_ha_state()
        await self.device.set_position(self.endpoint, target_position)
        # self._attr_current_cover_position = target_position
        # self.async_write_ha_state()


class AcGroupCover(AcGroupEntity, AcBaseCover):
    """Representation of a Cover Group."""

    entity_description: AcCoverDescription

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the cover."""
        await self.group.set_position(100)
        self._attr_current_cover_position = 100
        self.async_write_ha_state()

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close cover."""
        await self.group.set_position(0)
        self._attr_current_cover_position = 0
        self.async_write_ha_state()

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        """Move the cover to a specific position."""
        target_position = kwargs[ATTR_POSITION]
        await self.group.set_position(target_position)
        self._attr_current_cover_position = target_position
        self.async_write_ha_state()
