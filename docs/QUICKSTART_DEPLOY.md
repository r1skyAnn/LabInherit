# LabInherit 部署快速清单

> **目标：** 15 分钟内完成生产部署

---

## 前置条件检查

- [ ] Ubuntu 22.04+ 服务器，2C4G+ 配置
- [ ] 域名已解析到服务器 IP
- [ ] SSH root 或 sudo 权限
- [ ] SMTP 邮箱授权码（QQ/163/企业邮箱）

---

## 部署步骤

### 1. 一键安装依赖（5 分钟）

```bash
# 复制粘贴执行
sudo apt update && sudo apt install -y \
  python3.12 python3.12-venv python3.12-dev \
  nodejs npm mysql-server nginx git curl

# 安装 uv（可选，加速依赖安装）
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc
```

### 2. 配置数据库（2 分钟）

```bash
# 启动 MySQL
sudo systemctl start mysql

# 创建数据库（替换密码）
sudo mysql -e "
CREATE DATABASE labinherit CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'labinherit'@'localhost' IDENTIFIED BY 'YOUR_DB_PASSWORD';
GRANT ALL PRIVILEGES ON labinherit.* TO 'labinherit'@'localhost';
FLUSH PRIVILEGES;
"
```

### 3. 克隆代码（1 分钟）

```bash
sudo mkdir -p /opt/labinherit
sudo chown $USER:$USER /opt/labinherit
cd /opt
git clone YOUR_REPO_URL labinherit
cd labinherit
```

### 4. 配置环境变量（3 分钟）

```bash
# 后端配置
cp backend/.env.production.example backend/.env
nano backend/.env

# 必须修改：
# - APP_CORS_ORIGINS=https://your-domain.com
# - APP_BASE_URL=https://your-domain.com
# - DB_PASSWORD=YOUR_DB_PASSWORD
# - JWT_SECRET=$(openssl rand -hex 32)
# - SMTP_HOST/USER/PASSWORD（真实邮箱）

# 前端配置（通常默认即可）
cp frontend/.env.production.example frontend/.env.production
```

### 5. 一键部署（4 分钟）

```bash
chmod +x deploy/*.sh
./deploy/deploy.sh
```

脚本自动完成：
- ✅ 安装依赖
- ✅ 数据库迁移
- ✅ 前端构建
- ✅ 配置 systemd
- ✅ 启动服务

### 6. 配置 Nginx（2 分钟）

```bash
# 复制配置
sudo cp deploy/nginx/labinherit.conf /etc/nginx/sites-available/

# 修改域名
sudo nano /etc/nginx/sites-available/labinherit.conf
# 替换 your-domain.com 为真实域名

# 启用站点
sudo ln -s /etc/nginx/sites-available/labinherit.conf /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 7. 配置 HTTPS（自动，1 分钟）

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### 8. 健康检查

```bash
./deploy/healthcheck.sh
```

期望输出：
```
=========================================
  LabInherit 健康检查
=========================================
后端健康检查... ✓
Worker 进程检查... ✓
数据库连接检查... ✓
磁盘空间检查... ✓ (45% 已用)
前端文件检查... ✓
上传目录检查... ✓
=========================================
所有检查通过！
=========================================
```

---

## 快速验证

1. 打开浏览器访问 `https://your-domain.com`
2. 点击「登录」
3. 使用测试账号（如果运行了 seed）：
   - 邮箱：`owner@labinherit.local`
   - 密码：`Owner@123`
4. 创建项目 → 添加笔记 → 发表评论

---

## 常用命令

```bash
# 查看服务状态
sudo systemctl status labinherit-backend
sudo systemctl status labinherit-worker

# 查看日志
sudo journalctl -u labinherit-backend -f
sudo journalctl -u labinherit-worker -f

# 重启服务
sudo systemctl restart labinherit-backend labinherit-worker nginx

# 备份数据库
./deploy/backup-db.sh

# 更新代码
cd /opt/labinherit
git pull
./deploy/deploy.sh
```

---

## 故障排查

### 后端 502 错误
```bash
# 检查后端是否运行
curl http://127.0.0.1:8000/health

# 查看错误日志
sudo journalctl -u labinherit-backend -n 50
```

### 邮件不发送
```bash
# 检查 worker 日志
sudo journalctl -u labinherit-worker -f

# 检查 SMTP 配置
grep SMTP backend/.env
```

### 数据库连接失败
```bash
# 测试连接
source backend/.env
mysql -h"$DB_HOST" -u"$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -e "SELECT 1"
```

---

## 完整文档

详细部署指南：`docs/DEPLOYMENT.md`（507 行）

---

## 支持

- GitHub Issues
- 邮件：admin@your-domain.com
