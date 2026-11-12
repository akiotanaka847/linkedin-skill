# Modo revisar

Revisa un borrador antes de publicarlo: el tuyo, el de alguien del equipo o uno
escrito con otra herramienta. Primero corre el script; después, las cuatro
revisiones que el script no puede hacer.

## Paso 1: el script

Si el borrador es un archivo:

```bash
LI revisar <archivo> --tipo post
```

Si la persona lo pegó en la conversación, pásalo por la entrada estándar:

```bash
LI revisar - --tipo post <<'FIN'
(texto pegado)
FIN
```

Tipos: `post`, `comentario`, `titular`, `acerca`, `doc`. El script lee la lista
Nunca nombrar del perfil; para otro perfil, `--perfil <ruta>`. Sale con código 1
si hay errores.

| Código | Qué busca | Nivel |
|---|---|---|
| R01 | Raya o semirraya | error |
| R02 | Barra como separador | error |
| R03 | Muletillas de `muletillas.json` | error o aviso |
| R04 | Contrastes de póster (`no es X, es Y`, `no solo... sino`) | error o aviso |
| R05 | Primera línea en pregunta | aviso |
| R06 | Enlace en el texto | nota |
| R07 | Más de tres hashtags | aviso |
| R08 | Más de dos emojis, o emojis como viñetas | aviso |
| R09 | Más caracteres que el límite de referencia | error |
| R11 | Tres o más frases muy cortas seguidas | aviso |
| R12 | Más de una enumeración de tres | aviso |
| R13 | Etiquetas y bisagras (`Spoiler:`, `¿El resultado?`) | aviso |
| R14 | Falta el ¿ o el ¡ de apertura | aviso |
| R16 | Un nombre de la lista Nunca nombrar | error |
| R17 | Más de una exclamación | aviso |
| R18 | Línea en mayúsculas | aviso |

El script también lista las cifras que encontró y lo que se ve antes de "ver
más". Lo que va entre comillas invertidas se ignora, para poder citar una
muletilla en un documento.

## Paso 2: lo que el script no ve

1. **Trazabilidad.** Cada cifra de la lista tiene su fuente en el banco o en el
   material. Si no la tiene, se quita o se pregunta.
2. **Inferencias.** ¿El borrador afirma algo que la fuente no dice? Lo típico:
   la fuente describe cómo funciona algo hoy y el borrador dice que "se rompió" o
   que "todos tienen que cambiar". Se marca como opinión o se quita.
3. **Confidencialidad.** Más allá de la lista: clientes reconocibles por el
   contexto, nombres internos de sistemas, capturas, cifras del negocio de otro,
   lo dicho en una reunión.
4. **¿Lo podría haber escrito cualquiera?** Frase por frase. Las que sí, se
   cambian por una que lleve un detalle del caso.

## Paso 3: el informe

Primero los errores, después los avisos, después las cuatro revisiones. Cada
cambio propuesto va como par: la frase de ahora y la propuesta. No reescribas el
post entero salvo que la persona lo pida; si lo pide, vuelve a correr el script
sobre la versión nueva.

## Revisar textos de otras personas

Si el borrador es de alguien del equipo, el informe se lo puedes reenviar tal
cual. Las reglas de voz son las de esta skill, pero la voz es de esa persona: no
cambies su forma de hablar, solo lo que el revisor marca.
