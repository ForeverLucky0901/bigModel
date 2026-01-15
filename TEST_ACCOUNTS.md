# 测试账号信息

## 快速创建测试账号

运行以下命令创建测试账号：

```bash
# 使用Docker
docker-compose run --rm api python scripts/create_test_users.py

# 或直接运行
python scripts/create_test_users.py
```

## 默认测试账号

### 管理员账号
- **用户名**: `admin`
- **密码**: `admin123`
- **权限**: 管理员（可访问管理后台）

### 普通用户账号
- **用户名**: `test`
- **密码**: `test123`
- **权限**: 普通用户（只能使用聊天功能）

## 使用说明

1. 启动服务后，运行 `create_test_users.py` 脚本
2. 访问前端页面：http://localhost:3000 或你的域名
3. 使用上述账号登录即可

## 安全提示

⚠️ **这些是测试账号，仅用于开发环境！**

生产环境请：
1. 修改默认密码
2. 删除测试账号
3. 使用强密码策略
4. 启用双因素认证（如需要）
