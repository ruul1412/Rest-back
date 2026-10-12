from uuid import UUID
from datetime import date

from fastapi import HTTPException

from app.interfaces.schemas.menu_schema import (
    MenuDayCreateRequest, MenuDayUpdateRequest, MenuDayResponse,
    SlotCreateRequest, SlotUpdateRequest, SlotResponse,
    EntryCreateRequest, EntryUpdateRequest, EntryResponse,
)
from app.infrastructure.repositories.menu_repository import MenuRepository


# ── Helpers ───────────────────────────────────────────────────────────────────

def _slot_resp(e) -> SlotResponse:
    return SlotResponse(
        id=e.id, product_id=e.product_id, product_name=e.product_name,
        menu_price=e.menu_price, stock_start=e.stock_start,
        stock_current=e.stock_current, order_num=e.order_num,
        is_available=e.is_available,
    )

def _entry_resp(e) -> EntryResponse:
    return EntryResponse(
        id=e.id, product_id=e.product_id, product_name=e.product_name,
        order_num=e.order_num, is_active=e.is_active,
    )

def _menu_resp(e) -> MenuDayResponse:
    return MenuDayResponse(
        id=e.id, date=e.date, is_active=e.is_active, notes=e.notes,
        slots=[_slot_resp(s) for s in e.slots],
        entries=[_entry_resp(en) for en in e.entries],
    )


# ── MenuDay Use Cases ─────────────────────────────────────────────────────────

class ListMenuDaysUseCase:
    def __init__(self, repo: MenuRepository): self._repo = repo

    def execute(self) -> list[MenuDayResponse]:
        return [_menu_resp(e) for e in self._repo.get_all()]


class GetMenuDayUseCase:
    def __init__(self, repo: MenuRepository): self._repo = repo

    def execute(self, menu_day_id: UUID) -> MenuDayResponse:
        entity = self._repo.get_by_id(menu_day_id)
        if not entity:
            raise HTTPException(status_code=404, detail="Menú no encontrado")
        return _menu_resp(entity)


class GetTodayMenuUseCase:
    def __init__(self, repo: MenuRepository): self._repo = repo

    def execute(self) -> MenuDayResponse:
        entity = self._repo.get_today()
        if not entity:
            raise HTTPException(status_code=404, detail="No hay menú configurado para hoy")
        return _menu_resp(entity)


class CreateMenuDayUseCase:
    def __init__(self, repo: MenuRepository): self._repo = repo

    def execute(self, data: MenuDayCreateRequest) -> MenuDayResponse:
        if self._repo.date_exists(data.date):
            raise HTTPException(
                status_code=400,
                detail=f"Ya existe un menú para el {data.date}",
            )
        return _menu_resp(self._repo.create(data.date, data.notes))


class UpdateMenuDayUseCase:
    def __init__(self, repo: MenuRepository): self._repo = repo

    def execute(self, menu_day_id: UUID, data: MenuDayUpdateRequest) -> MenuDayResponse:
        entity = self._repo.update(
            menu_day_id,
            is_active=data.is_active,
            notes=data.notes,
        )
        if not entity:
            raise HTTPException(status_code=404, detail="Menú no encontrado")
        return _menu_resp(entity)


class DeleteMenuDayUseCase:
    def __init__(self, repo: MenuRepository): self._repo = repo

    def execute(self, menu_day_id: UUID) -> dict:
        if not self._repo.get_by_id(menu_day_id):
            raise HTTPException(status_code=404, detail="Menú no encontrado")
        self._repo.delete(menu_day_id)
        return {"detail": "Menú eliminado"}


# ── Slot Use Cases ────────────────────────────────────────────────────────────

class AddSlotUseCase:
    def __init__(self, repo: MenuRepository): self._repo = repo

    def execute(self, menu_day_id: UUID, data: SlotCreateRequest) -> SlotResponse:
        if not self._repo.get_by_id(menu_day_id):
            raise HTTPException(status_code=404, detail="Menú no encontrado")

        if not self._repo.product_is_menu_item(data.product_id):
            raise HTTPException(
                status_code=400,
                detail="El producto debe ser de tipo 'plato_menu' (is_menu_item=True)",
            )

        if self._repo.slot_product_exists(menu_day_id, data.product_id):
            raise HTTPException(
                status_code=400,
                detail="Ese producto ya está en el menú de este día",
            )

        entity = self._repo.add_slot(
            menu_day_id=menu_day_id,
            product_id=data.product_id,
            menu_price=data.menu_price,
            stock_start=data.stock_start,
            order_num=data.order_num,
        )
        return _slot_resp(entity)


class UpdateSlotUseCase:
    def __init__(self, repo: MenuRepository): self._repo = repo

    def execute(self, slot_id: UUID, data: SlotUpdateRequest) -> SlotResponse:
        entity = self._repo.update_slot(
            slot_id,
            menu_price=data.menu_price,
            stock_start=data.stock_start,
            order_num=data.order_num,
            is_available=data.is_available,
        )
        if not entity:
            raise HTTPException(status_code=404, detail="Slot no encontrado")
        return _slot_resp(entity)


class DeleteSlotUseCase:
    def __init__(self, repo: MenuRepository): self._repo = repo

    def execute(self, slot_id: UUID) -> dict:
        if not self._repo.delete_slot(slot_id):
            raise HTTPException(status_code=404, detail="Slot no encontrado")
        return {"detail": "Slot eliminado"}


# ── Entry Use Cases ───────────────────────────────────────────────────────────

class AddEntryUseCase:
    def __init__(self, repo: MenuRepository): self._repo = repo

    def execute(self, menu_day_id: UUID, data: EntryCreateRequest) -> EntryResponse:
        if not self._repo.get_by_id(menu_day_id):
            raise HTTPException(status_code=404, detail="Menú no encontrado")

        if not self._repo.product_is_entrada(data.product_id):
            raise HTTPException(
                status_code=400,
                detail="El producto debe ser de tipo 'entrada'",
            )

        if self._repo.entry_product_exists(menu_day_id, data.product_id):
            raise HTTPException(
                status_code=400,
                detail="Esa entrada ya está en el menú de este día",
            )

        entity = self._repo.add_entry(
            menu_day_id=menu_day_id,
            product_id=data.product_id,
            order_num=data.order_num,
        )
        return _entry_resp(entity)


class UpdateEntryUseCase:
    def __init__(self, repo: MenuRepository): self._repo = repo

    def execute(self, entry_id: UUID, data: EntryUpdateRequest) -> EntryResponse:
        entity = self._repo.update_entry(
            entry_id,
            order_num=data.order_num,
            is_active=data.is_active,
        )
        if not entity:
            raise HTTPException(status_code=404, detail="Entrada no encontrada")
        return _entry_resp(entity)


class DeleteEntryUseCase:
    def __init__(self, repo: MenuRepository): self._repo = repo

    def execute(self, entry_id: UUID) -> dict:
        if not self._repo.delete_entry(entry_id):
            raise HTTPException(status_code=404, detail="Entrada no encontrada")
        return {"detail": "Entrada eliminada"}