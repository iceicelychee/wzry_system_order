# 手机脚本对接 API 文档

本文档描述手机自动化脚本与订单管理系统的对接接口，包含二维码上传、状态更新、结果上报等功能。

---

## 接口概览

| 接口 | 方法 | 描述 | 认证 |
|------|------|------|------|
| `/api/client/order/{token}` | GET | 获取订单信息 | 否 |
| `/api/client/order/{token}/submit` | POST | 客户提交订单 | 否 |
| `/api/callback/qrcode` | POST | 上传登录二维码 | 否 |
| `/api/callback/status` | POST | 更新执行状态 | 否 |
| `/api/callback/result` | POST | 上报执行结果 | 否 |
| `/api/callback/ws/{token}` | WebSocket | 实时推送状态 | 否 |

---

## 1. 获取订单信息

脚本通过此接口验证订单有效性并获取基础信息。

**请求**

```http
GET /api/client/order/{token}
Host: localhost:8000
Content-Type: application/json
```

**路径参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| token | string | 是 | 订单唯一标识（64 位随机字符串） |

**响应示例**

```json
{
  "order_no": "ORD20260310001",
  "link_status": "已提交",
  "exec_status": "待执行",
  "system_type": "安卓 Q 区",
  "already_submitted": true
}
```

**字段说明**

| 字段 | 类型 | 说明 |
|------|------|------|
| order_no | string | 订单编号 |
| link_status | string | 链接状态：未填写/已提交/已过期/已禁用 |
| exec_status | string | 执行状态：待执行/执行中/成功/失败 |
| system_type | string | 系统类型：安卓 Q 区/苹果 Q 区/安卓 V 区/苹果 V 区 |
| already_submitted | boolean | 是否已提交（true 表示可以开始执行） |

**错误响应**

```json
// 404 - 订单不存在
{
  "detail": "Order not found"
}

// 403 - 链接已禁用或过期
{
  "detail": "Link disabled/expired"
}
```

---

## 2. 客户提交订单

客户通过链接填写并提交订单信息（包含游戏截图）。

**请求**

```http
POST /api/client/order/{token}/submit
Host: localhost:8000
Content-Type: multipart/form-data
```

**表单参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| system_type | string | 是 | 系统类型：安卓 Q 区/苹果 Q 区/安卓 V 区/苹果 V 区 |
| image | file | 是 | 游戏截图文件（JPG/PNG/BMP/GIF/WEBP，最大 5MB） |

**请求示例（Python）**

```python
import requests

url = "http://localhost:8000/api/client/order/abc123token/submit"
files = {
    'image': ('screenshot.jpg', open('screenshot.jpg', 'rb'), 'image/jpeg')
}
data = {
    'system_type': '安卓 Q 区'
}

response = requests.post(url, files=files, data=data)
print(response.json())
```

**响应示例**

```json
{
  "message": "Success",
  "order_no": "ORD20260310001"
}
```

**错误响应**

```json
// 400 - 格式不支持
{
  "detail": "Invalid format"
}

// 400 - 文件太大
{
  "detail": "Too large"
}

// 400 - 重复提交
{
  "detail": "Already submitted"
}
```

---

## 3. 上传登录二维码

脚本执行后，上传生成的登录二维码图片。

**请求**

```http
POST /api/callback/qrcode
Host: localhost:8000
Content-Type: multipart/form-data
```

**表单参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| order_token | string | 是 | 订单token |
| qrcode | file | 是 | 二维码图片文件（PNG 格式推荐） |
| expire_seconds | integer | 否 | 二维码有效时间（秒），默认 120 秒 |

**请求示例（Python）**

```python
import requests

url = "http://localhost:8000/api/callback/qrcode"
files = {
    'qrcode': ('qrcode.png', open('qrcode.png', 'rb'), 'image/png')
}
data = {
    'order_token': 'abc123token',
    'expire_seconds': 120
}

response = requests.post(url, files=files, data=data)
print(response.json())
```

**请求示例（curl）**

```bash
curl -X POST "http://localhost:8000/api/callback/qrcode" \
  -F "order_token=abc123token" \
  -F "qrcode=@qrcode.png" \
  -F "expire_seconds=120"
```

**响应示例**

```json
{
  "message": "二维码已接收"
}
```

**服务端行为**

1. 保存二维码图片到 `/uploads/qrcodes/` 目录
2. 创建 `ScriptCallback` 记录
3. 更新订单执行状态为 `running`
4. 添加执行日志："脚本已返回登录二维码，等待客户扫码"
5. 通过 WebSocket 推送给客户端

**WebSocket 推送数据**

```json
{
  "type": "qrcode",
  "qrcode_url": "/uploads/qrcodes/xxx.png",
  "expire_seconds": 120,
  "expired_at": "2026-03-10 12:34:56"
}
```

---

## 4. 更新执行状态

脚本在执行过程中实时更新状态（扫码、确认、过期等）。

**请求**

```http
POST /api/callback/status
Host: localhost:8000
Content-Type: application/json
```

**JSON参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| order_token | string | 是 | 订单token |
| status | string | 是 | 状态码（见下方说明） |
| message | string | 否 | 状态描述信息 |

**状态码说明**

| status | 说明 | 触发时机 |
|--------|------|----------|
| `qrcode_scanned` | 已扫码 | 客户扫描了二维码 |
| `qrcode_confirmed` | 已确认 | 客户确认登录 |
| `qrcode_expired` | 已过期 | 二维码超过有效期 |

**请求示例（Python）**

```python
import requests

url = "http://localhost:8000/api/callback/status"
data = {
    "order_token": "abc123token",
    "status": "qrcode_scanned",
    "message": "客户已扫描二维码"
}

response = requests.post(url, json=data)
print(response.json())
```

**请求示例（curl）**

```bash
curl -X POST "http://localhost:8000/api/callback/status" \
  -H "Content-Type: application/json" \
  -d '{"order_token":"abc123token","status":"qrcode_confirmed","message":"客户确认登录"}'
```

**响应示例**

```json
{
  "message": "状态已更新"
}
```

**服务端行为**

1. 更新 `ScriptCallback` 表中的 `qrcode_status`
2. 添加执行日志
3. 通过 WebSocket 推送给客户端

**WebSocket 推送数据**

```json
{
  "type": "status",
  "status": "qrcode_scanned",
  "message": "客户已扫描二维码"
}
```

---

## 5. 上报执行结果

脚本执行完成后，上报最终结果（成功或失败）。

**请求**

```http
POST /api/callback/result
Host: localhost:8000
Content-Type: application/json
```

**JSON参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| order_token | string | 是 | 订单token |
| success | boolean | 是 | 是否执行成功 |
| result | string | 否 | 成功时的结果描述 |
| error_msg | string | 否 | 失败时的错误信息 |

**请求示例（Python）**

```python
import requests

# 成功情况
url = "http://localhost:8000/api/callback/result"
data = {
    "order_token": "abc123token",
    "success": True,
    "result": "角色已成功创建，ID: 12345"
}

response = requests.post(url, json=data)
print(response.json())

# 失败情况
data_fail = {
    "order_token": "abc123token",
    "success": False,
    "error_msg": "网络连接超时，无法完成登录"
}

response = requests.post(url, json=data_fail)
print(response.json())
```

**请求示例（curl）**

```bash
# 成功
curl -X POST "http://localhost:8000/api/callback/result" \
  -H "Content-Type: application/json" \
  -d '{"order_token":"abc123token","success":true,"result":"角色创建成功"}'

# 失败
curl -X POST "http://localhost:8000/api/callback/result" \
  -H "Content-Type: application/json" \
  -d '{"order_token":"abc123token","success":false,"error_msg":"登录超时"}'
```

**响应示例**

```json
{
  "message": "结果已接收"
}
```

**服务端行为**

1. 更新订单 `exec_status` 为 `success` 或 `failed`
2. 更新 `ScriptCallback` 表的 `result` 或 `error_msg`
3. 添加执行日志
4. 通过 WebSocket 推送给客户端

**WebSocket 推送数据**

```json
{
  "type": "result",
  "success": true,
  "result": "角色已成功创建，ID: 12345",
  "error_msg": null
}
```

---

## 6. WebSocket 实时推送

客户端通过 WebSocket 连接实时接收脚本执行状态。

**连接地址**

```
ws://localhost:8000/api/callback/ws/{token}
```

**连接示例（前端 JavaScript）**

```javascript
const ws = new WebSocket('ws://localhost:8000/api/callback/ws/abc123token');

ws.onopen = () => {
  console.log('WebSocket 连接已建立');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('收到消息:', data);
  
  switch(data.type) {
   case 'qrcode':
      // 显示二维码
      showQrcode(data.qrcode_url, data.expire_seconds);
      break;
   case 'status':
      // 更新状态
     updateStatus(data.status, data.message);
      break;
   case 'result':
      // 显示结果
      showResult(data.success, data.result, data.error_msg);
      break;
  }
};

ws.onerror = (error) => {
  console.error('WebSocket 错误:', error);
};

ws.onclose = () => {
  console.log('WebSocket 连接已关闭');
};
```

**推送消息类型**

| type | 说明 | 字段 |
|------|------|------|
| `qrcode` | 二维码已上传 | qrcode_url, expire_seconds, expired_at |
| `status` | 状态更新 | status, message |
| `result` | 执行结果 | success, result, error_msg |

**连接错误码**

| 码值 | 说明 |
|------|------|
| 4004 | 订单不存在 |

---

## 完整流程示例

### 脚本执行流程

```python
import requests
import time

ORDER_TOKEN = "abc123token"
BASE_URL = "http://localhost:8000"

def execute_script():
    # 1. 验证订单
   resp = requests.get(f"{BASE_URL}/api/client/order/{ORDER_TOKEN}")
   order = resp.json()
    
    if not order.get('already_submitted'):
        print("订单尚未提交，等待...")
       return
    
    system_type = order['system_type']
    print(f"开始执行订单：{order['order_no']}, 系统类型：{system_type}")
    
    try:
        # 2. 执行脚本（模拟）
        print("正在启动游戏...")
        time.sleep(2)
        
        print("正在生成二维码...")
        # 这里调用实际的脚本生成二维码
        qrcode_path = generate_qrcode()  # 假设返回二维码文件路径
        
        # 3. 上传二维码
        with open(qrcode_path, 'rb') as f:
            files = {'qrcode': ('qrcode.png', f, 'image/png')}
            data = {
                'order_token': ORDER_TOKEN,
                'expire_seconds': 120
            }
           resp = requests.post(f"{BASE_URL}/api/callback/qrcode", 
                               files=files, data=data)
        print("二维码已上传")
        
        # 4. 等待扫码（轮询或等待回调）
        print("等待客户扫码...")
        wait_for_scan()
        
        # 5. 更新状态 - 已扫码
       requests.post(f"{BASE_URL}/api/callback/status", json={
            'order_token': ORDER_TOKEN,
            'status': 'qrcode_scanned',
            'message': '客户已扫描二维码'
        })
        
        # 6. 继续执行
        print("客户已确认登录")
       requests.post(f"{BASE_URL}/api/callback/status", json={
            'order_token': ORDER_TOKEN,
            'status': 'qrcode_confirmed',
            'message': '客户确认登录'
        })
        
        # 7. 执行主要任务
        print("正在创建角色...")
       result = create_character()  # 假设的执行函数
        
        # 8. 上报结果
       requests.post(f"{BASE_URL}/api/callback/result", json={
            'order_token': ORDER_TOKEN,
            'success': True,
            'result': f'角色创建成功：{result}'
        })
        
        print("执行完成")
        
   except Exception as e:
        # 9. 上报失败
       requests.post(f"{BASE_URL}/api/callback/result", json={
            'order_token': ORDER_TOKEN,
            'success': False,
            'error_msg': str(e)
        })
        print(f"执行失败：{e}")

# 运行脚本
execute_script()
```

---

## 错误处理建议

### 1. 网络错误

```python
try:
   response = requests.post(url, json=data, timeout=10)
   response.raise_for_status()
except requests.exceptions.Timeout:
    print("请求超时，稍后重试")
except requests.exceptions.ConnectionError:
    print("连接失败，检查网络")
except requests.exceptions.HTTPError as e:
    print(f"HTTP 错误：{e.response.status_code}")
```

### 2. 重试机制

```python
import time
from functools import wraps

def retry(max_attempts=3, delay=1):
   def decorator(func):
        @wraps(func)
       def wrapper(*args, **kwargs):
            for i in range(max_attempts):
                try:
                   return func(*args, **kwargs)
               except Exception as e:
                    if i == max_attempts - 1:
                        raise
                    print(f"第{i+1}次失败，{delay}秒后重试...")
                    time.sleep(delay)
       return wrapper
   return decorator

@retry(max_attempts=3, delay=2)
def upload_qrcode(token, qrcode_path):
    # 上传逻辑
   pass
```

---

## 安全建议

1. **Token 保护**: 订单token 应通过安全渠道发送给客户
2. **HTTPS**: 生产环境使用 HTTPS 加密传输
3. **文件验证**: 上传的文件应进行类型和大小验证
4. **频率限制**: 建议对回调接口添加频率限制防止滥用
5. **日志审计**: 所有操作应记录日志便于追溯

---

## 常见问题

### Q: 二维码上传后多久有效？

A: 默认 120 秒，可通过 `expire_seconds` 参数自定义。

### Q: 如何知道客户已扫码？

A: 通过 WebSocket 实时推送或轮询订单状态接口。

### Q: 脚本执行超时怎么处理？

A: 建议在脚本中设置超时时间，超时后主动上报失败结果。

### Q: 支持并发执行多个订单吗？

A: 支持，每个订单有独立的 token 和执行记录。

---

## 联系支持

如有问题请联系技术支持或查看项目文档。
