from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID
from decimal import Decimal
from datetime import date


@dataclass
class CompanyEntity:
    id:            UUID
    name:          str
    description:   Optional[str]
    phone:         Optional[str]
    is_active:     bool
    ruc:           Optional[str]