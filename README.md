# Stock Subscription System

## Project Overview

股票订阅系统：用户可订阅股票代码，系统校验标的有效性，并通过邮件合并推送行情与 AI 生成的投资建议。本项目采用 Django 提供 API 与业务逻辑，React 提供管理/订阅界面。

## Tech Stack

| 层级 | 技术 |
|------|------|
| 后端 | Python, Django |
| 数据库 | PostgreSQL |
| 前端 | React, Vite |
| 样式 | Tailwind CSS v4 |

已实现：**Django REST Framework**、**JWT**、**Subscription** 模型与 REST 接口、`yfinance` + **`YFINANCE_MOCK`** 股价与校验、基于 **Redis (`django-redis`)** 的跨进程价格缓存（默认 DB 1，TTL **120s**）、**合并 HTML 邮件**（console/SMTP）、**OpenAI `gpt-4o`** Demo 信号与 Fallback、**`POST /api/subscriptions/<id>/send_now/`**、以及基于 **Django-Q2 + Redis Broker** 的周期调度（美东工作日每小时）。Phase F 管理端已支持按用户分组管理（搜索用户、owner 级 Send Now/Delete User、按用户新增订阅）。详见 **`docs/API.md`** 与 **`AI_LOG.md`**。

## Getting Started

### 后端（Django）

1. 进入后端目录：`cd backend`
2. 创建并激活虚拟环境（示例）：
   - Windows: `python -m venv venv` → `.\venv\Scripts\activate`
   - macOS/Linux: `python3 -m venv venv` → `source venv/bin/activate`
3. 安装依赖：`pip install -r requirements.txt`
4. 配置环境变量（参考 `backend/.env.example`）：
   - 数据库：`POSTGRES_*`（未设置时本地回退 SQLite）
   - 价格缓存 Redis：`REDIS_CACHE_URL`（默认 `redis://127.0.0.1:6379/1`）
   - 任务队列 Redis：`REDIS_Q_URL`（默认 `redis://127.0.0.1:6379/2`，与缓存分库）
   - 可选覆盖：`REDIS_Q_HOST` / `REDIS_Q_PORT` / `REDIS_Q_DB` / `REDIS_Q_PASSWORD`
   - 行情与缓存：`YFINANCE_MOCK=1`、`PRICE_CACHE_TTL=120`
   - 合并发信 / AI：`OPENAI_API_KEY`（未设置则使用占位 Hold 文案）、`OPENAI_MODEL`（默认 `gpt-4o`）
   - 邮件：开发默认 **`EMAIL_BACKEND`** 为 **console**（邮件与合并 HTML 在终端输出）
5. 执行迁移：`python manage.py migrate`
6. 启动 Django API：`python manage.py runserver`
7. 启动任务集群（worker + scheduler）：`python manage.py qcluster`
8. **管理员账号**：执行 `python manage.py createsuperuser` 创建 `is_staff=True` 的管理员（用于 Admin 权限与 Django admin）。

### API 认证（JWT，SimpleJWT）

- `POST /api/auth/register/` — 注册普通用户（`is_staff=False`），请求体 JSON：**必填** `username`（须为**合法邮箱格式**，作为登录账号；服务端会规范为小写并写入 `User.email`）、**必填** `password`（≥8 字符，经 Django 密码校验）。响应含 `access`、`refresh` 与用户摘要。详见 **`docs/API.md`**。
- `POST /api/auth/token/` — 登录，请求体：`username`、`password`（按账号匹配，不做邮箱格式校验）。响应：`access`、`refresh`。
- `POST /api/auth/token/refresh/` — 请求体：`refresh`。响应：新的 `access`。
- `GET /api/auth/me/` / `GET /api/auth/users/`（admin）— 当前用户信息 / 管理页用户列表。
- 业务接口默认需在 Header 携带：`Authorization: Bearer <access>`。
- **Token 有效期**：Access **15 分钟**，Refresh **1 天**（见 `backend/core/settings.py` 中 `SIMPLE_JWT`）。未启用 refresh rotation / blacklist；生产环境可按需开启 `rest_framework_simplejwt` 的黑名单应用。

### 前端（React + Vite）

1. 进入前端目录：`cd frontend`
2. 安装依赖：`npm install`
3. 启动开发服务器：`npm run dev`（默认 `http://localhost:5173`）
4. 开发时 **需同时运行后端**：Vite 将 **`/api` 代理到** `http://127.0.0.1:8000`，前端请求使用相对路径 `/api/...` 即可。
5. 路由：`/login`（登录）、`/register`（注册）、`/dashboard`（受保护仪表盘）；未登录访问 `/dashboard` 会重定向到 `/login`。

## Key Features

- **股票代码实时验证**：通过 yfinance（或等价数据源）校验 Ticker 是否存在。
- **AI 驱动的投资建议（Demo）**：OpenAI 批量生成 Buy / Hold / Sell 与简短理由；失败时统一 Fallback（非实盘建议）。
- **智能邮件合并发送**：同一收件邮箱下多标的合并为一封 HTML 邮件（免责声明）；支持 **`send_now`** 与周期任务复用同一链路。
- **周期调度（Phase E）**：`America/New_York` 周一至周五，`09:00–17:00` 每小时任务；幂等按**纽约整点小时桶**（不是 rolling 60 分钟），同一自然小时严格只发送一次。
- **Admin 用户管理（Phase F）**：仅显示普通用户（不含管理员），支持用户搜索、owner 级发送、删除用户（二次确认）和按用户新增订阅。

## API 文档

- 后端 REST 与任务系统说明见 **`docs/API.md`**：认证、`validate_ticker`、订阅 CRUD、**`POST /api/subscriptions/<id>/send_now/`**（合并发信）、Phase E 调度/队列行为、环境变量与错误示例。

## AI Usage & Implementation

开发过程中使用 AI 辅助：需求拆解、接口设计、前后端脚手架、调试与文档整理。实现细节、阶段划分与后续任务以 **`AI_LOG.md`** 为准；若行为与 README 不一致，以 `AI_LOG.md` 与代码为准。

## Decisions & Assumptions

以下为需求未完全细化时的**合理默认**，可在确认后写入 `AI_LOG.md` 或本节的「变更记录」：

| 主题 | 假设 |
|------|------|
| 定时任务 | 已实现为 Django-Q2 每小时触发；业务窗口为美东工作日 9:00–17:00；幂等按纽约时区“自然小时桶”控制（同一自然小时严格只发送一次）。 |
| AI 提示词 | 输入包含股票代码、近期可获取的公开摘要数据；输出为结构化 JSON 或固定段落（Buy/Hold/Sell + 理由），具体模板在接入模型时定稿。 |
| 「立即发送」 | 指绕过下一次定时窗口、立即触发该用户（或该订阅）的合并邮件逻辑，与定时任务共用同一套合并与 AI 流水线 unless 另有产品定义。 |
| 部署 | 生产配置与云平台选型在阶段四落地；README 仅描述本地开发入口。 |
