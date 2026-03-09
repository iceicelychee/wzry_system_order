from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from models import get_db, Admin, Agent, AgentStatus, SiteConfig
from services.auth import verify_password, get_password_hash, create_access_token, get_current_admin

router = APIRouter(prefix="/api/auth", tags=["认证"])


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    username: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


@router.post("/login", response_model=LoginResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    admin = db.query(Admin).filter(Admin.username == form_data.username).first()
    if not admin or not verify_password(form_data.password, admin.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="账号或密码错误",
        )
    token = create_access_token({"sub": admin.username, "role": "admin"})
    return {"access_token": token, "token_type": "bearer", "username": admin.username}


@router.get("/me")
def get_me(current_admin: Admin = Depends(get_current_admin)):
    return {"id": current_admin.id, "username": current_admin.username}


@router.post("/change-password")
def change_password(
    req: ChangePasswordRequest,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    if not verify_password(req.old_password, current_admin.password):
        raise HTTPException(status_code=400, detail="原密码错误")
    current_admin.password = get_password_hash(req.new_password)
    db.commit()
    return {"message": "密码修改成功"}


class AgentLoginRequest(BaseModel):
    username: str
    password: str


@router.post("/agent-login")
def agent_login(req: AgentLoginRequest, db: Session = Depends(get_db)):
    agent = db.query(Agent).filter(Agent.username == req.username).first()
    if not agent or not verify_password(req.password, agent.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="账号或密码错误",
        )
    if agent.status != AgentStatus.enabled:
        raise HTTPException(status_code=403, detail="账号已被禁用")
    token = create_access_token({"sub": agent.username, "role": "agent"})
    return {
        "access_token": token,
        "token_type": "bearer",
        "username": agent.username,
        "balance": agent.balance,
    }


# ========== 站点配置（说明内容等） ==========

@router.get("/site-config/{key}")
def get_site_config(key: str, db: Session = Depends(get_db)):
    config = db.query(SiteConfig).filter(SiteConfig.config_key == key).first()
    return {"key": key, "value": config.config_value if config else ""}


class SiteConfigUpdate(BaseModel):
    value: str


@router.put("/site-config/{key}")
def update_site_config(
    key: str,
    req: SiteConfigUpdate,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    config = db.query(SiteConfig).filter(SiteConfig.config_key == key).first()
    if config:
        config.config_value = req.value
    else:
        config = SiteConfig(config_key=key, config_value=req.value)
        db.add(config)
    db.commit()
    return {"message": "保存成功"}
