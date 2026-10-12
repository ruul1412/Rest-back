from sqlalchemy import Column, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey
from app.core.database import Base
from app.infrastructure.db.mixins.auditable import AuditableBase
import uuid


class MenuDayEntryModel(Base, AuditableBase):
    __tablename__ = "menu_day_entries"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    menu_day_id = Column(UUID(as_uuid=True), ForeignKey("menu_days.id"),  nullable=False)
    product_id  = Column(UUID(as_uuid=True), ForeignKey("products.id"),   nullable=False)

    order_num   = Column(Integer, nullable=False, default=1, server_default="1")
    is_active = Column(Boolean, nullable=False, default=True, server_default="true")

    menu_day = relationship("MenuDayModel",  back_populates="entries")
    product  = relationship("ProductModel",  back_populates="menu_entries")

    # Entrada disponible en el menú de un día específico.

    # Auditoría: sí — necesitamos saber qué entradas se ofrecieron cada día
    # para el historial y para que el admin pueda editar la programación semanal.

    # DIFERENCIA CON menu_day_slots:
    #     - Las entradas NO tienen precio propio (son gratis hasta el límite de menús)
    #     - Las entradas NO tienen stock diario controlado
    #     - El precio lo calcula el servicio según la regla:
    #         entradas_gratis = cantidad de order_items con tipo_venta="menu" en la orden
    #         si entradas_pedidas <= entradas_gratis → precio = 0
    #         si entradas_pedidas >  entradas_gratis → precio = product.sale_price

    # IMPORTANTE: el product referenciado aquí debe ser de type.code = "entrada"
