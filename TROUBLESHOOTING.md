# 故障排查指南

## 常见问题与解决方案

### 1. SSE 流式响应问题

#### 问题：流式请求返回完整响应而不是流式数据

**原因：**
- Nginx 缓冲未关闭
- FastAPI 响应头配置错误
- 超时设置过短

**解决方案：**

1. **检查 Nginx 配置** (`nginx/conf.d/default.conf`)：
   ```nginx
   proxy_buffering off;
   proxy_cache off;
   proxy_request_buffering off;
   ```

2. **检查 FastAPI 响应头** (`app/api/chat.py`)：
   ```python
   headers={
       "Cache-Control": "no-cache",
       "Connection": "keep-alive",
       "X-Accel-Buffering": "no"
   }
   ```

3. **增加超时时间**：
   ```nginx
   proxy_read_timeout 300s;
   proxy_send_timeout 300s;
   ```

4. **测试流式响应**：
   ```bash
   curl -N https://your-domain.com/v1/chat/completions \
     -H "Authorization: Bearer YOUR_KEY" \
     -H "Content-Type: application/json" \
     -d '{"model":"gpt-3.5-turbo","messages":[{"role":"user","content":"test"}],"stream":true}'
   ```

### 2. 限流不生效

#### 问题：超过限制的请求仍然通过

**检查步骤：**

1. **验证 Redis 连接**：
   ```bash
   docker-compose exec redis redis-cli ping
   # 应该返回 PONG
   ```

2. **查看限流 key**：
   ```bash
   docker-compose exec redis redis-cli KEYS "rate_limit:*"
   ```

3. **手动测试限流**：
   ```bash
   # 快速发送多个请求
   for i in {1..100}; do
     curl -s https://your-domain.com/v1/chat/completions \
       -H "Authorization: Bearer YOUR_KEY" \
       -H "Content-Type: application/json" \
       -d '{"model":"gpt-3.5-turbo","messages":[{"role":"user","content":"test"}]}'
   done
   ```

4. **检查环境变量**：
   ```bash
   docker-compose exec api env | grep RATE_LIMIT
   ```

**可能原因：**
- Redis 连接失败（fail-open 策略允许通过）
- 限流中间件未正确执行
- 环境变量未正确加载

### 3. 上游请求失败

#### 问题：所有请求返回 503 或上游错误

**检查步骤：**

1. **查看上游 Key 状态**：
   ```python
   docker-compose exec api python -c "
   from app.models.base import SessionLocal
   from app.models.upstream import UpstreamKey
   db = SessionLocal()
   keys = db.query(UpstreamKey).all()
   for k in keys:
       print(f'Key {k.id}: status={k.status}, failures={k.failure_count}, errors={k.total_errors}')
   "
   ```

2. **检查上游 API 可用性**：
   ```bash
   # OpenAI
   curl https://api.openai.com/v1/models \
     -H "Authorization: Bearer YOUR_OPENAI_KEY"
   
   # Azure
   curl "https://your-resource.openai.azure.com/openai/deployments/gpt-35-turbo?api-version=2023-12-01-preview" \
     -H "api-key: YOUR_AZURE_KEY"
   ```

3. **查看错误日志**：
   ```bash
   docker-compose logs api | grep -i error
   ```

4. **重置熔断状态**：
   ```python
   # 手动重置（需要数据库访问）
   UPDATE upstream_keys SET status='healthy', failure_count=0, cooldown_until=NULL WHERE id=1;
   ```

**可能原因：**
- 上游 Key 已失效或额度用完
- 上游 API 服务不可用
- 网络连接问题
- 熔断机制触发

### 4. 数据库连接失败

#### 问题：服务启动失败，日志显示数据库连接错误

**检查步骤：**

1. **验证数据库服务**：
   ```bash
   docker-compose ps postgres
   docker-compose logs postgres
   ```

2. **测试数据库连接**：
   ```bash
   docker-compose exec postgres psql -U gpt_proxy -d gpt_proxy -c "SELECT 1;"
   ```

3. **检查环境变量**：
   ```bash
   docker-compose exec api env | grep POSTGRES
   ```

4. **检查数据库 URL**：
   ```python
   docker-compose exec api python -c "
   from app.config import settings
   print(settings.DATABASE_URL)
   "
   ```

**解决方案：**

1. **重启数据库**：
   ```bash
   docker-compose restart postgres
   ```

2. **检查数据库日志**：
   ```bash
   docker-compose logs postgres | tail -50
   ```

3. **验证数据库密码**：
   ```bash
   # 临时进入容器测试
   docker-compose exec postgres psql -U gpt_proxy -d gpt_proxy
   ```

### 5. 加密密钥问题

#### 问题：无法解密上游 Key

**错误信息：**
```
Failed to decrypt key: Invalid token
```

**原因：**
- `ENCRYPTION_KEY` 与加密时使用的密钥不一致
- 密钥格式错误（必须是32字节）

**解决方案：**

1. **生成新密钥**：
   ```bash
   openssl rand -hex 32
   ```

2. **更新环境变量**：
   ```bash
   # 编辑 .env
   ENCRYPTION_KEY=your-new-key-here
   ```

3. **重新加密所有上游 Key**：
   ```bash
   # 需要重新初始化上游密钥
   docker-compose run --rm api python scripts/init_upstream_keys.py
   ```

**注意：** 更改加密密钥会导致已加密的数据无法解密！

### 6. 配额检查失败

#### 问题：用户配额充足但请求被拒绝

**检查步骤：**

1. **查看用户配额**：
   ```python
   docker-compose exec api python -c "
   from app.models.base import SessionLocal
   from app.models.user import User
   from app.services.usage_tracker import UsageTracker
   db = SessionLocal()
   user = db.query(User).filter(User.username=='test').first()
   if user:
       print(f'Quota: {user.monthly_quota_tokens}')
       from datetime import datetime
       monthly = UsageTracker.get_monthly_usage(db, user.id, datetime.now().year, datetime.now().month)
       if monthly:
           print(f'Used: {monthly.total_tokens}')
   "
   ```

2. **检查配额逻辑**：
   - 配额检查在请求处理前进行
   - 使用估算的 token 数（可能不准确）
   - 实际用量在响应后记录

**解决方案：**

1. **增加配额**：
   ```sql
   UPDATE users SET monthly_quota_tokens=10000000 WHERE username='test';
   ```

2. **重置月度用量**：
   ```sql
   DELETE FROM usage_monthly WHERE user_id=1 AND year=2024 AND month=1;
   ```

### 7. Nginx 502 Bad Gateway

#### 问题：Nginx 返回 502 错误

**原因：**
- API 服务未启动
- API 服务崩溃
- 网络连接问题

**检查步骤：**

1. **查看 API 服务状态**：
   ```bash
   docker-compose ps api
   docker-compose logs api | tail -50
   ```

2. **测试 API 服务直接访问**：
   ```bash
   curl http://localhost:8000/health
   ```

3. **检查 Nginx 配置**：
   ```bash
   docker-compose exec nginx nginx -t
   ```

**解决方案：**

1. **重启 API 服务**：
   ```bash
   docker-compose restart api
   ```

2. **查看详细错误**：
   ```bash
   docker-compose logs -f api
   ```

### 8. HTTPS 证书问题

#### 问题：SSL 证书错误或过期

**检查步骤：**

1. **查看证书有效期**：
   ```bash
   openssl x509 -in nginx/ssl/fullchain.pem -noout -dates
   ```

2. **测试证书**：
   ```bash
   openssl s_client -connect your-domain.com:443 -servername your-domain.com
   ```

**解决方案：**

1. **续期证书**：
   ```bash
   sudo certbot renew
   ```

2. **复制新证书**：
   ```bash
   sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/
   sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/
   docker-compose restart nginx
   ```

### 9. 性能问题

#### 问题：响应慢或超时

**优化建议：**

1. **数据库连接池**：
   - 已在配置中设置 `pool_size=10`
   - 可根据负载调整

2. **Redis 连接**：
   - 使用连接池
   - 检查 Redis 性能：`docker-compose exec redis redis-cli --latency`

3. **Nginx 缓存**：
   - 对静态资源启用缓存
   - 禁用 API 路径缓存

4. **日志级别**：
   - 生产环境使用 `LOG_LEVEL=WARNING`
   - 减少日志 I/O

5. **监控资源使用**：
   ```bash
   docker stats
   ```

## 调试技巧

### 查看实时日志

```bash
# 所有服务
docker-compose logs -f

# 特定服务
docker-compose logs -f api
docker-compose logs -f nginx
```

### 进入容器调试

```bash
# API 容器
docker-compose exec api bash

# 数据库容器
docker-compose exec postgres psql -U gpt_proxy -d gpt_proxy

# Redis 容器
docker-compose exec redis redis-cli
```

### 测试 API

```bash
# 健康检查
curl https://your-domain.com/health

# 非流式请求
curl -v https://your-domain.com/v1/chat/completions \
  -H "Authorization: Bearer YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-3.5-turbo","messages":[{"role":"user","content":"test"}]}'

# 流式请求
curl -N -v https://your-domain.com/v1/chat/completions \
  -H "Authorization: Bearer YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-3.5-turbo","messages":[{"role":"user","content":"test"}],"stream":true}'
```

## 获取帮助

如果问题仍未解决：

1. 查看完整日志：`docker-compose logs > debug.log`
2. 检查系统资源：`docker stats`
3. 验证配置：`docker-compose config`
4. 检查网络：`docker network ls`
