"""Kaelra backend entrypoint.

Wires together the deterministic system (auth, dashboard, actions, memory,
files, devices, accounts) with the LLM reasoning layer behind a clean
/api router. Seeds the demo operator "Hetul" on startup.
"""

import logging

from fastapi import APIRouter, FastAPI
from starlette.middleware.cors import CORSMiddleware

from config import CORS_ORIGINS, close_client
from services.seed import seed_demo, ensure_demo_alive

from routes import auth as auth_routes
from routes import today as today_routes
from routes import chat as chat_routes
from routes import actions as actions_routes
from routes import knowledge as knowledge_routes
from routes import files as files_routes
from routes import accounts as accounts_routes
from routes import voice as voice_routes
from routes import google as google_routes
from routes import context as context_routes
from routes import skills as skills_routes

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("kaelra")

app = FastAPI(title="Kaelra — Personal AI Operator")

api_router = APIRouter(prefix="/api")


@api_router.get("/")
async def root():
    return {"message": "Kaelra is online.", "product": "Kaelra Daily Operator"}


@api_router.get("/health")
async def health():
    return {"status": "ok"}


# Mount feature routers
api_router.include_router(auth_routes.router, tags=["auth"])
api_router.include_router(today_routes.router, tags=["today"])
api_router.include_router(chat_routes.router, tags=["chat"])
api_router.include_router(actions_routes.router, tags=["actions"])
api_router.include_router(knowledge_routes.router, tags=["knowledge"])
api_router.include_router(files_routes.router, tags=["files"])
api_router.include_router(accounts_routes.router, tags=["accounts"])
api_router.include_router(voice_routes.router, tags=["voice"])
api_router.include_router(google_routes.router, tags=["google"])
api_router.include_router(context_routes.router, tags=["context"])
api_router.include_router(skills_routes.router, tags=["skills"])

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup():
    try:
        demo_id = await seed_demo()
        await ensure_demo_alive()
        logger.info("Demo operator ready (user_id=%s)", demo_id)
    except Exception as e:  # noqa: BLE001
        logger.exception("Demo seeding failed: %s", e)
    try:
        from services.scheduler import start_scheduler
        start_scheduler()
    except Exception as e:  # noqa: BLE001
        logger.exception("Scheduler start failed: %s", e)


@app.on_event("shutdown")
async def on_shutdown():
    try:
        from services.scheduler import shutdown_scheduler
        shutdown_scheduler()
    except Exception:
        pass
    close_client()
