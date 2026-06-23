"""Auth, profile, onboarding, settings and privacy routes."""

from fastapi import APIRouter, Depends, HTTPException

from config import get_db, DEMO_EMAIL, DEMO_PASSWORD
from models import SignupRequest, LoginRequest, OnboardingRequest, SettingsUpdate
from auth import hash_password, verify_password, create_token, get_current_user
from utils import new_id, now_iso, clean_doc
from services.seed import provision_defaults
from services.audit import log_event

router = APIRouter()


def _public_user(user: dict) -> dict:
    return {k: v for k, v in user.items() if k != "password"}


@router.post("/auth/signup")
async def signup(req: SignupRequest):
    db = get_db()
    if await db.users.find_one({"email": req.email.lower()}):
        raise HTTPException(status_code=400, detail="An account with this email already exists.")
    user_id = new_id()
    user = {
        "id": user_id,
        "email": req.email.lower(),
        "password": hash_password(req.password),
        "name": req.name or req.email.split("@")[0],
        "onboarded": False,
        "is_demo": False,
        "created_at": now_iso(),
    }
    await db.users.insert_one(user)
    await provision_defaults(user_id)
    await log_event(user_id, "auth.signup", "Account created")
    token = create_token(user_id)
    return {"token": token, "user": clean_doc(_public_user(user))}


@router.post("/auth/login")
async def login(req: LoginRequest):
    db = get_db()
    user = await db.users.find_one({"email": req.email.lower()})
    if not user or not verify_password(req.password, user.get("password", "")):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    token = create_token(user["id"])
    await log_event(user["id"], "auth.login", "Signed in")
    return {"token": token, "user": clean_doc(_public_user(user))}


@router.post("/auth/demo")
async def demo_login():
    db = get_db()
    user = await db.users.find_one({"email": DEMO_EMAIL})
    if not user:
        raise HTTPException(status_code=500, detail="Demo account not provisioned yet.")
    token = create_token(user["id"])
    return {"token": token, "user": clean_doc(_public_user(user))}


@router.get("/auth/me")
async def me(user: dict = Depends(get_current_user)):
    db = get_db()
    profile = await db.profiles.find_one({"user_id": user["id"]})
    return {"user": _public_user(user), "profile": clean_doc(profile)}


@router.post("/onboarding")
async def save_onboarding(req: OnboardingRequest, user: dict = Depends(get_current_user)):
    db = get_db()
    user_id = user["id"]
    profile_doc = {
        "name": req.name,
        "call_me": req.call_me,
        "routine": req.routine,
        "tone": req.tone,
        "interests": req.interests,
        "life_areas": req.life_areas,
        "notifications_enabled": req.notifications_enabled,
        "device_sync": req.device_sync,
        "proactive_briefing": req.proactive_briefing,
        "voice_enabled": True,
        "approval_rules": {"emails": True, "jobs": True, "calendar": True, "files": True, "purchases": True},
        "updated_at": now_iso(),
    }
    existing = await db.profiles.find_one({"user_id": user_id})
    if existing:
        await db.profiles.update_one({"user_id": user_id}, {"$set": profile_doc})
    else:
        await db.profiles.insert_one({"id": new_id(), "user_id": user_id, "created_at": now_iso(), **profile_doc})

    await db.users.update_one({"id": user_id}, {"$set": {"onboarded": True, "name": req.name}})
    await provision_defaults(user_id)

    # Seed goals + key memories from onboarding answers
    for g in req.goals:
        if g.strip():
            await db.goals.insert_one({"id": new_id(), "user_id": user_id, "title": g.strip(),
                                       "description": "", "progress": 0.0, "target_date": None,
                                       "created_at": now_iso()})
    if req.routine:
        await db.memories.insert_one({"id": new_id(), "user_id": user_id, "category": "Work/class schedule",
                                      "content": req.routine, "important": True, "temporary": False,
                                      "created_at": now_iso()})
    for area in req.life_areas:
        if area.strip():
            await db.memories.insert_one({"id": new_id(), "user_id": user_id, "category": "Things to monitor",
                                          "content": f"Keep an eye on: {area.strip()}", "important": False,
                                          "temporary": False, "created_at": now_iso()})
    await log_event(user_id, "onboarding.completed", "Onboarding completed")
    updated = await db.users.find_one({"id": user_id})
    return {"user": clean_doc(_public_user(updated)), "profile": clean_doc(await db.profiles.find_one({"user_id": user_id}))}


@router.put("/settings")
async def update_settings(req: SettingsUpdate, user: dict = Depends(get_current_user)):
    db = get_db()
    changes = {k: v for k, v in req.model_dump().items() if v is not None}
    if changes:
        changes["updated_at"] = now_iso()
        await db.profiles.update_one({"user_id": user["id"]}, {"$set": changes}, upsert=True)
        if "name" in changes:
            await db.users.update_one({"id": user["id"]}, {"$set": {"name": changes["name"]}})
        await log_event(user["id"], "settings.updated", "Updated settings", meta={"fields": list(changes.keys())})
    return clean_doc(await db.profiles.find_one({"user_id": user["id"]}))


@router.get("/privacy/export")
async def export_data(user: dict = Depends(get_current_user)):
    db = get_db()
    uid = user["id"]
    collections = ["profiles", "memories", "goals", "routines", "places", "actions",
                   "notifications", "files", "file_summaries", "messages",
                   "conversation_sessions", "daily_briefings", "audit_log",
                   "connected_accounts", "devices"]
    export = {"user": _public_user(user)}
    for c in collections:
        docs = await db[c].find({"user_id": uid}, {"_id": 0, "text": 0}).to_list(1000)
        export[c] = docs
    await log_event(uid, "privacy.export", "Exported all data")
    return export


@router.delete("/privacy/data")
async def delete_data(user: dict = Depends(get_current_user)):
    db = get_db()
    uid = user["id"]
    collections = ["memories", "goals", "routines", "places", "actions", "notifications",
                   "files", "file_summaries", "messages", "conversation_sessions",
                   "daily_briefings", "audit_log"]
    for c in collections:
        await db[c].delete_many({"user_id": uid})
    await log_event(uid, "privacy.delete", "Deleted all Kaelra-stored data")
    return {"ok": True, "message": "All your data has been deleted."}
