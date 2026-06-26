# LabInherit Frontend

Vue 3 + Vite + TypeScript + Element Plus + Pinia + Vue Router.

## 本地开发

```bash
# 方式 1：pnpm（推荐）
pnpm install
pnpm dev

# 方式 2：npm
npm install
npm run dev
```

打开 http://localhost:5173

> 前端 dev server 通过 Vite proxy 把 `/api/*` 转发到后端 `http://localhost:8000`。
> 如果后端跑在别处，新建 `frontend/.env.local` 写入 `VITE_BACKEND_URL=http://your-host:8000`。

## 跑测试 / 类型检查

```bash
pnpm type-check
pnpm lint
pnpm format
pnpm build   # 包含类型检查
```

## 目录约定

```
src/
├── api/        axios 封装 + 业务 API（按后端模块分包）
├── stores/     Pinia 状态
├── router/     Vue Router
├── views/      页面级组件（按业务域分包）
├── components/ 可复用组件
├── utils/      工具函数
├── App.vue     根组件
├── main.ts     入口
└── style.css   全局样式
```

模块约定和后端一致：每个业务域一个子目录，方便后续拆包。