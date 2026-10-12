# from uuid import UUID
# from decimal import Decimal

# from fastapi import HTTPException

# from app.interfaces.schemas.payment_schema import (
#     PaymentCreateRequest, PaymentResponse, SplitResponse,
# )
# from app.infrastructure.repositories.payment_repository import PaymentRepository
# from app.infrastructure.repositories.order_repository import OrderGroupRepository
# from app.domain.payment.payment_entity import PaymentEntity


# # ── Helper ────────────────────────────────────────────────────────────────────

# def _resp(e: PaymentEntity) -> PaymentResponse:
#     return PaymentResponse(
#         id=e.id,
#         group_id=e.group_id,
#         amount=e.amount,
#         status=e.status,
#         pagado_at=e.pagado_at,
#         splits=[
#             SplitResponse(id=s.id, method=s.method,
#                           amount=s.amount, reference=s.reference)
#             for s in e.splits
#         ],
#     )


# # ── Use Cases ─────────────────────────────────────────────────────────────────

# class GetPaymentByGroupUseCase:
#     def __init__(self, repo: PaymentRepository): self._repo = repo

#     def execute(self, group_id: UUID) -> PaymentResponse:
#         entity = self._repo.get_by_group(group_id)
#         if not entity:
#             raise HTTPException(status_code=404, detail="Pago no encontrado")
#         return _resp(entity)


# class ProcessPaymentUseCase:
#     """
#     Procesa el pago de un grupo:
#       1. Verifica que el grupo existe y está abierto
#       2. Verifica que no esté ya pagado
#       3. Valida que los splits sumen exactamente el total del grupo
#       4. Crea el pago + splits y cierra el grupo + libera la mesa
#     """
#     def __init__(self, pay_repo: PaymentRepository,
#                  group_repo: OrderGroupRepository):
#         self._pay_repo   = pay_repo
#         self._group_repo = group_repo

#     def execute(self, group_id: UUID,
#                 data: PaymentCreateRequest) -> PaymentResponse:

#         # Verificar grupo abierto
#         if not self._pay_repo.group_exists_and_open(group_id):
#             raise HTTPException(
#                 status_code=400,
#                 detail="El grupo no existe o no está abierto",
#             )

#         # Verificar que no esté ya pagado
#         if self._pay_repo.already_paid(group_id):
#             raise HTTPException(
#                 status_code=400,
#                 detail="Este grupo ya fue pagado",
#             )

#         # Obtener total del grupo
#         group_total = self._pay_repo.get_group_total(group_id)

#         # Validar que los splits sumen el total exacto
#         splits_total = sum(s.amount for s in data.splits)
#         if splits_total != group_total:
#             raise HTTPException(
#                 status_code=400,
#                 detail=(
#                     f"Los splits suman S/{splits_total:.2f} "
#                     f"pero el total del grupo es S/{group_total:.2f}"
#                 ),
#             )

#         # Crear pago + splits
#         entity = self._pay_repo.create_and_pay(
#             group_id=group_id,
#             amount=group_total,
#             splits=[
#                 {"method": s.method, "amount": s.amount, "reference": s.reference}
#                 for s in data.splits
#             ],
#         )

#         # Cerrar grupo y liberar mesa
#         group = self._group_repo.get_by_id(group_id)
#         self._group_repo.close(group_id, group.table_id if group else None)

#         return _resp(entity)


# class CancelPaymentUseCase:
#     def __init__(self, pay_repo: PaymentRepository,
#                  group_repo: OrderGroupRepository):
#         self._pay_repo   = pay_repo
#         self._group_repo = group_repo

#     def execute(self, group_id: UUID) -> dict:
#         entity = self._pay_repo.get_by_group(group_id)
#         if not entity:
#             raise HTTPException(status_code=404, detail="Pago no encontrado")
#         if entity.status != "pagado":
#             raise HTTPException(
#                 status_code=400,
#                 detail="Solo se puede cancelar un pago en estado 'pagado'",
#             )

#         self._pay_repo.cancel(entity.id)

#         # Reabrir el grupo
#         group = self._group_repo.get_by_id(group_id)
#         if group:
#             from app.infrastructure.models.order_group_model import OrderGroupModel
#             self._pay_repo._db.query(OrderGroupModel).filter(
#                 OrderGroupModel.id == group_id
#             ).update({"status": "abierto"})

#         return {"detail": "Pago cancelado y grupo reabierto"}

from uuid import UUID
from decimal import Decimal

from fastapi import HTTPException

from app.interfaces.schemas.payment_schema import (
    PaymentCreateRequest, PaymentResponse, SplitResponse,
)
from app.infrastructure.repositories.payment_repository import PaymentRepository
from app.infrastructure.repositories.order_repository import OrderGroupRepository, OrderRepository
from app.domain.payment.payment_entity import PaymentEntity


# ── Helper ────────────────────────────────────────────────────────────────────

def _resp(e: PaymentEntity) -> PaymentResponse:
    return PaymentResponse(
        id=e.id,
        group_id=e.group_id,
        amount=e.amount,
        status=e.status,
        pagado_at=e.pagado_at,
        splits=[
            SplitResponse(id=s.id, method=s.method,
                          amount=s.amount, reference=s.reference)
            for s in e.splits
        ],
    )


# ── Use Cases ─────────────────────────────────────────────────────────────────

class GetPaymentByGroupUseCase:
    def __init__(self, repo: PaymentRepository): self._repo = repo

    def execute(self, group_id: UUID) -> PaymentResponse:
        entity = self._repo.get_by_group(group_id)
        if not entity:
            raise HTTPException(status_code=404, detail="Pago no encontrado")
        return _resp(entity)


class ProcessPaymentUseCase:
    """
    Procesa el pago de un grupo:
      1. Verifica que el grupo existe y está abierto
      2. Verifica que no esté ya pagado
      3. Valida que los splits sumen exactamente el total del grupo
      4. Crea el pago + splits y cierra el grupo + libera la mesa
    """
    def __init__(self, pay_repo: PaymentRepository,
                 group_repo: OrderGroupRepository,
                 order_repo: OrderRepository):
        self._pay_repo   = pay_repo
        self._group_repo = group_repo
        self._order_repo = order_repo

    def execute(self, group_id: UUID,
                data: PaymentCreateRequest) -> PaymentResponse:

        # Verificar grupo abierto
        if not self._pay_repo.group_exists_and_open(group_id):
            raise HTTPException(
                status_code=400,
                detail="El grupo no existe o no está abierto",
            )

        # Verificar que no esté ya pagado
        if self._pay_repo.already_paid(group_id):
            raise HTTPException(
                status_code=400,
                detail="Este grupo ya fue pagado",
            )

        # Obtener total del grupo
        group_total = self._pay_repo.get_group_total(group_id)

        # Validar que los splits sumen el total exacto
        splits_total = sum(s.amount for s in data.splits)
        if splits_total != group_total:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Los splits suman S/{splits_total:.2f} "
                    f"pero el total del grupo es S/{group_total:.2f}"
                ),
            )

        # Crear pago + splits
        entity = self._pay_repo.create_and_pay(
            group_id=group_id,
            amount=group_total,
            splits=[
                {"method": s.method, "amount": s.amount, "reference": s.reference}
                for s in data.splits
            ],
        )

        # Cerrar grupo y liberar mesa
        group = self._group_repo.get_by_id(group_id)
        self._group_repo.close(group_id, group.table_id if group else None)

        # Sin módulo de cocina todavía: el pago es la señal de que la orden
        # se sirvió, así que se marca 'entregado' para no ensuciar el reporte
        # de estado de órdenes (que si no, se queda todo en 'pendiente').
        self._order_repo.mark_group_orders_delivered(group_id)

        return _resp(entity)


class CancelPaymentUseCase:
    def __init__(self, pay_repo: PaymentRepository,
                 group_repo: OrderGroupRepository):
        self._pay_repo   = pay_repo
        self._group_repo = group_repo

    def execute(self, group_id: UUID) -> dict:
        entity = self._pay_repo.get_by_group(group_id)
        if not entity:
            raise HTTPException(status_code=404, detail="Pago no encontrado")
        if entity.status != "pagado":
            raise HTTPException(
                status_code=400,
                detail="Solo se puede cancelar un pago en estado 'pagado'",
            )

        self._pay_repo.cancel(entity.id)

        # Reabrir el grupo
        group = self._group_repo.get_by_id(group_id)
        if group:
            from app.infrastructure.models.order_group_model import OrderGroupModel
            self._pay_repo._db.query(OrderGroupModel).filter(
                OrderGroupModel.id == group_id
            ).update({"status": "abierto"})

        return {"detail": "Pago cancelado y grupo reabierto"}