import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
from . import config


# ── Escaneo TCP ───────────────────────────────────────────────

# Intenta establecer una conexión TCP al puerto indicado.
# Usa connect_ex() en lugar de connect() para evitar excepciones:
# devuelve 0 si el puerto está abierto, otro número si está cerrado o filtrado.
def escanear_puerto(host, puerto):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(config.TIMEOUT)
        resultado = s.connect_ex((host, puerto))
        s.close()
        return resultado == 0
    except Exception:
        return False


# Lanza escanear_puerto() en paralelo para todos los puertos usando un pool
# de hilos. as_completed() procesa cada resultado en cuanto termina, sin
# esperar al orden original. El callback se llama tras cada puerto para
# avanzar la barra de progreso. Devuelve la lista de puertos abiertos ordenada.
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
