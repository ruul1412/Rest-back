class OrderDomainError(Exception):
    """Base — todos los errores del dominio Order heredan de aquí"""
 
 
# ── OrderGroup ───────────────────────────────────────────────
class OrderGroupNotFoundError(OrderDomainError):
    """El grupo solicitado no existe"""
 
class OrderGroupClosedError(OrderDomainError):
    """El grupo ya está cerrado o cancelado y no acepta cambios"""
 
class OrderGroupCannotBeChargedError(OrderDomainError):
    """El grupo tiene órdenes pendientes que impiden el cobro"""
 
 
# ── Order ────────────────────────────────────────────────────
class OrderNotFoundError(OrderDomainError):
    """La orden solicitada no existe"""
 
class EmptyOrderError(OrderDomainError):
    """La orden debe tener al menos un item"""
 
class InvalidOrderTransitionError(OrderDomainError):
    """Transición de estado no permitida"""
 
 
# ── Producto ─────────────────────────────────────────────────
class ProductNotFoundError(OrderDomainError):
    """Producto no existe"""
 
class ProductNotAvailableError(OrderDomainError):
    """Producto existe pero está inactivo"""
 
class InvalidQuantityError(OrderDomainError):
    """Cantidad inválida (debe ser > 0)"""
 
 
# ── Payment ──────────────────────────────────────────────────
class PaymentAlreadyPaidError(OrderDomainError):
    """El grupo ya fue cobrado"""
 
class PaymentNotFoundError(OrderDomainError):
    """No existe payment para este grupo"""
 
