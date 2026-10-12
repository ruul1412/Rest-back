from sqlalchemy import Column, Integer, Numeric,Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey
from app.core.database import Base
from app.infrastructure.db.mixins.auditable import AuditableBase
import uuid


class MenuDaySlotModel(Base, AuditableBase):
    __tablename__ = "menu_day_slots"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    menu_day_id = Column(UUID(as_uuid=True), ForeignKey("menu_days.id"),  nullable=False)
    product_id  = Column(UUID(as_uuid=True), ForeignKey("products.id"),   nullable=False)

    menu_price      = Column(Numeric(12, 2), nullable=False)
    stock_start    = Column(Integer, nullable=False, default=0)
    stock_current  = Column(Integer, nullable=False, default=0)
    order_num        = Column(Integer, nullable=False, default=1, server_default="1")
    is_available = Column(Boolean, nullable=False, default=True, server_default="true")

    menu_day    = relationship("MenuDayModel",    back_populates="slots")
    product     = relationship("ProductModel",    back_populates="menu_slots")
    order_items = relationship("OrderItemModel",  back_populates="menu_slot")

    # Un segundo disponible en el menú de un día específico.
    # Tiene precio propio (distinto al de carta) y stock diario controlado.

    # Auditoría: sí — los cambios de stock_inicio y precio_menu deben
    # quedar registrados para el análisis de pronóstico futuro.

    # CAMPOS CLAVE:
    #     precio_menu  → precio dentro del menú (menor que el de carta)
    #                    Ej: pollo guisado en menú=S/10, en carta no existe
    #     stock_inicio → cuántas porciones preparó cocina hoy (lo registra el admin)
    #     stock_actual → se decrementa en 1 por cada order_item de tipo "menu"
    #                    vendidos = stock_inicio - stock_actual
    #                    Este cálculo permite el pronóstico por día de la semana

    # FLUJO DE STOCK:
    #     Admin registra: stock_inicio = 15
    #     Se venden 4 porciones: stock_actual = 11
    #     Sistema marca is_available=False cuando stock_actual = 0
    #     Al cierre del día: vendidos = 15 - stock_actual (histórico para pronóstico)
