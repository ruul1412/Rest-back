from app.domain.enums.order_enum import OrderStatus

from sqlalchemy import Column, String, Numeric, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey
from app.core.database import Base
from app.infrastructure.db.mixins.auditable import AuditableBase
import uuid


class OrderModel(Base, AuditableBase):
    __tablename__ = "orders"

    id       = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id = Column(UUID(as_uuid=True), ForeignKey("order_groups.id"), nullable=False)
    status   = Column(String(20), default=OrderStatus.pendiente, nullable=False)
    type     = Column(String(20), nullable=True)  # pido de orden llevar / mesa / delivery
    total    = Column(Numeric(12, 2), nullable=False, default=0)
    notes    = Column(String, nullable=True)       # comentario adicional a un pedido
    disposables_qty = Column(Integer, nullable=False, default=0)


    group       = relationship("OrderGroupModel", back_populates="orders")
    order_items = relationship("OrderItemModel",  back_populates="order", cascade="all, delete-orphan")