"""
MF-AI-Zero - v1.4 stílus/válaszminőség teszt (response_style.py + guard.py
integráció).

Hét rész:
  1. fix_grammar_and_punctuation() - szóköz/írásjel/nagybetű javítás.
  2. remove_duplicate_sentences() - ismétlődő mondatok eltávolítása.
  3. soften_if_too_short() - rövid válasz bővítése, tartalom nélküli
     lezáró mondattal.
  4. score_response_quality() - szabályalapú pontszám.
  5. apply_style() - teljes pipeline + "NEM változtat tényeket" teszt:
     minden tartalmi szó megmarad, csak a forma változik.
  6. Integrációs teszt: guarded_route_and_respond() valódi candidate A
     modellel - style_used/response_quality_score/final_response_length
     mezők jelen vannak; --no-style kikapcsolja; a determinisztikus
     rendszerválaszokon (memória-mentés visszaigazolás) NEM fut le.
  7. Többkörös beszélgetés a style réteggel együtt - a guard/memory/
     knowledge/web mezői nem sérülnek.

Futtatás:
    python tests/test_v1_4_response_style.py
"""

import os
import random
import sys
import tempfile

SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
sys.path.insert(0, SRC_DIR)

from response_style import (  # noqa: E402
    apply_style,
    fix_grammar_and_punctuation,
    remove_duplicate_sentences,
    score_response_quality,
    soften_if_too_short,
)

FAILURES = []


def check(label, condition):
    status = "OK" if condition else "FAIL"
    print(f"  [{status}] {label}")
    if not condition:
        FAILURES.append(label)


# ---------------------------------------------------------------------------
# 1) fix_grammar_and_punctuation()
# ---------------------------------------------------------------------------
print("--- fix_grammar_and_punctuation() teszt ---")

check("felesleges szóköz írásjel előtt eltávolítva",
      fix_grammar_and_punctuation("szia  , hogy vagy ??") == "Szia, hogy vagy?")
check("hiányzó szóköz írásjel után pótolva",
      fix_grammar_and_punctuation("Ez egy mondat.Ez a masik mondat") == "Ez egy mondat. Ez a masik mondat.")
check("kisbetűs kezdet nagybetűsítve", fix_grammar_and_punctuation("nincs") == "Nincs.")
check("hiányzó mondatvégi írásjel pótolva",
      fix_grammar_and_punctuation("ez egy válasz") == "Ez egy válasz.")
check("többszörös felkiáltójel összevonva",
      fix_grammar_and_punctuation("De jó!!!") == "De jó!")
check("üres string -> üres string marad", fix_grammar_and_punctuation("") == "")
check("már helyes mondat változatlan marad (csak whitespace trim)",
      fix_grammar_and_punctuation("Ez egy helyes mondat.") == "Ez egy helyes mondat.")
check("ellipszis ('...') NEM sérül",
      "..." in fix_grammar_and_punctuation("Erről még gondolkodom..."))


# ---------------------------------------------------------------------------
# 2) remove_duplicate_sentences()
# ---------------------------------------------------------------------------
print("\n--- remove_duplicate_sentences() teszt ---")

result = remove_duplicate_sentences("A kitartás fontos. A kitartás fontos. Más mondat.")
check("ismétlődő mondat eltávolítva, az egyedi mondatok megmaradnak",
      "kitartás fontos" in result.lower() and "más mondat" in result.lower()
      and result.lower().count("kitartás fontos") == 1)

no_dup = "Ez egy mondat. Ez egy másik mondat."
check("nincs ismétlés -> a szöveg változatlan", remove_duplicate_sentences(no_dup) == no_dup)

single = "Csak egy mondat."
check("egyetlen mondat -> változatlan", remove_duplicate_sentences(single) == single)


# ---------------------------------------------------------------------------
# 3) soften_if_too_short()
# ---------------------------------------------------------------------------
print("\n--- soften_if_too_short() teszt ---")

short_reply = "Nincs."
softened = soften_if_too_short(short_reply, rng=random.Random(42))
check("túl rövid válasz -> hosszabb lesz", len(softened) > len(short_reply))
check("túl rövid válasz -> az EREDETI szöveg benne marad (nem törli a tartalmat)",
      short_reply.rstrip(".") in softened)

long_reply = "Ez egy elég hosszú, teljes mondat, aminek semmi baja, nem kell bővíteni."
check("elég hosszú válasz -> változatlan marad", soften_if_too_short(long_reply) == long_reply)

check("üres szöveg -> üres marad", soften_if_too_short("") == "")


# ---------------------------------------------------------------------------
# 4) score_response_quality()
# ---------------------------------------------------------------------------
print("\n--- score_response_quality() teszt ---")

clean_text = "Ez egy rendes, teljes mondat, aminek semmilyen formai hibája nincsen."
score, flags = score_response_quality(clean_text, clean_text)
check("hibátlan válasz -> magas pontszám, nincs flag", score == 100 and flags == [])

score2, flags2 = score_response_quality(
    "A kitartás fontos. A kitartás fontos.", "A kitartás fontos. A kitartás fontos."
)
check("ismétlődő mondatos eredeti -> had_duplicate_sentences flag", "had_duplicate_sentences" in flags2)

score3, flags3 = score_response_quality("nincs", "nincs")
check("hiányzó mondatvégi írásjel -> missing_end_punctuation flag", "missing_end_punctuation" in flags3)

score4, flags4 = score_response_quality("De jó???", "De jó???")
check("többszörös írásjel -> excessive_repeated_punctuation flag", "excessive_repeated_punctuation" in flags4)

check("score mindig [0,100] tartományban", all(
    0 <= score_response_quality(t, t)[0] <= 100
    for t in ["", "nincs", "A A A. A A A.", "Rendes mondat."]
))


# ---------------------------------------------------------------------------
# 5) apply_style() - teljes pipeline + "NEM változtat tényeket"
# ---------------------------------------------------------------------------
print("\n--- apply_style() teszt (nem változtat tényeket) ---")

styled, info = apply_style("nincs kedvenc filmem , mert nem neztem filmeket")
check("apply_style() javítja a formát (nagybetű, mondatvégi pont)",
      styled[0].isupper() and styled[-1] in ".!?")
check("apply_style() minden EREDETI tartalmi szót megtart (nem talál ki új infót, nem törli a tényt)",
      all(w in styled.lower() for w in ["nincs", "kedvenc", "filmem", "neztem", "filmeket"]))
check("apply_style() info dict tartalmazza a kötelező mezőket", all(
    k in info for k in ("style_used", "response_quality_score", "final_response_length")
))

styled_disabled, info_disabled = apply_style("nincs kedvenc filmem", enabled=False)
check("enabled=False -> a szöveg változatlan", styled_disabled == "nincs kedvenc filmem")
check("enabled=False -> style_used=False", info_disabled["style_used"] is False)

styled_empty, info_empty = apply_style("")
check("üres szöveg -> style_used=False, nincs hiba", info_empty["style_used"] is False)

fact_text = "Budapesten dolgozom és Tibornak hívnak"
styled_fact, _ = apply_style(fact_text)
check("konkrét tényt tartalmazó mondat -> a tények szó szerint megmaradnak",
      "budapesten" in styled_fact.lower() and "tibornak" in styled_fact.lower())


# ---------------------------------------------------------------------------
# 6) Integrációs teszt: guarded_route_and_respond() valódi candidate A modellel
# ---------------------------------------------------------------------------
print("\n--- Integrációs teszt: guarded_route_and_respond() + style ---")

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

    # a) sima kérdés -> style mezők jelen vannak
    reply_a, intent_a, model_used_a, sentence_info_a, guard_info_a = guarded_route_and_respond(
        general_model, instruction_model, "Mi a kedvenc filmed?", temperature=0.6,
        style_enabled=True,
    )
    check("style_enabled=True -> guard_info tartalmazza a v1.4 mezőket", all(
        k in guard_info_a for k in ("style_used", "response_quality_score", "final_response_length")
    ))
    check("response_quality_score [0,100] tartományban vagy None",
          guard_info_a["response_quality_score"] is None or 0 <= guard_info_a["response_quality_score"] <= 100)
    check("final_response_length megegyezik a tényleges válasz hosszával",
          guard_info_a["final_response_length"] == len(reply_a) or guard_info_a["final_response_length"] is None)
    check("a válasz mondatvégi írásjellel zárul (a stílus-réteg javította)", reply_a.rstrip()[-1] in ".!?")

    # b) --no-style -> nem fut a réteg
    reply_b, intent_b, model_used_b, sentence_info_b, guard_info_b = guarded_route_and_respond(
        general_model, instruction_model, "Mi a kedvenc filmed?", temperature=0.6,
        style_enabled=False,
    )
    check("style_enabled=False -> style_used=False", guard_info_b["style_used"] is False)
    check("style_enabled=False -> response_quality_score=None (nem futott le a réteg)",
          guard_info_b["response_quality_score"] is None)

    # c) determinisztikus rendszerválaszon (memória-mentés) a style NEM fut le
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_store = os.path.join(tmp_dir, "memories.json")
        reply_c, intent_c, model_used_c, sentence_info_c, guard_info_c = guarded_route_and_respond(
            general_model, instruction_model, "Jegyezd meg, hogy szeretem a teát.", temperature=0.6,
            style_enabled=True, long_memory_enabled=True, long_memory_store_path=tmp_store,
        )
    check("memória-mentés visszaigazolásán a style_used marad False (nem éri el a _finalize-t)",
          guard_info_c["long_memory_saved"] is True and guard_info_c["style_used"] is False)
    check("a memória-mentés visszaigazolás szövege változatlan formátumú ('Megjegyeztem')",
          "Megjegyeztem" in reply_c)
else:
    print(f"  (kihagyva - nincs candidate A modell: {candidate_a_path})")


# ---------------------------------------------------------------------------
# 7) Többkörös beszélgetés style réteggel - guard/memory/knowledge/web érintetlen
# ---------------------------------------------------------------------------
print("\n--- Többkörös beszélgetés style réteggel (guard/memory/knowledge/web érintetlen) ---")

if os.path.exists(candidate_a_path):
    from conversation_manager import ConversationState

    conv_state = ConversationState()
    reply1, intent1, _, _, guard_info1 = guarded_route_and_respond(
        general_model, instruction_model, "Mi a kedvenc filmed?", temperature=0.6,
        conversation_state=conv_state, conversation_manager_enabled=True, style_enabled=True,
    )
    conv_state.update("Mi a kedvenc filmed?", reply1, intent1, needed_context=False)

    reply2, intent2, _, _, guard_info2 = guarded_route_and_respond(
        general_model, instruction_model, "Folytasd!", temperature=0.6,
        conversation_state=conv_state, conversation_manager_enabled=True, style_enabled=True,
    )
    check("többkörös beszélgetés + style -> conversation_state_used=True továbbra is működik",
          guard_info2["conversation_state_used"] is True)
    check("többkörös beszélgetés + style -> style mezők is jelen vannak", all(
        k in guard_info2 for k in ("style_used", "response_quality_score", "final_response_length")
    ))
    check("a 2. válasz is mondatvégi írásjellel zárul", reply2.rstrip()[-1] in ".!?")
    check("a guard egyéb rétegei (memory/knowledge/web) mezői is érintetlenül jelen vannak", all(
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
