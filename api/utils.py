from datetime import datetime


def _parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value)
