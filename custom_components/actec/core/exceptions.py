class NormallyClosed(Exception):
    """正常关闭连接."""

    def __init__(self, message: str = "正常关闭连接") -> None:
        super().__init__(message)


class UnsupportedGateway(Exception):
    """不支持的网关设备."""
