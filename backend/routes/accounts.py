"""Connected accounts routes."""

from fastapi import APIRouter, Depends, HTTPException

from config import get_db
from models import AccountConnectRequest
from auth import get_current_user
from utils import now_iso, clean_docs
from services.seed import provision_defaults
from services.audit import log_event

router = APIRouter()


@router.get("/accounts")
async def list_accounts(user: dict = Depends(get_current_user)):
    db = get_db()
    await provision_defaults(user["id"])
    docs = await db.connected_accounts.find({"user_id": user["id"]}).to_list(100)
    return clean_docs(docs)


@router.put("/accounts/{provider}")
async def update_account(provider: str, req: AccountConnectRequest, user: dict = Depends(get_current_user)):
    db = get_db()
    account = await db.connected_accounts.find_one({"user_id": user["id"], "provider": provider})
    if not account:
        raise HTTPException(status_code=404, detail="Connector not found")
    if account.get("status") == "coming_soon":
        raise HTTPException(status_code=400, detail="This connector is coming soon.")
    new_status = "connected" if req.status == "connected" else "not_connected"
    await db.connected_accounts.update_one(
        {"user_id": user["id"], "provider": provider},
        {"$set": {"status": new_status, "connected_at": now_iso() if new_status == "connected" else None}},
    )
    await log_event(user["id"], f"account.{new_status}", f"{provider} → {new_status}")
    doc = await db.connected_accounts.find_one({"user_id": user["id"], "provider": provider}, {"_id": 0})
    return doc
