"""Class / School skill: schedule, assignments/deadlines, study plans, professor replies."""

from __future__ import annotations

from config import get_db
from utils import new_id, now_iso, clean_docs, clean_doc, is_demo_user
from services.audit import log_event
from services.actions import create_actions
from services import kaelra
from llm import complete, TaskType


async def ensure_seed(user_id: str):
    db = get_db()
    if await db.classes.count_documents({"user_id": user_id}) > 0:
        return
    if not await is_demo_user(user_id):
        return  # real users: classes/assignments come from their own input + connected sources
    classes = [
        {"name": "CS-401 Software Engineering", "professor": "Prof. Adams", "professor_email": "adams@university.edu",
         "schedule": "Mon/Wed 11:00 AM", "location": "Hall B"},
        {"name": "CS-330 Databases", "professor": "Dr. Lin", "professor_email": "lin@university.edu",
         "schedule": "Tue/Thu 1:00 PM", "location": "Hall D"},
    ]
    await db.classes.insert_many([{"id": new_id(), "user_id": user_id, "created_at": now_iso(), **c} for c in classes])
    assignments = [
        {"title": "Assignment 3 (REST APIs)", "course": "CS-401", "due": "Oct 18, 11:59 PM", "status": "todo", "priority": "high"},
        {"title": "Midterm prep", "course": "CS-401", "due": "Oct 25", "status": "todo", "priority": "high"},
        {"title": "ER diagram lab", "course": "CS-330", "due": "Oct 20", "status": "in_progress", "priority": "medium"},
    ]
    await db.assignments.insert_many([{"id": new_id(), "user_id": user_id, "created_at": now_iso(), **a} for a in assignments])


async def overview(user_id: str) -> dict:
    db = get_db()
    await ensure_seed(user_id)
    classes = clean_docs(await db.classes.find({"user_id": user_id}).to_list(100))
    assignments = clean_docs(await db.assignments.find({"user_id": user_id}).sort("created_at", 1).to_list(200))
    return {"classes": classes, "assignments": assignments}


async def add_assignment(user_id: str, data: dict) -> dict:
    db = get_db()
    doc = {"id": new_id(), "user_id": user_id, "status": "todo", "priority": "medium",
           "created_at": now_iso(), **data}
    await db.assignments.insert_one(doc)
    await log_event(user_id, "class.assignment_added", f"Added assignment: {data.get('title')}")
    return clean_doc(doc)


async def set_assignment_status(user_id: str, aid: str, status: str) -> dict | None:
    db = get_db()
    await db.assignments.update_one({"user_id": user_id, "id": aid}, {"$set": {"status": status}})
    a = await db.assignments.find_one({"user_id": user_id, "id": aid})
    return clean_doc(a)


async def study_plan(user_id: str, aid: str, profile: dict) -> dict:
    db = get_db()
    a = await db.assignments.find_one({"user_id": user_id, "id": aid})
    title = a.get("title") if a else "your assignment"
    due = a.get("due") if a else "soon"
    system = kaelra.persona(profile) + "\n\nCreate a short, motivating 3-5 step study plan with time estimates."
    try:
        plan = await complete(system=system, prompt=f"Assignment: {title}. Due: {due}.",
                              session_id=f"class-{user_id}", task=TaskType.DRAFT)
    except Exception:
        plan = f"1) Break {title} into milestones. 2) Draft. 3) Review before {due}."
    acts = await create_actions(user_id, [{
        "type": "study_plan", "title": f"Study plan: {title}",
        "what": plan, "why": f"Stay ahead of the {due} deadline.", "source": "Class skill", "sensitive": False}],
        origin="class")
    return {"plan": plan, "actions_prepared": len(acts)}


async def professor_reply(user_id: str, class_id: str, note: str, profile: dict) -> dict:
    db = get_db()
    c = await db.classes.find_one({"user_id": user_id, "id": class_id})
    prof = c.get("professor") if c else "your professor"
    system = kaelra.persona(profile) + "\n\nDraft a respectful, concise email to a professor. 4-6 sentences."
    try:
        body = await complete(system=system, prompt=f"To {prof}. Context: {note}",
                              session_id=f"class-{user_id}", task=TaskType.DRAFT)
    except Exception:
        body = f"Dear {prof}, {note}. Thank you for your time."
    acts = await create_actions(user_id, [{
        "type": "professor_reply_draft", "title": f"Email draft to {prof}",
        "what": body, "why": "Prepared a draft — not sent until you approve.",
        "source": "Class skill", "sensitive": True, "requires_approval": True}], origin="class")
    return {"draft": body, "actions_prepared": len(acts)}
