# Deploy — local dev stack & production reference

## 本地开发（默认）

```bash
# 1. 复制环境变量
cp deploy/.env.example deploy/.env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# 2. 一键起服务
cd deploy
docker compose up -d

# 3. 等待 MySQL 健康
docker compose ps
# mysql: healthy / backend: running / frontend: running / worker: running

# 4. 验证
curl http://localhost:8000/health
# {"status":"ok"}

# 浏览器：http://localhost:5173
# API 文档：http://localhost:8000/docs
```

## 清理

```bash
# 停止并删除容器，保留数据卷
docker compose down

# 完全清理（含数据卷）
docker compose down -v
```

## 服务端口

| 服务 | 端口 | 用途 |
|---|---|---|
| frontend | 5173 | Vite dev server |
| backend | 8000 | uvicorn |
| mysql | 3306 | 数据库 |
| worker | - | 占位（S4 启用） |

## 生产部署

参见 [`docs/superpowers/plans/2026-06-24-s0-infrastructure-skeleton.md`](../docs/superpowers/plans/2026-06-24-s0-infrastructure-skeleton.md) 第 10 节，以及 S6 阶段的部署细化。