"""Action Queue routes."""

from fastapi import APIRouter, Depends, HTTPException

from models import ActionUpdate, ActionCreate
from auth import get_current_user
from services.actions import list_actions, update_action, create_action

router = APIRouter()


@router.get("/actions")
async def get_actions(status: str | None = None, user: dict = Depends(get_current_user)):
    return await list_actions(user["id"], status)


@router.post("/actions")
async def add_action(req: ActionCreate, user: dict = Depends(get_current_user)):
    created = await create_action(user["id"], req.model_dump(), origin="user")
    if not created:
        raise HTTPException(status_code=400, detail="Could not create action (maybe a duplicate).")
    return created


@router.put("/actions/{action_id}")
async def patch_action(action_id: str, req: ActionUpdate, user: dict = Depends(get_current_user)):
    updated = await update_action(user["id"], action_id, req.model_dump())
    if not updated:
        raise HTTPException(status_code=404, detail="Action not found")
    return updated
