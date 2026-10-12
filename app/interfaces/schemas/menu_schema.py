from pydantic import BaseModel, field_validator
from typing import Optional
from uuid import UUID
from decimal import Decimal
from datetime import date


# ── Slot (segundo del menú) ───────────────────────────────────────────────────

class SlotCreateRequest(BaseModel):
    product_id:  UUID
    menu_price:  Decimal
    stock_start: int
    order_num:   int = 1

    @field_validator("menu_price")
    @classmethod
    def price_positive(cls, v):
        if v <= 0:
            raise ValueError("El precio debe ser mayor a 0")
        return v

    @field_validator("stock_start")
    @classmethod
    def stock_positive(cls, v):
        if v <= 0:
            raise ValueError("El stock debe ser mayor a 0")
        return v


class SlotUpdateRequest(BaseModel):
    menu_price:   Optional[Decimal] = None
    stock_start:  Optional[int]     = None
    order_num:    Optional[int]     = None
    is_available: Optional[bool]    = None


class SlotResponse(BaseModel):
    id:            UUID
    product_id:    UUID
    product_name:  str
    menu_price:    Decimal
    stock_start:   int
    stock_current: int
    order_num:     int
    is_available:  bool


# ── Entry (entrada del menú) ──────────────────────────────────────────────────

class EntryCreateRequest(BaseModel):
    product_id: UUID
    order_num:  int = 1


class EntryUpdateRequest(BaseModel):
    order_num:  Optional[int]  = None
    is_active:  Optional[bool] = None


class EntryResponse(BaseModel):
    id:           UUID
    product_id:   UUID
    product_name: str
    order_num:    int
    is_active:    bool


# ── MenuDay ───────────────────────────────────────────────────────────────────

class MenuDayCreateRequest(BaseModel):
    date:  date
    notes: Optional[str] = None


class MenuDayUpdateRequest(BaseModel):
    is_active: Optional[bool] = None
    notes:     Optional[str]  = None


class MenuDayResponse(BaseModel):
    id:        UUID
    date:      date
    is_active: bool
    notes:     Optional[str]      = None
    slots:     list[SlotResponse]  = []
    entries:   list[EntryResponse] = []