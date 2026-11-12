# Changelog

## [1.0.0] - 2026-11-12

Primera versión.

### Incluye
- `/linkedin` con nueve modos: entrevista, post, revisar, calendario, comentar, perfil, equipo, publicar y resultados.
- Banco de historias con cifra, fecha, fuente y si cada caso se puede publicar.
- Doce formatos de post, cada uno atado a un tipo de caso.
- `linkedin.py revisar`: 16 reglas (rayas, barras, muletillas en español e inglés, contrastes de póster, etiquetas, signos de apertura, nombres de la lista Nunca nombrar, límites de caracteres) y la lista de cifras para trazar. Sale con código 1 si hay errores.
- `linkedin.py registrar`, `metricas` y `resumen`: registro en CSV con los campos que muestra LinkedIn y medianas por pilar, formato e idioma.
- Carpeta de datos fuera del repo (`~/.config/linkedin-skill/` o `LINKEDIN_SKILL_DIR`).

### Notas
- La skill no publica ni lee LinkedIn por su cuenta: la sección 8.2 de las condiciones de uso prohíbe el scraping y los bots para publicar, comentar o reaccionar.
- Tests herméticos con `unittest`, sin red, en macOS, Linux y Windows.
