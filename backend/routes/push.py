"""Web Push routes — subscribe/unsubscribe + VAPID public key + test delivery."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from auth import get_current_user
from services import push as push_service

router = APIRouter()


class SubscribeBody(BaseModel):
    subscription: dict
    device_id: str | None = None


class UnsubscribeBody(BaseModel):
    endpoint: str


@router.get("/push/vapid-public-key")
async def vapid_public_key():
    return {"public_key": await push_service.public_key()}


@router.get("/push/status")
async def push_status(user: dict = Depends(get_current_user)):
    return {"subscribed": await push_service.has_subscription(user["id"])}


@router.post("/push/subscribe")
async def subscribe(body: SubscribeBody, user: dict = Depends(get_current_user)):
    ok = await push_service.save_subscription(user["id"], body.subscription, body.device_id)
    return {"ok": ok}


@router.post("/push/unsubscribe")
async def unsubscribe(body: UnsubscribeBody, user: dict = Depends(get_current_user)):
    await push_service.remove_subscription(user["id"], body.endpoint)
    return {"ok": True}


@router.post("/push/test")
async def test_push(user: dict = Depends(get_current_user)):
    sent = await push_service.send_push(
        user["id"], "Kaelra is connected",
        "This is how I'll reach you when something needs you.", url="/", tag="test")
    return {"ok": sent > 0, "sent": sent}
