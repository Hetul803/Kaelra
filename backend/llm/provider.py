"""LLM provider abstraction over emergentintegrations.

Exposes a small, stable interface (`complete`, `complete_json`, `stream`) so
the rest of Kaelra never imports emergentintegrations directly. Swapping or
adding providers later only touches this file + router.py.
"""

from __future__ import annotations

import json
import os
import re
import logging
from abc import ABC, abstractmethod
from typing import AsyncIterator, Optional

from emergentintegrations.llm.chat import (
    LlmChat,
    UserMessage,
    TextDelta,
    StreamDone,
)

from .router import TaskType, route_model

logger = logging.getLogger("kaelra.llm")

_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)


class LLMProvider(ABC):
    """Stable interface used by the rest of the system."""

    @abstractmethod
    async def complete(
        self,
        *,
        system: str,
        prompt: str,
        session_id: str,
        task: TaskType = TaskType.CONVERSATION,
        max_tokens: int = 2048,
    ) -> str:
        ...

    @abstractmethod
    def stream(
        self,
        *,
        system: str,
        prompt: str,
        session_id: str,
        task: TaskType = TaskType.CONVERSATION,
        max_tokens: int = 2048,
    ) -> AsyncIterator[str]:
        ...


class EmergentLLMProvider(LLMProvider):
    """Concrete provider backed by the Emergent Universal LLM Key."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("EMERGENT_LLM_KEY")
        if not self.api_key:
            raise RuntimeError("EMERGENT_LLM_KEY not configured")

    def _chat(self, system: str, session_id: str, task: TaskType) -> LlmChat:
        provider, model = route_model(task)
        return LlmChat(
            api_key=self.api_key,
            session_id=session_id,
            system_message=system,
        ).with_model(provider, model)

    async def complete(
        self,
        *,
        system: str,
        prompt: str,
        session_id: str,
        task: TaskType = TaskType.CONVERSATION,
        max_tokens: int = 2048,
    ) -> str:
        """Accumulate a streamed response into a single string."""
        chat = self._chat(system, session_id, task)
        parts: list[str] = []
        async for event in chat.stream_message(UserMessage(text=prompt)):
            if isinstance(event, TextDelta):
                parts.append(event.content)
            elif isinstance(event, StreamDone):
                break
        return "".join(parts).strip()

    async def stream(
        self,
        *,
        system: str,
        prompt: str,
        session_id: str,
        task: TaskType = TaskType.CONVERSATION,
        max_tokens: int = 2048,
    ) -> AsyncIterator[str]:
        """Yield text deltas as they arrive (for SSE)."""
        chat = self._chat(system, session_id, task)
        async for event in chat.stream_message(UserMessage(text=prompt)):
            if isinstance(event, TextDelta):
                yield event.content
            elif isinstance(event, StreamDone):
                break


# ---------------------------------------------------------------------------
# Module-level convenience singletons + helpers
# ---------------------------------------------------------------------------

_provider: Optional[LLMProvider] = None


def get_provider() -> LLMProvider:
    global _provider
    if _provider is None:
        _provider = EmergentLLMProvider()
    return _provider


async def complete(
    *,
    system: str,
    prompt: str,
    session_id: str,
    task: TaskType = TaskType.CONVERSATION,
    max_tokens: int = 2048,
) -> str:
    return await get_provider().complete(
        system=system,
        prompt=prompt,
        session_id=session_id,
        task=task,
        max_tokens=max_tokens,
    )


def stream(
    *,
    system: str,
    prompt: str,
    session_id: str,
    task: TaskType = TaskType.CONVERSATION,
    max_tokens: int = 2048,
) -> AsyncIterator[str]:
    return get_provider().stream(
        system=system,
        prompt=prompt,
        session_id=session_id,
        task=task,
        max_tokens=max_tokens,
    )


def _extract_json(text: str):
    """Best-effort parse of a JSON object/array from an LLM response."""
    text = text.strip()
    # 1) fenced ```json ... ``` block
    m = _JSON_FENCE_RE.search(text)
    if m:
        candidate = m.group(1).strip()
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass
    # 2) raw parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # 3) slice between first/last brace or bracket
    for open_c, close_c in (("{", "}"), ("[", "]")):
        start = text.find(open_c)
        end = text.rfind(close_c)
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                continue
    raise ValueError("Could not parse JSON from LLM response")


async def complete_json(
    *,
    system: str,
    prompt: str,
    session_id: str,
    task: TaskType = TaskType.ACTION_EXTRACTION,
    max_tokens: int = 3000,
):
    """Run a completion and parse strict JSON out of it.

    We append a firm instruction to return JSON only and then robustly extract
    it (handles markdown fences / stray prose).
    """
    hardened_system = (
        system
        + "\n\nIMPORTANT: Respond with ONLY valid JSON. No markdown, no prose, "
        "no explanation before or after the JSON."
    )
    raw = await complete(
        system=hardened_system,
        prompt=prompt,
        session_id=session_id,
        task=task,
        max_tokens=max_tokens,
    )
    return _extract_json(raw)
