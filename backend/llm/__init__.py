"""Kaelra LLM layer.

This package isolates the *language/reasoning* layer from the rest of the
system. Kaelra's real intelligence lives in the deterministic backend
(memory, routines, actions, connectors, briefing engine). The LLM is only
used for natural language, summarization, drafting, prioritization and
conversation.

The provider abstraction lets us route different *tasks* to different models
later (e.g. fast/cheap model for classification, a stronger model for
reasoning) without touching call sites.
"""

from .provider import (
    LLMProvider,
    EmergentLLMProvider,
    get_provider,
    complete,
    complete_json,
    stream,
)
from .router import TaskType, route_model

__all__ = [
    "LLMProvider",
    "EmergentLLMProvider",
    "get_provider",
    "complete",
    "complete_json",
    "stream",
    "TaskType",
    "route_model",
]
