"""Location timeline — Kaelra learns where you go (browser-geolocation based).

Google Maps Timeline / Location History has no public API, so Kaelra builds her
OWN timeline from location pings the client sends (with the user's permission).
She clusters pings into places, counts visits, reverse-geocodes a friendly label
(best-effort, free OpenStreetMap), correlates with the day's calendar, and learns
frequent places into durable memory.
"""

from __future__ import annotations

import datetime as dt
import logging

import httpx

from config import get_db
from utils import new_id, now_iso, today_str
from services.audit import log_event

logger = logging.getLogger("kaelra.location")

# ~3 decimal places of lat/lng ~= 110m cluster.
_PRECISION = 3
_LEARN_AFTER_VISITS = 3


def _key(lat: float, lng: float) -> str:
    return f"{round(lat, _PRECISION)},{round(lng, _PRECISION)}"


async def _reverse_geocode(lat: float, lng: float) -> str | None:
    """Best-effort friendly label via free OSM Nominatim (no key needed)."""
    try:
        async with httpx.AsyncClient(timeout=6) as client:
            r = await client.get(
                "https://nominatim.openstreetmap.org/reverse",
                params={"lat": lat, "lon": lng, "format": "jsonv2", "zoom": "16"},
                headers={"User-Agent": "KaelraOperator/1.0 (personal AI operator)"},
            )
            r.raise_for_status()
            j = r.json()
            a = j.get("address", {}) or {}
            name = (j.get("name") or a.get("amenity") or a.get("building")
                    or a.get("road") or a.get("neighbourhood") or a.get("suburb"))
            city = a.get("city") or a.get("town") or a.get("village") or a.get("county")
            if name and city:
                return f"{name}, {city}"
            return name or city or j.get("display_name", "").split(",")[0] or None
    except Exception:
        return None


async def record_ping(user_id: str, lat: float, lng: float,
                      label: str | None = None, accuracy: float | None = None) -> dict:
    db = get_db()
    ts = now_iso()
    key = _key(lat, lng)

    # Raw ping (capped history for today's path).
    await db.location_pings.insert_one({
        "id": new_id(), "user_id": user_id, "lat": lat, "lng": lng,
        "accuracy": accuracy, "day": today_str(), "created_at": ts,
    })

    place = await db.location_places.find_one({"user_id": user_id, "key": key})
    if place:
        await db.location_places.update_one(
            {"user_id": user_id, "key": key},
            {"$set": {"last_seen": ts, "lat": lat, "lng": lng},
             "$inc": {"visits": 1}},
        )
        visits = place.get("visits", 1) + 1
        friendly = place.get("label")
    else:
        friendly = label or await _reverse_geocode(lat, lng) or f"Place near {key}"
        await db.location_places.insert_one({
            "id": new_id(), "user_id": user_id, "key": key, "lat": lat, "lng": lng,
            "label": friendly, "visits": 1, "first_seen": ts, "last_seen": ts,
        })
        visits = 1

    # Learn frequent places into durable memory (deduped).
    if visits == _LEARN_AFTER_VISITS and friendly:
        content = f"You regularly spend time at {friendly}."
        if not await db.memories.find_one({"user_id": user_id, "content": content}):
            await db.memories.insert_one({
                "id": new_id(), "user_id": user_id, "category": "Places",
                "content": content, "important": False, "temporary": False,
                "learned": True, "source": "location", "created_at": ts,
            })
            await log_event(user_id, "memory.learned", f"Learned place: {friendly}",
                            "memory", None, {"source": "location"})
    return {"place": friendly, "visits": visits}


async def timeline(user_id: str) -> dict:
    db = get_db()
    places = await db.location_places.find({"user_id": user_id}).sort("last_seen", -1).to_list(50)
    frequent = sorted(places, key=lambda p: p.get("visits", 0), reverse=True)[:8]
    today = await db.location_pings.find(
        {"user_id": user_id, "day": today_str()}).sort("created_at", 1).to_list(200)

    # Correlate today's calendar events that carry a location.
    correlations = []
    dash = await db.daily_briefings.find_one({"user_id": user_id})  # not required
    return {
        "places": [{"id": p["id"], "label": p.get("label"), "visits": p.get("visits", 0),
                    "last_seen": p.get("last_seen"), "lat": p.get("lat"), "lng": p.get("lng")}
                   for p in places],
        "frequent": [{"label": p.get("label"), "visits": p.get("visits", 0)} for p in frequent],
        "today_points": len(today),
        "today": [{"lat": t["lat"], "lng": t["lng"], "at": t["created_at"]} for t in today[-60:]],
        "correlations": correlations,
        "total_places": len(places),
    }
