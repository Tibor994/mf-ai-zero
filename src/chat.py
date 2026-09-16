"""
MF-AI-Zero - beszélgetős (chat) mód.

Ez a szkript a betanított modell KÖRÉ épít egy egyszerű terminálos chat
felületet. A v0.7-től kezdve alapból egy "chat" formátumra (User:/AI:
kérdés-válasz párokra) tanított modellt tölt be (models/mf_ai_zero_chat_v0_7.pt)
- ez a modell ténylegesen megpróbál válaszolni a kérdéseidre, nem csak
önálló motivációs mondatokat ír, mint a korábbi (v0.1-v0.4) modellek.
A --model-path kapcsolóval bármelyik régi modell is betölthető, ha
összehasonlításként ki akarod próbálni.

A v0.7e-től kezdve egy egyszerű ROUTER (lásd router.py) dönti el minden
üzenetnél, melyik modell válaszoljon: általános beszélgetéshez mindig a
v0.7 modellt használja (abban a legjobb), explicit mondatszám-kéréshez
("Írj 5 mondatot...") pedig a v0.7c modellt (ez utóbbira specializálták).
Ezt méréssel igazoltuk (lásd tests/test_v07e_router.py): a két modell
szétválasztása jobb eredményt ad, mint bármelyik modell önmagában
próbálná mindkét feladatot ellátni.

Fontos tudni, mit kapsz:
  - Ez továbbra is egy kicsi, karakter-alapú LSTM, nem egy igazi chatbot.
  - A chat-modell annyi kérdés-válasz párt látott tanítás közben, amennyi
    a data/chat_train.txt-ben van - ismeretlen témájú vagy szokatlanul
    megfogalmazott kérdésekre kevésbé lesz pontos a válasza.
  - A beszélgetés előzményét (utolsó 5 váltás) megjegyzi és a végén elmenti,
    de a válaszgeneráláshoz csak a legutóbbi üzenetedet használja promptként
    - egy ekkora karakteralapú modell nem tudna értelmesen mit kezdeni egy
    hosszú, több körös párbeszéd-kontextussal. A "memória" itt tehát a
    beszélgetés nyomon követését és naplózását szolgálja, nem azt, hogy a
    modell ténylegesen "emlékezne" a korábbi mondatokra.

Ez egy működő prototípus - ne várj tőle ChatGPT-szintű társalgást.

A v0.8-tól minden AI-válasz automatikusan kiértékelődik egy egyszerű,
szabályalapú pontozással (lásd evaluator.py), és bekerül a
learning_log/feedback.jsonl naplóba (lásd learning_log.py) - ez CSAK
NAPLÓZ, nem tanít és nem módosít semmilyen modellt.

Futtatás:
    python src/chat.py
    python src/chat.py --temperature 0.6
    python src/chat.py --model-path models/mf_ai_zero_v0_4.pt

Parancsok a chat közben:
    /exit        kilépés (a beszélgetés mentve marad)
    /reset       a beszélgetés-memória törlése
    /temp 0.6    a temperature (kreativitás) átállítása
    /help        parancsok kiírása
"""

import argparse
import os
import random
import re
from collections import deque
from datetime import datetime

import torch

import config
from evaluator import evaluate_reply
from generate import generate, load_model, split_into_sentences
from learning_log import log_feedback

MEMORY_SIZE = 5
MIN_SENTENCES = 3
MAX_SENTENCES = 6
MAX_GEN_LENGTH = 600
CONVERSATIONS_DIR = os.path.join(config.BASE_DIR, "conversations")

# v0.7b: egyszerű intent-felismerés arra, ha a user konkrét mondatszámot kér
# ("írj 5 mondatot...", "magyarázd el 4 mondatban...", "mondj 6 mondatot...").
# Ahelyett, hogy a modellre bíznánk, hogy ezt a számot "megértse" és
# betartsa (amit egy ekkora karakter-alapú modell nem tud megbízhatóan),
# a program maga olvassa ki a számot, és azt írja elő a --sentences logikának.
SENTENCE_COUNT_WORDS = {
    "egy": 1, "két": 2, "kettő": 2, "három": 3, "négy": 4, "öt": 5,
    "hat": 6, "hét": 7, "nyolc": 8, "kilenc": 9, "tíz": 10,
}
SENTENCE_COUNT_PATTERN = re.compile(
    r"\b(\d+|" + "|".join(SENTENCE_COUNT_WORDS) + r")\s*mondat", re.IGNORECASE
)
SENTENCE_COUNT_MIN = 1
SENTENCE_COUNT_MAX = 10


def detect_sentence_count(text):
    """Megkeresi, hogy a user kért-e konkrét mondatszámot a szövegében (pl.
    "írj 5 mondatot", "4 mondatban", "mondj 6 mondatot"). Ha talál, azt a
    számot adja vissza (1-10 közé korlátozva), különben None-t - ekkor a
    hívó fél dönti el a mondatszámot (pl. a webes felület legördülője, vagy
    a terminálos chat véletlen 3-6 közötti választása). Fontos: ez csak
    OLVASSA a szöveget, nem módosítja - a téma (pl. "az erőről") így
    sosem esik ki a modellnek küldött promptból."""
    match = SENTENCE_COUNT_PATTERN.search(text)
    if not match:
        return None
    token = match.group(1).lower()
    count = int(token) if token.isdigit() else SENTENCE_COUNT_WORDS[token]
    return max(SENTENCE_COUNT_MIN, min(SENTENCE_COUNT_MAX, count))

HELP_TEXT = """Elérhető parancsok:
  /exit        kilépés a chatből (a beszélgetés mentve marad)
  /reset       a beszélgetés-memória törlése
  /temp 0.6    a temperature (kreativitás) átállítása
  /help        ez a súgó"""

INTRO_TEXT = """Ez egy kicsi, karakter-alapú AI, motivációs magyar mondatokon tanítva -
NEM egy igazi chatbot. A válaszai a megtanult mondatstílust folytatják,
nem biztos, hogy tartalmilag felelnek a kérdésedre. Ez egy működő
prototípus, ne várj tőle ChatGPT-szintű társalgást."""


def parse_args():
    parser = argparse.ArgumentParser(description="MF-AI-Zero beszélgetős mód.")
    parser.add_argument(
        "--model-path",
        type=str,
        default=config.CHAT_MODEL_PATH,
        help="Melyik modell válaszoljon az ÁLTALÁNOS beszélgetésre (alapértelmezés: "
        "a v0.7 chat-modell).",
    )
    parser.add_argument(
        "--instruction-model-path",
        type=str,
        default=os.path.join(config.BASE_DIR, "models", "mf_ai_zero_chat_v0_7c.pt"),
        help="Melyik modell válaszoljon az explicit mondatszám-kérésekre "
        "(pl. 'Írj 5 mondatot...') - alapértelmezés: a v0.7c modell.",
    )
    parser.add_argument(
        "--no-router",
        action="store_true",
        help="Router kikapcsolása: minden üzenetre (mondatszám-kérésre is) csak a "
        "--model-path modell válaszol, a v0.7-v0.7c útválasztás nélkül.",
    )
    parser.add_argument(
        "--no-guard",
        action="store_true",
        help="A v0.9-guard (kategória-alapú tartalmi őr + retry + kontrollált "
        "fallback, lásd guard.py) kikapcsolása - ekkor a router nyers válasza "
        "megy tovább, ellenőrzés/javítás nélkül (a --no-router kapcsolóval "
        "együtt nincs hatása, mert az már a routert is kikapcsolja).",
    )
    parser.add_argument(
        "--no-memory",
        action="store_true",
        help="A v0.9 rövid memória (lásd memory.py) kikapcsolása - ekkor a "
        "modell SOHA nem kap korábbi váltásból épített kontextust, még akkor "
        "sem, ha a user egyértelműen visszautal ('folytasd', 'amit mondtam', "
        "'előző', vagy egy rövid 'az'/'ez' kérdés).",
    )
    parser.add_argument(
        "--no-long-memory",
        action="store_true",
        help="A v1.0 hosszú távú memória (lásd long_term_memory.py) "
        "kikapcsolása - ekkor a rendszer nem ment ('jegyezd meg...') és nem "
        "keres vissza korábbi, fájlba mentett memóriákat.",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.7,
        help="Kezdő temperature érték (kreativitás mértéke).",
    )
    return parser.parse_args()


def start_conversation_file():
    os.makedirs(CONVERSATIONS_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(CONVERSATIONS_DIR, f"conversation_{timestamp}.txt")


def respond(model, stoi, itos, device, user_message, temperature, sentence_target=None, prompt_format="plain", context_prefix=""):
    """Egy AI választ generál a user_message-re. A promptból kiszűrjük azokat
    a karaktereket, amiket a modell nem ismer (ugyanúgy, ahogy a generate()
    belül is teszi), hogy pontosan tudjuk, hol kezdődik a ténylegesen
    generált rész.

    context_prefix: opcionális, a v0.9 rövid memória (lásd memory.py)
    használja - egy rövid, natív "User: ...\\nAI: ...\\n\\n" formátumú
    előzmény-blokk, amit a promptba a user_message ELÉ illesztünk. Alapból
    üres string, ami a korábbi (memória nélküli) viselkedést adja vissza
    változatlanul.

    sentence_target: hány mondatot generáljon. Ha a user_message-ben
    felismerhető egy konkrét mondatszám-kérés (pl. "írj 5 mondatot"), az
    mindig felülírja ezt az értéket. Ha nincs ilyen kérés a szövegben, és
    sentence_target sincs megadva, 3-6 között véletlenszerűen választ (ezt
    használja a terminálos chat); a webes felület a felhasználó által a
    legördülőben választott konkrét értéket adja át ide.

    prompt_format: "chat" esetén a promptot "User: <üzenet>\\nAI:" alakra
    csomagoljuk (FONTOS: záró szóköz NÉLKÜL, annak ellenére, hogy a tanító
    adatban "AI: " szóközzel szerepel - méréssel igazolt, hogy ha a
    promptban mi magunk adjuk hozzá a szóközt, a modell sokkal
    megbízhatatlanabbul válaszol, mint ha ő maga generálja azt első
    karakterként; ez a modell rejtett állapotának egy finomsága, nem
    elírás). Ez a formátum teszi lehetővé, hogy a modell tényleg a
    kérdésre válaszoljon, ne csak egy önálló mondatot folytasson. "plain"
    esetén (a régi, v0.1-v0.4 modellek) a user_message-et közvetlenül,
    csomagolás nélkül kapja."""
    if prompt_format == "chat":
        model_prompt = f"{context_prefix}User: {user_message}\nAI:"
    else:
        model_prompt = user_message

    known_prompt = "".join(ch for ch in model_prompt if ch in stoi)
    if not known_prompt:
        return "Bocsánat, egyetlen ismert karaktert sem találtam az üzenetedben."

    requested_count = detect_sentence_count(user_message)
    if requested_count is not None:
        sentence_target = requested_count
    elif sentence_target is None:
        sentence_target = random.randint(MIN_SENTENCES, MAX_SENTENCES)

    # Ha a user kifejezetten egy adott mondatszámot kért, több próbálkozásból
    # választjuk a legjobbat: a modell (kis mérete miatt) néha idő előtt
    # "befejezettnek" érzi a választ, és egy kitalált következő kérdésbe kezd
    # - ezt levágjuk, de emiatt rövidebb lehet a végeredmény a kértnél. A
    # program itt "segít be" azzal, hogy újrapróbálja, és a legtöbb valódi
    # mondatot tartalmazó változatot adja vissza, hiszen a cél az, hogy a
    # kért mondatszámot lehetőleg tényleg teljesítsük.
    attempts = 8 if requested_count is not None else 1
    best_reply, best_count = "", -1

    for _ in range(attempts):
        text = generate(
            model=model,
            prompt=model_prompt,
            stoi=stoi,
            itos=itos,
            length=MAX_GEN_LENGTH,
            temperature=temperature,
            device=device,
            sentences=sentence_target,
        )
        reply = text[len(known_prompt):].strip()

        # Ha a modell egy kitalált következő "User:" kérdést (vagy akár egy
        # újabb "AI:" választ) is elkezdett volna generálni - mert a tanító
        # adatban a válaszok után ez következett -, azt levágjuk: minket
        # csak az aktuális, egyetlen válasz érdekel.
        cutoffs = [i for i in (reply.find("\nUser:"), reply.find("\nAI:")) if i != -1]
        if cutoffs:
            reply = reply[: min(cutoffs)].strip()

        count = len(split_into_sentences(reply))
        if count > best_count:
            best_reply, best_count = reply, count
        if requested_count is None or count >= requested_count:
            break

    return best_reply if best_reply else "..."


def handle_command(command_line, temperature, memory):
    """Egy /-lal kezdődő parancsot dolgoz fel. Visszaadja az (esetleg
    módosított) temperature-t, és hogy a chat folytatódjon-e (False = kilépés)."""
    command, _, arg = command_line.partition(" ")
    command = command.lower().strip()
    arg = arg.strip()

    if command == "/exit":
        print("Viszlát!")
        return temperature, False

    if command == "/reset":
        memory.clear()
        print("(A beszélgetés-memória törölve.)")
        return temperature, True

    if command == "/help":
        print(HELP_TEXT)
        return temperature, True

    if command == "/temp":
        try:
            new_temp = float(arg)
            if new_temp <= 0:
                raise ValueError
        except ValueError:
            print("Hibás érték. Használat: /temp 0.6 (pozitív szám)")
            return temperature, True
        print(f"(Temperature beállítva: {new_temp})")
        return new_temp, True

    print(f"Ismeretlen parancs: {command}  (súgó: /help)")
    return temperature, True


def main():
    args = parse_args()
    temperature = args.temperature

    device = torch.device("cpu")
    print("Modell betöltése...")
    model, stoi, itos, prompt_format = load_model(device, args.model_path)
    print(f"Kész! Általános modell: {args.model_path} (formátum: {prompt_format})")

    general_model = (model, stoi, itos, device, prompt_format)
    instruction_model = None
    router_active = not args.no_router

    # Helyi import: a router.py (és a guard.py, ami a routerre épül) a
    # chat.py-ból importál (detect_sentence_count, respond), ezért
    # modulszinten importálva körkörös importot okozna.
    from router import detect_intent, route_and_respond
    from guard import guarded_route_and_respond

    guard_active = router_active and not args.no_guard
    memory_active = guard_active and not args.no_memory
    long_memory_active = guard_active and not args.no_long_memory

    if router_active:
        i_model, i_stoi, i_itos, i_fmt = load_model(device, args.instruction_model_path)
        instruction_model = (i_model, i_stoi, i_itos, device, i_fmt)
        print(f"Kész! Mondatszám-kérésekhez: {args.instruction_model_path} (formátum: {i_fmt})")
    print()
    print(INTRO_TEXT)
    print()
    print(HELP_TEXT)
    print(f"\n(Jelenlegi temperature: {temperature})\n")

    memory = deque(maxlen=MEMORY_SIZE)
    conversation_path = start_conversation_file()

    with open(conversation_path, "a", encoding="utf-8") as log_file:
        while True:
            try:
                user_message = input("User: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nViszlát!")
                break

            if not user_message:
                continue

            if user_message.startswith("/"):
                temperature, keep_going = handle_command(user_message, temperature, memory)
                if not keep_going:
                    break
                continue

            guard_info = None
            if guard_active:
                reply, intent, model_used, sentence_info, guard_info = guarded_route_and_respond(
                    general_model, instruction_model, user_message, temperature,
                    history=list(memory), memory_enabled=memory_active,
                    long_memory_enabled=long_memory_active,
                )
            elif router_active:
                reply, intent, model_used, sentence_info = route_and_respond(
                    general_model, instruction_model, user_message, temperature
                )
            else:
                reply = respond(
                    model, stoi, itos, device, user_message, temperature, prompt_format=prompt_format
                )
                intent = detect_intent(user_message)
                model_used = args.model_path
                sentence_info = None
            print(f"AI: {reply}")

            # v0.8: minden választ kiértékelünk (szabályalapú pontozás) és
            # naplózunk - ez CSAK NAPLÓZ, nem tanít és nem módosítja a választ.
            # v0.9-guard: ha a guard aktív volt, a napló a guard_info mezőivel
            # (detected_intent/expected_answer_type/guard_triggered/...) is
            # kiegészül (lásd learning_log.py).
            score, flags = evaluate_reply(user_message, reply, intent, sentence_info)
            log_feedback(user_message, reply, intent, model_used, score, flags, sentence_info, guard_info=guard_info)

            memory.append((user_message, reply))

            log_file.write(f"User: {user_message}\n")
            log_file.write(f"AI: {reply}\n")
            log_file.flush()

    print(f"\nA beszélgetés elmentve ide: {conversation_path}")


if __name__ == "__main__":
    main()
