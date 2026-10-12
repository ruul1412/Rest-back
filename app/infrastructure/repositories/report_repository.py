from datetime import date, datetime, timedelta, time
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy import func, extract
from sqlalchemy.orm import Session

from app.infrastructure.models.order_group_model import OrderGroupModel
from app.infrastructure.models.order_model import OrderModel
from app.infrastructure.models.order_item_model import OrderItemModel
from app.infrastructure.models.payment_model import PaymentModel
from app.infrastructure.models.payment_split_model import PaymentSplitModel
from app.infrastructure.models.menu_day_model import MenuDayModel
from app.infrastructure.models.menu_day_slot_model import MenuDaySlotModel
from app.infrastructure.models.product_model import ProductModel
from app.infrastructure.models.category_model import CategoryModel

# Zona horaria del local — Perú no tiene horario de verano, offset fijo -05:00.
# Mismo criterio que ya usa order_repository.py: convertir límites de día
# LOCAL a UTC antes de filtrar (sargable, usa índice), en vez de aplicar
# func.date() directo sobre la columna timestamptz (que Postgres evalúa en
# UTC por defecto y desfasa el "día" hasta 5 horas antes de medianoche real).
LOCAL_TZ = ZoneInfo("America/Lima")


def _range_bounds_utc(date_from: date, date_to: date) -> tuple[datetime, datetime]:
    """[inicio, fin) del rango de días en hora local, ya convertido a UTC."""
    start_local = datetime.combine(date_from, time.min, tzinfo=LOCAL_TZ)
    end_local = datetime.combine(date_to, time.min, tzinfo=LOCAL_TZ) + timedelta(days=1)
    return start_local, end_local


def _local_date_expr(column):
    """Expresión SQL: fecha calendario en hora LOCAL de una columna timestamptz.
    Se usa solo para agrupar (GROUP BY), nunca para filtrar el WHERE principal."""
    return func.date(func.timezone("America/Lima", column))


def _local_hour_expr(column):
    """Expresión SQL: hora del día (0-23) en hora LOCAL de una columna timestamptz."""
    return extract("hour", func.timezone("America/Lima", column))


class ReportRepository:

    def __init__(self, db: Session):
        self._db = db

    # ── Resumen diario (legacy) ─────────────────────────────────────────────────

    def daily_summary(self, target_date: date) -> dict:
        start_utc, end_utc = _range_bounds_utc(target_date, target_date)

        revenue = (
            self._db.query(func.coalesce(func.sum(OrderGroupModel.total), 0))
            .filter(
                OrderGroupModel.created_at >= start_utc,
                OrderGroupModel.created_at < end_utc,
                OrderGroupModel.status == "cerrado",
            )
            .scalar()
        )

        total_groups = (
            self._db.query(func.count(OrderGroupModel.id))
            .filter(
                OrderGroupModel.created_at >= start_utc,
                OrderGroupModel.created_at < end_utc,
                OrderGroupModel.status == "cerrado",
            )
            .scalar()
        )

        total_orders = (
            self._db.query(func.count(OrderModel.id))
            .join(OrderGroupModel, OrderGroupModel.id == OrderModel.group_id)
            .filter(
                OrderModel.created_at >= start_utc,
                OrderModel.created_at < end_utc,
            )
            .scalar()
        )

        menu_items = (
            self._db.query(func.coalesce(func.sum(OrderItemModel.quantity), 0))
            .join(OrderModel, OrderModel.id == OrderItemModel.order_id)
            .filter(
                OrderModel.created_at >= start_utc,
                OrderModel.created_at < end_utc,
                OrderItemModel.sale_type == "menu",
            )
            .scalar()
        )

        methods = (
            self._db.query(
                PaymentSplitModel.method,
                func.sum(PaymentSplitModel.amount).label("total"),
                func.count(PaymentSplitModel.id).label("count"),
            )
            .join(PaymentModel, PaymentModel.id == PaymentSplitModel.payment_id)
            .join(OrderGroupModel, OrderGroupModel.id == PaymentModel.group_id)
            .filter(
                OrderGroupModel.created_at >= start_utc,
                OrderGroupModel.created_at < end_utc,
                PaymentModel.status == "pagado",
            )
            .group_by(PaymentSplitModel.method)
            .all()
        )

        return {
            "date":            target_date,
            "total_revenue":   Decimal(str(revenue)),
            "total_orders":    int(total_orders),
            "total_groups":    int(total_groups),
            "menu_items_sold": int(menu_items),
            "payment_methods": [
                {"method": m.method, "total": Decimal(str(m.total)), "count": m.count}
                for m in methods
            ],
        }

    # ── Top productos ─────────────────────────────────────────────────────────

    def top_products(self, date_from: date, date_to: date, limit: int = 10) -> list[dict]:
        start_utc, end_utc = _range_bounds_utc(date_from, date_to)

        rows = (
            self._db.query(
                ProductModel.id.label("product_id"),
                ProductModel.name.label("product_name"),
                OrderItemModel.sale_type,
                func.sum(OrderItemModel.quantity).label("quantity"),
                func.sum(OrderItemModel.quantity * OrderItemModel.unit_price).label("total"),
            )
            .join(OrderItemModel, OrderItemModel.product_id == ProductModel.id)
            .join(OrderModel, OrderModel.id == OrderItemModel.order_id)
            .filter(
                OrderModel.created_at >= start_utc,
                OrderModel.created_at < end_utc,
                OrderItemModel.is_free == False,
            )
            .group_by(ProductModel.id, ProductModel.name, OrderItemModel.sale_type)
            .order_by(func.sum(OrderItemModel.quantity).desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "product_id":   str(r.product_id),
                "product_name": r.product_name,
                "sale_type":    r.sale_type,
                "quantity":     int(r.quantity),
                "total":        Decimal(str(r.total)),
            }
            for r in rows
        ]

    # ── Reporte de menú del día ───────────────────────────────────────────────

    def menu_day_report(self, target_date: date) -> dict | None:
        # MenuDayModel.date es una columna Date pura (sin hora), no necesita
        # conversión de zona horaria.
        menu = (
            self._db.query(MenuDayModel)
            .filter(MenuDayModel.date == target_date)
            .first()
        )
        if not menu:
            return None

        slots = (
            self._db.query(
                ProductModel.name.label("product_name"),
                MenuDaySlotModel.menu_price,
                MenuDaySlotModel.stock_start,
                MenuDaySlotModel.stock_current,
            )
            .join(ProductModel, ProductModel.id == MenuDaySlotModel.product_id)
            .filter(MenuDaySlotModel.menu_day_id == menu.id)
            .order_by(MenuDaySlotModel.order_num)
            .all()
        )

        slot_list = []
        total_sold = 0
        total_revenue = Decimal("0")

        for s in slots:
            sold = s.stock_start - s.stock_current
            revenue = Decimal(str(s.menu_price)) * sold
            total_sold += sold
            total_revenue += revenue
            slot_list.append({
                "product_name":  s.product_name,
                "menu_price":    Decimal(str(s.menu_price)),
                "stock_start":   s.stock_start,
                "stock_current": s.stock_current,
                "sold":          sold,
                "revenue":       revenue,
            })

        return {
            "date":          menu.date,
            "is_active":     menu.is_active,
            "total_sold":    total_sold,
            "total_revenue": total_revenue,
            "slots":         slot_list,
        }

    # ── Reporte por rango de fechas (pagos) ────────────────────────────────────

    def payment_range(self, date_from: date, date_to: date) -> dict:
        start_utc, end_utc = _range_bounds_utc(date_from, date_to)

        total = (
            self._db.query(func.coalesce(func.sum(PaymentModel.amount), 0))
            .filter(
                PaymentModel.pagado_at >= start_utc,
                PaymentModel.pagado_at < end_utc,
                PaymentModel.status == "pagado",
            )
            .scalar()
        )

        count = (
            self._db.query(func.count(PaymentModel.id))
            .filter(
                PaymentModel.pagado_at >= start_utc,
                PaymentModel.pagado_at < end_utc,
                PaymentModel.status == "pagado",
            )
            .scalar()
        )

        methods = (
            self._db.query(
                PaymentSplitModel.method,
                func.sum(PaymentSplitModel.amount).label("total"),
                func.count(PaymentSplitModel.id).label("count"),
            )
            .join(PaymentModel, PaymentModel.id == PaymentSplitModel.payment_id)
            .filter(
                PaymentModel.pagado_at >= start_utc,
                PaymentModel.pagado_at < end_utc,
                PaymentModel.status == "pagado",
            )
            .group_by(PaymentSplitModel.method)
            .all()
        )

        return {
            "date_from":     date_from,
            "date_to":       date_to,
            "total_revenue": Decimal(str(total)),
            "total_paid":    int(count),
            "payment_methods": [
                {"method": m.method, "total": Decimal(str(m.total)), "count": m.count}
                for m in methods
            ],
        }

    # ── Dashboard: KPIs con comparativo vs periodo anterior ────────────────────

    def _period_totals(self, date_from: date, date_to: date) -> dict:
        """Totales crudos de un periodo — usado dos veces (actual y anterior)."""
        start_utc, end_utc = _range_bounds_utc(date_from, date_to)

        revenue = (
            self._db.query(func.coalesce(func.sum(OrderGroupModel.total), 0))
            .filter(
                OrderGroupModel.created_at >= start_utc,
                OrderGroupModel.created_at < end_utc,
                OrderGroupModel.status == "cerrado",
            )
            .scalar()
        )

        groups = (
            self._db.query(func.count(OrderGroupModel.id))
            .filter(
                OrderGroupModel.created_at >= start_utc,
                OrderGroupModel.created_at < end_utc,
                OrderGroupModel.status == "cerrado",
            )
            .scalar()
        )

        orders = (
            self._db.query(func.count(OrderModel.id))
            .join(OrderGroupModel, OrderGroupModel.id == OrderModel.group_id)
            .filter(
                OrderModel.created_at >= start_utc,
                OrderModel.created_at < end_utc,
            )
            .scalar()
        )

        # Costo de lo vendido (para utilidad bruta). Se restringe al MISMO
        # conjunto que el ingreso (grupos cerrado, mismo rango local) — si no,
        # un pedido de una mesa todavía abierta suma costo sin su ingreso
        # correspondiente y da utilidad negativa.
        # Productos sin cost_price cuentan como costo 0 — se avisa con has_missing_costs.
        cost = (
            self._db.query(
                func.coalesce(
                    func.sum(OrderItemModel.quantity * func.coalesce(ProductModel.cost_price, 0)),
                    0,
                )
            )
            .join(OrderModel, OrderModel.id == OrderItemModel.order_id)
            .join(OrderGroupModel, OrderGroupModel.id == OrderModel.group_id)
            .join(ProductModel, ProductModel.id == OrderItemModel.product_id)
            .filter(
                OrderModel.created_at >= start_utc,
                OrderModel.created_at < end_utc,
                OrderGroupModel.status == "cerrado",
                OrderItemModel.is_free == False,
            )
            .scalar()
        )

        missing_costs = (
            self._db.query(func.count(OrderItemModel.id))
            .join(OrderModel, OrderModel.id == OrderItemModel.order_id)
            .join(OrderGroupModel, OrderGroupModel.id == OrderModel.group_id)
            .join(ProductModel, ProductModel.id == OrderItemModel.product_id)
            .filter(
                OrderModel.created_at >= start_utc,
                OrderModel.created_at < end_utc,
                OrderGroupModel.status == "cerrado",
                OrderItemModel.is_free == False,
                ProductModel.cost_price.is_(None),
            )
            .scalar()
        )

        revenue = Decimal(str(revenue))
        cost = Decimal(str(cost))

        return {
            "revenue": revenue,
            "orders": int(orders),
            "groups": int(groups),
            "utility": revenue - cost,
            "has_missing_costs": missing_costs > 0,
        }

    @staticmethod
    def _delta_pct(current: Decimal, previous: Decimal) -> float | None:
        if previous is None or previous == 0:
            return None
        return round(float((current - previous) / previous) * 100, 2)

    def dashboard_summary(self, date_from: date, date_to: date) -> dict:
        period_days = (date_to - date_from).days + 1
        prev_date_to = date_from - timedelta(days=1)
        prev_date_from = prev_date_to - timedelta(days=period_days - 1)

        current = self._period_totals(date_from, date_to)
        previous = self._period_totals(prev_date_from, prev_date_to)

        avg_ticket_current = (
            current["revenue"] / current["groups"] if current["groups"] else Decimal("0")
        )
        avg_ticket_previous = (
            previous["revenue"] / previous["groups"] if previous["groups"] else Decimal("0")
        )

        start_utc, end_utc = _range_bounds_utc(date_from, date_to)
        methods = (
            self._db.query(
                PaymentSplitModel.method,
                func.sum(PaymentSplitModel.amount).label("total"),
                func.count(PaymentSplitModel.id).label("count"),
            )
            .join(PaymentModel, PaymentModel.id == PaymentSplitModel.payment_id)
            .join(OrderGroupModel, OrderGroupModel.id == PaymentModel.group_id)
            .filter(
                OrderGroupModel.created_at >= start_utc,
                OrderGroupModel.created_at < end_utc,
                PaymentModel.status == "pagado",
            )
            .group_by(PaymentSplitModel.method)
            .all()
        )

        margin_pct = (
            float(current["utility"] / current["revenue"] * 100)
            if current["revenue"] else 0.0
        )

        return {
            "date_from": date_from,
            "date_to": date_to,
            "prev_date_from": prev_date_from,
            "prev_date_to": prev_date_to,
            "total_revenue": {
                "value": current["revenue"],
                "delta_pct": self._delta_pct(current["revenue"], previous["revenue"]),
            },
            "total_orders": {
                "value": current["orders"],
                "delta_pct": self._delta_pct(Decimal(current["orders"]), Decimal(previous["orders"])),
            },
            "avg_ticket": {
                "value": avg_ticket_current,
                "delta_pct": self._delta_pct(avg_ticket_current, avg_ticket_previous),
            },
            "groups_served": {
                "value": current["groups"],
                "delta_pct": self._delta_pct(Decimal(current["groups"]), Decimal(previous["groups"])),
            },
            "gross_utility": {
                "value": current["utility"],
                "delta_pct": self._delta_pct(current["utility"], previous["utility"]),
            },
            "margin_pct": round(margin_pct, 2),
            "has_missing_costs": current["has_missing_costs"],
            "payment_methods": [
                {"method": m.method, "total": Decimal(str(m.total)), "count": m.count}
                for m in methods
            ],
        }

    # ── Dashboard: ventas por hora ──────────────────────────────────────────────

    def sales_by_hour(self, date_from: date, date_to: date) -> dict:
        start_utc, end_utc = _range_bounds_utc(date_from, date_to)
        hour_expr = _local_hour_expr(OrderModel.created_at)

        rows = (
            self._db.query(
                hour_expr.label("hour"),
                func.sum(OrderItemModel.quantity * OrderItemModel.unit_price).label("revenue"),
                func.count(func.distinct(OrderModel.id)).label("orders_count"),
            )
            .join(OrderItemModel, OrderItemModel.order_id == OrderModel.id)
            .filter(
                OrderModel.created_at >= start_utc,
                OrderModel.created_at < end_utc,
                OrderItemModel.is_free == False,
            )
            .group_by(hour_expr)
            .all()
        )

        by_hour = {int(r.hour): r for r in rows}
        hours = [
            {
                "hour": h,
                "revenue": Decimal(str(by_hour[h].revenue)) if h in by_hour else Decimal("0"),
                "orders_count": int(by_hour[h].orders_count) if h in by_hour else 0,
            }
            for h in range(24)
        ]

        return {"date_from": date_from, "date_to": date_to, "hours": hours}

    # ── Dashboard: estado de órdenes ────────────────────────────────────────────

    def order_status_counts(self, date_from: date, date_to: date) -> dict:
        start_utc, end_utc = _range_bounds_utc(date_from, date_to)

        rows = (
            self._db.query(
                OrderModel.status,
                func.count(OrderModel.id).label("count"),
            )
            .filter(
                OrderModel.created_at >= start_utc,
                OrderModel.created_at < end_utc,
            )
            .group_by(OrderModel.status)
            .all()
        )

        total = sum(r.count for r in rows)
        statuses = [
            {
                "status": r.status,
                "count": int(r.count),
                "percentage": round((r.count / total * 100), 2) if total else 0.0,
            }
            for r in rows
        ]

        return {"date_from": date_from, "date_to": date_to, "total": int(total), "statuses": statuses}

    # ── Dashboard: ventas por categoría ─────────────────────────────────────────

    def sales_by_category(self, date_from: date, date_to: date) -> dict:
        start_utc, end_utc = _range_bounds_utc(date_from, date_to)

        rows = (
            self._db.query(
                CategoryModel.id.label("category_id"),
                CategoryModel.name.label("category_name"),
                func.sum(OrderItemModel.quantity * OrderItemModel.unit_price).label("revenue"),
            )
            .join(ProductModel, ProductModel.category_id == CategoryModel.id)
            .join(OrderItemModel, OrderItemModel.product_id == ProductModel.id)
            .join(OrderModel, OrderModel.id == OrderItemModel.order_id)
            .filter(
                OrderModel.created_at >= start_utc,
                OrderModel.created_at < end_utc,
                OrderItemModel.is_free == False,
            )
            .group_by(CategoryModel.id, CategoryModel.name)
            .order_by(func.sum(OrderItemModel.quantity * OrderItemModel.unit_price).desc())
            .all()
        )

        total_revenue = sum((Decimal(str(r.revenue)) for r in rows), Decimal("0"))
        categories = [
            {
                "category_id": str(r.category_id),
                "category_name": r.category_name,
                "revenue": Decimal(str(r.revenue)),
                "percentage": round(float(Decimal(str(r.revenue)) / total_revenue * 100), 2)
                if total_revenue else 0.0,
            }
            for r in rows
        ]

        return {
            "date_from": date_from,
            "date_to": date_to,
            "total_revenue": total_revenue,
            "categories": categories,
        }

    # ── Dashboard: tendencia de ventas (rango de días) ──────────────────────────

    def sales_trend(self, date_from: date, date_to: date) -> dict:
        start_utc, end_utc = _range_bounds_utc(date_from, date_to)
        day_expr = _local_date_expr(OrderGroupModel.created_at)

        rows = (
            self._db.query(
                day_expr.label("day"),
                func.sum(OrderGroupModel.total).label("revenue"),
                func.count(func.distinct(OrderModel.id)).label("orders_count"),
            )
            .join(OrderModel, OrderModel.group_id == OrderGroupModel.id)
            .filter(
                OrderGroupModel.created_at >= start_utc,
                OrderGroupModel.created_at < end_utc,
                OrderGroupModel.status == "cerrado",
            )
            .group_by(day_expr)
            .all()
        )

        by_day = {r.day: r for r in rows}
        points = []
        d = date_from
        while d <= date_to:
            r = by_day.get(d)
            points.append({
                "date": d,
                "revenue": Decimal(str(r.revenue)) if r else Decimal("0"),
                "orders_count": int(r.orders_count) if r else 0,
            })
            d += timedelta(days=1)

        return {"date_from": date_from, "date_to": date_to, "points": points}