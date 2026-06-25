"""Skill routes: Jobs, Class, Founder/Aegisure, Smart Home."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from config import get_db
from auth import get_current_user
from services.skills import jobs as jobs_skill
from services.skills import class_skill
from services.skills import founder as founder_skill
from services.skills import smarthome
from services.skills import detect as skill_detect

router = APIRouter()


@router.get("/skills/relevant")
async def skills_relevant(user: dict = Depends(get_current_user)):
    return {"skills": await skill_detect.relevant_skills(user["id"])}


async def _profile(user):
    db = get_db()
    return await db.profiles.find_one({"user_id": user["id"]}) or {}


# ------------------------------- Jobs -------------------------------
class StatusBody(BaseModel):
    status: str


@router.get("/jobs")
async def jobs_overview(user: dict = Depends(get_current_user)):
    return await jobs_skill.get_overview(user["id"], await _profile(user))


@router.get("/jobs/best-resume")
async def jobs_best_resume(user: dict = Depends(get_current_user)):
    return {"resume": await jobs_skill.best_resume(user["id"])}


class JobSearchBody(BaseModel):
    keywords: str | None = None
    location: str | None = None
    limit: int | None = 8


class JobSaveBody(BaseModel):
    job: dict


@router.post("/jobs/search")
async def jobs_search(body: JobSearchBody, user: dict = Depends(get_current_user)):
    return await jobs_skill.search_matches(
        user["id"], await _profile(user), body.keywords, body.location, body.limit or 8)


@router.post("/jobs/save")
async def jobs_save(body: JobSaveBody, user: dict = Depends(get_current_user)):
    return await jobs_skill.save_match(user["id"], body.job)


@router.post("/jobs/{job_id}/status")
async def jobs_set_status(job_id: str, body: StatusBody, user: dict = Depends(get_current_user)):
    res = await jobs_skill.set_status(user["id"], job_id, body.status)
    if not res:
        raise HTTPException(status_code=400, detail="Invalid job or status")
    return res


@router.post("/jobs/{job_id}/recruiter-reply")
async def jobs_recruiter_reply(job_id: str, user: dict = Depends(get_current_user)):
    return await jobs_skill.draft_recruiter_reply(user["id"], job_id, await _profile(user))


# ------------------------------- Class ------------------------------
class AssignmentBody(BaseModel):
    title: str
    course: str | None = None
    due: str | None = None
    priority: str | None = "medium"


class NoteBody(BaseModel):
    note: str


@router.get("/class")
async def class_overview(user: dict = Depends(get_current_user)):
    return await class_skill.overview(user["id"])


@router.post("/class/assignments")
async def class_add_assignment(body: AssignmentBody, user: dict = Depends(get_current_user)):
    return await class_skill.add_assignment(user["id"], body.model_dump(exclude_none=True))


@router.post("/class/assignments/{aid}/status")
async def class_assignment_status(aid: str, body: StatusBody, user: dict = Depends(get_current_user)):
    res = await class_skill.set_assignment_status(user["id"], aid, body.status)
    if not res:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return res


@router.post("/class/assignments/{aid}/study-plan")
async def class_study_plan(aid: str, user: dict = Depends(get_current_user)):
    return await class_skill.study_plan(user["id"], aid, await _profile(user))


@router.post("/class/{class_id}/professor-reply")
async def class_prof_reply(class_id: str, body: NoteBody, user: dict = Depends(get_current_user)):
    return await class_skill.professor_reply(user["id"], class_id, body.note, await _profile(user))


# ------------------------------ Founder -----------------------------
class TaskBody(BaseModel):
    title: str
    priority: str | None = "medium"


class TopicBody(BaseModel):
    topic: str | None = None


@router.get("/founder")
async def founder_overview(user: dict = Depends(get_current_user)):
    return await founder_skill.overview(user["id"])


@router.post("/founder/tasks")
async def founder_add_task(body: TaskBody, user: dict = Depends(get_current_user)):
    return await founder_skill.add_task(user["id"], body.model_dump(exclude_none=True))


@router.post("/founder/tasks/{tid}/status")
async def founder_task_status(tid: str, body: StatusBody, user: dict = Depends(get_current_user)):
    res = await founder_skill.set_task_status(user["id"], tid, body.status)
    if not res:
        raise HTTPException(status_code=404, detail="Task not found")
    return res


@router.post("/founder/checklist/{cid}/toggle")
async def founder_toggle_checklist(cid: str, user: dict = Depends(get_current_user)):
    res = await founder_skill.toggle_checklist(user["id"], cid)
    if not res:
        raise HTTPException(status_code=404, detail="Checklist item not found")
    return res


@router.post("/founder/draft-post")
async def founder_draft_post(body: TopicBody, user: dict = Depends(get_current_user)):
    return await founder_skill.draft_post(user["id"], body.topic, await _profile(user))


@router.post("/founder/summarize-metrics")
async def founder_metrics(user: dict = Depends(get_current_user)):
    return await founder_skill.summarize_metrics(user["id"], await _profile(user))


# ----------------------------- Smart Home ---------------------------
class DeviceStateBody(BaseModel):
    state: dict


class HomeRoutineBody(BaseModel):
    name: str
    actions: str | None = ""


@router.get("/home")
async def home_overview(user: dict = Depends(get_current_user)):
    return await smarthome.overview(user["id"])


@router.put("/home/devices/{device_id}")
async def home_set_device(device_id: str, body: DeviceStateBody, user: dict = Depends(get_current_user)):
    res = await smarthome.set_device_state(user["id"], device_id, body.state)
    if res.get("error") == "not_found":
        raise HTTPException(status_code=404, detail="Device not found")
    return res


@router.post("/home/morning-routine")
async def home_morning(user: dict = Depends(get_current_user)):
    return await smarthome.run_morning_routine(user["id"])


@router.post("/home/routines")
async def home_add_routine(body: HomeRoutineBody, user: dict = Depends(get_current_user)):
    return await smarthome.add_routine(user["id"], body.model_dump(exclude_none=True))
