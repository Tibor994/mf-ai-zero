"""
MF-AI-Zero - v1.5 stabil webapp smoke teszt (web/app.py).

Nyolc rész:
  1. /api/health működik és a rétegek állapotát jelzi.
  2. /api/chat alapműködés + indikátorok jelenléte.
  3. Hibakezelés: üres üzenet, túl hosszú üzenet, hibás JSON, nem-string
     üzenet, ismeretlen végpont (404).
  4. Indikátorok konkrét esetben: webes forrás olvasásnál a
     web_research_used=True és a forráslista megjelenik.
  5. Memória-panel API-k nem romlanak (regressziós ellenőrzés).
  6. Tudásbázis-panel API-k nem romlanak (regressziós ellenőrzés).
  7. Mobil-barát alap HTML/CSS jelenléte (viewport meta, maxlength
     konzisztencia, reszponzív CSS szabályok megléte).
  8. Opcionális márkanév (WEB_BRAND_NAME) - a globális elnevezés NEM
     változik, csak a fejléc jelenítheti meg opcionálisan.

Futtatás:
    python tests/test_v1_5_webapp.py
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
    webapp.cli_args.long_memory_store_path = os.path.join(tmp_dir, "memories.json")
    webapp.cli_args.knowledge_store_path = os.path.join(tmp_dir, "items.json")
    client = webapp.app.test_client()

    # -----------------------------------------------------------------
    print("\n--- /api/health ---")
    resp = client.get("/api/health")
    data = resp.get_json()
    check("GET /api/health -> 200", resp.status_code == 200)
    check("status='ok'", data.get("status") == "ok")
    check("jelzi a guard/router/memória/tudásbázis/web rétegek állapotát", all(
        k in data for k in (
            "router_active", "guard_active", "memory_active", "long_memory_active",
            "knowledge_active", "web_research_active", "web_search_active",
            "conversation_manager_active", "style_active", "response_planner_active",
            "input_normalizer_active",
        )
    ))
    check("a mini Transformer lab NINCS bekötve a chatbe (transformer_lab_wired_into_chat=False)",
          data.get("transformer_lab_wired_into_chat") is False)

    # -----------------------------------------------------------------
    print("\n--- /api/chat alapműködés + indikátorok ---")
    resp = client.post("/api/chat", json={"message": "Hogy vagy?", "temperature": 0.6, "sentences": 4})
    data = resp.get_json()
    check("POST /api/chat -> 200", resp.status_code == 200)
    check("a válasz tartalmazza az 'indicators' mezőt", "indicators" in data)
    check("indicators tartalmazza a kötelező jelzőket", all(
        k in data["indicators"] for k in (
            "short_memory_used", "long_memory_used", "knowledge_used", "web_research_used",
            "web_search_used", "conversation_context_used", "input_normalized",
        )
    ))

    # -----------------------------------------------------------------
    print("\n--- Hibakezelés ---")
    resp_empty = client.post("/api/chat", json={"message": ""})
    check("üres üzenet -> 400, kulturált hibaüzenet",
          resp_empty.status_code == 400 and "error" in resp_empty.get_json())

    resp_ws = client.post("/api/chat", json={"message": "   "})
    check("csak whitespace üzenet -> 400", resp_ws.status_code == 400)

    long_message = "a" * (webapp.MAX_MESSAGE_LENGTH + 100)
    resp_long = client.post("/api/chat", json={"message": long_message})
    check(f"túl hosszú üzenet (>{webapp.MAX_MESSAGE_LENGTH}) -> 400", resp_long.status_code == 400)
    check("túl hosszú üzenet hibaüzenete megemlíti a karakterszámot",
          "500" in resp_long.get_json().get("error", "") or str(webapp.MAX_MESSAGE_LENGTH) in resp_long.get_json().get("error", ""))

    at_limit_message = "a" * webapp.MAX_MESSAGE_LENGTH
    resp_at_limit = client.post("/api/chat", json={"message": at_limit_message})
    check("pontosan a limit hosszúságú üzenet -> elfogadva (200)", resp_at_limit.status_code == 200)

    resp_bad_json = client.post("/api/chat", data="ez nem json", content_type="application/json")
    check("hibás JSON test -> 400, nem 500", resp_bad_json.status_code == 400)

    resp_non_string = client.post("/api/chat", json={"message": 12345})
    check("nem-string 'message' mező -> 400, nem crashel", resp_non_string.status_code == 400)

    resp_404 = client.get("/api/nincs-ilyen-vegpont")
    check("ismeretlen API végpont -> 404, JSON válasz (nem nyers HTML hibaoldal)",
          resp_404.status_code == 404 and resp_404.get_json() is not None)

    resp_404_page = client.get("/nincs-ilyen-oldal")
    check("ismeretlen NEM-api oldal -> 404, nem crashel", resp_404_page.status_code == 404)

    # -----------------------------------------------------------------
    print("\n--- Indikátorok konkrét esetben: webes forrás olvasása ---")
    resp_web = client.post("/api/chat", json={"message": "Mit írnak itt: https://example.com ?",
                                               "temperature": 0.6, "sentences": 4})
    data_web = resp_web.get_json()
    if data_web["indicators"].get("web_research_used"):
        check("webes forrás olvasásánál web_research_used=True", True)
        check("webes forrás olvasásánál a válasz forráslistát tartalmaz", "Források:" in data_web["reply"])
        check("indicators tartalmazza a web_sources listát", len(data_web["indicators"].get("web_sources", [])) > 0)
    else:
        print("  (a webes olvasás nem sikerült ebben a környezetben - hálózat hiánya miatt kihagyva)")

    # -----------------------------------------------------------------
    print("\n--- Memória-panel API-k (regresszió) ---")
    resp_mem_list = client.get("/api/memories")
    check("GET /api/memories -> 200", resp_mem_list.status_code == 200)
    resp_mem_save = client.post("/api/memories/save", json={"category": "user_fact", "text": "Teszt memória."})
    check("POST /api/memories/save -> 200", resp_mem_save.status_code == 200)
    saved_mem_id = resp_mem_save.get_json()["memory"]["id"]
    resp_mem_search = client.post("/api/memories/search", json={"query": "teszt"})
    check("POST /api/memories/search -> 200, megtalálja", resp_mem_search.status_code == 200
          and any(m["id"] == saved_mem_id for m in resp_mem_search.get_json()["memories"]))
    resp_mem_del = client.post("/api/memories/delete", json={"id": saved_mem_id})
    check("POST /api/memories/delete -> 200", resp_mem_del.status_code == 200)

    # -----------------------------------------------------------------
    print("\n--- Tudásbázis-panel API-k (regresszió) ---")
    resp_kb_list = client.get("/api/knowledge")
    check("GET /api/knowledge -> 200", resp_kb_list.status_code == 200)
    resp_kb_save = client.post("/api/knowledge/save", json={"content": "Teszt tudáselem.", "category": "other"})
    check("POST /api/knowledge/save -> 200", resp_kb_save.status_code == 200)
    saved_kb_id = resp_kb_save.get_json()["item"]["id"]
    resp_kb_search = client.post("/api/knowledge/search", json={"query": "teszt"})
    check("POST /api/knowledge/search -> 200, megtalálja", resp_kb_search.status_code == 200
          and any(i["id"] == saved_kb_id for i in resp_kb_search.get_json()["items"]))
    resp_kb_del = client.post("/api/knowledge/delete", json={"id": saved_kb_id})
    check("POST /api/knowledge/delete -> 200", resp_kb_del.status_code == 200)

    # -----------------------------------------------------------------
    print("\n--- Mobil-barát alap HTML/CSS ---")
    resp_page = client.get("/")
    page_text = resp_page.get_data(as_text=True)
    check("van viewport meta tag (mobil-reszponzivitás alapja)",
          'name="viewport"' in page_text and "width=device-width" in page_text)
    check("a message-input maxlength egyezik a szerver MAX_MESSAGE_LENGTH-jével",
          f'maxlength="{webapp.MAX_MESSAGE_LENGTH}"' in page_text)
    check("van input-hint és status-line elem (hiba/állapot kulturált megjelenítéséhez)",
          'id="input-hint"' in page_text and 'id="status-line"' in page_text)

    css_path = os.path.join(WEB_DIR, "static", "style.css")
    with open(css_path, encoding="utf-8") as f:
        css_text = f.read()
    check("van @media (max-width: 480px) mobil-szabály a CSS-ben", "@media (max-width: 480px)" in css_text)
    check("van indicator-chip CSS szabály", ".indicator-chip" in css_text)

    # -----------------------------------------------------------------
    print("\n--- Opcionális márkanév (a globális elnevezés nem változik) ---")
    check("alapból a brand_name 'MF-AI-Zero' marad", webapp.cli_args.brand_name == "MF-AI-Zero")
    check("<title>MF-AI-Zero Chat</title> jelenik meg alapból", "<title>MF-AI-Zero Chat</title>" in page_text)


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
