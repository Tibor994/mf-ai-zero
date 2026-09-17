"""
MF-AI-Zero - v1.4.2 user input normalizer (typo-tolerant understanding).

CÉL: a router/guard/memory/web/conversation_manager pontosabban értse a
hibásan, gyorsan, szlengesen írt magyar szöveget - DE ez egy SZIGORÚAN
ÓVATOS, WHITELIST-alapú javítás, NEM egy általános helyesírás-ellenőrző
és NEM fuzzy/edit-distance alapú találgatás (az könnyen félrevihetne
valódi szavakat, neveket, rövidítéseket).

Működés:
  - Egy FIX, kézzel ellenőrzött szótár (KNOWN_TYPOS) mondja meg, mely
    PONTOS, EGÉSZ szavakat (SOSEM részszavakat/substringeket!) cseréljük
    le, és milyen magabiztossággal (confidence).
  - Egy tokenre CSAK akkor alkalmazzuk a cserét, ha az tisztán, kisbetűvel
    írt szó - nincs benne szám, "@", "/", "\\", "_", zárójel, és nincs
    benne "." sem (ez véd a linkek/e-mailek/kódok/fájlnevek ellen), ÉS a
    token nem tartalmaz nagybetűt (ez véd a nevek/rövidítések/mondatkezdő
    tulajdonnevek ellen - a szótárban szereplő szavak eleve nem
    tulajdonnevek).
  - Ha a szótári bejegyzés magabiztossága a MIN_CONFIDENCE küszöb ALATT
    van, a csere NEM történik meg (a modul így bővíthető bizonytalanabb
    jelöltekkel is anélkül, hogy azok automatikusan aktívvá válnának).
  - Az EREDETI szöveg MINDIG megmarad (original_text) - a normalized_text
    egy MÁSIK, külön mező, amit a hívó fél (guard.py) választása szerint
    használ a további feldolgozáshoz, de a napló mindkettőt rögzíti.
"""

import re

# (eredeti_szó_kisbetűvel) -> (javított_szó, confidence 0-1 között)
# CSAK kézzel ellenőrzött, egyértelmű elírások/rövidítések - a lista
# szándékosan kicsi és konzervatív.
KNOWN_TYPOS = {
    "nm": ("nem", 0.9),
    "hixg": ("hogy", 0.85),
    "higx": ("hogy", 0.85),
    "hgy": ("hogy", 0.9),
    "kezs": ("kész", 0.85),
    "ertem": ("értem", 0.95),
    "bezyelgesunk": ("beszélgessünk", 0.8),
    "am": ("amúgy", 0.7),
    "lezs": ("lesz", 0.85),
}

MIN_CONFIDENCE = 0.6

_WORD_CHARS = r"a-zA-ZáéíóöőúüűÁÉÍÓÖŐÚÜŰ"
_CHUNK_PATTERN = re.compile(r"\S+|\s+")
_LEADING_PUNCT = re.compile(rf"^[^{_WORD_CHARS}]+")
_TRAILING_PUNCT = re.compile(rf"[^{_WORD_CHARS}]+$")

# egy token BIZTOSAN kimarad a javításból, ha ezek közül bármelyiket
# tartalmazza - szám, kukac, per, backslash, aláhúzás, kapcsos/szögletes
# zárójel, "://" (URL), "www." (URL) - ez véd link/email/kód/fájlnév ellen
_UNSAFE_TOKEN_PATTERN = re.compile(r"[0-9@/\\_<>{}\[\]=;#]|https?:|www\.")

# Ha az EGÉSZ üzenetben feltűnik BÁRMELYIK kód-gyanús jel (zárójelek,
# pontosvessző, összehasonlító/nyíl operátorok), a teljes üzenetet
# érintetlenül hagyjuk - egy kódrészletben a "hgy"-hez hasonló token is
# valójában változónév/paraméter lehet, nem elírás, és egy token-szintű
# védelem (lásd _UNSAFE_TOKEN_PATTERN) ezt nem mindig kapja el, ha a
# "kódjel" egy MÁSIK szóhoz tapad (pl. "print(am + hgy)").
_CODE_LIKE_MESSAGE_PATTERN = re.compile(r"[(){}\[\];]|==|!=|->|=>|::")


def normalize_input(text):
    """Fő belépési pont. Visszaad egy dict-et: {"original_text",
    "normalized_text", "normalization_confidence", "detected_typos"}.

    detected_typos: [{"original","corrected","confidence"}, ...] - az
    ÖSSZES ténylegesen elvégzett csere, sorrendben.
    normalization_confidence: a legalacsonyabb megbízhatóságú alkalmazott
    csere értéke (konzervatív, "leggyengébb láncszem" elv) - ha nem
    történt csere, 1.0 (nem kockáztattunk semmit)."""
    text = text or ""
    if not text.strip() or _CODE_LIKE_MESSAGE_PATTERN.search(text):
        return {
            "original_text": text,
            "normalized_text": text,
            "normalization_confidence": 1.0,
            "detected_typos": [],
        }

    detected = []
    confidences = []
    pieces = []

    for chunk in _CHUNK_PATTERN.findall(text):
        if chunk.isspace():
            pieces.append(chunk)
            continue

        if _UNSAFE_TOKEN_PATTERN.search(chunk):
            pieces.append(chunk)
            continue

        leading_match = _LEADING_PUNCT.match(chunk)
        leading = leading_match.group(0) if leading_match else ""
        rest = chunk[len(leading):]
        trailing_match = _TRAILING_PUNCT.search(rest)
        trailing = trailing_match.group(0) if trailing_match else ""
        core = rest[: len(rest) - len(trailing)] if trailing else rest

        # "." a szó BELSEJÉBEN (pl. "app.py", "pelda.com") -> fájlnév/
        # domain-gyanús, nem nyúlunk hozzá. A mondatvégi pontot a
        # trailing-stripping már kiemelte, ide csak a belső "." jut.
        if not core or not core.islower() or "." in core:
            pieces.append(chunk)
            continue

        entry = KNOWN_TYPOS.get(core)
        if not entry:
            pieces.append(chunk)
            continue

        correction, confidence = entry
        if confidence < MIN_CONFIDENCE:
            pieces.append(chunk)
            continue

        detected.append({"original": core, "corrected": correction, "confidence": confidence})
        confidences.append(confidence)
        pieces.append(f"{leading}{correction}{trailing}")

    normalized_text = "".join(pieces)
    overall_confidence = min(confidences) if confidences else 1.0

    return {
        "original_text": text,
        "normalized_text": normalized_text,
        "normalization_confidence": overall_confidence,
        "detected_typos": detected,
    }
