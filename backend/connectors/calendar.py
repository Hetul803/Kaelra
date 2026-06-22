"""Mock Google Calendar connector."""

from datetime import timedelta

from .base import BaseConnector, ConnectorResult, at_time, fmt_time


class CalendarConnector(BaseConnector):
    provider = "google_calendar"
    name = "Google Calendar"

    async def fetch(self, user_id: str, profile: dict) -> ConnectorResult:
        # Real Google data when connected, else realistic demo data.
        try:
            from services.google_api import calendar_today
            real = await calendar_today(user_id)
            if real is not None:
                return ConnectorResult(provider=self.provider, connected=True, data=real)
        except Exception:
            pass
        # Deterministic, realistic "today" schedule for the demo operator.
        work_start = at_time(14, 0)
        work_end = at_time(22, 0)
        class_start = at_time(11, 0)
        class_end = at_time(12, 15)
        standup = at_time(9, 30)

        events = [
            {
                "id": "evt_standup",
                "title": "Aegisure founder sync",
                "start": fmt_time(standup),
                "end": fmt_time(standup + timedelta(minutes=30)),
                "start_iso": standup.isoformat(),
                "location": "Google Meet",
                "kind": "work",
            },
            {
                "id": "evt_class",
                "title": "CS-401 Lecture (REST APIs)",
                "start": fmt_time(class_start),
                "end": fmt_time(class_end),
                "start_iso": class_start.isoformat(),
                "location": "Hall B",
                "kind": "class",
            },
            {
                "id": "evt_work",
                "title": "Work shift",
                "start": fmt_time(work_start),
                "end": fmt_time(work_end),
                "start_iso": work_start.isoformat(),
                "location": "Downtown Store",
                "kind": "work",
            },
        ]
        return ConnectorResult(
            provider=self.provider,
            connected=True,
            data={"events": events, "primary_event": events[-1]},
        )
