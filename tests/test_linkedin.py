"""Tests de la skill /linkedin. Solo biblioteca estándar, sin red."""

import csv
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from datetime import date, datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
SKILL = RAIZ / "plugins" / "linkedin" / "skills" / "linkedin"
SCRIPT = SKILL / "linkedin.py"

spec = importlib.util.spec_from_file_location("linkedin", SCRIPT)
li = importlib.util.module_from_spec(spec)
spec.loader.exec_module(li)

RAYA = "\u2014"
SEMIRRAYA = "\u2013"


def codigos(texto, tipo="post", nunca=(), nivel=None, idioma="auto", prohibidas=(), avisos_obligatorios=()):
    inf = li.revisar(texto, tipo=tipo, idioma=idioma, nunca=nunca,
                     prohibidas=prohibidas, avisos_obligatorios=avisos_obligatorios)
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
        en = [c["cifra"] for c in li.revisar("A 90 minutes workshop, 3 days later.")["cifras"]]
        self.assertEqual(en, ["90 minutes", "3 days"])

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


MARCA = """# Marca

estado: en uso

## Nunca nombrar

- Cliente Reservado (NDA)

## Frases prohibidas

- resultados garantizados
- (instrucción de la plantilla)

## Aviso obligatorio

- Contenido informativo, no constituye asesoría (versión corta).

## Programación

- Zona horaria: America/Bogota
"""

AVISO = "Contenido informativo, no constituye asesoría (versión corta)."


def borrador_pagina(texto, **meta):
    base = {"destino": "pagina", "idioma": "es", "pilar": "Eventos", "estado": "aprobado",
            "aprobado_por": "Equipo de eventos", "aprobado_el": "2026-11-12",
            "programado_para": "2026-11-20 09:30"}
    base.update({k: v for k, v in meta.items() if v is not None})
    for k in [k for k, v in meta.items() if v is None]:
        base.pop(k, None)
    cabecera = "\n".join("%s: %s" % kv for kv in base.items())
    return "---\n%s\n---\n\n%s\n\n%s\n\n## Trazabilidad\n\n| a | b |\n" % (cabecera, texto, AVISO)


class Marca(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.carpeta = Path(self.tmp.name)
        li.iniciar(self.carpeta)
        (self.carpeta / "marca.md").write_text(MARCA, encoding="utf-8")
        (self.carpeta / "perfil.md").write_text("## Nunca nombrar\n\n- Proyecto Interno\n", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_plantilla_de_marca_no_trae_reglas(self):
        plantilla = SKILL / "plantillas" / "marca.md"
        for seccion in ("Nunca nombrar", "Frases prohibidas", "Aviso obligatorio"):
            self.assertEqual(li.leer_lista(plantilla, seccion, cortar_nota=False), [], seccion)
        self.assertEqual(li.leer_campo(plantilla, "Zona horaria"), "")

    def test_reglas_segun_destino(self):
        nunca, prohibidas, avisos = li.reglas_de_destino(self.carpeta, "perfil")
        self.assertEqual((nunca, prohibidas, avisos), (["Proyecto Interno"], [], []))
        nunca, prohibidas, avisos = li.reglas_de_destino(self.carpeta, "pagina")
        self.assertEqual(nunca, ["Proyecto Interno", "Cliente Reservado"])
        self.assertEqual(prohibidas, ["resultados garantizados"])
        self.assertEqual(avisos, [AVISO])
        self.assertEqual(li.leer_campo(self.carpeta / "marca.md", "Zona horaria"), "America/Bogota")

    def test_frase_prohibida_y_aviso_obligatorio(self):
        texto = "Ofrecemos Resultados Garantizados en 14 semanas."
        cods = codigos(texto, prohibidas=["resultados garantizados"], avisos_obligatorios=[AVISO], nivel="error")
        self.assertIn("R19", cods)
        self.assertIn("R20", cods)
        bien = "Redujimos el cierre contable de 14 a 9 días.\n\n" + AVISO.replace(" ", "  ")
        self.assertEqual(codigos(bien, avisos_obligatorios=[AVISO], nivel="error"), [])

    def test_cli_usa_la_marca_cuando_el_borrador_es_de_pagina(self):
        b = self.carpeta / "borradores" / "pagina.md"
        b.write_text(borrador_pagina("Con Cliente Reservado logramos resultados garantizados."), encoding="utf-8")
        r = subprocess.run([sys.executable, str(SCRIPT), "revisar", str(b), "--json"], capture_output=True,
                           text=True, env=dict(os.environ, LINKEDIN_SKILL_DIR=str(self.carpeta), PYTHONUTF8="1"))
        inf = json.loads(r.stdout)
        self.assertEqual(r.returncode, 1)
        self.assertEqual(inf["destino"], "pagina")
        self.assertTrue({"R16", "R19"} <= {h["codigo"] for h in inf["hallazgos"]})

    def test_registrar_pide_aprobacion_en_posts_de_pagina(self):
        b = self.carpeta / "borradores" / "sin-aprobar.md"
        b.write_text(borrador_pagina("Abrimos la inscripción al taller del 3 de diciembre.",
                                     aprobado_por=None, estado="borrador"), encoding="utf-8")
        with self.assertRaises(SystemExit):
            li.registrar(self.carpeta, b, url="https://www.linkedin.com/feed/update/9")


class Exportacion(unittest.TestCase):
    AHORA = datetime(2026, 11, 12, 10, 0)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.carpeta = Path(self.tmp.name)
        li.iniciar(self.carpeta)
        (self.carpeta / "marca.md").write_text(MARCA, encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def escribir(self, nombre, contenido):
        (self.carpeta / "borradores" / nombre).write_text(contenido, encoding="utf-8")

    def preparar(self):
        return li.preparar_exportacion(self.carpeta, ahora=self.AHORA)

    def test_exporta_solo_lo_aprobado_de_pagina(self):
        self.escribir("a.md", borrador_pagina("Abrimos la inscripción al taller del 3 de diciembre.",
                                              enlace="https://ejemplo.com/registro"))
        self.escribir("b.md", borrador_pagina("Borrador que nadie aprobó todavía.", estado="borrador"))
        self.escribir("c.md", borrador_pagina("Post personal.", destino="perfil"))
        piezas, errores, avisos = self.preparar()
        self.assertEqual(errores, [])
        self.assertEqual([p["archivo"] for p in piezas], ["a.md"])
        self.assertEqual(piezas[0]["zona_horaria"], "America/Bogota")
        self.assertEqual(piezas[0]["aprobado_por"], "Equipo de eventos")

        salida = self.carpeta / "h.csv"
        li.escribir_hootsuite(piezas, salida, "dmy")
        filas = list(csv.reader(salida.open(encoding="utf-8")))
        self.assertEqual(len(filas), 1)
        self.assertEqual(filas[0][0], "20/11/2026 09:30")
        self.assertTrue(filas[0][1].startswith("Abrimos la inscripción"))
        self.assertEqual(filas[0][2], "https://ejemplo.com/registro")

    def test_cada_regla_de_hootsuite(self):
        self.escribir("sin-aprobador.md", borrador_pagina("Uno.", aprobado_por=None))
        self.escribir("minuto.md", borrador_pagina("Dos, con su dato de 12 sesiones.", programado_para="2026-11-21 09:32"))
        self.escribir("pronto.md", borrador_pagina("Tres, con su dato de 4 ponentes.", programado_para="2026-11-12 10:10"))
        self.escribir("mismo-horario-1.md", borrador_pagina("Cuatro, con 30 cupos.", programado_para="2026-11-22 08:00"))
        self.escribir("mismo-horario-2.md", borrador_pagina("Cinco, con 2 sedes.", programado_para="2026-11-22 08:00"))
        self.escribir("dup-1.md", borrador_pagina("Texto repetido con 3 datos.", programado_para="2026-11-23 08:00"))
        self.escribir("dup-2.md", borrador_pagina("Texto  repetido con 3 datos.", programado_para="2026-11-24 08:00"))
        self.escribir("revisor.md", borrador_pagina("En resumen, resultados garantizados.", programado_para="2026-11-25 08:00"))
        # Imagen en el formato anterior a 1.2.0: un párrafo suelto, sin alt, origen ni archivo.
        self.escribir("imagen.md", borrador_pagina("Seis, con 5 talleres.", programado_para="2026-11-26 08:00")
                      + "\n## Imagen\n\nUna foto del taller.\n")
        _, errores, avisos = self.preparar()
        texto = "\n".join(errores)
        self.assertIn("sin-aprobador.md: falta aprobado_por", texto)
        self.assertIn("minuto.md: Hootsuite pide minutos terminados en 0 o 5", texto)
        self.assertIn("pronto.md", texto)
        self.assertIn("mismo-horario-1.md y mismo-horario-2.md: misma hora", texto)
        self.assertIn("dup-1.md y dup-2.md: mismo texto", texto)
        self.assertIn("revisor.md: no pasa el revisor (R03, R19)", texto)
        self.assertIn("imagen.md: no pasa el revisor (R21, R22)", texto)
        self.assertIn("imagen.md: la imagen no tiene archivo", texto)
        self.assertIn("imagen.md: un post con imagen necesita huella_aprobada", texto)
        self.assertTrue(any(a.startswith("imagen.md") for a in avisos))

    def test_todo_o_nada_desde_la_linea_de_comandos(self):
        self.escribir("bien.md", borrador_pagina("Abrimos la inscripción al taller del 3 de diciembre.",
                                                 programado_para="2030-01-15 09:30"))
        self.escribir("mal.md", borrador_pagina("Otro post de 2 líneas.", programado_para="2030-01-15 09:31"))
        env = dict(os.environ, LINKEDIN_SKILL_DIR=str(self.carpeta), PYTHONUTF8="1")
        r = subprocess.run([sys.executable, str(SCRIPT), "exportar"], capture_output=True, text=True, env=env)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertFalse((self.carpeta / "exportaciones").exists())
        (self.carpeta / "borradores" / "mal.md").unlink()
        salida = self.carpeta / "lista.json"
        r = subprocess.run([sys.executable, str(SCRIPT), "exportar", "--formato", "json", "--salida", str(salida)],
                           capture_output=True, text=True, env=env)
        self.assertEqual(r.returncode, 0, r.stdout)
        datos = json.loads(salida.read_text(encoding="utf-8"))
        self.assertEqual(datos[0]["programado_para"], "2030-01-15T09:30")
        self.assertEqual(set(datos[0]), {"archivo", "programado_para", "zona_horaria", "texto", "enlace", "pilar",
                                         "formato", "tipo_pieza", "aprobado_por", "aprobado_el", "lleva_imagen",
                                         "imagen", "huella"})
        self.assertIsNone(datos[0]["imagen"])
        self.assertRegex(datos[0]["huella"], r"^[0-9a-f]{64}$")


def png(ruta, contenido=b"prueba"):
    """Un archivo con la firma de PNG. El revisor no abre la imagen; basta con que exista."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_bytes(bytes([137, 80, 78, 71, 13, 10, 26, 10]) + contenido)
    return ruta


def seccion_imagen(**campos):
    return "\n## Imagen\n\n" + "".join("- %s: %s\n" % kv for kv in campos.items())


ALT = "Gráfico de barras: el cierre contable bajó de 14 a 9 días."


class Imagenes(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.carpeta = Path(self.tmp.name)
        li.iniciar(self.carpeta)
        self.biblioteca = self.carpeta / "biblioteca"
        self.foto = png(self.biblioteca / "cierre.png")
        marca = MARCA + "\n## Imágenes\n\n- Generar imágenes: no\n\n### Bibliotecas aprobadas\n\n- %s\n" % self.biblioteca
        (self.carpeta / "marca.md").write_text(marca, encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def politica(self, destino="pagina"):
        return li.politica_de_imagen(self.carpeta, destino)

    def cods(self, imagen, destino="pagina", nivel=None, nunca=(), prohibidas=()):
        inf = li.revisar("Bajamos el cierre de 14 a 9 días.", imagen=imagen, politica_imagen=self.politica(destino),
                         base=self.carpeta, nunca=nunca, prohibidas=prohibidas)
        return [h["codigo"] for h in inf["hallazgos"] if nivel is None or h["nivel"] == nivel]

    def imagen(self, **campos):
        base = {"origen": "biblioteca", "archivo": str(self.foto), "alt": ALT}
        base.update(campos)
        return li.leer_imagen(seccion_imagen(**base))

    def test_leer_imagen(self):
        contenido = ("---\nidioma: es\n---\n\nTexto del post.\n" + seccion_imagen(
            origen="Plantilla", archivo="imagenes/a.png", alt=ALT, texto="De 14 a 9 días")
            + "\n## Notas\n\n- archivo: esto no es de la imagen\n")
        img = li.leer_imagen(contenido)
        self.assertEqual(img["origen"], "plantilla")
        self.assertEqual(img["archivo"], "imagenes/a.png")
        self.assertEqual(img["texto"], "De 14 a 9 días")
        self.assertEqual(li.separar_borrador(contenido)[1], "Texto del post.")
        self.assertEqual(li.leer_imagen("## Imagen\n\nUna foto del taller.\n")["muestra"], "Una foto del taller.")
        self.assertIsNone(li.leer_imagen("Texto sin imagen.\n\n## Imagenes viejas\n\n- alt: x\n"))

    def test_imagen_completa_pasa(self):
        self.assertEqual(self.cods(self.imagen()), [])

    def test_texto_alternativo(self):
        self.assertIn("R21", self.cods(self.imagen(alt=""), nivel="error"))
        self.assertIn("R21", self.cods(self.imagen(alt="a" * 121), nivel="aviso"))
        self.assertIn("R21", self.cods(self.imagen(alt="a" * 4087), nivel="error"))

    def test_origen(self):
        self.assertIn("R22", self.cods(self.imagen(origen="internet"), nivel="error"))
        self.assertIn("R22", self.cods(self.imagen(origen=""), nivel="error"))

    def test_archivo(self):
        self.assertEqual(self.cods(self.imagen(archivo="")), ["R23"])
        self.assertIn("R23", self.cods(self.imagen(archivo=""), nivel="aviso"))
        self.assertIn("R23", self.cods(self.imagen(archivo=str(png(self.biblioteca / "a.webp"))), nivel="error"))
        self.assertIn("R23", self.cods(self.imagen(archivo=str(self.biblioteca / "no-existe.png")), nivel="error"))
        relativo = self.imagen(archivo="biblioteca/cierre.png")
        self.assertEqual(self.cods(relativo), [])

    def test_imagen_generada_segun_la_marca(self):
        generada = self.imagen(origen="generada", archivo=str(png(self.carpeta / "generadas" / "g.png")),
                               prompt="Ilustración de un calendario")
        self.assertIn("R24", self.cods(generada, nivel="error"))
        self.assertNotIn("R24", self.cods(generada, destino="perfil"))
        marca = (self.carpeta / "marca.md").read_text(encoding="utf-8")
        (self.carpeta / "marca.md").write_text(marca.replace("Generar imágenes: no", "Generar imágenes: sí"),
                                               encoding="utf-8")
        self.assertNotIn("R24", self.cods(generada))

    def test_bibliotecas_aprobadas(self):
        afuera = png(self.carpeta / "descargas" / "x.png")
        self.assertIn("R25", self.cods(self.imagen(archivo=str(afuera)), nivel="error"))
        self.assertNotIn("R25", self.cods(self.imagen(archivo=str(afuera)), destino="perfil"))
        escape = str(self.biblioteca / ".." / "descargas" / "x.png")
        self.assertIn("R25", self.cods(self.imagen(archivo=escape), nivel="error"))
        web = ["https://marca.ejemplo.com/imagenes"]
        self.assertTrue(li._en_biblioteca("https://marca.ejemplo.com/imagenes/a.png", web))
        self.assertFalse(li._en_biblioteca("https://marca.ejemplo.com/imagenes-viejas/a.png", web))
        self.assertFalse(li._en_biblioteca("https://marca.ejemplo.com/imagenes/../otra/a.png", web))

    def test_texto_sobre_la_imagen_pasa_por_las_reglas(self):
        inf = li.revisar("Bajamos el cierre de 14 a 9 días.", imagen=self.imagen(texto="En resumen, Cliente Reservado"),
                         politica_imagen=self.politica(), base=self.carpeta, nunca=["Cliente Reservado"])
        mensajes = [h["mensaje"] for h in inf["hallazgos"] if h["codigo"] in ("R03", "R16")]
        self.assertEqual(len(mensajes), 2)
        self.assertTrue(all(m.startswith("En la imagen") for m in mensajes))
        self.assertIn("R19", self.cods(self.imagen(texto="Resultados garantizados"), prohibidas=["resultados garantizados"]))

    def test_huella(self):
        img = self.imagen()
        h = li.huella("Texto.", img, self.carpeta)
        self.assertEqual(h, li.huella("Texto.", img, self.carpeta))
        self.assertNotEqual(h, li.huella("Texto distinto.", img, self.carpeta))
        self.assertNotEqual(h, li.huella("Texto.", self.imagen(alt="Otro alt"), self.carpeta))
        self.assertNotEqual(h, li.huella("Texto.", None, self.carpeta))
        png(self.foto, b"otra foto con el mismo nombre")
        self.assertNotEqual(h, li.huella("Texto.", img, self.carpeta))

    def borrador_con_imagen(self, nombre="foto.md", huella_aprobada=True, **campos):
        img = {"origen": "biblioteca", "archivo": "../biblioteca/cierre.png", "alt": ALT}
        img.update(campos)
        contenido = borrador_pagina("Bajamos el cierre contable de 14 a 9 días.",
                                    programado_para="2030-01-15 09:30") + seccion_imagen(**img)
        ruta = self.carpeta / "borradores" / nombre
        ruta.write_text(contenido, encoding="utf-8")
        if huella_aprobada:
            meta, texto = li.separar_borrador(contenido)
            h = li.huella(texto, li.leer_imagen(contenido), ruta.parent)
            ruta.write_text(contenido.replace("estado: aprobado", "estado: aprobado\nhuella_aprobada: " + h),
                            encoding="utf-8")
        return ruta

    def test_exporta_la_imagen_con_su_huella(self):
        self.borrador_con_imagen()
        piezas, errores, avisos = li.preparar_exportacion(self.carpeta, ahora=datetime(2026, 11, 12, 10, 0))
        self.assertEqual(errores, [])
        img = piezas[0]["imagen"]
        self.assertEqual(img["archivo"], str(self.foto.resolve()))
        self.assertEqual(img["sha256"], li.sha256_de_archivo(self.foto))
        self.assertEqual(img["alt"], ALT)
        self.assertTrue(piezas[0]["lleva_imagen"])
        self.assertTrue(any("Hootsuite" in a for a in avisos))

    def test_no_exporta_si_cambio_despues_de_aprobado(self):
        self.borrador_con_imagen()
        png(self.foto, b"la foto cambio en la biblioteca")
        _, errores, _ = li.preparar_exportacion(self.carpeta, ahora=datetime(2026, 11, 12, 10, 0))
        self.assertIn("foto.md: cambió después de aprobado", "\n".join(errores))

    def test_no_exporta_una_imagen_sin_huella(self):
        self.borrador_con_imagen(huella_aprobada=False)
        _, errores, _ = li.preparar_exportacion(self.carpeta, ahora=datetime(2026, 11, 12, 10, 0))
        self.assertIn("foto.md: un post con imagen necesita huella_aprobada", "\n".join(errores))

    def test_comandos_revisar_huella_y_registrar(self):
        ruta = self.borrador_con_imagen()
        env = dict(os.environ, LINKEDIN_SKILL_DIR=str(self.carpeta), PYTHONUTF8="1")
        correr = lambda *a: subprocess.run([sys.executable, str(SCRIPT)] + list(a), capture_output=True,
                                           text=True, env=env)
        r = correr("revisar", str(ruta), "--json")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertEqual(json.loads(r.stdout)["imagen"]["origen"], "biblioteca")
        r = correr("huella", str(ruta))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertRegex(r.stdout.strip(), r"^[0-9a-f]{64}$")
        ruta.write_text(ruta.read_text(encoding="utf-8").replace("de 14 a 9", "de 15 a 9"), encoding="utf-8")
        self.assertEqual(correr("huella", str(ruta)).returncode, 1)
        with self.assertRaises(SystemExit):
            li.registrar(self.carpeta, ruta, url="https://www.linkedin.com/feed/update/5")

    def test_plantilla_de_marca_sin_politica(self):
        plantilla = SKILL / "plantillas" / "marca.md"
        politica = li.politica_de_imagen(self.carpeta, "pagina", marca=plantilla)
        self.assertEqual(politica, {"generar": False, "bibliotecas": []})


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
        leer = lambda r: json.loads((RAIZ / r).read_text(encoding="utf-8"))
        claude = leer("plugins/linkedin/.claude-plugin/plugin.json")
        portable = leer("plugins/linkedin/plugin.json")
        market_claude = leer(".claude-plugin/marketplace.json")
        market_codex = leer(".agents/plugins/marketplace.json")
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        version_skill = re.search(r'^version:\s*"([^"]+)"', skill, re.M).group(1)
        version_log = re.search(r"^## \[([^\]]+)\]", (RAIZ / "CHANGELOG.md").read_text(encoding="utf-8"), re.M).group(1)
        self.assertEqual({claude["version"], portable["version"], version_skill, version_log}, {version_log})
        self.assertEqual(claude["name"], portable["name"])
        self.assertEqual(claude["description"], portable["description"])
        self.assertTrue(portable["$schema"].startswith("https://agent-plugins.org/schemas/"))
        self.assertEqual(market_claude["name"], market_codex["name"])
        self.assertEqual(market_claude["plugins"][0]["source"], "./plugins/linkedin")
        self.assertEqual(market_claude["plugins"][0]["name"], claude["name"])
        entrada = market_codex["plugins"][0]
        self.assertEqual(entrada["name"], portable["name"])
        self.assertEqual(entrada["source"], {"source": "local", "path": "./plugins/linkedin"})
        self.assertTrue((RAIZ / entrada["source"]["path"]).is_dir())
        self.assertTrue({"installation", "authentication"} <= set(entrada["policy"]))
        self.assertIn("category", entrada)
        self.assertTrue((SKILL / "agents" / "openai.yaml").exists())

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
        for patron in ("perfil.local.md", "marca.local.md", "registro.csv", "borradores/", "exportaciones/"):
            self.assertIn(patron, ignorados)


if __name__ == "__main__":
    unittest.main()
