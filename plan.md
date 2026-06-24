# Kaelra Daily Operator (v0) — Development Plan (Updated)

## 1) Objectives
- Deliver a **logged-in full-stack production-ready app** (FastAPI + React + MongoDB) for **Kaelra**, a **personal AI operator** (not a chatbot wrapper): proactive, warm, deterministic, and safe.
- Keep a **deterministic system core** (memory, routines, actions, permissions, approval gates, audit logs, device sync) with an **LLM reasoning layer** (Claude Sonnet 4.5) and a **connector/integration layer**.
- Support **real Google integrations** (Calendar/Gmail/Drive) via OAuth + token storage, with **graceful fallbacks only when credentials are missing or API calls fail**.
- Support **real premium voice** via **ElevenLabs TTS** (backend-proxied) with **browser Web Speech API fallback** for TTS and STT.
- Make Kaelra feel effortless and “AGI-like” by making **Kaelra the home**, with **context learned from connected sources + ongoing behavior**, not questionnaires.
- Run a **Context Builder** after connecting sources: index connected sources, propose memories (user-approved), and prepare actions with approval gates.
- Provide **skill capabilities** (Jobs, Class, Founder, Smart Home) that are **real-data-ready**, but only surface what’s relevant per user to prevent overwhelm.
- **NEW (this batch):**
  - Implement **Continuous Background Re-index** to keep context fresh automatically (new emails/events/files) without manual rebuild.
  - Implement **real Push Notifications** (Web Push) for routines/alerts so Kaelra can reach users outside the app.
  - Add a **real jobs provider abstraction** ("LinkedIn Jobs" via third-party API) with env-key gating + strict demo-only mock fallback.
  - Preserve a **clean-slate new-user experience** (no mock data in real accounts; demo remains rich).

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
  - **PKCE fix:** resolved `invalid_grant (Missing code verifier)` by disabling PKCE auto-generation for confidential web-client flow. **Do not re-enable PKCE.**
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

### Phase 7 — Always-fresh Kaelra (Continuous Re-index + Push) + Jobs Provider — ⏳ PENDING (APPROVED / NEXT)
**Trigger:** User approved this batch.

#### Phase 7.1 — Continuous Background Re-index (APScheduler) — ⏳ PENDING
**Goal:** Automatically keep Kaelra’s index and “what matters” feed current as new items appear, without requiring a manual Context Builder rebuild.

**Design principles**
- **Deterministic & cheap:** no LLM in the background pass.
- **Baseline-first to avoid spam:** on first run after enabling, record cursors (latest email/event/file) but do **not** emit notifications for historical items.
- **Privacy-first:** only for connected sources; respect `context_state.indexing_paused`.
- **Mock isolation:** never create demo-like items for real users.

**Backend implementation**
- Add `services/reindex.py`:
  - `ensure_baseline(user_id)` stores cursors: `gmail_last_seen`, `calendar_last_seen`, `drive_last_seen`.
  - `poll_once(user_id)` fetches latest items and detects **new** ones since cursor.
  - `emit_notification(...)` creates an in-app notification (existing `notifications` collection).
  - `emit_feed_note(...)` optional: rely on notifications as feed items (feed already includes recent notifications).
- Add cursor fields in `context_state` document (no schema migration required, just `$set`).
- Add APScheduler job `reindex_tick` (e.g., every 2–5 minutes):
  - Iterate users with indexing enabled + google connected.
  - For each, run `poll_once` safely with timeouts.
- Implement Google “delta style” polling using existing readers (v0):
  - Gmail: compare message IDs returned by `gmail_important` list; track top N IDs.
  - Calendar: compare event IDs for today + next few days (simple lookahead); track IDs.
  - Drive: compare file IDs from `drive_files` (recently modified).

**Outputs**
- New important email → notification + feed item via notifications.
- Meeting soon (e.g., within 60–90 minutes) → notification.
- New/changed Drive docs needing attention → notification.

#### Phase 7.2 — Real Push Notifications (Web Push) for routines/alerts — ⏳ PENDING
**Goal:** Deliver Kaelra’s proactive reminders outside the app (browser push) with no third-party push vendor.

**Tech**
- Web Push + VAPID using:
  - `pywebpush==2.0.0`
  - `py-vapid==1.9.2`
- Store subscriptions in Mongo by `user_id` + device.

**Backend implementation**
- Add env vars:
  - `VAPID_PRIVATE_KEY_PEM` (PEM) **or** file path-based loading (choose one; keep simple).
  - `VAPID_SUBJECT` (e.g., `mailto:admin@kaelra.ai`).
- Add `services/push.py`:
  - `get_public_key()` returns applicationServerKey (base64url for uncompressed point).
  - `save_subscription(user_id, sub, device_id)`.
  - `send_push(user_id, title, body, data={...})` iterates active subscriptions.
  - Handle invalid subscriptions (410/404) by deleting them.
- Add routes `routes/push.py`:
  - `GET /api/push/vapid-public-key`
  - `POST /api/push/subscribe`
  - `POST /api/push/unsubscribe`
  - `POST /api/push/test` (dev-only or guarded) to verify delivery.
- Wire push delivery into existing notification creation:
  - Update scheduler `_notify(...)` to also call `push.send_push(...)` **when** `profile.notifications_enabled` is true and a subscription exists.
  - Update reindex emission similarly.

**Frontend implementation**
- Add service worker `/public/sw.js`:
  - `self.addEventListener('push', ...)` show notification.
  - `notificationclick` focuses/open Kaelra app.
- Add client helper `src/lib/push.js`:
  - Register SW.
  - Fetch vapid key from backend.
  - Subscribe with `PushManager.subscribe`.
  - Send subscription to backend along with a stable `device_id`.
- Update Settings:
  - Add a “Push notifications (browser)” section:
    - Toggle to enable/disable.
    - If unsupported (Safari/HTTP), show graceful copy.
    - Button “Test notification”.

#### Phase 7.3 — Jobs Provider: “LinkedIn Jobs” via third-party API + Search UI — ⏳ PENDING
**Reality check (documented):** LinkedIn does not provide a broadly-available public job search API; implement via a third-party provider.

**Backend implementation**
- Add `services/jobs_providers/`:
  - Interface: `search(profile, keywords, location, limit)`.
  - Provider 1: `jsearch` (OpenWeb Ninja / RapidAPI JSearch) using `httpx`.
  - Provider 2: mock connector (existing) — **demo only**.
- Env vars:
  - `JSEARCH_API_KEY` (or RapidAPI key + host header depending on chosen endpoint)
  - `JOB_PROVIDER=jsearch|mock`
- Normalization to existing job shape:
  - `{title, company, location, salary, match, tags, url}`
  - Store results into `jobs` collection with id, status pipeline.
- Add endpoints:
  - `POST /api/jobs/search` (returns normalized matches; optional `persist=true`)
  - Keep existing `/api/jobs` overview endpoints.

**Frontend implementation**
- Extend Jobs page:
  - Add a compact “Search jobs” panel: keywords + location + search.
  - Results list uses existing JobCard style.
  - “Save” action persists to pipeline.
- Preserve clean Kaelra home:
  - No job results should appear unless user searches or Kaelra has real signals.

#### Phase 7.4 — Clean-slate new-user experience hardening + wipe script — ⏳ PENDING
**Goal:** Ensure user can test as a completely new, unknown user without any mock leakage.

**Backend tasks**
- Audit all seed/provision paths:
  - Confirm **all** mock provisioning remains strictly behind `is_demo=True`.
- Add `scripts/wipe_non_demo.py`:
  - Deletes all users where `is_demo != True` and all their related docs.
  - Keeps demo operator intact.
  - Optionally allow `--email` or `--user_id` targeted wipe.

**Verification checklist**
- New signup → Kaelra Home shows empty feed + warm greeting + Google connect CTA.
- Skills sidebar shows none until real context exists (or user creates data).
- No demo calendar/email/files appear.
- Context Builder rebuild clears stale cache and regenerates briefing from real sources.

---

## 3) Next Actions (Updated)
1) **Implement Phase 7** in this order:
   1. Backend reindex service + scheduler job
   2. Backend web-push service + routes + scheduler wiring
   3. Jobs provider abstraction + Jobs search endpoint
   4. Frontend service worker + subscription UI + settings controls
   5. Frontend Jobs search UI
2) **Testing & QA**
   - Backend unit/API tests for:
     - Reindex cursor baseline behavior
     - Push subscription create/delete + send
     - Jobs search provider fallback behavior
   - Frontend validation:
     - Push subscription works (supported browsers)
     - Kaelra home stays decluttered for fresh users
   - E2E regression pass (desktop + mobile)
3) **Wipe non-demo accounts** using wipe script so the user can test as a brand-new user.

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
- **Always-fresh success (NEW):**
  - Background reindex detects only **new** emails/events/files after baseline.
  - Emits in-app notifications (and feed items via notifications).
  - Respects indexing pause and connected-account status.
- **Push success (NEW):**
  - Web Push subscription stored per user/device.
  - Routine fires → in-app notification + web push delivered when enabled.
  - Invalid subscriptions cleaned up automatically.
- **Jobs provider success (NEW):**
  - Real provider path works when API key set.
  - Graceful mock fallback exists **only** for demo or when configured explicitly.
  - No job mock data appears for real new users.
- **Kaelra-first product success:**
  - Kaelra is the home; dashboard is the control panel.
  - Skills are auto-detected; only relevant ones are shown to prevent overwhelm.
  - Feed items open a Kaelra-spoken + structured-card experience.
- **Safety & privacy success:**
  - Sensitive actions always go through Action Queue approval gates.
  - Users can disconnect, pause indexing, delete indexed data, review suggested memories.

---

## Google OAuth Redirect URIs to Register (Google Cloud Console)
Because the frontend computes `redirect_uri = window.location.origin + "/auth/google"`:
1) **Emergent preview app:**
   - `https://kaelra-operator.preview.emergentagent.com/auth/google`
2) **Future production:**
   - `https://<your-production-frontend-domain>/auth/google`

> Scope choice: currently using **Drive read-only** (`drive.readonly`) to support indexing + “find best resume” scenarios. A stricter `drive.file` can be offered later as an optional privacy mode for public users.

---

## Constraints / Non-negotiables (Engineering Guardrails)
- **Do not re-enable Google PKCE** (`autogenerate_code_verifier=False` must remain) for the confidential web client flow.
- **Do not change** `REACT_APP_BACKEND_URL` / `MONGO_URL` wiring.
- **Mock data must remain strictly gated** to `is_demo=True`.
- Keep Kaelra dark-glass design system (teal primary, amber accent); avoid purple gradients.
