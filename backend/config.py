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
