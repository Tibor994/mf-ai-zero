"""
MF-AI-Zero - v1.4.1 választervező teszt (response_planner.py +
response_style.py apply_structure() + guard.py integráció).

Hat rész:
  1. detect_response_type() - a 8 típus felismerése, kifejezetten a
     feladatban kért esetekkel: magyarázat -> explanation, "írd
     lépésekben" -> step_by_step, "foglaljad össze" -> summary, sima laza
     beszélgetés -> casual_chat.
  2. build_response_plan() - a típushoz tartozó instrukció-konfiguráció.
  3. build_response_plan_prompt_context() - natív formátum.
  4. apply_structure() (response_style.py) - lépés-/lista-tördelés,
     összegzés-vágás - "NEM változtat tényeket" teszt: minden eredeti
     mondat szó szerint megmarad, csak az elrendezés változik.
  5. Integrációs teszt: guarded_route_and_respond() valódi candidate A
     modellel - guard_info tartalmazza a kötelező mezőket
     (response_plan_used/response_type/target_length/wants_steps/
     wants_list); --no-response-planner kikapcsolja; a guard kategória-
     rendszere (retry/fallback) továbbra is működik.

Futtatás:
    python tests/test_v1_4_1_response_planner.py
"""

import os
import sys

SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
sys.path.insert(0, SRC_DIR)

from response_planner import (  # noqa: E402
    RESPONSE_TYPES,
    build_response_plan,
    build_response_plan_prompt_context,
    detect_response_type,
)
from response_style import apply_structure, apply_style  # noqa: E402

FAILURES = []


def check(label, condition):
    status = "OK" if condition else "FAIL"
    print(f"  [{status}] {label}")
    if not condition:
        FAILURES.append(label)


# ---------------------------------------------------------------------------
# 1) detect_response_type()
# ---------------------------------------------------------------------------
print("--- detect_response_type() teszt ---")

check("'Magyarázd el, hogyan működik a router.' -> explanation",
      detect_response_type("Magyarázd el, hogyan működik a router.") == "explanation")
check("'Miért van az, hogy néha furán válaszolsz?' -> explanation",
      detect_response_type("Miért van az, hogy néha furán válaszolsz?") == "explanation")

check("'Írd le lépésekben, hogyan tanítsam a modellt.' -> step_by_step",
      detect_response_type("Írd le lépésekben, hogyan tanítsam a modellt.") == "step_by_step")
check("'Lépésről lépésre magyarázd el a telepítést.' -> step_by_step",
      detect_response_type("Lépésről lépésre magyarázd el a telepítést.") == "step_by_step")

check("'Foglaljad össze röviden a projektet.' -> summary",
      detect_response_type("Foglaljad össze röviden a projektet.") == "summary")
check("'Foglald össze egy mondatban.' -> summary",
      detect_response_type("Foglald össze egy mondatban.") == "summary")

check("'Sorolj fel pár tudásbázis kategóriát.' -> list",
      detect_response_type("Sorolj fel pár tudásbázis kategóriát.") == "list")

check("'Hogy vagy?' -> casual_chat", detect_response_type("Hogy vagy?") == "casual_chat")
check("'Szia, mizu?' -> casual_chat", detect_response_type("Szia, mizu?") == "casual_chat")

check("'Melyiket válasszam, a candidate A-t vagy B-t?' -> decision_help",
      detect_response_type("Melyiket válasszam, a candidate A-t vagy B-t?") == "decision_help")
check("'Van hiba a kódomban, segítenél debug-olni?' -> code_help",
      detect_response_type("Van hiba a kódomban, segítenél debug-olni?") == "code_help")

check("üres szöveg -> casual_chat (biztonságos alapértelmezés)", detect_response_type("") == "casual_chat")


# ---------------------------------------------------------------------------
# 2) build_response_plan()
# ---------------------------------------------------------------------------
print("\n--- build_response_plan() teszt ---")

plan = build_response_plan("Írd le lépésekben, hogyan tanítsam a modellt.")
check("step_by_step terv -> wants_steps=True", plan["wants_steps"] is True)
check("step_by_step terv -> wants_list=False", plan["wants_list"] is False)

plan_list = build_response_plan("Sorolj fel pár tudásbázis kategóriát.")
check("list terv -> wants_list=True", plan_list["wants_list"] is True)

plan_summary = build_response_plan("Foglaljad össze röviden a projektet.")
check("summary terv -> wants_summary=True, target_length=short",
      plan_summary["wants_summary"] is True and plan_summary["target_length"] == "short")

plan_explanation = build_response_plan("Magyarázd el, hogyan működik a router.")
check("explanation terv -> target_length=long", plan_explanation["target_length"] == "long")

for rtype in RESPONSE_TYPES:
    p = build_response_plan("teszt szöveg " + rtype)
    check(f"minden RESPONSE_TYPES elemhez van konfiguráció (itt csak a mezők megléte számít: {rtype})",
          all(k in p for k in ("response_type", "target_length", "wants_steps", "wants_list",
                                "wants_summary", "wants_casual_tone")))


# ---------------------------------------------------------------------------
# 3) build_response_plan_prompt_context()
# ---------------------------------------------------------------------------
print("\n--- build_response_plan_prompt_context() teszt ---")

ctx = build_response_plan_prompt_context(build_response_plan("Magyarázd el, hogyan működik a router."))
check("build_response_plan_prompt_context() 'User:'/'AI:' natív formátumú",
      ctx.startswith("User:") and "\nAI:" in ctx and ctx.endswith("\n\n"))
check("build_response_plan_prompt_context(None) üres string", build_response_plan_prompt_context(None) == "")


# ---------------------------------------------------------------------------
# 4) apply_structure() - "NEM változtat tényeket"
# ---------------------------------------------------------------------------
print("\n--- apply_structure() teszt (nem változtat tényeket) ---")

three_sentences = "Ez az első lépés. Ez a második lépés. Ez a harmadik lépés."
steps_plan = {"wants_steps": True, "wants_list": False, "wants_summary": False}
structured = apply_structure(three_sentences, steps_plan)
check("wants_steps -> számozott lista lesz", structured.startswith("1. ") and "\n2. " in structured)
check("wants_steps -> minden EREDETI mondat szó szerint megmarad", all(
    s.strip() in structured for s in ["Ez az első lépés.", "Ez a második lépés.", "Ez a harmadik lépés."]
))

list_plan = {"wants_steps": False, "wants_list": True, "wants_summary": False}
listed = apply_structure(three_sentences, list_plan)
check("wants_list -> pontokba szedett lista lesz", listed.startswith("- ") and "\n- " in listed)
check("wants_list -> minden EREDETI mondat szó szerint megmarad", all(
    s.strip() in listed for s in ["Ez az első lépés.", "Ez a második lépés.", "Ez a harmadik lépés."]
))

summary_plan = {"wants_steps": False, "wants_list": False, "wants_summary": True}
summarized = apply_structure(three_sentences, summary_plan)
check("wants_summary -> csak az első 2 mondat marad", "harmadik lépés" not in summarized
      and "első lépés" in summarized and "második lépés" in summarized)

single_sentence = "Csak egy mondat van itt."
check("egyetlen mondatnál wants_steps NEM formáz (nincs mit lépésekre bontani)",
      apply_structure(single_sentence, steps_plan) == single_sentence)
check("egyetlen mondatnál wants_list NEM formáz", apply_structure(single_sentence, list_plan) == single_sentence)

check("plan=None -> a szöveg változatlan", apply_structure(three_sentences, None) == three_sentences)

styled, info = apply_style(three_sentences, plan=steps_plan)
check("apply_style() plan-nel is helyesen működik, style_used=True", info["style_used"] is True)


# ---------------------------------------------------------------------------
# 5) Integrációs teszt: guarded_route_and_respond() valódi candidate A modellel
# ---------------------------------------------------------------------------
print("\n--- Integrációs teszt: guarded_route_and_respond() + response_planner ---")

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

    # a) explanation kérdés -> response_type='explanation'
    reply_a, intent_a, model_used_a, sentence_info_a, guard_info_a = guarded_route_and_respond(
        general_model, instruction_model, "Magyarázd el, miért válaszolsz néha furán.", temperature=0.6,
        response_planner_enabled=True,
    )
    check("magyarázat kérésnél guard_info['response_type']=='explanation'",
          guard_info_a["response_type"] == "explanation")
    check("response_plan_used=True", guard_info_a["response_plan_used"] is True)
    check("guard_info tartalmazza az összes kötelező mezőt", all(
        k in guard_info_a for k in ("response_plan_used", "response_type", "target_length",
                                     "wants_steps", "wants_list")
    ))

    # b) "írd lépésekben" -> response_type='step_by_step'
    reply_b, intent_b, model_used_b, sentence_info_b, guard_info_b = guarded_route_and_respond(
        general_model, instruction_model, "Írd le lépésekben, hogyan tanítsam a modellt.", temperature=0.6,
        response_planner_enabled=True,
    )
    check("'írd lépésekben' kérésnél response_type='step_by_step'",
          guard_info_b["response_type"] == "step_by_step" and guard_info_b["wants_steps"] is True)

    # c) "foglaljad össze" -> response_type='summary'
    reply_c, intent_c, model_used_c, sentence_info_c, guard_info_c = guarded_route_and_respond(
        general_model, instruction_model, "Foglaljad össze röviden, ki vagy.", temperature=0.6,
        response_planner_enabled=True,
    )
    check("'foglaljad össze' kérésnél response_type='summary'", guard_info_c["response_type"] == "summary")

    # d) sima laza beszélgetés -> response_type='casual_chat'
    reply_d, intent_d, model_used_d, sentence_info_d, guard_info_d = guarded_route_and_respond(
        general_model, instruction_model, "Hogy vagy ma?", temperature=0.6,
        response_planner_enabled=True,
    )
    check("sima laza beszélgetésnél response_type='casual_chat'", guard_info_d["response_type"] == "casual_chat")

    # e) --no-response-planner -> response_plan_used marad False
    reply_e, intent_e, model_used_e, sentence_info_e, guard_info_e = guarded_route_and_respond(
        general_model, instruction_model, "Magyarázd el, miért válaszolsz néha furán.", temperature=0.6,
        response_planner_enabled=False,
    )
    check("response_planner_enabled=False -> response_plan_used=False", guard_info_e["response_plan_used"] is False)
    check("response_planner_enabled=False -> response_type=None", guard_info_e["response_type"] is None)

    # f) a guard kategória-rendszere (on-topic/retry/fallback) továbbra is működik
    check("a választervező mellett a guard többi mezője is jelen van", all(
        k in guard_info_a for k in (
            "detected_intent", "expected_answer_type", "guard_triggered",
            "memory_used", "knowledge_used", "web_used", "style_used",
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
