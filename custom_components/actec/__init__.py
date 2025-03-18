"""Home Assistant integration for AcTEC devices."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_MAC, CONF_TOKEN, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import (
    ConfigEntryAuthFailed,
    ConfigEntryError,
    ConfigEntryNotReady,
)
from homeassistant.helpers.device_registry import DeviceEntry

from .config_flow import CONF_AREA_NAME_RULE
from .const import DOMAIN
from .core.gateway import AcGateway

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.COVER,
    Platform.EVENT,
    Platform.LIGHT,
    Platform.SENSOR,
    Platform.SWITCH,
]

type AcConfigEntry = ConfigEntry[AcGateway]


class AcConfigEntryError(ConfigEntryError):
    def __init__(self, translation_key: str) -> None:
        super().__init__(
            translation_domain=DOMAIN,
            translation_key=translation_key,
        )


async def async_setup_entry(hass: HomeAssistant, entry: AcConfigEntry) -> bool:
    """Set up AcTEC devices from a config entry."""

    _LOGGER.debug("async_setup_entry: %s", entry.entry_id)
    # _LOGGER.debug("entry.options: %s", entry.options)

    host = entry.data[CONF_HOST]
    mac = entry.data[CONF_MAC]
    token = entry.data[CONF_TOKEN]
    area_name_rule = entry.options[CONF_AREA_NAME_RULE]
    gateway = AcGateway(host, mac, token)

    entry.runtime_data = gateway

    try:
        await gateway.connect()
    except ConnectionError as e:
        raise ConfigEntryNotReady from e
    except OSError as e:
        if e.errno == 113:
            raise ConfigEntryNotReady from e
        raise AcConfigEntryError("not_supported") from e
    except Exception as e:
        raise AcConfigEntryError("not_supported") from e

    try:
        response = await gateway.get_ha_report()
    except Exception as e:
        raise AcConfigEntryError("not_supported") from e

    head = response[0]
    if not head.get("success"):
        # 未同意授权
        raise ConfigEntryAuthFailed

    body = response[1] if len(response) > 1 else {}
    if "integrated_list" not in body:
        raise AcConfigEntryError("data_format_error")

    try:
        gateway.init_devices(body["integrated_list"], area_name_rule)
    except Exception as e:
        raise AcConfigEntryError("data_format_error") from e

    await gateway.ensure_alive()

    entry.async_create_background_task(hass, gateway.start_main_loop(), "main")
    entry.async_create_background_task(hass, gateway.start_ping_loop(), "ping")

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(entry_update_listener))

    return True


async def entry_update_listener(hass: HomeAssistant, entry: AcConfigEntry) -> None:
    """Handle updates to the config entry options."""
    # https://developers.home-assistant.io/docs/config_entries_options_flow_handler/#signal-updates
    _LOGGER.debug("[%s] Update options: %s", entry.entry_id, entry.options)
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: AcConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("async_unload_entry: %s", entry.entry_id)
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if gateway := entry.runtime_data:
        await gateway.close()
    return unload_ok


async def async_remove_config_entry_device(
    hass: HomeAssistant, config_entry: AcConfigEntry, device_entry: DeviceEntry
) -> bool:
    """Remove a device from a config entry."""
    # reference: https://developers.home-assistant.io/docs/device_registry_index/#removing-devices
    _LOGGER.debug("[%s] Remove device: %s", config_entry.entry_id, device_entry.id)
    return True
