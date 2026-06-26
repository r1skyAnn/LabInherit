# S1 账号与权限 子 Spec

> **对应父 spec：** [`2026-06-24-labinherit-architecture-design.md`](./2026-06-24-labinherit-architecture-design.md) 第 4–6 节
> **前一阶段：** [`2026-06-24-s0-infrastructure-skeleton.md`](./2026-06-24-s0-infrastructure-skeleton.md)
> **日期：** 2026-06-24

## 1. 目标

把"账号与权限"这条主线**完整**做出来，让 S2 之后的所有业务接口都建立在稳定可靠的认证与权限基础之上。

**S1 结束后，** 你能：
- 用账号密码登录
- 邀请码 + 邮箱注册一个新用户（进入审核队列）
- 管理员审批通过后，新用户变成 `active+member` 才能登录
- 修改自己的资料 / 头像 / 密码
- 忘记密码 → 邮箱重置链接（开发期打印到控制台）
- 管理员生成 / 列出 / 作废邀请码
- 管理员列出 / 决策审核队列
- 受保护 API 强制要登录；越权调用 401/403

## 2. 范围（必须做）

### 2.1 数据模型（Alembic 迁移）

4 张表，与父 spec 第 4 节一致：

**`users`**
- `id` (bigint PK)
- `email` (varchar(255) unique, indexed)
- `password_hash` (varchar(255))
- `display_name` (varchar(64))
- `status` (enum: `active` / `graduated` / `archived`)
- `role` (enum: `member` / `admin` / `owner`)
- `last_login_at` (datetime nullable)
- `created_at`, `updated_at`

**`user_profiles`**
- `id` PK
- `user_id` (FK users.id, unique)
- `enrollment_year`, `graduation_year` (smallint nullable)
- `research_direction` (varchar(128) nullable)
- `current_affiliation` (varchar(128) nullable)
- `bio` (text nullable)
- `avatar_url` (varchar(512) nullable)

**`invites`**
- `id` PK
- `code` (varchar(32) unique, indexed) — 自动生成的随机码
- `created_by` (FK users.id)
- `max_uses` (int, default 1)
- `used_count` (int, default 0)
- `expires_at` (datetime nullable)
- `note` (varchar(255) nullable)
- `revoked_at` (datetime nullable) — 软作废
- `created_at`

**`audit_queue`**
- `id` PK
- `user_id` (FK users.id, indexed)
- `submitted_payload_json` (JSON) — 报名时填的资料
- `reviewer_id` (FK users.id nullable)
- `status` (enum: `pending` / `approved` / `rejected`)
- `decision_note` (text nullable)
- `decided_at` (datetime nullable)
- `created_at`, `updated_at`

### 2.2 后端模块

**`app/modules/auth/`**
- `router.py`：`/api/v1/auth/login`、`/logout`、`/forgot-password`、`/reset-password`
- `service.py`：登录态校验、密码 hash 校验、token 签发
- `schemas.py`：`LoginRequest`、`TokenResponse`、`ForgotPasswordRequest`、`ResetPasswordRequest`
- 无 `models.py`（auth 是横切关注点）

**`app/modules/users/`**
- `router.py`：`/api/v1/users/me`、`PATCH /me`、`POST /me/change-password`
- `service.py`：当前用户信息读写
- `models.py`：`User`、`UserProfile`
- `schemas.py`：`UserOut`、`UserUpdate`、`ChangePasswordRequest`

**`app/modules/invites/`**
- `router.py`：
  - `POST /api/v1/invites` — 管理员创建
  - `GET /api/v1/invites` — 管理员列表
  - `POST /api/v1/invites/{id}/revoke` — 管理员作废
  - `POST /api/v1/invites/redeem` — **公开**！任何人凭邀请码 + 邮箱报名
- `service.py`：码生成（secrets.token_urlsafe）、原子递增 used_count
- `models.py`：`Invite`
- `schemas.py`：`InviteOut`、`InviteCreateRequest`、`RedeemRequest`

**`app/modules/audit/`**
- `router.py`：
  - `GET /api/v1/admin/audit-queue` — 管理员列表
  - `POST /api/v1/admin/audit-queue/{id}/decision` — 批准 / 拒绝
- `service.py`：决策时切换 `users.status` → active
- `models.py`：`AuditQueue`
- `schemas.py`：`AuditEntryOut`、`DecisionRequest`

### 2.3 横切：`app/core/deps.py`（新增）

- `get_current_user(token, db)` FastAPI Depends
- `require_role(*roles)` 装饰器工厂
- `require_owner_or_admin(getattr_fn, id_param)` 装饰器工厂

### 2.4 邮件（dev 模式：控制台打印）

- `app/utils/email.py`：`send_email(to, subject, body_text, body_html)`
- 优先用 `aiosmtplib` 发；SMTP 配置不全时**降级到 stdout**（带明显 banner 方便开发期看）
- 重置密码链接：`{APP_BASE_URL}/reset-password?token=...`
- 审核通过通知：写 subject + body，调用同一个 send_email

### 2.5 Alembic 迁移

- `alembic revision --autogenerate -m "s1: users, profiles, invites, audit_queue"`
- 在 `alembic/versions/` 生成一个或多个 migration 文件
- 保留 `alembic upgrade head` 可用

### 2.6 后端测试（pytest，SQLite 内存库）

- `tests/test_auth.py`：登录成功/失败/账号被 archive
- `tests/test_users.py`：me/patch/change-password
- `tests/test_invites.py`：生成/兑换/作废/超限
- `tests/test_audit.py`：列表/决策
- `tests/test_deps.py`：依赖注入、权限拒绝

> 关键设计：**测试用 SQLite 内存库**（`aiosqlite`），不需要真 MySQL。生产路径由 CI 跑。

### 2.7 前端模块

**`src/stores/auth.ts`**（Pinia）
- state：`user`、`token`、`status`（loading/ready）
- actions：`login`、`logout`、`fetchMe`、`register`
- 持久化：`token` 存 `localStorage`，刷新自动恢复

**`src/stores/user.ts`**
- 当前用户详细资料缓存

**API 封装**：
- `src/api/auth.ts`：`login`、`forgotPassword`、`resetPassword`
- `src/api/users.ts`：`getMe`、`updateMe`、`changePassword`
- `src/api/invites.ts`：`createInvite`、`listInvites`、`revokeInvite`、`redeemInvite`
- `src/api/admin.ts`：`listAuditQueue`、`decideAudit`

**页面**（views）：
- `Login.vue` — 邮箱 + 密码，登录成功跳 `/` 或上一个页面
- `ForgotPassword.vue` — 输入邮箱，发重置链接
- `ResetPassword.vue` — 链接带 token，重置新密码
- `Register.vue` — 邀请码 + 邮箱 + 密码 + 显示名 + 报名资料，提交后进审核队列
- `Profile.vue` — 我的资料编辑 + 改密 + 注销
- `AdminAuditQueue.vue` — 管理员视角，批准 / 拒绝
- `AdminInvites.vue` — 管理员视角，生成 / 列表 / 作废邀请码

**布局**：
- `layouts/DefaultLayout.vue` — 顶栏（Logo + 用户菜单 + 登出）+ 侧栏（导航，按角色显隐）+ 主体区
- `layouts/AuthLayout.vue` — 简洁居中卡片（登录/注册/重置用）

**路由守卫**：
- `router/guards.ts`：`requireAuth`、`requireRole('admin','owner')`
- 在路由 meta 里声明 `requiresAuth`、`requiredRoles`

**API 客户端增强**：
- 401 时自动清 token 跳登录

### 2.8 seed 脚本（`app/scripts/seed.py`）

- 创建 1 个 `owner`：`owner@labinherit.local` / `Owner@123`
- 创建 2 个 admin
- 创建 5 个 graduated（已毕业师兄师姐，演示用）
- 创建 3 个 active member
- 生成 3 个邀请码（每个 max_uses=1）
- 打印到 stdout 方便你直接登录测试

## 3. 不在 S1 范围（明确不做）

- ❌ OAuth / 第三方登录
- ❌ 邮箱验证激活（邀请码审核 = 激活）
- ❌ 头像上传（S2+ 加 OSS / 本地）
- ❌ 多角色叠加（一人只有一个 role）
- ❌ 团队 / 组织 / 实验室（先单实验室）
- ❌ 任何业务笔记 / 项目 / 评论
- ❌ 通知中心（站内通知 S4 引入）
- ❌ 真实的邮件发送（dev 模式仅控制台）
- ❌ 速率限制 / 验证码（防刷留 S6）
- ❌ 前端 vitest（S3 一起做）

## 4. 验收标准（S1 完成的客观判定）

每一条都要在终端或浏览器中**可复现**：

### 4.1 数据层
1. ✅ `alembic upgrade head` 跑通，4 张表建好
2. ✅ `alembic downgrade -1` 回滚成功

### 4.2 后端 API
3. ✅ `POST /api/v1/invites/redeem` 公开可用 → 写入 audit_queue
4. ✅ `POST /api/v1/auth/login` 正确账号返回 JWT，错误返回 401
5. ✅ `archived` 用户登录返回 403
6. ✅ `GET /api/v1/users/me` 无 token 401，有 token 200
7. ✅ `POST /api/v1/admin/audit-queue/{id}/decision` 批准后该用户能登录，拒绝后不能
8. ✅ `POST /api/v1/invites` 普通用户 403，admin 200
9. ✅ 邀请码超 `max_uses` 后 redeem 409

### 4.3 测试
10. ✅ `uv run pytest` 全部通过（预计 ≥ 20 个测试）

### 4.4 前端
11. ✅ 访问 `/login` 输入 owner 账号登录成功，token 存 localStorage
12. ✅ 邀请码注册流程：填邀请码 + 邮箱 + 密码 → 提示"等待审核"
13. ✅ 管理员登录 → 进入审核队列 → 批准 → 新账号能登录
14. ✅ 邀请码生成页：管理员能创建并看到码
15. ✅ 忘记密码：提交邮箱后控制台看到重置链接
16. ✅ 未登录访问 `/profile` 跳 `/login`
17. ✅ 普通用户访问 `/admin/audit-queue` 跳 403 提示页

### 4.5 综合
18. ✅ seed 脚本运行后 stdout 打印所有可登录账号 + 邀请码
19. ✅ `ruff check` + `pnpm lint:check` + `pnpm build` 全部通过
20. ✅ 演示数据下完成"邀请码注册 → 审核通过 → 登录"完整链路

## 5. 关键决策

### 5.1 测试用 SQLite 内存库

- `pyproject.toml` 加 `aiosqlite` 到 dev
- `tests/conftest.py` 用 `pytest-asyncio` + `engine.begin()` 在每个 session 创建表，结束时 drop
- 业务代码不感知差异（同一个 SQLAlchemy 异步接口）

### 5.2 Token 形态

- JWT，`sub` 是 `user.id` 字符串
- payload 额外带 `role`、`status`，方便日志和审计
- 有效期 24h（与父 spec 一致）
- 无 refresh token（MVP 不做）

### 5.3 密码强度

- 注册时：≥ 8 字符
- 修改密码：旧密码 + 新密码双重校验
- 忘记密码重置：邮件链接 + 一次性 token（30 分钟过期，独立 claim）

### 5.4 邀请码生成

- 12 字符 `secrets.token_urlsafe(9)`，去掉 `-` `_` 易混字符
- 大写便于复制：`code.upper().replace('-','').replace('_','')[:12]`
- 全表唯一约束

### 5.5 审计决策的并发安全

- 决策时 `SELECT ... FOR UPDATE` 锁 audit_queue 行
- 批准用 `users.status = 'active'` 事务内更新
- 拒绝不改 users，保留在 audit_queue.status='rejected'

### 5.6 邮件降级策略

- `send_email` 函数先尝试 SMTP，失败 / 配置不全时走 stdout
- stdout 模式打印 banner + 链接，方便 dev 测试

## 6. 风险与缓解

| 风险 | 缓解 |
|---|---|
| SQLite 异步不支持所有 SQLAlchemy 特性 | 只用最普通的：枚举/JSON/字符串索引 |
| 邮箱 token 泄漏 | 30 分钟过期 + 一次性（用过的 token 标记为 used） |
| 邀请码暴力枚举 | 12 字符 + 96^12 空间；预留 rate-limit 钩子（S6 加） |
| JWT secret 弱 | S0 已加 ≥ 16 字符校验 |
| 软删除一致性 | `users.status` 是状态字段，不是软删除；硬删除不做 |

## 7. S1 完成后的检查清单

- [ ] 4 张表迁移成功
- [ ] ≥ 20 个测试通过
- [ ] 前端能跑完整流程
- [ ] seed 脚本可用
- [ ] 完结报告
- [ ] README 章节更新（S1 状态：完成）