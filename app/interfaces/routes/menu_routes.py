from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.config import settings
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
from app.infrastructure.unit_of_work import UnitOfWork

router = APIRouter(prefix="/menu", tags=["Menu"])


def route_message(message: str):
    def decorator(func):
        func.response_message = message
        return func
    return decorator


_admin        = Depends(require_roles(["admin"]))
_admin_cocina = Depends(require_roles(["admin", "cocina"]))
_all_staff    = Depends(require_roles(["admin", "mesero", "cajero", "cocina", "bartender"]))


def _repo(db: Session = Depends(get_db)) -> MenuRepository:
    return MenuRepository(db)


# ── MenuDay ───────────────────────────────────────────────────────────────────

@route_message("Menús obtenidos correctamente")
@router.get("", dependencies=[_all_staff])
def list_menu_days(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE),
    repo: MenuRepository = Depends(_repo),
):
    return ListMenuDaysUseCase(repo).execute(page=page, page_size=page_size)


@route_message("Menú del día obtenido correctamente")
@router.get("/today", response_model=MenuDayResponse, dependencies=[_all_staff])
def get_today_menu(repo: MenuRepository = Depends(_repo)):
    return GetTodayMenuUseCase(repo).execute()


@route_message("Menú obtenido correctamente")
@router.get("/{menu_day_id}", response_model=MenuDayResponse, dependencies=[_all_staff])
def get_menu_day(menu_day_id: UUID, repo: MenuRepository = Depends(_repo)):
    return GetMenuDayUseCase(repo).execute(menu_day_id)


@route_message("Menú creado correctamente")
@router.post("", response_model=MenuDayResponse, status_code=201, dependencies=[_admin_cocina])
def create_menu_day(data: MenuDayCreateRequest, db: Session = Depends(get_db)):
    uow = UnitOfWork(db)
    result = CreateMenuDayUseCase(uow.menu).execute(data)
    uow.commit()
    return result


@route_message("Menú actualizado correctamente")
@router.patch("/{menu_day_id}", response_model=MenuDayResponse, dependencies=[_admin_cocina])
def update_menu_day(menu_day_id: UUID, data: MenuDayUpdateRequest, db: Session = Depends(get_db)):
    uow = UnitOfWork(db)
    result = UpdateMenuDayUseCase(uow.menu).execute(menu_day_id, data)
    uow.commit()
    return result


@route_message("Menú eliminado correctamente")
@router.delete("/{menu_day_id}", dependencies=[_admin])
def delete_menu_day(menu_day_id: UUID, db: Session = Depends(get_db)):
    uow = UnitOfWork(db)
    result = DeleteMenuDayUseCase(uow.menu).execute(menu_day_id)
    uow.commit()
    return result


# ── Slots (segundos) ──────────────────────────────────────────────────────────

@route_message("Horario agregado correctamente")
@router.post("/{menu_day_id}/slots", response_model=SlotResponse, status_code=201, dependencies=[_admin_cocina])
def add_slot(menu_day_id: UUID, data: SlotCreateRequest, db: Session = Depends(get_db)):
    uow = UnitOfWork(db)
    result = AddSlotUseCase(uow.menu).execute(menu_day_id, data)
    uow.commit()
    return result


@route_message("Horario actualizado correctamente")
@router.patch("/slots/{slot_id}", response_model=SlotResponse, dependencies=[_admin_cocina])
def update_slot(slot_id: UUID, data: SlotUpdateRequest, db: Session = Depends(get_db)):
    uow = UnitOfWork(db)
    result = UpdateSlotUseCase(uow.menu).execute(slot_id, data)
    uow.commit()
    return result


@route_message("Horario eliminado correctamente")
@router.delete("/slots/{slot_id}", dependencies=[_admin])
def delete_slot(slot_id: UUID, db: Session = Depends(get_db)):
    uow = UnitOfWork(db)
    result = DeleteSlotUseCase(uow.menu).execute(slot_id)
    uow.commit()
    return result


# ── Entries (entradas) ────────────────────────────────────────────────────────

@route_message("Entrada agregada correctamente")
@router.post("/{menu_day_id}/entries", response_model=EntryResponse, status_code=201, dependencies=[_admin_cocina])
def add_entry(menu_day_id: UUID, data: EntryCreateRequest, db: Session = Depends(get_db)):
    uow = UnitOfWork(db)
    result = AddEntryUseCase(uow.menu).execute(menu_day_id, data)
    uow.commit()
    return result


@route_message("Entrada actualizada correctamente")
@router.patch("/entries/{entry_id}", response_model=EntryResponse, dependencies=[_admin_cocina])
def update_entry(entry_id: UUID, data: EntryUpdateRequest, db: Session = Depends(get_db)):
    uow = UnitOfWork(db)
    result = UpdateEntryUseCase(uow.menu).execute(entry_id, data)
    uow.commit()
    return result


@route_message("Entrada eliminada correctamente")
@router.delete("/entries/{entry_id}", dependencies=[_admin])
def delete_entry(entry_id: UUID, db: Session = Depends(get_db)):
    uow = UnitOfWork(db)
    result = DeleteEntryUseCase(uow.menu).execute(entry_id)
    uow.commit()
    return result