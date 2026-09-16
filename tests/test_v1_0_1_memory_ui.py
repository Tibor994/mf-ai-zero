"""
MF-AI-Zero - v1.0.1 memória UI/API smoke teszt.

A web/app.py memória-kezelő végpontjait teszteli (GET /api/memories,
POST /api/memories/search, POST /api/memories/delete, POST
/api/memories/save) Flask test clienttel, egy IDEIGLENES store_path-ra
állítva a szervert - az éles long_term_memory/memories.json-t NEM érinti.

Ez NEM a chat-generálást teszteli (azt a test_v09_guard.py,
test_v09_memory.py, test_v1_0_long_memory.py és a compare_v09_guard.py
fedi le) - kizárólag azt, hogy a memória-kezelő felület API-rétege
helyesen listáz/keres/ment/töröl, és hogy a "ne mentsen automatikusan"
szabály a manuális mentési végponton keresztül is csak explicit kérésre
ír.

Futtatás:
    python tests/test_v1_0_1_memory_ui.py
"""

import os
import sys
import tempfile

WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "web")
SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
sys.path.insert(0, WEB_DIR)
sys.path.insert(0, SRC_DIR)

FAILURES = []


def check(label, condition):
    status = "OK" if condition else "FAIL"
    print(f"  [{status}] {label}")
    if not condition:
        FAILURES.append(label)


print("--- web/app.py betöltése (modell betöltés, ez eltarthat pár másodpercig) ---")
import app as webapp  # noqa: E402

with tempfile.TemporaryDirectory() as tmp_dir:
    store_path = os.path.join(tmp_dir, "memories.json")
    # A modult MÁR betöltöttük - a store_path-ot az élő cli_args objektumon
    # írjuk felül, hogy a teszt garantáltan NE az éles fájlt használja.
    webapp.cli_args.long_memory_store_path = store_path

    client = webapp.app.test_client()

    # -----------------------------------------------------------------
    print("\n--- GET /api/memories (üres store) ---")
    resp = client.get("/api/memories")
    data = resp.get_json()
    check("GET /api/memories -> 200", resp.status_code == 200)
    check("üres store -> memories=[]", data["memories"] == [])
    check("válasz tartalmazza a categories listát", "categories" in data and len(data["categories"]) == 5)

    # -----------------------------------------------------------------
    print("\n--- POST /api/memories/save (kézi mentés) ---")
    resp = client.post("/api/memories/save", json={"category": "user_preference", "text": "Szereti a teát."})
    data = resp.get_json()
    check("POST /api/memories/save -> 200", resp.status_code == 200)
    check("a válasz tartalmazza az új memóriát id-val", "memory" in data and data["memory"].get("id"))
    check("a mentett rekord source='manual_ui'", data["memory"]["source"] == "manual_ui")
    saved_id = data["memory"]["id"]

    resp_empty = client.post("/api/memories/save", json={"category": "user_fact", "text": "   "})
    check("üres szövegű mentés -> 400 hiba", resp_empty.status_code == 400)

    resp_bad_cat = client.post("/api/memories/save", json={"category": "nem_letezik", "text": "valami"})
    check("érvénytelen kategória -> mégis elmenti (user_fact fallback), nem dob hibát",
          resp_bad_cat.status_code == 200)

    # -----------------------------------------------------------------
    print("\n--- GET /api/memories (mentés után) ---")
    resp = client.get("/api/memories")
    data = resp.get_json()
    check("GET /api/memories -> tartalmazza a mentett rekordot", any(m["id"] == saved_id for m in data["memories"]))

    resp_cat = client.get("/api/memories?category=user_preference")
    data_cat = resp_cat.get_json()
    check("category szűrő -> csak azt a kategóriát adja vissza",
          all(m["category"] == "user_preference" for m in data_cat["memories"]) and len(data_cat["memories"]) >= 1)

    resp_bad_cat_filter = client.get("/api/memories?category=nem_letezik")
    check("GET /api/memories érvénytelen category paraméterrel -> 400", resp_bad_cat_filter.status_code == 400)

    # -----------------------------------------------------------------
    print("\n--- POST /api/memories/search ---")
    resp = client.post("/api/memories/search", json={"query": "tea"})
    data = resp.get_json()
    check("keresés 'tea'-ra megtalálja a mentett memóriát", any(m["id"] == saved_id for m in data["memories"]))

    resp_no_match = client.post("/api/memories/search", json={"query": "marslakó ufó randomszó"})
    check("keresés irreleváns szóra -> üres lista", resp_no_match.get_json()["memories"] == [])

    resp_empty_query = client.post("/api/memories/search", json={"query": ""})
    check("üres query -> üres lista, nem hibázik", resp_empty_query.status_code == 200
          and resp_empty_query.get_json()["memories"] == [])

    # -----------------------------------------------------------------
    print("\n--- POST /api/memories/delete (soft delete) ---")
    resp = client.post("/api/memories/delete", json={"id": saved_id})
    data = resp.get_json()
    check("POST /api/memories/delete -> 200, deleted=True", resp.status_code == 200 and data["deleted"] is True)

    resp_active = client.get("/api/memories?active=true")
    check("soft delete után active=true szűrővel NEM jelenik meg",
          all(m["id"] != saved_id for m in resp_active.get_json()["memories"]))

    resp_all = client.get("/api/memories?active=false")
    matching = [m for m in resp_all.get_json()["memories"] if m["id"] == saved_id]
    check("soft delete után active=false szűrővel MEGJELENIK, active=False mezővel",
          len(matching) == 1 and matching[0]["active"] is False)

    resp_missing = client.post("/api/memories/delete", json={"id": "nem-letezo-id-xyz"})
    check("nem létező id törlése -> 404, deleted=False",
          resp_missing.status_code == 404 and resp_missing.get_json()["deleted"] is False)

    resp_no_id = client.post("/api/memories/delete", json={})
    check("hiányzó id -> 400", resp_no_id.status_code == 400)

    # -----------------------------------------------------------------
    print("\n--- Biztonsági szabály: a chat /api/chat végpont NEM ment automatikusan ---")
    resp = client.post("/api/chat", json={"message": "Szeretem a kávét.", "temperature": 0.6, "sentences": 4})
    check("'Szeretem a kávét.' (sima kijelentés) -> /api/chat válaszol", resp.status_code == 200)
    resp_check = client.get("/api/memories?active=false")
    remaining = [m for m in resp_check.get_json()["memories"] if "kávét" in m["text"].lower()]
    check("sima kijelentés a chatben NEM hozott létre új memóriát", remaining == [])

    resp2 = client.post("/api/chat", json={"message": "Jegyezd meg, hogy szeretem a kávét.",
                                            "temperature": 0.6, "sentences": 4})
    check("'Jegyezd meg...' -> /api/chat válaszol", resp2.status_code == 200)
    check("'Jegyezd meg...' válasza determinisztikus visszaigazolás", "Megjegyeztem" in resp2.get_json()["reply"])
    resp_check2 = client.get("/api/memories?active=true")
    saved_via_chat = [m for m in resp_check2.get_json()["memories"] if "kávét" in m["text"].lower()]
    check("explicit 'jegyezd meg' a chatben TÉNYLEGESEN mentett egy memóriát", len(saved_via_chat) == 1)


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
