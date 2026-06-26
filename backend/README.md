# LabInherit Backend

FastAPI + SQLAlchemy 2.x async + Pydantic v2 + MySQL 8.

## 本地开发

```bash
# 方式 1：用 uv（推荐）
uv sync
uv run uvicorn app.main:app --reload --port 8000

# 方式 2：用 pip
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

## 跑测试

```bash
uv run pytest
```

## 代码质量

```bash
uv run ruff check .
uv run ruff format .
uv run mypy app
```

## 数据库迁移

```bash
# 生成新迁移
uv run alembic revision --autogenerate -m "add users table"

# 升级到最新
uv run alembic upgrade head

# 回滚一步
uv run alembic downgrade -1
```

## 关键端点

| 路径 | 说明 |
|---|---|
| `GET /health` | 简易存活探针 |
| `GET /api/v1/health` | 存活 + DB 连通性 |
| `GET /docs` | Swagger UI |
| `GET /redoc` | ReDoc |
| `GET /openapi.json` | OpenAPI 规范导出 |

## 目录约定

每个业务模块（auth/users/projects/...）固定四层：

- `router.py`：HTTP 边界（FastAPI APIRouter）
- `service.py`：业务逻辑（不依赖 FastAPI）
- `models.py`：SQLAlchemy ORM
- `schemas.py`：Pydantic DTO
