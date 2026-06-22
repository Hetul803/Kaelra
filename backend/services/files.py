"""File service — extract text from uploads and summarize via the LLM."""

import io

from fastapi import UploadFile

from config import get_db, UPLOAD_DIR
from utils import new_id, now_iso, clean_doc, clean_docs
from services import kaelra
from services.audit import log_event
from services.actions import create_actions


def _extract_text(filename: str, raw: bytes) -> str:
    name = filename.lower()
    try:
        if name.endswith(".pdf"):
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(raw))
            return "\n".join((page.extract_text() or "") for page in reader.pages)
        if name.endswith(".docx"):
            import docx
            document = docx.Document(io.BytesIO(raw))
            return "\n".join(p.text for p in document.paragraphs)
        # txt / md / csv / json / code
        return raw.decode("utf-8", errors="ignore")
    except Exception as e:  # noqa: BLE001
        return f"[Kaelra could not parse this file: {e}]"


async def save_and_summarize(user: dict, upload: UploadFile) -> dict:
    db = get_db()
    user_id = user["id"]
    raw = await upload.read()
    file_id = new_id()
    safe_name = upload.filename or "upload"
    stored = UPLOAD_DIR / f"{file_id}_{safe_name}"
    try:
        stored.write_bytes(raw)
    except Exception:
        pass

    text = _extract_text(safe_name, raw)

    file_doc = {
        "id": file_id,
        "user_id": user_id,
        "name": safe_name,
        "kind": (safe_name.rsplit(".", 1)[-1].lower() if "." in safe_name else "file"),
        "size": len(raw),
        "text": text[:200000],
        "important": False,
        "created_at": now_iso(),
    }
    await db.files.insert_one(file_doc)

    profile = await db.profiles.find_one({"user_id": user_id}) or {}
    summary = await kaelra.summarize_file(profile, safe_name, text, f"file-{file_id}")

    summary_doc = {
        "id": new_id(),
        "user_id": user_id,
        "file_id": file_id,
        "summary": summary.get("summary", ""),
        "people": summary.get("people", []),
        "deadlines": summary.get("deadlines", []),
        "action_items": summary.get("action_items", []),
        "key_context": summary.get("key_context", []),
        "created_at": now_iso(),
    }
    await db.file_summaries.insert_one(summary_doc)
    await log_event(user_id, "file.summarized", f"Summarized {safe_name}", "file", file_id)

    # Turn extracted deadlines into prepared (non-sensitive) reminder actions.
    actions = []
    for d in summary.get("deadlines", [])[:5]:
        title = d.get("title") if isinstance(d, dict) else str(d)
        date = d.get("date") if isinstance(d, dict) else ""
        if title:
            actions.append({
                "type": "assignment_reminder",
                "title": f"Reminder: {title}",
                "what": f"Deadline {date} from {safe_name}",
                "why": "Extracted from a file you uploaded so you don't miss it.",
                "source": safe_name,
                "sensitive": False,
            })
    created = await create_actions(user_id, actions, origin="file_summary")

    return {
        "file": clean_doc({k: v for k, v in file_doc.items() if k != "text"}),
        "summary": clean_doc(summary_doc),
        "actions_prepared": len(created),
    }


async def list_files(user_id: str) -> list[dict]:
    db = get_db()
    files = await db.files.find({"user_id": user_id}, {"text": 0}).sort("created_at", -1).to_list(100)
    summaries = await db.file_summaries.find({"user_id": user_id}).to_list(200)
    by_file = {s["file_id"]: s for s in summaries}
    out = []
    for f in clean_docs(files):
        f["summary"] = clean_doc(by_file.get(f["id"]))
        out.append(f)
    return out


async def get_file_text(user_id: str, file_id: str) -> tuple[dict | None, str]:
    db = get_db()
    f = await db.files.find_one({"user_id": user_id, "id": file_id})
    if not f:
        return None, ""
    return clean_doc({k: v for k, v in f.items() if k != "text"}), f.get("text", "")


async def set_important(user_id: str, file_id: str, important: bool) -> dict | None:
    db = get_db()
    await db.files.update_one({"user_id": user_id, "id": file_id}, {"$set": {"important": important}})
    f = await db.files.find_one({"user_id": user_id, "id": file_id}, {"text": 0})
    return clean_doc(f)


async def delete_file(user_id: str, file_id: str) -> bool:
    db = get_db()
    res = await db.files.delete_one({"user_id": user_id, "id": file_id})
    await db.file_summaries.delete_many({"user_id": user_id, "file_id": file_id})
    return res.deleted_count > 0
