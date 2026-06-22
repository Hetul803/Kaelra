"""Base connector interface + shared time helpers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any


@dataclass
class ConnectorResult:
    provider: str
    connected: bool
    data: Any = field(default_factory=dict)
    error: str | None = None


class BaseConnector(ABC):
    """Contract every skill connector must satisfy.

    Real OAuth connectors will implement the same methods; only the data
    source changes. The rest of Kaelra depends solely on this interface.
    """

    provider: str = "base"
    name: str = "Base"

    @abstractmethod
    async def fetch(self, user_id: str, profile: dict) -> ConnectorResult:
        """Return the connector's data for the given user."""
        raise NotImplementedError


# --------------------------- time helpers ---------------------------

def _local_now() -> datetime:
    return datetime.now(timezone.utc)


def at_time(hour: int, minute: int = 0) -> datetime:
    """Today at the given hour/minute (UTC reference for demo)."""
    n = _local_now()
    return n.replace(hour=hour, minute=minute, second=0, microsecond=0)


def fmt_time(dt: datetime) -> str:
    return dt.strftime("%-I:%M %p")
