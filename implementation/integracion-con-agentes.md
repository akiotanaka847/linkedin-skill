# Usar /linkedin dentro de otro agente

Para un equipo que ya tiene su propio agente de marketing (en Python, con LangGraph
u otro framework) y quiere usar el revisor y la exportación como herramientas
deterministas, sin la conversación de la skill.

## Qué se puede usar

| Pieza | Para qué | Cómo |
|---|---|---|
| `linkedin.py revisar --json` | Revisar un borrador antes de la aprobación humana | Proceso aparte o `import` |
| `linkedin.py huella <borrador>` | Atar la aprobación al texto y a la imagen exactos | Proceso aparte o `import` |
| `linkedin.py exportar --formato json` | Entregar lo aprobado a la herramienta que programa | Proceso aparte |
| `muletillas.json` | Ajustar la lista de frases por equipo | Editar el archivo |
| `plantillas/marca.md` | Reglas de la página: nunca nombrar, frases prohibidas, aviso obligatorio, imágenes | Un archivo por página |

El registro (`registrar`, `metricas`, `resumen`) escribe un CSV y no está pensado
para varios usuarios a la vez. En un servicio, guarda lo publicado en la base de
datos del agente y usa solo `revisar` y `exportar`.

## Dónde va en el flujo

1. **Redactar** (modelo): el agente arma el borrador con las reglas de
   `referencias/voz.md` en su prompt. Si el post lleva imagen, la elige de una
   biblioteca o la genera con su propio modelo de imágenes siguiendo
   `modos/imagen.md`, y la describe en `## Imagen`.
2. **Revisar** (determinista): `revisar`. Si hay errores, el informe vuelve al paso
   1. Tres vueltas como mucho; después pasa a una persona con el informe.
3. **Pausa de aprobación** (persona): quien aprueba ve el texto, la imagen y el
   informe del revisor, incluidas las cifras que hay que trazar. En LangGraph es el
   nodo que llama a `interrupt()`. Al aprobar, el agente guarda la salida de
   `huella` en `huella_aprobada`.
4. **Programar** (determinista): con la aprobación registrada en el borrador,
   `exportar` entrega el JSON a la herramienta que llama a Hootsuite, o el CSV
   para la carga masiva.

## Contrato de `revisar`

Entrada: el texto por la entrada estándar (o un archivo), más `--tipo`
(`post`, `comentario`, `titular`, `acerca`) y `--destino` (`perfil` o `pagina`).
Con `--destino pagina`, el revisor lee `marca.md` de la carpeta de datos.

Salida con `--json`:

```json
{
  "tipo": "post",
  "idioma": "es",
  "destino": "pagina",
  "caracteres": 812,
  "palabras": 131,
  "antes_de_ver_mas": "Primeros 210 caracteres...",
  "hallazgos": [
    {"codigo": "R19", "nivel": "error", "mensaje": "...", "linea": 4, "fragmento": "..."}
  ],
  "cifras": [{"cifra": "32 minutos", "linea": 1}],
  "imagen": {
    "muestra": "Gráfico con la caída del cierre contable",
    "origen": "plantilla",
    "archivo": "imagenes/cierre.png",
    "alt": "Gráfico de barras: el cierre bajó de 14 a 9 días.",
    "texto": "De 14 a 9 días",
    "derechos": "Plantilla de la marca",
    "prompt": ""
  },
  "errores": 1,
  "avisos": 0
}
```

`imagen` es `null` si el borrador no trae `## Imagen`. Los hallazgos de la imagen
(R21 a R25 y los del texto que va sobre ella) llegan en `hallazgos` con `linea` en
`null`. Las rutas relativas del archivo se leen desde la carpeta del borrador; con
la entrada estándar, desde la carpeta actual, así que en un servicio conviene usar
rutas absolutas.

Código de salida: 0 si pasa, 1 si hay errores, 2 si los argumentos están mal.

## Contrato de `huella`

`linkedin.py huella <borrador>` imprime un SHA-256 en hexadecimal del texto del
post, del contenido del archivo de la imagen (o de su dirección, si es web), del
texto alternativo y del texto de la imagen. Si el borrador trae `huella_aprobada` y
no coincide, sale con código 1. `exportar` y `registrar` hacen la misma
comparación, y `exportar` rechaza un post de página con imagen que no tenga
`huella_aprobada`.

Con una imagen en una dirección web, la huella cubre la dirección y no el
contenido: la herramienta que publica tiene que descargar el archivo y comprobarlo,
o la imagen se guarda en una ruta local antes de aprobar.

Ejemplo de herramienta:

```python
import json
import os
import subprocess
import sys

LINKEDIN_PY = "/ruta/a/plugins/linkedin/skills/linkedin/linkedin.py"
DATOS = "/ruta/a/la/carpeta/de/la/pagina"  # contiene marca.md


def revisar_borrador(texto: str, destino: str = "pagina") -> dict:
    r = subprocess.run(
        [sys.executable, LINKEDIN_PY, "revisar", "-", "--json", "--destino", destino],
        input=texto, capture_output=True, text=True,
        env={**os.environ, "LINKEDIN_SKILL_DIR": DATOS, "PYTHONUTF8": "1"},
    )
    if r.returncode not in (0, 1):
        raise RuntimeError(r.stderr)
    return json.loads(r.stdout)
```

## Contrato de `exportar --formato json`

Una lista, una entrada por post de página aprobado:

```json
[
  {
    "archivo": "2026-12-01-evento.md",
    "programado_para": "2026-12-03T09:30",
    "zona_horaria": "America/Bogota",
    "texto": "Texto del post.",
    "enlace": "https://ejemplo.com/registro",
    "pilar": "Eventos",
    "formato": "F10 La convocatoria",
    "tipo_pieza": "evento",
    "aprobado_por": "Equipo de eventos",
    "aprobado_el": "2026-12-01",
    "lleva_imagen": true,
    "imagen": {
      "origen": "biblioteca",
      "archivo": "/ruta/absoluta/a/la/foto.png",
      "sha256": "SHA-256 del archivo, o null si es una dirección web",
      "alt": "Texto alternativo",
      "texto": "",
      "derechos": "Foto propia del evento, con permiso de quienes salen",
      "prompt": "",
      "muestra": "La sala del taller"
    },
    "huella": "SHA-256 del texto y la imagen, igual a huella_aprobada"
  }
]
```

`programado_para` va sin zona: la zona es la de `marca.md`. `imagen` es `null` si
el post no lleva. Antes de subir la imagen al Images API de LinkedIn o a Hootsuite,
la herramienta que publica comprueba que el `sha256` del archivo sigue siendo el
mismo. Si alguna pieza no cumple (sin aprobación, horario repetido, texto repetido,
minutos que no terminan en 0 o 5, menos de 20 minutos de margen, no pasa el
revisor, huella que no coincide, imagen sin archivo o sin `huella_aprobada`), el
comando sale con código 1 y no escribe nada.

## Lo que la skill no hace en un agente

No llama a la API de LinkedIn ni a la de Hootsuite, y no genera imágenes. Publicar en una página de
empresa por API exige credenciales y permisos que son de la organización; esa
herramienta la escribe el equipo del agente y recibe el JSON de arriba.
