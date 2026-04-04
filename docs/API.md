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
| `username` | string | 是 | 与注册时一致，为 **邮箱**（规范化后小写）。 |
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

## 2. Django Admin（非 REST）

| Path | 说明 |
|------|------|
| `GET /admin/` | Django 自带管理后台（Session 登录，与 JWT 独立）。需先 `createsuperuser`。 |

---

## 3. 规划中接口（`spec.md` / `tasks.md`，尚未实现）

实现后应在本文件中补充请求/响应与权限说明。

| Method | Path | 说明 |
|--------|------|------|
| `GET`, `POST` | `/api/subscriptions/` | 列表（按角色过滤）/ 创建订阅 |
| `GET`, `PATCH`, `DELETE` | `/api/subscriptions/<id>/` | 单条查询、更新、删除 |
| `POST` | `/api/subscriptions/<id>/send_now/` | 立即发送邮件 |
| `POST` | `/api/validate_ticker/` | （可选）异步校验股票代码 |

**权限约定（与代码对齐后生效）**

- 默认 **`IsAuthenticated`**。
- 普通用户：仅操作 **本人** `owner` 的订阅；对象级可使用 `subscriptions.permissions.IsSubscriptionOwnerOrStaff`。
- 管理员（`is_staff=True`）：可访问 **全部** 订阅；仅管理员接口可使用 `IsStaffUser`。

---

## 4. 与 CORS

开发环境下，前端 Vite 默认源（如 `http://localhost:5173`）已在 `backend/core/settings.py` 的 `CORS_ALLOWED_ORIGINS` 中配置；生产环境需按部署域名追加。

---

## 5. 变更记录

| 日期 | 摘要 |
|------|------|
| 2026-04-04 | 初版：认证三接口 + 规划中订阅接口列表。 |
| 2026-04-04 | 注册：`username` 必须为邮箱格式（作登录名），与 `User.email` 同步；无单独 `email` 字段。 |
