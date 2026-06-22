"""Mock Maps / commute connector. Computes a leave-by time deterministically."""

from datetime import timedelta

from .base import BaseConnector, ConnectorResult, at_time, fmt_time
from utils import is_demo_user


class MapsConnector(BaseConnector):
    provider = "maps"
    name = "Maps / Commute"

    async def fetch(self, user_id: str, profile: dict) -> ConnectorResult:
        if not await is_demo_user(user_id):
            return ConnectorResult(provider=self.provider, connected=False, data={})
        commute_minutes = 29
        buffer_minutes = 0
        work_start = at_time(14, 0)
        leave_by = work_start - timedelta(minutes=commute_minutes + buffer_minutes)
        return ConnectorResult(
            provider=self.provider,
            connected=True,
            data={
                "destination": "Downtown Store",
                "event_title": "Work shift",
                "event_start": fmt_time(work_start),
                "commute_minutes": commute_minutes,
                "traffic": "light",
                "leave_by": fmt_time(leave_by),
                "leave_by_iso": leave_by.isoformat(),
                "weather": {"summary": "Clear, 72\u00b0F", "condition": "clear"},
            },
        )
