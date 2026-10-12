from dataclasses import dataclass
from pydantic import BaseModel

@dataclass
class ProcessPaymentInput:
    group_id: str
    metodo: str       # "efectivo" | "tarjeta" | "yape" | "plin" | "mixto"
    # pagado_por: str   # user_id del cajero

class ProcessPaymentRequest(BaseModel):
    metodo: str   # "efectivo" | "tarjeta" |