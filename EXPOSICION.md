# Guía de Exposición Oral — Scanner de Puertos
**Duración objetivo: 12-14 minutos**

---

## Antes de entrar al aula

- Terminal abierta en `proyecto_2/`
- VM víctima encendida y con su IP anotada
- Probado una vez en casa que el escaneo llega a la VM
- Comando preparado para copiar/pegar si los nervios juegan en contra

---

## BLOQUE 1 — Introducción y contexto (2 min)

> *Empieza sin mirar el ordenador. Habla al profesor y a la clase.*

**Lo que dices:**

"He desarrollado un scanner de puertos en Python. La idea surgió de un escenario real de ciberseguridad: imagina que eres un auditor o un atacante que ha conseguido acceso a una máquina, pero esa máquina no tiene nmap instalado y no tienes permisos para instalar nada. Solo tienes Python.

Ahí es donde entra este proyecto. Con solo Python y una librería de visualización, puedo hacer exactamente lo mismo que haría nmap en su modalidad más básica: descubrir qué puertos tiene abiertos una máquina, qué servicios corren en esos puertos, capturar el banner del servicio para saber la versión, y estimar el sistema operativo del objetivo."

---

## BLOQUE 2 — La librería externa: rich (2 min)

> *Aquí puedes abrir el terminal y ejecutar el script una vez rápido para que vean la interfaz antes de explicarla.*

**Lo que dices:**

"La librería externa elegida es `rich`, instalable con `pip install rich`. 

¿Por qué rich y no python-nmap? Porque python-nmap es un wrapper que necesita nmap instalado en el sistema. Si no hay nmap, no funciona. Rich en cambio es pura visualización: no tiene dependencias del sistema operativo, no necesita binarios externos, y hace que la salida de consola sea completamente diferente a un simple print."

**Señala en pantalla:**
- La cabecera con panel
- La tabla de información del objetivo
- La barra de progreso animada
- La tabla de resultados con colores

"Sin rich, esto sería texto plano imposible de leer en una demo. Con rich, el profesor ve de un vistazo qué puerto está abierto, qué servicio tiene, y qué versión de software está corriendo."

---

## BLOQUE 3 — Estructura del proyecto (2 min)

> *Muestra el árbol de archivos en terminal: `find proyecto_2 -type f | sort`*

**Lo que dices:**

"El proyecto está organizado en un paquete Python llamado `scanner_pkg` con seis módulos, cada uno con una responsabilidad única:

- `config.py` — toda la configuración en un sitio: timeouts, número de hilos, mapa de servicios conocidos
- `red.py` — parsea la entrada del usuario: convierte un CIDR en lista de IPs, convierte `1-1024` en lista de puertos
- `scanner.py` — el núcleo: abre conexiones TCP con socket y usa ThreadPoolExecutor para hacerlo en paralelo
- `servicios.py` — para cada puerto abierto, identifica el servicio y captura el banner
- `os_detect.py` — hace un ping, extrae el TTL y estima el sistema operativo
- `display.py` — toda la interfaz visual con rich: tablas, barra de progreso, colores

Y `main.py` que es el punto de entrada: recoge los argumentos con argparse y coordina todo."

---

## BLOQUE 4 — Demo en vivo (5 min)

> *Esta es la parte más importante. Hazlo despacio, explicando cada línea que aparece.*

**Paso 1 — Enseña la ayuda**
```bash
python main.py --help
```
"Primero la ayuda. Vemos que acepta una IP o un rango CIDR, podemos elegir los puertos, el timeout, el número de hilos..."

**Paso 2 — Escaneo básico contra la VM**
```bash
python main.py <IP_VM> -p 1-1024
```
Mientras carga, explica:
"Está lanzando 150 hilos en paralelo. Cada hilo intenta una conexión TCP a un puerto. Si el puerto responde, lo marca como abierto. Primero hace un ping para detectar el sistema operativo por el TTL..."

Cuando aparezcan los resultados:
"Aquí vemos los puertos abiertos. El TTL que ha devuelto el ping es 64, que corresponde a Linux. En Windows sería 128. Y aquí en la columna Banner vemos qué software y versión está corriendo en ese puerto."

**Paso 3 — Escaneo de puertos específicos**
```bash
python main.py <IP_VM> -p 22,80,443,3306,5432
```
"Si ya sé qué puertos me interesan puedo escanear solo esos. Es mucho más rápido."

**Paso 4 (opcional si hay tiempo) — CIDR**
```bash
python main.py 192.168.1.0/24 -p 22,80
```
"También puedo escanear una red entera. Le paso el rango en notación CIDR y escanea todos los hosts."

---

## BLOQUE 5 — Dificultades y soluciones (1-2 min)

**Lo que dices:**

"Las tres dificultades principales que encontré:

Primera: la velocidad. Escanear 1024 puertos de forma secuencial tardaba 17 minutos con timeout de 1 segundo. La solución fue `ThreadPoolExecutor` con 150 hilos en paralelo. Ahora tarda menos de un segundo.

Segunda: la barra de progreso no se actualizaba en tiempo real porque el hilo principal estaba bloqueado esperando a los workers. La solución fue pasar una función `callback` que cada hilo llama al terminar su puerto, y ese callback avanza la barra.

Tercera: el flag del comando ping es diferente en Windows (`-n`) y en Linux (`-c`). Lo resolví detectando el sistema operativo del atacante con `platform.system()` antes de construir el comando."

---

## Posibles preguntas del profesor

**¿Qué diferencia hay con nmap?**
"Nmap es una herramienta compilada en C con años de desarrollo, hace decenas de tipos de escaneo (SYN, UDP, XMAS...). Este script solo hace TCP connect scan, que es el más básico. Pero la ventaja es que no necesita instalación y funciona en cualquier máquina con Python."

**¿Por qué usas connect_ex en vez de connect?**
"connect() lanza una excepción si el puerto está cerrado, lo que es más lento de gestionar. connect_ex() devuelve un código de error numérico: 0 significa éxito, cualquier otro número significa cerrado o filtrado. Es más eficiente en un bucle de miles de puertos."

**¿Qué es el banner grabbing?**
"Cuando te conectas a un servidor, muchos servicios envían automáticamente una línea de presentación con su nombre y versión. Eso es el banner. Por ejemplo, OpenSSH responde con `SSH-2.0-OpenSSH_8.9p1`. Capturarlo nos da información de versión sin necesidad de autenticarnos."

**¿Qué es el TTL y cómo detecta el SO?**
"TTL son las siglas de Time To Live. Es un campo del paquete IP que se decrementa en 1 en cada router que atraviesa. Los sistemas operativos tienen valores iniciales distintos: Linux arranca en 64, Windows en 128, los routers Cisco en 255. Si el objetivo responde con TTL=61, fue Linux y el paquete pasó por 3 routers."

**¿Podría hacer un escaneo UDP?**
"UDP es más complejo porque es un protocolo sin conexión. No hay handshake, así que no puedes saber si el puerto está abierto o simplemente no responde. Requeriría enviar paquetes específicos por servicio y analizar las respuestas ICMP. Es algo que se podría añadir como mejora."

**¿Qué módulos estándar usas?**
"socket para las conexiones TCP, concurrent.futures para el ThreadPoolExecutor, ipaddress para parsear rangos CIDR, subprocess para ejecutar el ping, argparse para la CLI, re para extraer el TTL con una expresión regular, platform para detectar el SO del atacante, y time para medir la duración del escaneo."
