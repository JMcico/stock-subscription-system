# Tasks — Implementation order (SPEC mode)

Derived from `spec.md` (accepted). Work top-to-bottom unless parallelized. Mark items done in PRs or local notes; `checklist.md` mirrors verification.

---

## Phase A — Auth & API skeleton

- [x] **A1** Add JWT (`djangorestframework-simplejwt`), wire URLs and settings (access/refresh lifetimes, rotation — document in README).
- [x] **A2** User provisioning: `createsuperuser` for admin (`is_staff=True`); regular users `is_staff=False` — optional `POST /api/auth/register/` or seed users only; document chosen path.
- [x] **A3** DRF: subscription routes require `IsAuthenticated`; permission classes distinguish **regular** (`is_staff=False`, queryset = own) vs **admin** (`is_staff=True`, queryset = all) per `spec.md` §3.
- [x] **A4** Frontend: login screen; store access/refresh token; attach `Authorization: Bearer`; logout clears storage.
- [x] **A5** Frontend route guard: unauthenticated → login.

---

## Phase B — Subscription model, validation & price cache

- [x] **B1** Django app (e.g. `subscriptions`) + `Subscription` model: `owner` (FK User), `ticker`, `subscriber_email`, `created_at`, `updated_at`, **`last_notified_price`**, **`last_notified_time`** (nullable); unique `(owner, ticker, subscriber_email)`; migrations on PostgreSQL.
- [x] **B2** `yfinance` ticker validation (real path); clear errors for invalid/unknown symbols.
- [x] **B3** Mock fallback (env e.g. `YFINANCE_MOCK=1` or settings flag); unit test at least one real and one mock path.
- [x] **B4** Serializers + validation on create; enforce uniqueness and the validation on ticker.
- [x] **B5** Optional `POST /api/validate_ticker/` for async UI checks.
- [x] **B6** Configure **Django cache** (`CACHES`) per `spec.md` §11 — local: `LocMemCache` or file; prod: document Redis if used; single code path for dev.
- [x] **B7** Shared **`get_price(ticker)`** via **`django.core.cache`**: cache-first, then yfinance (or mock); **TTL 120s** (`PRICE_CACHE_TTL`); used by list UI, Send Now, and scheduler.

---

## Phase C — Subscription CRUD API

> *Note:* 与 Phase B 同批交付；已与 Phase B 一并验收。

- [x] **C1** ViewSet or list/create: regular users see **only** `owner=request.user`; admin (`is_staff`) sees **all** — same routes, filtered queryset (per `spec.md` §10).
- [x] **C2** `GET/PATCH/DELETE /api/subscriptions/:id/` with object-level permission: owner **or** admin.
- [x] **C3** `DELETE` allowed for owner or admin (admin support deletes per §3).
- [x] **C4** List/detail responses include **current price** from **cached** `get_price` (§11); document TTL and behavior when cache miss / yfinance fails.

---

## Phase D — Email + AI (OpenAI GPT-4o)

- [x] **D1** Email backend: console (dev); SMTP or transactional provider (prod) via `EMAIL_*` env.
- [x] **D2** Templates: HTML + text; fixed **not financial advice** disclaimer footer.
- [x] **D3** **OpenAI API — GPT-4o** per `spec.md` §9: env `OPENAI_API_KEY` (and optional model override); build `{ signal, reason }`; timeout + **fallback** string if API fails (document).
- [x] **D4** Merge builder: group by normalized `subscriber_email`; one MIME message with each ticker’s price + AI line + disclaimer.
- [x] **D5** `POST .../send_now/`: per `spec.md` §6 — merge **same subscriber_email within that user** for that action; send; on success update each included row’s **`last_notified_price`** / **`last_notified_time`**.
- [x] **D6** Logging: email failures + mock yfinance + AI fallback traceable in logs.

---

## Phase E — Scheduling

23. **E1** Choose Celery / Django-Q / `django-crontab` + management command; deps + README ops (worker, beat/cron).
24. **E2** Hourly job: `America/New_York`, Mon–Fri, **09:00–17:00 inclusive** (nine ticks incl. 17:00) per `spec.md` §8.
25. **E3** **Idempotency:** dedupe per subscription per hour (or equivalent) so retries do not double-send §8.
26. **E4** Scheduled run uses same merge + email + AI + **`last_notified_price`** update paths as Send Now where applicable.
27. **E5** Local runbook: run worker + scheduler alongside Django.

---

## Phase F — Frontend UI

28. **F1** Subscription form: ticker + email; client email format validation; server errors; loading states.
29. **F2** Table: ticker, **price** (from API/cache-backed field), email, **Delete**, **Send Now**; confirm delete.
30. **F3** **Regular** (`is_staff=False`): UI scoped to own data; **Admin**: list all subscriptions (extra column owner optional); same app, role-based fetch or single list endpoint behavior.
31. **F4** Tailwind polish: responsive, accessible controls.

---

## Phase G — Self-chosen enhancement

32. **G1** Implement pick from `spec.md` §7 (default: **email send history** — model + API + minimal UI or admin).
33. **G2** README: what / why / value; align with submission notes.

---

## Phase H — Deploy & submission

34. **H1** Production settings: `DEBUG=False`, `ALLOWED_HOSTS`, DB from env, `CACHES`/Redis if prod, `OPENAI_*` / `EMAIL_*` on host.
35. **H2** Deploy API + DB + worker; deploy frontend (static or reverse proxy).
36. **H3** Hosted smoke test using `checklist.md`.
37. **H4** Extend `AI_LOG.md` (prompts, corrections, verification).

---

## Dependencies graph (summary)

- **C*** depends on **A***, **B***.  
- **D*** depends on **C*** (subscriptions exist) and **B7** (prices).  
- **E*** depends on **D*** (shared send/merge/AI).  
- **F*** depends on **A***, **C***, **D** for Send Now.  
- **G** after **D** or parallel **E/F**.  
- **H** last.
