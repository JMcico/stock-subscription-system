# Specification — Stock Subscription System (Hextom Take-Home)

**Source:** Hextom Software Engineer — 2nd Round Take-Home (PDF).  
**Mode:** SPEC — this document is the single source of truth for *what* we build; `tasks.md` is *how we sequence work*; `checklist.md` is *verification before submit*.

---

## 1. Purpose

Build a web application that lets authenticated users subscribe to stock price updates by email. The system validates tickers against real symbols (Yahoo Finance / `yfinance`), sends merged periodic emails (Eastern business hours), and includes per-stock **demo-only** AI Buy/Hold/Sell text. Regular users see only their subscriptions; admins see all.

---

## 2. Fixed stack (non-negotiable per brief)

| Layer | Choice |
|--------|--------|
| Backend | Python, Django, PostgreSQL |
| Frontend | React, Tailwind CSS |
| Market data | Yahoo Finance; `yfinance` acceptable; mock fallback when API fails |
| AI-assisted development | Encouraged; understanding and explainability required |

*Implementation note:* Frontend may use Vite (already in repo) as the React toolchain; requirement is **React + Tailwind**, not a specific bundler.

---

## 3. User roles & security

| Role | Capabilities |
|------|----------------|
| **Regular user** (`is_staff=False`) | Log in; CRUD **own** subscriptions only; trigger **Send Now** for single row; receive email about the specific stock price for addresses tied to their subscriptions (see §6). |
| **Admin** (`is_staff=True`) | List/view/manage **all** users’ subscriptions;  admin can delete any subscription for support. |

**Authentication:** Token-based API auth (e.g. JWT via `djangorestframework-simplejwt`) or session cookies with CSRF for SPA — **decision:** JWT + `Authorization: Bearer` for REST, with refresh strategy documented. Passwords hashed via Django defaults.

**Authorization:** Every list/detail/mutation endpoint scoped by user unless admin.

---

## 4. Functional requirements (traceability to brief)

| ID | Brief § | Requirement |
|----|---------|-------------|
| FR-1 | 1 | Web UI: form with **ticker** + **email**. Validate email format (RFC-practical). Validate ticker is a **real** symbol via `yfinance` (or agreed fallback). |
| FR-2 | 2 | Web UI: table/list of subscriptions showing **ticker**, **current price**, **email**, **Delete**, **Send Now**. |
| FR-3 | 2, 7 | **Send Now** sends one email to that subscription’s email with current price(s) for that logical send unit and **AI Buy/Hold/Sell + short reason** per stock (demo disclaimer in email body). |
| FR-4 | 3 | **Periodic send:** every **hour**, **Mon–Fri**, **09:00–17:00 America/New_York** (inclusive window — see §8). |
| FR-5 | 4 | **Merge:** same recipient email → one email with multiple tickers/lines (prices + AI per stock), not N separate emails. |
| FR-6 | 5 | Primary path: live `yfinance`; documented **mock** path when rate-limited/down. |
| FR-7 | 6 | Secure login; regular = own data only; admin = all subscriptions. |
| FR-8 | 7 | AI recommendation: exactly one of Buy / Hold / Sell + short reason per stock; lightweight integration acceptable if documented. |
| FR-9 | 8 | **One self-chosen enhancement** — see §7. |
| FR-10 | 11–12 | Deployed demo + repo; **AI usage record** maintained (extend `AI_LOG.md`). |

---

## 5. Data model (conceptual)

- **User** — Django `User` (username/email as needed for login).
- **Subscription**
  - `owner` → `User` (nullable only if brief ever allowed anonymous — **assumption:** subscriptions are always owned by the logged-in user who created them).
  - `ticker` — normalized uppercase string.
  - `subscriber_email` — email receiving updates (may differ from `User.email`; brief asks for email field on subscription).
  - `created_at`, `updated_at`.
  - `last_notified_price`.
  - `last_notified_time` — timestamp of last outbound notification (email send), nullable until first send.

**Uniqueness assumption:** `(owner, ticker, subscriber_email)` unique to avoid duplicate rows in UI (document if we relax).

---

## 6. Email merge rules

- **Grouping key:** `subscriber_email` (case-normalized) within one scheduled run.
- **Content:** For each ticker in the group: symbol, current price (and currency if available), AI line + disclaimer.
- **Send Now:** For a single subscription row, either send one email for that row only, or if other subscriptions share the same email for the same user, merge into one send — **decision:** **Merge by email across that user’s subscriptions for that click** so behavior matches periodic sends (document in README).

---

## 7. Self-chosen enhancement (proposal for v1)

**Candidate:** **Email send history** — persist each outbound send (timestamp, recipient, tickers included, trigger: `scheduled` | `send_now`, success/failure).  
**Why:** Directly supports debugging, interview demo narrative (“what was sent when”), and user trust.  
**Alternative:** Live price sparkline dashboard — higher UI effort; can swap if product preference changes.  
**Final pick:** Confirm in README + one paragraph in submission notes.

---

## 8. Scheduling specification (documented ambiguity)

- **Timezone:** `America/New_York`.
- **Days:** Monday–Friday (weekday calendar in that TZ).
- **Hours:** 09:00–17:00 inclusive of both endpoints — **interpretation:** fire at 09:00, 10:00, …, 17:00 (nine fires per day). If interview prefers half-open `[09:00, 17:00)`, adjust to eight fires; **current SPEC:** **nine hourly ticks including 5 PM**.
- **Mechanism:** Celery + Redis/RabbitMQ **or** Django-Q **or** `django-crontab` + management command — **decision:** pick one, document ops setup for deploy.
- **Idempotency:** Same hour must not double-send same subscription (use DB flag or dedupe key per period).

---

## 9. AI recommendation (lightweight)

- **Input:** Ticker, latest price.
- **Output:** JSON or structured text: `{ "signal": "Buy"|"Hold"|"Sell", "reason": "<= N chars" }`.
- **Provider:** OpenAI API (GPT-4o) — **decision:** implement one path in code, document env vars and cost.
- **Disclaimer:** Fixed footer in email: not financial advice, demo only.

---

## 10. API surface (REST, indicative)

*Exact paths in OpenAPI or README during implementation.*

- `POST /api/auth/register/` — create regular user (`is_staff=False`); body **username** (must be a valid **email** string used as login id), **password**; `User.email` is set equal to **username**; returns access + refresh JWT.
- `POST /api/auth/token/` — obtain JWT pair (username + password).
- `POST /api/auth/token/refresh/` — refresh access token.
- `GET/POST /api/subscriptions/` — list (scoped), create.
- `GET/PATCH/DELETE /api/subscriptions/:id/` — detail, update (if needed), delete.
- `POST /api/subscriptions/:id/send_now/` — enqueue or sync send.
- `POST /api/validate_ticker/` — optional dedicated endpoint for async UI validation.
- Admin: same routes with broader queryset **or** `GET /api/admin/subscriptions/` — **decision:** filter in viewset via `IsAdminUser` for list all.

---

## 11. Non-functional

- **CORS:** Allow frontend origin in dev/prod settings.
- **Secrets:** `.env` not committed; production env on host platform.
- **Logging:** Structured enough to trace email failures and yfinance mock usage.
- **Performance:** Acceptable for demo scale (hundreds of subscriptions); no premature sharding. 
- **Caching:** Implement a simple caching mechanism (e.g., Django Cache) for stock prices

---

## 12. Change control

Updates to this SPEC after review with the team: bump a **Revision** footer (date + one-line summary). First approved baseline: see git history for `spec.md`.

**Revision 0 — 2026-04-04:** Initial draft from take-home PDF + repo constraints.

**Revision 1 — 2026-04-04:** Accepted baseline after review — Regular/Admin via `is_staff`; JWT + scoped APIs; `Subscription.last_notified_price`; periodic & Send Now email merge by normalized `subscriber_email` per owner; America/New_York Mon–Fri hourly **09:00–17:00 inclusive** (nine ticks); OpenAI **GPT-4o** for Buy/Hold/Sell + reason; **Django cache** for stock prices (`spec.md` §11); `tasks.md` / `checklist.md` synchronized to this spec.
