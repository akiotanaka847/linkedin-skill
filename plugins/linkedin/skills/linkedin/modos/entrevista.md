# Modo entrevista

Llena `perfil.md` y `banco-de-historias.md` con datos que la persona pueda
defender. Es el primer modo para quien nunca ha usado la skill, y el que se usa
cuando el banco se queda corto.

## Dos maneras de llenar el banco

**Conversando.** Rondas de tres preguntas como mucho. Después de cada ronda,
escribe lo que salió y muestra las historias nuevas.

**Desde tus archivos.** La persona señala carpetas o documentos propios: informes,
notas de proyecto, README, registros de aprendizajes, presentaciones. Léelos y
propón historias, cada una con la cita textual que la sostiene y la ruta del
archivo. La persona confirma cada historia antes de que entre al banco. Es la
manera más rápida: casi todo el mundo ya escribió sus mejores casos en algún lado.

## Primera sesión

1. Corre `LI estado`. Si la carpeta no existe, `LI iniciar`.
2. Perfil, en este orden: rol y empresa, a quién le escribe y qué quiere que pase,
   idiomas, pilares con su peso, la lista Nunca nombrar. Esta última no se salta:
   pregunta por clientes con acuerdo de confidencialidad, nombres internos de
   sistemas y proyectos sin anunciar.
3. Cinco historias como mínimo, repartidas en por lo menos tres pilares.
4. Cambia `estado: vacío` por `estado: en uso` y pon la fecha en los dos archivos.

## Preguntas que sacan el detalle

- ¿Qué número de tu trabajo te sorprendió este año? ¿Cómo lo mediste?
- ¿Qué se rompió la última vez? ¿Cuánto costó y quién se dio cuenta primero?
- ¿Qué creías hace seis meses que ya no crees? ¿Qué te hizo cambiar?
- ¿Qué le explicas una y otra vez a gente de otra área?
- ¿Qué construiste que nadie te pidió? ¿Quién lo usa hoy?
- ¿En qué no estás de acuerdo con la mayoría de tu sector?
- ¿A quién del equipo le debes algo concreto este trimestre?

## Cuando la respuesta es vaga

"Mejoró bastante" o "nos ahorró mucho tiempo" no entra así. Pregunta una vez por
el número y por dónde se puede ver. Si no lo hay, la historia entra con
"Cifra: sin cifra" y "Fuente: de memoria". Nunca completes un número por tu
cuenta, ni redondeado ni "aproximado".

## Campos que no se dejan vacíos

- **Fuente.** Archivo, enlace, documento o "de memoria".
- **Publicable.** Sí, sin nombres o no. Si la historia toca a un cliente, la
  respuesta por defecto es "sin nombres" hasta que la persona diga otra cosa.

## Entrevista para un post

Cuando la persona tiene un tema pero no el material, cinco preguntas sobre ese
tema y nada más. Lo que salga se ordena en cinco líneas y pasa a `modos/post.md`:

1. **Momento:** cuándo y dónde pasó.
2. **Cifra:** el número que lo prueba.
3. **Giro:** qué cambió en lo que la persona pensaba o hacía.
4. **Quién piensa distinto:** y por qué.
5. **Cierre:** la pregunta que le harías al lector.

Una línea sin respuesta queda escrita como "sin respuesta"; el modo post no la
rellena.

## Lo que no hace este modo

No redacta posts. Entrega historias y un esqueleto; redactar es de `modos/post.md`.
