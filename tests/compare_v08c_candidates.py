"""
MF-AI-Zero - v0.8c candidate-osszehasonlito.

Ugyanaz a modszertan, mint compare_v08b_candidates.py: a
test_v07e_router.py teljes tesztkeszletet TOBBSZOR (5x) lefuttatja
mindegyik megadott altalanos modellel, es osszehasonlitja:
  - altalanos chat atlag es MINIMUM (egyetlen futas se essen a kuszob ala)
  - mondatszam pontossag (nem szabad romlania)
  - intent pontossag, parancs/koszones/bucsu (nem szabad romlania)
  - routerhiba (mindig 0-nak kell maradnia)

Ez a szkript NEM modosit semmilyen modellt vagy adatot - csak meri es
riportalja az eredmenyt.

Futtatás:
    python tests/compare_v08c_candidates.py
"""

import os
import statistics
import sys

SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
sys.path.insert(0, SRC_DIR)

import config  # noqa: E402
from test_v07e_router import run_suite  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

RUNS_PER_MODEL = 5
MIN_GENERAL_SINGLE_RUN = 15   # egyetlen futás se essen ez alá
MIN_GENERAL_AVERAGE = 17      # az átlagnak legalább ennyinek kell lennie

MODELS = {
    "v0.7 (jelenlegi alap)": config.CHAT_MODEL_PATH,
    "v0.8b_candidate_a": os.path.join(config.BASE_DIR, "models", "mf_ai_zero_chat_v0_8b_a.pt"),
    "v0.8c_candidate_c": os.path.join(config.BASE_DIR, "models", "mf_ai_zero_chat_v0_8c.pt"),
}


def main():
    summary = {}

    for label, model_path in MODELS.items():
        if not os.path.exists(model_path):
            print(f"KIHAGYVA (nincs ilyen fájl): {label} -> {model_path}")
            continue

        print(f"\n{'=' * 78}\n{label}  ({model_path})\n{'=' * 78}")

        general_scores = []
        sentence_scores = []
        intent_scores = []
        cmd_scores = []
        wrong_model_counts = []
        stable_flags = []

        for run_idx in range(1, RUNS_PER_MODEL + 1):
            result = run_suite(general_model_path=model_path, verbose=False)
            general_scores.append(result["general_ok"])
            sentence_scores.append(result["sentence_ok"])
            intent_scores.append(result["intent_accuracy"])
            cmd_scores.append(result["cmd_ok"])
            wrong_model_counts.append(result["wrong_model_for_non_sentence"])
            stable_flags.append(result["stable"])
            print(f"  futás {run_idx}: általános={result['general_ok']}/20  "
                  f"mondatszám={result['sentence_ok']}/20  "
                  f"parancs={result['cmd_ok']}/10  "
                  f"routerhiba={result['wrong_model_for_non_sentence']}")

        avg = statistics.mean(general_scores)
        mn = min(general_scores)
        mx = max(general_scores)

        summary[label] = {
            "general_scores": general_scores,
            "general_avg": avg,
            "general_min": mn,
            "general_max": mx,
            "sentence_scores": sentence_scores,
            "sentence_avg": statistics.mean(sentence_scores),
            "intent_avg": statistics.mean(intent_scores),
            "cmd_avg": statistics.mean(cmd_scores),
            "wrong_model_total": sum(wrong_model_counts),
        }

        print(f"\n  Általános chat: {general_scores}  ->  átlag={avg:.1f}  min={mn}  max={mx}")
        print(f"  Mondatszám átlag: {statistics.mean(sentence_scores):.1f}/20")
        print(f"  Parancs átlag: {statistics.mean(cmd_scores):.1f}/10")
        print(f"  Routerhiba összesen: {sum(wrong_model_counts)} (elvárt: 0)")

    # ------------------------------------------------------------------
    print(f"\n\n{'#' * 78}\nÖSSZEHASONLÍTÓ TÁBLÁZAT\n{'#' * 78}")
    header = f"{'Modell':<28}{'ált.átlag':<12}{'ált.min':<10}{'mondatsz.átlag':<16}{'parancs.átlag':<14}{'routerhiba':<12}{'megfelel?'}"
    print(header)
    print("-" * len(header))

    best_label = None
    best_avg = -1

    for label, s in summary.items():
        meets_avg = s["general_avg"] >= MIN_GENERAL_AVERAGE
        meets_min = s["general_min"] >= MIN_GENERAL_SINGLE_RUN
        meets_sentence = s["sentence_avg"] >= 19
        meets_cmd = s["cmd_avg"] >= 9
        meets_router = s["wrong_model_total"] == 0
        meets_all = meets_avg and meets_min and meets_sentence and meets_cmd and meets_router

        print(f"{label:<28}{s['general_avg']:<12.1f}{s['general_min']:<10}"
              f"{s['sentence_avg']:<16.1f}{s['cmd_avg']:<14.1f}{s['wrong_model_total']:<12}"
              f"{'IGEN' if meets_all else 'nem'}")

        if meets_all and s["general_avg"] > best_avg:
            best_avg = s["general_avg"]
            best_label = label

    print(f"\nElfogadási küszöbök: átlag >= {MIN_GENERAL_AVERAGE}/20 ÉS minden futás >= "
          f"{MIN_GENERAL_SINGLE_RUN}/20 ÉS mondatszám átlag >= 19/20 ÉS parancs átlag >= 9/10 "
          f"ÉS routerhiba == 0")

    if best_label:
        print(f"\nLegjobb, a küszöböt teljesítő modell: {best_label}")
        print("STÁTUSZ: STABIL")
    else:
        print("\nEgyik modell sem teljesíti maradéktalanul a küszöböt.")
        print("STÁTUSZ: NEM STABIL")

    return summary, best_label


if __name__ == "__main__":
    main()
