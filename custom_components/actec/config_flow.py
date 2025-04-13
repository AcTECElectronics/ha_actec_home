import logging
import random
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.const import (
    CONF_HOST,
    CONF_MAC,
    CONF_TOKEN,
    MAJOR_VERSION,
    MINOR_VERSION,
)
from homeassistant.core import callback
from homeassistant.helpers.device_registry import format_mac

from .const import DOMAIN
from .core.client import AcClient

if (MAJOR_VERSION, MINOR_VERSION) >= (2025, 2):
    from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo
else:
    from homeassistant.components.zeroconf import ZeroconfServiceInfo

_LOGGER = logging.getLogger(__name__)

CONF_AREA_NAME_RULE = "area_name_rule"


class AcConfigFlow(ConfigFlow, domain=DOMAIN):
    """AcTEC config flow."""

    VERSION = 1
    MINOR_VERSION = 1

    host: str | None = None  # 网关地址
    mac: str | None = None  # 网关mac
    token: str | None = None  # 提供给网关的唯一标识

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle a flow initiated by the user."""
        return self.async_abort(reason="user_step_not_supported")

    async def async_step_zeroconf(self, discovery_info: ZeroconfServiceInfo):
        """Handle a flow initialized by Zeroconf discovery."""
        _LOGGER.debug("async_step_zeroconf: %s", discovery_info)

        properties = discovery_info.properties
        if properties.get("ip") is None or properties.get("mac") is None:
            return self.async_abort(reason="invalid_zeroconf_info")

        self.host = properties["ip"]
        self.mac = format_mac(properties["mac"])

        await self.async_set_unique_id(self.mac)
        self._abort_if_unique_id_configured(updates={CONF_HOST: self.host})

        self.token = "".join(random.choice("0123456789abcdef") for _ in range(12))
        _LOGGER.debug("host: %s, mac: %s my_id: %s", self.host, self.mac, self.token)
        return await self.async_step_pairing()

    async def async_step_pairing(self, user_input: dict[str, Any] | None = None):
        """提示用户点击确定."""
        _LOGGER.debug("async_step_pairing: %s", user_input)
        if user_input is None:
            # zeroconf
            return self.async_show_form(step_id="pairing")
        # 点了确定之后

        # 测试一下连接
        if errors := await _test_connect(self.host, self.token):
            return self.async_show_form(
                step_id="pairing",
                errors=errors,
            )
        return await self.async_step_options()

    async def async_step_options(self, user_input: dict[str, Any] | None = None):
        """选择区域命名规则."""
        _LOGGER.debug("async_step_options: %s", user_input)
        if user_input is None:
            return self.async_show_form(
                step_id="options",
                data_schema=vol.Schema(
                    {
                        vol.Required(
                            CONF_AREA_NAME_RULE,
                            description={"suggested_value": "floor_room"},
                        ): vol.In(
                            {
                                "none": "不同步",
                                "floor_room": "楼层 房间（1层 客厅）",
                                "room": "房间（客厅）",
                                "floor": "楼层（1层）",
                            }
                        ),
                    }
                ),
            )

        area_name_rule = user_input[CONF_AREA_NAME_RULE]
        return self.async_create_entry(
            title=self.host,
            data={
                CONF_HOST: self.host,
                CONF_MAC: self.mac,
                CONF_TOKEN: self.token,
            },
            options={
                CONF_AREA_NAME_RULE: area_name_rule,
            },
        )

    async def async_step_reauth(self, entry_data: dict[str, Any]):
        """Perform reauth upon an API authentication error.

        source: This will always be "SOURCE_REAUTH"
        entry_id: The entry_id of the config entry that needs reauthentication
        unique_id: The unique_id of the config entry that needs reauthentication
        """
        _LOGGER.debug("async_step_reauth: %s", entry_data)
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input: dict[str, Any] | None = None):
        """Dialog that informs the user that reauth is required."""
        _LOGGER.debug("async_step_reauth_confirm: %s", user_input)
        if user_input is None:
            return self.async_show_form(step_id="reauth_confirm")
        if (MAJOR_VERSION, MINOR_VERSION) >= (2024, 11):
            reauth_entry = self._get_reauth_entry()
        else:
            reauth_entry = self.hass.config_entries.async_get_entry(
                self.context["entry_id"]
            )
            assert reauth_entry is not None, "Could not find reauth entry"
        host = reauth_entry.data[CONF_HOST]
        token = reauth_entry.data[CONF_TOKEN]
        if errors := await _test_connect(host, token):
            return self.async_show_form(step_id="reauth_confirm", errors=errors)
        return self.async_update_reload_and_abort(reauth_entry)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(OptionsFlow):
    def __init__(self, config_entry: ConfigEntry) -> None:
        if (MAJOR_VERSION, MINOR_VERSION) < (2024, 12):
            self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        """Manage the options."""

        if user_input is None:
            old_options = self.config_entry.options
            return self.async_show_form(
                step_id="init",
                data_schema=vol.Schema(
                    {
                        vol.Required(
                            CONF_AREA_NAME_RULE,
                            default=old_options[CONF_AREA_NAME_RULE],
                        ): vol.In(
                            {
                                "none": "不同步",
                                "floor_room": "楼层 房间（1层 客厅）",
                                "room": "房间（客厅）",
                                "floor": "楼层（1层）",
                            }
                        ),
                    }
                ),
            )

        area_name_rule = user_input[CONF_AREA_NAME_RULE]
        return self.async_create_entry(data={CONF_AREA_NAME_RULE: area_name_rule})


async def _test_connect(host: str, token: str):
    errors = {}
    client = AcClient(host, token, lambda x: None)
    try:
        await client.connect()
        response = await client.get_ha_report()
        if not response[0].get("success"):
            # 未同意授权
            errors = {
                "base": "请保持app打开状态，然后点击确定。在app中确认分享后，再次点击确定",
            }
    except Exception as e:
        errors = {"base": str(e)}
    finally:
        await client.close()
    return errors
