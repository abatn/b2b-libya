"""
Libya B2B Platform - Routes Package
Registers all route modules onto the FastAPI app.
"""

from fastapi import FastAPI

from routes.admin_escrow import router as admin_escrow_router
from routes.admin_suppliers import router as admin_suppliers_router
from routes.auth_routes import router as auth_router
from routes.b2b import router as b2b_router
from routes.cart import router as cart_router
from routes.chat import router as chat_router
from routes.escrow import router as escrow_router
from routes.messages import router as messages_router
from routes.monitoring import router as monitoring_router
from routes.notifications import router as notifications_router
from routes.orders import router as orders_router
from routes.payment_routes import router as payment_router
from routes.products import router as products_router
from routes.qr_routes import router as qr_router
from routes.reviews import router as reviews_router
from routes.rfq import router as rfq_router
from routes.search import router as search_router
from routes.shipping import router as shipping_router
from routes.static_pages import router as static_router
from routes.suppliers import router as suppliers_router
from routes.sync_routes import router as sync_router


def register_routes(app: FastAPI):
    """Include all routers on the app."""
    app.include_router(notifications_router)
    app.include_router(products_router)
    app.include_router(orders_router)
    app.include_router(b2b_router)
    app.include_router(suppliers_router)
    app.include_router(rfq_router)
    app.include_router(messages_router)
    app.include_router(chat_router)
    app.include_router(qr_router)
    app.include_router(sync_router)
    app.include_router(monitoring_router)
    app.include_router(search_router)
    app.include_router(reviews_router)
    app.include_router(static_router)
    app.include_router(auth_router)
    app.include_router(cart_router)
    app.include_router(escrow_router)
    app.include_router(admin_escrow_router)
    app.include_router(admin_suppliers_router)
    app.include_router(payment_router)
    app.include_router(shipping_router)
