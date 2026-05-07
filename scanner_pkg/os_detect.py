import subprocess
import platform
import re


# ── Detección de SO por TTL ───────────────────────────────────

def detectar_os(host):
    # TTL <= 64 → Linux/macOS | <= 128 → Windows | <= 255 → Cisco/Router
    try:
        flag = '-n' if platform.system().lower() == 'windows' else '-c'
        resultado = subprocess.run(
            ['ping', flag, '1', '-W', '2', host],
            capture_output=True,
            text=True,
            timeout=5
        )
        salida = resultado.stdout + resultado.stderr

        match = re.search(r'ttl[=\s](\d+)', salida, re.IGNORECASE)
        if not match:
            return 'No responde al ping'

        ttl = int(match.group(1))

        if ttl <= 64:
            return f'Linux / macOS  (TTL={ttl})'
        elif ttl <= 128:
            return f'Windows  (TTL={ttl})'
        elif ttl <= 255:
            return f'Cisco / Router  (TTL={ttl})'
        else:
            return f'Desconocido  (TTL={ttl})'

    except FileNotFoundError:
        return 'ping no disponible'
    except subprocess.TimeoutExpired:
        return 'Timeout'
    except Exception as e:
        return f'Error: {e}'
