def order_to_dict(order: Order) -> dict:
    latest_cb = order.callbacks[-1] if order.callbacks else None
    # 使用前端地址构建完整链接
    frontend_url = settings.FRONTEND_URL
   return {
        "id": order.id,
        "order_no": order.order_no,
        "client_link": f"{frontend_url}/order/{order.token}",
        "token": order.token,
        "system_type": order.system_type,
        "image_path": order.image_path,
        "image_url": f"/uploads/orders/{os.path.basename(order.image_path)}" if order.image_path else None,
        "link_status": order.link_status,
        "exec_status": order.exec_status,
        "remark": order.remark,
        "created_at": order.created_at.strftime("%Y-%m-%d %H:%M:%S") if order.created_at else None,
        "submitted_at": order.submitted_at.strftime("%Y-%m-%d %H:%M:%S") if order.submitted_at else None,
        "qrcode_status": latest_cb.qrcode_status if latest_cb else None,
        "qrcode_url": f"/uploads/qrcodes/{os.path.basename(latest_cb.qrcode_path)}" if latest_cb and latest_cb.qrcode_path else None,
    }

