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

from conversation_manager import resolve_conversation_context
from evaluator import evaluate_reply
from file_reader import build_file_prompt_context
from input_normalizer import normalize_input
from response_planner import build_response_plan, build_response_plan_prompt_context
from response_style import apply_style
from knowledge_base import (
    build_knowledge_prompt_context,
    retrieve_relevant as retrieve_relevant_knowledge,
)
from long_term_memory import (
    CATEGORY_LABELS as MEMORY_CATEGORY_LABELS,
    build_long_memory_prompt_context,
    detect_explicit_save,
    detect_memory_candidate,
    retrieve_relevant as retrieve_relevant_memories,
    save_memory,
)
from memory import resolve_memory_context
from router import route_and_respond
from web_research import (
    build_web_prompt_context,
    detect_urls,
    format_source_citations,
    research_urls,
)
from web_search import detect_search_query, search_and_research

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
    long_memory_enabled=True, long_memory_store_path=None,
    knowledge_enabled=True, knowledge_store_path=None,
    web_enabled=True, web_search_enabled=True,
    conversation_state=None, conversation_manager_enabled=True,
    style_enabled=True, response_planner_enabled=True,
    input_normalizer_enabled=True,
    active_file=None, file_context_enabled=True,
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
      long_memory_candidate          - a v1.0 hosszú távú memória heurisztikája
                              szerint EZ AZ ÜZENET érdemes lenne megjegyzésre
                              (CSAK jelzés - önmagában semmit nem ment)
      long_memory_candidate_category - a fenti jelzéshez tartozó becsült
                              kategória, vagy None
      long_memory_saved              - történt-e TÉNYLEGES mentés ebben a
                              körben (csak explicit "jegyezd meg..." kérésre)
      long_memory_saved_id           - az újonnan mentett memória id-ja, vagy None
      long_memory_retrieved_ids      - a válaszadáshoz felhasznált, releváns
                              hosszú távú memóriák id-jai (legfeljebb 5)
      long_memory_retrieved_count    - a fenti lista hossza
      knowledge_used          - használt-e a v1.1 saját tudásbázis (volt-e
                              releváns, aktív találat)
      knowledge_items          - a felhasznált tudáselemek id-jai (legfeljebb 3)
      knowledge_query          - a kereséshez használt szöveg (a user_message)
      web_used                 - történt-e sikeres v1.2 webkutatás (volt-e a
                              user üzenetében legalább 1 sikeresen olvasható URL)
      web_sources               - a felhasznált források listája (legfeljebb 5),
                              [{"url","title","domain"}, ...]
      web_detected_urls        - a user üzenetében TALÁLT URL-ek (akkor is, ha
                              az olvasásuk sikertelen volt)
      web_errors                - sikertelen olvasási kísérletek [{"url","reason"}]
      web_search_used            - a v1.2.1 lekérdezés-alapú keresés
                              ténylegesen felhasznált-e tartalmat a válaszhoz
      web_search_query            - a felismert keresési lekérdezés (vagy None,
                              ha nem volt keresési kérés a user üzenetében)
      web_search_provider         - melyik provider szolgáltatta a találatokat
                              ("none"/"duckduckgo"/"bing"), vagy None
      web_search_results_count    - hány nyers találatot adott a provider
      web_search_error            - miért nem sikerült (pl.
                              "no_provider_configured", "no_results_found",
                              "no_readable_sources", "provider_error"), vagy None
      conversation_state_used     - használta-e a promptban a v1.3
                              beszélgetés-állapot összefoglalóját (csak
                              explicit visszautalásnál, lásd
                              conversation_manager.detect_context_need)
      active_topic                 - a state aktuális active_topic mezője
      current_goal                  - a state aktuális current_goal mezője
      conversation_summary          - a ténylegesen felhasznált összefoglaló
                              (None, ha conversation_state_used=False)
      style_used                    - a v1.4 stílus-réteg ténylegesen
                              módosította-e a végső választ (formai
                              javítás és/vagy lezáró mondat hozzáadása)
      response_quality_score        - szabályalapú minőségi pontszám (0-100)
                              az EREDETI (stílus-javítás előtti) válaszon
      final_response_length         - a végleges (stílus után is) válasz
                              karakterhossza
      response_plan_used            - épült-e és lett-e felhasználva
                              v1.4.1 választerv (mindig True, ha
                              response_planner_enabled és general_chat
                              intent - a terv mindig készül, csak a
                              formázó hatása függ a típustól)
      response_type                 - a felismert válasz-típus (lásd
                              response_planner.RESPONSE_TYPES)
      target_length                  - "short"/"medium"/"long"
      wants_steps                    - kért-e lépésekre bontást
      wants_list                     - kért-e listaformázást
      input_normalizer_used          - történt-e ténylegesen elírás-javítás
                              (lásd input_normalizer.py)
      original_text                   - a user EREDETI, változatlan szövege
      normalized_text                  - a (esetlegesen) javított szöveg -
                              EZ megy tovább a router/guard/memory/web/
                              conversation_manager feldolgozásba
      detected_typos                   - a ténylegesen javított szavak listája
                              [{"original","corrected","confidence"}, ...]
      normalization_confidence          - a leggyengébb alkalmazott javítás
                              megbízhatósága (1.0, ha nem történt csere)
      file_used                          - történt-e ténylegesen feltöltött
                              fájl-kontextus felhasználás (lásd file_reader.py)
      file_name                          - az aktív fájl neve (vagy None)
      file_type                          - az aktív fájl kiterjesztése (vagy None)
      file_size                          - az aktív fájl mérete bájtban (vagy None)
      file_summary_used                  - a felhasznált fájl-összefoglaló
                              szövege (vagy None)
    """
    # --- v1.4.2 user input normalizer: MINDEN intentnél lefut, a router
    # ELŐTT - egy szigorúan óvatos, whitelist-alapú elírás/szleng-javítás
    # (lásd input_normalizer.py). Az EREDETI szöveg megmarad naplózásra,
    # a további feldolgozás (router/guard/memory/web/conversation) a
    # normalizált szöveggel dolgozik, ha van mit javítani.
    original_user_message = user_message
    normalization = normalize_input(user_message)
    input_normalizer_used = input_normalizer_enabled and bool(normalization["detected_typos"])
    if input_normalizer_used:
        user_message = normalization["normalized_text"]

    reply, intent, model_used, sentence_info = route_and_respond(
        general_model, instruction_model, user_message, temperature, sentence_target
    )

    guard_info = {
        "input_normalizer_used": input_normalizer_used,
        "original_text": original_user_message,
        "normalized_text": user_message,
        "detected_typos": normalization["detected_typos"] if input_normalizer_enabled else [],
        "normalization_confidence": normalization["normalization_confidence"] if input_normalizer_enabled else 1.0,
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
        "long_memory_candidate": False,
        "long_memory_candidate_category": None,
        "long_memory_saved": False,
        "long_memory_saved_id": None,
        "long_memory_retrieved_ids": [],
        "long_memory_retrieved_count": 0,
        "knowledge_used": False,
        "knowledge_items": [],
        "knowledge_query": None,
        "web_used": False,
        "web_sources": [],
        "web_detected_urls": [],
        "web_errors": [],
        "web_search_used": False,
        "web_search_query": None,
        "web_search_provider": None,
        "web_search_results_count": 0,
        "web_search_error": None,
        "conversation_state_used": False,
        "active_topic": None,
        "current_goal": None,
        "conversation_summary": None,
        "style_used": False,
        "response_quality_score": None,
        "final_response_length": None,
        "response_plan_used": False,
        "response_type": None,
        "target_length": None,
        "wants_steps": False,
        "wants_list": False,
        "file_used": False,
        "file_name": None,
        "file_type": None,
        "file_size": None,
        "file_summary_used": None,
    }

    if intent != "general_chat":
        return reply, intent, model_used, sentence_info, guard_info

    from chat import respond as chat_respond

    model, stoi, itos, device, prompt_format = general_model

    # --- v1.0 hosszú távú memória, 1. lépés: heurisztikus jelzés (mindig
    # lefut, naplózási célra), majd EXPLICIT mentési kérés ellenőrzése -
    # ez az EGYETLEN útvonal, ami ténylegesen ír a store-ba. Ha ez talál
    # egyezést, a válasz egy determinisztikus visszaigazolás - a modellt
    # meg sem hívjuk, mert egy "jegyezd meg..." meta-kérésre a kis LSTM
    # sosem lett tanítva, a válasza megbízhatatlan lenne.
    if long_memory_enabled:
        is_candidate, candidate_category = detect_memory_candidate(user_message)
        guard_info["long_memory_candidate"] = is_candidate
        guard_info["long_memory_candidate_category"] = candidate_category

        should_save, extracted_text = detect_explicit_save(user_message)
        if should_save:
            _, guessed_category = detect_memory_candidate(extracted_text)
            save_category = candidate_category or guessed_category or "user_fact"
            saved = save_memory(
                save_category, extracted_text, confidence=1.0, source="explicit",
                store_path=long_memory_store_path,
            )
            if saved:
                guard_info["long_memory_saved"] = True
                guard_info["long_memory_saved_id"] = saved["id"]
                guard_info["expected_answer_type"] = "memory_save"
                label = MEMORY_CATEGORY_LABELS.get(saved["category"], saved["category"])
                reply = f"Megjegyeztem ({label}): \"{saved['text']}\"."
                return reply, intent, model_used, sentence_info, guard_info

    # --- v1.0 hosszú távú memória, 2. lépés: legfeljebb 5 RELEVÁNS,
    # aktív memória visszakeresése (ha nincs találat, ez a blokk nem
    # változtat semmin - üres store esetén garantáltan inaktív). ---
    long_prompt_context = ""
    if long_memory_enabled:
        relevant = retrieve_relevant_memories(user_message, limit=5, store_path=long_memory_store_path)
        if relevant:
            guard_info["long_memory_retrieved_ids"] = [m["id"] for m in relevant]
            guard_info["long_memory_retrieved_count"] = len(relevant)
            long_prompt_context = build_long_memory_prompt_context(relevant)

    # --- v1.1 saját tudásbázis: legfeljebb 3 RELEVÁNS, aktív tudáselem
    # visszakeresése (ha nincs találat, ez a blokk nem változtat semmin -
    # üres knowledge_base esetén garantáltan inaktív). Ez a modul SOSEM ír
    # a chat mellékhatásaként - kizárólag olvas (lásd knowledge_base.py). ---
    knowledge_prompt_context = ""
    if knowledge_enabled:
        guard_info["knowledge_query"] = user_message
        relevant_knowledge = retrieve_relevant_knowledge(
            user_message, limit=3, store_path=knowledge_store_path
        )
        if relevant_knowledge:
            guard_info["knowledge_used"] = True
            guard_info["knowledge_items"] = [item["id"] for item in relevant_knowledge]
            knowledge_prompt_context = build_knowledge_prompt_context(relevant_knowledge)

    # --- v1.2.1 webes keresés: CSAK akkor lép életbe, ha a user üzenete
    # kifejezetten keresésre kér ("keress rá...", "nézz utána...",
    # "googlezd meg..." - lásd web_search.detect_search_query). Ha nincs
    # provider konfigurálva vagy nincs (olvasható) találat, egy rövid,
    # DETERMINISZTIKUS státuszüzenetet ad vissza - a modellt meg sem
    # hívjuk, mert erre a meta-kérésre sosem lett tanítva. Ha SIKERÜL,
    # ugyanaz a prompt-kontextus/forráslista mechanizmus fut, mint a
    # sima URL-olvasásnál (lásd lejjebb).
    web_prompt_context = ""
    web_sources = []
    search_triggered = False
    if web_search_enabled:
        should_search, search_query = detect_search_query(user_message)
        if should_search:
            search_triggered = True
            guard_info["web_search_query"] = search_query
            result = search_and_research(search_query, search_limit=5, read_limit=3)
            guard_info["web_search_provider"] = result.get("provider")
            guard_info["web_search_results_count"] = len(result.get("search_results") or [])

            if not result["ok"]:
                guard_info["web_search_error"] = result["error"]
                guard_info["expected_answer_type"] = "web_search_status"
                if result["error"] == "no_provider_configured":
                    status_reply = ("A webes keresés jelenleg nincs konfigurálva (nincs beállítva "
                                     "WEB_SEARCH_PROVIDER) - adj meg egy konkrét URL-t, azt el tudom olvasni.")
                elif result["error"] == "no_results_found":
                    status_reply = f"Nem találtam publikus találatot erre: \"{search_query}\"."
                elif result["error"] == "no_readable_sources":
                    status_reply = f"Találtam találatot erre: \"{search_query}\", de egyiket sem tudtam elolvasni."
                else:
                    status_reply = "A webes keresés most nem sikerült."
                return status_reply, intent, model_used, sentence_info, guard_info

            web_sources = result["sources"]
            guard_info["web_used"] = True
            guard_info["web_sources"] = [
                {"url": s["url"], "title": s["title"], "domain": s["domain"]} for s in web_sources
            ]
            guard_info["web_detected_urls"] = [s["url"] for s in web_sources]
            guard_info["web_errors"] = result.get("errors") or []
            guard_info["web_search_used"] = True
            web_prompt_context = build_web_prompt_context(web_sources)

    # --- v1.2 webkutatás: CSAK akkor lép életbe, ha a user üzenete
    # kifejezetten tartalmaz http(s):// URL-t (explicit jel), ÉS nem volt
    # már sikeres keresési kör fentebb. Legfeljebb 5 forrást olvas,
    # mindegyikről rövid kivonatot készít - ha egyik sem olvasható, ez a
    # blokk nem változtat semmin. ---
    if web_enabled and not search_triggered:
        detected_urls = detect_urls(user_message)
        if detected_urls:
            guard_info["web_detected_urls"] = detected_urls
            web_sources, web_errors = research_urls(detected_urls, limit=5)
            guard_info["web_errors"] = web_errors
            if web_sources:
                guard_info["web_used"] = True
                guard_info["web_sources"] = [
                    {"url": s["url"], "title": s["title"], "domain": s["domain"]} for s in web_sources
                ]
                web_prompt_context = build_web_prompt_context(web_sources)

    # --- v1.6 feltöltött fájl kontextus: CSAK akkor, ha a hívó fél
    # (web/app.py/chat.py) egy KONKRÉT, MÁR feltöltött fájlt jelölt meg
    # aktívnak (active_file) - ez a modul soha nem böngészi/választja ki
    # magától a fájlt. Rövid kivonat kerül a promptba, a teljes tartalom
    # NEM (lásd file_reader.build_file_prompt_context()). ---
    file_prompt_context = ""
    if file_context_enabled and active_file:
        guard_info["file_used"] = True
        guard_info["file_name"] = active_file.get("name")
        guard_info["file_type"] = active_file.get("type")
        guard_info["file_size"] = active_file.get("size")
        guard_info["file_summary_used"] = active_file.get("summary")
        file_prompt_context = build_file_prompt_context(active_file)

    # --- v0.9 rövid memória: csak akkor avatkozik be, ha a user
    # egyértelműen visszautal egy korábbi váltásra (lásd memory.py) - ha
    # nem, prompt_context üres marad, és a válasz pontosan ugyanaz, mint
    # memória nélkül.
    memory_info, short_prompt_context = resolve_memory_context(user_message, history, enabled=memory_enabled)
    guard_info.update(memory_info)

    # --- v1.3 beszélgetés-állapot: CSAK akkor kerül a promptba, ha a user
    # kifejezetten igényli (lásd conversation_manager.detect_context_need)
    # - "folytasd", "az előző", "ezt javítsd", "amit mondtam", "akkor a
    # másik", vagy egy rövid névmásos utalás. A state-et a HÍVÓ FÉL
    # (chat.py/web/app.py) tartja életben és frissíti - a guard.py csak
    # OLVASSA. ---
    conversation_info, conversation_prompt_context, _needed_context = resolve_conversation_context(
        user_message, conversation_state, enabled=conversation_manager_enabled
    )
    guard_info.update(conversation_info)

    # --- v1.4.1 választervező: ELŐRE eldönti, milyen TÍPUSÚ választ vár a
    # kérdés (rövid/magyarázat/lépésenkénti/lista/összegzés/kód-segítség/
    # döntés-segítség/laza beszélgetés) - ez az INFORMÁCIÓ (nem tartalom!)
    # egy gyenge prompt-nudge-ként az utolsó kontextus-blokk, ÉS a
    # response_style.py-nak adott instrukció (lásd _finalize), ami a
    # MEGLÉVŐ válasz FORMÁJÁT (lépés-/lista-tördelés, hossz-elvárás)
    # igazítja hozzá - tényt nem ír át.
    response_plan = None
    response_plan_prompt_context = ""
    if response_planner_enabled:
        response_plan = build_response_plan(user_message)
        guard_info["response_plan_used"] = True
        guard_info["response_type"] = response_plan["response_type"]
        guard_info["target_length"] = response_plan["target_length"]
        guard_info["wants_steps"] = response_plan["wants_steps"]
        guard_info["wants_list"] = response_plan["wants_list"]
        response_plan_prompt_context = build_response_plan_prompt_context(response_plan)

    # A tudásbázis, a webkutatás, a feltöltött fájl, a hosszú memória, a
    # rövid memória, a beszélgetés-állapot és a választerv mind KÜLÖN
    # mechanizmus marad (külön mezők, külön kapcsoló) - a promptban a
    # kért, kontrollált sorrendben illesztjük őket: tudásbázis -> webes
    # forrás -> feltöltött fájl -> hosszú távú tények -> legutolsó váltás
    # -> beszélgetés-összefoglaló -> választerv (a kérdéshez legközelebb).
    prompt_context = (
        knowledge_prompt_context + web_prompt_context + file_prompt_context + long_prompt_context
        + short_prompt_context + conversation_prompt_context + response_plan_prompt_context
    )

    def _finalize(final_reply):
        """v1.4: determinisztikus stílus-utófeldolgozás (írásjel/nagybetű-
        javítás, ismétlés-eltávolítás, túl rövid válasz puhítása - lásd
        response_style.py) a TARTALMI válaszon, majd a webes forráslista
        csatolása a VÉGÉHEZ (nem a stílus-rétegen megy át, ez strukturált
        hivatkozás, nem beszélgetős szöveg) - "adjon forráslistát a
        válaszhoz" követelmény. A v1.4.1 választervet (ha volt) is itt
        adjuk át - a stílus-réteg ez alapján tördeli lépésekre/listára
        vagy vágja rövidebbre a MÁR MEGLÉVŐ mondatokat (lásd
        response_style.apply_structure())."""
        styled_reply, style_info = apply_style(final_reply, enabled=style_enabled, plan=response_plan)
        guard_info.update(style_info)
        if guard_info["web_used"] and web_sources:
            citations = format_source_citations(web_sources)
            if citations:
                return f"{styled_reply}\n\nForrások: {citations}"
        return styled_reply

    if prompt_context:
        reply = chat_respond(
            model, stoi, itos, device, user_message, temperature,
            sentence_target=sentence_target, prompt_format=prompt_format,
            context_prefix=prompt_context,
        )

    category = detect_category(user_message)
    guard_info["expected_answer_type"] = category or "general"
    if category is None:
        return _finalize(reply), intent, model_used, sentence_info, guard_info

    _, flags = evaluate_reply(user_message, reply, intent, sentence_info)
    on_topic = is_on_topic(category, reply)
    bleed = looks_like_identity_bleed(category, reply)

    if on_topic and not bleed and not flags:
        return _finalize(reply), intent, model_used, sentence_info, guard_info

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
        return _finalize(retry_reply), intent, model_used, sentence_info, guard_info

    # --- retry is elfogadhatatlan: kontrollált fallback ---
    guard_info["fallback_used"] = True
    guard_info["failure_reason"] = _failure_reason(retry_on_topic, retry_bleed, retry_flags)
    fallback_reply = pick_fallback(category)
    guard_info["corrected_answer"] = fallback_reply
    return _finalize(fallback_reply), intent, model_used, sentence_info, guard_info
