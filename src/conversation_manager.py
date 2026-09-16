"""
MF-AI-Zero - v1.3 beszélgetés-állapot kezelő (conversation manager).

CÉL: az AI ne veszítse el a fonalat több üzeneten át, DE ez NEM azt
jelenti, hogy a modell teljes chat historyt kap - lásd chat.py fejléce:
egy ekkora karakter-alapú LSTM nem tudna értelmesen mit kezdeni egy
hosszú, több körös kontextussal.

Amit ez a modul csinál: EGYSZERŰ, SZABÁLYALAPÚ (nem ML) állapotot tart
nyilván a beszélgetésről (active_topic, current_goal, last_user_intent,
open_questions, pending_tasks, last_decision), és ebből egy RÖVID,
KONTROLLÁLT conversation_summary-t épít. Ez a summary CSAK akkor kerül a
modell promptjába, ha a user üzenete kifejezetten igényli (visszautal,
"folytasd", "ezt javítsd" stb. - lásd detect_context_need()) - egyébként
a válasz pontosan úgy megy, mint enélkül.

FONTOS, amit ez a modul SZÁNDÉKOSAN NEM csinál:
  - NEM ad teljes chat historyt a modellnek - csak egy rövid, tömör
    összefoglalót, és azt is csak indokolt esetben.
  - NEM ír a hosszú távú memóriába (long_term_memory.py) vagy a
    tudásbázisba (knowledge_base.py) - ez a modul KIZÁRÓLAG a folyamat
    memóriájában él (ugyanaz a modell, mint a v0.9 rövid memória
    `history` deque-je vagy a webes `recent_exchanges`), a
    beszélgetés/szerver újraindításával elvész.
  - NEM tanul semmit automatikusan - szabályalapú kulcsszó-mintázatok
    döntik el, mikor mit frissít, nincs mögötte gépi tanulás.

Az ÁLLAPOTOT (ConversationState) a HÍVÓ FÉL (chat.py, web/app.py) hozza
létre és tartja életben a beszélgetés/szerver folyamat memóriájában -
ugyanaz a felelősségi elv, mint a v0.9 rövid memória `history` deque-jénél.
A guard.py CSAK OLVASSA (a prompt-kontextushoz), a frissítés
(ConversationState.update()) a hívó fél feladata minden váltás UTÁN.
"""

import re
import unicodedata

MAX_OPEN_QUESTIONS = 3
MAX_PENDING_TASKS = 3
MAX_SUMMARY_CHARS = 260
MAX_PROMPT_CHARS = 200
MAX_FIELD_CHARS = 70


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


# ---------------------------------------------------------------------------
# 1) "Igazán kell a kontextus?" felismerés - CSAK ezekre a fordulatokra
#    (és rövid, névmásos utalásra) épül be a conversation_summary a
#    promptba. Ugyanaz az elv, mint a v0.9 rövid memóriánál
#    (memory.detect_followup) - itt a user KIFEJEZETTEN kért, bővebb
#    fordulatokkal bővítve ("ezt javítsd", "akkor a másik").
# ---------------------------------------------------------------------------

CONTEXT_TRIGGER_GROUPS = [
    ("folytasd",),
    ("folytassuk",),
    ("az", "elozo"),
    ("ezt", "javitsd"),
    ("javitsd", "ki"),
    ("amit", "mondtam"),
    ("amit", "irtam"),
    ("akkor", "masik"),
    ("korabban", "mondtam"),
    ("mint", "az", "elobb"),
]

WEAK_DEICTIC_WORDS = {"az", "ez", "azt", "ezt", "arrol", "errol", "azzal", "ezzel", "annak", "ennek"}
WEAK_MAX_WORDS = 5


def detect_context_need(text):
    """Visszaadja (kell_kontextus: bool, ok: str|None) - ugyanaz a két
    kategória, mint a rövid memóriánál: "explicit_backreference" (pl.
    "folytasd", "ezt javítsd") vagy "short_deictic_followup" (rövid,
    névmásos kérdés)."""
    normalized = _normalize(text)
    if not normalized:
        return False, None
    for group in CONTEXT_TRIGGER_GROUPS:
        if all(keyword in normalized for keyword in group):
            return True, "explicit_backreference"
    words = re.sub(r"[^\w\s]", " ", normalized).split()
    if 0 < len(words) <= WEAK_MAX_WORDS and any(w in WEAK_DEICTIC_WORDS for w in words):
        return True, "short_deictic_followup"
    return False, None


# ---------------------------------------------------------------------------
# 2) Könnyű, szabályalapú detektorok az állapot mezőihez - NEM NLU/ML,
#    egyszerű kulcsszó-mintázatok (ugyanaz a stílus, mint
#    long_term_memory.CANDIDATE_PATTERNS-nél).
# ---------------------------------------------------------------------------

GOAL_KEYWORDS = ["a celom", "azon dolgozom", "szeretnek elerni", "kovetkezo lepesem", "az a tervem"]
CLOSURE_KEYWORDS = ["rendben", "ertem", "koszonom", "oke", "szuper", "az jo volt", "megvan", "kesz vagyunk"]
TASK_KEYWORDS = [
    "irj", "keress ra", "keresd meg", "nezz utana", "jegyezd meg", "keszits", "csinald meg",
    "mutasd meg", "magyarazd el", "sorolj fel", "hasonlitsd ossze",
]


def _matches_any(normalized_text, keywords):
    return any(kw in normalized_text for kw in keywords)


# ---------------------------------------------------------------------------
# 3) Az állapot maga - a hívó fél (chat.py / web/app.py) hozza létre és
#    tartja életben a folyamat memóriájában.
# ---------------------------------------------------------------------------


class ConversationState:
    def __init__(self):
        self.active_topic = None
        self.current_goal = None
        self.last_user_intent = None
        self.open_questions = []
        self.pending_tasks = []
        self.last_decision = None
        self.conversation_summary = None

    def reset(self):
        self.__init__()

    def update(self, user_message, reply, intent, needed_context=False):
        """Minden váltás UTÁN hívandó (a hívó fél felelőssége - a guard.py
        nem hívja meg magától). needed_context: a detect_context_need()
        eredménye erre az üzenetre - ha True, az ÚJ üzenet valószínűleg a
        MEGLÉVŐ témáról szól, ezért NEM írjuk felül vele az active_topic-ot."""
        normalized = _normalize(user_message)
        self.last_user_intent = intent

        if not needed_context and user_message and user_message.strip():
            self.active_topic = _trim(user_message.strip(), MAX_FIELD_CHARS)

        if _matches_any(normalized, GOAL_KEYWORDS):
            self.current_goal = _trim(user_message.strip(), MAX_FIELD_CHARS)

        if _matches_any(normalized, CLOSURE_KEYWORDS):
            self.open_questions = []
            self.pending_tasks = []
        else:
            if user_message and user_message.strip().endswith("?"):
                q = _trim(user_message.strip(), MAX_FIELD_CHARS)
                if q not in self.open_questions:
                    self.open_questions.append(q)
                    self.open_questions = self.open_questions[-MAX_OPEN_QUESTIONS:]
            if _matches_any(normalized, TASK_KEYWORDS):
                t = _trim(user_message.strip(), MAX_FIELD_CHARS)
                if t not in self.pending_tasks:
                    self.pending_tasks.append(t)
                    self.pending_tasks = self.pending_tasks[-MAX_PENDING_TASKS:]

        if reply and reply.strip():
            self.last_decision = _trim(reply.strip(), MAX_FIELD_CHARS)

        self.conversation_summary = self._build_summary()

    def _build_summary(self):
        parts = []
        if self.active_topic:
            parts.append(f"Eddig erről volt szó: \"{self.active_topic}\".")
        if self.current_goal:
            parts.append(f"A cél: \"{self.current_goal}\".")
        if self.open_questions:
            parts.append(f"Nyitott kérdés: \"{self.open_questions[-1]}\".")
        if self.pending_tasks:
            parts.append(f"Függőben: \"{self.pending_tasks[-1]}\".")
        if self.last_decision:
            parts.append(f"Utoljára ezt mondtam: \"{self.last_decision}\".")
        return _trim(" ".join(parts), MAX_SUMMARY_CHARS)

    def as_dict(self):
        return {
            "active_topic": self.active_topic,
            "current_goal": self.current_goal,
            "last_user_intent": self.last_user_intent,
            "open_questions": list(self.open_questions),
            "pending_tasks": list(self.pending_tasks),
            "last_decision": self.last_decision,
            "conversation_summary": self.conversation_summary,
        }


# ---------------------------------------------------------------------------
# 4) Prompt-kontextus építés - ugyanaz a natív "User:/AI:\n\n" elv, mint a
#    többi kontextus-modulnál (memory.py, long_term_memory.py,
#    knowledge_base.py, web_research.py).
# ---------------------------------------------------------------------------


def build_conversation_prompt_context(summary):
    if not summary:
        return ""
    short = _trim(summary, MAX_PROMPT_CHARS)
    return f"User: Miről beszélgettünk eddig?\nAI: {short}\n\n"


def resolve_conversation_context(user_text, state, enabled=True):
    """Fő belépési pont a guard.py számára. Visszaad egy
    (conversation_info, prompt_context, needed_context) hármast:

    conversation_info: dict a learning_log-hoz - conversation_state_used/
    active_topic/current_goal/conversation_summary mezőkkel.
    prompt_context: "" (nincs szükség rá) vagy a
    build_conversation_prompt_context() eredménye.
    needed_context: a detect_context_need() nyers eredménye - a hívó
    (guard.py) ezt adja tovább a state.update()-nek, hogy az
    active_topic csak tényleg ÚJ témánál íródjon felül.
    """
    info = {
        "conversation_state_used": False,
        "active_topic": state.active_topic if state else None,
        "current_goal": state.current_goal if state else None,
        "conversation_summary": None,
    }
    if not enabled or state is None:
        return info, "", False

    needed_context, _reason = detect_context_need(user_text)
    if not needed_context or not state.conversation_summary:
        return info, "", needed_context

    info["conversation_state_used"] = True
    info["conversation_summary"] = state.conversation_summary
    prompt_context = build_conversation_prompt_context(state.conversation_summary)
    return info, prompt_context, needed_context
