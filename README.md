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

（计划中还包括：Django REST framework、JWT 认证、yfinance、邮件与定时任务组件等，详见 `AI_LOG.md`。）

## Getting Started

### 后端（Django）

1. 进入后端目录：`cd backend`
2. 创建并激活虚拟环境（示例）：
   - Windows: `python -m venv venv` → `.\venv\Scripts\activate`
   - macOS/Linux: `python3 -m venv venv` → `source venv/bin/activate`
3. 安装依赖：`pip install -r requirements.txt`
4. 配置环境变量或 `settings.py` 中的 PostgreSQL 连接信息。
5. 执行迁移：`python manage.py migrate`
6. 启动开发服务器：`python manage.py runserver`

### 前端（React + Vite）

1. 进入前端目录：`cd frontend`
2. 安装依赖：`npm install`
3. 启动开发服务器：`npm run dev`

## Key Features

- **股票代码实时验证**：通过 yfinance（或等价数据源）校验 Ticker 是否存在。
- **AI 驱动的投资建议**：对订阅标的生成 Buy / Hold / Sell 及理由（具体模型与接口见实现与 `AI_LOG.md`）。
- **智能邮件合并发送**：同一用户多只股票合并为一封邮件定时或手动触发。

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
