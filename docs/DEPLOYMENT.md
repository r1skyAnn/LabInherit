# LabInherit 生产部署指南

> **适用场景：** 单台 Linux 服务器（Ubuntu 22.04+ / Debian 11+）部署完整应用

---

## 服务器要求

### 硬件配置
- CPU: 2 核心及以上
- 内存: 4GB 及以上
- 磁盘: 20GB 可用空间
- 网络: 公网 IP 或域名

### 软件环境
- **操作系统：** Ubuntu 22.04 LTS（推荐）
- **Python：** 3.12+
- **Node.js：** 20 LTS+
- **MySQL：** 8.0+
- **Nginx：** 1.18+
- **Git：** 2.x

---

## 一键部署步骤

### 1. 准备服务器

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装基础工具
sudo apt install -y git curl wget build-essential

# 安装 Python 3.12
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt install -y python3.12 python3.12-venv python3.12-dev

# 安装 Node.js 20
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# 安装 MySQL 8.0
sudo apt install -y mysql-server mysql-client

# 安装 Nginx
sudo apt install -y nginx

# 安装 uv（Python 包管理器，可选但推荐）
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc
```

### 2. 配置 MySQL

```bash
# 启动 MySQL
sudo systemctl start mysql
sudo systemctl enable mysql

# 安全配置（设置 root 密码）
sudo mysql_secure_installation

# 创建数据库和用户
sudo mysql -u root -p
```

在 MySQL 中执行：

```sql
CREATE DATABASE labinherit CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'labinherit'@'localhost' IDENTIFIED BY 'YOUR_STRONG_PASSWORD';
GRANT ALL PRIVILEGES ON labinherit.* TO 'labinherit'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 3. 克隆项目

```bash
# 创建项目目录
sudo mkdir -p /opt/labinherit
sudo chown $USER:$USER /opt/labinherit

# 克隆代码（使用你的仓库地址）
cd /opt
git clone https://github.com/your-org/labinherit.git
cd labinherit
```

### 4. 配置环境变量

#### 后端配置

```bash
# 复制配置模板
cp backend/.env.production.example backend/.env

# 编辑配置
nano backend/.env
```

**必须修改的配置项：**

```bash
# 改为 production
APP_ENV=production

# 改为你的域名
APP_CORS_ORIGINS=https://your-domain.com
APP_BASE_URL=https://your-domain.com

# 配置数据库（使用步骤 2 中创建的密码）
DB_HOST=localhost
DB_PASSWORD=YOUR_STRONG_PASSWORD

# 生成 32 位随机密钥（重要！）
JWT_SECRET=$(openssl rand -hex 32)

# 配置 SMTP（使用真实邮件服务）
SMTP_HOST=smtp.qq.com
SMTP_PORT=587
SMTP_USER=your-email@qq.com
SMTP_PASSWORD=your-smtp-auth-code
SMTP_FROM=your-email@qq.com

# 上传目录
UPLOAD_DIR=/data/labinherit/uploads
```

#### 前端配置

```bash
# 复制配置
cp frontend/.env.production.example frontend/.env.production

# 编辑（通常默认即可）
nano frontend/.env.production
```

### 5. 安装依赖

#### 后端依赖

```bash
cd backend

# 使用 uv（推荐）
uv sync

# 或使用 pip
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e .
```

#### 前端依赖

```bash
cd ../frontend
npm install
```

### 6. 数据库迁移

```bash
cd ../backend

# 执行迁移
uv run alembic upgrade head

# 或
source .venv/bin/activate
alembic upgrade head
```

### 7. 初始化数据（可选）

```bash
# 运行 seed 脚本创建测试账号
uv run python -m app.scripts.seed

# 会创建：
# - owner@labinherit.local (密码: Owner@123)
# - admin1@labinherit.local (密码: Admin@123)
# - member1@labinherit.local (密码: Member@123)
```

### 8. 构建前端

```bash
cd ../frontend
npm run build

# 构建产物在 dist/ 目录
```

### 9. 配置 Systemd 服务

```bash
# 复制服务文件
sudo cp deploy/labinherit-backend.service /etc/systemd/system/
sudo cp deploy/labinherit-worker.service /etc/systemd/system/

# 修改服务文件中的路径（如果不是 /opt/labinherit）
sudo nano /etc/systemd/system/labinherit-backend.service
sudo nano /etc/systemd/system/labinherit-worker.service

# 创建 www-data 用户（如果不存在）
sudo useradd -r -s /bin/false www-data || true

# 设置权限
sudo chown -R www-data:www-data /opt/labinherit
sudo mkdir -p /data/labinherit/uploads
sudo chown -R www-data:www-data /data/labinherit

# 重载 systemd
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start labinherit-backend
sudo systemctl start labinherit-worker

# 设置开机自启
sudo systemctl enable labinherit-backend
sudo systemctl enable labinherit-worker

# 检查状态
sudo systemctl status labinherit-backend
sudo systemctl status labinherit-worker
```

### 10. 配置 Nginx

```bash
# 复制配置文件
sudo cp deploy/nginx/labinherit.conf /etc/nginx/sites-available/

# 修改域名
sudo nano /etc/nginx/sites-available/labinherit.conf
# 将 your-domain.com 改为你的实际域名

# 启用站点
sudo ln -s /etc/nginx/sites-available/labinherit.conf /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重启 Nginx
sudo systemctl restart nginx
```

### 11. 配置 HTTPS（Let's Encrypt）

```bash
# 安装 certbot
sudo apt install -y certbot python3-certbot-nginx

# 申请证书（自动配置 Nginx）
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# 测试自动续期
sudo certbot renew --dry-run
```

### 12. 运行健康检查

```bash
cd /opt/labinherit
./deploy/healthcheck.sh
```

---

## 快速部署脚本

如果已完成步骤 1-4，可以使用一键部署脚本：

```bash
cd /opt/labinherit
./deploy/deploy.sh
```

脚本会自动：
- 拉取最新代码
- 安装依赖
- 执行数据库迁移
- 构建前端
- 重启服务

---

## 维护操作

### 查看日志

```bash
# 后端日志
sudo journalctl -u labinherit-backend -f

# Worker 日志
sudo journalctl -u labinherit-worker -f

# Nginx 日志
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### 备份数据库

```bash
cd /opt/labinherit
./deploy/backup-db.sh

# 备份文件保存在 /data/labinherit/backups/
```

### 恢复数据库

```bash
source backend/.env
gunzip < /data/labinherit/backups/labinherit_20260917_120000.sql.gz | \
  mysql -h"$DB_HOST" -u"$DB_USER" -p"$DB_PASSWORD" "$DB_NAME"
```

### 更新应用

```bash
cd /opt/labinherit
git pull origin master
./deploy/deploy.sh
```

### 重启服务

```bash
sudo systemctl restart labinherit-backend
sudo systemctl restart labinherit-worker
sudo systemctl restart nginx
```

---

## 监控建议

### 1. 使用 Uptime Kuma / Prometheus

```bash
# 监控 /health 端点
curl -f http://localhost:8000/health
```

### 2. 配置日志轮转

创建 `/etc/logrotate.d/labinherit`：

```
/var/log/labinherit/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        systemctl reload labinherit-backend > /dev/null 2>&1 || true
    endscript
}
```

### 3. 配置邮件告警

使用 cron 定时运行健康检查：

```bash
# 编辑 crontab
crontab -e

# 每 5 分钟检查一次
*/5 * * * * /opt/labinherit/deploy/healthcheck.sh || echo "LabInherit 健康检查失败" | mail -s "Alert" admin@your-domain.com
```

---

## 常见问题

### 1. 数据库连接失败

```bash
# 检查 MySQL 是否运行
sudo systemctl status mysql

# 检查用户权限
mysql -u labinherit -p -e "SHOW GRANTS;"
```

### 2. Worker 未发送邮件

```bash
# 检查 worker 日志
sudo journalctl -u labinherit-worker -n 100

# 检查 SMTP 配置
# 确保 SMTP_HOST 不是 smtp.example.com
```

### 3. 前端 404

```bash
# 检查 Nginx 配置
sudo nginx -t

# 检查前端文件是否存在
ls -la /opt/labinherit/frontend/dist/

# 检查 Nginx 权限
sudo chown -R www-data:www-data /opt/labinherit/frontend/dist/
```

### 4. JWT 校验失败

```bash
# 确保 JWT_SECRET 在重启后未改变
# 确保前后端的 APP_BASE_URL 一致
```

### 5. 上传文件失败

```bash
# 检查上传目录权限
ls -la /data/labinherit/uploads/
sudo chown -R www-data:www-data /data/labinherit/uploads/
sudo chmod 755 /data/labinherit/uploads/
```

---

## 性能优化

### 1. 数据库索引

所有必要索引已在迁移中创建，无需手动添加。

### 2. Nginx 缓存

已在配置文件中启用静态资源缓存和 Gzip 压缩。

### 3. 后端 Workers

根据 CPU 核心数调整 systemd 服务文件中的 `--workers` 参数：

```bash
# 推荐值：CPU 核心数 × 2 + 1
--workers 4
```

### 4. MySQL 优化

编辑 `/etc/mysql/mysql.conf.d/mysqld.cnf`：

```ini
[mysqld]
innodb_buffer_pool_size = 1G
max_connections = 200
query_cache_size = 0
query_cache_type = 0
```

---

## 安全加固

### 1. 防火墙

```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 2. 限制数据库访问

```bash
# 确保 MySQL 只监听 localhost
sudo nano /etc/mysql/mysql.conf.d/mysqld.cnf

# bind-address = 127.0.0.1
```

### 3. 定期更新

```bash
sudo apt update && sudo apt upgrade -y
```

---

## 支持与反馈

- 文档问题：查看项目 README.md
- Bug 反馈：提交 GitHub Issue
- 邮件支持：admin@your-domain.com
