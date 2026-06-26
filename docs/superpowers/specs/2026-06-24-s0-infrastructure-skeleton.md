# S0 基础设施 子 Spec

> **本 spec 是 LabInherit 整体架构设计的第一阶段实施规范。**
> **父 spec：** [`2026-06-24-labinherit-architecture-design.md`](./2026-06-24-labinherit-architecture-design.md)
> **日期：** 2026-06-24

## 1. 目标

把项目的"骨架"立起来，让后续 S1–S6 都能在可运行的环境里增量交付。**S0 结束后，你应该能 `git clone && docker compose up`，5 分钟内看到前后端的 hello 页面。**

## 2. 范围（必须做）

### 2.1 monorepo 骨架

完整仓库结构按父 spec 第 3 节落地，但每个目录在 S0 阶段是"空壳 + 最小占位文件"：

- `backend/`：FastAPI 项目，能起 `uvicorn app.main:app`，暴露 `/health` 和 `/api/v1/health`
- `frontend/`：Vue3 + Vite 项目，能起 `npm run dev`，显示 "LabInherit" 首页
- `deploy/docker-compose.yml`：一键起 mysql + backend + worker(占位) + frontend
- `docs/`：架构 spec + 本子 spec
- `.gitignore`、`.editorconfig`、`README.md`

### 2.2 后端最小实现

- FastAPI + Uvicorn
- SQLAlchemy 2.x **异步**配置（连 MySQL，但 S0 不创建业务表，只连上）
- Alembic 初始化（空 migration）
- 配置管理：`pydantic-settings` 读 `.env`
- CORS 中间件（前端 dev 调后端用）
- 健康检查：`GET /health`、`GET /api/v1/health` 返回 `{"status": "ok"}`
- 基础错误处理中间件
- Dockerfile（开发模式：挂载代码卷，热重载）
- `.env.example`

### 2.3 前端最小实现

- Vue 3.4+ + Vite 5+ + TypeScript 5+
- Vue Router 4（一个首页 `/`）
- Pinia（基础配置，不写 store）
- Axios（封装一个 `apiClient`，拦截器占位）
- Element Plus（按需引入，配置好但 S0 不实际用复杂组件）
- Vite proxy：开发期 `/api` 转发到 `http://backend:8000`
- 健康检查调用：首页展示 "Backend: ok / fail"
- Dockerfile（开发模式：vite dev server）
- `.env.example`

### 2.4 Docker Compose

服务：
- `mysql`：MySQL 8.0，volume 持久化，健康检查
- `backend`：uvicorn 开发模式，热重载
- `worker`：占位脚本（`while true; do sleep 3600; done`），等 S4 替换
- `frontend`：vite dev server，端口 5173

网络：所有服务在 `labinherit-net` 网络。
依赖：backend 等 mysql 健康通过才启动。

### 2.5 CI（最小）

GitHub Actions，单 workflow 文件 `.github/workflows/ci.yml`：
- 后端：`ruff check`、`ruff format --check`、`pytest`（即使没测试也要能跑出 0 失败）
- 前端：`npm run lint`、`npm run build`
- 触发：push / PR

### 2.6 git 初始化

`git init`，提交 S0 所有文件，commit message 遵循 conventional commits：`chore(scaffold): bootstrap LabInherit monorepo skeleton`。

## 3. 不在 S0 范围（明确不做）

- ❌ 任何业务模型（users/notes/projects 等）—— S1 之后才有
- ❌ 任何业务 API（除健康检查）—— S1+
- ❌ 任何认证逻辑 —— S1
- ❌ Alembic 业务迁移 —— S1
- ❌ 前端业务页面 —— S3+
- ❌ 反向代理 nginx —— S6
- ❌ HTTPS / 域名 —— 上云时
- ❌ 真正的 worker 进程 —— S4
- ❌ Playwright E2E —— S6

## 4. 验收标准（S0 完成的客观判定）

每一条都必须在终端实际跑过、有可见输出：

1. ✅ `git status` 显示工作区干净（除了可能的 .env）
2. ✅ `cat README.md` 显示完整"如何本地启动"说明
3. ✅ `docker compose -f deploy/docker-compose.yml up -d` 成功启动 4 个容器
4. ✅ `docker compose ps` 显示 mysql `healthy`，其他 `running`
5. ✅ 浏览器访问 `http://localhost:5173` 显示 "LabInherit" + "Backend: ok"
6. ✅ `curl http://localhost:8000/api/v1/health` 返回 `{"status":"ok"}`
7. ✅ `curl http://localhost:8000/docs` 显示 Swagger UI（即使只有 health 接口）
8. ✅ `cd backend && ruff check .` 通过
9. ✅ `cd frontend && npm run build` 成功
10. ✅ `cd frontend && npm run lint` 通过
11. ✅ README 顶部有"演示截图/SVG 占位"
12. ✅ `.env.example` 完整，`.env` 已 gitignore

## 5. 关键决策（不可绕过）

### 5.1 后端 Python 版本与依赖

- Python 3.12+
- 包管理：`uv`（快、现代、面试加分）；pyproject.toml 标准
- 关键依赖版本范围：
  - `fastapi>=0.115`
  - `uvicorn[standard]>=0.32`
  - `sqlalchemy[asyncio]>=2.0.36`
  - `aiomysql>=0.2.0`
  - `alembic>=1.14`
  - `pydantic-settings>=2.6`
  - `python-jose[cryptography]>=3.3`（S1 用，S0 先装上避免后续冲突）
  - `passlib[bcrypt]>=1.7.4`（S1 用）
  - `pytest>=8.3` + `pytest-asyncio>=0.24` + `httpx>=0.28`

### 5.2 前端关键依赖

- Node 20 LTS+
- 包管理：`pnpm`（快、节省磁盘、面试加分）
- `vue@^3.5`
- `vite@^5.4`
- `typescript@^5.6`
- `vue-router@^4.4`
- `pinia@^2.2`
- `axios@^1.7`
- `element-plus@^2.8`
- `@vueuse/core@^11`
- `eslint@^9` + `@vue/eslint-config-typescript`
- `prettier@^3.3`

### 5.3 端口约定

- 前端 dev：5173
- 后端 dev：8000
- MySQL：3306（容器内）

### 5.4 路径别名

- 前端：`@/` → `src/`
- 后端：`app.` 显式导入（不用相对路径）

## 6. 风险与缓解

| 风险 | 缓解 |
|---|---|
| Windows 上 Docker 启动慢 | README 提示"首次启动 5-10 分钟属于正常" |
| MySQL 容器首次启动需等待初始化 | docker-compose 加 healthcheck，backend depends_on condition: service_healthy |
| Python 3.12 在 Windows 上装 uv 出问题 | README 提供 pip 安装备选 |
| pnpm 未安装 | README 提供 npm/yarn 备选 |
| Windows 路径反斜杠在某些命令里炸 | 全部用 `python -m xxx` 风格，避免裸脚本 |

## 7. S0 完成后，进入 S1 前的检查清单

- [ ] 仓库结构完整
- [ ] 前后端各自能独立启
- [ ] docker compose 一键起
- [ ] CI 通过
- [ ] README 写好
- [ ] 第一次 git commit 已完成