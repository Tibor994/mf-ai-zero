"""
MF-AI-Zero - v0.9 rövid memória.

FONTOS, amit ez a modul SZÁNDÉKOSAN NEM csinál:
  - NEM hosszú távú memória (nincs fájlba mentett, beszélgetések közötti
    "emlékezet" - minden az aktuális folyamat memóriájában él, a program
    leállásával elvész).
  - NEM személyes adatbázis (nincs user-azonosítás, nincs tárolt profil).
  - NEM tanul automatikusan a memóriából (a learning_log csak naplóz,
    ahogy eddig is - lásd learning_log.py).
  - NEM ad a modellnek hosszú, nyers chat historyt - még akkor sem, ha a
    memória aktiválódik, LEGFELJEBB az UTOLSÓ egy váltást illeszti a
    promptba, tömörítve.

Amit CSINÁL: ha a user üzenete egyértelműen egy korábbi váltásra utal
vissza ("folytasd", "amit mondtam", "előző", vagy egy rövid, névmásos
("az", "ez") followup kérdés), egy rövid (max. 1-3 mondatnyi) összefoglalót
készít az utolsó váltásból - MINDEN MÁS esetben nem csinál semmit, a
válasz pontosan úgy megy tovább, mint a v0.9-guard rétegben eddig.

Ez a modul NEM tudja, mi a router/guard - önállóan tesztelhető, a
guard.py hívja meg és illeszti a döntését a saját folyamatába.
"""

import re
import unicodedata

MAX_HISTORY_TURNS = 2     # legfeljebb ennyi korábbi váltást nézünk meg a summary-hoz
MAX_SUMMARY_CHARS = 220   # kb. 1-3 rövid mondatnyi limit a naplózott summary-hoz
MAX_PROMPT_USER_CHARS = 80
MAX_PROMPT_REPLY_CHARS = 120
WEAK_MAX_WORDS = 5        # ennél rövidebb üzenetnél számít a puszta "az"/"ez" is


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


# Egyértelmű, explicit visszautaló fordulatok - a csoport MINDEN elemének
# (részszövegként, bármilyen sorrendben) szerepelnie kell a normalizált
# szövegben. Ez toleránsabb a magyar toldalékolásra/szórendre, mint egy
# fix mondat-egyezés.
STRONG_KEYWORD_GROUPS = [
    ("amit", "mondtam"),
    ("amit", "irtam"),
    ("folytasd",),
    ("folytassuk",),
    ("elozo",),
    ("korabban", "mondtam"),
    ("mint", "az", "elobb"),
    ("visszaterve",),
]

# Rövid, névmásos followup - CSAK akkor számít, ha az üzenet rövid
# (max. WEAK_MAX_WORDS szó), különben az "az"/"ez" túl gyakori magyar
# szó ahhoz, hogy önmagában visszautalást jelentsen (pl. "Mi AZ
# életkorod?" - itt az "az" egyszerű névelő, nem visszautalás).
WEAK_DEICTIC_WORDS = {"az", "ez", "azt", "ezt", "arrol", "errol", "azzal", "ezzel", "annak", "ennek"}


def detect_followup(user_text):
    """Visszaadja (memory_hasznos: bool, ok: str|None).

    ok értékei: "explicit_backreference" (egyértelmű fordulat, pl.
    "folytasd", "amit mondtam", "előző") vagy "short_deictic_followup"
    (rövid, névmásos kérdés, pl. "És az?", "Mit jelent ez?"). Ha egyik sem
    illik, (False, None)."""
    normalized = _normalize(user_text)
    if not normalized:
        return False, None

    for group in STRONG_KEYWORD_GROUPS:
        if all(keyword in normalized for keyword in group):
            return True, "explicit_backreference"

    words = re.sub(r"[^\w\s]", " ", normalized).split()
    if 0 < len(words) <= WEAK_MAX_WORDS and any(w in WEAK_DEICTIC_WORDS for w in words):
        return True, "short_deictic_followup"

    return False, None


def build_summary(history):
    """Tömör, EMBERI OLVASÁSRA szánt összefoglaló (a learning_log-ba) az
    utolsó (max MAX_HISTORY_TURNS) váltásból. Legfeljebb MAX_SUMMARY_CHARS
    hosszú - nem generál semmit, csak a meglévő szöveget vágja."""
    if not history:
        return ""
    recent = list(history)[-MAX_HISTORY_TURNS:]
    parts = []
    for user_msg, ai_reply in recent:
        u = _trim(user_msg, 60)
        a = _trim(ai_reply, 80)
        if u and a:
            parts.append(f"Korábban ezt kérdezted: \"{u}\", és ezt válaszoltam: \"{a}\".")
    return _trim(" ".join(parts), MAX_SUMMARY_CHARS)


def build_prompt_context(history):
    """A modell PROMPTJÁBA illesztendő kontextus - KIZÁRÓLAG a
    legutolsó egy váltásból (nem többől), natív "User: ...\\nAI: ...\\n\\n"
    formában, mert a tanító adat is ilyen blokkokból áll ("\\n\\n"-vel
    elválasztva) - ez a legkisebb kockázatú módja annak, hogy a kis
    karakter-alapú modell ismerős szerkezetű promptot kapjon, ne hosszú,
    szokatlan formátumú nyers historyt."""
    if not history:
        return ""
    user_msg, ai_reply = list(history)[-1]
    u = _trim(user_msg, MAX_PROMPT_USER_CHARS)
    a = _trim(ai_reply, MAX_PROMPT_REPLY_CHARS)
    if not u or not a:
        return ""
    return f"User: {u}\nAI: {a}\n\n"


def resolve_memory_context(user_text, history, enabled=True):
    """Fő belépési pont: eldönti, KELL-e memória ehhez az üzenethez, és ha
    igen, elkészíti a summary-t (naplózáshoz) és a prompt-kontextust
    (generáláshoz). Visszaad egy (memory_info, prompt_context) párt:

    memory_info: dict a learning_log-hoz - memory_used/memory_summary/
    memory_reason mezőkkel.
    prompt_context: "" (nincs memória) vagy a build_prompt_context() által
    épített rövid előzmény-blokk, amit a hívó a modell promptja elé
    illeszthet.
    """
    if not enabled:
        return {"memory_used": False, "memory_summary": "", "memory_reason": "disabled"}, ""

    followup, reason = detect_followup(user_text)
    if not followup:
        return {"memory_used": False, "memory_summary": "", "memory_reason": "no_backreference_detected"}, ""

    if not history:
        return {"memory_used": False, "memory_summary": "", "memory_reason": "no_history_available"}, ""

    summary = build_summary(history)
    prompt_context = build_prompt_context(history)
    if not summary or not prompt_context:
        return {"memory_used": False, "memory_summary": "", "memory_reason": "no_history_available"}, ""

    memory_info = {"memory_used": True, "memory_summary": summary, "memory_reason": reason}
    return memory_info, prompt_context
