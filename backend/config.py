"""Central configuration + database handle for Kaelra."""

import os
from pathlib import Path

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ.get("DB_NAME", "kaelra")
JWT_SECRET = os.environ.get("JWT_SECRET", "kaelra-dev-secret")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_DAYS = 30
EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY")
CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*").split(",")

# --- Google OAuth (optional; app runs in mock mode until these are set) ---
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "").strip()
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "").strip()
GOOGLE_SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/drive.readonly",
]


def google_configured() -> bool:
    return bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)


# --- ElevenLabs voice (optional; browser Web Speech fallback when absent) ---
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY", "").strip()
ELEVENLABS_VOICE_ID = os.environ.get("ELEVENLABS_VOICE_ID", "EXAVITQu4vr4xnSDxMaL").strip()  # "Sarah" warm female


def elevenlabs_configured() -> bool:
    return bool(ELEVENLABS_API_KEY)

UPLOAD_DIR = ROOT_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# Demo account credentials (seeded on startup)
DEMO_EMAIL = "demo@kaelra.ai"
DEMO_PASSWORD = "kaelra"

_client = AsyncIOMotorClient(MONGO_URL)
db = _client[DB_NAME]


def get_db():
    return db


def close_client():
    _client.close()
