from app.domain.enums.order_enum import GroupStatus
from sqlalchemy import Column, String, Numeric, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey
from app.core.database import Base
from app.infrastructure.db.mixins.auditable import AuditableBase
import uuid

class OrderGroupModel(Base, AuditableBase):
    __tablename__ = "order_groups"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id        = Column(UUID(as_uuid=True), ForeignKey("users.id"),   nullable=False)
    table_id       = Column(UUID(as_uuid=True), ForeignKey("tables.id"),  nullable=True)
    customer_name  = Column(String, nullable=True)
    status         = Column(String(20), default=GroupStatus.abierto, nullable=False)
    total          = Column(Numeric(12, 2), nullable=False, default=0)
    notes_group    = Column(String, nullable=True)
    closed_at      = Column(DateTime(timezone=True), nullable=True)  # se setea al cerrar/cancelar

    # Relaciones
    user    = relationship("UserModel",    back_populates="order_groups")
    table   = relationship("TableModel",   back_populates="order_groups")
    orders  = relationship("OrderModel",   back_populates="group", cascade="all, delete-orphan")
    payment = relationship("PaymentModel", back_populates="group", uselist=False)