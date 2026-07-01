"""Google OAuth routes (Calendar / Gmail / Drive).

REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
The frontend always passes redirect_uri = window.location.origin + "/auth/google".
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from config import google_configured
from auth import get_current_user, create_token
from services import google_oauth

router = APIRouter()


class CallbackRequest(BaseModel):
    code: str
    redirect_uri: str
    state: str | None = None


@router.get("/oauth/google/status")
async def google_status(user: dict = Depends(get_current_user)):
    return await google_oauth.status(user["id"])


@router.get("/oauth/google/accounts")
async def google_accounts(user: dict = Depends(get_current_user)):
    return {"accounts": await google_oauth.list_accounts(user["id"])}


@router.get("/oauth/google/url")
async def google_url(redirect_uri: str, user: dict = Depends(get_current_user)):
    if not google_configured():
        raise HTTPException(status_code=400, detail="Google is not configured yet. Add GOOGLE_CLIENT_ID/SECRET.")
    state = create_token(user["id"])  # opaque, ties the flow to this user
    url = google_oauth.build_auth_url(redirect_uri, state)
    return {"url": url}


@router.post("/oauth/google/callback")
async def google_callback(req: CallbackRequest, user: dict = Depends(get_current_user)):
    if not google_configured():
        raise HTTPException(status_code=400, detail="Google is not configured.")
    try:
        result = await google_oauth.exchange_code(user["id"], req.code, req.redirect_uri)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Google connection failed: {e}")
    return {"ok": True, **result}


@router.post("/oauth/google/disconnect")
async def google_disconnect(email: str | None = None, user: dict = Depends(get_current_user)):
    await google_oauth.disconnect(user["id"], email)
    return {"ok": True}
