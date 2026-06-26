# LabInherit 开发进度总结

> 日期：2026-06-25（更新）

---

## 已完成

### S0 - 基础设施 ✅ (2026-06-24)
- monorepo 骨架（backend/ + frontend/ + deploy/）
- FastAPI 后端入口 + 健康检查 + CORS + 异常处理
- SQLAlchemy 异步配置 + Alembic 迁移框架
- Vue3 + Vite + TypeScript + Element Plus 前端骨架
- Docker Compose 配置
- CI（GitHub Actions）

### S1 - 账号与权限 ✅ (2026-06-24)
- **数据模型**：users / user_profiles / invites / audit_queue（4 张表）
- **后端模块**：auth / users / invites / audit + JWT 中间件 + 权限装饰器
- **前端页面**（6 个）：登录 / 注册 / 忘记密码 / 重置密码 / 个人资料 / 审核队列 / 邀请码管理
- **测试**：20+ pytest 用例

### S2 - 项目与分类树 ✅ (2026-06-25)
- **数据模型**：projects / categories（物化路径树，每项目独立）
- **后端模块**：projects（CRUD）+ categories（CRUD + 树构建 + 路径维护）
- **前端页面**：项目列表 + 项目详情 + 分类管理
- **组件**：ProjectCard / ProjectForm / CategoryTree
- **测试**：11 个 projects 用例 + 10 个 categories 用例

### S3 - 笔记核心 ✅ (2026-06-25)
- **数据模型**：notes（作者快照：姓名/邮箱/入学/毕业年份）
- **后端模块**：notes（CRUD + 搜索 + 点赞）
- **前端页面**：笔记列表（筛选/搜索）+ 笔记详情（Markdown 渲染）
- **组件**：NoteCard / NoteForm / MarkdownRenderer
- **图片上传**：POST /api/v1/upload（按项目+笔记隔离存储，格式校验）
- **置顶**：is_pinned 切换（列表 + 详情页）
- **测试**：10 个 notes 用例

---

## 开发环境修复的 Bug

| 文件 | 问题 | 修复 |
|------|------|------|
| `app/main.py` | `add_exception_handler` 漏参数 | 补 `AppError` + `Exception` |
| `app/main.py` | email-validator 拒 `.local` 域名 | monkey-patch + `special_use_domain_names` 黑名单 |
| `app/modules/users/models.py` | `audit_records` FK 歧义 | 指定 `foreign_keys` |
| `app/modules/audit/service.py` | `decide` 返 ORM 崩 `model_validate` | 手动 `AuditEntryOut` |
| `src/router/index.ts` | 路由守卫 `requiresAuth` 倒置 → 死循环 | `!== false` → `=== true` |
| `src/stores/auth.ts` | 登录后先调 `/users/me` 再存 token → 401 | 先存 token |
| `vite.config.ts` | 缺 `base` + `server` 被误删 | 补 `server:` 结构 |
| `backend/.env` | bcrypt 5.0.0 不兼容 passlib | `pip install bcrypt==4.0.1` |

---

## 数据库迁移链

`alembic/versions/`
- `s1_account_permissions` → base
- `s2_projects` → projects
- `s3_announcements_members` → announcements
- `s4_categories` → categories
- `s5_notes` → notes

---

## 当前启动方式

```bash
# 后端
cd backend
alembic upgrade head        # 跑过 s5_notes 迁移
uvicorn app.main:app --reload --port 8000
http://localhost:5173/labinherit/  # 前端
npm run dev                    # Vite HMR
```

---

## 登录测试账号（seed 后可用）

| 角色 | 邮箱 | 密码 |
|------|------|------|
| 导师(owner) | owner@labinherit.local | Owner@123 |
| 大师兄(admin) | admin1@labinherit.local | Admin@123 |
| 大师兄(admin) | admin2@labinherit.local | Admin@223 |
| 在读成员 | member1@labinherit.local | Member@123 |
| 已毕业 | alumni1@labinherit.local | Grad@123 |
| 待审核 | pending@labinherit.local | Pending@123 |

---

## 仍待开发（按顺序）

| 编号 | 内容 |
|------|------|
| **S4** | 评论 + 追问引擎（状态机 + 邮件 outbox + worker + 站内通知） |
| **S5** | 看板与管理端（聚合数据 + admin dashboard + 身份转换 UI） |
| **S6** | 打磨（搜索、OpenAPI 文档站、E2E） |
