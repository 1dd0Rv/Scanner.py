import ipaddress
import socket


# ── Funciones de red ──────────────────────────────────────────

# Recibe el argumento -p del usuario (ej: '22,80,100-200') y lo convierte
# en una lista de enteros ordenada y sin duplicados para pasársela al scanner.
def parsear_puertos(rango):
    """Convierte '1-1024' o '22,80,443' en lista de enteros."""
    puertos = []
    for parte in rango.split(','):
        parte = parte.strip()
        if '-' in parte:
            inicio, fin = parte.split('-', 1)
            puertos.extend(range(int(inicio), int(fin) + 1))
        else:
            puertos.append(int(parte))
    return sorted(set(puertos))


# Recibe el objetivo del usuario (IP, hostname o rango CIDR) y devuelve
# una lista de IPs string. Si es CIDR, expande todos los hosts de la red.
# Si no se reconoce como red, lo trata como host único.
def parsear_hosts(objetivo):
    """Convierte IP, hostname o CIDR en lista de hosts."""
    try:
        red = ipaddress.ip_network(objetivo, strict=False)
        return [str(ip) for ip in red.hosts()]
    except ValueError:
        return [objetivo]


# Consulta el DNS para obtener la IP de un hostname.
# Si el usuario ya pasó una IP directamente, la devuelve tal cual.
# Devuelve None si no se puede resolver, para que main.py muestre el error.
def resolver_hostname(host):
    """Resuelve hostname a IP. Devuelve None si falla."""
    try:
        return socket.gethostbyname(host)
    except socket.gaierror:
        return None
