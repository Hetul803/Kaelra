# Kaelra Daily Operator (v0) — Development Plan (Updated)

## 1) Objectives
- Deliver a **logged-in full-stack production-ready app** (FastAPI + React + MongoDB) for **Kaelra**, a **personal AI operator** (not a chatbot wrapper): proactive, warm, deterministic, safe.
- Keep a **deterministic system core** (memory, routines, actions, permissions, approval gates, audit logs, device sync) with an **LLM reasoning layer** (Claude Sonnet 4.5) and a **connector/integration layer**.
- Support **real Google integrations** (Calendar/Gmail/Drive) via OAuth + token storage, with **graceful fallbacks only when credentials are missing or API calls fail**.
- Support **real premium voice** via **ElevenLabs TTS** (backend-proxied) with **browser Web Speech API fallback** for TTS/STT.
- Make Kaelra feel “Entity-like” by making **Kaelra the home**, with **ambient presence**, **speaker-first interactions**, and **continuous background learning** from connected sources.
- Run a **Context Builder** after connecting sources: index connected sources, propose memories (user-approved), and prepare actions with approval gates.
- Ensure **excellent memory architecture**:
  - **Server-side single source of truth** (Mongo) for memories/goals/routines/actions/learned facts.
  - **Cross-device sync by default**: any device reads the same memory state via APIs.
  - Continuous ingestion → learned memories → consolidation (LLM) → durable “operator memory”.
- Provide **skill capabilities** (Jobs, Class, Smart Home) that are **real-data-ready**, surfaced only when relevant. *(Founder kept in codebase but hidden in UI for now.)*

### ✅ Completed in Phases 1–7 + Hotfixes (Phase 7.6)
- Continuous Background Re-index (APScheduler) — baseline-first (no spam), deterministic, auto-learns memories.
- Real Web Push notifications (VAPID; backend + service worker + Settings toggle).
- Jobs provider abstraction (LinkedIn/JSearch via third-party; sample fallback) + Jobs search/save UI.
- Cinematic “Entity” Kaelra Home: living orb, ambient status, proactive feed, continuous-memory stream.
- Self-healing greeting (deterministic fallback when LLM transiently fails).
- Clean-slate new-user experience (mock data strictly demo-only).
- **Phase 7.6 Hotfixes (✅ verified by testing_agent):**
  - Fixed **double-speak** (TTS de-dupe + session greeting guard).
  - Differentiated **Dashboard** into a **Control Panel** (no duplicate chat/greeting).
  - Added **News** to feed + KaelraSpeaks cards.
  - Added “**show me …**” local voice/text commands (open email/calendar/news/job pages/cards).

---

## 2) Implementation Steps

### Phase 1 — Core POC (Isolation) — ✅ COMPLETE
**Result:** `test_core.py` passed ALL 3 checks — (1) warm personal daily briefing from structured context, (2) valid JSON action proposals with correct sensitive/approval flags, (3) file summary + deadlines/people/action-items extraction.

### Phase 2 — V1 App Development — ✅ COMPLETE
**Result:** Full Kaelra app shipped.
- Backend (FastAPI+Mongo): deterministic system layers + LLM layer + connector abstraction + Action Queue approvals + briefing engine + device sync + audit logging.
- Frontend (React+shadcn/Tailwind): core screens + premium dark glass UI + orb + SSE streaming chat.

### Phase 3 — Stabilization, UX Polish, and Safety/Privacy Hardening — ✅ COMPLETE

### Phase 4 — Architecture Extensions — ✅ COMPLETE
- Voice layer, Google OAuth, APScheduler routines, Context Builder, Skills scaffolding.

### Phase 5 — Real Integrations + Skill Frontends — ✅ COMPLETE
- Real Google OAuth flow (PKCE disabled; confidential client), ElevenLabs, Context Builder improvements, mock/demo isolation.

### Phase 6 — Kaelra-first Redesign — ✅ COMPLETE
- Kaelra as Home (`/`), Control Panel at `/dashboard`, skill auto-detection, KaelraSpeaks feed UX.

### Phase 7 — Always-fresh Kaelra (“Entity” build) — ✅ COMPLETE
- Continuous re-index + auto-learning memories.
- Web Push.
- Jobs provider + search UI.
- Cinematic Home + self-healing greeting.
- Wipe script + clean-slate.

### Phase 7.6 — “Entity polish” hotfixes — ✅ COMPLETE
- **Double-speak fixed**.
- Dashboard decluttered into **Control Panel**.
- **News** added to `/api/feed` and KaelraSpeaks.
- “Show me …” local commands on Home.

---

## Phase 8 — “The Entity”: Connect-everything + Cross-device memory + Timeline (Planned)
**North star:** Kaelra becomes the single interface. Users should not have to open separate email/calendar/news apps.

### Phase 8.0 — Architecture decision: Unified Connected Sources (Foundation)
**Goal:** Support multiple accounts across multiple providers (Google, Microsoft, iCloud) feeding one shared memory/index pipeline.

**Model changes (planned)**
- Introduce/extend a unified connected source model:
  - `connected_sources` (or extend `connected_accounts`) records: `{provider, account_email, label, scopes, status, created_at, updated_at}`
  - Provider-specific token storage keyed by `{user_id, provider, account_email}`.
- Connectors aggregate over **all connected sources** for a provider and merge results.

**Pipeline changes (planned)**
- `reindex_all()` iterates all connected sources for each user.
- All connectors feed the same:
  1) indexed items → 2) learned memories → 3) consolidation → 4) feed/actions.

---

### Phase 8.1 — Multi-account Google (P1)
**Goal:** Connect multiple Gmail/Calendar/Drive accounts simultaneously.

**Backend (planned)**
- Token store: allow multiple token rows per `user_id` keyed by `account_email`.
- OAuth callback: detect account email from token/userinfo and upsert tokens for that specific source.
- Connectors: iterate all connected google sources, merge + dedupe by stable IDs.

**Frontend (planned)**
- Connected Accounts: “Add another Google account” + show list of connected Google identities.

**Success criteria**
- Two Gmail accounts connected → feed merges both without duplicates.

---

### Phase 8.2 — LLM Memory Consolidation (P1)
**Goal:** Convert high-churn learned memories into compact, durable operator memory.

**Approach (planned)**
- Consolidation job (APScheduler daily or every N hours):
  - Group learned memories by category/source/time window.
  - Ask LLM to produce:
    - canonical facts (stable)
    - preferences
    - important people/threads
    - “watch rules” suggestions
  - Write back:
    - consolidated `memories` (learned=false, important possibly true)
    - archive/mark older learned items as consolidated.

**Controls (planned)**
- Settings: allow user to pause consolidation, review changes, revert.

---

### Phase 8.3 — App-wide Wake-word + Voice Commands Everywhere (P1)
**Goal:** Kaelra can respond from anywhere in the app.

**Web constraints**
- True 24/7 background wake word requires native OS services.
- In web/PWA we can provide: wake-word while the tab/app is open (Chrome/Edge) + push notifications.

**Planned implementation**
- Add a single global Kaelra presence layer in `AppShell`:
  - one voice owner (prevents collisions)
  - optional always-listening mode (when supported)
  - commands: “show me email/calendar/news/files/jobs/memory/queue” etc.
- Continue to route most requests to `/talk` for full reasoning.

---

### Phase 8.4 — Browser Location Timeline (P1)
**Goal:** Build Kaelra’s own timeline (visits, routes) and correlate with calendar/email.

**Reasoning**
- Google Maps Timeline / Location History has no public API.
- We implement first-party capture with user permission.

**Backend (planned)**
- Collections:
  - `location_samples` (raw points)
  - `visits` (clustered places)
  - `timeline` (daily stitched narrative)
- Correlation:
  - match visits to calendar event locations
  - match visits to email timestamps (arrivals, commute patterns)

**Frontend (planned)**
- Prompt for location permission (opt-in).
- Timeline view (day/week) with Kaelra narration + “show me route” actions.

---

### Phase 8.5 — PWA + Push polish (P1)
**Goal:** Make Kaelra feel like an installed cross-device operator.

**Planned implementation**
- Add `manifest.json` (name, icons, theme colors, start_url) and improve install prompts.
- Ensure push works reliably on Android/desktop; document iOS limitations.

---

### Phase 8.6 — Microsoft/Outlook + Microsoft 365 (P1)
**Goal:** Connect Outlook mail + calendar. Build now with mock fallback; user adds Azure creds later.

**Backend (planned)**
- Add `microsoft_oauth.py` and token store (multi-account ready).
- Implement connectors:
  - `outlook_mail`
  - `outlook_calendar`
- If creds missing: sample/demo-only or clearly labeled SAMPLE responses.

**Frontend (planned)**
- Connected Accounts UI: “Connect Microsoft” + “Add another Microsoft account”.

---

### Phase 8.7 — iCloud (Planned / research-first)
**Reality constraints**
- iCloud has limited official APIs; may require app-specific passwords + CalDAV/CardDAV or private APIs.

**Planned approach**
- Add iCloud as a connect option with:
  - a placeholder connector + mock fallback
  - a research track to determine feasible integration path (CalDAV/CardDAV).

---

### Phase 8.8 — Founder skill hidden (UI)
**Requirement:** Remove Founder from UI but keep code.

**Planned changes**
- Hide Founder in skill detection + sidebar.
- Keep `/founder` route and backend services for later re-enable.

---

## Phase 9 — Entity Wiring + Cost-Aware Kaelra (IN PROGRESS)
**North star:** Kaelra is one always-present Entity. The user just talks; she navigates, controls the app, shows things, and asks "what's next" — with minimal LLM/voice spend and one unified, continuous memory.

### 9.1 — Wire "Pass 3" into the app root
- App.js: add routes `/timeline` (Protected) and `/auth/microsoft` (MicrosoftCallback); mount `<KaelraPresence />` globally.
- index.js: register the service worker on load (PWA + push).
- public/index.html: add `<link rel="manifest">`, apple-touch/theme meta.
- AppShell: add Timeline to Control panel nav; host global `<KaelraPresence />`.

### 9.2 — Entity control loop (client-side, cost-free)
- Shared `lib/kaelraCommand.js`: parse navigation/show/open/done/what-next intents locally.
- KaelraPresence: ON by default (gesture-gated), routes wake-word commands through the local router first (free), only real reasoning falls through to `/talk` (LLM).
- Home + presence speak short confirmations via **browser TTS** (`speakLocal`, free); premium ElevenLabs reserved for true replies.
- "done"/"what next" → Kaelra asks what to see next (spoken, no LLM).

### 9.3 — Connect-everything UI
- ConnectedAccounts: dedicated Microsoft 365 card (mirror Google, mock/idle until Azure creds) + multi-account Google list ("Add another Google account", per-account disconnect).

### 9.4 — Unified continuous memory UI
- Memory: consolidation panel (insights + "Consolidate now"), framed as one continuous evolution (not separate boxes).

### 9.5 — Cost optimization (backend)
- router.py: route ACTION_EXTRACTION / QUICK / PRIORITIZATION to a cheaper Haiku-class model; keep CONVERSATION/BRIEFING/DRAFT on Sonnet 4.5.
- chat.py: gate the second `actions_from_turn` LLM call behind a cheap keyword heuristic (skip for navigational/informational turns) — roughly halves per-turn LLM cost.

**Guardrails preserved:** no PKCE change, no env changes, mock/sample data stays demo-gated, dark-glass teal/amber design.

---

## 3) Next Actions (Updated)

### Immediate
- User tests as a brand-new user (clean slate) and connects Google.

### Phase 8 build order (confirmed)
1) Multi-account Google
2) LLM memory consolidation
3) App-wide wake-word/voice commands
4) Location timeline
5) PWA + push polish
6) Microsoft/Outlook connector (mock fallback until keys)
7) iCloud (research-first, placeholder + future CalDAV/CardDAV)
8) Hide Founder from UI

---

## 4) Success Criteria (Updated)
- **Entity feel**
  - Kaelra Home is speaker-first; cards show real email/event/news/file content.
  - Kaelra responds to “show me …” from the Home and (Phase 8.3) anywhere.
- **Memory excellence**
  - Unified memory store across devices.
  - Continuous ingestion + consolidation yields stable, searchable memories.
- **Connect-everything**
  - Google multi-account works; Microsoft/iCloud scaffolding exists with clear key-gating.
- **Timeline intelligence**
  - User-opt-in location timeline correlates with calendar and email.
- **Safety**
  - Approval gates remain enforced; sensitive actions never auto-send.
- **No mock leakage**
  - Mock/sample data only for demo or explicitly-labeled sample API fallbacks.

---

## Google OAuth Redirect URIs to Register (Google Cloud Console)
Because the frontend computes `redirect_uri = window.location.origin + "/auth/google"`:
1) **Emergent preview app:**
   - `https://kaelra-operator.preview.emergentagent.com/auth/google`
2) **Future production:**
   - `https://<your-production-frontend-domain>/auth/google`

> Scope choice remains **Drive read-only** (`drive.readonly`) for resume/document indexing.

---

## Constraints / Non-negotiables (Engineering Guardrails)
- **Do not re-enable Google PKCE** (`autogenerate_code_verifier=False` must remain).
- **Do not change** `REACT_APP_BACKEND_URL` / `MONGO_URL` wiring.
- **Mock/sample data must be strictly gated** to `is_demo=True` (except explicitly-labeled sample API fallbacks like Jobs search results that are not persisted unless user saves).
- Keep Kaelra dark-glass design system (teal primary, amber accent); avoid purple gradients.
