import asyncio
from asyncio import StreamReader, StreamWriter
from collections.abc import AsyncGenerator, Callable
from datetime import datetime
from enum import Enum
import json
import logging

from .exceptions import NormallyClosed, UnsupportedGateway
from .utils import parse_host

_LOGGER = logging.getLogger(__name__)


class AcClientStatus(Enum):
    DISCONNECTED = 0
    CONNECTED = 1
    RECONNECTING = 2
    CLOSED = 3  # 最终状态


class AcClient:
    def __init__(
        self,
        host: str,
        token: str,
        on_state_changed: Callable[[AcClientStatus], None],
    ) -> None:
        self.host, self.port = parse_host(host)
        self.token = token
        self.reader: StreamReader | None = None
        self.writer: StreamWriter | None = None
        self.status = AcClientStatus.DISCONNECTED
        self.on_state_changed = on_state_changed
        self._retry_count = 0
        self._last_received_time = datetime.now()

    async def connect(self) -> None:
        if self.reader or self.writer:
            _LOGGER.warning("已经连接到网关 %s，不可重复连接。", self.host)
            return

        self._last_received_time = datetime.now()

        # 连接网关
        _LOGGER.debug("正在连接网关 %s", self.host)
        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)

        # 接收“login:”提示
        login_prompt = await self._read_exact(6)
        if login_prompt != b"login:":
            raise UnsupportedGateway(f"错误的登录提示: {login_prompt.decode('utf-8')}")

        # 发送密码
        self.writer.write(b"ACTEC123\r\n")
        await self.writer.drain()
        # 检测连接，没被断开就说明密码正确。
        await self.ensure_alive()

        # 连接成功
        self.status = AcClientStatus.CONNECTED
        self.on_state_changed(self.status)
        self._retry_count = 0
        self.__ping_error_printed = False

    async def close(self, reconnect: bool = False) -> None:
        try:
            self.status = (
                AcClientStatus.RECONNECTING if reconnect else AcClientStatus.CLOSED
            )
            self.on_state_changed(self.status)
            if writer := self.writer:
                self.writer = None
                self.reader = None
                writer.close()
                await writer.wait_closed()
                _LOGGER.debug("客户端关闭连接成功")
        except Exception as e:
            _LOGGER.debug("客户端关闭连接出错 %s", e)

    async def _reconnect(self) -> None:
        await self.close(True)
        await asyncio.sleep(1)
        while self.status != AcClientStatus.CONNECTED:
            try:
                await self.connect()
                _LOGGER.info("重连成功")
            except Exception as e:
                self._retry_count += 1
                wait = 2**self._retry_count
                _LOGGER.error("重连失败，%s秒后重试。%s", wait, e)
                await asyncio.sleep(wait)

    async def take_response(self) -> AsyncGenerator[list[dict] | dict]:
        """接收下一个响应，这里会处理重试逻辑，直到获得一个可用的包再返回给上层."""
        while True:
            try:
                yield await self._take_response()
                self._last_received_time = datetime.now()
            except ConnectionError as e:
                if self.status == AcClientStatus.RECONNECTING:
                    # _LOGGER.debug("正在重连，%s", e)
                    await asyncio.sleep(2)
                    continue
                if self.status == AcClientStatus.CLOSED:
                    raise NormallyClosed from e
                _LOGGER.error(e)
                await self._reconnect()
            except Exception:
                await self.close()
                raise

    async def _take_response(self) -> list[dict] | dict:
        start_char = (await self._read_exact(1)).decode("utf-8")
        if start_char != "[":
            raise ConnectionError("Invalid start character")

        vendor = (await self._read_exact(2)).decode("utf-8")
        if vendor != "AT":
            raise ConnectionError("Invalid vendor")

        # noinspection PyUnusedLocal
        (await self._read_exact(12)).decode("utf-8")
        # _LOGGER.debug(mac)
        length_str = (await self._read_exact(4)).decode("utf-8")
        length = int(length_str, 16)
        content = (await self._read_exact(length)).decode("utf-8")
        end_char = (await self._read_exact(1)).decode("utf-8")

        if end_char != "]":
            raise ConnectionError("Invalid end character")

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise ConnectionError("Invalid JSON content") from e

    __ping_error_printed = False

    async def loop_ping(self):
        while self.status != AcClientStatus.CLOSED:
            try:
                await asyncio.sleep(25)
                await self.send_ping()
            except Exception as e:
                if self.__ping_error_printed:
                    _LOGGER.error("PING ERROR: %s", e)
                    self.__ping_error_printed = True

    async def send_ping(self) -> None:
        now = datetime.now()
        if (now - self._last_received_time).total_seconds() > 85:
            _LOGGER.error("长时间未收到网关数据，尝试重连")
            await self._reconnect()
            return
        await self.send_command([{"namespace": "system", "command": "ping"}, {}])

    async def get_ha_report(self):
        await self.send_command(
            [{"namespace": "ha", "command": "get"}, {"action": "report"}]
        )
        response = await self._take_response()
        _LOGGER.debug("<= %s", response)
        return response

    async def send_command(self, data: list[dict]) -> None:
        if not self.writer:
            raise ConnectionError("尚未与网关建立连接")

        content: str = json.dumps(data, separators=(",", ":"))  # 转为 JSON 格式
        message: bytes = f"[AT{self.token}{len(content):04X}{content}]".encode()
        try:
            # _LOGGER.debug("=> %s", content)
            _LOGGER.debug("=> %s", message)
            self.writer.write(message)
            await self.writer.drain()
        except Exception as e:
            _LOGGER.error("[发送失败] %s", e)
            raise

    async def _read_exact(self, length: int) -> bytes:
        """从流中精确读取指定长度的数据."""
        if not self.reader:
            raise ConnectionError("尚未与网关建立连接")
        data = b""
        while len(data) < length:
            packet = await self.reader.read(length - len(data))
            if not packet:
                raise ConnectionError("连接已被关闭")
            data += packet
        return data

    async def ensure_alive(self):
        await asyncio.sleep(0.5)
        if not self.writer or not self.reader:
            _LOGGER.debug("ensure_alive, no writer or no reader")
            await self._reconnect()
        elif self.writer.is_closing():
            _LOGGER.debug("ensure_alive, writer is closing")
            await self._reconnect()
        elif self.reader.at_eof():
            _LOGGER.debug("ensure_alive, reader at eof")
            await self._reconnect()
        else:
            _LOGGER.debug("ensure_alive.")
