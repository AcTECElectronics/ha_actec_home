from asyncio import Future
import logging

from .client import AcClient, AcClientStatus
from .device import AcDevice
from .exceptions import NormallyClosed
from .group import AcGroup
from .scene import AcScene
from .types import FloorInfo

_LOGGER = logging.getLogger(__name__)


class AcGateway:
    def __init__(self, host: str, mac: str, token: str) -> None:
        self.mac = mac
        self._client = AcClient(host, token, self._on_state_changed)
        self.devices: dict[str, AcDevice] = {}
        self.scenes: dict[int, AcScene] = {}
        self.groups: dict[int, AcGroup] = {}
        self._pending_device_set: Future | None = None
        self._pending_device_get: dict[(str, int, str), list[Future]] = {}
        self._pending_scene_trigger: Future | None = None
        self._pending_group_set: Future | None = None

    @property
    def available(self) -> bool:
        return self._client.status == AcClientStatus.CONNECTED

    def _on_state_changed(self, status: AcClientStatus) -> None:
        _LOGGER.debug("status => %s", status.name)
        available = status == AcClientStatus.CONNECTED
        for device in self.devices.values():
            device.set_available(available)
        for scene in self.scenes.values():
            scene.set_available(available)
        for group in self.groups.values():
            group.set_available(available)

    async def connect(self) -> None:
        await self._client.connect()

    async def get_ha_report(self):
        # [{'namespace': 'ha', 'response': 'get', 'success': False, 'type': 'none'}]
        return await self._client.get_ha_report()

    def init_devices(self, raw_data: list[FloorInfo], area_name_rule: str) -> None:
        _LOGGER.debug("开始解析设备列表")
        for floor_info in raw_data:
            floor_name = floor_info["floor_name"]
            for room_info in floor_info["rooms"]:
                if area_name_rule == "floor_room":
                    suggested_area = f"{floor_name} {room_info['name']}"
                elif area_name_rule == "room":
                    suggested_area = f"{room_info['name']}"
                elif area_name_rule == "floor":
                    suggested_area = floor_name
                else:
                    suggested_area = None
                for device_info in room_info["devices"]:
                    device = AcDevice(self, device_info, suggested_area)
                    self.devices[device_info["device_id"]] = device
                for scene_info in room_info["scenes"]:
                    scene = AcScene(
                        self,
                        scene_info,
                        f"{floor_name} {room_info['name']}",
                        suggested_area,
                    )
                    self.scenes[scene_info["scene_id"]] = scene
                for group_info in room_info["groups"]:
                    group = AcGroup(self, group_info, suggested_area)
                    self.groups[group_info["group_id"]] = group
        _LOGGER.debug(
            "解析成功, %s 个设备, %s 个场景, %s 个组",
            len(self.devices),
            len(self.scenes),
            len(self.groups),
        )

    async def start_main_loop(self) -> None:
        _LOGGER.debug("start_main_loop")
        try:
            async for response in self._client.take_response():
                _LOGGER.debug("<= %s", response)
                if isinstance(response, list):
                    self._handle_message(
                        response[0], response[1] if len(response) > 1 else {}
                    )
                else:
                    _LOGGER.warning("<= 未处理的消息: %s", response)
        except NormallyClosed:
            _LOGGER.debug("正常关闭，结束主循环")
        except Exception as e:
            _LOGGER.error("出现错误，请尝试重载集成: %s", e)

    def _handle_message(self, head: dict, body: dict) -> None:
        """处理接收到的消息."""
        ns = head.get("namespace")
        resp = head.get("response")
        tp = head.get("type")
        if ns == "device_control" and tp == "device_property":
            device_id = body.get("device_id")
            if device_id in self.devices:
                self.devices[device_id].update_property(body)
            else:
                _LOGGER.warning("未知设备消息 %s", device_id)
        elif ns == "device_control" and resp == "get":
            key = (body["device_id"], body["endpoint"], body["action"])
            if pending := self._pending_device_get.get(key):
                pending.pop(0).set_result(body)
        elif ns == "device_control" and resp == "set":
            if self._pending_device_set:
                self._pending_device_set.set_result(body)
                self._pending_device_set = None
        elif ns == "scene_control" and resp == "trigger":
            if self._pending_scene_trigger:
                self._pending_scene_trigger.set_result(body)
                self._pending_scene_trigger = None
        elif ns == "group_control" and resp == "set":
            if self._pending_group_set:
                self._pending_group_set.set_result(body)
                self._pending_group_set = None
        elif ns == "system" and resp == "ping":
            pass
        else:
            _LOGGER.warning("未处理的消息: %s %s", head, body)

    async def close(self) -> None:
        await self._client.close()

    async def start_ping_loop(self) -> None:
        await self._client.loop_ping()

    async def set_device_property(
        self, device_id: str, endpoint: int, action: str, data: dict
    ) -> None:
        feature = Future()
        self._pending_device_set = feature
        await self._client.send_command(
            [
                {"namespace": "device_control", "command": "set"},
                {
                    "device_id": device_id,
                    "endpoint": endpoint,
                    "action": action,
                    "property": data,
                },
            ]
        )
        return await feature

    async def get_device_property(
        self, device_id: str, endpoint: int, action: str
    ) -> None:
        await self._client.send_command(
            [
                {"namespace": "device_control", "command": "get"},
                {
                    "device_id": device_id,
                    "endpoint": endpoint,
                    "action": action,
                },
            ]
        )

    async def trigger_scene(self, scene_id: int) -> None:
        feature = Future()
        self._pending_scene_trigger = feature
        await self._client.send_command(
            [
                {"namespace": "scene_control", "command": "trigger"},
                {"scene_id": scene_id},
            ]
        )
        return await feature

    async def set_group_property(self, group_id: int, action: str, data: dict) -> None:
        feature = Future()
        self._pending_group_set = feature
        await self._client.send_command(
            [
                {"namespace": "group_control", "command": "set"},
                {
                    "group_id": group_id,
                    "action": action,
                    "property": data,
                },
            ]
        )
        return await feature

    async def ensure_alive(self):
        await self._client.ensure_alive()
