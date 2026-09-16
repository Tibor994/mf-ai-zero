"""
MF-AI-Zero - v0.8 teszt: válaszértékelő (evaluator.py) + tanulási napló
(learning_log.py).

Két részből áll:
  1. Gyors, modell nélküli EGYSÉGTESZTEK az evaluate_reply() szabályaira
     és a log_feedback() fájlba írására (szintetikus példákkal, nem
     igényel modellbetöltést, másodpercek alatt lefut).
  2. Egy rövid INTEGRÁCIÓS teszt, ami a valódi v0.7e routert (v0.7 +
     v0.7c modell) futtatja néhány golden teszten, hogy megmutassa: a
     kiértékelés/naplózás valóban rákapcsolódik a router kimenetére,
     hiba nélkül, és NEM változtatja meg a router válaszát.

Ez a teszt NEM tanít semmit, és NEM módosítja a golden_chat_tests.json
fájlt vagy bármelyik modellt - csak a v0.8 naplózó rétege ellenőrzi.

Futtatás:
    python tests/test_v08_learning_log.py
"""

import json
import os
import sys
import tempfile

SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
sys.path.insert(0, SRC_DIR)

from evaluator import evaluate_reply  # noqa: E402
from learning_log import log_feedback  # noqa: E402

FAILURES = []


def check(label, condition):
    status = "OK" if condition else "FAIL"
    print(f"  [{status}] {label}")
    if not condition:
        FAILURES.append(label)


# ---------------------------------------------------------------------------
# 1) evaluate_reply() egységtesztek
# ---------------------------------------------------------------------------
print("--- evaluate_reply() egységtesztek ---")

score, flags = evaluate_reply("Szia!", "", "general_chat")
check("üres válasz -> empty_or_fallback flag", "empty_or_fallback" in flags)
check("üres válasz -> alacsony pontszám", score <= 40)

score, flags = evaluate_reply("Szia!", "...", "general_chat")
check("'...' placeholder -> empty_or_fallback flag", "empty_or_fallback" in flags)

score, flags = evaluate_reply(
    "Szia, ki vagy?",
    "Szia! Én az MF-AI-Zero vagyok, egy saját, nulláról tanított magyar AI prototípus.",
    "general_chat",
)
check("jó, tiszta válasz -> nincs flag", flags == [])
check("jó, tiszta válasz -> 100 pont", score == 100)

score, flags = evaluate_reply(
    "Írj 5 mondatot az erőről.",
    "Kicsi vagyok.\nAI: Ez egy kitalált folytatás.",
    "sentence_request",
    sentence_info=(5, 1, False),
)
check("kiszivárgott 'AI:' címke -> leaked_label flag", "leaked_label" in flags)

score, flags = evaluate_reply(
    "Írj 3 mondatot a kitartásról.",
    "A kitartás fontos. A kitartás fontos. Más mondat.",
    "sentence_request",
    sentence_info=(3, 3, False),
)
check("ismétlődő mondat -> duplicate_sentence flag", "duplicate_sentence" in flags)

score, flags = evaluate_reply("Köszönöm!", "Ok", "general_chat")
check("nagyon rövid válasz -> too_short flag", "too_short" in flags)

score, flags = evaluate_reply(
    "Írj 5 mondatot az erőről.",
    "Egy mondat. Két mondat. Három mondat.",
    "sentence_request",
    sentence_info=(5, 3, False),
)
check("mondatszám eltérés -> sentence_count_mismatch flag", "sentence_count_mismatch" in flags)
check("mondatszám eltérés -> pontlevonás", score < 100)

score, flags = evaluate_reply(
    "Írj 3 mondatot a célokról.",
    "Egy mondat. Két mondat. Három mondat.",
    "sentence_request",
    sentence_info=(3, 3, True),
)
check("determinisztikus javítás -> deterministic_fix_applied flag", "deterministic_fix_applied" in flags)

score, flags = evaluate_reply("Mi a célod?", "A célom, hogy segítsek.", "general_chat", sentence_info=None)
check("sentence_info=None general_chat-nél nem okoz hibát", isinstance(score, int))

# score mindig 0-100 kozott
for reply in ["", "...", "A A A A A A A", "Rendben mondat egy. Mondat kettő. Mondat kettő."]:
    s, _ = evaluate_reply("teszt", reply, "general_chat")
    check(f"score mindig [0,100] tartományban ({reply[:20]!r})", 0 <= s <= 100)


# ---------------------------------------------------------------------------
# 2) log_feedback() - fájlba írás ellenőrzése (ideiglenes fájlba, NEM az
#    éles learning_log/feedback.jsonl-be)
# ---------------------------------------------------------------------------
print("\n--- log_feedback() fájlba írás teszt ---")

with tempfile.TemporaryDirectory() as tmp_dir:
    tmp_log_path = os.path.join(tmp_dir, "test_feedback.jsonl")

    record1 = log_feedback(
        "Szia, ki vagy?", "Szia! Én az MF-AI-Zero vagyok.", "general_chat", "v0.7",
        100, [], sentence_info=None, log_path=tmp_log_path,
    )
    record2 = log_feedback(
        "Írj 3 mondatot az erőről.", "Egy. Kettő. Három.", "sentence_request", "v0.7c",
        75, ["sentence_count_mismatch"], sentence_info=(3, 3, False), log_path=tmp_log_path,
    )

    check("log_feedback visszaad egy dict-et", isinstance(record1, dict))
    check("a fájl létrejött", os.path.exists(tmp_log_path))

    with open(tmp_log_path, encoding="utf-8") as f:
        lines = [line for line in f if line.strip()]

    check("2 sor került a fájlba (append működik)", len(lines) == 2)

    parsed1 = json.loads(lines[0])
    parsed2 = json.loads(lines[1])

    check("1. rekord user_message helyes", parsed1["user_message"] == "Szia, ki vagy?")
    check("1. rekord tartalmazza a szükséges mezőket", all(
        k in parsed1 for k in (
            "timestamp", "user_message", "ai_reply", "intent", "model_used",
            "reply_length_chars", "reply_length_words", "quality_score", "quality_flags",
        )
    ))
    check("1. rekordnak nincs sentence_requested mezője (sentence_info=None volt)",
          "sentence_requested" not in parsed1)
    check("2. rekordnak van sentence_requested/actual/fixed mezője",
          all(k in parsed2 for k in ("sentence_requested", "sentence_actual", "sentence_fixed")))
    check("2. rekord quality_flags helyes", parsed2["quality_flags"] == ["sentence_count_mismatch"])
    check("ékezetes karakterek nem escapelve (ensure_ascii=False)", "Szia" in lines[0] and "\\u" not in lines[0])


# ---------------------------------------------------------------------------
# 3) Rövid integrációs teszt: a valódi v0.7e router + evaluator + logger
#    láncot futtatjuk pár golden teszten, ideiglenes naplófájlba.
# ---------------------------------------------------------------------------
print("\n--- Integrációs teszt: router + evaluator + logger (valódi modellekkel) ---")

import torch  # noqa: E402

import config  # noqa: E402
from generate import load_model  # noqa: E402
from router import route_and_respond  # noqa: E402

device = torch.device("cpu")
general_model_tuple = load_model(device, config.CHAT_MODEL_PATH)
instruction_model_tuple = load_model(
    device, os.path.join(config.BASE_DIR, "models", "mf_ai_zero_chat_v0_7c.pt")
)
general_model = (*general_model_tuple[:3], device, general_model_tuple[3])
instruction_model = (*instruction_model_tuple[:3], device, instruction_model_tuple[3])

INTEGRATION_CASES = [
    ("Szia, ki vagy?", "general_chat"),
    ("Írj 3 mondatot az erőről.", "sentence_request"),
    ("Viszlát!", "goodbye"),
]

with tempfile.TemporaryDirectory() as tmp_dir:
    tmp_log_path = os.path.join(tmp_dir, "integration_feedback.jsonl")

    for text, expected_intent in INTEGRATION_CASES:
        reply, intent, model_used, sentence_info = route_and_respond(
            general_model, instruction_model, text, temperature=0.6
        )
        check(f"'{text}' -> intent helyes ({expected_intent})", intent == expected_intent)

        score, flags = evaluate_reply(text, reply, intent, sentence_info)
        record = log_feedback(text, reply, intent, model_used, score, flags, sentence_info, log_path=tmp_log_path)

        check(f"'{text}' -> a router válasza változatlan a naplózás után is",
              record["ai_reply"] == reply)
        check(f"'{text}' -> score a [0,100] tartományban", 0 <= score <= 100)

    with open(tmp_log_path, encoding="utf-8") as f:
        integration_lines = [line for line in f if line.strip()]
    check("mindhárom eset bekerült a naplóba", len(integration_lines) == len(INTEGRATION_CASES))


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
