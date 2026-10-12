from sqlalchemy import Column, String, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.infrastructure.db.mixins.auditable import AuditableBase
import uuid

#
# | code       | tiene_variantes | es_menu_item | descuenta_stock |
# | plato_menu | False           | True         | True            |
# | carta      | False           | False        | False           |
# | entrada    | False           | False        | False           |
# | bebida     | True            | False        | True            |
# | postre     | False           | False        | False           |
# | adicional  | False           | False        | False           |
#
# tiene_variantes  → tiene tallas (solo bebidas)
# es_menu_item     → aparece en menu_day_slots con stock diario controlado
# descuenta_stock  → al venderse descuenta products.stock (futuro inventario)


class ProductTypeModel(Base, AuditableBase):
    __tablename__ = "product_types"

    id   = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    code = Column(String, nullable=False, unique=True)

    has_variants = Column(Boolean, nullable=False, default=False, server_default="false")
    is_menu_item     = Column(Boolean, nullable=False, default=False, server_default="false")
    deducts_stock  = Column(Boolean, nullable=False, default=False, server_default="false")

    products = relationship("ProductModel", back_populates="product_type")