"""Google OAuth 2.0 (offline / refresh-token) for Calendar, Gmail and Drive.

MULTI-ACCOUNT: a user can connect several Google accounts at once. Tokens are
stored one document per (user_id, email) in `google_tokens`; readers aggregate
across every connected account.

Production-ready 3-legged web flow. The app runs in MOCK mode whenever
GOOGLE_CLIENT_ID/SECRET are not configured.

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

GOOGLE_PROVIDERS = ("google_calendar", "gmail", "google_drive")


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
        prompt="consent select_account",  # refresh_token + let user pick which account
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
    email = _userinfo_email(creds) or "account"
    token_doc = {
        "user_id": user_id,
        "email": email,
        "access_token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "scopes": list(creds.scopes or GOOGLE_SCOPES),
        "expiry": creds.expiry.isoformat() if creds.expiry else None,
        "updated_at": now_iso(),
    }
    db = get_db()
    # Multi-account: key by (user_id, email). Preserve refresh_token if Google
    # omits it on a re-consent for an already-linked account.
    existing = await db.google_tokens.find_one({"user_id": user_id, "email": email})
    if existing and not token_doc["refresh_token"]:
        token_doc["refresh_token"] = existing.get("refresh_token")
    await db.google_tokens.update_one(
        {"user_id": user_id, "email": email}, {"$set": token_doc}, upsert=True)
    for provider in GOOGLE_PROVIDERS:
        await db.connected_accounts.update_one(
            {"user_id": user_id, "provider": provider},
            {"$set": {"status": "connected", "connected_at": now_iso(),
                      "account_email": email, "real": True}},
            upsert=True,
        )
    await log_event(user_id, "google.connected", f"Connected Google account {email}")
    accounts = await list_accounts(user_id)
    return {"email": email, "scopes": token_doc["scopes"], "accounts": accounts}


def _userinfo_email(creds: Credentials) -> str | None:
    try:
        from googleapiclient.discovery import build
        svc = build("oauth2", "v2", credentials=creds, cache_discovery=False)
        info = svc.userinfo().get().execute()
        return info.get("email")
    except Exception:
        return None


def _creds_from_tok(tok: dict) -> Credentials:
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
    return creds


async def get_all_credentials(user_id: str) -> list[tuple[str, Credentials]]:
    """Refreshed credentials for EVERY connected Google account of the user."""
    if not google_configured():
        return []
    db = get_db()
    out: list[tuple[str, Credentials]] = []
    async for tok in db.google_tokens.find({"user_id": user_id}):
        if not tok.get("refresh_token"):
            continue
        creds = _creds_from_tok(tok)
        try:
            if not creds.valid:
                creds.refresh(GoogleRequest())
                await db.google_tokens.update_one(
                    {"user_id": user_id, "email": tok.get("email")},
                    {"$set": {"access_token": creds.token,
                              "expiry": creds.expiry.isoformat() if creds.expiry else None,
                              "updated_at": now_iso()}},
                )
        except Exception:
            continue
        out.append((tok.get("email", "account"), creds))
    return out


async def get_credentials(user_id: str, email: str | None = None) -> Credentials | None:
    """Single account credentials (first valid, or a specific email). Back-compat."""
    all_creds = await get_all_credentials(user_id)
    if not all_creds:
        return None
    if email:
        for em, creds in all_creds:
            if em == email:
                return creds
    return all_creds[0][1]


async def list_accounts(user_id: str) -> list[dict]:
    db = get_db()
    out = []
    async for tok in db.google_tokens.find({"user_id": user_id}):
        out.append({"email": tok.get("email"), "scopes": tok.get("scopes", []),
                    "connected_at": tok.get("updated_at")})
    return out


async def is_connected(user_id: str) -> bool:
    if not google_configured():
        return False
    db = get_db()
    return bool(await db.google_tokens.find_one({"user_id": user_id, "refresh_token": {"$ne": None}}))


async def status(user_id: str) -> dict:
    accounts = await list_accounts(user_id)
    return {
        "configured": google_configured(),
        "connected": len(accounts) > 0,
        "email": accounts[0]["email"] if accounts else None,
        "accounts": accounts,
        "count": len(accounts),
        "scopes": accounts[0]["scopes"] if accounts else [],
    }


async def disconnect(user_id: str, email: str | None = None):
    db = get_db()
    if email:
        await db.google_tokens.delete_one({"user_id": user_id, "email": email})
    else:
        await db.google_tokens.delete_many({"user_id": user_id})
    remaining = await db.google_tokens.count_documents({"user_id": user_id})
    if remaining == 0:
        for provider in GOOGLE_PROVIDERS:
            await db.connected_accounts.update_one(
                {"user_id": user_id, "provider": provider},
                {"$set": {"status": "not_connected", "connected_at": None,
                          "account_email": None, "real": False}},
            )
    await log_event(user_id, "google.disconnected",
                    f"Disconnected Google account {email or '(all)'}")
