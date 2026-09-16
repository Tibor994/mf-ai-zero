"""
MF-AI-Zero - v0.9 rövid memória teszt (memory.py + guard.py integráció).

Négy rész:
  1. detect_followup() - visszautaló ("folytasd", "amit mondtam", "előző",
     rövid "az"/"ez" kérdés) vs. sima ÚJ kérdés (nem szabad aktiválódnia).
  2. build_summary() / build_prompt_context() - a hossz-korlátok (max 1-3
     mondat, max ~220 karakter a summary-nál) és hogy CSAK a legutóbbi
     váltásból épül a prompt-kontextus, nem a teljes historyból.
  3. resolve_memory_context() - a négy lehetséges eset (kikapcsolva / nincs
     visszautalás / nincs history / van visszautalás + van history).
  4. Integrációs teszt: guarded_route_and_respond() valódi candidate A
     modellel - visszautaló üzenet + history -> memory_used=True; sima új
     kérdés -> memory_used=False; a guard/fallback réteg (v0.9-guard)
     ettől függetlenül ugyanúgy működik tovább.

Futtatás:
    python tests/test_v09_memory.py
"""

import os
import sys

SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
sys.path.insert(0, SRC_DIR)

from memory import (  # noqa: E402
    MAX_SUMMARY_CHARS,
    build_prompt_context,
    build_summary,
    detect_followup,
    resolve_memory_context,
)

FAILURES = []


def check(label, condition):
    status = "OK" if condition else "FAIL"
    print(f"  [{status}] {label}")
    if not condition:
        FAILURES.append(label)


# ---------------------------------------------------------------------------
# 1) detect_followup()
# ---------------------------------------------------------------------------
print("--- detect_followup() teszt: visszautalás vs. sima új kérdés ---")

BACKREFERENCE_CASES = [
    "Folytasd!",
    "Folytassuk ezt a gondolatot.",
    "Amit az előbb mondtam, arra gondoltam...",
    "Amit korábban írtam, azt hogy érted?",
    "Az előzőt nem egészen értettem.",
    "Mint az előbb mondtad, arról volna szó...",
    "Visszatérve arra, amit mondtál...",
    "Mit jelent ez?",
    "És az?",
    "Az miért?",
    "Ezt hogy érted?",
]
for text in BACKREFERENCE_CASES:
    used, reason = detect_followup(text)
    check(f"'{text}' -> visszautalásnak ismeri fel (kapott: used={used}, reason={reason!r})",
          used and reason in ("explicit_backreference", "short_deictic_followup"))

NEW_QUESTION_CASES = [
    "Mi a kedvenc filmed?",
    "Hány éves vagy?",
    "Szia, ki vagy?",
    "Tudsz verset írni?",
    "Miért válaszolsz néha furán?",
    "Van emlékezeted?",
    "Mi a különbség közted és egy nagy AI chatbot között?",
    "Hogy vagy?",
    "Mi újság?",
    "Köszönöm!",
    "Milyen érzés AI-nak lenni?",
]
for text in NEW_QUESTION_CASES:
    used, reason = detect_followup(text)
    check(f"'{text}' -> NEM visszautalás (kapott: used={used}, reason={reason!r})", not used)


# ---------------------------------------------------------------------------
# 2) build_summary() / build_prompt_context()
# ---------------------------------------------------------------------------
print("\n--- build_summary() / build_prompt_context() teszt ---")

history = [
    ("Mi a kedvenc filmed?", "Nincs kedvenc filmem, hiszen nem néztem filmeket."),
    ("Van emlékezeted?", "Nincs hosszú távú emlékezetem, csak az aktuális beszélgetés alatt."),
]

summary = build_summary(history)
check("build_summary() nem üres, ha van history", len(summary) > 0)
check(f"build_summary() a {MAX_SUMMARY_CHARS} karakteres limiten belül marad (hossz={len(summary)})",
      len(summary) <= MAX_SUMMARY_CHARS)
check("build_summary() legfeljebb 3 mondatnyi (max 2 mondatzáró pont, a vágás '...'-ját nem számítva)",
      summary.replace("...", "").count(".") <= 3)

prompt_ctx = build_prompt_context(history)
check("build_prompt_context() 'User:'/'AI:' natív formátumú",
      prompt_ctx.startswith("User:") and "\nAI:" in prompt_ctx)
check("build_prompt_context() a '\\n\\n'-vel zárul (a tanító adat blokk-elválasztója)",
      prompt_ctx.endswith("\n\n"))
check("build_prompt_context() CSAK a legutolsó váltásból épül (a régebbi kérdés NINCS benne)",
      "kedvenc filmed" not in prompt_ctx and "emlékezeted" in prompt_ctx)

check("build_summary([]) üres string", build_summary([]) == "")
check("build_prompt_context([]) üres string", build_prompt_context([]) == "")

long_history = [("x" * 500, "y" * 500)]
check("build_prompt_context() hosszú váltásnál is korlátozott hosszú marad",
      len(build_prompt_context(long_history)) < 300)


# ---------------------------------------------------------------------------
# 3) resolve_memory_context()
# ---------------------------------------------------------------------------
print("\n--- resolve_memory_context() teszt (4 eset) ---")

info, ctx = resolve_memory_context("Folytasd!", history, enabled=False)
check("kikapcsolva -> memory_used=False, reason='disabled'",
      info["memory_used"] is False and info["memory_reason"] == "disabled" and ctx == "")

info, ctx = resolve_memory_context("Mi a kedvenc filmed?", history, enabled=True)
check("nincs visszautalás -> memory_used=False, reason='no_backreference_detected'",
      info["memory_used"] is False and info["memory_reason"] == "no_backreference_detected" and ctx == "")

info, ctx = resolve_memory_context("Folytasd!", [], enabled=True)
check("visszautalás, de nincs history -> memory_used=False, reason='no_history_available'",
      info["memory_used"] is False and info["memory_reason"] == "no_history_available" and ctx == "")

info, ctx = resolve_memory_context("Folytasd!", history, enabled=True)
check("visszautalás + van history -> memory_used=True, van summary és prompt_context",
      info["memory_used"] is True and len(info["memory_summary"]) > 0 and ctx != "")


# ---------------------------------------------------------------------------
# 4) Integrációs teszt: guarded_route_and_respond() valódi candidate A modellel
# ---------------------------------------------------------------------------
print("\n--- Integrációs teszt: guarded_route_and_respond() + memória, valódi modellel ---")

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

    sample_history = [("Mi a kedvenc filmed?", "Nincs kedvenc filmem, hiszen nem néztem filmeket.")]

    # a) visszautaló kérdés + history -> memory_used=True
    reply, intent, model_used, sentence_info, guard_info = guarded_route_and_respond(
        general_model, instruction_model, "És az miért van?", temperature=0.6,
        history=sample_history, memory_enabled=True,
    )
    check("visszautaló kérdés + history -> guard_info['memory_used'] is True",
          guard_info["memory_used"] is True)
    check("visszautaló kérdés + history -> van memory_summary", len(guard_info["memory_summary"]) > 0)
    check("visszautaló kérdés + history -> guard_info tartalmazza a memory mezőket", all(
        k in guard_info for k in ("memory_used", "memory_summary", "memory_reason")
    ))

    # b) sima ÚJ kérdés + van history -> memory_used=False (nem aktiválódik feleslegesen)
    reply2, intent2, model_used2, sentence_info2, guard_info2 = guarded_route_and_respond(
        general_model, instruction_model, "Tudsz verset írni?", temperature=0.6,
        history=sample_history, memory_enabled=True,
    )
    check("sima új kérdés + van history -> guard_info['memory_used'] is False",
          guard_info2["memory_used"] is False)
    check("sima új kérdés -> memory_reason='no_backreference_detected'",
          guard_info2["memory_reason"] == "no_backreference_detected")

    # c) memory_enabled=False -> soha nem aktiválódik, még visszautalásnál sem
    reply3, intent3, model_used3, sentence_info3, guard_info3 = guarded_route_and_respond(
        general_model, instruction_model, "Folytasd!", temperature=0.6,
        history=sample_history, memory_enabled=False,
    )
    check("memory_enabled=False -> memory_used=False még visszautalásnál is",
          guard_info3["memory_used"] is False and guard_info3["memory_reason"] == "disabled")

    # d) a guard/fallback réteg (kategória-ellenőrzés) továbbra is működik memóriával együtt
    check("visszautaló kérdésnél is fut a kategória-ellenőrzés (expected_answer_type kitöltve)",
          guard_info["expected_answer_type"] != "")
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
