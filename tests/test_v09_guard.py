"""
MF-AI-Zero - v0.9-guard teszt: kategória-felismerés (guard.py) + a
learning_log guard_info bővítésének (learning_log.py) ellenőrzése.

Három rész:
  1. detect_category() - a 7 kategória felismerése különféle
     megfogalmazásokra (rövid, elütéses, haveri, hosszabb, szinonim), NEM
     fix kérdés-lista alapján.
  2. A kontrollált fallback válaszok GARANCIÁJA: minden fallback válasz
     ténylegesen teljesíti a saját kategóriája kulcsszó-elvárását (ha ez
     nem így lenne, a fallback maga bukna meg a golden teszten).
  3. log_feedback() guard_info bővítés - visszafelé kompatibilis (ha
     guard_info=None, a rekord formátuma változatlan), és helyesen
     egészíti ki a rekordot, ha meg van adva.
  4. Rövid integrációs teszt: guarded_route_and_respond() ténylegesen
     lefut a valódi candidate A modellel, és a guard_info dict minden
     elvárt mezőt tartalmaz.

Futtatás:
    python tests/test_v09_guard.py
"""

import json
import os
import sys
import tempfile

SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
sys.path.insert(0, SRC_DIR)

from guard import (  # noqa: E402
    CATEGORY_FALLBACKS,
    detect_category,
    guarded_route_and_respond,
    is_on_topic,
)
from learning_log import log_feedback  # noqa: E402

FAILURES = []


def check(label, condition):
    status = "OK" if condition else "FAIL"
    print(f"  [{status}] {label}")
    if not condition:
        FAILURES.append(label)


# ---------------------------------------------------------------------------
# 1) detect_category() - kategória-felismerés variációkra, NEM fix listára
# ---------------------------------------------------------------------------
print("--- detect_category() teszt (variációk: rövid / elütéses / haveri / hosszú / szinonim) ---")

CATEGORY_CASES = [
    ("Hány éves vagy?", "age"),
    ("hany eves vagy", "age"),                              # elütéses (ékezet nélkül)
    ("Mennyi idős vagy?", "age"),                            # szinonim
    ("Van egyáltalán életkorod?", "age"),                    # hosszabb
    ("Hogy vagy?", "smalltalk"),
    ("Mizu?", "smalltalk"),                                  # haveri/rövid
    ("Hogy telik a napod eddig?", "smalltalk"),               # hosszabb
    ("Mi újság?", "smalltalk"),
    ("mi ujsag", "smalltalk"),                                # elütéses
    ("Van emlékezeted?", "memory"),
    ("van emlekezeted", "memory"),                            # elütéses
    ("Emlékszel a korábbi beszélgetésekre?", "memory"),       # hosszabb
    ("Mi a kedvenc filmed?", "preference"),
    ("Szoktál filmet nézni?", "preference"),
    ("Tudsz verset írni?", "capability"),
    ("tudsz verset irni", "capability"),                      # elütéses
    ("Írnál nekem egy verset?", "capability"),
    ("Miért válaszolsz néha furán?", "explanation"),
    ("miert van hogy furan valaszolsz", "explanation"),       # elütéses
    ("Mi a különbség közted és egy nagy AI chatbot között?", "explanation"),
    ("miben kulonbozol egy nagy AI-tol", "explanation"),      # elütéses
    ("Szia, ki vagy?", "identity"),
    ("Mi a célod?", None),                                    # nincs guard-kategória
]

for text, expected in CATEGORY_CASES:
    got = detect_category(text)
    check(f"'{text}' -> kategória={expected!r} (kapott: {got!r})", got == expected)


# ---------------------------------------------------------------------------
# 2) A fallback válaszok garanciája - mindegyik teljesíti a saját
#    kategóriája kulcsszó-elvárását (is_on_topic)
# ---------------------------------------------------------------------------
print("\n--- Fallback válaszok garancia-teszt (mindegyik teljesíti a saját kulcsszavát) ---")

for category, options in CATEGORY_FALLBACKS.items():
    for reply in options:
        check(f"[{category}] fallback teljesíti a kulcsszó-elvárást: {reply[:40]!r}...",
              is_on_topic(category, reply))


# ---------------------------------------------------------------------------
# 3) log_feedback() guard_info bővítés
# ---------------------------------------------------------------------------
print("\n--- log_feedback() guard_info bővítés teszt ---")

with tempfile.TemporaryDirectory() as tmp_dir:
    tmp_log_path = os.path.join(tmp_dir, "guard_feedback.jsonl")

    # guard_info=None -> a rekord formátuma VÁLTOZATLAN kell maradjon
    record_no_guard = log_feedback(
        "Szia, ki vagy?", "Szia! Én az MF-AI-Zero vagyok.", "general_chat", "v0.7",
        100, [], sentence_info=None, log_path=tmp_log_path,
    )
    check("guard_info=None -> nincs 'guard_triggered' mező a rekordban",
          "guard_triggered" not in record_no_guard)

    guard_info = {
        "detected_intent": "general_chat",
        "expected_answer_type": "age",
        "guard_triggered": True,
        "retry_count": 1,
        "fallback_used": True,
        "failure_reason": "category_mismatch",
        "corrected_answer": "Nincs igazi életkorom, hiszen egy program vagyok.",
        "used_for_training": False,
    }
    record_guard = log_feedback(
        "Hány éves vagy?", "Nincs igazi életkorom, hiszen egy program vagyok.",
        "general_chat", "v0.8b_candidate_a", 100, [],
        sentence_info=None, log_path=tmp_log_path, guard_info=guard_info,
    )
    check("guard_info megadva -> minden guard mező bekerül a rekordba", all(
        record_guard.get(k) == v for k, v in guard_info.items()
    ))

    with open(tmp_log_path, encoding="utf-8") as f:
        lines = [line for line in f if line.strip()]
    check("mindkét sor bekerült a naplóba", len(lines) == 2)
    parsed_guard = json.loads(lines[1])
    check("a guard mezők a fájlban is megjelennek", parsed_guard.get("fallback_used") is True)
    check("'used_for_training' mindig False a guard-korrekcióknál",
          parsed_guard.get("used_for_training") is False)


# ---------------------------------------------------------------------------
# 4) Integrációs teszt: guarded_route_and_respond() valódi modellel
# ---------------------------------------------------------------------------
print("\n--- Integrációs teszt: guarded_route_and_respond() valódi candidate A modellel ---")

import torch  # noqa: E402

import config  # noqa: E402
from generate import load_model  # noqa: E402

device = torch.device("cpu")
candidate_a_path = os.path.join(config.BASE_DIR, "models", "mf_ai_zero_chat_v0_8b_a.pt")

if os.path.exists(candidate_a_path):
    g_tuple = load_model(device, candidate_a_path)
    i_tuple = load_model(device, os.path.join(config.BASE_DIR, "models", "mf_ai_zero_chat_v0_7c.pt"))
    general_model = (*g_tuple[:3], device, g_tuple[3])
    instruction_model = (*i_tuple[:3], device, i_tuple[3])

    for text in ["Hány éves vagy?", "Írj 3 mondatot az erőről.", "Viszlát!"]:
        reply, intent, model_used, sentence_info, guard_info = guarded_route_and_respond(
            general_model, instruction_model, text, temperature=0.6
        )
        check(f"'{text}' -> guarded_route_and_respond nem dob hibát, választ ad",
              isinstance(reply, str) and len(reply) > 0)
        check(f"'{text}' -> guard_info tartalmazza az összes elvárt mezőt", all(
            k in guard_info for k in (
                "detected_intent", "expected_answer_type", "guard_triggered",
                "retry_count", "fallback_used", "failure_reason",
                "corrected_answer", "used_for_training",
            )
        ))
        check(f"'{text}' -> nem general_chat intentnél a guard nem avatkozik be",
              guard_info["guard_triggered"] is False if intent != "general_chat" else True)
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
