# 快速开始指南

## 5分钟快速部署

### 1. 准备环境变量

```bash
# 复制示例文件
cp env.example .env

# 编辑配置（必须修改）
nano .env
```

**必须配置的项：**
- `POSTGRES_PASSWORD`: 数据库密码
- `ENCRYPTION_KEY`: 加密密钥（运行 `openssl rand -hex 32` 生成）
- `OPENAI_API_KEYS`: 你的 OpenAI API Key（多个用逗号分隔）
- 或 `AZURE_ENDPOINT`, `AZURE_API_KEYS`: Azure OpenAI 配置

### 2. 启动服务

```bash
# 启动数据库和Redis
docker-compose up -d postgres redis

# 等待服务就绪（约30秒）
sleep 30

# 初始化数据库
docker-compose run --rm api python scripts/init_db.py

# 初始化上游密钥
docker-compose run --rm api python scripts/init_upstream_keys.py

# 创建管理员
docker-compose run --rm api python scripts/create_admin.py

# 启动所有服务
docker-compose up -d
```

### 3. 配置HTTPS（可选但推荐）

```bash
# 安装certbot
sudo apt install certbot python3-certbot-nginx -y

# 获取证书（替换your-domain.com）
sudo certbot certonly --standalone -d your-domain.com

# 复制证书
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/
sudo chown $USER:$USER nginx/ssl/*

# 重启Nginx
docker-compose restart nginx
```

### 4. 测试API

```bash
# 替换 YOUR_PROXY_KEY 为创建管理员时输出的Key
export PROXY_KEY="sk-proxy-..."

# 健康检查
curl https://your-domain.com/health

# 测试请求
curl https://your-domain.com/v1/chat/completions \
  -H "Authorization: Bearer $PROXY_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [
      {"role": "user", "content": "Hello!"}
    ]
  }'
```

## 使用示例

### Python SDK

```python
from openai import OpenAI

# 只改 base_url，其他完全兼容
client = OpenAI(
    api_key="sk-proxy-your-proxy-key-here",
    base_url="https://your-domain.com/v1"
)

# 使用方式与OpenAI完全一致
response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "user", "content": "Hello, world!"}
    ]
)

print(response.choices[0].message.content)
```

### 流式响应

```python
from openai import OpenAI

client = OpenAI(
    api_key="sk-proxy-your-proxy-key-here",
    base_url="https://your-domain.com/v1"
)

stream = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "user", "content": "Tell me a story"}
    ],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

### cURL

```bash
# 非流式
curl https://your-domain.com/v1/chat/completions \
  -H "Authorization: Bearer sk-proxy-..." \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello"}]
  }'

# 流式（SSE）
curl -N https://your-domain.com/v1/chat/completions \
  -H "Authorization: Bearer sk-proxy-..." \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello"}],
    "stream": true
  }'
```

## 管理操作

### 创建新用户

```bash
docker-compose run --rm api python scripts/create_user.py \
  --username testuser \
  --email test@example.com \
  --quota-tokens 1000000
```

### 查看日志

```bash
# 所有服务
docker-compose logs -f

# 特定服务
docker-compose logs -f api
```

### 重启服务

```bash
docker-compose restart api
```

## 常见问题

### 服务无法启动

1. 检查环境变量：`docker-compose config`
2. 查看日志：`docker-compose logs api`
3. 检查端口占用：`netstat -tulpn | grep 8000`

### API返回401

- 检查Authorization header格式：`Bearer sk-proxy-...`
- 验证API Key是否有效：查看数据库 `api_keys` 表

### 流式响应不工作

- 检查Nginx配置：`proxy_buffering off;`
- 查看Nginx日志：`docker-compose logs nginx`

更多问题请参考 [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
