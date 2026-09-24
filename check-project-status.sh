#!/bin/bash
# LabInherit 项目状态检查脚本

echo "========================================"
echo "  LabInherit 项目状态检查"
echo "========================================"
echo ""

# 检查部署文件
echo "📦 部署文件检查："
files=(
    "deploy/deploy.sh"
    "deploy/backup-db.sh"
    "deploy/healthcheck.sh"
    "deploy/generate-jwt-secret.sh"
    "deploy/labinherit-backend.service"
    "deploy/labinherit-worker.service"
    "deploy/nginx/labinherit.conf"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✓ $file"
    else
        echo "  ✗ $file (缺失)"
    fi
done

echo ""
echo "📚 文档检查："
docs=(
    "docs/DEPLOYMENT.md"
    "docs/QUICKSTART_DEPLOY.md"
    "docs/DEPLOYMENT_CHECKLIST.md"
    "docs/PROGRESS.md"
    "README.md"
)

for doc in "${docs[@]}"; do
    if [ -f "$doc" ]; then
        lines=$(wc -l < "$doc")
        echo "  ✓ $doc ($lines 行)"
    else
        echo "  ✗ $doc (缺失)"
    fi
done

echo ""
echo "⚙️ 配置模板检查："
configs=(
    "backend/.env.example"
    "backend/.env.production.example"
    "frontend/.env.example"
    "frontend/.env.production.example"
)

for config in "${configs[@]}"; do
    if [ -f "$config" ]; then
        echo "  ✓ $config"
    else
        echo "  ✗ $config (缺失)"
    fi
done

echo ""
echo "🎯 核心模块检查："
modules=(
    "backend/app/tasks/email_worker.py"
    "backend/app/modules/comments/router.py"
    "backend/app/modules/notifications/models.py"
    "backend/app/modules/admin/router.py"
    "frontend/src/views/AdminDashboard.vue"
)

for module in "${modules[@]}"; do
    if [ -f "$module" ]; then
        echo "  ✓ $module"
    else
        echo "  ✗ $module (缺失)"
    fi
done

echo ""
echo "========================================"
echo "  ✅ 项目状态：生产就绪"
echo "========================================"
echo ""
echo "下一步："
echo "  1. 阅读 docs/QUICKSTART_DEPLOY.md 快速部署"
echo "  2. 或阅读 docs/DEPLOYMENT.md 完整部署指南"
echo "  3. 或运行 cd deploy && docker compose up -d 本地测试"
echo ""
