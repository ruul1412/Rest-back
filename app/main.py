import json

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.core.config import settings
from app.infrastructure.models import *
# actualizados
from app.interfaces.routes.auth_routes import router as auth_routes
from app.interfaces.routes.user_routes import router as user_routes
from app.interfaces.routes.permission_routes import router as permission_routes
from app.interfaces.routes.catalog_routes import category_router, product_type_router, product_router
from app.interfaces.routes.table_routes import router as table_routes
from app.interfaces.routes.menu_routes import router as menu_routes
from app.interfaces.routes.payment_routes import router as payment_routes
from app.interfaces.routes.company_routes import router as company_routes
from app.interfaces.routes.branch_routes import router as branch_routes

# antiguos
from app.interfaces.routes.orden_routes import router as order_routes
from app.interfaces.routes.report_routes import router as report_routes
# from app.interfaces.routes.print_routes import router as print_routes

from app.infrastructure.db.seed_roles import seed_roles
from app.infrastructure.db.seed_admin import seed_admin
from app.infrastructure.db.seed_catalog import seed_catalog


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


def get_route_success_message(request):
    endpoint = request.scope.get("endpoint")
    custom_message = getattr(endpoint, "response_message", None)
    if custom_message:
        return custom_message

    if request.url.path == "/":
        return "API Restaurante funcionando 🚀"

    return "Operación exitosa"


def should_skip_standardization(request) -> bool:
    path = request.url.path
    if path in {"/openapi.json", "/docs", "/redoc", "/docs/oauth2-redirect"}:
        return True
    if path.startswith("/docs") or path.startswith("/redoc"):
        return True
    return False


@app.middleware("http")
async def standardize_api_response(request, call_next):
    if should_skip_standardization(request):
        return await call_next(request)

    response = await call_next(request)

    content_type = response.headers.get("content-type", "")
    if "application/json" not in content_type:
        return response

    try:
        body = b""
        async for chunk in response.body_iterator:
            body += chunk
    except Exception:
        return response

    if not body:
        return response

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return response

    if isinstance(payload, dict) and all(key in payload for key in ["success", "message", "data", "errors", "total"]):
        return response

    is_success = response.status_code < 400
    route_message = get_route_success_message(request)

    if isinstance(payload, dict):
        if "items" in payload and "total" in payload:
            message = route_message if is_success else (payload.get("message") or "Error en la operación")
            data = payload.get("items", [])
            errors = [] if is_success else [message]
            total = payload.get("total", len(data) if isinstance(data, list) else 0)
            success = is_success
        elif payload.get("detail") is not None:
            message = payload["detail"]
            data = []
            errors = [message]
            total = 0
            success = False
        else:
            message = route_message if is_success else (payload.get("message") or "Error en la operación")
            data = {k: v for k, v in payload.items() if k not in {"message", "success", "errors", "total"}}
            errors = [] if is_success else [message]
            total = payload.get("total", 0)
            success = is_success
    elif isinstance(payload, list):
        message = route_message if is_success else "Error en la operación"
        data = payload
        errors = [] if is_success else [message]
        total = len(payload)  # provisional: luego se reemplazará por total real de la consulta paginada
        success = is_success
    elif payload is None:
        message = route_message if is_success else "Error en la operación"
        data = []
        errors = [] if is_success else [message]
        total = 0
        success = is_success
    else:
        message = route_message if is_success else "Error en la operación"
        data = payload
        errors = [] if is_success else [message]
        total = 0
        success = is_success

    wrapped = {
        "success": success,
        "message": message,
        "data": data,
        "errors": errors,
        "total": total,
    }

    headers = {k: v for k, v in response.headers.items() if k.lower() not in {"content-length", "transfer-encoding"}}
    return JSONResponse(
        content=wrapped,
        status_code=response.status_code,
        headers=headers,
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
app.include_router(company_routes)
app.include_router(branch_routes)

# app.include_router(print_routes)

@app.get("/")
def root():
    return {"message": "API Restaurante funcionando 🚀"}