# DocMind Frontend

React 18 + Vite 前端，对接 DocMind FastAPI 后端。

## 前提条件

- Node.js 18+
- 后端服务运行在 `http://localhost:8000`（先启动后端再启动前端）

## 启动开发服务器

```bash
cd frontend
npm install
npm run dev
# 访问 http://localhost:5173
```

## 环境变量

`.env.development` 中 `VITE_API_BASE_URL` 默认为空，通过 Vite proxy 将 `/api/*` 转发到
`http://localhost:8000`，无需修改即可开发。

## 构建生产包

```bash
npm run build
# 产物在 frontend/dist/，可由 nginx / FastAPI StaticFiles 托管
```

## 技术说明

| 项目 | 实现 |
|------|------|
| SSE 流式读取 | `fetch + ReadableStream.getReader()` 手动解析，而非 EventSource（后者不支持 POST）|
| 全局状态 | `React Context + useReducer`，无第三方状态库 |
| 历史会话 | `localStorage` 持久化，刷新后保持 |
| API 代理 | Vite devServer.proxy `/api` → `http://localhost:8000` |
| 样式 | 手写 CSS，无 UI 组件库 |
