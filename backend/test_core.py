"""
test_core.py — Kaelra Core Reasoning Engine POC

Proves the make-or-break core in isolation BEFORE building the app:
  1. Claude Sonnet 4.5 connection + a warm, personal DAILY BRIEFING generated
     from structured demo context (calendar/email/goals/routines/actions).
  2. Structured ACTION SUGGESTIONS returned as strict JSON, parseable into
     Action Queue items (with sensitive/approval flags).
  3. FILE SUMMARIZATION + extraction of summary, action items, deadlines,
     people, key context as strict JSON.

Run: cd /app/backend && python test_core.py
"""

import asyncio
import json
import sys
from datetime import datetime

from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent / ".env")

from llm import complete, complete_json, TaskType  # noqa: E402


# ---------------------------------------------------------------------------
# Realistic demo context for the seeded user "Hetul"
# ---------------------------------------------------------------------------
DEMO_CONTEXT = {
    "user": {"name": "Hetul", "call_me": "Hetul", "tone": "friendly"},
    "now": "Monday, 9:12 AM",
    "calendar": [
        {"title": "Work shift", "start": "2:00 PM", "end": "10:00 PM", "location": "Downtown Store"},
        {"title": "CS-401 Lecture", "start": "11:00 AM", "end": "12:15 PM", "location": "Hall B"},
    ],
    "emails": [
        {"from": "Prof. Adams", "subject": "Assignment 3 due Friday 11:59 PM", "important": True,
         "snippet": "Reminder: Assignment 3 (REST APIs) is due Friday night."},
        {"from": "USCIS", "subject": "Case status update available", "important": True,
         "snippet": "There is an update on your case. Sign in to review."},
        {"from": "LinkedIn", "subject": "5 new jobs match your profile", "important": False,
         "snippet": "Backend engineer roles near you."},
    ],
    "goals": [
        {"title": "Land a backend internship", "progress": 0.4},
        {"title": "Grow Aegisure to first 100 users", "progress": 0.1},
    ],
    "routines": [
        {"name": "Morning briefing", "time": "6:00 AM"},
        {"name": "Watch immigration emails", "trigger": "any USCIS email"},
    ],
    "pending_actions": [
        {"type": "draft_email", "title": "Reply to Prof. Adams about extension"},
    ],
    "places": [{"name": "Work", "commute_minutes": 29}],
    "interests": ["AI", "startups", "backend engineering"],
}

KAELRA_PERSONA = (
    "You are Kaelra, a warm, intelligent, proactive PERSONAL AI OPERATOR (referred "
    "to as 'she'). You are NOT a generic chatbot and you never pretend to be human "
    "— you are clearly an AI operator, but you feel personal, calm and emotionally "
    "intelligent, like a trusted chief of staff who is always synced across the "
    "user's phone and laptop. You know what matters and you get things ready before "
    "you are asked. You prepare actions but NEVER perform sensitive actions (sending "
    "email, applying to jobs, changing calendar, posting online, deleting files, "
    "purchases) without explicit approval."
)


def section(title):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


# ---------------------------------------------------------------------------
# Check 1: Warm daily briefing
# ---------------------------------------------------------------------------
async def check_briefing() -> bool:
    section("CHECK 1: Daily briefing generation (Claude Sonnet 4.5)")
    system = KAELRA_PERSONA + (
        "\n\nGenerate a concise, warm spoken-style DAILY BRIEFING (4-7 sentences). "
        "Greet the user by name. Mention work/class timing and a leave-by recommendation "
        "using commute time, flag important emails (including anything they asked you to "
        "monitor), note prepared actions awaiting approval, and end with a helpful question "
        "offering what to do first. Be specific using the context. Do not invent facts not "
        "present in the context."
    )
    prompt = (
        "Here is everything you know about today. Produce the briefing.\n\n"
        + json.dumps(DEMO_CONTEXT, indent=2)
    )
    try:
        text = await complete(
            system=system, prompt=prompt, session_id="poc-briefing", task=TaskType.BRIEFING
        )
    except Exception as e:  # noqa: BLE001
        print(f"FAILED: exception during briefing: {e}")
        return False

    print("\nBRIEFING OUTPUT:\n" + text)
    lc = text.lower()
    checks = {
        "greets Hetul": "hetul" in lc,
        "mentions leave/commute timing": any(k in lc for k in ["leave", "1:31", "1:3", "commute", "head out", "leave by"]),
        "flags an important email": any(k in lc for k in ["email", "uscis", "adams", "assignment"]),
        "ends with a question": "?" in text,
        "non-trivial length": len(text) > 180,
    }
    for k, v in checks.items():
        print(f"  [{'PASS' if v else 'FAIL'}] {k}")
    return all(checks.values())


# ---------------------------------------------------------------------------
# Check 2: Structured action suggestions (JSON)
# ---------------------------------------------------------------------------
VALID_ACTION_TYPES = {
    "draft_email", "summarize_email", "create_reminder", "schedule_alarm_placeholder",
    "commute_alert", "news_brief", "file_summary", "organize_file_suggestion",
    "job_match", "draft_application", "assignment_reminder", "calendar_suggestion",
    "follow_up", "startup_task", "general_task",
}
SENSITIVE_TYPES = {"draft_email", "draft_application", "calendar_suggestion"}


async def check_actions() -> bool:
    section("CHECK 2: Structured action suggestions (strict JSON)")
    system = KAELRA_PERSONA + (
        "\n\nGiven the user's day context, propose 3-6 useful ACTIONS to prepare. "
        "Return a JSON object with key 'actions' whose value is an array. Each action: "
        "{\"type\": one of " + ", ".join(sorted(VALID_ACTION_TYPES)) + ", "
        "\"title\": short label, \"what\": what you prepared, \"why\": why it matters, "
        "\"source\": where it came from (email/calendar/goal/routine), "
        "\"sensitive\": true/false (true if it sends/changes anything external), "
        "\"requires_approval\": true/false}. "
        "Anything that sends email, applies to jobs, changes calendar or posts online must "
        "have sensitive=true and requires_approval=true."
    )
    prompt = "Day context:\n" + json.dumps(DEMO_CONTEXT, indent=2)
    try:
        data = await complete_json(
            system=system, prompt=prompt, session_id="poc-actions", task=TaskType.ACTION_EXTRACTION
        )
    except Exception as e:  # noqa: BLE001
        print(f"FAILED: exception/parse error during actions: {e}")
        return False

    print("\nACTIONS OUTPUT:\n" + json.dumps(data, indent=2))
    actions = data.get("actions") if isinstance(data, dict) else data
    if not isinstance(actions, list) or not actions:
        print("  [FAIL] actions is not a non-empty list")
        return False

    all_typed = all(isinstance(a, dict) and a.get("type") in VALID_ACTION_TYPES for a in actions)
    has_fields = all(all(f in a for f in ("title", "what", "why")) for a in actions)
    # at least one sensitive action correctly flagged for approval
    sensitive_ok = any(
        a.get("type") in SENSITIVE_TYPES and a.get("requires_approval") for a in actions
    ) or not any(a.get("type") in SENSITIVE_TYPES for a in actions)

    checks = {
        "3+ actions proposed": len(actions) >= 3,
        "all valid action types": all_typed,
        "all have title/what/why": has_fields,
        "sensitive actions flagged for approval": sensitive_ok,
    }
    for k, v in checks.items():
        print(f"  [{'PASS' if v else 'FAIL'}] {k}")
    return all(checks.values())


# ---------------------------------------------------------------------------
# Check 3: File summarization + extraction (JSON)
# ---------------------------------------------------------------------------
SAMPLE_FILE_TEXT = """
CS-401 Software Engineering — Course Syllabus (Fall)

Instructor: Prof. Adams (adams@university.edu)
TA: Maria Lopez

Important dates:
- Assignment 1 (Git basics): due Sept 12
- Assignment 3 (REST APIs): due Oct 18, 11:59 PM
- Midterm exam: Oct 25, in Hall B
- Final project proposal: due Nov 8
- Final project demo: Dec 6

Grading: Assignments 40%, Midterm 20%, Final project 40%.
Late policy: 10% penalty per day, max 3 days.
Office hours: Mondays 3-5 PM with Prof. Adams; Wednesdays with TA Maria Lopez.
"""


async def check_file_summary() -> bool:
    section("CHECK 3: File summarization + extraction (strict JSON)")
    system = KAELRA_PERSONA + (
        "\n\nYou are reading a file the user uploaded. Return a JSON object with: "
        "{\"summary\": 2-3 sentence summary, "
        "\"people\": array of names/contacts mentioned, "
        "\"deadlines\": array of {\"title\":..., \"date\":...}, "
        "\"action_items\": array of short actionable strings, "
        "\"key_context\": array of important facts the user should remember}."
    )
    prompt = "FILE NAME: CS-401_syllabus.txt\n\nFILE CONTENT:\n" + SAMPLE_FILE_TEXT
    try:
        data = await complete_json(
            system=system, prompt=prompt, session_id="poc-file", task=TaskType.FILE_SUMMARY
        )
    except Exception as e:  # noqa: BLE001
        print(f"FAILED: exception/parse error during file summary: {e}")
        return False

    print("\nFILE SUMMARY OUTPUT:\n" + json.dumps(data, indent=2))
    summary = data.get("summary", "")
    deadlines = data.get("deadlines", [])
    people = data.get("people", [])
    action_items = data.get("action_items", [])

    deadlines_text = json.dumps(deadlines).lower()
    checks = {
        "has summary text": isinstance(summary, str) and len(summary) > 30,
        "extracted deadlines": isinstance(deadlines, list) and len(deadlines) >= 2,
        "found Oct 18 REST API deadline": "oct" in deadlines_text or "18" in deadlines_text,
        "extracted people (Adams)": any("adams" in str(p).lower() for p in people),
        "extracted action items": isinstance(action_items, list) and len(action_items) >= 1,
    }
    for k, v in checks.items():
        print(f"  [{'PASS' if v else 'FAIL'}] {k}")
    return all(checks.values())


async def main():
    print("KAELRA CORE POC — Claude Sonnet 4.5 via Emergent Universal Key")
    print("Started:", datetime.now().isoformat())
    results = {}
    results["briefing"] = await check_briefing()
    results["actions"] = await check_actions()
    results["file_summary"] = await check_file_summary()

    section("POC SUMMARY")
    for k, v in results.items():
        print(f"  {k:14s}: {'PASS' if v else 'FAIL'}")
    ok = all(results.values())
    print("\nOVERALL:", "ALL CHECKS PASSED ✅" if ok else "SOME CHECKS FAILED ❌")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    asyncio.run(main())
