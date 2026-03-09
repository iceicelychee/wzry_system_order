$content = Get-Content "api/order.py" -Raw -Encoding UTF8
$content= $content -replace '\{base_url\}/order/\{order\.token\}', '{settings.FRONTEND_URL}/order/{order.token}'
Set-Content"api/order.py" $value $content -Encoding UTF8 -NoNewline
Write-Host "修改成功"
