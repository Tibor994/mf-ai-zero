"""
MF-AI-Zero - v0.7e router regressziós teszt.

A tests/golden_chat_tests.json fix tesztkészletén ellenőrzi:
  1. az intent-felismerés (detect_intent) pontosságát,
  2. hogy általános kérdésre TÉNYLEG a v0.7 modell válaszol-e, és a
     válasz tartalmilag elfogadható-e (kulcsszó-egyezés),
  3. hogy mondatszám-kérésre TÉNYLEG a v0.7c modell válaszol-e, és a
     végeredmény pontosan a kért mondatszámból áll-e,
  4. a parancs/köszönés/búcsú intent-felismerést.

A végén táblázatban kiírja az eredményt, és a feladatban rögzített
elfogadási feltételek alapján STABIL / NEM STABIL státuszt ad.

Futtatás:
    python tests/test_v07e_router.py
    python tests/test_v07e_router.py --model-path models/mf_ai_zero_chat_v0_8b_a.pt

A --model-path kapcsoló ELÉG az ÁLTALÁNOS (general_chat/greeting/goodbye/
command) modell cseréjéhez, pl. egy v0.8b candidate kiértékeléséhez - a
mondatszám-modell (v0.7c) és a router.py logikája nem változik. Alapból
(kapcsoló nélkül) pontosan úgy fut, mint eddig (config.CHAT_MODEL_PATH,
azaz a v0.7 modell).
"""

import argparse
import json
import os
import sys

SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
sys.path.insert(0, SRC_DIR)

import torch  # noqa: E402

import config  # noqa: E402
from generate import load_model  # noqa: E402
from router import detect_intent, route_and_respond  # noqa: E402

TESTS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "golden_chat_tests.json")

# Elfogadási feltételek (a feladat specifikációja szerint)
MIN_INTENT_ACCURACY = 0.95
MIN_GENERAL_OK = 15  # / 20
MIN_SENTENCE_OK = 19  # / 20
MIN_CMD_OK = 9  # / 10


def load_tests():
    with open(TESTS_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return data["tests"]


def run_suite(general_model_path=None, verbose=True, respond_fn=None):
    """Lefuttatja a teljes tesztkészletet, és visszaad egy eredmény-dict-et
    (ez teszi lehetővé, hogy más szkriptek - pl. egy candidate-összehasonlító
    - programból, ismételve hívják, kiírás nélkül is).

    respond_fn: opcionális, (general_model, instruction_model, text,
    temperature=0.6) -> (reply, intent, model_used, sentence_info) aláírású
    függvény, ami a router.route_and_respond()-ot helyettesíti - pl. a
    guard.guarded_route_and_respond() köré írt adapter, hogy UGYANAZZAL a
    mérőszámmal (golden_chat_tests.json, azonos küszöbök) legyen
    összehasonlítható a guard/fallback réteggel kiegészített válasz is.
    Alapból (None) a szokásos route_and_respond fut, változatlan
    viselkedéssel."""
    responder = respond_fn or route_and_respond
    general_model_path = general_model_path or config.CHAT_MODEL_PATH
    tests = load_tests()
    if verbose:
        print(f"Betöltött tesztek: {len(tests)}\n")

    device = torch.device("cpu")
    if verbose:
        print(f"Modellek betöltése (általános: {general_model_path}, mondatszám: v0.7c)...")
    g_model, g_stoi, g_itos, g_fmt = load_model(device, general_model_path)
    i_model, i_stoi, i_itos, i_fmt = load_model(
        device, os.path.join(config.BASE_DIR, "models", "mf_ai_zero_chat_v0_7c.pt")
    )
    general_model = (g_model, g_stoi, g_itos, device, g_fmt)
    instruction_model = (i_model, i_stoi, i_itos, device, i_fmt)
    if verbose:
        print("Kész.\n")

    intent_correct = 0
    general_ok = 0
    general_total = 0
    sentence_ok = 0
    sentence_total = 0
    cmd_ok = 0
    cmd_total = 0
    wrong_model_for_non_sentence = 0  # v0.7c soha ne válaszoljon altalanos kerdesre

    rows = []

    for t in tests:
        text = t["text"]
        expected_intent = t["expected_intent"]
        category = t["category"]

        detected = detect_intent(text)
        intent_hit = detected == expected_intent
        if intent_hit:
            intent_correct += 1

        if category == "command_greeting_goodbye":
            cmd_total += 1
            if intent_hit:
                cmd_ok += 1
            rows.append((t["id"], category, text, expected_intent, detected, "-", "-"))
            continue

        # general es sentence_request esetén ténylegesen le is futtatjuk a routert
        # (vagy a respond_fn-nel helyettesített változatot, pl. guard+fallback)
        reply, routed_intent, model_used, sentence_info = responder(
            general_model, instruction_model, text, temperature=0.6
        )

        if category == "general":
            general_total += 1
            # "v0.7" a router belső elnevezése az általános modellre, függetlenül
            # attól, melyik checkpointot töltöttük be ide (pl. egy v0.8b candidate-ot)
            if model_used != "v0.7":
                wrong_model_for_non_sentence += 1
            reply_low = reply.lower()
            keyword_hit = any(kw in reply_low for kw in t.get("keywords", []))
            if keyword_hit:
                general_ok += 1
            rows.append((t["id"], category, text, expected_intent, detected,
                         "OK" if keyword_hit else "X", f"[{model_used}] {reply[:70]}"))

        elif category == "sentence_request":
            sentence_total += 1
            requested_n, actual_n, fixed = sentence_info
            exact = actual_n == requested_n
            if exact:
                sentence_ok += 1
            note = f"kért={requested_n} kapott={actual_n}" + (" (javítva)" if fixed else "")
            rows.append((t["id"], category, text, expected_intent, detected,
                         "OK" if exact else "X", f"[{model_used}] {note}"))

    intent_accuracy = intent_correct / len(tests)

    checks = {
        "intent_accuracy": intent_accuracy >= MIN_INTENT_ACCURACY,
        "general_chat": general_ok >= MIN_GENERAL_OK,
        "sentence_count": sentence_ok >= MIN_SENTENCE_OK,
        "command_greeting_goodbye": cmd_ok >= MIN_CMD_OK,
        "no_wrong_model_routing": wrong_model_for_non_sentence == 0,
    }
    stable = all(checks.values())

    if verbose:
        # --- Részletes táblázat ---
        print(f"{'ID':<5}{'kategória':<22}{'szöveg':<45}{'elvárt':<16}{'detekt.':<16}{'talált':<7}megjegyzés")
        print("-" * 150)
        for row_id, category, text, expected, detected, hit, note in rows:
            text_short = (text[:42] + "...") if len(text) > 45 else text
            print(f"{row_id:<5}{category:<22}{text_short:<45}{expected:<16}{detected:<16}{hit:<7}{note}")

        print(f"\n{'=' * 78}\nÖSSZESÍTETT EREDMÉNY\n{'=' * 78}")
        print(f"Intent-felismerés pontossága: {intent_correct}/{len(tests)} = {intent_accuracy * 100:.1f}%  (elvárt: >= {MIN_INTENT_ACCURACY * 100:.0f}%)")
        print(f"Általános chat sikerarány:    {general_ok}/{general_total}  (elvárt: >= {MIN_GENERAL_OK}/20)")
        print(f"Mondatszám pontosság:         {sentence_ok}/{sentence_total}  (elvárt: >= {MIN_SENTENCE_OK}/20)")
        print(f"Parancs/köszönés/búcsú:       {cmd_ok}/{cmd_total}  (elvárt: >= {MIN_CMD_OK}/10)")
        print(f"v0.7c tévesen válaszolt általános kérdésre: {wrong_model_for_non_sentence} eset (elvárt: 0)")

        print("\nElfogadási feltételek:")
        for name, passed in checks.items():
            print(f"  [{'PASS' if passed else 'FAIL'}] {name}")

        print(f"\n{'#' * 78}")
        print(f"STÁTUSZ: {'STABIL' if stable else 'NEM STABIL'}")
        print(f"{'#' * 78}")

    return {
        "stable": stable,
        "checks": checks,
        "intent_accuracy": intent_accuracy,
        "general_ok": general_ok,
        "general_total": general_total,
        "sentence_ok": sentence_ok,
        "sentence_total": sentence_total,
        "cmd_ok": cmd_ok,
        "cmd_total": cmd_total,
        "wrong_model_for_non_sentence": wrong_model_for_non_sentence,
        "rows": rows,
    }


def main():
    parser = argparse.ArgumentParser(description="MF-AI-Zero v0.7e router regressziós teszt.")
    parser.add_argument(
        "--model-path", type=str, default=None,
        help="Az ÁLTALÁNOS (general_chat) modell felülbírálása (alapból a v0.7 / "
        "config.CHAT_MODEL_PATH). A mondatszám-modell (v0.7c) és a router.py "
        "nem változik.",
    )
    args = parser.parse_args()
    result = run_suite(general_model_path=args.model_path, verbose=True)
    return result["stable"]


if __name__ == "__main__":
    main()
