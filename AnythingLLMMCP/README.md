# AnythingLLM MCP Server（MVP）

一个最小的 MCP Server：用 **Python + MCP 2026-07-28 协议**、**streamable-http** 传输，桥接本机安装的 AnythingLLM（`http://localhost:3001`）。

只暴露 **1 个工具**：

| 工具 | 作用 |
|---|---|
| `ask_first_workspace(question)` | 取 AnythingLLM **第一个工作区**，返回它的**文件数量**，并把问题发给该工作区得到 **AI 回答** |

它内部依次调用 AnythingLLM API：
`GET /api/v1/workspaces` → `GET /api/v1/workspace/{slug}`（读 `documents` 长度）→ `POST /api/v1/workspace/{slug}/chat`。

## 前置条件

1. 本机 AnythingLLM 已启动，地址为 `http://localhost:3001`（Swagger 文档：`http://localhost:3001/api/docs/`）。
2. 已在 AnythingLLM 里创建好 API Key，并至少有一个工作区。
3. Python 3.10+。

## 安装

```bash
cd anythingllm-mcp
pip install -r requirements.txt
```

## 配置（环境变量）

```bash
# 必填：在 AnythingLLM 中创建的 API Key
export ANYTHINGLLM_API_KEY="你的-key"

# 选填：AnythingLLM 地址，默认 http://localhost:3001
export ANYTHINGLLM_BASE="http://localhost:3001"
```

## 启动

前台运行（看日志，Ctrl+C 停止）：

```bash
mcp run server.py --transport streamable-http
```

启动后 MCP 端点为 `http://127.0.0.1:8000/mcp`。

> 也可用 `uv run mcp run server.py --transport streamable-http`，无需先装依赖。

后台运行（生成 PID 便于停止）：

```bash
nohup mcp run server.py --transport streamable-http > server.log 2>&1 &
echo $! > server.pid
```

## 停止

- 前台：直接按 `Ctrl+C`。
- 后台：

```bash
kill "$(cat server.pid)"
rm -f server.pid
```

确认 8000 端口已释放：

```bash
lsof -i :8000 || echo "已停止"
```

## 项目级 MCP 配置

本目录的 `.mcp.json` 已配置好项目级 MCP（HTTP 指向本服务）：

```json
{
  "mcpServers": {
    "anythingllm": { "type": "http", "url": "http://127.0.0.1:8000/mcp" }
  }
}
```

在支持项目级 MCP 的客户端（如 Claude Code / Cursor / VS Code MCP 等）中打开本目录，即可识别到 `anythingllm` 这个 HTTP MCP 服务。

## 测试

先按上面启动 MCP 服务，然后在**新的聊天 session** 里问：

> 我的工作区有多少个文件

客户端会调用 `ask_first_workspace`，返回类似：

```
工作区：默认工作区（slug=default-workspace）
该工作区共有 3 个文件。
AI 回答：……
```
