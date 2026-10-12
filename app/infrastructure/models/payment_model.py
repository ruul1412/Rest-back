from app.domain.enums.table_payment_enum import PaymentStatus
from sqlalchemy import Column, String, Numeric, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey
from app.core.database import Base
from app.infrastructure.db.mixins.auditable import AuditableBase
import uuid

class PaymentModel(Base, AuditableBase):
    __tablename__ = "payments"

    id        = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id  = Column(UUID(as_uuid=True), ForeignKey("order_groups.id"), nullable=False)
    amount     = Column(Numeric(12, 2), nullable=False)  # monto
    status    = Column(String(20),   default=PaymentStatus.pendiente, nullable=False)
    pagado_at = Column(DateTime(timezone=True), nullable=True)

    group = relationship("OrderGroupModel", back_populates="payment")
    splits = relationship("PaymentSplitModel", back_populates="payment", cascade="all, delete-orphan")