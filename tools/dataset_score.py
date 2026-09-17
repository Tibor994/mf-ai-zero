"""
MF-AI-Zero - v1.7.4 dataset foundation: determinisztikus minőségpontozó.

CÉL: minden (már validálással átment) sorra egy 0-100 közötti quality_score
értéket adni - ugyanaz a szabályalapú, NEM ML-alapú elv, mint a
src/evaluator.py-nál (lásd annak fejlécét is): objektív, ellenőrizhető
szabályok, nem "vélemény". A pontszám NEM dönt automatikusan semmiről -
csak egy jelzés, ami alapján később (KÉZI vagy külön, explicit lépésben)
válogatni lehet.

Szempontok (mindegyik egy konkrét, ellenőrizhető szabály - lásd PENALTIES):
  - nyelvhelyesség / nincs torz szó / nincs ismétlődő karaktersorozat
  - érthetőség (nem túl rövid, nem túl hosszú, van záró írásjel)
  - magyar természetesség (nincs nyilvánvaló angol keveredés)
  - instruction/output kapcsolat (durva szó-átfedés heurisztika)
  - nincs hallucination-szerű túlállítás (overclaiming minták)
  - nincs túl sablonos/generikus válasz (ismert töltelék-mondatok)

Használat parancssorból:
    python tools/dataset_score.py data/clean/batch1.jsonl

Használat modulként:
    from dataset_score import score_row
"""

import argparse
import json
import os
import re
import sys

SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
sys.path.insert(0, SRC_DIR)
from evaluator import _has_garbled_token, _has_repeated_char_run  # noqa: E402

from dataset_validate import (  # noqa: E402
    MAX_OUTPUT_CHARS,
    MIN_OUTPUT_WORDS,
    _contains_english_mixing,
    _contains_overclaiming,
)

MAX_SCORE = 100
MIN_SCORE = 0

PENALTIES = {
    "garbled_token": 35,
    "repeated_char_run": 30,
    "too_short": 25,
    "too_long": 10,
    "english_mixing": 15,
    "overclaiming": 25,
    "no_terminal_punctuation": 5,
    "generic_template": 15,
    "low_instruction_overlap": 10,
}

# v1.7.4 - ismert, túl sablonos/generikus, INDOKLÁS NÉLKÜLI "kitérő"
# válaszok - SZÁNDÉKOSAN csak a szinte szó szerinti, teljesen kopár
# guard.py-fallback-szerű mintákat tartalmazza. FONTOS: nem tartalmaz
# olyan általánosabb "nem tudom" kezdetű fordulatot, ami az
# uncertain_lookup kategória LEGITIM, jól indokolt bizonytalanság-
# válaszaiban is előfordulhat (pl. "Ezt nem tudom megmondani, mert
# nincs friss adatom.") - egy ilyen válasz NEM sablonos, hanem pont a
# kívánt, őszinte viselkedés, ezért nem szabad büntetni.
_GENERIC_TEMPLATE_PHRASES = [
    "erről egyelőre nem tudok ennél pontosabb választ adni",
    "erről nem tudok többet mondani",
]

_SENTENCE_END_RE = re.compile(r"[.!?…]$")
_WORD_RE = re.compile(r"[a-záéíóöőúüű0-9]+", re.IGNORECASE)


def _normalize_words(text):
    return set(w.lower() for w in _WORD_RE.findall(text or ""))


def _looks_generic_template(output):
    low = output.strip().lower()
    return any(phrase in low for phrase in _GENERIC_TEMPLATE_PHRASES)


def score_row(row):
    """Kiszámol egy (score, flags) párt egy MÁR validált sorra (dict).
    Nem dob hibát hiányzó mezőknél - feltételezi, hogy validate_row() már
    lefutott és a sor szerkezetileg rendben van; ha mégis hiányos, a
    hiányzó részekhez tartozó szabályokat egyszerűen kihagyja."""
    flags = []
    instruction = (row.get("instruction") or "").strip()
    output = (row.get("output") or "").strip()

    if not output:
        return MIN_SCORE, ["empty_output"]

    word_count = len(output.split())
    if word_count < MIN_OUTPUT_WORDS:
        flags.append("too_short")
    if len(output) > MAX_OUTPUT_CHARS:
        flags.append("too_long")

    if _has_garbled_token(output):
        flags.append("garbled_token")
    if _has_repeated_char_run(output):
        flags.append("repeated_char_run")

    if _contains_english_mixing(output):
        flags.append("english_mixing")

    if _contains_overclaiming(output):
        flags.append("overclaiming")

    if not _SENTENCE_END_RE.search(output):
        flags.append("no_terminal_punctuation")

    if _looks_generic_template(output):
        flags.append("generic_template")

    if instruction and word_count >= MIN_OUTPUT_WORDS:
        instruction_words = _normalize_words(instruction)
        output_words = _normalize_words(output)
        # csak akkor jelezzük, ha SZINTE SEMMI szó-átfedés nincs ÉS a
        # válasz elég rövid ahhoz, hogy ez ne csak egy hosszabb, saját
        # szavakkal megfogalmazott (de egyébként releváns) válasz legyen -
        # ez SZÁNDÉKOSAN óvatos, sok jó választ NEM büntet.
        overlap = instruction_words & output_words
        if not overlap and word_count <= 6:
            flags.append("low_instruction_overlap")

    score = MAX_SCORE - sum(PENALTIES[flag] for flag in flags)
    return max(MIN_SCORE, min(MAX_SCORE, score)), flags


def score_file(path):
    """Beolvas egy JSONL fájlt (feltételezve, hogy minden sor valid JSON -
    validate_file()-t célszerű előbb lefuttatni), és visszaad egy listát:
    [{"row_number", "id", "score", "flags"}, ...]."""
    results = []
    with open(path, "r", encoding="utf-8") as f:
        for line_number, raw_line in enumerate(f, start=1):
            stripped = raw_line.strip()
            if not stripped:
                continue
            try:
                row = json.loads(stripped)
            except json.JSONDecodeError:
                continue
            score, flags = score_row(row)
            results.append({
                "row_number": line_number,
                "id": row.get("id") if isinstance(row, dict) else None,
                "score": score,
                "flags": flags,
            })
    return results


def _main():
    parser = argparse.ArgumentParser(description="MF-AI-Zero dataset minőségpontozó.")
    parser.add_argument("path", help="A pontozandó .jsonl fájl elérési útja.")
    args = parser.parse_args()

    results = score_file(args.path)
    for r in results:
        flags_text = f" ({', '.join(r['flags'])})" if r["flags"] else ""
        print(f"sor {r['row_number']} (id={r['id']}): score={r['score']}{flags_text}")
    if results:
        avg = sum(r["score"] for r in results) / len(results)
        print(f"\nÁtlag pontszám: {avg:.1f}/100 ({len(results)} sor)")


if __name__ == "__main__":
    _main()
