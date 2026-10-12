from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID

# class UserCreate(BaseModel):
#     email: EmailStr
#     password: str
#     roles: list[str] = []
#     first_name: str | None = None
#     last_name: str | None = None
#     phone: str | None = None
#     dni: str | None = None


# class UserLogin(BaseModel):
#     email: EmailStr
#     password: str

# ── Requests ──────────────────────────────────────────────────────────────────
 
class UserCreateRequest(BaseModel):
    email:      EmailStr
    password:   str
    first_name: Optional[str] = None
    last_name:  Optional[str] = None
    phone:      Optional[str] = None
    dni:        Optional[str] = None
 
 
class UserUpdateRequest(BaseModel):
    first_name: Optional[str] = None
    last_name:  Optional[str] = None
    phone:      Optional[str] = None
    dni:        Optional[str] = None
 
 
class AssignRoleRequest(BaseModel):
    role_code: str

# ── Responses ─────────────────────────────────────────────────────────────────
 
class UserResponse(BaseModel):
    id:         UUID
    email:      str
    first_name: Optional[str] = None
    last_name:  Optional[str] = None
    phone:      Optional[str] = None
    dni:        Optional[str] = None
    is_active:  bool
    role_name:  Optional[str] = None
    role_code:  Optional[str] = None
 
    @property
    def full_name(self) -> str:
        parts = [self.first_name, self.last_name]
        return " ".join(p for p in parts if p) or self.email