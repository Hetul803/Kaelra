# Kaelra Daily Operator (v0) — Development Plan (Updated)

## 1) Objectives
- Deliver a **logged-in full-stack production-ready app** (FastAPI + React + MongoDB) for **Kaelra**, a **personal AI operator** (not a chatbot wrapper): proactive, warm, deterministic, and safe.
- Keep a **deterministic system core** (memory, routines, actions, permissions, audit logs, device sync) with an **LLM reasoning layer** (Claude Sonnet 4.5) and a **connector/integration layer**.
- Support **real Google integrations** (Calendar/Gmail/Drive) via OAuth + token storage, with **graceful fallbacks only when credentials are missing or API calls fail**.
- Support **real premium voice** via **ElevenLabs TTS** (backend-proxied) with **browser Web Speech API fallback** for TTS and STT.
- Make Kaelra feel like an OS: after connecting sources, run a **Context Builder** that indexes connected sources, proposes memories, and prepares actions with approval gates.
- Provide **Skill dashboards** (Jobs, Class, Founder/Aegisure Workspace, Smart Home) that integrate with Action Queue + audit logging and are **real-data-ready**.

---

## 2) Implementation Steps

### Phase 1 — Core POC (Isolation) — ✅ COMPLETE
**Result:** `test_core.py` passed ALL 3 checks — (1) warm personal daily briefing from structured context, (2) valid JSON action proposals with correct sensitive/approval flags, (3) file summary + deadlines/people/action-items extraction. LLM abstraction (`llm/` package: provider.py + router.py) built with Claude Sonnet 4.5 (`anthropic/claude-sonnet-4-5-20250929`) via Emergent key. Streaming + `complete_json` helpers ready.

### Phase 2 — V1 App Development — ✅ COMPLETE
**Result:** Full Kaelra app shipped.
- Backend (FastAPI+Mongo): deterministic system layers + LLM layer + connector abstraction + Action Queue approvals + briefing engine + device sync + audit logging.
- Frontend (React+shadcn/Tailwind): **11 core screens** (Auth, Onboarding, Today, Talk, Action Queue, Memory, Files, Routines, Connected Accounts, Devices, Settings) + premium dark glass UI + Kaelra orb + SSE streaming chat.
- Fixes: CRA/CRACO WDS shim, unicode rendering, chat stream race condition, mobile nav z-index.
- Testing: Backend 59/59, Frontend 9/9.

### Phase 3 — Stabilization, UX Polish, and Safety/Privacy Hardening — ✅ COMPLETE
**Result:** Safety/UX hardening implemented (audit log viewer, export/delete endpoints, improved loading/empty states, approval-first patterns).

### Phase 4 — Architecture Extensions (interfaces ready; implementations optional for v0) — ✅ COMPLETE
**Result:** Real-ready architecture landed.
- **Voice layer** added (ElevenLabs backend route + browser fallback).
- **Google OAuth** backend service + token storage + real API readers for Calendar/Gmail/Drive.
- **APScheduler** background engine for routines.
- **Context Builder** backend implemented with progress steps + indexing + suggested memories.
- **Four skill modules** added (Jobs, Class, Founder, Smart Home) with endpoints and Action Queue integration.

---

### Phase 5 — Real Integrations + Skill Frontends (Current Session) — 🚧 IN PROGRESS
**Context:** User will provide real credentials in secrets panel:
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `ELEVENLABS_API_KEY`
- `ELEVENLABS_VOICE_ID`

**Principle:** Use real integrations when configured; keep graceful fallbacks only if a key is missing or an API call fails.

#### P0 (Highest Priority)
1) **Real Google OAuth frontend flow (Calendar/Gmail/Drive)**
   - Update Connected Accounts screen to show a single **“Connect Google”** experience (covers Calendar + Gmail + Drive).
   - Flow:
     1. Frontend calls `GET /api/oauth/google/url?redirect_uri=<window.location.origin>/auth/google`
     2. Redirect user to Google consent screen
     3. Frontend callback page `/auth/google` parses `code` and calls `POST /api/oauth/google/callback` with `{code, redirect_uri}`
     4. Update UI connector statuses + show connected email + scopes.
   - After success: trigger Context Builder (next item).

2) **Wire ElevenLabs TTS (premium voice) + fallback**
   - Verify `/api/voice/status` reports `provider=elevenlabs` when keys are present.
   - Verify `/api/voice/tts` returns playable audio; fallback to browser `speechSynthesis` when ElevenLabs fails.
   - Persist voice preferences in Settings (voice enabled + autospeak preference) and ensure Talk respects these.

3) **Browser Web Speech API fallback for STT/TTS**
   - Ensure mic input uses Web Speech STT when available; show clear error states when not supported.
   - Ensure speaking can be stopped/muted and does not break chat streaming.

4) **Context Builder loading/indexing UI (post-Google connection)**
   - After OAuth success, show progress steps from backend `PROGRESS_STEPS`:
     - “Give me a moment — I’m learning what matters to you.”
     - “I’m organizing your context.”
     - “I’m finding important files, routines, deadlines, and people.”
     - “I’m preparing your first personal briefing.”
     - “Your Kaelra context is ready.”
   - Display summary:
     - Indexed: calendar events, important emails, drive files
     - Suggested memories (approve/reject)
     - Prepared actions (Action Queue)
     - Sources connected (“I searched the sources you connected” copy)

5) **E2E testing for real connection flow + graceful fallback**
   - Test with keys present:
     - Connect Google → Context Builder → Today dashboard reflects real sources
     - Talk auto-speak uses ElevenLabs
   - Test with keys missing or API failure:
     - Google endpoints show configured=false / helpful errors
     - Voice falls back to browser TTS

#### P1 (Next)
6) **Talk.js voice UI polish + verification**
   - Confirm mic toggle, listening state/orb state, auto-speak toggle, stop speaking, and fallback behavior.
   - Ensure no regressions in streaming chat, history, new-chat cancellation.

7) **Skill Frontends (4 dashboards)**
   - Build and route pages for:
     - Jobs / Career (`/jobs`)
     - Class / School (`/class`)
     - Founder / Aegisure Workspace (`/founder`)
     - Smart Home (`/home`)
   - Each skill UI must include:
     - Dashboard section/screen (matching design_guidelines)
     - Prepared actions + Action Queue integration
     - Demo fallback behavior (already supported by backend)
     - Real-data-ready architecture (connector abstraction maintained)
     - Audit logging visibility via existing settings audit trail

8) **Privacy + Context controls in Settings**
   - Add controls:
     - Disconnect Google
     - Pause/resume indexing
     - Delete indexed data
     - Review/approve/reject suggested memories
   - Privacy language:
     - “I searched the sources you connected.”
     - Clear source list + disconnect behavior

9) **Onboarding copy updates + full E2E (desktop + mobile)**
   - Update onboarding and connected-accounts messaging to reflect real integrations and Context Builder.
   - Run full E2E across desktop + mobile layouts.

---

## 3) Next Actions (Updated)
1) Implement **Google OAuth frontend wiring** (Connected Accounts + `/auth/google` callback) and confirm authorized redirect URIs.
2) Add **Context Builder post-connect loading + summary UI**.
3) Verify **ElevenLabs** end-to-end in Talk with fallback + preference persistence.
4) Run **E2E testing** of connection/indexing/briefing and fallback paths.
5) Build **4 skill dashboards** and add missing routes.
6) Expand **Settings privacy/context controls** (disconnect/pause/delete/review suggestions).

---

## 4) Success Criteria (Updated)
- **Integration success:**
  - Google OAuth connects reliably; Calendar/Gmail/Drive data loads when connected.
  - Redirect URIs configured correctly; tokens stored; disconnect works.
- **Voice success:**
  - ElevenLabs TTS works when keys present; browser fallback works when not.
  - User can start/stop listening and stop speaking; preferences persist.
- **Context success:**
  - After connecting sources, Context Builder shows progress states and produces:
    - Indexed counts
    - Suggested memories (reviewable/approvable)
    - Prepared actions (approval gated)
- **Product success:**
  - Today dashboard + briefing incorporate real calendar/email/drive context where available.
  - Skill dashboards render correctly, prepare actions, and log to audit.
- **Safety & privacy success:**
  - Kaelra only references connected sources; users can disconnect and delete indexed data.
  - Sensitive actions (email drafts/lock controls/etc.) always go through Action Queue approval gates.

---

## Google OAuth Redirect URIs to Register (Google Cloud Console)
Because the frontend computes `redirect_uri = window.location.origin + "/auth/google"`:
1) **Emergent preview app:**
   - `https://kaelra-operator.preview.emergentagent.com/auth/google`
2) **Future production:**
   - `https://<your-production-frontend-domain>/auth/google`

> Note on scopes: current backend config uses Drive *read* scope (`drive.readonly`) to support indexing and “find best resume” scenarios. If you want strict least-privilege `drive.file`, we can switch, but it may prevent reading existing resumes not created by Kaelra.