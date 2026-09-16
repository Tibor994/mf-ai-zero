"""
MF-AI-Zero - v1.2 webkutatás (web_research).

CÉL: az AI tudjon NYILVÁNOS weboldalakról információt olvasni, és a
válaszadáshoz FORRÁS-ALAPÚ, hivatkozott kontextusként felhasználni.

Hogyan aktiválódik: amikor a user üzenete tartalmaz egy vagy több
http(s):// URL-t - ez egy EXPLICIT, egyértelmű jel ("olvasd el ezt: ..."),
NEM egy automatikus, önálló webkereső ügynök. Ez a modul NEM keres
("Google-öz") a weben - kizárólag a user által MEGADOTT URL-eket olvassa
el. Legfeljebb MAX_SOURCES (5) forrást dolgoz fel egyszerre.

FONTOS, amit ez a modul SZÁNDÉKOSAN NEM csinál:
  - NEM automatikus, "vak" internetes tanulás - a talált szöveg csak a
    válasz PROMPTJÁBA kerülő, rövid kontextus, és a válaszhoz csatolt
    forráslista. A tudásbázisba (knowledge_base) NEM ír automatikusan.
  - NEM próbál bejelentkezős/fizetős/CAPTCHA-s vagy egyéb védett oldalt
    megkerülni - egyetlen, egyszerű GET kérést küld, VALÓDI (nem
    böngészőnek álcázott) User-Agent-tel; ha az oldal 401/402/403/407/429
    választ ad, vagy CAPTCHA-gyanús, azt egyszerűen "nem olvasható"-ként
    kezeli, nem próbálkozik újra más fejléccel/proxyval.
  - NEM ér el belső/privát hálózati címet (SSRF-védelem: localhost, privát
    IP-tartományok, link-local címek blokkolva) - csak a nyilvános
    interneten publikált oldalakat olvassa.
  - NEM tanítja újra a modellt semmilyen webes tartalommal.
  - A talált tartalomból KIZÁRÓLAG jóváhagyás után (lásd
    to_knowledge_candidates() + a hívó fél explicit save_knowledge()
    hívása) kerülhet bármi a tudásbázisba - ez a modul saját magától
    sosem ír a knowledge_base-be.
"""

import ipaddress
import re
import socket
import unicodedata
import urllib.error
import urllib.request
from html.parser import HTMLParser
from urllib.parse import urlparse

MAX_SOURCES = 5
DEFAULT_SOURCES = 3
REQUEST_TIMEOUT = 8
MAX_CONTENT_BYTES = 2_000_000  # 2 MB - ennél nagyobb oldalt nem dolgoz fel
EXCERPT_CHARS = 400
MAX_PROMPT_EXCERPT_CHARS = 150
MAX_CONTEXT_CHARS = 260

ALLOWED_SCHEMES = ("http", "https")
BLOCKED_STATUS_CODES = {401, 402, 403, 407, 429}

USER_AGENT = (
    "MF-AI-Zero-WebResearch/1.2 (research client, own use; "
    "does not impersonate a browser)"
)

URL_PATTERN = re.compile(r"https?://[^\s<>\"'\]\)]+")


def _normalize(text):
    text = (text or "").lower()
    decomposed = unicodedata.normalize("NFKD", text)
    without_accents = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", without_accents).strip()


def _trim(text, limit):
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 3)].rstrip() + "..."


def detect_urls(text):
    """Kinyeri a szövegben szereplő http(s):// URL-eket, sorrendtartóan,
    duplikátum nélkül - EZ a modul egyetlen "keresési" mechanizmusa: nem
    keres a weben, csak azt olvassa, amit a user kifejezetten megadott."""
    if not text:
        return []
    found = URL_PATTERN.findall(text)
    cleaned = []
    for url in found:
        url = url.rstrip(".,;:!?)")
        if url not in cleaned:
            cleaned.append(url)
    return cleaned


# ---------------------------------------------------------------------------
# SSRF-védelem: csak nyilvános, kívülről elérhető hosztokra engedünk kérést.
# ---------------------------------------------------------------------------


def _is_safe_host(hostname):
    """Igaz, ha a hosztnév biztonságosan elérhető (NEM oldódik fel privát/
    belső IP-címre). Ha a név EGYÁLTALÁN NEM oldható fel (nem létező
    domain), az NEM SSRF-kockázat (nincs mit elérni) - ezt a tényleges
    kérés fogja természetesen "network_error"-ként jelenteni, itt True-t
    adunk vissza, hogy ne keveredjen össze a két hibatípus."""
    if not hostname:
        return False
    if hostname.lower() in ("localhost",):
        return False
    try:
        infos = socket.getaddrinfo(hostname, None)
    except (socket.gaierror, UnicodeError):
        return True
    if not infos:
        return True
    for info in infos:
        ip_str = info[4][0]
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            continue
        if (ip.is_private or ip.is_loopback or ip.is_link_local
                or ip.is_reserved or ip.is_multicast or ip.is_unspecified):
            return False
    return True


# ---------------------------------------------------------------------------
# Letöltés + HTML -> tiszta szöveg kinyerés (csak stdlib, nincs külső
# függőség - sem requests, sem bs4 nincs telepítve ebben a projektben)
# ---------------------------------------------------------------------------


class _TextExtractor(HTMLParser):
    """Egyszerű HTML -> szöveg kinyerő: kihagyja a script/style/nav/
    footer/header tartalmát, külön gyűjti a <title>-t."""

    _SKIP_TAGS = ("script", "style", "noscript", "nav", "footer", "header")

    def __init__(self):
        super().__init__()
        self._skip_stack = []
        self._in_title = False
        self.title_parts = []
        self.text_parts = []

    def handle_starttag(self, tag, attrs):
        if tag in self._SKIP_TAGS:
            self._skip_stack.append(tag)
        if tag == "title":
            self._in_title = True

    def handle_endtag(self, tag):
        if self._skip_stack and self._skip_stack[-1] == tag:
            self._skip_stack.pop()
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title_parts.append(data)
            return
        if self._skip_stack:
            return
        stripped = data.strip()
        if stripped:
            self.text_parts.append(stripped)

    @property
    def title(self):
        return " ".join("".join(self.title_parts).split())

    @property
    def text(self):
        return " ".join(self.text_parts)


def fetch_url(url, timeout=REQUEST_TIMEOUT):
    """Egyetlen GET kérés egy URL-re. Visszaad egy dict-et:
    {"ok": bool, "url":, "status_code":, "html":, "error":}.

    Nincs újrapróbálkozás, nincs fejléc-trükközés, nincs CAPTCHA-kezelés -
    ha az oldal blokkolja a kérést, azt egyszerűen jelentjük, nem
    próbáljuk megkerülni."""
    parsed = urlparse(url)
    if parsed.scheme not in ALLOWED_SCHEMES:
        return {"ok": False, "url": url, "status_code": None, "html": None, "error": "invalid_scheme"}
    if not parsed.netloc:
        return {"ok": False, "url": url, "status_code": None, "html": None, "error": "invalid_url"}
    if not _is_safe_host(parsed.hostname):
        return {"ok": False, "url": url, "status_code": None, "html": None, "error": "blocked_host"}

    request = urllib.request.Request(
        url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"}
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status = response.status
            content_type = (response.headers.get("Content-Type") or "").lower()
            if "text/html" not in content_type and "text/plain" not in content_type:
                return {"ok": False, "url": url, "status_code": status, "html": None,
                        "error": "unsupported_content_type"}
            raw = response.read(MAX_CONTENT_BYTES + 1)
            truncated = len(raw) > MAX_CONTENT_BYTES
            if truncated:
                raw = raw[:MAX_CONTENT_BYTES]
            charset = response.headers.get_content_charset() or "utf-8"
            try:
                html = raw.decode(charset, errors="replace")
            except LookupError:
                html = raw.decode("utf-8", errors="replace")
            return {"ok": True, "url": url, "status_code": status, "html": html, "error": None}
    except urllib.error.HTTPError as exc:
        if exc.code in BLOCKED_STATUS_CODES:
            return {"ok": False, "url": url, "status_code": exc.code, "html": None, "error": "access_blocked"}
        return {"ok": False, "url": url, "status_code": exc.code, "html": None,
                "error": f"http_error_{exc.code}"}
    except (urllib.error.URLError, socket.timeout, TimeoutError, OSError):
        return {"ok": False, "url": url, "status_code": None, "html": None, "error": "network_error"}
    except Exception:
        # Bármilyen más, előre nem látott hiba (pl. fejléc-kódolási hiba)
        # se szakítsa meg a hívó folyamatot - egyszerűen "nem olvasható".
        return {"ok": False, "url": url, "status_code": None, "html": None, "error": "unknown_error"}


def summarize_source(url, timeout=REQUEST_TIMEOUT):
    """Letölt egy URL-t, kinyeri a tiszta szöveget, és egy rövid forrás-
    összefoglalót ad vissza: {"url","ok","title","domain","excerpt",
    "content_length"} (hiba esetén {"url","ok":False,"error",...})."""
    fetched = fetch_url(url, timeout=timeout)
    if not fetched["ok"]:
        return {"url": url, "ok": False, "error": fetched["error"], "status_code": fetched.get("status_code")}

    parser = _TextExtractor()
    try:
        parser.feed(fetched["html"])
    except Exception:
        return {"url": url, "ok": False, "error": "parse_error", "status_code": fetched.get("status_code")}

    text = parser.text
    if not text:
        return {"url": url, "ok": False, "error": "no_readable_text", "status_code": fetched.get("status_code")}

    domain = urlparse(url).netloc
    title = parser.title or domain
    return {
        "url": url,
        "ok": True,
        "title": _trim(title, 120),
        "domain": domain,
        "excerpt": _trim(text, EXCERPT_CHARS),
        "content_length": len(text),
    }


def research_urls(urls, limit=DEFAULT_SOURCES):
    """Legfeljebb `limit` (max MAX_SOURCES) URL-t dolgoz fel. Visszaad egy
    (sources, errors) párt: sources a sikeresen feldolgozott források
    listája, errors a sikertelenekről szóló {"url","reason"} bejegyzések."""
    limit = max(0, min(limit, MAX_SOURCES))
    unique_urls = []
    for url in urls:
        if url not in unique_urls:
            unique_urls.append(url)
    unique_urls = unique_urls[:limit]

    sources, errors = [], []
    for url in unique_urls:
        result = summarize_source(url)
        if result["ok"]:
            sources.append(result)
        else:
            errors.append({"url": url, "reason": result["error"]})
    return sources, errors


# ---------------------------------------------------------------------------
# Prompt-kontextus + forráslista + (jóváhagyás előtti) tudás-jelöltek
# ---------------------------------------------------------------------------


def build_web_prompt_context(sources):
    """Rövid, natív "User:/AI:\\n\\n" formátumú prompt-kontextus a
    válaszgeneráláshoz - ugyanaz az elv, mint a memória/tudásbázis
    modulokban: rövid, ismerős szerkezetű, nem nyers szövegdömping."""
    if not sources:
        return ""
    facts = [_trim(s["excerpt"], MAX_PROMPT_EXCERPT_CHARS) for s in sources[:MAX_SOURCES]]
    facts = [f for f in facts if f]
    if not facts:
        return ""
    joined = _trim("; ".join(facts), MAX_CONTEXT_CHARS)
    return f"User: Mit találtál erről a weboldalon?\nAI: Ezt találtam: {joined}.\n\n"


def format_source_citations(sources):
    """Emberi olvasásra szánt forráslista-szöveg, amit a válaszhoz lehet
    csatolni - "adjon forráslistát a válaszhoz" követelmény."""
    if not sources:
        return ""
    lines = [f"{s['title']} ({s['domain']})" for s in sources[:MAX_SOURCES]]
    return "; ".join(lines)


def to_knowledge_candidates(sources):
    """A talált forrásokból knowledge_base-formátumú JELÖLTEKET épít -
    ezeket a hívó fél MUTATHATJA a usernek, de NEM menti automatikusan. A
    tényleges mentés csak explicit jóváhagyással, egy KÜLÖN
    knowledge_base.save_knowledge() hívással történhet."""
    candidates = []
    for s in sources:
        candidates.append({
            "title": s["title"],
            "content": s["excerpt"],
            "category": "technical",
            "tags": [s["domain"]],
            "source": s["url"],
        })
    return candidates
