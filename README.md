# 订单管理系统

一个功能完善的订单管理平台，支持管理员、代理和客户三种角色，提供订单管理、图库管理、余额充值等功能。
## 项目截图
<img width="1874" height="922" alt="d1601f9e47042930812e0b76c5485e6f" src="https://github.com/user-attachments/assets/4ad621e5-8118-436d-a865-1cd5a9e60a8f" />
<img width="1874" height="922" alt="1895cae679df7ca08e540a8a904ac406" src="https://github.com/user-attachments/assets/022b3736-dfb5-40d7-821b-a165a74d1ae8" />
<img width="1874" height="922" alt="b8b4fbaec167398a110d4734f4845807" src="https://github.com/user-attachments/assets/41376adb-4ee3-4fe0-ba56-fbbe157c5b31" />
<img width="1874" height="922" alt="b8b4fbaec167398a110d4734f4845807" src="https://github.com/user-attachments/assets/466ee160-7568-4c22-b1ba-19efe3abb9e8" />
<img width="1874" height="922" alt="27591d4fb1cc20ef007f752052d1c08f" src="https://github.com/user-attachments/assets/59c343d2-a454-4560-9dc9-20dd840e6745" />
<img width="1874" height="922" alt="2db1e2ce4bf2e93d79a716a179693b1e" src="https://github.com/user-attachments/assets/dad28477-44cd-4e0a-9bb4-4cdaa8d236e5" />

## 系统架构

### 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python + FastAPI + SQLAlchemy + MySQL |
| 前端 | Vue 3 + Element Plus + Pinia + Vue Router |
| 部署 | Uvicorn + Vite |

### 目录结构

```
order-system/
├── backend/                 # 后端服务
│   ├── api/                # API 路由模块
│   │   ├── auth.py         # 认证相关
│   │   ├── order.py        # 订单管理
│   │   ├── gallery.py      # 图库管理
│   │   ├── agent.py        # 代理管理
│   │   ├── client.py       # 客户端接口
│   │   └── callback.py     # 回调处理
│   ├── models/             # 数据模型
│   │   ├── models.py       # 业务模型定义
│   │   └── database.py     # 数据库连接配置
│   ├── services/           # 业务逻辑
│   │   ├── auth.py         # 认证服务
│   │   └── order_utils.py  # 订单工具
│   ├── main.py             # 应用入口
│   ├── config.py           # 配置文件
│   └── requirements.txt    # Python 依赖
│
├── frontend/               # 前端应用
│   ├── src/
│   │   ├── views/          # 页面视图
│   │   │   ├── admin/      # 管理员页面
│   │   │   ├── agent/      # 代理页面
│   │   │   └── client/     # 客户端页面
│   │   ├── api/            # API 接口封装
│   │   ├── router/         # 路由配置
│   │   └── main.js         # 应用入口
│   ├── package.json        # Node 依赖
│   └── vite.config.js      # Vite 配置
│
└── README.md               # 项目文档
```

## 功能模块

### 1. 管理员后台

- **登录认证**: JWT Token 认证，24小时有效期
- **订单管理**: 创建、查看、编辑、禁用、删除订单
- **批量操作**: 批量创建、批量删除、导出订单
- **图库管理**: 图片上传、分类管理、批量勾选删除/分类
- **代理管理**: 创建代理、余额充值、密码重置
- **操作日志**: 记录管理员和代理的操作行为

### 2. 代理后台

- **登录认证**: 独立的代理登录入口
- **订单管理**: 查看自己的订单、创建新订单
- **余额管理**: 查看余额变动记录
- **个人设置**: 修改密码

### 3. 客户端

- **订单填写**: 客户通过链接填写订单信息
- **图片上传**: 支持本地上传（带16:9裁剪）或图库选图
- **状态查询**: 实时查看订单处理状态
- **自动跳转**: 已提交订单自动跳转到状态页面

## 核心功能特性

### 安全优化

- **密钥管理**: SECRET_KEY 使用环境变量配置，带安全随机回退
- **CORS 限制**: 限制为指定域名，收紧 HTTP 方法和请求头
- **SQL 注入防护**: LIKE 查询特殊字符转义
- **API 文档控制**: 生产环境可关闭 Swagger 文档暴露
- **文件上传验证**: 扩展名白名单 + 大小限制

### 性能优化

- **数据库连接池**: 配置 pool_size、max_overflow、pool_recycle
- **N+1 查询优化**: 使用 joinedload 预加载关联数据
- **数据库索引**: 外键和常用查询字段添加索引
- **批量导出优化**: 分批查询防止内存溢出
- **并发安全**: 使用 with_for_update() 行级锁防止竞态条件

### 图片处理

- **16:9 裁剪**: 本地上传图片支持固定比例裁剪
- **批量管理**: 图库支持批量勾选、删除、分类
- **分类管理**: 灵活的图库分类体系
- **图片预览**: 支持大图预览

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- MySQL 8.0+

### 后端启动

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件配置数据库连接等信息

# 启动服务
python main.py
```

后端服务默认运行在 http://localhost:8000

### 前端启动

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端服务默认运行在 http://localhost:5174

### 默认账号

- **管理员**: admin / admin123
- **代理**: 通过管理员后台创建

## API 接口

### 认证模块

| 接口 | 方法 | 描述 |
|------|------|------|
| /api/auth/login | POST | 管理员登录 |
| /api/auth/agent-login | POST | 代理登录 |
| /api/auth/me | GET | 获取当前用户信息 |

### 订单模块

| 接口 | 方法 | 描述 |
|------|------|------|
| /api/order/list | GET | 订单列表 |
| /api/order/create | POST | 创建订单 |
| /api/order/detail/{id} | GET | 订单详情 |
| /api/order/update/{id} | PUT | 更新订单 |
| /api/order/delete/{id} | DELETE | 删除订单 |
| /api/order/batch-delete | POST | 批量删除 |
| /api/order/export | GET | 导出订单 |

### 图库模块

| 接口 | 方法 | 描述 |
|------|------|------|
| /api/gallery/list | GET | 图片列表 |
| /api/gallery/upload | POST | 上传图片 |
| /api/gallery/delete/{id} | DELETE | 删除图片 |
| /api/gallery/batch-delete | POST | 批量删除 |
| /api/gallery/batch-category | POST | 批量设置分类 |
| /api/gallery/category/list | GET | 分类列表 |
| /api/gallery/category/create | POST | 创建分类 |

### 代理模块

| 接口 | 方法 | 描述 |
|------|------|------|
| /api/agent/list | GET | 代理列表 |
| /api/agent/create | POST | 创建代理 |
| /api/agent/recharge/{id} | POST | 余额充值 |
| /api/agent/my-orders | GET | 我的订单 |

### 客户端模块

| 接口 | 方法 | 描述 |
|------|------|------|
| /api/client/order/{token} | GET | 获取订单信息 |
| /api/client/order/{token}/submit | POST | 提交订单 |
| /api/client/order/{token}/status | GET | 查询订单状态 |

### 回调模块

| 接口 | 方法 | 描述 |
|------|------|------|
| /api/callback/qrcode | POST | 上传二维码 |
| /api/callback/status | POST | 更新状态 |
| /api/callback/result | POST | 上报执行结果 |
| /api/callback/ws/{token} | WebSocket | 状态实时推送 |

## 配置说明

### 后端配置 (.env)

```env
# 数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=order_system

# 安全配置
SECRET_KEY=your-secret-key-here
CORS_ORIGINS=http://localhost:5174,http://127.0.0.1:5174

# 连接池配置
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_RECYCLE=3600

# API文档
ENABLE_DOCS=true
```

### 前端配置 (vite.config.js)

```javascript
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5174,
    proxy: {
      '/api': { target: 'http://localhost:8000', changeOrigin: true },
      '/uploads': { target: 'http://localhost:8000', changeOrigin: true },
    }
  }
})
```

## 部署建议

### 生产环境

1. **关闭调试模式**: 设置 `ENABLE_DOCS=false`
2. **使用 HTTPS**: 配置 SSL 证书
3. **数据库安全**: 使用强密码，限制访问 IP
4. **文件存储**: 考虑使用对象存储服务
5. **日志监控**: 配置日志收集和告警

### Docker 部署

```dockerfile
# 后端 Dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```dockerfile
# 前端 Dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY package.json .
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
```

## 更新日志

### v1.0.0

- 基础订单管理功能
- 管理员和代理权限体系
- 图库管理功能
- 客户端订单提交流程
- 安全与性能优化
- 图片16:9裁剪功能
- 图库批量操作功能

## 许可证

MIT License
