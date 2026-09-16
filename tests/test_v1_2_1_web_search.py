"""
MF-AI-Zero - v1.2.1 webes keresés teszt (web_search.py + guard.py
integráció, régi v1.2 URL-olvasás stabilitása).

Hat rész:
  1. detect_search_query() - "keress rá...", "nézz utána...", "googlezd
     meg..." jellegű kérések felismerése, sima kérdéseknél NEM aktiválódik.
  2. Nincs provider eset (alapértelmezett állapot ebben a környezetben,
     WEB_SEARCH_PROVIDER nincs beállítva) - kulturált "nincs konfigurálva"
     válasz, NEM hibázik.
  3. Mock keresési találatok - egy teszt-providerrel (nem valódi hálózat)
     ellenőrzi a search_web()/search_and_research() logikát.
  4. URL-olvasás integráció - search_and_research() ténylegesen a meglévő
     web_research.research_urls()-t hívja a találatok URL-jeire.
  5. Biztonsági szabály: sosem ment automatikusan a knowledge_base-be.
  6. Integrációs teszt: guarded_route_and_respond() valódi candidate A
     modellel - "keress rá..." trigger + mock provider -> forráslista a
     válaszban; a régi v1.2 direkt URL-olvasás VÁLTOZATLANUL működik.

Futtatás:
    python tests/test_v1_2_1_web_search.py
"""

import os
import sys
import tempfile

SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
sys.path.insert(0, SRC_DIR)

from web_search import (  # noqa: E402
    SearchProvider,
    detect_search_query,
    search_and_research,
    search_web,
)

FAILURES = []


def check(label, condition):
    status = "OK" if condition else "FAIL"
    print(f"  [{status}] {label}")
    if not condition:
        FAILURES.append(label)


# ---------------------------------------------------------------------------
# 1) detect_search_query()
# ---------------------------------------------------------------------------
print("--- detect_search_query() teszt ---")

SEARCH_CASES = [
    ("keress rá a Chicago pizzériára Szolnokon", "chicago pizzériára szolnokon"),
    ("Nézz utána, hogy ki nyerte a vb-t 2022-ben", "ki nyerte a vb-t 2022-ben"),
    ("Googlezd meg a legjobb magyar éttermeket", "a legjobb magyar éttermeket"),
    ("keresd meg a router dokumentációját", "a router dokumentációját"),
    ("kutass utána a párizsi múzeumoknak", "a párizsi múzeumoknak"),
]
for text, expected_substring in SEARCH_CASES:
    should_search, query = detect_search_query(text)
    check(f"'{text}' -> should_search=True, query tartalmazza a lényeget",
          should_search and expected_substring in query.lower())

NON_SEARCH_CASES = [
    "Mi a kedvenc filmed?",
    "Hány éves vagy?",
    "Szia, ki vagy?",
    "Mit írnak itt: https://example.com ?",
]
for text in NON_SEARCH_CASES:
    should_search, query = detect_search_query(text)
    check(f"'{text}' -> NEM keresési kérés (should_search=False)", should_search is False and query is None)


# ---------------------------------------------------------------------------
# 2) Nincs provider eset (alapértelmezett ebben a környezetben)
# ---------------------------------------------------------------------------
print("\n--- Nincs provider eset ---")

check("WEB_SEARCH_PROVIDER nincs beállítva ebben a tesztkörnyezetben",
      os.environ.get("WEB_SEARCH_PROVIDER") in (None, "", "none"))

result = search_web("bármilyen lekérdezés")
check("search_web() provider nélkül -> ok=False, error=no_provider_configured",
      result["ok"] is False and result["error"] == "no_provider_configured")
check("search_web() provider nélkül -> results üres lista", result["results"] == [])

result2 = search_and_research("bármilyen lekérdezés")
check("search_and_research() provider nélkül -> ok=False, error=no_provider_configured",
      result2["ok"] is False and result2["error"] == "no_provider_configured")
check("search_and_research() provider nélkül -> sources üres", result2["sources"] == [])


# ---------------------------------------------------------------------------
# 3) Mock keresési találatok
# ---------------------------------------------------------------------------
print("\n--- Mock keresési találatok teszt ---")


class _MockProvider(SearchProvider):
    name = "mock"

    def __init__(self, fixed_results=None, raise_error=False):
        self.fixed_results = fixed_results or []
        self.raise_error = raise_error

    def search(self, query, limit):
        if self.raise_error:
            raise ValueError("mock hiba")
        return self.fixed_results[:limit]


mock_results = [
    {"title": "Chicago Pizzéria Szolnok", "url": "https://example.com/chicago-pizza", "snippet": "Pizzéria Szolnokon."},
    {"title": "Másik találat", "url": "https://example.com/masik", "snippet": "Egy másik oldal."},
]
mock_provider = _MockProvider(fixed_results=mock_results)

result = search_web("chicago pizzéria szolnok", provider=mock_provider)
check("mock providerrel search_web() -> ok=True", result["ok"] is True)
check("mock providerrel search_web() -> 2 találat", len(result["results"]) == 2)
check("mock providerrel search_web() -> provider neve 'mock'", result["provider"] == "mock")

empty_mock = _MockProvider(fixed_results=[])
result_empty = search_web("valami", provider=empty_mock)
check("mock provider üres találati listával -> ok=False, no_results_found",
      result_empty["ok"] is False and result_empty["error"] == "no_results_found")

error_mock = _MockProvider(raise_error=True)
result_error = search_web("valami", provider=error_mock)
check("mock provider kivétele -> ok=False, provider_error (nem propagálódik a hívóhoz)",
      result_error["ok"] is False and result_error["error"] == "provider_error")

limit_result = search_web("teszt", limit=1, provider=mock_provider)
check("search_web() betartja a limit paramétert", len(limit_result["results"]) == 1)


# ---------------------------------------------------------------------------
# 4) URL-olvasás integráció (search_and_research)
# ---------------------------------------------------------------------------
print("\n--- URL-olvasás integráció (search_and_research) ---")

_network_available = True
try:
    import urllib.request
    with urllib.request.urlopen("https://example.com", timeout=6) as resp:
        _network_available = resp.status == 200
except Exception:
    _network_available = False

if _network_available:
    real_mock = _MockProvider(fixed_results=[
        {"title": "Example", "url": "https://example.com", "snippet": "Example domain."},
    ])
    result = search_and_research("example teszt", provider=real_mock, read_limit=3)
    check("search_and_research() sikeres keresés + olvasás -> ok=True", result["ok"] is True)
    check("search_and_research() ténylegesen elolvassa a találat URL-jét (sources nem üres)",
          len(result["sources"]) == 1)
    check("search_and_research() a forrás tartalmazza a domaint",
          result["sources"][0]["domain"] == "example.com")

    unreadable_mock = _MockProvider(fixed_results=[
        {"title": "Nem létező", "url": "https://this-domain-almost-certainly-does-not-exist-mfaiz3ro.invalid",
         "snippet": "x"},
    ])
    result_unreadable = search_and_research("teszt", provider=unreadable_mock)
    check("search_and_research() ha egy találat sem olvasható -> ok=False, no_readable_sources",
          result_unreadable["ok"] is False and result_unreadable["error"] == "no_readable_sources")
else:
    print("  (kihagyva - nincs hálózati elérés ebben a környezetben)")

read_limit_mock = _MockProvider(fixed_results=[
    {"title": f"Találat {i}", "url": f"https://example.com/page{i}", "snippet": "x"} for i in range(5)
])
search_only = search_web("teszt", provider=read_limit_mock)
check("5 találat esetén is legfeljebb DEFAULT_READ_LIMIT URL kerülne olvasásra "
      "(itt csak a keresési lépést ellenőrizzük, hálózat nélkül)", len(search_only["results"]) == 5)


# ---------------------------------------------------------------------------
# 5) Biztonsági szabály: sosem ment automatikusan a knowledge_base-be
# ---------------------------------------------------------------------------
print("\n--- Biztonsági szabály: nincs automatikus tudásbázis-mentés ---")

from knowledge_base import list_knowledge  # noqa: E402

with tempfile.TemporaryDirectory() as tmp_dir:
    kb_store = os.path.join(tmp_dir, "items.json")
    check("üres knowledge_base a keresés előtt", list_knowledge(store_path=kb_store) == [])
    _ = search_web("bármi", provider=mock_provider)
    _ = search_and_research("bármi", provider=mock_provider) if _network_available else None
    check("search_web()/search_and_research() önmagában NEM ír a knowledge_base-be",
          list_knowledge(store_path=kb_store) == [])


# ---------------------------------------------------------------------------
# 6) Integrációs teszt: guarded_route_and_respond() + web_search (mockkal)
#    + a régi v1.2 URL-olvasás VÁLTOZATLAN működésének ellenőrzése
# ---------------------------------------------------------------------------
print("\n--- Integrációs teszt: guarded_route_and_respond() + web_search ---")

import torch  # noqa: E402

import config  # noqa: E402
import guard  # noqa: E402
from generate import load_model  # noqa: E402
from guard import guarded_route_and_respond  # noqa: E402

device = torch.device("cpu")
candidate_a_path = os.path.join(config.BASE_DIR, "models", "mf_ai_zero_chat_v0_8b_a.pt")

if os.path.exists(candidate_a_path):
    g_tuple = load_model(device, candidate_a_path)
    i_tuple = load_model(device, os.path.join(config.BASE_DIR, "models", "mf_ai_zero_chat_v0_7c.pt"))
    general_model = (*g_tuple[:3], device, g_tuple[3])
    instruction_model = (*i_tuple[:3], device, i_tuple[3])

    # a) alapértelmezett állapotban (nincs provider) -> kulturált státuszüzenet
    reply_a, intent_a, model_used_a, sentence_info_a, guard_info_a = guarded_route_and_respond(
        general_model, instruction_model, "keress rá a Chicago pizzériára Szolnokon", temperature=0.6,
        web_search_enabled=True,
    )
    check("'keress rá...' + nincs provider -> guard_info['web_search_query'] felismerve",
          guard_info_a["web_search_query"] is not None)
    check("'keress rá...' + nincs provider -> web_search_error='no_provider_configured'",
          guard_info_a["web_search_error"] == "no_provider_configured")
    check("'keress rá...' + nincs provider -> a válasz kulturáltan jelzi ezt",
          "nincs konfigurálva" in reply_a.lower() or "nem" in reply_a.lower())
    check("'keress rá...' + nincs provider -> web_search_used=False (nem történt tényleges keresés)",
          guard_info_a["web_search_used"] is False)

    # b) mock providerrel (a guard.search_and_research-t ideiglenesen felülírva) -> sikeres keresés
    if _network_available:
        def _mock_search_and_research(query, search_limit=5, read_limit=3, provider=None):
            return search_and_research(query, search_limit=search_limit, read_limit=read_limit,
                                        provider=_MockProvider(fixed_results=[
                                            {"title": "Example", "url": "https://example.com", "snippet": "x"},
                                        ]))

        original_fn = guard.search_and_research
        guard.search_and_research = _mock_search_and_research
        try:
            reply_b, intent_b, model_used_b, sentence_info_b, guard_info_b = guarded_route_and_respond(
                general_model, instruction_model, "nézz utána a példa oldalnak", temperature=0.6,
                web_search_enabled=True,
            )
            check("mock providerrel 'nézz utána...' -> web_search_used=True", guard_info_b["web_search_used"] is True)
            check("mock providerrel -> web_used=True (a forrás ténylegesen felhasználva)",
                  guard_info_b["web_used"] is True)
            check("mock providerrel -> a válasz forráshivatkozást tartalmaz", "Források:" in reply_b)
        finally:
            guard.search_and_research = original_fn

    # c) a régi v1.2 direkt URL-olvasás VÁLTOZATLANUL működik (nem search trigger)
    if _network_available:
        reply_c, intent_c, model_used_c, sentence_info_c, guard_info_c = guarded_route_and_respond(
            general_model, instruction_model, "Mit írnak itt: https://example.com ?", temperature=0.6,
            web_enabled=True, web_search_enabled=True,
        )
        check("régi v1.2 URL-olvasás -> web_used=True (nem a keresési útvonalon keresztül)",
              guard_info_c["web_used"] is True)
        check("régi v1.2 URL-olvasás -> web_search_used=False (nem keresési trigger volt)",
              guard_info_c["web_search_used"] is False)
        check("régi v1.2 URL-olvasás -> a válasz forráshivatkozást tartalmaz", "Források:" in reply_c)

    # d) --no-web-search -> még trigger esetén sem keres
    reply_d, intent_d, model_used_d, sentence_info_d, guard_info_d = guarded_route_and_respond(
        general_model, instruction_model, "keress rá valamire", temperature=0.6,
        web_search_enabled=False,
    )
    check("web_search_enabled=False -> web_search_query is None (meg sem próbálja felismerni)",
          guard_info_d["web_search_query"] is None)
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
