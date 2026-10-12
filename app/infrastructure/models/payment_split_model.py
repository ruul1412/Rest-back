from sqlalchemy import Column, String, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey
from app.core.database import Base
from app.infrastructure.db.mixins.auditable import AuditableBase
import uuid

class PaymentSplitModel(Base, AuditableBase):
    __tablename__ = "payment_splits"
 
    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payment_id = Column(UUID(as_uuid=True), ForeignKey("payments.id"), nullable=False)
    method     = Column(String(20), nullable=False)   # efectivo | tarjeta | yape | plin | transferencia
    amount     = Column(Numeric(12, 2), nullable=False)
    reference  = Column(String, nullable=True)        # número de operación, últimos 4 dígitos, etc.
 
    # Relaciones
    payment = relationship("PaymentModel", back_populates="splits")