"""HTTP client for the pet hospital Go REST API."""

import json
import time
from typing import Any

import httpx

from pet_hospital_mcp.config import SETTINGS
from pet_hospital_mcp.errors import (
    BackendAPIError,
    BackendInvalidResponse,
    BackendTimeout,
    BackendUnavailable,
)

MAX_RETRIES = 2
REQUEST_TIMEOUT = 10.0


def _call_with_retry(method: str, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    url = f"{SETTINGS.pet_hospital_base_url.rstrip('/')}{path}"
    last_exc: Exception | None = None

    for attempt in range(MAX_RETRIES + 1):
        try:
            with httpx.Client(timeout=httpx.Timeout(REQUEST_TIMEOUT)) as client:
                response = client.request(method, url, params=params)
        except httpx.TimeoutException as e:
            last_exc = e
            if attempt < MAX_RETRIES:
                time.sleep(0.3 * (attempt + 1))
                continue
            raise BackendTimeout()
        except httpx.ConnectError as e:
            last_exc = e
            if attempt < MAX_RETRIES:
                time.sleep(0.3 * (attempt + 1))
                continue
            raise BackendUnavailable(f"无法连接上游服务: {e}")
        except httpx.HTTPError as e:
            last_exc = e
            if attempt < MAX_RETRIES:
                time.sleep(0.3 * (attempt + 1))
                continue
            raise BackendUnavailable(f"HTTP 请求异常: {e}")

        try:
            body: dict[str, Any] = response.json()
        except (json.JSONDecodeError, ValueError) as e:
            raise BackendInvalidResponse(f"JSON 解析失败: {e}")

        go_code: int = body.get("code", 0)
        if go_code >= 400:
            msg = body.get("message", "未知上游错误")
            raise BackendAPIError(msg, {"http_status": response.status_code, "go_code": go_code})

        return body

    raise BackendUnavailable(f"重试 {MAX_RETRIES} 次后仍然失败: {last_exc}")


def list_pets(params: dict[str, Any]) -> dict[str, Any]:
    clean = {k: v for k, v in params.items() if v is not None}
    resp = _call_with_retry("GET", "/api/v1/pets", params=clean)
    data = resp.get("data")
    if data is None:
        raise BackendInvalidResponse("上游返回缺少 data 字段")
    if not isinstance(data, dict):
        raise BackendInvalidResponse("上游 data 字段类型异常")
    return data
