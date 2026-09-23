"""MCP server assembly."""

from mcp.server import MCPServer
from starlette.responses import JSONResponse
from starlette.requests import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.applications import Starlette

from pet_hospital_mcp.config import SETTINGS
from pet_hospital_mcp.tools.list_pets import list_pets

# We advertise an older protocol version so the MCP client uses
# role: "function" instead of role: "tool" for tool results.
# Newer model APIs may not support role: "tool".
ADVERTISED_PROTOCOL = "2025-11-25"


class ProtocolVersionMiddleware(BaseHTTPMiddleware):
    """Add MCP protocol version header to all responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["mcp-protocol-version"] = ADVERTISED_PROTOCOL
        return response


def create_app() -> MCPServer:
    server = MCPServer(
        name="pet-hospital-mcp",
        title="宠物医院 MCP 服务",
        description="通过 MCP 协议暴露宠物医院 REST API 能力给 AI Agent",
        version="1.0.0",
    )

    server.add_tool(
        list_pets,
        name="list_pets",
        description=(
            "查询宠物医院的患者档案列表。支持全文检索、按字段过滤、"
            "按总花费区间筛选、排序和分页。"
        ),
        structured_output=False,
    )

    @server.custom_route("/health", methods=["GET"])
    async def health_check(request: Request) -> JSONResponse:
        return JSONResponse({
            "status": "healthy",
            "mcp_protocol": ADVERTISED_PROTOCOL,
            "sdk_version": "mcp==2.0.0",
            "transport": "streamable-http",
            "stateless": True,
        })

    return server


def get_starlette_app():
    server = create_app()
    raw_app = server.streamable_http_app(
        streamable_http_path="/mcp",
        json_response=True,
        stateless_http=True,
    )
    # Wrap with protocol version middleware
    return ProtocolVersionMiddleware(raw_app)


async def run_async() -> None:
    import uvicorn

    app = get_starlette_app()
    config = uvicorn.Config(
        app,
        host=SETTINGS.mcp_host,
        port=SETTINGS.mcp_port,
        log_level="info",
    )
    server = uvicorn.Server(config)
    await server.serve()
