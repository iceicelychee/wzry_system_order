# 订单管理系统 - 启动说明

## 环境要求
- Python 3.10+
- Node.js 18+
- MySQL 5.7+

---

## 后端启动

### 1. 配置数据库
编辑 `backend/.env` 文件，修改数据库连接信息：
```
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=你的密码
DB_NAME=order_system
```

### 2. 创建数据库
在 MySQL 中执行：
```sql
CREATE DATABASE order_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 3. 安装依赖
```bash
cd backend
pip install -r requirements.txt
```

### 4. 启动后端
```bash
cd backend
python main.py
```
后端运行在 http://localhost:8000
API文档访问 http://localhost:8000/docs

**默认管理员账号：admin / admin123**（首次启动自动创建）

---

## 前端启动

### 开发模式
```bash
cd frontend
npm install
npm run dev
```
前端运行在 http://localhost:5173

### 生产构建
```bash
cd frontend
npm run build
```

---

## 脚本对接说明

脚本执行完成后通过以下接口回调后端：

### 上传二维码
```
POST http://localhost:8000/api/callback/qrcode
Form参数：
  - order_token: 订单token（从订单链接中获取）
  - qrcode: 二维码图片文件
  - expire_seconds: 二维码有效期（秒，默认120）
```

### 更新状态
```
POST http://localhost:8000/api/callback/status
JSON参数：
  - order_token: 订单token
  - status: qrcode_scanned | qrcode_confirmed | qrcode_expired | running
  - message: 状态说明（可选）
```

### 上报执行结果
```
POST http://localhost:8000/api/callback/result
JSON参数：
  - order_token: 订单token
  - success: true | false
  - result: 成功结果说明（可选）
  - error_msg: 失败原因（可选）
```
