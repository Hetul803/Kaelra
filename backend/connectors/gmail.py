"""Mock Gmail connector."""

from .base import BaseConnector, ConnectorResult


class GmailConnector(BaseConnector):
    provider = "gmail"
    name = "Gmail"

    async def fetch(self, user_id: str, profile: dict) -> ConnectorResult:
        emails = [
            {
                "id": "em_adams",
                "from": "Prof. Adams",
                "from_email": "adams@university.edu",
                "subject": "Assignment 3 (REST APIs) due Friday 11:59 PM",
                "snippet": "Reminder: Assignment 3 is due Friday night. Office hours Monday 3-5 PM if you need help.",
                "important": True,
                "unread": True,
                "received": "7:42 AM",
                "needs_reply": True,
            },
            {
                "id": "em_uscis",
                "from": "USCIS",
                "from_email": "no-reply@uscis.dhs.gov",
                "subject": "Your case status: no change",
                "snippet": "There is no new update on your case at this time. We will notify you of any change.",
                "important": True,
                "unread": True,
                "received": "6:05 AM",
                "needs_reply": False,
                "monitored": "immigration",
            },
            {
                "id": "em_linkedin",
                "from": "LinkedIn Jobs",
                "from_email": "jobs@linkedin.com",
                "subject": "5 new backend roles match your profile",
                "snippet": "Backend Engineer roles near you at 3 startups and 2 mid-size companies.",
                "important": False,
                "unread": True,
                "received": "5:30 AM",
                "needs_reply": False,
            },
            {
                "id": "em_invoice",
                "from": "Stripe",
                "from_email": "receipts@stripe.com",
                "subject": "Your Aegisure subscription receipt",
                "snippet": "Payment of $29.00 succeeded for Aegisure Pro.",
                "important": False,
                "unread": False,
                "received": "Yesterday",
                "needs_reply": False,
            },
        ]
        important = [e for e in emails if e["important"]]
        return ConnectorResult(
            provider=self.provider,
            connected=True,
            data={
                "emails": emails,
                "important": important,
                "unread_count": sum(1 for e in emails if e["unread"]),
            },
        )
