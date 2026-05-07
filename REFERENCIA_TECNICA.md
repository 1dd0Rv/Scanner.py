# Referencia técnica personal — Cómo funciona cada parte

> Archivo de uso personal. Explica el "por qué" de cada decisión técnica.

---

## Flujo completo de ejecución

```
Usuario escribe: python main.py 192.168.1.1 -p 1-1024

main.py
  1. argparse recoge los argumentos
  2. red.parsear_puertos("1-1024")  →  [1, 2, 3, ..., 1024]
  3. red.parsear_hosts("192.168.1.1")  →  ["192.168.1.1"]
  4. red.resolver_hostname("192.168.1.1")  →  "192.168.1.1"
  5. os_detect.detectar_os("192.168.1.1")  →  "Linux / macOS (TTL=64)"
  6. display.mostrar_info_objetivo(...)  →  tabla de resumen
  7. scanner.escanear_host(...)  →  [22, 80, 3306]  (puertos abiertos)
  8. servicios.obtener_servicio(22)  →  "SSH"
  9. servicios.obtener_banner("192.168.1.1", 22)  →  "SSH-2.0-OpenSSH_8.9"
 10. display.mostrar_resultados(...)  →  tabla final
```

---

## config.py — Configuración global

```python
TIMEOUT = 1.0        # segundos que espera cada hilo antes de declarar el puerto cerrado
MAX_THREADS = 150    # hilos paralelos. Más hilos = más rápido pero más carga en la red
DEFAULT_PORTS = '1-1024'
BANNER_TIMEOUT = 2.0 # el banner necesita más tiempo porque hay que enviar/recibir datos
```

**¿Por qué 150 hilos y no 1000?**  
Con 1000 hilos el sistema operativo empieza a rechazar conexiones (límite de file descriptors).  
150 es un equilibrio entre velocidad y estabilidad.

**¿Por qué leer de variables de entorno?**  
Permite cambiar el comportamiento sin tocar el código:
```bash
SCAN_TIMEOUT=0.5 SCAN_THREADS=200 python main.py 192.168.1.1
```

**SERVICIOS_CONOCIDOS**  
Diccionario `{puerto: nombre}`. Se consulta antes que el sistema operativo porque es más rápido y fiable para los puertos más comunes.

---

## red.py — Parseo de entrada

### parsear_puertos()

```python
"1-1024"      →  [1, 2, 3, ..., 1024]      # rango
"22,80,443"   →  [22, 80, 443]             # lista
"22,80-90"    →  [22, 80, 81, ..., 90]     # combinado
```

El truco clave: `set()` al final elimina duplicados si el usuario pone rangos solapados como `1-100,50-200`.

### parsear_hosts()

```python
"192.168.1.1"      →  ["192.168.1.1"]                     # IP individual
"192.168.1.0/24"   →  ["192.168.1.1", ..., "192.168.1.254"]  # CIDR
"scanme.nmap.org"  →  ["scanme.nmap.org"]                  # hostname
```

`ipaddress.ip_network(objetivo, strict=False)` acepta tanto `192.168.1.0/24` como `192.168.1.5/24` (strict=False ignora los bits de host).  
`.hosts()` excluye la dirección de red (.0) y la de broadcast (.255).

### resolver_hostname()

Convierte hostname a IP. Si falla devuelve `None` y main.py salta ese host.  
`socket.gethostbyname()` usa el DNS del sistema, igual que haría cualquier otra herramienta.

---

## scanner.py — El núcleo del escaneo

### escanear_puerto()

```python
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# AF_INET = IPv4, SOCK_STREAM = TCP (orientado a conexión)

s.settimeout(config.TIMEOUT)
# Sin timeout el hilo se quedaría bloqueado indefinidamente en puertos filtrados

resultado = s.connect_ex((host, puerto))
# connect_ex devuelve 0 si la conexión tuvo éxito (puerto ABIERTO)
# devuelve errno (111, 113...) si fue rechazada o no hubo respuesta (CERRADO/FILTRADO)
```

**¿Por qué connect_ex y no connect?**  
`connect()` lanza una excepción en puertos cerrados → hay que capturarla → más lento.  
`connect_ex()` devuelve un número → `resultado == 0` es suficiente → más limpio y rápido.

### escanear_host()

```python
with ThreadPoolExecutor(max_workers=150) as executor:
    futuros = {executor.submit(escanear_puerto, host, p): p for p in puertos}
    for futuro in as_completed(futuros):
        # as_completed() devuelve cada futuro en el orden en que termina,
        # no en el orden en que se lanzó. Así procesamos resultados en tiempo real.
        puerto = futuros[futuro]
        if futuro.result():
            abiertos.append(puerto)
        callback()  # avanza la barra de progreso
```

**¿Cómo funciona ThreadPoolExecutor?**  
Crea un pool de 150 hilos. `submit()` encola tareas. Los hilos las van cogiendo del pool.  
Cuando un hilo termina, su resultado queda en el `Future` correspondiente.  
`as_completed()` es un iterador que "desbloquea" cada Future cuando su hilo termina.

**¿Por qué `{executor.submit(...): p for p in puertos}`?**  
Es un diccionario `{futuro: puerto}`. Cuando `as_completed` nos devuelve un futuro,  
hacemos `futuros[futuro]` para saber a qué puerto corresponde ese resultado.

---

## servicios.py — Identificación de servicios y banners

### obtener_servicio()

```python
if puerto in config.SERVICIOS_CONOCIDOS:
    return config.SERVICIOS_CONOCIDOS[puerto]  # rápido, de memoria
try:
    return socket.getservbyport(puerto, 'tcp')  # consulta /etc/services del SO
except OSError:
    return 'Desconocido'
```

Primero busca en nuestro diccionario. Si no está, pregunta al sistema operativo.  
`/etc/services` en Linux / `%WINDIR%\system32\drivers\etc\services` en Windows.

### obtener_banner()

```python
s.connect((host, puerto))

if puerto in (80, 8080, 8443):
    s.send(b'HEAD / HTTP/1.0\r\nHost: ' + host.encode() + b'\r\n\r\n')
# HTTP no envía nada hasta que el cliente habla primero.
# HEAD pide solo las cabeceras (sin body), suficiente para ver Server: Apache/2.4...

banner = s.recv(1024).decode('utf-8', errors='ignore').strip()
# 1024 bytes es suficiente para la primera línea de cualquier banner
# errors='ignore' evita que caracteres no-UTF8 rompan el script

return banner.split('\n')[0].strip()[:60]
# Solo la primera línea, máximo 60 caracteres para que quepa en la tabla
```

**¿Por qué algunos banners aparecen como "—"?**  
Tres razones posibles:
1. El servicio no envía banner (MySQL, PostgreSQL necesitan autenticación primero)
2. El BANNER_TIMEOUT expiró antes de recibir datos
3. El servicio espera que el cliente hable primero y no hemos implementado su protocolo

---

## os_detect.py — Detección de SO por TTL

### ¿Qué es el TTL?

TTL = Time To Live. Campo del paquete IP. Cada router que atraviesa el paquete lo decrementa en 1.  
Cuando llega a 0, el router descarta el paquete (evita bucles infinitos).

**Valores de TTL inicial por SO:**
| SO | TTL inicial | Si llega con TTL=61... |
|----|------------|------------------------|
| Linux / macOS | 64 | fue Linux, pasó por 3 routers |
| Windows | 128 | fue Windows, pasó por 67 routers |
| Cisco / Router | 255 | fue un dispositivo de red |

### Cómo funciona el código

```python
flag = '-n' if platform.system().lower() == 'windows' else '-c'
# En Windows el flag para "número de paquetes" es -n, en Unix es -c

resultado = subprocess.run(
    ['ping', flag, '1', '-W', '2', host],
    # 1 = un solo paquete, -W 2 = esperar máximo 2 segundos
    capture_output=True,   # captura stdout y stderr en vez de imprimirlos
    text=True,             # decodifica bytes a string automáticamente
    timeout=5              # si ping tarda más de 5s, lanza TimeoutExpired
)

match = re.search(r'ttl[=\s](\d+)', salida, re.IGNORECASE)
# regex que busca "ttl=64" o "TTL 64" o "TTL=128" etc.
# (\d+) captura los dígitos del TTL en el grupo 1

ttl = int(match.group(1))  # convierte "64" a 64
```

**¿Por qué `re.IGNORECASE`?**  
En Linux la salida es `ttl=64`, en Windows es `TTL=128`. El flag ignora mayúsculas.

---

## display.py — Interfaz visual con rich

### Console

```python
console = Console()
# Objeto global compartido por todos los módulos.
# Gestiona colores, anchura del terminal, y si la salida va a un archivo o a pantalla.
```

### Panel y cabecera

```python
texto = Text("Scanner de Puertos  —  SAD", justify="center", style="bold cyan")
console.print(Panel(texto, border_style="cyan", padding=(1, 4)))
# Panel dibuja el borde con caracteres Unicode (╭─╮│╰─╯)
# padding=(1, 4) = 1 línea de margen vertical, 4 de margen horizontal
```

### Tabla de información

```python
tabla = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
# show_header=False: no queremos fila de cabecera en esta tabla
# box.SIMPLE: solo línea horizontal sin bordes verticales (más limpio)
```

### Progress (barra de progreso)

```python
Progress(
    SpinnerColumn(),          # el spinner giratorio de la izquierda
    TextColumn("..."),        # texto descriptivo
    BarColumn(bar_width=40),  # la barra ━━━━━━━━
    TaskProgressColumn(),     # porcentaje "100%"
    TimeElapsedColumn(),      # tiempo transcurrido "0:00:01"
)
```

**¿Por qué necesita el callback?**  
`escanear_host()` corre en hilos. El hilo principal está dentro del `with Progress()`.  
Cada hilo worker llama a `callback()` al terminar → el callback llama a `progreso.advance(tarea)` → la barra se actualiza.  
Sin callback, la barra solo se actualizaría al final (inútil).

### Tabla de resultados

```python
tabla.add_column("Puerto", style="bold yellow", justify="right", width=8)
# style aplica color a todas las celdas de esa columna
# justify="right" alinea los números a la derecha

"[bold green]ABIERTO[/bold green]"
# Markup de rich: igual que HTML pero con corchetes
# bold = negrita, green = color verde
```

---

## main.py — Coordinador

### argparse

```python
parser.add_argument('-p', '--puertos', default=config.DEFAULT_PORTS, ...)
# -p versión corta, --puertos versión larga. El usuario puede usar cualquiera.
# default= valor si el usuario no pasa el argumento
```

### El callback de progreso

```python
with crear_progreso() as progreso:
    tarea = progreso.add_task(f'Escaneando {host}...', total=len(puertos))
    puertos_abiertos = escanear_host(
        host, puertos,
        callback=lambda: progreso.advance(tarea)
        # lambda: función anónima sin argumentos que avanza la tarea en 1
    )
```

**¿Por qué lambda?**  
`escanear_host` espera un callable sin argumentos.  
`progreso.advance(tarea)` necesita el argumento `tarea`.  
`lambda: progreso.advance(tarea)` envuelve la llamada con el argumento ya incluido (closure).

### KeyboardInterrupt

```python
try:
    main()
except KeyboardInterrupt:
    console.print('[bold yellow][!] Escaneo interrumpido[/bold yellow]')
    sys.exit(0)
# Sin esto, Ctrl+C muestra un traceback feo en pantalla.
# sys.exit(0) = salida limpia (código 0 = sin error)
```

---

## Preguntas técnicas que pueden surgir

**¿Qué es un socket?**  
Un punto final de comunicación. Cuando haces `socket.connect((host, puerto))`, el SO hace el TCP handshake (SYN → SYN-ACK → ACK). Si el servidor acepta la conexión, el puerto está abierto. Si responde con RST, está cerrado. Si no responde, está filtrado (firewall).

**¿Diferencia entre puerto abierto, cerrado y filtrado?**  
- Abierto: hay un servicio escuchando, acepta la conexión
- Cerrado: no hay servicio, el SO responde con RST (rechazo inmediato)
- Filtrado: un firewall descarta el paquete sin responder → timeout

**¿Por qué el escaneo es más lento en puertos filtrados?**  
Porque no hay respuesta. El socket espera hasta que expira el timeout (1 segundo).  
Los puertos cerrados responden inmediatamente con RST, así que son rápidos.

**¿Qué es un future?**  
Un objeto que representa el resultado de una operación que todavía no ha terminado.  
`executor.submit(función)` devuelve un Future inmediatamente.  
`futuro.result()` bloquea hasta que la función termina y devuelve su resultado.

**¿Qué es un daemon thread?**  
(No aplica aquí pero puede salir del keylogger)  
Un hilo que muere automáticamente cuando el proceso principal termina.  
Sin daemon=True, el proceso seguiría vivo mientras el hilo esté corriendo.
