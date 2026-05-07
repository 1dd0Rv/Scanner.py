import ipaddress
import socket


# ── Funciones de red ──────────────────────────────────────────

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


def parsear_hosts(objetivo):
    """Convierte IP, hostname o CIDR en lista de hosts."""
    try:
        red = ipaddress.ip_network(objetivo, strict=False)
        return [str(ip) for ip in red.hosts()]
    except ValueError:
        return [objetivo]


def resolver_hostname(host):
    """Resuelve hostname a IP. Devuelve None si falla."""
    try:
        return socket.gethostbyname(host)
    except socket.gaierror:
        return None
