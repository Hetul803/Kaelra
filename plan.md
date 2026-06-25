# Kaelra Daily Operator (v0) — Development Plan (Updated)

## 1) Objectives
- Deliver a **logged-in full-stack production-ready app** (FastAPI + React + MongoDB) for **Kaelra**, a **personal AI operator** (not a chatbot wrapper): proactive, warm, deterministic, and safe.
- Keep a **deterministic system core** (memory, routines, actions, permissions, approval gates, audit logs, device sync) with an **LLM reasoning layer** (Claude Sonnet 4.5) and a **connector/integration layer**.
- Support **real Google integrations** (Calendar/Gmail/Drive) via OAuth + token storage, with **graceful fallbacks only when credentials are missing or API calls fail**.
- Support **real premium voice** via **ElevenLabs TTS** (backend-proxied) with **browser Web Speech API fallback** for TTS and STT.
- Make Kaelra feel effortless and “AGI-like” by making **Kaelra the home**, with **context learned from connected sources + ongoing behavior**, not questionnaires.
- Run a **Context Builder** after connecting sources: index connected sources, propose memories (user-approved), and prepare actions with approval gates.
- Provide **skill capabilities** (Jobs, Class, Founder, Smart Home) that are **real-data-ready**, but only surface what’s relevant per user to prevent overwhelm.
- **NEW (this batch) — ✅ COMPLETED:**
  - Implement **Continuous Background Re-index** to keep context fresh automatically (new emails/events/files) without manual rebuild.
  - Implement **real Push Notifications** (Web Push) for routines/alerts so Kaelra can reach users outside the app.
  - Add a **real jobs provider abstraction** ("LinkedIn Jobs" via third-party API) with env-key gating + strict clean-slate behavior.
  - Deliver a **cinematic “Entity” Kaelra Home**: ambient presence, living orb, proactive feed, continuous-memory stream.
  - Ensure **self-healing greeting**: Kaelra always greets even if LLM is transiently unavailable.
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
- Backend: stable (prior single “fail” was an outdated expectation about Google being unconfigured).
- Frontend: core flows pass; verified fresh account is clean + decluttered; demo account remains alive.

---

### Phase 7 — Always-fresh Kaelra (“Entity” build): Continuous Re-index + Push + Jobs Provider + Cinematic Home — ✅ COMPLETE
**Trigger:** User approved this batch.

#### Phase 7.1 — Continuous Background Re-index (APScheduler) — ✅ COMPLETE
**Goal:** Automatically keep Kaelra’s index and “what matters” current as new items appear, without requiring a manual Context Builder rebuild.

**Design principles (implemented)**
- **Deterministic & cheap:** no LLM in the background pass.
- **Baseline-first to avoid spam:** first pass records “seen” IDs and does not notify historical items.
- **Privacy-first:** only for connected sources; respects `context_state.indexing_paused`.
- **Clean-slate:** no demo-like data is created for real users.

**Backend implementation (delivered)**
- Added `services/reindex.py`:
  - Maintains `reindex_state` per user: seen email/event/file IDs and `baseline_done`.
  - Polls connectors (Gmail/Calendar/Drive) and detects **new** items.
  - Emits in-app notifications via unified notifier.
  - **Auto-learns** lightweight **learned memories** (`memories.learned=True`, `source=email|drive|calendar`) for continuous memory consumption.
- APScheduler:
  - Added job `kaelra_reindex_tick` (runs every ~3 min).

**Outputs (delivered)**
- New important email → in-app notification (and push if enabled).
- Meeting soon → reminder notification.
- New/attention-worthy Drive doc → notification.
- Learned memories → surfaced in the Home “What I’ve learned” stream.

#### Phase 7.2 — Real Push Notifications (Web Push) for routines/alerts — ✅ COMPLETE
**Goal:** Deliver Kaelra’s proactive reminders outside the app (browser push) with no third-party push vendor.

**Tech (delivered)**
- Web Push + VAPID using:
  - `pywebpush==2.0.0`
  - `py-vapid==1.9.2`
- VAPID keys are **auto-generated at runtime** and stored in Mongo (`app_config: {id:'vapid'}`), so deployment only needs HTTPS.

**Backend implementation (delivered)**
- Added `services/push.py`:
  - `public_key()` for the browser.
  - `save_subscription/remove_subscription`.
  - `send_push` to all subscriptions (auto-cleans invalid 404/410).
- Added `services/notify.py` unified notifier:
  - Always records an in-app notification.
  - Sends Web Push when `profile.notifications_enabled` is true.
- Added routes `routes/push.py`:
  - `GET /api/push/vapid-public-key`
  - `GET /api/push/status`
  - `POST /api/push/subscribe`
  - `POST /api/push/unsubscribe`
  - `POST /api/push/test`
- Scheduler integration:
  - Routine notifications and reindex notifications route through unified notifier (in-app + push).

**Frontend implementation (delivered)**
- Added service worker `/public/sw.js`:
  - Displays notification on push.
  - `notificationclick` focuses/opens Kaelra.
- Added client helper `src/lib/push.js`:
  - Registers SW, fetches VAPID key, subscribes, stores subscription server-side.
- Settings:
  - Added **Browser alerts** card with toggle + “Test alert”.
- Kaelra Home:
  - Ambient status line can nudge “Enable alerts”.

#### Phase 7.3 — Jobs Provider: “LinkedIn Jobs” via third-party API + Search UI — ✅ COMPLETE
**Reality check (implemented):** LinkedIn does not provide a broadly-available public job search API; integration is done via a third-party provider.

**Backend implementation (delivered)**
- Added `services/skills/jobs_provider.py`:
  - Provider abstraction via RapidAPI-style endpoint (supports a LinkedIn Jobs Search API host and JSearch-like hosts).
  - **SAMPLE fallback** when no API key is configured.
- Added endpoints:
  - `POST /api/jobs/search` → returns normalized results `{title, company, location, salary, match, tags, url, description}` plus `{sample, provider}`.
  - `POST /api/jobs/save` → saves a job to pipeline.
- Clean-slate behavior:
  - SAMPLE results are clearly labeled and do not auto-pollute a fresh user’s home (user must explicitly save to persist).

**Frontend implementation (delivered)**
- Jobs page now includes a “Search live jobs” panel:
  - keywords + location inputs
  - results list
  - sample banner when key absent
  - “Save to pipeline” action

#### Phase 7.4 — Cinematic “Entity” Home + Self-healing greeting — ✅ COMPLETE
**Goal:** Make the home feel alive, present, and operator-like.

**Frontend (delivered)**
- Cinematic Kaelra Home redesign:
  - Living orb hero with presence states
  - Ambient status line (“Watching… · Learned N · Synced…”) + quick CTA
  - Always-present conversation composer (text + mic + stop)
  - Priority feed with tabs (All/Email/Calendar/Files)
  - “What I’ve learned” continuous-memory stream
  - Warm empty states for brand-new users

**Backend (delivered)**
- `GET /api/feed` enriched with:
  - `learned` + `learned_count`
  - `watching` sources + `synced_at`
- Self-healing briefing:
  - Kaelra greeting uses LLM when available; falls back to deterministic greeting if LLM fails.

#### Phase 7.5 — Clean-slate hardening + wipe script — ✅ COMPLETE
- Added `scripts/wipe_non_demo.py`.
- Executed wipe: removed **all non-demo users** (17 wiped). Confirmed:
  - only `demo@kaelra.ai` remains
  - `google_tokens` = 0
  - `push_subscriptions` = 0

**Testing results (completed)**
- Backend: high pass rate; remaining “fails” were test expectation mismatches (Google OAuth configured; sample jobs mode).
- Frontend: demo flows 100%.
- New-user flow: signup → onboarding verified in browser. (Earlier report of “signup blocked” was a false positive due to placeholder/mode mismatch.)

---

## 3) Next Actions (Updated)

### Immediate (for your fresh new-user test)
1) **Create a new account** on `/auth`.
2) Confirm new-user experience:
   - Kaelra greets warmly on onboarding.
   - One-click Google connect.
   - Kaelra Home shows empty feed + connect CTA until connected.
   - Skills auto-detected (none initially; appear after context exists).

### Deployment keys to plug in (production)
- **Google OAuth:** Client ID + Client Secret + redirect URIs. Add your Google user as a Test User in Google Cloud Console while in testing mode.
- **Jobs provider (optional for live results):** `LINKEDIN_JOBS_API_KEY` (RapidAPI). Without it, the app shows SAMPLE results.
- **ElevenLabs (optional premium voice):** `ELEVENLABS_API_KEY` + `ELEVENLABS_VOICE_ID`.
- **Web Push:** no key required (VAPID auto-generated); must deploy under **HTTPS**.

### Future / Deferred (post-v0)
- **Multi-account Google** connections (multiple Gmail/Calendar accounts simultaneously).
- **Founder/Analytics real APIs** (replace remaining mocks).
- **Mobile/native push** (iOS Safari limitations; consider a native wrapper or PWA strategies).
- **Memory consolidation** (LLM-based summarization/compaction of learned memories; privacy controls).

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
- **Always-fresh success (delivered):**
  - Background reindex detects only **new** emails/events/files after baseline.
  - Emits in-app notifications (and feed items via notifications).
  - Learns lightweight memories (learned=true) and surfaces them in Home.
  - Respects indexing pause and connected-account status.
- **Push success (delivered):**
  - Web Push subscription stored per user/device.
  - Routine fires → in-app notification + web push delivered when enabled.
  - Invalid subscriptions cleaned up automatically.
- **Jobs provider success (delivered):**
  - Provider path works when API key set.
  - Graceful SAMPLE fallback when unconfigured.
  - No job mock data appears automatically for real new users.
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
