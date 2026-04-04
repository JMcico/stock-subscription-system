# 项目计划 (Project Plan) 与任务拆解 (Task Breakdown)

## 阶段一：基础架构与环境配置 (Foundation)

### 后端搭建

- 初始化 Django 项目。
- 配置 PostgreSQL 数据库连接。
- 安装并集成：`djangorestframework`、`django-cors-headers`、`yfinance`。

### 前端搭建

- 使用 React + Vite 初始化前端工程。
- 配置 **Tailwind CSS v4**。

### 用户系统

- 基于 Django 内置 `User` 模型实现 **JWT 认证**。
- 权限区分：
  - **Admin**：可查看全部数据。
  - **Regular**：仅可查看个人数据。

---

## 阶段二：订阅核心逻辑 (Subscription Logic)

### 数据模型

- 创建 `Subscription` 模型，字段包含：`Ticker`、`Email`、`User ID`（及与用户的关联）。

### Ticker 验证

- 集成 `yfinance` 编写校验逻辑，确保股票代码在数据源中真实存在。

### API 开发

- 提供 REST 接口：**创建**、**列表**、**删除** 订阅。

### 前端 UI

- 订阅表单（含前端/接口校验）。
- 订阅列表，支持 **删除** 与 **立即发送** 操作。

---

## 阶段三：定时任务与邮件系统 (Scheduling & Email)

### 邮件合并逻辑

- 将同一用户的多个股票订阅合并为 **一封邮件** 发送。

### AI 推荐集成

- 接入 AI 接口，为每只股票生成 **Buy / Hold / Sell** 建议及简要理由。

### 定时调度

- 使用 **Celery** 或 **Django-Q** 配置定时任务。
- 调度规则：**美国东部时间** 周一至周五 **9:00–17:00**，**每小时** 执行一次。

---

## 阶段四：增强功能与优化 (Enhancement & Refinement)

### 自定义增强功能（建议方向）

- **股价波动实时看板**，或
- **邮件发送历史记录**（二选一或按优先级实现）。

### 错误处理

- 为 `yfinance` 增加 **Mock** 机制，在 API 不可用或异常时仍可开发与测试。

### 部署准备

- 编写生产环境配置文件。
- 准备部署至云平台（具体平台与流程在实施阶段确定）。


# 开发日志 (Dev Log)

| 完成时间 (UTC+0 日期) | 已完成工作摘要 | AI 工具 |
|----------------------|----------------|---------|
| 2026-04-04 | 编写根目录 `README.md`（Overview、技术栈、Getting Started、Key Features、AI 使用说明、Decisions & Assumptions）。 | Cursor Agent |
| 2026-04-04 | 整理本文件上半部分为分阶段「项目计划 & 任务拆解」（Markdown 结构化）。 | Cursor Agent |
| 2026-04-04 | 新增 `backend/requirements.txt`（按当时虚拟环境 `pip list` 固定版本；后追加 `python-dotenv`）。 | Cursor Agent |
| 2026-04-04 | 核对 README 所列依赖：前端 `npm install` / `npm run build` 通过；后端包可安装并 `manage.py check` 通过；补全 Tailwind v4 入口 `@import "tailwindcss"`（`frontend/src/index.css`）。 | Cursor Agent |
| 2026-04-04 | Django：`INSTALLED_APPS` 注册 `rest_framework`、`corsheaders`；`CorsMiddleware`；`CORS_ALLOWED_ORIGINS` 含 Vite 默认端口；数据库在设置 `POSTGRES_*` 时用 PostgreSQL，否则 SQLite；`load_dotenv(backend/.env)`。新增 `backend/.env.example`。 | Cursor Agent |
| 2026-04-04 | 本地 PostgreSQL 就绪后：创建 `backend/.env` 写入 `stock_db` / `postgres` / 本机连接信息；强化 `.gitignore`（`**/.env`）确保密钥文件不进入 GitHub。 | Cursor Agent |
| 2026-04-04 | **SPEC 模式**：依据 Hextom 二轮 take-home PDF 起草根目录 `spec.md`（需求追溯、数据模型、合并/调度/AI/缓存等）、`tasks.md`（分阶段实现顺序）、`checklist.md`（提交前验收）。 | Cursor Agent |
| 2026-04-04 | **Jim** 接受并修改 `spec.md` 后，将 `tasks.md`、`checklist.md` 与之对齐（如 `is_staff` 角色、JWT、`last_notified_price`、Django Cache 股价、OpenAI GPT-4o、美东 9–17 整点含 17:00、Send Now 与定时合并规则等）。 | Cursor Agent |
| 2026-04-04 | `spec.md` §12 Change control 增补 **Revision 1** 脚注（日期 + 与 R0 差异摘要）。 | Cursor Agent |
| 2026-04-04 | **Phase A（A1–A3）**：集成 `djangorestframework-simplejwt`（Access 15m / Refresh 1d）、`REST_FRAMEWORK` 默认 `JWTAuthentication` + `IsAuthenticated`；`api/auth/token/`、`token/refresh/`、`auth/register/`；`subscriptions.permissions` 中 `IsStaffUser`、`IsSubscriptionOwnerOrStaff`；`spec.md` §10 与 `README.md` JWT 说明同步。 | Cursor Agent |
| 2026-04-04 | 注册：先要求独立必填 `email` 并新增 **`docs/API.md`**；后改为 **以邮箱作为 `username`**（`validate_email`），`User.email` 与规范化小写后的 `username` 一致；更新 `docs/API.md`、`spec.md` §10、`README.md`。 | Cursor Agent |
| 2026-04-04 | **Phase A A4/A5**：`EnsureApiTrailingSlashMiddleware`（`/api` 无尾斜杠 → 308）；前端 `react-router-dom`、登录/注册页（Email→`username`）、`AuthProvider`、`ProtectedRoute`/`GuestRoute`、Vite `/api` 代理。 | Cursor Agent |
| 2026-04-04 | **验收**：维护者本地验证注册/登录 UI 与流程正常；已勾选 `tasks.md` A4/A5、`checklist.md` 相关项（§9 技术栈、前端质量、SPEC hygiene；§6 / §3 记进度说明）。 | Cursor Agent |

> **说明**：上表「AI 工具」统一记为 **Cursor Agent**（Cursor 内置对话式 Agent；底层模型由 Cursor 路由，会话内未固定单一模型名称）。若需精确到某次对话的模型，可在 Cursor 界面导出或查看用量详情后手工补一行。

---