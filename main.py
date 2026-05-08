#!/usr/bin/env python3

import argparse
import sys
import os
import time

sys.path.insert(0, os.path.dirname(__file__))

import scanner_pkg.config as config
from scanner_pkg.red import parsear_puertos, parsear_hosts, resolver_hostname
from scanner_pkg.scanner import escanear_host
from scanner_pkg.servicios import obtener_servicio, obtener_banner
from scanner_pkg.os_detect import detectar_os
from scanner_pkg.display import (
    console,
    mostrar_cabecera,
    mostrar_info_objetivo,
    crear_progreso,
    mostrar_resultados,
    mostrar_error,
    mostrar_info,
)


# ── Argumentos ────────────────────────────────────────────────

# Define todos los argumentos que acepta el programa por línea de comandos.
# argparse se encarga de validarlos, mostrar el --help y devolver
# un objeto con los valores listos para usar.
def parse_args():
    parser = argparse.ArgumentParser(description='Scanner de puertos educativo - SAD')
    parser.add_argument('objetivo', help='IP, hostname o rango CIDR')
    parser.add_argument('-p', '--puertos', default=config.DEFAULT_PORTS,
                        help='Puertos a escanear (ej: 1-1024 ó 22,80,443)')
    parser.add_argument('-t', '--timeout', type=float, default=config.TIMEOUT,
                        help=f'Timeout por puerto en segundos (por defecto: {config.TIMEOUT})')
    parser.add_argument('--threads', type=int, default=config.MAX_THREADS,
                        help=f'Hilos paralelos (por defecto: {config.MAX_THREADS})')
    parser.add_argument('--no-banner', action='store_true',
                        help='No intentar capturar banners')
    parser.add_argument('--no-os', action='store_true',
                        help='No intentar detectar el sistema operativo')
    return parser.parse_args()


# ── Main ──────────────────────────────────────────────────────

# Función principal que orquesta todo el flujo del programa:
# 1. Recoge los argumentos del usuario
# 2. Muestra la cabecera
# 3. Parsea puertos y hosts
# 4. Para cada host: detecta SO, escanea puertos en paralelo y muestra resultados
def main():
    args = parse_args()
    config.TIMEOUT     = args.timeout
    config.MAX_THREADS = args.threads

    mostrar_cabecera()

    try:
        puertos = parsear_puertos(args.puertos)
    except ValueError as e:
        mostrar_error(f'Rango de puertos inválido: {e}')
        sys.exit(1)

    hosts = parsear_hosts(args.objetivo)

    for host in hosts:
        console.rule(f'[bold cyan]{host}[/bold cyan]')

        ip = resolver_hostname(host)
        if ip is None:
            mostrar_error(f'No se pudo resolver el host: {host}')
            continue

        os_detectado = '—'
        if not args.no_os:
            mostrar_info(f'Detectando SO de {host}...')
            os_detectado = detectar_os(host)

        mostrar_info_objetivo(host, ip, os_detectado, len(puertos))

        inicio = time.time()
        with crear_progreso() as progreso:
            tarea = progreso.add_task(f'Escaneando {host}...', total=len(puertos))
            puertos_abiertos = escanear_host(
                host, puertos,
                callback=lambda: progreso.advance(tarea)
            )
        tiempo = time.time() - inicio

        resultados = []
        for puerto in puertos_abiertos:
            servicio = obtener_servicio(puerto)
            banner   = obtener_banner(host, puerto) if not args.no_banner else ''
            resultados.append((puerto, servicio, banner))

        mostrar_resultados(host, resultados, tiempo)
        console.print()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        console.print('\n[bold yellow][!] Escaneo interrumpido por el usuario[/bold yellow]')
        sys.exit(0)
