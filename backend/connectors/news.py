"""Mock News connector. Returns a briefing tuned to the user's interests."""

from .base import BaseConnector, ConnectorResult
from utils import is_demo_user

_ARTICLES = {
    "AI": [
        {"title": "Anthropic ships new agent tooling for developers", "source": "TechCrunch"},
        {"title": "Open models close the gap on reasoning benchmarks", "source": "The Verge"},
    ],
    "startups": [
        {"title": "Seed rounds rebound as AI-native SaaS heats up", "source": "Crunchbase News"},
        {"title": "Solo founders are shipping faster with AI operators", "source": "Indie Hackers"},
    ],
    "backend engineering": [
        {"title": "FastAPI 0.115 brings faster startup and better typing", "source": "PyCoder's Weekly"},
        {"title": "Designing idempotent APIs: patterns that scale", "source": "InfoQ"},
    ],
    "immigration": [
        {"title": "USCIS updates processing-time estimates for work visas", "source": "Boundless"},
    ],
}


class NewsConnector(BaseConnector):
    provider = "news"
    name = "News Briefing"

    async def fetch(self, user_id: str, profile: dict) -> ConnectorResult:
        if not await is_demo_user(user_id):
            return ConnectorResult(provider=self.provider, connected=False,
                                   data={"articles": [], "interests": profile.get("interests", [])})
        interests = profile.get("interests") or ["AI", "startups", "backend engineering"]
        articles = []
        for interest in interests:
            for a in _ARTICLES.get(interest, []):
                articles.append({**a, "interest": interest})
        if not articles:
            articles = [{"title": "Your interests will shape tomorrow's briefing.", "source": "Kaelra", "interest": "general"}]
        return ConnectorResult(
            provider=self.provider,
            connected=True,
            data={"articles": articles[:6], "interests": interests},
        )
