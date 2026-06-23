"""Deterministic skill auto-detection (v0).

Kaelra only surfaces a skill when she sees a real signal for it — recruiter/job
emails or a resume -> Jobs; coursework signals -> Class; founder activity -> Founder;
a real smart-home device -> Home. The demo operator sees all skills.
"""

from config import get_db
from utils import is_demo_user

SKILL_DEFS = {
    "jobs":    {"label": "Jobs & Career",   "route": "/jobs",    "icon": "briefcase"},
    "class":   {"label": "Class & School",  "route": "/class",   "icon": "graduation"},
    "founder": {"label": "Founder Workspace", "route": "/founder", "icon": "rocket"},
    "home":    {"label": "Smart Home",      "route": "/home",    "icon": "home"},
}

JOB_HINTS = ["recruit", "hiring", " role", "position", "opportunit", "interview",
             "linkedin", "indeed", "career", "application", "job ", "internship", "offer letter"]
CLASS_HINTS = ["assignment", "syllabus", "professor", "course", "lecture", "homework",
               "exam", "semester", "registrar", "canvas", ".edu", "midterm", "quiz"]
FOUNDER_HINTS = ["launch", "investor", "startup", "waitlist", "founder", "pitch",
                 "product hunt", "mrr", "fundrais", "seed round"]


async def relevant_skills(user_id: str) -> list[dict]:
    db = get_db()
    if await is_demo_user(user_id):
        return [{"key": k, **v, "reason": "Demo workspace"} for k, v in SKILL_DEFS.items()]

    items = await db.indexed_items.find({"user_id": user_id}).to_list(500)
    blobs = [((it.get("title") or "") + " " + (it.get("meta") or "")).lower() for it in items]
    blob = " ".join(blobs)

    def has(hints):
        return any(h in blob for h in hints)

    out = {}

    has_resume = any(("resume" in b or " cv" in b) for b in blobs)
    if has(JOB_HINTS) or has_resume or await db.jobs.count_documents({"user_id": user_id}) > 0:
        out["jobs"] = ("I noticed job/recruiter activity" if has(JOB_HINTS)
                       else "I found your resume" if has_resume else "You're tracking applications")

    if (has(CLASS_HINTS)
            or await db.classes.count_documents({"user_id": user_id}) > 0
            or await db.assignments.count_documents({"user_id": user_id}) > 0):
        out["class"] = "I see coursework signals"

    has_founder_data = (await db.project_tasks.count_documents({"user_id": user_id}) > 0
                        or await db.project_checklist.count_documents({"user_id": user_id}) > 0)
    if has(FOUNDER_HINTS) or has_founder_data:
        out["founder"] = "You're building something"

    if await db.home_devices.count_documents({"user_id": user_id}) > 0:
        out["home"] = "Smart-home devices connected"

    return [{"key": k, **SKILL_DEFS[k], "reason": reason} for k, reason in out.items()]
