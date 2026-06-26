# S0 基础设施 实施 Plan

> **对应 spec：** [`2026-06-24-s0-infrastructure-skeleton.md`](./2026-06-24-s0-infrastructure-skeleton.md)
> **目标读者：** 执行本计划的 agent（包括我自己后续接手时）
> **完成判定：** 12 条验收标准（见 spec 第 4 节）全部 ✅

---

## 任务分组

按"代码可独立验证"切成 5 个 checkpoint。每个 checkpoint 完成后**做一次 `git commit`**，失败就回滚到上一个 checkpoint。

---

## Checkpoint 1：仓库根 + git + 通用配置

**目的：** 让仓库成为一个标准、规范、可被 git 跟踪的项目。

### 1.1 操作清单

```bash
# 1. git init
cd F:\VibeCodingCase\sss
git init
git config user.email "you@example.com"   # 用户后续可改
git config user.name "Your Name"

# 2. 创建目录骨架
mkdir -p backend/app/{core,db,modules,schemas,tasks,utils}
mkdir -p backend/tests
mkdir -p frontend/src/{api,stores,router,views,components,utils}
mkdir -p deploy/nginx
mkdir -p docs/superpowers/specs docs/superpowers/plans docs/api
mkdir -p .github/workflows
```

### 1.2 文件清单

- `.gitignore`（Python + Node + Vue + IDE + OS + .env + 数据卷）
- `.editorconfig`（LF 行尾、UTF-8、缩进 4 空格 Python / 2 空格前端）
- `.gitattributes`（统一 LF）
- `LICENSE`（MIT）
- `README.md`（含徽章占位 + 项目简介 + 「快速开始」 + 「开发指南」 + 「部署」 + 「架构文档链接」）

### 1.3 验证

```bash
git status          # 应该看到很多 untracked
ls -la              # 看到所有目录
cat .gitignore      # 看到合理规则
```

### 1.4 提交

```bash
git add .
git commit -m "chore(scaffold): bootstrap LabInherit monorepo skeleton"
```

---

## Checkpoint 2：Backend 最小可跑

**目的：** 独立跑通 FastAPI，暴露 `/health`，能连 MySQL（即使还没表）。

### 2.1 操作清单

```bash
cd backend

# 用 uv 初始化（用户没装 uv 时退回 pip）
uv init --python 3.12 --no-readme
# 或：python -m venv .venv && source .venv/bin/activate
```

### 2.2 文件清单

**`backend/pyproject.toml`**：声明所有依赖与开发依赖；`[tool.ruff]` 配置。

**`backend/.env.example`**：
```
APP_NAME=LabInherit
APP_ENV=local
APP_DEBUG=true
APP_HOST=0.0.0.0
APP_PORT=8000
APP_CORS_ORIGINS=http://localhost:5173

DB_HOST=mysql
DB_PORT=3306
DB_USER=labinherit
DB_PASSWORD=labinherit_dev
DB_NAME=labinherit

# S1 起会用，先占位
JWT_SECRET=change-me-in-production-please
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM=noreply@labinherit.local
```

**`backend/app/core/config.py`**：pydantic-settings 配置类。

**`backend/app/db/session.py`**：SQLAlchemy 异步引擎 + `get_db` 依赖。

**`backend/app/core/exceptions.py`**：全局异常类。

**`backend/app/core/middleware.py`**：CORS + 异常处理中间件。

**`backend/app/main.py`**：
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.middleware import register_middlewares
from app.api.v1 import api_v1_router

app = FastAPI(title=settings.APP_NAME, debug=settings.APP_DEBUG)
register_middlewares(app)
app.include_router(api_v1_router, prefix="/api/v1")

@app.get("/health", tags=["meta"])
async def health():
    return {"status": "ok"}
```

**`backend/app/api/__init__.py`** + **`backend/app/api/v1/__init__.py`**：聚合所有路由，S0 只含 `health` 路由。

**`backend/app/api/v1/health.py`**：返回 `{"status":"ok","db":"ok"}`（尝试一次 DB ping）。

**`backend/alembic.ini`** + **`backend/alembic/env.py`** + **`backend/alembic/script.py.mako`**：Alembic 初始化，配置为异步。

**`backend/alembic/versions/.gitkeep`**。

**`backend/Dockerfile`**：
```dockerfile
FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir uv
COPY pyproject.toml ./
RUN uv pip install --system -e .
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

**`backend/.dockerignore`**：排除 `.venv`、`.env`、`__pycache__`、`tests/`。

**`backend/tests/__init__.py`** + **`backend/tests/test_health.py`**：一个最小 pytest。

**`backend/README.md`**：单独说明 backend 启动方式。

### 2.3 验证（本地，不依赖 Docker）

```bash
cd backend
uv sync                      # 或 pip install -e .
uv run uvicorn app.main:app --reload --port 8000
# 另一个终端：
curl http://localhost:8000/health
# 期望：{"status":"ok"}

curl http://localhost:8000/api/v1/health
# 期望：{"status":"ok","db":"fail"|"ok"}  (本地没 MySQL，db:fail 是预期的，但应用不能崩)

curl http://localhost:8000/docs
# 期望：Swagger UI

uv run pytest
# 期望：1 passed

uv run ruff check .
uv run ruff format --check .
```

### 2.4 提交

```bash
git add backend/
git commit -m "feat(backend): bootstrap FastAPI skeleton with health checks"
```

---

## Checkpoint 3：Frontend 最小可跑

**目的：** 独立跑通 Vue3 + Vite + TypeScript，能渲染首页并调用后端健康检查。

### 3.1 操作清单

```bash
cd frontend
pnpm create vite@latest . -- --template vue-ts
# 用户没 pnpm 时退到 npm
```

### 3.2 文件清单

**`frontend/package.json`**：脚本 `dev` / `build` / `preview` / `lint` / `format`，依赖含上述清单。

**`frontend/vite.config.ts`**：
```typescript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'
import path from 'node:path'

export default defineConfig({
  plugins: [
    vue(),
    AutoImport({ resolvers: [ElementPlusResolver()] }),
    Components({ resolvers: [ElementPlusResolver()] }),
  ],
  resolve: {
    alias: { '@': path.resolve(__dirname, 'src') },
  },
  server: {
    port: 5173,
    proxy: { '/api': { target: 'http://localhost:8000', changeOrigin: true } },
  },
})
```

**`frontend/tsconfig.json`** + **`tsconfig.node.json`**：路径别名 + 严格模式。

**`frontend/src/main.ts`**：挂载 router、pinia、Element Plus。

**`frontend/src/router/index.ts`**：一个 `/` 路由，指向 `views/Home.vue`。

**`frontend/src/stores/.gitkeep`**。

**`frontend/src/api/client.ts`**：axios 实例，baseURL `/api/v1`，拦截器占位。

**`frontend/src/api/health.ts`**：调用 `/health`。

**`frontend/src/views/Home.vue`**：渲染 "LabInherit" 标题 + 后端健康状态徽章。

**`frontend/src/App.vue`**：基础布局。

**`frontend/src/style.css`**：基础 reset。

**`frontend/eslint.config.js`**：Vue3 + TS 规则。

**`frontend/.prettierrc.json`**。

**`frontend/.env.example`**：
```
VITE_API_BASE=/api/v1
```

**`frontend/Dockerfile`**：
```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json pnpm-lock.yaml* ./
RUN corepack enable && pnpm install
COPY . .
EXPOSE 5173
CMD ["pnpm", "dev", "--host", "0.0.0.0"]
```

**`frontend/.dockerignore`**：排除 `node_modules`、`dist`、`.env`。

**`frontend/README.md`**：单独说明 frontend 启动方式。

### 3.3 验证（本地）

```bash
cd frontend
pnpm install
pnpm dev
# 浏览器打开 http://localhost:5173
# 看到 "LabInherit" 标题 + 绿色 "Backend: ok" 徽章（前提：后端在跑）
pnpm build
pnpm lint
pnpm format
```

### 3.4 提交

```bash
git add frontend/
git commit -m "feat(frontend): bootstrap Vue3 + Vite + TS skeleton"
```

---

## Checkpoint 4：Docker Compose 一键起

**目的：** 一个命令把整个栈跑起来。

### 4.1 文件清单

**`deploy/docker-compose.yml`**：
```yaml
name: labinherit

services:
  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: rootpass
      MYSQL_DATABASE: labinherit
      MYSQL_USER: labinherit
      MYSQL_PASSWORD: labinherit_dev
    volumes:
      - mysql_data:/var/lib/mysql
    ports:
      - "3306:3306"
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-uroot", "-prootpass"]
      interval: 5s
      timeout: 5s
      retries: 10
    networks: [labinherit-net]

  backend:
    build:
      context: ../backend
      dockerfile: Dockerfile
    env_file: ../backend/.env
    environment:
      DB_HOST: mysql
    ports:
      - "8000:8000"
    volumes:
      - ../backend:/app
    depends_on:
      mysql: { condition: service_healthy }
    networks: [labinherit-net]

  worker:
    build:
      context: ../backend
      dockerfile: Dockerfile
    command: ["python", "-c", "import time; print('worker placeholder'); [time.sleep(3600) for _ in iter(int, 1)]"]
    env_file: ../backend/.env
    environment:
      DB_HOST: mysql
    depends_on:
      mysql: { condition: service_healthy }
    networks: [labinherit-net]

  frontend:
    build:
      context: ../frontend
      dockerfile: Dockerfile
    ports:
      - "5173:5173"
    volumes:
      - ../frontend:/app
      - /app/node_modules
    environment:
      VITE_API_BASE: /api/v1
    depends_on:
      - backend
    networks: [labinherit-net]

volumes:
  mysql_data:

networks:
  labinherit-net:
    driver: bridge
```

**`deploy/.env.example`**：
```
MYSQL_ROOT_PASSWORD=rootpass
MYSQL_PASSWORD=labinherit_dev
```

### 4.2 验证

```bash
cp deploy/.env.example deploy/.env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

cd deploy
docker compose up -d
# 等 30 秒
docker compose ps
# 期望：mysql healthy, 其他 running

curl http://localhost:8000/api/v1/health
# 期望：{"status":"ok","db":"ok"}

# 浏览器打开 http://localhost:5173
# 期望：LabInherit + Backend: ok
```

### 4.3 关闭 & 清理

```bash
docker compose down            # 停止，保留 volume
docker compose down -v         # 完全清理（含数据）
```

### 4.4 提交

```bash
git add deploy/
git commit -m "feat(deploy): add docker-compose for local dev stack"
```

---

## Checkpoint 5：CI

**目的：** push 即跑 lint + test + build。

### 5.1 文件清单

**`.github/workflows/ci.yml`**：
```yaml
name: CI

on: [push, pull_request]

jobs:
  backend:
    runs-on: ubuntu-latest
    services:
      mysql:
        image: mysql:8.0
        env:
          MYSQL_ROOT_PASSWORD: rootpass
          MYSQL_DATABASE: labinherit
          MYSQL_USER: labinherit
          MYSQL_PASSWORD: labinherit_dev
        ports: ['3306:3306']
        options: --health-cmd="mysqladmin ping" --health-interval=5s --health-retries=10
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - name: Install uv
        run: pip install uv
      - name: Sync deps
        working-directory: backend
        run: uv sync
      - name: Ruff check
        working-directory: backend
        run: uv run ruff check .
      - name: Ruff format check
        working-directory: backend
        run: uv run ruff format --check .
      - name: Pytest
        working-directory: backend
        env:
          DB_HOST: 127.0.0.1
          DB_PORT: 3306
          DB_USER: labinherit
          DB_PASSWORD: labinherit_dev
          DB_NAME: labinherit
          JWT_SECRET: ci-secret
        run: uv run pytest

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
        with: { version: 9 }
      - uses: actions/setup-node@v4
        with: { node-version: 20, cache: pnpm, cache-dependency-path: frontend/pnpm-lock.yaml }
      - name: Install
        working-directory: frontend
        run: pnpm install --frozen-lockfile
      - name: Lint
        working-directory: frontend
        run: pnpm lint
      - name: Build
        working-directory: frontend
        run: pnpm build
```

### 5.2 验证

```bash
git add .github/
git commit -m "ci: add GitHub Actions for backend + frontend"
git push
# 在 GitHub 上看 Actions 是否绿
```

---

## Checkpoint 6：根 README 收口

把 README 写完整，包含：

1. 项目简介（一句话 + 痛点）
2. **演示截图/ASCII 框占位**（S3 之后换真实截图）
3. 快速开始（5 步本地启动）
4. 开发指南（前后端分别怎么跑 + 怎么测试）
5. 部署指南（指向 deploy/）
6. 架构文档（链接到 `docs/superpowers/specs/`）
7. 贡献指南
8. License

---

## 风险检查表（实施时盯紧）

- [ ] Docker 是否在本机可用？版本 ≥ 20.10？
- [ ] uv / pnpm / Node 20 / Python 3.12 是否就绪？若没有，README 给出降级方案
- [ ] Windows 路径在 Docker volume 挂载时是否需要转 win-style？默认 Compose 已经处理
- [ ] 端口 3306/5173/8000 是否被占用？
- [ ] alembic env.py 是否正确处理异步（这是 S0 最常踩的坑）？

---

## 完工判定（12 条验收）

实施完成后逐条勾选，全部 ✅ 才算 S0 done。任何一条失败都不能进入 S1。