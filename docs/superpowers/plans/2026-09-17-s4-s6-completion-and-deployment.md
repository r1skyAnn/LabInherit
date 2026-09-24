# S4-S6 完成与生产部署计划

> **日期：** 2026-09-17
> **目标：** 完成 S4（邮件 worker）、S5（前端看板）、S6（打磨）并部署到生产服务器

---

## 当前状态评估

### ✅ 已完成（S0-S3 + 部分 S4/S5）
- 基础设施、账号权限、项目分类、笔记核心
- 评论模型、通知系统、email_outbox 表结构
- 后端管理 API（dashboard KPI、stale projects、hot notes）

### ❌ 待完成
- **S4 核心**：真正的邮件发送 worker + 重试机制
- **S5 核心**：前端管理看板 UI
- **S6 核心**：部署脚本、环境配置、生产验证

---

## 执行计划（3 阶段，预计 2-3 小时）

### 阶段 1：S4 邮件 Worker 实现（45 分钟）

#### 1.1 实现邮件发送 worker
**文件：** `backend/app/tasks/email_worker.py`

实现内容：
- 异步循环，每 5 秒查询 `email_outbox` WHERE status='queued' AND next_attempt_at <= NOW()
- 使用 `SELECT ... FOR UPDATE SKIP LOCKED` 防止多实例竞争
- 调用 `app.core.email.send_email()` 实际发送
- 成功 → status='sent'
- 失败 → retry_count++, next_attempt_at = NOW() + 2^retry_count 分钟
- 最多 5 次重试，超限 → status='failed'
- 日志记录所有发送尝试

#### 1.2 完善邮件发送核心
**文件：** `backend/app/core/email.py`

确保内容：
- 使用 `aiosmtplib` 发送邮件
- 支持 TLS/STARTTLS
- 开发环境 SMTP 未配置时走 stdout mock
- 异常处理和错误信息捕获

#### 1.3 更新 email_outbox 模型
**文件：** `backend/app/modules/notifications/models.py`

确保字段：
- `next_attempt_at` (datetime, indexed)
- `retry_count` (int, default=0)
- `last_error` (text, nullable)
- `sent_at` (datetime, nullable)

#### 1.4 测试
```bash
cd backend
# 创建测试评论，检查 email_outbox 是否写入
# 运行 worker，观察日志
python -m app.tasks.email_worker
```

---

### 阶段 2：S5 前端管理看板（60 分钟）

#### 2.1 创建管理看板主页面
**文件：** `frontend/src/views/AdminDashboard.vue`

包含组件：
- KPI 卡片网格：用户统计、待审核数、开放追问数、断代项目数、失败邮件数
- 断代项目列表（表格，带最后活跃时间）
- 热门笔记 Top 10（点赞 + 评论数排序）
- 失败邮件列表（红色 badge，显示错误原因）
- 未回答追问列表（显示天数）

#### 2.2 身份状态管理组件
**文件：** `frontend/src/components/admin/UserStatusManager.vue`

功能：
- 用户列表（带状态 badge：active/graduated/archived）
- 状态转换按钮（active → graduated → archived）
- 角色变更（member ↔ admin，owner 不可改）
- 确认弹窗

#### 2.3 路由注册
**文件：** `frontend/src/router/index.ts`

添加路由：
```typescript
{
  path: '/admin/dashboard',
  name: 'AdminDashboard',
  component: () => import('@/views/AdminDashboard.vue'),
  meta: { requiresAuth: true, requiresRole: ['admin', 'owner'] }
}
```

#### 2.4 导航菜单更新
**文件：** `frontend/src/layouts/DefaultLayout.vue`

为 admin/owner 添加「管理看板」菜单项。

---

### 阶段 3：S6 打磨与生产部署（45 分钟）

#### 3.1 生产环境配置
**文件：** `backend/.env.production.example`

关键配置：
- `APP_ENV=production`
- `APP_DEBUG=false`
- `DB_HOST=<生产数据库地址>`
- `DB_PASSWORD=<强密码>`
- `JWT_SECRET=<32位随机字符串>`
- `SMTP_HOST/USER/PASSWORD`（真实 SMTP）
- `APP_BASE_URL=<生产域名>`
- `APP_CORS_ORIGINS=<生产域名>`

#### 3.2 部署脚本
**文件：** `deploy/deploy.sh`

脚本内容：
```bash
#!/bin/bash
# 1. 拉取最新代码
# 2. 检查 .env 配置
# 3. 安装依赖
# 4. 运行数据库迁移
# 5. 构建前端
# 6. 重启服务（systemd/supervisor）
```

#### 3.3 Systemd 服务文件
**文件：** `deploy/labinherit-backend.service`
**文件：** `deploy/labinherit-worker.service`

#### 3.4 Nginx 配置
**文件：** `deploy/nginx/labinherit.conf`

配置内容：
- 前端静态文件 serve
- /api 反向代理到后端
- /docs、/redoc 代理
- Gzip 压缩
- 请求大小限制（上传文件）

#### 3.5 数据库备份脚本
**文件：** `deploy/backup-db.sh`

```bash
#!/bin/bash
mysqldump -h $DB_HOST -u $DB_USER -p$DB_PASSWORD $DB_NAME > backup_$(date +%Y%m%d_%H%M%S).sql
```

#### 3.6 健康检查脚本
**文件：** `deploy/healthcheck.sh`

检查项：
- 后端 /health 返回 200
- Worker 进程运行中
- 数据库连接正常
- 磁盘空间充足

#### 3.7 部署文档
**文件：** `docs/DEPLOYMENT.md`

包含章节：
- 服务器要求（Ubuntu 22.04+、Python 3.12+、Node.js 20+、MySQL 8.0+、Nginx）
- 一键部署步骤
- 环境变量配置说明
- 常见问题排查
- 备份与恢复
- 监控建议

---

## 验收标准（Acceptance Criteria）

### S4 验收
- [ ] 创建评论后，email_outbox 表有记录且 status='queued'
- [ ] Worker 启动后自动拉取 queued 邮件并发送
- [ ] SMTP 配置正确时，收件人实际收到邮件
- [ ] 发送失败时，retry_count 递增，next_attempt_at 延后
- [ ] 5 次重试失败后，status 变为 'failed'

### S5 验收
- [ ] Admin 角色登录后能看到管理看板菜单
- [ ] 看板显示 KPI 数据（用户统计、断代项目、热门笔记）
- [ ] 断代项目列表显示超过 90 天无活动的项目
- [ ] 失败邮件列表显示 status='failed' 的邮件及错误原因
- [ ] 用户状态管理页面能切换 active/graduated/archived

### S6 验收
- [ ] 在生产服务器上成功运行 deploy.sh
- [ ] 前端通过 Nginx 访问正常（静态资源加载）
- [ ] 后端 API 通过 /api 路径访问正常
- [ ] 数据库迁移在生产环境执行成功
- [ ] Worker 进程通过 systemd 管理并自动重启
- [ ] 健康检查脚本返回正常状态
- [ ] 登录 → 创建项目 → 写笔记 → 评论 → 追问完整流程测试通过

---

## 风险与应对

| 风险 | 应对措施 |
|------|---------|
| SMTP 配置错误导致邮件发不出 | 开发环境先用 stdout mock，生产环境用 QQ/163 邮箱测试 |
| 生产数据库迁移失败 | 先在测试环境验证迁移脚本，部署前备份数据库 |
| Worker 进程意外退出 | systemd 配置 Restart=always，监控日志 |
| 前端打包后路径问题 | vite.config.ts 配置正确的 base，测试 nginx 路由 |
| 生产环境依赖安装失败 | 使用 requirements.txt 固定版本，Docker 构建验证 |

---

## 时间线

| 时间 | 阶段 | 里程碑 |
|------|------|--------|
| T+0min | 开始 | 阅读计划，环境检查 |
| T+45min | S4 完成 | Worker 正常发送邮件 |
| T+105min | S5 完成 | 管理看板 UI 完整 |
| T+150min | S6 完成 | 生产部署脚本就绪 |
| T+180min | 验收 | 生产环境完整测试通过 |

---

## 执行顺序

1. **先完成 S4 worker** — 独立可测，不依赖前端
2. **再完成 S5 看板** — 依赖 S4 邮件数据，前端最后验证
3. **最后 S6 部署** — 需要完整功能后才能部署验证

---

## 完工标志

- 所有验收标准 ✅
- 生产服务器上运行稳定 24 小时无崩溃
- README 更新部署文档链接
- Git 打 tag `v1.0.0`
