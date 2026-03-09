import uuid
import os
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pydantic import BaseModel

from models import get_db, Gallery, GalleryCategory, OperationLog
from services.auth import get_current_admin
from config import settings
import aiofiles

router = APIRouter(prefix="/api/gallery", tags=["图库管理"])

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp"}


class CategoryCreate(BaseModel):
    name: str


@router.get("/category/list")
def get_categories(db: Session = Depends(get_db)):
    cats = db.query(GalleryCategory).order_by(GalleryCategory.created_at).all()
    return [{"id": c.id, "name": c.name} for c in cats]


@router.post("/category/create")
def create_category(
    req: CategoryCreate,
    current_admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    if db.query(GalleryCategory).filter(GalleryCategory.name == req.name).first():
        raise HTTPException(status_code=400, detail="分类名称已存在")
    cat = GalleryCategory(name=req.name)
    db.add(cat)
    db.add(OperationLog(admin_id=current_admin.id, action="创建图库分类", target=req.name))
    db.commit()
    db.refresh(cat)
    return {"id": cat.id, "name": cat.name}


@router.delete("/category/delete/{category_id}")
def delete_category(
    category_id: int,
    current_admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    cat = db.query(GalleryCategory).filter(GalleryCategory.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="分类不存在")
    db.delete(cat)
    db.add(OperationLog(admin_id=current_admin.id, action="删除图库分类", target=cat.name))
    db.commit()
    return {"message": "分类已删除"}


@router.get("/list")
def get_gallery_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category_id: Optional[int] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Gallery)
    if category_id:
        query = query.filter(Gallery.category_id == category_id)
    if keyword:
        query = query.filter(Gallery.name.contains(keyword) | Gallery.tags.contains(keyword))
    total = query.count()
    items = query.order_by(desc(Gallery.created_at)).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "total": total,
        "list": [
            {
                "id": g.id,
                "name": g.name,
                "category_id": g.category_id,
                "image_url": f"/uploads/gallery/{os.path.basename(g.image_path)}",
                "tags": g.tags,
                "created_at": g.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
            for g in items
        ],
    }


@router.post("/upload")
async def upload_gallery_image(
    name: str = Form(...),
    category_id: Optional[int] = Form(None),
    tags: Optional[str] = Form(None),
    image: UploadFile = File(...),
    current_admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    ext = os.path.splitext(image.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="不支持的图片格式")
    if image.size and image.size > settings.MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="图片大小不能超过5MB")

    file_name = f"{uuid.uuid4().hex}{ext}"
    save_path = os.path.join(settings.UPLOAD_DIR, "gallery", file_name)
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    async with aiofiles.open(save_path, "wb") as f:
        await f.write(await image.read())

    gallery = Gallery(name=name, category_id=category_id, image_path=save_path, tags=tags)
    db.add(gallery)
    db.add(OperationLog(admin_id=current_admin.id, action="上传图库图片", target=name))
    db.commit()
    db.refresh(gallery)

    return {
        "id": gallery.id,
        "name": gallery.name,
        "image_url": f"/uploads/gallery/{file_name}",
    }


@router.delete("/delete/{image_id}")
def delete_gallery_image(
    image_id: int,
    current_admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    img = db.query(Gallery).filter(Gallery.id == image_id).first()
    if not img:
        raise HTTPException(status_code=404, detail="图片不存在")
    if img.image_path and os.path.exists(img.image_path):
        os.remove(img.image_path)
    db.delete(img)
    db.add(OperationLog(admin_id=current_admin.id, action="删除图库图片", target=img.name))
    db.commit()
    return {"message": "图片已删除"}


class BatchDeleteRequest(BaseModel):
    ids: list[int]


@router.post("/batch-delete")
def batch_delete_gallery_images(
    req: BatchDeleteRequest,
    current_admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    images = db.query(Gallery).filter(Gallery.id.in_(req.ids)).all()
    deleted_count = 0
    for img in images:
        if img.image_path and os.path.exists(img.image_path):
            os.remove(img.image_path)
        db.delete(img)
        deleted_count += 1
    if deleted_count > 0:
        db.add(OperationLog(admin_id=current_admin.id, action="批量删除图库图片", target=f"共{deleted_count}张"))
    db.commit()
    return {"message": f"已删除 {deleted_count} 张图片"}


class BatchCategoryRequest(BaseModel):
    ids: list[int]
    category_id: Optional[int] = None


@router.post("/batch-category")
def batch_set_gallery_category(
    req: BatchCategoryRequest,
    current_admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    if req.category_id:
        cat = db.query(GalleryCategory).filter(GalleryCategory.id == req.category_id).first()
        if not cat:
            raise HTTPException(status_code=404, detail="分类不存在")
    updated = db.query(Gallery).filter(Gallery.id.in_(req.ids)).update({"category_id": req.category_id})
    db.add(OperationLog(admin_id=current_admin.id, action="批量设置图片分类", target=f"共{updated}张"))
    db.commit()
    return {"message": f"已更新 {updated} 张图片的分类"}
