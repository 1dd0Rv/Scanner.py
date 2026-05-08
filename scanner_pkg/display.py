from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn, TextColumn
from rich import box

console = Console()


# ── Funciones de visualización ────────────────────────────────

# Imprime el panel de título al arrancar el programa.
def mostrar_cabecera():
    texto = Text("Scanner de Puertos  —  1dd0Rv", justify="center", style="bold cyan")
    console.print(Panel(texto, border_style="cyan", padding=(1, 4)))


# Muestra una tabla con los datos del objetivo antes de empezar el escaneo:
# hostname, IP resuelta, SO detectado y número de puertos que se van a escanear.
def mostrar_info_objetivo(host, ip, os_detectado, total_puertos):
    tabla = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
    tabla.add_column(style="bold dim", width=20)
    tabla.add_column()
    tabla.add_row("Objetivo",            f"[bold]{host}[/bold]")
    tabla.add_row("IP resuelta",         ip or "[red]No resuelta[/red]")
    tabla.add_row("SO detectado",        os_detectado)
    tabla.add_row("Puertos a escanear",  str(total_puertos))
    console.print(tabla)


# Crea y devuelve una barra de progreso de rich con spinner, barra, porcentaje
# y tiempo transcurrido. Se usa con 'with' en main.py para que se cierre sola.
def crear_progreso():
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=40),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console,
    )


# Muestra la tabla final con todos los puertos abiertos encontrados,
# su servicio y banner. Si no hay ninguno abierto, muestra un panel de aviso.
# Al final imprime el total de puertos abiertos y el tiempo que tardó el escaneo.
def mostrar_resultados(host, resultados, tiempo):
    console.print()

    if not resultados:
        console.print(Panel(
            "[bold red]No se encontraron puertos abiertos.[/bold red]",
            border_style="red"
        ))
        return

    tabla = Table(
        title=f"[bold cyan]Puertos abiertos en {host}[/bold cyan]",
        box=box.ROUNDED,
        border_style="cyan",
        show_lines=True,
        padding=(0, 1),
    )
    tabla.add_column("Puerto",   style="bold yellow", justify="right",  width=8)
    tabla.add_column("Estado",   justify="center",                       width=10)
    tabla.add_column("Servicio", style="bold white",                     width=14)
    tabla.add_column("Banner",   style="dim",                            min_width=20)

    for puerto, servicio, banner in resultados:
        tabla.add_row(
            str(puerto),
            "[bold green]ABIERTO[/bold green]",
            servicio,
            banner or "—",
        )

    console.print(tabla)
    console.print(
        f"\n[bold green]{len(resultados)} puerto(s) abierto(s)[/bold green]"
        f"  [dim]·  Tiempo: {tiempo:.2f}s[/dim]"
    )


# Imprime un mensaje de error en rojo. Se usa cuando algo falla
# pero el programa puede continuar (host no resuelto, puerto inválido...).
def mostrar_error(mensaje):
    console.print(f"[bold red][!] {mensaje}[/bold red]")


# Imprime un mensaje informativo en gris tenue para no distraer al usuario
# mientras el scanner trabaja (ej: "Detectando SO...").
def mostrar_info(mensaje):
    console.print(f"[dim]{mensaje}[/dim]")
