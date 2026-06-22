# Kaelra Daily Operator (v0) — Development Plan

## 1) Objectives
- Deliver a **logged-in full-stack app** (FastAPI + React + MongoDB) for “Kaelra Daily Operator” that feels like a **personal operating system** (not chatbot UI).
- Prove the **core reasoning engine** works in isolation using **Claude Sonnet 4.5** (`anthropic/claude-sonnet-4-5-20250929`) via **Emergent Universal LLM Key** + `emergentintegrations`, with a **model-provider abstraction**.
- Implement deterministic system layers: **memory, routines, reminders/notifications (model), action queue w/ approvals, device sync records, audit logs**, and **background daily briefing precompute + cache**.
- Use **placeholder connectors** (Calendar/Gmail/Drive/Maps) with realistic demo data + clean interfaces for future OAuth.
- Support **real file upload + AI summarization/extraction** (action items, deadlines, people, key context).
- Ship all **11 core screens**, demo user “Hetul”, streaming chat, voice-ready UI, and strong privacy controls.

---

## 2) Implementation Steps

### Phase 1 — Core POC (Isolation) — ✅ COMPLETE
**Result:** `test_core.py` passed ALL 3 checks on first run — (1) warm personal daily briefing from structured context, (2) valid JSON action proposals with correct sensitive/approval flags, (3) file summary + deadlines/people/action-items extraction. LLM abstraction (`llm/` package: provider.py + router.py) built with Claude Sonnet 4.5 (`claude-sonnet-4-5-20250929`) via Emergent key. Streaming + `complete_json` helpers ready.

### Phase 1 (original) — Core POC (Isolation; do not proceed until SUCCESS)
**Goal:** validate the make-or-break “Kaelra reasoning engine” loop end-to-end via a single script.
- Web research (quick) on: best practices for **structured JSON extraction** + **prompting for action proposals** with Claude.
- Add backend env: `EMERGENT_LLM_KEY=...`; confirm `emergentintegrations` import.
- Implement **LLM provider abstraction** (interface + Claude provider) with **streaming default**, plus a helper for “structured JSON only” responses.
- Create `test_core.py` that proves:
  1) Warm, personal **daily briefing** generated from **structured demo context** (calendar/email/goals/routines/actions/devices).
  2) **Action suggestions** returned as strict JSON parseable into Action Queue items.
  3) **File text summarization** + extraction of people/deadlines/action items into structured JSON.
- Iterate prompts/parsers until:
  - JSON is consistently valid.
  - Briefing quality is “instant-ready” and matches Kaelra tone.

**User stories (Phase 1):**
1. As a user, I want Kaelra to generate a warm daily briefing from my schedule/goals so I instantly know what matters.
2. As a user, I want Kaelra to propose actions as structured items so I can approve them safely.
3. As a user, I want Kaelra to summarize a file and extract deadlines so I don’t miss obligations.
4. As a user, I want the system to cache a briefing so asking later feels instant.
5. As a user, I want Kaelra’s outputs to be consistent and parseable so the product is reliable.

---

### Phase 2 — V1 App Development (Build around proven core; delay real OAuth/voice providers)
**Goal:** create the working product experience with minimal mocks (only for external connectors/voice execution).
- **Call `design_agent`** for Kaelra UI guidelines (dark elegant, glass cards, gradients, orb presence, motion).
- Backend foundations (FastAPI + MongoDB):
  - Collections + models: users, profiles, devices, connected_accounts, memories, goals, routines, places, daily_briefings, conversation_sessions, messages, actions, notifications, files, file_summaries, skill_runs, audit_log, user_feedback.
  - Seed script: demo user **Hetul** with realistic connected data, files, routines, actions.
  - Connector interfaces + mock implementations: Calendar/Gmail/Drive/Maps producing realistic data + `skill_runs` logging.
  - **Briefing engine**: background job + on-demand regeneration; store cached daily briefings; “last updated” metadata.
  - Action Queue service: create actions from LLM suggestions; enforce **approval for sensitive actions**; audit log every transition.
  - File service: upload, text extraction (pdf/docx/txt), store, summarize via LLM, store file_summaries + derived actions.
  - Chat service: streaming SSE; conversation storage; context injection from memory/routines/today snapshot; tool/skill hooks to propose actions.
  - Device service: register/update device heartbeat; expose sync status.
- Frontend (React, mobile-first, premium desktop command center):
  - Implement 11 screens + navigation shell (Today as default).
  - Today Dashboard cards: briefing, schedule, important emails, reminders, commute placeholder, news, goals, files needing attention, action queue preview, device sync status.
  - Talk to Kaelra: streaming chat, suggested prompts, voice button (UI only), orb/presence.
  - Action Queue: approve/reject/edit/snooze; status filters; show “why” + sources.
  - Memory + Routines/Notifications: CRUD flows, “forget” controls.
  - Connected Accounts/Devices/Settings: placeholder connector states; permissions + privacy.

**Conclude Phase 2:** run 1 round of end-to-end testing (signup/demo login → dashboard → chat → actions → file upload → summaries → approvals).

**User stories (Phase 2):**
1. As a user, I want a Today dashboard that shows my day at a glance without chatting.
2. As a user, I want Kaelra to prepare actions and require my approval before anything sensitive happens.
3. As a user, I want to upload a syllabus/resume/email PDF and immediately get a summary + extracted action items.
4. As a user, I want Kaelra to remember preferences and routines and use them in briefings.
5. As a user, I want to start with a demo account that feels alive and realistic.

---

### Phase 3 — Stabilization, UX Polish, and Safety/Privacy Hardening
- Add robust validation + error states (empty states, loading states like “Kaelra is checking your day…”).
- Add audit log viewer (basic) + export/delete data endpoints.
- Tighten approval rules + permission model (connected accounts, memory categories).
- Improve briefing caching strategy (TTL, regeneration triggers: new file, new routine, action state changes).
- Add PWA readiness: manifest, icons, offline-friendly shell for dashboard (data may be stale).

**Conclude Phase 3:** run 1 round of end-to-end testing + regression on POC behaviors.

**User stories (Phase 3):**
1. As a user, I want to see an audit trail so I trust what Kaelra did and why.
2. As a user, I want to export or delete my data so I feel in control.
3. As a user, I want Kaelra to handle failures gracefully (LLM down, file parse fail) without breaking the app.
4. As a user, I want briefings to load instantly from cache most of the time.
5. As a user, I want Kaelra’s tone/personality settings to reflect in briefings and chat.

---

### Phase 4 — Architecture Extensions (interfaces ready; implementations optional for v0)
- Voice layer abstraction (STT/TTS provider interfaces; no provider wired).
- OAuth-ready connector framework (Google integration stubs: scopes, token store schema, sync jobs) without enabling.
- Job scheduler abstraction for periodic routines (morning briefing, email checks) with local dev-friendly scheduler.

**User stories (Phase 4):**
1. As a user, I want voice-first UX to be ready even if voice is “coming soon.”
2. As a user, I want to connect Google services later without the app needing a rewrite.
3. As a user, I want routines to run automatically and update my dashboard.
4. As a user, I want Kaelra to work consistently across devices with clear sync status.
5. As a user, I want future skills to plug in cleanly (Jobs, Classes, Founder Work).

---

## 3) Next Actions
1. Implement LLM abstraction + Claude Sonnet 4.5 wiring via `emergentintegrations` (streaming-first).
2. Write and run `test_core.py` until all 3 POC checks succeed reliably.
3. Call `design_agent` and lock UI system + component patterns.
4. Scaffold backend schema + seed demo user Hetul + mock connectors.
5. Build Today Dashboard + Talk + Action Queue + Files first (core UX loop), then remaining screens.

---

## 4) Success Criteria
- **POC success:** `test_core.py` consistently (a) generates high-quality daily briefing, (b) returns valid JSON action proposals, (c) summarizes files + extracts structured items.
- **Product success:** demo login shows a fully populated command center; briefing loads instantly from cache; streaming chat works; file upload→summary works; action approvals enforced.
- **System success:** memories/routines/actions/devices/audit logs persist correctly; connectors are swappable; privacy controls (forget/export/delete) function.
- **UX success:** feels premium, dark elegant, non-generic; clear states (“prepared actions”, “waiting approval”, “last updated”).
