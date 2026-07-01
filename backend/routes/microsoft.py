"""Microsoft (Outlook / 365) OAuth routes — mirrors the Google flow.

The frontend passes redirect_uri = window.location.origin + "/auth/microsoft".
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from config import microsoft_configured
from auth import get_current_user, create_token
from services import microsoft_oauth

router = APIRouter()


class CallbackRequest(BaseModel):
    code: str
    redirect_uri: str
    state: str | None = None


@router.get("/oauth/microsoft/status")
async def ms_status(user: dict = Depends(get_current_user)):
    return await microsoft_oauth.status(user["id"])


@router.get("/oauth/microsoft/url")
async def ms_url(redirect_uri: str, user: dict = Depends(get_current_user)):
    if not microsoft_configured():
        raise HTTPException(status_code=400, detail="Microsoft is not configured yet. Add MICROSOFT_CLIENT_ID/SECRET.")
    state = create_token(user["id"])
    return {"url": microsoft_oauth.build_auth_url(redirect_uri, state)}


@router.post("/oauth/microsoft/callback")
async def ms_callback(req: CallbackRequest, user: dict = Depends(get_current_user)):
    if not microsoft_configured():
        raise HTTPException(status_code=400, detail="Microsoft is not configured.")
    try:
        result = await microsoft_oauth.exchange_code(user["id"], req.code, req.redirect_uri)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Microsoft connection failed: {e}")
    return {"ok": True, **result}


@router.post("/oauth/microsoft/disconnect")
async def ms_disconnect(email: str | None = None, user: dict = Depends(get_current_user)):
    await microsoft_oauth.disconnect(user["id"], email)
    return {"ok": True}
