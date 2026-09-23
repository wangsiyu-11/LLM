"""list_pets tool implementation."""

import json
import logging
import math
import time
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from pet_hospital_mcp.errors import (
    BackendAPIError,
    BackendInvalidResponse,
    BackendTimeout,
    BackendUnavailable,
    InternalError,
    MCPError,
    ValidationError,
)

import json
from pet_hospital_mcp.rest_client import list_pets as call_list_pets

logger = logging.getLogger("pet_hospital_mcp.tools.list_pets")

VALID_SPECIES = ["犬", "猫", "兔", "鸟", "仓鼠", "爬宠", "其他"]
VALID_STATUS = ["待就诊", "就诊中", "住院中", "已康复", "慢性病随访"]
VALID_SORT_BY = [
    "id", "name", "ownerName", "species", "doctor", "disease",
    "status", "totalCost", "visitCount", "createdAt", "updatedAt",
]
VALID_ORDER = ["asc", "desc"]


class ListPetsInput(BaseModel):
    model_config = {"extra": "forbid", "validate_assignment": True}

    q: str | None = Field(None, description="全文检索关键词")
    name: str | None = Field(None, description="宠物名")
    ownerName: str | None = Field(None, description="主人姓名")
    ownerPhone: str | None = Field(None, description="主人电话")
    species: str | None = Field(None, description="物种")
    doctor: str | None = Field(None, description="主治医生")
    disease: str | None = Field(None, description="疾病/诊断")
    status: str | None = Field(None, description="就诊状态")
    min: float | None = Field(None, ge=0, description="总花费下限")
    max: float | None = Field(None, ge=0, description="总花费上限")
    sortBy: str | None = Field(None, description="排序字段")
    order: str | None = Field(None, description="排序方向")
    page: int | None = Field(None, ge=1, description="页码")
    pageSize: int | None = Field(None, ge=1, le=500, description="每页条数")

    @field_validator("species")
    @classmethod
    def _check_species(cls, v: str | None) -> str | None:
        if v is not None and v not in VALID_SPECIES:
            raise ValueError(f"species 必须是以下之一: {', '.join(VALID_SPECIES)}")
        return v

    @field_validator("status")
    @classmethod
    def _check_status(cls, v: str | None) -> str | None:
        if v is not None and v not in VALID_STATUS:
            raise ValueError(f"status 必须是以下之一: {', '.join(VALID_STATUS)}")
        return v

    @field_validator("sortBy")
    @classmethod
    def _check_sort_by(cls, v: str | None) -> str | None:
        if v is not None and v not in VALID_SORT_BY:
            raise ValueError(f"sortBy 必须是以下之一: {', '.join(VALID_SORT_BY)}")
        return v

    @field_validator("order")
    @classmethod
    def _check_order(cls, v: str | None) -> str | None:
        if v is not None and v not in VALID_ORDER:
            raise ValueError(f"order 必须是 asc 或 desc，收到: {v!r}")
        return v

    @model_validator(mode="after")
    def _check_min_max(self) -> "ListPetsInput":
        if self.min is not None and self.max is not None and self.min > self.max:
            raise ValueError("min 不能大于 max")
        return self


def _parse_pet_item(item: dict[str, Any]) -> dict[str, Any]:
    if item.get("records") is None:
        item["records"] = []
    if item.get("charges") is None:
        item["charges"] = []
    return item


def _error_result(error: MCPError) -> str:
    raise ValueError(json.dumps(error.to_dict(), ensure_ascii=False))


async def list_pets(
    q: str | None = None,
    name: str | None = None,
    ownerName: str | None = None,
    ownerPhone: str | None = None,
    species: str | None = None,
    doctor: str | None = None,
    disease: str | None = None,
    status: str | None = None,
    min: float | None = None,
    max: float | None = None,
    sortBy: str | None = None,
    order: str | None = None,
    page: int | None = None,
    pageSize: int | None = None,
) -> dict[str, Any]:
    """Query the pet hospital patient list."""

    # Reject NaN and Infinity
    for fname, val in [("min", min), ("max", max)]:
        if val is not None and (isinstance(val, float) and (math.isnan(val) or math.isinf(val))):
            return _error_result(ValidationError(f"{fname} 不允许为 NaN 或 Infinity"))

    # Validate with Pydantic model
    try:
        validated = ListPetsInput(
            q=q, name=name, ownerName=ownerName, ownerPhone=ownerPhone,
            species=species, doctor=doctor, disease=disease, status=status,
            min=min, max=max, sortBy=sortBy, order=order, page=page, pageSize=pageSize,
        )
    except ValueError as e:
        return _error_result(ValidationError(str(e)))

    params = validated.model_dump(exclude_none=True)
    start = time.monotonic()

    try:
        data = call_list_pets(params)
    except (BackendTimeout, BackendUnavailable, BackendAPIError, BackendInvalidResponse) as e:
        duration_ms = int((time.monotonic() - start) * 1000)
        logger.info("list_pets error", extra={
            "tool_name": "list_pets", "params": params,
            "status": e.code, "duration_ms": duration_ms,
        })
        return _error_result(e)
    except Exception as e:
        duration_ms = int((time.monotonic() - start) * 1000)
        logger.error("list_pets internal error", extra={
            "tool_name": "list_pets", "params": params,
            "status": "INTERNAL_ERROR", "duration_ms": duration_ms, "error": str(e),
        })
        return _error_result(InternalError(str(e)))

    # Normalize null records/charges
    items_raw = data.get("items") or []
    if not isinstance(items_raw, list):
        return _error_result(BackendInvalidResponse("items 字段类型异常"))
    data["items"] = [_parse_pet_item(item) for item in items_raw]

    duration_ms = int((time.monotonic() - start) * 1000)
    logger.info("list_pets success", extra={
        "tool_name": "list_pets", "params": params,
        "status": "OK", "duration_ms": duration_ms, "total": data.get("total"),
    })

    return json.dumps(data, ensure_ascii=False)
