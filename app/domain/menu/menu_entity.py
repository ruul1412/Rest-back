from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID
from decimal import Decimal
from datetime import date


@dataclass
class MenuDaySlotEntity:
    id:            UUID
    menu_day_id:   UUID
    product_id:    UUID
    product_name:  str
    menu_price:    Decimal
    stock_start:   int
    stock_current: int
    order_num:     int
    is_available:  bool


@dataclass
class MenuDayEntryEntity:
    id:           UUID
    menu_day_id:  UUID
    product_id:   UUID
    product_name: str
    order_num:    int
    is_active:    bool


@dataclass
class MenuDayEntity:
    id:        UUID
    date:      date
    is_active: bool
    notes:     Optional[str]           = None
    slots:     list[MenuDaySlotEntity] = field(default_factory=list)
    entries:   list[MenuDayEntryEntity] = field(default_factory=list)