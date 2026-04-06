# Backend API 说明（Django REST）

本文描述当前仓库中 **已实现** 的 HTTP 接口；与 `spec.md` 规划一致但尚未落地的接口在文末单独列出，便于对照实现进度。

**Base URL（本地开发）**  
`http://127.0.0.1:8000`（`python manage.py runserver` 默认端口）

**尾斜杠**  
所有路径在 Django 侧均以 **`/` 结尾** 注册。若请求 **`/api/...` 且未以 `/` 结尾**，中间件会返回 **HTTP 308** 重定向到带尾斜杠的 URL，以便 **POST 等请求体在重定向后仍保留**（不要用无尾斜杠的 URL 直接发 POST，以免旧客户端按 301 变成 GET）。

**内容类型**  
请求与响应主体一般为 **`application/json`**，除非另有说明。

**鉴权**  
除明确标注为「公开」的接口外，后续业务接口将要求请求头：

```http
Authorization: Bearer <access_token>
```

Access / Refresh 的有效期见 `backend/core/settings.py` 中的 `SIMPLE_JWT`（当前：Access **15 分钟**，Refresh **1 天**）。

---

## 1. 认证（Auth）— 已实现

### 1.1 用户注册

| 项目 | 说明 |
|------|------|
| **Method / Path** | `POST /api/auth/register/` |
| **鉴权** | 公开（无需 Token） |
| **说明** | 创建普通用户（`is_staff=False`）。**`username` 必须为合法邮箱格式**，并作为登录标识；服务端会 **trim + 小写** 规范化，`User.email` 与 `username` 存成同一字符串，便于与 Subscription 的邮箱体系对齐。格式不合法或该邮箱已被占用时注册失败。 |

**请求体（JSON）**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `username` | string | 是 | **须为有效邮箱地址**（Django `validate_email`）；作为登录用户名；规范化后须全局唯一（与 `User.username` / `User.email` 冲突均拒绝）。 |
| `password` | string | 是 | 至少 **8** 字符；经 Django `AUTH_PASSWORD_VALIDATORS` 校验。 |

**成功响应** `201 Created`

```json
{
  "refresh": "<jwt-refresh>",
  "access": "<jwt-access>",
  "user": {
    "id": 1,
    "username": "alice@example.com",
    "email": "alice@example.com",
    "is_staff": false
  }
}
```

**错误响应（示例）**

| HTTP | 场景 |
|------|------|
| `400 Bad Request` | 缺少字段、`username` 非合法邮箱、`password` 校验失败、该邮箱已被注册、密码强度不足等。 |

错误体为 DRF 常规结构，例如：

```json
{
  "username": ["Enter a valid email address."]
}
```

或

```json
{
  "username": ["A user with this email already exists."]
}
```

---

### 1.2 登录（获取 Token 对）

| 项目 | 说明 |
|------|------|
| **Method / Path** | `POST /api/auth/token/` |
| **鉴权** | 公开 |

**请求体（JSON）**

| 字段 | 类型 | 必填 |
|------|------|------|
| `username` | string | 是 | 登录用户名（按账户匹配，不做邮箱格式校验）。 |
| `password` | string | 是 |

**成功响应** `200 OK`

```json
{
  "refresh": "<jwt-refresh>",
  "access": "<jwt-access>"
}
```

**错误响应** `401 Unauthorized` — 凭据错误（SimpleJWT 默认行为）。

---

### 1.3 刷新 Access Token

| 项目 | 说明 |
|------|------|
| **Method / Path** | `POST /api/auth/token/refresh/` |
| **鉴权** | 公开 |

**请求体（JSON）**

| 字段 | 类型 | 必填 |
|------|------|------|
| `refresh` | string | 是 |

**成功响应** `200 OK`

```json
{
  "access": "<new-jwt-access>"
}
```

**错误响应** `401` — refresh 无效或过期。

---

### 1.4 当前登录用户信息

| 项目 | 说明 |
|------|------|
| **Method / Path** | `GET /api/auth/me/` |
| **鉴权** | 需登录 |

**成功响应** `200 OK`

```json
{
  "id": 1,
  "username": "alice@example.com",
  "email": "alice@example.com",
  "is_staff": false
}
```

用于前端在登录后恢复用户资料（如 `email`、`is_staff`）并驱动角色化 UI。

---

### 1.5 管理员用户列表

| 项目 | 说明 |
|------|------|
| **Method / Path** | `GET /api/auth/users/` |
| **鉴权** | 需管理员登录 |

返回 admin dashboard 用户管理列表（当前仅返回非管理员用户）。

### 1.6 管理员删除用户

| 项目 | 说明 |
|------|------|
| **Method / Path** | `DELETE /api/auth/users/<user_id>/` |
| **鉴权** | 需管理员登录 |

说明：删除目标用户及其级联订阅；后端禁止删除当前登录管理员自身。

---

## 2. 订阅（Subscriptions）— 已实现

以下接口均需：

```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

**权限**

| 角色 | 列表 / 创建 | 单条详情 / 修改 / 删除 |
|------|-------------|------------------------|
| 普通用户（`is_staff=false`） | 仅 **本人** `owner` 的订阅 | 仅 **本人** 拥有的行 |
| 管理员（`is_staff=true`） | **全部** 用户的订阅 | 任意行 |

---

### 2.1 校验股票代码（可选，供表单异步校验）

| 项目 | 说明 |
|------|------|
| **Method / Path** | `POST /api/validate_ticker/` |
| **鉴权** | 需登录 |

**请求体（JSON）**

```json
{
  "ticker": "AAPL"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `ticker` | string | 是 | 股票代码；服务端会 `trim` 并转为大写再校验。 |

**成功响应** `200 OK`

```json
{
  "valid": true,
  "ticker": "AAPL",
  "price": "123.4567"
}
```

`price` 为当前缓存/行情价（字符串，与 `get_price` 一致；`YFINANCE_MOCK=1` 时为模拟随机价）。

**失败响应** `400 Bad Request`（代码无效、无行情等）

```json
{
  "valid": false,
  "error": "Ticker \"XXXX\" is not a valid symbol or has no recent market data."
}
```

**上游异常** `502 Bad Gateway`（极少）

```json
{
  "valid": false,
  "error": "Could not validate ticker \"AAPL\". Try again or check your network."
}
```

---

### 2.2 订阅列表

| 项目 | 说明 |
|------|------|
| **Method / Path** | `GET /api/subscriptions/` |
| **鉴权** | 需登录 |

**请求体**  
无。

**成功响应** `200 OK`

```json
[
  {
    "id": 1,
    "ticker": "AAPL",
    "subscriber_email": "alice@example.com",
    "current_price": "198.7500",
    "last_notified_price": null,
    "last_notified_time": null,
    "created_at": "2026-04-05T12:00:01.123456Z",
    "updated_at": "2026-04-05T12:00:01.123456Z"
  }
]
```

| 字段 | 说明 |
|------|------|
| `owner` | 只读；订阅拥有者账号（`owner.email` 或 `owner.username`）。管理员视图可直接显示该列。 |
| `current_price` | 只读；通过 `get_price(ticker)` 计算，**先读 Django 缓存，未命中再拉 yfinance（或 MOCK 随机价）**；TTL 默认 **120s**（`PRICE_CACHE_TTL`）。拉取失败时可能为 `null`。 |
| `last_notified_price` / `last_notified_time` | 首次发送邮件前一般为 `null`（由后续发送逻辑写入）。 |

---

### 2.3 创建订阅

| 项目 | 说明 |
|------|------|
| **Method / Path** | `POST /api/subscriptions/` |
| **鉴权** | 需登录；`owner` 自动为当前用户，**勿**在 body 中传 `owner`。 |

**请求体（JSON）**

```json
{
  "ticker": "AAPL",
  "subscriber_email": "notify@example.com"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `ticker` | string | 是 | 须为 Yahoo Finance 能识别的标的（或 MOCK 规则下通过校验）；存库为大写。 |
| `subscriber_email` | string | 是 | 收件邮箱；会规范为小写。 |

**成功响应** `201 Created` — body 与列表单项结构相同（含 `id`、`current_price` 等）。

**校验失败** `400 Bad Request`

```json
{
  "ticker": ["Ticker \"XYZBAD\" is not a valid symbol or has no recent market data."]
}
```

或邮箱格式错误：

```json
{
  "subscriber_email": ["Enter a valid email address."]
}
```

**唯一约束冲突** `400 Bad Request`（同一 `owner` + `ticker` + `subscriber_email` 已存在）

```json
{
  "non_field_errors": [
    "You already have a subscription for this ticker and email address."
  ]
}
```

---

### 2.4 单条订阅详情

| 项目 | 说明 |
|------|------|
| **Method / Path** | `GET /api/subscriptions/<id>/` |
| **鉴权** | 需登录；非本人且非管理员 → `403` / `404`（视路由与权限而定）。 |

**请求体**  
无。

**成功响应** `200 OK` — 与列表中单条对象结构相同。

**失败** `404 Not Found` — id 不存在或无权限。

---

### 2.5 更新订阅（部分更新）

| 项目 | 说明 |
|------|------|
| **Method / Path** | `PATCH /api/subscriptions/<id>/` |
| **鉴权** | 需登录；仅能改本人或（管理员）任意行。 |

**请求体（JSON）** — 可只传要改的字段，例如：

```json
{
  "ticker": "MSFT",
  "subscriber_email": "other@example.com"
}
```

**成功响应** `200 OK` — 返回更新后的完整对象。

若修改后与其它行冲突唯一约束，返回与 **2.3** 相同的 `non_field_errors`。

---

### 2.6 删除订阅

| 项目 | 说明 |
|------|------|
| **Method / Path** | `DELETE /api/subscriptions/<id>/` |
| **鉴权** | 需登录。 |

**请求体**  
无。

**成功响应** `204 No Content`（无 body）。

---

### 2.7 立即发送合并邮件（Send Now）

| 项目 | 说明 |
|------|------|
| **Method / Path** | `POST /api/subscriptions/<id>/send_now/` |
| **鉴权** | 需登录；仅能对自己拥有的订阅行操作，**管理员**可对任意行触发。 |

**行为（与 `spec.md` §6 一致）**

- 以该行的 **`owner`** 与 **`subscriber_email`**（不区分大小写）为键，查出**同一用户、同一收件邮箱**下的**全部** `Subscription` 行。
- 按 **`subscriber_email`** 分组；**每一组发送一封 HTML 邮件**（控制台后端下内容打印在 **runserver 终端**）。
- 每组内所有 ticker：先取价（`get_price`），再 **一次 OpenAI（`gpt-4o`，可 `OPENAI_MODEL` 覆盖）批量**生成每条 Demo 的 Buy/Hold/Sell + 理由；失败时使用占位文案。
- 发送成功后，更新该组内每条订阅的 **`last_notified_price`**、**`last_notified_time`**。

**请求体**  
无（空 JSON `{}` 亦可）。

```json
{}
```

**成功响应** `200 OK`

```json
{
  "status": "sent",
  "emails_sent": 1,
  "groups": 1,
  "subscribers": ["notify@example.com"]
}
```

| 字段 | 说明 |
|------|------|
| `emails_sent` | 实际发出的邮件封数（按收件邮箱计）。 |
| `groups` | 本请求合并出的分组数（通常与 `subscriber_email` 种类数一致）。 |
| `subscribers` | 收件邮箱列表。 |

**失败响应** `502 Bad Gateway` — 发信异常（如 SMTP 未配好且非 console）。

```json
{
  "detail": "...",
  "code": "send_failed"
}
```

**依赖环境**

- `OPENAI_API_KEY`：未设置时 AI 为占位 **Hold / AI analysis temporarily unavailable**（仍发邮件）。
- 开发环境默认 **`EMAIL_BACKEND=console`**，邮件正文在**运行 `runserver` 的终端**中显示；合并后的 **HTML 也会在终端额外打印**便于检查。

---

### 2.8 一键发送（Dashboard 批量 Send Now）

| 项目 | 说明 |
|------|------|
| **Method / Path** | `POST /api/subscriptions/send_now/` |
| **鉴权** | 需登录；普通用户作用于“自己的全部订阅”，管理员作用于“当前可见范围内全部订阅”。 |

**行为**

- 按 `(owner, subscriber_email)` 分组后发送；
- 每组调用同一套合并邮件发送链路（与 2.7 保持一致）；
- 用于前端 `Manage Subscriptions` 区域的一键操作按钮。

**成功响应** `200 OK`

```json
{
  "status": "sent",
  "emails_sent": 2,
  "groups": 2,
  "subscribers": ["a@example.com", "b@example.com"]
}
```

---

### 2.9 Owner 级一键发送（Admin Dashboard）

| 项目 | 说明 |
|------|------|
| **Method / Path** | `POST /api/subscriptions/owners/<owner_id>/send_now/` |
| **鉴权** | 需登录；管理员用于对单个 owner 一键发送。 |

说明：仅对该 owner 的订阅执行分组合并发送（按 `subscriber_email`）。

### 2.10 Admin 代用户创建订阅

`POST /api/subscriptions/` 在管理员场景支持附加字段：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `target_owner_id` | integer | 否 | 管理员指定目标用户 owner；未传时仍默认当前用户。 |

---

## 3. 定时任务与队列（Phase E）— 已实现

> 说明：该部分为后端任务系统行为，不是对外 HTTP 接口。

### 3.1 调度与执行

- 使用 **Django-Q2 + Redis Broker**。
- 任务函数：`subscriptions.tasks.run_hourly_checks`。
- 调度记录：启动后由应用自动确保 `django_q.Schedule` 中存在每小时任务（`run_hourly_subscription_checks`）。
- 时间窗：仅在 `America/New_York` 的周一至周五、`09:00` 到 `17:00`（含）执行发送逻辑。

### 3.2 合并与幂等规则

- 周期任务与 `send_now` 复用同一发送链路：`send_subscription_emails`（按 `subscriber_email` 合并）。
- 幂等按 **纽约时区整点小时桶**判定（不是 rolling 60 分钟）：
  - 若 `last_notified_time` 与当前时间处于同一 NY 自然小时，默认不重复发送；
  - 若已跨入下一 NY 小时，可发送。

### 3.3 Worker 启动

```bash
cd backend
python manage.py qcluster
```

可选：仅运行一轮后退出（本地排查用）

```bash
python manage.py qcluster --run-once
```

---

## 4. Django Admin（非 REST）

| Path | 说明 |
|------|------|
| `GET /admin/` | Django 自带管理后台（Session 登录，与 JWT 独立）。需先 `createsuperuser`。 |

---

## 5. 环境与第三方（便于联调）

| 变量 | 默认 | 说明 |
|------|------|------|
| `YFINANCE_MOCK` | `0` | 设为 `1` / `true` / `yes` 时，`get_price` 使用**随机价**；校验仍尽量走 yfinance，失败时 MOCK 下可放宽。 |
| `PRICE_CACHE_TTL` | `120` | 股价缓存秒数（`django.core.cache`）。 |
| `REDIS_CACHE_URL` | `redis://127.0.0.1:6379/1` | Django 缓存后端地址（`django-redis`）。 |
| `REDIS_Q_URL` | `redis://127.0.0.1:6379/2` | Django-Q2 Broker 地址（建议与缓存分库）。 |
| `REDIS_Q_HOST` / `REDIS_Q_PORT` / `REDIS_Q_DB` / `REDIS_Q_PASSWORD` | 空 | 可覆盖 `REDIS_Q_URL` 解析结果。 |
| `OPENAI_API_KEY` | 空 | OpenAI API Key；未设置时合并邮件中的 AI 行为使用**固定 Fallback**（Hold + 不可用说明）。 |
| `OPENAI_MODEL` | `gpt-4o` | 聊天模型名。 |
| `EMAIL_BACKEND` | `django.core.mail.backends.console.EmailBackend` | 开发用控制台邮件；生产可改为 SMTP 并配置 `EMAIL_HOST` 等。 |
| `DEFAULT_FROM_EMAIL` | `noreply@stock-subscription.local` | `From` 头。 |

---

## 6. 与 CORS

开发环境下，前端 Vite 默认源（如 `http://localhost:5173`）已在 `backend/core/settings.py` 的 `CORS_ALLOWED_ORIGINS` 中配置；生产环境需按部署域名追加。

---

## 7. 变更记录

| 日期 | 摘要 |
|------|------|
| 2026-04-04 | 初版：认证三接口 + 规划中订阅接口列表。 |
| 2026-04-04 | 注册：`username` 必须为邮箱格式（作登录名），与 `User.email` 同步；无单独 `email` 字段。 |
| 2026-04-05 | 补充订阅 API：`validate_ticker`、`subscriptions` CRUD、错误 JSON 示例；环境变量 `YFINANCE_MOCK` / `PRICE_CACHE_TTL`。 |
| 2026-04-05 | Phase D：`POST .../send_now/`、合并 HTML 邮件、OpenAI、`OPENAI_*` / `EMAIL_*` 说明。 |
| 2026-04-05 | 维护者验收 `send_now`（console 邮件 / 终端 HTML 预览）；与 `tasks.md` / `checklist` / README 状态一致。 |
| 2026-04-06 | Phase E：Redis 缓存 + Django-Q2（Redis Broker）已接入；新增 `qcluster` 运行说明、定时任务行为和“按 NY 整点小时桶”幂等规则。 |
| 2026-04-06 | 调整周期任务策略：移除“同小时内 >1% 波动可重发”逻辑，改为同一 NY 小时严格只发送一次。 |
| 2026-04-06 | Phase F 对齐：新增 `GET /api/auth/me/`；订阅返回补充只读 `owner` 字段供管理员表格显示。 |
| 2026-04-06 | Dashboard 交互更新：新增 `POST /api/subscriptions/send_now/` 一键发送；登录字段说明调整为 username 匹配登录（不做邮箱格式校验）。 |
| 2026-04-06 | Admin 管理增强：新增 `GET /api/auth/users/`、`DELETE /api/auth/users/<id>/`、`POST /api/subscriptions/owners/<owner_id>/send_now/`，并支持 admin 通过 `target_owner_id` 代用户新增订阅。 |
