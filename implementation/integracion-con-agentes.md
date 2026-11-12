# Usar /linkedin dentro de otro agente

Para un equipo que ya tiene su propio agente de marketing (en Python, con LangGraph
u otro framework) y quiere usar el revisor y la exportación como herramientas
deterministas, sin la conversación de la skill.

## Qué se puede usar

| Pieza | Para qué | Cómo |
|---|---|---|
| `linkedin.py revisar --json` | Revisar un borrador antes de la aprobación humana | Proceso aparte o `import` |
| `linkedin.py exportar --formato json` | Entregar lo aprobado a la herramienta que programa | Proceso aparte |
| `muletillas.json` | Ajustar la lista de frases por equipo | Editar el archivo |
| `plantillas/marca.md` | Reglas de la página: nunca nombrar, frases prohibidas, aviso obligatorio | Un archivo por página |

El registro (`registrar`, `metricas`, `resumen`) escribe un CSV y no está pensado
para varios usuarios a la vez. En un servicio, guarda lo publicado en la base de
datos del agente y usa solo `revisar` y `exportar`.

## Dónde va en el flujo

1. **Redactar** (modelo): el agente arma el borrador con las reglas de
   `referencias/voz.md` en su prompt.
2. **Revisar** (determinista): `revisar`. Si hay errores, el informe vuelve al paso
   1. Tres vueltas como mucho; después pasa a una persona con el informe.
3. **Pausa de aprobación** (persona): quien aprueba ve el texto y el informe del
   revisor, incluidas las cifras que hay que trazar. En LangGraph es el nodo que
   llama a `interrupt()`.
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
  "errores": 1,
  "avisos": 0
}
```

Código de salida: 0 si pasa, 1 si hay errores, 2 si los argumentos están mal.

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
    "lleva_imagen": false
  }
]
```

`programado_para` va sin zona: la zona es la de `marca.md`. Si alguna pieza no
cumple (sin aprobación, horario repetido, texto repetido, minutos que no terminan
en 0 o 5, menos de 20 minutos de margen, no pasa el revisor), el comando sale con
código 1 y no escribe nada.

## Lo que la skill no hace en un agente

No llama a la API de LinkedIn ni a la de Hootsuite. Publicar en una página de
empresa por API exige credenciales y permisos que son de la organización; esa
herramienta la escribe el equipo del agente y recibe el JSON de arriba.
