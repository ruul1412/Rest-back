import socket
import time
from app.core.config import settings

PRINTER_IP   = settings.PRINTER_IP
PRINTER_PORT = settings.PRINTER_PORT

# sale_type que van a la sección ENTRADAS (sumados globalmente).
# Los demás van a la sección PLATOS.
TIPOS_ENTRADA = {"entrada", "sopa"}


# ---------------------------------------------------------------------------
# Bajo nivel: socket → impresora
# ---------------------------------------------------------------------------
def send_to_printer(data: bytes, retries: int = 3, retry_delay: float = 0.6) -> bool:
    """
    Muchas impresoras térmicas de red duermen su módulo Wi-Fi/Ethernet tras
    un rato sin tráfico, o solo aceptan una conexión TCP a la vez. El primer
    intento después de estar inactiva puede colgarse hasta el timeout —
    por eso reintentamos automáticamente con un pequeño delay en vez de
    fallar directo (evita que el usuario tenga que cancelar y recrear
    la orden para que imprima).
    """
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(5)
                s.connect((PRINTER_IP, PRINTER_PORT))
                s.sendall(data)
            return True
        except Exception as e:
            last_error = e
            print(f"[PRINTER] Intento {attempt}/{retries} falló: {e}")
            if attempt < retries:
                time.sleep(retry_delay)

    print(f"[PRINTER] Error tras {retries} intentos: {last_error}")
    return False          # fallo silencioso — no revienta la orden


# ---------------------------------------------------------------------------
# Helpers ESC/POS
# ---------------------------------------------------------------------------
ESC = b'\x1b'
GS  = b'\x1d'

def _bold(on: bool) -> bytes:
    return ESC + b'E' + (b'\x01' if on else b'\x00')

def _align(pos: str) -> bytes:
    code = {'left': b'\x00', 'center': b'\x01', 'right': b'\x02'}.get(pos, b'\x00')
    return ESC + b'a' + code

def _font_size(big: bool) -> bytes:
    return ESC + b'!' + (b'\x30' if big else b'\x00')

def _line(text: str = '') -> bytes:
    return (text + '\n').encode('utf-8')

def _separator(char: str = '-', width: int = 32) -> bytes:
    return (char * width + '\n').encode()


# ---------------------------------------------------------------------------
# Consolidación de items
# ---------------------------------------------------------------------------
def _consolidate(items: list) -> list:
    """
    Devuelve dos listas: (platos, entradas).

    PLATOS
    ------
    Agrupa por (product_id, sale_type, variant_id, notas).
    - Sin nota   → se suman en una sola línea.
    - Con nota   → línea propia por cada nota distinta.
    - Adicionales (children) se consolidan dentro de su plato.

    ENTRADAS / SOPAS
    ----------------
    Se extraen de los children de cada plato (y de items directos del mismo
    tipo) y se suman globalmente por product_id, sin nota.
    Items con cantidad 0 se descartan.
    """
    plato_buckets: dict[tuple, dict] = {}
    entrada_buckets: dict[str, dict] = {}

    def _acumular_entrada(child: dict, qty: int):
        if qty <= 0:
            return
        pid = child.get("product_id", "")
        if pid not in entrada_buckets:
            entrada_buckets[pid] = {**child, "cantidad": qty, "notas": "", "children": []}
        else:
            entrada_buckets[pid]["cantidad"] += qty

    for item in items:
        st   = (item.get("sale_type") or "carta").lower()
        pid  = item.get("product_id") or item.get("id", "")
        vid  = item.get("variant_id") or ""
        nota = (item.get("notas") or "").strip()
        qty  = item.get("cantidad", 1)

        # Item directo de tipo entrada/sopa → pool global
        if st in TIPOS_ENTRADA:
            _acumular_entrada(item, qty)
            continue

        # Plato normal
        key = (pid, st, vid, nota)
        if key not in plato_buckets:
            plato_buckets[key] = {**item, "notas": nota, "children": []}
        else:
            plato_buckets[key]["cantidad"] += qty

        # Procesar children
        for child in item.get("children", []):
            child_st  = (child.get("sale_type") or "adicional").lower()
            child_qty = child.get("cantidad", 0)

            if child_st in TIPOS_ENTRADA:
                _acumular_entrada(child, child_qty)
            else:
                # Adicional → consolidar dentro del plato
                cpid  = child.get("product_id", "")
                cnota = (child.get("notas") or "").strip()
                ck    = (cpid, cnota)
                existing = {
                    (c.get("product_id"), (c.get("notas") or "").strip()): c
                    for c in plato_buckets[key]["children"]
                }
                if ck in existing:
                    existing[ck]["cantidad"] += child_qty
                else:
                    existing[ck] = {**child, "cantidad": child_qty}
                plato_buckets[key]["children"] = list(existing.values())

    platos   = list(plato_buckets.values())
    entradas = list(entrada_buckets.values())
    return platos, entradas


# ---------------------------------------------------------------------------
# Construcción de la comanda
# ---------------------------------------------------------------------------
def _build_comanda(tipo, cliente_nombre, notas_group, items) -> bytes:
    platos, entradas = _consolidate(items)
    lines: list[bytes] = []

    # ── Reset e inicialización ────────────────────────────────────────────
    lines.append(ESC + b'@')
    lines.append(GS  + b'W' + b'\x40\x02')   # ancho 576 dots
    lines.append(ESC + b'M\x00')              # font A

    # ── Cabecera ──────────────────────────────────────────────────────────
    lines.append(_align('center'))
    lines.append(_bold(True))
    lines.append(_font_size(True))
    lines.append(_line('Restaurante Hank\u00b4a'))
    lines.append(_font_size(False))
    lines.append(_bold(False))
    lines.append(_line())
    lines.append(_bold(True))
    lines.append(_line('*** COMANDA ***'))
    lines.append(_bold(False))
    lines.append(_align('left'))

    # ── Datos de la orden ─────────────────────────────────────────────────
    lines.append(_separator())
    lines.append(_bold(True))
    lines.append(_font_size(True))
    lines.append(_line(f'Tipo   : {(tipo or "mesa").upper()}'))
    lines.append(_line(f'Cliente: {cliente_nombre or "-"}'))
    lines.append(_font_size(False))
    lines.append(_bold(False))
    if notas_group:
        lines.append(_line(f'Nota   : {notas_group}'))
    lines.append(_separator())

    # ── Sección PLATOS ────────────────────────────────────────────────────
    if platos:
        lines.append(_bold(True))
        lines.append(_line('-- PLATOS --'))
        lines.append(_bold(False))
        lines.append(_line())

        for item in platos:
            qty  = item["cantidad"]
            name = item["product_name"]
            variant = item.get("variant_name") or item.get("variante") or ""
            display_name = f'{name} ({variant})' if variant else name

            lines.append(_bold(True))
            lines.append(_line(f'  x{qty}  {display_name}'))
            lines.append(_bold(False))

            if item.get("notas"):
                lines.append(_line(f'       >> {item["notas"]}'))

            for child in item.get("children", []):
                child_qty  = child.get("cantidad", 1)
                child_name = child.get("product_name", "")
                lines.append(_line(f'         + x{child_qty} {child_name}'))
                if child.get("notas"):
                    lines.append(_line(f'           >> {child["notas"]}'))

            lines.append(_line())

        lines.append(_separator())

    # ── Sección ENTRADAS ──────────────────────────────────────────────────
    if entradas:
        lines.append(_bold(True))
        lines.append(_line('-- ENTRADAS --'))
        lines.append(_bold(False))
        lines.append(_line())

        for item in entradas:
            qty  = item["cantidad"]
            name = item["product_name"]
            lines.append(_line(f'  x{qty}  {name}'))

        lines.append(_line())
        lines.append(_separator())

    # ── Pie ───────────────────────────────────────────────────────────────
    total = sum(i["cantidad"] for i in platos) + sum(i["cantidad"] for i in entradas)
    lines.append(_align('center'))
    lines.append(_line(f'{total} producto(s)'))
    lines.append(_line())
    lines.append(GS + b'V\x41\x03')   # corte parcial
    # Buzzer
    lines.append(ESC + b'\x42\x03\x03')

    return b''.join(lines)


# ---------------------------------------------------------------------------
# Punto de entrada público
# ---------------------------------------------------------------------------
def print_comanda(tipo, cliente_nombre, notas_group, items) -> bool:
    data = _build_comanda(tipo, cliente_nombre, notas_group, items)
    return send_to_printer(data)


# ---------------------------------------------------------------------------
# DEBUG temporal — eliminar una vez confirmada la estructura de items
# Agrega esta función y llámala en lugar de print_comanda para ver el log
# ---------------------------------------------------------------------------
def debug_items(items) -> None:
    """
    Llama esto desde donde invocas print_comanda para ver en los logs
    exactamente qué estructura llega antes de procesar.
    
    Uso rápido:
        from app.utils.printer import debug_items
        debug_items(orden.items)
    """
    import json
    print("[PRINTER-DEBUG] === items recibidos ===", flush=True)
    for i, item in enumerate(items):
        children = item.get("children") or []
        print(
            f"  [{i}] sale_type={item.get('sale_type')!r:12} "
            f"cantidad={item.get('cantidad')}  "
            f"name={item.get('product_name')!r}  "
            f"children={[c.get('product_name') for c in children]}",
            flush=True
        )
    print("[PRINTER-DEBUG] === fin ===", flush=True)