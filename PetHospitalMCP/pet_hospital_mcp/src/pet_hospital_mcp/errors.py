"""Structured error types for unified MCP error responses."""

from typing import Any


class MCPError(Exception):
    def __init__(self, code: str, message: str, details: dict[str, Any] | None = None) -> None:
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
            }
        }


class ValidationError(MCPError):
    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__("VALIDATION_ERROR", message, details)


class BackendTimeout(MCPError):
    def __init__(self, message: str = "上游服务超时") -> None:
        super().__init__("BACKEND_TIMEOUT", message)


class BackendUnavailable(MCPError):
    def __init__(self, message: str = "上游服务不可用") -> None:
        super().__init__("BACKEND_UNAVAILABLE", message)


class BackendAPIError(MCPError):
    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__("BACKEND_API_ERROR", message, details)


class BackendInvalidResponse(MCPError):
    def __init__(self, message: str = "上游返回数据格式异常") -> None:
        super().__init__("BACKEND_INVALID_RESPONSE", message)


class InternalError(MCPError):
    def __init__(self, message: str = "服务器内部错误") -> None:
        super().__init__("INTERNAL_ERROR", message)
