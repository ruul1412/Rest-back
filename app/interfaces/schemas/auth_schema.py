from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID
 
 
class LoginRequest(BaseModel):
    email:    EmailStr
    password: str
 
 
class TokenResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"
 
 
class MeResponse(BaseModel):
    id:        UUID
    email:     str
    full_name: str
    role_name: Optional[str] = None
    role_code: Optional[str] = None
    is_active: bool
 