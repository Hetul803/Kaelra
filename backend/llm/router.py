"""Task -> model routing.

Centralizes the mapping of a logical *task* to a concrete (provider, model).
For v0 everything routes to Claude Sonnet 4.5 (warm, natural, emotionally
intelligent) as requested, but the indirection means we can later send, say,
classification or quick prioritization to a faster/cheaper model without
changing any business logic.
"""

from enum import Enum


class TaskType(str, Enum):
    CONVERSATION = "conversation"          # Talk to Kaelra (streaming)
    BRIEFING = "briefing"                  # Daily briefing generation
    ACTION_EXTRACTION = "action_extraction"  # Propose structured actions
    FILE_SUMMARY = "file_summary"          # Summarize + extract from files
    DRAFT = "draft"                        # Draft emails / posts / replies
    PRIORITIZATION = "prioritization"      # Rank / classify importance
    QUICK = "quick"                        # Short, cheap helper calls


# Default Kaelra brain (v0). Claude Sonnet 4.5 — warm, natural conversation.
DEFAULT_PROVIDER = "anthropic"
DEFAULT_MODEL = "claude-sonnet-4-5-20250929"

# Cheap/fast brain for structured, non-conversational helper calls. Keeping
# these off the premium model dramatically lowers token cost with no user-facing
# quality loss (JSON extraction / classification / consolidation).
CHEAP_PROVIDER = "anthropic"
CHEAP_MODEL = "claude-haiku-4-5-20251001"

# Per-task overrides. Conversation, briefing and drafting stay on the premium
# brain (quality matters); everything structured/behind-the-scenes uses the
# cheaper model to minimize spend.
_ROUTES: dict[TaskType, tuple[str, str]] = {
    TaskType.CONVERSATION: (DEFAULT_PROVIDER, DEFAULT_MODEL),
    TaskType.BRIEFING: (DEFAULT_PROVIDER, DEFAULT_MODEL),
    TaskType.DRAFT: (DEFAULT_PROVIDER, DEFAULT_MODEL),
    TaskType.ACTION_EXTRACTION: (CHEAP_PROVIDER, CHEAP_MODEL),
    TaskType.FILE_SUMMARY: (DEFAULT_PROVIDER, DEFAULT_MODEL),
    TaskType.PRIORITIZATION: (CHEAP_PROVIDER, CHEAP_MODEL),
    TaskType.QUICK: (CHEAP_PROVIDER, CHEAP_MODEL),
}


def route_model(task: TaskType) -> tuple[str, str]:
    """Return (provider, model) for a given task."""
    return _ROUTES.get(task, (DEFAULT_PROVIDER, DEFAULT_MODEL))
