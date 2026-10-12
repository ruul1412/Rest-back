from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.interfaces.schemas.menu_schema import (
    MenuDayCreateRequest, MenuDayUpdateRequest, MenuDayResponse,
    SlotCreateRequest, SlotUpdateRequest, SlotResponse,
    EntryCreateRequest, EntryUpdateRequest, EntryResponse,
)
from app.application.menu.menu_use_cases import (
    ListMenuDaysUseCase, GetMenuDayUseCase, GetTodayMenuUseCase,
    CreateMenuDayUseCase, UpdateMenuDayUseCase, DeleteMenuDayUseCase,
    AddSlotUseCase, UpdateSlotUseCase, DeleteSlotUseCase,
    AddEntryUseCase, UpdateEntryUseCase, DeleteEntryUseCase,
)
from app.interfaces.dependencies.auth_dependencies import require_roles
from app.infrastructure.repositories.menu_repository import MenuRepository

router = APIRouter(prefix="/menu", tags=["Menu"])

_admin        = Depends(require_roles(["admin"]))
_admin_cocina = Depends(require_roles(["admin", "cocina"]))
_all_staff    = Depends(require_roles(["admin", "mesero", "cajero", "cocina", "bartender"]))


def _repo(db: Session = Depends(get_db)) -> MenuRepository:
    return MenuRepository(db)


# ── MenuDay ───────────────────────────────────────────────────────────────────

@router.get("", response_model=list[MenuDayResponse], dependencies=[_all_staff])
def list_menu_days(repo: MenuRepository = Depends(_repo)):
    return ListMenuDaysUseCase(repo).execute()


@router.get("/today", response_model=MenuDayResponse, dependencies=[_all_staff])
def get_today_menu(repo: MenuRepository = Depends(_repo)):
    return GetTodayMenuUseCase(repo).execute()


@router.get("/{menu_day_id}", response_model=MenuDayResponse, dependencies=[_all_staff])
def get_menu_day(menu_day_id: UUID, repo: MenuRepository = Depends(_repo)):
    return GetMenuDayUseCase(repo).execute(menu_day_id)


@router.post("", response_model=MenuDayResponse, status_code=201, dependencies=[_admin_cocina])
def create_menu_day(data: MenuDayCreateRequest, db: Session = Depends(get_db)):
    result = CreateMenuDayUseCase(MenuRepository(db)).execute(data)
    db.commit()
    return result


@router.patch("/{menu_day_id}", response_model=MenuDayResponse, dependencies=[_admin_cocina])
def update_menu_day(menu_day_id: UUID, data: MenuDayUpdateRequest, db: Session = Depends(get_db)):
    result = UpdateMenuDayUseCase(MenuRepository(db)).execute(menu_day_id, data)
    db.commit()
    return result


@router.delete("/{menu_day_id}", dependencies=[_admin])
def delete_menu_day(menu_day_id: UUID, db: Session = Depends(get_db)):
    result = DeleteMenuDayUseCase(MenuRepository(db)).execute(menu_day_id)
    db.commit()
    return result


# ── Slots (segundos) ──────────────────────────────────────────────────────────

@router.post("/{menu_day_id}/slots", response_model=SlotResponse, status_code=201, dependencies=[_admin_cocina])
def add_slot(menu_day_id: UUID, data: SlotCreateRequest, db: Session = Depends(get_db)):
    result = AddSlotUseCase(MenuRepository(db)).execute(menu_day_id, data)
    db.commit()
    return result


@router.patch("/slots/{slot_id}", response_model=SlotResponse, dependencies=[_admin_cocina])
def update_slot(slot_id: UUID, data: SlotUpdateRequest, db: Session = Depends(get_db)):
    result = UpdateSlotUseCase(MenuRepository(db)).execute(slot_id, data)
    db.commit()
    return result


@router.delete("/slots/{slot_id}", dependencies=[_admin])
def delete_slot(slot_id: UUID, db: Session = Depends(get_db)):
    result = DeleteSlotUseCase(MenuRepository(db)).execute(slot_id)
    db.commit()
    return result


# ── Entries (entradas) ────────────────────────────────────────────────────────

@router.post("/{menu_day_id}/entries", response_model=EntryResponse, status_code=201, dependencies=[_admin_cocina])
def add_entry(menu_day_id: UUID, data: EntryCreateRequest, db: Session = Depends(get_db)):
    result = AddEntryUseCase(MenuRepository(db)).execute(menu_day_id, data)
    db.commit()
    return result


@router.patch("/entries/{entry_id}", response_model=EntryResponse, dependencies=[_admin_cocina])
def update_entry(entry_id: UUID, data: EntryUpdateRequest, db: Session = Depends(get_db)):
    result = UpdateEntryUseCase(MenuRepository(db)).execute(entry_id, data)
    db.commit()
    return result


@router.delete("/entries/{entry_id}", dependencies=[_admin])
def delete_entry(entry_id: UUID, db: Session = Depends(get_db)):
    result = DeleteEntryUseCase(MenuRepository(db)).execute(entry_id)
    db.commit()
    return result