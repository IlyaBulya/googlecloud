import os
from datetime import date, timedelta
from typing import Any


def ensure_directory(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def date_range(start_date: str, end_date: str) -> list[str]:
    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)
    dates = []
    current = start
    while current <= end:
        dates.append(current.isoformat())
        current += timedelta(days=1)
    return dates


def safe_get(data: dict[str, Any], *keys: str, default: Any = None) -> Any:
    value = data
    for key in keys:
        if not isinstance(value, dict):
            return default
        value = value.get(key, default)
    return value
