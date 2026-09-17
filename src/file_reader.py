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
