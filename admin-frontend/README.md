# 管理后台前端

独立的管理后台前端项目，基于 Vue 3 + Vite + Tailwind CSS。

## 功能

- 用户管理（查看、创建、启用/禁用、编辑配额）
- API Key管理（查看、创建、启用/禁用、删除）
- 用量统计（总请求数、总Token数、活跃用户、每日记录）

## 开发

```bash
# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build
```

## 访问

- 开发环境：http://localhost:3001
- 生产环境：https://your-domain.com/admin

## 技术栈

- Vue 3 (Composition API)
- Vue Router 4
- Pinia (状态管理)
- Axios (HTTP客户端)
- Tailwind CSS (样式框架)

## 路由

- `/login` - 登录页面
- `/` - 概览仪表板
- `/users` - 用户管理
- `/api-keys` - API Key管理
- `/usage` - 用量统计
