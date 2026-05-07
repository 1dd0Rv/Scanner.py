import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
from . import config


# ── Escaneo TCP ───────────────────────────────────────────────

def escanear_puerto(host, puerto):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(config.TIMEOUT)
        resultado = s.connect_ex((host, puerto))
        s.close()
        return resultado == 0
    except Exception:
        return False


def escanear_host(host, puertos, callback=None):
    abiertos = []
    with ThreadPoolExecutor(max_workers=config.MAX_THREADS) as executor:
        futuros = {executor.submit(escanear_puerto, host, p): p for p in puertos}
        for futuro in as_completed(futuros):
            puerto = futuros[futuro]
            try:
                if futuro.result():
                    abiertos.append(puerto)
            except Exception:
                pass
            if callback:
                callback()
    return sorted(abiertos)
