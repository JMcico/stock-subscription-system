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
