# Modo publicar

Lleva un borrador aprobado hasta LinkedIn y lo deja anotado en el registro. La
skill prepara todo; la persona publica.

## Por qué la persona publica

Las condiciones de uso de LinkedIn prohíben "bots or other unauthorized automated
methods" para crear, comentar, reaccionar o compartir publicaciones (sección 8.2).
Esta skill no publica, no programa por API y no maneja el navegador para publicar.
Ver `referencias/linkedin.md`.

## Paso 1: revisión limpia

`LI revisar <borrador>` con cero errores. Si el borrador cambió después de la
última revisión, se revisa otra vez.

## Paso 2: aprobación del texto exacto

Muestra el texto final en un bloque y pregunta si se publica así. La aprobación
vale para ese texto: si cambia una coma, se vuelve a mostrar. Una aprobación de
otro día o de otro borrador no cuenta.

## Paso 3: el paquete

Con la aprobación, entrega en este orden:

1. **El texto**, en un bloque para copiar.
2. **El primer comentario**, si hay, en otro bloque.
3. **La imagen**, si hay: qué muestra y el texto alternativo.
4. **Cuándo.** El día que fija el calendario. La hora sale del perfil o, con datos
   suficientes, del registro; la skill no recomienda "horarios óptimos" sin datos
   propios.
5. **Cómo programarlo**, si no sale ya: en el editor de LinkedIn, el ícono del
   reloj, entre 10 minutos y 3 meses desde ahora.

## Paso 4: después de publicar

Cuando la persona pegue la URL del post:

```bash
LI registrar <borrador> --url <url>
```

Luego:

- Cambia `estado: borrador` por `estado: publicado` en el borrador.
- Actualiza la fila del calendario a "publicado".
- Agrega la fecha en el campo "Usada en" de la historia del banco.
- Recuérdale a la persona que en siete días se miden las métricas
  (`modos/resultados.md`). Siempre a los siete días, para que los posts se
  puedan comparar.

## Posts de página

Si el borrador dice `destino: pagina`, la aprobación es la del equipo que indica
`marca.md` y la salida es Hootsuite: sigue `modos/marca.md` (aprobación por rol y
`LI exportar`). `LI registrar` rechaza un post de página sin `aprobado_por` y
`aprobado_el`.

## Si la persona se arrepiente

Antes de publicar, no pasa nada. Después, la persona edita o borra el post en
LinkedIn; en el registro se deja la fila y se anota en `## Notas` del borrador
qué pasó.
