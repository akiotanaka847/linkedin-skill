# Modo resultados

Anota las métricas de cada post y dice qué funciona con los datos de la propia
persona, no con estudios ajenos.

## Cuándo se mide

A los siete días de publicado, siempre. Si un post se mide a los dos días y otro a
los veinte, no se pueden comparar.

## Paso 1: qué falta

`LI resumen` lista los posts con siete días o más sin métricas.

## Paso 2: anotar

La persona abre las estadísticas del post en LinkedIn y dicta o pega los números.
LinkedIn advierte que son estimaciones.

| En LinkedIn | En el registro |
|---|---|
| Impressions | `--impresiones` |
| Members reached | `--alcance` |
| Reactions | `--reacciones` |
| Comments | `--comentarios` |
| Reposts | `--compartidos` |
| Saves | `--guardados` |
| Sends on LinkedIn | `--envios` |
| Profile viewers from this post | `--visitas-perfil` |
| Followers gained from this post | `--seguidores` |

```bash
LI metricas 12 --impresiones 2310 --reacciones 41 --comentarios 9 --compartidos 2 --guardados 6
```

Solo se anotan los números que la persona tiene a la vista. Un campo sin dato se
deja vacío, no en cero.

## Paso 3: leer el resumen

`LI resumen` agrupa por pilar, formato e idioma, con medianas de impresiones y de
interacción (reacciones más comentarios más compartidos, sobre impresiones).

Cómo se lee:

1. **Medianas, no promedios.** Un post que se disparó mueve el promedio de todo
   el grupo; la mediana no.
2. **Menos de cinco posts en un grupo: no se concluye nada.** El resumen lo marca.
3. **Se compara lo comparable.** Español con español, inglés con inglés.
4. **Los guardados aparte.** Un post con pocas reacciones y muchos guardados
   sirve de consulta; es un buen formato para F5 y F9.
5. **Sin causas inventadas.** "Este formato rinde más" se puede decir con datos;
   "rinde más porque el algoritmo premia X" no.

## Paso 4: llevarlo al calendario

Con un grupo de cinco posts o más que destaque, propón mover pesos en el
calendario (diez puntos por mes como mucho). Deja siempre un espacio al mes para
probar algo nuevo, o el resumen solo va a confirmar lo que ya haces.
