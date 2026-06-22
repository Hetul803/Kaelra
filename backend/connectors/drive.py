"""Mock Google Drive connector."""

from .base import BaseConnector, ConnectorResult


class DriveConnector(BaseConnector):
    provider = "google_drive"
    name = "Google Drive"

    async def fetch(self, user_id: str, profile: dict) -> ConnectorResult:
        try:
            from services.google_api import drive_files
            real = await drive_files(user_id)
            if real is not None:
                return ConnectorResult(provider=self.provider, connected=True, data=real)
        except Exception:
            pass
        files = [
            {
                "id": "dr_syllabus",
                "name": "CS-401_syllabus.pdf",
                "kind": "pdf",
                "modified": "2 days ago",
                "needs_attention": True,
                "reason": "Contains deadlines Kaelra hasn't turned into reminders yet",
            },
            {
                "id": "dr_resume",
                "name": "Hetul_Resume_2025.pdf",
                "kind": "pdf",
                "modified": "1 week ago",
                "needs_attention": False,
            },
            {
                "id": "dr_pitch",
                "name": "Aegisure_pitch_deck.pdf",
                "kind": "pdf",
                "modified": "3 days ago",
                "needs_attention": False,
            },
        ]
        return ConnectorResult(
            provider=self.provider,
            connected=True,
            data={"files": files, "needs_attention": [f for f in files if f.get("needs_attention")]},
        )
