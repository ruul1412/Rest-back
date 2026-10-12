from fastapi import FastAPI
from app.core.config import settings
from app.infrastructure.models import *
from fastapi.middleware.cors import CORSMiddleware
# actualizados
from app.interfaces.routes.auth_routes import router as auth_routes
from app.interfaces.routes.user_routes import router as user_routes
from app.interfaces.routes.permission_routes import router as permission_routes
from app.interfaces.routes.catalog_routes import category_router, product_type_router, product_router
from app.interfaces.routes.table_routes import router as table_routes
from app.interfaces.routes.menu_routes import router as menu_routes
from app.interfaces.routes.payment_routes import router as payment_routes

# antiguos
from app.interfaces.routes.orden_routes import router as order_routes
from app.interfaces.routes.report_routes import router as report_routes
# from app.interfaces.routes.print_routes import router as print_routes

from app.infrastructure.db.seed_roles import seed_roles
from app.infrastructure.db.seed_admin import seed_admin
from app.infrastructure.db.seed_catalog import seed_catalog
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app):
    seed_roles()
    seed_admin()
    seed_catalog()
    yield

app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan
)
# app = FastAPI(title=settings.APP_NAME)

# @app.on_event("startup")
# def startup():
#     seed_roles()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # luego restringes
    # allow_origins=["http://localhost:3000"],
    # allow_origins=["http://localhost:5173"],
    # allow_origins=["http://192.168.0.159:5173"], #configuracion para red local 
    # uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    # allow_credentials=False,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes)
app.include_router(user_routes)
app.include_router(permission_routes)
app.include_router(category_router)
app.include_router(product_type_router)
app.include_router(product_router)
app.include_router(table_routes)
app.include_router(menu_routes)
app.include_router(order_routes)
app.include_router(payment_routes)
app.include_router(report_routes)

# app.include_router(print_routes)

@app.get("/")
def root():
    return {"message": "API Restaurante funcionando 🚀"}