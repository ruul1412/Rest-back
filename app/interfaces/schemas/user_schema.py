
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
    role_code: Optional[str] = None


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
class BranchAssignmentResponse(BaseModel):
    branch_id: UUID
    branch_name: str
    company_name: Optional[str] = None
    role_code: Optional[str] = None
    role_name: Optional[str] = None
    is_active: bool
    is_deleted: bool = False
    
class UserResponse(BaseModel):
    id: UUID
    email: str

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    dni: Optional[str] = None

    # Estado global de la cuenta
    is_active: bool
    is_deleted: bool = False

    # Rol según el contexto
    role_name: Optional[str] = None
    role_code: Optional[str] = None

    # Estado de la asignación a una sucursal
    branch_is_active: Optional[bool] = None
    branch_is_deleted: Optional[bool] = None

    # Asignaciones del usuario a sus sucursales
    assignments: list[BranchAssignmentResponse] = []

    @property
    def full_name(self) -> str:
        parts = [self.first_name, self.last_name]
        return " ".join(p for p in parts if p) or self.email
# ============================================
class UserSearchResponse(BaseModel):
    id: UUID
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None