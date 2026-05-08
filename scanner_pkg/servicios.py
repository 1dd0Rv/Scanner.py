import socket
from . import config


# ── Servicios y banners ───────────────────────────────────────

# Devuelve el nombre del servicio asociado a un puerto.
# Primero consulta el diccionario local (más rápido), si no está
# recurre a socket.getservbyport() que consulta la base de datos del sistema.
def obtener_servicio(puerto):
    if puerto in config.SERVICIOS_CONOCIDOS:
        return config.SERVICIOS_CONOCIDOS[puerto]
    try:
        return socket.getservbyport(puerto, 'tcp')
    except OSError:
        return 'Desconocido'


# Abre una conexión TCP al puerto y lee los primeros bytes que envía el servicio.
# Ese texto es el banner: revela qué software y versión está corriendo.
# Para HTTP envía una petición HEAD primero porque esos servidores no
# envían nada espontáneamente. Devuelve solo la primera línea, máximo 60 caracteres.
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
