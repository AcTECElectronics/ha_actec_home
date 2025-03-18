from dataclasses import dataclass
import logging

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import AcConfigEntry
from .const import DOMAIN, MANUFACTURER
from .core.scene import AcScene
from .entity import AcEntityDescription

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class AcSceneButtonDescription(AcEntityDescription, ButtonEntityDescription):
    """Describes AcTEC scene button."""

    PLATFORM: Platform = Platform.BUTTON
    key: str = "scene"
    translation_key = "scene"


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: AcConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up AcTEC buttons."""

    gateway = config_entry.runtime_data
    entities = [AcSceneButton(scene) for scene in gateway.scenes.values()]
    async_add_entities(entities)


class AcSceneButton(ButtonEntity):
    """Representation of a Scene Trigger Button."""

    entity_description: AcSceneButtonDescription

    _attr_should_poll: bool = False

    def __init__(self, scene: AcScene) -> None:
        super().__init__()
        self.scene = scene
        description = AcSceneButtonDescription(name=scene.scene_name)
        self.entity_description = description
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{scene.unique_id}")},
            manufacturer=MANUFACTURER,
            suggested_area=scene.suggested_area,
            translation_key="scene_device",
            translation_placeholders={"room_name": scene.room_name},
        )
        self._attr_unique_id = f"{DOMAIN}_{scene.unique_id}"
        self.entity_id = f"{description.PLATFORM}.{self.unique_id}"

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        await super().async_added_to_hass()
        self._attr_available = self.scene.gateway.available
        self.async_on_remove(self.scene.add_available_listener(self.set_available))

    def set_available(self, available: bool) -> None:
        self._attr_available = available
        self.async_write_ha_state()

    async def async_press(self) -> None:
        """Press the button."""
        await self.scene.trigger_scene()
