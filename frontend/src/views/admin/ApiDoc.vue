<template>
  <div class="api-doc">
    <el-card shadow="never" style="margin-bottom:16px">
      <template #header>
        <span style="font-size:16px;font-weight:600">手机脚本 API 对接说明</span>
        <el-tag style="margin-left:12px" type="info">Base URL: http://47.103.11.175</el-tag>
      </template>
      <el-alert type="info" :closable="false" show-icon style="margin-bottom:0">
        <template #title>脚本专用接口无需设置自定义Header，使用表单提交即可，适合按键精灵手机助手等环境</template>
      </el-alert>
    </el-card>

    <!-- 流程图 -->
    <el-card shadow="never" style="margin-bottom:16px">
      <template #header><span>执行流程</span></template>
      <div class="flow-steps">
        <div class="flow-step" v-for="(step, i) in flowSteps" :key="i">
          <div class="step-num">{{ i + 1 }}</div>
          <div class="step-text">{{ step }}</div>
          <el-icon v-if="i < flowSteps.length - 1" class="step-arrow"><ArrowRight /></el-icon>
        </div>
      </div>
    </el-card>

    <!-- API 列表 -->
    <el-card shadow="never" v-for="api in apis" :key="api.title" style="margin-bottom:16px">
      <template #header>
        <div style="display:flex;align-items:center;gap:10px">
          <el-tag :type="api.method === 'POST' ? 'danger' : (api.method === 'GET' ? 'success' : 'warning')" size="small">
            {{ api.method }}
          </el-tag>
          <code class="api-path">{{ api.path }}</code>
          <span style="color:#606266;font-size:14px">{{ api.title }}</span>
        </div>
      </template>

      <div v-if="api.desc" class="api-desc">{{ api.desc }}</div>

      <div v-if="api.params" style="margin-top:12px">
        <div class="section-title">请求参数</div>
        <el-table :data="api.params" size="small" border>
          <el-table-column prop="name" label="参数名" width="160" />
          <el-table-column prop="type" label="类型" width="100" />
          <el-table-column prop="required" label="必填" width="70">
            <template #default="{row}">
              <el-tag :type="row.required ? 'danger' : 'info'" size="small">{{ row.required ? '是' : '否' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="desc" label="说明" />
        </el-table>
      </div>

      <div v-if="api.request" style="margin-top:12px">
        <div class="section-title">请求示例</div>
        <pre class="code-block">{{ api.request }}</pre>
      </div>

      <div v-if="api.response" style="margin-top:12px">
        <div class="section-title">响应示例</div>
        <pre class="code-block">{{ api.response }}</pre>
      </div>
    </el-card>

    <!-- 按键精灵示例 -->
    <el-card shadow="never">
      <template #header><span>按键精灵手机助手 MQB 示例</span></template>
      <pre class="code-block">{{ mqbExample }}</pre>
    </el-card>
  </div>
</template>

<script setup>
const flowSteps = [
  '脚本登录获取Token',
  '获取待执行订单信息',
  '下载订单图片到手机',
  '启动游戏获取登录二维码',
  '上传二维码等待客户扫码',
  '执行操作并上报结果',
]

const apis = [
  {
    method: 'POST',
    path: '/api/callback/script_login',
    title: '脚本专用登录',
    desc: '使用表单提交，无需设置Header，返回Token用于后续接口调用。',
    params: [
      { name: 'username', type: 'string', required: true, desc: '管理员用户名' },
      { name: 'password', type: 'string', required: true, desc: '管理员密码' },
    ],
    request: `POST /api/callback/script_login
Content-Type: application/x-www-form-urlencoded

username=admin&password=admin123`,
    response: `{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "username": "admin"
}`,
  },
  {
    method: 'GET',
    path: '/api/callback/script_orders?token=xxx',
    title: '获取待执行订单',
    desc: 'Token通过URL参数传递，返回订单信息及图片URL。',
    params: [
      { name: 'token', type: 'string', required: true, desc: '登录接口返回的access_token' },
    ],
    response: `{
  "total": 1,
  "order_no": "ORD20260310001",
  "token": "abc123xyz",
  "system_type": "安卓Q区",
  "image_url": "/uploads/orders/xxx.png"
}`,
  },
  {
    method: 'POST',
    path: '/api/callback/script_qrcode',
    title: '上传登录二维码',
    desc: '脚本解码二维码得到文本内容，通过表单提交。服务端自动生成二维码图片并推送给客户端。',
    params: [
      { name: 'order_token', type: 'string', required: true, desc: '订单token（从订单信息获取）' },
      { name: 'qrcode_text', type: 'string', required: true, desc: '二维码解码后的文本内容' },
      { name: 'expire_seconds', type: 'int', required: false, desc: '有效期秒数，默认120' },
    ],
    request: `POST /api/callback/script_qrcode
Content-Type: application/x-www-form-urlencoded

order_token=abc123xyz&qrcode_text=https://example.com/login&expire_seconds=120`,
    response: `{"message": "二维码已接收"}`,
  },
  {
    method: 'POST',
    path: '/api/callback/script_status',
    title: '更新扫码状态',
    desc: '客户扫码、确认或二维码过期时调用，通知服务端更新状态。',
    params: [
      { name: 'order_token', type: 'string', required: true, desc: '订单token' },
      { name: 'status', type: 'string', required: true, desc: '状态值：qrcode_scanned/qrcode_confirmed/qrcode_expired' },
      { name: 'message', type: 'string', required: false, desc: '附加说明' },
    ],
    request: `POST /api/callback/script_status
Content-Type: application/x-www-form-urlencoded

order_token=abc123xyz&status=qrcode_scanned&message=客户已扫码`,
    response: `{"message": "状态已更新"}`,
  },
  {
    method: 'POST',
    path: '/api/callback/script_result',
    title: '上报执行结果',
    desc: '脚本执行完成后上报结果，客户端页面自动展示成功或失败。',
    params: [
      { name: 'order_token', type: 'string', required: true, desc: '订单token' },
      { name: 'success', type: 'string', required: true, desc: '是否成功：true/false' },
      { name: 'result', type: 'string', required: false, desc: '成功时的结果说明' },
      { name: 'error_msg', type: 'string', required: false, desc: '失败时的错误信息' },
    ],
    request: `// 成功
order_token=abc123xyz&success=true&result=修改完成

// 失败
order_token=abc123xyz&success=false&error_msg=登录超时`,
    response: `{"message": "结果已接收"}`,
  },
]

const mqbExample = `// 王者荣耀订单处理脚本 - 按键精灵手机助手
// 所有接口使用表单提交，无需设置Header

Dim BASE_URL
BASE_URL = "http://47.103.11.175"

Dim g_token, g_order_token, g_order_no, g_system_type, g_image_url

// 1. 登录获取Token
Function LoginAndGetToken()
    Dim apiAddr, postData, resp
    apiAddr = BASE_URL & "/api/callback/script_login"
    postData = "username=admin&password=admin123"
    resp = Url.Post(apiAddr, postData)
    g_token = JsonGetStr(resp, "access_token")
End Function

// 2. 获取待执行订单
Function GetPendingOrder()
    Dim apiAddr, resp
    apiAddr = BASE_URL & "/api/callback/script_orders?token=" & g_token
    resp = Url.Get(apiAddr)
    g_order_token = JsonGetStr(resp, "token")
    g_order_no = JsonGetStr(resp, "order_no")
    g_system_type = JsonGetStr(resp, "system_type")
    g_image_url = JsonGetStr(resp, "image_url")
End Function

// 3. 下载订单图片（使用紫猫插件）
Function DownloadOrderImage()
    Dim imgUrl, savePath
    imgUrl = BASE_URL & g_image_url
    savePath = "/sdcard/DCIM/order_" & g_order_no & ".png"
    zm.HttpDownload imgUrl, savePath
End Function

// 4. 上传二维码文本
Function UploadQRCode(qrText)
    Dim apiAddr, postData, resp
    apiAddr = BASE_URL & "/api/callback/script_qrcode"
    postData = "order_token=" & g_order_token & "&qrcode_text=" & qrText & "&expire_seconds=120"
    resp = Url.Post(apiAddr, postData)
End Function

// 5. 更新状态
Function UpdateStatus(statusVal, msg)
    Dim apiAddr, postData, resp
    apiAddr = BASE_URL & "/api/callback/script_status"
    postData = "order_token=" & g_order_token & "&status=" & statusVal & "&message=" & msg
    resp = Url.Post(apiAddr, postData)
End Function

// 6. 上报结果
Function ReportResult(success, resultMsg, errMsg)
    Dim apiAddr, postData, resp, successStr
    apiAddr = BASE_URL & "/api/callback/script_result"
    If success Then
        successStr = "true"
    Else
        successStr = "false"
    End If
    postData = "order_token=" & g_order_token & "&success=" & successStr & "&result=" & resultMsg & "&error_msg=" & errMsg
    resp = Url.Post(apiAddr, postData)
End Function

// JSON解析辅助函数
Function JsonGetStr(jsonStr, key)
    Dim s, e, searchKey
    searchKey = Chr(34) & key & Chr(34)
    s = InStr(1, jsonStr, searchKey)
    If s = 0 Then
        JsonGetStr = ""
        Exit Function
    End If
    s = s + Len(searchKey)
    Do While Mid(jsonStr, s, 1) = ":" Or Mid(jsonStr, s, 1) = " "
        s = s + 1
    Loop
    If Mid(jsonStr, s, 1) = Chr(34) Then
        s = s + 1
        e = InStr(s, jsonStr, Chr(34))
        If e > s Then
            JsonGetStr = Mid(jsonStr, s, e - s)
        End If
    End If
End Function
`
</script>

<style scoped>
.api-doc {
  max-width: 960px;
}
.flow-steps {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}
.flow-step {
  display: flex;
  align-items: center;
  gap: 6px;
}
.step-num {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #409eff;
  color: #fff;
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.step-text {
  font-size: 13px;
  color: #303133;
  white-space: nowrap;
}
.step-arrow {
  color: #c0c4cc;
  font-size: 16px;
}
.api-path {
  font-size: 13px;
  background: #f4f4f5;
  padding: 2px 8px;
  border-radius: 4px;
  color: #303133;
}
.api-desc {
  color: #606266;
  font-size: 13px;
  line-height: 1.6;
}
.section-title {
  font-size: 13px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}
.code-block {
  background: #1e1e1e;
  color: #d4d4d4;
  padding: 16px;
  border-radius: 6px;
  font-size: 12px;
  line-height: 1.6;
  overflow-x: auto;
  white-space: pre;
  margin: 0;
}
</style>
