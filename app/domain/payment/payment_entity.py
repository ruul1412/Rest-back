from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID
from decimal import Decimal
from datetime import datetime


@dataclass
class PaymentSplitEntity:
    id:        UUID
    method:    str        # efectivo | tarjeta | yape | plin | transferencia
    amount:    Decimal
    reference: Optional[str] = None


@dataclass
class PaymentEntity:
    id:         UUID
    group_id:   UUID
    amount:     Decimal
    status:     str       # pendiente | pagado | cancelado
    pagado_at:  Optional[datetime]        = None
    splits:     list[PaymentSplitEntity]  = field(default_factory=list)