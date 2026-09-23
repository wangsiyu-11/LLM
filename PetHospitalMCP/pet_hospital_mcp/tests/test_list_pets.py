"""Tests for the list_pets tool and MCP server."""

import json
import math
from typing import Any

import httpx
import pytest
import respx

from pet_hospital_mcp.tools.list_pets import (
    VALID_ORDER,
    VALID_SORT_BY,
    VALID_SPECIES,
    VALID_STATUS,
    ListPetsInput,
    list_pets,
)

BASE_URL = "http://127.0.0.1:8080"

_OK_UPSTREAM: dict[str, Any] = {
    "code": 200,
    "message": "ok",
    "data": {
        "items": [
            {
                "id": "PET-000001",
                "name": "\u65fa\u8d22",
                "species": "\u72ac",
                "breed": "\u91d1\u6bdb\u5bfb\u56de\u72ac",
                "gender": "\u516c",
                "ageMonths": 36,
                "color": "\u91d1\u9ec4",
                "chipNo": "CHIP-90001",
                "ownerName": "\u5f20\u4e09",
                "ownerPhone": "13800001111",
                "ownerAddr": "\u5317\u4eac\u5e02\u671d\u9633\u533a",
                "doctor": "\u674e\u533b\u751f",
                "disease": "\u6025\u6027\u80a0\u80c3\u708e",
                "status": "\u5df2\u5eb7\u590d",
                "allergy": "\u9752\u9709\u7d20\u8fc7\u654f",
                "note": "",
                "records": [
                    {
                        "id": "MR-001",
                        "visitDate": "2025-01-12",
                        "doctor": "\u674e\u533b\u751f",
                        "diagnosis": "\u6025\u6027\u80a0\u80c3\u708e",
                        "symptoms": "\u5455\u5410 3 \u6b21\u3001\u8179\u6cfb",
                        "treatment": "\u9759\u8109\u8865\u6db2 + \u6d88\u708e",
                        "prescription": ["\u963f\u83ab\u897f\u6797\u514b\u62c9\u7ef4\u9178"],
                        "weightKg": 28.4,
                        "temperature": 39.2,
                        "followUp": "3 \u5929\u540e\u590d\u68c0",
                        "charge": 860,
                        "createdAt": "2025-01-12T10:00:00",
                    }
                ],
                "charges": [
                    {
                        "id": "CH-001",
                        "item": "\u8840\u5e38\u89c4\u68c0\u67e5",
                        "category": "\u68c0\u67e5",
                        "amount": 180,
                        "doctor": "\u674e\u533b\u751f",
                        "date": "2025-01-12",
                        "note": "",
                    }
                ],
                "totalCost": 1180.0,
                "visitCount": 2,
                "createdAt": "2025-01-12T10:00:00",
                "updatedAt": "2025-01-15T14:00:00",
            }
        ],
        "total": 1,
        "page": 1,
        "pageSize": 20,
        "totalPages": 1,
        "totalCost": 1180.0,
    },
    "time": "2026-09-16T12:00:00",
}


@pytest.mark.asyncio
async def test_list_pets_basic():
    """Verify request path and params are forwarded."""
    with respx.mock(base_url=BASE_URL) as respx_mock:
        route = respx_mock.get("/api/v1/pets").respond(200, json=_OK_UPSTREAM)

        result = await list_pets(
            species="\u72ac", sortBy="totalCost", order="desc", page=1, pageSize=10,
        )

        assert route.called
        req = route.calls[0].request
        assert req.url.path == "/api/v1/pets"
        assert req.url.params.get("species") == "\u72ac"
        assert req.url.params.get("sortBy") == "totalCost"
        assert req.url.params.get("order") == "desc"
        assert req.url.params.get("page") == "1"
        assert req.url.params.get("pageSize") == "10"

        text = json.loads(result)
        assert text["total"] == 1
        assert text["items"][0]["id"] == "PET-000001"
        assert text["page"] == 1
        assert text["pageSize"] == 20
        assert text["totalCost"] == 1180.0


@pytest.mark.asyncio
async def test_list_pets_all_params():
    """All query params forwarded correctly."""
    with respx.mock(base_url=BASE_URL) as respx_mock:
        route = respx_mock.get("/api/v1/pets").respond(200, json=_OK_UPSTREAM)

        await list_pets(
            q="\u80a0\u80c3\u708e", name="\u65fa\u8d22",
            ownerName="\u5f20\u4e09", ownerPhone="13800001111",
            species="\u72ac", doctor="\u674e\u533b\u751f",
            disease="\u80a0\u80c3\u708e", status="\u5df2\u5eb7\u590d",
            min=100.0, max=5000.0, sortBy="totalCost", order="desc",
            page=2, pageSize=50,
        )

        req = route.calls[0].request
        assert req.url.params.get("q") == "\u80a0\u80c3\u708e"
        assert req.url.params.get("name") == "\u65fa\u8d22"
        assert req.url.params.get("ownerName") == "\u5f20\u4e09"
        assert req.url.params.get("ownerPhone") == "13800001111"
        assert req.url.params.get("species") == "\u72ac"
        assert req.url.params.get("doctor") == "\u674e\u533b\u751f"
        assert req.url.params.get("disease") == "\u80a0\u80c3\u708e"
        assert req.url.params.get("status") == "\u5df2\u5eb7\u590d"
        assert req.url.params.get("min") == "100.0"
        assert req.url.params.get("max") == "5000.0"
        assert req.url.params.get("sortBy") == "totalCost"
        assert req.url.params.get("order") == "desc"
        assert req.url.params.get("page") == "2"
        assert req.url.params.get("pageSize") == "50"


@pytest.mark.parametrize(
    "kwargs,expected_error",
    [
        ({"species": "\u6050\u9f99"}, "species \u5fc5\u987b\u662f\u4ee5\u4e0b\u4e4b\u4e00"),
        ({"status": "\u5df2\u6b7b\u4ea1"}, "status \u5fc5\u987b\u662f\u4ee5\u4e0b\u4e4b\u4e00"),
        ({"sortBy": "nonexistent"}, "sortBy \u5fc5\u987b\u662f\u4ee5\u4e0b\u4e4b\u4e00"),
        ({"order": "up"}, "order \u5fc5\u987b\u662f asc \u6216 desc"),
        ({"page": 0}, "greater than or equal to 1"),
        ({"page": -1}, "greater than or equal to 1"),
        ({"pageSize": 0}, "greater than or equal to 1"),
        ({"pageSize": 501}, "less than or equal to 500"),
        ({"pageSize": -1}, "greater than or equal to 1"),
        ({"min": -1}, "greater than or equal to 0"),
        ({"max": -5}, "greater than or equal to 0"),
        ({"min": 100, "max": 50}, "min \u4e0d\u80fd\u5927\u4e8e max"),
    ],
)
@pytest.mark.asyncio
async def test_input_validation_errors(kwargs, expected_error):
    """Validation errors raise ValueError with structured JSON."""
    with pytest.raises(ValueError) as exc_info:
        await list_pets(**kwargs)
    err = json.loads(str(exc_info.value))
    assert err["error"]["code"] == "VALIDATION_ERROR"
    assert expected_error in err["error"]["message"]


@pytest.mark.parametrize(
    "value,field_name",
    [
        (math.nan, "min"),
        (math.inf, "min"),
        (-math.inf, "min"),
        (math.nan, "max"),
        (math.inf, "max"),
    ],
)
@pytest.mark.asyncio
async def test_nan_infinity_rejection(value, field_name):
    """NaN and Infinity should be rejected."""
    kwargs = {field_name: value}
    with pytest.raises(ValueError) as exc_info:
        await list_pets(**kwargs)
    err = json.loads(str(exc_info.value))
    assert err["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_unknown_field_rejected():
    """Extra unknown fields should be rejected by Pydantic model."""
    with pytest.raises(Exception, match="Extra inputs are not permitted"):
        ListPetsInput(**{"unknown_field": "value", "species": "\u72ac"})


@pytest.mark.asyncio
async def test_backend_400():
    """Go API returning 4xx should produce BACKEND_API_ERROR."""
    error_body = {"code": 400, "message": "species \u53c2\u6570\u65e0\u6548", "data": None}
    with respx.mock(base_url=BASE_URL) as respx_mock:
        respx_mock.get("/api/v1/pets").respond(400, json=error_body)

        with pytest.raises(ValueError) as exc_info:
            await list_pets(name="valid-param")
        err = json.loads(str(exc_info.value))
        assert err["error"]["code"] == "BACKEND_API_ERROR"


@pytest.mark.asyncio
async def test_backend_500():
    """Go API returning 5xx should produce BACKEND_API_ERROR."""
    with respx.mock(base_url=BASE_URL) as respx_mock:
        respx_mock.get("/api/v1/pets").respond(500, json={"code": 500, "message": "Internal Server Error"})

        with pytest.raises(ValueError) as exc_info:
            await list_pets()
        err = json.loads(str(exc_info.value))
        assert err["error"]["code"] == "BACKEND_API_ERROR"


@pytest.mark.asyncio
async def test_timeout():
    """Timeout raises BACKEND_TIMEOUT."""
    with respx.mock(base_url=BASE_URL) as respx_mock:
        respx_mock.get("/api/v1/pets").mock(side_effect=httpx.TimeoutException("timeout"))

        with pytest.raises(ValueError) as exc_info:
            await list_pets()
        err = json.loads(str(exc_info.value))
        assert err["error"]["code"] == "BACKEND_TIMEOUT"


@pytest.mark.asyncio
async def test_connection_error():
    """Connection error raises BACKEND_UNAVAILABLE."""
    with respx.mock(base_url=BASE_URL) as respx_mock:
        respx_mock.get("/api/v1/pets").mock(side_effect=httpx.ConnectError("connection refused"))

        with pytest.raises(ValueError) as exc_info:
            await list_pets()
        err = json.loads(str(exc_info.value))
        assert err["error"]["code"] == "BACKEND_UNAVAILABLE"


@pytest.mark.asyncio
async def test_invalid_json():
    """Non-JSON response raises BACKEND_INVALID_RESPONSE."""
    with respx.mock(base_url=BASE_URL) as respx_mock:
        respx_mock.get("/api/v1/pets").respond(200, text="not json")

        with pytest.raises(ValueError) as exc_info:
            await list_pets()
        err = json.loads(str(exc_info.value))
        assert err["error"]["code"] == "BACKEND_INVALID_RESPONSE"


@pytest.mark.asyncio
async def test_missing_data_field():
    """Response without data field raises BACKEND_INVALID_RESPONSE."""
    with respx.mock(base_url=BASE_URL) as respx_mock:
        respx_mock.get("/api/v1/pets").respond(200, json={"code": 200, "message": "ok"})

        with pytest.raises(ValueError) as exc_info:
            await list_pets()
        err = json.loads(str(exc_info.value))
        assert err["error"]["code"] == "BACKEND_INVALID_RESPONSE"


def test_list_pets_input_schema():
    """Input schema has correct field types and constraints."""
    schema = ListPetsInput.model_json_schema()
    props = schema.get("properties", {})
    assert "required" not in schema or len(schema.get("required", [])) == 0
    assert props["species"]["anyOf"]
    assert props["page"]["anyOf"]
    assert props["pageSize"]["anyOf"]
    assert props["min"]["anyOf"]
    assert props["max"]["anyOf"]
    assert schema.get("additionalProperties") is False or schema.get("extra") == "forbid"


def test_list_pets_allowed_values():
    """Allowed values are comprehensive."""
    assert "\u72ac" in VALID_SPECIES
    assert "\u732b" in VALID_SPECIES
    assert "\u5f85\u5c31\u8bca" in VALID_STATUS
    assert "\u5df2\u5eb7\u590d" in VALID_STATUS
    assert "totalCost" in VALID_SORT_BY
    assert "asc" in VALID_ORDER
    assert "desc" in VALID_ORDER


@pytest.mark.asyncio
async def test_null_records_charges():
    """records and charges being null must be normalized to empty lists."""
    upstream = {
        "code": 200,
        "message": "ok",
        "data": {
            "items": [
                {
                    "id": "PET-000002",
                    "name": "\u549c\u549c",
                    "species": "\u732b",
                    "ownerName": "\u674e\u56db",
                    "ownerPhone": "13900002222",
                    "doctor": "\u738b\u533b\u751f",
                    "disease": "\u732b\u761f",
                    "status": "\u4f4f\u9662\u4e2d",
                    "records": None,
                    "charges": None,
                    "totalCost": 0.0,
                    "visitCount": 0,
                    "createdAt": "2026-01-01T00:00:00",
                    "updatedAt": "2026-01-01T00:00:00",
                }
            ],
            "total": 1,
            "page": 1,
            "pageSize": 20,
            "totalPages": 1,
            "totalCost": 0.0,
        },
    }
    with respx.mock(base_url=BASE_URL) as respx_mock:
        respx_mock.get("/api/v1/pets").respond(200, json=upstream)

        result = await list_pets()
        text = json.loads(result)
        item = text["items"][0]
        assert item["records"] == []
        assert item["charges"] == []
