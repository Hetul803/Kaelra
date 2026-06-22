"""Pydantic request/response models for Kaelra API.

MongoDB documents are stored as dicts; these models validate inputs and shape
selected responses. We keep them permissive (extra=ignore) where helpful.
"""

from typing import Any, Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


# ----------------------------- Auth -----------------------------
class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=4)
    name: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# --------------------------- Onboarding -------------------------
class OnboardingRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: str
    call_me: str
    routine: Optional[str] = None
    goals: list[str] = []
    interests: list[str] = []
    life_areas: list[str] = []
    tone: str = "friendly"  # calm | friendly | direct | energetic
    notifications_enabled: bool = True
    device_sync: bool = True
    proactive_briefing: bool = True


# ----------------------------- Memory ---------------------------
class MemoryRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    category: str
    content: str
    important: bool = False
    temporary: bool = False


class MemoryUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    category: Optional[str] = None
    content: Optional[str] = None
    important: Optional[bool] = None
    temporary: Optional[bool] = None


# ----------------------------- Goals ----------------------------
class GoalRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    title: str
    description: Optional[str] = None
    progress: float = 0.0
    target_date: Optional[str] = None


class GoalUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    title: Optional[str] = None
    description: Optional[str] = None
    progress: Optional[float] = None
    target_date: Optional[str] = None


# ---------------------------- Routines --------------------------
class RoutineRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: str
    description: Optional[str] = None
    schedule: Optional[str] = None  # e.g. "6:00 AM" or "any USCIS email"
    type: str = "general"
    enabled: bool = True


class RoutineUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: Optional[str] = None
    description: Optional[str] = None
    schedule: Optional[str] = None
    type: Optional[str] = None
    enabled: Optional[bool] = None


# ----------------------------- Chat -----------------------------
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


# ---------------------------- Actions ---------------------------
class ActionUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    status: Optional[str] = None  # approved | rejected | completed | snoozed | pending
    title: Optional[str] = None
    what: Optional[str] = None
    snooze_until: Optional[str] = None


class ActionCreate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    type: str
    title: str
    what: str
    why: Optional[str] = None
    source: Optional[str] = None
    sensitive: bool = False


# -------------------------- Notifications -----------------------
class NotificationCreate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    title: str
    body: Optional[str] = None
    type: str = "reminder"
    scheduled_for: Optional[str] = None


# ----------------------------- Devices --------------------------
class DeviceHeartbeat(BaseModel):
    model_config = ConfigDict(extra="ignore")
    device_id: str
    name: Optional[str] = None
    kind: str = "laptop"  # laptop | phone | tablet
    voice_enabled: bool = False


# ----------------------------- Settings -------------------------
class SettingsUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: Optional[str] = None
    call_me: Optional[str] = None
    tone: Optional[str] = None
    notifications_enabled: Optional[bool] = None
    device_sync: Optional[bool] = None
    proactive_briefing: Optional[bool] = None
    voice_enabled: Optional[bool] = None
    interests: Optional[list[str]] = None
    approval_rules: Optional[dict[str, Any]] = None


class AccountConnectRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    status: str = "connected"  # connected | not_connected
