# 前端项目

基于 Vue 3 + Vite + Tailwind CSS 的前端应用，包含：
- 用户登录/注册
- 聊天界面（类似ChatGPT）
- 管理后台（用户管理、API Key管理、用量统计）

## 开发

```bash
# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build
```

## 环境变量

创建 `.env` 文件：

```env
VITE_API_BASE_URL=/api
```

## 功能

### 1. 登录/注册
- 用户注册（用户名、邮箱、密码）
- 用户登录（JWT认证）
- 自动保存登录状态

### 2. 聊天界面
- 实时流式对话
- 支持多轮对话
- 自动获取用户API Key

### 3. 管理后台（仅管理员）
- 用户管理（创建、禁用、编辑配额）
- API Key管理（创建、禁用、删除）
- 用量统计（总请求数、总Token数、活跃用户）

## 技术栈

- Vue 3 (Composition API)
- Vue Router 4
- Pinia (状态管理)
- Axios (HTTP客户端)
- Tailwind CSS (样式框架)

## 样式说明

项目使用 Tailwind CSS 进行样式设计，所有样式类名都基于 Tailwind 的工具类。

如果样式不显示，请确保：
1. 已安装依赖：`npm install`
2. Tailwind CSS 已正确配置（`tailwind.config.js`）
3. PostCSS 已配置（`postcss.config.js`）
4. 样式文件已导入（`src/style.css` 包含 `@tailwind` 指令）
