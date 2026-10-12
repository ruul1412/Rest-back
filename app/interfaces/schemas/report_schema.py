from pydantic import BaseModel
from typing import Optional
from datetime import date
from decimal import Decimal


# ── Resumen diario (legacy, se mantiene por compatibilidad) ───────────────────

class PaymentMethodSummary(BaseModel):
    method: str
    total:  Decimal
    count:  int


class DailySummaryResponse(BaseModel):
    date:              date
    total_revenue:     Decimal
    total_orders:      int
    total_groups:      int
    menu_items_sold:   int
    payment_methods:   list[PaymentMethodSummary] = []


# ── Productos más vendidos ────────────────────────────────────────────────────

class TopProductResponse(BaseModel):
    product_id:   str
    product_name: str
    sale_type:    str
    quantity:     int
    total:        Decimal


# ── Reporte de menú ───────────────────────────────────────────────────────────

class MenuSlotReportResponse(BaseModel):
    product_name:  str
    menu_price:    Decimal
    stock_start:   int
    stock_current: int
    sold:          int
    revenue:       Decimal


class MenuDayReportResponse(BaseModel):
    date:          date
    is_active:     bool
    total_sold:    int
    total_revenue: Decimal
    slots:         list[MenuSlotReportResponse] = []


# ── Reporte de pagos por rango ────────────────────────────────────────────────

class PaymentRangeResponse(BaseModel):
    date_from:     date
    date_to:       date
    total_revenue: Decimal
    total_paid:    int
    payment_methods: list[PaymentMethodSummary] = []


# ── Dashboard: KPIs con comparativo ────────────────────────────────────────────

class KpiValue(BaseModel):
    value:      Decimal
    delta_pct:  Optional[float] = None  # None si no hay dato del periodo anterior


class DashboardSummaryResponse(BaseModel):
    date_from:        date
    date_to:          date
    prev_date_from:   date
    prev_date_to:     date
    total_revenue:    KpiValue
    total_orders:     KpiValue
    avg_ticket:       KpiValue
    groups_served:    KpiValue
    gross_utility:    KpiValue
    margin_pct:       float
    has_missing_costs: bool
    payment_methods:  list[PaymentMethodSummary] = []


# ── Dashboard: ventas por hora ─────────────────────────────────────────────────

class HourlySales(BaseModel):
    hour:         int
    revenue:      Decimal
    orders_count: int


class SalesByHourResponse(BaseModel):
    date_from: date
    date_to:   date
    hours:     list[HourlySales]


# ── Dashboard: estado de órdenes ───────────────────────────────────────────────

class OrderStatusCount(BaseModel):
    status:     str
    count:      int
    percentage: float


class OrderStatusResponse(BaseModel):
    date_from: date
    date_to:   date
    total:     int
    statuses:  list[OrderStatusCount]


# ── Dashboard: ventas por categoría ────────────────────────────────────────────

class CategorySales(BaseModel):
    category_id:   str
    category_name: str
    revenue:       Decimal
    percentage:    float


class SalesByCategoryResponse(BaseModel):
    date_from:     date
    date_to:       date
    total_revenue: Decimal
    categories:    list[CategorySales]

class TrendPoint(BaseModel):
    date: date
    revenue: Decimal
    orders_count: int


class SalesTrendResponse(BaseModel):
    date_from: date
    date_to: date
    points: list[TrendPoint]