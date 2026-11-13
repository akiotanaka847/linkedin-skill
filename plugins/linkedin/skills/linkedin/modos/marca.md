# Modo marca

Contenido a nombre de una organización: la página de empresa en LinkedIn y las
variantes que el equipo publica en sus perfiles. Sirve a un equipo de marketing
que redacta con un agente, revisa por roles y programa en Hootsuite.

## La diferencia con un post personal

| | Post personal | Post de página |
|---|---|---|
| Perfil | `perfil.md` | `marca.md` (más la lista Nunca nombrar de `perfil.md`) |
| Voz | La de la persona | La de la guía de marca |
| Aprobación | La persona | El equipo que indica `marca.md` |
| Salida | La persona copia y publica | Exportación a Hootsuite o a otro agente |
| En el borrador | `destino: perfil` | `destino: pagina` |

## Paso 0: el perfil de marca

1. `LI estado`. Si `marca.md` está vacío, se llena antes de redactar nada.
2. La voz sale de fuentes, no de intuición: pide la guía de marca, cinco a diez
   posts de la página que el equipo considere buenos y dos o tres artículos
   recientes. Léelos y propón la sección "Voz de marca" con citas cortas de esas
   fuentes. El equipo confirma.
3. Pregunta quién revisa cada tipo de pieza (tabla Aprobación), qué no se puede
   decir (Frases prohibidas), si hay un aviso legal que va siempre (Aviso
   obligatorio) y la zona horaria de la página.

## Tres piezas típicas

### Un artículo publicado se vuelve post de página

1. El material es el artículo. Saca de él el caso, la cifra o la conclusión que
   sostiene el post, con cita textual. Un post por artículo; nunca el resumen.
2. Formato según el caso (`referencias/formatos.md`), casi siempre F11 o F3.
3. El enlace al artículo va en `enlace:` del borrador. Hootsuite lo adjunta.
4. Si el equipo quiere amplificarlo, prepara el kit de `modos/equipo.md`: dos o
   tres ángulos para que cada persona escriba su variante con `destino: perfil`.

### Un evento se vuelve una serie

Datos de entrada, todos del registro del evento: nombre, fecha, hora con zona
horaria, modalidad, ciudad o enlace, cierre de inscripciones, ponentes (con su
permiso) y enlace de registro. Si falta un dato, se pregunta; no se completa.

| Pieza | Cuándo | Qué lleva |
|---|---|---|
| Anuncio | Al abrir la inscripción | Qué se va a aprender, quién habla, fecha y enlace |
| Recordatorio | Una semana antes | Un dato concreto de la agenda o de un ponente |
| Último llamado | El día anterior al cierre | Cupos o fecha de cierre, si se conocen |
| Resumen | Hasta tres días después | Un hallazgo del evento, con permiso de quien lo dijo |

Las fechas de la tabla son la regla de la casa; el calendario del equipo de
eventos manda.

### Un caso de la organización

Igual que `modos/post.md`, con dos diferencias: el caso tiene que estar aprobado
para uso público por quien sea dueño de la relación con el cliente, y la tabla
de trazabilidad nombra el documento de donde sale cada cifra.

## El borrador de página

```
---
destino: pagina
tipo_pieza: evento
idioma: en
pilar: Eventos
formato: F10 La convocatoria
revisa: Equipo de eventos
estado: borrador
programado_para: 2026-12-03 09:30
enlace: https://ejemplo.com/registro
---

Texto del post.

## Trazabilidad

| Dato | Fuente |
|---|---|
```

- `programado_para` va en la hora local de la página, con minutos terminados en 0
  o 5.
- `aprobado_por` y `aprobado_el` los escribe el agente solo cuando la persona dice
  quién aprobó y cuándo. Nunca se infieren.
- Al aprobarse: `estado: aprobado` y `huella_aprobada:` con lo que devuelve
  `LI huella <borrador>`. Un post con imagen no se exporta sin huella.
- La imagen, si hay, va en `## Imagen` (ver `modos/imagen.md`) y sigue las reglas
  de `## Imágenes` en `marca.md`.

## Revisión

`LI revisar <borrador>`. Con `destino: pagina`, además de las reglas de siempre,
el revisor bloquea las frases prohibidas de la marca (R19), exige el aviso
obligatorio (R20) y, si hay imagen, bloquea las generadas cuando la marca no las
permite (R24) y los archivos fuera de sus bibliotecas aprobadas (R25).

## Aprobación por rol

1. La tarjeta de aprobación (la de `modos/post.md`) va a quien indica la tabla
   Aprobación de `marca.md` para ese tipo de pieza.
2. La persona que usa la skill confirma quién aprobó y cuándo. El agente escribe
   `aprobado_por`, `aprobado_el`, `huella_aprobada` y `estado: aprobado`.
3. Si alguien cambia el texto o la imagen después de aprobado, vuelve a
   `estado: borrador` y se borra la aprobación. Si nadie lo hace, la huella deja de
   coincidir y `exportar` lo detiene.

## Programación

```bash
LI exportar --formato hootsuite --formato-fecha dmy
```

Junta todos los borradores de página aprobados y escribe un CSV para la carga
masiva de Hootsuite: columna A fecha y hora, B texto, C enlace. Antes de escribir
nada comprueba que cada pieza pase el revisor, tenga aprobación, caiga en minutos
terminados en 0 o 5, esté a 20 minutos o más de ahora, no comparta horario ni
texto con otra y que no pasen de 350. Si algo falla, no exporta nada.

Las imágenes no viajan en la carga masiva: se agregan en Hootsuite después, con el
archivo y el texto alternativo del borrador. Antes de la primera carga, compara el
archivo con la plantilla que descarga el Bulk Composer de Hootsuite (ver
`referencias/linkedin.md`). El JSON sí lleva la imagen: su archivo, su SHA-256 y su
texto alternativo.

Para otro agente o un servicio que llame a la API de Hootsuite:

```bash
LI exportar --formato json
```

El contrato del JSON está en `implementation/integracion-con-agentes.md` del
repositorio.

## Después de publicar

Igual que `modos/publicar.md`: `LI registrar <borrador> --url <url>` (exige la
aprobación en el borrador) y métricas a los siete días.
