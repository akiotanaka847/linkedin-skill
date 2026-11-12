# Changelog

## [1.1.0] - 2026-11-12

### Agrega
- Compatibilidad con Codex: manifiesto portable `plugins/linkedin/plugin.json` (esquema de Agent Plugins, con `extensions.com.openai`), marketplace del repo en `.agents/plugins/marketplace.json` y `agents/openai.yaml` en la skill. Probado con Codex CLI 0.167.2: `codex plugin marketplace add` y `codex plugin add linkedin@linkedin-skill` instalan el plugin, y la skill aparece en la lista que recibe el modelo.
- Modo `marca` para la página de empresa: voz sacada de la guía de marca y de posts anteriores, artículos convertidos en posts, series de eventos, aprobación por rol y variantes para los perfiles del equipo.
- Plantilla `marca.md` con Nunca nombrar, Frases prohibidas, Aviso obligatorio, tabla de aprobación y zona horaria.
- Reglas R19 (frase prohibida por la marca) y R20 (falta el aviso obligatorio) en `linkedin.py revisar`, activas cuando el borrador dice `destino: pagina`.
- `linkedin.py exportar`: CSV para la carga masiva de Hootsuite o JSON para otro agente. Todo o nada: valida aprobación, revisor, minutos en 0 o 5, 20 minutos de margen, horarios y textos únicos y el tope de 350.
- `implementation/integracion-con-agentes.md`: cómo usar el revisor y la exportación como herramientas de un agente en Python.

### Cambia
- `linkedin.py registrar` rechaza un post de página sin `aprobado_por` y `aprobado_el`, y anota el destino en el registro.
- En el SKILL.md, `homepage` y `repository` pasan a `metadata`, y se quita `user-invocable` (el valor por defecto ya es verdadero).

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
