# LabInherit 开发快速参考

> 给开发者的"我拿到了仓库，接下来怎么搞"一页纸。
> 上线相关：见 [`deploy/README.md`](../deploy/README.md)。

## 1. 一次性环境准备

### 工具链

| 工具 | 最低版本 | 备注 |
|---|---|---|
| Python | 3.12+ | 后端 |
| uv | 任意 | 推荐；退回 `pip` 也能跑 |
| Node | 20 LTS | 前端 |
| pnpm | 9+ | 推荐；退回 `npm` 也能跑 |
| Docker | 20.10+ | 跑 MySQL 容器 |
| MySQL | 8.0+ | 容器即可，无需本地装 |

### Windows 提示

- PowerShell 即可。
- Docker Desktop for Windows 必装。
- 长路径支持：组策略开 `LongPathsEnabled`，避免路径过长失败。

## 2. 首次启动

```bash
# 0. 进入仓库根
cd labinherit

# 1. 复制环境变量
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
cp deploy/.env.example deploy/.env

# 2. 一键起服务
cd deploy
docker compose up -d

# 3. 等 MySQL 健康（约 15-30 秒首次）
docker compose ps
# 期望：mysql: (healthy)

# 4. 打开浏览器
# 前端：   http://localhost:5173
# API 文档：http://localhost:8000/docs
```

如果不想用 Docker，只跑前后端 + 远程 MySQL：

```bash
# 后端（需要本机 Python 3.12+）
cd backend
uv sync
uv run uvicorn app.main:app --reload --port 8000

# 前端（需要本机 Node 20+）
cd frontend
pnpm install
pnpm dev
```

## 3. 跑测试

```bash
# 后端
cd backend
uv run pytest

# 前端类型检查 + 构建
cd frontend
pnpm type-check
pnpm build
```

## 4. 数据库迁移

```bash
cd backend
# 生成新迁移（autogenerate）
uv run alembic revision --autogenerate -m "add xxx table"

# 应用迁移
uv run alembic upgrade head

# 回滚
uv run alembic downgrade -1
```

## 5. 代码风格

```bash
# 后端
cd backend
uv run ruff format .
uv run ruff check .

# 前端
cd frontend
pnpm format
pnpm lint
```

## 6. 提交代码

项目使用 [Conventional Commits](https://www.conventionalcommits.org/)：

```bash
git commit -m "feat(notes): add markdown rendering"
git commit -m "fix(auth): reject empty password"
git commit -m "docs: update s0 plan"
```

## 7. 常见问题

**Q：`docker compose up` 后 mysql 一直 starting？**
A：首次启动需要 15-30 秒初始化数据目录。看 `docker compose logs mysql`。

**Q：前端 5173 一直转圈 / 后端 fail？**
A：先看 `docker compose ps`，确认 backend 是 running；再 `curl http://localhost:8000/health`。

**Q：改了后端代码没生效？**
A：backend 容器是 `--reload` 模式，应该自动重启；没生效就 `docker compose restart backend`。

**Q：改了前端代码没生效？**
A：Vite HMR 应该自动刷新；浏览器缓存问题硬刷 `Ctrl+Shift+R`。

**Q：SMTP 怎么配？**
A：S0 不需要，S4 起会用到。届时在 `backend/.env` 填 `SMTP_HOST/PORT/USER/PASSWORD`。

## 8. 当前阶段（S0）状态

- ✅ 仓库骨架
- ✅ 后端 FastAPI 启动 + 健康检查 + 5 个测试通过
- ✅ 前端 Vue3 启动 + 后端联通
- ✅ Docker Compose 一键起
- ✅ CI：lint + format + test + build
- ⏳ 业务功能：S1–S6 依次交付
