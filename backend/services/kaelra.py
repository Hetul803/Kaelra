"""Kaelra reasoning — the LLM layer (persona, briefing, actions, chat, files).

Every prompt makes clear Kaelra is a warm, proactive PERSONAL AI OPERATOR
('she'), never a human, and that sensitive actions require approval.
"""

import json

from llm import complete, complete_json, stream, TaskType

VALID_ACTION_TYPES = [
    "draft_email", "summarize_email", "create_reminder", "schedule_alarm_placeholder",
    "commute_alert", "news_brief", "file_summary", "organize_file_suggestion",
    "job_match", "draft_application", "assignment_reminder", "calendar_suggestion",
    "follow_up", "startup_task", "general_task",
]

SENSITIVE_TYPES = {
    "draft_email", "draft_application", "calendar_suggestion",
}

_TONE_GUIDE = {
    "calm": "Speak in a calm, grounding, unhurried way. Reassuring and spacious.",
    "friendly": "Speak warmly and personally, like a trusted friend who has your back.",
    "direct": "Be concise and direct. Lead with the most important thing, minimal fluff.",
    "energetic": "Be upbeat and motivating, with positive momentum (no exclamation spam).",
}


def persona(profile: dict) -> str:
    name = profile.get("call_me") or profile.get("name") or "there"
    tone = profile.get("tone", "friendly")
    return (
        f"You are Kaelra, a warm, intelligent, proactive PERSONAL AI OPERATOR (referred to as 'she'). "
        f"You are {name}'s personal chief of staff, synced across their phone and laptop. "
        "You are NOT a generic chatbot and you NEVER pretend to be human — you are clearly an AI operator, "
        "but you feel personal, calm and emotionally intelligent. You know what matters and you get things "
        "ready before you are asked. "
        f"TONE: {_TONE_GUIDE.get(tone, _TONE_GUIDE['friendly'])} "
        "You PREPARE actions but NEVER perform sensitive actions (sending email, applying to jobs, "
        "changing calendar, posting online, deleting/moving files, purchases) without explicit approval. "
        "You only use facts present in the provided context; you never invent the user's schedule, emails, or data."
    )


# ----------------------------- Briefing -----------------------------
async def generate_briefing_text(profile: dict, context: dict, session_id: str) -> str:
    system = persona(profile) + (
        "\n\nGenerate a warm, spoken-style DAILY BRIEFING (4-7 sentences). "
        "Greet the user by name. Mention work/class timing and a clear leave-by recommendation using "
        "the commute data. Flag important emails (including anything they asked you to monitor). "
        "Note prepared actions awaiting approval. Touch on goals or news only if relevant. "
        "End with a helpful question offering what to do first. Be specific using the context. "
        "Never invent facts not present in the context."
    )
    prompt = "Here is everything you know about today:\n\n" + json.dumps(_slim(context), indent=2)
    return await complete(system=system, prompt=prompt, session_id=session_id, task=TaskType.BRIEFING)


async def propose_actions(profile: dict, context: dict, session_id: str) -> list[dict]:
    system = persona(profile) + (
        "\n\nGiven the user's day, propose 3-6 useful ACTIONS to prepare. Return JSON: "
        '{"actions": [{"type": one of [' + ", ".join(VALID_ACTION_TYPES) + '], '
        '"title": short label, "what": what you prepared, "why": why it matters, '
        '"source": where it came from, "sensitive": bool, "requires_approval": bool}]}. '
        "Anything that sends email, applies to jobs, changes calendar or posts online MUST have "
        "sensitive=true and requires_approval=true. Be specific and genuinely useful."
    )
    prompt = "Day context:\n" + json.dumps(_slim(context), indent=2)
    try:
        data = await complete_json(
            system=system, prompt=prompt, session_id=session_id, task=TaskType.ACTION_EXTRACTION
        )
    except Exception:
        return []
    actions = data.get("actions") if isinstance(data, dict) else data
    return [a for a in (actions or []) if isinstance(a, dict) and a.get("type") in VALID_ACTION_TYPES]


# ----------------------------- Chat -----------------------------
def chat_system(profile: dict, context: dict) -> str:
    return persona(profile) + (
        "\n\nYou are in a live conversation with the user. Use the CONTEXT below to answer with specifics "
        "(their real schedule, emails, goals, reminders, files). Be concise and warm. When you prepare "
        "something actionable, say so clearly and mention it will appear in their Action Queue for approval "
        "if it is sensitive. Never claim you sent an email or changed anything — you only prepare."
        "\n\nCONTEXT:\n" + json.dumps(_slim(context), indent=2)
    )


def chat_prompt(history: list[dict], message: str) -> str:
    lines = []
    for m in history[-10:]:
        role = "User" if m.get("role") == "user" else "Kaelra"
        lines.append(f"{role}: {m.get('content', '')}")
    lines.append(f"User: {message}")
    lines.append("Kaelra:")
    return "\n".join(lines)


def stream_chat(profile: dict, context: dict, history: list[dict], message: str, session_id: str):
    return stream(
        system=chat_system(profile, context),
        prompt=chat_prompt(history, message),
        session_id=session_id,
        task=TaskType.CONVERSATION,
    )


async def actions_from_turn(profile: dict, context: dict, user_msg: str, reply: str, session_id: str) -> list[dict]:
    """After a chat turn, decide if any actions should be prepared. Returns [] often."""
    system = persona(profile) + (
        "\n\nBased ONLY on this conversation turn, decide if Kaelra should prepare any concrete actions "
        "for the user's Action Queue. If nothing actionable, return {\"actions\": []}. Otherwise return "
        '{"actions": [{"type": one of [' + ", ".join(VALID_ACTION_TYPES) + '], "title":..., "what":..., '
        '"why":..., "source": "conversation", "sensitive": bool, "requires_approval": bool}]}. '
        "Only propose actions the user actually wants. Sensitive = sends/changes anything external."
    )
    prompt = f"User said: {user_msg}\n\nKaelra replied: {reply}"
    try:
        data = await complete_json(
            system=system, prompt=prompt, session_id=session_id, task=TaskType.ACTION_EXTRACTION
        )
    except Exception:
        return []
    actions = data.get("actions") if isinstance(data, dict) else data
    return [a for a in (actions or []) if isinstance(a, dict) and a.get("type") in VALID_ACTION_TYPES]


# ----------------------------- Files -----------------------------
async def summarize_file(profile: dict, filename: str, text: str, session_id: str) -> dict:
    system = persona(profile) + (
        "\n\nYou are reading a file the user uploaded. Return JSON with: "
        '{"summary": 2-3 sentence summary, "people": [names/contacts], '
        '"deadlines": [{"title":..., "date":...}], "action_items": [short strings], '
        '"key_context": [important facts to remember]}.'
    )
    prompt = f"FILE NAME: {filename}\n\nFILE CONTENT:\n{text[:12000]}"
    try:
        return await complete_json(
            system=system, prompt=prompt, session_id=session_id, task=TaskType.FILE_SUMMARY
        )
    except Exception as e:  # noqa: BLE001
        return {"summary": f"Kaelra couldn't fully read this file ({e}).", "people": [],
                "deadlines": [], "action_items": [], "key_context": []}


async def answer_about_file(profile: dict, filename: str, text: str, question: str, session_id: str) -> str:
    system = persona(profile) + (
        f"\n\nThe user is asking about the file '{filename}'. Answer using only its content. Be concise."
        f"\n\nFILE CONTENT:\n{text[:12000]}"
    )
    return await complete(system=system, prompt=question, session_id=session_id, task=TaskType.FILE_SUMMARY)


# ----------------------------- helpers -----------------------------
def _slim(context: dict) -> dict:
    """Trim context for prompting (drop heavy/raw fields, keep signal)."""
    emails = context.get("emails") or {}
    files = context.get("files") or {}
    return {
        "now": __import__("datetime").datetime.now().strftime("%A, %-I:%M %p"),
        "profile": context.get("profile"),
        "calendar": (context.get("calendar") or {}).get("events") if context.get("calendar") else None,
        "important_emails": emails.get("important"),
        "commute": context.get("commute"),
        "news": (context.get("news") or {}).get("articles") if context.get("news") else None,
        "goals": [{"title": g.get("title"), "progress": g.get("progress")} for g in context.get("goals", [])],
        "routines": [{"name": r.get("name"), "schedule": r.get("schedule")} for r in context.get("routines", [])],
        "things_to_monitor": [m.get("content") for m in context.get("memories", []) if m.get("category") == "Things to monitor"],
        "files_needing_attention": files.get("needs_attention"),
        "pending_actions": [{"title": a.get("title"), "type": a.get("type")} for a in context.get("pending_actions", [])],
    }
