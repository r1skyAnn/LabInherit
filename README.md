# LabInherit 实验室薪火传舵平台

> 把实验室历代项目经验结构化沉淀下来，让师弟师妹不再重复踩坑，让毕业师兄师姐的经验不随人离开。

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Vue 3.5+](https://img.shields.io/badge/vue-3.5+-green.svg)](https://vuejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-teal.svg)](https://fastapi.tiangolo.com/)

## 痛点

1. 师弟师妹重复踩同样的坑（环境/调参/Bug）
2. 毕业师兄师姐带走最宝贵的项目经验
3. 传统笔记没有"挂在哪个项目下"的强约束，散乱难找
4. 知识传承没有"异步追问"的闭环机制

## 核心特性

- **结构化**：笔记必须挂在【真实课题项目】下，分类支持无限级树
- **跨时空追问**：评论 + 类 GitHub Issue 状态机，邮件 SMTP 兜底，离线 10 年也不丢
- **身份管理**：在读/毕业/归档三态流转，导师 + 历代大师兄多级管理
- **质量看板**：断代项目、热帖、失败邮件一览无遗
- **Markdown 友好**：原生 MD 编辑，code/表格/公式一应俱全

## 快速开始

### 本地开发（5 分钟）

```bash
# 1. 克隆
git clone <repo-url> labinherit
cd labinherit

# 2. 准备环境变量
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# 3. 一键起服务
cd deploy
docker compose up -d

# 4. 等待 MySQL 健康（约 15-30 秒）
docker compose ps   # 等 mysql 变 healthy

# 5. 打开浏览器
# 前端：http://localhost:5173
# 后端 API 文档：http://localhost:8000/docs
```

### 生产部署（15 分钟）

```bash
# 1. 安装依赖（Ubuntu 22.04）
sudo apt install -y python3.12 nodejs npm mysql-server nginx

# 2. 配置数据库
sudo mysql -e "CREATE DATABASE labinherit; CREATE USER 'labinherit'@'localhost' IDENTIFIED BY 'strong_password';"

# 3. 克隆代码
cd /opt && git clone <repo-url> labinherit && cd labinherit

# 4. 配置环境变量
cp backend/.env.production.example backend/.env
nano backend/.env  # 修改 DB_PASSWORD、JWT_SECRET、SMTP_*

# 5. 一键部署
./deploy/deploy.sh

# 6. 配置 Nginx + HTTPS
sudo cp deploy/nginx/labinherit.conf /etc/nginx/sites-enabled/
sudo certbot --nginx -d your-domain.com
```

**📖 完整部署指南：** [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) | **🚀 快速清单：** [`docs/QUICKSTART_DEPLOY.md`](docs/QUICKSTART_DEPLOY.md)

## 技术栈

| 层 | 选型 | 说明 |
|---|---|---|
| 前端 | Vue 3 + Vite + TypeScript + Element Plus + Pinia | 现代 SPA，单页流畅体验 |
| 后端 | FastAPI + SQLAlchemy 2.x async + Pydantic v2 | 异步高性能，自动 OpenAPI |
| 数据库 | MySQL 8.0 | 实验室场景够用，运维简单 |
| 异步 | asyncio 单进程 worker | MVP 轻量，可升级 Celery+Redis |
| 部署 | Docker Compose | 本地一键，云上可直接迁 |

## 项目结构

```
labinherit/
├── backend/                FastAPI 后端（按业务域分包）
├── frontend/               Vue3 前端
├── deploy/                 Docker Compose 一键起
├── docs/
│   └── superpowers/
│       ├── specs/          设计 spec
│       └── plans/          实施 plan
└── .github/workflows/      CI
```

详细架构见 [`docs/superpowers/specs/2026-06-24-labinherit-architecture-design.md`](docs/superpowers/specs/2026-06-24-labinherit-architecture-design.md)。

## 开发指南

### 后端

```bash
cd backend
uv sync                 # 或 pip install -e .
uv run uvicorn app.main:app --reload --port 8000
uv run pytest
uv run ruff check .
uv run ruff format .
```

### 前端

```bash
cd frontend
pnpm install
pnpm dev
pnpm build
pnpm lint
```

## 路线图

| 阶段 | 名称 | 状态 |
|---|---|---|
| S0 | 基础设施（monorepo + docker + CI + hello） | ✅ 完成 |
| S1 | 账号与权限 | ✅ 完成 |
| S2 | 项目与树状分类 | ✅ 完成 |
| S3 | 笔记核心 | ✅ 完成 |
| S4 | 评论 + 追问引擎 | ✅ 完成 |
| S5 | 看板与管理端 | ✅ 完成 |
| S6 | 打磨与部署 | ✅ 完成 |

## 开发指南

详细架构见 [`docs/superpowers/specs/2026-06-24-labinherit-architecture-design.md`](docs/superpowers/specs/2026-06-24-labinherit-architecture-design.md)  
进度记录见 [`docs/PROGRESS.md`](docs/PROGRESS.md)

### 测试账号（运行 seed 后）

| 角色 | 邮箱 | 密码 |
|------|------|------|
| 导师 | owner@labinherit.local | Owner@123 |
| 大师兄 | admin1@labinherit.local | Admin@123 |
| 成员 | member1@labinherit.local | Member@123 |

### 运维操作

```bash
# 查看服务状态
sudo systemctl status labinherit-backend labinherit-worker

# 查看日志
sudo journalctl -u labinherit-backend -f

# 备份数据库
./deploy/backup-db.sh

# 健康检查
./deploy/healthcheck.sh

# 更新代码
git pull && ./deploy/deploy.sh
```

## 贡献指南

1. Fork → Feature Branch → PR
2. 提交遵循 [Conventional Commits](https://www.conventionalcommits.org/)
3. 后端 `ruff format` + `ruff check` 通过
4. 前端 `npm run lint` + `npm run build` 通过
5. 测试覆盖新增逻辑

## License

[MIT](LICENSE)
