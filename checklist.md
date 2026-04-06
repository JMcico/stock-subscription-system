# Checklist — Pre-review & submission (Hextom take-home)

Use this before opening a PR or sending the submission link. Items map to the PDF, **`spec.md` (accepted)**, and implementation.

---

## Environment & repo

- [x] `README.md` states how to run backend (venv, migrate, worker/scheduler if any), frontend (`npm install`, `npm run dev`), and **required env vars** (DB, `OPENAI_API_KEY`, `EMAIL_*`, optional `YFINANCE_MOCK`, cache/Redis if used). *(含 Phase D：`OPENAI_*`、console/SMTP 邮件；详见 README / `docs/API.md`)*
- [ ] `backend/.env` is **not** committed; `.gitignore` covers `**/.env`.
- [ ] `requirements.txt` / lockfiles match runnable deploy.
- [ ] PostgreSQL is default for local + prod (no accidental SQLite-only production).

---

## `spec.md` alignment (accepted baseline)

- [x] **§3 Roles:** Regular = `is_staff=False` (own subscriptions, Send Now on own rows); Admin = `is_staff=True` (all subscriptions, delete any). JWT `Authorization: Bearer` documented.  
  - *Progress:* 前后端角色权限与管理员用户管理界面已对齐（含 per-owner send/delete/user-search）。
- [x] **§5 Model:** `Subscription` 含 **`last_notified_price`** / **`last_notified_time`**；联合唯一约束已建库。***Send Now** 成功后会回写两字段；定时发送待 Phase E。*
- [x] **§6 Merge:** Periodic + **Send Now** merge by **normalized subscriber_email** within the **same user** for that action.  
  - *Progress:* **Send Now + 周期调度**均按 `subscriber_email` 合并并验证。
- [x] **§8 Schedule:** Mon–Fri, `America/New_York`, hourly **09:00–17:00 inclusive** (nine fires including 17:00).  
  - *Implemented idempotency:* 按纽约时区整点小时桶去重（同一自然小时内不重复发送）。
- [x] **§9 AI:** **OpenAI GPT-4o**（`OPENAI_MODEL`）；`get_ai_recommendation` / batch；失败 Fallback；见 `docs/API.md`、`backend/.env.example`。
- [x] **§11 Caching:** **Django cache**（`LocMemCache` dev）用于 **`get_price`**；TTL **120s**（`PRICE_CACHE_TTL`）；见 `docs/API.md` / README。
- [x] **§7 Enhancement:** Implemented and explained in README (default candidate: email send history). *(已交付 NotificationLog + API + dashboard Recent Notifications)*

---

## Requirement traceability (PDF)

- [x] **§1** UI create: ticker + email; validated (email format + real ticker via yfinance primary path). *(当前实现：regular 用户仅输入 ticker，email 自动绑定账号；admin 在每个用户卡片下为该用户新增订阅)*
- [x] **§2** UI list: ticker, **current price**, email, **Delete**, **Send Now**. *(Send Now 现为 owner 级/批量操作，更贴合 dashboard 使用场景)*
- [x] **§2 + §7** Email: price + **Buy/Hold/Sell** + short reason per stock + demo disclaimer. *(合并 HTML 邮件 + `send_now` API 已验证；前端邮件 UI 待 Phase F)*
- [x] **§3** Hourly emails Mon–Fri, 9 AM–5 PM **Eastern** — matches `spec.md` §8.
- [x] **§4** Same recipient email + multiple tickers → **one merged** email (periodic + Send Now per §6).
- [x] **§5** Yahoo/`yfinance` primary; **mock** documented and testable. *(API + `YFINANCE_MOCK`；`docs/API.md` §5)*
- [x] **§6** Login; regular = **own** only; admin = **all** (`is_staff`).  
  - *Progress:* 登录与管理界面已完成；admin 登录 token 内存态（不落盘），admin 管理页仅面向普通用户。
- [x] **§8** Self-chosen feature + README (what / why / value). *(邮件审计与历史追踪已实现并文档化)*
- [x] **§9** Stack: Django + PostgreSQL + React + Tailwind.
- [ ] **§11** Repo link + **hosted** URL work for reviewers.
- [ ] **§12** **AI usage** in `AI_LOG.md` (plan, prompts, fixes, verification).

---

## Security & data sanity

- [ ] No secrets in git history (rotate if ever committed).
- [x] API returns **403/404** for other users’ subscription IDs (not 200 with wrong data). *(订阅 API 已验证)*
- [x] Non-admin cannot list or mutate other users’ subscriptions. *( queryset / object 权限)*
- [ ] CORS and `ALLOWED_HOSTS` correct for production URL.

---

## Functional smoke tests (manual)

- [x] Login as **regular** (`is_staff=False`) → create subscription → list shows row with **cached-backed** price. *(REST/API 已验证)*
- [x] Delete own row → gone; cannot access another user’s id. *(API)*
- [x] Login as **admin** → sees **all** subscriptions; can delete another user’s row (per spec). *(API)*
- [x] **Send Now** on a row: email received (or console); if same user has two subs **same email**, **one** merged email for that click (§6). *(API + console 日志已验证)*
- [x] **Periodic** job: content matches merge rules; **idempotency** — no duplicate sends for same hour after retry (§8). *(按 America/New_York 整点小时桶去重验证通过)*
- [ ] **Mock yfinance** on → UI/API still behave per docs.
- [x] **OpenAI** failure → graceful fallback still sends email or errors clearly (per your documented behavior). *(未配 Key 或 API 异常时 Hold + 占位理由；邮件仍发送)*

---

## Frontend quality

- [x] Tailwind used consistently; layout OK on narrow viewport.
- [x] API errors surfaced (validation, network, 401). *(登录/注册 + 订阅创建/校验)*

---

## Submission package

- [ ] Hosted app: production login works (not localhost-only secrets).
- [ ] Submission note: repo URL, demo URL, test credentials if allowed, pointer to enhancement in README.
- [ ] Optional: transcripts per brief.

---

## SPEC hygiene

- [ ] `spec.md` **Revision** footer updated if assumptions change after baseline.
- [x] `tasks.md` / this file updated when spec changes (keep in sync). *(Phase A–D 任务与验收状态已同步)*
