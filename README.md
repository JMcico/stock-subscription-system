# Stock Subscription System

## Project Overview

股票订阅系统：用户可订阅股票代码，系统校验标的有效性，并（按计划）通过邮件合并推送行情与 AI 生成的投资建议。本项目采用 Django 提供 API 与业务逻辑，React 提供管理/订阅界面。

## Tech Stack

| 层级 | 技术 |
|------|------|
| 后端 | Python, Django |
| 数据库 | PostgreSQL |
| 前端 | React, Vite |
| 样式 | Tailwind CSS v4 |

已实现：**Django REST Framework**、**JWT**、**Subscription** 模型与 REST 接口、`yfinance` + **`YFINANCE_MOCK`** 股价与校验、`django.core.cache` 股价缓存（TTL **120s**）、**合并 HTML 邮件**（console/SMTP）、**OpenAI `gpt-4o`** Demo 信号与 Fallback、**`POST /api/subscriptions/<id>/send_now/`**。**定时调度（美东工作日每小时）**与**前端订阅管理 UI** 待后续阶段；详见 **`docs/API.md`** 与 **`AI_LOG.md`**。

## Getting Started

### 后端（Django）

1. 进入后端目录：`cd backend`
2. 创建并激活虚拟环境（示例）：
   - Windows: `python -m venv venv` → `.\venv\Scripts\activate`
   - macOS/Linux: `python3 -m venv venv` → `source venv/bin/activate`
3. 安装依赖：`pip install -r requirements.txt`
4. 配置环境变量或 `settings.py` 中的 PostgreSQL 连接信息（可参考 `backend/.env.example`）。可选：`YFINANCE_MOCK=1`、`PRICE_CACHE_TTL=120`；**合并发信 / AI**：`OPENAI_API_KEY`（未设置则使用占位 Hold 文案）、`OPENAI_MODEL`（默认 `gpt-4o`）；开发默认 **`EMAIL_BACKEND`** 为 **console**（邮件与合并 HTML 在终端输出）。
5. 执行迁移：`python manage.py migrate`
6. 启动开发服务器：`python manage.py runserver`
7. **管理员账号**：执行 `python manage.py createsuperuser` 创建 `is_staff=True` 的管理员（用于 Admin 权限与 Django admin）。

### API 认证（JWT，SimpleJWT）

- `POST /api/auth/register/` — 注册普通用户（`is_staff=False`），请求体 JSON：**必填** `username`（须为**合法邮箱格式**，作为登录账号；服务端会规范为小写并写入 `User.email`）、**必填** `password`（≥8 字符，经 Django 密码校验）。响应含 `access`、`refresh` 与用户摘要。详见 **`docs/API.md`**。
- `POST /api/auth/token/` — 登录，请求体：`username`（注册时使用的邮箱）、`password`。响应：`access`、`refresh`。
- `POST /api/auth/token/refresh/` — 请求体：`refresh`。响应：新的 `access`。
- 业务接口默认需在 Header 携带：`Authorization: Bearer <access>`。
- **Token 有效期**：Access **15 分钟**，Refresh **1 天**（见 `backend/core/settings.py` 中 `SIMPLE_JWT`）。未启用 refresh rotation / blacklist；生产环境可按需开启 `rest_framework_simplejwt` 的黑名单应用。

### 前端（React + Vite）

1. 进入前端目录：`cd frontend`
2. 安装依赖：`npm install`
3. 启动开发服务器：`npm run dev`（默认 `http://localhost:5173`）
4. 开发时 **需同时运行后端**：Vite 将 **`/api` 代理到** `http://127.0.0.1:8000`，前端请求使用相对路径 `/api/...` 即可。
5. 路由：`/login`（登录）、`/register`（注册）；登录成功后进入受保护的首页 `/`。表单中的 **Email** 会作为 API 请求体里的 **`username`** 提交。

## Key Features

- **股票代码实时验证**：通过 yfinance（或等价数据源）校验 Ticker 是否存在。
- **AI 驱动的投资建议（Demo）**：OpenAI 批量生成 Buy / Hold / Sell 与简短理由；失败时统一 Fallback（非实盘建议）。
- **智能邮件合并发送**：同一收件邮箱下多标的合并为一封 HTML 邮件（免责声明）；**`send_now`** 即时触发；定时任务待实现。

## API 文档

- 后端 REST 说明见 **`docs/API.md`**：认证、`validate_ticker`、订阅 CRUD、**`POST /api/subscriptions/<id>/send_now/`**（合并发信）、环境变量与错误示例。

## AI Usage & Implementation

开发过程中使用 AI 辅助：需求拆解、接口设计、前后端脚手架、调试与文档整理。实现细节、阶段划分与后续任务以 **`AI_LOG.md`** 为准；若行为与 README 不一致，以 `AI_LOG.md` 与代码为准。

## Decisions & Assumptions

以下为需求未完全细化时的**合理默认**，可在确认后写入 `AI_LOG.md` 或本节的「变更记录」：

| 主题 | 假设 |
|------|------|
| 定时任务 | 美东工作日 9:00–17:00 **整点**每小时一次（具体分钟可在实现时固定为 `:00` 或按 Celery beat 配置调整）。 |
| AI 提示词 | 输入包含股票代码、近期可获取的公开摘要数据；输出为结构化 JSON 或固定段落（Buy/Hold/Sell + 理由），具体模板在接入模型时定稿。 |
| 「立即发送」 | 指绕过下一次定时窗口、立即触发该用户（或该订阅）的合并邮件逻辑，与定时任务共用同一套合并与 AI 流水线 unless 另有产品定义。 |
| 部署 | 生产配置与云平台选型在阶段四落地；README 仅描述本地开发入口。 |
