# 前端功能说明

## 功能概览

已实现完整的 Vue 3 前端应用，包括：

### 1. 用户认证
- ✅ 用户注册（用户名、邮箱、密码）
- ✅ 用户登录（JWT认证）
- ✅ 自动保存登录状态
- ✅ 路由守卫（未登录自动跳转）

### 2. 聊天界面
- ✅ 类似ChatGPT的对话界面
- ✅ 实时流式响应（SSE）
- ✅ 多轮对话支持
- ✅ 自动获取用户API Key
- ✅ 消息历史记录

### 3. 管理后台（仅管理员）
- ✅ 用户管理
  - 查看用户列表
  - 创建新用户
  - 启用/禁用用户
  - 编辑用户配额
- ✅ API Key管理
  - 查看所有API Key
  - 创建新Key
  - 启用/禁用Key
  - 删除Key
- ✅ 用量统计
  - 总请求数
  - 总Token数
  - 活跃用户数
  - 每日用量记录

## 技术实现

### 前端技术栈
- **Vue 3** (Composition API)
- **Vue Router 4** (路由)
- **Pinia** (状态管理)
- **Axios** (HTTP客户端)
- **Vite** (构建工具)

### 后端API
- `/api/auth/register` - 用户注册
- `/api/auth/login` - 用户登录
- `/api/auth/me` - 获取当前用户信息
- `/api/admin/users` - 用户管理
- `/api/admin/api-keys` - API Key管理
- `/api/admin/usage` - 用量统计
- `/api/v1/chat/completions` - 聊天接口

## 部署说明

### 开发环境

```bash
cd frontend
npm install
npm run dev
```

访问：http://localhost:3000

### 生产环境

前端已集成到 Docker Compose 中：

```bash
# 构建并启动所有服务（包括前端）
docker-compose up -d

# 仅构建前端
docker-compose build frontend

# 查看前端日志
docker-compose logs -f frontend
```

前端服务运行在 `frontend:80`，通过 Nginx 反向代理访问。

## 路由说明

- `/login` - 登录页面
- `/register` - 注册页面
- `/chat` - 聊天界面（需登录）
- `/admin` - 管理后台（需管理员权限）

## 状态管理

使用 Pinia 管理全局状态：

- `auth` store: 用户认证状态
  - `user`: 当前用户信息
  - `token`: JWT token
  - `isAuthenticated`: 是否已登录
  - `isAdmin`: 是否管理员

## 样式说明

使用 Tailwind CSS 类名（内联），无需额外安装。

主要样式：
- 响应式布局
- 现代化UI设计
- 深色/浅色主题支持（可扩展）

## 常见问题

### 1. 前端无法连接后端API

检查：
- 后端服务是否启动
- `VITE_API_BASE_URL` 环境变量是否正确
- Nginx配置是否正确代理 `/api` 路径

### 2. 登录后跳转失败

检查：
- JWT token是否正确保存
- 路由守卫是否正确配置
- 后端 `/api/auth/me` 接口是否正常

### 3. 流式响应不工作

检查：
- 浏览器是否支持 SSE
- 网络连接是否正常
- 后端SSE配置是否正确

## 下一步扩展

可考虑添加：
- [ ] 消息历史持久化
- [ ] 多模型选择
- [ ] 对话导出
- [ ] 主题切换
- [ ] 移动端适配
- [ ] 实时通知
- [ ] 文件上传
