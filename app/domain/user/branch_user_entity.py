from dataclasses import dataclass
from uuid import UUID

@dataclass
class BranchUserEntity:
    user_id: UUID
    branch_id: UUID
    branch_name: str
    company_id: UUID
    company_name: str
    role_id: UUID
    role_code: str
    role_name: str
    is_default: bool