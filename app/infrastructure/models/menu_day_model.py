from sqlalchemy import Column, String, Boolean, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.infrastructure.db.mixins.auditable import AuditableBase
import uuid


class MenuDayModel(Base, AuditableBase):
    __tablename__ = "menu_days"

    id     = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    date  = Column(Date,    nullable=False, unique=True)
    is_active  = Column(Boolean, nullable=False, default=True, server_default="true")
    notes  = Column(String,  nullable=True)   # ej: "feriado, menú reducido"

    slots = relationship(
        "MenuDaySlotModel",
        back_populates="menu_day",
        cascade="all, delete-orphan",
        order_by="MenuDaySlotModel.order_num",
    )
    entries = relationship(
        "MenuDayEntryModel",
        back_populates="menu_day",
        cascade="all, delete-orphan",
        order_by="MenuDayEntryModel.order_num",
    )
    
    # Configuración del menú para un día específico.
    # El admin puede cargar toda la semana por adelantado.

    # Auditoría: sí — necesitamos saber si se activó/desactivó un día
    # y cuándo se hicieron cambios (ej: cancelar el menú de un feriado).

    # Un registro por día con menú activo.
    # Si no existe registro para una fecha → ese día no hay menú.

    # Relaciones:
    #     slots   → los segundos disponibles ese día (platos del menú con stock)
    #     entries → las entradas disponibles ese día (sin stock propio)
   