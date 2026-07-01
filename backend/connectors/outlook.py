"""Outlook / Microsoft 365 connectors (mail + calendar).

Try Microsoft Graph (when Azure creds are set + account connected); otherwise
return an empty (not-connected) result so nothing is fabricated for real users.
"""

from .base import BaseConnector, ConnectorResult


class OutlookMailConnector(BaseConnector):
    provider = "outlook_mail"
    name = "Outlook Mail"

    async def fetch(self, user_id: str, profile: dict) -> ConnectorResult:
        try:
            from services.microsoft_api import outlook_important
            real = await outlook_important(user_id)
            if real is not None:
                return ConnectorResult(self.provider, True, real)
        except Exception:
            pass
        return ConnectorResult(self.provider, False,
                               {"emails": [], "important": [], "unread_count": 0})


class OutlookCalendarConnector(BaseConnector):
    provider = "outlook_calendar"
    name = "Outlook Calendar"

    async def fetch(self, user_id: str, profile: dict) -> ConnectorResult:
        try:
            from services.microsoft_api import outlook_events
            real = await outlook_events(user_id)
            if real is not None:
                return ConnectorResult(self.provider, True, real)
        except Exception:
            pass
        return ConnectorResult(self.provider, False, {"events": [], "primary_event": None})
