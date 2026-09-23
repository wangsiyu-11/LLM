"""Configuration from environment variables."""

import os


def _resolve_host(default: str) -> str:
    return os.environ.get("MCP_HOST", default)


def _resolve_port(default: int) -> int:
    raw = os.environ.get("MCP_PORT", str(default))
    try:
        return int(raw)
    except (ValueError, TypeError):
        return default


def _resolve_base_url(default: str) -> str:
    return os.environ.get("PET_HOSPITAL_BASE_URL", default)


class Settings:
    __slots__ = ("mcp_host", "mcp_port", "pet_hospital_base_url")

    def __init__(self) -> None:
        self.mcp_host: str = _resolve_host("127.0.0.1")
        self.mcp_port: int = _resolve_port(8000)
        self.pet_hospital_base_url: str = _resolve_base_url("http://127.0.0.1:8080")

    @property
    def mcp_address(self) -> str:
        return f"{self.mcp_host}:{self.mcp_port}"


SETTINGS = Settings()
