"""
MF-AI-Zero - v1.1 saját tudásbázis (knowledge base).

FONTOS KÜLÖNBSÉG a v1.0 hosszú távú memóriától (long_term_memory.py):
  - long_term_memory  = a FELHASZNÁLÓRÓL/beszélgetésről megjegyzett dolgok
                        (preferencia, tény, cél, javítás) - "ki ő, mit
                        mondott".
  - knowledge_base     = ÁLTALÁNOS vagy PROJEKT-szintű tudásanyag, amit az
                        AI válaszadás előtt kereshet (később dokumentumok/
                        jegyzetek/szabályok is bekerülhetnek ide) - "mit
                        tudunk erről a témáról", függetlenül attól, ki
                        mondta.

A két modul emiatt SZÁNDÉKOSAN külön fájl, külön mappa, külön kapcsoló -
ahogy a rövid és hosszú memória is külön maradt (lásd memory.py vs
long_term_memory.py).

FONTOS, amit ez a modul SZÁNDÉKOSAN NEM csinál:
  - NEM tanul automatikusan a chatből - tudáselem KIZÁRÓLAG explicit
    save_knowledge() hívással kerül be (API/UI mentés), sosem a
    beszélgetés melléktermékeként.
  - NINCS automatikus internetes keresés - csak a már mentett, helyi JSON
    store-ban keres.
  - NEM külső adatbázis - egyetlen, ember által is átolvasható JSON fájl
    (knowledge_base/items.json).

Amit CSINÁL (ugyanaz az elv, mint long_term_memory.py-nál):
  - save_knowledge()    - egy új tudáselem mentése.
  - list_knowledge()    - listázás (kategória/tag szerint szűrve).
  - search_knowledge()  - egyszerű kulcsszó/tő-egyezésen alapuló keresés a
                        title+content+tags mezőkön.
  - delete_knowledge()  - alapból SOFT delete (active=False).
  - retrieve_relevant()       - válaszadás ELŐTT hívható: legfeljebb
                        MAX_CONTEXT_ITEMS (3) releváns, aktív tudáselemet
                        ad vissza.
  - build_knowledge_prompt_context() - a visszakeresett elemekből egy
                        rövid, natív "User:/AI:\\n\\n" formátumú
                        prompt-kontextust épít.

Minden fájlba-író/olvasó függvény elfogad egy opcionális `store_path`
paramétert - a tesztek ezt IDEIGLENES fájlra állítva futnak, az éles
knowledge_base/items.json-t nem érintik.
"""

import json
import os
import re
import unicodedata
import uuid
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KNOWLEDGE_DIR = os.path.join(BASE_DIR, "knowledge_base")
KNOWLEDGE_PATH = os.path.join(KNOWLEDGE_DIR, "items.json")

VALID_CATEGORIES = (
    "ai_project", "business", "training", "rules", "technical", "personal_notes", "other",
)
DEFAULT_CATEGORY = "other"

MAX_CONTEXT_ITEMS = 3
MAX_CONTENT_CHARS_IN_CONTEXT = 70
MAX_CONTEXT_CHARS = 220

CATEGORY_LABELS = {
    "ai_project": "AI-projekt",
    "business": "üzleti",
    "training": "tanítás",
    "rules": "szabály",
    "technical": "technikai",
    "personal_notes": "személyes jegyzet",
    "other": "egyéb",
}


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
    store_path = store_path or KNOWLEDGE_PATH
    if not os.path.exists(store_path):
        return []
    try:
        with open(store_path, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def _save_all(records, store_path=None):
    store_path = store_path or KNOWLEDGE_PATH
    os.makedirs(os.path.dirname(store_path), exist_ok=True)
    with open(store_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# CRUD műveletek
# ---------------------------------------------------------------------------


def save_knowledge(title, content, category=DEFAULT_CATEGORY, tags=None,
                    confidence=1.0, source="manual", store_path=None):
    """Ment egy új tudáselemet. content kötelező (üres esetén None-t ad
    vissza, nem ment); title üres esetén a content elejéből képződik.
    Érvénytelen category esetén DEFAULT_CATEGORY-ra esik vissza (nem dob
    hibát)."""
    content = (content or "").strip()
    if not content:
        return None
    title = (title or "").strip() or _trim(content, 60)
    if category not in VALID_CATEGORIES:
        category = DEFAULT_CATEGORY
    tags = sorted({t.strip() for t in (tags or []) if t and t.strip()})

    now = datetime.now().isoformat(timespec="seconds")
    record = {
        "id": uuid.uuid4().hex[:12],
        "title": title,
        "content": content,
        "category": category,
        "tags": tags,
        "source": source,
        "created_at": now,
        "updated_at": now,
        "confidence": confidence,
        "active": True,
    }
    records = _load_all(store_path)
    records.append(record)
    _save_all(records, store_path)
    return record


def list_knowledge(category=None, tag=None, active_only=True, store_path=None):
    records = _load_all(store_path)
    if category is not None:
        records = [r for r in records if r.get("category") == category]
    if tag is not None:
        records = [r for r in records if tag in (r.get("tags") or [])]
    if active_only:
        records = [r for r in records if r.get("active", True)]
    return records


def _shares_stem(word_a, word_b, min_prefix=4):
    """Ugyanaz a durva "tő-egyezés", mint long_term_memory.py-ban - a
    magyar toldalékolás miatt egy pontos szóegyezés túl szigorú lenne."""
    common = 0
    for ca, cb in zip(word_a, word_b):
        if ca != cb:
            break
        common += 1
    threshold = min(min_prefix, len(word_a), len(word_b))
    return threshold > 0 and common >= threshold


def _searchable_text(record):
    tags_text = " ".join(record.get("tags") or [])
    return f"{record.get('title', '')} {record.get('content', '')} {tags_text}"


def search_knowledge(query, category=None, active_only=True, limit=5, store_path=None):
    """Egyszerű kulcsszó/tő-egyezésen alapuló keresés a title+content+tags
    mezőkön - NEM embedding/AI alapú, szándékosan átlátható."""
    query_words = [w for w in _normalize(query).split() if len(w) >= 3]
    if not query_words:
        return []
    candidates = list_knowledge(category=category, active_only=active_only, store_path=store_path)
    scored = []
    for record in candidates:
        text_words = [w for w in _normalize(_searchable_text(record)).split() if len(w) >= 3]
        overlap = sum(1 for qw in query_words if any(_shares_stem(qw, tw) for tw in text_words))
        if overlap > 0:
            scored.append((overlap, record))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [record for _, record in scored[:limit]]


def delete_knowledge(item_id, hard=False, store_path=None):
    """Alapból SOFT delete (active=False) - lásd long_term_memory.py
    delete_memory() ugyanezen elve. hard=True esetén véglegesen törli."""
    records = _load_all(store_path)
    found = False
    new_records = []
    for record in records:
        if record.get("id") == item_id:
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
# Visszakeresés válaszadás előtt + prompt-kontextus építés
# ---------------------------------------------------------------------------


def retrieve_relevant(query, limit=3, store_path=None):
    """Legfeljebb MAX_CONTEXT_ITEMS (3) releváns, aktív tudáselem - SOSEM
    több, még ha limit nagyobbat kérne is. Ha nincs releváns találat,
    üres listát ad vissza - a hívó ilyenkor NEM erőltet semmit."""
    limit = max(0, min(limit, MAX_CONTEXT_ITEMS))
    if limit == 0:
        return []
    return search_knowledge(query, active_only=True, limit=limit, store_path=store_path)


def build_knowledge_prompt_context(items):
    """A visszakeresett tudáselemekből egy rövid, natív
    "User:/AI:\\n\\n" formátumú prompt-kontextust épít - ugyanaz az elv,
    mint a rövid/hosszú memóriánál: ismerős szerkezet a kis modellnek,
    nem hosszú, nyers szövegdömping."""
    if not items:
        return ""
    facts = [_trim(item.get("content", ""), MAX_CONTENT_CHARS_IN_CONTEXT) for item in items[:MAX_CONTEXT_ITEMS]]
    facts = [f for f in facts if f]
    if not facts:
        return ""
    joined = _trim("; ".join(facts), MAX_CONTEXT_CHARS)
    return f"User: Van erről valamilyen tudásod?\nAI: Igen, ezt tudom róla: {joined}.\n\n"
