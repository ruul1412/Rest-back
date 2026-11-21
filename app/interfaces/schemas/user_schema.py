
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr

# =========================================================
# REQUESTS
# =========================================================

# -------------------------
# Usuarios
# -------------------------

class UserCreateRequest(BaseModel):
    email: EmailStr
    password: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    dni: Optional[str] = None
    branch_id: Optional[UUID] = None
    role_code: str


class UserUpdateRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    dni: Optional[str] = None


class UserStatusRequest(BaseModel):
    is_active: bool


# -------------------------
# Roles globales
# -------------------------

class AssignRoleRequest(BaseModel):
    role_code: str


# -------------------------
# Asignaciones por sucursal
# -------------------------

class AssignBranchUserRequest(BaseModel):
    branch_id: UUID
    role_code: str


class UpdateBranchRoleRequest(BaseModel):
    branch_id: UUID
    role_code: str


class SetBranchUserStatusRequest(BaseModel):
    branch_id: UUID
    is_active: bool


# =========================================================
# RESPONSES
# =========================================================

class UserResponse(BaseModel):
    id: UUID
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    dni: Optional[str] = None
    is_active: bool
    role_name: Optional[str] = None
    role_code: Optional[str] = None

    @property
    def full_name(self) -> str:
        parts = [self.first_name, self.last_name]
        return " ".join(p for p in parts if p) or self.email
