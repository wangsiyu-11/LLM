import os
import json
import httpx

MCP_TOOLS_SCHEMA = []
MCP_TOOLS_MAP = {}

def get_mcp_tools_schema():
    return MCP_TOOLS_SCHEMA

def connect_mcp_servers():
    config_path = os.path.join(os.getcwd(), ".mcp.json")
    if not os.path.exists(config_path):
        print("[MCP] 未找到 .mcp.json")
        return
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    for name, cfg in config.get("mcpServers", {}).items():
        try:
            _connect(name, cfg)
        except Exception as e:
            print(f"[MCP] {name} 连接失败: {e}")

def _connect(name, cfg):
    url = cfg.get("url", "")
    MCP_TOOLS_MAP[name] = {"url": url}
    headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
    resp = httpx.post(url, headers=headers, json={
        "jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "wAgent", "version": "1.0"}}
    }, timeout=30)
    data = resp.json()
    session_id = resp.headers.get("mcp-session-id", "")
    MCP_TOOLS_MAP[name]["session_id"] = session_id
    MCP_TOOLS_MAP[name]["headers"] = headers
    if session_id:
        headers["mcp-session-id"] = session_id
    resp2 = httpx.post(url, headers=headers, json={"jsonrpc": "2.0", "method": "notifications/initialized"}, timeout=30)
    resp3 = httpx.post(url, headers=headers, json={"jsonrpc": "2.0", "id": 2, "method": "tools/list"}, timeout=30)
    tools_data = resp3.json()
    tools = tools_data.get("result", {}).get("tools", [])
    for t in tools:
        MCP_TOOLS_SCHEMA.append({
            "type": "function",
            "function": {
                "name": f"{name}__{t['name']}",
                "description": t.get("description", ""),
                "parameters": t.get("inputSchema", {"type": "object", "properties": {}})
            }
        })
    print(f"[MCP] {name} 已连接，加载 {len(tools)} 个工具")

def call_mcp_tool(full_name, args):
    server_name, tool_name = full_name.split("__", 1)
    srv = MCP_TOOLS_MAP.get(server_name)
    if not srv:
        return f"MCP Server {server_name} 未连接"
    resp = httpx.post(srv["url"], headers=srv["headers"], json={
        "jsonrpc": "2.0", "id": 3, "method": "tools/call",
        "params": {"name": tool_name, "arguments": args}
    }, timeout=60)
    data = resp.json()
    if "result" in data:
        content = data["result"].get("content", [])
        if content:
            return content[0].get("text", str(content))
        return str(data["result"])
    return str(data.get("error", data))
