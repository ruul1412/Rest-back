
from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class BranchOptionResponse(BaseModel):
    branch_id: UUID
    branch_name: str
    company_id: UUID
    company_name: str
    role_code: str
    role_name: str
    is_default: bool


class LoginResponse(BaseModel):
    access_token: Optional[str] = None
    selection_token: Optional[str] = None
    requires_branch_selection: bool = False
    token_type: str = "bearer"
    memberships: list[BranchOptionResponse] = []


class SelectBranchRequest(BaseModel):
    selection_token: str
    branch_id: UUID


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MeResponse(BaseModel):
    id: UUID
    email: str
    full_name: str

    # Contexto de autenticación
    scope: str
    role_code: Optional[str] = None
    role_name: Optional[str] = None

    # Empresa y sucursal
    company_id: Optional[UUID] = None
    company_name: Optional[str] = None
    branch_id: Optional[UUID] = None
    branch_name: Optional[str] = None

    is_active: bool
