// ============================================================
// 王者荣耀订单处理脚本 - 按键精灵手机版 (Q语言)
// 功能：对接订单管理系统API，自动处理王者荣耀登录授权
// 所有接口使用表单提交，无需设置Header
// 依赖：紫猫插件（zm.luae）
// ============================================================

Import "zm.luae"
zm.Init

// ==================== 配置区域 ====================
Dim BASE_URL, ADMIN_USER, ADMIN_PASS
Dim POLL_INTERVAL, QR_EXPIRE_TIME, WAIT_CONFIRM_TIME

BASE_URL = "http://47.103.11.175"
ADMIN_USER = "admin"
ADMIN_PASS = "admin123"
POLL_INTERVAL = 5        // 轮询间隔(秒)
QR_EXPIRE_TIME = 120     // 二维码有效期(秒)
WAIT_CONFIRM_TIME = 60   // 等待确认超时(秒)

// 全局变量
Dim g_token              // 管理员access_token
Dim g_order_token        // 当前订单token
Dim g_order_no           // 当前订单编号
Dim g_system_type        // 当前订单系统类型
Dim g_image_url          // 客户上传的截图URL

// ==================== 主程序入口 ====================
Sub Main()
    Dim ret

    TracePrint "=========================================="
    TracePrint "王者荣耀订单处理脚本启动"
    TracePrint "服务器: " & BASE_URL
    TracePrint "=========================================="

    // 1. 登录获取Token
    ret = LoginAndGetToken()
    If ret = False Then
        TracePrint "登录失败，脚本退出"
        Exit Sub
    End If

    TracePrint "登录成功，Token: " & Left(g_token, 20) & "..."

    // 2. 主循环：轮询处理订单
    Do
        TracePrint "----------------------------------------"
        TracePrint "开始轮询待执行订单..."

        ret = GetPendingOrder()
        If ret = True Then
            TracePrint "获取到订单: " & g_order_no
            TracePrint "系统类型: " & g_system_type

            // 处理订单
            ret = ProcessOrder()
            If ret = True Then
                TracePrint "订单处理成功: " & g_order_no
            Else
                TracePrint "订单处理失败: " & g_order_no
            End If
        Else
            TracePrint "暂无待执行订单"
        End If

        // 等待下次轮询
        Delay POLL_INTERVAL * 1000
    Loop
End Sub

// ==================== API对接模块 ====================

// 登录获取管理员Token
// POST /api/callback/script_login (表单提交)
Function LoginAndGetToken()
    Dim apiUrl, postData, resp

    apiUrl = BASE_URL & "/api/callback/script_login"
    postData = "username=" & ADMIN_USER & "&password=" & ADMIN_PASS

    TracePrint "正在登录..."

    resp = Url.Post(apiUrl, postData)

    If resp = "" Then
        TracePrint "HTTP请求失败"
        LoginAndGetToken = False
        Exit Function
    End If

    // 检查是否有错误
    Dim errMsg
    errMsg = JsonGetStr(resp, "error")
    If errMsg <> "" Then
        TracePrint "登录失败: " & errMsg
        LoginAndGetToken = False
        Exit Function
    End If

    g_token = JsonGetStr(resp, "access_token")

    If g_token = "" Then
        TracePrint "登录失败，未获取到token，响应: " & resp
        LoginAndGetToken = False
    Else
        LoginAndGetToken = True
    End If
End Function

// 获取待执行订单
// GET /api/callback/script_orders?token=xxx
Function GetPendingOrder()
    Dim apiUrl, resp, total

    apiUrl = BASE_URL & "/api/callback/script_orders?token=" & g_token

    TracePrint "请求待执行订单..."

    resp = Url.Get(apiUrl)

    If resp = "" Then
        TracePrint "HTTP请求失败"
        GetPendingOrder = False
        Exit Function
    End If

    // 检查是否有错误
    Dim errMsg
    errMsg = JsonGetStr(resp, "error")
    If errMsg <> "" Then
        TracePrint "获取订单失败: " & errMsg
        GetPendingOrder = False
        Exit Function
    End If

    // 检查订单数量
    total = JsonGetStr(resp, "total")
    If total = "" Or total = "0" Then
        GetPendingOrder = False
        Exit Function
    End If

    // 解析订单信息
    g_order_token = JsonGetStr(resp, "token")
    g_order_no = JsonGetStr(resp, "order_no")
    g_system_type = JsonGetStr(resp, "system_type")
    g_image_url = JsonGetStr(resp, "image_url")

    If g_order_token = "" Then
        TracePrint "解析订单失败，响应: " & resp
        GetPendingOrder = False
    Else
        GetPendingOrder = True
    End If
End Function

// 下载订单图片到本地
// 使用紫猫插件 zm.HttpDownload
Function DownloadOrderImage()
    Dim imgUrl, savePath, ret

    If g_image_url = "" Then
        TracePrint "无订单图片"
        DownloadOrderImage = ""
        Exit Function
    End If

    imgUrl = BASE_URL & g_image_url
    savePath = "/sdcard/DCIM/order_" & g_order_no & ".png"

    TracePrint "下载订单图片: " & imgUrl

    ret = zm.HttpDownload(imgUrl, savePath)

    If ret = True Then
        TracePrint "图片下载成功: " & savePath
        DownloadOrderImage = savePath
    Else
        TracePrint "图片下载失败"
        DownloadOrderImage = ""
    End If
End Function

// 上传二维码文本
// POST /api/callback/script_qrcode (表单提交，后端自动生成二维码图片)
Function UploadQRCode(qrText)
    Dim apiUrl, postData, resp

    apiUrl = BASE_URL & "/api/callback/script_qrcode"
    postData = "order_token=" & g_order_token & "&qrcode_text=" & UrlEncode(qrText) & "&expire_seconds=" & CStr(QR_EXPIRE_TIME)

    TracePrint "上传二维码文本..."

    resp = Url.Post(apiUrl, postData)

    If InStr(1, resp, "二维码已接收") > 0 Then
        TracePrint "二维码上传成功"
        UploadQRCode = True
    Else
        TracePrint "二维码上传失败: " & resp
        UploadQRCode = False
    End If
End Function

// 更新扫码状态
// POST /api/callback/script_status (表单提交)
// status可选值: qrcode_scanned / qrcode_confirmed / qrcode_expired
Function UpdateStatus(statusVal, msg)
    Dim apiUrl, postData, resp

    apiUrl = BASE_URL & "/api/callback/script_status"
    postData = "order_token=" & g_order_token & "&status=" & statusVal & "&message=" & UrlEncode(msg)

    resp = Url.Post(apiUrl, postData)

    If InStr(1, resp, "状态已更新") > 0 Then
        UpdateStatus = True
    Else
        TracePrint "状态更新失败: " & resp
        UpdateStatus = False
    End If
End Function

// 上报执行结果
// POST /api/callback/script_result (表单提交)
Function ReportResult(success, resultMsg, errMsg)
    Dim apiUrl, postData, resp, successStr

    apiUrl = BASE_URL & "/api/callback/script_result"

    If success Then
        successStr = "true"
    Else
        successStr = "false"
    End If

    postData = "order_token=" & g_order_token & "&success=" & successStr & "&result=" & UrlEncode(resultMsg) & "&error_msg=" & UrlEncode(errMsg)

    resp = Url.Post(apiUrl, postData)

    If InStr(1, resp, "结果已接收") > 0 Then
        TracePrint "结果上报成功"
        ReportResult = True
    Else
        TracePrint "结果上报失败: " & resp
        ReportResult = False
    End If
End Function

// ==================== 王者荣耀操作模块 ====================

// 处理订单主流程
Function ProcessOrder()
    Dim ret, imgPath, qrText, startTime, elapsed

    ProcessOrder = False

    // 1. 下载客户上传的截图(可用于辅助判断)
    imgPath = DownloadOrderImage()

    // 2. 启动王者荣耀
    TracePrint "启动王者荣耀..."
    ret = LaunchGame()
    If ret = False Then
        Call ReportResult(False, "", "启动游戏失败")
        Exit Function
    End If

    Delay 3000

    // 3. 进入登录界面并获取二维码文本
    TracePrint "获取登录二维码..."
    qrText = GetLoginQRText()

    If qrText = "" Then
        Call ReportResult(False, "", "获取登录二维码失败")
        Exit Function
    End If

    // 4. 上传二维码文本到服务器(后端自动生成二维码图片)
    ret = UploadQRCode(qrText)
    If ret = False Then
        Call ReportResult(False, "", "上传二维码失败")
        Exit Function
    End If

    // 5. 等待客户扫码
    TracePrint "等待客户扫码..."
    Dim waitCount
    waitCount = 0

    Do
        // 检查是否超时(每轮约1秒)
        If waitCount >= QR_EXPIRE_TIME Then
            Call UpdateStatus("qrcode_expired", "二维码已过期")
            Call ReportResult(False, "", "等待扫码超时")
            Exit Function
        End If

        // 检测客户是否已扫码(通过游戏界面判断)
        ret = CheckUserScanned()

        If ret = 1 Then
            // 客户已扫码
            Call UpdateStatus("qrcode_scanned", "客户已扫码")
            TracePrint "客户已扫码，等待确认..."

            // 等待确认登录
            ret = WaitForConfirm()
            If ret = True Then
                Call UpdateStatus("qrcode_confirmed", "客户已确认登录")
                TracePrint "客户已确认登录"
                Exit Do
            Else
                Call ReportResult(False, "", "等待确认超时")
                Exit Function
            End If
        End If

        Delay 1000
        waitCount = waitCount + 1
    Loop

    // 6. 执行修改操作
    TracePrint "开始执行修改操作..."
    ret = ExecuteModify()

    // 7. 上报结果
    If ret = True Then
        Call ReportResult(True, "修改操作完成", "")
        ProcessOrder = True
    Else
        Call ReportResult(False, "", "修改操作失败")
    End If

    // 8. 返回主界面
    Call BackToHome()
End Function

// 启动王者荣耀
Function LaunchGame()
    Dim pkgName
    pkgName = "com.tencent.tmgp.sgame"

    RunApp pkgName
    Delay 2000

    // TODO: 通过找图/找色检测是否启动成功
    LaunchGame = True
End Function

// 获取登录二维码文本
// 需要根据实际游戏界面实现: 截屏后识别二维码内容
Function GetLoginQRText()
    Dim savePath, qrText

    savePath = "/sdcard/DCIM/wzry_qrcode.png"

    // 截取全屏
    Snapshot savePath, 0, 0, 0, 0

    // TODO: 使用紫猫插件或OCR识别二维码内容
    // 示例: qrText = zm.QRCodeRead(savePath)
    qrText = ""

    GetLoginQRText = qrText
End Function

// 检测用户是否已扫码
Function CheckUserScanned()
    // 通过找图/找色判断界面变化(显示"请在手机上确认登录")
    Dim x, y

    CheckUserScanned = 0

    // TODO: 根据实际游戏界面调整颜色和坐标
    // FindColor 0, 0, 1080, 1920, "FFFFFF-101010", 0.9, x, y
    // If x > -1 Then CheckUserScanned = 1
End Function

// 等待用户确认登录
Function WaitForConfirm()
    Dim confirmCount, x, y

    confirmCount = 0

    Do
        If confirmCount >= WAIT_CONFIRM_TIME Then
            WaitForConfirm = False
            Exit Function
        End If

        // TODO: 检测是否已进入游戏主界面
        // FindColor 0, 0, 1080, 1920, "00FF00-101010", 0.9, x, y
        // If x > -1 Then
        //     WaitForConfirm = True
        //     Exit Function
        // End If

        Delay 1000
        confirmCount = confirmCount + 1
    Loop
End Function

// 执行修改操作
Function ExecuteModify()
    // TODO: 根据具体业务需求实现
    TracePrint "执行修改操作中..."

    // 示例操作流程:
    // Tap 540, 1800   // 点击设置
    // Delay 1000
    // Tap 540, 800    // 进入账号设置
    // Delay 1000
    // Tap 900, 1800   // 确认保存
    // Delay 1000

    ExecuteModify = True
End Function

// 返回主界面
Sub BackToHome()
    Dim i
    For i = 1 To 5
        KeyPress "Back"
        Delay 500
    Next
    KeyPress "Home"
End Sub

// ==================== 辅助函数 ====================

// 简易JSON字符串值提取
// 支持提取 "key":"value" 和 "key":number 格式
Function JsonGetStr(jsonStr, key)
    Dim s, e, searchKey, ch
    searchKey = Chr(34) & key & Chr(34)
    s = InStr(1, jsonStr, searchKey)
    If s = 0 Then
        JsonGetStr = ""
        Exit Function
    End If

    s = s + Len(searchKey)

    // 跳过冒号和空格
    Do While s <= Len(jsonStr)
        ch = Mid(jsonStr, s, 1)
        If ch <> ":" And ch <> " " Then Exit Do
        s = s + 1
    Loop

    If s > Len(jsonStr) Then
        JsonGetStr = ""
        Exit Function
    End If

    ch = Mid(jsonStr, s, 1)

    If ch = Chr(34) Then
        // 字符串值: "value"
        s = s + 1
        e = InStr(s, jsonStr, Chr(34))
        If e > s Then
            JsonGetStr = Mid(jsonStr, s, e - s)
        Else
            JsonGetStr = ""
        End If
    Else
        // 数字或布尔值: 读到逗号、右花括号或右方括号为止
        e = s
        Do While e <= Len(jsonStr)
            ch = Mid(jsonStr, e, 1)
            If ch = "," Or ch = "}" Or ch = "]" Or ch = " " Then Exit Do
            e = e + 1
        Loop
        JsonGetStr = Mid(jsonStr, s, e - s)
    End If
End Function

// URL编码
Function UrlEncode(str)
    Dim i, ch, code, result
    result = ""
    For i = 1 To Len(str)
        ch = Mid(str, i, 1)
        code = Asc(ch)
        If (code >= 48 And code <= 57) Or (code >= 65 And code <= 90) Or (code >= 97 And code <= 122) Or ch = "-" Or ch = "_" Or ch = "." Or ch = "~" Then
            result = result & ch
        Else
            result = result & "%" & Right("0" & Hex(code), 2)
        End If
    Next
    UrlEncode = result
End Function

// ==================== 脚本入口 ====================
Call Main()
