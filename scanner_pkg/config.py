import os

# ── Configuración ─────────────────────────────────────────────

TIMEOUT        = float(os.environ.get('SCAN_TIMEOUT', 1.0))
MAX_THREADS    = int(os.environ.get('SCAN_THREADS', 150))
DEFAULT_PORTS  = '1-1024'
BANNER_TIMEOUT = float(os.environ.get('BANNER_TIMEOUT', 2.0))

# ── Servicios conocidos ───────────────────────────────────────

SERVICIOS_CONOCIDOS = {
    21:    'FTP',
    22:    'SSH',
    23:    'Telnet',
    25:    'SMTP',
    53:    'DNS',
    80:    'HTTP',
    110:   'POP3',
    135:   'RPC',
    139:   'NetBIOS',
    143:   'IMAP',
    443:   'HTTPS',
    445:   'SMB',
    993:   'IMAPS',
    995:   'POP3S',
    1433:  'MSSQL',
    3306:  'MySQL',
    3389:  'RDP',
    5432:  'PostgreSQL',
    5900:  'VNC',
    6379:  'Redis',
    8080:  'HTTP-Alt',
    8443:  'HTTPS-Alt',
    27017: 'MongoDB',
}
