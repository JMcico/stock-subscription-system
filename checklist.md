# Checklist — Pre-review & submission (Hextom take-home)

Use this before opening a PR or sending the submission link. Items map to the PDF, **`spec.md` (accepted)**, and implementation.

---

## Environment & repo

- [ ] `README.md` states how to run backend (venv, migrate, worker/scheduler if any), frontend (`npm install`, `npm run dev`), and **required env vars** (DB, `OPENAI_API_KEY`, `EMAIL_*`, optional `YFINANCE_MOCK`, cache/Redis if used).
- [ ] `backend/.env` is **not** committed; `.gitignore` covers `**/.env`.
- [ ] `requirements.txt` / lockfiles match runnable deploy.
- [ ] PostgreSQL is default for local + prod (no accidental SQLite-only production).

---

## `spec.md` alignment (accepted baseline)

- [ ] **§3 Roles:** Regular = `is_staff=False` (own subscriptions, Send Now on own rows); Admin = `is_staff=True` (all subscriptions, delete any). JWT `Authorization: Bearer` documented.  
  - *Progress:* JWT 与前端 token 存储/路由守卫已落地；**订阅级** Regular/Admin 行为待实现。
- [ ] **§5 Model:** `Subscription` includes **`last_notified_price`** (updated on successful send per implementation/tasks).
- [ ] **§6 Merge:** Periodic + **Send Now** merge by **normalized subscriber_email** within the **same user** for that action.
- [ ] **§8 Schedule:** Mon–Fri, `America/New_York`, hourly **09:00–17:00 inclusive** (nine fires including 17:00).
- [ ] **§9 AI:** **OpenAI GPT-4o** (or documented alias); output Buy/Hold/Sell + short reason; key from env; failure behavior documented.
- [ ] **§11 Caching:** **Django cache** (or equivalent) used for **stock prices**; TTL/layers documented for dev vs prod.
- [ ] **§7 Enhancement:** Implemented and explained in README (default candidate: email send history).

---

## Requirement traceability (PDF)

- [ ] **§1** UI create: ticker + email; validated (email format + real ticker via yfinance primary path).
- [ ] **§2** UI list: ticker, **current price**, email, **Delete**, **Send Now**.
- [ ] **§2 + §7** Email: price + **Buy/Hold/Sell** + short reason per stock + demo disclaimer.
- [ ] **§3** Hourly emails Mon–Fri, 9 AM–5 PM **Eastern** — matches `spec.md` §8.
- [ ] **§4** Same recipient email + multiple tickers → **one merged** email (periodic + Send Now per §6).
- [ ] **§5** Yahoo/`yfinance` primary; **mock** documented and testable.
- [ ] **§6** Login; regular = **own** only; admin = **all** (`is_staff`).  
  - *Progress:* **Secure login + JWT + 注册/登录 UI** 已本地验证；订阅级权限待 Subscription API/UI。
- [ ] **§8** Self-chosen feature + README (what / why / value).
- [x] **§9** Stack: Django + PostgreSQL + React + Tailwind.
- [ ] **§11** Repo link + **hosted** URL work for reviewers.
- [ ] **§12** **AI usage** in `AI_LOG.md` (plan, prompts, fixes, verification).

---

## Security & data sanity

- [ ] No secrets in git history (rotate if ever committed).
- [ ] API returns **403/404** for other users’ subscription IDs (not 200 with wrong data).
- [ ] Non-admin cannot list or mutate other users’ subscriptions.
- [ ] CORS and `ALLOWED_HOSTS` correct for production URL.

---

## Functional smoke tests (manual)

- [ ] Login as **regular** (`is_staff=False`) → create subscription → list shows row with **cached-backed** price.
- [ ] Delete own row → gone; cannot access another user’s id.
- [ ] Login as **admin** → sees **all** subscriptions; can delete another user’s row (per spec).
- [ ] **Send Now** on a row: email received (or console); if same user has two subs **same email**, **one** merged email for that click (§6).
- [ ] **Periodic** job: content matches merge rules; **idempotency** — no duplicate sends for same hour after retry (§8).
- [ ] **Mock yfinance** on → UI/API still behave per docs.
- [ ] **OpenAI** failure → graceful fallback still sends email or errors clearly (per your documented behavior).

---

## Frontend quality

- [x] Tailwind used consistently; layout OK on narrow viewport.
- [x] API errors surfaced (validation, network, 401). *(登录/注册流程已验证)*

---

## Submission package

- [ ] Hosted app: production login works (not localhost-only secrets).
- [ ] Submission note: repo URL, demo URL, test credentials if allowed, pointer to enhancement in README.
- [ ] Optional: transcripts per brief.

---

## SPEC hygiene

- [ ] `spec.md` **Revision** footer updated if assumptions change after baseline.
- [x] `tasks.md` / this file updated when spec changes (keep in sync). *(Phase A 任务与验收状态已同步)*
