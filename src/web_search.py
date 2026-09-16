"""
MF-AI-Zero - v1.2.1 webes keresés (web_search).

CÉL: a user ne csak konkrét URL-t adhasson meg (lásd web_research.py,
v1.2), hanem kereshessen is ("keress rá a Chicago pizzériára Szolnokon",
"nézz utána...", "googlezd meg..."). Ez a modul csak a KERESÉST végzi
(kulcsszó -> találati lista) - a találatok tényleges elolvasása a
meglévő, stabil web_research.py feladata marad (lásd search_and_research()
a fájl végén, ami a kettőt összeköti).

FONTOS, amit ez a modul SZÁNDÉKOSAN NEM csinál:
  - NEM scrape-eli agresszíven a Google (vagy bármelyik keresőmotor)
    HTML-ét - ez sértené a keresők használati feltételeit, és könnyen
    instabil/blokkolt is lenne. Helyette PROVIDER-alapú réteg: konkrét,
    hivatalos keresési API-kat hív (lásd _PROVIDERS).
  - Ha NINCS beállítva provider (ez az ALAPÉRTELMEZETT állapot - a
    WEB_SEARCH_PROVIDER env változó nélkül semmi nem aktiválódik magától),
    KULTURÁLTAN jelzi, hogy a keresés nincs konfigurálva - nem próbál
    kerülőutat.
  - NEM próbál fizetős/belépős/CAPTCHA-s keresőoldalt megkerülni.
  - NEM ment semmit automatikusan a tudásbázisba - ez itt is (mint a
    web_research.py-nál) csak jelölt-generálásig terjed.

Provider-réteg (env változók):
  WEB_SEARCH_PROVIDER = "none" (alapértelmezett) | "duckduckgo" | "bing"
  WEB_SEARCH_API_KEY  = csak API-kulcsos providerekhez (pl. "bing")

  - "duckduckgo": a DuckDuckGo hivatalos, publikus Instant Answer JSON
    API-ját hívja (api.duckduckgo.com/?format=json) - nem igényel API
    kulcsot, nem HTML-scraping, a DDG saját, erre szánt végpontja. Fontos
    korlát: ez elsősorban ismert fogalmakhoz/entitásokhoz ad rövid
    összefoglalót, NEM általános, minden témára kiterjedő webkeresés -
    sok (pl. helyi/lokális) kérdésre üres találati listát ad, ez NEM hiba,
    csak a provider korlátja.
  - "bing": Bing Web Search API (Azure Cognitive Services) - API kulcsot
    igényel (WEB_SEARCH_API_KEY), csak akkor aktiválódik, ha ez be van
    állítva.
"""

import json
import os
import re
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

MAX_RESULTS = 5
DEFAULT_RESULTS = 5
DEFAULT_READ_LIMIT = 3
REQUEST_TIMEOUT = 8

USER_AGENT = (
    "MF-AI-Zero-WebSearch/1.2.1 (research client, own use; "
    "does not impersonate a browser)"
)


def _normalize(text):
    text = (text or "").lower()
    decomposed = unicodedata.normalize("NFKD", text)
    without_accents = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", without_accents).strip()


# ---------------------------------------------------------------------------
# 1) Kereső-lekérdezés felismerése a user szövegében ("keress rá...",
#    "nézz utána...", "googlezd meg...") - EZ az egyetlen aktiváló jel,
#    nincs automatikus, minden üzenetnél lefutó keresés.
# ---------------------------------------------------------------------------

SEARCH_TRIGGER_PATTERNS = [
    r"keress\s+r[aá]",
    r"keress\s+ut[aá]na",
    r"n[eé]zz\s+ut[aá]na",
    r"n[eé]zzel?\s+ut[aá]na",
    r"googlezd\s+meg",
    r"googlizd\s+meg",
    r"keresd\s+meg",
    r"kutass\s+ut[aá]na",
    r"j[aá]rj\s+ut[aá]na",
]


def detect_search_query(text):
    """Visszaadja (should_search: bool, query: str|None). A query a
    trigger-kifejezés UTÁNI, megtisztított rész - ha a trigger után nem
    marad tartalmas szöveg, should_search=False (nincs mit keresni)."""
    text = text or ""
    for pattern in SEARCH_TRIGGER_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            continue
        remainder = text[match.end():]
        remainder = re.sub(r"^[\s,:-]+", "", remainder)
        remainder = re.sub(r"^hogy\b[\s,]*", "", remainder, flags=re.IGNORECASE)
        remainder = remainder.strip().rstrip(".!?").strip()
        if remainder:
            return True, remainder
    return False, None


# ---------------------------------------------------------------------------
# 2) Provider-interfész - konkrét keresési API-k, NEM HTML-scraping
# ---------------------------------------------------------------------------


class SearchProvider:
    name = "base"

    def search(self, query, limit):
        """Visszaad egy listát [{"title","url","snippet"}, ...] alakban.
        Hiba esetén kivételt dobhat - a hívó (search_web) elkapja."""
        raise NotImplementedError


class NoProvider(SearchProvider):
    """Ez fut, ha nincs WEB_SEARCH_PROVIDER beállítva - NEM próbál semmit,
    kulturáltan jelzi a hívónak, hogy a keresés nincs konfigurálva."""

    name = "none"

    def search(self, query, limit):
        return []


class DuckDuckGoProvider(SearchProvider):
    """A DuckDuckGo hivatalos, publikus Instant Answer JSON API-ja - nem
    igényel kulcsot, nem HTML-scraping (lásd a modul fejléce)."""

    name = "duckduckgo"

    def search(self, query, limit):
        params = urllib.parse.urlencode({
            "q": query, "format": "json", "no_html": "1", "no_redirect": "1", "skip_disambig": "1",
        })
        url = f"https://api.duckduckgo.com/?{params}"
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
            data = json.loads(response.read().decode("utf-8", errors="replace"))

        results = []
        if data.get("AbstractURL") and data.get("AbstractText"):
            results.append({
                "title": data.get("Heading") or query,
                "url": data["AbstractURL"],
                "snippet": data["AbstractText"],
            })
        for topic in data.get("RelatedTopics", []):
            if len(results) >= limit:
                break
            if isinstance(topic, dict) and topic.get("FirstURL") and topic.get("Text"):
                results.append({
                    "title": topic.get("Text", "")[:80],
                    "url": topic["FirstURL"],
                    "snippet": topic.get("Text", ""),
                })
        return results[:limit]


class BingProvider(SearchProvider):
    """Bing Web Search API (Azure Cognitive Services) - API kulcsot
    igényel (WEB_SEARCH_API_KEY), csak akkor aktiválódik, ha be van
    állítva. Ez a "API-kulcsos provider" opció a két lehetőség közül."""

    name = "bing"
    ENDPOINT = "https://api.bing.microsoft.com/v7.0/search"

    def __init__(self, api_key):
        self.api_key = api_key

    def search(self, query, limit):
        params = urllib.parse.urlencode({"q": query, "count": limit, "mkt": "hu-HU"})
        url = f"{self.ENDPOINT}?{params}"
        request = urllib.request.Request(
            url, headers={"Ocp-Apim-Subscription-Key": self.api_key, "User-Agent": USER_AGENT}
        )
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
            data = json.loads(response.read().decode("utf-8", errors="replace"))
        results = []
        for item in (data.get("webPages", {}) or {}).get("value", [])[:limit]:
            results.append({
                "title": item.get("name", ""),
                "url": item.get("url", ""),
                "snippet": item.get("snippet", ""),
            })
        return results


def _resolve_provider():
    """Env változókból dönti el, melyik provider aktív. Alapértelmezés
    "none" - EXPLICIT WEB_SEARCH_PROVIDER beállítás nélkül semmi nem
    aktiválódik magától."""
    provider_name = (os.environ.get("WEB_SEARCH_PROVIDER") or "none").strip().lower()
    if provider_name in ("", "none"):
        return NoProvider()
    if provider_name == "duckduckgo":
        return DuckDuckGoProvider()
    if provider_name == "bing":
        api_key = os.environ.get("WEB_SEARCH_API_KEY")
        if not api_key:
            return NoProvider()
        return BingProvider(api_key)
    return NoProvider()


# ---------------------------------------------------------------------------
# 3) Fő belépési pont: keresés
# ---------------------------------------------------------------------------


def search_web(query, limit=DEFAULT_RESULTS, provider=None):
    """Visszaad egy dict-et: {"ok","provider","results","error"}.

    provider: opcionális, teszteléshez - ha megadod, ezt használja a
    _resolve_provider() env-alapú döntése helyett (pl. egy mock
    providerrel a valódi hálózat elkerülésére)."""
    limit = max(1, min(limit, MAX_RESULTS))
    query = (query or "").strip()
    if not query:
        return {"ok": False, "provider": None, "results": [], "error": "empty_query"}

    active_provider = provider or _resolve_provider()
    if isinstance(active_provider, NoProvider):
        return {"ok": False, "provider": "none", "results": [], "error": "no_provider_configured"}

    try:
        results = active_provider.search(query, limit)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError, ValueError, KeyError):
        return {"ok": False, "provider": active_provider.name, "results": [], "error": "provider_error"}

    results = results[:limit]
    if not results:
        return {"ok": False, "provider": active_provider.name, "results": [], "error": "no_results_found"}
    return {"ok": True, "provider": active_provider.name, "results": results, "error": None}


def search_and_research(query, search_limit=DEFAULT_RESULTS, read_limit=DEFAULT_READ_LIMIT, provider=None):
    """Összeköti a keresést a meglévő, stabil web_research.research_urls()
    olvasóval: query -> találatok -> (a találatok URL-jeiből, legfeljebb
    read_limit darabból) tényleges oldal-olvasás -> kivonat.

    Helyi import: hogy a web_search.py önmagában (web_research nélkül is)
    importálható/tesztelhető maradjon, és elkerüljük a körkörös importot."""
    from web_research import research_urls

    search_result = search_web(query, limit=search_limit, provider=provider)
    base = {
        "ok": False, "provider": search_result["provider"], "search_results": search_result["results"],
        "sources": [], "errors": [], "error": search_result["error"],
    }
    if not search_result["ok"]:
        return base

    urls = [r["url"] for r in search_result["results"] if r.get("url")][:read_limit]
    if not urls:
        base["error"] = "no_results_found"
        return base

    sources, errors = research_urls(urls, limit=read_limit)
    if not sources:
        base["errors"] = errors
        base["error"] = "no_readable_sources"
        return base

    return {
        "ok": True, "provider": search_result["provider"], "search_results": search_result["results"],
        "sources": sources, "errors": errors, "error": None,
    }
