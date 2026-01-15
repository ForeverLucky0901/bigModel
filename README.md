# OpenAI 风格接口 GPT 中转服务

## 架构概览

```
┌─────────────┐
│   Client    │ (使用 OpenAI SDK，只改 base_url)
└──────┬──────┘
       │ HTTPS (443)
       ▼
┌─────────────────┐
│   Nginx (443)   │ (反向代理 + SSL终止)
└──────┬──────────┘
       │ HTTP (8000)
       ▼
┌─────────────────┐
│  FastAPI (8000) │ (鉴权、限流、路由)
└──────┬──────────┘
       │
       ├─► Redis (限流计数、缓存)
       ├─► PostgreSQL (用户、密钥、用量、审计)
       │
       ▼
┌─────────────────┐
│  Upstream Pool   │ (Key池管理、熔断、轮询)
└──────┬──────────┘
       │
       ├─► OpenAI API
       └─► Azure OpenAI
```

## 核心功能

1. **接口兼容**: `/v1/chat/completions` 完全兼容 OpenAI 格式
2. **鉴权系统**: 基于 Proxy API Key 的多用户体系
3. **限流保护**: IP + Key 双重限流（RPM/TPM）
4. **配额管理**: 月度额度、实时扣减、用量统计
5. **Key池管理**: 多上游Key轮询、权重、熔断恢复
6. **审计日志**: 请求记录、用量统计、隐私保护
7. **一键部署**: Docker Compose + Nginx + Let's Encrypt

## 快速开始

### 1. 准备环境变量

```bash
cp .env.example .env
# 编辑 .env 填入你的配置
```

### 2. 启动服务

```bash
docker-compose up -d
```

### 3. 初始化数据库

```bash
docker-compose exec api python scripts/init_db.py
```

### 4. 验证服务

```bash
# 健康检查
curl https://your-domain.com/health

# 测试API
curl https://your-domain.com/v1/chat/completions \
  -H "Authorization: Bearer YOUR_PROXY_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-3.5-turbo","messages":[{"role":"user","content":"Hello"}]}'
```

## 目录结构

```
.
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 应用入口
│   ├── config.py            # 配置管理
│   ├── models/              # SQLAlchemy 模型
│   ├── schemas/             # Pydantic 模型
│   ├── api/                 # API 路由
│   ├── middleware/          # 中间件（鉴权、限流）
│   ├── services/            # 业务逻辑
│   └── utils/               # 工具函数
├── scripts/
│   ├── init_db.py           # 数据库初始化
│   └── create_admin.py      # 创建管理员
├── migrations/              # Alembic 迁移
├── nginx/
│   └── nginx.conf           # Nginx 配置
├── docker/
│   └── entrypoint.sh        # 容器启动脚本
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── requirements.txt
```

## 环境变量说明

详见 `.env.example`

## 核心特性

### ✅ 已实现功能

1. **OpenAI 兼容接口**
   - `/v1/chat/completions` 完全兼容 OpenAI API
   - 支持流式（SSE）和非流式响应
   - 支持所有 OpenAI 参数（temperature, top_p, max_tokens 等）

2. **鉴权系统**
   - 基于 Proxy API Key 的多用户体系
   - 每个用户可拥有多个 API Key
   - 支持 Key 级别的模型限制和速率限制

3. **限流保护**
   - 双重限流：API Key + IP 地址
   - 支持 RPM（每分钟请求数）和 TPM（每分钟Token数）
   - 基于 Redis 的滑动窗口计数

4. **配额管理**
   - 月度 Token 配额
   - 实时配额检查
   - 自动用量统计（每日/每月聚合）

5. **Key 池管理**
   - 支持多个上游 Key（OpenAI 或 Azure OpenAI）
   - 权重轮询调度
   - 自动熔断与恢复
   - 失败计数和健康状态跟踪

6. **审计日志**
   - 完整的请求记录（时间、IP、用户、模型、Token、耗时）
   - 可配置的隐私保护（默认不记录完整 prompt）
   - 每日/每月用量聚合

7. **安全特性**
   - 上游 Key 加密存储（Fernet 对称加密）
   - HTTPS 支持（Let's Encrypt）
   - 敏感信息脱敏

8. **部署与运维**
   - Docker Compose 一键部署
   - Nginx 反向代理 + SSL
   - 数据库迁移工具（Alembic）
   - 初始化脚本

## 常见问题

### SSE 流式响应不工作
- 检查 Nginx 配置：`proxy_buffering off;`
- 检查 FastAPI：使用 `StreamingResponse`
- 检查超时设置
- 详见 [故障排查指南](TROUBLESHOOTING.md)

### 限流不生效
- 确认 Redis 连接正常
- 检查限流中间件是否启用
- 查看 Redis 中的 key 是否存在
- 详见 [故障排查指南](TROUBLESHOOTING.md)

### 上游请求失败
- 检查 Key 池状态（健康检查）
- 查看熔断日志
- 确认上游 API 可用性
- 详见 [故障排查指南](TROUBLESHOOTING.md)

## 安全检查清单

- [ ] 所有环境变量已正确配置
- [ ] 上游 Key 已加密存储
- [ ] 限流规则已启用
- [ ] 审计日志已开启
- [ ] 数据库备份已配置
- [ ] HTTPS 证书已配置
- [ ] 防火墙规则已设置
- [ ] 监控告警已配置
