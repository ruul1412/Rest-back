from sqlalchemy import Column, String, Boolean, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey
from app.core.database import Base
from app.infrastructure.db.mixins.auditable import AuditableBase
import uuid


class ProductModel(Base, AuditableBase):
    __tablename__ = "products"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name        = Column(String, nullable=False)
    cost_price  = Column(Numeric(12, 2), nullable=True)   # nullable: al inicio puede no conocerse
    sale_price  = Column(Numeric(12, 2), nullable=False)
    image_url   = Column(String, nullable=True)
    is_available = Column(Boolean, nullable=False, default=True, server_default="true")
    is_active   = Column(Boolean,nullable=False, server_default="true", default=True)
    stock       = Column(Integer, default=0, nullable=True)

    type_id     = Column(UUID(as_uuid=True), ForeignKey("product_types.id"), nullable=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"))

    product_type  = relationship("ProductTypeModel", back_populates="products")
    category      = relationship("CategoryModel",    back_populates="products")
    order_items   = relationship("OrderItemModel",   back_populates="product")

    # Solo para bebidas (tiene_variantes=True)
    variants = relationship(
        "ProductVariantModel",
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="ProductVariantModel.orden_num",
    )

    # Apariciones en menús del día como segundo
    menu_slots   = relationship("MenuDaySlotModel",  back_populates="product")

    # Apariciones en menús del día como entrada
    menu_entries = relationship("MenuDayEntryModel", back_populates="product")