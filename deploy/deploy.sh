#!/bin/bash
# LabInherit 生产部署脚本
# 用法: ./deploy.sh [--skip-build] [--skip-migrate]

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

SKIP_BUILD=false
SKIP_MIGRATE=false

# Parse arguments
for arg in "$@"; do
  case $arg in
    --skip-build) SKIP_BUILD=true ;;
    --skip-migrate) SKIP_MIGRATE=true ;;
    *) echo "Unknown option: $arg"; exit 1 ;;
  esac
done

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  LabInherit 生产部署${NC}"
echo -e "${GREEN}========================================${NC}"

# ── Step 1: 检查环境配置 ──
echo -e "\n${YELLOW}[1/7] 检查环境配置...${NC}"

if [ ! -f "$BACKEND_DIR/.env" ]; then
  echo -e "${RED}错误: backend/.env 不存在${NC}"
  echo "请复制 backend/.env.production.example 并配置"
  exit 1
fi

if [ ! -f "$FRONTEND_DIR/.env.production" ]; then
  echo -e "${YELLOW}警告: frontend/.env.production 不存在，使用默认配置${NC}"
  cp "$FRONTEND_DIR/.env.production.example" "$FRONTEND_DIR/.env.production" || true
fi

# Check JWT secret
if grep -q "CHANGE_ME" "$BACKEND_DIR/.env"; then
  echo -e "${RED}错误: .env 中仍有 CHANGE_ME 占位符，请配置真实密钥${NC}"
  exit 1
fi

echo -e "${GREEN}✓ 环境配置检查通过${NC}"

# ── Step 2: 拉取最新代码（如果是 git 仓库）──
echo -e "\n${YELLOW}[2/7] 同步代码...${NC}"
if [ -d "$PROJECT_ROOT/.git" ]; then
  cd "$PROJECT_ROOT"
  git pull origin master || echo "跳过 git pull (可能是本地部署)"
else
  echo "非 git 仓库，跳过代码拉取"
fi

# ── Step 3: 安装后端依赖 ──
echo -e "\n${YELLOW}[3/7] 安装后端依赖...${NC}"
cd "$BACKEND_DIR"

if command -v uv &> /dev/null; then
  echo "使用 uv 安装依赖..."
  uv sync
elif [ -f "requirements.txt" ]; then
  echo "使用 pip 安装依赖..."
  pip install -r requirements.txt
else
  echo -e "${RED}错误: 未找到 uv 或 requirements.txt${NC}"
  exit 1
fi

echo -e "${GREEN}✓ 后端依赖安装完成${NC}"

# ── Step 4: 数据库迁移 ──
if [ "$SKIP_MIGRATE" = false ]; then
  echo -e "\n${YELLOW}[4/7] 执行数据库迁移...${NC}"
  cd "$BACKEND_DIR"
  
  # Backup database first
  source .env
  BACKUP_FILE="/tmp/labinherit_backup_$(date +%Y%m%d_%H%M%S).sql"
  echo "备份数据库到 $BACKUP_FILE ..."
  mysqldump -h"$DB_HOST" -u"$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" > "$BACKUP_FILE" 2>/dev/null || echo "备份跳过(数据库可能不存在)"
  
  echo "运行 alembic upgrade head..."
  if command -v uv &> /dev/null; then
    uv run alembic upgrade head
  else
    alembic upgrade head
  fi
  
  echo -e "${GREEN}✓ 数据库迁移完成${NC}"
else
  echo -e "\n${YELLOW}[4/7] 跳过数据库迁移 (--skip-migrate)${NC}"
fi

# ── Step 5: 构建前端 ──
if [ "$SKIP_BUILD" = false ]; then
  echo -e "\n${YELLOW}[5/7] 构建前端...${NC}"
  cd "$FRONTEND_DIR"
  
  if [ ! -d "node_modules" ]; then
    echo "安装前端依赖..."
    npm install
  fi
  
  echo "打包前端..."
  npm run build
  
  echo -e "${GREEN}✓ 前端构建完成 (dist/)${NC}"
else
  echo -e "\n${YELLOW}[5/7] 跳过前端构建 (--skip-build)${NC}"
fi

# ── Step 6: 检查并创建上传目录 ──
echo -e "\n${YELLOW}[6/7] 检查上传目录...${NC}"
source "$BACKEND_DIR/.env"
UPLOAD_DIR="${UPLOAD_DIR:-./uploads}"

if [ ! -d "$UPLOAD_DIR" ]; then
  echo "创建上传目录: $UPLOAD_DIR"
  mkdir -p "$UPLOAD_DIR"
fi

chmod 755 "$UPLOAD_DIR"
echo -e "${GREEN}✓ 上传目录就绪: $UPLOAD_DIR${NC}"

# ── Step 7: 重启服务 ──
echo -e "\n${YELLOW}[7/7] 重启服务...${NC}"

# 检测 systemd 服务
if systemctl is-active --quiet labinherit-backend.service; then
  echo "重启 labinherit-backend.service..."
  sudo systemctl restart labinherit-backend.service
  echo "重启 labinherit-worker.service..."
  sudo systemctl restart labinherit-worker.service
  echo -e "${GREEN}✓ Systemd 服务已重启${NC}"
elif command -v supervisorctl &> /dev/null; then
  echo "使用 supervisor 重启..."
  sudo supervisorctl restart labinherit:*
  echo -e "${GREEN}✓ Supervisor 服务已重启${NC}"
else
  echo -e "${YELLOW}未检测到 systemd 或 supervisor，请手动重启服务${NC}"
  echo "后端启动: cd $BACKEND_DIR && uvicorn app.main:app --host 0.0.0.0 --port 8000"
  echo "Worker 启动: cd $BACKEND_DIR && python -m app.tasks.email_worker"
fi

# ── 完成 ──
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  部署完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "后端 API: http://your-server:8000/docs"
echo "前端文件: $FRONTEND_DIR/dist/"
echo ""
echo "下一步:"
echo "1. 配置 Nginx 代理（参考 deploy/nginx/labinherit.conf）"
echo "2. 运行健康检查: ./deploy/healthcheck.sh"
echo "3. 查看服务日志: sudo journalctl -u labinherit-backend -f"
