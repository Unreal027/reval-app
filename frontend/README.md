# ReVal 前端（React + Vite + TypeScript）

最小可用页面骨架，覆盖登录、案例管理/导入/检索、发起估价（比较法/收益法/成本法）、任务查看与报告生成/下载。

## 本地开发

```bash
cd frontend
npm install
npm run dev
```

- 开发服务器默认 `http://localhost:5173`，`/api` 由 Vite 代理到 `http://localhost:8000`（见 `vite.config.ts`），需先启动后端。
- 生产构建：`npm run build`（产物在 `dist/`）。

## Docker

`docker-compose.yml` 中包含 `frontend` 服务（多阶段构建：Node 构建 + Nginx 托管静态文件），Caddy 将 `/api/*` 反代到后端，其余请求转发到前端。

## 页面说明

- `/login`：手机号/密码登录
- `/`：概览与管理员初始化默认比较法系数入口
- `/comparables`：案例新增/编辑/删除（按角色权限）、Excel 导入（.xlsx）、半径检索、关键词/区域筛选与分页列表
- `/valuations`：创建估价任务（comparison/income/cost）、查看任务与修正明细、生成并下载 Docx 报告
