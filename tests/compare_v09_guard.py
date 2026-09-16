"""
MF-AI-Zero - v0.9-guard összehasonlító.

A v0.8b/v0.8c körök bebizonyították, hogy ÚJRATANÍTÁSSAL nem lehet
megbízhatóan stabilizálni ezt a kis modellt (lásd a v0.8c riportot: minél
több témát próbálunk egyszerre "megjavítani" új adattal, annál inkább
szétesik az általános koherencia).

Ez a szkript ezért NEM új modellt hasonlít össze, hanem ugyanazt a
candidate A modellt HÁROM módon futtatja végig a golden tesztkészleten:
  1. v0.7 (jelenlegi alap)           - router, guard NÉLKÜL
  2. v0.8b_candidate_a (guard nélkül) - router, guard NÉLKÜL
  3. v0.8b_candidate_a + guard/fallback - router.route_and_respond() +
     guard.guarded_route_and_respond() (kategória-felismerés, evaluator-
     ellenőrzés, 1x retry, kontrollált fallback - lásd guard.py)

Ugyanaz a mérőszám (test_v07e_router.run_suite, azonos küszöbök), 5x
lefuttatva mindegyik változatnál, hogy az átlag ÉS a minimum is látszódjon.

Ez a szkript NEM modosit semmilyen modellt vagy adatot - csak meri és
riportalja az eredmenyt.

Futtatás:
    python tests/compare_v09_guard.py
"""

import os
import statistics
import sys

SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
sys.path.insert(0, SRC_DIR)

import config  # noqa: E402
from guard import guarded_route_and_respond  # noqa: E402
from test_v07e_router import run_suite  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

RUNS_PER_MODEL = 5
MIN_GENERAL_SINGLE_RUN = 15   # egyetlen futás se essen ez alá
MIN_GENERAL_AVERAGE = 17      # az átlagnak legalább ennyinek kell lennie
MIN_SENTENCE_AVG = 19
MIN_CMD_AVG = 9

CANDIDATE_A_PATH = os.path.join(config.BASE_DIR, "models", "mf_ai_zero_chat_v0_8b_a.pt")


def _guarded_responder(general_model, instruction_model, text, temperature=0.6):
    """Adapter: guarded_route_and_respond() 5 elemű visszatérését a
    run_suite() által elvárt 4 elemű (reply, intent, model_used,
    sentence_info) alakra vágja - a guard_info-t itt eldobjuk, mert ez a
    szkript csak a végső válasz minőségét méri, nem a guard belső
    statisztikáit (azokat a learning_log rögzíti, lásd tests/test_v09_guard.py)."""
    reply, intent, model_used, sentence_info, _guard_info = guarded_route_and_respond(
        general_model, instruction_model, text, temperature=temperature
    )
    return reply, intent, model_used, sentence_info


RUNS = [
    ("v0.7 (jelenlegi alap)", config.CHAT_MODEL_PATH, None),
    ("v0.8b_candidate_a (guard nélkül)", CANDIDATE_A_PATH, None),
    ("v0.8b_candidate_a + guard/fallback", CANDIDATE_A_PATH, _guarded_responder),
]


def main():
    summary = {}

    for label, model_path, respond_fn in RUNS:
        if not os.path.exists(model_path):
            print(f"KIHAGYVA (nincs ilyen fájl): {label} -> {model_path}")
            continue

        print(f"\n{'=' * 78}\n{label}  ({model_path})\n{'=' * 78}")

        general_scores, sentence_scores, cmd_scores, wrong_model_counts = [], [], [], []

        for run_idx in range(1, RUNS_PER_MODEL + 1):
            result = run_suite(general_model_path=model_path, verbose=False, respond_fn=respond_fn)
            general_scores.append(result["general_ok"])
            sentence_scores.append(result["sentence_ok"])
            cmd_scores.append(result["cmd_ok"])
            wrong_model_counts.append(result["wrong_model_for_non_sentence"])
            print(f"  futás {run_idx}: általános={result['general_ok']}/20  "
                  f"mondatszám={result['sentence_ok']}/20  "
                  f"parancs={result['cmd_ok']}/10  "
                  f"routerhiba={result['wrong_model_for_non_sentence']}")

        avg = statistics.mean(general_scores)
        mn = min(general_scores)

        summary[label] = {
            "general_scores": general_scores,
            "general_avg": avg,
            "general_min": mn,
            "sentence_avg": statistics.mean(sentence_scores),
            "cmd_avg": statistics.mean(cmd_scores),
            "wrong_model_total": sum(wrong_model_counts),
        }

        print(f"\n  Általános chat: {general_scores}  ->  átlag={avg:.1f}  min={mn}")
        print(f"  Mondatszám átlag: {statistics.mean(sentence_scores):.1f}/20")
        print(f"  Parancs átlag: {statistics.mean(cmd_scores):.1f}/10")
        print(f"  Routerhiba összesen: {sum(wrong_model_counts)} (elvárt: 0)")

    # ------------------------------------------------------------------
    print(f"\n\n{'#' * 78}\nÖSSZEHASONLÍTÓ TÁBLÁZAT\n{'#' * 78}")
    header = f"{'Változat':<38}{'ált.átlag':<12}{'ált.min':<10}{'mondatsz.':<12}{'parancs':<10}{'routerhiba':<12}{'megfelel?'}"
    print(header)
    print("-" * len(header))

    best_label = None
    best_avg = -1

    for label, s in summary.items():
        meets_avg = s["general_avg"] >= MIN_GENERAL_AVERAGE
        meets_min = s["general_min"] >= MIN_GENERAL_SINGLE_RUN
        meets_sentence = s["sentence_avg"] >= MIN_SENTENCE_AVG
        meets_cmd = s["cmd_avg"] >= MIN_CMD_AVG
        meets_router = s["wrong_model_total"] == 0
        meets_all = meets_avg and meets_min and meets_sentence and meets_cmd and meets_router

        print(f"{label:<38}{s['general_avg']:<12.1f}{s['general_min']:<10}"
              f"{s['sentence_avg']:<12.1f}{s['cmd_avg']:<10.1f}{s['wrong_model_total']:<12}"
              f"{'IGEN' if meets_all else 'nem'}")

        if meets_all and s["general_avg"] > best_avg:
            best_avg = s["general_avg"]
            best_label = label

    print(f"\nElfogadási küszöbök: átlag >= {MIN_GENERAL_AVERAGE}/20 ÉS minden futás >= "
          f"{MIN_GENERAL_SINGLE_RUN}/20 ÉS mondatszám átlag >= {MIN_SENTENCE_AVG}/20 ÉS "
          f"parancs átlag >= {MIN_CMD_AVG}/10 ÉS routerhiba == 0")

    if best_label:
        print(f"\nLegjobb, a küszöböt teljesítő változat: {best_label}")
        print("STÁTUSZ: STABIL")
    else:
        print("\nEgyik változat sem teljesíti maradéktalanul a küszöböt.")
        print("STÁTUSZ: NEM STABIL")

    return summary, best_label


if __name__ == "__main__":
    main()
