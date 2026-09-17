"""
MF-AI-Zero - v0.8 válaszértékelő.

Egyszerű, SZABÁLYALAPÚ pontozás egy AI válaszra - nem gépi tanulás, csak
konkrét, ellenőrizhető feltételek. A cél: legyen egy objektív jelzés
arról, mennyire "gyanús" egy válasz, hogy később (külön lépésben, külön
szkripttel) ebből javító tanítóadatot lehessen válogatni.

Ez a modul CSAK ÉRTÉKEL - semmilyen tanítást nem indít el, és a
kiszámított pontszám/flag-ek nem befolyásolják a ténylegesen visszaadott
választ (a generálás után, utólag fut le).

A szabályok azokra a konkrét hibatípusokra épülnek, amiket a projekt
korábbi fejlesztése (v0.7b-v0.7e) során ténylegesen megfigyeltünk:
üres/placeholder válasz, kiszivárgott "User:"/"AI:" címke, ismétlődő
mondat egy válaszon belül, túl rövid válasz, és (mondatszám-kéréseknél)
eltérő mondatszám a kérttől.
"""

import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate import split_into_sentences  # noqa: E402

MAX_SCORE = 100
MIN_SCORE = 0

# Pontlevonások szabályonként - ezek a projekt eddigi tapasztalatai alapján
# hozzávetőlegesen súlyozottak (súlyosabb, gyakoribb hibák nagyobb levonást
# kapnak), nem egzakt tudományos mérőszám.
PENALTIES = {
    "empty_or_fallback": 60,
    "leaked_label": 30,
    "duplicate_sentence": 20,
    "too_short": 15,
    "sentence_count_mismatch": 25,
    "deterministic_fix_applied": 10,
    "garbled_token": 30,
    "repeated_char_run": 25,
}

# v1.7.3 - a kis karakter-alapú LSTM néha egy legalább 5 betűs, magánhangzó
# NÉLKÜLI "szót" generál (két szó összefolyása/töredéke) - ez szinte
# biztosan nem valódi magyar szó. FONTOS: ez SZÁNDÉKOSAN konzervatív -
# egy valódi szótár/nyelvi modell nélkül nem lehet minden "közel jó, de
# téves" torzulást (pl. "szavem" a "szívem" helyett) megbízhatóan
# elkapni, csak a LEGDURVÁBB, egyértelmű eseteket (nincs benne
# magánhangzó, VAGY ugyanaz a karakter 4+ egymás után ismétlődik).
_VOWELS = set("aeiouáéíóöőúüű")
_WORD_PATTERN = re.compile(r"[A-Za-zÀ-ÿ]+")
_REPEATED_CHAR_PATTERN = re.compile(r"(.)\1{3,}")


def _has_garbled_token(text):
    for token in _WORD_PATTERN.findall(text or ""):
        if len(token) >= 5 and not any(ch.lower() in _VOWELS for ch in token):
            return True
    return False


def _has_repeated_char_run(text):
    return bool(_REPEATED_CHAR_PATTERN.search(text or ""))


def evaluate_reply(user_message, reply, intent, sentence_info=None):
    """Kiértékel egy AI választ, és visszaad egy (score, flags) párt.

    score: 0-100 közötti egész szám (100 = semmilyen ismert probléma nem
    észlelhető; nem jelenti azt, hogy a válasz tartalmilag helyes, csak
    hogy a vizsgált szabályok egyike sem jelzett hibát).

    flags: a ténylegesen észlelt problémák nevei (lista, üres ha nincs).

    sentence_info: a router.route_and_respond() harmadik visszatérési
    értéke - (kért_mondatszám, tényleges_mondatszám, történt-e
    determinisztikus_javítás). Csak sentence_request intentnél releváns,
    egyébként hagyd None-on.
    """
    flags = []
    reply = reply or ""
    stripped = reply.strip()

    if not stripped or stripped == "...":
        flags.append("empty_or_fallback")

    if "\nUser:" in reply or "\nAI:" in reply or stripped.startswith(("User:", "AI:")):
        flags.append("leaked_label")

    sentences = split_into_sentences(reply)
    normalized = [s.strip().lower() for s in sentences]
    if len(normalized) > 1 and len(normalized) != len(set(normalized)):
        flags.append("duplicate_sentence")

    word_count = len(stripped.split())
    if 0 < word_count < 3:
        flags.append("too_short")

    if _has_garbled_token(stripped):
        flags.append("garbled_token")

    if _has_repeated_char_run(stripped):
        flags.append("repeated_char_run")

    if intent == "sentence_request" and sentence_info is not None:
        requested_n, actual_n, fixed = sentence_info
        if actual_n != requested_n:
            flags.append("sentence_count_mismatch")
        if fixed:
            flags.append("deterministic_fix_applied")

    score = MAX_SCORE - sum(PENALTIES[flag] for flag in flags)
    score = max(MIN_SCORE, min(MAX_SCORE, score))
    return score, flags
