"""
MF-AI-Zero - v1.0 hosszú távú memória teszt (long_term_memory.py + guard.py
integráció).

Öt rész:
  1. CRUD egységtesztek (save/list/search/delete) - IDEIGLENES store_path-
     szal, az éles long_term_memory/memories.json-t NEM érinti.
  2. detect_memory_candidate() - heurisztikus "érdemes megjegyezni" jelzés.
  3. detect_explicit_save() - CSAK explicit "jegyezd meg..." kérésnél ad
     should_save=True-t, sima kijelentésnél SOSEM.
  4. build_long_memory_prompt_context() - hossz-korlát, natív formátum.
  5. Integrációs teszt: guarded_route_and_respond() valódi candidate A
     modellel - explicit mentés ténylegesen ír a store-ba, sima kijelentés
     NEM ment automatikusan (a kötelező biztonsági szabály), majd egy
     releváns kérdés visszakeresi a mentett memóriát.

Futtatás:
    python tests/test_v1_0_long_memory.py
"""

import os
import sys
import tempfile

SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
sys.path.insert(0, SRC_DIR)

from long_term_memory import (  # noqa: E402
    build_long_memory_prompt_context,
    delete_memory,
    detect_explicit_save,
    detect_memory_candidate,
    list_memories,
    save_memory,
    search_memories,
)

FAILURES = []


def check(label, condition):
    status = "OK" if condition else "FAIL"
    print(f"  [{status}] {label}")
    if not condition:
        FAILURES.append(label)


# ---------------------------------------------------------------------------
# 1) CRUD egységtesztek - ideiglenes store_path
# ---------------------------------------------------------------------------
print("--- CRUD teszt (save/list/search/delete, ideiglenes store) ---")

with tempfile.TemporaryDirectory() as tmp_dir:
    store_path = os.path.join(tmp_dir, "memories.json")

    check("üres store -> list_memories() üres lista", list_memories(store_path=store_path) == [])

    rec1 = save_memory("user_preference", "Szereti a teát.", confidence=0.9, source="explicit", store_path=store_path)
    rec2 = save_memory("user_fact", "Budapesten dolgozik.", confidence=1.0, source="explicit", store_path=store_path)
    rec3 = save_memory("current_goal", "A v1.0 memóriát fejleszti.", store_path=store_path)

    check("save_memory() visszaad egy dict-et minden mezővel", all(
        k in rec1 for k in ("id", "category", "text", "created_at", "updated_at", "confidence", "source", "active")
    ))
    check("save_memory() active=True alapból", rec1["active"] is True)
    check("save_memory() érvénytelen kategóriánál DEFAULT_CATEGORY-ra esik vissza",
          save_memory("nem_letezo_kategoria", "teszt szöveg", store_path=store_path)["category"] == "user_fact")
    check("save_memory() üres szövegnél None-t ad vissza (nem ment)",
          save_memory("user_fact", "   ", store_path=store_path) is None)

    all_active = list_memories(store_path=store_path)
    check("list_memories() az összes aktív rekordot visszaadja", len(all_active) == 4)  # rec1-3 + a default-category teszt

    pref_only = list_memories(category="user_preference", store_path=store_path)
    check("list_memories(category=...) csak azt a kategóriát adja vissza",
          len(pref_only) == 1 and pref_only[0]["id"] == rec1["id"])

    found = search_memories("tea", store_path=store_path)
    check("search_memories() kulcsszó-egyezéssel megtalálja a releváns memóriát",
          any(r["id"] == rec1["id"] for r in found))

    not_found = search_memories("marslakó ufó", store_path=store_path)
    check("search_memories() nem ad vissza semmit, ha nincs kulcsszó-egyezés", not_found == [])

    deleted = delete_memory(rec2["id"], store_path=store_path)
    check("delete_memory() true-t ad vissza, ha talált egyezést", deleted is True)
    check("delete_memory() után (soft) a memória NEM jelenik meg list_memories()-ben",
          rec2["id"] not in [r["id"] for r in list_memories(store_path=store_path)])
    check("delete_memory() után a rekord MÉG BENNE van a fájlban, csak inaktív (active=False)",
          any(r["id"] == rec2["id"] and r["active"] is False for r in list_memories(active_only=False, store_path=store_path)))

    not_found_delete = delete_memory("nem-letezo-id", store_path=store_path)
    check("delete_memory() false-t ad vissza, ha nincs ilyen id", not_found_delete is False)

    hard_deleted = delete_memory(rec3["id"], hard=True, store_path=store_path)
    check("delete_memory(hard=True) után a rekord TELJESEN eltűnik",
          hard_deleted is True and rec3["id"] not in [r["id"] for r in list_memories(active_only=False, store_path=store_path)])


# ---------------------------------------------------------------------------
# 2) detect_memory_candidate()
# ---------------------------------------------------------------------------
print("\n--- detect_memory_candidate() teszt ---")

CANDIDATE_CASES = [
    "Szeretem a teát.",
    "Nem szeretem a telet.",
    "A célom, hogy befejezzem ezt a projektet.",
    "Helyesbítek, nem ezt mondtam korábban.",
    "Ez a projekt egy karakter-alapú LSTM-mel indult.",
    "A nevem Tibor.",
]
for text in CANDIDATE_CASES:
    is_candidate, category = detect_memory_candidate(text)
    check(f"'{text}' -> candidate=True, van kategória (kapott: {is_candidate}, {category!r})",
          is_candidate and category is not None)

NON_CANDIDATE_CASES = [
    "Mi a kedvenc filmed?",
    "Hány éves vagy?",
    "Szia!",
    "Írj 3 mondatot az erőről.",
]
for text in NON_CANDIDATE_CASES:
    is_candidate, category = detect_memory_candidate(text)
    check(f"'{text}' -> NEM candidate (kapott: {is_candidate})", not is_candidate)


# ---------------------------------------------------------------------------
# 3) detect_explicit_save() - CSAK explicit kérésnél ment
# ---------------------------------------------------------------------------
print("\n--- detect_explicit_save() teszt (biztonsági szabály: csak explicit kérésre) ---")

EXPLICIT_CASES = [
    ("Jegyezd meg, hogy szeretem a teát.", "szeretem a teát"),
    ("jegyezd meg hogy Budapesten dolgozom", "budapesten dolgozom"),
    ("Ne felejtsd el, hogy holnap határidő van!", "holnap határidő van"),
    ("Emlékezz rá, hogy a kedvenc színem a kék.", "a kedvenc színem a kék"),
]
for text, expected_substring in EXPLICIT_CASES:
    should_save, extracted = detect_explicit_save(text)
    check(f"'{text}' -> should_save=True, extracted tartalmazza a lényeget",
          should_save and expected_substring in extracted.lower())

NON_EXPLICIT_CASES = [
    "Szeretem a teát.",              # candidate, de NEM explicit kérés
    "A célom, hogy befejezzem ezt.",  # candidate, de NEM explicit kérés
    "Mi a kedvenc filmed?",
    "Hogy vagy?",
]
for text in NON_EXPLICIT_CASES:
    should_save, extracted = detect_explicit_save(text)
    check(f"'{text}' -> should_save=False (VESZÉLYES lenne automatikusan menteni)",
          should_save is False and extracted is None)


# ---------------------------------------------------------------------------
# 4) build_long_memory_prompt_context()
# ---------------------------------------------------------------------------
print("\n--- build_long_memory_prompt_context() teszt ---")

sample_memories = [
    {"text": "Szereti a teát."},
    {"text": "Budapesten dolgozik."},
]
ctx = build_long_memory_prompt_context(sample_memories)
check("build_long_memory_prompt_context() 'User:'/'AI:' natív formátumú",
      ctx.startswith("User:") and "\nAI:" in ctx)
check("build_long_memory_prompt_context() a '\\n\\n'-vel zárul", ctx.endswith("\n\n"))
check("build_long_memory_prompt_context() tartalmazza mindkét tényt",
      "teát" in ctx and "budapesten" in ctx.lower())
check("build_long_memory_prompt_context([]) üres string", build_long_memory_prompt_context([]) == "")

many_memories = [{"text": f"Tény szám {i} egy hosszabb mondatban leírva."} for i in range(10)]
long_ctx = build_long_memory_prompt_context(many_memories)
check("build_long_memory_prompt_context() max 5 tényt épít be (rövid marad sok memóriánál is)",
      len(long_ctx) < 400)


# ---------------------------------------------------------------------------
# 5) Integrációs teszt: guarded_route_and_respond() valódi candidate A modellel
# ---------------------------------------------------------------------------
print("\n--- Integrációs teszt: guarded_route_and_respond() + hosszú memória ---")

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

    with tempfile.TemporaryDirectory() as tmp_dir:
        store_path = os.path.join(tmp_dir, "memories.json")

        # a) sima kijelentés -> NEM ment automatikusan (a kötelező biztonsági szabály)
        reply_a, intent_a, model_used_a, sentence_info_a, guard_info_a = guarded_route_and_respond(
            general_model, instruction_model, "Szeretem a teát.", temperature=0.6,
            long_memory_enabled=True, long_memory_store_path=store_path,
        )
        check("sima kijelentés -> long_memory_saved=False", guard_info_a["long_memory_saved"] is False)
        check("sima kijelentés -> long_memory_candidate=True (csak jelzés)",
              guard_info_a["long_memory_candidate"] is True)
        check("sima kijelentés után a store MÉG ÜRES (nem történt automatikus mentés)",
              list_memories(store_path=store_path) == [])

        # b) explicit "jegyezd meg" -> TÉNYLEGES mentés
        reply_b, intent_b, model_used_b, sentence_info_b, guard_info_b = guarded_route_and_respond(
            general_model, instruction_model, "Jegyezd meg, hogy szeretem a teát.", temperature=0.6,
            long_memory_enabled=True, long_memory_store_path=store_path,
        )
        check("explicit mentés -> long_memory_saved=True", guard_info_b["long_memory_saved"] is True)
        check("explicit mentés -> van long_memory_saved_id", guard_info_b["long_memory_saved_id"] is not None)
        check("explicit mentés -> a válasz determinisztikus visszaigazolás ('Megjegyeztem')",
              "Megjegyeztem" in reply_b)
        check("explicit mentés után a store TARTALMAZZA az új rekordot",
              len(list_memories(store_path=store_path)) == 1)

        # c) egy releváns kérdés visszakeresi a mentett memóriát
        reply_c, intent_c, model_used_c, sentence_info_c, guard_info_c = guarded_route_and_respond(
            general_model, instruction_model, "Mit szeretek inni?", temperature=0.6,
            long_memory_enabled=True, long_memory_store_path=store_path,
        )
        check("releváns kérdés -> long_memory_retrieved_count > 0",
              guard_info_c["long_memory_retrieved_count"] > 0)
        check("releváns kérdés -> long_memory_retrieved_ids tartalmazza a mentett id-t",
              guard_info_b["long_memory_saved_id"] in guard_info_c["long_memory_retrieved_ids"])

        # d) --no-long-memory (long_memory_enabled=False) -> még explicit kérésre sem ment
        reply_d, intent_d, model_used_d, sentence_info_d, guard_info_d = guarded_route_and_respond(
            general_model, instruction_model, "Jegyezd meg, hogy kék az ég.", temperature=0.6,
            long_memory_enabled=False, long_memory_store_path=store_path,
        )
        check("long_memory_enabled=False -> még explicit kérésre sem ment",
              guard_info_d["long_memory_saved"] is False)
        check("long_memory_enabled=False -> a store mérete NEM változott",
              len(list_memories(store_path=store_path)) == 1)
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
