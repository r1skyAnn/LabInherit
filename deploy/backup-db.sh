#!/bin/bash
# 数据库备份脚本
# 用法: ./backup-db.sh [backup-dir]

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"

# 默认备份目录
BACKUP_DIR="${1:-/data/labinherit/backups}"

# 加载数据库配置
if [ ! -f "$BACKEND_DIR/.env" ]; then
    echo "错误: backend/.env 不存在"
    exit 1
fi

source "$BACKEND_DIR/.env"

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 生成备份文件名
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/labinherit_${TIMESTAMP}.sql"

echo "备份数据库: $DB_NAME"
echo "目标文件: $BACKUP_FILE"

# 执行备份
mysqldump \
    -h"$DB_HOST" \
    -P"$DB_PORT" \
    -u"$DB_USER" \
    -p"$DB_PASSWORD" \
    --single-transaction \
    --routines \
    --triggers \
    --events \
    "$DB_NAME" > "$BACKUP_FILE"

# 压缩备份
gzip "$BACKUP_FILE"
BACKUP_FILE="${BACKUP_FILE}.gz"

echo "备份完成: $BACKUP_FILE"
echo "文件大小: $(du -h "$BACKUP_FILE" | cut -f1)"

# 清理 30 天前的备份
find "$BACKUP_DIR" -name "labinherit_*.sql.gz" -mtime +30 -delete
echo "已清理 30 天前的备份"
