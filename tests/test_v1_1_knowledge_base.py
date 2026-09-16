"""
MF-AI-Zero - v1.1 saját tudásbázis teszt (knowledge_base.py + guard.py
integráció).

Négy rész:
  1. CRUD egységtesztek (save/list/search/delete, kategória+tag szűrés) -
     IDEIGLENES store_path-szal, az éles knowledge_base/items.json-t NEM
     érinti.
  2. build_knowledge_prompt_context() - hossz-korlát, natív formátum.
  3. Biztonsági szabály: a knowledge_base SOSEM ír automatikusan a chat
     mellékhatásaként - csak explicit save_knowledge() híváson keresztül.
  4. Integrációs teszt: guarded_route_and_respond() valódi candidate A
     modellel - egy mentett tudáselem visszakeresésre kerül egy releváns
     kérdésnél, de NEM egy irreleváns kérdésnél; a rövid/hosszú memória és
     a guard a tudásbázistól függetlenül tovább működik.

Futtatás:
    python tests/test_v1_1_knowledge_base.py
"""

import os
import sys
import tempfile

SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
sys.path.insert(0, SRC_DIR)

from knowledge_base import (  # noqa: E402
    build_knowledge_prompt_context,
    delete_knowledge,
    list_knowledge,
    save_knowledge,
    search_knowledge,
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
    store_path = os.path.join(tmp_dir, "items.json")

    check("üres store -> list_knowledge() üres lista", list_knowledge(store_path=store_path) == [])

    rec1 = save_knowledge(
        "MF-AI-Zero architektúra", "Karakter-alapú LSTM, embedding=64, hidden=128, 2 réteg.",
        category="ai_project", tags=["lstm", "architektura"], source="manual", store_path=store_path,
    )
    rec2 = save_knowledge(
        "Router elv", "Intent-routing: általános kérdésre v0.7, mondatszám-kérésre v0.7c válaszol.",
        category="technical", tags=["router"], store_path=store_path,
    )
    rec3 = save_knowledge("", "Cím nélküli jegyzet automatikus címmel.", category="other", store_path=store_path)

    check("save_knowledge() visszaad egy dict-et minden mezővel", all(
        k in rec1 for k in ("id", "title", "content", "category", "tags", "source",
                            "created_at", "updated_at", "confidence", "active")
    ))
    check("save_knowledge() active=True alapból", rec1["active"] is True)
    check("save_knowledge() üres title esetén a content elejéből képez címet",
          rec3["title"] and rec3["title"] != "")
    check("save_knowledge() érvénytelen kategóriánál DEFAULT_CATEGORY-ra esik vissza",
          save_knowledge("x", "y", category="nem_letezik", store_path=store_path)["category"] == "other")
    check("save_knowledge() üres content esetén None-t ad vissza (nem ment)",
          save_knowledge("cím", "   ", store_path=store_path) is None)
    check("save_knowledge() a tags listát rendezve, duplikátum nélkül tárolja",
          rec1["tags"] == sorted(set(rec1["tags"])))

    all_active = list_knowledge(store_path=store_path)
    check("list_knowledge() az összes aktív rekordot visszaadja", len(all_active) == 4)

    tech_only = list_knowledge(category="technical", store_path=store_path)
    check("list_knowledge(category=...) csak azt a kategóriát adja vissza",
          len(tech_only) == 1 and tech_only[0]["id"] == rec2["id"])

    tag_filtered = list_knowledge(tag="router", store_path=store_path)
    check("list_knowledge(tag=...) csak a taggelt elemeket adja vissza",
          len(tag_filtered) == 1 and tag_filtered[0]["id"] == rec2["id"])

    found_content = search_knowledge("embedding", store_path=store_path)
    check("search_knowledge() a content mezőben is keres", any(r["id"] == rec1["id"] for r in found_content))

    found_title = search_knowledge("architektura", store_path=store_path)
    check("search_knowledge() a title mezőben is keres (toldalékolással)",
          any(r["id"] == rec1["id"] for r in found_title))

    found_tag = search_knowledge("router", store_path=store_path)
    check("search_knowledge() a tags mezőben is keres", any(r["id"] == rec2["id"] for r in found_tag))

    not_found = search_knowledge("marslakó ufó", store_path=store_path)
    check("search_knowledge() nem ad vissza semmit, ha nincs kulcsszó-egyezés", not_found == [])

    deleted = delete_knowledge(rec2["id"], store_path=store_path)
    check("delete_knowledge() true-t ad vissza, ha talált egyezést", deleted is True)
    check("delete_knowledge() után (soft) a tudáselem NEM jelenik meg list_knowledge()-ben",
          rec2["id"] not in [r["id"] for r in list_knowledge(store_path=store_path)])
    check("delete_knowledge() után a rekord MÉG BENNE van a fájlban, csak inaktív",
          any(r["id"] == rec2["id"] and r["active"] is False
              for r in list_knowledge(active_only=False, store_path=store_path)))

    not_found_delete = delete_knowledge("nem-letezo-id", store_path=store_path)
    check("delete_knowledge() false-t ad vissza, ha nincs ilyen id", not_found_delete is False)

    hard_deleted = delete_knowledge(rec3["id"], hard=True, store_path=store_path)
    check("delete_knowledge(hard=True) után a rekord TELJESEN eltűnik",
          hard_deleted is True and rec3["id"] not in [r["id"] for r in list_knowledge(active_only=False, store_path=store_path)])


# ---------------------------------------------------------------------------
# 2) build_knowledge_prompt_context()
# ---------------------------------------------------------------------------
print("\n--- build_knowledge_prompt_context() teszt ---")

sample_items = [
    {"content": "Karakter-alapú LSTM, embedding=64, hidden=128."},
    {"content": "Intent-routing: v0.7 és v0.7c modellek."},
]
ctx = build_knowledge_prompt_context(sample_items)
check("build_knowledge_prompt_context() 'User:'/'AI:' natív formátumú",
      ctx.startswith("User:") and "\nAI:" in ctx)
check("build_knowledge_prompt_context() a '\\n\\n'-vel zárul", ctx.endswith("\n\n"))
check("build_knowledge_prompt_context() tartalmazza mindkét tényt",
      "lstm" in ctx.lower() and "routing" in ctx.lower())
check("build_knowledge_prompt_context([]) üres string", build_knowledge_prompt_context([]) == "")

many_items = [{"content": f"Tudáselem szám {i} egy hosszabb mondatban leírva."} for i in range(10)]
long_ctx = build_knowledge_prompt_context(many_items)
check("build_knowledge_prompt_context() max 3 elemet épít be (rövid marad sok elemnél is)",
      len(long_ctx) < 350)


# ---------------------------------------------------------------------------
# 3) Biztonsági szabály: SOSEM ír automatikusan
# ---------------------------------------------------------------------------
print("\n--- Biztonsági szabály: a knowledge_base sosem ír automatikusan ---")

with tempfile.TemporaryDirectory() as tmp_dir2:
    store_path2 = os.path.join(tmp_dir2, "items.json")
    check("üres store marad üres, amíg nincs explicit save_knowledge() hívás",
          list_knowledge(store_path=store_path2) == [])
    check("search_knowledge() önmagában NEM ír semmit (csak olvas)",
          search_knowledge("bármi", store_path=store_path2) == [] and list_knowledge(store_path=store_path2) == [])


# ---------------------------------------------------------------------------
# 4) Integrációs teszt: guarded_route_and_respond() valódi candidate A modellel
# ---------------------------------------------------------------------------
print("\n--- Integrációs teszt: guarded_route_and_respond() + knowledge_base ---")

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

    with tempfile.TemporaryDirectory() as tmp_dir3:
        k_store = os.path.join(tmp_dir3, "items.json")
        m_store = os.path.join(tmp_dir3, "memories.json")

        save_knowledge(
            "Router architektúra", "A router külön modellt használ általános kérdésre és mondatszám-kérésre.",
            category="technical", tags=["router", "architektura"], store_path=k_store,
        )

        # a) releváns kérdés -> knowledge_used=True
        reply_a, intent_a, model_used_a, sentence_info_a, guard_info_a = guarded_route_and_respond(
            general_model, instruction_model, "Mesélj a router architektúrájáról!", temperature=0.6,
            long_memory_enabled=True, long_memory_store_path=m_store,
            knowledge_enabled=True, knowledge_store_path=k_store,
        )
        check("releváns kérdés -> guard_info['knowledge_used'] is True", guard_info_a["knowledge_used"] is True)
        check("releváns kérdés -> knowledge_items nem üres", len(guard_info_a["knowledge_items"]) > 0)
        check("releváns kérdés -> knowledge_query == a user üzenet",
              guard_info_a["knowledge_query"] == "Mesélj a router architektúrájáról!")

        # b) irreleváns kérdés -> knowledge_used=False, NEM erőltet semmit
        reply_b, intent_b, model_used_b, sentence_info_b, guard_info_b = guarded_route_and_respond(
            general_model, instruction_model, "Mi a kedvenc filmed?", temperature=0.6,
            long_memory_enabled=True, long_memory_store_path=m_store,
            knowledge_enabled=True, knowledge_store_path=k_store,
        )
        check("irreleváns kérdés -> guard_info['knowledge_used'] is False", guard_info_b["knowledge_used"] is False)
        check("irreleváns kérdés -> knowledge_items üres", guard_info_b["knowledge_items"] == [])

        # c) knowledge_enabled=False -> még releváns kérdésre sem keres
        reply_c, intent_c, model_used_c, sentence_info_c, guard_info_c = guarded_route_and_respond(
            general_model, instruction_model, "Mesélj a router architektúrájáról!", temperature=0.6,
            knowledge_enabled=False, knowledge_store_path=k_store,
        )
        check("knowledge_enabled=False -> knowledge_used=False még releváns kérdésnél is",
              guard_info_c["knowledge_used"] is False)

        # d) a guard/short-memory/long-memory mezők továbbra is jelen vannak (nem tört el semmi)
        check("a tudásbázis mellett a guard többi mezője is jelen van", all(
            k in guard_info_a for k in (
                "detected_intent", "expected_answer_type", "guard_triggered",
                "memory_used", "long_memory_saved", "knowledge_used", "knowledge_items", "knowledge_query",
            )
        ))
else:
    print(f"  (kihagyva - nincs candidate A modell: {candidate_a_path})")


# ---------------------------------------------------------------------------
# 5) web/app.py API smoke teszt (GET/POST /api/knowledge/*) - Flask test
#    clienttel, IDEIGLENES store_path-ra állítva, az éles
#    knowledge_base/items.json-t NEM érinti.
# ---------------------------------------------------------------------------
print("\n--- web/app.py /api/knowledge/* smoke teszt ---")

WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "web")
sys.path.insert(0, WEB_DIR)

import app as webapp  # noqa: E402

with tempfile.TemporaryDirectory() as tmp_dir4:
    web_store_path = os.path.join(tmp_dir4, "items.json")
    webapp.cli_args.knowledge_store_path = web_store_path
    client = webapp.app.test_client()

    resp = client.get("/api/knowledge")
    data = resp.get_json()
    check("GET /api/knowledge -> 200, üres store esetén items=[]",
          resp.status_code == 200 and data["items"] == [])
    check("GET /api/knowledge válasza tartalmazza a 7 kategóriát", len(data["categories"]) == 7)

    resp = client.post("/api/knowledge/save", json={
        "title": "Teszt cím", "content": "Ez egy teszt tudáselem a smoke teszthez.",
        "category": "ai_project", "tags": "teszt, smoke",
    })
    data = resp.get_json()
    check("POST /api/knowledge/save -> 200, visszaadja az elemet", resp.status_code == 200 and "item" in data)
    check("POST /api/knowledge/save -> a tags vesszős stringből listává alakul",
          data["item"]["tags"] == ["smoke", "teszt"])
    web_item_id = data["item"]["id"]

    resp_empty = client.post("/api/knowledge/save", json={"content": "   "})
    check("üres content mentése -> 400", resp_empty.status_code == 400)

    resp = client.get("/api/knowledge")
    check("GET /api/knowledge -> mentés után tartalmazza az elemet",
          any(i["id"] == web_item_id for i in resp.get_json()["items"]))

    resp = client.post("/api/knowledge/search", json={"query": "smoke teszt"})
    check("POST /api/knowledge/search -> megtalálja a mentett elemet",
          any(i["id"] == web_item_id for i in resp.get_json()["items"]))

    resp_bad_cat = client.get("/api/knowledge?category=nem_letezik")
    check("GET /api/knowledge érvénytelen category paraméterrel -> 400", resp_bad_cat.status_code == 400)

    resp = client.post("/api/knowledge/delete", json={"id": web_item_id})
    check("POST /api/knowledge/delete -> 200, deleted=True",
          resp.status_code == 200 and resp.get_json()["deleted"] is True)

    resp_active = client.get("/api/knowledge?active=true")
    check("törlés után active=true szűrővel NEM jelenik meg",
          all(i["id"] != web_item_id for i in resp_active.get_json()["items"]))

    resp_missing = client.post("/api/knowledge/delete", json={"id": "nem-letezo-id"})
    check("nem létező id törlése -> 404", resp_missing.status_code == 404)

    # Biztonsági szabály: a chat /api/chat végpont NEM ment a tudásbázisba automatikusan
    before_count = len(client.get("/api/knowledge?active=false").get_json()["items"])
    resp_chat = client.post("/api/chat", json={"message": "A router külön modellt használ mondatszámhoz.",
                                                "temperature": 0.6, "sentences": 4})
    check("sima chat üzenet -> /api/chat válaszol", resp_chat.status_code == 200)
    after_count = len(client.get("/api/knowledge?active=false").get_json()["items"])
    check("sima chat üzenet NEM hozott létre új tudáselemet (elemszám nem nőtt)", after_count == before_count)


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
