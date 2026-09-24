#!/bin/bash
# LabInherit 健康检查脚本
# 用法: ./healthcheck.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"

ERRORS=0

echo "========================================="
echo "  LabInherit 健康检查"
echo "========================================="

# ── 1. 后端健康检查 ──
echo -n "后端健康检查... "
if curl -f -s http://127.0.0.1:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗ 后端无响应${NC}"
    ERRORS=$((ERRORS + 1))
fi

# ── 2. Worker 进程检查 ──
echo -n "Worker 进程检查... "
if pgrep -f "app.tasks.email_worker" > /dev/null; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗ Worker 未运行${NC}"
    ERRORS=$((ERRORS + 1))
fi

# ── 3. 数据库连接检查 ──
echo -n "数据库连接检查... "
if [ -f "$BACKEND_DIR/.env" ]; then
    source "$BACKEND_DIR/.env"
    if mysqladmin ping -h"$DB_HOST" -u"$DB_USER" -p"$DB_PASSWORD" --silent 2>/dev/null; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗ 数据库连接失败${NC}"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo -e "${YELLOW}⊘ 跳过 (.env 不存在)${NC}"
fi

# ── 4. 磁盘空间检查 ──
echo -n "磁盘空间检查... "
DISK_USAGE=$(df -h / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -lt 90 ]; then
    echo -e "${GREEN}✓ (${DISK_USAGE}% 已用)${NC}"
else
    echo -e "${RED}✗ 磁盘空间不足 (${DISK_USAGE}% 已用)${NC}"
    ERRORS=$((ERRORS + 1))
fi

# ── 5. 前端文件检查 ──
echo -n "前端文件检查... "
if [ -f "$PROJECT_ROOT/frontend/dist/index.html" ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${YELLOW}⊘ 前端未构建 (运行 npm run build)${NC}"
fi

# ── 6. 上传目录权限检查 ──
if [ -f "$BACKEND_DIR/.env" ]; then
    source "$BACKEND_DIR/.env"
    echo -n "上传目录检查... "
    UPLOAD_DIR="${UPLOAD_DIR:-./uploads}"
    if [ -d "$UPLOAD_DIR" ] && [ -w "$UPLOAD_DIR" ]; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗ 上传目录不可写: $UPLOAD_DIR${NC}"
        ERRORS=$((ERRORS + 1))
    fi
fi

# ── 7. Systemd 服务状态 ──
if command -v systemctl &> /dev/null; then
    echo ""
    echo "Systemd 服务状态:"
    for service in labinherit-backend labinherit-worker; do
        if systemctl is-active --quiet "$service.service" 2>/dev/null; then
            echo -e "  ${GREEN}✓${NC} $service.service"
        else
            echo -e "  ${RED}✗${NC} $service.service (未运行或未安装)"
        fi
    done
fi

# ── 总结 ──
echo ""
echo "========================================="
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}所有检查通过！${NC}"
    exit 0
else
    echo -e "${RED}发现 $ERRORS 个问题${NC}"
    exit 1
fi
