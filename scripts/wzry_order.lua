-- ============================================================
-- 王者荣耀订单处理脚本 - 按键精灵手机助手 (Lua语言)
-- 功能：对接订单管理系统API，自动处理王者荣耀登录授权
-- 所有接口使用表单提交，无需设置Header
-- 依赖：紫猫插件（zm.luae）
-- ============================================================

require "zm"
zm.Init()

-- ==================== 配置区域 ====================
local CONFIG = {
    BASE_URL = "http://47.103.11.175",
    ADMIN_USER = "admin",
    ADMIN_PASS = "admin123",
    POLL_INTERVAL = 5,        -- 轮询间隔(秒)
    QR_EXPIRE_TIME = 120,     -- 二维码有效期(秒)
    WAIT_CONFIRM_TIME = 60,   -- 等待确认超时(秒)
}

-- 全局状态
local g_token = nil           -- 管理员access_token
local g_order_token = nil     -- 当前订单token
local g_order_no = nil        -- 当前订单编号
local g_system_type = nil     -- 当前订单系统类型
local g_image_url = nil       -- 客户上传的截图URL

-- ==================== 辅助函数 ====================

-- 简易JSON字符串值提取: 支持 "key":"value" 和 "key":number
local function jsonGetStr(jsonStr, key)
    if not jsonStr or jsonStr == "" then return "" end

    local searchKey = '"' .. key .. '"'
    local s = string.find(jsonStr, searchKey, 1, true)
    if not s then return "" end

    s = s + #searchKey

    -- 跳过冒号和空格
    while s <= #jsonStr do
        local ch = string.sub(jsonStr, s, s)
        if ch ~= ":" and ch ~= " " then break end
        s = s + 1
    end

    if s > #jsonStr then return "" end

    local ch = string.sub(jsonStr, s, s)

    if ch == '"' then
        -- 字符串值
        s = s + 1
        local e = string.find(jsonStr, '"', s, true)
        if e and e > s then
            return string.sub(jsonStr, s, e - 1)
        end
        return ""
    else
        -- 数字/布尔值: 读到逗号、}、]或空格为止
        local e = s
        while e <= #jsonStr do
            local c = string.sub(jsonStr, e, e)
            if c == "," or c == "}" or c == "]" or c == " " then break end
            e = e + 1
        end
        return string.sub(jsonStr, s, e - 1)
    end
end

-- URL编码
local function urlEncode(str)
    if not str then return "" end
    str = string.gsub(str, "([^%w%-%.%_%~])", function(c)
        return string.format("%%%02X", string.byte(c))
    end)
    return str
end

-- ==================== API对接模块 ====================

-- 登录获取管理员Token
-- POST /api/callback/script_login (表单提交)
local function loginAndGetToken()
    local apiUrl = CONFIG.BASE_URL .. "/api/callback/script_login"
    local postData = "username=" .. CONFIG.ADMIN_USER .. "&password=" .. CONFIG.ADMIN_PASS

    print("正在登录...")

    local resp = Url.Post(apiUrl, postData)

    if not resp or resp == "" then
        print("HTTP请求失败")
        return false
    end

    -- 检查是否有错误
    local errMsg = jsonGetStr(resp, "error")
    if errMsg ~= "" then
        print("登录失败: " .. errMsg)
        return false
    end

    g_token = jsonGetStr(resp, "access_token")

    if g_token == "" then
        print("登录失败，未获取到token，响应: " .. resp)
        return false
    end

    return true
end

-- 获取待执行订单
-- GET /api/callback/script_orders?token=xxx
local function getPendingOrder()
    local apiUrl = CONFIG.BASE_URL .. "/api/callback/script_orders?token=" .. g_token

    print("请求待执行订单...")

    local resp = Url.Get(apiUrl)

    if not resp or resp == "" then
        print("HTTP请求失败")
        return false
    end

    -- 检查是否有错误
    local errMsg = jsonGetStr(resp, "error")
    if errMsg ~= "" then
        print("获取订单失败: " .. errMsg)
        return false
    end

    -- 检查订单数量
    local total = jsonGetStr(resp, "total")
    if total == "" or total == "0" then
        return false
    end

    -- 解析订单信息
    g_order_token = jsonGetStr(resp, "token")
    g_order_no = jsonGetStr(resp, "order_no")
    g_system_type = jsonGetStr(resp, "system_type")
    g_image_url = jsonGetStr(resp, "image_url")

    if not g_order_token or g_order_token == "" then
        print("解析订单失败，响应: " .. resp)
        return false
    end

    return true
end

-- 下载订单图片到本地
-- 使用紫猫插件 zm.HttpDownload
local function downloadOrderImage()
    if not g_image_url or g_image_url == "" then
        print("无订单图片")
        return nil
    end

    local imgUrl = CONFIG.BASE_URL .. g_image_url
    local savePath = "/sdcard/DCIM/order_" .. g_order_no .. ".png"

    print("下载订单图片: " .. imgUrl)

    local ret = zm.HttpDownload(imgUrl, savePath)

    if ret then
        print("图片下载成功: " .. savePath)
        return savePath
    else
        print("图片下载失败")
        return nil
    end
end

-- 上传二维码文本
-- POST /api/callback/script_qrcode (表单提交，后端自动生成二维码图片)
local function uploadQRCode(qrText)
    local apiUrl = CONFIG.BASE_URL .. "/api/callback/script_qrcode"
    local postData = "order_token=" .. g_order_token
        .. "&qrcode_text=" .. urlEncode(qrText)
        .. "&expire_seconds=" .. tostring(CONFIG.QR_EXPIRE_TIME)

    print("上传二维码文本...")

    local resp = Url.Post(apiUrl, postData)

    if resp and string.find(resp, "二维码已接收", 1, true) then
        print("二维码上传成功")
        return true
    else
        print("二维码上传失败: " .. tostring(resp))
        return false
    end
end

-- 更新扫码状态
-- POST /api/callback/script_status (表单提交)
-- statusVal可选: qrcode_scanned / qrcode_confirmed / qrcode_expired
local function updateStatus(statusVal, msg)
    local apiUrl = CONFIG.BASE_URL .. "/api/callback/script_status"
    local postData = "order_token=" .. g_order_token
        .. "&status=" .. statusVal
        .. "&message=" .. urlEncode(msg or "")

    local resp = Url.Post(apiUrl, postData)

    if resp and string.find(resp, "状态已更新", 1, true) then
        return true
    else
        print("状态更新失败: " .. tostring(resp))
        return false
    end
end

-- 上报执行结果
-- POST /api/callback/script_result (表单提交)
local function reportResult(success, resultMsg, errMsg)
    local apiUrl = CONFIG.BASE_URL .. "/api/callback/script_result"
    local successStr = success and "true" or "false"
    local postData = "order_token=" .. g_order_token
        .. "&success=" .. successStr
        .. "&result=" .. urlEncode(resultMsg or "")
        .. "&error_msg=" .. urlEncode(errMsg or "")

    local resp = Url.Post(apiUrl, postData)

    if resp and string.find(resp, "结果已接收", 1, true) then
        print("结果上报成功")
        return true
    else
        print("结果上报失败: " .. tostring(resp))
        return false
    end
end

-- ==================== 王者荣耀操作模块 ====================

-- 启动王者荣耀
local function launchGame()
    local pkgName = "com.tencent.tmgp.sgame"
    runApp(pkgName)
    mSleep(2000)
    -- TODO: 通过找图/找色检测是否启动成功
    return true
end

-- 获取登录二维码文本
-- 需要根据实际游戏界面实现: 截屏后识别二维码内容
local function getLoginQRText()
    local savePath = "/sdcard/DCIM/wzry_qrcode.png"

    -- 截取全屏
    snapshot(savePath, 0, 0, 0, 0)

    -- TODO: 使用紫猫插件或OCR识别二维码内容
    -- 示例: local qrText = zm.QRCodeRead(savePath)
    local qrText = ""

    return qrText
end

-- 检测用户是否已扫码
local function checkUserScanned()
    -- 通过找图/找色判断界面变化(显示"请在手机上确认登录")
    -- TODO: 根据实际游戏界面调整颜色和坐标
    -- local x, y = findColor(0, 0, 1080, 1920, "FFFFFF-101010", 0.9)
    -- if x ~= -1 then return 1 end
    return 0
end

-- 等待用户确认登录
local function waitForConfirm()
    local startTime = os.clock()

    while true do
        local elapsed = os.clock() - startTime

        if elapsed > CONFIG.WAIT_CONFIRM_TIME then
            return false
        end

        -- TODO: 检测是否已进入游戏主界面
        -- local x, y = findColor(0, 0, 1080, 1920, "00FF00-101010", 0.9)
        -- if x ~= -1 then return true end

        mSleep(1000)
    end
end

-- 执行修改操作
local function executeModify()
    -- TODO: 根据具体业务需求实现
    print("执行修改操作中...")

    -- 示例操作流程:
    -- tap(540, 1800)   -- 点击设置
    -- mSleep(1000)
    -- tap(540, 800)    -- 进入账号设置
    -- mSleep(1000)
    -- tap(900, 1800)   -- 确认保存
    -- mSleep(1000)

    return true
end

-- 返回主界面
local function backToHome()
    for i = 1, 5 do
        keycode("KEYCODE_BACK")
        mSleep(500)
    end
    keycode("KEYCODE_HOME")
end

-- 处理订单主流程
local function processOrder()
    -- 1. 下载客户上传的截图(可用于辅助判断)
    local imgPath = downloadOrderImage()

    -- 2. 启动王者荣耀
    print("启动王者荣耀...")
    if not launchGame() then
        reportResult(false, nil, "启动游戏失败")
        return false
    end

    mSleep(3000)

    -- 3. 获取登录二维码文本
    print("获取登录二维码...")
    local qrText = getLoginQRText()

    if not qrText or qrText == "" then
        reportResult(false, nil, "获取登录二维码失败")
        return false
    end

    -- 4. 上传二维码文本到服务器(后端自动生成二维码图片)
    if not uploadQRCode(qrText) then
        reportResult(false, nil, "上传二维码失败")
        return false
    end

    -- 5. 等待客户扫码
    print("等待客户扫码...")
    local startTime = os.clock()

    while true do
        local elapsed = os.clock() - startTime

        -- 检查超时
        if elapsed > CONFIG.QR_EXPIRE_TIME then
            updateStatus("qrcode_expired", "二维码已过期")
            reportResult(false, nil, "等待扫码超时")
            return false
        end

        -- 检测客户是否已扫码
        local scanStatus = checkUserScanned()

        if scanStatus == 1 then
            updateStatus("qrcode_scanned", "客户已扫码")
            print("客户已扫码，等待确认...")

            if waitForConfirm() then
                updateStatus("qrcode_confirmed", "客户已确认登录")
                print("客户已确认登录")
                break
            else
                reportResult(false, nil, "等待确认超时")
                return false
            end
        end

        mSleep(1000)
    end

    -- 6. 执行修改操作
    print("开始执行修改操作...")
    local modifySuccess = executeModify()

    -- 7. 上报结果
    if modifySuccess then
        reportResult(true, "修改操作完成", nil)
    else
        reportResult(false, nil, "修改操作失败")
    end

    -- 8. 返回主界面
    backToHome()

    return modifySuccess
end

-- ==================== 主程序入口 ====================
local function main()
    print("==========================================")
    print("王者荣耀订单处理脚本启动")
    print("服务器: " .. CONFIG.BASE_URL)
    print("==========================================")

    -- 1. 登录获取Token
    if not loginAndGetToken() then
        print("登录失败，脚本退出")
        return
    end

    print("登录成功，Token: " .. string.sub(g_token, 1, 20) .. "...")

    -- 2. 主循环：轮询处理订单
    while true do
        print("----------------------------------------")
        print("开始轮询待执行订单...")

        local hasOrder = getPendingOrder()
        if hasOrder then
            print("获取到订单: " .. g_order_no)
            print("系统类型: " .. g_system_type)

            local success = processOrder()
            if success then
                print("订单处理成功: " .. g_order_no)
            else
                print("订单处理失败: " .. g_order_no)
            end
        else
            print("暂无待执行订单")
        end

        -- 等待下次轮询
        mSleep(CONFIG.POLL_INTERVAL * 1000)
    end
end

-- ==================== 脚本入口 ====================
main()
