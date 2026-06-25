"""Jobs provider — real third-party search (\"LinkedIn Jobs\" / JSearch via
RapidAPI) with a graceful MOCK fallback.

LinkedIn has no broadly-available public job-search API, so live results come
from a configured RapidAPI provider. Set LINKEDIN_JOBS_API_KEY to go live; until
then Kaelra returns clearly-labelled SAMPLE results so the UI is fully testable.
Results are normalized to {title, company, location, salary, match, tags, url}.
"""

from __future__ import annotations

import logging

import httpx

from config import (
    LINKEDIN_JOBS_API_KEY, LINKEDIN_JOBS_API_HOST, LINKEDIN_JOBS_API_URL, JOBS_PROVIDER,
)

logger = logging.getLogger("kaelra.jobs")

SKILL_TAGS = [
    "react", "fastapi", "python", "mongodb", "aws", "sql", "typescript", "docker",
    "kubernetes", "go", "node", "java", "kotlin", "swift", "rust", "machine learning",
    "data", "backend", "frontend", "full-stack", "devops", "graphql", "redis",
]


def configured() -> bool:
    return bool(LINKEDIN_JOBS_API_KEY)


def _provider() -> str:
    if JOBS_PROVIDER in ("linkedin", "jsearch", "mock"):
        return JOBS_PROVIDER
    return "linkedin" if configured() else "mock"  # auto


def _salary(item: dict):
    lo = item.get("job_min_salary") or item.get("min_salary") or item.get("salary_min")
    hi = item.get("job_max_salary") or item.get("max_salary") or item.get("salary_max")
    cur = item.get("salary_currency") or item.get("currency") or "USD"
    try:
        if lo or hi:
            lo_s = str(int(float(lo))) if lo else ""
            hi_s = str(int(float(hi))) if hi else ""
            dash = "-" if lo_s and hi_s else ""
            return f"{cur} {lo_s}{dash}{hi_s}".strip()
    except (TypeError, ValueError):
        pass
    return item.get("salary") or None


def _norm(item: dict, skills: list[str]) -> dict:
    title = item.get("job_title") or item.get("title") or item.get("position") or "Untitled role"
    company = (item.get("employer_name") or item.get("company") or item.get("organization")
               or item.get("company_name") or "Unknown")
    location = (item.get("job_location") or item.get("location") or item.get("job_city")
                or item.get("locations_derived") or "Remote")
    if isinstance(location, list):
        location = location[0] if location else "Remote"
    description = item.get("job_description") or item.get("description") or ""
    url = (item.get("job_apply_link") or item.get("url") or item.get("job_url")
           or item.get("apply_url") or item.get("link") or "")
    text = f"{title} {company} {location} {description}".lower()
    matched = [s for s in (skills or []) if s and s.lower() in text]
    tags = sorted(set(matched + [t for t in SKILL_TAGS if t in text]))[:6]
    score = min(0.98, 0.55 + 0.08 * len(matched) + 0.02 * len(tags))
    return {
        "title": title,
        "company": company,
        "location": location if isinstance(location, str) else "Remote",
        "salary": _salary(item),
        "match": round(score, 2),
        "tags": tags,
        "url": url,
        "description": (description or "")[:400],
    }


def _mock(keywords: str, location: str, limit: int) -> list[dict]:
    loc = location or "Remote"
    base = [
        {"title": "Backend Engineer Intern", "company": "Northwind Labs", "location": loc,
         "salary": "$40/hr", "tags": ["Python", "FastAPI", "MongoDB"], "match": 0.92,
         "url": "https://www.linkedin.com/jobs/", "description": "Build APIs with Python/FastAPI."},
        {"title": f"{(keywords or 'Software Engineer').title()}", "company": "Vela Systems",
         "location": loc, "salary": "$120k", "tags": ["Go", "APIs", "Cloud"], "match": 0.86,
         "url": "https://www.linkedin.com/jobs/", "description": "Cloud APIs and services."},
        {"title": "Platform Engineer", "company": "Lumen AI", "location": "Remote",
         "salary": "$135k", "tags": ["Python", "Kubernetes"], "match": 0.83,
         "url": "https://www.linkedin.com/jobs/", "description": "Kubernetes platform work."},
        {"title": "Full-Stack Developer", "company": "Harbor", "location": loc,
         "salary": "$110k", "tags": ["React", "Node", "SQL"], "match": 0.78,
         "url": "https://www.linkedin.com/jobs/", "description": "React + Node product team."},
        {"title": "Backend Engineer - Payments", "company": "Tessellate", "location": "Remote",
         "salary": "$125k", "tags": ["Python", "Stripe", "APIs"], "match": 0.75,
         "url": "https://www.linkedin.com/jobs/", "description": "Payments APIs at scale."},
    ]
    return base[:limit]


async def _search_rapidapi(keywords: str, location: str, limit: int, host: str, url: str) -> list[dict]:
    headers = {"x-rapidapi-key": LINKEDIN_JOBS_API_KEY, "x-rapidapi-host": host}
    if "jsearch" in host:
        endpoint = url or f"https://{host}/search"
        params = {"query": f"{keywords} in {location}".strip(), "num_pages": "1", "page": "1"}
    else:
        # LinkedIn Job Search API (RapidAPI) style
        endpoint = url or f"https://{host}/active-jb-7d"
        params = {"title_filter": keywords or "", "location_filter": location or "", "limit": str(limit)}
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(endpoint, params=params, headers=headers)
        r.raise_for_status()
        data = r.json()
    if isinstance(data, dict):
        return data.get("data") or data.get("jobs") or data.get("results") or data.get("hits") or []
    if isinstance(data, list):
        return data
    return []


async def search(keywords: str, location: str, skills: list[str], limit: int = 8) -> dict:
    prov = _provider()
    if prov == "mock":
        return {"results": _mock(keywords, location, limit), "sample": True, "provider": "mock"}
    try:
        host = LINKEDIN_JOBS_API_HOST if prov == "linkedin" else "jsearch.p.rapidapi.com"
        raw = await _search_rapidapi(keywords, location, limit, host, LINKEDIN_JOBS_API_URL)
        results = [_norm(it, skills) for it in raw[:limit] if isinstance(it, dict)]
        results = [r for r in results if r["title"]]
        results.sort(key=lambda x: x["match"], reverse=True)
        if not results:
            return {"results": _mock(keywords, location, limit), "sample": True, "provider": prov,
                    "note": "No live results right now; showing samples."}
        return {"results": results, "sample": False, "provider": prov}
    except Exception as e:  # noqa: BLE001
        logger.warning("jobs provider failed (%s); falling back to mock: %s", prov, e)
        return {"results": _mock(keywords, location, limit), "sample": True, "provider": "mock",
                "note": "Provider error; showing samples."}
