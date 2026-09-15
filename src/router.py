"""
MF-AI-Zero - v0.7e intent router.

Az eddigi kísérletek (v0.7c, v0.7d) megmutatták, hogy HA egyetlen modellt
próbálunk megtanítani mind az általános beszélgetésre, mind a pontos
mondatszámú válaszokra, az egyik rovására megy a másiknak - a modell
"összezavarodik" a kétféle válaszstílus között.

A v0.7e megoldása: NEM egy modellbe gyömöszölünk mindent, hanem egy
egyszerű, szabályalapú routert teszünk a modellek elé:
  - "általános" üzenetekhez (bemutatkozás, célok, köszönés, búcsú, stb.)
    mindig a v0.7 modell válaszol, mert abban ez a legjobb.
  - Explicit mondatszám-kéréshez ("Írj 5 mondatot...") a v0.7c modell
    válaszol (ami erre specializálódott: 20/20 pontos találat a saját
    tesztjén), a meglévő 8x-os újrapróbálkozással (lásd chat.respond()),
    plusz egy determinisztikus utófeldolgozással, ami GARANTÁLJA, hogy a
    végeredmény pontosan N mondatból álljon, még akkor is, ha a modell
    generálása 8 próbálkozás után sem talált el pontosan N-et.

Ez a modul NEM tanít semmit - csak a meglévő, már betanított v0.7 és
v0.7c checkpointokat routolja a bemenet szándéka (intent) alapján.
"""

import re

from chat import detect_sentence_count, respond
from generate import split_into_sentences

GOODBYE_KEYWORDS = ["viszlát", "viszontlátásra", "jó éjszakát", "pá"]
GREETING_KEYWORDS = ["szia", "helló", "hello", "jó napot", "üdv", "üdvözöllek"]

# Ha a determinisztikus kiegészítésnek nincs miből dolgoznia (a modell
# egyetlen mondatot sem adott vissza), ezzel töltjük fel a hiányzó részt.
FALLBACK_SENTENCE = "Erről egyelőre nem tudok ennél részletesebb választ adni."

INTENTS = ("command", "sentence_request", "goodbye", "greeting", "general_chat")


def _significant_words(text):
    """Írásjelek nélküli, kisbetűs szavak listája - a rövid köszönés/búcsú
    felismeréshez kell, hogy pl. a "Szia!" és a "Szia, ki vagy?" ne essen
    egy kategóriába (utóbbi valódi kérdést tartalmaz, tehát general_chat)."""
    cleaned = re.sub(r"[^\w\sáéíóöőúüű]", " ", text.lower())
    return [w for w in cleaned.split() if w]


def detect_intent(user_text):
    """Eldönti az üzenet szándékát. Öt lehetséges érték: "command",
    "sentence_request", "goodbye", "greeting", "general_chat".

    Sorrend (az első találat dönt):
      1. "/"-lal kezdődik -> command
      2. explicit mondatszám-kérés (detect_sentence_count) -> sentence_request
      3. rövid (max. 2 tartalmi szavas) búcsú-szó -> goodbye
      4. rövid (max. 2 tartalmi szavas) köszönés-szó -> greeting
      5. minden más -> general_chat
    """
    stripped = (user_text or "").strip()
    if not stripped:
        return "general_chat"

    if stripped.startswith("/"):
        return "command"

    if detect_sentence_count(stripped) is not None:
        return "sentence_request"

    words = _significant_words(stripped)
    if len(words) <= 2:
        joined = " ".join(words)
        if any(kw in joined for kw in GOODBYE_KEYWORDS):
            return "goodbye"
        if any(kw in joined for kw in GREETING_KEYWORDS):
            return "greeting"

    return "general_chat"


def enforce_sentence_count(sentences, n):
    """Determinisztikusan pontosan n mondatra vágja/egészíti ki a listát.
    Ez az UTOLSÓ biztonsági háló, miután a respond() belső, 8 próbálkozásos
    újragenerálása sem talált el pontosan n mondatot - itt már nem
    generálunk újra, csak vágunk (ha több van) vagy a meglévő mondatokat
    ismételjük (ha kevesebb van), hogy a végeredmény mindig pontosan n
    mondatból álljon."""
    sentences = list(sentences) or [FALLBACK_SENTENCE]
    if len(sentences) >= n:
        return sentences[:n]
    padded = list(sentences)
    i = 0
    while len(padded) < n:
        padded.append(sentences[i % len(sentences)])
        i += 1
    return padded


def route_and_respond(general_model, instruction_model, user_message, temperature=0.6, sentence_target=None):
    """Fő belépési pont: eldönti az intentet, majd a megfelelő modellel
    válaszol.

    general_model / instruction_model: (model, stoi, itos, device,
    prompt_format) 5-elemű tuple - előbbi a v0.7 (általános chat), utóbbi
    a v0.7c (mondatszám-kérések). command/greeting/goodbye/general_chat
    esetén mindig a general_model válaszol.

    sentence_target: csak a general_chat/greeting/goodbye/command úton
    számít (pl. a webes felület "Mondatok" legördülője) - a
    sentence_request útvonalon mindig a SZÖVEGBŐL felismert N szám dönt,
    ezt a paraméter nem írja felül (az explicit "Írj N mondatot" kérés
    mindig elsőbbséget élvez).

    Visszaadja: (reply, intent, model_used, sentence_info)
    sentence_info csak sentence_request esetén nem None:
      (kért_mondatszám, tényleges_mondatszám, történt-e determinisztikus_javítás)
    """
    intent = detect_intent(user_message)

    if intent == "sentence_request":
        model, stoi, itos, device, prompt_format = instruction_model
        requested_n = detect_sentence_count(user_message)

        reply = respond(
            model, stoi, itos, device, user_message, temperature,
            prompt_format=prompt_format,
        )
        sentences = split_into_sentences(reply)

        fixed = False
        if len(sentences) != requested_n:
            sentences = enforce_sentence_count(sentences, requested_n)
            reply = " ".join(sentences)
            fixed = True

        return reply, intent, "v0.7c", (requested_n, len(sentences), fixed)

    # command / greeting / goodbye / general_chat -> mindig a v0.7 (altalanos) modell.
    # (a tényleges "/exit" stb. parancs-végrehajtás a chat.py fő ciklusának
    # felelőssége, a router itt csak az intent-et állapítja meg helyesen -
    # ha idáig eljutunk parancs szöveggel, azt egyszerű szövegként válaszoljuk meg.)
    model, stoi, itos, device, prompt_format = general_model
    reply = respond(
        model, stoi, itos, device, user_message, temperature,
        sentence_target=sentence_target, prompt_format=prompt_format,
    )
    return reply, intent, "v0.7", None
