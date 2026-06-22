"""Google OAuth 2.0 (offline / refresh-token) for Calendar, Gmail and Drive.

Production-ready 3-legged web flow. The app runs in MOCK mode whenever
GOOGLE_CLIENT_ID/SECRET are not configured; once configured, users connect
their own Google account and Kaelra reads real data via least-privilege scopes.

REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
(The frontend passes redirect_uri = window.location.origin + "/auth/google".)
"""

from __future__ import annotations

import datetime as dt

from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleRequest

from config import (
    GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_SCOPES, google_configured, get_db,
)
from utils import now_iso
from services.audit import log_event


def _client_config(redirect_uri: str) -> dict:
    return {
        "web": {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [redirect_uri],
        }
    }


def build_auth_url(redirect_uri: str, state: str) -> str:
    # Confidential web client (has client_secret) -> classic code flow, no PKCE.
    # PKCE must be disabled because the auth URL and token exchange happen in two
    # separate requests; an auto-generated code_verifier cannot survive between them
    # (which otherwise causes "invalid_grant: Missing code verifier").
    flow = Flow.from_client_config(
        _client_config(redirect_uri), scopes=GOOGLE_SCOPES, autogenerate_code_verifier=False,
    )
    flow.redirect_uri = redirect_uri
    url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",  # ensure refresh_token is returned
        state=state,
    )
    return url


async def exchange_code(user_id: str, code: str, redirect_uri: str) -> dict:
    flow = Flow.from_client_config(
        _client_config(redirect_uri), scopes=GOOGLE_SCOPES, autogenerate_code_verifier=False,
    )
    flow.redirect_uri = redirect_uri
    flow.fetch_token(code=code)
    creds = flow.credentials
    email = _userinfo_email(creds)
    token_doc = {
        "user_id": user_id,
        "access_token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "scopes": list(creds.scopes or GOOGLE_SCOPES),
        "expiry": creds.expiry.isoformat() if creds.expiry else None,
        "email": email,
        "updated_at": now_iso(),
    }
    db = get_db()
    await db.google_tokens.update_one({"user_id": user_id}, {"$set": token_doc}, upsert=True)
    # Mark the three Google connectors connected
    for provider in ("google_calendar", "gmail", "google_drive"):
        await db.connected_accounts.update_one(
            {"user_id": user_id, "provider": provider},
            {"$set": {"status": "connected", "connected_at": now_iso(), "account_email": email, "real": True}},
        )
    await log_event(user_id, "google.connected", f"Connected Google account {email}")
    return {"email": email, "scopes": token_doc["scopes"]}


def _userinfo_email(creds: Credentials) -> str | None:
    try:
        from googleapiclient.discovery import build
        svc = build("oauth2", "v2", credentials=creds, cache_discovery=False)
        info = svc.userinfo().get().execute()
        return info.get("email")
    except Exception:
        return None


async def get_credentials(user_id: str) -> Credentials | None:
    """Return refreshed Credentials for the user, or None if not connected."""
    if not google_configured():
        return None
    db = get_db()
    tok = await db.google_tokens.find_one({"user_id": user_id})
    if not tok or not tok.get("refresh_token"):
        return None
    expiry = None
    if tok.get("expiry"):
        try:
            expiry = dt.datetime.fromisoformat(tok["expiry"]).replace(tzinfo=None)
        except Exception:
            expiry = None
    creds = Credentials(
        token=tok.get("access_token"),
        refresh_token=tok.get("refresh_token"),
        token_uri=tok.get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        scopes=tok.get("scopes", GOOGLE_SCOPES),
    )
    creds.expiry = expiry
    try:
        if not creds.valid:
            creds.refresh(GoogleRequest())
            await db.google_tokens.update_one(
                {"user_id": user_id},
                {"$set": {"access_token": creds.token,
                          "expiry": creds.expiry.isoformat() if creds.expiry else None,
                          "updated_at": now_iso()}},
            )
    except Exception:
        return None
    return creds


async def is_connected(user_id: str) -> bool:
    if not google_configured():
        return False
    db = get_db()
    tok = await db.google_tokens.find_one({"user_id": user_id})
    return bool(tok and tok.get("refresh_token"))


async def status(user_id: str) -> dict:
    db = get_db()
    tok = await db.google_tokens.find_one({"user_id": user_id})
    return {
        "configured": google_configured(),
        "connected": bool(tok and tok.get("refresh_token")),
        "email": tok.get("email") if tok else None,
        "scopes": tok.get("scopes", []) if tok else [],
    }


async def disconnect(user_id: str):
    db = get_db()
    await db.google_tokens.delete_one({"user_id": user_id})
    for provider in ("google_calendar", "gmail", "google_drive"):
        await db.connected_accounts.update_one(
            {"user_id": user_id, "provider": provider},
            {"$set": {"status": "not_connected", "connected_at": None, "account_email": None, "real": False}},
        )
    await log_event(user_id, "google.disconnected", "Disconnected Google account")
