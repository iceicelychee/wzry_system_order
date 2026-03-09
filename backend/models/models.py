from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from .database import Base
import enum


class SystemType(str, enum.Enum):
    android_q = "安卓Q区"
    ios_q = "苹果Q区"
    android_v = "安卓V区"
    ios_v = "苹果V区"


class LinkStatus(str, enum.Enum):
    unfilled = "未填写"
    submitted = "已提交"
    expired = "已过期"
    disabled = "已禁用"


class ExecStatus(str, enum.Enum):
    pending = "待执行"
    running = "执行中"
    success = "成功"
    failed = "失败"


class QrcodeStatus(str, enum.Enum):
    waiting = "待扫码"
    scanned = "已扫码"
    confirmed = "已确认"
    expired = "已过期"


class AgentStatus(str, enum.Enum):
    enabled = "启用"
    disabled = "禁用"


class Admin(Base):
    __tablename__ = "admin"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    operation_logs = relationship("OperationLog", back_populates="admin")


class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    balance = Column(Integer, default=0, nullable=False)
    status = Column(SAEnum(AgentStatus), default=AgentStatus.enabled)
    remark = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    orders = relationship("Order", back_populates="agent")
    balance_logs = relationship("BalanceLog", back_populates="agent", lazy="dynamic")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_no = Column(String(30), unique=True, nullable=False, index=True)
    token = Column(String(64), unique=True, nullable=False, index=True)
    system_type = Column(SAEnum(SystemType), nullable=True)
    image_path = Column(String(255), nullable=True)
    link_status = Column(SAEnum(LinkStatus), default=LinkStatus.unfilled)
    exec_status = Column(SAEnum(ExecStatus), default=ExecStatus.pending)
    remark = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    submitted_at = Column(DateTime, nullable=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=True)

    agent = relationship("Agent", back_populates="orders")
    callbacks = relationship("ScriptCallback", back_populates="order", cascade="all, delete-orphan")
    exec_logs = relationship("ExecLog", back_populates="order", cascade="all, delete-orphan")


class ScriptCallback(Base):
    __tablename__ = "script_callbacks"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)
    qrcode_path = Column(String(255), nullable=True)
    qrcode_status = Column(SAEnum(QrcodeStatus), default=QrcodeStatus.waiting, index=True)
    qrcode_expired_at = Column(DateTime, nullable=True, index=True)
    result = Column(Text, nullable=True)
    error_msg = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now, index=True)

    order = relationship("Order", back_populates="callbacks")


class ExecLog(Base):
    __tablename__ = "exec_logs"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)
    log_content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.now, index=True)

    order = relationship("Order", back_populates="exec_logs")


class GalleryCategory(Base):
    __tablename__ = "gallery_category"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    images = relationship("Gallery", back_populates="category")


class Gallery(Base):
    __tablename__ = "gallery"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    category_id = Column(Integer, ForeignKey("gallery_category.id"), nullable=True)
    image_path = Column(String(255), nullable=False)
    tags = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    category = relationship("GalleryCategory", back_populates="images")


class OperationLog(Base):
    __tablename__ = "operation_logs"

    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, ForeignKey("admin.id"), nullable=True)
    action = Column(String(100), nullable=False)
    target = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    admin = relationship("Admin", back_populates="operation_logs")


class BalanceLog(Base):
    __tablename__ = "balance_logs"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False, index=True)
    change_amount = Column(Integer, nullable=False)
    balance_after = Column(Integer, nullable=False)
    reason = Column(String(200), nullable=False)
    operator= Column(String(50), nullable=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.now, index=True)

    agent = relationship("Agent", back_populates="balance_logs")


class SiteConfig(Base):
    __tablename__ = "site_config"

    id = Column(Integer, primary_key=True, index=True)
    config_key = Column(String(100), unique=True, nullable=False)
    config_value = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
