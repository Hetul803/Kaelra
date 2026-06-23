# Kaelra Daily Operator (v0) — Development Plan (Updated)

## 1) Objectives
- Deliver a **logged-in full-stack production-ready app** (FastAPI + React + MongoDB) for **Kaelra**, a **personal AI operator** (not a chatbot wrapper): proactive, warm, deterministic, and safe.
- Keep a **deterministic system core** (memory, routines, actions, permissions, audit logs, device sync) with an **LLM reasoning layer** (Claude Sonnet 4.5) and a **connector/integration layer**.
- Support **real Google integrations** (Calendar/Gmail/Drive) via OAuth + token storage, with **graceful fallbacks only when credentials are missing or API calls fail**.
- Support **real premium voice** via **ElevenLabs TTS** (backend-proxied) with **browser Web Speech API fallback** for TTS and STT.
- Make Kaelra feel effortless and “AGI-like” by making **Kaelra the home**, with **context learned from connected sources + ongoing behavior**, not from user questionnaires.
- Make Kaelra feel like an OS: after connecting sources, run a **Context Builder** that indexes connected sources, proposes memories, and prepares actions with approval gates.
- Provide skill capabilities (Jobs, Class, Founder, Smart Home) that are **real-data-ready**, but only surface what’s relevant to each user to prevent overwhelm.

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

### Phase 5 — Real Integrations + Skill Frontends (Completed) — ✅ COMPLETE
**Principle:** Use real integrations when configured; keep graceful fallbacks only if a key is missing or an API call fails.

**Completed deliverables (recent):**
- **Google OAuth frontend flow** fully wired:
  - Connected Accounts → **Connect Google** → Google consent → `/auth/google` callback → token exchange.
  - **PKCE fix**: resolved `invalid_grant (Missing code verifier)` by disabling PKCE auto-generation for confidential web-client flow.
- **ElevenLabs TTS verified live** with `ELEVENLABS_API_KEY` + `ELEVENLABS_VOICE_ID`; browser TTS fallback retained.
- **Context Builder UX** improved:
  - Added **progress bar** + step messaging and **auto-advance** (no manual refresh).
  - Context Builder now **clears stale suggested memories + stale pending actions** and **forces a real briefing regeneration** on each build.
  - Verified that a real connected user’s briefing/actions are now derived from **real Gmail/Drive/Calendar**, not demo.
- **Mock/demo data gating**:
  - Real signups now start clean (no mock calendar/email/drive/maps/news; no seeded skill data).
  - Demo operator remains “alive” via startup repair to keep demo connectors connected.
- **Skill frontends shipped**:
  - `/jobs`, `/class`, `/founder`, `/home` dashboards built and routed.
  - Sensitive actions are approval-gated and logged (recruiter replies, professor emails, LinkedIn post drafts, door locks).
- **Settings privacy/context controls** shipped:
  - Disconnect Google, pause indexing, delete indexed data, review suggested memories.
- **Onboarding rebuilt to be frictionless**:
  - Minimal “what should I call you?” + **Connect Google** primary CTA.

**Testing:** backend + frontend E2E passes in both mock and configured modes; real ElevenLabs verified; Google OAuth verified end-to-end through callback.

---

### Phase 6 — Kaelra-first Redesign (User-aligned) — 🚧 IN PROGRESS
**Goal:** Make Kaelra feel effortless and “movie-like” by making **Kaelra the home**, reducing dashboard clutter, auto-detecting relevant skills, and making notifications open a **Kaelra speaks + card** experience.

> Delivery preference: build **Phase 6.1 → 6.2 → 6.3** in sequence, and present once all are complete.

#### Phase 6.1 (P0) — Declutter + Skill Auto-detection + Kaelra-as-Home
**Frontend / Navigation**
- Make **`/` the Kaelra Home** (orb + proactive feed + conversation).
- Move current Today dashboard to **`/dashboard`** (Control Panel).
- Redirect `/talk` → `/` (Kaelra Home).
- AppShell navigation redesign:
  - **Kaelra**: Home (primary)
  - **Skills**: show only **relevant** skills for the user (hide if none)
  - **Control Panel**: Dashboard, Action Queue, Memory, Files, Routines, Connected Accounts, Devices, Settings

**Backend**
- Add a deterministic endpoint: `GET /api/skills/relevant`
  - Rule-based (v0) detection from real signals:
    - **Jobs**: recruiter/job emails, resume detected in Drive/files, job-thread activity
    - **Class**: `.edu` emails, syllabus/assignment docs, calendar class events
    - **Founder**: project docs, founder-ish tasks, repeated launch/metrics signals
    - **Smart Home**: only if a real smart-home connector is connected (v0 may remain hidden for real users)
  - Demo user can show all skills.

**Dashboard declutter**
- For real users, show only cards that have content (avoid “too much stuff”).

#### Phase 6.2 (P0) — Kaelra-first onboarding (Voice intro + guided connect)
- After signup:
  - Kaelra introduces herself **by speaking** (ElevenLabs).
  - If muted: show text “You’re muted — here’s what I’d say.” and continue.
  - Kaelra guides the user to connect Google (and later add additional accounts).
- Connect Google → Context Builder → land on Kaelra Home.

#### Phase 6.3 (P0) — Notifications + “Kaelra speaks” experience
**Backend**
- Add a notification feed generator with structured payloads:
  - Morning summary
  - Important email arrived (Gmail)
  - Meeting soon (Calendar)
  - File/document follow-up (Drive)
- Notifications include card payload references, not raw data dumps.

**Frontend**
- Kaelra Home shows a **proactive feed**.
- Tapping a feed item opens a **Kaelra speaks** view:
  - If not muted: auto-play ElevenLabs + show email/event/file card.
  - If muted: show “You’re muted — here’s what I’d say” + text + card + tap-to-play.
- Respect global mute / stop-speaking control.

#### Phase 6.4 (Later) — Multi-account Google + continuous background re-index
- Allow connecting multiple Google accounts (multiple gmail/calendar/drive sources).
- Background re-index / watchers to keep context fresh without manual rebuild.

**Testing Plan for Phase 6**
- Run targeted tests after each subphase (6.1/6.2/6.3).
- Run full E2E desktop+mobile before final presentation.

---

## 3) Next Actions (Updated)
1) Implement **Phase 6.1**:
   - Kaelra Home as `/`, Dashboard as `/dashboard`, updated AppShell nav.
   - Backend `GET /api/skills/relevant` and frontend conditional Skills menu.
   - Dashboard declutter (only show cards with content).
2) Implement **Phase 6.2**:
   - Kaelra-first onboarding with spoken intro + guided Google connect.
3) Implement **Phase 6.3**:
   - Notification feed + “Kaelra speaks” detail view with auto-voice when unmuted.
4) Full E2E tests desktop+mobile; ensure privacy language: “I searched the sources you connected.”

---

## 4) Success Criteria (Updated)
- **Integration success:**
  - Google OAuth connects reliably; Calendar/Gmail/Drive data loads when connected.
  - Tokens stored; disconnect works; indexing can be paused/deleted.
  - No demo/mock data appears for real users.
- **Voice success:**
  - ElevenLabs TTS works when configured; browser fallback works.
  - Global mute/stop-speaking is respected; Kaelra indicates muted state.
- **Context success:**
  - Context Builder shows progress and completes without manual refresh.
  - Context build regenerates briefing/actions from real sources and clears stale artifacts.
- **Kaelra-first product success (Phase 6):**
  - Kaelra is the home; dashboard becomes control panel.
  - Skills are auto-detected and only relevant ones are shown.
  - Notifications open a Kaelra-spoken + structured-card experience (not a chat-only view).
- **Safety & privacy success:**
  - Kaelra only references connected sources.
  - Users can disconnect, pause indexing, delete indexed data, and review suggested memories.
  - Sensitive actions always go through Action Queue approval gates.

---

## Google OAuth Redirect URIs to Register (Google Cloud Console)
Because the frontend computes `redirect_uri = window.location.origin + "/auth/google"`:
1) **Emergent preview app:**
   - `https://kaelra-operator.preview.emergentagent.com/auth/google`
2) **Future production:**
   - `https://<your-production-frontend-domain>/auth/google`

> Scope choice: currently using **Drive read-only** (`drive.readonly`) to support indexing + “find best resume” scenarios. A stricter `drive.file` can be offered later as an optional privacy mode for public users.
