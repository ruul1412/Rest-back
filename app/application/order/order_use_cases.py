# from uuid import UUID
# from decimal import Decimal
# from datetime import date as date_type
# from typing import Optional

# from fastapi import HTTPException

# from app.interfaces.schemas.order_schema import (
#     OrderGroupCreateRequest, OrderGroupResponse,
#     OrderCreateRequest, OrderResponse, OrderStatusRequest,
#     OrderItemResponse,
# )
# from app.infrastructure.repositories.order_repository import (
#     OrderGroupRepository, OrderRepository,
# )
# from app.domain.order.order_entity import OrderGroupEntity, OrderEntity, OrderItemEntity
# from app.domain.user.user_entity import UserEntity


# # ── Helpers ───────────────────────────────────────────────────────────────────

# def _item_resp(e: OrderItemEntity) -> OrderItemResponse:
#     return OrderItemResponse(
#         id=e.id, product_id=e.product_id, product_name=e.product_name,
#         sale_type=e.sale_type, quantity=e.quantity,
#         unit_price=e.unit_price, subtotal=e.subtotal,
#         is_free=e.is_free, is_auto=e.is_auto,
#         variant_id=e.variant_id, variant_name=e.variant_name,
#         menu_slot_id=e.menu_slot_id, parent_item_id=e.parent_item_id,
#         notes=e.notes,
#         children=[_item_resp(c) for c in e.children],
#     )


# def _order_resp(e: OrderEntity) -> OrderResponse:
#     return OrderResponse(
#         id=e.id, group_id=e.group_id, status=e.status,
#         total=e.total, type=e.type, notes=e.notes,
#         disposables_qty=e.disposables_qty,
#         items=[_item_resp(i) for i in e.items],
#     )


# def _group_resp(e: OrderGroupEntity) -> OrderGroupResponse:
#     return OrderGroupResponse(
#         id=e.id, user_id=e.user_id, status=e.status, total=e.total,
#         table_id=e.table_id, table_number=e.table_number,
#         customer_name=e.customer_name, notes_group=e.notes_group,
#         created_at=e.created_at, closed_at=e.closed_at,
#         orders=[_order_resp(o) for o in e.orders],
#     )


# # ── Helper: armar items para la comanda ───────────────────────────────────────

# def _build_comanda_items(order_items: list) -> list:
#     """
#     Convierte la lista de OrderItemEntity (ya jerárquica: cada item trae sus
#     adicionales en .children) en la estructura de dicts que espera
#     print_comanda/_consolidate.

#     IMPORTANTE: order_items aquí NO es una lista plana con padres e hijos
#     mezclados — el repositorio ya filtra y solo entrega items raíz
#     (parent_item_id is None), con sus adicionales anidados en item.children.
#     Por eso el armado tiene que ser recursivo sobre .children, no buscar
#     parent_item_id en la misma lista (eso nunca encuentra nada, porque los
#     hijos no están ahí).
#     """
#     def _to_dict(item) -> dict:
#         return {
#             "product_id":   str(item.product_id),
#             "product_name": item.product_name,
#             "sale_type":    item.sale_type,          # ← clave para _consolidate
#             "cantidad":     item.quantity,
#             "notas":        item.notes or "",
#             "variant_id":   str(item.variant_id) if item.variant_id else "",
#             "variant_name": item.variant_name or "",
#             "children":     [_to_dict(c) for c in (item.children or [])],
#         }

#     return [_to_dict(item) for item in order_items]


# def _recalculate_group_total(order_repo: OrderRepository,
#                               group_repo: OrderGroupRepository,
#                               group_id: UUID) -> None:
#     """
#     Suma el total de las órdenes del grupo y lo guarda en OrderGroupModel.total.

#     IMPORTANTE: excluye las órdenes con status 'cancelado' — una orden
#     cancelada no debe seguir aportando a lo que se le cobra a la mesa.
#     Se usa tanto al crear una orden como al cambiar su status (p.ej. al
#     cancelarla), para que el total de la mesa quede siempre consistente.
#     """
#     from sqlalchemy import func
#     total = order_repo._db.query(
#         func.sum(OrderModel.total)
#     ).filter(
#         OrderModel.group_id == group_id,
#         OrderModel.status != "cancelado",
#     ).scalar()
#     group_repo.update_total(group_id, Decimal(total or 0))


# # ── OrderGroup Use Cases ──────────────────────────────────────────────────────

# class ListOrderGroupsUseCase:
#     def __init__(self, repo: OrderGroupRepository): self._repo = repo

#     def execute(self, status: Optional[str] = None,
#                 date: Optional[date_type] = None) -> list[OrderGroupResponse]:
#         return [_group_resp(e) for e in self._repo.get_all(status, date)]


# class GetOrderGroupUseCase:
#     def __init__(self, repo: OrderGroupRepository): self._repo = repo

#     def execute(self, group_id: UUID) -> OrderGroupResponse:
#         entity = self._repo.get_by_id(group_id)
#         if not entity:
#             raise HTTPException(status_code=404, detail="Grupo no encontrado")
#         return _group_resp(entity)


# class CreateOrderGroupUseCase:
#     def __init__(self, repo: OrderGroupRepository): self._repo = repo

#     def execute(self, data: OrderGroupCreateRequest,
#                 current_user: UserEntity) -> OrderGroupResponse:
#         if data.table_id:
#             existing = self._repo.get_open_by_table(data.table_id)
#             if existing:
#                 raise HTTPException(
#                     status_code=400,
#                     detail="La mesa ya tiene una cuenta abierta",
#                 )
#             from app.infrastructure.models.table_model import TableModel
#             self._repo._db.query(TableModel).filter(
#                 TableModel.id == data.table_id
#             ).update({"status": "ocupada"})

#         entity = self._repo.create(
#             user_id=current_user.id,
#             table_id=data.table_id,
#             customer_name=data.customer_name,
#             notes_group=data.notes_group,
#         )
#         return _group_resp(entity)


# class CloseOrderGroupUseCase:
#     def __init__(self, repo: OrderGroupRepository): self._repo = repo

#     def execute(self, group_id: UUID) -> dict:
#         entity = self._repo.get_by_id(group_id)
#         if not entity:
#             raise HTTPException(status_code=404, detail="Grupo no encontrado")
#         if entity.status != "abierto":
#             raise HTTPException(status_code=400, detail="El grupo no está abierto")

#         self._repo.close(group_id, entity.table_id)
#         return {"detail": "Cuenta cerrada correctamente"}


# class CancelOrderGroupUseCase:
#     def __init__(self, group_repo: OrderGroupRepository, order_repo: OrderRepository):
#         self._group_repo = group_repo
#         self._order_repo = order_repo

#     def execute(self, group_id: UUID) -> dict:
#         entity = self._group_repo.get_by_id(group_id)
#         if not entity:
#             raise HTTPException(status_code=404, detail="Grupo no encontrado")
#         if entity.status == "cerrado":
#             raise HTTPException(status_code=400, detail="No se puede cancelar un grupo cerrado")

#         # Restablecer stock de cada orden del grupo que no estuviera ya cancelada
#         for order in entity.orders:
#             if order.status != "cancelado":
#                 self._order_repo.restore_stock_for_order(order.id)

#         self._group_repo.cancel(group_id, entity.table_id)
#         return {"detail": "Grupo cancelado"}


# # ── Order Use Cases ───────────────────────────────────────────────────────────

# class GetOrderUseCase:
#     def __init__(self, repo: OrderRepository): self._repo = repo

#     def execute(self, order_id: UUID) -> OrderResponse:
#         entity = self._repo.get_by_id(order_id)
#         if not entity:
#             raise HTTPException(status_code=404, detail="Orden no encontrada")
#         return _order_resp(entity)


# class CreateOrderUseCase:
#     """
#     Crea una orden con sus items aplicando las reglas de negocio:
#       - menu    → precio del slot, descuenta stock_current
#       - carta   → precio de sale_price del producto
#       - bebida  → precio de la variante (variant_id obligatorio)
#       - entrada → gratis hasta el límite de platos de menú pedidos
#       - adicional → precio de sale_price, lleva parent_item_id
#     """
#     def __init__(self, group_repo: OrderGroupRepository,
#                  order_repo: OrderRepository):
#         self._group_repo = group_repo
#         self._order_repo = order_repo

#     def execute(self, group_id: UUID,
#                 data: OrderCreateRequest) -> OrderResponse:

#         group = self._group_repo.get_by_id(group_id)
#         if not group:
#             raise HTTPException(status_code=404, detail="Grupo no encontrado")
#         if group.status != "abierto":
#             raise HTTPException(status_code=400, detail="El grupo no está abierto")

#         order_model = self._order_repo.create(
#             group_id=group_id,
#             type=data.type,
#             notes=data.notes,
#             disposables_qty=data.disposables_qty,
#         )
#         order_id = order_model.id
#         order_total = Decimal("0")

#         for item_req in data.items:

#             if item_req.sale_type == "menu":
#                 if not item_req.menu_slot_id:
#                     raise HTTPException(
#                         status_code=400,
#                         detail="Los items de tipo 'menu' requieren menu_slot_id",
#                     )
#                 unit_price = self._order_repo.get_slot_price(item_req.menu_slot_id)
#                 if unit_price is None:
#                     raise HTTPException(status_code=404, detail="Slot de menú no encontrado")

#                 ok = self._order_repo.decrement_slot_stock(item_req.menu_slot_id)
#                 if not ok:
#                     raise HTTPException(
#                         status_code=400,
#                         detail="No hay stock disponible para ese plato del menú",
#                     )

#             elif item_req.sale_type == "entrada":
#                 unit_price = self._order_repo.get_product_price(item_req.product_id)
#                 if unit_price is None:
#                     raise HTTPException(status_code=404, detail="Producto no encontrado")

#                 menu_count   = self._order_repo.count_menu_items_in_order(order_id)
#                 entry_count  = self._order_repo.count_entry_items_in_order(order_id)
#                 entries_free = max(0, menu_count - entry_count)
#                 is_free      = entries_free >= item_req.quantity
#                 if is_free:
#                     unit_price = Decimal("0")

#             elif item_req.sale_type == "carta":
#                 if item_req.variant_id:
#                     unit_price = self._order_repo.get_variant_price(item_req.variant_id)
#                     if unit_price is None:
#                         raise HTTPException(status_code=404, detail="Variante no encontrada")
#                 else:
#                     unit_price = self._order_repo.get_product_price(item_req.product_id)
#                     if unit_price is None:
#                         raise HTTPException(status_code=404, detail="Producto no encontrado")
#                 is_free = False

#             elif item_req.sale_type == "adicional":
#                 if not item_req.parent_item_id:
#                     raise HTTPException(
#                         status_code=400,
#                         detail="Los adicionales requieren parent_item_id",
#                     )
#                 unit_price = self._order_repo.get_product_price(item_req.product_id)
#                 if unit_price is None:
#                     raise HTTPException(status_code=404, detail="Producto no encontrado")
#                 is_free = False

#             else:
#                 raise HTTPException(status_code=400, detail=f"sale_type inválido: {item_req.sale_type}")

#             subtotal = unit_price * item_req.quantity
#             order_total += subtotal

#             parent_model = self._order_repo.add_item(
#                 order_id=order_id,
#                 product_id=item_req.product_id,
#                 sale_type=item_req.sale_type,
#                 quantity=item_req.quantity,
#                 unit_price=unit_price,
#                 subtotal=subtotal,
#                 is_free=item_req.sale_type == "entrada" and unit_price == Decimal("0"),
#                 variant_id=item_req.variant_id,
#                 menu_slot_id=item_req.menu_slot_id,
#                 parent_item_id=item_req.parent_item_id,
#                 notes=item_req.notes,
#             )

#             # Adicionales anidados del item recien creado.
#             # El front los manda como item.adicionales = [{product_id, quantity}].
#             # Aqui ya conocemos el id real del padre (parent_model.id) recien
#             # flusheado, asi que los creamos como items hijos sale_type='adicional'.
#             for ad in (item_req.adicionales or []):
#                 ad_price = self._order_repo.get_product_price(ad.product_id)
#                 if ad_price is None:
#                     raise HTTPException(status_code=404, detail="Adicional no encontrado")

#                 ad_subtotal = ad_price * ad.quantity
#                 order_total += ad_subtotal

#                 self._order_repo.add_item(
#                     order_id=order_id,
#                     product_id=ad.product_id,
#                     sale_type="adicional",
#                     quantity=ad.quantity,
#                     unit_price=ad_price,
#                     subtotal=ad_subtotal,
#                     is_free=False,
#                     variant_id=None,
#                     menu_slot_id=None,
#                     parent_item_id=parent_model.id,
#                     notes=ad.notes,
#                 )

#         # Descartables: S/ 1.00 c/u — incluidos en el total de la orden
#         DISPOSABLE_PRICE = Decimal("1.00")
#         order_total += DISPOSABLE_PRICE * Decimal(data.disposables_qty or 0)

#         self._order_repo.update_total(order_id, order_total)
#         _recalculate_group_total(self._order_repo, self._group_repo, group_id)

#         # Recuperar orden completa para imprimir
#         order_entity = self._order_repo.get_by_id(order_id)

#         # ── Imprimir comanda (fallo silencioso) ───────────────────────────────
#         try:
#             from app.core.printer import print_comanda
#             print_comanda(
#                 tipo=data.type or "mesa",
#                 cliente_nombre=group.customer_name,
#                 notas_group=group.notes_group,
#                 items=_build_comanda_items(order_entity.items),  # ← estructura correcta
#             )
#         except Exception as e:
#             print(f"[PRINTER] No se pudo imprimir la comanda: {e}")

#         return _order_resp(order_entity)


# class UpdateOrderStatusUseCase:
#     def __init__(self, repo: OrderRepository, group_repo: OrderGroupRepository):
#         self._repo = repo
#         self._group_repo = group_repo

#     def execute(self, order_id: UUID, data: OrderStatusRequest) -> OrderResponse:
#         current = self._repo.get_by_id(order_id)
#         if not current:
#             raise HTTPException(status_code=404, detail="Orden no encontrada")

#         # Al cancelar la orden se restablece el stock de sus platos de menú —
#         # solo una vez: si ya estaba cancelada, no se vuelve a sumar el stock.
#         if data.status == "cancelado" and current.status != "cancelado":
#             self._repo.restore_stock_for_order(order_id)

#         entity = self._repo.update_status(order_id, data.status)
#         if not entity:
#             raise HTTPException(status_code=404, detail="Orden no encontrada")

#         # El total de la mesa/grupo depende de qué órdenes siguen activas
#         # (una orden cancelada ya no debe sumar), así que se recalcula cada
#         # vez que cambia el status de una orden.
#         _recalculate_group_total(self._repo, self._group_repo, entity.group_id)

#         return _order_resp(entity)


# # Import necesario para _recalculate_group_total
# from app.infrastructure.models.order_model import OrderModel


from uuid import UUID
from decimal import Decimal
from datetime import date as date_type
from typing import Optional

from fastapi import HTTPException

from app.interfaces.schemas.order_schema import (
    OrderGroupCreateRequest, OrderGroupResponse,
    OrderCreateRequest, OrderResponse, OrderStatusRequest,
    OrderItemResponse,
)
from app.infrastructure.repositories.order_repository import (
    OrderGroupRepository, OrderRepository,
)
from app.domain.order.order_entity import OrderGroupEntity, OrderEntity, OrderItemEntity
from app.domain.user.user_entity import UserEntity


# ── Helpers ───────────────────────────────────────────────────────────────────

def _item_resp(e: OrderItemEntity) -> OrderItemResponse:
    return OrderItemResponse(
        id=e.id, product_id=e.product_id, product_name=e.product_name,
        sale_type=e.sale_type, quantity=e.quantity,
        unit_price=e.unit_price, subtotal=e.subtotal,
        is_free=e.is_free, is_auto=e.is_auto,
        variant_id=e.variant_id, variant_name=e.variant_name,
        menu_slot_id=e.menu_slot_id, parent_item_id=e.parent_item_id,
        notes=e.notes,
        children=[_item_resp(c) for c in e.children],
    )


def _order_resp(e: OrderEntity) -> OrderResponse:
    return OrderResponse(
        id=e.id, group_id=e.group_id, status=e.status,
        total=e.total, type=e.type, notes=e.notes,
        disposables_qty=e.disposables_qty,
        items=[_item_resp(i) for i in e.items],
    )


def _group_resp(e: OrderGroupEntity) -> OrderGroupResponse:
    return OrderGroupResponse(
        id=e.id, user_id=e.user_id, status=e.status, total=e.total,
        table_id=e.table_id, table_number=e.table_number,
        customer_name=e.customer_name, notes_group=e.notes_group,
        created_at=e.created_at, closed_at=e.closed_at,
        orders=[_order_resp(o) for o in e.orders],
    )


# ── Helper: armar items para la comanda ───────────────────────────────────────

def _build_comanda_items(order_items: list) -> list:
    """
    Convierte la lista de OrderItemEntity (ya jerárquica: cada item trae sus
    adicionales en .children) en la estructura de dicts que espera
    print_comanda/_consolidate.

    IMPORTANTE: order_items aquí NO es una lista plana con padres e hijos
    mezclados — el repositorio ya filtra y solo entrega items raíz
    (parent_item_id is None), con sus adicionales anidados en item.children.
    Por eso el armado tiene que ser recursivo sobre .children, no buscar
    parent_item_id en la misma lista (eso nunca encuentra nada, porque los
    hijos no están ahí).
    """
    def _to_dict(item) -> dict:
        return {
            "product_id":   str(item.product_id),
            "product_name": item.product_name,
            "sale_type":    item.sale_type,          # ← clave para _consolidate
            "cantidad":     item.quantity,
            "notas":        item.notes or "",
            "variant_id":   str(item.variant_id) if item.variant_id else "",
            "variant_name": item.variant_name or "",
            "children":     [_to_dict(c) for c in (item.children or [])],
        }

    return [_to_dict(item) for item in order_items]


def _recalculate_group_total(order_repo: OrderRepository,
                              group_repo: OrderGroupRepository,
                              group_id: UUID) -> None:
    """
    Suma el total de las órdenes del grupo y lo guarda en OrderGroupModel.total.

    IMPORTANTE: excluye las órdenes con status 'cancelado' — una orden
    cancelada no debe seguir aportando a lo que se le cobra a la mesa.
    Se usa tanto al crear una orden como al cambiar su status (p.ej. al
    cancelarla), para que el total de la mesa quede siempre consistente.
    """
    from sqlalchemy import func
    total = order_repo._db.query(
        func.sum(OrderModel.total)
    ).filter(
        OrderModel.group_id == group_id,
        OrderModel.status != "cancelado",
    ).scalar()
    group_repo.update_total(group_id, Decimal(total or 0))


# ── OrderGroup Use Cases ──────────────────────────────────────────────────────

class ListOrderGroupsUseCase:
    def __init__(self, repo: OrderGroupRepository): self._repo = repo

    def execute(self, status: Optional[str] = None,
                date: Optional[date_type] = None) -> list[OrderGroupResponse]:
        return [_group_resp(e) for e in self._repo.get_all(status, date)]


class GetOrderGroupUseCase:
    def __init__(self, repo: OrderGroupRepository): self._repo = repo

    def execute(self, group_id: UUID) -> OrderGroupResponse:
        entity = self._repo.get_by_id(group_id)
        if not entity:
            raise HTTPException(status_code=404, detail="Grupo no encontrado")
        return _group_resp(entity)


class CreateOrderGroupUseCase:
    def __init__(self, repo: OrderGroupRepository): self._repo = repo

    def execute(self, data: OrderGroupCreateRequest,
                current_user: UserEntity) -> OrderGroupResponse:
        if data.table_id:
            existing = self._repo.get_open_by_table(data.table_id)
            if existing:
                raise HTTPException(
                    status_code=400,
                    detail="La mesa ya tiene una cuenta abierta",
                )
            from app.infrastructure.models.table_model import TableModel
            self._repo._db.query(TableModel).filter(
                TableModel.id == data.table_id
            ).update({"status": "ocupada"})

        entity = self._repo.create(
            user_id=current_user.id,
            table_id=data.table_id,
            customer_name=data.customer_name,
            notes_group=data.notes_group,
        )
        return _group_resp(entity)


class CloseOrderGroupUseCase:
    def __init__(self, repo: OrderGroupRepository): self._repo = repo

    def execute(self, group_id: UUID) -> dict:
        entity = self._repo.get_by_id(group_id)
        if not entity:
            raise HTTPException(status_code=404, detail="Grupo no encontrado")
        if entity.status != "abierto":
            raise HTTPException(status_code=400, detail="El grupo no está abierto")

        self._repo.close(group_id, entity.table_id)
        return {"detail": "Cuenta cerrada correctamente"}


class CancelOrderGroupUseCase:
    def __init__(self, group_repo: OrderGroupRepository, order_repo: OrderRepository):
        self._group_repo = group_repo
        self._order_repo = order_repo

    def execute(self, group_id: UUID) -> dict:
        entity = self._group_repo.get_by_id(group_id)
        if not entity:
            raise HTTPException(status_code=404, detail="Grupo no encontrado")
        if entity.status == "cerrado":
            raise HTTPException(status_code=400, detail="No se puede cancelar un grupo cerrado")

        # Restablecer stock de cada orden del grupo que no estuviera ya cancelada
        for order in entity.orders:
            if order.status != "cancelado":
                self._order_repo.restore_stock_for_order(order.id)

        self._group_repo.cancel(group_id, entity.table_id)
        return {"detail": "Grupo cancelado"}


# ── Order Use Cases ───────────────────────────────────────────────────────────

class GetOrderUseCase:
    def __init__(self, repo: OrderRepository): self._repo = repo

    def execute(self, order_id: UUID) -> OrderResponse:
        entity = self._repo.get_by_id(order_id)
        if not entity:
            raise HTTPException(status_code=404, detail="Orden no encontrada")
        return _order_resp(entity)


class CreateOrderUseCase:
    """
    Crea una orden con sus items aplicando las reglas de negocio:
      - menu    → precio del slot, descuenta stock_current
      - carta   → precio de sale_price del producto
      - bebida  → precio de la variante (variant_id obligatorio)
      - entrada → gratis hasta el límite de platos de menú pedidos
      - adicional → precio de sale_price, lleva parent_item_id
    """
    def __init__(self, group_repo: OrderGroupRepository,
                 order_repo: OrderRepository):
        self._group_repo = group_repo
        self._order_repo = order_repo

    def execute(self, group_id: UUID,
                data: OrderCreateRequest) -> OrderResponse:

        group = self._group_repo.get_by_id(group_id)
        if not group:
            raise HTTPException(status_code=404, detail="Grupo no encontrado")
        if group.status != "abierto":
            raise HTTPException(status_code=400, detail="El grupo no está abierto")

        order_model = self._order_repo.create(
            group_id=group_id,
            type=data.type,
            notes=data.notes,
            disposables_qty=data.disposables_qty,
        )
        order_id = order_model.id
        order_total = Decimal("0")

        for item_req in data.items:

            if item_req.sale_type == "menu":
                if not item_req.menu_slot_id:
                    raise HTTPException(
                        status_code=400,
                        detail="Los items de tipo 'menu' requieren menu_slot_id",
                    )
                unit_price = self._order_repo.get_slot_price(item_req.menu_slot_id)
                if unit_price is None:
                    raise HTTPException(status_code=404, detail="Slot de menú no encontrado")

                ok = self._order_repo.decrement_slot_stock(item_req.menu_slot_id, item_req.quantity)
                if not ok:
                    raise HTTPException(
                        status_code=400,
                        detail="No hay stock disponible para ese plato del menú",
                    )

            elif item_req.sale_type == "entrada":
                unit_price = self._order_repo.get_product_price(item_req.product_id)
                if unit_price is None:
                    raise HTTPException(status_code=404, detail="Producto no encontrado")

                menu_count   = self._order_repo.count_menu_items_in_order(order_id)
                entry_count  = self._order_repo.count_entry_items_in_order(order_id)
                entries_free = max(0, menu_count - entry_count)
                is_free      = entries_free >= item_req.quantity
                if is_free:
                    unit_price = Decimal("0")

            elif item_req.sale_type == "carta":
                if item_req.variant_id:
                    unit_price = self._order_repo.get_variant_price(item_req.variant_id)
                    if unit_price is None:
                        raise HTTPException(status_code=404, detail="Variante no encontrada")
                else:
                    unit_price = self._order_repo.get_product_price(item_req.product_id)
                    if unit_price is None:
                        raise HTTPException(status_code=404, detail="Producto no encontrado")
                is_free = False

            elif item_req.sale_type == "adicional":
                if not item_req.parent_item_id:
                    raise HTTPException(
                        status_code=400,
                        detail="Los adicionales requieren parent_item_id",
                    )
                unit_price = self._order_repo.get_product_price(item_req.product_id)
                if unit_price is None:
                    raise HTTPException(status_code=404, detail="Producto no encontrado")
                is_free = False

            else:
                raise HTTPException(status_code=400, detail=f"sale_type inválido: {item_req.sale_type}")

            subtotal = unit_price * item_req.quantity
            order_total += subtotal

            parent_model = self._order_repo.add_item(
                order_id=order_id,
                product_id=item_req.product_id,
                sale_type=item_req.sale_type,
                quantity=item_req.quantity,
                unit_price=unit_price,
                subtotal=subtotal,
                is_free=item_req.sale_type == "entrada" and unit_price == Decimal("0"),
                variant_id=item_req.variant_id,
                menu_slot_id=item_req.menu_slot_id,
                parent_item_id=item_req.parent_item_id,
                notes=item_req.notes,
            )

            # Adicionales anidados del item recien creado.
            # El front los manda como item.adicionales = [{product_id, quantity}].
            # Aqui ya conocemos el id real del padre (parent_model.id) recien
            # flusheado, asi que los creamos como items hijos sale_type='adicional'.
            for ad in (item_req.adicionales or []):
                ad_price = self._order_repo.get_product_price(ad.product_id)
                if ad_price is None:
                    raise HTTPException(status_code=404, detail="Adicional no encontrado")

                ad_subtotal = ad_price * ad.quantity
                order_total += ad_subtotal

                self._order_repo.add_item(
                    order_id=order_id,
                    product_id=ad.product_id,
                    sale_type="adicional",
                    quantity=ad.quantity,
                    unit_price=ad_price,
                    subtotal=ad_subtotal,
                    is_free=False,
                    variant_id=None,
                    menu_slot_id=None,
                    parent_item_id=parent_model.id,
                    notes=ad.notes,
                )

        # Descartables: S/ 1.00 c/u — incluidos en el total de la orden
        DISPOSABLE_PRICE = Decimal("1.00")
        order_total += DISPOSABLE_PRICE * Decimal(data.disposables_qty or 0)

        self._order_repo.update_total(order_id, order_total)
        _recalculate_group_total(self._order_repo, self._group_repo, group_id)

        # Recuperar orden completa para imprimir
        order_entity = self._order_repo.get_by_id(order_id)

        # ── Imprimir comanda (fallo silencioso) ───────────────────────────────
        try:
            from app.core.printer import print_comanda
            print_comanda(
                tipo=data.type or "mesa",
                cliente_nombre=group.customer_name,
                notas_group=group.notes_group,
                items=_build_comanda_items(order_entity.items),  # ← estructura correcta
            )
        except Exception as e:
            print(f"[PRINTER] No se pudo imprimir la comanda: {e}")

        return _order_resp(order_entity)


class UpdateOrderStatusUseCase:
    def __init__(self, repo: OrderRepository, group_repo: OrderGroupRepository):
        self._repo = repo
        self._group_repo = group_repo

    def execute(self, order_id: UUID, data: OrderStatusRequest) -> OrderResponse:
        current = self._repo.get_by_id(order_id)
        if not current:
            raise HTTPException(status_code=404, detail="Orden no encontrada")

        # Al cancelar la orden se restablece el stock de sus platos de menú —
        # solo una vez: si ya estaba cancelada, no se vuelve a sumar el stock.
        if data.status == "cancelado" and current.status != "cancelado":
            self._repo.restore_stock_for_order(order_id)

        entity = self._repo.update_status(order_id, data.status)
        if not entity:
            raise HTTPException(status_code=404, detail="Orden no encontrada")

        # El total de la mesa/grupo depende de qué órdenes siguen activas
        # (una orden cancelada ya no debe sumar), así que se recalcula cada
        # vez que cambia el status de una orden.
        _recalculate_group_total(self._repo, self._group_repo, entity.group_id)

        return _order_resp(entity)


# Import necesario para _recalculate_group_total
from app.infrastructure.models.order_model import OrderModel