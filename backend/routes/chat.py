"""Talk to Kaelra — streaming chat + session/message persistence."""

import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from config import get_db
from models import ChatRequest
from auth import get_current_user
from utils import new_id, now_iso, clean_doc, clean_docs
from services.context import build_today_context
from services import kaelra
from services.actions import create_actions
from services.audit import log_event

router = APIRouter()


async def _ensure_session(user_id: str, session_id: str | None) -> str:
    db = get_db()
    if session_id:
        existing = await db.conversation_sessions.find_one({"user_id": user_id, "id": session_id})
        if existing:
            return session_id
    sid = session_id or new_id()
    await db.conversation_sessions.insert_one({
        "id": sid, "user_id": user_id, "title": "New conversation",
        "created_at": now_iso(), "updated_at": now_iso(),
    })
    return sid


@router.get("/chat/sessions")
async def list_sessions(user: dict = Depends(get_current_user)):
    db = get_db()
    docs = await db.conversation_sessions.find({"user_id": user["id"]}).sort("updated_at", -1).to_list(100)
    return clean_docs(docs)


@router.get("/chat/sessions/{session_id}/messages")
async def get_messages(session_id: str, user: dict = Depends(get_current_user)):
    db = get_db()
    docs = await db.messages.find({"user_id": user["id"], "session_id": session_id}).sort("created_at", 1).to_list(500)
    return clean_docs(docs)


async def _save_message(user_id, session_id, role, content):
    db = get_db()
    doc = {"id": new_id(), "user_id": user_id, "session_id": session_id,
           "role": role, "content": content, "created_at": now_iso()}
    await db.messages.insert_one(doc)
    return doc


@router.post("/chat/stream")
async def chat_stream(req: ChatRequest, user: dict = Depends(get_current_user)):
    db = get_db()
    user_id = user["id"]
    session_id = await _ensure_session(user_id, req.session_id)

    history_docs = await db.messages.find(
        {"user_id": user_id, "session_id": session_id}
    ).sort("created_at", 1).to_list(500)
    history = [{"role": m["role"], "content": m["content"]} for m in history_docs]

    await _save_message(user_id, session_id, "user", req.message)
    # Title the session from first user message
    if not history:
        title = (req.message[:48] + "…") if len(req.message) > 48 else req.message
        await db.conversation_sessions.update_one({"id": session_id}, {"$set": {"title": title}})

    context = await build_today_context(user)
    profile = context["profile"]

    async def event_gen():
        yield f"data: {json.dumps({'type': 'session', 'session_id': session_id})}\n\n"
        parts = []
        try:
            async for delta in kaelra.stream_chat(profile, context, history, req.message, f"chat-{session_id}"):
                parts.append(delta)
                yield f"data: {json.dumps({'type': 'delta', 'content': delta})}\n\n"
        except Exception as e:  # noqa: BLE001
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        reply = "".join(parts).strip()
        await _save_message(user_id, session_id, "assistant", reply)
        await db.conversation_sessions.update_one({"id": session_id}, {"$set": {"updated_at": now_iso()}})
        await log_event(user_id, "chat.message", "Conversation turn", "session", session_id)

        created = []
        try:
            proposed = await kaelra.actions_from_turn(profile, context, req.message, reply, f"chat-{session_id}")
            created = await create_actions(user_id, proposed, origin="conversation")
        except Exception:
            created = []
        yield f"data: {json.dumps({'type': 'actions', 'actions': created})}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"},
    )


@router.delete("/chat/sessions/{session_id}")
async def delete_session(session_id: str, user: dict = Depends(get_current_user)):
    db = get_db()
    await db.conversation_sessions.delete_one({"user_id": user["id"], "id": session_id})
    await db.messages.delete_many({"user_id": user["id"], "session_id": session_id})
    return {"ok": True}
