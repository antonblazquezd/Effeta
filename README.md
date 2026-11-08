# Contador de emoticonos del chat

Script en Python que cuenta los emoticonos de un chat exportado de WhatsApp
(`_chat.txt`) entre dos fechas y los agrupa por categorías de ofrecimiento.

## Qué hace

Lee el archivo del chat, recorre los mensajes comprendidos entre una fecha
inicial y una fecha final (ambas incluidas) y cuenta cuántos emoticonos de cada
tipo se han enviado, traduciéndolos a su significado.

### Categorías

| Emoticono | Significado |
|-----------|-------------|
| 🍞 + 🍷 | Misa (un pan y un vino) |
| 🌹 | Un misterio del Rosario |
| 🙏 | Rezo |
| 🕯️ | Media hora de adoración |
| 📖 | Una hora de estudio |
| 💪 | Una hora de trabajo |
| 🥇 / 🏅 | Una hora de esfuerzo |
| 🚫 | Abstinencia |
| 🏃 | Una hora de deporte |
| 👼 | Rezar el Ángelus |
| ☀️ (cualquier sol) | Ofrecimiento del día |
| 🌙 (cualquier luna) | Ofrecimiento de la noche |

## Cómo se usa

El script se ejecuta desde la terminal con Python 3:

```bash
# Contar entre dos fechas (ambas incluidas)
python3 contar_emoticonos.py 15/8/25 30/8/25

# Contar todo el archivo (sin indicar fechas)
python3 contar_emoticonos.py

# Usar otro archivo de chat
python3 contar_emoticonos.py 1/9/25 11/9/25 --archivo otro_chat.txt
```

### Argumentos

- `desde` *(opcional)*: fecha inicial en formato `D/M/AA` o `D/M/AAAA`
  (por ejemplo `15/8/25` o `15/08/2025`). Si se omite, cuenta desde el principio.
- `hasta` *(opcional)*: fecha final, mismo formato. Si se omite, cuenta hasta el final.
- `--archivo` *(opcional)*: ruta del archivo de chat. Por defecto `_chat.txt`.

Ambas fechas son **inclusivas**: `15/8/25 30/8/25` incluye tanto el día 15 como el 30.

### Ejemplo de salida

```
Conteo de emoticonos desde 15/8/2025 hasta 30/8/2025
==================================================
Misa.................................... 69
Un misterio del Rosario................. 62
Rezo.................................... 13
Media hora de adoración................. 3
Una hora de estudio..................... 0
Una hora de trabajo..................... 5
Una hora de esfuerzo.................... 1
Abstinencia............................. 0
Una hora de deporte..................... 33
Rezar Angelus........................... 32
Ofrecimiento del día.................... 1
Ofrecimiento de la noche................ 0
==================================================
TOTAL................................... 219
```

## Cómo funciona por dentro

### 1. Lectura por mensajes

El archivo exportado tiene una línea por mensaje con el formato:

```
[15/8/25, 11:46:32] Nombre: 🍞🍷
```

El script detecta la cabecera `[fecha, hora]` con una expresión regular y extrae
la fecha de cada mensaje. La hora se ignora: solo se usan día, mes y año.

Un mensaje puede ocupar **varias líneas** (mensajes multilínea). Las líneas que
no empiezan por una cabecera `[fecha, hora]` se consideran continuación del
mensaje anterior y heredan su fecha, de modo que no se pierde ningún emoticono.

Para evitar contar emojis que pudiera haber en el nombre de la persona, la
cabecera se elimina antes de contar.

### 2. Normalización ("todos del mismo color")

Antes de contar, cada mensaje se limpia de los caracteres que solo cambian la
apariencia del emoji pero no su significado:

- **Modificadores de tono de piel** (🏻 🏼 🏽 🏾 🏿): así `🙏`, `🙏🏻` y `🙏🏽`
  cuentan como el mismo emoji.
- **Selectores de variación** (como el que hace que `🕯` se muestre a color).
- **Uniones ZWJ y signos de género/dirección** que aparecen en secuencias
  compuestas como `🏃‍♂️` o `🏃🏻‍♀️‍➡️`, de forma que todas las variantes de
  correr cuentan como deporte.

### 3. Conteo de emoticonos

- **Varios emojis en un mensaje**: cada emoji se cuenta por separado. Por
  ejemplo `🌹🌹🌹🌹🌹` cuenta como 5 misterios del Rosario.

- **Misa (pan + vino)**: dentro de cada mensaje se emparejan los panes (🍞) con
  los vinos (🍷). El número de misas es el mínimo entre la cantidad de panes y la
  de vinos, **sin importar el orden ni los espacios**. Ejemplos:
  - `🍞🍷` → 1 misa
  - `🍞 🍷 🍞 🍷` → 2 misas
  - `🍷 🍞` → 1 misa (orden invertido)
  - `🍞🍞🍷` → 1 misa (el pan sobrante se ignora)

  El emparejamiento es por mensaje: un pan de un mensaje no se empareja con un
  vino de otro mensaje distinto.

- **Ofrecimiento del día / de la noche**: no se usa una lista fija de emojis,
  sino que se reconoce **cualquier sol** (☀️ 🌞 🌝 ...) como ofrecimiento del día
  y **cualquier luna** (🌙 🌜 🌛 y las distintas fases) como ofrecimiento de la
  noche, identificándolos por su nombre Unicode. El girasol (🌻) se excluye
  aunque su nombre contenga "sun".

- **Esfuerzo**: se cuentan tanto la medalla de oro (🥇) como la medalla
  genérica (🏅).

### 4. Resultado

Al final imprime el conteo de cada categoría en un orden fijo y el total de
emoticonos contados en el rango de fechas indicado.

## Requisitos

- Python 3 (no necesita instalar ninguna librería externa).
- El archivo de chat exportado de WhatsApp en formato de texto (`_chat.txt`).
