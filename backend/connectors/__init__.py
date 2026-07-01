"""Skill / connector layer.

Every external capability (Calendar, Gmail, Drive, Maps, News, ...) implements
the same :class:`BaseConnector` interface. v0 ships mock implementations that
return realistic demo data, but because all access goes through this interface
and a connected-account state machine, real OAuth-backed connectors can be
dropped in later without touching the briefing engine, dashboard, or chat.
"""

from .base import BaseConnector, ConnectorResult
from .calendar import CalendarConnector
from .gmail import GmailConnector
from .drive import DriveConnector
from .maps import MapsConnector
from .news import NewsConnector
from .outlook import OutlookMailConnector, OutlookCalendarConnector
from .icloud import ICloudCalendarConnector

# Registry of all known connectors keyed by provider id.
CONNECTORS: dict[str, BaseConnector] = {
    c.provider: c
    for c in [
        CalendarConnector(),
        GmailConnector(),
        DriveConnector(),
        MapsConnector(),
        NewsConnector(),
        OutlookMailConnector(),
        OutlookCalendarConnector(),
        ICloudCalendarConnector(),
    ]
}

# Catalog used by the Connected Accounts screen (includes 'coming soon' ones).
CONNECTOR_CATALOG = [
    {"provider": "google_calendar", "name": "Google Calendar", "icon": "calendar", "category": "Schedule", "default_state": "connected"},
    {"provider": "gmail", "name": "Gmail", "icon": "mail", "category": "Email", "default_state": "connected"},
    {"provider": "google_drive", "name": "Google Drive", "icon": "folder", "category": "Files", "default_state": "connected"},
    {"provider": "outlook_mail", "name": "Outlook Mail", "icon": "mail", "category": "Email", "default_state": "not_connected"},
    {"provider": "outlook_calendar", "name": "Outlook Calendar", "icon": "calendar", "category": "Schedule", "default_state": "not_connected"},
    {"provider": "icloud_calendar", "name": "iCloud Calendar", "icon": "cloud", "category": "Schedule", "default_state": "not_connected"},
    {"provider": "maps", "name": "Maps / Commute", "icon": "map-pin", "category": "Location", "default_state": "connected"},
    {"provider": "news", "name": "News Briefing", "icon": "newspaper", "category": "Interests", "default_state": "connected"},
    {"provider": "notifications", "name": "Notifications", "icon": "bell", "category": "System", "default_state": "connected"},
    {"provider": "github", "name": "GitHub", "icon": "github", "category": "Developer", "default_state": "not_connected"},
    {"provider": "smart_home", "name": "Smart Home", "icon": "home", "category": "Home", "default_state": "coming_soon"},
]

__all__ = [
    "BaseConnector",
    "ConnectorResult",
    "CONNECTORS",
    "CONNECTOR_CATALOG",
]
