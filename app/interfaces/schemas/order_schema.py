from pydantic import BaseModel, field_validator
from typing import Optional
from uuid import UUID
from decimal import Decimal
from datetime import datetime

SALE_TYPES = {"menu", "carta", "adicional", "entrada"}
GROUP_STATUSES = {"abierto", "cerrado", "cancelado"}
ORDER_STATUSES = {"pendiente", "en_proceso", "listo", "entregado", "cancelado"}


# ── OrderItem ─────────────────────────────────────────────────────────────────

class OrderItemAdicionalRequest(BaseModel):
    product_id: UUID
    quantity:   int           = 1
    notes:      Optional[str] = None

    @field_validator("quantity")
    @classmethod
    def quantity_positive(cls, v):
        if v <= 0:
            raise ValueError("La cantidad debe ser mayor a 0")
        return v


class OrderItemRequest(BaseModel):
    product_id:     UUID
    sale_type:      str
    quantity:       int             = 1
    variant_id:     Optional[UUID]  = None
    menu_slot_id:   Optional[UUID]  = None
    parent_item_id: Optional[UUID]  = None
    notes:          Optional[str]   = None
    adicionales:    Optional[list[OrderItemAdicionalRequest]] = None

    @field_validator("sale_type")
    @classmethod
    def valid_sale_type(cls, v):
        if v not in SALE_TYPES:
            raise ValueError(f"sale_type inválido. Opciones: {SALE_TYPES}")
        return v

    @field_validator("quantity")
    @classmethod
    def quantity_positive(cls, v):
        if v <= 0:
            raise ValueError("La cantidad debe ser mayor a 0")
        return v


class OrderItemResponse(BaseModel):
    id:             UUID
    product_id:     UUID
    product_name:   str
    sale_type:      str
    quantity:       int
    unit_price:     Decimal
    subtotal:       Decimal
    is_free:        bool
    is_auto:        bool
    variant_id:     Optional[UUID]  = None
    variant_name:   Optional[str]   = None
    menu_slot_id:   Optional[UUID]  = None
    parent_item_id: Optional[UUID]  = None
    notes:          Optional[str]   = None
    children:       list["OrderItemResponse"] = []


# ── Order ─────────────────────────────────────────────────────────────────────

class OrderCreateRequest(BaseModel):
    items:           list[OrderItemRequest]
    type:            Optional[str]  = None   # mesa | llevar | delivery
    notes:           Optional[str]  = None
    disposables_qty: int            = 0

    @field_validator("items")
    @classmethod
    def items_not_empty(cls, v):
        if not v:
            raise ValueError("El pedido debe tener al menos un item")
        return v


class OrderStatusRequest(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def valid_status(cls, v):
        if v not in ORDER_STATUSES:
            raise ValueError(f"Estado inválido. Opciones: {ORDER_STATUSES}")
        return v


class OrderResponse(BaseModel):
    id:              UUID
    group_id:        UUID
    status:          str
    total:           Decimal
    type:            Optional[str]  = None
    notes:           Optional[str]  = None
    disposables_qty: int            = 0
    items:           list[OrderItemResponse] = []


# ── OrderGroup ────────────────────────────────────────────────────────────────

class OrderGroupCreateRequest(BaseModel):
    table_id:      Optional[UUID]  = None
    customer_name: Optional[str]   = None
    notes_group:   Optional[str]   = None


class OrderGroupResponse(BaseModel):
    id:            UUID
    user_id:       UUID
    status:        str
    total:         Decimal
    table_id:      Optional[UUID]  = None
    table_number:  Optional[int]   = None
    customer_name: Optional[str]   = None
    notes_group:   Optional[str]   = None
    created_at:    Optional[datetime] = None
    closed_at:     Optional[datetime] = None
    orders:        list[OrderResponse] = []