"""
MF-AI-Zero - v1.2 webkutatás teszt (web_research.py + guard.py integráció).

Hat rész:
  1. detect_urls() - URL-kinyerés szövegből.
  2. SSRF-védelem - localhost/privát IP-cím tiltása.
  3. Valódi hálózati teszt: publikus URL olvasása (https://example.com -
     stabil, IANA által fenntartott, pont erre a célra ajánlott teszt-
     domain). Ha nincs hálózati elérés, ez a szakasz kihagyásra kerül
     (nem bukik el emiatt a teljes teszt).
  4. Rossz URL kezelése - érvénytelen séma, nem létező domain.
  5. Túl hosszú oldal rövidítése - szintetikus, hosszú HTML-lel (nem
     igényel hálózatot).
  6. Integrációs teszt: guarded_route_and_respond() valódi candidate A
     modellel - URL a user üzenetében -> web_used=True + forráslista a
     válaszban; nincs URL -> web_used=False; a tudásbázis SOSEM ír
     automatikusan (csak explicit save_knowledge()/API hívással).

Futtatás:
    python tests/test_v1_2_web_research.py
"""

import os
import sys
import tempfile

SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
sys.path.insert(0, SRC_DIR)

from web_research import (  # noqa: E402
    EXCERPT_CHARS,
    MAX_SOURCES,
    _TextExtractor,
    _is_safe_host,
    build_web_prompt_context,
    detect_urls,
    fetch_url,
    format_source_citations,
    research_urls,
    summarize_source,
    to_knowledge_candidates,
)

FAILURES = []


def check(label, condition):
    status = "OK" if condition else "FAIL"
    print(f"  [{status}] {label}")
    if not condition:
        FAILURES.append(label)


# ---------------------------------------------------------------------------
# 1) detect_urls()
# ---------------------------------------------------------------------------
print("--- detect_urls() teszt ---")

check("egy URL felismerve", detect_urls("Nézd meg ezt: https://example.com") == ["https://example.com"])
check("két URL, sorrendtartó, duplikátum nélkül", detect_urls(
    "https://a.com és https://b.com és https://a.com megint"
) == ["https://a.com", "https://b.com"])
check("mondatvégi írásjel levágva", detect_urls("Lásd https://example.com/page.") == ["https://example.com/page"])
check("nincs URL -> üres lista", detect_urls("Ez egy sima mondat URL nélkül.") == [])
check("üres szöveg -> üres lista", detect_urls("") == [])
check("zárójelbe tett URL -> a zárójel nem kerül bele", detect_urls("(https://example.com)") == ["https://example.com"])


# ---------------------------------------------------------------------------
# 2) SSRF-védelem
# ---------------------------------------------------------------------------
print("\n--- SSRF-védelem teszt ---")

check("localhost -> nem biztonságos host", _is_safe_host("localhost") is False)
check("127.0.0.1 -> nem biztonságos host", _is_safe_host("127.0.0.1") is False)
check("0.0.0.0 -> nem biztonságos host", _is_safe_host("0.0.0.0") is False)
check("192.168.1.1 (privát tartomány) -> nem biztonságos host", _is_safe_host("192.168.1.1") is False)
check("10.0.0.5 (privát tartomány) -> nem biztonságos host", _is_safe_host("10.0.0.5") is False)

result = fetch_url("http://127.0.0.1/admin")
check("fetch_url() blokkolja a localhost-ot -> ok=False, error=blocked_host",
      result["ok"] is False and result["error"] == "blocked_host")

result = fetch_url("ftp://example.com/file")
check("fetch_url() elutasítja a nem http(s) sémát -> error=invalid_scheme",
      result["ok"] is False and result["error"] == "invalid_scheme")


# ---------------------------------------------------------------------------
# 3) Valódi hálózati teszt - publikus URL olvasása
# ---------------------------------------------------------------------------
print("\n--- Valódi hálózati teszt: https://example.com olvasása ---")

_network_available = True
try:
    _probe = fetch_url("https://example.com", timeout=6)
    _network_available = _probe["ok"]
except Exception:
    _network_available = False

if _network_available:
    result = summarize_source("https://example.com")
    check("summarize_source() sikeresen olvassa a publikus oldalt", result["ok"] is True)
    check("summarize_source() kinyeri a címet", "example" in result["title"].lower())
    check("summarize_source() domain mezője helyes", result["domain"] == "example.com")
    check("summarize_source() nem üres kivonat", len(result["excerpt"]) > 0)
    check("summarize_source() kivonat a hossz-korláton belül", len(result["excerpt"]) <= EXCERPT_CHARS)

    sources, errors = research_urls(["https://example.com"], limit=3)
    check("research_urls() egy sikeres forrást ad vissza", len(sources) == 1 and errors == [])

    ctx = build_web_prompt_context(sources)
    check("build_web_prompt_context() 'User:'/'AI:' natív formátumú",
          ctx.startswith("User:") and "\nAI:" in ctx and ctx.endswith("\n\n"))

    citations = format_source_citations(sources)
    check("format_source_citations() tartalmazza a domaint", "example.com" in citations)

    candidates = to_knowledge_candidates(sources)
    check("to_knowledge_candidates() knowledge_base-kompatibilis mezőket ad",
          len(candidates) == 1 and all(
              k in candidates[0] for k in ("title", "content", "category", "tags", "source")
          ))
else:
    print("  (kihagyva - nincs hálózati elérés ebben a környezetben)")


# ---------------------------------------------------------------------------
# 4) Rossz URL kezelése
# ---------------------------------------------------------------------------
print("\n--- Rossz URL kezelése ---")

result = fetch_url("https://this-domain-almost-certainly-does-not-exist-mfaiz3ro.invalid")
check("nem létező domain -> ok=False, network_error", result["ok"] is False and result["error"] == "network_error")

result = fetch_url("nincs-is-url-formatum")
check("nem URL formátumú szöveg -> ok=False, invalid_url vagy invalid_scheme",
      result["ok"] is False and result["error"] in ("invalid_url", "invalid_scheme"))

sources, errors = research_urls(["https://this-domain-almost-certainly-does-not-exist-mfaiz3ro.invalid"])
check("research_urls() a sikertelen URL-t az errors listába teszi, NEM a sources-ba",
      sources == [] and len(errors) == 1 and errors[0]["reason"] == "network_error")


# ---------------------------------------------------------------------------
# 5) Túl hosszú oldal rövidítése - szintetikus HTML, nem igényel hálózatot
# ---------------------------------------------------------------------------
print("\n--- Túl hosszú oldal rövidítése (szintetikus HTML) ---")

long_html = "<html><head><title>Hosszú teszt oldal</title></head><body>"
long_html += "<script>var x = 'ez script, nem szabad bekerulnie';</script>"
long_html += "<p>" + ("Ez egy nagyon hosszú bekezdés szöveg ismétlődéssel. " * 200) + "</p>"
long_html += "</body></html>"

parser = _TextExtractor()
parser.feed(long_html)
check("_TextExtractor kihagyja a <script> tartalmát", "ez script" not in parser.text.lower())
check("_TextExtractor kinyeri a címet", parser.title == "Hosszú teszt oldal")
check("_TextExtractor a teljes (hosszú) szöveget adja vissza (a vágás summarize_source-ban történik)",
      len(parser.text) > EXCERPT_CHARS)

many_urls = [f"https://example.com/page{i}" for i in range(10)]
limited_sources, _ = research_urls([], limit=100)
check("research_urls() limit sosem lépi túl MAX_SOURCES-t (üres lista -> üres eredmény)", limited_sources == [])
check(f"MAX_SOURCES értéke {MAX_SOURCES} (max 3-5 forrás egyszerre)", 3 <= MAX_SOURCES <= 5)


# ---------------------------------------------------------------------------
# 6) Integrációs teszt: guarded_route_and_respond() valódi candidate A modellel
# ---------------------------------------------------------------------------
print("\n--- Integrációs teszt: guarded_route_and_respond() + webkutatás ---")

import torch  # noqa: E402

import config  # noqa: E402
from generate import load_model  # noqa: E402
from guard import guarded_route_and_respond  # noqa: E402
from knowledge_base import list_knowledge  # noqa: E402

device = torch.device("cpu")
candidate_a_path = os.path.join(config.BASE_DIR, "models", "mf_ai_zero_chat_v0_8b_a.pt")

if os.path.exists(candidate_a_path) and _network_available:
    g_tuple = load_model(device, candidate_a_path)
    i_tuple = load_model(device, os.path.join(config.BASE_DIR, "models", "mf_ai_zero_chat_v0_7c.pt"))
    general_model = (*g_tuple[:3], device, g_tuple[3])
    instruction_model = (*i_tuple[:3], device, i_tuple[3])

    with tempfile.TemporaryDirectory() as tmp_dir:
        k_store = os.path.join(tmp_dir, "items.json")

        # a) URL a user üzenetében -> web_used=True, forráslista a válaszban
        reply_a, intent_a, model_used_a, sentence_info_a, guard_info_a = guarded_route_and_respond(
            general_model, instruction_model, "Mit írnak itt: https://example.com ?", temperature=0.6,
            web_enabled=True, knowledge_enabled=True, knowledge_store_path=k_store,
        )
        check("URL a user üzenetében -> guard_info['web_used'] is True", guard_info_a["web_used"] is True)
        check("URL a user üzenetében -> web_sources nem üres", len(guard_info_a["web_sources"]) > 0)
        check("URL a user üzenetében -> a válasz tartalmaz forráshivatkozást ('Források:')",
              "Források:" in reply_a)
        check("web_detected_urls tartalmazza a beküldött URL-t",
              "https://example.com" in guard_info_a["web_detected_urls"])

        # b) nincs URL -> web_used=False, nincs erőltetett forrás
        reply_b, intent_b, model_used_b, sentence_info_b, guard_info_b = guarded_route_and_respond(
            general_model, instruction_model, "Mi a kedvenc filmed?", temperature=0.6,
            web_enabled=True,
        )
        check("nincs URL a kérdésben -> guard_info['web_used'] is False", guard_info_b["web_used"] is False)
        check("nincs URL -> nincs forráshivatkozás a válaszban", "Források:" not in reply_b)

        # c) web_enabled=False -> még URL esetén sem kutat
        reply_c, intent_c, model_used_c, sentence_info_c, guard_info_c = guarded_route_and_respond(
            general_model, instruction_model, "Mit írnak itt: https://example.com ?", temperature=0.6,
            web_enabled=False,
        )
        check("web_enabled=False -> web_used=False még URL esetén is", guard_info_c["web_used"] is False)

        # d) biztonsági szabály: a webkutatás NEM ír automatikusan a knowledge_base-be
        check("webkutatás után a knowledge_base ÜRES marad (nincs automatikus mentés)",
              list_knowledge(active_only=False, store_path=k_store) == [])
else:
    print(f"  (kihagyva - nincs candidate A modell vagy nincs hálózat: {candidate_a_path})")


# ---------------------------------------------------------------------------
# 7) web/app.py API smoke teszt (POST /api/web/research, /api/web/save-candidate)
# ---------------------------------------------------------------------------
print("\n--- web/app.py /api/web/* smoke teszt ---")

if _network_available:
    WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "web")
    sys.path.insert(0, WEB_DIR)

    import app as webapp  # noqa: E402

    with tempfile.TemporaryDirectory() as tmp_dir2:
        web_k_store = os.path.join(tmp_dir2, "items.json")
        webapp.cli_args.knowledge_store_path = web_k_store
        client = webapp.app.test_client()

        resp = client.post("/api/web/research", json={"urls": ["https://example.com"]})
        data = resp.get_json()
        check("POST /api/web/research -> 200", resp.status_code == 200)
        check("POST /api/web/research -> egy sikeres forrás", len(data["sources"]) == 1)
        check("POST /api/web/research -> ad knowledge_candidates-et (de nem menti)",
              len(data["knowledge_candidates"]) == 1)
        check("POST /api/web/research után a knowledge_base MÉG üres (nincs automatikus mentés)",
              list_knowledge(active_only=False, store_path=web_k_store) == [])

        resp_no_url = client.post("/api/web/research", json={"urls": []})
        check("üres urls lista -> 400", resp_no_url.status_code == 400)

        candidate = data["knowledge_candidates"][0]
        resp_save = client.post("/api/web/save-candidate", json=candidate)
        data_save = resp_save.get_json()
        check("POST /api/web/save-candidate -> 200, elmenti a jelöltet",
              resp_save.status_code == 200 and "item" in data_save)
        check("POST /api/web/save-candidate után a knowledge_base tartalmazza az elemet",
              len(list_knowledge(active_only=False, store_path=web_k_store)) == 1)

        resp_empty = client.post("/api/web/save-candidate", json={"content": "  "})
        check("üres content jóváhagyása -> 400", resp_empty.status_code == 400)
else:
    print("  (kihagyva - nincs hálózati elérés ebben a környezetben)")


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
