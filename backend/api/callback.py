import uuid
import os
import io
import base64
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel
import qrcode

from models import get_db, Order, ScriptCallback, ExecLog, LinkStatus, ExecStatus, QrcodeStatus
from config import settings
import aiofiles

router = APIRouter(prefix="/api/callback", tags=["脚本回调"])

# WebSocket 连接管理
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, token: str, websocket: WebSocket):
        await websocket.accept()
        if token not in self.active_connections:
            self.active_connections[token] = []
        self.active_connections[token].append(websocket)

    def disconnect(self, token: str, websocket: WebSocket):
        if token in self.active_connections:
            self.active_connections[token].remove(websocket)

    async def send_to_order(self, token: str, data: dict):
        if token in self.active_connections:
            dead = []
            for ws in self.active_connections[token]:
                try:
                    await ws.send_json(data)
                except Exception:
                    dead.append(ws)
            for ws in dead:
                self.active_connections[token].remove(ws)


manager = ConnectionManager()


@router.websocket("/ws/{token}")
async def websocket_endpoint(token: str, websocket: WebSocket, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.token == token).first()
    if not order:
        await websocket.close(code=4004)
        return
    await manager.connect(token, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(token, websocket)


class StatusUpdate(BaseModel):
    order_token: str
    status: str
    message: Optional[str] = None


class ResultUpdate(BaseModel):
    order_token: str
    success: bool
    result: Optional[str] = None
    error_msg: Optional[str] = None


@router.post("/qrcode")
async def receive_qrcode(
    order_token: str = Form(...),
    expire_seconds: int = Form(120),
    qrcode: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """脚本回传二维码图片"""
    order = db.query(Order).filter(Order.token == order_token).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    ext = os.path.splitext(qrcode.filename)[1].lower() if qrcode.filename else ".png"
    file_name = f"{uuid.uuid4().hex}{ext}"
    save_path = os.path.join(settings.UPLOAD_DIR, "qrcodes", file_name)
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    async with aiofiles.open(save_path, "wb") as f:
        await f.write(await qrcode.read())

    expired_at = datetime.now() + timedelta(seconds=expire_seconds)
    cb = ScriptCallback(
        order_id=order.id,
        qrcode_path=save_path,
        qrcode_status=QrcodeStatus.waiting,
        qrcode_expired_at=expired_at,
    )
    db.add(cb)
    order.exec_status = ExecStatus.running
    db.add(ExecLog(order_id=order.id, log_content="脚本已返回登录二维码，等待客户扫码"))
    db.commit()
    db.refresh(cb)

    await manager.send_to_order(order_token, {
        "type": "qrcode",
        "qrcode_url": f"/uploads/qrcodes/{file_name}",
        "expire_seconds": expire_seconds,
        "expired_at": expired_at.strftime("%Y-%m-%d %H:%M:%S"),
    })

    return {"message": "二维码已接收"}


class QrcodeBase64(BaseModel):
    order_token: str
    qrcode_base64: str
    expire_seconds: int = 120


@router.post("/qrcode_base64")
async def receive_qrcode_base64(req: QrcodeBase64, db: Session = Depends(get_db)):
    """脚本回传二维码图片(base64编码)"""
    order = db.query(Order).filter(Order.token == req.order_token).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    try:
        img_data = base64.b64decode(req.qrcode_base64)
    except Exception:
        raise HTTPException(status_code=400, detail="base64解码失败")

    file_name = f"{uuid.uuid4().hex}.png"
    save_path = os.path.join(settings.UPLOAD_DIR, "qrcodes", file_name)
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    async with aiofiles.open(save_path, "wb") as f:
        await f.write(img_data)

    expired_at = datetime.now() + timedelta(seconds=req.expire_seconds)
    cb = ScriptCallback(
        order_id=order.id,
        qrcode_path=save_path,
        qrcode_status=QrcodeStatus.waiting,
        qrcode_expired_at=expired_at,
    )
    db.add(cb)
    order.exec_status = ExecStatus.running
    db.add(ExecLog(order_id=order.id, log_content="脚本已返回登录二维码，等待客户扫码"))
    db.commit()
    db.refresh(cb)

    await manager.send_to_order(req.order_token, {
        "type": "qrcode",
        "qrcode_url": f"/uploads/qrcodes/{file_name}",
        "expire_seconds": req.expire_seconds,
        "expired_at": expired_at.strftime("%Y-%m-%d %H:%M:%S"),
    })

    return {"message": "二维码已接收"}


@router.post("/status")
async def update_status(req: StatusUpdate, db: Session = Depends(get_db)):
    """脚本更新执行状态"""
    order = db.query(Order).filter(Order.token == req.order_token).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    status_map = {
        "qrcode_scanned": QrcodeStatus.scanned,
        "qrcode_confirmed": QrcodeStatus.confirmed,
        "qrcode_expired": QrcodeStatus.expired,
    }
    if req.status in status_map and order.callbacks:
        latest_cb = order.callbacks[-1]
        latest_cb.qrcode_status = status_map[req.status]

    db.add(ExecLog(order_id=order.id, log_content=req.message or req.status))
    db.commit()

    await manager.send_to_order(req.order_token, {
        "type": "status",
        "status": req.status,
        "message": req.message,
    })

    return {"message": "状态已更新"}


@router.post("/result")
async def receive_result(req: ResultUpdate, db: Session = Depends(get_db)):
    """脚本回传执行结果"""
    order = db.query(Order).filter(Order.token == req.order_token).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    order.exec_status = ExecStatus.success if req.success else ExecStatus.failed

    if order.callbacks:
        latest_cb = order.callbacks[-1]
        latest_cb.result = req.result
        latest_cb.error_msg = req.error_msg

    log_msg = f"执行{'成功' if req.success else '失败'}: {req.result or req.error_msg or ''}"
    db.add(ExecLog(order_id=order.id, log_content=log_msg))
    db.commit()

    await manager.send_to_order(req.order_token, {
        "type": "result",
        "success": req.success,
        "result": req.result,
        "error_msg": req.error_msg,
    })

    return {"message": "结果已接收"}


class QrcodeText(BaseModel):
    order_token: str
    qrcode_text: str
    expire_seconds: int = 120


@router.post("/qrcode_text")
async def receive_qrcode_text(req: QrcodeText, db: Session = Depends(get_db)):
    """脚本回传二维码文本内容，后端生成二维码图片"""
    order = db.query(Order).filter(Order.token == req.order_token).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    if not req.qrcode_text.strip():
        raise HTTPException(status_code=400, detail="二维码文本为空")

    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(req.qrcode_text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    img_data = buf.getvalue()

    file_name = f"{uuid.uuid4().hex}.png"
    save_path = os.path.join(settings.UPLOAD_DIR, "qrcodes", file_name)
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    async with aiofiles.open(save_path, "wb") as f:
        await f.write(img_data)

    expired_at = datetime.now() + timedelta(seconds=req.expire_seconds)
    cb = ScriptCallback(
        order_id=order.id,
        qrcode_path=save_path,
        qrcode_status=QrcodeStatus.waiting,
        qrcode_expired_at=expired_at,
    )
    db.add(cb)
    order.exec_status = ExecStatus.running
    db.add(ExecLog(order_id=order.id, log_content="脚本已返回登录二维码，等待客户扫码"))
    db.commit()
    db.refresh(cb)

    await manager.send_to_order(req.order_token, {
        "type": "qrcode",
        "qrcode_url": f"/uploads/qrcodes/{file_name}",
        "expire_seconds": req.expire_seconds,
        "expired_at": expired_at.strftime("%Y-%m-%d %H:%M:%S"),
    })

    return {"message": "二维码已接收"}


# ==================== 脚本专用接口(纯表单+URL参数，无需自定义Header) ====================

@router.post("/script_login")
def script_login(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    """脚本专用登录(表单提交)"""
    from models import Admin
    from services.auth import verify_password, create_access_token
    admin = db.query(Admin).filter(Admin.username == username).first()
    if not admin or not verify_password(password, admin.password):
        return {"error": "账号或密码错误", "access_token": ""}
    token = create_access_token({"sub": admin.username, "role": "admin"})
    return {"access_token": token, "username": admin.username}


@router.get("/script_orders")
def script_get_orders(token: str, db: Session = Depends(get_db)):
    """脚本专用获取待执行订单(token通过URL参数传递)"""
    from jose import JWTError, jwt as jose_jwt
    try:
        jose_jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except (JWTError, Exception):
        return {"error": "token无效", "total": 0}

    orders = db.query(Order).filter(
        Order.exec_status == ExecStatus.pending
    ).order_by(Order.id.asc()).limit(1).all()
    if not orders:
        return {"total": 0}

    o = orders[0]
    image_url = ""
    if o.image_path:
        image_url = f"/uploads/orders/{os.path.basename(o.image_path)}"
    return {
        "total": 1,
        "order_no": o.order_no,
        "token": o.token,
        "system_type": o.system_type or "",
        "image_url": image_url,
    }


@router.post("/script_qrcode")
async def script_upload_qrcode(
    order_token: str = Form(...),
    qrcode_text: str = Form(...),
    expire_seconds: int = Form(120),
    db: Session = Depends(get_db),
):
    """脚本专用上传二维码文本(纯表单)"""
    order = db.query(Order).filter(Order.token == order_token).first()
    if not order:
        return {"error": "订单不存在"}

    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(qrcode_text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    img_data = buf.getvalue()

    file_name = f"{uuid.uuid4().hex}.png"
    save_path = os.path.join(settings.UPLOAD_DIR, "qrcodes", file_name)
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    async with aiofiles.open(save_path, "wb") as f:
        await f.write(img_data)

    expired_at = datetime.now() + timedelta(seconds=expire_seconds)
    cb = ScriptCallback(
        order_id=order.id,
        qrcode_path=save_path,
        qrcode_status=QrcodeStatus.waiting,
        qrcode_expired_at=expired_at,
    )
    db.add(cb)
    order.exec_status = ExecStatus.running
    db.add(ExecLog(order_id=order.id, log_content="脚本已返回登录二维码，等待客户扫码"))
    db.commit()
    db.refresh(cb)

    await manager.send_to_order(order_token, {
        "type": "qrcode",
        "qrcode_url": f"/uploads/qrcodes/{file_name}",
        "expire_seconds": expire_seconds,
        "expired_at": expired_at.strftime("%Y-%m-%d %H:%M:%S"),
    })

    return {"message": "二维码已接收"}


@router.post("/script_status")
async def script_update_status(
    order_token: str = Form(...),
    status: str = Form(...),
    message: str = Form(""),
    db: Session = Depends(get_db),
):
    """脚本专用更新状态(纯表单)"""
    order = db.query(Order).filter(Order.token == order_token).first()
    if not order:
        return {"error": "订单不存在"}

    status_map = {
        "qrcode_scanned": QrcodeStatus.scanned,
        "qrcode_confirmed": QrcodeStatus.confirmed,
        "qrcode_expired": QrcodeStatus.expired,
    }
    if status in status_map and order.callbacks:
        latest_cb = order.callbacks[-1]
        latest_cb.qrcode_status = status_map[status]

    db.add(ExecLog(order_id=order.id, log_content=message or status))
    db.commit()

    await manager.send_to_order(order_token, {
        "type": "status",
        "status": status,
        "message": message,
    })

    return {"message": "状态已更新"}


@router.post("/script_result")
async def script_report_result(
    order_token: str = Form(...),
    success: str = Form(...),
    result: str = Form(""),
    error_msg: str = Form(""),
    db: Session = Depends(get_db),
):
    """脚本专用上报结果(纯表单)"""
    order = db.query(Order).filter(Order.token == order_token).first()
    if not order:
        return {"error": "订单不存在"}

    is_success = success.lower() in ("true", "1", "yes")
    order.exec_status = ExecStatus.success if is_success else ExecStatus.failed

    if order.callbacks:
        latest_cb = order.callbacks[-1]
        latest_cb.result = result
        latest_cb.error_msg = error_msg

    log_msg = f"执行{'成功' if is_success else '失败'}: {result or error_msg or ''}"
    db.add(ExecLog(order_id=order.id, log_content=log_msg))
    db.commit()

    await manager.send_to_order(order_token, {
        "type": "result",
        "success": is_success,
        "result": result,
        "error_msg": error_msg,
    })

    return {"message": "结果已接收"}
