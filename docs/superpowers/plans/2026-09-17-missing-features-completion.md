# 缺失功能补全开发计划

> **日期：** 2026-09-17  
> **目标：** 补全 S4-S6 真正缺失的功能

---

## 问题诊断

经过检查，发现以下问题：

### ✅ 已完成（无需修改）
- Email worker 核心逻辑完整（`app.tasks.email_worker.py`）
- Email worker 已集成到 FastAPI lifespan（自动后台运行）
- 所有 API、前端、文档都已完成

### ❌ 缺失部分（需要补全）

1. **Email worker 独立运行入口**
   - 当前只能通过 FastAPI lifespan 运行
   - Systemd 服务需要独立的 `python -m app.tasks.email_worker` 入口
   - **需要添加 `__main__` 块**

2. **Email worker CLI 工具**（可选优化）
   - 添加命令行参数（`--interval`, `--batch-size`）
   - 添加优雅退出信号处理（SIGTERM, SIGINT）

---

## 开发计划

### 任务 1：添加 Email Worker 独立运行入口（必需）
**文件：** `backend/app/tasks/email_worker.py`

**需求：**
- 添加 `__main__` 块
- 支持 `python -m app.tasks.email_worker` 运行
- 支持信号处理（SIGTERM, SIGINT）优雅退出
- 添加启动日志

**预计时间：** 15 分钟

---

### 任务 2：添加 CLI 参数支持（可选优化）
**文件：** `backend/app/tasks/email_worker.py`

**需求：**
- 使用 `argparse` 添加命令行参数
- `--interval` 覆盖轮询间隔
- `--batch-size` 覆盖批量大小
- `--log-level` 设置日志级别

**预计时间：** 10 分钟

---

### 任务 3：测试验证
**测试项：**
1. ✓ 独立运行：`python -m app.tasks.email_worker`
2. ✓ 信号退出：Ctrl+C 优雅退出
3. ✓ Systemd 集成：`systemctl start labinherit-worker`
4. ✓ 邮件发送：创建评论 → 检查 email_outbox → 观察日志

**预计时间：** 10 分钟

---

## 总时间：35 分钟

---

## 执行顺序

1. **任务 1** - 添加独立运行入口（必需）
2. **任务 2** - 添加 CLI 参数（可选，建议做）
3. **任务 3** - 测试验证

---

## 验收标准

- [ ] 可以独立运行：`cd backend && python -m app.tasks.email_worker`
- [ ] 日志输出正常（显示启动信息、轮询日志）
- [ ] Ctrl+C 可以优雅退出（显示 "Email worker stopped."）
- [ ] Systemd 服务可以启动（`systemctl start labinherit-worker`）
- [ ] 创建评论后邮件自动发送（或进入队列）
- [ ] 失败重试机制正常（retry_count 递增）

---

## 风险

**无风险** - 只是添加入口函数，不修改核心逻辑。
