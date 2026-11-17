# 甲骨文云 A1 部署与运维指南

适用于本项目骨架（FastAPI + PostgreSQL/PostGIS + Caddy, Docker Compose）。

## 1. 实例与网络准备

1. **实例规格**：A1 Flexible，建议 2 OCPU / 12GB 内存，Ubuntu 22.04/24.04 ARM64，启动盘 ≥ 50GB。
2. **网络安全**（VCN 安全列表 / NSG）：
   - 入站：TCP 22（SSH，仅限你的 IP）、TCP 80、TCP 443；ICMP 按需放行（便于 ping 排障）。
   - 出站：全部放行（拉镜像、申请证书、时间同步等）。
3. **域名**：将域名 A 记录指向实例公网 IP。Caddy 自动申请 Let’s Encrypt 证书依赖 80/443 可达与正确域名解析。
4. **系统初始化**（示例）：
   ```bash
   sudo apt update && sudo apt upgrade -y
   sudo apt install -y docker.io docker-compose-v2 stress-ng fail2ban ufw curl git
   sudo systemctl enable --now docker
   sudo usermod -aG docker $USER
   ```

## 2. 应用部署

1. 上传项目到服务器，例如 `/opt/reval-app`：
   ```bash
   sudo mkdir -p /opt/reval-app
   # 将本仓库 reval-app/ 内容拷贝到 /opt/reval-app
   cd /opt/reval-app
   ```
2. 配置环境变量：
   ```bash
   cp .env.example .env
   # 编辑 .env：修改 POSTGRES_PASSWORD、JWT_SECRET、FIRST_ADMIN_* 等强密码
   ```
3. 配置域名：在 `.env` 中设置 `DOMAIN=你的域名`（Caddyfile 使用 `{$DOMAIN:localhost}` 自动读取；本地/无域名联调可用 `localhost` 或 `:80` 场景按需调整）。 Caddy 会将 `/api/*` 反代到后端，其余请求转发到前端静态站点。
4. 启动与迁移：
   ```bash
   docker compose up -d --build
   docker compose exec backend alembic upgrade head
   docker compose ps
   docker compose logs -f backend
   ```
5. 验证：
   - `https://你的域名/api/health` 应返回 `{"status":"ok","db":true,...}`
   - `https://你的域名/api/docs` 可打开 Swagger
   - 使用 `.env` 中 `FIRST_ADMIN_PHONE` / `FIRST_ADMIN_PASSWORD` 登录 `/api/auth/login`

## 3. 防回收与可用性

Oracle 文档：7 天滑动窗口内 **CPU 95 百分位 < 20% 且网络利用率 < 20% 且内存利用率 < 20%**（A1 含内存）才可能回收。

- **CPU（建议启用）**：部署 [backend/scripts/keepalive](backend/scripts/keepalive) 为 cron：
  ```bash
  sudo cp backend/scripts/keepalive /etc/cron.d/keepalive
  sudo chmod 644 /etc/cron.d/keepalive
  ```
  该任务每小时 0/30 分各跑 3 分钟单核 35% 负载，足以打破 95 分位阈值，开销很低。
- **内存**：`docker-compose.yml` 已为 PostgreSQL 配置 `shared_buffers=512MB` 等参数；2 OCPU/12GB 实例上数据库+后端常驻一般可稳定超过 20% 内存利用率。
- **网络/监控**：使用 UptimeRobot 等免费监控每 5 分钟请求一次 `https://你的域名/api/health`，同时获得宕机告警。

## 4. 备份与恢复

- **每日备份**：[backend/scripts/backup_db.sh](backend/scripts/backup_db.sh)
  ```bash
  sudo mkdir -p /opt/reval-backups
  sudo chmod +x /opt/reval-app/backend/scripts/backup_db.sh
  # crontab 示例（root）：
  # 10 3 * * * BACKUP_DIR=/opt/reval-backups /opt/reval-app/backend/scripts/backup_db.sh >> /var/log/reval_backup.log 2>&1
  ```
- **恢复**：
  ```bash
  gunzip -c /opt/reval-backups/reval_YYYYMMDD_HHMMSS.sql.gz | \
    docker compose exec -T db psql -U reval -d reval
  ```
- **建议**：每周将一份备份复制到对象存储（OCI Object Storage 免费额度）或其他异地位置，防实例回收/磁盘故障。

## 5. 更新与回滚

```bash
cd /opt/reval-app
git pull  # 或重新上传
docker compose up -d --build
docker compose exec backend alembic upgrade head
```
回滚前先确认数据库迁移可逆性；生产环境建议在升级前做一次 `pg_dump`。

## 6. 常见排查

- `docker compose ps` / `docker compose logs -f backend db caddy`
- 健康检查：`curl -s http://127.0.0.1:8000/api/health`（容器内）或公网域名
- 证书签发失败：确认 80/443 放行、域名解析正确、Caddyfile 域名无误
- PostGIS/空间查询异常：`docker compose exec db psql -U reval -d reval -c "SELECT PostGIS_Version();"`
- 内存紧张：调低 PostgreSQL `shared_buffers` 或 `max_connections`，观察 `docker stats`