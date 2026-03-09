$loginResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/auth/login" -Method POST -ContentType "application/x-www-form-urlencoded" -Body "username=admin&password=admin123"
$token = $loginResponse.access_token
$headers = @{ Authorization = "Bearer $token" }
$orders = Invoke-RestMethod -Uri "http://localhost:8000/api/order/list?page=1" -Method GET -Headers $headers
Write-Host "订单链接：" $orders.list[0].client_link
