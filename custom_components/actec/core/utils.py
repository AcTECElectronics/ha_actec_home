def parse_host(host: str) -> tuple[str, int]:
    """Parse the host string to extract the hostname and port."""
    if ":" in host:
        h, p = host.split(":")
        return h, int(p)
    return host, 8023
