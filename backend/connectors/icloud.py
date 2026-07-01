"""iCloud connector (placeholder / research-first).

Apple has no broad public REST API for iCloud Mail/Calendar. The feasible path
is CalDAV/CardDAV using an app-specific password (stored per user). Until that
is wired, this connector is connect-ready in the catalog and returns empty data
(never fabricated) so real users see a clean state.
"""

from .base import BaseConnector, ConnectorResult


class ICloudCalendarConnector(BaseConnector):
    provider = "icloud_calendar"
    name = "iCloud Calendar"

    async def fetch(self, user_id: str, profile: dict) -> ConnectorResult:
        # CalDAV integration (app-specific password) is the planned real path.
        return ConnectorResult(self.provider, False, {"events": [], "primary_event": None})
