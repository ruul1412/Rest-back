from typing import Optional
from uuid import UUID
from datetime import date as date_type

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.interfaces.schemas.order_schema import (
    OrderGroupCreateRequest, OrderGroupResponse,
    OrderCreateRequest, OrderResponse, OrderStatusRequest,
)
from app.application.order.order_use_cases import (
    ListOrderGroupsUseCase, GetOrderGroupUseCase,
    CreateOrderGroupUseCase, CloseOrderGroupUseCase, CancelOrderGroupUseCase,
    GetOrderUseCase, CreateOrderUseCase, UpdateOrderStatusUseCase,
)
from app.interfaces.dependencies.auth_dependencies import require_roles, get_current_user
from app.infrastructure.repositories.order_repository import OrderGroupRepository, OrderRepository
from app.domain.user.user_entity import UserEntity

router = APIRouter(prefix="/orders", tags=["Orders"])

_admin         = Depends(require_roles(["admin"]))
_all_staff     = Depends(require_roles(["admin", "mesero", "cajero", "cocina", "bartender"]))
_create_order  = Depends(require_roles(["admin", "mesero", "bartender"]))
_update_status = Depends(require_roles(["admin", "mesero", "cocina", "bartender"]))
_close_order   = Depends(require_roles(["admin", "cajero"]))


# ── OrderGroups ───────────────────────────────────────────────────────────────

@router.get("/groups", response_model=list[OrderGroupResponse], dependencies=[_all_staff])
def list_groups(
    status: Optional[str] = None,
    date: Optional[date_type] = None,   # YYYY-MM-DD — solo aplica a status=cerrado/cancelado
    db: Session = Depends(get_db),
):
    return ListOrderGroupsUseCase(OrderGroupRepository(db)).execute(status, date)


@router.get("/groups/{group_id}", response_model=OrderGroupResponse, dependencies=[_all_staff])
def get_group(group_id: UUID, db: Session = Depends(get_db)):
    return GetOrderGroupUseCase(OrderGroupRepository(db)).execute(group_id)


@router.post("/groups", response_model=OrderGroupResponse, status_code=201)
def create_group(
    data: OrderGroupCreateRequest,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(require_roles(["admin", "mesero", "cajero", "bartender"])),
):
    result = CreateOrderGroupUseCase(OrderGroupRepository(db)).execute(data, current_user)
    db.commit()
    return result


@router.patch("/groups/{group_id}/close", dependencies=[_close_order])
def close_group(group_id: UUID, db: Session = Depends(get_db)):
    result = CloseOrderGroupUseCase(OrderGroupRepository(db)).execute(group_id)
    db.commit()
    return result


@router.patch("/groups/{group_id}/cancel", dependencies=[_admin])
def cancel_group(group_id: UUID, db: Session = Depends(get_db)):
    result = CancelOrderGroupUseCase(
        group_repo=OrderGroupRepository(db),
        order_repo=OrderRepository(db),
    ).execute(group_id)
    db.commit()
    return result


# ── Orders ────────────────────────────────────────────────────────────────────

@router.get("/{order_id}", response_model=OrderResponse, dependencies=[_all_staff])
def get_order(order_id: UUID, db: Session = Depends(get_db)):
    return GetOrderUseCase(OrderRepository(db)).execute(order_id)


@router.post("/groups/{group_id}/orders", response_model=OrderResponse, status_code=201)
def create_order(
    group_id: UUID,
    data: OrderCreateRequest,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(require_roles(["admin", "mesero", "bartender"])),
):
    result = CreateOrderUseCase(
        group_repo=OrderGroupRepository(db),
        order_repo=OrderRepository(db),
    ).execute(group_id, data)
    db.commit()
    return result


@router.patch("/{order_id}/status", dependencies=[_update_status])
def update_order_status(
    order_id: UUID,
    data: OrderStatusRequest,
    db: Session = Depends(get_db),
):
    result = UpdateOrderStatusUseCase(
        repo=OrderRepository(db),
        group_repo=OrderGroupRepository(db),
    ).execute(order_id, data)
    db.commit()
    return result