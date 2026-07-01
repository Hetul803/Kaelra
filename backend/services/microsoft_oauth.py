"""Microsoft Identity (Outlook / Microsoft 365) OAuth 2.0 — multi-account.

Authorization-code flow against login.microsoftonline.com. Reads Mail + Calendar
via Microsoft Graph. Runs in MOCK/idle mode until MICROSOFT_CLIENT_ID/SECRET are
set (same pattern as Google/LinkedIn — the user adds Azure creds later).

Tokens are stored one document per (user_id, email) in `microsoft_tokens`.
"""

from __future__ import annotations

import datetime as dt
import urllib.parse

import httpx

from config import (
    MICROSOFT_CLIENT_ID, MICROSOFT_CLIENT_SECRET, MICROSOFT_TENANT, MICROSOFT_SCOPES,
    microsoft_configured, get_db,
)
from utils import now_iso
from services.audit import log_event

MS_PROVIDERS = ("outlook_mail", "outlook_calendar")


def _authority() -> str:
    return f"https://login.microsoftonline.com/{MICROSOFT_TENANT or 'common'}"


def build_auth_url(redirect_uri: str, state: str) -> str:
    params = {
        "client_id": MICROSOFT_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "response_mode": "query",
        "scope": " ".join(MICROSOFT_SCOPES),
        "state": state,
        "prompt": "select_account",
    }
    return f"{_authority()}/oauth2/v2.0/authorize?" + urllib.parse.urlencode(params)


async def exchange_code(user_id: str, code: str, redirect_uri: str) -> dict:
    data = {
        "client_id": MICROSOFT_CLIENT_ID,
        "client_secret": MICROSOFT_CLIENT_SECRET,
        "code": code,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
        "scope": " ".join(MICROSOFT_SCOPES),
    }
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post(f"{_authority()}/oauth2/v2.0/token", data=data)
        r.raise_for_status()
        tok = r.json()
    email = await _me_email(tok.get("access_token"))
    expiry = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=tok.get("expires_in", 3600))).isoformat()
    doc = {
        "user_id": user_id, "email": email or "account",
        "access_token": tok.get("access_token"), "refresh_token": tok.get("refresh_token"),
        "expiry": expiry, "scopes": MICROSOFT_SCOPES, "updated_at": now_iso(),
    }
    db = get_db()
    existing = await db.microsoft_tokens.find_one({"user_id": user_id, "email": doc["email"]})
    if existing and not doc["refresh_token"]:
        doc["refresh_token"] = existing.get("refresh_token")
    await db.microsoft_tokens.update_one(
        {"user_id": user_id, "email": doc["email"]}, {"$set": doc}, upsert=True)
    for provider in MS_PROVIDERS:
        await db.connected_accounts.update_one(
            {"user_id": user_id, "provider": provider},
            {"$set": {"status": "connected", "connected_at": now_iso(),
                      "account_email": doc["email"], "real": True}}, upsert=True)
    await log_event(user_id, "microsoft.connected", f"Connected Microsoft account {doc['email']}")
    return {"email": doc["email"], "accounts": await list_accounts(user_id)}


async def _me_email(access_token: str | None) -> str | None:
    if not access_token:
        return None
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get("https://graph.microsoft.com/v1.0/me",
                                 headers={"Authorization": f"Bearer {access_token}"})
            r.raise_for_status()
            j = r.json()
            return j.get("mail") or j.get("userPrincipalName")
    except Exception:
        return None


async def get_access_token(user_id: str, email: str | None = None) -> str | None:
    """Return a valid access token for one account (refresh if needed)."""
    tokens = await _all_tokens(user_id)
    if not tokens:
        return None
    tok = next((t for t in tokens if t.get("email") == email), tokens[0]) if email else tokens[0]
    return await _ensure_fresh(tok)


async def get_all_access_tokens(user_id: str) -> list[tuple[str, str]]:
    out = []
    for tok in await _all_tokens(user_id):
        at = await _ensure_fresh(tok)
        if at:
            out.append((tok.get("email", "account"), at))
    return out


async def _all_tokens(user_id: str) -> list[dict]:
    if not microsoft_configured():
        return []
    db = get_db()
    return await db.microsoft_tokens.find({"user_id": user_id}).to_list(20)


async def _ensure_fresh(tok: dict) -> str | None:
    try:
        expiry = dt.datetime.fromisoformat(tok["expiry"]) if tok.get("expiry") else None
        if expiry and expiry > dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=60):
            return tok.get("access_token")
    except Exception:
        pass
    if not tok.get("refresh_token"):
        return tok.get("access_token")
    data = {
        "client_id": MICROSOFT_CLIENT_ID, "client_secret": MICROSOFT_CLIENT_SECRET,
        "refresh_token": tok["refresh_token"], "grant_type": "refresh_token",
        "scope": " ".join(MICROSOFT_SCOPES),
    }
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(f"{_authority()}/oauth2/v2.0/token", data=data)
            r.raise_for_status()
            new = r.json()
        expiry = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=new.get("expires_in", 3600))).isoformat()
        db = get_db()
        await db.microsoft_tokens.update_one(
            {"user_id": tok["user_id"], "email": tok.get("email")},
            {"$set": {"access_token": new.get("access_token"),
                      "refresh_token": new.get("refresh_token") or tok["refresh_token"],
                      "expiry": expiry, "updated_at": now_iso()}})
        return new.get("access_token")
    except Exception:
        return None


async def list_accounts(user_id: str) -> list[dict]:
    return [{"email": t.get("email"), "connected_at": t.get("updated_at")}
            for t in await _all_tokens(user_id)]


async def status(user_id: str) -> dict:
    accounts = await list_accounts(user_id)
    return {"configured": microsoft_configured(), "connected": len(accounts) > 0,
            "email": accounts[0]["email"] if accounts else None,
            "accounts": accounts, "count": len(accounts)}


async def disconnect(user_id: str, email: str | None = None):
    db = get_db()
    if email:
        await db.microsoft_tokens.delete_one({"user_id": user_id, "email": email})
    else:
        await db.microsoft_tokens.delete_many({"user_id": user_id})
    if await db.microsoft_tokens.count_documents({"user_id": user_id}) == 0:
        for provider in MS_PROVIDERS:
            await db.connected_accounts.update_one(
                {"user_id": user_id, "provider": provider},
                {"$set": {"status": "not_connected", "connected_at": None,
                          "account_email": None, "real": False}})
    await log_event(user_id, "microsoft.disconnected", f"Disconnected Microsoft {email or '(all)'}")
