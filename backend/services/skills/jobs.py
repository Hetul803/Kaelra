"""Jobs / Career skill.

Data model: job matches + an application tracker (status pipeline). Connector
abstraction (JobsConnector) yields matches — mock now, real Jobs API later.
Kaelra recommends the best resume from indexed files, drafts recruiter replies
(approval-gated), and tracks applications. Every action is logged.
"""

from __future__ import annotations

from config import get_db
from utils import new_id, now_iso, clean_docs, clean_doc, is_demo_user
from services.audit import log_event
from services.actions import create_actions
from services import kaelra
from llm import complete, TaskType

PIPELINE = ["matched", "saved", "applied", "interviewing", "offer", "rejected"]


class JobsConnector:
    """Mock jobs source; swap for a real Jobs API later (same interface)."""
    provider = "jobs"

    async def matches(self, profile: dict) -> list[dict]:
        return [
            {"title": "Backend Engineer Intern", "company": "Northwind Labs", "location": "Remote",
             "salary": "$40/hr", "match": 0.92, "tags": ["Python", "FastAPI", "MongoDB"]},
            {"title": "Software Engineer (New Grad)", "company": "Vela Systems", "location": "Austin, TX",
             "salary": "$110k", "match": 0.86, "tags": ["Go", "APIs", "Cloud"]},
            {"title": "Platform Engineer Intern", "company": "Lumen AI", "location": "Remote",
             "salary": "$45/hr", "match": 0.83, "tags": ["Python", "Kubernetes"]},
            {"title": "Full-Stack Developer", "company": "Harbor", "location": "NYC (Hybrid)",
             "salary": "$95k", "match": 0.78, "tags": ["React", "Node", "SQL"]},
            {"title": "Backend Intern - Payments", "company": "Tessellate", "location": "Remote",
             "salary": "$42/hr", "match": 0.75, "tags": ["Python", "Stripe", "APIs"]},
        ]


_connector = JobsConnector()


async def ensure_seed(user_id: str, profile: dict):
    db = get_db()
    if await db.jobs.count_documents({"user_id": user_id}) > 0:
        return
    if not await is_demo_user(user_id):
        return  # real users: matches arrive from real sources, not mock data
    matches = await _connector.matches(profile)
    docs = [{"id": new_id(), "user_id": user_id, "status": "matched", "created_at": now_iso(),
             "updated_at": now_iso(), **m} for m in matches]
    if docs:
        await db.jobs.insert_many(docs)


async def get_overview(user_id: str, profile: dict) -> dict:
    db = get_db()
    await ensure_seed(user_id, profile)
    jobs = clean_docs(await db.jobs.find({"user_id": user_id}).sort("match", -1).to_list(100))
    matches = [j for j in jobs if j["status"] == "matched"]
    pipeline = {s: [j for j in jobs if j["status"] == s] for s in PIPELINE if s != "matched"}
    return {"matches": matches, "pipeline": pipeline, "counts": {s: len([j for j in jobs if j["status"] == s]) for s in PIPELINE}}


async def best_resume(user_id: str) -> dict | None:
    """Recommend the best resume from indexed files/uploads."""
    db = get_db()
    files = await db.files.find({"user_id": user_id}).to_list(100)
    resumes = [f for f in files if "resume" in (f.get("name", "").lower()) or "cv" in f.get("name", "").lower()]
    if not resumes:
        return None
    pick = sorted(resumes, key=lambda f: f.get("created_at", ""), reverse=True)[0]
    return {"id": pick["id"], "name": pick["name"],
            "reason": "Most recent resume on file; tailored to backend roles."}


async def set_status(user_id: str, job_id: str, status: str) -> dict | None:
    db = get_db()
    if status not in PIPELINE:
        return None
    await db.jobs.update_one({"user_id": user_id, "id": job_id},
                             {"$set": {"status": status, "updated_at": now_iso()}})
    job = await db.jobs.find_one({"user_id": user_id, "id": job_id})
    if not job:
        return None
    label = {"saved": "save_job", "applied": "mark_applied"}.get(status)
    await log_event(user_id, f"jobs.{status}", f"{status.title()}: {job.get('title')} @ {job.get('company')}",
                    "job", job_id)
    if status == "applied":
        await create_actions(user_id, [{
            "type": "create_follow_up", "title": f"Follow up on {job.get('company')} application",
            "what": "Set a reminder to follow up in 5 days.", "why": "Following up boosts response rates.",
            "source": "Jobs skill", "sensitive": False}], origin="jobs")
    return clean_doc(job)


async def draft_recruiter_reply(user_id: str, job_id: str, profile: dict) -> dict:
    db = get_db()
    job = await db.jobs.find_one({"user_id": user_id, "id": job_id})
    resume = await best_resume(user_id)
    title = job.get("title") if job else "the role"
    company = job.get("company") if job else "the company"
    system = kaelra.persona(profile) + (
        "\n\nDraft a warm, concise professional reply to a recruiter expressing interest and "
        "offering to share a resume. 4-6 sentences. Sign as the user.")
    prompt = f"Role: {title} at {company}. Resume to attach: {resume['name'] if resume else 'my resume'}."
    try:
        body = await complete(system=system, prompt=prompt, session_id=f"jobs-{user_id}", task=TaskType.DRAFT)
    except Exception:
        body = f"Hi, thank you for reaching out about {title} at {company}. I'm very interested and would love to share my resume and chat further. Best regards."
    acts = await create_actions(user_id, [{
        "type": "draft_recruiter_reply",
        "title": f"Recruiter reply for {title} @ {company}",
        "what": body + (f"\n\n[Attach: {resume['name']}]" if resume else ""),
        "why": "Prepared a reply with your best resume — not sent until you approve.",
        "source": "Jobs skill", "sensitive": True, "requires_approval": True}], origin="jobs")
    return {"draft": body, "resume": resume, "actions_prepared": len(acts)}
