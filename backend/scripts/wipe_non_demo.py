"""DANGER: wipe all NON-demo users and their data for a clean-slate test.

Keeps the seeded demo operator (is_demo=True) intact.

Usage:
    python scripts/wipe_non_demo.py             # wipe ALL non-demo users
    python scripts/wipe_non_demo.py --email a@b.com   # wipe one user by email
"""

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import get_db  # noqa: E402

USER_COLLECTIONS = [
    "profiles", "memories", "goals", "routines", "places", "actions", "notifications",
    "files", "file_summaries", "messages", "conversation_sessions", "daily_briefings",
    "audit_log", "connected_accounts", "devices", "google_tokens", "push_subscriptions",
    "reindex_state", "context_state", "indexed_items", "suggested_memories", "jobs",
    "assignments", "classes", "home_devices", "project_tasks", "project_checklist",
    "projects", "skill_runs",
]


async def main(email: str | None = None):
    db = get_db()
    q = {"email": email.lower()} if email else {"is_demo": {"$ne": True}}
    users = await db.users.find(q).to_list(10000)
    ids = [u["id"] for u in users]
    print(f"Found {len(ids)} non-demo user(s) to wipe.")
    for c in USER_COLLECTIONS:
        res = await db[c].delete_many({"user_id": {"$in": ids}})
        if res.deleted_count:
            print(f"  {c}: deleted {res.deleted_count}")
    if ids:
        await db.users.delete_many({"id": {"$in": ids}})
    print("Done. Demo operator preserved.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--email", default=None)
    args = ap.parse_args()
    asyncio.run(main(args.email))
