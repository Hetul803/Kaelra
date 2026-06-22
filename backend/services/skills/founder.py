"""Founder / Aegisure Workspace skill: projects, tasks, metrics, launch checklist, post drafts."""

from __future__ import annotations

from config import get_db
from utils import new_id, now_iso, clean_docs, clean_doc, is_demo_user
from services.audit import log_event
from services.actions import create_actions
from services import kaelra
from llm import complete, TaskType


_EMPTY_DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def _empty_metrics() -> dict:
    return {
        "impressions": 0, "clicks": 0, "ctr": 0, "signups": 0,
        "trend": "Connect an analytics source and I'll track your traction.",
        "series": [{"day": d, "impressions": 0} for d in _EMPTY_DAYS],
    }


class AnalyticsConnector:
    """Mock analytics source for the founder workspace (real API later)."""
    provider = "analytics"

    def snapshot(self) -> dict:
        return {
            "impressions": 4820, "clicks": 38, "ctr": 0.79, "signups": 12,
            "trend": "impressions up, clicks flat — sharpen the hook",
            "series": [{"day": d, "impressions": v} for d, v in
                       zip(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
                           [420, 560, 610, 700, 820, 760, 950])],
        }


_analytics = AnalyticsConnector()


async def ensure_seed(user_id: str):
    db = get_db()
    if await db.projects.count_documents({"user_id": user_id}) > 0:
        return
    pid = new_id()
    if not await is_demo_user(user_id):
        # Real users get a clean, empty workspace they build up themselves.
        await db.projects.insert_one({"id": pid, "user_id": user_id, "name": "My Workspace",
                                      "tagline": "Your founder workspace — add your project, tasks and checklist.",
                                      "stage": "Idea", "created_at": now_iso()})
        return
    await db.projects.insert_one({"id": pid, "user_id": user_id, "name": "Aegisure",
                                  "tagline": "Security checks for indie builders",
                                  "stage": "Pre-launch", "created_at": now_iso()})
    tasks = [
        {"title": "Ship demo video", "status": "in_progress", "priority": "high"},
        {"title": "Write launch tweet/LinkedIn post", "status": "todo", "priority": "high"},
        {"title": "Set up waitlist analytics", "status": "todo", "priority": "medium"},
        {"title": "Talk to 5 users this week", "status": "todo", "priority": "high"},
    ]
    await db.project_tasks.insert_many([{"id": new_id(), "user_id": user_id, "project_id": pid,
                                         "created_at": now_iso(), **t} for t in tasks])
    checklist = [
        {"item": "Landing page live", "done": True},
        {"item": "Demo recorded", "done": False},
        {"item": "Launch post drafted", "done": False},
        {"item": "First 10 users contacted", "done": False},
        {"item": "Pricing decided", "done": True},
    ]
    await db.project_checklist.insert_many([{"id": new_id(), "user_id": user_id, "project_id": pid,
                                             "created_at": now_iso(), **c} for c in checklist])


async def overview(user_id: str) -> dict:
    db = get_db()
    await ensure_seed(user_id)
    project = clean_doc(await db.projects.find_one({"user_id": user_id}))
    tasks = clean_docs(await db.project_tasks.find({"user_id": user_id}).sort("created_at", 1).to_list(200))
    checklist = clean_docs(await db.project_checklist.find({"user_id": user_id}).sort("created_at", 1).to_list(50))
    metrics = _analytics.snapshot() if await is_demo_user(user_id) else _empty_metrics()
    return {"project": project, "tasks": tasks, "checklist": checklist, "metrics": metrics}


async def add_task(user_id: str, data: dict) -> dict:
    db = get_db()
    project = await db.projects.find_one({"user_id": user_id})
    doc = {"id": new_id(), "user_id": user_id, "project_id": project["id"] if project else None,
           "status": "todo", "priority": "medium", "created_at": now_iso(), **data}
    await db.project_tasks.insert_one(doc)
    await log_event(user_id, "founder.task_added", f"Task: {data.get('title')}")
    return clean_doc(doc)


async def set_task_status(user_id: str, tid: str, status: str) -> dict | None:
    db = get_db()
    await db.project_tasks.update_one({"user_id": user_id, "id": tid}, {"$set": {"status": status}})
    return clean_doc(await db.project_tasks.find_one({"user_id": user_id, "id": tid}))


async def toggle_checklist(user_id: str, cid: str) -> dict | None:
    db = get_db()
    c = await db.project_checklist.find_one({"user_id": user_id, "id": cid})
    if not c:
        return None
    await db.project_checklist.update_one({"id": cid}, {"$set": {"done": not c.get("done")}})
    return clean_doc(await db.project_checklist.find_one({"id": cid}))


async def draft_post(user_id: str, topic: str, profile: dict) -> dict:
    db = get_db()
    project = await db.projects.find_one({"user_id": user_id}) or {}
    pname = project.get("name", "my startup")
    ptag = project.get("tagline", "")
    pstage = project.get("stage", "")
    system = kaelra.persona(profile) + (
        "\n\nDraft a compelling LinkedIn post for the user's startup. Hook in line 1, "
        "value in the middle, soft CTA at the end. 90-140 words. No hashtag spam. "
        "Write it ready-to-post in first person; do not ask the user for more info.")
    prompt = (f"Startup: {pname} - {ptag} (stage: {pstage}). "
              f"Topic/angle: {topic or 'launch announcement + demo, building in public'}.")
    try:
        post = await complete(system=system, prompt=prompt,
                              session_id=f"founder-{user_id}", task=TaskType.DRAFT)
    except Exception:
        post = f"Building {pname} in public - {ptag}. Here's the demo. Would love your feedback."
    acts = await create_actions(user_id, [{
        "type": "draft_linkedin_post", "title": "LinkedIn launch post (draft)",
        "what": post, "why": "A stronger demo-focused post to lift your click-through — posts only after approval.",
        "source": "Founder skill", "sensitive": True, "requires_approval": True}], origin="founder")
    return {"post": post, "actions_prepared": len(acts)}


async def summarize_metrics(user_id: str, profile: dict) -> dict:
    if not await is_demo_user(user_id):
        return {"summary": "Connect an analytics source (or add your numbers) and I'll summarize your traction and suggest a growth move.",
                "metrics": _empty_metrics(), "actions_prepared": 0}
    snap = _analytics.snapshot()
    system = kaelra.persona(profile) + "\n\nIn 2-3 sentences, summarize these startup metrics and suggest one growth move."
    import json
    try:
        summary = await complete(system=system, prompt=json.dumps(snap),
                                 session_id=f"founder-{user_id}", task=TaskType.PRIORITIZATION)
    except Exception:
        summary = "Impressions are climbing but clicks are flat — sharpen your hook and add a clearer CTA."
    acts = await create_actions(user_id, [{
        "type": "suggest_growth_action", "title": "Growth move: sharpen your post hook",
        "what": summary, "why": "Your CTR is low despite strong reach.", "source": "Founder skill", "sensitive": False}],
        origin="founder")
    return {"summary": summary, "metrics": snap, "actions_prepared": len(acts)}
