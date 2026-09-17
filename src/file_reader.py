"""
MF-AI-Zero - v1.6 fájlfeltöltés + fájlolvasás (file_reader).

CÉL: a user tölthessen fel egy szöveg-alapú fájlt, amit az AI a
válaszadáshoz kontextusként használhat - A FELTÖLTÉS MAGA az engedély
(nincs külön jóváhagyó felugró ablak), DE ez a modul KIZÁRÓLAG a
ténylegesen feltöltött fájl TARTALMÁT dolgozza fel, amit a hívó fél
(web/app.py) egy multipart file-upload kérésből ad át neki (nyers
bájtokként) - SOHA nem nyúl a szerver fájlrendszeréhez, és SOHA nem kap/
használ fájlrendszer-elérési utat paraméterként.

FONTOS BIZTONSÁGI SZABÁLYOK (mind szándékos, dokumentált korlátozás):
  - NEM ír a lemezre - a feltöltött fájl tartalma KIZÁRÓLAG a szerver
    folyamat memóriájában él (ugyanaz az elv, mint a v0.9 rövid memória
    `history`-jánál vagy a v1.3 beszélgetés-állapotnál) - emiatt fájlnév/
    path-alapú lemez-hozzáférési kockázat STRUKTURÁLISAN sem merülhet
    fel, mert nincs is "olvasd be ezt az útvonalat" funkció.
  - NEM böngészi a gépet, NEM fogad el semmilyen fájlrendszer-elérési
    utat - csak a ténylegesen feltöltött bájtokat dolgozza fel.
  - NEM szerkeszt fájlt - v1.6-ban KIZÁRÓLAG olvasás.
  - Kiterjesztés-alapú ÉS kulcsszó-alapú tiltólista védi a
    .env/titok/kulcs/token/.git/rendszerfájl jellegű feltöltéseket, még
    akkor is, ha a kiterjesztésük véletlenül engedélyezett lenne.
  - Fájlméret-korlát (MAX_FILE_SIZE) és bináris-tartalom felismerés
    (érvénytelen UTF-8 vagy NUL-bájt -> elutasítva) - v1.6-ban NEM
    próbál bináris/kép/hang tartalmat értelmezni.
  - A file_summary/kontextus-kivonat SOSEM kerül automatikusan hosszú
    távú memóriába vagy tudásbázisba - ahhoz külön, KÉSŐBBI, explicit
    lépés kell (lásd to_knowledge_candidate() - ez is csak JAVASOL,
    nem ment, ugyanaz az elv, mint web_research.to_knowledge_candidates()).
"""

import json
import os
import re
import unicodedata
import uuid
from datetime import datetime

ALLOWED_EXTENSIONS = {".txt", ".md", ".json", ".jsonl", ".csv", ".py", ".js", ".html", ".css", ".log"}
MAX_FILE_SIZE = 200_000   # bájt (~200 KB) - kis, szöveg-alapú fájlokra szánva
MAX_STORED_FILES = 5      # egy "megosztott beszélgetésben" legfeljebb ennyi fájl él egyszerre
MAX_SUMMARY_CHARS = 300
MAX_PROMPT_EXCERPT_CHARS = 280
MAX_CANDIDATE_CHARS = 600
MAX_ANSWER_EXCERPT_CHARS = 300

# v1.7.2 - determinisztikus fájl-leírás kiterjesztésenként (lásd
# build_file_answer()). Csak a ténylegesen támogatott (ALLOWED_EXTENSIONS)
# kiterjesztésekre van bejegyzés - a fallback szöveg minden más esetre.
FILE_TYPE_DESCRIPTIONS = {
    ".html": "Ez egy HTML dokumentum (weboldal-vázlat).",
    ".css": "Ez egy CSS stíluslap (kinézet-leírás).",
    ".js": "Ez egy JavaScript fájl (kód).",
    ".py": "Ez egy Python szkript (kód).",
    ".json": "Ez strukturált JSON adat.",
    ".jsonl": "Ez soronkénti JSON (JSONL) adat.",
    ".csv": "Ez vesszővel tagolt (CSV) adattábla.",
    ".md": "Ez egy Markdown dokumentum.",
    ".log": "Ez egy naplófájl (log).",
    ".txt": "Ez egy egyszerű szöveges fájl.",
}

# v1.7.2 - determinisztikus (NEM AI-alapú) felismerés: a user üzenete a
# FELTÖLTÖTT FÁJLRÓL kérdez-e. Két feltétel EGYÜTT: (1) a szöveg említi a
# fájlt/dokumentumot, (2) tartalmaz egy kérdés/tartalom-kérő szót. Csak
# ekkor kapcsol be a guard.py-beli determinisztikus fájl-válasz - minden
# más esetben a normál (LSTM-alapú) válaszadás fut, változatlanul.
FILE_MENTION_MARKERS = ["fajl", "dokumentum"]
FILE_QUESTION_MARKERS = [
    "mit", "mi ", "mi?", "milyen", "mirol", "tartalmaz", "tartalma",
    "osszefoglal", "ossze", "elemez", "reszlet", "mutasd", "miota", "miben",
]

# Kulcsszavak, amik miatt egy fájlnevet MINDIG elutasítunk, FÜGGETLENÜL a
# kiterjesztéstől - ".env", "secret.txt", "api_key.json", "id_rsa.txt" stb.
BLOCKED_NAME_PATTERNS = [
    "env", "secret", "titok", "kulcs", "token", "jelszo", "password",
    "credential", "private_key", "id_rsa", ".git", "wallet", "apikey", "api_key",
]


def _normalize(text):
    text = (text or "").lower()
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def _trim(text, limit):
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 3)].rstrip() + "..."


class FileValidationError(Exception):
    """Egy feltöltött fájl elutasításának oka - a `code` géppel is
    értelmezhető (a hívó ebből választ kulturált hibaüzenetet/UI-jelzést),
    a `message` már emberi olvasásra kész magyar szöveg."""

    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


def sanitize_display_name(raw_name):
    """A kliens által küldött fájlnevet KIZÁRÓLAG megjelenítésre tisztítja
    - eltávolítja az esetleges path-komponenseket (os.path.basename,
    mindkét irányú perjellel) és a nem nyomtatható karaktereket. Ezt a
    nevet SOSEM használjuk lemez-elérési útként, csak címkeként."""
    raw_name = (raw_name or "").strip().replace("\\", "/")
    name = os.path.basename(raw_name)
    name = "".join(ch for ch in name if ch.isprintable())
    name = name.strip().lstrip(".")  # ne kezdődhessen rejtett-fájlként (pl. "..foo")
    return name[:150] or "feltoltott_fajl"


def is_extension_allowed(filename):
    _, ext = os.path.splitext(filename.lower())
    return ext in ALLOWED_EXTENSIONS


def is_name_blocked(filename):
    normalized = _normalize(filename)
    normalized = re.sub(r"[^a-z0-9.]+", "", normalized)
    return any(pattern in normalized for pattern in BLOCKED_NAME_PATTERNS)


def looks_binary(raw_bytes):
    """Nagyon egyszerű bináris-felismerés: NUL-bájt VAGY érvénytelen
    UTF-8 -> biztosan nem az a "sima szöveg", amit v1.6-ban kezelni
    tudunk."""
    if b"\x00" in raw_bytes:
        return True
    try:
        raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return True
    return False


def validate_upload(filename, raw_bytes):
    """Elvégzi az ÖSSZES biztonsági ellenőrzést egy feltöltött fájlon.
    Sikeres esetben a megtisztított (path nélküli) megjelenítendő nevet
    adja vissza; hiba esetén FileValidationError-t dob."""
    display_name = sanitize_display_name(filename)

    if not raw_bytes:
        raise FileValidationError("empty_file", "A fájl üres.")
    if len(raw_bytes) > MAX_FILE_SIZE:
        raise FileValidationError(
            "file_too_large",
            f"A fájl túl nagy ({len(raw_bytes):,} bájt, max. {MAX_FILE_SIZE:,} bájt engedélyezett).",
        )
    if not is_extension_allowed(display_name):
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
        raise FileValidationError(
            "unsupported_type",
            f"Nem támogatott fájltípus. Támogatott kiterjesztések: {allowed}.",
        )
    if is_name_blocked(display_name):
        raise FileValidationError(
            "blocked_filename",
            "Ez a fájlnév érzékeny adatra utal (pl. .env/titok/kulcs/token/.git), "
            "ezért biztonsági okból nem olvasom be.",
        )
    if looks_binary(raw_bytes):
        raise FileValidationError(
            "binary_not_supported",
            "A fájl bináris tartalmúnak tűnik - egyelőre csak szöveges fájlokat tudok beolvasni.",
        )

    return display_name


def read_text(raw_bytes):
    return raw_bytes.decode("utf-8", errors="replace")


def build_file_summary(display_name, text):
    """Rövid, DETERMINISZTIKUS (NEM AI-generált) összefoglaló: sor-/
    karakterszám + egy rövid tartalmi részlet."""
    line_count = text.count("\n") + (1 if text and not text.endswith("\n") else 0)
    char_count = len(text)
    preview = _trim(" ".join(text.split()), MAX_SUMMARY_CHARS)
    return f"{display_name}: {line_count} sor, {char_count} karakter. Részlet: \"{preview}\""


def build_file_record(filename, raw_bytes):
    """Validál, beolvas és összeállít egy fájl-rekordot. Ez a rekord
    KIZÁRÓLAG a hívó (web/app.py) folyamat-memóriájában él - a modul maga
    sosem ír fájlt lemezre. FileValidationError-t dob, ha a fájl bármelyik
    biztonsági ellenőrzésen elbukik."""
    display_name = validate_upload(filename, raw_bytes)
    text = read_text(raw_bytes)
    _, ext = os.path.splitext(display_name.lower())
    now = datetime.now().isoformat(timespec="seconds")
    return {
        "id": uuid.uuid4().hex[:12],
        "name": display_name,
        "type": ext,
        "size": len(raw_bytes),
        "content": text,
        "summary": build_file_summary(display_name, text),
        "uploaded_at": now,
    }


def build_file_prompt_context(file_record):
    """Rövid, natív "User:/AI:\\n\\n" formátumú prompt-kontextus - ugyanaz
    az elv, mint a többi kontextus-modulnál (memory.py, knowledge_base.py,
    web_research.py stb.): a modell csak egy RÖVID kivonatot kap, nem a
    teljes fájltartalmat."""
    if not file_record:
        return ""
    excerpt = _trim(" ".join((file_record.get("content") or "").split()), MAX_PROMPT_EXCERPT_CHARS)
    if not excerpt:
        return ""
    name = file_record.get("name", "a feltöltött fájl")
    return f"User: Mi van a feltöltött fájlban ({name})?\nAI: Ebben van: {excerpt}\n\n"


def is_file_question(text):
    """Determinisztikus, kulcsszó-alapú felismerés: a user szövege a
    feltöltött fájlról/dokumentumról kérdez-e. NEM AI-alapú - ugyanaz az
    elv, mint a többi trigger-felismerőnél (memory.detect_followup,
    conversation_manager.detect_context_need): whitelist-alapú, olcsó,
    determinisztikus, könnyen tesztelhető. Csak akkor True, ha a szöveg
    EGYÜTT tartalmaz egy fájl-említést ÉS egy kérdés/tartalom-kérő szót -
    így egy sima "Szia!" vagy egy fájlt nem is említő kérdés sosem
    kapcsolja be a hívó fél determinisztikus fájl-válaszát."""
    normalized = _normalize(text)
    if not any(marker in normalized for marker in FILE_MENTION_MARKERS):
        return False
    return any(marker in normalized for marker in FILE_QUESTION_MARKERS)


def describe_file_type(ext):
    return FILE_TYPE_DESCRIPTIONS.get((ext or "").lower(), "Ez egy szöveges fájl.")


# ---------------------------------------------------------------------------
# v1.7.3 - fájltípusonkénti, DETERMINISZTIKUS (kizárólag reguláris
# kifejezésekkel/string-műveletekkel dolgozó, NEM AI-alapú) tartalom-
# elemzés. Ezek a függvények SOSEM "találnak ki" semmit - csak azt
# jelentik, amit ténylegesen megtalálnak a szövegben; ha semmit nem
# találnak, a hívó (a *_summary függvények) ezt őszintén jelzik.
# ---------------------------------------------------------------------------

_HTML_TAG_TEXT_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
_HTML_HEADING_RE = re.compile(r"<h[1-3][^>]*>(.*?)</h[1-3]>", re.IGNORECASE | re.DOTALL)
_HTML_TAG_STRIP_RE = re.compile(r"<[^>]+>")

_HTML_FEATURE_PATTERNS = [
    ("stylesheet", re.compile(r"<style[\s>]|rel=[\"']stylesheet[\"']", re.IGNORECASE), "CSS-stílus"),
    ("script", re.compile(r"<script[\s>]", re.IGNORECASE), "JavaScript-kód"),
    ("form", re.compile(r"<form[\s>]", re.IGNORECASE), "űrlap"),
    ("button", re.compile(r"<button[\s>]", re.IGNORECASE), "gomb"),
    ("canvas", re.compile(r"<canvas[\s>]", re.IGNORECASE), "canvas (grafikus terület)"),
    ("nav", re.compile(r"<nav[\s>]", re.IGNORECASE), "navigáció"),
    ("img", re.compile(r"<img[\s>]", re.IGNORECASE), "kép"),
]


def analyze_html(content):
    title_match = _HTML_TAG_TEXT_RE.search(content)
    title = None
    if title_match:
        title = " ".join(_HTML_TAG_STRIP_RE.sub(" ", title_match.group(1)).split())[:120] or None

    headings = []
    for match in _HTML_HEADING_RE.finditer(content):
        text = " ".join(_HTML_TAG_STRIP_RE.sub(" ", match.group(1)).split())
        if text:
            headings.append(text[:80])
        if len(headings) >= 5:
            break

    features = [label for _, pattern, label in _HTML_FEATURE_PATTERNS if pattern.search(content)]
    return {"title": title, "headings": headings, "features": features}


def _summarize_html(content):
    info = analyze_html(content)
    sentences = ["Ez egy weboldalnak (HTML dokumentumnak) tűnik."]
    if info["title"]:
        sentences.append(f"A címe alapján valószínűleg \"{info['title']}\" a neve vagy a témája.")
    if info["headings"]:
        sentences.append("Felismerhető fő részek/címsorok: " + "; ".join(info["headings"]) + ".")
    if info["features"]:
        sentences.append("Tartalmaz: " + ", ".join(info["features"]) + ".")
    if "űrlap" in info["features"] and "gomb" in info["features"]:
        sentences.append("Ez alapján valószínűleg interakcióra/adatbekérésre (pl. űrlap kitöltésére) szolgálhat.")
    elif "canvas (grafikus terület)" in info["features"]:
        sentences.append("A canvas elem alapján lehet, hogy grafikus vagy játék jellegű tartalom.")
    elif not info["title"] and not info["headings"] and not info["features"]:
        sentences.append("Nagyon egyszerű, kevés felismerhető elemmel - nem tudok többet biztosan mondani róla.")
    return " ".join(sentences)


_CSS_SELECTOR_RE = re.compile(r"([.#]?[\w-]+(?:[.#][\w-]+)*)\s*\{")
_CSS_MEDIA_RE = re.compile(r"@media", re.IGNORECASE)
_CSS_COLOR_RE = re.compile(r"(?:^|[\s;{])(color|background(?:-color)?)\s*:\s*([^;}]+)", re.IGNORECASE)


def analyze_css(content):
    selectors = _CSS_SELECTOR_RE.findall(content)
    return {
        "selector_count": len(selectors),
        "sample_selectors": selectors[:5],
        "has_media": bool(_CSS_MEDIA_RE.search(content)),
        "color_count": len(_CSS_COLOR_RE.findall(content)),
    }


def _summarize_css(content):
    info = analyze_css(content)
    if info["selector_count"] == 0:
        return "Ez egy CSS stíluslap, de nem találtam benne egyértelmű stílusszabályt."
    sentences = [f"Ez egy CSS stíluslap, {info['selector_count']} stílusszabályt találtam benne."]
    if info["sample_selectors"]:
        sentences.append("Néhány felismert szelektor: " + ", ".join(info["sample_selectors"]) + ".")
    if info["has_media"]:
        sentences.append("Reszponzív (@media) szabályokat is tartalmaz.")
    if info["color_count"]:
        sentences.append(f"{info['color_count']} szín/háttérszín-beállítást találtam benne.")
    return " ".join(sentences)


_JS_FUNCTION_RE = re.compile(r"function\s+([A-Za-z_$][\w$]*)\s*\(")
_JS_ARROW_RE = re.compile(r"(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?\(")
_JS_EVENT_RE = re.compile(r"addEventListener\(\s*[\"']([\w-]+)[\"']")
_JS_API_PATTERNS = ["fetch(", "XMLHttpRequest", "axios", "$.ajax"]


def analyze_js(content):
    functions = list(dict.fromkeys(_JS_FUNCTION_RE.findall(content) + _JS_ARROW_RE.findall(content)))
    events = list(dict.fromkeys(_JS_EVENT_RE.findall(content)))
    apis = [p.rstrip("(") for p in _JS_API_PATTERNS if p in content]
    return {"functions": functions, "events": events, "apis": apis}


def _summarize_js(content):
    info = analyze_js(content)
    if info["functions"]:
        sentences = [f"Ez egy JavaScript fájl, {len(info['functions'])} felismerhető függvénnyel: "
                     + ", ".join(info["functions"][:6]) + "."]
    else:
        sentences = ["Ez egy JavaScript fájl, de nem találtam benne egyértelműen elnevezett függvényt."]
    if info["events"]:
        sentences.append("Eseménykezelőket is tartalmaz: " + ", ".join(info["events"][:6]) + ".")
    if info["apis"]:
        sentences.append("API-hívásra utaló mintát is találtam benne (" + ", ".join(info["apis"]) + ").")
    return " ".join(sentences)


_PY_DEF_RE = re.compile(r"^\s*def\s+([A-Za-z_]\w*)\s*\(", re.MULTILINE)
_PY_CLASS_RE = re.compile(r"^\s*class\s+([A-Za-z_]\w*)", re.MULTILINE)
_PY_IMPORT_RE = re.compile(r"^\s*(?:import|from)\s+([\w.]+)", re.MULTILINE)
_PY_ROUTE_RE = re.compile(r"@\w+\.route\(\s*[\"']([^\"']+)[\"']")


def analyze_python(content):
    return {
        "functions": _PY_DEF_RE.findall(content),
        "classes": _PY_CLASS_RE.findall(content),
        "imports": list(dict.fromkeys(_PY_IMPORT_RE.findall(content))),
        "routes": _PY_ROUTE_RE.findall(content),
    }


def _summarize_python(content):
    info = analyze_python(content)
    if not info["functions"] and not info["classes"]:
        return "Ez egy Python szkript, de nem találtam benne egyértelműen elnevezett függvényt vagy osztályt."
    sentences = ["Ez egy Python szkript."]
    if info["classes"]:
        sentences.append("Felismert osztályok: " + ", ".join(info["classes"][:6]) + ".")
    if info["functions"]:
        sentences.append("Felismert függvények: " + ", ".join(info["functions"][:8]) + ".")
    if info["routes"]:
        sentences.append("Webes végpontokat (route) is tartalmaz: " + ", ".join(info["routes"][:5]) + ".")
    if info["imports"]:
        sentences.append("Használt modulok: " + ", ".join(info["imports"][:6]) + ".")
    return " ".join(sentences)


def analyze_json(content):
    try:
        data = json.loads(content)
    except (ValueError, TypeError):
        return {"valid": False}
    if isinstance(data, dict):
        return {"valid": True, "kind": "objektum", "keys": list(data.keys()), "count": len(data)}
    if isinstance(data, list):
        return {"valid": True, "kind": "lista", "keys": [], "count": len(data)}
    return {"valid": True, "kind": "egyszerű érték", "keys": [], "count": 0}


def _summarize_json(content):
    info = analyze_json(content)
    if not info["valid"]:
        return ("Ez egy JSON fájl, de a tartalma nem elemezhető szabályos JSON-ként "
                "- lehet, hogy hiányos vagy hibás.")
    if info["kind"] == "objektum":
        keys_text = ", ".join(info["keys"][:8]) if info["keys"] else "(nincs kulcs)"
        return f"Ez egy JSON fájl, egy objektumot ír le {info['count']} kulccsal: {keys_text}."
    if info["kind"] == "lista":
        return f"Ez egy JSON fájl, egy {info['count']} elemű listát tartalmaz."
    return "Ez egy JSON fájl, egy egyszerű (nem objektum/lista) értéket tartalmaz."


_MD_HEADING_RE = re.compile(r"^#{1,6}\s*(.+)$", re.MULTILINE)


def analyze_markdown(content):
    headings = [h.strip() for h in _MD_HEADING_RE.findall(content)]
    return {"headings": headings, "count": len(headings)}


def _summarize_markdown(content):
    info = analyze_markdown(content)
    if not info["headings"]:
        return "Ez egy Markdown dokumentum, de nem találtam benne címsorokat."
    return (f"Ez egy Markdown dokumentum {info['count']} címsorral: "
            + ", ".join(info["headings"][:6]) + ".")


_TYPE_SUMMARIZERS = {
    ".html": _summarize_html,
    ".css": _summarize_css,
    ".js": _summarize_js,
    ".py": _summarize_python,
    ".json": _summarize_json,
    ".md": _summarize_markdown,
}


def build_file_answer(file_record):
    """Determinisztikus (NEM a kis LSTM által generált) válasz a feltöltött
    fájlról - akkor hívjuk, amikor is_file_question()==True és van aktív
    fájl, VAGY amikor a guard.py kimeneti minőség-őre elutasítja a modell
    válaszát és van aktív fájl (lásd guard.py). Mindig a TÉNYLEGES
    fájltartalomból (reguláris kifejezéses elemzésből) és metaadatokból
    épül fel, sosem "kitalál" semmit - ha bizonytalan/üres a tartalom,
    ezt őszintén jelzi, nem generál helyette kitalált szöveget."""
    if not file_record:
        return "Jelenleg nincs aktív feltöltött fájl, amiről beszélhetnék."

    name = file_record.get("name", "a feltöltött fájl")
    ext = (file_record.get("type") or "").lower()
    size = file_record.get("size", 0)
    content = file_record.get("content") or ""

    if not content.strip():
        return f"A feltöltött fájl (\"{name}\") tartalma üresnek tűnik - nincs miről beszélnem."

    summarizer = _TYPE_SUMMARIZERS.get(ext)
    if summarizer:
        content_summary = summarizer(content)
    else:
        content_summary = describe_file_type(ext)

    size_text = f"{size:,}".replace(",", " ")
    excerpt = _trim(" ".join(content.split()), MAX_ANSWER_EXCERPT_CHARS)

    parts = [
        "A feltöltött fájl alapján ezt látom:",
        content_summary,
        f"A fájl neve \"{name}\", mérete {size_text} bájt.",
    ]
    if excerpt:
        parts.append(f"Tartalmából egy részlet: \"{excerpt}\"")
    return " ".join(parts)


def to_knowledge_candidate(file_record):
    """Ugyanaz az elv, mint web_research.to_knowledge_candidates(): CSAK
    JAVASOL egy tudásbázis-formátumú jelöltet, NEM ment automatikusan. A
    tényleges mentés egy KÜLÖN, explicit lépés (későbbi kör/UI-akció) -
    lásd knowledge_base.save_knowledge()."""
    if not file_record:
        return None
    return {
        "title": file_record.get("name", "Feltöltött fájl"),
        "content": _trim(file_record.get("content") or "", MAX_CANDIDATE_CHARS),
        "category": "technical",
        "tags": [file_record.get("type", "").lstrip(".")] if file_record.get("type") else [],
        "source": f"file:{file_record.get('name', 'ismeretlen')}",
    }


def public_file_record(file_record):
    """A fájl-rekord "publikus" (API-válaszba/naplóba szánt) nézete - a
    TELJES tartalom (content) NEM kerül bele, csak a metaadat+összefoglaló."""
    if not file_record:
        return None
    return {k: v for k, v in file_record.items() if k != "content"}
