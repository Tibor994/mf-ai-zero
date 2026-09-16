"""
MF-AI-Zero - v1.0 hosszú távú memória.

FONTOS, amit ez a modul SZÁNDÉKOSAN NEM csinál:
  - NEM tanul meg automatikusan mindent - egy sima kijelentés ("Szeretem a
    teát.") csak "memory_candidate"-ként jelölődik (naplózási célra), DE
    NEM kerül mentésre. Tényleges mentés KIZÁRÓLAG explicit útvonalon
    történik ("jegyezd meg, hogy ...", lásd detect_explicit_save()).
  - NEM nagy, komplex adatbázis - egyetlen, ember által is átolvasható
    JSON fájl (long_term_memory/memories.json), nincs külső DB-függőség.
  - NEM kever össze semmit a rövid (v0.9, memory.py) memóriával - az egy
    KÜLÖN modul, külön mechanizmus (folyamat-memóriában élő, csak az
    aktuális beszélgetés 1-2 utolsó váltása), ez pedig fájlba mentett,
    beszélgetések közötti, de KATEGORIZÁLT és VISSZAKERESHETŐ tényadat.

Amit CSINÁL:
  - save_memory()    - egy új memória mentése (kategória + szöveg +
                        metaadatok: id/created_at/updated_at/confidence/
                        source/active).
  - list_memories()  - memóriák listázása (kategória szerint szűrve,
                        alapból csak az aktívak).
  - search_memories()- egyszerű kulcsszó-egyezésen alapuló keresés (NINCS
                        embedding/AI - szándékosan egyszerű, átlátható).
  - delete_memory()  - alapból SOFT delete (active=False, updated_at
                        frissül) - visszakereshető marad, hogy miért lett
                        törölve, de válaszadáshoz többé nem kerül elő.
                        hard=True esetén véglegesen eltávolítja a rekordot.
  - detect_memory_candidate() - heurisztika: "ezt talán érdemes lenne
                        megjegyezni" - CSAK jelzés, nem ment semmit.
  - detect_explicit_save()    - heurisztika: a user KIFEJEZETTEN kérte a
                        mentést ("jegyezd meg...") - ez az EGYETLEN
                        útvonal, ami ténylegesen ír a store-ba.
  - retrieve_relevant()       - válaszadás ELŐTT hívható: legfeljebb
                        MAX_CONTEXT_MEMORIES (5) releváns, aktív memóriát
                        ad vissza a user aktuális üzenetéhez.
  - build_long_memory_prompt_context() - a visszakeresett memóriákból egy
                        rövid, natív "User:/AI:\\n\\n" formátumú
                        prompt-kontextust épít (ugyanaz az elv, mint a
                        v0.9 rövid memóriánál - ismerős szerkezet a kis
                        modellnek, nem hosszú nyers szöveg).

Minden fájlba-író/olvasó függvény elfogad egy opcionális `store_path`
paramétert - ez teszi lehetővé, hogy a tesztek IDEIGLENES fájlt
használjanak, ne az éles long_term_memory/memories.json-t szennyezzék be.
"""

import json
import os
import re
import unicodedata
import uuid
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LONG_MEMORY_DIR = os.path.join(BASE_DIR, "long_term_memory")
LONG_MEMORY_PATH = os.path.join(LONG_MEMORY_DIR, "memories.json")

VALID_CATEGORIES = (
    "user_preference", "user_fact", "project_fact", "current_goal", "correction",
)
DEFAULT_CATEGORY = "user_fact"

MAX_CONTEXT_MEMORIES = 5
MAX_FACT_CHARS = 60
MAX_CONTEXT_CHARS = 220


def _normalize(text):
    text = (text or "").lower()
    decomposed = unicodedata.normalize("NFKD", text)
    without_accents = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", without_accents).strip()


def _trim(text, limit):
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 3)].rstrip() + "..."


# ---------------------------------------------------------------------------
# Fájlba mentés / olvasás - egyszerű JSON lista, NEM adatbázis
# ---------------------------------------------------------------------------


def _load_all(store_path=None):
    store_path = store_path or LONG_MEMORY_PATH
    if not os.path.exists(store_path):
        return []
    try:
        with open(store_path, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def _save_all(records, store_path=None):
    store_path = store_path or LONG_MEMORY_PATH
    os.makedirs(os.path.dirname(store_path), exist_ok=True)
    with open(store_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# CRUD műveletek
# ---------------------------------------------------------------------------


def save_memory(category, text, confidence=1.0, source="explicit", store_path=None):
    """Ment egy új memóriát. Ha a category nem a VALID_CATEGORIES egyike,
    DEFAULT_CATEGORY-ra esik vissza (nem dob hibát - a category-találgatás
    eleve csak egy heurisztika, sosem szabad emiatt elveszíteni a mentést).
    Üres/whitespace-only szöveget NEM ment (visszaad None-t)."""
    text = (text or "").strip()
    if not text:
        return None
    if category not in VALID_CATEGORIES:
        category = DEFAULT_CATEGORY

    now = datetime.now().isoformat(timespec="seconds")
    record = {
        "id": uuid.uuid4().hex[:12],
        "category": category,
        "text": text,
        "created_at": now,
        "updated_at": now,
        "confidence": confidence,
        "source": source,
        "active": True,
    }
    records = _load_all(store_path)
    records.append(record)
    _save_all(records, store_path)
    return record


def list_memories(category=None, active_only=True, store_path=None):
    records = _load_all(store_path)
    if category is not None:
        records = [r for r in records if r.get("category") == category]
    if active_only:
        records = [r for r in records if r.get("active", True)]
    return records


def _shares_stem(word_a, word_b, min_prefix=4):
    """Durva, de egyszerű "tő-egyezés": a magyar toldalékolás (pl. "tea" /
    "teát" / "teával", "szeretem" / "szereti") miatt egy pontos szóegyezés
    túl szigorú lenne - itt elég, ha a két szó eleje egyezik legalább
    min(min_prefix, a rövidebb szó hossza) karakteren át."""
    common = 0
    for ca, cb in zip(word_a, word_b):
        if ca != cb:
            break
        common += 1
    threshold = min(min_prefix, len(word_a), len(word_b))
    return threshold > 0 and common >= threshold


def search_memories(query, category=None, active_only=True, limit=5, store_path=None):
    """Egyszerű kulcsszó-átfedésen alapuló keresés - NEM embedding/AI
    alapú, szándékosan átlátható és determinisztikus. Csak azokat a
    memóriákat adja vissza, amikkel van legalább egy közös szó(tő) - a
    2-3 karakteresnél rövidebb szavakat (névelők, kötőszavak) figyelmen
    kívül hagyjuk, mert ezek önmagukban nem jelentenek releváns egyezést."""
    query_words = [w for w in _normalize(query).split() if len(w) >= 3]
    if not query_words:
        return []
    candidates = list_memories(category=category, active_only=active_only, store_path=store_path)
    scored = []
    for record in candidates:
        text_words = [w for w in _normalize(record.get("text", "")).split() if len(w) >= 3]
        overlap = sum(1 for qw in query_words if any(_shares_stem(qw, tw) for tw in text_words))
        if overlap > 0:
            scored.append((overlap, record))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [record for _, record in scored[:limit]]


def delete_memory(memory_id, hard=False, store_path=None):
    """Alapból SOFT delete (active=False) - a rekord megmarad a fájlban,
    de list/search/retrieve többé nem adja vissza (active_only=True az
    alapértelmezés mindenhol). hard=True esetén a rekord véglegesen
    eltűnik a store-ból. Visszaadja, hogy talált-e ilyen id-t."""
    records = _load_all(store_path)
    found = False
    new_records = []
    for record in records:
        if record.get("id") == memory_id:
            found = True
            if hard:
                continue
            record = dict(record)
            record["active"] = False
            record["updated_at"] = datetime.now().isoformat(timespec="seconds")
        new_records.append(record)
    if found:
        _save_all(new_records, store_path)
    return found


# ---------------------------------------------------------------------------
# Heurisztikák: "érdemes megjegyezni" jelzés vs. explicit mentési parancs
# ---------------------------------------------------------------------------

CANDIDATE_PATTERNS = {
    "user_preference": ["szeretem", "nem szeretem", "utalom", "kedvelem", "a kedvencem", "imadom"],
    "current_goal": ["a celom", "azon dolgozom", "szeretnek elerni", "kovetkezo lepesem"],
    "correction": ["helyesbitek", "nem ugy van", "tevedtel", "javitsd ki", "nem ezt mondtam"],
    "project_fact": ["ez a projekt", "ez a rendszer", "ebben a repoban", "ez a kodbazis"],
    "user_fact": ["a nevem", "abban dolgozom", "abban lakom", "en egy", "foglalkozasom"],
}


def detect_memory_candidate(text):
    """Visszaad (candidate: bool, category: str|None) - CSAK JELZÉS,
    semmit nem ment. Az első illeszkedő kategória dönt."""
    normalized = _normalize(text)
    if not normalized:
        return False, None
    for category, keywords in CANDIDATE_PATTERNS.items():
        if any(kw in normalized for kw in keywords):
            return True, category
    return False, None


EXPLICIT_SAVE_PATTERNS = [
    r"jegyezd\s+meg",
    r"jegyezd\s+fel",
    r"ne\s+felejtsd\s+el",
    r"eml[ée]kezz\s+r[áa]",
    r"fontos\s+hogy\s+tudd",
]


def detect_explicit_save(text):
    """Visszaad (should_save: bool, extracted_text: str|None). Az
    extracted_text a trigger-kifejezés UTÁNI rész, megtisztítva a vezető
    írásjelektől/"hogy" szótól - EZ kerül ténylegesen mentésre, ha
    should_save=True. Ha a trigger után nem marad tartalmas szöveg,
    should_save=False (nincs mit menteni)."""
    text = text or ""
    for pattern in EXPLICIT_SAVE_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            continue
        remainder = text[match.end():]
        remainder = re.sub(r"^[\s,:-]+", "", remainder)
        remainder = re.sub(r"^hogy\b[\s,]*", "", remainder, flags=re.IGNORECASE)
        remainder = remainder.strip().rstrip(".!").strip()
        if remainder:
            return True, remainder
    return False, None


# ---------------------------------------------------------------------------
# Visszakeresés válaszadás előtt + prompt-kontextus építés
# ---------------------------------------------------------------------------


def retrieve_relevant(user_text, limit=5, store_path=None):
    """Legfeljebb MAX_CONTEXT_MEMORIES releváns, aktív memória - SOSEM
    több, még ha limit nagyobbat kérne is."""
    limit = max(0, min(limit, MAX_CONTEXT_MEMORIES))
    if limit == 0:
        return []
    return search_memories(user_text, active_only=True, limit=limit, store_path=store_path)


def build_long_memory_prompt_context(memories):
    """A visszakeresett memóriákból egy rövid, natív "User:/AI:\\n\\n"
    formátumú prompt-kontextust épít - ugyanaz az elv, mint a v0.9 rövid
    memóriánál (memory.py): a modell csak ismerős szerkezetű, RÖVID
    szöveget kap, nem nyers, hosszú adatdömpinget."""
    if not memories:
        return ""
    facts = [_trim(m.get("text", ""), MAX_FACT_CHARS) for m in memories[:MAX_CONTEXT_MEMORIES]]
    facts = [f for f in facts if f]
    if not facts:
        return ""
    joined = _trim("; ".join(facts), MAX_CONTEXT_CHARS)
    return f"User: Mit tudsz rólam eddig?\nAI: Eddig ezeket jegyeztem meg: {joined}.\n\n"


CATEGORY_LABELS = {
    "user_preference": "kedvelés",
    "user_fact": "tény",
    "project_fact": "projekt-tény",
    "current_goal": "cél",
    "correction": "javítás",
}
