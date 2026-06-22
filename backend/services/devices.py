"""Device sync service — register heartbeats so Kaelra feels synced everywhere."""

from config import get_db
from utils import new_id, now_iso, clean_doc, clean_docs


async def heartbeat(user_id: str, device_id: str, name: str, kind: str, voice_enabled: bool) -> dict:
    db = get_db()
    existing = await db.devices.find_one({"user_id": user_id, "device_id": device_id})
    if existing:
        await db.devices.update_one(
            {"user_id": user_id, "device_id": device_id},
            {"$set": {"last_active": now_iso(), "name": name, "kind": kind,
                      "voice_enabled": voice_enabled}},
        )
        doc = await db.devices.find_one({"user_id": user_id, "device_id": device_id})
        return clean_doc(doc)
    doc = {
        "id": new_id(),
        "user_id": user_id,
        "device_id": device_id,
        "name": name,
        "kind": kind,
        "voice_enabled": voice_enabled,
        "notifications_enabled": True,
        "created_at": now_iso(),
        "last_active": now_iso(),
    }
    await db.devices.insert_one(doc)
    return clean_doc(doc)


async def list_devices(user_id: str) -> list[dict]:
    db = get_db()
    docs = await db.devices.find({"user_id": user_id}).sort("last_active", -1).to_list(50)
    return clean_docs(docs)
