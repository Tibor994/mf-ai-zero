"""
MF-AI-Zero - v1.3 beszélgetés-állapot kezelő teszt (conversation_manager.py
+ guard.py integráció).

Hat rész:
  1. detect_context_need() - "folytasd", "ezt javítsd", "az előző", "amit
     mondtam", "akkor a másik", rövid névmásos utalás vs. sima ÚJ kérdés.
  2. ConversationState.update() - active_topic/current_goal/
     open_questions/pending_tasks/last_decision/conversation_summary
     helyes karbantartása.
  3. build_conversation_prompt_context() / resolve_conversation_context()
     - formátum és a 4 lehetséges eset.
  4. Többfordulós beszélgetés teszt valódi candidate A modellel: (1) user
     mond valamit, (2) user visszautal rá ("folytasd"), (3) az AI
     ténylegesen megkapja az összefoglalót a promptban.
  5. "Ezt javítsd" teszt + sima ÚJ kérdésnél NEM keveredik bele a régi téma.
  6. Biztonsági szabály: a state SOSEM ír hosszú távú memóriába/
     tudásbázisba, és a guard/rövid-memória/tudásbázis/web mezői
     változatlanul jelen vannak.

Futtatás:
    python tests/test_v1_3_conversation_manager.py
"""

import os
import sys

SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
sys.path.insert(0, SRC_DIR)

from conversation_manager import (  # noqa: E402
    ConversationState,
    build_conversation_prompt_context,
    detect_context_need,
    resolve_conversation_context,
)

FAILURES = []


def check(label, condition):
    status = "OK" if condition else "FAIL"
    print(f"  [{status}] {label}")
    if not condition:
        FAILURES.append(label)


# ---------------------------------------------------------------------------
# 1) detect_context_need()
# ---------------------------------------------------------------------------
print("--- detect_context_need() teszt ---")

CONTEXT_CASES = [
    "Folytasd!",
    "Folytassuk ezt.",
    "Az előzőt nem értettem.",
    "Ezt javítsd ki légyszi.",
    "Amit mondtam, arra gondoltam.",
    "Akkor a másikat mondd el.",
    "Mint az előbb mondtad...",
    "Mit jelent ez?",
    "És az?",
]
for text in CONTEXT_CASES:
    needed, reason = detect_context_need(text)
    check(f"'{text}' -> kell kontextus (kapott: needed={needed}, reason={reason!r})",
          needed and reason in ("explicit_backreference", "short_deictic_followup"))

NON_CONTEXT_CASES = [
    "Mi a kedvenc filmed?",
    "Hány éves vagy?",
    "Szia, ki vagy?",
    "Tudsz verset írni?",
    "Milyen érzés AI-nak lenni?",
]
for text in NON_CONTEXT_CASES:
    needed, reason = detect_context_need(text)
    check(f"'{text}' -> NEM kell kontextus", needed is False)


# ---------------------------------------------------------------------------
# 2) ConversationState.update()
# ---------------------------------------------------------------------------
print("\n--- ConversationState.update() teszt ---")

state = ConversationState()
check("kezdeti állapot: minden mező üres/None", state.active_topic is None and state.open_questions == []
      and state.pending_tasks == [] and state.current_goal is None and state.last_decision is None)

state.update("Mi a kedvenc filmed?", "Nincs kedvenc filmem.", "general_chat", needed_context=False)
check("sima ÚJ üzenet -> active_topic frissül", state.active_topic == "Mi a kedvenc filmed?")
check("last_user_intent frissül", state.last_user_intent == "general_chat")
check("last_decision a válaszból épül", state.last_decision == "Nincs kedvenc filmem.")
check("conversation_summary nem üres, ha van active_topic", bool(state.conversation_summary))

state.update("És miért nincs?", "Mert nem néztem filmeket.", "general_chat", needed_context=True)
check("VISSZAUTALÓ üzenetnél az active_topic NEM íródik felül",
      state.active_topic == "Mi a kedvenc filmed?")

state2 = ConversationState()
state2.update("A célom, hogy befejezzem ezt a projektet.", "Sok sikert hozzá!", "general_chat", needed_context=False)
check("cél-jellegű üzenet -> current_goal frissül", state2.current_goal is not None)

state3 = ConversationState()
state3.update("Mi a különbség köztünk?", "Válasz.", "general_chat", needed_context=False)
check("kérdés (végén '?') -> bekerül az open_questions-be", "Mi a különbség köztünk?" in state3.open_questions)
state3.update("Köszönöm, értem!", "Szívesen.", "general_chat", needed_context=False)
check("lezáró jellegű üzenet -> open_questions kiürül", state3.open_questions == [])

state4 = ConversationState()
state4.update("Írj egy verset a tavaszról.", "Rendben.", "general_chat", needed_context=False)
check("feladat-jellegű üzenet -> bekerül a pending_tasks-ba", len(state4.pending_tasks) == 1)

state5 = ConversationState()
for i in range(5):
    state5.update(f"Kérdés {i}?", "Válasz.", "general_chat", needed_context=False)
check("open_questions sosem lépi túl MAX_OPEN_QUESTIONS-t", len(state5.open_questions) <= 3)

d = state.as_dict()
check("as_dict() tartalmazza az összes mezőt", all(
    k in d for k in ("active_topic", "current_goal", "last_user_intent", "open_questions",
                      "pending_tasks", "last_decision", "conversation_summary")
))

state.reset()
check("reset() után minden mező üres", state.active_topic is None and state.conversation_summary is None)


# ---------------------------------------------------------------------------
# 3) build_conversation_prompt_context() / resolve_conversation_context()
# ---------------------------------------------------------------------------
print("\n--- build_conversation_prompt_context() / resolve_conversation_context() teszt ---")

ctx = build_conversation_prompt_context("Eddig erről volt szó: \"filmek\".")
check("build_conversation_prompt_context() 'User:'/'AI:' natív formátumú",
      ctx.startswith("User:") and "\nAI:" in ctx and ctx.endswith("\n\n"))
check("build_conversation_prompt_context('') üres string", build_conversation_prompt_context("") == "")

fresh_state = ConversationState()
fresh_state.update("Mi a kedvenc filmed?", "Nincs kedvenc filmem.", "general_chat", needed_context=False)

info, prompt_ctx, needed = resolve_conversation_context("Folytasd!", fresh_state, enabled=True)
check("visszautaló üzenet + van summary -> conversation_state_used=True", info["conversation_state_used"] is True)
check("prompt_ctx nem üres", prompt_ctx != "")

info2, prompt_ctx2, needed2 = resolve_conversation_context("Mi a kedvenc filmed?", fresh_state, enabled=True)
check("sima ÚJ kérdés -> conversation_state_used=False", info2["conversation_state_used"] is False)
check("sima ÚJ kérdés -> prompt_ctx üres", prompt_ctx2 == "")

info3, prompt_ctx3, needed3 = resolve_conversation_context("Folytasd!", fresh_state, enabled=False)
check("enabled=False -> conversation_state_used=False még visszautalásnál is", info3["conversation_state_used"] is False)

info4, prompt_ctx4, needed4 = resolve_conversation_context("Folytasd!", ConversationState(), enabled=True)
check("visszautalás, de üres state (nincs summary) -> conversation_state_used=False",
      info4["conversation_state_used"] is False)


# ---------------------------------------------------------------------------
# 4) Többfordulós beszélgetés teszt valódi candidate A modellel
# ---------------------------------------------------------------------------
print("\n--- Többfordulós beszélgetés teszt (guarded_route_and_respond) ---")

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

    conv_state = ConversationState()

    # 1. forduló: user mond valamit (sima, új téma)
    reply1, intent1, model_used1, sentence_info1, guard_info1 = guarded_route_and_respond(
        general_model, instruction_model, "Mi a kedvenc filmed?", temperature=0.6,
        conversation_state=conv_state, conversation_manager_enabled=True,
    )
    conv_state.update("Mi a kedvenc filmed?", reply1, intent1, needed_context=False)
    check("1. forduló -> guard_info tartalmazza a v1.3 mezőket", all(
        k in guard_info1 for k in ("conversation_state_used", "active_topic", "current_goal", "conversation_summary")
    ))
    check("1. forduló után conv_state.active_topic beállt", conv_state.active_topic == "Mi a kedvenc filmed?")

    # 2. forduló: user visszautal rá ("folytasd") -> az AI kapja az összefoglalót
    reply2, intent2, model_used2, sentence_info2, guard_info2 = guarded_route_and_respond(
        general_model, instruction_model, "Folytasd!", temperature=0.6,
        conversation_state=conv_state, conversation_manager_enabled=True,
    )
    check("2. forduló ('folytasd') -> conversation_state_used=True", guard_info2["conversation_state_used"] is True)
    check("2. forduló -> a felhasznált conversation_summary tartalmazza az 1. téma egy részét",
          "kedvenc filmed" in (guard_info2["conversation_summary"] or "").lower())

    # 3. forduló: "ezt javítsd" - szintén visszautalás
    reply3, intent3, model_used3, sentence_info3, guard_info3 = guarded_route_and_respond(
        general_model, instruction_model, "Ezt javítsd ki!", temperature=0.6,
        conversation_state=conv_state, conversation_manager_enabled=True,
    )
    check("3. forduló ('ezt javítsd') -> conversation_state_used=True", guard_info3["conversation_state_used"] is True)

    conv_state.update("Ezt javítsd ki!", reply3, intent3, needed_context=True)
    check("visszautaló forduló UTÁN az active_topic MÉG mindig az eredeti téma",
          conv_state.active_topic == "Mi a kedvenc filmed?")

    # 4. forduló: sima ÚJ kérdés -> NE keveredjen bele a régi téma
    reply4, intent4, model_used4, sentence_info4, guard_info4 = guarded_route_and_respond(
        general_model, instruction_model, "Hány éves vagy?", temperature=0.6,
        conversation_state=conv_state, conversation_manager_enabled=True,
    )
    check("4. forduló (sima ÚJ kérdés) -> conversation_state_used=False (nincs összekeverés)",
          guard_info4["conversation_state_used"] is False)

    # 5. --no-conversation-manager (enabled=False) -> még 'folytasd'-nál sem
    reply5, intent5, model_used5, sentence_info5, guard_info5 = guarded_route_and_respond(
        general_model, instruction_model, "Folytasd!", temperature=0.6,
        conversation_state=conv_state, conversation_manager_enabled=False,
    )
    check("conversation_manager_enabled=False -> conversation_state_used=False még 'folytasd'-nál is",
          guard_info5["conversation_state_used"] is False)

    # 6. biztonsági szabály: a guard egyéb rétegei (memory/knowledge/web) mezői érintetlenek
    check("a conversation manager mellett a többi réteg mezői is jelen vannak", all(
        k in guard_info2 for k in (
            "memory_used", "long_memory_saved", "knowledge_used", "web_used", "web_search_used",
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
