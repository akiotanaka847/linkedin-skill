# linkedin-skill

**Skills para Claude Code, empezando por LinkedIn: `/linkedin`.**

`/linkedin` escribe, revisa y lleva la cuenta de lo que publicas en LinkedIn a
partir de casos reales: el número que te sorprendió, lo que se rompió, lo que
construiste. Guarda esos casos en un banco con su cifra y su fuente, y ningún
borrador usa un dato que no esté ahí. Un script revisa cada texto antes de que lo
veas y bloquea las muletillas, las rayas, las barras y los nombres de clientes que
no pueden salir.

**No publica por ti.** Redacta, te muestra la tarjeta de aprobación y te entrega el
paquete listo. Tú publicas, porque las condiciones de uso de LinkedIn prohíben los
bots para publicar, comentar o reaccionar.

## Instalación

```bash
/plugin marketplace add akiotanaka847/linkedin-skill
/plugin install linkedin@linkedin-skill
```

Como plugin, Claude Code la muestra con espacio de nombres: `/linkedin:linkedin`.
Si prefieres `/linkedin` a secas, copia la carpeta de la skill:

```bash
git clone https://github.com/akiotanaka847/linkedin-skill.git
cp -r linkedin-skill/plugins/linkedin/skills/linkedin ~/.claude/skills/
```

Requiere Python 3.9 o superior, sin dependencias.

## SKILLS

| Skill | Qué hace | Docs |
|---|---|---|
| [`/linkedin`](plugins/linkedin/skills/linkedin/SKILL.md) | Banco de historias, posts a partir de un caso, revisión, calendario, comentarios, perfil, equipo y métricas | [diseño](implementation/linkedin-diseno.md) |

## Modos

| Modo | Qué hace |
|---|---|
| `entrevista` | Te pregunta, o lee tus informes y notas, y llena el perfil y el banco de historias con cifra y fuente |
| `post` | Redacta un post a partir de un caso del banco, o de un webinar, una transcripción o un documento (un caso por post) |
| `revisar` | Corre el revisor y después lo que un script no ve: cifras sin fuente, inferencias, confidencialidad |
| `calendario` | Reparte las próximas semanas por pilares; cada fecha apunta a una historia del banco |
| `comentar` | Dos opciones de comentario para un post ajeno, o respuestas ordenadas para los comentarios en los tuyos |
| `perfil` | Titular, Acerca de, experiencia y destacados, respaldados por el banco |
| `equipo` | Kit para embajadores (sin textos para copiar), vacantes con nivel de inglés y rango, reconocimientos con permiso |
| `publicar` | Aprobación del texto exacto, paquete para pegar o programar en LinkedIn, registro |
| `resultados` | Métricas a los siete días y medianas por pilar, formato e idioma |

## Qué resuelve

1. **Posts que no suenan a plantilla.** Cada post sale de un caso con su detalle
   raro. Doce formatos (la cifra rara, lo que se rompió, el supuesto falso, la
   lectura comentada...) arrancan de un tipo de caso, no de un tema.
2. **Cero cifras inventadas.** El borrador trae una tabla de trazabilidad con la
   fuente de cada número. El revisor lista todas las cifras que encuentra para
   que ninguna se escape.
3. **Confidencialidad de agencia.** La lista Nunca nombrar del perfil bloquea el
   borrador. Clientes, nombres internos y lo dicho en reuniones quedan fuera.
4. **Un revisor que se puede leer.** `linkedin.py revisar` aplica 16 reglas con
   código, nivel y sugerencia. Las muletillas viven en
   [`muletillas.json`](plugins/linkedin/skills/linkedin/muletillas.json), en
   español e inglés, y las puedes cambiar.
5. **Tus datos, no los de otros.** La skill no repite horarios óptimos ni
   multiplicadores de alcance de estudios ajenos. Con diez posts medidos,
   `resumen` te dice qué te funciona a ti, y no concluye nada con menos de cinco
   posts por grupo.

## Uso rápido

```bash
/linkedin entrevista
```

```bash
/linkedin post sobre cómo bajamos los errores del flujo de aprobaciones
```

```bash
/linkedin post desde ~/Documents/webinar-transcripcion.md
```

```bash
/linkedin revisar este borrador: (pegas el texto)
```

```bash
/linkedin comentar (pegas el post)
```

## Dónde quedan tus datos

En `~/.config/linkedin-skill/`, fuera del repositorio:

```
perfil.md                Quién eres, a quién le escribes, pilares, Nunca nombrar
banco-de-historias.md    Tus casos con cifra, fecha, fuente y si son publicables
calendario.md            Las próximas semanas
borradores/              Un archivo por post, con su trazabilidad
registro.csv             Lo publicado y sus métricas
```

Para usar otra carpeta, define `LINKEDIN_SKILL_DIR`. La primera vez,
`/linkedin entrevista` la crea y la llena.

## El revisor por su cuenta

Funciona sin Claude Code, sobre cualquier texto:

```bash
python3 plugins/linkedin/skills/linkedin/linkedin.py revisar borrador.md
python3 plugins/linkedin/skills/linkedin/linkedin.py revisar - --tipo comentario < comentario.txt
```

Sale con código 1 si hay errores, así que sirve en un hook o en CI.

## Tests

```bash
python3 -m unittest discover -s tests -v
```

Incluye una prueba que pasa todos los documentos del repo por el revisor: este
README también.

## Licencia

MIT. Ver [LICENSE](LICENSE).
