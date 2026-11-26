from pydantic import BaseModel, field_validator
from typing import Optional
from uuid import UUID

# ── Response ──────────────────────────────────────────────────────────────────

class CompanyResponse(BaseModel):
    id:       UUID
    name:     str
    description: Optional[str] = None
    phone: Optional[str] = None
    ruc: Optional[str] = None
    is_active: bool

# ── Request ──────────────────────────────────────────────────────────────────

class CompanyCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    phone: Optional[str] = None
    ruc: Optional[str] = None

class CompanyUpdateRequest(CompanyCreateRequest):
    is_active: bool

class CompanyStatusUpdateRequest(BaseModel):
    is_active: bool    