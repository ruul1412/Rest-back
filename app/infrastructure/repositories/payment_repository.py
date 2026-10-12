from typing import Optional
from uuid import UUID
from decimal import Decimal
from datetime import datetime, timezone

from sqlalchemy.orm import Session, joinedload

from app.infrastructure.models.payment_model import PaymentModel
from app.infrastructure.models.payment_split_model import PaymentSplitModel
from app.infrastructure.models.order_group_model import OrderGroupModel
from app.domain.payment.payment_entity import PaymentEntity, PaymentSplitEntity


# ── Mappers ───────────────────────────────────────────────────────────────────

def _split_to_entity(m: PaymentSplitModel) -> PaymentSplitEntity:
    return PaymentSplitEntity(
        id=m.id, method=m.method,
        amount=m.amount, reference=m.reference,
    )


def _payment_to_entity(m: PaymentModel) -> PaymentEntity:
    return PaymentEntity(
        id=m.id,
        group_id=m.group_id,
        amount=m.amount,
        status=m.status,
        pagado_at=m.pagado_at,
        splits=[_split_to_entity(s) for s in (m.splits or [])],
    )


# ── PaymentRepository ─────────────────────────────────────────────────────────

class PaymentRepository:

    def __init__(self, db: Session):
        self._db = db

    def _base_query(self):
        return (
            self._db.query(PaymentModel)
            .options(joinedload(PaymentModel.splits))
        )

    def get_by_id(self, payment_id: UUID) -> Optional[PaymentEntity]:
        m = self._base_query().filter(PaymentModel.id == payment_id).first()
        return _payment_to_entity(m) if m else None

    def get_by_group(self, group_id: UUID) -> Optional[PaymentEntity]:
        m = self._base_query().filter(PaymentModel.group_id == group_id).first()
        return _payment_to_entity(m) if m else None

    def get_group_total(self, group_id: UUID) -> Decimal:
        m = self._db.query(OrderGroupModel.total).filter(
            OrderGroupModel.id == group_id
        ).first()
        return m.total if m else Decimal("0")

    def group_exists_and_open(self, group_id: UUID) -> bool:
        m = self._db.query(OrderGroupModel.status).filter(
            OrderGroupModel.id == group_id
        ).first()
        return m and m.status == "abierto"

    def already_paid(self, group_id: UUID) -> bool:
        m = self._db.query(PaymentModel.status).filter(
            PaymentModel.group_id == group_id
        ).first()
        return m and m.status == "pagado"

    def create_and_pay(self, group_id: UUID, amount: Decimal,
                       splits: list[dict]) -> PaymentEntity:
        """
        Crea el pago, agrega los splits y lo marca como pagado en una sola operación.
        """
        now = datetime.now(timezone.utc)

        payment = PaymentModel(
            group_id=group_id,
            amount=amount,
            status="pagado",
            pagado_at=now,
        )
        self._db.add(payment)
        self._db.flush()

        for s in splits:
            self._db.add(PaymentSplitModel(
                payment_id=payment.id,
                method=s["method"],
                amount=s["amount"],
                reference=s.get("reference"),
            ))

        self._db.flush()
        return _payment_to_entity(
            self._base_query().filter(PaymentModel.id == payment.id).first()
        )

    def cancel(self, payment_id: UUID) -> bool:
        m = self._db.query(PaymentModel).filter(PaymentModel.id == payment_id).first()
        if not m:
            return False
        m.status = "cancelado"
        self._db.flush()
        return True