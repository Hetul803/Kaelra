"""Seeding + provisioning.

`provision_defaults` gives every new user a populated, alive experience
(connected mock accounts + a starter device). `seed_demo` builds the rich demo
operator "Hetul" with realistic schedule, emails, goals, routines, files and
prepared actions so Kaelra feels alive on first login.
"""

from config import get_db, DEMO_EMAIL, DEMO_PASSWORD
from connectors import CONNECTOR_CATALOG
from auth import hash_password
from utils import new_id, now_iso


async def provision_defaults(user_id: str):
    """Create default connected-account states for a user (idempotent)."""
    db = get_db()
    existing = {a["provider"] async for a in db.connected_accounts.find({"user_id": user_id})}
    for c in CONNECTOR_CATALOG:
        if c["provider"] in existing:
            continue
        await db.connected_accounts.insert_one({
            "id": new_id(),
            "user_id": user_id,
            "provider": c["provider"],
            "name": c["name"],
            "icon": c["icon"],
            "category": c["category"],
            "status": c["default_state"],
            "connected_at": now_iso() if c["default_state"] == "connected" else None,
            "created_at": now_iso(),
        })


async def _insert_many(coll, user_id, items, base):
    db = get_db()
    docs = []
    for it in items:
        docs.append({"id": new_id(), "user_id": user_id, "created_at": now_iso(), **base, **it})
    if docs:
        await coll.insert_many(docs)


async def seed_demo():
    """Create (idempotently) the demo operator account."""
    db = get_db()
    existing = await db.users.find_one({"email": DEMO_EMAIL})
    if existing:
        return existing["id"]

    user_id = new_id()
    await db.users.insert_one({
        "id": user_id,
        "email": DEMO_EMAIL,
        "password": hash_password(DEMO_PASSWORD),
        "name": "Hetul",
        "onboarded": True,
        "is_demo": True,
        "created_at": now_iso(),
    })

    await db.profiles.insert_one({
        "id": new_id(),
        "user_id": user_id,
        "name": "Hetul",
        "call_me": "Hetul",
        "routine": "CS student during the day, work shifts in the afternoon/evening, building Aegisure on the side.",
        "tone": "friendly",
        "interests": ["AI", "startups", "backend engineering", "immigration"],
        "life_areas": ["School", "Career", "Immigration", "Aegisure (startup)"],
        "notifications_enabled": True,
        "device_sync": True,
        "proactive_briefing": True,
        "voice_enabled": False,
        "approval_rules": {"emails": True, "jobs": True, "calendar": True, "files": True, "purchases": True},
        "created_at": now_iso(),
    })

    await provision_defaults(user_id)

    # Memories
    await _insert_many(db.memories, user_id, [
        {"category": "Personal facts", "content": "Goes by Hetul. International student on a work visa.", "important": True, "temporary": False},
        {"category": "Work/class schedule", "content": "Work shifts usually start at 2:00 PM at the Downtown Store.", "important": True, "temporary": False},
        {"category": "Work/class schedule", "content": "CS-401 lecture Mon/Wed 11:00 AM in Hall B.", "important": False, "temporary": False},
        {"category": "Goals", "content": "Wants a backend engineering internship this cycle.", "important": True, "temporary": False},
        {"category": "Preferences", "content": "Prefers a friendly, concise tone. Likes being told the leave-by time.", "important": False, "temporary": False},
        {"category": "Important people", "content": "Prof. Adams teaches CS-401 (adams@university.edu).", "important": False, "temporary": False},
        {"category": "Places", "content": "Work is the Downtown Store, ~29 min commute.", "important": False, "temporary": False},
        {"category": "Routines", "content": "Likes a morning briefing around 6:00 AM.", "important": False, "temporary": False},
        {"category": "Interests", "content": "AI, startups, backend engineering.", "important": False, "temporary": False},
        {"category": "Important documents/files", "content": "CS-401 syllabus has all assignment deadlines.", "important": False, "temporary": False},
        {"category": "Things to monitor", "content": "Watch for immigration / USCIS emails and flag them immediately.", "important": True, "temporary": False},
        {"category": "Things to monitor", "content": "Track Aegisure post performance (impressions vs clicks).", "important": False, "temporary": False},
    ], base={})

    # Goals
    await _insert_many(db.goals, user_id, [
        {"title": "Land a backend internship", "description": "Apply to aligned roles, keep resume sharp.", "progress": 0.4, "target_date": None},
        {"title": "Grow Aegisure to first 100 users", "description": "Ship demo content, talk to users weekly.", "progress": 0.1, "target_date": None},
        {"title": "Finish CS-401 with an A", "description": "Stay ahead of assignments and the midterm.", "progress": 0.6, "target_date": None},
    ], base={})

    # Routines
    await _insert_many(db.routines, user_id, [
        {"name": "Morning briefing", "description": "Brief me on what matters today.", "schedule": "6:00 AM", "type": "briefing", "enabled": True},
        {"name": "Leave-time reminder", "description": "Remind me when to leave for work.", "schedule": "before each shift", "type": "commute", "enabled": True},
        {"name": "Watch immigration emails", "description": "Flag any USCIS / immigration email instantly.", "schedule": "any USCIS email", "type": "email_monitor", "enabled": True},
        {"name": "Check assignment deadlines", "description": "Surface upcoming assignment deadlines.", "schedule": "daily", "type": "deadline", "enabled": True},
        {"name": "Daily tech news briefing", "description": "A short briefing on AI & startups.", "schedule": "8:00 AM", "type": "news", "enabled": True},
        {"name": "Nightly tomorrow prep", "description": "Prepare tomorrow before I sleep.", "schedule": "10:30 PM", "type": "prep", "enabled": False},
    ], base={})

    # Places
    await _insert_many(db.places, user_id, [
        {"name": "Work", "address": "Downtown Store", "commute_minutes": 29},
        {"name": "Campus", "address": "University, Hall B", "commute_minutes": 18},
    ], base={})

    # A sample uploaded file + summary
    file_id = new_id()
    await db.files.insert_one({
        "id": file_id,
        "user_id": user_id,
        "name": "CS-401_syllabus.pdf",
        "kind": "pdf",
        "size": 18240,
        "text": ("CS-401 Software Engineering Syllabus. Instructor Prof. Adams (adams@university.edu). "
                 "Assignment 3 (REST APIs) due Oct 18 11:59 PM. Midterm Oct 25 in Hall B. "
                 "Final project demo Dec 6. Late policy: 10% per day, max 3 days."),
        "important": True,
        "created_at": now_iso(),
    })
    await db.file_summaries.insert_one({
        "id": new_id(),
        "user_id": user_id,
        "file_id": file_id,
        "summary": "CS-401 Software Engineering syllabus from Prof. Adams. Key deadlines: Assignment 3 (Oct 18), Midterm (Oct 25), Final demo (Dec 6). Late work loses 10% per day.",
        "people": ["Prof. Adams", "Maria Lopez (TA)"],
        "deadlines": [
            {"title": "Assignment 3 (REST APIs)", "date": "Oct 18, 11:59 PM"},
            {"title": "Midterm exam", "date": "Oct 25"},
            {"title": "Final project demo", "date": "Dec 6"},
        ],
        "action_items": ["Start Assignment 3 early", "Add midterm to calendar", "Save Prof. Adams contact"],
        "key_context": ["Late policy: 10%/day, max 3 days", "Midterm is in Hall B"],
        "created_at": now_iso(),
    })

    # Prepared (pending) actions \u2014 the alive Action Queue on first login
    await _insert_many(db.actions, user_id, [
        {"type": "draft_email", "title": "Reply to Prof. Adams about Assignment 3",
         "what": "Drafted a short reply confirming you're on track and asking one clarifying question.",
         "why": "He emailed about Assignment 3 due Friday; a quick reply keeps you in good standing.",
         "source": "Gmail", "sensitive": True, "requires_approval": True, "status": "pending",
         "origin": "daily_briefing", "snooze_until": None, "updated_at": now_iso()},
        {"type": "commute_alert", "title": "Leave by 1:31 PM for your 2:00 PM shift",
         "what": "Prepared a leave-time reminder based on a 29-minute commute with light traffic.",
         "why": "So you arrive on time without rushing.",
         "source": "Maps + Calendar", "sensitive": False, "requires_approval": False, "status": "pending",
         "origin": "daily_briefing", "snooze_until": None, "updated_at": now_iso()},
        {"type": "job_match", "title": "Review 5 backend roles that match you",
         "what": "Saved 5 backend engineer roles for your review.",
         "why": "Supports your goal to land a backend internship.",
         "source": "LinkedIn", "sensitive": False, "requires_approval": False, "status": "pending",
         "origin": "daily_briefing", "snooze_until": None, "updated_at": now_iso()},
        {"type": "startup_task", "title": "Better Aegisure demo post draft",
         "what": "Your last post got impressions but no clicks \u2014 I drafted a stronger demo-focused post.",
         "why": "To improve click-through on your Aegisure growth goal.",
         "source": "Goals", "sensitive": False, "requires_approval": False, "status": "pending",
         "origin": "daily_briefing", "snooze_until": None, "updated_at": now_iso()},
        {"type": "follow_up", "title": "USCIS case \u2014 no change today",
         "what": "Checked your monitored immigration mail; nothing new came in.",
         "why": "You asked me to watch immigration emails closely.",
         "source": "Gmail (monitored)", "sensitive": False, "requires_approval": False, "status": "pending",
         "origin": "daily_briefing", "snooze_until": None, "updated_at": now_iso()},
    ], base={})

    # Devices
    await _insert_many(db.devices, user_id, [
        {"device_id": "demo-macbook", "name": "Hetul's MacBook Pro", "kind": "laptop",
         "voice_enabled": False, "notifications_enabled": True, "last_active": now_iso()},
        {"device_id": "demo-iphone", "name": "Hetul's iPhone", "kind": "phone",
         "voice_enabled": True, "notifications_enabled": True, "last_active": now_iso()},
    ], base={})

    return user_id
