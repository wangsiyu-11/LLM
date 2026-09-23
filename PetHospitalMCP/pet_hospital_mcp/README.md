# 宠物医院 MCP 服务

将 [Pet Hospital REST API](https://github.com/example/pet-hospital) 的能力通过 MCP 协议暴露给 AI Agent。

## 架构

```
AI Agent (MCP 客户端)
    |
    | Streamable HTTP (/mcp, 无状态)
    |
pet-hospital-mcp (Python MCP Server, SDK 2.x)
    |
    | HTTP REST
    |
pet-hospital (Go REST API)
    |
    `-- data/pet.db
```

## 技术栈

- **SDK**: `mcp==2.0.0` (`MCPServer`, 非 `FastMCP`)
- **协议**: MCP 2026-07-28 (Streamable HTTP, 无状态)
- **REST 客户端**: httpx
- **校验**: Pydantic v2
- **运行**: uvicorn

## 快速开始

### 环境要求

- Python 3.11+
- Go 1.22+ (用于启动上游宠物医院服务)

### 1. 启动 Go REST API

```bash
cd ..  # 回到仓库根目录
go run . -seed
```

默认监听 `http://127.0.0.1:8080`。

### 2. 安装 MCP 服务依赖

```bash
cd pet_hospital_mcp
pip install -e .
```

### 3. 启动 MCP 服务

```bash
cd pet_hospital_mcp
python -m pet_hospital_mcp
```

默认监听 `http://127.0.0.1:8000`。可通过环境变量配置：

| 变量 | 说明 | 默认值 |
|---|---|---|
| `MCP_HOST` | 监听地址 | `127.0.0.1` |
| `MCP_PORT` | 监听端口 | `8000` |
| `PET_HOSPITAL_BASE_URL` | Go REST API 地址 | `http://127.0.0.1:8080` |

### 4. 验证

```bash
# 健康检查
curl http://127.0.0.1:8000/health

# 发现工具列表（MCP 协议端点）
curl -X POST http://127.0.0.1:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"method":"tools/list","params":{},"jsonrpc":"2.0","id":1}'

# 调用 list_pets
curl -X POST http://127.0.0.1:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"method":"tools/call","params":{"name":"list_pets","arguments":{"species":"犬","page":1,"pageSize":10}},"jsonrpc":"2.0","id":2}'
```

### MCP Inspector 验证

```bash
npx @modelcontextprotocol/inspector \
  -e MCP_HOST=127.0.0.1 \
  -e MCP_PORT=8000 \
  -e PET_HOSPITAL_BASE_URL=http://127.0.0.1:8080 \
  python -m pet_hospital_mcp
```

## 端点

| 路径 | 方法 | 说明 |
|---|---|---|
| `/mcp` | POST | MCP Streamable HTTP 端点 |
| `/health` | GET | 健康检查 |

## 当前实现的工具

### `list_pets`

查询宠物医院患者档案列表。

**参数**（全部可选）:

| 参数 | 类型 | 说明 | 校验规则 |
|---|---|---|---|
| `q` | string | 全文检索关键词 | 空格分词，AND 语义 |
| `name` | string | 宠物名 | 精确匹配 |
| `ownerName` | string | 主人姓名 | 精确匹配 |
| `ownerPhone` | string | 主人电话 | 精确匹配 |
| `species` | string | 物种 | 必须是: 犬/猫/兔/鸟/仓鼠/爬宠/其他 |
| `doctor` | string | 主治医生 | 精确匹配 |
| `disease` | string | 疾病/诊断 | 精确匹配 |
| `status` | string | 就诊状态 | 必须是: 待就诊/就诊中/住院中/已康复/慢性病随访 |
| `min` | number | 总花费下限(元) | ≥ 0 |
| `max` | number | 总花费上限(元) | ≥ 0, ≥ min |
| `sortBy` | string | 排序字段 | id/name/ownerName/species/doctor/disease/status/totalCost/visitCount/createdAt/updatedAt |
| `order` | string | 排序方向 | asc/desc |
| `page` | integer | 页码 | ≥ 1 |
| `pageSize` | integer | 每页条数 | 1-500 |

**返回**: `{ items, total, page, pageSize, totalPages, totalCost }`

## 错误格式

```json
{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "可读信息",
        "details": {}
    }
}
```

错误码: `VALIDATION_ERROR`, `BACKEND_TIMEOUT`, `BACKEND_UNAVAILABLE`, `BACKEND_API_ERROR`, `BACKEND_INVALID_RESPONSE`, `INTERNAL_ERROR`

## 运行测试

```bash
cd pet_hospital_mcp
pytest -q
```

## 阶段说明

当前仅实现了阶段一的 `list_pets` 工具。后续阶段会在此结构上扩展更多工具，无需修改现有模块。
