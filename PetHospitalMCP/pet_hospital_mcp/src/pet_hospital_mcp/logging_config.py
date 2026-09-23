"""JSON logging configuration with sensitive-field redaction."""

import json
import logging
import re
import sys
from typing import Any

_SENSITIVE_FIELDS = re.compile(
    r"(?i)\\b(ownerPhone|owner_addr|ownerAddr|chipNo|chip_no)\\b"
)


def _redact_value(key: str, value: Any) -> Any:
    if _SENSITIVE_FIELDS.search(key) and isinstance(value, str):
        if len(value) > 4:
            return value[:2] + "****" + value[-2:]
        return "****"
    return value


def _redact_dict(data: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    result: dict[str, Any] = {}
    for k, v in data.items():
        full_key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            result[k] = _redact_dict(v, full_key)
        elif _SENSITIVE_FIELDS.search(full_key) and isinstance(v, str):
            result[k] = _redact_value(full_key, v)
        else:
            result[k] = v
    return result


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        data: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt or "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "extra"):
            extra = record.extra
            if isinstance(extra, dict):
                data.update(_redact_dict(extra))
        return json.dumps(data, ensure_ascii=False)


def setup_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter(datefmt="%Y-%m-%dT%H:%M:%S"))
    root = logging.getLogger("pet_hospital_mcp")
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    root.handlers.clear()
    root.addHandler(handler)
    logging.getLogger("mcp").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
