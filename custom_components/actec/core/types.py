from enum import IntEnum
from typing import TypedDict


class ProductMode(IntEnum):
    ON_OFF = 1
    BRIGHTNESS = 2
    RGB = 3
    RGB_COLOR_TEMP = 4
    COLOR_TEMP = 5
    CURTAIN = 6
    KEY = 7  # 按键
    SENSOR = 8  # PIR传感器


class GroupType(IntEnum):
    ON_OFF = 1
    BRIGHTNESS = 2
    COLOR_TEMP = 3
    RGB_COLOR_TEMP = 4
    CURTAIN = 5


class ProductKeyType(IntEnum):
    PUSH_BUTTON = 0
    SINGLE_SWITCH = 1


class DeviceInfo(TypedDict):
    name: str
    device_id: str
    product_key: str
    product_mode: ProductMode | None
    product_channel: int | None
    product_key_type: ProductKeyType | None


class SceneInfo(TypedDict):
    name: str
    scene_id: int


class GroupInfo(TypedDict):
    name: str
    group_id: int
    group_type: GroupType


class RoomInfo(TypedDict):
    name: str
    devices: list[DeviceInfo]
    scenes: list[SceneInfo]
    groups: list[GroupInfo]


class FloorInfo(TypedDict):
    floor_name: str
    rooms: list[RoomInfo]
