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


# Default Kaelra brain (v0). Claude Sonnet 4.5.
DEFAULT_PROVIDER = "anthropic"
DEFAULT_MODEL = "claude-sonnet-4-5-20250929"

# Per-task overrides. Today they all point at the default brain, but this is
# where future routing decisions live (e.g. QUICK -> a haiku-class model).
_ROUTES: dict[TaskType, tuple[str, str]] = {
    TaskType.CONVERSATION: (DEFAULT_PROVIDER, DEFAULT_MODEL),
    TaskType.BRIEFING: (DEFAULT_PROVIDER, DEFAULT_MODEL),
    TaskType.ACTION_EXTRACTION: (DEFAULT_PROVIDER, DEFAULT_MODEL),
    TaskType.FILE_SUMMARY: (DEFAULT_PROVIDER, DEFAULT_MODEL),
    TaskType.DRAFT: (DEFAULT_PROVIDER, DEFAULT_MODEL),
    TaskType.PRIORITIZATION: (DEFAULT_PROVIDER, DEFAULT_MODEL),
    TaskType.QUICK: (DEFAULT_PROVIDER, DEFAULT_MODEL),
}


def route_model(task: TaskType) -> tuple[str, str]:
    """Return (provider, model) for a given task."""
    return _ROUTES.get(task, (DEFAULT_PROVIDER, DEFAULT_MODEL))
