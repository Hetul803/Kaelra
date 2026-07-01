"""Location timeline routes."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from auth import get_current_user
from services import location as loc

router = APIRouter()


class PingBody(BaseModel):
    lat: float
    lng: float
    label: str | None = None
    accuracy: float | None = None


@router.post("/location/ping")
async def location_ping(body: PingBody, user: dict = Depends(get_current_user)):
    return await loc.record_ping(user["id"], body.lat, body.lng, body.label, body.accuracy)


@router.get("/location/timeline")
async def location_timeline(user: dict = Depends(get_current_user)):
    return await loc.timeline(user["id"])
