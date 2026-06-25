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


_RESUME_KEYWORDS = ["python", "fastapi", "mongodb", "react", "node", "docker", "kubernetes",
                    "go", "java", "sql", "aws", "typescript", "graphql", "rust", "kotlin", "swift"]


async def user_skills(user_id: str, profile: dict) -> list[str]:
    """Derive a skill list from profile interests + indexed resume text."""
    db = get_db()
    skills: list[str] = []
    for i in (profile or {}).get("interests", []) or []:
        if i and i not in skills:
            skills.append(i)
    files = await db.files.find({"user_id": user_id}).to_list(50)
    for f in files:
        name = (f.get("name") or "").lower()
        if "resume" in name or "cv" in name:
            txt = (f.get("text") or "").lower()
            for kw in _RESUME_KEYWORDS:
                if kw in txt and kw not in skills:
                    skills.append(kw)
    return skills[:12]


async def search_matches(user_id: str, profile: dict, keywords: str | None,
                         location: str | None, limit: int = 8) -> dict:
    """Search live jobs via the provider (LinkedIn/JSearch) with mock fallback.

    Only REAL (non-sample) results are persisted into the pipeline so a fresh
    user's clean home/feed is never polluted by sample data.
    """
    from services.skills import jobs_provider
    skills = await user_skills(user_id, profile)
    if not keywords:
        keywords = " ".join(skills[:3]) or "software engineer"
    res = await jobs_provider.search(keywords, location or "Remote", skills, limit)
    if not res.get("sample"):
        for r in res.get("results", []):
            if await db_jobs_dupe(user_id, r):
                continue
            await get_db().jobs.insert_one({
                "id": new_id(), "user_id": user_id, "status": "matched",
                "created_at": now_iso(), "updated_at": now_iso(), **r,
            })
        await log_event(user_id, "jobs.searched", f"Searched jobs: {keywords}", "jobs", None,
                        {"count": len(res.get("results", [])), "provider": res.get("provider")})
    res["keywords"] = keywords
    return res


async def db_jobs_dupe(user_id: str, job: dict) -> bool:
    db = get_db()
    return bool(await db.jobs.find_one(
        {"user_id": user_id, "title": job.get("title"), "company": job.get("company")}))


async def save_match(user_id: str, job: dict) -> dict:
    db = get_db()
    fields = {k: job.get(k) for k in ("title", "company", "location", "salary", "match", "tags", "url", "description")}
    existing = await db.jobs.find_one({"user_id": user_id, "title": job.get("title"), "company": job.get("company")})
    if existing:
        await db.jobs.update_one({"id": existing["id"]}, {"$set": {"status": "saved", "updated_at": now_iso()}})
        await log_event(user_id, "jobs.saved", f"Saved: {job.get('title')} @ {job.get('company')}", "job", existing["id"])
        return clean_doc(await db.jobs.find_one({"id": existing["id"]}))
    doc = {"id": new_id(), "user_id": user_id, "status": "saved",
           "created_at": now_iso(), "updated_at": now_iso(), **fields}
    await db.jobs.insert_one(doc)
    await log_event(user_id, "jobs.saved", f"Saved: {job.get('title')} @ {job.get('company')}", "job", doc["id"])
    return clean_doc(doc)


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
