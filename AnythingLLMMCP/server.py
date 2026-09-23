"""AnythingLLM MCP Server（MVP）。"""
import os
import httpx
from mcp.server import MCPServer

BASE_URL = os.getenv("ANYTHINGLLM_BASE", "http://localhost:3001").rstrip("/")
API_KEY = os.getenv("ANYTHINGLLM_API_KEY", "")

mcp = MCPServer("anythingllm-mcp")

@mcp.tool()
def ask_first_workspace(question: str) -> str:
    """查询本机 AnythingLLM 第一个工作区。输入任何问题，返回：工作区名称、文件数量、以及 AnythingLLM 的 AI 回答。当用户问'我的工作区有多少个文件''工作区文件数''有几个文件'等问题时，必须使用此工具。"""
    headers = {"Authorization": f"Bearer {API_KEY}"}
    with httpx.Client(base_url=BASE_URL, headers=headers, timeout=(10, 120)) as client:
        workspaces = client.get("/api/v1/workspaces").json().get("workspaces", [])
        if not workspaces:
            return "未找到任何工作区，请先在 AnythingLLM 中创建一个工作区。"
        slug = workspaces[0]["slug"]
        detail = client.get(f"/api/v1/workspace/{slug}").json().get("workspace", {})
        file_count = len(detail.get("documents", []))
        name = detail.get("name", slug)
        chat = client.post(f"/api/v1/workspace/{slug}/chat",
                           json={"message": question, "mode": "chat"}).json()
        answer = chat.get("textResponse", "")
    return (f"工作区：{name}（slug={slug}）\n"
            f"该工作区共有 {file_count} 个文件。\n"
            f"AI 回答：{answer}")
