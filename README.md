# Scanner de Puertos Educativo

Herramienta de reconocimiento de red desarrollada con fines educativos para la asignatura **SAD (Seguridad y Alta Disponibilidad)**.  
Permite descubrir puertos abiertos, identificar servicios, capturar banners y estimar el sistema operativo de un host — **sin depender de nmap ni de ningún binario externo**.

> **Aviso legal:** Esta herramienta está diseñada exclusivamente para entornos controlados y con autorización expresa.  
> Su uso en redes o sistemas ajenos sin permiso es ilegal.

---

## Tabla de contenidos

1. [Descripción](#descripción)
2. [Librería externa](#librería-externa)
3. [Requisitos](#requisitos)
4. [Instalación](#instalación)
5. [Ejecución](#ejecución)
6. [Estructura del proyecto](#estructura-del-proyecto)
7. [Funcionamiento interno](#funcionamiento-interno)
8. [Ejemplo de salida](#ejemplo-de-salida)
9. [Dificultades y soluciones](#dificultades-y-soluciones)

---

## Descripción

El scanner educativo realiza cuatro tareas de reconocimiento:

1. **Escaneo TCP**: intenta conectarse a cada puerto para determinar si está abierto.
2. **Detección de servicios**: identifica qué servicio corre en cada puerto (SSH, HTTP, MySQL...).
3. **Captura de banners**: se conecta al puerto abierto y lee la respuesta del servicio para obtener versión y software.
4. **Detección de SO**: analiza el TTL del ping para estimar el sistema operativo del objetivo.

Soporta IPs individuales, hostnames y rangos CIDR (`192.168.1.0/24`).  
Usa hasta 150 hilos en paralelo, escaneando 1024 puertos en menos de un segundo.

---

## Librería externa

| Librería | Instalación | Versión mínima | Finalidad |
|----------|-------------|----------------|-----------|
| `rich` | `pip install rich` | 13.0 | Interfaz de consola visual: tablas, barras de progreso, colores y paneles |

`rich` es el único paquete externo del proyecto. Todo el escaneo se realiza con módulos estándar de Python (`socket`, `threading`, etc.), lo que permite ejecutar la herramienta en cualquier sistema con Python instalado sin necesitar nmap ni otros binarios.

---

## Requisitos

- Python **3.8** o superior
- pip
- Sistema operativo: Linux, macOS o Windows
- Red con acceso al objetivo (para uso real)

---

## Instalación

```bash
# 1. Entrar en la carpeta del proyecto
cd proyecto_2/

# 2. Instalar la única dependencia externa
pip install rich
```

No hay más dependencias. La herramienta está lista para ejecutarse.

---

## Ejecución

```bash
# Escaneo básico (puertos 1-1024)
python main.py 192.168.1.1

# Puertos específicos
python main.py 192.168.1.1 -p 22,80,443,3306

# Rango de puertos personalizado
python main.py 192.168.1.1 -p 1-65535

# Rango de red completo (CIDR)
python main.py 192.168.1.0/24 -p 22,80,443

# Sin detección de SO (más rápido)
python main.py 192.168.1.1 --no-os

# Sin captura de banners
python main.py 192.168.1.1 --no-banner

# Ver ayuda
python main.py --help
```

### Opciones disponibles

| Opción | Descripción | Por defecto |
|--------|-------------|-------------|
| `objetivo` | IP, hostname o rango CIDR | — |
| `-p`, `--puertos` | Puertos a escanear | `1-1024` |
| `-t`, `--timeout` | Timeout por puerto (segundos) | `1.0` |
| `--threads` | Hilos paralelos | `150` |
| `--no-banner` | No capturar banners | desactivado |
| `--no-os` | No detectar SO | desactivado |

Detener el escaneo: `Ctrl + C`

---

## Estructura del proyecto

```
proyecto_2/
├── main.py                   # Punto de entrada — CLI con argparse
├── .env.example              # Variables de entorno opcionales
├── README.md
└── scanner_pkg/              # Paquete principal
    ├── __init__.py           # Exporta las funciones públicas
    ├── config.py             # Configuración global (timeouts, hilos, servicios)
    ├── red.py                # Parseo de IPs, CIDR y rangos de puertos
    ├── scanner.py            # Escaneo TCP con ThreadPoolExecutor
    ├── servicios.py          # Detección de servicios y captura de banners
    ├── os_detect.py          # Estimación de SO por TTL del ping
    └── display.py            # Toda la UI con rich (tablas, progreso, colores)
```

Cada módulo tiene una única responsabilidad. `display.py` no sabe nada de sockets; `scanner.py` no sabe nada de cómo mostrar los resultados.

---

## Funcionamiento interno

```
main.py
  │
  ├─ red.py ──────────► Convierte "192.168.1.0/24" en lista de IPs
  │                      Convierte "1-1024" en lista de puertos
  │
  ├─ os_detect.py ────► ping -c 1 <host> → parsea TTL → estima SO
  │
  ├─ scanner.py ──────► ThreadPoolExecutor (150 hilos)
  │                        └─ socket.connect_ex() por cada puerto
  │                        └─ devuelve lista de puertos abiertos
  │
  ├─ servicios.py ────► Para cada puerto abierto:
  │                        ├─ Busca en mapa de servicios conocidos
  │                        └─ Conecta y lee banner (recv 1024 bytes)
  │
  └─ display.py ──────► rich: cabecera, tabla de info, barra de progreso, tabla de resultados
```

### Módulos estándar utilizados

| Módulo | Uso en el proyecto |
|--------|--------------------|
| `socket` | Conexiones TCP para el escaneo y captura de banners |
| `concurrent.futures` | `ThreadPoolExecutor` para escaneo paralelo |
| `ipaddress` | Expansión de rangos CIDR |
| `subprocess` | Ejecución del ping para detección de SO |
| `argparse` | Interfaz de línea de comandos |
| `re` | Extracción del TTL de la salida del ping |
| `os` | Lectura de variables de entorno |
| `sys` | Control de salida del proceso |
| `time` | Medición del tiempo de escaneo |
| `platform` | Detección del SO del atacante (flag del ping) |

---

## Ejemplo de salida

```
╭──────────────────────────────────────────────╮
│         Scanner de Puertos  —  SAD           │
╰──────────────────────────────────────────────╯

──────────────────── 192.168.1.105 ─────────────────────
Detectando SO de 192.168.1.105...

   Objetivo              192.168.1.105
   IP resuelta           192.168.1.105
   SO detectado          Linux / macOS  (TTL=64)
   Puertos a escanear    1024

  Escaneando 192.168.1.105... ━━━━━━━━━━━━━━━━━━━━ 100% 0:00:01

             Puertos abiertos en 192.168.1.105
╭─────────┬────────────┬──────────┬─────────────────────────╮
│  Puerto │   Estado   │ Servicio │ Banner                  │
├─────────┼────────────┼──────────┼─────────────────────────┤
│      22 │  ABIERTO   │ SSH      │ SSH-2.0-OpenSSH_8.9p1   │
│      80 │  ABIERTO   │ HTTP     │ HTTP/1.1 200 OK         │
│    3306 │  ABIERTO   │ MySQL    │ —                       │
╰─────────┴────────────┴──────────┴─────────────────────────╯

3 puerto(s) abierto(s)  ·  Tiempo: 1.24s
```

---

## Dificultades y soluciones

| Dificultad encontrada | Solución aplicada |
|-----------------------|-------------------|
| Escaneo lento en rangos grandes | `ThreadPoolExecutor` con 150 hilos paralelos |
| Salida de consola poco visual | Librería `rich` para tablas, colores y barra de progreso |
| La barra de progreso no se actualizaba en tiempo real | Pasar un `callback` desde `escanear_host()` que llama a `progreso.advance()` |
| El flag de ping es diferente en Windows y Linux | Detección del SO del atacante con `platform.system()` |
| Algunos servicios HTTP no envían banner espontáneamente | Enviar petición `HEAD /` para provocar la respuesta del servidor |
| Parseo de CIDR y rangos de puertos en el mismo módulo | Módulo `red.py` dedicado exclusivamente a parsing de entrada |
