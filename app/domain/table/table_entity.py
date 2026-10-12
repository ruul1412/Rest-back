from dataclasses import dataclass
from uuid import UUID


@dataclass
class TableEntity:
    id:       UUID
    number:   int
    capacity: int
    status:   str   # libre | ocupada | reservada