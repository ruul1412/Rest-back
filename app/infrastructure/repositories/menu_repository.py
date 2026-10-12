from typing import Optional
from uuid import UUID
from datetime import date

from sqlalchemy.orm import Session, joinedload

from app.infrastructure.models.menu_day_model import MenuDayModel
from app.infrastructure.models.menu_day_slot_model import MenuDaySlotModel
from app.infrastructure.models.menu_day_entry_model import MenuDayEntryModel
from app.infrastructure.models.product_model import ProductModel
from app.domain.menu.menu_entity import MenuDayEntity, MenuDaySlotEntity, MenuDayEntryEntity


# ── Mappers ───────────────────────────────────────────────────────────────────

def _slot_to_entity(m: MenuDaySlotModel) -> MenuDaySlotEntity:
    return MenuDaySlotEntity(
        id=m.id,
        menu_day_id=m.menu_day_id,
        product_id=m.product_id,
        product_name=m.product.name if m.product else "",
        menu_price=m.menu_price,
        stock_start=m.stock_start,
        stock_current=m.stock_current,
        order_num=m.order_num,
        is_available=m.is_available,
    )


def _entry_to_entity(m: MenuDayEntryModel) -> MenuDayEntryEntity:
    return MenuDayEntryEntity(
        id=m.id,
        menu_day_id=m.menu_day_id,
        product_id=m.product_id,
        product_name=m.product.name if m.product else "",
        order_num=m.order_num,
        is_active=m.is_active,
    )


def _menu_to_entity(m: MenuDayModel) -> MenuDayEntity:
    return MenuDayEntity(
        id=m.id,
        date=m.date,
        is_active=m.is_active,
        notes=m.notes,
        slots=[_slot_to_entity(s) for s in (m.slots or [])],
        entries=[_entry_to_entity(e) for e in (m.entries or [])],
    )


# ── MenuRepository ────────────────────────────────────────────────────────────

class MenuRepository:

    def __init__(self, db: Session):
        self._db = db

    def _base_query(self):
        return (
            self._db.query(MenuDayModel)
            .options(
                joinedload(MenuDayModel.slots).joinedload(MenuDaySlotModel.product),
                joinedload(MenuDayModel.entries).joinedload(MenuDayEntryModel.product),
            )
        )

    # ── MenuDay ───────────────────────────────────────────────────────────────

    def get_all(self) -> list[MenuDayEntity]:
        return [_menu_to_entity(m) for m in
                self._base_query().order_by(MenuDayModel.date.desc()).all()]

    def get_by_id(self, menu_day_id: UUID) -> Optional[MenuDayEntity]:
        m = self._base_query().filter(MenuDayModel.id == menu_day_id).first()
        return _menu_to_entity(m) if m else None

    def get_by_date(self, target_date: date) -> Optional[MenuDayEntity]:
        m = self._base_query().filter(MenuDayModel.date == target_date).first()
        return _menu_to_entity(m) if m else None

    def get_today(self) -> Optional[MenuDayEntity]:
        from datetime import date as date_type
        return self.get_by_date(date_type.today())

    def date_exists(self, target_date: date, exclude_id: UUID = None) -> bool:
        q = self._db.query(MenuDayModel.id).filter(MenuDayModel.date == target_date)
        if exclude_id:
            q = q.filter(MenuDayModel.id != exclude_id)
        return q.first() is not None

    def create(self, target_date: date, notes: Optional[str] = None) -> MenuDayEntity:
        m = MenuDayModel(date=target_date, notes=notes, is_active=True)
        self._db.add(m)
        self._db.flush()
        return _menu_to_entity(
            self._base_query().filter(MenuDayModel.id == m.id).first()
        )

    def update(self, menu_day_id: UUID, **fields) -> Optional[MenuDayEntity]:
        m = self._db.query(MenuDayModel).filter(MenuDayModel.id == menu_day_id).first()
        if not m:
            return None
        for key, value in fields.items():
            if value is not None:
                setattr(m, key, value)
        self._db.flush()
        return _menu_to_entity(
            self._base_query().filter(MenuDayModel.id == menu_day_id).first()
        )

    def delete(self, menu_day_id: UUID) -> bool:
        m = self._db.query(MenuDayModel).filter(MenuDayModel.id == menu_day_id).first()
        if not m:
            return False
        self._db.delete(m)
        self._db.flush()
        return True

    # ── Slots ─────────────────────────────────────────────────────────────────

    def get_slot(self, slot_id: UUID) -> Optional[MenuDaySlotEntity]:
        m = (
            self._db.query(MenuDaySlotModel)
            .options(joinedload(MenuDaySlotModel.product))
            .filter(MenuDaySlotModel.id == slot_id)
            .first()
        )
        return _slot_to_entity(m) if m else None

    def slot_product_exists(self, menu_day_id: UUID, product_id: UUID) -> bool:
        return self._db.query(MenuDaySlotModel.id).filter(
            MenuDaySlotModel.menu_day_id == menu_day_id,
            MenuDaySlotModel.product_id == product_id,
        ).first() is not None

    def add_slot(self, menu_day_id: UUID, product_id: UUID,
                 menu_price, stock_start: int, order_num: int) -> MenuDaySlotEntity:
        m = MenuDaySlotModel(
            menu_day_id=menu_day_id,
            product_id=product_id,
            menu_price=menu_price,
            stock_start=stock_start,
            stock_current=stock_start,   # al crear, current = start
            order_num=order_num,
            is_available=True,
        )
        self._db.add(m)
        self._db.flush()
        return self.get_slot(m.id)

    def update_slot(self, slot_id: UUID, **fields) -> Optional[MenuDaySlotEntity]:
        m = self._db.query(MenuDaySlotModel).filter(MenuDaySlotModel.id == slot_id).first()
        if not m:
            return None
        for key, value in fields.items():
            if value is not None:
                setattr(m, key, value)
        # Si actualizan stock_start, sincronizar stock_current
        if "stock_start" in fields and fields["stock_start"] is not None:
            m.stock_current = fields["stock_start"]
        self._db.flush()
        return self.get_slot(slot_id)

    def delete_slot(self, slot_id: UUID) -> bool:
        m = self._db.query(MenuDaySlotModel).filter(MenuDaySlotModel.id == slot_id).first()
        if not m:
            return False
        self._db.delete(m)
        self._db.flush()
        return True

    # ── Entries ───────────────────────────────────────────────────────────────

    def get_entry(self, entry_id: UUID) -> Optional[MenuDayEntryEntity]:
        m = (
            self._db.query(MenuDayEntryModel)
            .options(joinedload(MenuDayEntryModel.product))
            .filter(MenuDayEntryModel.id == entry_id)
            .first()
        )
        return _entry_to_entity(m) if m else None

    def entry_product_exists(self, menu_day_id: UUID, product_id: UUID) -> bool:
        return self._db.query(MenuDayEntryModel.id).filter(
            MenuDayEntryModel.menu_day_id == menu_day_id,
            MenuDayEntryModel.product_id == product_id,
        ).first() is not None

    def add_entry(self, menu_day_id: UUID, product_id: UUID,
                  order_num: int) -> MenuDayEntryEntity:
        m = MenuDayEntryModel(
            menu_day_id=menu_day_id,
            product_id=product_id,
            order_num=order_num,
            is_active=True,
        )
        self._db.add(m)
        self._db.flush()
        return self.get_entry(m.id)

    def update_entry(self, entry_id: UUID, **fields) -> Optional[MenuDayEntryEntity]:
        m = self._db.query(MenuDayEntryModel).filter(MenuDayEntryModel.id == entry_id).first()
        if not m:
            return None
        for key, value in fields.items():
            if value is not None:
                setattr(m, key, value)
        self._db.flush()
        return self.get_entry(entry_id)

    def delete_entry(self, entry_id: UUID) -> bool:
        m = self._db.query(MenuDayEntryModel).filter(MenuDayEntryModel.id == entry_id).first()
        if not m:
            return False
        self._db.delete(m)
        self._db.flush()
        return True

    # ── Validaciones de producto ──────────────────────────────────────────────

    def product_is_menu_item(self, product_id: UUID) -> bool:
        """Verifica que el producto sea de type.is_menu_item=True (plato_menu)."""
        from app.infrastructure.models.product_type_model import ProductTypeModel
        result = (
            self._db.query(ProductTypeModel.is_menu_item)
            .join(ProductModel, ProductModel.type_id == ProductTypeModel.id)
            .filter(ProductModel.id == product_id)
            .first()
        )
        return result and result.is_menu_item

    def product_is_entrada(self, product_id: UUID) -> bool:
        """Verifica que el producto sea de type.code='entrada'."""
        from app.infrastructure.models.product_type_model import ProductTypeModel
        result = (
            self._db.query(ProductTypeModel.code)
            .join(ProductModel, ProductModel.type_id == ProductTypeModel.id)
            .filter(ProductModel.id == product_id)
            .first()
        )
        return result and result.code == "entrada"