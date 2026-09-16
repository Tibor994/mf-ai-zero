"""
MF-AI-Zero - v0.8 tanulási napló.

Minden AI-választ elment egy sor JSON-ként (JSONL formátum - soronként
egy önálló JSON objektum) a learning_log/feedback.jsonl fájlba: user
üzenet, AI válasz, intent, melyik modell válaszolt, a válasz hossza,
minőségi pontszám és a talált problémák (lásd evaluator.py).

FONTOS: ez a modul KIZÁRÓLAG NAPLÓZ - nem tanít semmit, nem módosít
egyetlen modellt sem. A cél, hogy később, egy KÜLÖN lépésben (külön
szkripttel, emberi átnézéssel) ebből a naplóból lehessen javító
tanítóadatot válogatni - például az alacsony pontszámú válaszokat
átnézve, és jobb választ írva a hozzájuk tartozó kérdésre.

A JSONL formátum azért jó erre, mert soronként appendálható (nem kell a
teljes fájlt újraírni minden mentésnél), és soronként/eszközfüggetlenül
könnyen feldolgozható (pl. "grep", vagy egy egyszerű Python szkript,
ami sorról sorra json.loads()-ol).
"""

import json
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEARNING_LOG_DIR = os.path.join(BASE_DIR, "learning_log")
LEARNING_LOG_PATH = os.path.join(LEARNING_LOG_DIR, "feedback.jsonl")


def log_feedback(
    user_message,
    reply,
    intent,
    model_used,
    score,
    flags,
    sentence_info=None,
    log_path=None,
    guard_info=None,
):
    """Egy sort ír a tanulási naplóba. Visszaadja a felépített rekordot
    (dict-ként) - ez hasznos lehet pl. a teszteknek, hogy ellenőrizzék a
    tartalmát anélkül, hogy vissza kéne olvasniuk a fájlt.

    log_path: csak teszteléshez hasznos - ha megadod, nem az alapértelmezett
    learning_log/feedback.jsonl-be ír, hanem a megadott fájlba.

    guard_info: opcionális, a guard.guarded_route_and_respond() 5. elemeként
    visszaadott dict (lásd guard.py). Ha meg van adva, a rekord kiegészül a
    detected_intent/expected_answer_type/guard_triggered/retry_count/
    fallback_used/failure_reason/corrected_answer/used_for_training
    mezőkkel - ha None (alapértelmezés, pl. a v0.8-as, guard nélküli
    naplózásnál), a rekord formátuma VÁLTOZATLAN marad a korábbi
    verzióhoz képest.

    Ha a fájlba írás bármiért meghiúsul (pl. jogosultsági hiba), a hiba
    el van nyelve - a naplózás sosem szakíthatja meg a beszélgetést."""
    log_path = log_path or LEARNING_LOG_PATH

    record = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "user_message": user_message,
        "ai_reply": reply,
        "intent": intent,
        "model_used": model_used,
        "reply_length_chars": len(reply or ""),
        "reply_length_words": len((reply or "").split()),
        "quality_score": score,
        "quality_flags": flags,
    }
    if sentence_info is not None:
        requested_n, actual_n, fixed = sentence_info
        record["sentence_requested"] = requested_n
        record["sentence_actual"] = actual_n
        record["sentence_fixed"] = fixed
    if guard_info is not None:
        record.update(guard_info)

    try:
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError:
        pass

    return record
