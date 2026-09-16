"""
MF-AI-Zero - v1.4.1 választervező (response_planner).

CÉL: a rendszer ELŐRE eldöntse, milyen TÍPUSÚ választ vár a kérdés (rövid
válasz, magyarázat, lépésekre bontott útmutató, lista, összegzés,
kód-segítség, döntés-segítség, laza beszélgetés), és ezt az INFORMÁCIÓT -
NEM új tartalmat - adja tovább a MEGLÉVŐ válaszláncnak:
  - a promptba egy rövid, natív "User:/AI:\\n\\n" formátumú instrukciós
    blokk kerül (lásd build_response_plan_prompt_context), UGYANOLYAN elv
    szerint, mint a knowledge/web/memory/conversation kontextus-blokkok;
  - a response_style.py apply_style()-ja a plan alapján FORMÁZZA (nem
    generálja újra!) a modell MÁR KÉSZ válaszát: lépésekre/listára tördeli
    a MEGLÉVŐ mondatokat, összegzésnél rövidebbre vágja, és a "túl rövid"
    küszöböt a válasz típusához igazítja.

FONTOS, amit ez a modul SZÁNDÉKOSAN NEM csinál:
  - NEM ír át tényt, NEM generál új tartalmat - a formázás (lépés-/
    listaszámozás, összegzés-vágás) a MEGLÉVŐ mondatok SZÖVEGÉT nem
    módosítja, csak elrendezi/válogatja őket.
  - NEM egy második nyelvmodell - egyszerű, kulcsszó-mintázat alapú
    osztályozó (ugyanaz a stílus, mint guard.detect_category).
  - ŐSZINTE KORLÁT: a kis, motivációs magyar szövegen tanított
    karakter-alapú LSTM nem egy instrukciókövető nagy LLM - a promptba
    illesztett "légy lépésenkénti/listás/tömör" instrukció csak egy
    GYENGE nudge a generáláshoz, a VALÓDI, megbízható hatás a
    response_style.py-beli, utólagos, determinisztikus formázásból jön.
    code_help/decision_help típusnál a modell tartalmilag nem tud
    érdemben kódot írni vagy komplex döntést segíteni - a felismerés itt
    elsősorban naplózási/jövőbeli bővítési célt szolgál.
"""

import re
import unicodedata

RESPONSE_TYPES = (
    "short_answer", "explanation", "step_by_step", "list", "summary",
    "code_help", "decision_help", "casual_chat",
)


def _normalize(text):
    text = (text or "").lower()
    decomposed = unicodedata.normalize("NFKD", text)
    without_accents = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", without_accents).strip()


# ---------------------------------------------------------------------------
# 1) Válasz-típus felismerés - kulcsszó-mintázat alapú, NEM ML.
#    Ellenőrzési sorrend számít az átfedések miatt (a specifikusabb
#    fordulatok előrébb állnak).
# ---------------------------------------------------------------------------

TYPE_PATTERNS = {
    "step_by_step": [
        "lepesekben", "lepesrol lepesre", "lepesenkent", "hogyan csinaljam",
        "mi a menete", "milyen lepesek", "lepeseket",
    ],
    "list": [
        "sorolj fel", "listazd", "milyen fajtai vannak", "adj egy listat",
        "sorold fel", "milyen tipusai vannak",
    ],
    "summary": [
        "foglald ossze", "foglaljad ossze", "roviden osszefoglalva",
        "egy mondatban", "tomoren", "dedd meg tomoren",
    ],
    "code_help": [
        "kodot", "kod hiba", "programozz", "fuggvenyt", "szintaxis", "debug",
        "programkod", "kodban",
    ],
    "decision_help": [
        "melyiket valasszam", "mit javasolsz", "segits dontani", "erdemes e",
        "melyik jobb", "melyiket ajanlod",
    ],
    "explanation": [
        "magyarazd el", "miert van az hogy", "mi az oka", "hogyan mukodik",
        "fejtsd ki", "mit jelent", "magyarazatot",
    ],
}

# Ellenőrzési sorrend - az első találat dönt.
TYPE_ORDER = ("step_by_step", "list", "summary", "code_help", "decision_help", "explanation")

CASUAL_HINTS = [
    "hogy vagy", "mizu", "szia", "mi ujsag", "hogy s mint", "helyes",
    "koszonom", "hali",
]

SHORT_ANSWER_MAX_WORDS = 4


def detect_response_type(text):
    """Visszaadja a felismert válasz-típust (RESPONSE_TYPES egyike).
    Sosem ad vissza None-t - ha semmi nem illik, "casual_chat"-re esik
    vissza (ez a legkevésbé tolakodó alapértelmezés)."""
    normalized = _normalize(text)
    if not normalized:
        return "casual_chat"
    # az írásjeleket (vessző, pont, stb.) eltávolítjuk az egyezés-
    # kereséshez, hogy pl. "az, hogy" is illeszkedjen a "az hogy"
    # mintázatra - a többszavas fordulatok szórendben/tagolásban
    # ingadozhatnak, az írásjel-eltérés ne akadályozza a felismerést.
    normalized = re.sub(r"[^\w\s]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()

    for response_type in TYPE_ORDER:
        if any(pattern in normalized for pattern in TYPE_PATTERNS[response_type]):
            return response_type

    if any(hint in normalized for hint in CASUAL_HINTS):
        return "casual_chat"

    words = normalized.split()
    if len(words) <= SHORT_ANSWER_MAX_WORDS:
        return "short_answer"
    return "casual_chat"


# ---------------------------------------------------------------------------
# 2) Típusonkénti instrukció-konfiguráció - CSAK formai elvárás, nem
#    tartalom.
# ---------------------------------------------------------------------------

RESPONSE_TYPE_CONFIG = {
    "short_answer":  {"target_length": "short",  "wants_steps": False, "wants_list": False, "wants_summary": False, "wants_casual_tone": False},
    "explanation":   {"target_length": "long",   "wants_steps": False, "wants_list": False, "wants_summary": False, "wants_casual_tone": False},
    "step_by_step":  {"target_length": "medium", "wants_steps": True,  "wants_list": False, "wants_summary": False, "wants_casual_tone": False},
    "list":          {"target_length": "medium", "wants_steps": False, "wants_list": True,  "wants_summary": False, "wants_casual_tone": False},
    "summary":       {"target_length": "short",  "wants_steps": False, "wants_list": False, "wants_summary": True,  "wants_casual_tone": False},
    "code_help":     {"target_length": "medium", "wants_steps": False, "wants_list": False, "wants_summary": False, "wants_casual_tone": False},
    "decision_help": {"target_length": "medium", "wants_steps": False, "wants_list": False, "wants_summary": False, "wants_casual_tone": False},
    "casual_chat":   {"target_length": "short",  "wants_steps": False, "wants_list": False, "wants_summary": False, "wants_casual_tone": True},
}

PLAN_DESCRIPTIONS = {
    "short_answer": "Adj rövid, közvetlen választ.",
    "explanation": "Fejtsd ki bővebben, magyarázd el részletesebben.",
    "step_by_step": "Bontsd lépésekre a választ.",
    "list": "Listaszerűen sorold fel a válasz elemeit.",
    "summary": "Adj rövid, tömör összegzést.",
    "code_help": "Segíts a technikai kérdésben, amennyire tudsz.",
    "decision_help": "Segíts mérlegelni a döntést.",
    "casual_chat": "Válaszolj közvetlen, beszélgetős hangnemben.",
}


def build_response_plan(user_text):
    """Visszaad egy dict-et: {"response_type","target_length",
    "wants_steps","wants_list","wants_summary","wants_casual_tone"}."""
    response_type = detect_response_type(user_text)
    config = RESPONSE_TYPE_CONFIG[response_type]
    return {"response_type": response_type, **config}


def build_response_plan_prompt_context(plan):
    """Rövid, natív "User:/AI:\\n\\n" formátumú instrukciós blokk a
    promptba - ugyanaz az elv, mint a többi kontextus-modulnál. ŐSZINTE
    KORLÁT: ez csak egy gyenge nudge a kis modellnek, a megbízható hatás
    a response_style.py utólagos formázásából jön (lásd modul-fejléc)."""
    if not plan:
        return ""
    description = PLAN_DESCRIPTIONS.get(plan.get("response_type"))
    if not description:
        return ""
    return f"User: Milyen legyen a válaszod stílusa?\nAI: {description}\n\n"
