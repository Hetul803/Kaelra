"""Shared helpers: id generation, time, and Mongo (de)serialization."""

import uuid
from datetime import datetime, timezone, date
from typing import Any


def new_id() -> str:
    return str(uuid.uuid4())


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def today_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def serialize(obj: Any) -> Any:
    """Recursively convert a document into JSON-safe primitives.

    Critical for MongoDB + FastAPI: strips ``_id`` and converts datetime/date
    objects to ISO strings so responses never hit the
    'datetime not JSON serializable' pitfall.
    """
    if isinstance(obj, dict):
        return {k: serialize(v) for k, v in obj.items() if k != "_id"}
    if isinstance(obj, list):
        return [serialize(v) for v in obj]
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    return obj


def clean_doc(doc: dict | None) -> dict | None:
    """Serialize a single Mongo doc (or None)."""
    if doc is None:
        return None
    return serialize(doc)


def clean_docs(docs: list[dict]) -> list[dict]:
    return [serialize(d) for d in docs]


async def is_demo_user(user_id: str) -> bool:
    """True only for the seeded demo operator. Used to gate realistic demo/mock
    data so real signups start with a clean slate and fill in from real sources."""
    from config import get_db
    db = get_db()
    u = await db.users.find_one({"id": user_id}, {"is_demo": 1})
    return bool(u and u.get("is_demo"))
