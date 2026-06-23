# Kaelra Daily Operator (v0) — Development Plan (Updated)

## 1) Objectives
- Deliver a **logged-in full-stack production-ready app** (FastAPI + React + MongoDB) for **Kaelra**, a **personal AI operator** (not a chatbot wrapper): proactive, warm, deterministic, and safe.
- Keep a **deterministic system core** (memory, routines, actions, permissions, approval gates, audit logs, device sync) with an **LLM reasoning layer** (Claude Sonnet 4.5) and a **connector/integration layer**.
- Support **real Google integrations** (Calendar/Gmail/Drive) via OAuth + token storage, with **graceful fallbacks only when credentials are missing or API calls fail**.
- Support **real premium voice** via **ElevenLabs TTS** (backend-proxied) with **browser Web Speech API fallback** for TTS and STT.
- Make Kaelra feel effortless and “AGI-like” by making **Kaelra the home**, with **context learned from connected sources + ongoing behavior**, not questionnaires.
- Run a **Context Builder** after connecting sources: index connected sources, propose memories (user-approved), and prepare actions with approval gates.
- Provide **skill capabilities** (Jobs, Class, Founder, Smart Home) that are **real-data-ready**, but only surface what’s relevant per user to prevent overwhelm.

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

### Phase 5 — Real Integrations + Skill Frontends — ✅ COMPLETE
**Principle:** Use real integrations when configured; keep graceful fallbacks only if a key is missing or an API call fails.

**Completed deliverables:**
- **Google OAuth frontend flow** fully wired:
  - Connected Accounts → **Connect Google** → Google consent → `/auth/google` callback → token exchange.
  - **PKCE fix:** resolved `invalid_grant (Missing code verifier)` by disabling PKCE auto-generation for confidential web-client flow.
- **ElevenLabs TTS verified live** (real MP3 returned) with `ELEVENLABS_API_KEY` + `ELEVENLABS_VOICE_ID`; browser fallback retained.
- **Context Builder UX** improved:
  - Added **progress bar** + step messaging and **auto-advance** (no manual refresh).
  - Context Builder now **clears stale suggested memories + stale pending actions** and **forces a real briefing regeneration** on each build.
  - Verified connected user’s briefing/actions are derived from **real Gmail/Drive/Calendar**, not demo.
- **Mock/demo data gating (critical UX fix):**
  - Real signups now start **clean** (no mock Calendar/Gmail/Drive/Maps/News; no seeded skill data).
  - Demo operator remains “alive” via startup repair (`ensure_demo_alive`) so demo connectors stay connected.
- **Skill frontends shipped**:
  - `/jobs`, `/class`, `/founder`, `/home` dashboards built and routed.
  - Sensitive actions are approval-gated and logged (recruiter replies, professor emails, LinkedIn post drafts, door locks).
- **Settings privacy/context controls shipped**:
  - Disconnect Google, pause indexing, delete indexed data, review suggested memories.
- **Onboarding rebuilt to be frictionless**:
  - Minimal “what should I call you?” + **Connect Google** primary CTA.

**Testing:** backend + frontend E2E passes in both mock and configured modes; real ElevenLabs verified; Google OAuth verified end-to-end through callback.

---

### Phase 6 — Kaelra-first Redesign (User-aligned) — ✅ COMPLETE
**Goal:** Make Kaelra feel effortless and “movie-like” by making **Kaelra the home**, reducing dashboard clutter, auto-detecting relevant skills, and making feed items open a **Kaelra speaks + card** experience.

#### Phase 6.1 — Declutter + Skill Auto-detection + Kaelra-as-Home — ✅ COMPLETE
**Frontend / Navigation**
- Made **`/` the Kaelra Home** (`Kaelra.js`): orb presence + greeting + composer + proactive feed.
- Moved old Today dashboard to **`/dashboard`** and labeled it **Control Panel**.
- AppShell navigation regrouped:
  - **Kaelra**: Home (primary)
  - **Skills**: show only **relevant** skills (with **“Explore all skills”** toggle for discovery)
  - **Control panel**: Dashboard, Routines, Connected Accounts, Devices, Settings & Privacy

**Backend**
- Added deterministic auto-detection endpoint: `GET /api/skills/relevant`
  - Rule-based detection from indexed signals (resume/job/recruiter cues; coursework cues; founder activity; smart-home device presence).
  - Demo user returns all skills.

**Declutter behavior**
- Fresh signups remain clean and non-overwhelming: no mock cards and no unnecessary seeded skill content.

#### Phase 6.2 — Kaelra-first onboarding (Voice intro + guided connect) — ✅ COMPLETE
- Onboarding now includes **Kaelra speaking** an intro (ElevenLabs if configured; browser fallback).
- Added mute/replay control; text always visible.
- Primary CTA is still **Connect Google**, then Context Builder, then land on Kaelra home.
- **Voice defaults ON** for new signups and demo profile.

#### Phase 6.3 — Proactive Feed + “Kaelra speaks” experience — ✅ COMPLETE
**Backend**
- Added `GET /api/feed` to generate proactive feed items from real context:
  - Important emails
  - Next event
  - Files needing attention
  - Recent Kaelra notifications
  - Includes `greeting`, `pending_actions`, and structured `card` payloads.

**Frontend**
- Kaelra Home shows a **proactive feed**.
- Tapping a feed item opens **KaelraSpeaks** modal:
  - If not muted: auto-play Kaelra narration (ElevenLabs preferred) + show email/event/file card.
  - If muted: shows “You’re muted — here’s what I’d say” + text + card + Play button.
- Global mute persists through Settings (`voice_enabled`).

**Testing**
- Backend: 104/105 passed (the 1 “fail” was an outdated expectation about Google being unconfigured).
- Frontend: core flows pass; verified fresh account is clean + decluttered; demo account remains alive.

---

### Phase 7 (Deferred / Future) — Multi-account Google + Continuous Background Re-index — ⏳ PENDING
**Trigger:** Implement when requested.
- Allow connecting multiple Google accounts (multiple Gmail/Calendar/Drive sources).
- Continuous background re-index/watchers to keep context fresh without manual rebuild:
  - new important email → proactive feed item + notification
  - meeting soon → proactive feed item + notification
  - new/changed Drive docs → indexing + follow-up suggestions
- Privacy controls remain first-class: per-account disconnect, pause indexing, delete indexed data, review suggested memories.

---

## 3) Next Actions (Updated)
1) **Stabilize Kaelra-first UX** (short polish pass):
   - Ensure Kaelra Home always has an immediate response state (loading skeletons) and never requires manual refresh.
   - Ensure briefings and feed are always derived from connected sources and/or user-created data.
2) **(When requested) Phase 7:** implement multi-account Google and continuous background re-index + notification delivery.
3) Continue E2E regression testing after any major changes (desktop + mobile).

---

## 4) Success Criteria (Updated)
- **Integration success:**
  - Google OAuth connects reliably; Calendar/Gmail/Drive data loads when connected.
  - Tokens stored; disconnect works; indexing can be paused/deleted.
  - No demo/mock data appears for real users.
- **Voice success:**
  - ElevenLabs TTS works when configured; browser fallback works.
  - Global mute/stop-speaking is respected; Kaelra indicates muted state.
  - Voice defaults ON for new signups (user can mute anytime).
- **Context success:**
  - Context Builder shows progress and completes without manual refresh.
  - Context build regenerates briefing/actions from real sources and clears stale artifacts.
- **Kaelra-first product success:**
  - Kaelra is the home; dashboard is the control panel.
  - Skills are auto-detected; only relevant ones are shown to prevent overwhelm.
  - Feed items open a Kaelra-spoken + structured-card experience (not a chat-only view).
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
