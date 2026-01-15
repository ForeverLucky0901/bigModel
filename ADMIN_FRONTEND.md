# 管理后台前端说明

## 项目结构

管理后台已独立为单独的前端项目：`admin-frontend/`

```
admin-frontend/
├── src/
│   ├── pages/
│   │   ├── Login.vue      # 登录页面
│   │   ├── Dashboard.vue  # 概览仪表板
│   │   ├── Users.vue      # 用户管理
│   │   ├── ApiKeys.vue    # API Key管理
│   │   └── Usage.vue      # 用量统计
│   ├── components/
│   │   └── Layout.vue     # 布局组件
│   ├── stores/
│   │   └── auth.js        # 认证状态管理
│   └── router/
│       └── index.js       # 路由配置
├── Dockerfile
├── nginx.conf
└── package.json
```

## 访问方式

### 开发环境
```bash
cd admin-frontend
npm install
npm run dev
```
访问：http://localhost:3001

### 生产环境
通过 Nginx 代理访问：`https://your-domain.com/admin`

## 路由说明

- `/admin/login` - 登录页面
- `/admin/` - 概览仪表板
- `/admin/users` - 用户管理
- `/admin/api-keys` - API Key管理
- `/admin/usage` - 用量统计

## 与主前端的区别

1. **独立项目**：完全独立的前端工程，不依赖主前端
2. **独立部署**：可以单独部署和更新
3. **独立路由**：使用 `/admin` 作为 base 路径
4. **独立认证**：使用独立的 token 存储（`admin-token`）

## 部署

管理后台已集成到 Docker Compose 中：

```bash
# 构建并启动
docker-compose up -d admin-frontend

# 查看日志
docker-compose logs -f admin-frontend
```

## 测试账号

使用管理员账号登录：
- 用户名：`admin`
- 密码：`admin123`
