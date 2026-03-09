import uuid
import os
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel

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

    # 保存二维码图片
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

    # 推送给客户端
    await manager.send_to_order(order_token, {
        "type": "qrcode",
        "qrcode_url": f"/uploads/qrcodes/{file_name}",
        "expire_seconds": expire_seconds,
        "expired_at": expired_at.strftime("%Y-%m-%d %H:%M:%S"),
    })

    return {"message": "二维码已接收"}


@router.post("/status")
async def update_status(req: StatusUpdate, db: Session = Depends(get_db)):
    """脚本更新执行状态"""
    order = db.query(Order).filter(Order.token == req.order_token).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    # 更新二维码状态
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
