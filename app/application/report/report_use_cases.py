from datetime import date

from fastapi import HTTPException

from app.interfaces.schemas.report_schema import (
    DailySummaryResponse, PaymentMethodSummary,
    TopProductResponse, MenuDayReportResponse,
    MenuSlotReportResponse, PaymentRangeResponse,
    DashboardSummaryResponse, KpiValue,
    SalesByHourResponse, HourlySales,
    OrderStatusResponse, OrderStatusCount,
    SalesByCategoryResponse, CategorySales,SalesTrendResponse,
    TrendPoint
)
from app.infrastructure.repositories.report_repository import ReportRepository


class DailySummaryUseCase:
    def __init__(self, repo: ReportRepository): self._repo = repo

    def execute(self, target_date: date) -> DailySummaryResponse:
        data = self._repo.daily_summary(target_date)
        return DailySummaryResponse(
            date=data["date"],
            total_revenue=data["total_revenue"],
            total_orders=data["total_orders"],
            total_groups=data["total_groups"],
            menu_items_sold=data["menu_items_sold"],
            payment_methods=[
                PaymentMethodSummary(**m) for m in data["payment_methods"]
            ],
        )


class TopProductsUseCase:
    def __init__(self, repo: ReportRepository): self._repo = repo

    def execute(self, date_from: date, date_to: date, limit: int = 10) -> list[TopProductResponse]:
        if date_from > date_to:
            raise HTTPException(
                status_code=400,
                detail="date_from no puede ser mayor que date_to",
            )
        return [TopProductResponse(**r) for r in
                self._repo.top_products(date_from, date_to, limit)]


class MenuDayReportUseCase:
    def __init__(self, repo: ReportRepository): self._repo = repo

    def execute(self, target_date: date) -> MenuDayReportResponse:
        data = self._repo.menu_day_report(target_date)
        if not data:
            raise HTTPException(
                status_code=404,
                detail=f"No hay menú configurado para {target_date}",
            )
        return MenuDayReportResponse(
            date=data["date"],
            is_active=data["is_active"],
            total_sold=data["total_sold"],
            total_revenue=data["total_revenue"],
            slots=[MenuSlotReportResponse(**s) for s in data["slots"]],
        )


class PaymentRangeUseCase:
    def __init__(self, repo: ReportRepository): self._repo = repo

    def execute(self, date_from: date, date_to: date) -> PaymentRangeResponse:
        if date_from > date_to:
            raise HTTPException(
                status_code=400,
                detail="date_from no puede ser mayor que date_to",
            )
        data = self._repo.payment_range(date_from, date_to)
        return PaymentRangeResponse(
            date_from=data["date_from"],
            date_to=data["date_to"],
            total_revenue=data["total_revenue"],
            total_paid=data["total_paid"],
            payment_methods=[
                PaymentMethodSummary(**m) for m in data["payment_methods"]
            ],
        )


# ── Dashboard ───────────────────────────────────────────────────────────────

class DashboardSummaryUseCase:
    def __init__(self, repo: ReportRepository): self._repo = repo

    def execute(self, date_from: date, date_to: date) -> DashboardSummaryResponse:
        if date_from > date_to:
            raise HTTPException(
                status_code=400,
                detail="date_from no puede ser mayor que date_to",
            )
        data = self._repo.dashboard_summary(date_from, date_to)
        return DashboardSummaryResponse(
            date_from=data["date_from"],
            date_to=data["date_to"],
            prev_date_from=data["prev_date_from"],
            prev_date_to=data["prev_date_to"],
            total_revenue=KpiValue(**data["total_revenue"]),
            total_orders=KpiValue(**data["total_orders"]),
            avg_ticket=KpiValue(**data["avg_ticket"]),
            groups_served=KpiValue(**data["groups_served"]),
            gross_utility=KpiValue(**data["gross_utility"]),
            margin_pct=data["margin_pct"],
            has_missing_costs=data["has_missing_costs"],
            payment_methods=[
                PaymentMethodSummary(**m) for m in data["payment_methods"]
            ],
        )


class SalesByHourUseCase:
    def __init__(self, repo: ReportRepository): self._repo = repo

    def execute(self, date_from: date, date_to: date) -> SalesByHourResponse:
        if date_from > date_to:
            raise HTTPException(
                status_code=400,
                detail="date_from no puede ser mayor que date_to",
            )
        data = self._repo.sales_by_hour(date_from, date_to)
        return SalesByHourResponse(
            date_from=data["date_from"],
            date_to=data["date_to"],
            hours=[HourlySales(**h) for h in data["hours"]],
        )


class OrderStatusUseCase:
    def __init__(self, repo: ReportRepository): self._repo = repo

    def execute(self, date_from: date, date_to: date) -> OrderStatusResponse:
        if date_from > date_to:
            raise HTTPException(
                status_code=400,
                detail="date_from no puede ser mayor que date_to",
            )
        data = self._repo.order_status_counts(date_from, date_to)
        return OrderStatusResponse(
            date_from=data["date_from"],
            date_to=data["date_to"],
            total=data["total"],
            statuses=[OrderStatusCount(**s) for s in data["statuses"]],
        )


class SalesByCategoryUseCase:
    def __init__(self, repo: ReportRepository): self._repo = repo

    def execute(self, date_from: date, date_to: date) -> SalesByCategoryResponse:
        if date_from > date_to:
            raise HTTPException(
                status_code=400,
                detail="date_from no puede ser mayor que date_to",
            )
        data = self._repo.sales_by_category(date_from, date_to)
        return SalesByCategoryResponse(
            date_from=data["date_from"],
            date_to=data["date_to"],
            total_revenue=data["total_revenue"],
            categories=[CategorySales(**c) for c in data["categories"]],
        )

class SalesTrendUseCase:
    def __init__(self, repo: ReportRepository): self._repo = repo

    def execute(self, date_from: date, date_to: date) -> SalesTrendResponse:
        if date_from > date_to:
            raise HTTPException(status_code=400, detail="date_from no puede ser mayor que date_to")
        data = self._repo.sales_trend(date_from, date_to)
        return SalesTrendResponse(
            date_from=data["date_from"], date_to=data["date_to"],
            points=[TrendPoint(**p) for p in data["points"]],
        )