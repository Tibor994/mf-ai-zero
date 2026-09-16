"""
MF-AI-Zero - v1.4 stílus / válaszminőség (response_style).

CÉL: a válaszok érezhetően természetesebbek, rendezettebbek legyenek - DE
ez KIZÁRÓLAG felszíni, DETERMINISZTIKUS utófeldolgozás a modell MÁR KÉSZ
válaszán, NEM új generálás és NEM újratanítás. A projekt kis, karakter-
alapú LSTM-je nem egy nagy LLM - nem lehet neki "hangozz természetesebben"
típusú instrukciót adni, mert nem érti/nem követi megbízhatóan. Ezért ez a
modul SZABÁLYALAPÚ szövegműveletekkel dolgozik:

  1. fix_grammar_and_punctuation() - szóköz-hibák, hiányzó/felesleges
     írásjelek, nagybetűsítés javítása.
  2. remove_duplicate_sentences() - szó szerint ismétlődő mondatok
     eltávolítása (az evaluator.py CSAK JELZI ugyanezt - itt ténylegesen
     el is távolítjuk a végleges válaszból).
  3. soften_if_too_short() - ha a válasz (a fenti javítások UTÁN is) túl
     rövid, egy RÖVID, TARTALOM NÉLKÜLI, barátságos lezáró mondatot told
     hozzá egy fix pool-ból - ez SOSEM tény, SOSEM új infó.

FONTOS, amit ez a modul SZÁNDÉKOSAN NEM csinál:
  - NEM változtatja meg a válasz TARTALMÁT/tényeit - kizárólag formai
    (írásjel/nagybetű/ismétlés) javítást végez.
  - NEM generál/talál ki új információt - az esetlegesen hozzáadott
    lezáró mondat egy FIX, kézzel írt, tartalom nélküli pool-ból jön
    (_FRIENDLY_CONNECTORS), sosem a modell generálja, és semmilyen
    tényállítást nem tartalmaz.
  - NEM fut le a determinisztikus rendszerválaszokon (pl. a hosszú távú
    memória mentési visszaigazolása "Megjegyeztem: ...", a webes keresés
    "nincs konfigurálva" státuszüzenete) - ezeket a guard.py direktben,
    a stílus-réteg megkerülésével adja vissza, mert ezek már eleve
    pontosak/tömörek.
"""

import random
import re

from generate import split_into_sentences

MIN_NATURAL_WORDS = 4  # ez alatt számít "túl rövidnek" egy válasz - az
# evaluator.py "too_short" küszöbénél (word_count < 3) valamivel megengedőbb,
# hogy egy már amúgy is teljes, természetes rövid válasz (pl. "Szívesen,
# örülök neki!") NE kapjon felesleges, redundáns toldást.
MAX_SCORE = 100
MIN_SCORE = 0

SENTENCE_END_CHARS = (".", "!", "?", "…")

# Rövid, TARTALOM NÉLKÜLI, barátságos lezáró mondatok - egyik sem
# állít tényt, csak beszélgetős "töltő" fordulat. Csak akkor kerül a
# válasz végére, ha a válasz (a formai javítások után is) túl rövid.
_FRIENDLY_CONNECTORS = [
    "Remélem, ez segít!",
    "Szólj, ha többet szeretnél tudni erről!",
    "Ha van még kérdésed, szívesen válaszolok.",
    "Remélem, ezzel tudtam segíteni.",
    "Örülök, hogy erről beszélgethettünk.",
]

PENALTIES = {
    "had_duplicate_sentences": 15,
    "too_short_after_styling": 20,
    "missing_end_punctuation": 10,
    "excessive_repeated_punctuation": 5,
}


def fix_grammar_and_punctuation(text):
    """Determinisztikus írásjel/nagybetű-javítás - NEM változtat
    szavakon/tartalmon, csak a formán."""
    text = (text or "").strip()
    if not text:
        return text

    # többszörös szóköz -> egy
    text = re.sub(r"[ \t]+", " ", text)
    # szóköz írásjel ELŐTT eltávolítva (pl. "Szia ." -> "Szia.")
    text = re.sub(r"\s+([.,!?;:])", r"\1", text)
    # hiányzó szóköz írásjel UTÁN, ha rögtön betű/szám követi
    text = re.sub(r"([.,!?;:])(?=[^\s.,!?;:])", r"\1 ", text)
    # többszörös "!"/"?" összevonása (pl. "???" -> "?")
    text = re.sub(r"([!?])\1+", r"\1", text)
    # két pont -> egy (a hármas "..." ellipszis érintetlen marad)
    text = re.sub(r"(?<!\.)\.\.(?!\.)", ".", text)
    text = re.sub(r"[ \t]+", " ", text).strip()

    if text:
        text = text[0].upper() + text[1:]

    def _cap_after_sentence_end(match):
        return match.group(1) + match.group(2).upper()

    text = re.sub(r"([.!?]\s+)([a-záéíóöőúüű])", _cap_after_sentence_end, text)

    if text and text[-1] not in SENTENCE_END_CHARS:
        text += "."
    return text


def remove_duplicate_sentences(text):
    """Szó szerint (kis/nagybetűtől függetlenül) ismétlődő mondatokat
    távolít el, az ELSŐ előfordulást megtartva - a tartalom (a megmaradó
    mondatok szövege) NEM változik."""
    sentences = split_into_sentences(text or "")
    if len(sentences) <= 1:
        return text
    seen = set()
    deduped = []
    changed = False
    for sentence in sentences:
        key = sentence.strip().lower()
        if key and key in seen:
            changed = True
            continue
        if key:
            seen.add(key)
        deduped.append(sentence)
    if not changed:
        return text
    return " ".join(deduped)


def soften_if_too_short(text, min_words=MIN_NATURAL_WORDS, rng=None):
    """Ha a válasz túl rövid (kevesebb, mint min_words szó), egy fix,
    tartalom nélküli lezáró mondatot told hozzá - a MEGLÉVŐ tartalom
    változatlan marad, csak kiegészül."""
    text = text or ""
    if not text.strip():
        return text
    word_count = len(text.split())
    if word_count >= min_words:
        return text
    chooser = rng or random
    connector = chooser.choice(_FRIENDLY_CONNECTORS)
    return f"{text} {connector}"


def score_response_quality(original_text, styled_text):
    """Egyszerű, szabályalapú pontszám (0-100) - ugyanaz a stílus, mint
    evaluator.evaluate_reply(): konkrét, ellenőrizhető feltételek, nem
    gépi tanulás. Az EREDETI (stílus-javítás ELŐTTI) szövegen méri a
    hibákat, hogy lássuk, ténylegesen mennyit segített a réteg."""
    flags = []
    original_text = original_text or ""
    styled_text = styled_text or ""

    sentences = split_into_sentences(original_text)
    normalized = [s.strip().lower() for s in sentences]
    if len(normalized) > 1 and len(normalized) != len(set(normalized)):
        flags.append("had_duplicate_sentences")

    if len(styled_text.split()) < MIN_NATURAL_WORDS:
        flags.append("too_short_after_styling")

    stripped_original = original_text.strip()
    if stripped_original and stripped_original[-1] not in SENTENCE_END_CHARS:
        flags.append("missing_end_punctuation")

    if re.search(r"([!?])\1{1,}", original_text):
        flags.append("excessive_repeated_punctuation")

    score = MAX_SCORE - sum(PENALTIES[flag] for flag in flags)
    return max(MIN_SCORE, min(MAX_SCORE, score)), flags


# v1.4.1: a response_planner target_length értékeihez tartozó "túl rövid"
# szóküszöbök - CSAK azt szabályozzák, mikor told hozzá a réteg egy
# tartalom nélküli lezáró mondatot, tartalmat nem generálnak.
_TARGET_LENGTH_MIN_WORDS = {"short": MIN_NATURAL_WORDS, "medium": 6, "long": 8}


def apply_structure(text, plan):
    """A response_planner terve alapján ÁTRENDEZI (nem újraírja!) a MÁR
    MEGLÉVŐ mondatokat - számozott listává (wants_steps) vagy pontokba
    szedett listává (wants_list), illetve összegzésnél (wants_summary)
    az első 1-2 mondatra rövidíti a választ. Csak akkor formáz listává/
    lépésekké, ha legalább 2 mondat van - egyetlen mondatot nem
    "listáz", mert az félrevezető lenne."""
    if not plan or not text:
        return text

    sentences = [s.strip() for s in split_into_sentences(text) if s.strip()]

    if plan.get("wants_summary") and len(sentences) > 2:
        return " ".join(sentences[:2])

    if plan.get("wants_steps") and len(sentences) >= 2:
        return "\n".join(f"{i}. {s}" for i, s in enumerate(sentences, start=1))

    if plan.get("wants_list") and len(sentences) >= 2:
        return "\n".join(f"- {s}" for s in sentences)

    return text


def apply_style(text, enabled=True, rng=None, plan=None):
    """Fő belépési pont. Visszaad egy (styled_text, style_info) párt.

    plan: opcionális, a response_planner.build_response_plan() eredménye
    - ha meg van adva, a válasz FORMÁJÁT (lásd apply_structure()) és a
    "túl rövid" küszöböt a tervezett válasz-típushoz igazítja. SOSEM
    változtat tartalmat/tényt.

    style_info: {"style_used", "response_quality_score",
    "final_response_length"} - a learning_log-hoz (lásd guard.py).
    style_used=True, ha a szöveg ténylegesen megváltozott a
    feldolgozás során (nem csak lefutott a réteg)."""
    original = text or ""
    if not enabled or not original.strip():
        return original, {
            "style_used": False,
            "response_quality_score": None,
            "final_response_length": len(original),
        }

    cleaned = fix_grammar_and_punctuation(original)
    deduped = remove_duplicate_sentences(cleaned)
    deduped = fix_grammar_and_punctuation(deduped)

    structured = apply_structure(deduped, plan) if plan else deduped

    min_words = _TARGET_LENGTH_MIN_WORDS.get((plan or {}).get("target_length"), MIN_NATURAL_WORDS)
    final_text = soften_if_too_short(structured, min_words=min_words, rng=rng)

    score, _flags = score_response_quality(original, final_text)

    return final_text, {
        "style_used": final_text != original,
        "response_quality_score": score,
        "final_response_length": len(final_text),
    }
