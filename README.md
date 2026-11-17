# reval-app 房地产估价系统

FastAPI + PostgreSQL(PostGIS) + React,部署于甲骨文云 A1(ARM)免费实例。

## 本地开发 / 快速启动

```bash
cp .env.example .env       # 修改密码与密钥，设置 DOMAIN（本地可用 localhost）
docker compose up -d --build
docker compose exec backend alembic upgrade head
```

- Web 前端: http://localhost （或 https://your-domain）
- 健康检查: http://localhost/api/health
- 后端 API 文档: http://localhost/api/docs
- 初始管理员账号由 `.env` 中 `FIRST_ADMIN_PHONE` / `FIRST_ADMIN_PASSWORD` 决定（首次迁移自动创建）

前端单独开发见 [frontend/README.md](frontend/README.md)（Vite dev server 代理 `/api` 到本地后端）。

## 已实现骨架能力

- **认证与用户**：`/api/auth/login`、`/api/auth/refresh`、`/api/auth/me`，用户列表/启停（管理员）
- **可比案例**：CRUD + 关键词/区域筛选 + PostGIS 半径检索（`POST /api/comparables/nearby`）+ Excel 批量导入（`POST /api/comparables/import`，`.xlsx`，必需列：`community,lng,lat,area,deal_price,deal_date`）
- **修正系数配置**：`/api/factors` CRUD（管理员写、登录可读），`POST /api/factors/seed-defaults` 一键写入比较法默认系数（`area/floor/build_year/distance`）
- **估价任务/引擎**：`POST /api/valuations` 创建并计算，`GET /api/valuations`、`GET /api/valuations/{id}` 查询（含修正明细与 `_calc_meta`）
  - `comparison`：按半径选取可比案例，使用 `factor_configs`（type=`comparison`）驱动面积/楼层/建成年代修正与距离权重
  - `income`：需在 `subject_info` 提供 `monthly_rent`、`cap_rate`(或 `yield_rate`)，可选 `vacancy_rate`/`annual_cost_rate`
  - `cost`：需在 `subject_info` 提供 `land_unit_price`、`replacement_unit_cost`、`depreciation_rate` 等参数；参数不足时状态为 `insufficient_params`
- **估价报告（M4 骨架）**：`POST /api/reports/generate`（按 `task_id` 生成 docx）、`GET /api/reports`、`GET /api/reports/{id}`、`GET /api/reports/{id}/download`；报告包含估价对象信息、结果、计算参数/元信息、比较法修正明细（如适用）与免责声明，文件落盘于 `REPORTS_DIR`（compose 默认挂载 `reports_data` 到 `/app/reports`）
- **运维**：PostgreSQL 内存参数已在 compose 中做 12GB 实例适配；防回收 cron、备份脚本、systemd 示例见 `backend/scripts/`。详细部署见 [DEPLOY_ORACLE_A1.md](DEPLOY_ORACLE_A1.md)。

> 数据库迁移：新增报告表迁移 `0003_reports`，部署/升级后执行 `docker compose exec backend alembic upgrade head`。

## 结构

```
reval-app/
├── docker-compose.yml
├── .env.example
├── DEPLOY_ORACLE_A1.md      # A1 部署、防回收、备份恢复指南
├── caddy/Caddyfile          # /api -> backend, 其余 -> frontend
├── backend/                 # FastAPI 应用
│   ├── app/
│   │   ├── api/             # auth/users/comparables/valuations/factors/reports 路由
│   │   ├── core/            # 配置、安全、数据库、依赖
│   │   ├── models/          # SQLAlchemy 模型
│   │   ├── schemas/         # Pydantic schema
│   │   └── services/        # 估价计算、报告生成等业务逻辑
│   ├── alembic/             # 数据库迁移(含 0003_reports)
│   ├── scripts/             # keepalive/backup/systemd
│   └── Dockerfile
└── frontend/                # React + Vite + TypeScript 最小可用页面
    ├── src/                 # 登录/概览/案例管理/估价与报告页面
    ├── Dockerfile           # 多阶段构建 + Nginx
    └── nginx.conf
```

## 常用命令

```bash
docker compose exec backend alembic upgrade head    # 迁移
docker compose exec db pg_dump -U reval reval > backup.sql  # 备份
docker compose logs -f backend                      # 日志
docker compose ps                                   # 状态
```

详见 [DEPLOY_ORACLE_A1.md](DEPLOY_ORACLE_A1.md)。
