"""Tests de la skill /linkedin. Solo biblioteca estándar, sin red."""

import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
SKILL = RAIZ / "plugins" / "linkedin" / "skills" / "linkedin"
SCRIPT = SKILL / "linkedin.py"

spec = importlib.util.spec_from_file_location("linkedin", SCRIPT)
li = importlib.util.module_from_spec(spec)
spec.loader.exec_module(li)

RAYA = "\u2014"
SEMIRRAYA = "\u2013"


def codigos(texto, tipo="post", nunca=(), nivel=None, idioma="auto"):
    inf = li.revisar(texto, tipo=tipo, idioma=idioma, nunca=nunca)
    return [h["codigo"] for h in inf["hallazgos"] if nivel is None or h["nivel"] == nivel]


class Rayas(unittest.TestCase):
    def test_raya_y_semirraya_son_error(self):
        self.assertIn("R01", codigos("Lo medí" + RAYA + "y salió mal.", nivel="error"))
        self.assertIn("R01", codigos("De 9" + SEMIRRAYA + "10 de la mañana.", nivel="error"))

    def test_guion_corto_pasa(self):
        self.assertNotIn("R01", codigos("Un flujo de punta a punta, end-to-end, en Fusion."))


class Barras(unittest.TestCase):
    def test_barra_entre_palabras_es_error(self):
        self.assertIn("R02", codigos("Escribe en ES/EN y/o portugués.", nivel="error"))

    def test_urls_numeros_y_rutas_largas_pasan(self):
        texto = ("Ver https://example.com/a/b y www.example.org/x. Atención 24/7. "
                 "El archivo src/fusion/blueprint.json y linkedin.com/in/alguien.")
        self.assertNotIn("R02", codigos(texto))


class Muletillas(unittest.TestCase):
    def test_muletilla_que_bloquea(self):
        self.assertIn("R03", codigos("En resumen, funcionó.", nivel="error"))
        self.assertIn("R03", codigos("Eso es clave para el equipo.", nivel="error"))
        self.assertIn("R03", codigos("We had to delve into it.", nivel="error"))

    def test_uso_literal_no_bloquea(self):
        self.assertNotIn("R03", codigos("Guardé la clave de API en el .env del proyecto."))

    def test_aviso_no_bloquea(self):
        inf = li.revisar("Es un paso fundamental del flujo.")
        self.assertEqual(inf["errores"], 0)
        self.assertIn("R03", [h["codigo"] for h in inf["hallazgos"] if h["nivel"] == "aviso"])

    def test_lista_valida(self):
        datos = json.loads((SKILL / "muletillas.json").read_text(encoding="utf-8"))
        for idioma in ("es", "en"):
            for item in datos[idioma]:
                self.assertIn(item["nivel"], ("error", "aviso"), item)
                re.compile(item["patron"])


class Contrastes(unittest.TestCase):
    def test_no_es_x_es_y(self):
        self.assertIn("R04", codigos("No es una herramienta, es un método.", nivel="error"))
        self.assertIn("R04", codigos("No solo ahorra tiempo sino que evita errores.", nivel="error"))
        self.assertIn("R04", codigos("It's not a tool, it's a habit.", nivel="error"))
        self.assertIn("R04", codigos("This is not just automation but judgment.", nivel="error"))

    def test_contraste_de_gerundios(self):
        self.assertIn("R04", codigos("Lo encontré midiendo, no leyendo."))
        self.assertIn("R04", codigos("I found it by measuring, not reading."))
        self.assertNotIn("R04", codigos("Lo encontré midiendo las llamadas por segundo."))

    def test_es_decir_pasa(self):
        self.assertNotIn("R04", codigos("No es posible, es decir, no con este presupuesto."))


class Forma(unittest.TestCase):
    def test_primera_linea_pregunta(self):
        self.assertIn("R05", codigos("¿Sabías que Fusion libera cada semana?\n\nPues sí."))
        self.assertNotIn("R05", codigos("Fusion libera cada semana.\n\n¿Lo sabías?"))

    def test_hashtags_y_emojis(self):
        self.assertIn("R07", codigos("Texto.\n\n#uno #dos #tres #cuatro"))
        self.assertNotIn("R07", codigos("Texto en C# y en F#. #uno #dos"))
        self.assertIn("R08", codigos("\U0001F680 Uno\n✅ Dos\n\U0001F4A1 Tres"))

    def test_longitud(self):
        self.assertIn("R09", codigos("a " * 1501, nivel="error"))
        self.assertIn("R09", codigos("a" * 1251, tipo="comentario", nivel="error"))
        self.assertIn("R09", codigos("a" * 221, tipo="titular", nivel="error"))
        self.assertNotIn("R09", codigos("a" * 2900))

    def test_fragmentos_apilados(self):
        self.assertIn("R11", codigos("Lo medí.\nFalló.\nOtra vez.\nY otra.\nAl final entendí por qué pasaba eso."))

    def test_triadas(self):
        texto = "Fue rápido, barato y confiable. El equipo, el cliente y el proveedor quedaron bien."
        self.assertIn("R12", codigos(texto))
        self.assertNotIn("R12", codigos("Fue rápido, barato y confiable. Después medimos otra vez."))

    def test_etiquetas(self):
        self.assertIn("R13", codigos("Cambiamos el flujo.\n¿El resultado?\nMenos errores."))
        self.assertIn("R13", codigos("La lección: medir antes."))

    def test_signos_de_apertura(self):
        self.assertIn("R14", codigos("Medimos todo. Qué pasó? Nada.", idioma="es"))
        self.assertNotIn("R14", codigos("Medimos todo. ¿Qué pasó? Nada.", idioma="es"))
        self.assertNotIn("R14", codigos("We measured. What happened? Nothing.", idioma="en"))

    def test_exclamaciones_y_mayusculas(self):
        self.assertIn("R17", codigos("¡Listo! ¡Salió!"))
        self.assertIn("R18", codigos("ESTO CAMBIÓ MI FORMA DE TRABAJAR\n\nY lo cuento."))


class NuncaNombrar(unittest.TestCase):
    def test_lee_la_lista_del_perfil(self):
        with tempfile.TemporaryDirectory() as d:
            perfil = Path(d) / "perfil.md"
            perfil.write_text(
                "# Perfil\n\n## Nombres\n\n- Libre SA\n\n## Nunca nombrar\n\n"
                "- Acme Corp (cliente con NDA)\n- proyecto-orion\n- (placeholder)\n\n## Temas fuera\n\n- Salud\n",
                encoding="utf-8")
            self.assertEqual(li.leer_nunca_nombrar(perfil), ["Acme Corp", "proyecto-orion"])

    def test_bloquea_el_nombre_sin_importar_mayusculas(self):
        cods = codigos("Trabajamos con ACME CORP en el flujo.", nunca=["Acme Corp"], nivel="error")
        self.assertIn("R16", cods)
        self.assertNotIn("R16", codigos("Trabajamos con Acmeco en el flujo.", nunca=["Acme"]))

    def test_plantilla_no_trae_nombres(self):
        self.assertEqual(li.leer_nunca_nombrar(SKILL / "plantillas" / "perfil.md"), [])


class Otros(unittest.TestCase):
    def test_codigo_entre_comillas_invertidas_se_ignora(self):
        self.assertEqual(codigos("Evita `en resumen` y `y/o`.", tipo="doc"), [])
        # Un tramo partido en dos líneas del mismo párrafo, como en Markdown.
        self.assertEqual(codigos("Nada de `no es X, es Y`, `no se trata de X, se\n"
                                 "trata de Y`, `no solo X sino Y`.", tipo="doc"), [])
        self.assertEqual(codigos("```\nEn resumen, y/o.\n```\nTexto limpio.", tipo="doc"), [])

    def test_comando_con_barra_no_es_separador(self):
        self.assertNotIn("R02", codigos("Diseño de /linkedin y de /coliseo.", tipo="doc"))
        self.assertIn("R02", codigos("Diseño de cliente / proveedor.", tipo="doc"))
        self.assertNotIn("R02", codigos("Lee [el diseño](implementation/linkedin-diseno.md).", tipo="doc"))
        self.assertNotIn("R02", codigos("Está en referencias/linkedin.md.", tipo="doc"))

    def test_cifras_para_trazar(self):
        inf = li.revisar("Bajó de 1.068 a 10 veces por segundo, con 0,2% de CPU en 2026.")
        cifras = [c["cifra"] for c in inf["cifras"]]
        self.assertIn("1.068", cifras)
        self.assertIn("10 veces", cifras)
        self.assertIn("0,2%", cifras)
        self.assertIn("2026", cifras)

    def test_separar_borrador(self):
        meta, texto = li.separar_borrador(
            "---\nidioma: es\npilar: Oficio\n---\n\nPrimera línea.\n\nSegunda.\n\n"
            "## Primer comentario\n\nhttps://x.com\n\n## Trazabilidad\n\n| a | b |\n")
        self.assertEqual(meta, {"idioma": "es", "pilar": "Oficio"})
        self.assertEqual(texto.strip(), "Primera línea.\n\nSegunda.")

    def test_idioma(self):
        self.assertEqual(li.detectar_idioma("El flujo de aprobación se cayó por la noche."), "es")
        self.assertEqual(li.detectar_idioma("The approval flow broke at night and nobody saw it."), "en")


class CarpetaYRegistro(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.carpeta = Path(self.tmp.name) / "datos"

    def tearDown(self):
        self.tmp.cleanup()

    def test_iniciar_no_pisa(self):
        primero = dict(li.iniciar(self.carpeta))
        self.assertTrue(all(v == "creado" for v in primero.values()))
        (self.carpeta / "perfil.md").write_text("mío", encoding="utf-8")
        segundo = dict(li.iniciar(self.carpeta))
        self.assertTrue(all(v == "ya existía" for v in segundo.values()))
        self.assertEqual((self.carpeta / "perfil.md").read_text(encoding="utf-8"), "mío")

    def test_plantillas_vacias(self):
        li.iniciar(self.carpeta)
        for nombre in li.ARCHIVOS_PLANTILLA:
            self.assertTrue(li.plantilla_vacia(self.carpeta / nombre), nombre)
        self.assertEqual(li.contar_historias(self.carpeta / "banco-de-historias.md"), 0)

    def test_registrar_medir_resumir(self):
        li.iniciar(self.carpeta)
        borrador = self.carpeta / "borradores" / "2026-11-01-prueba.md"
        borrador.write_text("---\nidioma: es\npilar: Oficio\nformato: F1 La cifra rara\n---\n\n"
                            "Mi app llamaba a Python 1.068 veces por segundo.\n\n## Trazabilidad\n\n| x | y |\n",
                            encoding="utf-8")
        f1 = li.registrar(self.carpeta, borrador, url="https://www.linkedin.com/feed/update/1", fecha="2026-11-01")
        li.registrar(self.carpeta, borrador, url="https://www.linkedin.com/feed/update/2", fecha="2026-11-10")
        self.assertEqual(f1["id"], "1")
        self.assertEqual(f1["pilar"], "Oficio")
        self.assertEqual(f1["primera_linea"], "Mi app llamaba a Python 1.068 veces por segundo.")
        with self.assertRaises(SystemExit):
            li.registrar(self.carpeta, borrador, url="https://www.linkedin.com/feed/update/1")

        r = li.resumir(li.leer_registro(self.carpeta / "registro.csv"), hoy=date(2026, 11, 12))
        self.assertEqual([p["id"] for p in r["pendientes"]], ["1"])

        li.anotar_metricas(self.carpeta, "1", {"impresiones": 1000, "reacciones": 30, "comentarios": 8,
                                               "compartidos": 2, "guardados": None}, fecha="2026-11-08")
        filas = li.leer_registro(self.carpeta / "registro.csv")
        self.assertAlmostEqual(li.tasa_interaccion(filas[0]), 0.04)
        self.assertEqual(filas[0]["guardados"], "")
        r = li.resumir(filas, hoy=date(2026, 11, 12))
        self.assertEqual(r["medidos"], 1)
        self.assertEqual(r["pendientes"], [])
        self.assertFalse(r["por_pilar"][0]["muestra_suficiente"])
        with self.assertRaises(SystemExit):
            li.anotar_metricas(self.carpeta, "99", {"impresiones": 1})


class LineaDeComandos(unittest.TestCase):
    def correr(self, *args, entrada=None, env_extra=None):
        env = dict(os.environ, **(env_extra or {}))
        return subprocess.run([sys.executable, str(SCRIPT)] + list(args), input=entrada,
                              capture_output=True, text=True, env=env)

    def test_revisar_codigos_de_salida(self):
        with tempfile.TemporaryDirectory() as d:
            env = {"LINKEDIN_SKILL_DIR": d}
            mal = self.correr("revisar", "-", entrada="En resumen, salió bien.", env_extra=env)
            bien = self.correr("revisar", "-", entrada="Medimos 14 flujos y 3 fallaban de noche.", env_extra=env)
            self.assertEqual(mal.returncode, 1, mal.stdout + mal.stderr)
            self.assertEqual(bien.returncode, 0, bien.stdout + bien.stderr)
            self.assertIn("CIFRAS PARA TRAZAR", bien.stdout)

    def test_iniciar_y_estado(self):
        with tempfile.TemporaryDirectory() as d:
            env = {"LINKEDIN_SKILL_DIR": str(Path(d) / "x")}
            self.assertEqual(self.correr("iniciar", env_extra=env).returncode, 0)
            estado = self.correr("estado", env_extra=env)
            self.assertEqual(estado.returncode, 0)
            self.assertIn("0 historias", estado.stdout)


class Repositorio(unittest.TestCase):
    def archivos(self, *sufijos):
        for p in RAIZ.rglob("*"):
            if ".git" in p.parts or not p.is_file():
                continue
            if p.suffix in sufijos:
                yield p

    def test_sin_rayas_en_el_repo(self):
        for p in self.archivos(".md", ".json", ".py", ".yml"):
            texto = p.read_text(encoding="utf-8")
            self.assertNotIn(RAYA, texto, p)
            self.assertNotIn(SEMIRRAYA, texto, p)

    def test_documentos_pasan_el_revisor(self):
        for p in list(self.archivos(".md")):
            inf = li.revisar(p.read_text(encoding="utf-8"), tipo="doc")
            errores = [(h["linea"], h["codigo"], h["fragmento"]) for h in inf["hallazgos"] if h["nivel"] == "error"]
            self.assertEqual(errores, [], p)

    def test_manifiestos_y_versiones(self):
        plugin = json.loads((RAIZ / "plugins/linkedin/.claude-plugin/plugin.json").read_text(encoding="utf-8"))
        market = json.loads((RAIZ / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        version_skill = re.search(r'^version:\s*"([^"]+)"', skill, re.M).group(1)
        version_log = re.search(r"^## \[([^\]]+)\]", (RAIZ / "CHANGELOG.md").read_text(encoding="utf-8"), re.M).group(1)
        self.assertEqual(plugin["version"], version_skill)
        self.assertEqual(plugin["version"], version_log)
        self.assertEqual(market["plugins"][0]["source"], "./plugins/linkedin")
        self.assertEqual(market["plugins"][0]["name"], plugin["name"])

    def test_descripcion_de_la_skill(self):
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        cabecera = skill.split("---")[1]
        desc = re.search(r"description: >-\n((?:  .*\n)+)", cabecera).group(1)
        desc = " ".join(l.strip() for l in desc.splitlines())
        self.assertLessEqual(len(desc), 1024)
        self.assertIn("name: linkedin", cabecera)

    def test_modos_y_referencias_existen(self):
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        for ruta in re.findall(r"`((?:modos|referencias)/[\w-]+\.md)`", skill):
            self.assertTrue((SKILL / ruta).exists(), ruta)

    def test_datos_personales_fuera_del_repo(self):
        ignorados = (RAIZ / ".gitignore").read_text(encoding="utf-8")
        for patron in ("perfil.local.md", "registro.csv", "borradores/"):
            self.assertIn(patron, ignorados)


if __name__ == "__main__":
    unittest.main()
