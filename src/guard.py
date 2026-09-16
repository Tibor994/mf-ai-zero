"""
MF-AI-Zero - v0.9-guard: intent-alapú tartalmi őr (guard) + kontrollált
fallback réteg az általános chat (general_chat) válaszokra.

Miért kell ez?

A v0.8b/v0.8c kísérletek (lásd tests/diagnose_v08b_a_results.json,
tests/diagnose_v08c_c_results.json) bebizonyították, hogy ÚJRATANÍTÁSSAL
(új adat hozzáadásával, akár minimális, 1x súlyú, pár százalékos
mennyiségben is) NEM lehet megbízhatóan stabilizálni ezt a kis
karakter-alapú LSTM-et: egy-egy témán javítva más, korábban jó kérdés
romlik el ("whack-a-mole" - candidate A javította a 4 célkérdést, de
elrontotta "Hány éves vagy?"-ot; candidate C, ami még több témát próbált
egyszerre javítani, összességében MINDEN modellnél rosszabb lett).

Ez a modul ezért NEM tanítással, hanem egy a modell FÖLÉ épített,
szabályalapú biztonsági réteggel próbálja csökkenteni a leggyakoribb,
azonosított hibát: az "identitás/bemutatkozás-attraktor" jelenséget,
amikor a modell egy oda nem illő kérdésre (pl. "Hány éves vagy?") a
megtanult "Szia! Én az MF-AI-Zero vagyok..." bemutatkozó válasszal felel.

Működés (csak general_chat intentnél lép életbe):
  1. detect_category(): a user szövegét egy 7 KATEGÓRIA egyikébe sorolja
     (identity, age, smalltalk, memory, preference, capability,
     explanation) - NEM fix kérdés->válasz lista, hanem kulcsszó-mintázat
     alapú, ezért a kérdés megfogalmazásának (elütés, rövidítés, haveri
     stílus) variációira is működik.
  2. A modell (a router.route_and_respond() útján) megadja a szokásos
     válaszát.
  3. is_on_topic() + looks_like_identity_bleed() + evaluator.evaluate_reply()
     eldönti, hogy a válasz elfogadható-e a kategóriához képest.
  4. Ha NEM elfogadható: EGY retry (a modell újragenerál, ugyanazzal a
     promptal, más mintavétellel).
  5. Ha a retry is elfogadhatatlan: KONTROLLÁLT fallback - egy előre
     megírt, természetes, a kategóriának megfelelő válasz (NEM
     bemutatkozás), amit a kategória alapján választunk, nem a konkrét
     kérdésszöveg alapján.

FONTOS: ez a modul NEM módosítja a router.py-t és NEM tanít semmit - csak
egy opcionális, a route_and_respond() KIMENETÉRE épülő ellenőrző/javító
réteg, amit a hívó fél (chat.py, tesztek) választhat.
"""

import random
import re
import unicodedata

from evaluator import evaluate_reply
from memory import resolve_memory_context
from router import route_and_respond

# ---------------------------------------------------------------------------
# Ékezet-független, kisbetűs normalizálás - hogy az elütéses / ékezet
# nélküli kérdésváltozatok (pl. "hany eves vagy", "miert van hogy furan
# valaszolsz") is felismerésre kerüljenek.
# ---------------------------------------------------------------------------


def _normalize(text):
    text = (text or "").lower()
    decomposed = unicodedata.normalize("NFKD", text)
    without_accents = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", without_accents).strip()


# ---------------------------------------------------------------------------
# Kategóriák: felismerő mintázatok (ékezet nélküli, kisbetűs részszöveg-
# egyezés a normalizált user szövegben) - EZ NEM fix kérdés-lista, hanem
# minden kategóriához több, jellemző fordulat, hogy a variációk (rövid,
# elütéses, haveri, hosszabb, szinonim megfogalmazás) is felismerhetők
# legyenek.
# ---------------------------------------------------------------------------
CATEGORY_PATTERNS = {
    "identity": [
        "ki vagy", "mi vagy", "kicsoda vagy", "bemutatkoz",
    ],
    "age": [
        "hany eves", "mennyi idos", "eletkorod", "hany eve letezel",
        "mikor szulettel", "milyen regi vagy", "miota letezel", "oreg vagy",
    ],
    "memory": [
        "emlekszel", "emlekezeted", "van memoriad", "elmentetted",
        "meg tudod jegyezni", "hosszu tavu memoria",
    ],
    "preference": [
        "kedvenc film", "kedvenc mozid", "szoktal filmet nezni",
        "milyen filmeket szeretsz", "film amit imadsz", "szereted a filmeket",
        "mit szoktal nezni",
    ],
    "capability": [
        "tudsz verset", "irnal nekem egy verset", "megy a verseles",
        "kolto is vagy", "tudsz rimelni", "irj egy rovid verset",
        "erzeked a kolteszethez", "irni egy verset", "szoktal verset irni",
    ],
    "explanation": [
        "miert valaszolsz", "miert furcsak", "miert van hogy furan",
        "felreertelek", "fura dolgokat mondasz", "miert hibazol",
        "nem mindig erthetoek", "csuszik el neha", "kulonbseg kozted",
        "miben kulonbozol", "olyan vagy mint a chatgpt",
        "mennyivel vagy gyengebb", "miert nem vagy olyan okos",
        "mi kulonboztet meg", "hasonlitasz egy nagy ai", "miben mas vagy",
    ],
    "smalltalk": [
        "hogy vagy", "hogy s mint", "hogy erzed magad", "mizu",
        "mi ujsag", "mi a helyzet", "hogy telik a napod", "jol vagy",
        "minden rendben van veled", "mi van veled mostanaban",
        "erdekes ujdonsag", "mesel valami erdekes",
    ],
}

# Ellenőrzési sorrend - az elsőnek talált kategória dönt. Az "identity" áll
# elöl, mert néhány mintázata ("mi vagy") rövidebb/általánosabb, mint pl. a
# "smalltalk" fordulatai.
CATEGORY_ORDER = [
    "identity", "age", "memory", "preference", "capability",
    "explanation", "smalltalk",
]


def detect_category(user_text):
    """Visszaadja a user szöveg guard-kategóriáját (a fenti 7 közül), vagy
    None-t, ha egyik mintázat sem illik rá - ez utóbbi esetben a guard NEM
    avatkozik be (a válasz változatlanul megy tovább)."""
    normalized = _normalize(user_text)
    if not normalized:
        return None
    for category in CATEGORY_ORDER:
        for pattern in CATEGORY_PATTERNS[category]:
            if pattern in normalized:
                return category
    return None


# ---------------------------------------------------------------------------
# Kategóriánkénti elvárt kulcsszavak - UGYANAZOK a kulcsszavak, amiket a
# golden_chat_tests.json a kapcsolódó kérdéseknél elvár (lásd
# tests/golden_chat_tests.json, g01/g05/g09/g10/g11/g12/g14/g15/g17), hogy a
# guard "elfogadható-e a válasz" döntése összhangban legyen azzal, amit a
# hivatalos teszt is elfogad.
# ---------------------------------------------------------------------------
CATEGORY_KEYWORDS = {
    "identity": ["mf-ai-zero", "ai vagyok", "program vagyok", "gép vagyok"],
    "age": ["életkor", "program vagyok", "nincs"],
    "memory": ["emlék", "memór"],
    "preference": ["film", "nem néztem", "nincs kedvenc"],
    "capability": ["verset", "tanulom", "nem tudok"],
    "explanation": [
        "tanuló modell", "furán", "karakterenként", "hibázik", "kicsi",
        "különbség", "nagy",
    ],
    "smalltalk": ["programnak", "hangulat", "készen áll", "újdonság", "élek", "beszélgetünk"],
}

# Az "identitás-attraktor" hiba felismerésére: ha egy NEM identity
# kategóriájú kérdésre a válasz ezekre a jellegzetes bemutatkozó
# fordulatokra hasonlít, az valószínűleg téves (más kategóriába tartozó
# kérdésre adott, betanult "alapértelmezett" válasz).
IDENTITY_SIGNATURE = ["mf-ai-zero", "nulláról tanított", "saját, nulláról"]


def is_on_topic(category, reply):
    """Igaz, ha a válasz tartalmazza a kategóriához elvárt kulcsszavak
    egyikét (ugyanaz a logika, mint a golden teszteknél)."""
    reply_low = (reply or "").lower()
    keywords = CATEGORY_KEYWORDS.get(category, [])
    return any(kw in reply_low for kw in keywords)


def looks_like_identity_bleed(category, reply):
    """Igaz, ha egy NEM identity kategóriájú kérdésre a válasz mégis a
    bemutatkozó/identitás mintázatot adja vissza - ez a projekt eddigi
    diagnózisai szerint a leggyakoribb, konkrét hibatípus."""
    if category == "identity":
        return False
    reply_low = (reply or "").lower()
    return any(sig in reply_low for sig in IDENTITY_SIGNATURE)


# ---------------------------------------------------------------------------
# Kontrollált fallback válaszok kategóriánként - természetes, rövid-közepes
# magyar mondatok, NEM bemutatkozás-stílusúak (kivéve az identity
# kategóriát, ahol pont ez az elvárt válasz). Ezek a v0.8b/v0.8c köralatt
# már bevált (kulcsszó-egyezést garantáltan teljesítő) válaszok.
# ---------------------------------------------------------------------------
CATEGORY_FALLBACKS = {
    "identity": [
        "Szia! Én az MF-AI-Zero vagyok, egy saját, nulláról tanított magyar AI prototípus.",
    ],
    "age": [
        "Nincs igazi életkorom, hiszen egy program vagyok, nem egy élőlény.",
        "Program vagyok, szóval nincs életkorom a szó hagyományos értelmében.",
        "Az életkor emberi fogalom, nekem nincs ilyenem, csak egy tanítási dátumom.",
    ],
    "memory": [
        "Nincs hosszú távú emlékezetem, csak az aktuális beszélgetés alatt emlékszem arra, amit írtál.",
        "Van egyfajta memóriám, de csak addig tart, amíg tart ez a beszélgetés.",
        "Az emlékezetem nagyon korlátozott - csak eddig a beszélgetésig emlékszem vissza.",
    ],
    "preference": [
        "Nincs kedvenc filmem, hiszen nem néztem filmeket - csak magyar szövegen tanultam.",
        "Nem szoktam filmet nézni, mert nincs ilyen képességem - csak szöveget értek.",
        "Sosem néztem filmet, szóval nem tudok választani egy kedvencet.",
    ],
    "capability": [
        "Igazi verset még nem tudok jól írni, de tanulom - egyelőre inkább rövid, motiváló mondatokban vagyok erős.",
        "Nem vagyok költő, verset még nem tanultam meg írni rendesen.",
        "Verset egyelőre nem tudok szépen írni, de szívesen próbálkoznék, ha tanítanának rá.",
    ],
    "explanation": [
        "Mert még egy kicsi, tanuló modell vagyok. Karakterenként generálom a szöveget, és néha rosszul jóslom meg a folytatást.",
        "Előfordul, hogy összekeverem a mintázatokat, mert kicsi vagyok ehhez a feladathoz.",
        "A fő különbség a méret: én egy nagyon kicsi modell vagyok, a nagy AI chatbotok ennél sokkal-sokkal nagyobbak és több adaton tanultak.",
    ],
    "smalltalk": [
        "Egy programnak nincs igazi hangulata, de készen állok beszélgetni! Te hogy vagy?",
        "Programnak lenni jó, mindig készen állok - és te hogy vagy?",
        "Nincs igazán újdonság nálam, hiszen nem élek a szó hagyományos értelmében - most is csak azért vagyok itt, mert beszélgetünk.",
    ],
}


def pick_fallback(category):
    options = CATEGORY_FALLBACKS.get(category)
    if not options:
        return "Erről egyelőre nem tudok ennél pontosabb választ adni."
    return random.choice(options)


def _failure_reason(on_topic, bleed, flags):
    reasons = []
    if bleed:
        reasons.append("identity_bleed")
    if not on_topic:
        reasons.append("category_mismatch")
    if flags:
        reasons.append("structural_flags:" + ",".join(flags))
    return "+".join(reasons) if reasons else None


def guarded_route_and_respond(
    general_model, instruction_model, user_message, temperature=0.6,
    sentence_target=None, history=None, memory_enabled=True,
):
    """Ugyanaz a visszatérési forma, mint a router.route_and_respond()-é,
    PLUSZ egy 5. elem: a guard_info dict (a learning_log bővítéséhez).

    history: opcionális, a v0.9 rövid memória bemenete - egy lista/deque
    (user_message, ai_reply) párokból, IDŐRENDBEN (a legutolsó befejezett
    váltás a végén). Csak akkor van hatása, ha a user üzenete egyértelműen
    visszautal egy korábbi váltásra (lásd memory.detect_followup) - minden
    más esetben a viselkedés PONTOSAN ugyanaz, mint memória nélkül.
    memory_enabled=False-szal (vagy history=None/üres) a memória réteg
    teljesen inaktív.

    guard_info mezői:
      detected_intent      - a router 5-way intentje (general_chat/...)
      expected_answer_type - a guard finomabb, 7 kategóriás besorolása
                              (identity/age/smalltalk/memory/preference/
                              capability/explanation), vagy "general", ha
                              egyik mintázat sem illik a szövegre
      guard_triggered       - avatkozott-e be a guard (az első válasz nem
                              volt elfogadható a kategóriához képest)
      retry_count           - hány újragenerálás történt (0 vagy 1)
      fallback_used          - a végleges válasz egy előre megírt fallback-e
      failure_reason         - miért nem volt elfogadható a válasz (vagy None)
      corrected_answer       - a guard által javított végső válasz, ha
                              különbözik az eredeti modell-választól
                              (egyébként None)
      used_for_training     - MINDIG False (jelölő mező: ezek a
                              korrekciók/fallbackek NEM automatikusan
                              tanítóadat-jelöltek, emberi átnézés nélkül)
      memory_used            - használt-e a v0.9 rövid memória
      memory_summary         - a naplózott, tömör (max 1-3 mondatos)
                              összefoglaló (üres, ha memory_used=False)
      memory_reason          - miért (nem) használtuk a memóriát: "disabled",
                              "no_backreference_detected",
                              "no_history_available",
                              "explicit_backreference" vagy
                              "short_deictic_followup"
    """
    reply, intent, model_used, sentence_info = route_and_respond(
        general_model, instruction_model, user_message, temperature, sentence_target
    )

    guard_info = {
        "detected_intent": intent,
        "expected_answer_type": "general",
        "guard_triggered": False,
        "retry_count": 0,
        "fallback_used": False,
        "failure_reason": None,
        "corrected_answer": None,
        "used_for_training": False,
        "memory_used": False,
        "memory_summary": "",
        "memory_reason": "not_applicable",
    }

    if intent != "general_chat":
        return reply, intent, model_used, sentence_info, guard_info

    from chat import respond as chat_respond

    model, stoi, itos, device, prompt_format = general_model

    # --- v0.9 rövid memória: csak akkor avatkozik be, ha a user
    # egyértelműen visszautal egy korábbi váltásra (lásd memory.py) - ha
    # nem, prompt_context üres marad, és a válasz pontosan ugyanaz, mint
    # memória nélkül.
    memory_info, prompt_context = resolve_memory_context(user_message, history, enabled=memory_enabled)
    guard_info.update(memory_info)

    if prompt_context:
        reply = chat_respond(
            model, stoi, itos, device, user_message, temperature,
            sentence_target=sentence_target, prompt_format=prompt_format,
            context_prefix=prompt_context,
        )

    category = detect_category(user_message)
    guard_info["expected_answer_type"] = category or "general"
    if category is None:
        return reply, intent, model_used, sentence_info, guard_info

    _, flags = evaluate_reply(user_message, reply, intent, sentence_info)
    on_topic = is_on_topic(category, reply)
    bleed = looks_like_identity_bleed(category, reply)

    if on_topic and not bleed and not flags:
        return reply, intent, model_used, sentence_info, guard_info

    # --- guard beavatkozik: 1x retry, ugyanazzal a modellel (a memória-
    # kontextust, ha volt, a retry is megkapja) ---
    guard_info["guard_triggered"] = True
    retry_reply = chat_respond(
        model, stoi, itos, device, user_message, temperature,
        sentence_target=sentence_target, prompt_format=prompt_format,
        context_prefix=prompt_context,
    )
    guard_info["retry_count"] = 1

    _, retry_flags = evaluate_reply(user_message, retry_reply, intent, None)
    retry_on_topic = is_on_topic(category, retry_reply)
    retry_bleed = looks_like_identity_bleed(category, retry_reply)

    if retry_on_topic and not retry_bleed and not retry_flags:
        guard_info["corrected_answer"] = retry_reply
        return retry_reply, intent, model_used, sentence_info, guard_info

    # --- retry is elfogadhatatlan: kontrollált fallback ---
    guard_info["fallback_used"] = True
    guard_info["failure_reason"] = _failure_reason(retry_on_topic, retry_bleed, retry_flags)
    fallback_reply = pick_fallback(category)
    guard_info["corrected_answer"] = fallback_reply
    return fallback_reply, intent, model_used, sentence_info, guard_info
