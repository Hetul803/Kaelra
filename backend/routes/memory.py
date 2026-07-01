"""Memory + consolidation routes."""

from fastapi import APIRouter, Depends

from auth import get_current_user
from config import get_db
from services import memory_consolidation as mc

router = APIRouter()


@router.post("/memory/consolidate")
async def consolidate_now(user: dict = Depends(get_current_user)):
    return await mc.consolidate(user["id"], force=True)


@router.get("/memory/insights")
async def memory_insights(user: dict = Depends(get_current_user)):
    db = get_db()
    uid = user["id"]
    return {
        "total": await db.memories.count_documents({"user_id": uid}),
        "learned": await db.memories.count_documents({"user_id": uid, "learned": True}),
        "consolidated": await db.memories.count_documents({"user_id": uid, "source": "consolidation"}),
        "pending_consolidation": await db.memories.count_documents(
            {"user_id": uid, "learned": True, "consolidated": {"$ne": True}}),
    }
