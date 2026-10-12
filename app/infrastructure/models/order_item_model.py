from sqlalchemy import Column, String, Integer, Numeric, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey
from app.core.database import Base
from app.infrastructure.db.mixins.auditable import AuditableBase
import uuid


class OrderItemModel(Base, AuditableBase):
    __tablename__ = "order_items"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id       = Column(UUID(as_uuid=True), ForeignKey("orders.id"),           nullable=False)
    product_id     = Column(UUID(as_uuid=True), ForeignKey("products.id"),         nullable=False)
    variant_id     = Column(UUID(as_uuid=True), ForeignKey("product_variants.id"), nullable=True)
    menu_slot_id   = Column(UUID(as_uuid=True), ForeignKey("menu_day_slots.id"),   nullable=True)
    parent_item_id = Column(UUID(as_uuid=True), ForeignKey("order_items.id"),      nullable=True)

    sale_type     = Column(String(15), nullable=False)

    quantity        = Column(Integer,       nullable=False)
    unit_price  = Column(Numeric(10, 2), nullable=False)
    subtotal        = Column(Numeric(10, 2), nullable=False)
    notes           = Column(String,         nullable=True)

    order     = relationship("OrderModel",          back_populates="order_items")
    product   = relationship("ProductModel",        back_populates="order_items")
    variant   = relationship("ProductVariantModel", back_populates="order_items")
    menu_slot = relationship("MenuDaySlotModel",    back_populates="order_items")

    is_free    = Column(Boolean, nullable=False, default=False)
    # entrada gratuita del menú (unit_price=0, subtotal=0)

    is_auto    = Column(Boolean, nullable=False, default=False)

    # Relación reflexiva — adicionales y entradas apuntan a su item padre
    parent   = relationship("OrderItemModel", remote_side="OrderItemModel.id",
                            foreign_keys="[OrderItemModel.parent_item_id]",
                              back_populates="children")
    children = relationship("OrderItemModel",
                            foreign_keys="[OrderItemModel.parent_item_id]",
                            back_populates="parent")