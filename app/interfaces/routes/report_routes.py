from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.interfaces.schemas.report_schema import (
    DailySummaryResponse, TopProductResponse,
    MenuDayReportResponse, PaymentRangeResponse,
    DashboardSummaryResponse, SalesByHourResponse,
    OrderStatusResponse, SalesByCategoryResponse,
    SalesTrendResponse,
)
from app.application.report.report_use_cases import (
    DailySummaryUseCase, TopProductsUseCase,
    MenuDayReportUseCase, PaymentRangeUseCase,
    DashboardSummaryUseCase, SalesByHourUseCase,
    OrderStatusUseCase, SalesByCategoryUseCase,SalesTrendUseCase
)
from app.interfaces.dependencies.auth_dependencies import require_roles
from app.infrastructure.repositories.report_repository import ReportRepository

router = APIRouter(prefix="/reports", tags=["Reports"])


def route_message(message: str):
    def decorator(func):
        func.response_message = message
        return func
    return decorator


_admin_cajero = Depends(require_roles(["admin", "cajero"]))


def _repo(db: Session = Depends(get_db)) -> ReportRepository:
    return ReportRepository(db)


@route_message("Resumen diario obtenido correctamente")
@router.get("/daily", response_model=DailySummaryResponse, dependencies=[_admin_cajero])
def daily_summary(
    target_date: date = Query(default=None, description="Fecha (YYYY-MM-DD). Por defecto: hoy"),
    repo: ReportRepository = Depends(_repo),
):
    return DailySummaryUseCase(repo).execute(target_date or date.today())


@route_message("Top productos obtenidos correctamente")
@router.get("/top-products", response_model=list[TopProductResponse], dependencies=[_admin_cajero])
def top_products(
    date_from: date = Query(default=None, description="Fecha inicio. Por defecto: hoy"),
    date_to:   date = Query(default=None, description="Fecha fin. Por defecto: hoy"),
    limit:     int  = Query(default=10, ge=1, le=50),
    repo: ReportRepository = Depends(_repo),
):
    today = date.today()
    return TopProductsUseCase(repo).execute(date_from or today, date_to or today, limit)


@route_message("Reporte del menú obtenido correctamente")
@router.get("/menu", response_model=MenuDayReportResponse, dependencies=[_admin_cajero])
def menu_report(
    target_date: date = Query(default=None, description="Fecha. Por defecto: hoy"),
    repo: ReportRepository = Depends(_repo),
):
    return MenuDayReportUseCase(repo).execute(target_date or date.today())


@route_message("Pagos obtenidos correctamente")
@router.get("/payments", response_model=PaymentRangeResponse, dependencies=[_admin_cajero])
def payment_range(
    date_from: date = Query(..., description="Fecha inicio (YYYY-MM-DD)"),
    date_to:   date = Query(..., description="Fecha fin (YYYY-MM-DD)"),
    repo: ReportRepository = Depends(_repo),
):
    return PaymentRangeUseCase(repo).execute(date_from, date_to)


# ── Dashboard ───────────────────────────────────────────────────────────────

@route_message("Resumen del dashboard obtenido correctamente")
@router.get("/summary", response_model=DashboardSummaryResponse, dependencies=[_admin_cajero])
def dashboard_summary(
    date_from: date = Query(default=None, description="Fecha inicio. Por defecto: hoy"),
    date_to:   date = Query(default=None, description="Fecha fin. Por defecto: hoy"),
    repo: ReportRepository = Depends(_repo),
):
    today = date.today()
    return DashboardSummaryUseCase(repo).execute(date_from or today, date_to or today)


@route_message("Ventas por hora obtenidas correctamente")
@router.get("/sales-by-hour", response_model=SalesByHourResponse, dependencies=[_admin_cajero])
def sales_by_hour(
    date_from: date = Query(default=None, description="Fecha inicio. Por defecto: hoy"),
    date_to:   date = Query(default=None, description="Fecha fin. Por defecto: hoy"),
    repo: ReportRepository = Depends(_repo),
):
    today = date.today()
    return SalesByHourUseCase(repo).execute(date_from or today, date_to or today)


@route_message("Estado de pedidos obtenido correctamente")
@router.get("/order-status", response_model=OrderStatusResponse, dependencies=[_admin_cajero])
def order_status(
    date_from: date = Query(default=None, description="Fecha inicio. Por defecto: hoy"),
    date_to:   date = Query(default=None, description="Fecha fin. Por defecto: hoy"),
    repo: ReportRepository = Depends(_repo),
):
    today = date.today()
    return OrderStatusUseCase(repo).execute(date_from or today, date_to or today)


@route_message("Ventas por categoría obtenidas correctamente")
@router.get("/sales-by-category", response_model=SalesByCategoryResponse, dependencies=[_admin_cajero])
def sales_by_category(
    date_from: date = Query(default=None, description="Fecha inicio. Por defecto: hoy"),
    date_to:   date = Query(default=None, description="Fecha fin. Por defecto: hoy"),
    repo: ReportRepository = Depends(_repo),
):
    today = date.today()
    return SalesByCategoryUseCase(repo).execute(date_from or today, date_to or today)

@route_message("Tendencia de ventas obtenida correctamente")
@router.get("/sales-trend", response_model=SalesTrendResponse, dependencies=[_admin_cajero])
def sales_trend(
    date_from: date = Query(...), date_to: date = Query(...),
    repo: ReportRepository = Depends(_repo),
):
    return SalesTrendUseCase(repo).execute(date_from, date_to)