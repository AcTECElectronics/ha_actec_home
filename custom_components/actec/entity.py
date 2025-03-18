from dataclasses import dataclass

from slugify import slugify

from homeassistant.const import Platform
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity, EntityDescription

from .const import DOMAIN, MANUFACTURER
from .core.device import AcDevice
from .core.group import AcGroup


@dataclass(frozen=True, kw_only=True)
class AcEntityDescription(EntityDescription):
    """Description of an AcTEC entity."""

    PLATFORM: Platform
    has_entity_name: bool = True


class AcDeviceEntity(Entity):
    """Base class for AcTEC device."""

    entity_description: AcEntityDescription
    _attr_should_poll: bool = False

    def __init__(
        self,
        device: AcDevice,
        endpoint: int,
        description: AcEntityDescription,
    ) -> None:
        self.device = device
        self.endpoint = endpoint
        self.entity_description = description
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device.unique_id)},
            manufacturer=MANUFACTURER,
            name=device.device_name,
            suggested_area=device.suggested_area,
        )
        self._attr_unique_id = slugify(
            f"{DOMAIN}_{device.unique_id}_{endpoint}_{description.key}", separator="_"
        )
        self.entity_id = f"{description.PLATFORM}.{self.unique_id}"

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        await super().async_added_to_hass()
        self.async_on_remove(self.device.add_listener(self.endpoint, self.update_state))
        self._attr_available = self.device.gateway.available
        self.async_on_remove(self.device.add_available_listener(self.set_available))

    def update_state(self, body: dict) -> None:
        """Update state."""

    def set_available(self, available: bool) -> None:
        self._attr_available = available
        self.async_write_ha_state()


class AcGroupEntity(Entity):
    """Base class for AcTEC group."""

    entity_description: AcEntityDescription
    _attr_should_poll: bool = False

    def __init__(self, group: AcGroup, description: AcEntityDescription) -> None:
        self.group = group
        self.entity_description = description
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{group.unique_id}")},
            manufacturer=MANUFACTURER,
            name=group.group_name,
            suggested_area=group.suggested_area,
        )
        self._attr_unique_id = f"{DOMAIN}_{group.unique_id}"
        self.entity_id = f"{description.PLATFORM}.{self.unique_id}"

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        await super().async_added_to_hass()
        self._attr_available = self.group.gateway.available
        self.async_on_remove(self.group.add_available_listener(self.set_available))

    def set_available(self, available: bool) -> None:
        self._attr_available = available
        self.async_write_ha_state()
