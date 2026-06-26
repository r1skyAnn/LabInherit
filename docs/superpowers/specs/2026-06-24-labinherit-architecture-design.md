# LabInherit 架构设计 Spec

> **For agentic workers:** 本文档为整体架构设计，不展开每个子模块的实施细节。每个后续子任务（账号、项目、笔记、追问、看板）都将基于本文档衍生独立子 spec 与子 plan。
>
> **状态：** 已与用户逐节确认（5 节全部 OK）
> **日期：** 2026-06-24

---

## 1. 背景与目标

**LabInherit（实验室薪火传舵平台）** 是一个**单实验室内部使用**的全栈平台，核心目的是把实验室历代积累的项目经验结构化沉淀下来，让师弟师妹不再重复踩坑、毕业师兄师姐的经验不随人离开。

**双端定位：**
- **C 端（师弟师妹 / 已毕业师兄师姐）**：以真实课题/项目为线索的结构化笔记系统 + 跨时空异步追问
- **B 端（导师 / 历代大弟子）**：人员审核、身份状态流转、知识质量看板

**痛点：**
1. 师弟师妹重复踩同样的坑（环境/调参/Bug）
2. 毕业师兄师姐带走最宝贵的项目经验
3. 传统笔记没有"挂在哪个项目下"的强约束，散乱难找
4. 知识传承没有"异步追问"的闭环机制

**非目标（YAGNI）：**
- 不做多租户、不做开放注册、不做付费/订阅
- 不做富文本所见即所得（先 Markdown）
- 不做 Elasticsearch（先 MySQL LIKE）
- 不做微服务（单体分层即可）
- 不做 AI 摘要/推荐（架构留口子，不实现）

---

## 2. 已敲定的产品决策（来自 brainstorming）

| 维度 | 决策 |
|---|---|
| 用户身份模型 | 扁平身份 + 角色标签：`users.status` (active/graduated/archived) + `users.role` (member/admin/owner) |
| 入组流程 | 邀请码注册 + 审核队列 |
| 追问机制 | 评论 + 类 GitHub Issue 的追问跟进 + 邮件 SMTP 兜底通知 |
| 树状分类 | 路径式物化路径，无限级 |
| 笔记编辑器 | Markdown |
| 技术栈 | Vue3 + FastAPI + MySQL（Python 路线） |
| 部署形态 | 本地先跑通（Docker Compose），架构留口子上云 |
| 邮件 | SMTP 异步发送，邮件 outbox 表 + 后台 worker 兜底 |
| 搜索 | MySQL LIKE（接口可插拔） |
| 认证 | 账号密码 + 忘记密码 |
| 架构风格 | 方案 A：单体分层 FastAPI + Vue3 SPA |

---

## 3. 仓库结构

monorepo 单仓多包，每个目录职责单一：

```
labinherit/
├── backend/                    FastAPI 后端
│   ├── app/
│   │   ├── main.py             入口，挂载中间件、注册路由
│   │   ├── core/               跨模块基础设施（config / security / exceptions / deps）
│   │   ├── db/                 SQLAlchemy 异步引擎、Session、Alembic 配置
│   │   ├── modules/
│   │   │   ├── auth/           账号、密码、登录、Token、忘记密码
│   │   │   ├── users/          用户档案、身份标签
│   │   │   ├── projects/       课题/项目
│   │   │   ├── categories/     树状分类
│   │   │   ├── notes/          笔记（Markdown + 版本）
│   │   │   ├── comments/       评论 + 类 GitHub Issue 追问
│   │   │   ├── ask/            追问引擎：状态机、邮件兜底
│   │   │   ├── notifications/  站内通知
│   │   │   ├── stats/          看板聚合数据
│   │   │   └── admin/          审核、身份转换、看板视图
│   │   ├── schemas/            Pydantic 模型（DTO）
│   │   ├── tasks/              异步任务（worker 等）
│   │   └── utils/
│   ├── alembic/                数据库迁移
│   ├── tests/                  pytest 单元/集成测试
│   ├── pyproject.toml
│   ├── Dockerfile
│   └── .env.example
├── frontend/                   Vue3 前端
│   ├── src/
│   │   ├── api/                按后端模块生成的 axios 封装
│   │   ├── stores/             Pinia 状态管理
│   │   ├── router/             Vue Router
│   │   ├── views/              页面（按业务域分包）
│   │   ├── components/         通用组件（Markdown 渲染、树、卡片、看板）
│   │   └── utils/
│   ├── package.json
│   ├── vite.config.ts
│   ├── Dockerfile
│   └── .env.example
├── deploy/
│   ├── docker-compose.yml      一键起 backend + frontend + mysql + worker
│   └── nginx/                  前端 nginx 配置
├── docs/
│   ├── superpowers/
│   │   ├── specs/              设计 spec（本文件 + 后续子 spec）
│   │   └── plans/              实施 plan
│   └── api/                    OpenAPI 导出
├── .gitignore
├── .editorconfig
├── README.md
└── LICENSE
```

**模块内部约定**：每个 `modules/<name>/` 固定四层：
- `router.py`：HTTP 边界（FastAPI APIRouter）
- `service.py`：业务逻辑（不依赖 FastAPI）
- `models.py`：SQLAlchemy ORM
- `schemas.py`：Pydantic DTO

后续子 spec 沿用此切分，可独立交付。

---

## 4. 核心数据模型（11 张表）

只列关键字段；省略 `id` / `created_at` / `updated_at` / `deleted_at`（软删可选）。

### 4.1 用户与身份

**`users`**
- `email` (unique, indexed)
- `password_hash`
- `display_name`
- `status` (enum: `active` / `graduated` / `archived`)
- `role` (enum: `member` / `admin` / `owner`)
- `last_login_at`

**`user_profiles`**
- `user_id` (FK, unique)
- `enrollment_year`, `graduation_year`
- `research_direction`
- `current_affiliation`
- `bio`

### 4.2 入组与审核

**`invites`**
- `code` (unique, indexed)
- `created_by` (FK → users.id)
- `max_uses`, `used_count`
- `expires_at`
- `note`

**`audit_queue`**
- `user_id` (FK)
- `submitted_payload_json`
- `reviewer_id` (FK → users.id, nullable)
- `status` (enum: `pending` / `approved` / `rejected`)
- `decision_note`

### 4.3 课题与树状分类

**`projects`**
- `slug` (unique, indexed)
- `name`, `description`
- `status` (enum: `active` / `archived`)
- `owner_id` (FK → users.id)

**`categories`**
- `project_id` (FK, indexed)
- `parent_id` (FK self, nullable, indexed)
- `name`
- `path` (物化路径，例如 `/1/4/9/`, indexed)
- `order` (同级排序)
- unique constraint: (`project_id`, `parent_id`, `name`)

### 4.4 笔记

**`notes`**
- `project_id` (FK, indexed)
- `category_id` (FK, indexed)
- `author_id` (FK → users.id, indexed)
- `title`, `content_md`, `content_html` (渲染缓存)
- `version` (int)
- `status` (enum: `draft` / `published` / `archived`)
- `like_count`, `comment_count`, `view_count` (反范式冗余，读路径加速)
- `last_activity_at` (看板断代判定用)
- fulltext index: (`title`, `content_md`)（MySQL 5.7+ 内置 FULLTEXT）

**`note_versions`** (结构先建好，MVP 不写不查)
- `note_id` (FK)
- `version` (int)
- `content_md`
- `editor_id` (FK)
- `change_summary`

**`note_likes`** (避免同一用户重复点赞)
- `note_id` (FK), `user_id` (FK), unique (`note_id`, `user_id`)

### 4.5 评论与追问

**`comments`**
- `target_type` (enum: `note` / `comment`)
- `target_id` (bigint)
- `parent_id` (FK self, nullable) — 追问的回复层级
- `author_id` (FK)
- `content` (Markdown)
- `status` (enum: `open` / `answered` / `closed`)
- 索引: (`target_type`, `target_id`, `status`)

> 同一张 `comments` 表同时承担"普通评论"和"Issue 追问"两个角色。追问靠 `target_type=note` + `status` 表达，普通评论永远 `open` 不写状态机。

### 4.6 通知与异步

**`notifications`**
- `user_id` (FK, indexed)
- `type` (enum: `ask_opened` / `ask_answered` / `ask_closed` / `system`)
- `payload_json`
- `read_at` (nullable)
- 索引: (`user_id`, `read_at`)

**`email_outbox`**
- `to`, `cc`, `subject`, `body_text`, `body_html`
- `related_type`, `related_id` (用于关联追问/评论)
- `status` (enum: `queued` / `sent` / `failed`)
- `retry_count`, `last_error`
- `next_attempt_at`
- 索引: (`status`, `next_attempt_at`)

---

## 5. 权限模型

### 5.1 三档装饰器

| 装饰器 | 含义 |
|---|---|
| `@require_auth` | 必须登录 |
| `@require_role("admin", "owner")` | 必须是管理员或导师 |
| `@require_owner_or_admin` | 资源作者本人 OR 管理员 |

### 5.2 权限矩阵

| 行为 | 登录用户 | 作者 / 管理员 | 仅管理员 |
|---|---|---|---|
| 浏览笔记/项目/树 | ✅ | ✅ | ✅ |
| 写笔记/评论 | ✅ | ✅ | ✅ |
| 追问 Issue 状态变更 | ❌ | ✅ | ✅ |
| 删除/置顶笔记 | ❌ | ✅ | ✅ |
| 创建项目 | ❌ | ✅ | ✅ |
| 树状分类增删改 | ❌ | ✅ | ✅ |
| 审核注册申请 | ❌ | ❌ | ✅ |
| 改 `status`/`role` | ❌ | ❌ | ✅ |
| 查看看板 | ❌ | ❌ | ✅ |
| 改自己密码/资料 | ✅ | ✅ | ✅ |

### 5.3 身份状态流转

```
[外] ──invite+audit──▶ active ──毕业事件──▶ graduated ──长期不活跃──▶ archived
                              ▲
                              └── admin 可恢复
```

`role` 与 `status` 独立：`active+member` 是普通在读；`active+admin` 是大师兄；`graduated+member` 是普通校友；`graduated+owner` 不允许（owner 必须是 active）。

---

## 6. 核心 API（RESTful）

所有受保护接口需要 `Authorization: Bearer <jwt>`。响应统一 JSON，分页格式 `{items, total, page, page_size}`。

### 6.1 认证与账号

```
POST   /api/auth/login
POST   /api/auth/logout
POST   /api/auth/forgot-password
POST   /api/auth/reset-password
POST   /api/invites/redeem                # 邀请码注册（写入 audit_queue）

GET    /api/users/me
PATCH  /api/users/me
POST   /api/users/me/change-password
```

### 6.2 项目与树

```
GET    /api/projects
POST   /api/projects
GET    /api/projects/{slug}
PATCH  /api/projects/{slug}
GET    /api/projects/{slug}/categories/tree
POST   /api/projects/{slug}/categories
PATCH  /api/categories/{id}
DELETE /api/categories/{id}
```

### 6.3 笔记

```
GET    /api/notes?project=&category=&q=&author=&page=
POST   /api/notes
GET    /api/notes/{id}
PATCH  /api/notes/{id}
DELETE /api/notes/{id}
POST   /api/notes/{id}/like
DELETE /api/notes/{id}/like
```

### 6.4 评论与追问

```
GET    /api/notes/{id}/comments
POST   /api/notes/{id}/comments
PATCH  /api/comments/{id}                  # 改状态、改内容
GET    /api/projects/{slug}/asks           # 跨笔记汇总所有 open 追问（看板用）
```

### 6.5 通知

```
GET    /api/notifications?unread_only=
PATCH  /api/notifications/{id}/read
POST   /api/notifications/read-all
```

### 6.6 管理端

```
GET    /api/admin/audit-queue
POST   /api/admin/audit-queue/{id}/decision
GET    /api/admin/dashboard
GET    /api/admin/dashboard/stale-projects
GET    /api/admin/dashboard/hot-notes
GET    /api/admin/dashboard/failed-emails
POST   /api/admin/users/{id}/role
POST   /api/admin/users/{id}/status
```

---

## 7. 异步事件流（灵魂功能）

### 7.1 追问状态机

```
            open ──answer──▶ answered ──close──▶ closed
              │                  │
              └──close───────────┴──▶ closed
```

`comments.status` 字段驱动：`open`（默认）/ `answered`（被作者或其他人答复）/ `closed`（作者或管理员关闭）。每次状态变化触发：写 `notifications` + 写 `email_outbox`。

### 7.2 异步管道

```
师弟点击"向作者追问"
        │
        ▼
[comments] 写入 status=open
        │
        ▼
同步事务中：
  ├─ INSERT notifications (作者 user_id)
  └─ INSERT email_outbox(status=queued)
        │
        ▼
HTTP 响应返回 (≤ 200ms)
        │
        ▼
后台 worker (独立进程 python -m app.tasks.email_worker)
  轮询 email_outbox WHERE status='queued' AND next_attempt_at <= NOW()
        │
        ├─ 发成功 → status=sent
        ├─ 发失败 → retry_count++, next_attempt_at = NOW() + 2^retry_count min, 最多 5 次
        └─ 5 次仍失败 → status=failed (管理员看板可见)
```

### 7.3 "跨时空"额外保障

- **作者快照**：`notes` 表冗余 `author_display_name`、`author_enrollment_year`、`author_graduation_year`，避免账号 `archived` 后笔记失语境
- **失败显眼**：看板对 `status=failed` 邮件用红色 badge 突出，管理员可走其他渠道联系师兄
- **永久沉淀**：追问 + 答复永远挂在笔记下方，不因作者离线而消失
- **接口抽象**：邮件发送走 `EmailSender` 协议，未来切换 Celery+Redis 或 SES 不影响业务代码

### 7.4 后台 worker（MVP）

`backend/app/tasks/email_worker.py`：
- `asyncio` 单进程
- `while True` 循环，每 5 秒一批
- 用 `SELECT ... FOR UPDATE SKIP LOCKED` 抢占（MySQL 8 特性），允许多实例
- 日志走标准 logging

无 Redis / 无 Celery。本地 `docker compose up` 自动启动。云上同样命令。

---

## 8. 管理看板

### 8.1 `/api/admin/dashboard` 响应结构

```json
{
  "kpis": {
    "users": {"active": 30, "graduated": 48, "archived": 3},
    "pending_audits": 2,
    "open_asks": 7,
    "stale_projects": 3,
    "failed_emails": 1,
    "notes_total": 412,
    "comments_total": 1280
  },
  "stale_projects": [
    {"slug": "smart-car-2021", "name": "智能车 2021", "last_activity_at": "2025-09-12", "owner": "张三"}
  ],
  "hot_notes": [
    {"id": 88, "title": "激光雷达噪声处理实战", "project_slug": "smart-car-2021", "like_count": 42, "comment_count": 9}
  ],
  "unanswered_asks": [
    {"id": 1024, "note_id": 88, "asker": "李四", "opened_at": "2026-06-01", "days_open": 23}
  ],
  "failed_emails": [
    {"id": 7, "to": "alumnus@old-domain.com", "subject": "有人在追问你的笔记", "retry_count": 5, "last_error": "SMTP 550 ..."}
  ]
}
```

### 8.2 断代判定规则

`STALE_DAYS=90`（可配置）。`last_activity_at` 取自 `notes.last_activity_at` 与该项目下任何评论的 `updated_at` 的最大值。

---

## 9. 测试策略

| 层 | 工具 | 覆盖目标 |
|---|---|---|
| 后端单元 | `pytest` + `pytest-asyncio` | `service.py` 业务逻辑、状态机、权限装饰器 |
| 后端集成 | `pytest` + `httpx.AsyncClient` + 测试用 SQLite | 关键 API 端到端 |
| 前端组件 | `vitest` + `@vue/test-utils` | Markdown 渲染、树状分类、Issue 卡片 |
| 前端 E2E | `playwright`（后期 S6） | 登录 → 写笔记 → 追问 完整链路 |

**测试 DB**：本地默认 `aiosqlite:///:memory:`，CI 切到 MySQL service container。

**测试夹具（conftest）**：
- `db_session`：每个测试函数一个独立事务，回滚
- `client`：异步 HTTP 客户端
- `make_user(role, status)`：工厂函数
- `auth_headers(user)`：自动签 JWT

---

## 10. 部署

### 10.1 本地一键启动

```bash
git clone <repo>
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
docker compose -f deploy/docker-compose.yml up -d
sleep 10
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.scripts.seed   # 演示数据
# 浏览器打开 http://localhost:5173
```

`docker-compose.yml` 服务：
- `mysql`：MySQL 8，volume 持久化
- `backend`：uvicorn，挂载代码卷（开发模式热重载）
- `worker`：python -m app.tasks.email_worker
- `frontend`：vite dev server（开发模式）/ nginx（生产）

### 10.2 上云

- `backend/Dockerfile`：生产构建用 uvicorn + gunicorn，多 worker
- `frontend/Dockerfile`：生产构建用 nginx serve static
- MySQL 切云厂商 RDS
- 前端丢 CDN，后端丢云服务器 / K8s
- 配置域名 + HTTPS + 真实 SMTP
- `.env.production` 集中管理所有 secret

---

## 11. 后续子任务拆分（执行顺序）

每个子任务都是独立 spec + plan + 实现循环。**强烈建议按以下顺序**，每一阶段都能独立跑、独立可见：

| 编号 | 名称 | 产出可演示 |
|---|---|---|
| **S0** | 基础设施 | monorepo 骨架、Docker Compose 一键起、CI、最小 hello、健康检查 |
| **S1** | 账号与权限 | 注册邀请码 + 审核 + 登录 + JWT 中间件 |
| **S2** | 项目与树状分类 | 项目的 CRUD、物化路径树 |
| **S3** | 笔记核心 | 笔记 CRUD + Markdown 渲染 + 树内浏览 + 点赞 |
| **S4** | 评论 + 追问引擎 | 评论 + 状态机 + 邮件 outbox + worker + 站内通知 |
| **S5** | 看板与管理端 | 聚合数据 + admin dashboard + 身份转换 UI |
| **S6** | 打磨 | 搜索、忘记密码、OpenAPI 文档站、README、Playwright E2E |

---

## 12. 风险与未决项

| 风险 | 应对 |
|---|---|
| SMTP 域名/SPF 配置坑 | MVP 阶段允许在 `.env` 配任意 SMTP（QQ/163/Gmail 都行），上线再换成自有域名 |
| 物化路径在极端深嵌套下变慢 | 加 `path` 长度检查，超过 10 层拒绝（实验室场景足够） |
| 单一 owner 离职后无主 | `owner` 角色不允许 `graduated`；admin 列表必须 ≥ 2 人 |
| 历史数据迁移 | MVP 无历史数据，忽略 |
| 笔记搜索未来不够用 | 接口层抽象 `SearchBackend` 协议，MVP 用 LIKE，未来换 ES |

---

## 13. 文档与代码规范

- 后端：`ruff` lint + `ruff format`，`mypy --strict`
- 前端：`eslint` + `prettier`
- 提交：`conventional commits`（feat/fix/docs/refactor/test/chore）
- API 文档：FastAPI 自动 OpenAPI，导出到 `docs/api/openapi.json`
- README：含「本地开发」「上云部署」「架构总览」「贡献指南」四节
