import uuid
import os
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from models import get_db, Order, ExecLog, ScriptCallback, SystemType, LinkStatus, ExecStatus
from config import settings
import aiofiles

router = APIRouter(prefix="/api/client", tags=["Client"])

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp"}


@router.get("/order/{token}")
def get_order_by_token(token: str, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.token == token).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.link_status in [LinkStatus.disabled, LinkStatus.expired]:
        raise HTTPException(status_code=403, detail="Link disabled/expired")
    return {
        "order_no": order.order_no,
        "link_status": order.link_status,
        "exec_status": order.exec_status,
        "system_type": order.system_type,
        "already_submitted": order.link_status == LinkStatus.submitted,
    }


@router.get("/order/{token}/status")
def get_order_status(token: str, db: Session = Depends(get_db)):
    """轮询查询订单执行状态（WebSocket 降级备用）"""
    order = db.query(Order).filter(Order.token == token).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    result = {
        "exec_status": order.exec_status,
        "qrcode_url": None,
        "qrcode_status": None,
        "qrcode_expired_at": None,
        "result": None,
        "error_msg": None,
    }

    latest_cb = db.query(ScriptCallback).filter(
        ScriptCallback.order_id == order.id
    ).order_by(ScriptCallback.id.desc()).first()

    if latest_cb:
        result["qrcode_url"] = f"/uploads/qrcodes/{os.path.basename(latest_cb.qrcode_path)}" if latest_cb.qrcode_path else None
        result["qrcode_status"] = latest_cb.qrcode_status
        result["qrcode_expired_at"] = latest_cb.qrcode_expired_at.strftime("%Y-%m-%d %H:%M:%S") if latest_cb.qrcode_expired_at else None
        result["result"] = latest_cb.result
        result["error_msg"] = latest_cb.error_msg

    return result


@router.post("/order/{token}/submit")
async def submit_order(
    token: str,
    system_type: SystemType = Form(...),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    order = db.query(Order).filter(Order.token == token).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.link_status in [LinkStatus.disabled, LinkStatus.expired]:
        raise HTTPException(status_code=403, detail="Link disabled/expired")
    # 执行中不允许重新提交
    if order.exec_status == ExecStatus.running:
        raise HTTPException(status_code=400, detail="Order already in execution")

    ext = os.path.splitext(image.filename)[1].lower() if image.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Invalid format")

    content = await image.read()
    if len(content) > settings.MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Too large")

    file_name = f"{uuid.uuid4().hex}{ext}"
    save_path = os.path.join(settings.UPLOAD_DIR, "orders", file_name)
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    async with aiofiles.open(save_path, "wb") as f:
        await f.write(content)

    order.system_type = system_type
    order.image_path = save_path
    order.link_status = LinkStatus.submitted
    order.exec_status = ExecStatus.pending
    order.submitted_at = datetime.now()

    db.add(ExecLog(order_id=order.id, log_content=f"客户提交: {system_type}"))
    db.commit()

    return {"message": "Success", "order_no": order.order_no}


@router.post("/order/{token}/refresh-qrcode")
def refresh_qrcode(token: str, db: Session = Depends(get_db)):
    """用户请求刷新二维码 - 将当前二维码状态设为过期，触发脚本重新生成"""
    order = db.query(Order).filter(Order.token == token).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.exec_status != ExecStatus.running:
        raise HTTPException(status_code=400, detail="Order not in execution")

    # 查找最新的回调记录，将二维码状态设为过期
    latest_cb = db.query(ScriptCallback).filter(
        ScriptCallback.order_id == order.id
    ).order_by(ScriptCallback.id.desc()).first()

    if latest_cb and latest_cb.qrcode_status == "pending":
        latest_cb.qrcode_status = "expired"
        latest_cb.qrcode_expired_at = datetime.now()
        db.add(ExecLog(order_id=order.id, log_content="用户手动刷新二维码"))
        db.commit()
        return {"message": "二维码已标记为过期，系统将重新生成"}

    return {"message": "当前无可刷新的二维码"}
