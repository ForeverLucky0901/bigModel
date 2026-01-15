# 系统架构文档

## 总体架构

```
┌─────────────────────────────────────────────────────────────┐
│                        客户端层                              │
│  (OpenAI SDK / cURL / 其他HTTP客户端)                       │
└───────────────────────┬─────────────────────────────────────┘
                        │ HTTPS (443)
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                      Nginx 反向代理层                        │
│  - SSL终止 (Let's Encrypt)                                   │
│  - 请求路由                                                  │
│  - SSE流式支持 (proxy_buffering off)                         │
└───────────────────────┬─────────────────────────────────────┘
                        │ HTTP (8000)
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI 应用层                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 中间件栈                                              │  │
│  │  - IP限流 (Redis)                                      │  │
│  │  - API Key鉴权                                        │  │
│  │  - Key限流 (Redis)                                    │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ API路由                                               │  │
│  │  - /v1/chat/completions (兼容OpenAI)                  │  │
│  │  - /health (健康检查)                                  │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 业务逻辑层                                            │  │
│  │  - 配额检查 (PostgreSQL)                              │  │
│  │  - Key池选择 (权重轮询)                               │  │
│  │  - 上游请求转发 (httpx)                               │  │
│  │  - 用量统计 (PostgreSQL)                              │  │
│  │  - 审计日志 (PostgreSQL)                              │  │
│  └──────────────────────────────────────────────────────┘  │
└───────────┬───────────────────────────────┬─────────────────┘
            │                               │
            ▼                               ▼
┌──────────────────────┐      ┌──────────────────────────────┐
│   PostgreSQL         │      │        Redis                 │
│  - 用户管理          │      │  - 限流计数                 │
│  - API Key           │      │  - 缓存（可选）             │
│  - 上游Key（加密）    │      │  - 会话（可选）             │
│  - 用量统计          │      └──────────────────────────────┘
│  - 审计日志          │
└──────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────┐
│                    上游API服务                               │
│  ┌──────────────────┐          ┌──────────────────┐        │
│  │  OpenAI API      │          │ Azure OpenAI      │        │
│  │  - Chat          │          │  - Chat           │        │
│  │  - Completions   │          │  - Completions    │        │
│  └──────────────────┘          └──────────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

## 数据流

### 1. 请求处理流程

```
客户端请求
    │
    ▼
Nginx (SSL终止、路由)
    │
    ▼
FastAPI中间件
    ├─► IP限流检查 (Redis)
    ├─► API Key鉴权 (PostgreSQL)
    └─► Key限流检查 (Redis)
    │
    ▼
API路由处理
    ├─► 模型权限检查
    ├─► 配额检查 (PostgreSQL)
    ├─► Key池选择 (PostgreSQL)
    │   └─► 权重轮询 / 健康检查
    │
    ▼
上游请求转发
    ├─► 解密上游Key
    ├─► 创建上游客户端 (httpx)
    ├─► 发送请求 (OpenAI/Azure)
    └─► 处理响应 (流式/非流式)
    │
    ▼
响应处理
    ├─► 记录用量 (PostgreSQL)
    ├─► 更新Key池状态
    └─► 返回响应给客户端
```

### 2. 限流流程

```
请求到达
    │
    ▼
检查Redis中的限流计数
    ├─► key: rate_limit:key:{api_key}:rpm
    ├─► key: rate_limit:key:{api_key}:tpm
    ├─► key: rate_limit:ip:{client_ip}:rpm
    └─► key: rate_limit:ip:{client_ip}:tpm
    │
    ▼
判断是否超限
    ├─► 是 → 返回 429 Too Many Requests
    └─► 否 → 继续处理
    │
    ▼
更新计数 (INCR/INCRBY)
    └─► 设置过期时间 (60秒)
```

### 3. Key池管理流程

```
选择上游Key
    │
    ▼
查询健康Key (PostgreSQL)
    ├─► status = 'healthy'
    └─► status = 'cooldown' (检查是否到期)
    │
    ▼
权重轮询选择
    ├─► 计算总权重
    ├─► 随机选择（基于权重）
    └─► 返回选中的Key
    │
    ▼
请求上游API
    ├─► 成功 → 记录成功，重置失败计数
    └─► 失败 → 增加失败计数
         │
         ▼
    检查熔断条件
         ├─► failure_count >= threshold
         └─► 进入cooldown状态
              └─► 设置cooldown_until时间
```

## 数据库设计

### 核心表结构

#### users (用户表)
- `id`: 主键
- `username`: 用户名（唯一）
- `email`: 邮箱（唯一）
- `is_active`: 是否激活
- `is_admin`: 是否管理员
- `monthly_quota_tokens`: 月度Token配额
- `monthly_quota_amount`: 月度金额配额

#### api_keys (代理API Key表)
- `id`: 主键
- `key`: API Key（唯一索引）
- `user_id`: 用户ID（外键）
- `is_active`: 是否激活
- `allowed_models`: 允许的模型列表（JSON）
- `rate_limit_rpm`: 速率限制（RPM）
- `rate_limit_tpm`: Token限制（TPM）

#### upstream_keys (上游Key表)
- `id`: 主键
- `upstream_type`: 上游类型（openai/azure）
- `encrypted_key`: 加密的密钥
- `weight`: 权重
- `status`: 状态（healthy/cooldown/disabled）
- `failure_count`: 失败计数
- `cooldown_until`: 冷却到期时间

#### usage_records (请求记录表)
- `id`: 主键
- `user_id`: 用户ID
- `api_key_id`: API Key ID
- `upstream_key_id`: 上游Key ID
- `model`: 模型名称
- `prompt_tokens`: Prompt Token数
- `completion_tokens`: Completion Token数
- `total_tokens`: 总Token数
- `response_status`: 响应状态码
- `response_time_ms`: 响应时间（毫秒）
- `client_ip`: 客户端IP
- `request_body`: 请求体（可选，根据LOG_PROMPT_BODY）

#### usage_daily (每日用量聚合表)
- `id`: 主键
- `user_id`: 用户ID
- `date`: 日期（YYYY-MM-DD）
- `total_requests`: 总请求数
- `total_tokens`: 总Token数

#### usage_monthly (每月用量聚合表)
- `id`: 主键
- `user_id`: 用户ID
- `year`: 年份
- `month`: 月份
- `total_requests`: 总请求数
- `total_tokens`: 总Token数

## 关键技术点

### 1. SSE流式响应

**问题**：Nginx默认会缓冲响应，导致流式数据无法实时传输。

**解决方案**：
- Nginx配置：`proxy_buffering off;`
- FastAPI响应头：`X-Accel-Buffering: no`
- 超时设置：`proxy_read_timeout 300s`

### 2. 密钥加密

**方案**：使用 Fernet（对称加密）

**流程**：
1. 生成32字节密钥：`openssl rand -hex 32`
2. 存储到环境变量：`ENCRYPTION_KEY`
3. 加密上游Key：`encrypt_key(plain_key)`
4. 存储到数据库：`encrypted_key` 字段
5. 使用时解密：`decrypt_key(encrypted_key)`

### 3. 限流实现

**方案**：Redis + 滑动窗口

**实现**：
- 使用 `INCR` 和 `EXPIRE` 实现滑动窗口
- Key格式：`rate_limit:{type}:{identifier}:{window}`
- 过期时间：60秒（对应1分钟窗口）

### 4. 熔断机制

**策略**：
- 连续失败N次 → 进入cooldown状态
- Cooldown期间不选择该Key
- Cooldown到期后自动恢复
- 恢复后成功N次 → 重置失败计数

### 5. 配额检查

**时机**：请求处理前

**方法**：
1. 估算Token数（基于消息长度）
2. 查询当前月度用量
3. 检查：`current_usage + estimated_tokens <= quota`
4. 超限则拒绝请求

**注意**：实际Token数在响应后记录，可能存在估算误差。

## 性能优化

### 1. 数据库连接池
- `pool_size=10`: 基础连接数
- `max_overflow=20`: 最大溢出连接数
- `pool_pre_ping=True`: 连接前检查

### 2. Redis连接
- 单例模式，复用连接
- 连接超时：5秒
- 自动重连

### 3. Nginx配置
- `worker_processes auto`: 自动设置worker数
- `worker_connections 1024`: 每个worker最大连接数
- `keepalive_timeout 65`: Keep-alive超时

### 4. 异步处理
- FastAPI异步路由
- httpx异步客户端
- 流式响应使用异步生成器

## 安全考虑

### 1. 密钥安全
- 上游Key加密存储
- 加密密钥不存储在代码中
- 环境变量文件权限控制

### 2. 访问控制
- API Key鉴权
- 用户状态检查
- IP限流防护

### 3. 数据隐私
- 默认不记录完整prompt
- 日志脱敏（Authorization header）
- 敏感信息加密

### 4. 网络安全
- HTTPS强制
- 内部服务不暴露
- 防火墙规则

## 扩展性

### 水平扩展
- 无状态API服务，可多实例部署
- Redis共享状态（限流计数）
- PostgreSQL主从复制

### 垂直扩展
- 增加数据库连接池大小
- 增加Redis内存
- 增加Nginx worker数

### 功能扩展
- 支持更多上游服务（Claude、Gemini等）
- 添加管理后台
- 集成监控告警（Prometheus + Grafana）
- 添加Webhook通知
