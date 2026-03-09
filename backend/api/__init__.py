from api.auth import router as auth_router
from api.order import router as order_router
from api.gallery import router as gallery_router
from api.callback import router as callback_router
from api.client import router as client_router

__all__ = [auth_router, order_router, gallery_router, callback_router, client_router]
