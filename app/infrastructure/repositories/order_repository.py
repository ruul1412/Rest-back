# from typing import Optional
# from uuid import UUID
# from decimal import Decimal
# from datetime import datetime, date as date_type, time, timedelta
# from zoneinfo import ZoneInfo

# from sqlalchemy.orm import Session, joinedload

# from app.infrastructure.models.order_group_model import OrderGroupModel
# from app.infrastructure.models.order_model import OrderModel
# from app.infrastructure.models.order_item_model import OrderItemModel
# from app.infrastructure.models.table_model import TableModel
# from app.infrastructure.models.product_model import ProductModel
# from app.infrastructure.models.product_varient_model import ProductVariantModel
# from app.infrastructure.models.menu_day_slot_model import MenuDaySlotModel
# from app.domain.order.order_entity import OrderGroupEntity, OrderEntity, OrderItemEntity
# from app.domain.enums.order_enum import OrderStatus

# # Zona horaria del local — Perú no tiene horario de verano, offset fijo -05:00.
# LOCAL_TZ = ZoneInfo("America/Lima")


# def _day_bounds_utc(day: date_type) -> tuple[datetime, datetime]:
#     """Medianoche a medianoche del `day` en hora local, convertido a UTC
#     para poder comparar contra columnas timestamptz."""
#     start_local = datetime.combine(day, time.min, tzinfo=LOCAL_TZ)
#     end_local = start_local + timedelta(days=1)
#     return start_local, end_local


# # ── Mappers ───────────────────────────────────────────────────────────────────

# def _item_to_entity(m: OrderItemModel) -> OrderItemEntity:
#     return OrderItemEntity(
#         id=m.id,
#         order_id=m.order_id,
#         product_id=m.product_id,
#         product_name=m.product.name if m.product else "",
#         sale_type=m.sale_type,
#         quantity=m.quantity,
#         unit_price=m.unit_price,
#         subtotal=m.subtotal,
#         is_free=m.is_free,
#         is_auto=m.is_auto,
#         variant_id=m.variant_id,
#         variant_name=m.variant.name if m.variant else None,
#         menu_slot_id=m.menu_slot_id,
#         parent_item_id=m.parent_item_id,
#         notes=m.notes,
#         children=[_item_to_entity(c) for c in (m.children or [])],
#     )


# def _order_to_entity(m: OrderModel) -> OrderEntity:
#     return OrderEntity(
#         id=m.id,
#         group_id=m.group_id,
#         status=m.status,
#         total=m.total,
#         type=m.type,
#         notes=m.notes,
#         disposables_qty=m.disposables_qty,
#         items=[_item_to_entity(i) for i in (m.order_items or []) if i.parent_item_id is None],
#     )


# def _group_to_entity(m: OrderGroupModel) -> OrderGroupEntity:
#     return OrderGroupEntity(
#         id=m.id,
#         user_id=m.user_id,
#         status=m.status,
#         total=m.total,
#         table_id=m.table_id,
#         table_number=m.table.number if m.table else None,
#         customer_name=m.customer_name,
#         notes_group=m.notes_group,
#         created_at=m.created_at,
#         closed_at=m.closed_at,
#         orders=[_order_to_entity(o) for o in (m.orders or [])],
#     )


# def _item_options():
#     return joinedload(OrderModel.order_items).options(
#         joinedload(OrderItemModel.product),
#         joinedload(OrderItemModel.variant),
#         joinedload(OrderItemModel.children).joinedload(OrderItemModel.product),
#     )


# def _group_options():
#     return [
#         joinedload(OrderGroupModel.table),
#         joinedload(OrderGroupModel.orders).options(_item_options()),
#     ]


# # ── OrderGroupRepository ──────────────────────────────────────────────────────

# class OrderGroupRepository:

#     def __init__(self, db: Session):
#         self._db = db

#     def _base_query(self):
#         return self._db.query(OrderGroupModel).options(*_group_options())

#     def get_all(self, status: Optional[str] = None,
#                 date: Optional[date_type] = None) -> list[OrderGroupEntity]:
#         q = self._base_query().order_by(OrderGroupModel.created_at.desc())
#         if status:
#             q = q.filter(OrderGroupModel.status == status)

#         # Las cuentas "cerrado"/"cancelado" se acumularían para siempre si no
#         # se acotan por día. Por defecto mostramos solo las del día de hoy
#         # (hora local); si se pasa `date` explícito, se usa ese día en su lugar.
#         # Las "abierto" nunca se filtran por fecha: siguen activas sin importar
#         # cuándo se crearon.
#         if status in ("cerrado", "cancelado"):
#             target_day = date or datetime.now(LOCAL_TZ).date()
#             start_utc, end_utc = _day_bounds_utc(target_day)
#             q = q.filter(
#                 OrderGroupModel.closed_at >= start_utc,
#                 OrderGroupModel.closed_at < end_utc,
#             )

#         return [_group_to_entity(m) for m in q.all()]

#     def get_by_id(self, group_id: UUID) -> Optional[OrderGroupEntity]:
#         m = self._base_query().filter(OrderGroupModel.id == group_id).first()
#         return _group_to_entity(m) if m else None

#     def get_open_by_table(self, table_id: UUID) -> Optional[OrderGroupEntity]:
#         m = self._base_query().filter(
#             OrderGroupModel.table_id == table_id,
#             OrderGroupModel.status == "abierto",
#         ).first()
#         return _group_to_entity(m) if m else None

#     def create(self, user_id: UUID, table_id: Optional[UUID],
#                customer_name: Optional[str], notes_group: Optional[str]) -> OrderGroupEntity:
#         m = OrderGroupModel(
#             user_id=user_id,
#             table_id=table_id,
#             customer_name=customer_name,
#             notes_group=notes_group,
#             status="abierto",
#             total=Decimal("0"),
#         )
#         self._db.add(m)
#         self._db.flush()
#         return _group_to_entity(
#             self._base_query().filter(OrderGroupModel.id == m.id).first()
#         )

#     def update_total(self, group_id: UUID, total: Decimal) -> None:
#         self._db.query(OrderGroupModel).filter(
#             OrderGroupModel.id == group_id
#         ).update({"total": total})

#     def close(self, group_id: UUID, table_id: Optional[UUID]) -> bool:
#         m = self._db.query(OrderGroupModel).filter(OrderGroupModel.id == group_id).first()
#         if not m:
#             return False
#         m.status = "cerrado"
#         m.closed_at = datetime.now(LOCAL_TZ)
#         # Liberar mesa si la hay
#         if table_id:
#             self._db.query(TableModel).filter(
#                 TableModel.id == table_id
#             ).update({"status": "libre"})
#         self._db.flush()
#         return True

#     def cancel(self, group_id: UUID, table_id: Optional[UUID]) -> bool:
#         m = self._db.query(OrderGroupModel).filter(OrderGroupModel.id == group_id).first()
#         if not m:
#             return False
#         m.status = "cancelado"
#         m.closed_at = datetime.now(LOCAL_TZ)
#         if table_id:
#             self._db.query(TableModel).filter(
#                 TableModel.id == table_id
#             ).update({"status": "libre"})
#         self._db.flush()
#         return True


# # ── OrderRepository ───────────────────────────────────────────────────────────

# class OrderRepository:

#     def __init__(self, db: Session):
#         self._db = db

#     def _base_query(self):
#         return self._db.query(OrderModel).options(_item_options())

#     def get_by_id(self, order_id: UUID) -> Optional[OrderEntity]:
#         m = self._base_query().filter(OrderModel.id == order_id).first()
#         return _order_to_entity(m) if m else None

#     def get_by_group(self, group_id: UUID) -> list[OrderEntity]:
#         return [_order_to_entity(m) for m in
#                 self._base_query().filter(OrderModel.group_id == group_id).all()]

#     def create(self, group_id: UUID, type: Optional[str],
#                notes: Optional[str], disposables_qty: int) -> OrderModel:
#         """Retorna el model directamente para poder agregar items en la misma tx."""
#         m = OrderModel(
#             group_id=group_id,
#             status="pendiente",
#             total=Decimal("0"),
#             type=type,
#             notes=notes,
#             disposables_qty=disposables_qty,
#         )
#         self._db.add(m)
#         self._db.flush()
#         return m

#     def update_total(self, order_id: UUID, total: Decimal) -> None:
#         self._db.query(OrderModel).filter(
#             OrderModel.id == order_id
#         ).update({"total": total})

#     def update_status(self, order_id: UUID, status: str) -> Optional[OrderEntity]:
#         m = self._db.query(OrderModel).filter(OrderModel.id == order_id).first()
#         if not m:
#             return None
#         m.status = status
#         self._db.flush()
#         return self.get_by_id(order_id)

#     def mark_group_orders_delivered(self, group_id: UUID) -> None:
#         """
#         Marca como 'entregado' todas las órdenes de un grupo que todavía no
#         estén 'cancelado'. Se usa al procesar el pago: mientras no exista un
#         módulo de cocina que mueva pendiente -> preparacion -> listo -> entregado,
#         el pago es la única señal real de que la orden se sirvió — sin esto,
#         todo se queda en 'pendiente' para siempre y el reporte de estado de
#         órdenes queda inservible.
#         """
#         self._db.query(OrderModel).filter(
#             OrderModel.group_id == group_id,
#             OrderModel.status != OrderStatus.cancelado,
#         ).update({"status": OrderStatus.entregado}, synchronize_session=False)
#         self._db.flush()

#     # ── Helpers de precio ─────────────────────────────────────────────────────

#     def get_product_price(self, product_id: UUID) -> Optional[Decimal]:
#         m = self._db.query(ProductModel.sale_price).filter(
#             ProductModel.id == product_id).first()
#         return m.sale_price if m else None

#     def get_variant_price(self, variant_id: UUID) -> Optional[Decimal]:
#         m = self._db.query(ProductVariantModel.price).filter(
#             ProductVariantModel.id == variant_id).first()
#         return m.price if m else None

#     def get_slot_price(self, slot_id: UUID) -> Optional[Decimal]:
#         m = self._db.query(MenuDaySlotModel.menu_price).filter(
#             MenuDaySlotModel.id == slot_id).first()
#         return m.menu_price if m else None

#     def decrement_slot_stock(self, slot_id: UUID) -> bool:
#         """Decrementa stock_current en 1. Marca is_available=False si llega a 0."""
#         m = self._db.query(MenuDaySlotModel).filter(
#             MenuDaySlotModel.id == slot_id).first()
#         if not m or m.stock_current <= 0:
#             return False
#         m.stock_current -= 1
#         if m.stock_current == 0:
#             m.is_available = False
#         self._db.flush()
#         return True

#     def restore_slot_stock(self, slot_id: UUID, quantity: int = 1) -> None:
#         """
#         Inversa de decrement_slot_stock — repone stock_current al cancelar
#         una orden que ya lo había descontado. Reactiva is_available si el
#         slot se había marcado agotado.
#         """
#         m = self._db.query(MenuDaySlotModel).filter(
#             MenuDaySlotModel.id == slot_id).first()
#         if not m:
#             return
#         m.stock_current += quantity
#         if m.stock_current > 0:
#             m.is_available = True
#         self._db.flush()

#     def restore_stock_for_order(self, order_id: UUID) -> None:
#         """
#         Repone el stock de todos los items de tipo 'menu' de una orden —
#         se llama al cancelarla, para deshacer los decrementos hechos al
#         crearla (orden A: 2 platos X → decrementa 2 → cancelar → +2).
#         Solo 'menu' descuenta stock hoy; carta/bebida no tocan inventario.
#         """
#         items = (
#             self._db.query(OrderItemModel)
#             .filter(
#                 OrderItemModel.order_id == order_id,
#                 OrderItemModel.sale_type == "menu",
#                 OrderItemModel.menu_slot_id.isnot(None),
#             )
#             .all()
#         )
#         for item in items:
#             self.restore_slot_stock(item.menu_slot_id, item.quantity)

#     def count_menu_items_in_order(self, order_id: UUID) -> int:
#         """Cuenta cuántos items de tipo 'menu' hay en la orden (para regla de entradas gratis)."""
#         from sqlalchemy import func
#         result = self._db.query(
#             func.sum(OrderItemModel.quantity)
#         ).filter(
#             OrderItemModel.order_id == order_id,
#             OrderItemModel.sale_type == "menu",
#             OrderItemModel.is_free == False,
#         ).scalar()
#         return int(result or 0)

#     def count_entry_items_in_order(self, order_id: UUID) -> int:
#         """
#         Cuenta cuántas unidades de tipo 'entrada' hay en la orden (gratis o
#         pagadas). Se usa para saber cuánto cupo de entradas gratis ya se
#         consumió; si solo contáramos las pagadas, una entrada ya marcada
#         gratis nunca reduciría el cupo y todas las siguientes también
#         saldrían gratis.
#         """
#         from sqlalchemy import func
#         result = self._db.query(
#             func.sum(OrderItemModel.quantity)
#         ).filter(
#             OrderItemModel.order_id == order_id,
#             OrderItemModel.sale_type == "entrada",
#         ).scalar()
#         return int(result or 0)

#     def add_item(self, order_id: UUID, product_id: UUID, sale_type: str,
#                  quantity: int, unit_price: Decimal, subtotal: Decimal,
#                  is_free: bool = False, is_auto: bool = False,
#                  variant_id: Optional[UUID] = None,
#                  menu_slot_id: Optional[UUID] = None,
#                  parent_item_id: Optional[UUID] = None,
#                  notes: Optional[str] = None) -> OrderItemModel:
#         m = OrderItemModel(
#             order_id=order_id,
#             product_id=product_id,
#             sale_type=sale_type,
#             quantity=quantity,
#             unit_price=unit_price,
#             subtotal=subtotal,
#             is_free=is_free,
#             is_auto=is_auto,
#             variant_id=variant_id,
#             menu_slot_id=menu_slot_id,
#             parent_item_id=parent_item_id,
#             notes=notes,
#         )
#         self._db.add(m)
#         self._db.flush()
#         return m
from typing import Optional
from uuid import UUID
from decimal import Decimal
from datetime import datetime, date as date_type, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session, joinedload

from app.infrastructure.models.order_group_model import OrderGroupModel
from app.infrastructure.models.order_model import OrderModel
from app.infrastructure.models.order_item_model import OrderItemModel
from app.infrastructure.models.table_model import TableModel
from app.infrastructure.models.product_model import ProductModel
from app.infrastructure.models.product_varient_model import ProductVariantModel
from app.infrastructure.models.menu_day_slot_model import MenuDaySlotModel
from app.domain.order.order_entity import OrderGroupEntity, OrderEntity, OrderItemEntity
from app.domain.enums.order_enum import OrderStatus

# Zona horaria del local — Perú no tiene horario de verano, offset fijo -05:00.
LOCAL_TZ = ZoneInfo("America/Lima")


def _day_bounds_utc(day: date_type) -> tuple[datetime, datetime]:
    """Medianoche a medianoche del `day` en hora local, convertido a UTC
    para poder comparar contra columnas timestamptz."""
    start_local = datetime.combine(day, time.min, tzinfo=LOCAL_TZ)
    end_local = start_local + timedelta(days=1)
    return start_local, end_local


# ── Mappers ───────────────────────────────────────────────────────────────────

def _item_to_entity(m: OrderItemModel) -> OrderItemEntity:
    return OrderItemEntity(
        id=m.id,
        order_id=m.order_id,
        product_id=m.product_id,
        product_name=m.product.name if m.product else "",
        sale_type=m.sale_type,
        quantity=m.quantity,
        unit_price=m.unit_price,
        subtotal=m.subtotal,
        is_free=m.is_free,
        is_auto=m.is_auto,
        variant_id=m.variant_id,
        variant_name=m.variant.name if m.variant else None,
        menu_slot_id=m.menu_slot_id,
        parent_item_id=m.parent_item_id,
        notes=m.notes,
        children=[_item_to_entity(c) for c in (m.children or [])],
    )


def _order_to_entity(m: OrderModel) -> OrderEntity:
    return OrderEntity(
        id=m.id,
        group_id=m.group_id,
        status=m.status,
        total=m.total,
        type=m.type,
        notes=m.notes,
        disposables_qty=m.disposables_qty,
        items=[_item_to_entity(i) for i in (m.order_items or []) if i.parent_item_id is None],
    )


def _group_to_entity(m: OrderGroupModel) -> OrderGroupEntity:
    return OrderGroupEntity(
        id=m.id,
        user_id=m.user_id,
        status=m.status,
        total=m.total,
        table_id=m.table_id,
        table_number=m.table.number if m.table else None,
        customer_name=m.customer_name,
        notes_group=m.notes_group,
        created_at=m.created_at,
        closed_at=m.closed_at,
        orders=[_order_to_entity(o) for o in (m.orders or [])],
    )


def _item_options():
    return joinedload(OrderModel.order_items).options(
        joinedload(OrderItemModel.product),
        joinedload(OrderItemModel.variant),
        joinedload(OrderItemModel.children).joinedload(OrderItemModel.product),
    )


def _group_options():
    return [
        joinedload(OrderGroupModel.table),
        joinedload(OrderGroupModel.orders).options(_item_options()),
    ]


# ── OrderGroupRepository ──────────────────────────────────────────────────────

class OrderGroupRepository:

    def __init__(self, db: Session):
        self._db = db

    def _base_query(self):
        return self._db.query(OrderGroupModel).options(*_group_options())

    def get_all(self, status: Optional[str] = None,
                date: Optional[date_type] = None) -> list[OrderGroupEntity]:
        q = self._base_query().order_by(OrderGroupModel.created_at.desc())
        if status:
            q = q.filter(OrderGroupModel.status == status)

        # Las cuentas "cerrado"/"cancelado" se acumularían para siempre si no
        # se acotan por día. Por defecto mostramos solo las del día de hoy
        # (hora local); si se pasa `date` explícito, se usa ese día en su lugar.
        # Las "abierto" nunca se filtran por fecha: siguen activas sin importar
        # cuándo se crearon.
        if status in ("cerrado", "cancelado"):
            target_day = date or datetime.now(LOCAL_TZ).date()
            start_utc, end_utc = _day_bounds_utc(target_day)
            q = q.filter(
                OrderGroupModel.closed_at >= start_utc,
                OrderGroupModel.closed_at < end_utc,
            )

        return [_group_to_entity(m) for m in q.all()]

    def get_by_id(self, group_id: UUID) -> Optional[OrderGroupEntity]:
        m = self._base_query().filter(OrderGroupModel.id == group_id).first()
        return _group_to_entity(m) if m else None

    def get_open_by_table(self, table_id: UUID) -> Optional[OrderGroupEntity]:
        m = self._base_query().filter(
            OrderGroupModel.table_id == table_id,
            OrderGroupModel.status == "abierto",
        ).first()
        return _group_to_entity(m) if m else None

    def create(self, user_id: UUID, table_id: Optional[UUID],
               customer_name: Optional[str], notes_group: Optional[str]) -> OrderGroupEntity:
        m = OrderGroupModel(
            user_id=user_id,
            table_id=table_id,
            customer_name=customer_name,
            notes_group=notes_group,
            status="abierto",
            total=Decimal("0"),
        )
        self._db.add(m)
        self._db.flush()
        return _group_to_entity(
            self._base_query().filter(OrderGroupModel.id == m.id).first()
        )

    def update_total(self, group_id: UUID, total: Decimal) -> None:
        self._db.query(OrderGroupModel).filter(
            OrderGroupModel.id == group_id
        ).update({"total": total})

    def close(self, group_id: UUID, table_id: Optional[UUID]) -> bool:
        m = self._db.query(OrderGroupModel).filter(OrderGroupModel.id == group_id).first()
        if not m:
            return False
        m.status = "cerrado"
        m.closed_at = datetime.now(LOCAL_TZ)
        # Liberar mesa si la hay
        if table_id:
            self._db.query(TableModel).filter(
                TableModel.id == table_id
            ).update({"status": "libre"})
        self._db.flush()
        return True

    def cancel(self, group_id: UUID, table_id: Optional[UUID]) -> bool:
        m = self._db.query(OrderGroupModel).filter(OrderGroupModel.id == group_id).first()
        if not m:
            return False
        m.status = "cancelado"
        m.closed_at = datetime.now(LOCAL_TZ)
        if table_id:
            self._db.query(TableModel).filter(
                TableModel.id == table_id
            ).update({"status": "libre"})
        self._db.flush()
        return True


# ── OrderRepository ───────────────────────────────────────────────────────────

class OrderRepository:

    def __init__(self, db: Session):
        self._db = db

    def _base_query(self):
        return self._db.query(OrderModel).options(_item_options())

    def get_by_id(self, order_id: UUID) -> Optional[OrderEntity]:
        m = self._base_query().filter(OrderModel.id == order_id).first()
        return _order_to_entity(m) if m else None

    def get_by_group(self, group_id: UUID) -> list[OrderEntity]:
        return [_order_to_entity(m) for m in
                self._base_query().filter(OrderModel.group_id == group_id).all()]

    def create(self, group_id: UUID, type: Optional[str],
               notes: Optional[str], disposables_qty: int) -> OrderModel:
        """Retorna el model directamente para poder agregar items en la misma tx."""
        m = OrderModel(
            group_id=group_id,
            status="pendiente",
            total=Decimal("0"),
            type=type,
            notes=notes,
            disposables_qty=disposables_qty,
        )
        self._db.add(m)
        self._db.flush()
        return m

    def update_total(self, order_id: UUID, total: Decimal) -> None:
        self._db.query(OrderModel).filter(
            OrderModel.id == order_id
        ).update({"total": total})

    def update_status(self, order_id: UUID, status: str) -> Optional[OrderEntity]:
        m = self._db.query(OrderModel).filter(OrderModel.id == order_id).first()
        if not m:
            return None
        m.status = status
        self._db.flush()
        return self.get_by_id(order_id)

    def mark_group_orders_delivered(self, group_id: UUID) -> None:
        """
        Marca como 'entregado' todas las órdenes de un grupo que todavía no
        estén 'cancelado'. Se usa al procesar el pago: mientras no exista un
        módulo de cocina que mueva pendiente -> preparacion -> listo -> entregado,
        el pago es la única señal real de que la orden se sirvió — sin esto,
        todo se queda en 'pendiente' para siempre y el reporte de estado de
        órdenes queda inservible.
        """
        self._db.query(OrderModel).filter(
            OrderModel.group_id == group_id,
            OrderModel.status != OrderStatus.cancelado,
        ).update({"status": OrderStatus.entregado}, synchronize_session=False)
        self._db.flush()

    # ── Helpers de precio ─────────────────────────────────────────────────────

    def get_product_price(self, product_id: UUID) -> Optional[Decimal]:
        m = self._db.query(ProductModel.sale_price).filter(
            ProductModel.id == product_id).first()
        return m.sale_price if m else None

    def get_variant_price(self, variant_id: UUID) -> Optional[Decimal]:
        m = self._db.query(ProductVariantModel.price).filter(
            ProductVariantModel.id == variant_id).first()
        return m.price if m else None

    def get_slot_price(self, slot_id: UUID) -> Optional[Decimal]:
        m = self._db.query(MenuDaySlotModel.menu_price).filter(
            MenuDaySlotModel.id == slot_id).first()
        return m.menu_price if m else None

    def decrement_slot_stock(self, slot_id: UUID, quantity: int = 1) -> bool:
        """Decrementa stock_current en `quantity`. Marca is_available=False si llega a 0."""
        m = self._db.query(MenuDaySlotModel).filter(
            MenuDaySlotModel.id == slot_id).first()
        if not m or m.stock_current < quantity:
            return False
        m.stock_current -= quantity
        if m.stock_current == 0:
            m.is_available = False
        self._db.flush()
        return True

    def restore_slot_stock(self, slot_id: UUID, quantity: int = 1) -> None:
        """
        Inversa de decrement_slot_stock — repone stock_current al cancelar
        una orden que ya lo había descontado. Reactiva is_available si el
        slot se había marcado agotado.
        """
        m = self._db.query(MenuDaySlotModel).filter(
            MenuDaySlotModel.id == slot_id).first()
        if not m:
            return
        m.stock_current += quantity
        if m.stock_current > 0:
            m.is_available = True
        self._db.flush()

    def restore_stock_for_order(self, order_id: UUID) -> None:
        """
        Repone el stock de todos los items de tipo 'menu' de una orden —
        se llama al cancelarla, para deshacer los decrementos hechos al
        crearla (orden A: 2 platos X → decrementa 2 → cancelar → +2).
        Solo 'menu' descuenta stock hoy; carta/bebida no tocan inventario.
        """
        items = (
            self._db.query(OrderItemModel)
            .filter(
                OrderItemModel.order_id == order_id,
                OrderItemModel.sale_type == "menu",
                OrderItemModel.menu_slot_id.isnot(None),
            )
            .all()
        )
        for item in items:
            self.restore_slot_stock(item.menu_slot_id, item.quantity)

    def count_menu_items_in_order(self, order_id: UUID) -> int:
        """Cuenta cuántos items de tipo 'menu' hay en la orden (para regla de entradas gratis)."""
        from sqlalchemy import func
        result = self._db.query(
            func.sum(OrderItemModel.quantity)
        ).filter(
            OrderItemModel.order_id == order_id,
            OrderItemModel.sale_type == "menu",
            OrderItemModel.is_free == False,
        ).scalar()
        return int(result or 0)

    def count_entry_items_in_order(self, order_id: UUID) -> int:
        """
        Cuenta cuántas unidades de tipo 'entrada' hay en la orden (gratis o
        pagadas). Se usa para saber cuánto cupo de entradas gratis ya se
        consumió; si solo contáramos las pagadas, una entrada ya marcada
        gratis nunca reduciría el cupo y todas las siguientes también
        saldrían gratis.
        """
        from sqlalchemy import func
        result = self._db.query(
            func.sum(OrderItemModel.quantity)
        ).filter(
            OrderItemModel.order_id == order_id,
            OrderItemModel.sale_type == "entrada",
        ).scalar()
        return int(result or 0)

    def add_item(self, order_id: UUID, product_id: UUID, sale_type: str,
                 quantity: int, unit_price: Decimal, subtotal: Decimal,
                 is_free: bool = False, is_auto: bool = False,
                 variant_id: Optional[UUID] = None,
                 menu_slot_id: Optional[UUID] = None,
                 parent_item_id: Optional[UUID] = None,
                 notes: Optional[str] = None) -> OrderItemModel:
        m = OrderItemModel(
            order_id=order_id,
            product_id=product_id,
            sale_type=sale_type,
            quantity=quantity,
            unit_price=unit_price,
            subtotal=subtotal,
            is_free=is_free,
            is_auto=is_auto,
            variant_id=variant_id,
            menu_slot_id=menu_slot_id,
            parent_item_id=parent_item_id,
            notes=notes,
        )
        self._db.add(m)
        self._db.flush()
        return m