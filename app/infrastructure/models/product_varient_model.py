from sqlalchemy import Column, String, Boolean, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey
from app.infrastructure.db.mixins.auditable import AuditableBase
from app.core.database import Base
import uuid


class ProductVariantModel(Base, AuditableBase ):
    __tablename__ = "product_variants"

    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    name       = Column(String,  nullable=False)
    price      = Column(Numeric(12, 2), nullable=False)
    orden_num      = Column(Integer, nullable=False, default=1, server_default="1")
    is_available = Column(Boolean, nullable=False, default=True, server_default="true")

    product     = relationship("ProductModel",   back_populates="variants")
    order_items = relationship("OrderItemModel", back_populates="variant")
 
    # Tallas de bebidas con precio propio.
    # Solo existe para productos con product_type.tiene_variantes = True.

    # Sin AuditableBase — las variantes son configuración simple.
    # Si cambia el precio de una talla se edita directo.
    # Si se elimina, se borra físicamente (no hay historial que preservar).

    # Ejemplos:
    #     Coca Cola → Personal S/3.00  orden=1
    #     Coca Cola → Mediano  S/5.00  orden=2
    #     Coca Cola → Litro    S/8.00  orden=3

    # El precio del order_item viene de aquí, NO de products.sale_price.
    # products.sale_price queda como referencial para mostrar en el catálogo.
    