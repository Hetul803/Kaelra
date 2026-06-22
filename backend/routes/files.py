"""Files routes — upload + AI summarization, ask-about-file, manage."""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel

from config import get_db
from auth import get_current_user
from services import files as file_service
from services import kaelra

router = APIRouter()


class AskRequest(BaseModel):
    question: str


@router.get("/files")
async def list_files(user: dict = Depends(get_current_user)):
    return await file_service.list_files(user["id"])


@router.post("/files/upload")
async def upload_file(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    return await file_service.save_and_summarize(user, file)


@router.post("/files/{file_id}/ask")
async def ask_file(file_id: str, req: AskRequest, user: dict = Depends(get_current_user)):
    meta, text = await file_service.get_file_text(user["id"], file_id)
    if not meta:
        raise HTTPException(status_code=404, detail="File not found")
    db = get_db()
    profile = await db.profiles.find_one({"user_id": user["id"]}) or {}
    answer = await kaelra.answer_about_file(profile, meta["name"], text, req.question, f"file-{file_id}")
    return {"answer": answer}


@router.put("/files/{file_id}/important")
async def toggle_important(file_id: str, important: bool = True, user: dict = Depends(get_current_user)):
    doc = await file_service.set_important(user["id"], file_id, important)
    if not doc:
        raise HTTPException(status_code=404, detail="File not found")
    return doc


@router.delete("/files/{file_id}")
async def remove_file(file_id: str, user: dict = Depends(get_current_user)):
    ok = await file_service.delete_file(user["id"], file_id)
    return {"ok": ok}
