# 订单管理系统 - 部署说明文档

本文档详细描述如何将订单管理系统部署到云服务器（以 Ubuntu 22.04 为例）。

---

## 目录

1. [环境要求](#环境要求)
2. [服务器初始化](#服务器初始化)
3. [数据库配置](#数据库配置)
4. [项目上传](#项目上传)
5. [后端部署](#后端部署)
6. [前端部署](#前端部署)
7. [Nginx 配置](#nginx-配置)
8. [HTTPS 配置](#https-配置推荐)
9. [防火墙配置](#防火墙配置)
10. [验证与测试](#验证与测试)
11. [运维管理](#运维管理)
12. [常见问题](#常见问题)

---

## 环境要求

### 硬件配置建议

| 配置 | 最低要求 | 推荐配置 |
|------|----------|----------|
| CPU | 1 核 | 2 核 |
| 内存 | 2GB | 4GB |
| 硬盘 | 20GB | 40GB+ |
| 带宽 | 1Mbps | 3Mbps+ |

### 软件版本

| 组件 | 版本要求 |
|------|----------|
| 操作系统 | Ubuntu 20.04+/Debian 10+ |
| Python | 3.10+ |
| Node.js | 18+ |
| MySQL | 8.0+ |
| Nginx | 1.18+ |

---

## 服务器初始化

### 1. 更新系统

```bash
sudo apt update && sudo apt upgrade-y
```

### 2. 安装基础软件

```bash
# 安装 Python 3.10+
sudo apt install python3 python3-pip python3-venv -y

# 验证 Python 版本
python3 --version  # 应 >= 3.10
```

### 3. 安装 Node.js 18+

```bash
# 使用 NodeSource 源
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs -y

# 验证版本
node --version  # 应 >= v18.0.0
npm --version
```

### 4. 安装 MySQL 8

```bash
sudo apt install mysql-server -y
sudo systemctl start mysql
sudo systemctl enable mysql

# 验证状态
sudo systemctl status mysql
```

### 5. 安装 Nginx

```bash
sudo apt install nginx -y
sudo systemctl start nginx
sudo systemctl enable nginx

# 验证状态
sudo systemctl status nginx
```

---

## 数据库配置

### 1. 登录 MySQL

```bash
sudo mysql-u root -p
```

### 2. 创建数据库和用户

```sql
-- 创建数据库
CREATE DATABASE order_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 创建专用用户（替换 '你的强密码' 为实际密码）
CREATE USER 'order_user'@'localhost' IDENTIFIED BY '你的强密码';

-- 授权
GRANT ALL PRIVILEGES ON order_system.* TO 'order_user'@'localhost';

-- 刷新权限
FLUSH PRIVILEGES;

-- 退出
EXIT;
```

### 3. 测试连接

```bash
mysql -u order_user -p
# 输入密码后应能成功登录
```

---

## 项目上传

### 方法一：Git 克隆（推荐）

```bash
# 在服务器上创建项目目录
sudo mkdir -p /opt/order-system
sudo chown $USER:$USER /opt/order-system

# 克隆代码（替换为你的仓库地址）
cd /opt
git clone <你的 Git 仓库地址> order-system
cd order-system
```

### 方法二：SCP 上传

```bash
# 本地打包（在项目根目录执行）
tar --exclude='node_modules' \
    --exclude='__pycache__' \
    --exclude='.env' \
    --exclude='venv' \
    --exclude='.git' \
    -czf order-system.tar.gz .

# 上传到服务器
scp order-system.tar.gz root@服务器IP:/opt/

# 服务器解压
cd /opt
mkdir -p order-system
cd order-system
tar -xzf /opt/order-system.tar.gz --strip-components=1
```

### 方法三：FTP/SFTP 上传

使用 FileZilla 等工具上传整个项目到 `/opt/order-system` 目录。

---

## 后端部署

### 1. 创建虚拟环境

```bash
cd /opt/order-system/backend

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 验证
which python  # 应指向 venv 内的 python
```

### 2. 安装依赖

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. 配置文件

```bash
# 复制配置模板
cp .env.example .env

# 编辑配置
nano .env
```

**编辑 `.env` 文件：**

```env
# ===== 数据库配置 =====
DB_HOST=localhost
DB_PORT=3306
DB_USER=order_user
DB_PASSWORD=你的强密码
DB_NAME=order_system

# ===== 安全配置 =====
# 生成随机密钥：python -c "import secrets; print(secrets.token_urlsafe(32))"
SECRET_KEY=这里替换为随机生成的 32 位以上字符串
CORS_ORIGINS=https://你的域名

# ===== 连接池配置 =====
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_RECYCLE=3600

# ===== API 文档 =====
# 生产环境必须设为 false
ENABLE_DOCS=false

# ===== 文件上传配置 =====
MAX_FILE_SIZE=5242880
UPLOAD_DIR=/opt/order-system/backend/uploads
```

### 4. 初始化数据库

```bash
# 确保在虚拟环境中
source venv/bin/activate

# 启动一次应用会自动创建表
python main.py &
sleep 3
kill %1

# 或者手动执行初始化脚本（如果有）
```

### 5. 创建 Systemd 服务

```bash
sudo nano /etc/systemd/system/order-backend.service
```

**写入以下内容：**

```ini
[Unit]
Description=Order System Backend Service
After=network.target mysql.service
Wants=mysql.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/order-system/backend
Environment="PATH=/opt/order-system/backend/venv/bin"
ExecStart=/opt/order-system/backend/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal

# 安全限制
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

### 6. 启动后端服务

```bash
# 重载 systemd
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start order-backend

# 设置开机自启
sudo systemctl enable order-backend

# 查看状态
sudo systemctl status order-backend

# 查看日志
sudo journalctl -u order-backend -f
```

---

## 前端部署

### 1. 安装依赖并构建

```bash
cd /opt/order-system/frontend

# 安装依赖
npm install

# 修改 Vite 配置（如果需要指定生产 API 地址）
nano vite.config.js
```

**确认 `vite.config.js` 代理配置：**

```javascript
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5174,
   proxy: {
      '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/uploads': { target: 'http://127.0.0.1:8000', changeOrigin: true },
    }
  }
})
```

### 2. 生产构建

```bash
# 执行构建
npm run build

# 构建产物在 dist/ 目录
ls -la dist/
```

### 3. 验证构建

```bash
# 本地预览（可选）
npm run preview
# 访问 http://localhost:4173
```

---

## Nginx 配置

### 1. 创建站点配置

```bash
sudo nano /etc/nginx/sites-available/order-system
```

**写入以下内容（替换 `你的域名` 为实际域名或服务器 IP）：**

```nginx
server {
   listen 80;
   server_name 你的域名;

    # 日志配置
    access_log /var/log/nginx/order-system-access.log;
    error_log /var/log/nginx/order-system-error.log;

    # 前端静态文件
    location / {
        root /opt/order-system/frontend/dist;
       index index.html;
        
        # SPA 路由支持
       try_files $uri $uri/ /index.html;
        
        # 缓存静态资源
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
           expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # 后端 API 代理
    location /api/ {
       proxy_pass http://127.0.0.1:8000;
        
        # 重要头部
       proxy_set_header Host $host;
       proxy_set_header X-Real-IP $remote_addr;
       proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时设置
       proxy_connect_timeout 60s;
       proxy_send_timeout 60s;
       proxy_read_timeout 60s;
    }

    # WebSocket 代理（状态实时推送）
    location /api/callback/ws/ {
       proxy_pass http://127.0.0.1:8000;
        
        # WebSocket 必需配置
       proxy_http_version 1.1;
       proxy_set_header Upgrade $http_upgrade;
       proxy_set_header Connection "upgrade";
        
        # 其他头部
       proxy_set_header Host $host;
       proxy_set_header X-Real-IP $remote_addr;
        
        # 长连接超时（1 天）
       proxy_read_timeout 86400s;
       proxy_send_timeout 86400s;
    }

    # 上传文件代理
    location /uploads/ {
       proxy_pass http://127.0.0.1:8000;
       proxy_set_header Host $host;
    }

    # 上传大小限制（10MB）
    client_max_body_size 10m;
    
    # 禁止访问隐藏文件
    location ~ /\. {
       deny all;
        access_log off;
        log_not_found off;
    }
}
```

### 2. 启用站点

```bash
# 创建软链接
sudo ln -s /etc/nginx/sites-available/order-system /etc/nginx/sites-enabled/

# 删除默认站点（避免冲突）
sudo rm /etc/nginx/sites-enabled/default

# 测试配置
sudo nginx -t

# 重启 Nginx
sudo systemctl restart nginx
```

### 3. 验证 Nginx

```bash
# 查看状态
sudo systemctl status nginx

# 查看错误日志
sudo tail -f /var/log/nginx/order-system-error.log
```

---

## HTTPS 配置（推荐）

### 1. 安装 Certbot

```bash
sudo apt install certbot python3-certbot-nginx -y
```

### 2. 申请 SSL 证书

```bash
# 替换为你的域名
sudo certbot --nginx -d 你的域名

# 按提示输入邮箱，同意条款
```

Certbot 会自动：
- 验证域名所有权
- 申请 SSL 证书
- 修改 Nginx 配置启用 HTTPS
- 配置自动重定向 HTTP → HTTPS

### 3. 验证自动续期

```bash
# 测试续期
sudo certbot renew --dry-run

# 查看续期定时器
systemctl list-timers | grep certbot
```

### 4. 手动配置（可选）

如果自动配置失败，手动修改 Nginx：

```nginx
server {
   listen 443 ssl http2;
   server_name 你的域名;

    ssl_certificate/etc/letsencrypt/live/你的域名/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/你的域名/privkey.pem;
    
    # SSL 优化配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # ... 其他配置同上 ...
}

# HTTP 自动跳转 HTTPS
server {
   listen 80;
   server_name 你的域名;
   return 301 https://$server_name$request_uri;
}
```

---

## 防火墙配置

### 1. 启用 UFW

```bash
sudo ufw enable
sudo ufw default deny incoming
sudo ufw default allow outgoing
```

### 2. 开放必要端口

```bash
# SSH（必须先开放，否则会断开连接！）
sudo ufw allow ssh

# HTTP
sudo ufw allow http

# HTTPS
sudo ufw allow https

# 如果需要直接访问后端（不推荐）
# sudo ufw allow 8000
```

### 3. 查看状态

```bash
sudo ufw status verbose
```

---

## 验证与测试

### 1. 检查服务状态

```bash
# 后端服务
sudo systemctl status order-backend

# Nginx
sudo systemctl status nginx

# MySQL
sudo systemctl status mysql
```

### 2. 访问测试

浏览器访问：
- HTTP: `http://你的域名`
- HTTPS: `https://你的域名`（推荐）

**首次登录：**
- 账号：`admin`
- 密码：`admin123`

**⚠️ 首次登录后立即修改默认密码！**

### 3. API 测试

```bash
# 测试后端接口（如果 ENABLE_DOCS=true）
curl https://你的域名/docs

# 测试登录接口
curl -X POST "https://你的域名/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

### 4. WebSocket 测试

打开浏览器开发者工具 → Network → WS，访问订单状态页面，应该能看到 WebSocket 连接成功。

---

## 运维管理

### 常用命令

```bash
# ===== 服务管理 =====
# 重启后端
sudo systemctl restart order-backend

# 重启 Nginx
sudo systemctl restart nginx

# 重启 MySQL
sudo systemctl restart mysql

# 查看所有服务状态
sudo systemctl status order-backend nginx mysql

# ===== 日志查看 =====
# 后端日志
sudo journalctl -u order-backend -f

# 后端日志（最近 100 行）
sudo journalctl -u order-backend -n 100

# Nginx 访问日志
sudo tail -f /var/log/nginx/order-system-access.log

# Nginx 错误日志
sudo tail -f /var/log/nginx/order-system-error.log

# ===== 更新代码 =====
# Git 方式
cd /opt/order-system
sudo git pull

# 重新构建前端
cd /opt/order-system/frontend
npm install && npm run build

# 重启后端
sudo systemctl restart order-backend

# ===== 数据库备份 =====
# 导出完整数据库
mysqldump -u order_user -p order_system > backup_$(date +%Y%m%d_%H%M%S).sql

# 恢复数据库
mysql -u order_user -p order_system < backup_20260310_120000.sql

# ===== 磁盘空间 =====
df -h
du -sh /opt/order-system/*
```

### 监控告警（可选）

安装监控工具：

```bash
# 安装 htop（进程监控）
sudo apt install htop -y

# 安装 netdata（实时监控面板）
bash <(curl -Ss https://my-netdata.io/kickstart.sh)
```

---

## 常见问题

### Q1: 后端无法启动

**检查步骤：**

```bash
# 1. 查看日志
sudo journalctl -u order-backend -f

# 2. 检查端口占用
sudo lsof -i :8000

# 3. 检查数据库连接
mysql -u order_user -p order_system -e "SELECT 1"

# 4. 检查虚拟环境
source /opt/order-system/backend/venv/bin/activate
which python
```

**常见错误：**

- `ModuleNotFoundError`: 依赖未安装 → `pip install -r requirements.txt`
- `Access denied for user`: 数据库密码错误 → 检查 `.env` 配置
- `Address already in use`: 端口被占用 → `sudo lsof -i :8000` 查看并处理

### Q2: 前端页面空白

**检查步骤：**

```bash
# 1. 查看 Nginx 错误日志
sudo tail -f /var/log/nginx/order-system-error.log

# 2. 检查 dist 目录是否存在
ls -la /opt/order-system/frontend/dist

# 3. 浏览器开发者工具查看控制台错误
```

**解决方案：**

- 重新构建前端：`cd /opt/order-system/frontend && npm run build`
- 清除浏览器缓存
- 检查 Nginx 配置的 `root` 路径是否正确

### Q3: API 请求失败（404/502）

**检查步骤：**

```bash
# 1. 检查后端是否运行
sudo systemctl status order-backend

# 2. 测试后端直连
curl http://127.0.0.1:8000/api/auth/me

# 3. 检查 Nginx 配置
sudo nginx -t

# 4. 查看 Nginx 错误日志
sudo tail -f /var/log/nginx/order-system-error.log
```

**常见原因：**

- 后端未启动 → `sudo systemctl start order-backend`
- Nginx 代理配置错误 → 检查 `proxy_pass` 地址
- CORS 配置错误 → 检查 `.env` 中的 `CORS_ORIGINS`

### Q4: WebSocket 连接失败

**检查步骤：**

```bash
# 1. 查看 Nginx WebSocket 配置
sudo cat /etc/nginx/sites-available/order-system | grep -A 20 "location /api/callback/ws"

# 2. 测试 WebSocket 连接
# 浏览器访问订单状态页面，打开开发者工具查看 WS 连接
```

**解决方案：**

确保 Nginx 配置包含：
```nginx
proxy_http_version 1.1;
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection "upgrade";
```

### Q5: 文件上传失败

**检查步骤：**

```bash
# 1. 检查 uploads 目录权限
ls -la /opt/order-system/backend/uploads

# 2. 检查 Nginx 上传大小限制
cat /etc/nginx/sites-available/order-system | grep client_max_body_size
```

**解决方案：**

```bash
# 设置目录权限
sudo chmod -R 755 /opt/order-system/backend/uploads

# Nginx 增加上传限制
client_max_body_size 10m;
```

### Q6: 数据库连接失败

```bash
# 1. 检查 MySQL 状态
sudo systemctl status mysql

# 2. 测试数据库连接
mysql -u order_user -p order_system

# 3. 检查 .env 配置
cat /opt/order-system/backend/.env | grep DB_

# 4. 重启后端
sudo systemctl restart order-backend
```

---

## 安全加固建议

### 1. 修改默认密码

首次登录后立即修改管理员默认密码（`admin/admin123`）。

### 2. 配置防火墙

只开放必要端口（80/443），关闭数据库远程访问。

```bash
sudo ufw status
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https
sudo ufw enable
```

### 3. 禁用 API 文档

生产环境设置 `ENABLE_DOCS=false`。

### 4. 定期更新

```bash
# 系统更新
sudo apt update && sudo apt upgrade -y

# Python 依赖更新
cd /opt/order-system/backend
source venv/bin/activate
pip install --upgrade -r requirements.txt

# Node 依赖更新
cd /opt/order-system/frontend
npm update
```

### 5. 日志轮转

配置日志轮转防止磁盘占满：

```bash
sudo nano /etc/logrotate.d/order-system
```

```
/var/log/nginx/order-system-*.log {
    daily
    missingok
    rotate 14
    compress
   delaycompress
    notifempty
   create 0640 www-data adm
    sharedscripts
    postrotate
        [ -f /var/run/nginx.pid ] && nginx -s reload
    endscript
}
```

---

## 联系支持

如遇到文档未覆盖的问题，请查看：
- 项目 README.md
- SCRIPT_API.md（脚本对接文档）
- 系统日志

---

**最后更新时间：** 2026-03-10  
**文档版本：** v1.0
