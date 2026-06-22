"""Memory, goals and routines routes (Kaelra's knowledge)."""

from fastapi import APIRouter, Depends, HTTPException

from config import get_db
from models import (MemoryRequest, MemoryUpdate, GoalRequest, GoalUpdate,
                    RoutineRequest, RoutineUpdate)
from auth import get_current_user
from utils import new_id, now_iso, clean_doc, clean_docs
from services.audit import log_event

router = APIRouter()

MEMORY_CATEGORIES = [
    "Personal facts", "Work/class schedule", "Goals", "Preferences",
    "Important people", "Places", "Routines", "Interests",
    "Important documents/files", "Things to monitor",
]


# ----------------------------- Memory -----------------------------
@router.get("/memories")
async def get_memories(category: str | None = None, user: dict = Depends(get_current_user)):
    db = get_db()
    query = {"user_id": user["id"]}
    if category and category != "all":
        query["category"] = category
    docs = await db.memories.find(query).sort("created_at", -1).to_list(500)
    return {"categories": MEMORY_CATEGORIES, "memories": clean_docs(docs)}


@router.post("/memories")
async def add_memory(req: MemoryRequest, user: dict = Depends(get_current_user)):
    db = get_db()
    doc = {"id": new_id(), "user_id": user["id"], "created_at": now_iso(), **req.model_dump()}
    await db.memories.insert_one(doc)
    await log_event(user["id"], "memory.added", f"Remembered: {req.content[:60]}")
    return clean_doc(doc)


@router.put("/memories/{memory_id}")
async def edit_memory(memory_id: str, req: MemoryUpdate, user: dict = Depends(get_current_user)):
    db = get_db()
    changes = {k: v for k, v in req.model_dump().items() if v is not None}
    if not changes:
        raise HTTPException(status_code=400, detail="Nothing to update")
    await db.memories.update_one({"user_id": user["id"], "id": memory_id}, {"$set": changes})
    doc = await db.memories.find_one({"user_id": user["id"], "id": memory_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Memory not found")
    return clean_doc(doc)


@router.delete("/memories/{memory_id}")
async def forget_memory(memory_id: str, user: dict = Depends(get_current_user)):
    db = get_db()
    doc = await db.memories.find_one({"user_id": user["id"], "id": memory_id})
    await db.memories.delete_one({"user_id": user["id"], "id": memory_id})
    if doc:
        await log_event(user["id"], "memory.forgotten", f"Forgot: {doc.get('content', '')[:60]}")
    return {"ok": True}


# ----------------------------- Goals ------------------------------
@router.get("/goals")
async def get_goals(user: dict = Depends(get_current_user)):
    db = get_db()
    return clean_docs(await db.goals.find({"user_id": user["id"]}).sort("created_at", -1).to_list(100))


@router.post("/goals")
async def add_goal(req: GoalRequest, user: dict = Depends(get_current_user)):
    db = get_db()
    doc = {"id": new_id(), "user_id": user["id"], "created_at": now_iso(), **req.model_dump()}
    await db.goals.insert_one(doc)
    await log_event(user["id"], "goal.added", f"Added goal: {req.title}")
    return clean_doc(doc)


@router.put("/goals/{goal_id}")
async def edit_goal(goal_id: str, req: GoalUpdate, user: dict = Depends(get_current_user)):
    db = get_db()
    changes = {k: v for k, v in req.model_dump().items() if v is not None}
    await db.goals.update_one({"user_id": user["id"], "id": goal_id}, {"$set": changes})
    doc = await db.goals.find_one({"user_id": user["id"], "id": goal_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Goal not found")
    return clean_doc(doc)


@router.delete("/goals/{goal_id}")
async def delete_goal(goal_id: str, user: dict = Depends(get_current_user)):
    db = get_db()
    await db.goals.delete_one({"user_id": user["id"], "id": goal_id})
    return {"ok": True}


# ---------------------------- Routines ----------------------------
@router.get("/routines")
async def get_routines(user: dict = Depends(get_current_user)):
    db = get_db()
    return clean_docs(await db.routines.find({"user_id": user["id"]}).sort("created_at", 1).to_list(100))


@router.post("/routines")
async def add_routine(req: RoutineRequest, user: dict = Depends(get_current_user)):
    db = get_db()
    doc = {"id": new_id(), "user_id": user["id"], "created_at": now_iso(), **req.model_dump()}
    await db.routines.insert_one(doc)
    await log_event(user["id"], "routine.added", f"Added routine: {req.name}")
    return clean_doc(doc)


@router.put("/routines/{routine_id}")
async def edit_routine(routine_id: str, req: RoutineUpdate, user: dict = Depends(get_current_user)):
    db = get_db()
    changes = {k: v for k, v in req.model_dump().items() if v is not None}
    await db.routines.update_one({"user_id": user["id"], "id": routine_id}, {"$set": changes})
    doc = await db.routines.find_one({"user_id": user["id"], "id": routine_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Routine not found")
    return clean_doc(doc)


@router.delete("/routines/{routine_id}")
async def delete_routine(routine_id: str, user: dict = Depends(get_current_user)):
    db = get_db()
    await db.routines.delete_one({"user_id": user["id"], "id": routine_id})
    return {"ok": True}
