"""Context Builder + scheduler (run-now / run-due) routes."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from config import get_db
from auth import get_current_user
from services import context_builder
from services import scheduler

router = APIRouter()


class ResolveRequest(BaseModel):
    approve: bool


class PauseRequest(BaseModel):
    paused: bool


@router.post("/context/build")
async def build_context(user: dict = Depends(get_current_user)):
    return await context_builder.build(user)


@router.get("/context/status")
async def context_status(user: dict = Depends(get_current_user)):
    return await context_builder.status(user["id"])


@router.get("/context/suggested-memories")
async def suggested_memories(user: dict = Depends(get_current_user)):
    return await context_builder.list_suggested(user["id"])


@router.post("/context/suggested-memories/{sm_id}/resolve")
async def resolve_suggested(sm_id: str, req: ResolveRequest, user: dict = Depends(get_current_user)):
    ok = await context_builder.resolve_suggested(user["id"], sm_id, req.approve)
    if not ok:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    return {"ok": True}


@router.post("/context/pause")
async def pause_indexing(req: PauseRequest, user: dict = Depends(get_current_user)):
    await context_builder.set_paused(user["id"], req.paused)
    return {"ok": True, "paused": req.paused}


@router.delete("/context/indexed")
async def delete_indexed(user: dict = Depends(get_current_user)):
    await context_builder.delete_indexed(user["id"])
    return {"ok": True}


# ----------------------------- Scheduler -----------------------------
@router.post("/routines/{routine_id}/run-now")
async def run_routine_now(routine_id: str, user: dict = Depends(get_current_user)):
    db = get_db()
    routine = await db.routines.find_one({"user_id": user["id"], "id": routine_id})
    if not routine:
        raise HTTPException(status_code=404, detail="Routine not found")
    result = await scheduler.fire_routine(user["id"], routine, user)
    return {"ok": True, "result": result}


@router.post("/scheduler/run-due")
async def run_due(user: dict = Depends(get_current_user)):
    fired = await scheduler.run_due()
    return {"ok": True, "fired": fired}
