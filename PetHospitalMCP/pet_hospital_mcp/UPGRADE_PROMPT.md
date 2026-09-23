# 阶段二升级提示

## 新增工具

在 `pet_hospital_mcp/src/pet_hospital_mcp/tools/` 目录下新增模块，格式参考 `list_pets.py`：

```text
tools/
├── __init__.py
├── list_pets.py       # 已完成
├── get_pet.py         # 按 ID 查询单个宠物
├── search_pets.py     # 全文检索
└── ...                # 更多工具
```

## 实现模式

每个新工具应:

1. 定义 Pydantic 输入/输出模型（含 `extra="forbid"` 和业务校验）
2. 实现 `async def tool_name(...)` 函数，返回 `dict` （Content + isError）
3. 在 `server.py` 的 `create_app()` 中通过 `server.add_tool(...)` 注册
4. 复用 `pet_hospital_mcp/rest_client.py` (`_call_with_retry`)
5. 复用 `pet_hospital_mcp/errors.py` 的异常类型
6. 日志中包含 `tool_name`, `params`, `status`, `duration_ms`
7. 敏感字段（ownerPhone, chipNo, ownerAddr）自动脱敏

## 通用工具注册模式（server.py）

```python
server.add_tool(
    my_new_tool,
    name="my_new_tool",
    description="工具描述",
)
```
