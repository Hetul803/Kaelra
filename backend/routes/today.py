"""Today dashboard, briefing, devices, notifications and audit routes."""

from fastapi import APIRouter, Depends

from config import get_db
from models import DeviceHeartbeat, NotificationCreate
from auth import get_current_user
from utils import new_id, now_iso, clean_doc, clean_docs
from services.context import build_today_context, build_card_payload
from services.briefing import generate, get_cached
from services.actions import counts
from services.devices import heartbeat, list_devices
from services.audit import log_event

router = APIRouter()


@router.get("/dashboard")
async def dashboard(user: dict = Depends(get_current_user)):
    context = await build_today_context(user)
    cards = build_card_payload(context)
    briefing = await get_cached(user["id"])
    action_counts = await counts(user["id"])
    devices = await list_devices(user["id"])
    return {
        "profile": context["profile"],
        "cards": cards,
        "briefing": briefing,
        "action_counts": action_counts,
        "devices": devices,
    }


@router.post("/briefing")
async def make_briefing(force: bool = False, user: dict = Depends(get_current_user)):
    briefing = await generate(user, force=force)
    action_counts = await counts(user["id"])
    return {"briefing": briefing, "action_counts": action_counts}


# ----------------------------- Devices -----------------------------
@router.post("/devices/heartbeat")
async def device_heartbeat(req: DeviceHeartbeat, user: dict = Depends(get_current_user)):
    return await heartbeat(user["id"], req.device_id, req.name or "This device", req.kind, req.voice_enabled)


@router.get("/devices")
async def devices(user: dict = Depends(get_current_user)):
    return await list_devices(user["id"])


# --------------------------- Notifications -------------------------
@router.get("/notifications")
async def get_notifications(user: dict = Depends(get_current_user)):
    db = get_db()
    docs = await db.notifications.find({"user_id": user["id"]}).sort("created_at", -1).to_list(100)
    return clean_docs(docs)


@router.post("/notifications")
async def create_notification(req: NotificationCreate, user: dict = Depends(get_current_user)):
    db = get_db()
    doc = {
        "id": new_id(),
        "user_id": user["id"],
        "title": req.title,
        "body": req.body,
        "type": req.type,
        "scheduled_for": req.scheduled_for,
        "status": "scheduled",
        "read": False,
        "created_at": now_iso(),
    }
    await db.notifications.insert_one(doc)
    await log_event(user["id"], "notification.created", f"Created reminder: {req.title}")
    return clean_doc(doc)


@router.put("/notifications/{notification_id}/read")
async def mark_read(notification_id: str, user: dict = Depends(get_current_user)):
    db = get_db()
    await db.notifications.update_one({"user_id": user["id"], "id": notification_id}, {"$set": {"read": True}})
    return {"ok": True}


@router.delete("/notifications/{notification_id}")
async def delete_notification(notification_id: str, user: dict = Depends(get_current_user)):
    db = get_db()
    await db.notifications.delete_one({"user_id": user["id"], "id": notification_id})
    return {"ok": True}


# ----------------------------- Audit -------------------------------
@router.get("/audit")
async def audit_log(user: dict = Depends(get_current_user)):
    db = get_db()
    docs = await db.audit_log.find({"user_id": user["id"]}).sort("created_at", -1).to_list(200)
    return clean_docs(docs)
