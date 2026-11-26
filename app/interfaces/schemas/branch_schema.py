from pydantic import BaseModel, field_validator
from typing import Optional
from uuid import UUID

# ── Response ──────────────────────────────────────────────────────────────────

class BranchResponse(BaseModel):
    id:       UUID
    name:     str
    description: Optional[str]
    phone:    Optional[str]
    address: Optional[str]
    is_active: bool
    company_name : str

# ── Request ──────────────────────────────────────────────────────────────────

class BranchCreateRequest(BaseModel):
    company_id: UUID
    name: str
    description: Optional[str]
    phone: Optional[str]
    address: Optional[str]
    is_active: Optional[bool] = None

class BranchUpdateRequest(BranchCreateRequest):
    pass

class BranchStatusUpdateRequest(BaseModel):
    is_active: bool