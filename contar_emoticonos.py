#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cuenta emoticonos en el chat exportado (_chat.txt) entre dos fechas.

Los emoticonos se cuentan ignorando el color (modificadores de tono de piel)
y los selectores de variación. Cada emoticono se traduce a una categoría:

    🍞 + 🍷   -> Misa (un pan y un vino, en cualquier orden y aunque haya espacios)
    🌹        -> Un misterio del Rosario
    🙏        -> Rezo
    🕯️        -> Media hora de adoración
    📖        -> Una hora de estudio
    💪        -> Una hora de trabajo
    🥇 / 🏅   -> Una hora de esfuerzo
    🚫        -> Abstinencia
    🏃        -> Una hora de deporte
    👼        -> Rezar Angelus
    ☀️        -> Ofrecimiento del día (cualquier sol)
    🌙        -> Ofrecimiento de la noche (cualquier luna)

Uso:
    python3 contar_emoticonos.py DESDE HASTA [--archivo _chat.txt]

Las fechas se indican como D/M/AA o D/M/AAAA (p.ej. 15/8/25 o 15/08/2025).
Ambas fechas son inclusivas. Si se omiten, se cuenta todo el archivo.

Ejemplos:
    python3 contar_emoticonos.py 15/8/25 30/8/25
    python3 contar_emoticonos.py 1/9/2025 11/9/2025 --archivo _chat.txt
"""

import argparse
import re
import sys
import unicodedata
from datetime import date

# --- Caracteres a ignorar para "contar como si fuesen todos del mismo color" ---
# Modificadores de tono de piel (Fitzpatrick) U+1F3FB..U+1F3FF
TONOS_PIEL = "".join(chr(c) for c in range(0x1F3FB, 0x1F3FF + 1))
# Selector de variación (VS16 = emoji, VS15 = texto) y Zero Width Joiner
VARIACION = "\uFE0F\uFE0E"
ZWJ = "\u200D"
# Símbolos direccionales que aparecen en secuencias como 🏃‍♀️‍➡️
EXTRA_SIGNOS = "\u2642\u2640\u27A1"  # ♂ ♀ ➡

CARACTERES_IGNORADOS = set(TONOS_PIEL + VARIACION + ZWJ + EXTRA_SIGNOS)


def limpiar(texto: str) -> str:
    """Quita modificadores de tono, selectores de variación, ZWJ y signos de genero/direccion."""
    return "".join(ch for ch in texto if ch not in CARACTERES_IGNORADOS)


# --- Definición de categorías ---
# La Misa son un pan (🍞) y un vino (🍷). Se emparejan dentro de cada mensaje
# sin importar el orden ni los espacios: nº de misas = min(nº panes, nº vinos).
PAN = "🍞"
VINO = "🍷"
MISA = "Misa"

EMOJIS_SIMPLES = {
    "🌹": "Un misterio del Rosario",
    "🙏": "Rezo",
    "🕯": "Media hora de adoración",
    "📖": "Una hora de estudio",
    "💪": "Una hora de trabajo",
    "🥇": "Una hora de esfuerzo",
    "🏅": "Una hora de esfuerzo",
    "🚫": "Abstinencia",
    "🏃": "Una hora de deporte",
    "👼": "Rezar Angelus",
    # El ofrecimiento (sol = día, luna = noche) se detecta aparte,
    # en la función categoria_ofrecimiento, por nombre Unicode.
}

OFRECIMIENTO_DEL_DIA = "Ofrecimiento del día"
OFRECIMIENTO_DE_LA_NOCHE = "Ofrecimiento de la noche"


def categoria_ofrecimiento(ch: str):
    """Devuelve la categoría de ofrecimiento según el carácter, o None.

    - Cualquier sol (☀, 🌞, 🌝, ...) -> Ofrecimiento del día
    - Cualquier luna (🌙, 🌜, 🌛, fases, ...) -> Ofrecimiento de la noche

    Se detecta por el nombre Unicode y se excluye el girasol ('SUNFLOWER').
    """
    try:
        nombre = unicodedata.name(ch)
    except ValueError:
        return None
    if "SUNFLOWER" in nombre:
        return None
    if "SUN" in nombre:
        return OFRECIMIENTO_DEL_DIA
    if "MOON" in nombre:
        return OFRECIMIENTO_DE_LA_NOCHE
    return None

# Orden de presentación de los resultados
ORDEN_CATEGORIAS = [
    "Misa",
    "Un misterio del Rosario",
    "Rezo",
    "Media hora de adoración",
    "Una hora de estudio",
    "Una hora de trabajo",
    "Una hora de esfuerzo",
    "Abstinencia",
    "Una hora de deporte",
    "Rezar Angelus",
    "Ofrecimiento del día",
    "Ofrecimiento de la noche",
]

# Regex para la cabecera de cada mensaje: [D/M/AA, HH:MM:SS]
RE_CABECERA = re.compile(r"^\[(\d{1,2})/(\d{1,2})/(\d{2,4}),\s*\d{1,2}:\d{2}(?::\d{2})?\]")


def parsear_fecha_cabecera(linea: str):
    """Devuelve un objeto date si la linea empieza con una cabecera de mensaje, o None."""
    m = RE_CABECERA.match(linea)
    if not m:
        return None
    dia, mes, anio = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if anio < 100:
        anio += 2000
    try:
        return date(anio, mes, dia)
    except ValueError:
        return None


def parsear_fecha_usuario(texto: str) -> date:
    """Convierte D/M/AA o D/M/AAAA a date."""
    partes = texto.strip().split("/")
    if len(partes) != 3:
        raise ValueError(f"Fecha no valida: '{texto}'. Usa el formato D/M/AA (p.ej. 15/8/25).")
    dia, mes, anio = (int(p) for p in partes)
    if anio < 100:
        anio += 2000
    return date(anio, mes, dia)


def contar_en_texto(texto: str, conteo: dict):
    """Cuenta emoticonos de UN mensaje (ya limpio de modificadores) y acumula en conteo.

    La Misa se cuenta emparejando panes y vinos del mensaje, sin importar el orden
    ni los espacios: nº de misas = min(nº de 🍞, nº de 🍷). Los panes y vinos
    sobrantes (sin pareja) no se cuentan como ninguna categoría.
    """
    # Misa: emparejar panes y vinos del mensaje
    misas = min(texto.count(PAN), texto.count(VINO))
    if misas:
        conteo[MISA] = conteo.get(MISA, 0) + misas

    # Resto de emojis: uno por uno
    for ch in texto:
        if ch == PAN or ch == VINO:
            continue  # ya contados como misas (o sobrantes que se ignoran)
        categoria = EMOJIS_SIMPLES.get(ch)
        if categoria:
            conteo[categoria] = conteo.get(categoria, 0) + 1
        else:
            # Cualquier sol -> ofrecimiento del día; cualquier luna -> de la noche
            ofrecimiento = categoria_ofrecimiento(ch)
            if ofrecimiento:
                conteo[ofrecimiento] = conteo.get(ofrecimiento, 0) + 1


def procesar_archivo(ruta: str, desde: date, hasta: date):
    conteo = {}
    # Acumulamos cada mensaje completo (cabecera + líneas de continuación) para
    # que la Misa se empareje pan/vino dentro del mismo mensaje.
    buffer_mensaje = []
    dentro_de_rango = False

    def volcar():
        if buffer_mensaje and dentro_de_rango:
            texto = "".join(buffer_mensaje)
            contar_en_texto(limpiar(texto), conteo)

    with open(ruta, "r", encoding="utf-8") as f:
        for linea_cruda in f:
            fecha = parsear_fecha_cabecera(linea_cruda)
            if fecha is not None:
                # Nueva cabecera: cerramos el mensaje anterior y empezamos uno nuevo
                volcar()
                dentro_de_rango = (desde is None or fecha >= desde) and (
                    hasta is None or fecha <= hasta
                )
                # Quitamos la cabecera para no contar emojis del nombre/fecha
                buffer_mensaje = [RE_CABECERA.sub("", linea_cruda, count=1)]
            else:
                # Línea de continuación: pertenece al mensaje anterior
                buffer_mensaje.append(linea_cruda)

        # Último mensaje del archivo
        volcar()

    return conteo


def main():
    parser = argparse.ArgumentParser(
        description="Cuenta emoticonos del chat entre dos fechas (ambas inclusive).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Ejemplo: python3 contar_emoticonos.py 15/8/25 30/8/25",
    )
    parser.add_argument("desde", nargs="?", help="Fecha inicial D/M/AA (inclusive). Si se omite, desde el principio.")
    parser.add_argument("hasta", nargs="?", help="Fecha final D/M/AA (inclusive). Si se omite, hasta el final.")
    parser.add_argument("--archivo", default="_chat.txt", help="Ruta del archivo de chat (por defecto _chat.txt).")
    args = parser.parse_args()

    try:
        desde = parsear_fecha_usuario(args.desde) if args.desde else None
        hasta = parsear_fecha_usuario(args.hasta) if args.hasta else None
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if desde and hasta and desde > hasta:
        print("Error: la fecha 'desde' es posterior a la fecha 'hasta'.", file=sys.stderr)
        sys.exit(1)

    try:
        conteo = procesar_archivo(args.archivo, desde, hasta)
    except FileNotFoundError:
        print(f"Error: no se encuentra el archivo '{args.archivo}'.", file=sys.stderr)
        sys.exit(1)

    # --- Salida ---
    etiqueta_desde = f"{desde.day}/{desde.month}/{desde.year}" if desde else "inicio"
    etiqueta_hasta = f"{hasta.day}/{hasta.month}/{hasta.year}" if hasta else "fin"
    print(f"Conteo de emoticonos desde {etiqueta_desde} hasta {etiqueta_hasta}")
    print("=" * 50)

    total = 0
    for categoria in ORDEN_CATEGORIAS:
        cantidad = conteo.get(categoria, 0)
        total += cantidad
        print(f"{categoria:.<40} {cantidad}")

    print("=" * 50)
    print(f"{'TOTAL':.<40} {total}")


if __name__ == "__main__":
    main()
