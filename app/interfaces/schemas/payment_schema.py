from pydantic import BaseModel, field_validator, model_validator
from typing import Optional
from uuid import UUID
from decimal import Decimal
from datetime import datetime

PAYMENT_METHODS  = {"efectivo", "tarjeta", "yape", "plin", "transferencia"}
PAYMENT_STATUSES = {"pendiente", "pagado", "cancelado"}


# ── Split ─────────────────────────────────────────────────────────────────────

class SplitRequest(BaseModel):
    method:    str
    amount:    Decimal
    reference: Optional[str] = None

    @field_validator("method")
    @classmethod
    def valid_method(cls, v):
        if v not in PAYMENT_METHODS:
            raise ValueError(f"Método inválido. Opciones: {PAYMENT_METHODS}")
        return v

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v):
        if v <= 0:
            raise ValueError("El monto debe ser mayor a 0")
        return v


class SplitResponse(BaseModel):
    id:        UUID
    method:    str
    amount:    Decimal
    reference: Optional[str] = None


# ── Payment ───────────────────────────────────────────────────────────────────

class PaymentCreateRequest(BaseModel):
    """
    Crea el pago y lo procesa en un solo paso.
    splits debe sumar exactamente el total del grupo.
    """
    splits: list[SplitRequest]

    @field_validator("splits")
    @classmethod
    def splits_not_empty(cls, v):
        if not v:
            raise ValueError("Debe haber al menos un método de pago")
        return v


class PaymentResponse(BaseModel):
    id:        UUID
    group_id:  UUID
    amount:    Decimal
    status:    str
    pagado_at: Optional[datetime] = None
    splits:    list[SplitResponse] = []