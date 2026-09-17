"""
MF-AI-Zero - v1.4.2 user input normalizer teszt (input_normalizer.py +
guard.py integráció).

Hat rész:
  1. normalize_input() - a feladatban kért 7 konkrét elírás javítása.
  2. Biztonsági szabály: linkeket/e-maileket/kódot/fájlneveket/neveket
     NEM módosít.
  3. detected_typos / normalization_confidence struktúra.
  4. Bizonytalan esetben (MIN_CONFIDENCE alatt) NEM javít.
  5. Integrációs teszt: guarded_route_and_respond() valódi candidate A
     modellel - guard_info tartalmazza a kötelező mezőket
     (input_normalizer_used/original_text/normalized_text/detected_typos/
     normalization_confidence); --no-input-normalizer kikapcsolja; egy
     elírásos üzenet a normalizálás UTÁN jobban felismerhető a guard
     kategória-rendszere által.
  6. guard/memory/web/conversation stabil marad a normalizer mellett is.

Futtatás:
    python tests/test_v1_4_2_input_normalizer.py
"""

import os
import sys

SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
sys.path.insert(0, SRC_DIR)

from input_normalizer import KNOWN_TYPOS, MIN_CONFIDENCE, normalize_input  # noqa: E402

FAILURES = []


def check(label, condition):
    status = "OK" if condition else "FAIL"
    print(f"  [{status}] {label}")
    if not condition:
        FAILURES.append(label)


# ---------------------------------------------------------------------------
# 1) A feladatban kért 7 konkrét elírás javítása
# ---------------------------------------------------------------------------
print("--- normalize_input() teszt - a kért 7 elírás ---")

TYPO_CASES = [
    ("nm", "nem"),
    ("hixg", "hogy"),
    ("higx", "hogy"),
    ("hgy", "hogy"),
    ("kezs", "kész"),
    ("ertem", "értem"),
    ("bezyelgesunk", "beszélgessünk"),
    ("am", "amúgy"),
    ("lezs", "lesz"),
]
for typo, expected in TYPO_CASES:
    result = normalize_input(f"szia {typo} valami")
    check(f"'{typo}' -> '{expected}' önálló szóként javítva",
          expected in result["normalized_text"].split())
    check(f"'{typo}' javítása szerepel a detected_typos listában",
          any(d["original"] == typo and d["corrected"] == expected for d in result["detected_typos"]))


# ---------------------------------------------------------------------------
# 2) Biztonsági szabály: linkek/e-mailek/kód/fájlnevek/nevek NEM módosulnak
# ---------------------------------------------------------------------------
print("\n--- Biztonsági szabály: linkek/kód/fájlnevek/nevek érintetlenek ---")

SAFE_CASES = [
    "Nézd meg ezt: https://example.com/nm-teszt",
    "Nyisd meg az app.py fájlt",
    "Mi az email cimed? valaki@nm.hu",
    "Nm neve Kovács János, ő is jön",
    "A www.pelda.hu/hgy oldalon van",
    "print(am + hgy)",
]
for text in SAFE_CASES:
    result = normalize_input(text)
    check(f"'{text}' -> a szöveg TELJESEN változatlan marad", result["normalized_text"] == text)
    check(f"'{text}' -> nincs detektált csere", result["detected_typos"] == [])

# kapitalizált (nagybetűvel írt) elírás-jelölt NEM javítódik (védi a
# neveket/mondatkezdő tulajdonneveket)
result_cap = normalize_input("Nm, ez biztos így van?")
check("nagybetűs 'Nm' NEM javítódik", "Nm" in result_cap["normalized_text"])


# ---------------------------------------------------------------------------
# 3) detected_typos / normalization_confidence struktúra
# ---------------------------------------------------------------------------
print("\n--- detected_typos / normalization_confidence struktúra ---")

result = normalize_input("nm ertem hgy mit mondtal")
check("original_text megegyezik a bemenettel", result["original_text"] == "nm ertem hgy mit mondtal")
check("normalized_text különbözik az eredetitől", result["normalized_text"] != result["original_text"])
check("3 javítás történt", len(result["detected_typos"]) == 3)
check("minden detected_typos elem tartalmazza a szükséges mezőket", all(
    k in d for d in result["detected_typos"] for k in ("original", "corrected", "confidence")
))
check("normalization_confidence a legalacsonyabb alkalmazott javítás értéke",
      result["normalization_confidence"] == min(d["confidence"] for d in result["detected_typos"]))

result_clean = normalize_input("Ez egy teljesen rendes mondat.")
check("nincs elírás -> normalization_confidence=1.0", result_clean["normalization_confidence"] == 1.0)
check("nincs elírás -> normalized_text == original_text",
      result_clean["normalized_text"] == result_clean["original_text"])

result_empty = normalize_input("")
check("üres szöveg -> nem hibázik, confidence=1.0", result_empty["normalization_confidence"] == 1.0)


# ---------------------------------------------------------------------------
# 4) Bizonytalan esetben (MIN_CONFIDENCE alatt) NEM javít
# ---------------------------------------------------------------------------
print("\n--- Bizonytalan eset: MIN_CONFIDENCE alatti bejegyzés nem aktiválódik ---")

check(f"minden jelenlegi szótári bejegyzés a MIN_CONFIDENCE ({MIN_CONFIDENCE}) felett van",
      all(conf >= MIN_CONFIDENCE for _corr, conf in KNOWN_TYPOS.values()))

# szintetikus, mesterségesen alacsony megbízhatóságú bejegyzéssel
_original_entry = KNOWN_TYPOS.get("zzz_teszt_szo")
KNOWN_TYPOS["zzz_teszt_szo"] = ("javitott_szo", 0.2)
try:
    result_low_conf = normalize_input("ez egy zzz_teszt_szo mondat")
    check("MIN_CONFIDENCE alatti bejegyzés NEM kerül alkalmazásra",
          "zzz_teszt_szo" in result_low_conf["normalized_text"] and result_low_conf["detected_typos"] == [])
finally:
    if _original_entry is None:
        del KNOWN_TYPOS["zzz_teszt_szo"]
    else:
        KNOWN_TYPOS["zzz_teszt_szo"] = _original_entry


# ---------------------------------------------------------------------------
# 5) Integrációs teszt: guarded_route_and_respond() valódi candidate A modellel
# ---------------------------------------------------------------------------
print("\n--- Integrációs teszt: guarded_route_and_respond() + input_normalizer ---")

import torch  # noqa: E402

import config  # noqa: E402
from generate import load_model  # noqa: E402
from guard import guarded_route_and_respond  # noqa: E402

device = torch.device("cpu")
candidate_a_path = os.path.join(config.BASE_DIR, "models", "mf_ai_zero_chat_v0_8b_a.pt")

if os.path.exists(candidate_a_path):
    g_tuple = load_model(device, candidate_a_path)
    i_tuple = load_model(device, os.path.join(config.BASE_DIR, "models", "mf_ai_zero_chat_v0_7c.pt"))
    general_model = (*g_tuple[:3], device, g_tuple[3])
    instruction_model = (*i_tuple[:3], device, i_tuple[3])

    # a) elírásos üzenet -> input_normalizer_used=True, guard_info tartalmazza a mezőket
    reply_a, intent_a, model_used_a, sentence_info_a, guard_info_a = guarded_route_and_respond(
        general_model, instruction_model, "hixg vagy?", temperature=0.6,
        input_normalizer_enabled=True,
    )
    check("elírásos üzenet -> input_normalizer_used=True", guard_info_a["input_normalizer_used"] is True)
    check("original_text az EREDETI (elírásos) szöveg", guard_info_a["original_text"] == "hixg vagy?")
    check("normalized_text a JAVÍTOTT szöveg", guard_info_a["normalized_text"] == "hogy vagy?")
    check("guard_info tartalmazza az összes kötelező mezőt", all(
        k in guard_info_a for k in ("input_normalizer_used", "original_text", "normalized_text",
                                     "detected_typos", "normalization_confidence")
    ))
    check("a javított szöveg alapján a guard felismeri a smalltalk kategóriát",
          guard_info_a["expected_answer_type"] == "smalltalk")

    # b) tiszta üzenet -> input_normalizer_used=False
    reply_b, intent_b, model_used_b, sentence_info_b, guard_info_b = guarded_route_and_respond(
        general_model, instruction_model, "Hogy vagy?", temperature=0.6,
        input_normalizer_enabled=True,
    )
    check("tiszta üzenet -> input_normalizer_used=False", guard_info_b["input_normalizer_used"] is False)
    check("tiszta üzenet -> normalized_text == original_text",
          guard_info_b["normalized_text"] == guard_info_b["original_text"])

    # c) --no-input-normalizer -> még elírásnál sem javít
    reply_c, intent_c, model_used_c, sentence_info_c, guard_info_c = guarded_route_and_respond(
        general_model, instruction_model, "hixg vagy?", temperature=0.6,
        input_normalizer_enabled=False,
    )
    check("input_normalizer_enabled=False -> input_normalizer_used=False", guard_info_c["input_normalizer_used"] is False)
    check("input_normalizer_enabled=False -> normalized_text == original_text (nyers szöveg megy tovább)",
          guard_info_c["normalized_text"] == guard_info_c["original_text"] == "hixg vagy?")

    # d) a normalizer mellett a guard többi mezője is jelen van (nincs regresszió)
    check("a normalizer mellett a guard többi rétegének mezői is jelen vannak", all(
        k in guard_info_a for k in (
            "detected_intent", "guard_triggered", "memory_used", "knowledge_used",
            "web_used", "style_used", "response_plan_used",
        )
    ))
else:
    print(f"  (kihagyva - nincs candidate A modell: {candidate_a_path})")


# ---------------------------------------------------------------------------
print(f"\n{'=' * 60}")
if FAILURES:
    print(f"EREDMÉNY: {len(FAILURES)} teszt megbukott:")
    for f in FAILURES:
        print(f"  - {f}")
    print("STÁTUSZ: NEM STABIL")
else:
    print("EREDMÉNY: minden teszt sikeres.")
    print("STÁTUSZ: STABIL")
print("=" * 60)

if __name__ == "__main__":
    sys.exit(1 if FAILURES else 0)
