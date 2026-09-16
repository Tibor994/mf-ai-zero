"""
MF-AI-Zero - v0.7e/v0.8 STABILITAS-DIAGNOZTIKA (nem pass/fail teszt).

Ez a szkript NEM módosít semmit (modellt, adatot, küszöböt) - kizárólag
MEGFIGYEL és RIPORTÁL, hogy pontosan megértsük, miért ingadozik a v0.7e
"általános chat" mérőszáma a golden_chat_tests.json 20 kérdésén.

Két mód:
  1. UNSEEDED (véletlen) mód: minden kérdést N-szer futtat, rögzített
     seed NÉLKÜL - ez azt mutatja meg, mennyire változékony a modell
     válasza természetes használat közben.
  2. SEEDED (determinisztikus) mód: minden kérdést M különböző, FIX
     seeddel futtat - ez szétválasztja, hogy egy adott kérdés "mindig"
     elbukik-e (rendszeres hiba), vagy csak néhány szerencsétlen
     véletlen mintavételnél (tiszta random ingadozás). Egy determinizmus-
     ellenőrzés is fut: ugyanazt a seedet kétszer lefuttatva pontosan
     ugyanazt a választ kell adnia - ha nem, az magában a mintavételi
     folyamatban van egy nem várt, kontrollálatlan véletlen elem.

Futtatás:
    python tests/diagnose_v07e_general_chat.py
    python tests/diagnose_v07e_general_chat.py --model-path models/mf_ai_zero_chat_v0_8b_a.pt --out tests/diagnose_v08b_a_results.json

A --model-path kapcsoló az ÁLTALÁNOS modellt cseréli (pl. egy v0.8b
candidate kiértékeléséhez) - a router.py és a mondatszám-modell (v0.7c)
nem változik.
"""

import argparse
import json
import os
import sys
from collections import defaultdict

SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
sys.path.insert(0, SRC_DIR)

import torch  # noqa: E402

import config  # noqa: E402
from generate import load_model  # noqa: E402
from router import route_and_respond  # noqa: E402

TESTS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "golden_chat_tests.json")

UNSEEDED_REPEATS = 8
SEEDED_SEEDS = list(range(101, 109))  # 8 fix seed


def load_general_tests():
    with open(TESTS_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return [t for t in data["tests"] if t["category"] == "general"]


def keyword_hit(reply, keywords):
    reply_low = reply.lower()
    return any(kw in reply_low for kw in keywords)


def main():
    parser = argparse.ArgumentParser(description="v0.7e altalanos chat stabilitas-diagnosztika.")
    parser.add_argument(
        "--model-path", type=str, default=None,
        help="Az ÁLTALÁNOS modell felülbírálása (alapból config.CHAT_MODEL_PATH, azaz v0.7).",
    )
    parser.add_argument(
        "--out", type=str, default=None,
        help="Hova mentse a részletes JSON eredményt (alapból tests/diagnose_v07e_results.json).",
    )
    args = parser.parse_args()
    general_model_path = args.model_path or config.CHAT_MODEL_PATH

    tests = load_general_tests()
    device = torch.device("cpu")

    print("Modellek betöltése...")
    g_model, g_stoi, g_itos, g_fmt = load_model(device, general_model_path)
    i_model, i_stoi, i_itos, i_fmt = load_model(
        device, os.path.join(config.BASE_DIR, "models", "mf_ai_zero_chat_v0_7c.pt")
    )
    general_model = (g_model, g_stoi, g_itos, device, g_fmt)
    instruction_model = (i_model, i_stoi, i_itos, device, i_fmt)
    print("Kész.\n")

    # -----------------------------------------------------------------
    # 1) UNSEEDED mód: minden kérdés UNSEEDED_REPEATS-szer, seed nélkül
    # -----------------------------------------------------------------
    print(f"{'=' * 78}\n1) UNSEEDED MÓD - {UNSEEDED_REPEATS} futás/kérdés, seed NÉLKÜL\n{'=' * 78}")

    unseeded_results = {}  # id -> {"passes": int, "fails": int, "wrong_model": int, "examples_fail": [...], "examples_pass": [...]}

    for t in tests:
        passes, fails, wrong_model = 0, 0, 0
        examples_fail, examples_pass = [], []
        for _ in range(UNSEEDED_REPEATS):
            reply, intent, model_used, _ = route_and_respond(
                general_model, instruction_model, t["text"], temperature=0.6
            )
            if model_used != "v0.7":
                wrong_model += 1
            hit = keyword_hit(reply, t["keywords"])
            if hit:
                passes += 1
                if len(examples_pass) < 2:
                    examples_pass.append(reply)
            else:
                fails += 1
                if len(examples_fail) < 3:
                    examples_fail.append(reply)
        unseeded_results[t["id"]] = {
            "text": t["text"], "keywords": t["keywords"],
            "passes": passes, "fails": fails, "wrong_model": wrong_model,
            "examples_fail": examples_fail, "examples_pass": examples_pass,
        }
        print(f"  {t['id']:<5} bukás: {fails}/{UNSEEDED_REPEATS}  \"{t['text']}\"")

    # -----------------------------------------------------------------
    # 2) SEEDED mód: minden kérdés a SEEDED_SEEDS mindegyikével, fixen
    # -----------------------------------------------------------------
    print(f"\n{'=' * 78}\n2) SEEDED MÓD - {len(SEEDED_SEEDS)} fix seed/kérdés\n{'=' * 78}")

    seeded_results = {}
    determinism_ok = True

    for t in tests:
        per_seed = {}
        for seed in SEEDED_SEEDS:
            torch.manual_seed(seed)
            reply, intent, model_used, _ = route_and_respond(
                general_model, instruction_model, t["text"], temperature=0.6
            )
            hit = keyword_hit(reply, t["keywords"])
            per_seed[seed] = (hit, reply, model_used)
        fails = sum(1 for hit, _, _ in per_seed.values() if not hit)
        seeded_results[t["id"]] = {"text": t["text"], "per_seed": per_seed, "fails": fails}
        print(f"  {t['id']:<5} bukás: {fails}/{len(SEEDED_SEEDS)}  \"{t['text']}\"")

    # Determinizmus-ellenőrzés: 3 kérdésnél megismételjük UGYANAZT a seedet,
    # és megnézzük, hogy tényleg bitre-pontosan ugyanazt a választ adja-e.
    print(f"\n{'=' * 78}\nDETERMINIZMUS-ELLENŐRZÉS (ugyanaz a seed -> ugyanaz a válasz?)\n{'=' * 78}")
    for t in tests[:3]:
        torch.manual_seed(999)
        reply_a, *_ = route_and_respond(general_model, instruction_model, t["text"], temperature=0.6)
        torch.manual_seed(999)
        reply_b, *_ = route_and_respond(general_model, instruction_model, t["text"], temperature=0.6)
        same = reply_a == reply_b
        determinism_ok = determinism_ok and same
        print(f"  {t['id']:<5} seed=999 kétszer ugyanaz: {'IGEN' if same else 'NEM'}")
        if not same:
            print(f"        1. futás: {reply_a}")
            print(f"        2. futás: {reply_b}")

    # -----------------------------------------------------------------
    # 3) Részletes hibajelentés
    # -----------------------------------------------------------------
    print(f"\n{'=' * 78}\n3) RÉSZLETES HIBAJELENTÉS (csak azok a kérdések, ahol volt bukás)\n{'=' * 78}")

    for t in tests:
        u = unseeded_results[t["id"]]
        s = seeded_results[t["id"]]
        if u["fails"] == 0 and s["fails"] == 0:
            continue
        print(f"\n--- {t['id']}: \"{t['text']}\" ---")
        print(f"    Elvárt jelleg (kulcsszavak): {t['keywords']}")
        print(f"    Unseeded bukás: {u['fails']}/{UNSEEDED_REPEATS}   Seeded bukás: {s['fails']}/{len(SEEDED_SEEDS)}")
        print(f"    Hibás modell válaszolt (nem v0.7): {u['wrong_model']}/{UNSEEDED_REPEATS}")
        if u["examples_fail"]:
            print("    Példa BUKOTT válasz(ok):")
            for ex in u["examples_fail"]:
                print(f"      - {ex}")
        if u["examples_pass"]:
            print("    Példa SIKERES válasz:")
            for ex in u["examples_pass"][:1]:
                print(f"      - {ex}")

    # -----------------------------------------------------------------
    # Összesítés
    # -----------------------------------------------------------------
    total_unseeded_fails = sum(r["fails"] for r in unseeded_results.values())
    total_unseeded_runs = len(tests) * UNSEEDED_REPEATS
    total_seeded_fails = sum(r["fails"] for r in seeded_results.values())
    total_seeded_runs = len(tests) * len(SEEDED_SEEDS)
    total_wrong_model = sum(r["wrong_model"] for r in unseeded_results.values())

    always_fail = [t["id"] for t in tests if unseeded_results[t["id"]]["fails"] == UNSEEDED_REPEATS
                   and seeded_results[t["id"]]["fails"] == len(SEEDED_SEEDS)]
    never_fail = [t["id"] for t in tests if unseeded_results[t["id"]]["fails"] == 0
                  and seeded_results[t["id"]]["fails"] == 0]
    sometimes_fail = [t["id"] for t in tests if t["id"] not in always_fail and t["id"] not in never_fail]

    print(f"\n{'=' * 78}\nÖSSZESÍTÉS\n{'=' * 78}")
    print(f"Unseeded összes bukás: {total_unseeded_fails}/{total_unseeded_runs} "
          f"({100 * total_unseeded_fails / total_unseeded_runs:.1f}%)")
    print(f"Seeded összes bukás:   {total_seeded_fails}/{total_seeded_runs} "
          f"({100 * total_seeded_fails / total_seeded_runs:.1f}%)")
    print(f"Rossz modell válaszolt általános kérdésre: {total_wrong_model}/{total_unseeded_runs} eset")
    print(f"Determinizmus (ugyanaz a seed -> ugyanaz a válasz): {'IGEN' if determinism_ok else 'NEM'}")
    print(f"\nMINDIG bukik (seed-független, valódi hiány): {always_fail if always_fail else '(nincs ilyen)'}")
    print(f"SOHA nem bukik (megbízható): {never_fail}")
    print(f"NÉHA bukik (seed/mintavétel-függő): {sometimes_fail if sometimes_fail else '(nincs ilyen)'}")

    # Eredmények mentése, hogy később is visszanézhetők legyenek
    out_path = args.out or os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "diagnose_v07e_results.json"
    )
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({
            "unseeded_repeats": UNSEEDED_REPEATS,
            "seeded_seeds": SEEDED_SEEDS,
            "determinism_ok": determinism_ok,
            "unseeded_results": unseeded_results,
            "seeded_results": {k: {"text": v["text"], "fails": v["fails"]} for k, v in seeded_results.items()},
            "always_fail": always_fail,
            "never_fail": never_fail,
            "sometimes_fail": sometimes_fail,
        }, f, ensure_ascii=False, indent=2)
    print(f"\nRészletes eredmény elmentve: {out_path}")


if __name__ == "__main__":
    main()
