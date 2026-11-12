# Voz

Reglas de escritura para todo lo que sale de esta skill: posts, comentarios,
respuestas, perfil y textos para el equipo. El perfil de cada persona suma las
suyas; si algo choca, manda el perfil.

La idea de fondo: lo genérico delata y lo específico no. Un lector no puede
comprobar un adjetivo, pero sí puede comprobar "1.068 veces por segundo". Cada
regla de abajo sale de ahí.

## Contenido

1. **Un caso real por post.** Una sola historia, con su cifra, su fecha y su
   detalle raro. Si el material trae cinco casos, salen cinco posts, no un
   resumen de los cinco.
2. **El detalle raro manda.** El dato que nadie inventaría (el formulario de 17
   casillas, el lunes 13 de julio, los 15 frames de audio) vale más que tres
   adjetivos. Búscalo en el banco antes de escribir.
3. **Cada cifra tiene fuente.** Está en el banco de historias o en el material
   que la persona pasó para ese post. Sin fuente, se quita. Si la fuente dice
   "mil", el post no dice "miles": la cifra se copia tal cual.
4. **No se publica una consecuencia que la fuente no dice.** Si la documentación
   dice "ahora X funciona así", el post no dice "X se rompió". La inferencia se
   marca como tuya ("lo que yo haría es...") o se quita.
5. **Lo que pasó en una reunión con cliente no se cuenta.** Ni quién dijo qué, ni
   en qué minuto, ni el nombre del cliente. Se cuenta lo que aprendiste, con el
   cliente fuera.

## Forma

1. **La primera línea cuenta un hecho o da una cifra.** Ni pregunta, ni aforismo,
   ni anuncio de lo que viene. Las preguntas van al cierre.
2. **Sin raya ni semirraya** (los guiones largos de U+2014 y U+2013). En su lugar:
   coma, dos puntos, paréntesis o punto. El guion corto de las palabras
   compuestas sí se usa.
3. **Sin barras como separador.** Nada de `y/o`, `ES/EN`, `cliente/proveedor`.
   Se escribe "y", "o" o se usa una coma. Las rutas de archivo y las fechas con
   números quedan como están.
4. **Sin contrastes de póster.** Nada de `no es X, es Y`, `no se trata de X, se
   trata de Y`, `no solo X sino Y`, `menos X, más Y`. Se dice lo que es, con el
   dato.
5. **Una enumeración de tres por post, como mucho.** Las tríadas ordenadas
   ("rápido, barato y confiable") suenan a plantilla. Si son tres cosas reales,
   que cada una lleve su dato.
6. **Sin etiquetas ni bisagras.** Nada de `Spoiler:`, `La lección:`, `¿El
   resultado?`, `Aquí va`, `Plot twist`. Se pasa directo al contenido.
7. **Frases de largo variado, sin forzarlo.** Tres frases de dos palabras
   seguidas, una debajo de otra, suenan a eslogan. Se unen.
8. **Párrafos de una o dos frases con línea en blanco entre ellos.** Así se lee en
   el celular.
9. **Signos de apertura en español.** `¿` y `¡` siempre. Una exclamación por
   post, como mucho.
10. **Hashtags: cero a tres, al final.** Emojis: cero a dos, nunca como viñetas.
11. **Enlaces en el primer comentario** por defecto. Es una regla de la casa
    para que el post se lea completo; no hay una fuente oficial que diga que
    LinkedIn castiga los enlaces.

## Palabras

La lista completa, con sugerencias, vive en `muletillas.json` y la revisa
`linkedin.py revisar`. Las más comunes:

- **Bloquean el borrador:** `en resumen`, `cabe destacar`, `hoy más que nunca`,
  `en el mundo actual`, `sin lugar a dudas`, `esto lo cambia todo`, `al siguiente
  nivel`, `es clave`, `punto clave`, `sinergia`, `apalancar`, `orgulloso de
  anunciar`, `en constante evolución`, `game changer`, `delve`, `deep dive`,
  `thrilled to announce`.
- **Avisan:** `fundamental`, `crucial`, `ecosistema`, `robusto`, `potenciar`,
  `innovador`, `transformador`, `mi viaje profesional`, `leverage`, `landscape`.
  A veces el uso es literal (la `clave` de una API, `navegar` un sitio); entonces
  se deja y se dice por qué.

## Español e inglés

- El idioma de cada post lo decide el perfil y el lector, no la costumbre.
- En español: tú o usted según el perfil, español neutro de Latinoamérica
  ("archivo", "video", "computador", "celular").
- En inglés aplican las mismas reglas. La lista de muletillas en inglés está en
  el mismo archivo.
- No se traduce un post palabra por palabra. Se escribe de nuevo para el otro
  lector, con el mismo caso.

## Prueba final

Antes de mostrar un borrador:

1. Corre `linkedin.py revisar`. Cero errores.
2. Cada aviso se corrige o se justifica en una línea.
3. Cada cifra que lista el revisor tiene su fuente en la tabla de trazabilidad.
4. Léelo de corrido. Si una frase podría estar en el post de cualquier otra
   persona, cámbiala por una que solo tú puedes escribir.
