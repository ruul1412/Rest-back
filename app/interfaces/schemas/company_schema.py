from pydantic import BaseModel, field_validator
from typing import Optional
from uuid import UUID

# ── Response ──────────────────────────────────────────────────────────────────

class CompanyResponse(BaseModel):
    id:       UUID
    name:     str
    description: Optional[str]
    phone:    Optional[str]
    is_active: bool
    ruc:      Optional[str]

# ── Request ──────────────────────────────────────────────────────────────────

class CompanyCreateRequest(BaseModel):
    name: str
    description: Optional[str]
    phone: Optional[str]
    ruc: Optional[str]

class CompanyUpdateRequest(CompanyCreateRequest):
    is_active: bool

class CompanyStatusUpdateRequest(BaseModel):
    is_active: bool    