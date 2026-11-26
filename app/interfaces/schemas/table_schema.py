from pydantic import BaseModel, field_validator
from typing import Optional
from uuid import UUID

TABLE_STATUSES = {"libre", "ocupada", "reservada","inhabilitada"}


# ── Requests ──────────────────────────────────────────────────────────────────

class TableCreateRequest(BaseModel):
    number:   int
    capacity: int
    description : Optional[str] = None

    @field_validator("number", "capacity")
    @classmethod
    def must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("Debe ser mayor a 0")
        return v


class TableUpdateRequest(BaseModel):
    number:   Optional[int] = None
    capacity: Optional[int] = None
    description : Optional[str] = None

class TableStatusRequest(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def valid_status(cls, v):
        if v not in TABLE_STATUSES:
            raise ValueError(f"Estado inválido. Opciones: {TABLE_STATUSES}")
        return v


# ── Response ──────────────────────────────────────────────────────────────────

class TableResponse(BaseModel):
    id:       UUID
    number:   int
    capacity: int
    status:   str
    description : Optional[str] = None