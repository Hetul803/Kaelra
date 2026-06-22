"""Smart Home skill: simulated controllable devices + home routines.

Clearly SIMULATED for v0 (real device APIs later) but behind a clean interface.
Sensitive devices (locks) are approval-gated: locking/unlocking creates a
pending action instead of acting immediately.
"""

from __future__ import annotations

from config import get_db
from utils import new_id, now_iso, clean_docs, clean_doc
from services.audit import log_event
from services.actions import create_actions

SENSITIVE_KINDS = {"lock"}


async def ensure_seed(user_id: str):
    db = get_db()
    if await db.home_devices.count_documents({"user_id": user_id}) > 0:
        return
    devices = [
        {"name": "Living room lights", "kind": "light", "room": "Living room", "state": {"on": False, "brightness": 70}},
        {"name": "Bedroom lights", "kind": "light", "room": "Bedroom", "state": {"on": False, "brightness": 40}},
        {"name": "Thermostat", "kind": "thermostat", "room": "Home", "state": {"temp": 71, "mode": "auto"}},
        {"name": "Front door", "kind": "lock", "room": "Entry", "state": {"locked": True}},
        {"name": "Security alarm", "kind": "alarm", "room": "Home", "state": {"armed": False}},
    ]
    await db.home_devices.insert_many([{"id": new_id(), "user_id": user_id, "created_at": now_iso(),
                                        "simulated": True, **d} for d in devices])
    routines = [
        {"name": "Good morning", "actions": "Turn on living room lights, set thermostat to 72\u00b0", "enabled": True},
        {"name": "Leaving home", "actions": "Lights off, lock door, arm alarm (asks approval)", "enabled": True},
        {"name": "Good night", "actions": "All lights off, thermostat to 68\u00b0, lock door (asks approval)", "enabled": True},
    ]
    await db.home_routines.insert_many([{"id": new_id(), "user_id": user_id, "created_at": now_iso(), **r} for r in routines])


async def overview(user_id: str) -> dict:
    db = get_db()
    await ensure_seed(user_id)
    devices = clean_docs(await db.home_devices.find({"user_id": user_id}).sort("created_at", 1).to_list(100))
    routines = clean_docs(await db.home_routines.find({"user_id": user_id}).sort("created_at", 1).to_list(50))
    return {"devices": devices, "routines": routines, "simulated": True}


async def set_device_state(user_id: str, device_id: str, new_state: dict) -> dict:
    """Update a device. Locks are approval-gated (don't change immediately)."""
    db = get_db()
    dev = await db.home_devices.find_one({"user_id": user_id, "id": device_id})
    if not dev:
        return {"error": "not_found"}
    if dev["kind"] in SENSITIVE_KINDS:
        # Do NOT change; create a pending approval action instead.
        acts = await create_actions(user_id, [{
            "type": "lock_door_pending_approval",
            "title": f"{'Lock' if new_state.get('locked') else 'Unlock'} {dev['name']}",
            "what": f"Requested to set {dev['name']} -> {'locked' if new_state.get('locked') else 'unlocked'}.",
            "why": "Locks are sensitive — Kaelra needs your approval.",
            "source": "Smart Home", "sensitive": True, "requires_approval": True}], origin="smarthome")
        await log_event(user_id, "home.lock_requested", f"Approval requested for {dev['name']}")
        return {"pending_approval": True, "device": clean_doc(dev), "actions_prepared": len(acts)}
    merged = {**dev.get("state", {}), **new_state}
    await db.home_devices.update_one({"id": device_id}, {"$set": {"state": merged}})
    await log_event(user_id, "home.device_set", f"Set {dev['name']}: {new_state}")
    dev = await db.home_devices.find_one({"id": device_id})
    return {"device": clean_doc(dev)}


async def run_morning_routine(user_id: str) -> dict:
    db = get_db()
    await ensure_seed(user_id)
    # Non-sensitive devices change immediately; locks would require approval.
    await db.home_devices.update_many({"user_id": user_id, "kind": "light", "room": "Living room"},
                                      {"$set": {"state.on": True}})
    await db.home_devices.update_many({"user_id": user_id, "kind": "thermostat"},
                                      {"$set": {"state.temp": 72}})
    await log_event(user_id, "home.morning_routine", "Ran Good Morning routine")
    return await overview(user_id)


async def add_routine(user_id: str, data: dict) -> dict:
    db = get_db()
    doc = {"id": new_id(), "user_id": user_id, "enabled": True, "created_at": now_iso(), **data}
    await db.home_routines.insert_one(doc)
    await log_event(user_id, "home.routine_added", f"Home routine: {data.get('name')}")
    return clean_doc(doc)
