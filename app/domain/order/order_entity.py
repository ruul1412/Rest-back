from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID
from decimal import Decimal
from datetime import datetime


@dataclass
class OrderItemEntity:
    id:             UUID
    order_id:       UUID
    product_id:     UUID
    product_name:   str
    sale_type:      str        # menu | carta | adicional | entrada
    quantity:       int
    unit_price:     Decimal
    subtotal:       Decimal
    is_free:        bool
    is_auto:        bool
    variant_id:     Optional[UUID]    = None
    variant_name:   Optional[str]     = None
    menu_slot_id:   Optional[UUID]    = None
    parent_item_id: Optional[UUID]    = None
    notes:          Optional[str]     = None
    children:       list["OrderItemEntity"] = field(default_factory=list)


@dataclass
class OrderEntity:
    id:              UUID
    group_id:        UUID
    status:          str
    total:           Decimal
    type:            Optional[str]   = None
    notes:           Optional[str]   = None
    disposables_qty: int             = 0
    items:           list[OrderItemEntity] = field(default_factory=list)


@dataclass
class OrderGroupEntity:
    id:            UUID
    user_id:       UUID
    status:        str
    total:         Decimal
    table_id:      Optional[UUID] = None
    table_number:  Optional[int]  = None
    customer_name: Optional[str]  = None
    notes_group:   Optional[str]  = None
    created_at:    Optional[datetime] = None
    closed_at:     Optional[datetime] = None
    orders:        list[OrderEntity] = field(default_factory=list)