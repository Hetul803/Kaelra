"""Web Push (VAPID) — Kaelra reaches the user outside the app.

Self-contained: generates a VAPID keypair on first use (stored in Mongo) and
sends real browser push notifications via pywebpush. No third-party push vendor
and no API key required — it just works once deployed over HTTPS.
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
from py_vapid import Vapid01
from pywebpush import webpush, WebPushException

from config import get_db, PUSH_CONTACT_EMAIL
from utils import new_id, now_iso

logger = logging.getLogger("kaelra.push")

_cache: dict = {}  # in-process cache: {"doc": <vapid doc>, "obj": <Vapid01>}


async def _load_or_create_vapid() -> dict:
    if _cache.get("doc"):
        return _cache["doc"]
    db = get_db()
    doc = await db.app_config.find_one({"id": "vapid"})
    if not doc:
        priv = ec.generate_private_key(ec.SECP256R1())
        priv_pem = priv.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        ).decode()
        pub_point = priv.public_key().public_bytes(
            serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint
        )
        public_key = base64.urlsafe_b64encode(pub_point).rstrip(b"=").decode()
        doc = {"id": "vapid", "private_pem": priv_pem, "public_key": public_key,
               "created_at": now_iso()}
        await db.app_config.update_one({"id": "vapid"}, {"$set": doc}, upsert=True)
    _cache["doc"] = doc
    return doc


async def _vapid_obj() -> Vapid01:
    if _cache.get("obj"):
        return _cache["obj"]
    doc = await _load_or_create_vapid()
    obj = Vapid01.from_pem(doc["private_pem"].encode())
    _cache["obj"] = obj
    return obj


async def ensure_keys():
    """Generate + cache VAPID keys at startup so the public key is ready."""
    await _vapid_obj()


async def public_key() -> str:
    return (await _load_or_create_vapid())["public_key"]


async def save_subscription(user_id: str, subscription: dict, device_id: str | None = None) -> bool:
    db = get_db()
    endpoint = (subscription or {}).get("endpoint")
    if not endpoint:
        return False
    await db.push_subscriptions.update_one(
        {"endpoint": endpoint},
        {"$set": {
            "id": new_id(), "user_id": user_id, "endpoint": endpoint,
            "keys": subscription.get("keys", {}), "device_id": device_id,
            "updated_at": now_iso(),
        }},
        upsert=True,
    )
    return True


async def remove_subscription(user_id: str, endpoint: str):
    db = get_db()
    await db.push_subscriptions.delete_one({"user_id": user_id, "endpoint": endpoint})


async def has_subscription(user_id: str) -> bool:
    db = get_db()
    return bool(await db.push_subscriptions.find_one({"user_id": user_id}))


def _send_one(vapid_obj: Vapid01, sub_info: dict, payload: str):
    # vapid_claims is mutated by pywebpush (adds exp/aud) — pass a fresh dict.
    webpush(
        subscription_info=sub_info,
        data=payload,
        vapid_private_key=vapid_obj,
        vapid_claims={"sub": PUSH_CONTACT_EMAIL},
        timeout=10,
    )


async def send_push(user_id: str, title: str, body: str = "", url: str = "/",
                    tag: str | None = None) -> int:
    """Deliver a push to all of a user's subscribed devices. Returns count sent."""
    db = get_db()
    subs = await db.push_subscriptions.find({"user_id": user_id}).to_list(50)
    if not subs:
        return 0
    vapid_obj = await _vapid_obj()
    payload = json.dumps({"title": title, "body": body or title, "url": url, "tag": tag or "kaelra"})
    sent = 0
    for s in subs:
        sub_info = {"endpoint": s["endpoint"], "keys": s.get("keys", {})}
        try:
            await asyncio.to_thread(_send_one, vapid_obj, sub_info, payload)
            sent += 1
        except WebPushException as e:
            status = getattr(getattr(e, "response", None), "status_code", None)
            if status in (404, 410):
                await db.push_subscriptions.delete_one({"endpoint": s["endpoint"]})
            else:
                logger.warning("web push failed: %s", e)
        except Exception as e:  # noqa: BLE001
            logger.warning("web push error: %s", e)
    return sent
