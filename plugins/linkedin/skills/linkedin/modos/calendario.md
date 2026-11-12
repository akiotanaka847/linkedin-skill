# Modo calendario

Arma las próximas semanas de publicación. Cada fecha apunta a una historia del
banco; una fecha sin historia no entra.

## Entradas

- Cuántas semanas (cuatro por defecto).
- La cadencia y los pilares con su peso, del perfil.
- El banco de historias.
- El registro, si ya hay posts medidos.

## Pasos

1. `LI estado`. Si hay diez posts medidos o más, `LI resumen` también.
2. Cuenta los espacios: semanas por posts por semana.
3. Reparte los espacios entre pilares según el peso. Redondea a favor del pilar
   con más historias disponibles.
4. A cada espacio, una historia publicable que no se haya usado en los últimos 60
   días (campo "Usada en").
5. A cada historia, el formato que le corresponde según `referencias/formatos.md`.
   El mismo formato no va dos veces seguidas.
6. Idioma de cada post según el perfil.
7. Revisa festivos y fechas del equipo con la persona antes de fijar días.
8. Escribe la tabla en `<DATOS>/calendario.md`, cambia el estado a `en uso` y pon
   la fecha.

## Cuando el banco no alcanza

Si faltan historias para un pilar, ese espacio se llena con "Sesión de entrevista:
<pilar>" y no con un tema genérico. Un calendario con temas sin caso produce
posts sin caso.

## Si ya hay datos

Con cinco posts medidos o más en un grupo (pilar, formato o idioma), el resumen
puede mover pesos. Muévelos de a poco: diez puntos por mes como mucho, y deja
siempre un espacio al mes para un formato que nunca has probado. Con menos de
cinco posts en el grupo, los pesos del perfil mandan.

## Revisión semanal

Una vez por semana: actualiza los estados (idea, borrador, aprobado, programado,
publicado, medido), mueve lo que no salió y marca qué posts ya cumplen siete días
para medir.

## Comentarios

El calendario puede incluir una meta de comentarios en posts ajenos por semana,
tomada del perfil. No asigna a quién comentar: eso sale del día a día.
