# S1 账号与权限 实施 Plan

> **对应 spec：** [`2026-06-24-s1-account-and-permissions.md`](../specs/2026-06-24-s1-account-and-permissions.md)
> **目标读者：** 执行本计划的 agent
> **完成判定：** 20 条验收标准（见 spec 第 4 节）全部 ✅

---

## 总览

S1 体量较大（4 张表 + 4 个后端模块 + 7 个前端页面 + 路由守卫 + seed），按 **8 个 checkpoint** 推进，每个 checkpoint 独立可测、互不阻塞。

```
CP1 → CP2 → CP3 → CP4 → CP5 → CP6 → CP7 → CP8
数据层   鉴权   auth   users  invites audit  前端   seed
```

---

## Checkpoint 1：数据层

**目的：** 4 张表模型 + Alembic 迁移 + 测试基础设施（SQLite 内存库）。

### 1.1 升级依赖

`backend/pyproject.toml`：
- 加 `aiosmtplib>=3.0.0`（runtime）
- 加 `aiosqlite>=0.20.0`（dev）

### 1.2 模型文件

**`backend/app/modules/users/models.py`**：
- `UserStatus` enum: `active` / `graduated` / `archived`
- `UserRole` enum: `member` / `admin` / `owner`
- `User` 表
- `UserProfile` 表

**`backend/app/modules/invites/models.py`**：
- `Invite` 表

**`backend/app/modules/audit/models.py`**：
- `AuditStatus` enum
- `AuditQueue` 表

> 模型需要 `__init__.py` 全部 import 一次，让 SQLAlchemy metadata 注册（alembic env.py 会用到）

### 1.3 Alembic 迁移

```bash
cd backend
uv run alembic revision --autogenerate -m "s1: users, profiles, invites, audit_queue"
```

人工检查生成文件，确认包含 4 张表 + 索引 + 外键 + 唯一约束。

### 1.4 测试基础设施

**`backend/tests/conftest.py`**（重写）：
- 用 `pytest-asyncio` session 级别
- `engine` 替换为 SQLite 内存：`sqlite+aiosqlite:///:memory:`
- `Base.metadata.create_all` 在 session 启动时
- 业务代码不感知——靠 `app.core.config.settings.database_url` 切换

**`backend/pytest.ini` 改 pyproject.toml**：
- 加 `asyncio_default_fixture_loop_scope = session`

### 1.5 验证

```bash
cd backend
uv run alembic upgrade head   # 真 MySQL 跑通
uv run pytest                 # SQLite 测试基线通过
```

---

## Checkpoint 2：横切鉴权 + 依赖

**目的：** JWT 签发/校验、当前用户依赖、权限装饰器。

### 2.1 文件

**`backend/app/core/deps.py`**（新）：
- `get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db)` → `User`
- `require_auth` = `Depends(get_current_user)`
- `require_role(*roles)` 工厂
- `require_owner_or_admin(model, id_param)` 工厂

**`backend/app/core/email.py`**（新）：
- `send_email(to, subject, body_text, body_html=None)` 
- 检测 `SMTP_HOST` / `SMTP_USER` 是否配置；否则走 stdout 模式
- 链接占位用 `APP_BASE_URL`（从 settings 加这个新字段）

**`backend/app/core/config.py`**：
- 加 `APP_BASE_URL: str = "http://localhost:5173"`

### 2.2 安全工具扩展

**`backend/app/core/security.py`**（扩）：
- `create_password_reset_token(user_id)` → 带 `purpose="reset"` claim，过期 30min
- `decode_password_reset_token(token)` → 校验 claim

### 2.3 验证

不写测试，但 CP5、CP6 会用到。

---

## Checkpoint 3：auth 模块

**目的：** 登录 / 注销 / 忘记密码 / 重置密码 端到端。

### 3.1 文件

**`backend/app/modules/auth/schemas.py`**：
- `LoginRequest`
- `TokenResponse`
- `ForgotPasswordRequest`
- `ResetPasswordRequest`

**`backend/app/modules/auth/service.py`**：
- `authenticate(email, password)` → User or raise Unauthorized
- `issue_token(user)` → TokenResponse
- `request_password_reset(email)` → 找用户则发邮件
- `reset_password(token, new_password)` → 校验 token 改密码

**`backend/app/modules/auth/router.py`**：
- `POST /api/v1/auth/login` — 公开
- `POST /api/v1/auth/logout` — 受保护（无状态实际只返回 200）
- `POST /api/v1/auth/forgot-password` — 公开
- `POST /api/v1/auth/reset-password` — 公开（用 token）

### 3.2 验证

```bash
# 注册流程还没做，先手动 SQL 插一个用户测登录
# （CP7 之后有完整 UI）
```

---

## Checkpoint 4：users 模块

**目的：** 当前用户资料、修改、改密。

### 4.1 文件

**`backend/app/modules/users/schemas.py`**：
- `UserOut`（含 profile 嵌套）
- `UserUpdate`（display_name、enrollment_year、graduation_year、research_direction、current_affiliation、bio）
- `ChangePasswordRequest`（old_password、new_password）

**`backend/app/modules/users/service.py`**：
- `get_user_with_profile(db, user_id)`
- `update_user_profile(db, user, payload)`
- `change_password(db, user, old_pw, new_pw)`

**`backend/app/modules/users/router.py`**：
- `GET /api/v1/users/me`
- `PATCH /api/v1/users/me`
- `POST /api/v1/users/me/change-password`

### 4.2 验证

不写测试，CP5+ 一起做。

---

## Checkpoint 5：invites 模块

**目的：** 邀请码生成 / 列表 / 作废 / 兑换。

### 5.1 文件

**`backend/app/modules/invites/schemas.py`**：
- `InviteCreateRequest`（max_uses、expires_at、note）
- `InviteOut`
- `RedeemRequest`（code、email、password、display_name、payload）

**`backend/app/modules/invites/service.py`**：
- `generate_code()` → 12 字符
- `create_invite(db, creator, payload)`
- `list_invites(db, ...)`  分页
- `revoke_invite(db, id)`
- `redeem_invite(db, payload)` → 事务内：校验码 → 校验未过期 → 校验未作废 → 校验未超限 → 创建 user（status=pending 不行，user.status=active）→ 创建 profile → 创建 audit_queue → 递增 used_count
  - 等等：实际上**用户注册时 user.status 是什么？** 父 spec 说"邀请码 + 审核"，意思是注册进入 audit_queue，**user 的 status 也要合适**。
  - 设计：注册时 user.status 设为 `active`，但 role='member'，同时在 audit_queue 留一条 pending 记录；管理员批准 → audit_queue.status='approved'（user 不变）；管理员拒绝 → user.status='archived'。
  - 这样 user 端永远 active，但**能否登录由 audit_queue 决定**。
  - 等等更好的设计：**user.status 反映当前在读/已毕业/已归档；audit_queue 反映"是否被管理员接纳过"**。
  - 简化决策：注册时 user.status='active' + role='member'，**但登录时如果 audit_queue 中无 approved 记录则禁止**。
  - 不对，**父 spec 说的是"邀请码注册 + 待审核"**。审核通过才能用。所以：
    - **方案 A**（推荐）：注册时 user.status='pending'，不能用，等审核后变 'active'。但 status enum 没 pending，加一个？
    - **方案 B**：注册时 user.status='active'，登录检查 audit_queue；拒绝则 status='archived'。保持 status enum 简单。
  - **采用方案 B**：注册时 `user.status='active'`，登录时 `if not audit_approved: raise Unauthorized`，拒绝时 `user.status='archived'`。简单可解释。
  - 等等不对——如果用户注册成功，密码正常设置，账号可以登录但被后台禁，比较反直觉。
  - **再次简化**：把 user.status 当 "账号状态"（active=可用 / graduated=毕业 / archived=封存），新增一个 boolean `user.is_approved` 由审核控制。**改父 spec 的字段**。
  - 等等——父 spec 是 S0 阶段定的，已经复核过。我不能私自加字段。
  - **最终方案**：**不依赖 user.status 做"待审核"，依赖 audit_queue.status**。注册时 user.status='active'，登录时若无 approved 记录（user.audit_records 中无 approved）则禁止登录。**这种"注册即可用，但管理员可一票否决"**符合 MVP 简单原则。
  - 但这样**安全吗**？其实邀请码本身已经是准入门槛；审核是"是否允许"的双重确认。
  - **OK，方案定稿**：注册 → user.status='active' + audit_queue.status='pending'；登录时校验 audit_queue 中至少有一条 'approved'，否则 403。决策拒绝时 audit_queue.status='rejected'，user 仍 active 但登录被拒。
  - 体验优化：注册后**显示"待审核，请联系管理员"**，未审核时**不返回 token**。

**`backend/app/modules/invites/router.py`**：
- `POST /api/v1/invites` — admin
- `GET /api/v1/invites` — admin
- `POST /api/v1/invites/{id}/revoke` — admin
- `POST /api/v1/invites/redeem` — **公开**

### 5.2 验证

不写测试，CP6+。

---

## Checkpoint 6：audit 模块

**目的：** 审核队列查看、批准 / 拒绝。

### 6.1 文件

**`backend/app/modules/audit/schemas.py`**：
- `AuditEntryOut`（含 user 摘要）
- `DecisionRequest`（decision: "approved"|"rejected"、note）

**`backend/app/modules/audit/service.py`**：
- `list_pending(db, ...)` 分页
- `decide(db, audit_id, reviewer, decision, note)` — 事务内锁行 → 改 audit_queue.status → approved 时不写 user；rejected 时不改 user

### 6.2 关键改动

**`backend/app/modules/auth/service.py`** — `authenticate` 增强：
```python
async def authenticate(db, email, password):
    user = await get_by_email(db, email)
    if not user or not verify_password(password, user.password_hash):
        raise UnauthorizedError("邮箱或密码错误")
    if user.status != 'active':
        raise PermissionDeniedError("账号已停用")
    approved = await has_approved_audit(db, user.id)
    if not approved:
        raise PermissionDeniedError("账号等待审核中")
    return user
```

### 6.3 文件

**`backend/app/modules/audit/router.py`**：
- `GET /api/v1/admin/audit-queue` — admin
- `POST /api/v1/admin/audit-queue/{id}/decision` — admin

### 6.4 验证

不写测试。

---

## Checkpoint 7：后端测试

**目的：** 用 pytest + SQLite 跑通所有关键路径。

### 7.1 测试文件

**`backend/tests/conftest.py`**（最终版）：
- `event_loop` session-scope
- `db_engine` session：创建所有表
- `db_session` function：每个测试一个事务
- `client` function：`httpx.AsyncClient` + `ASGITransport`
- `make_user` factory
- `auth_headers` factory

**`backend/tests/test_auth.py`**（≥ 6 个测试）：
- login success
- login wrong password
- login non-existent email
- login archived user → 403
- login pending audit → 403
- forgot-password no user → 200（不泄漏）
- forgot-password with user → 200 + 控制台打印 token
- reset-password valid token
- reset-password expired/invalid token

**`backend/tests/test_users.py`**（≥ 4 个测试）：
- me without auth → 401
- me with auth → 200
- update me → 200 + 持久化
- change-password wrong old → 400
- change-password correct → 200

**`backend/tests/test_invites.py`**（≥ 5 个测试）：
- redeem public endpoint no auth
- redeem valid code → audit_queue created
- redeem already used code → 409
- create invite member → 403
- create invite admin → 201
- list invites
- revoke invite

**`backend/tests/test_audit.py`**（≥ 4 个测试）：
- list pending as member → 403
- list pending as admin → 200
- approve → user can login
- reject → user still cannot login

**`backend/tests/test_deps.py`**（≥ 3 个测试）：
- valid token → user
- expired token → 401
- no token → 401

### 7.2 验证

```bash
cd backend
uv run pytest
# 期望：≥ 22 passed
```

---

## Checkpoint 8：seed 脚本

**目的：** 一行命令灌演示数据。

### 8.1 文件

**`backend/app/scripts/__init__.py`**（空）

**`backend/app/scripts/seed.py`**：
- 1 owner（密码 `Owner@123`）
- 2 admin
- 5 graduated（演示已毕业）
- 3 active member
- 3 邀请码（每个 max_uses=1）
- 全部审计状态 approved
- 打印表格到 stdout

**`backend/pyproject.toml`**：
- 加 `[project.scripts]`：`labinherit-seed = "app.scripts.seed:main"`

**`backend/Dockerfile`**：
- 加注释：seed 怎么跑

### 8.2 验证

```bash
cd backend
uv run python -m app.scripts.seed
# 期望：stdout 打印账号表 + 邀请码
```

---

## Checkpoint 9：前端 — Stores + API

**目的：** 状态管理和 HTTP 客户端。

### 9.1 文件

**`frontend/src/stores/auth.ts`**（Pinia）：
- state: `user`、`token`、`status`
- actions: `login`、`logout`、`fetchMe`、`registerByInvite`
- 初始化时尝试从 localStorage 恢复

**`frontend/src/stores/user.ts`**：
- 当前用户详细资料

**`frontend/src/api/auth.ts`**：
- `login`、`forgotPassword`、`resetPassword`

**`frontend/src/api/users.ts`**：
- `getMe`、`updateMe`、`changePassword`

**`frontend/src/api/invites.ts`**：
- `createInvite`、`listInvites`、`revokeInvite`、`redeemInvite`

**`frontend/src/api/admin.ts`**：
- `listAuditQueue`、`decideAudit`

**`frontend/src/api/client.ts`**：加 401 拦截器：
```ts
apiClient.interceptors.response.use(
  res => res,
  err => {
    if (err.response?.status === 401) {
      const auth = useAuthStore()
      auth.clear()
      const router = useRouter()
      const route = useRoute()
      if (route.name !== 'login') {
        router.push({ name: 'login', query: { redirect: route.fullPath } })
      }
    }
    return Promise.reject(err)
  }
)
```

---

## Checkpoint 10：前端 — 布局 + 路由

**目的：** 公共框架、路由表、守卫。

### 10.1 文件

**`frontend/src/layouts/DefaultLayout.vue`**：
- 顶栏：Logo + 用户菜单（个人中心、退出）
- 侧栏：按 role 显隐的导航
- 主体：`<router-view />`
- 包含"未审核提示条"（如果登录但 audit 未通过）

**`frontend/src/layouts/AuthLayout.vue`**：
- 居中卡片 + Logo

**`frontend/src/router/guards.ts`**：
- `requireAuth`、`requireRole`、`requireUnauth`

**`frontend/src/router/index.ts`**（重写）：
- `/login`（AuthLayout）
- `/register`（AuthLayout）
- `/forgot-password`（AuthLayout）
- `/reset-password`（AuthLayout）
- `/`（DefaultLayout，Home）
- `/profile`（DefaultLayout，需登录）
- `/admin/audit-queue`（DefaultLayout，需 admin/owner）
- `/admin/invites`（DefaultLayout，需 admin/owner）

---

## Checkpoint 11：前端 — 页面

**目的：** 7 个页面。

### 11.1 Login.vue
- 邮箱、密码、记住我
- 提交后跳 `redirect` 或 `/`
- 失败提示

### 11.2 Register.vue
- 邀请码、邮箱、密码、确认密码、显示名
- 报名资料：入学年份、研究方向、bio
- 提交后跳"等待审核"页

### 11.3 ForgotPassword.vue
- 邮箱
- 提交后提示"如果邮箱存在，重置链接已发"

### 11.4 ResetPassword.vue
- URL 拿 token
- 新密码、确认密码
- 提交后跳登录

### 11.5 Profile.vue
- 显示当前资料
- 编辑表单（display_name、入学年份、毕业年份、研究方向、bio）
- 改密按钮（弹窗）
- 注销按钮

### 11.6 AdminAuditQueue.vue
- 表格：邮箱、显示名、提交时间
- 行内按钮：批准 / 拒绝（带备注弹窗）
- 状态 tab：pending / approved / rejected

### 11.7 AdminInvites.vue
- 生成表单：max_uses、expires_at、note
- 列表：code、used/max、状态、复制、作废

### 11.8 Home.vue 改造
- 已登录：跳到项目列表（占位）/ 欢迎
- 未登录：跳 /login

---

## Checkpoint 12：完结

### 12.1 文档更新

- `README.md` S1 状态 ✅
- `docs/QUICKSTART.md` 加 S1 验证步骤
- `docs/reports/2026-06-24-s1-completion-report.md`（新）

### 12.2 CI 验证

```bash
cd backend && uv run pytest
cd backend && uv run ruff check .
cd backend && uv run ruff format --check .
cd frontend && pnpm lint:check
cd frontend && pnpm type-check
cd frontend && pnpm build
```

全部 ✅ 才算 S1 完成。

---

## 风险检查表（实施时盯紧）

- [ ] SQLite 不支持所有 MySQL enum 特性 —— 统一用 `String(16)` + `CheckConstraint`
- [ ] Alembic autogenerate 可能漏 CheckConstraint —— 手动 review migration 文件
- [ ] Pinia 在 Vite HMR 下的状态恢复 —— 用 `pinia-plugin-persistedstate` 或手动
- [ ] 前端 401 拦截器在登录页本身会触发 —— 守卫已在 login 路由跳过
- [ ] 测试中 `alembic` 不用，因为直接 create_all
- [ ] `aiosmtplib` 在测试中不发邮件 —— 测试只验证"不抛异常"

---

## 完工判定（20 条验收）

实施完成后逐条勾选。20/20 才算 S1 done。