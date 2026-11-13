# Diseño de /linkedin

Decisiones de diseño, con las alternativas descartadas. Para usar la skill, el
[README](../README.md) basta.

## D1. Una skill con modos, no nueve skills

Una sola entrada, `/linkedin`, con un SKILL.md corto que enruta y un archivo por
modo. El agente carga solo el modo que necesita.

**Descartado:** una skill por tarea. Nueve descripciones compiten por activarse
con el mismo pedido ("escribe algo para LinkedIn"), y las reglas compartidas
terminan copiadas en nueve sitios.

## D2. La persona publica

La skill no publica, no comenta, no reacciona y no lee LinkedIn. La sección 8.2
de las condiciones de uso prohíbe el scraping y los "bots or other unauthorized
automated methods" para crear, comentar, reaccionar o compartir publicaciones.

**Descartado:** integrar un servicio de publicación o un lector de terceros. Suma
una dependencia de pago, una credencial y un riesgo para la cuenta a cambio de
ahorrar un copiar y pegar. Programar ya lo hace el editor de LinkedIn.

## D3. El banco de historias es la fuente de verdad

Ningún borrador usa una cifra que no esté en el banco o en el material de ese
post. El borrador guarda una tabla de trazabilidad aparte del texto.

**Por qué:** lo que hace que un post suene escrito por una persona es el detalle
que nadie inventaría. Sin banco, el agente rellena con generalidades o, peor, con
números verosímiles.

## D4. Un script revisa; el agente revisa lo que el script no ve

`linkedin.py revisar` es determinista: rayas, barras, muletillas, contrastes,
etiquetas, nombres prohibidos, límites, cifras. El modo revisar suma cuatro
revisiones de juicio: trazabilidad, inferencias, confidencialidad y "¿lo podría
haber escrito cualquiera?".

**Por qué:** un agente que se revisa a sí mismo a ojo deja pasar lo mismo que
escribió. Un script con código de salida se puede poner en un hook o en CI.

## D5. Sin cifras de alcance de terceros

La skill no repite horarios óptimos, multiplicadores ni castigos del algoritmo
que vienen de estudios de proveedores. Lo que sí afirma sobre LinkedIn tiene la
fuente en `referencias/linkedin.md`. Lo demás sale del registro de la persona, con
un mínimo de cinco posts por grupo.

## D6. Datos personales fuera del repo

Perfil, banco, borradores y registro viven en `~/.config/linkedin-skill/`. El
repo solo trae plantillas vacías, y un test comprueba que la plantilla del perfil
no trae nombres.

**Descartado:** guardarlos dentro del repo con `.gitignore`. Un solo
`git add -A` en un fork público y el banco de historias (clientes, cifras,
errores) queda publicado.

## D7. Lo que va entre comillas invertidas se ignora

Para poder citar `en resumen` en la documentación sin que el revisor la bloquee.
En LinkedIn las comillas invertidas no se ven, así que un post real no las usa.

## D8. La imagen se describe, se revisa y se aprueba; la skill no la dibuja

El borrador trae la imagen en `## Imagen`: origen, archivo, texto alternativo,
texto sobre la imagen, derechos y prompt. El revisor la valida (R21 a R25) y pasa
el texto de la imagen por las mismas reglas del post. La aprobación queda atada a
una huella SHA-256 del texto, del contenido del archivo, del texto alternativo y
del texto de la imagen; `exportar` y `registrar` la comparan.

**Por qué la huella:** la imagen vive en un archivo aparte que puede cambiar sin
que nadie toque el borrador, por ejemplo cuando alguien reemplaza la foto en la
biblioteca con el mismo nombre. Sin huella, se publicaría una imagen que nadie
aprobó.

**Descartado:** generar la imagen desde `linkedin.py` llamando a un modelo de
imágenes. Rompe dos reglas del script (solo biblioteca estándar y sin red), ata la
skill a un proveedor y a una credencial. Cada entorno resuelve la imagen con lo que
tiene: un agente en la nube llama a su propio modelo de imágenes con el prompt del
modo imagen, y en un asistente sin esa herramienta la persona genera el archivo y
lo pasa.

## Pendiente

- Lectura de las estadísticas exportadas desde LinkedIn, en vez de dictar los
  números uno por uno.
- Un modo para newsletters de LinkedIn (artículos largos).
