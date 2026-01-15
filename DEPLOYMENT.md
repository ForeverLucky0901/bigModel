# 部署指南

## 前置要求

- Ubuntu 22.04 或类似 Linux 系统
- Docker 和 Docker Compose 已安装
- 域名已解析到服务器IP
- 服务器开放 80 和 443 端口

## 步骤 1: 准备环境

### 1.1 安装 Docker 和 Docker Compose

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装 Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 验证安装
docker --version
docker-compose --version
```

### 1.2 克隆或上传项目

```bash
cd /opt
git clone <your-repo> gpt_proxy
cd gpt_proxy
```

## 步骤 2: 配置环境变量

### 2.1 创建 .env 文件

```bash
cp .env.example .env
nano .env
```

### 2.2 配置关键变量

**必须配置：**

```bash
# 数据库密码（强密码）
POSTGRES_PASSWORD=your_secure_password_here

# Redis密码（可选但推荐）
REDIS_PASSWORD=your_redis_password

# 加密密钥（32字节，生成命令：openssl rand -hex 32）
ENCRYPTION_KEY=your-32-byte-encryption-key-here

# 上游配置
UPSTREAM_TYPE=openai  # 或 azure
OPENAI_API_KEYS=sk-xxx1,sk-xxx2  # 多个用逗号分隔

# 或 Azure 配置
AZURE_ENDPOINT=https://your-resource.openai.azure.com
AZURE_API_KEYS=key1,key2
AZURE_DEPLOYMENT_NAMES=gpt-35-turbo,gpt-4
```

## 步骤 3: 初始化数据库

### 3.1 启动数据库服务

```bash
docker-compose up -d postgres redis
```

等待服务就绪（约30秒）

### 3.2 创建数据库表

```bash
docker-compose run --rm api python scripts/init_db.py
```

### 3.3 初始化上游密钥

```bash
docker-compose run --rm api python scripts/init_upstream_keys.py
```

### 3.4 创建管理员用户

```bash
docker-compose run --rm api python scripts/create_admin.py --username admin --email admin@example.com
```

**重要：保存输出的 API Key！**

## 步骤 4: 配置 HTTPS（Let's Encrypt）

### 4.1 安装 Certbot

```bash
sudo apt install certbot python3-certbot-nginx -y
```

### 4.2 临时启动 Nginx（HTTP）

```bash
# 修改 nginx/conf.d/default.conf，暂时注释掉 SSL 配置
docker-compose up -d nginx
```

### 4.3 获取证书

```bash
# 停止容器
docker-compose stop nginx

# 使用 certbot 获取证书（交互式）
sudo certbot certonly --standalone -d your-domain.com

# 证书位置：
# /etc/letsencrypt/live/your-domain.com/fullchain.pem
# /etc/letsencrypt/live/your-domain.com/privkey.pem
```

### 4.4 复制证书到项目目录

```bash
# 创建 SSL 目录
mkdir -p nginx/ssl

# 复制证书
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/

# 修改权限
sudo chown $USER:$USER nginx/ssl/*
chmod 600 nginx/ssl/*
```

### 4.5 配置自动续期

```bash
# 编辑 crontab
sudo crontab -e

# 添加（每月1号凌晨3点续期）
0 3 1 * * certbot renew --quiet && docker-compose restart nginx
```

## 步骤 5: 启动所有服务

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f api

# 查看服务状态
docker-compose ps
```

## 步骤 6: 验证部署

### 6.1 健康检查

```bash
curl https://your-domain.com/health
```

预期输出：
```json
{
  "status": "healthy",
  "services": {
    "database": "healthy",
    "redis": "healthy"
  }
}
```

### 6.2 测试非流式请求

```bash
curl https://your-domain.com/v1/chat/completions \
  -H "Authorization: Bearer YOUR_PROXY_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [
      {"role": "user", "content": "Hello, world!"}
    ],
    "stream": false
  }'
```

### 6.3 测试流式请求（SSE）

```bash
curl -N https://your-domain.com/v1/chat/completions \
  -H "Authorization: Bearer YOUR_PROXY_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [
      {"role": "user", "content": "Tell me a short story"}
    ],
    "stream": true
  }'
```

## 常见问题排查

### SSE 流式响应不工作

**症状：** 流式请求返回完整响应而不是流式数据

**解决方案：**

1. 检查 Nginx 配置：
   ```nginx
   proxy_buffering off;
   proxy_cache off;
   ```

2. 检查 FastAPI 响应头：
   ```python
   headers={"X-Accel-Buffering": "no"}
   ```

3. 检查 Nginx 超时设置：
   ```nginx
   proxy_read_timeout 300s;
   ```

### 限流不生效

**症状：** 超过限制的请求仍然通过

**检查：**

1. Redis 连接：
   ```bash
   docker-compose exec redis redis-cli ping
   ```

2. 查看 Redis 中的限流 key：
   ```bash
   docker-compose exec redis redis-cli KEYS "rate_limit:*"
   ```

### 上游请求失败

**症状：** 所有请求返回 503 或错误

**检查：**

1. 上游 Key 状态：
   ```bash
   docker-compose exec api python -c "
   from app.models.base import SessionLocal
   from app.models.upstream import UpstreamKey
   db = SessionLocal()
   keys = db.query(UpstreamKey).all()
   for k in keys:
       print(f'Key {k.id}: {k.status}, failures: {k.failure_count}')
   "
   ```

2. 检查上游 API 可用性：
   ```bash
   curl https://api.openai.com/v1/models \
     -H "Authorization: Bearer YOUR_OPENAI_KEY"
   ```

### 数据库连接失败

**症状：** 服务启动失败，日志显示数据库连接错误

**检查：**

1. 数据库服务状态：
   ```bash
   docker-compose ps postgres
   ```

2. 数据库连接：
   ```bash
   docker-compose exec postgres psql -U gpt_proxy -d gpt_proxy -c "SELECT 1;"
   ```

3. 环境变量：
   ```bash
   docker-compose exec api env | grep POSTGRES
   ```

## 维护操作

### 查看日志

```bash
# 所有服务
docker-compose logs -f

# 特定服务
docker-compose logs -f api
docker-compose logs -f nginx
```

### 备份数据库

```bash
# 创建备份
docker-compose exec postgres pg_dump -U gpt_proxy gpt_proxy > backup_$(date +%Y%m%d).sql

# 恢复备份
docker-compose exec -T postgres psql -U gpt_proxy gpt_proxy < backup_20240101.sql
```

### 更新服务

```bash
# 拉取最新代码
git pull

# 重建镜像
docker-compose build

# 重启服务
docker-compose up -d
```

### 添加新的上游 Key

```bash
# 方法1: 通过环境变量（重启服务）
# 编辑 .env，添加新 key 到 OPENAI_API_KEYS
docker-compose restart api
docker-compose run --rm api python scripts/init_upstream_keys.py

# 方法2: 直接操作数据库（需要解密工具）
```

## 安全检查清单

部署前请确认：

- [ ] 所有环境变量已正确配置
- [ ] `ENCRYPTION_KEY` 已生成并保密（32字节）
- [ ] 数据库密码足够强
- [ ] Redis 密码已设置（生产环境）
- [ ] HTTPS 证书已配置
- [ ] 防火墙规则已设置（只开放 80/443）
- [ ] 上游 API Key 已加密存储
- [ ] 日志不包含敏感信息（`LOG_PROMPT_BODY=false`）
- [ ] 限流规则已启用
- [ ] 数据库备份已配置
- [ ] 监控告警已设置

## 性能优化建议

1. **数据库连接池**：已在配置中设置（pool_size=10）
2. **Redis 连接池**：使用单例模式
3. **Nginx 缓存**：对静态资源启用缓存
4. **日志轮转**：配置 logrotate
5. **监控**：集成 Prometheus + Grafana

## 下一步

- 配置监控和告警
- 设置数据库自动备份
- 配置日志聚合（ELK Stack）
- 实现管理后台（可选）
