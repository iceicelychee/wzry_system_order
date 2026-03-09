import os
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import settings
from models.database import engine, Base
from models.models import Admin
from models.database import SessionLocal
from services.auth import get_password_hash

from api.auth import router as auth_router
from api.order import router as order_router
from api.gallery import router as gallery_router
from api.callback import router as callback_router
from api.client import router as client_router
from api.agent import router as agent_router


def init_db():
    Base.metadata.create_all(bind=engine)
    # 迁移：给 orders 表添加 agent_id 列（如果不存在）
    from sqlalchemy import inspect as sa_inspect, text
    insp = sa_inspect(engine)
    columns = [c["name"] for c in insp.get_columns("orders")]
    if "agent_id" not in columns:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE orders ADD COLUMN agent_id INTEGER NULL"))
            try:
                conn.execute(text("ALTER TABLE orders ADD CONSTRAINT fk_orders_agent FOREIGN KEY (agent_id) REFERENCES agents(id)"))
            except Exception:
                pass
        print("已迁移：orders 表新增 agent_id 列")
    db = SessionLocal()
    try:
        admin = db.query(Admin).filter(Admin.username == "admin").first()
        if not admin:
            admin = Admin(username="admin", password=get_password_hash("admin123"))
            db.add(admin)
            db.commit()
            print("默认管理员账号已创建：admin / admin123")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "orders"), exist_ok=True)
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "gallery"), exist_ok=True)
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "qrcodes"), exist_ok=True)
    yield


app = FastAPI(
    title="订单管理系统",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.ENABLE_DOCS else None,
   redoc_url="/redoc" if settings.ENABLE_DOCS else None,
    openapi_url="/openapi.json" if settings.ENABLE_DOCS else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# 静态文件服务（图片访问）
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# 注册路由
app.include_router(auth_router)
app.include_router(order_router)
app.include_router(gallery_router)
app.include_router(callback_router)
app.include_router(client_router)
app.include_router(agent_router)


@app.get("/")
def root():
    return {"message": "订单管理系统 API 运行中", "docs": "/docs"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=True)
