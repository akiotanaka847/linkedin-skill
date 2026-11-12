#!/usr/bin/env python3
"""Herramienta de la skill /linkedin.

Cuatro trabajos deterministas que el agente no debe hacer a ojo:
  1. La carpeta de datos (perfil, marca, banco de historias, calendario, borradores, registro).
  2. La revisión de un borrador: rayas, barras, muletillas, contrastes de póster,
     nombres que no pueden salir, frases que la marca prohíbe, avisos obligatorios,
     cifras que hay que trazar.
  3. La exportación de lo aprobado para la página de empresa (CSV de Hootsuite o JSON
     para otro agente), con la aprobación como condición.
  4. El registro de lo publicado y el resumen de sus métricas.

Solo biblioteca estándar. Python 3.9 o superior.
"""

import argparse
import csv
import json
import os
import re
import shutil
import statistics
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent
PLANTILLAS = SKILL_DIR / "plantillas"
MULETILLAS = SKILL_DIR / "muletillas.json"

ARCHIVOS_PLANTILLA = ("perfil.md", "marca.md", "banco-de-historias.md", "calendario.md")

# Carga masiva de Hootsuite (Bulk Composer), según su ayuda: columna A fecha y hora,
# B texto, C enlace opcional; minutos terminados en 0 o 5; un post por horario; sin
# duplicados; hasta 350 filas; sin imágenes. La ayuda vigente pide 20 minutos de margen.
HOOTSUITE_MAX = 350
HOOTSUITE_MARGEN_MIN = 20
FORMATOS_FECHA = {"dmy": "%d/%m/%Y %H:%M", "mdy": "%m/%d/%Y %H:%M", "ymd": "%Y/%m/%d %H:%M"}

# Límites de referencia. El post sale del editor de LinkedIn; los otros tres son de
# guías de terceros (ver referencias/linkedin.md). El editor siempre tiene la última palabra.
LIMITES = {"post": 3000, "comentario": 1250, "titular": 220, "acerca": 2600, "doc": None}

# Aproximación de lo que se ve antes de "...ver más". Depende del dispositivo.
CORTE_VER_MAS = 210

RAYA = "\u2014"
SEMIRRAYA = "\u2013"

COLUMNAS = [
    "id", "fecha", "idioma", "pilar", "formato", "caracteres", "primera_linea", "url", "archivo",
    "impresiones", "alcance", "reacciones", "comentarios", "compartidos", "guardados", "envios",
    "visitas_perfil", "seguidores", "medido_el", "destino",
]
METRICAS = ["impresiones", "alcance", "reacciones", "comentarios", "compartidos", "guardados",
            "envios", "visitas_perfil", "seguidores"]

SECCIONES_FUERA_DEL_TEXTO = re.compile(
    r"^##\s+(primer comentario|trazabilidad|imagen|notas|variantes)\b", re.I)

LETRA = r"[^\W\d_]"
PALABRA = r"[^\W\d_]+"


# ---------------------------------------------------------------------------
# Carpeta de datos
# ---------------------------------------------------------------------------

def carpeta_datos():
    """Dónde viven los datos de la persona. Nunca dentro del repo de la skill."""
    env = os.environ.get("LINKEDIN_SKILL_DIR")
    if env:
        return Path(env).expanduser()
    return Path.home() / ".config" / "linkedin-skill"


def iniciar(carpeta):
    """Crea la carpeta y copia las plantillas que falten. No pisa nada."""
    carpeta.mkdir(parents=True, exist_ok=True)
    if os.name == "posix":
        os.chmod(carpeta, 0o700)
    (carpeta / "borradores").mkdir(exist_ok=True)
    informe = []
    for nombre in ARCHIVOS_PLANTILLA:
        destino = carpeta / nombre
        if destino.exists():
            informe.append((nombre, "ya existía"))
        else:
            shutil.copyfile(PLANTILLAS / nombre, destino)
            informe.append((nombre, "creado"))
    registro = carpeta / "registro.csv"
    if registro.exists():
        informe.append(("registro.csv", "ya existía"))
    else:
        with registro.open("w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(COLUMNAS)
        informe.append(("registro.csv", "creado"))
    return informe


def plantilla_vacia(ruta):
    """Una plantilla sin llenar conserva la línea 'estado: vacío'."""
    if not ruta.exists():
        return True
    return bool(re.search(r"^estado:\s*vac[ií]o\s*$", ruta.read_text(encoding="utf-8"), re.M))


def contar_historias(ruta):
    """Cada historia del banco es un encabezado '### '."""
    if not ruta.exists():
        return 0
    total, en_bloque = 0, False
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        if linea.strip().startswith("```"):
            en_bloque = not en_bloque
        elif not en_bloque and linea.startswith("### "):
            total += 1
    return total


def leer_lista(ruta, seccion, cortar_nota=True):
    """Lee las viñetas de una sección '## <seccion>' de un perfil o de la marca.

    Las viñetas que empiezan con '(' son instrucciones de la plantilla y se saltan. Con
    cortar_nota, lo que va después de ' (' es una nota y no forma parte del valor.
    """
    if not ruta or not Path(ruta).exists():
        return []
    valores, dentro = [], False
    patron = re.compile(r"^#+\s*" + re.escape(seccion) + r"\b", re.I)
    for linea in Path(ruta).read_text(encoding="utf-8").splitlines():
        if re.match(r"^#+\s", linea):
            dentro = bool(patron.match(linea))
            continue
        if dentro and linea.strip().startswith("- "):
            valor = linea.strip()[2:].strip()
            if cortar_nota:
                valor = valor.split(" (")[0].strip()
            if valor and not valor.startswith("(") and valor not in ("...", "…"):
                valores.append(valor)
    return valores


def leer_nunca_nombrar(ruta):
    """La lista '## Nunca nombrar': un nombre por viñeta."""
    return leer_lista(ruta, "Nunca nombrar")


def leer_campo(ruta, campo):
    """El valor de una línea '- <campo>: valor' en cualquier parte del archivo."""
    if not ruta or not Path(ruta).exists():
        return ""
    m = re.search(r"^-\s*" + re.escape(campo) + r":[ \t]*(.*)$",
                  Path(ruta).read_text(encoding="utf-8"), re.I | re.M)
    valor = m.group(1).strip() if m else ""
    return "" if valor.startswith("(") else valor


def reglas_de_destino(carpeta, destino, perfil=None, marca=None):
    """Listas que aplican según a nombre de quién sale el post.

    Un post de página suma la lista Nunca nombrar de la persona y la de la marca, y
    además las frases prohibidas y los avisos obligatorios de la marca.
    """
    perfil = Path(perfil) if perfil else carpeta / "perfil.md"
    nunca = leer_nunca_nombrar(perfil)
    prohibidas, avisos = [], []
    if destino == "pagina":
        marca = Path(marca) if marca else carpeta / "marca.md"
        nunca += [n for n in leer_nunca_nombrar(marca) if n not in nunca]
        prohibidas = leer_lista(marca, "Frases prohibidas")
        avisos = leer_lista(marca, "Aviso obligatorio", cortar_nota=False)
    return nunca, prohibidas, avisos


# ---------------------------------------------------------------------------
# Lectura de borradores
# ---------------------------------------------------------------------------

def separar_borrador(contenido):
    """Devuelve (metadatos, texto_del_post). Quita el encabezado y las secciones de trabajo."""
    meta = {}
    lineas = contenido.splitlines()
    if lineas and lineas[0].strip() == "---":
        for i in range(1, len(lineas)):
            if lineas[i].strip() == "---":
                for l in lineas[1:i]:
                    if ":" in l:
                        k, v = l.split(":", 1)
                        meta[k.strip()] = v.strip()
                lineas = lineas[i + 1:]
                break
    cuerpo = []
    for l in lineas:
        if SECCIONES_FUERA_DEL_TEXTO.match(l.strip()):
            break
        cuerpo.append(l)
    return meta, "\n".join(cuerpo).strip("\n")


# ---------------------------------------------------------------------------
# Revisión
# ---------------------------------------------------------------------------

STOP_ES = set("el la de que y en los se del las por un para con una es lo como más pero sus le ya o "
              "este sí porque esta entre cuando muy sin sobre también me hasta hay donde quien desde "
              "todo nos durante todos uno les ni contra otros ese eso ante ellos e esto mí antes "
              "algunos qué unos yo otro otras otra él tanto esa estos mucho quienes nada muchos cual "
              "poco ella estar estas algunas algo nosotros".split())
STOP_EN = set("the and to of a in is that for it with on as was you this be are at by not from "
              "or have an they which one had but what all were when we there can been has more if "
              "will so no out about up into than them only other new some could time these two may "
              "then do first any my now such like our over man me even most made after also did "
              "many before must through back years where much your way well down should because".split())


def detectar_idioma(texto):
    palabras = re.findall(PALABRA, texto.lower())
    es = sum(1 for p in palabras if p in STOP_ES)
    en = sum(1 for p in palabras if p in STOP_EN)
    if re.search(r"[¿¡ñáéíóú]", texto.lower()):
        es += 3
    return "en" if en > es else "es"


def cargar_muletillas(ruta=MULETILLAS):
    datos = json.loads(Path(ruta).read_text(encoding="utf-8"))
    reglas = []
    for idioma in ("es", "en"):
        for item in datos.get(idioma, []):
            patron = re.compile(r"(?<!\w)(?:" + item["patron"] + r")(?!\w)", re.I)
            reglas.append((patron, item["nivel"], item.get("sugerencia", ""), idioma))
    return reglas


def _sin_codigo(texto):
    """Borra los bloques ``` y el texto entre comillas invertidas, conservando los saltos de línea.

    Sirve para citar una muletilla en un documento sin que el revisor la bloquee. Un tramo
    entre comillas invertidas puede partirse en dos líneas dentro del mismo párrafo, como en
    Markdown; por eso se limpia el texto completo y no línea por línea.
    """
    salida, en_bloque = [], False
    for linea in texto.split("\n"):
        if linea.strip().startswith("```"):
            en_bloque = not en_bloque
            salida.append("")
        else:
            salida.append("" if en_bloque else linea)
    texto = "\n".join(salida)
    return re.sub(r"`(?:[^`\n]|\n(?![ \t]*\n))*`",
                  lambda m: re.sub(r"[^\n]", " ", m.group(0)), texto)


def _sin_urls(linea):
    linea = re.sub(r"\]\([^)]*\)", lambda m: " " * len(m.group(0)), linea)
    linea = re.sub(r"(https?://|www\.)\S+", lambda m: " " * len(m.group(0)), linea)
    return re.sub(r"\b[\w.-]+\.[a-z]{2,}/\S*", lambda m: " " * len(m.group(0)), linea)


def _fragmento(linea, inicio, fin, margen=30):
    a, b = max(0, inicio - margen), min(len(linea), fin + margen)
    return ("..." if a else "") + linea[a:b].strip() + ("..." if b < len(linea) else "")


CONTRASTES = [
    (r"\bno (es|son|era|eran|fue|fueron|ser[aá]) [^.!?\n]{1,80}?[,;:.]\s*(es|son|era|eran|fue|fueron|ser[aá])\b(?! decir)",
     "error", "Fórmula 'no es X, es Y'. Di directamente lo que es, con el dato."),
    (r"\bno se trata de [^.!?\n]{1,80}?[,;:.]\s*se trata de\b",
     "error", "Fórmula 'no se trata de X, se trata de Y'. Di de qué se trata y ya."),
    (r"\bno solo\b[^.!?\n]{0,100}?\bsino\b",
     "error", "Fórmula 'no solo X sino Y'. Quédate con lo que pesa más."),
    (r"\bmenos [^.!?\n,]{1,40}, m[aá]s [^.!?\n]{1,40}",
     "aviso", "Contraste de póster 'menos X, más Y'. Cambia por el caso."),
    (r"\b" + PALABRA + r"(?:ando|endo), no " + PALABRA + r"(?:ando|endo)\b",
     "aviso", "Contraste 'haciendo X, no Y'. Basta con lo que sí hiciste."),
    (r"\b" + PALABRA + r"ing, not " + PALABRA + r"ing\b",
     "aviso", "Contrast 'doing X, not Y'. Keep what you did."),
    (r"\b(it'?s|it is|this is|that'?s|that is) not (just |only |about )?[^.!?\n]{1,60}?[,;:.]\s*(it'?s|it is|this is|that'?s|that is)\b",
     "error", "Pattern 'it's not X, it's Y'. Say what it is, with the fact."),
    (r"\bnot just\b[^.!?\n]{0,80}?\bbut\b",
     "error", "Pattern 'not just X but Y'. Keep the part that matters."),
    (r"\bisn'?t (just |only |about )?[^.!?\n]{1,60}?[,;:.]\s*(it'?s|it is)\b",
     "error", "Pattern 'X isn't Y, it's Z'. Say what it is."),
]

ETIQUETAS = [
    r"^\s*(spoiler|plot twist|la lecci[oó]n|lecci[oó]n aprendida|moraleja|dato curioso|pro tip|bonus|tl;?dr|el resultado|the result|the lesson|takeaway|key takeaway)\s*[:?]",
    r"^\s*¿(el|la|lo|los|las) " + PALABRA + r"( " + PALABRA + r")?\?\s*$",
    r"^\s*(the result|the kicker|the catch|the twist|the truth|the best part)\?\s*$",
    r"^\s*(here'?s (what|how|why|the)|aqu[ií] (va|van|te dejo|est[aá]n?))\b",
]

EMOJI = re.compile("[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F000-\U0001F2FF⭐⬆↔-↪]")

CIFRA = re.compile(
    r"(?<![\w.,])\d+(?:[.,]\d+)*(?:\s?%|\s?(?:x|veces|times|ms|s|seg|minutos|minutes|min|h|horas|hours|d[ií]as|days|semanas|weeks|meses|months|a[nñ]os|years|"
    r"USD|COP|EUR|k|M|MB|GB|KB|px|fps)\b)?")

TRIADA = re.compile(
    r"\b" + PALABRA + r"(?: " + PALABRA + r")?, " + PALABRA + r"(?: " + PALABRA + r")?,? (?:y|e|o|u|and|or) "
    + PALABRA + r"(?: " + PALABRA + r")?\b", re.I)


def revisar(texto, tipo="post", idioma="auto", nunca=(), reglas_muletillas=None,
            prohibidas=(), avisos_obligatorios=()):
    """Revisa un texto y devuelve un informe con hallazgos ordenables por severidad."""
    if tipo not in LIMITES:
        raise ValueError("tipo desconocido: %s" % tipo)
    if reglas_muletillas is None:
        reglas_muletillas = cargar_muletillas()
    texto = texto.replace("\r\n", "\n").strip("\n")
    idioma = detectar_idioma(texto) if idioma == "auto" else idioma
    es_doc = tipo == "doc"
    hallazgos = []

    def agregar(codigo, nivel, mensaje, n_linea=None, fragmento=""):
        hallazgos.append({"codigo": codigo, "nivel": nivel, "mensaje": mensaje,
                          "linea": n_linea, "fragmento": fragmento})

    lineas = texto.split("\n")
    limpias = [_sin_urls(l) for l in _sin_codigo(texto).split("\n")]

    for n, linea in enumerate(limpias, 1):
        original = lineas[n - 1]
        # R01 rayas
        for m in re.finditer("[" + RAYA + SEMIRRAYA + "]| -- ", linea):
            agregar("R01", "error", "Raya o semirraya. Cámbiala por coma, dos puntos, paréntesis o punto.",
                    n, _fragmento(original, m.start(), m.end()))
        # R02 barras como separador
        for m in re.finditer(r"(?<![\w/.~])(" + PALABRA + r")(?:/| / )(" + PALABRA + r")(?![\w/]|\.\w)", linea):
            agregar("R02", "error", "Barra como separador. Usa 'y', 'o' o una coma.",
                    n, _fragmento(original, m.start(), m.end()))
        # R03 muletillas
        for patron, nivel, sugerencia, _ in reglas_muletillas:
            for m in patron.finditer(linea):
                agregar("R03", nivel, "Muletilla '%s'. %s" % (m.group(0), sugerencia),
                        n, _fragmento(original, m.start(), m.end()))
        # R04 contrastes de póster
        for patron, nivel, mensaje in CONTRASTES:
            for m in re.finditer(patron, linea, re.I):
                agregar("R04", nivel, mensaje, n, _fragmento(original, m.start(), m.end()))
        if re.search(r"\bno solo\b", linea, re.I) and not re.search(r"\bno solo\b[^.!?\n]{0,100}?\bsino\b", linea, re.I):
            agregar("R04", "aviso", "'No solo' suele anunciar un contraste. Revisa si sobra.", n,
                    _fragmento(original, *re.search(r"\bno solo\b", linea, re.I).span()))
        # R13 etiquetas y bisagras
        for patron in ETIQUETAS:
            if re.search(patron, linea, re.I):
                agregar("R13", "aviso", "Etiqueta o bisagra de revelación. Pasa directo al contenido.",
                        n, original.strip()[:80])
                break
        if es_doc:
            continue
        # R18 mayúsculas sostenidas
        letras = re.findall(LETRA, linea)
        if len(letras) >= 12 and sum(1 for c in letras if c.isupper()) / len(letras) >= 0.7:
            agregar("R18", "aviso", "Línea en mayúsculas. La intensidad va en las palabras.", n, original.strip()[:80])

    # R16 nombres que no pueden salir (también en documentos)
    plano = "\n".join(limpias)
    for nombre in nunca:
        for m in re.finditer(r"(?<!\w)" + re.escape(nombre) + r"(?!\w)", plano, re.I):
            n = plano.count("\n", 0, m.start()) + 1
            columna = m.start() - (plano.rfind("\n", 0, m.start()) + 1)
            agregar("R16", "error", "'%s' está en 'Nunca nombrar' del perfil." % nombre, n,
                    _fragmento(lineas[n - 1], columna, columna + len(m.group(0))))

    # R19 frases que la marca prohíbe (cumplimiento, promesas, claims sin respaldo)
    for frase in prohibidas:
        for m in re.finditer(r"(?<!\w)" + re.escape(frase) + r"(?!\w)", plano, re.I):
            n = plano.count("\n", 0, m.start()) + 1
            columna = m.start() - (plano.rfind("\n", 0, m.start()) + 1)
            agregar("R19", "error", "'%s' está en 'Frases prohibidas' de la marca." % frase, n,
                    _fragmento(lineas[n - 1], columna, columna + len(m.group(0))))

    # R20 avisos obligatorios de la marca (por ejemplo, un aviso legal)
    if tipo == "post" and avisos_obligatorios:
        normal = re.sub(r"\s+", " ", texto).lower()
        for aviso in avisos_obligatorios:
            if re.sub(r"\s+", " ", aviso).lower() not in normal:
                agregar("R20", "error", "Falta el aviso obligatorio de la marca: «%s»" % aviso[:120])

    visibles = [l for l in lineas if l.strip()]
    caracteres = len(texto)
    palabras = len(re.findall(r"\S+", texto))

    if not es_doc:
        # R05 primera línea en pregunta
        if tipo == "post" and visibles and "?" in visibles[0]:
            agregar("R05", "aviso", "La primera línea es una pregunta. Abre con el hecho o la cifra; la pregunta va al cierre.",
                    1, visibles[0].strip()[:80])
        # R06 enlaces
        if re.search(r"https?://|www\.", texto):
            agregar("R06", "info", "Hay un enlace en el texto. Por defecto va en el primer comentario.")
        # R07 hashtags
        hashtags = re.findall(r"(?<![\w&])#" + LETRA + r"\w*", texto)
        if len(hashtags) > 3:
            agregar("R07", "aviso", "%d hashtags. Deja tres como mucho." % len(hashtags))
        # R08 emojis
        emojis = EMOJI.findall(texto)
        if len(emojis) > 2:
            agregar("R08", "aviso", "%d emojis. Deja dos como mucho." % len(emojis))
        vinetas = [i for i, l in enumerate(lineas, 1) if l.strip() and EMOJI.match(l.strip())]
        if len(vinetas) >= 2:
            agregar("R08", "aviso", "Emojis usados como viñetas en %d líneas." % len(vinetas), vinetas[0])
        # R09 longitud
        limite = LIMITES[tipo]
        if limite and caracteres > limite:
            agregar("R09", "error", "%d caracteres; el límite de referencia para %s es %d." % (caracteres, tipo, limite))
        # R11 fragmentos apilados
        racha = []
        for i, l in enumerate(lineas, 1):
            if l.strip() and len(l.split()) <= 4:
                racha.append(i)
            elif l.strip():
                if len(racha) >= 3:
                    agregar("R11", "aviso", "%d frases muy cortas seguidas. Une alguna." % len(racha), racha[0])
                racha = []
        if len(racha) >= 3:
            agregar("R11", "aviso", "%d frases muy cortas seguidas. Une alguna." % len(racha), racha[0])
        # R12 tríadas
        triadas = [m.group(0) for m in TRIADA.finditer(plano)]
        if len(triadas) >= 2:
            agregar("R12", "aviso", "%d enumeraciones de tres. Deja una como mucho: %s" % (len(triadas), "; ".join(triadas[:3])))
        # R14 signos de apertura
        if idioma == "es":
            for n, linea in enumerate(limpias, 1):
                for cierre, apertura in (("?", "¿"), ("!", "¡")):
                    pos = 0
                    while True:
                        k = linea.find(cierre, pos)
                        if k < 0:
                            break
                        tramo = re.split(r"[.!?;]", linea[:k])[-1]
                        if apertura not in tramo:
                            agregar("R14", "aviso", "Falta el '%s' de apertura." % apertura, n,
                                    _fragmento(lineas[n - 1], max(0, k - 40), k + 1, 0))
                        pos = k + 1
        # R17 exclamaciones
        if texto.count("!") > 1:
            agregar("R17", "aviso", "%d signos de exclamación. Deja uno como mucho." % texto.count("!"))

    # R15 cifras para trazar
    cifras = []
    if not es_doc:
        for n, linea in enumerate(limpias, 1):
            for m in CIFRA.finditer(linea):
                cifras.append({"cifra": m.group(0).strip(), "linea": n})

    previa = re.sub(r"\s*\n\s*", " ", texto)
    if len(previa) > CORTE_VER_MAS:
        corte = previa.rfind(" ", 0, CORTE_VER_MAS)
        previa = previa[:corte if corte > 0 else CORTE_VER_MAS] + "..."

    orden = {"error": 0, "aviso": 1, "info": 2}
    hallazgos.sort(key=lambda h: (orden[h["nivel"]], h["linea"] or 0, h["codigo"]))
    return {
        "tipo": tipo, "idioma": idioma, "caracteres": caracteres, "palabras": palabras,
        "antes_de_ver_mas": previa if not es_doc else "",
        "hallazgos": hallazgos, "cifras": cifras,
        "errores": sum(1 for h in hallazgos if h["nivel"] == "error"),
        "avisos": sum(1 for h in hallazgos if h["nivel"] == "aviso"),
    }


def _miles(n):
    return "{:,}".format(n).replace(",", ".")


def imprimir_informe(inf):
    print("Revisión de %s en %s: %s caracteres, %s palabras." % (
        inf["tipo"], "español" if inf["idioma"] == "es" else "inglés",
        _miles(inf["caracteres"]), _miles(inf["palabras"])))
    if inf["antes_de_ver_mas"]:
        print('Antes de "ver más" (aproximado, depende del dispositivo):')
        print("  " + inf["antes_de_ver_mas"])
    for nivel, titulo in (("error", "ERRORES"), ("aviso", "AVISOS"), ("info", "NOTAS")):
        grupo = [h for h in inf["hallazgos"] if h["nivel"] == nivel]
        if not grupo:
            continue
        print("\n%s (%d)" % (titulo, len(grupo)))
        for h in grupo:
            donde = ("L%d " % h["linea"]) if h["linea"] else ""
            print("  %s%s %s" % (donde, h["codigo"], h["mensaje"]))
            if h["fragmento"]:
                print("      «%s»" % h["fragmento"])
    if inf["cifras"]:
        print("\nCIFRAS PARA TRAZAR (%d): cada una necesita su fuente en el banco o en el material." % len(inf["cifras"]))
        print("  " + ", ".join("%s (L%d)" % (c["cifra"], c["linea"]) for c in inf["cifras"]))
    print()
    if inf["errores"]:
        print("Resultado: no pasa, %d error%s." % (inf["errores"], "" if inf["errores"] == 1 else "es"))
    elif inf["avisos"]:
        print("Resultado: pasa, %d aviso%s por corregir o justificar." % (inf["avisos"], "" if inf["avisos"] == 1 else "s"))
    else:
        print("Resultado: pasa, sin avisos.")


# ---------------------------------------------------------------------------
# Registro y resultados
# ---------------------------------------------------------------------------

def leer_registro(ruta):
    if not ruta.exists():
        return []
    with ruta.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def escribir_registro(ruta, filas):
    tmp = ruta.with_suffix(".csv.tmp")
    with tmp.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNAS)
        w.writeheader()
        for fila in filas:
            w.writerow({k: fila.get(k, "") for k in COLUMNAS})
    os.replace(tmp, ruta)


def registrar(carpeta, archivo, url="", fecha=None, pilar=None, formato=None, idioma=None):
    ruta = carpeta / "registro.csv"
    if not ruta.exists():
        raise SystemExit("No hay registro.csv. Corre primero: linkedin.py iniciar")
    meta, texto = separar_borrador(Path(archivo).read_text(encoding="utf-8"))
    destino = meta.get("destino", "perfil")
    if destino == "pagina" and not (meta.get("aprobado_por") and meta.get("aprobado_el")):
        raise SystemExit("Un post de página necesita aprobado_por y aprobado_el en el borrador.")
    filas = leer_registro(ruta)
    if url and any(f["url"] == url for f in filas):
        raise SystemExit("Esa URL ya está en el registro.")
    nuevo_id = max([int(f["id"]) for f in filas if f["id"].isdigit()] or [0]) + 1
    primera = next((l.strip() for l in texto.splitlines() if l.strip()), "")
    fila = {
        "id": str(nuevo_id),
        "fecha": fecha or date.today().isoformat(),
        "idioma": idioma or meta.get("idioma") or detectar_idioma(texto),
        "pilar": pilar or meta.get("pilar", ""),
        "formato": formato or meta.get("formato", ""),
        "caracteres": str(len(texto)),
        "primera_linea": primera[:120],
        "url": url,
        "archivo": str(Path(archivo).resolve()),
        "destino": destino,
    }
    filas.append(fila)
    escribir_registro(ruta, filas)
    return fila


# ---------------------------------------------------------------------------
# Exportación de lo aprobado para la página de empresa
# ---------------------------------------------------------------------------

def preparar_exportacion(carpeta, ahora=None, marca=None, perfil=None):
    """Junta los borradores de página aprobados y los valida. Todo o nada.

    Devuelve (piezas, errores, avisos). Si hay errores no se exporta ninguna pieza:
    una carga a medias deja el calendario de la página en un estado que nadie revisó.
    """
    ahora = ahora or datetime.now()
    nunca, prohibidas, avisos_marca = reglas_de_destino(carpeta, "pagina", perfil, marca)
    piezas, errores, avisos = [], [], []
    for ruta in sorted((carpeta / "borradores").glob("*.md")):
        contenido = ruta.read_text(encoding="utf-8")
        meta, texto = separar_borrador(contenido)
        if meta.get("destino") != "pagina" or meta.get("estado") != "aprobado":
            continue
        nombre = ruta.name
        if not (meta.get("aprobado_por") and meta.get("aprobado_el")):
            errores.append("%s: falta aprobado_por o aprobado_el." % nombre)
            continue
        try:
            cuando = datetime.strptime(meta.get("programado_para", ""), "%Y-%m-%d %H:%M")
        except ValueError:
            errores.append("%s: programado_para debe ser AAAA-MM-DD HH:MM, en la hora de la página." % nombre)
            continue
        if cuando.minute % 5:
            errores.append("%s: Hootsuite pide minutos terminados en 0 o 5 (%s)." % (nombre, cuando.strftime("%H:%M")))
        if cuando < ahora + timedelta(minutes=HOOTSUITE_MARGEN_MIN):
            errores.append("%s: %s queda a menos de %d minutos de ahora." % (
                nombre, cuando.strftime("%Y-%m-%d %H:%M"), HOOTSUITE_MARGEN_MIN))
        inf = revisar(texto, "post", meta.get("idioma", "auto"), nunca,
                      prohibidas=prohibidas, avisos_obligatorios=avisos_marca)
        if inf["errores"]:
            codigos = sorted({h["codigo"] for h in inf["hallazgos"] if h["nivel"] == "error"})
            errores.append("%s: no pasa el revisor (%s)." % (nombre, ", ".join(codigos)))
        if re.search(r"^##\s+imagen\b", contenido, re.I | re.M):
            avisos.append("%s: la carga masiva no lleva imágenes; agrégala en Hootsuite después de subir el archivo." % nombre)
        piezas.append({
            "archivo": nombre, "programado_para": cuando.strftime("%Y-%m-%dT%H:%M"),
            "zona_horaria": leer_campo(Path(marca) if marca else carpeta / "marca.md", "Zona horaria"),
            "texto": texto, "enlace": meta.get("enlace", ""), "pilar": meta.get("pilar", ""),
            "formato": meta.get("formato", ""), "tipo_pieza": meta.get("tipo_pieza", ""),
            "aprobado_por": meta["aprobado_por"], "aprobado_el": meta["aprobado_el"],
            "lleva_imagen": bool(re.search(r"^##\s+imagen\b", contenido, re.I | re.M)),
        })
    vistos, textos = {}, {}
    for pz in piezas:
        if pz["programado_para"] in vistos:
            errores.append("%s y %s: misma hora; Hootsuite admite un post por horario." % (
                vistos[pz["programado_para"]], pz["archivo"]))
        vistos.setdefault(pz["programado_para"], pz["archivo"])
        clave = re.sub(r"\s+", " ", pz["texto"]).strip().lower()
        if clave in textos:
            errores.append("%s y %s: mismo texto; Hootsuite rechaza duplicados." % (textos[clave], pz["archivo"]))
        textos.setdefault(clave, pz["archivo"])
    if len(piezas) > HOOTSUITE_MAX:
        errores.append("%d piezas; Hootsuite acepta hasta %d por archivo." % (len(piezas), HOOTSUITE_MAX))
    return piezas, errores, avisos


def escribir_hootsuite(piezas, salida, formato_fecha="dmy"):
    """CSV para el Bulk Composer: A fecha y hora (24 h), B texto, C enlace. Sin encabezado."""
    with Path(salida).open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        for pz in sorted(piezas, key=lambda p: p["programado_para"]):
            cuando = datetime.strptime(pz["programado_para"], "%Y-%m-%dT%H:%M")
            w.writerow([cuando.strftime(FORMATOS_FECHA[formato_fecha]), pz["texto"], pz["enlace"]])


def anotar_metricas(carpeta, id_post, valores, fecha=None):
    ruta = carpeta / "registro.csv"
    filas = leer_registro(ruta)
    for fila in filas:
        if fila["id"] == str(id_post):
            for k, v in valores.items():
                if v is not None:
                    if v < 0:
                        raise SystemExit("%s no puede ser negativo." % k)
                    fila[k] = str(v)
            fila["medido_el"] = fecha or date.today().isoformat()
            escribir_registro(ruta, filas)
            return fila
    raise SystemExit("No hay un post con id %s en el registro." % id_post)


def _num(fila, k):
    v = fila.get(k, "")
    return int(v) if str(v).strip().isdigit() else None


def tasa_interaccion(fila):
    """Interacciones = reacciones + comentarios + compartidos, sobre impresiones."""
    imp = _num(fila, "impresiones")
    if not imp:
        return None
    return sum(_num(fila, k) or 0 for k in ("reacciones", "comentarios", "compartidos")) / imp


def resumir(filas, hoy=None, minimo=5):
    hoy = hoy or date.today()
    medidas = [f for f in filas if f.get("medido_el")]
    pendientes = []
    for f in filas:
        if f.get("medido_el"):
            continue
        try:
            dias = (hoy - datetime.strptime(f["fecha"], "%Y-%m-%d").date()).days
        except ValueError:
            dias = None
        if dias is None or dias >= 7:
            pendientes.append({"id": f["id"], "fecha": f["fecha"], "primera_linea": f["primera_linea"]})

    def agrupar(campo):
        grupos = {}
        for f in medidas:
            grupos.setdefault(f.get(campo) or "(sin dato)", []).append(f)
        salida = []
        for clave, fs in sorted(grupos.items()):
            imps = [_num(f, "impresiones") for f in fs if _num(f, "impresiones") is not None]
            tasas = [t for t in (tasa_interaccion(f) for f in fs) if t is not None]
            guard = [_num(f, "guardados") for f in fs if _num(f, "guardados") is not None]
            salida.append({
                "grupo": clave, "posts": len(fs),
                "mediana_impresiones": statistics.median(imps) if imps else None,
                "mediana_tasa": statistics.median(tasas) if tasas else None,
                "mediana_guardados": statistics.median(guard) if guard else None,
                "muestra_suficiente": len(fs) >= minimo,
            })
        return salida

    con_tasa = [f for f in medidas if tasa_interaccion(f) is not None]
    mejores = sorted(con_tasa, key=tasa_interaccion, reverse=True)[:3]
    return {
        "publicados": len(filas), "medidos": len(medidas), "pendientes": pendientes,
        "por_pilar": agrupar("pilar"), "por_formato": agrupar("formato"), "por_idioma": agrupar("idioma"),
        "mejores": [{"id": f["id"], "tasa": round(tasa_interaccion(f), 4),
                     "impresiones": _num(f, "impresiones"), "primera_linea": f["primera_linea"]} for f in mejores],
        "minimo_por_grupo": minimo,
    }


def imprimir_resumen(r):
    print("Publicados: %d. Con métricas: %d." % (r["publicados"], r["medidos"]))
    if r["pendientes"]:
        print("\nPENDIENTES DE MEDIR (7 días o más sin métricas):")
        for p in r["pendientes"]:
            print("  #%s %s  %s" % (p["id"], p["fecha"], p["primera_linea"][:70]))
    for campo, titulo in (("por_pilar", "POR PILAR"), ("por_formato", "POR FORMATO"), ("por_idioma", "POR IDIOMA")):
        if not r[campo]:
            continue
        print("\n%s" % titulo)
        for g in r[campo]:
            tasa = "%.1f%%" % (g["mediana_tasa"] * 100) if g["mediana_tasa"] is not None else "sin dato"
            imp = _miles(int(g["mediana_impresiones"])) if g["mediana_impresiones"] is not None else "sin dato"
            nota = "" if g["muestra_suficiente"] else "  (menos de %d posts: no concluyas)" % r["minimo_por_grupo"]
            print("  %-34s %3d posts, mediana %s impresiones, interacción %s%s" % (g["grupo"][:34], g["posts"], imp, tasa, nota))
    if r["mejores"]:
        print("\nMAYOR TASA DE INTERACCIÓN")
        for m in r["mejores"]:
            print("  #%s %.1f%% sobre %s impresiones  %s" % (m["id"], m["tasa"] * 100, _miles(m["impresiones"]), m["primera_linea"][:60]))


# ---------------------------------------------------------------------------
# Línea de comandos
# ---------------------------------------------------------------------------

def main(argv=None):
    p = argparse.ArgumentParser(prog="linkedin.py", description="Herramienta de la skill /linkedin.")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("ruta", help="Imprime la carpeta de datos.")
    sub.add_parser("iniciar", help="Crea la carpeta de datos con las plantillas que falten.")
    sub.add_parser("estado", help="Qué hay en la carpeta de datos.")

    pr = sub.add_parser("revisar", help="Revisa un borrador (archivo .md o '-' para leer de la entrada).")
    pr.add_argument("archivo")
    pr.add_argument("--tipo", choices=sorted(LIMITES), default="post")
    pr.add_argument("--idioma", choices=["auto", "es", "en"], default="auto")
    pr.add_argument("--perfil", help="Perfil con la lista 'Nunca nombrar'. Por defecto, el de la carpeta de datos.")
    pr.add_argument("--marca", help="Perfil de marca. Por defecto, marca.md de la carpeta de datos.")
    pr.add_argument("--destino", choices=["perfil", "pagina"],
                    help="A nombre de quién sale. Por defecto, el 'destino' del borrador o 'perfil'.")
    pr.add_argument("--json", action="store_true")

    pe = sub.add_parser("exportar", help="Exporta los posts de página aprobados (CSV de Hootsuite o JSON).")
    pe.add_argument("--formato", choices=["hootsuite", "json"], default="hootsuite")
    pe.add_argument("--formato-fecha", choices=sorted(FORMATOS_FECHA), default="dmy",
                    help="El mismo que elijas al subir el archivo a Hootsuite.")
    pe.add_argument("--salida", help="Archivo de salida. Por defecto, en exportaciones/ de la carpeta de datos.")
    pe.add_argument("--marca", help="Perfil de marca. Por defecto, marca.md de la carpeta de datos.")

    pg = sub.add_parser("registrar", help="Anota un post publicado en registro.csv.")
    pg.add_argument("archivo", help="El borrador aprobado.")
    pg.add_argument("--url", default="")
    pg.add_argument("--fecha", help="AAAA-MM-DD. Por defecto, hoy.")
    pg.add_argument("--pilar")
    pg.add_argument("--formato")
    pg.add_argument("--idioma", choices=["es", "en"])

    pm = sub.add_parser("metricas", help="Anota las métricas de un post del registro.")
    pm.add_argument("id")
    for m in METRICAS:
        pm.add_argument("--" + m.replace("_", "-"), type=int, dest=m)
    pm.add_argument("--fecha", help="Día de la medición, AAAA-MM-DD. Por defecto, hoy.")

    ps = sub.add_parser("resumen", help="Resume las métricas del registro.")
    ps.add_argument("--json", action="store_true")
    ps.add_argument("--minimo", type=int, default=5, help="Posts por grupo antes de sacar conclusiones.")

    a = p.parse_args(argv)
    carpeta = carpeta_datos()

    if a.cmd == "ruta":
        print(carpeta)
    elif a.cmd == "iniciar":
        for nombre, estado in iniciar(carpeta):
            print("%-24s %s" % (nombre, estado))
        print("\nCarpeta de datos: %s" % carpeta)
    elif a.cmd == "estado":
        if not carpeta.exists():
            print("No existe %s. Corre: linkedin.py iniciar" % carpeta)
            return 1
        filas = leer_registro(carpeta / "registro.csv")
        r = resumir(filas)
        print("Carpeta de datos: %s" % carpeta)
        print("perfil.md               %s" % ("vacío" if plantilla_vacia(carpeta / "perfil.md") else "en uso"))
        print("marca.md                %s" % ("vacío" if plantilla_vacia(carpeta / "marca.md") else "en uso"))
        print("banco-de-historias.md   %s, %d historias" % (
            "vacío" if plantilla_vacia(carpeta / "banco-de-historias.md") else "en uso",
            contar_historias(carpeta / "banco-de-historias.md")))
        n_b = len(list((carpeta / "borradores").glob("*.md")))
        print("borradores/             %d archivo%s" % (n_b, "" if n_b == 1 else "s"))
        print("registro.csv            %d publicados, %d pendientes de medir" % (len(filas), len(r["pendientes"])))
        print("Nunca nombrar           %d en el perfil, %d en la marca" % (
            len(leer_nunca_nombrar(carpeta / "perfil.md")), len(leer_nunca_nombrar(carpeta / "marca.md"))))
    elif a.cmd == "revisar":
        contenido = sys.stdin.read() if a.archivo == "-" else Path(a.archivo).read_text(encoding="utf-8")
        meta, texto = separar_borrador(contenido) if a.tipo != "doc" else ({}, contenido)
        destino = a.destino or meta.get("destino") or "perfil"
        nunca, prohibidas, avisos = reglas_de_destino(carpeta, destino, a.perfil, a.marca)
        inf = revisar(texto, a.tipo, a.idioma, nunca, prohibidas=prohibidas, avisos_obligatorios=avisos)
        inf["destino"] = destino
        if a.json:
            print(json.dumps(inf, ensure_ascii=False, indent=2))
        else:
            imprimir_informe(inf)
        return 1 if inf["errores"] else 0
    elif a.cmd == "exportar":
        piezas, errores, avisos = preparar_exportacion(carpeta, marca=a.marca)
        for av in avisos:
            print("AVISO  " + av)
        if errores:
            for e in errores:
                print("ERROR  " + e)
            print("\nNo se exportó nada: corrige los errores y vuelve a correr el comando.")
            return 1
        if not piezas:
            print("No hay posts de página con estado: aprobado.")
            return 0
        sello = datetime.now().strftime("%Y%m%d-%H%M")
        if a.salida:
            salida = Path(a.salida)
        else:
            (carpeta / "exportaciones").mkdir(exist_ok=True)
            salida = carpeta / "exportaciones" / ("%s-%s.%s" % (
                a.formato, sello, "csv" if a.formato == "hootsuite" else "json"))
        if a.formato == "hootsuite":
            escribir_hootsuite(piezas, salida, a.formato_fecha)
        else:
            salida.write_text(json.dumps(piezas, ensure_ascii=False, indent=2), encoding="utf-8")
        print("%d post%s exportado%s a %s" % (len(piezas), "" if len(piezas) == 1 else "s",
                                             "" if len(piezas) == 1 else "s", salida))
    elif a.cmd == "registrar":
        fila = registrar(carpeta, a.archivo, a.url, a.fecha, a.pilar, a.formato, a.idioma)
        print("Registrado #%s del %s: %s" % (fila["id"], fila["fecha"], fila["primera_linea"][:70]))
        print("Mide en 7 días: linkedin.py metricas %s --impresiones N --reacciones N --comentarios N --compartidos N" % fila["id"])
    elif a.cmd == "metricas":
        valores = {m: getattr(a, m) for m in METRICAS}
        if all(v is None for v in valores.values()):
            p.error("pasa al menos una métrica, por ejemplo --impresiones 1200")
        fila = anotar_metricas(carpeta, a.id, valores, a.fecha)
        t = tasa_interaccion(fila)
        print("Post #%s actualizado.%s" % (fila["id"], " Interacción: %.1f%%." % (t * 100) if t is not None else ""))
    elif a.cmd == "resumen":
        r = resumir(leer_registro(carpeta / "registro.csv"), minimo=a.minimo)
        if a.json:
            print(json.dumps(r, ensure_ascii=False, indent=2))
        else:
            imprimir_resumen(r)
    return 0


if __name__ == "__main__":
    sys.exit(main())
