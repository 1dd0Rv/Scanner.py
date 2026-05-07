import socket
from . import config


# ── Servicios y banners ───────────────────────────────────────

def obtener_servicio(puerto):
    if puerto in config.SERVICIOS_CONOCIDOS:
        return config.SERVICIOS_CONOCIDOS[puerto]
    try:
        return socket.getservbyport(puerto, 'tcp')
    except OSError:
        return 'Desconocido'


def obtener_banner(host, puerto):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(config.BANNER_TIMEOUT)
        s.connect((host, puerto))

        # Los puertos HTTP no envían banner sin petición previa
        if puerto in (80, 8080, 8443):
            s.send(b'HEAD / HTTP/1.0\r\nHost: ' + host.encode() + b'\r\n\r\n')

        banner = s.recv(1024).decode('utf-8', errors='ignore').strip()
        s.close()

        primera_linea = banner.split('\n')[0].strip()
        return primera_linea[:60] if primera_linea else ''
    except Exception:
        return ''
