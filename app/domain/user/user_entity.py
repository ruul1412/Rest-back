from dataclasses import dataclass
from typing import Optional
from uuid import UUID

@dataclass
class UserEntity:
    id:         UUID
    email:      str
    password:   str
    first_name: Optional[str] = None
    last_name:  Optional[str] = None
    phone:      Optional[str] = None
    dni:        Optional[str] = None
    is_active:  bool = True
    role_code:  Optional[str] = None
    role_name:  Optional[str] = None
 
    @property
    def full_name(self) -> str:
        parts = [self.first_name, self.last_name]
        return " ".join(p for p in parts if p) or self.email