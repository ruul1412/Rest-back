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

# ── Request ──────────────────────────────────────────────────────────────────

class BranchCreateRequest(BaseModel):
    name: str
    description: Optional[str]
    phone: Optional[str]
    address: Optional[str]

class BranchUpdateRequest(BranchCreateRequest):
    id: UUID
    is_active: bool
