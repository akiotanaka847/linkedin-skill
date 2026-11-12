# LinkedIn: lo que sabemos y de dónde sale

Solo entra aquí lo que tiene fuente. Lo que no la tiene se marca como regla de la
casa o se deja fuera. Revisado el 12 de noviembre de 2026.

## Lo que la plataforma prohíbe

Las condiciones de uso de LinkedIn (vigentes desde el 3 de noviembre de 2025)
prohíben dos cosas que definen cómo funciona esta skill:

- Usar "software, devices, scripts, robots" u otros medios para hacer scraping o
  copiar el servicio, perfiles incluidos.
- Usar "bots or other unauthorized automated methods" para crear, comentar,
  reaccionar o compartir publicaciones.

La página de ayuda "Automated activity on LinkedIn" agrega que no permiten
software ni extensiones de terceros que hagan scraping o automaticen actividad en
el sitio, y que hacerlo puede restringir la cuenta.

**Qué significa aquí:** la skill no lee LinkedIn con scrapers ni publica por ti.
Pegas el texto que quieres comentar, la skill redacta y tú publicas.

Fuentes: `https://www.linkedin.com/legal/user-agreement` (sección 8.2, "Don'ts") y
`https://www.linkedin.com/help/linkedin/answer/a1340567`.

## Programar un post

El editor de LinkedIn programa posts de forma nativa con el ícono del reloj, entre
10 minutos y 3 meses desde el momento actual. No se pueden programar eventos ni
vacantes. Las horas se convierten a UTC según la zona horaria del dispositivo.

Fuente: `https://www.linkedin.com/help/linkedin/answer/a1347212`.

## Métricas de cada post

LinkedIn muestra por post, y aclara que son estimaciones: impresiones, miembros
alcanzados, visitas al perfil desde el post, seguidores ganados, reacciones,
comentarios, compartidos (reposts), guardados y envíos por LinkedIn. Son los
campos que acepta `linkedin.py metricas`.

En esta skill, **interacción** es reacciones más comentarios más compartidos,
dividido entre impresiones. Los guardados se miran aparte: dicen si el post sirve
de consulta.

Fuente: `https://www.linkedin.com/help/linkedin/answer/a516971`.

## Límites de caracteres

| Campo | Límite | Fuente |
|---|---|---|
| Post | 3.000 | Lo hace cumplir el editor |
| Comentario | 1.250 | Guías de terceros |
| Titular del perfil | 220 | Guías de terceros |
| Acerca de | 2.600 | Guías de terceros |

No encontramos una página de ayuda oficial con los tres últimos. El editor avisa
si te pasas, así que el revisor los usa como referencia.

## "...ver más"

LinkedIn corta el post después de unas líneas. El punto exacto depende del
dispositivo y del ancho de pantalla, así que el revisor muestra los primeros 210
caracteres como aproximación. Lo que importa: la primera línea tiene que
sostenerse sola.

## Lo que esta skill no afirma

- **Horarios óptimos.** Los estudios que circulan miden el público de otras
  personas. El tuyo sale de tu registro cuando tengas datos.
- **Multiplicadores de alcance** ("los posts con número en la primera línea tienen
  34% más reacciones"). Casi todos vienen de proveedores con datos que no se
  pueden revisar.
- **Castigo a los enlaces.** No hay fuente oficial. Mandarlos al primer comentario
  es una regla de la casa, no un dato del algoritmo.

Cuando tengas diez posts medidos o más, `linkedin.py resumen` te dice qué te
funciona a ti. Con menos de cinco posts por grupo no se saca ninguna conclusión.
