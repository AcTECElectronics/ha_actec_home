from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING

from .types import SceneInfo
from .unit import AcBaseUnit

if TYPE_CHECKING:
    from .gateway import AcGateway


class AcScene(AcBaseUnit):
    def __init__(
        self,
        gateway: AcGateway,
        info: SceneInfo,
        room_name: str,
        suggested_area: str | None,
    ) -> None:
        super().__init__(gateway, suggested_area)
        self.scene_id: int = info["scene_id"]
        self.scene_name: str = info["name"]
        self.room_name: str = room_name

    @cached_property
    def unique_id(self) -> str:
        return f"{self.gateway.mac.replace(':', '')}_scene_{self.scene_id}"

    async def trigger_scene(self) -> None:
        """Trigger the scene."""
        await self.gateway.trigger_scene(self.scene_id)
