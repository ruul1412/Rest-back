# from uuid import UUID

# from fastapi import APIRouter, Depends
# from sqlalchemy.orm import Session

# from app.core.database import get_db
# from app.interfaces.schemas.payment_schema import PaymentCreateRequest, PaymentResponse
# from app.application.payment.payment_use_cases import (
#     GetPaymentByGroupUseCase,
#     ProcessPaymentUseCase,
#     CancelPaymentUseCase,
# )
# from app.interfaces.dependencies.auth_dependencies import require_roles
# from app.infrastructure.repositories.payment_repository import PaymentRepository
# from app.infrastructure.repositories.order_repository import OrderGroupRepository

# router = APIRouter(prefix="/payments", tags=["Payments"])

# _admin        = Depends(require_roles(["admin"]))
# _admin_cajero = Depends(require_roles(["admin", "cajero"]))


# @router.get("/groups/{group_id}", response_model=PaymentResponse, dependencies=[_admin_cajero])
# def get_payment(group_id: UUID, db: Session = Depends(get_db)):
#     return GetPaymentByGroupUseCase(PaymentRepository(db)).execute(group_id)


# @router.post("/groups/{group_id}", response_model=PaymentResponse, status_code=201, dependencies=[_admin_cajero])
# def process_payment(
#     group_id: UUID,
#     data: PaymentCreateRequest,
#     db: Session = Depends(get_db),
# ):
#     result = ProcessPaymentUseCase(
#         pay_repo=PaymentRepository(db),
#         group_repo=OrderGroupRepository(db),
#     ).execute(group_id, data)
#     db.commit()
#     return result


# @router.patch("/groups/{group_id}/cancel", dependencies=[_admin])
# def cancel_payment(group_id: UUID, db: Session = Depends(get_db)):
#     result = CancelPaymentUseCase(
#         pay_repo=PaymentRepository(db),
#         group_repo=OrderGroupRepository(db),
#     ).execute(group_id)
#     db.commit()
#     return result

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.interfaces.schemas.payment_schema import PaymentCreateRequest, PaymentResponse
from app.application.payment.payment_use_cases import (
    GetPaymentByGroupUseCase,
    ProcessPaymentUseCase,
    CancelPaymentUseCase,
)
from app.interfaces.dependencies.auth_dependencies import require_roles
from app.infrastructure.repositories.payment_repository import PaymentRepository
from app.infrastructure.repositories.order_repository import OrderGroupRepository, OrderRepository

router = APIRouter(prefix="/payments", tags=["Payments"])

_admin        = Depends(require_roles(["admin"]))
_admin_cajero = Depends(require_roles(["admin", "cajero"]))


@router.get("/groups/{group_id}", response_model=PaymentResponse, dependencies=[_admin_cajero])
def get_payment(group_id: UUID, db: Session = Depends(get_db)):
    return GetPaymentByGroupUseCase(PaymentRepository(db)).execute(group_id)


@router.post("/groups/{group_id}", response_model=PaymentResponse, status_code=201, dependencies=[_admin_cajero])
def process_payment(
    group_id: UUID,
    data: PaymentCreateRequest,
    db: Session = Depends(get_db),
):
    result = ProcessPaymentUseCase(
        pay_repo=PaymentRepository(db),
        group_repo=OrderGroupRepository(db),
        order_repo=OrderRepository(db),
    ).execute(group_id, data)
    db.commit()
    return result


@router.patch("/groups/{group_id}/cancel", dependencies=[_admin])
def cancel_payment(group_id: UUID, db: Session = Depends(get_db)):
    result = CancelPaymentUseCase(
        pay_repo=PaymentRepository(db),
        group_repo=OrderGroupRepository(db),
    ).execute(group_id)
    db.commit()
    return result