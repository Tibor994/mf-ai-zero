"""
MF-AI-Zero - MT-3: többfordulós beszélgetések duplikáció-ellenőrzése és közeli-változat csoportosítása.

CÉL: a `docs/MULTITURN_FORMAT.md` szerinti beszélgetés-rekordokat (a `tools/multiturn_validate.py`,
MT-1 által turns-validált bemenetet) összeveti egymással (fájlon belül és fájlok/csomagok között) és a
TE-1 exportált egyfordulós példákkal, és csoportazonosítót ad az összetartozó változatoknak, hogy a
későbbi MT-2 felosztás egy csoportot ne szórhasson szét. Módszer, normalizálás, pontszám-jelentés,
küszöbök és korlátok: `docs/MULTITURN_DEDUPE.md`.

ALAPELV: ugyanaz a téma megengedett, ugyanaz a TANÍTÁSI MINTA nem.
  * pontosan ismétlődő tanítási minta: elutasítás (`reject`) vagy javítás;
  * hasonlóság >= 0,90: felülvizsgálat (`review`); >= 0,95: alapból elutasítás (`reject`),
    kivéve a dokumentáltan eltérő képességet tanító, deklarált változatot (közös split_group) és a
    dokumentált kivételt (--exceptions);
  * a `reject`/`review` HALADÁSI TILTÁST jelent (a rekord `blocked`), NEM forrásadat-törlést;
    a bemeneti fájlokat az eszköz csak olvassa.
A státusz `clear_of_duplicate_findings` NEM elfogadás, NEM tartalmi ellenőrzés, NEM training-ready.

EGYSÉGEK ÉS PONTSZÁMOK (részletesen a dokumentációban):
  conversation  - teljes beszélgetés: szerep- és pozíció-őrző, "összevont" karakter-arány
                  (2*Sum(M_i)/Sum(la_i+lb_i), az azonos indexű és szerepű üzenetpárokon belül)
  sample        - egy assistant-fordulóra adott tanítási minta = (releváns előzmény, kérdés, válasz);
                  pontszám = min(kérdés, válasz, előzmény)
  export        - ugyanez a minta a TE-1 exportált egyfordulós példáival szemben (előzmény nélkül)
  A hasonlóság difflib.SequenceMatcher(None, a, b, autojunk=False) egyező-karakter aránya
  normalizált szövegen: szöveges átfedés, NEM bizonyított jelentésazonosság.

GYORSÍTÁS: a hossz- és karakter-multiset felső korlátok BIZONYÍTOTTAN pontosak (csak olyan párt
hagynak ki, amelynek pontszáma a küszöb alatt van; --no-prefilter a teljes összehasonlítás).
A paraphrase-heurisztika (tartalmi szó-átfedés) nem közelítő szűrő, hanem külön, jelölt szabály.

Használat:
    python tools/multiturn_dedupe.py --mode dataset|fixture --conversations <f1.jsonl> [<f2.jsonl> ...]
        --out-dir <mappa> [--te1-export <TE-1 futás-mappa>] [--exceptions <json>] [--name-bank <json>]
        [--run-name <név>] [--no-prefilter] [--no-name-normalization] [--handbook-strict]
    python tools/multiturn_dedupe.py --verify-report <dedupe_report.json>

Kilépési kódok: 0 lefutott, nincs blokkoló találat; 1 lefutott, VAN blokkoló találat (reject/review);
2 argumentumhiba; 10 bemeneti fájl hiba; 11 nem turns-validált rekord; 12 TE-1 export hiba;
13 kivétel-fájl hiba; 14 kimeneti útvonal hiba; 15 a bemenet megváltozott a jelentés óta;
16 a bemenet a futás közben megváltozott.
"""

import argparse
import bisect
import datetime
import hashlib
import json
import os
import re
import sys
import time
import unicodedata
from difflib import SequenceMatcher

import dataset_export_chat_text as te2
import dataset_export_train as te1
import multiturn_validate as mt1

TOOL_VERSION = "mt3-1.0"

# --- a kézikönyv döntési szabályai (NEM állíthatók parancssorból) ---------------------------
REVIEW_MIN = 0.90
REJECT_MIN = 0.95
# --- csoportosítási/jelölő szabályok (heurisztikák, dokumentálva; nem elfogadási szabályok) --
GROUP_MIN = 0.80              # összevont beszélgetés-hasonlóság: közeli változat (csak csoportosítás)
PARAPHRASE_MIN = 0.35         # tartalmi szó-átfedés (Jaccard): valószínű átfogalmazott változat -> review (ideiglenes kalibráció)
PARAPHRASE_MIN_WORDS = 15
MIN_DECISION_CHARS = 60       # e alatt (kérdés+válasz) a minta "triviális": hasonlóság nem dönt, csak a pontos egyezés
MIN_PARTIAL_CHARS = 30        # részleges egyezés-jelzéshez minimum kérdés/válasz hossz
MIN_SHARED_MESSAGE_CHARS = 20
MAX_GROUP_SIZE = 5
PERSONA_MAX = 3
DECLARED_GROUP_MAX = 3
VARIANT_SHARE_PLAN = 0.15

EXIT_INPUT, EXIT_INVALID, EXIT_TE1, EXIT_EXCEPTIONS, EXIT_OUTPUT, EXIT_CHANGED_AFTER, EXIT_CHANGED_DURING = 10, 11, 12, 13, 14, 15, 16

NON_WAIVABLE = {"duplicate_id", "exact_conversation"}
BLOCKING = {"reject", "review"}

DISCLAIMER = ("A `clear_of_duplicate_findings` állapot csak azt jelenti, hogy az ellenőrző nem talált blokkoló "
              "duplikáció-jelzést; NEM elfogadás, NEM tartalmi ellenőrzés, NEM training-ready. A szöveges "
              "hasonlóság nem bizonyított jelentésazonosság.")
LIMITATIONS = [
    "A hasonlóság karakter-alapú szöveges átfedés (SequenceMatcher egyező-karakter arány), nem jelentés-azonosság: az átfogalmazás nagyrészt észrevétlen marad; a paraphrase-jelzés külön, tartalmi szó-átfedésen alapuló heurisztika (felülvizsgálatot kér, sosem dönt).",
    "A pozíció-őrző beszélgetés-hasonlóság az azonos indexű üzeneteket veti össze: beszúrt vagy törölt váltás után a beszélgetés-szintű pontszám alacsony lehet; ezt a minta-szintű ellenőrzés és az üzenet-átfedés jelzései részben pótolják.",
    "Rövid szövegeknél (kérdés+válasz < 60 normalizált karakter) a 0,90/0,95 küszöb nem értelmezhető (1-2 karakter eltérés is 0,9 fölé visz): itt csak a pontos egyezés minősít.",
    "A névsemlegesítés a MT-0 névtár alapján történik (ragozott alakok szűk végződéslistával); a névtárban nem szereplő név különbségként számít.",
    "A minta releváns előzménye a `meta.depends` annotáció és az előző váltás: az annotáció helyességét az eszköz nem ellenőrzi.",
    "A csoportosítás egyszeres kötésű (tranzitív lezárás): egy hosszú lánc nagy csoportot adhat (lásd a csoportméret-jelzést).",
]

# ---------------------------------------------------------------------------
# normalizálás
# ---------------------------------------------------------------------------

_QUOTE_MAP = str.maketrans({"„": '"', "”": '"', "“": '"', "‘": "'", "’": "'", "–": "-", "—": "-", "…": "..."})
_LIST_MARKER_RE = re.compile(r"(?:(?<=\s)|^)(?:[0-9]{1,2}[.)]|[-•*])(?=\s+\S)")
_NONWORD_RE = re.compile(r"[^\w\s]|_")
_TOKEN_RE = re.compile(r"[^\W\d_]+")
NAME_PLACEHOLDER = "NÉV"


class NameMasker:
    """A névtár (jóváhagyott + tiltott keresztnevek) tokenjeit NÉV-re cseréli, hogy a névcserés változat
    egyezzen. Ragozott alakokat az MT-1 illesztőjével ismer fel."""

    def __init__(self, bank):
        self.groups = [("approved", bank["approved_given_names"]), ("blocked_given", bank["blocked_given_names"])]
        self.cache = {}

    def _is_name(self, tok):
        hit = self.cache.get(tok)
        if hit is None:
            hit = (len(tok) >= 2 and tok[0].isupper() and not tok.isupper()
                   and mt1._best_match(tok, self.groups) is not None)
            self.cache[tok] = hit
        return hit

    def __call__(self, text):
        return _TOKEN_RE.sub(lambda m: NAME_PLACEHOLDER if self._is_name(m.group(0)) else m.group(0), text)


def normalize(text, masker=None):
    """Formátum-/elválasztójel-mentes összehasonlítási alak: NFC, tipográfiai idézőjelek/gondolatjelek
    egységesítése, (opcionális) névsemlegesítés, listajelölők (`1.`, `-`, `•`) eltávolítása, kisbetű,
    írásjelek szóközre, szóközök összevonása. A számok és az ékezetek megmaradnak."""
    t = unicodedata.normalize("NFC", text).translate(_QUOTE_MAP)
    if masker is not None:
        t = masker(t)
    t = _LIST_MARKER_RE.sub(" ", t).casefold()
    return " ".join(_NONWORD_RE.sub(" ", t).split())


_ALPHABET = "abcdefghijklmnopqrstuvwxyzáéíóöőúüű0123456789 "


def char_vec(s):
    counts = [s.count(c) for c in _ALPHABET]
    counts.append(len(s) - sum(counts))     # egy közös vödör a ritka karaktereknek (a korlát így is felső korlát)
    return tuple(counts)


_STOP = set("""hogy nincs volt lesz vagy azt ezt ami akkor mint még meg már csak lehet kell egy egyik minden
igen nem van vannak szia köszi köszönöm szívesen rendben mert ezért így úgy akár akkor amit aztán majd
""".split())


def content_words(norm_text):
    words = norm_text.split()
    return {w[:4] for w in words if len(w) >= 4 and w not in _STOP} | {w for w in words if w.isdigit()}


# ---------------------------------------------------------------------------
# hasonlóság és bizonyítottan pontos előszűrés
# ---------------------------------------------------------------------------

def match_chars(a, b):
    """Az egyező karakterek száma (SequenceMatcher egyező blokkjainak összege), autojunk NÉLKÜL."""
    if not a or not b:
        return 0
    return sum(size for _i, _j, size in SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks())


def ratio_of(m, la, lb):
    return 2.0 * m / (la + lb) if (la + lb) else 1.0


class Stats:
    def __init__(self):
        self.d = {"pairs_considered": 0, "pruned_length": 0, "pruned_multiset": 0, "full_comparisons": 0}

    def add(self, other):
        for k, v in other.d.items():
            self.d[k] = self.d.get(k, 0) + v


def bounded_ratio(a, b, la, lb, va, vb, threshold, prefilter, stats):
    """Az a-b arány, ha >= threshold; különben None. Az előszűrés (hossz- és multiset-korlát) csak olyan párt
    hagy ki, amelynek aránya biztosan < threshold (M <= min(la, lb) és M <= a karakter-multisetek metszete,
    mert az egyező karakterek közös részsorozatot alkotnak)."""
    stats.d["pairs_considered"] += 1
    if la == 0 or lb == 0:
        return None
    if prefilter:
        if 2.0 * min(la, lb) / (la + lb) < threshold:
            stats.d["pruned_length"] += 1
            return None
        m_ub = min(la, lb, sum(map(min, va, vb)))
        if 2.0 * m_ub / (la + lb) < threshold:
            stats.d["pruned_multiset"] += 1
            return None
    stats.d["full_comparisons"] += 1
    r = ratio_of(match_chars(a, b), la, lb)
    return r if r >= threshold else None


def pooled_ratio(msgs_a, msgs_b):
    """Szerep- és pozíció-őrző összevont arány két üzenetlistán: [(role, norm_text), ...]. Csak az azonos
    indexű, azonos szerepű üzenetek illeszthetők; a párosítatlan üzenetek hossza a nevezőben szerepel."""
    total = sum(len(t) for _r, t in msgs_a) + sum(len(t) for _r, t in msgs_b)
    m = 0
    for (ra, ta), (rb, tb) in zip(msgs_a, msgs_b):
        if ra == rb:
            m += match_chars(ta, tb)
    return ratio_of(m, total, 0) if total else 1.0


def context_ratio(ca, cb):
    """Előzmény-hasonlóság (jobbra igazítva, szerep-őrző). Mindkettő üres -> 1,0; az egyik üres -> 0,0."""
    if not ca and not cb:
        return 1.0
    if not ca or not cb:
        return 0.0
    n = min(len(ca), len(cb))
    total = sum(len(t) for _r, t in ca) + sum(len(t) for _r, t in cb)
    m = 0
    for k in range(1, n + 1):
        (ra, ta), (rb, tb) = ca[-k], cb[-k]
        if ra == rb:
            m += match_chars(ta, tb)
    return ratio_of(m, total, 0) if total else 1.0


def ge(x, th, strict):
    return x > th if strict else x >= th


def at_boundary(x):
    return abs(x - REVIEW_MIN) < 1e-9 or abs(x - REJECT_MIN) < 1e-9


# ---------------------------------------------------------------------------
# adatmodell
# ---------------------------------------------------------------------------

class Rec:
    __slots__ = ("idx", "id", "file", "file_idx", "line", "family", "group", "persona", "msgs", "roles", "raw",
                 "norm", "nlens", "nvecs", "total", "words", "depends", "line_sha")


class Sample:
    """Tanítási minta: releváns előzmény, kérdés (norm.), válasz (norm.)."""
    __slots__ = ("kind", "owner", "turn", "q", "a", "ctx", "qlen", "alen", "qvec", "avec", "src")

    @property
    def trivial(self):
        return self.qlen + self.alen < MIN_DECISION_CHARS


def make_rec(idx, obj, file, file_idx, line, line_sha, masker):
    r = Rec()
    r.idx, r.id, r.file, r.file_idx, r.line, r.line_sha = idx, obj["id"], file, file_idx, line, line_sha
    meta = obj.get("meta") or {}
    r.family, r.group, r.persona = meta.get("family"), meta.get("split_group"), meta.get("persona")
    turns = obj["turns"]
    r.msgs = [(t["role"], t["text"]) for t in turns]
    r.roles = [t["role"] for t in turns]
    r.raw = [t["text"] for t in turns]
    r.norm = [normalize(t["text"], masker) for t in turns]
    r.nlens = [len(x) for x in r.norm]
    r.nvecs = [char_vec(x) for x in r.norm]
    r.total = sum(r.nlens)
    r.words = content_words(" ".join(r.norm))
    r.depends = {}
    for d in meta.get("depends") or []:
        if isinstance(d, dict) and isinstance(d.get("turn"), int) and isinstance(d.get("on"), list):
            r.depends[d["turn"]] = [i for i in d["on"] if isinstance(i, int)]
    return r


def build_conv_samples(rec):
    out = []
    for t in range(1, len(rec.msgs), 2):
        if rec.roles[t] != "assistant" or rec.roles[t - 1] != "user":
            continue
        idxs = sorted(i for i in ({t - 3, t - 2} | set(rec.depends.get(t, []))) if 0 <= i <= t - 2)
        s = Sample()
        s.kind, s.owner, s.turn = "conv", rec.idx, t
        s.q, s.a = rec.norm[t - 1], rec.norm[t]
        s.ctx = tuple((rec.roles[i], rec.norm[i]) for i in idxs)
        s.qlen, s.alen = len(s.q), len(s.a)
        s.qvec, s.avec = rec.nvecs[t - 1], rec.nvecs[t]
        s.src = None
        out.append(s)
    return out


def build_export_samples(rows, masker=None):
    out = []
    for i, r in enumerate(rows):
        obj = r["obj"]
        q = normalize(str(obj.get("instruction", "")) + (" " + str(obj.get("input", "")) if obj.get("input") else ""), None)
        a = normalize(str(obj.get("output", "")), None)
        s = Sample()
        s.kind, s.owner, s.turn = "te1", i, None
        s.q, s.a, s.ctx = q, a, ()
        s.qlen, s.alen = len(q), len(a)
        s.qvec, s.avec = char_vec(q), char_vec(a)
        s.src = {"file": r["source_file"], "line": r["source_line"]}
        out.append(s)
    return out


# ---------------------------------------------------------------------------
# döntési szabályok
# ---------------------------------------------------------------------------

def similarity_status(score, exact, strict):
    """reject / review / None a kézikönyv szabályai szerint (határeset: a >=; --handbook-strict a szó szerinti >)."""
    if exact or ge(score, REJECT_MIN, strict):
        return "reject"
    if ge(score, REVIEW_MIN, strict):
        return "review"
    return None


class Findings:
    def __init__(self):
        self.items = []
        self.edges = []      # (rec_a_idx, rec_b_idx, link_type, score)

    def add(self, scope, ftype, a, b, score, method, status, reason, extra=None):
        f = {"scope": scope, "type": ftype, "a": a, "b": b,
             "score": None if score is None else round(score, 6), "method": method,
             "status": status, "reason": reason, "at_boundary": bool(score is not None and at_boundary(score))}
        if extra:
            f["details"] = extra
        self.items.append(f)
        return f

    def link(self, ia, ib, link_type, score=None):
        self.edges.append((min(ia, ib), max(ia, ib), link_type, None if score is None else round(score, 6)))


def loc_conv(rec, turn=None):
    d = {"source": "conversation", "record": rec.id, "file": rec.file, "line": rec.line}
    if turn is not None:
        d["turn"] = turn
    return d


def loc_export(sample, row_id):
    d = {"source": "te1_export", "record": row_id}
    d.update(sample.src or {})
    return d


# ---------------------------------------------------------------------------
# beszélgetés-szintű ellenőrzés
# ---------------------------------------------------------------------------

def check_duplicate_ids(recs, export_ids, F):
    by_id = {}
    for r in recs:
        by_id.setdefault(r.id, []).append(r)
    for rid, group in sorted(by_id.items()):
        for k in range(1, len(group)):
            a, b = group[0], group[k]
            scope = "same_file" if a.file_idx == b.file_idx else "across_files"
            F.add("id", "duplicate_id", loc_conv(a), loc_conv(b), None, "azonosító-egyezés", "reject",
                  f"duplikált azonosító ({scope}); a beszélgetés azonosítója egyedi kell legyen", {"scope_detail": scope})
    for r in recs:
        if r.id in export_ids:
            F.add("id", "duplicate_id", loc_conv(r), {"source": "te1_export", "record": r.id}, None,
                  "azonosító-egyezés", "reject", "az azonosító megegyezik egy TE-1 exportált példa azonosítójával",
                  {"scope_detail": "vs_te1_export"})


def conv_pair_score(ra, rb, prefilter, stats, floor=GROUP_MIN):
    """Összevont, szerep- és pozíció-őrző arány; None, ha biztosan < floor (bizonyítottan pontos előszűrés)."""
    n = min(len(ra.norm), len(rb.norm))
    total = ra.total + rb.total
    stats.d["pairs_considered"] += 1
    if total == 0:
        return None
    if prefilter:
        m_ub = 0
        for k in range(n):
            la, lb = ra.nlens[k], rb.nlens[k]
            m_ub += la if la < lb else lb
        if 2.0 * m_ub / total < floor:
            stats.d["pruned_length"] += 1
            return None
        m_ub = 0
        for k in range(n):
            la, lb = ra.nlens[k], rb.nlens[k]
            m_ub += min(la, lb, sum(map(min, ra.nvecs[k], rb.nvecs[k])))
        if 2.0 * m_ub / total < floor:
            stats.d["pruned_multiset"] += 1
            return None
    stats.d["full_comparisons"] += 1
    m = 0
    for k in range(n):
        if ra.roles[k] == rb.roles[k]:
            m += match_chars(ra.norm[k], rb.norm[k])
    return 2.0 * m / total


def declared_variant(a, b):
    return bool(a.group) and a.group == b.group


def check_conversations(recs, prefilter, strict, F, stats, linked):
    """Pontos és közeli (pozíció- és szerep-őrző) egyezések."""
    exact_raw = {}
    exact_norm = {}
    for r in recs:
        exact_raw.setdefault(tuple(r.msgs), []).append(r)
        exact_norm.setdefault(tuple(zip(r.roles, r.norm)), []).append(r)
    done = set()          # a pár már döntési szintű (reject/review) beszélgetés-szintű találatot kapott
    for key, group in exact_raw.items():
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                a, b = group[i], group[j]
                if a.id == b.id:
                    continue            # azonos azonosítójú másolatot a duplicate_id jelzi
                F.add("conversation", "exact_conversation", loc_conv(a), loc_conv(b), 1.0,
                      "pontos szöveg- és szerep-egyezés (nyers)", "reject",
                      "pontosan ismétlődő beszélgetés (szerepek és üzenetsorrend is azonos)")
                F.link(a.idx, b.idx, "exact", 1.0)
                done.add((a.idx, b.idx))
    for key, group in exact_norm.items():
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                a, b = group[i], group[j]
                if (a.idx, b.idx) in done or a.id == b.id:
                    continue
                dv = declared_variant(a, b)
                F.add("conversation", "exact_after_normalization", loc_conv(a), loc_conv(b), 1.0,
                      "pontos egyezés normalizálás után (névsemlegesítés, írásjelek, listajelölők)",
                      "review" if dv else "reject",
                      ("deklarált változat (közös split_group): csak név/formátum különbözik, dokumentált eltérő képesség kell"
                       if dv else "normalizálás után pontosan azonos beszélgetés (pl. névcserés másolat)"))
                F.link(a.idx, b.idx, "exact_normalized", 1.0)
                done.add((a.idx, b.idx))

    n = len(recs)
    for i in range(n):
        a = recs[i]
        for j in range(i + 1, n):
            b = recs[j]
            if (a.idx, b.idx) in done:
                continue
            score = conv_pair_score(a, b, prefilter, stats)
            if score is not None and score >= GROUP_MIN:
                dv = declared_variant(a, b)
                st = similarity_status(score, False, strict)
                if st == "reject" and dv:
                    st, why = "review", "deklarált változat (közös split_group), hasonlóság a reject-határ fölött: dokumentált eltérő képesség kell"
                elif st == "reject":
                    why = "az összevont beszélgetés-hasonlóság a 0,95 határ fölött van: alapból elutasítás"
                elif st == "review":
                    why = "az összevont beszélgetés-hasonlóság a 0,90 határ fölött van: felülvizsgálat"
                else:
                    st, why = "info", "közeli változat (csoportosításra), a döntési határok alatt"
                F.add("conversation", "near_conversation" if st != "info" else "near_variant", loc_conv(a), loc_conv(b),
                      score, "összevont szerep- és pozíció-őrző karakter-arány (SequenceMatcher, autojunk=False)", st, why,
                      {"declared_variant": dv})
                F.link(a.idx, b.idx, "near_conversation", score)
                linked.add((a.idx, b.idx))
                if st != "info":
                    done.add((a.idx, b.idx))
                continue
    return done


def check_paraphrase_variants(recs, done, linked, F):
    """Heurisztika: tartalmi szó-átfedés (a szerep és a sorrend nélkül). Csak azokra a párokra fut, amelyekre a
    pozíció-őrző és az üzenet-átfedéses ellenőrzés nem adott találatot."""
    n = len(recs)
    for i in range(n):
        a = recs[i]
        if len(a.words) < PARAPHRASE_MIN_WORDS:
            continue
        for j in range(i + 1, n):
            b = recs[j]
            if (a.idx, b.idx) in done or (a.idx, b.idx) in linked or len(b.words) < PARAPHRASE_MIN_WORDS:
                continue
            jac = len(a.words & b.words) / len(a.words | b.words)
            if jac >= PARAPHRASE_MIN:
                F.add("conversation", "probable_paraphrase_variant", loc_conv(a), loc_conv(b), jac,
                      "tartalmi szó-átfedés (Jaccard, 4 karakteres töv, a szerep és a sorrend nélkül)", "review",
                      "valószínű átfogalmazott változat: a karakter-arány nem értelmezhető átfogalmazásnál, ezért felülvizsgálat",
                      {"heuristic": True})
                F.link(a.idx, b.idx, "paraphrase_heuristic", jac)
                done.add((a.idx, b.idx))


def check_message_overlap(recs, done, linked, F):
    """Azonos (normalizált) hosszabb üzenetek másik szerepben vagy másik helyen: szerepcsere / sorrendcsere."""
    index = {}
    for r in recs:
        for k, text in enumerate(r.norm):
            if len(text) >= MIN_SHARED_MESSAGE_CHARS:
                index.setdefault(text, []).append((r.idx, k))
    pairs = {}
    for text, occ in index.items():
        if len(occ) < 2:
            continue
        for x in range(len(occ)):
            for y in range(x + 1, len(occ)):
                (ia, ka), (ib, kb) = occ[x], occ[y]
                if ia == ib:
                    continue
                d = pairs.setdefault((ia, ib), {"same_pos": 0, "cross_role": 0, "same_role_other_pos": 0, "shared": 0})
                d["shared"] += 1
                ra, rb = recs[ia].roles[ka], recs[ib].roles[kb]
                if ka == kb and ra == rb:
                    d["same_pos"] += 1
                elif ra != rb:
                    d["cross_role"] += 1
                else:
                    d["same_role_other_pos"] += 1
    for (ia, ib), d in sorted(pairs.items()):
        a, b = recs[ia], recs[ib]
        if (a.idx, b.idx) in done:
            continue
        need = max(2, -(-3 * min(len(a.norm), len(b.norm)) // 5))         # a rövidebb beszélgetés üzeneteinek legalább 60%-a
        moved = d["cross_role"] + d["same_role_other_pos"]
        if d["shared"] < need or moved < max(2, -(-d["shared"] // 4)):
            continue
        if d["cross_role"] >= d["same_role_other_pos"]:
            ftype, why = "roles_swapped_messages", "az üzenetek szövege azonos, de másik szerepben szerepel (szerepcsere): nem azonos beszélgetés, de szoros szöveges átfedés"
        else:
            ftype, why = "messages_reordered", "az üzenetek szövege azonos, de másik helyen (más sorrendben vagy eltolva, pl. beszúrt váltás után) szerepel: nem azonos beszélgetés, de szoros szöveges átfedés"
        F.add("conversation", ftype, loc_conv(a), loc_conv(b), None,
              "azonos normalizált üzenetek száma (>= 20 karakter), szerep és pozíció szerint bontva", "review", why, dict(d))
        F.link(a.idx, b.idx, ftype, None)
        done.add((a.idx, b.idx))
        linked.add((a.idx, b.idx))


# ---------------------------------------------------------------------------
# minta-szintű ellenőrzés (előzménnyel együtt) és összevetés a TE-1 exporttal
# ---------------------------------------------------------------------------

def len_window(length, th):
    lo = int(length * th / (2.0 - th)) - 1
    hi = int(length * (2.0 - th) / th) + 2
    return max(lo, 0), hi


def evaluate_sample_pair(sa, sb, prefilter, strict, stats, F, recs, export_rows, run_id_map=None):
    """Egy minta-pár kiértékelése; találatot a Findings-be ír. sa/sb sorrendje rögzített (a korábbi = sa)."""
    rq = bounded_ratio(sa.q, sb.q, sa.qlen, sb.qlen, sa.qvec, sb.qvec, REVIEW_MIN, prefilter, stats)
    if rq is None:
        return
    rc = context_ratio(sa.ctx, sb.ctx)
    ra = bounded_ratio(sa.a, sb.a, sa.alen, sb.alen, sa.avec, sb.avec, REVIEW_MIN, prefilter, stats)
    exact = (sa.q == sb.q and sa.a == sb.a and sa.ctx == sb.ctx)
    both_trivial = sa.trivial and sb.trivial
    if sa.kind == "conv":
        rec_a = recs[sa.owner]
        loc_a = loc_conv(rec_a, sa.turn)
    else:
        loc_a = loc_export(sa, export_rows[sa.owner]["id"])
    if sb.kind == "conv":
        rec_b = recs[sb.owner]
        loc_b = loc_conv(rec_b, sb.turn)
    else:
        loc_b = loc_export(sb, export_rows[sb.owner]["id"])
    dv = sa.kind == "conv" and sb.kind == "conv" and declared_variant(recs[sa.owner], recs[sb.owner])
    scope = "export" if "te1" in (sa.kind, sb.kind) else "sample"
    comps = {"question": round(rq, 6), "context": round(rc, 6), "answer": None if ra is None else round(ra, 6),
             "context_kind": "üres-üres" if (not sa.ctx and not sb.ctx) else ("egyik üres" if (not sa.ctx or not sb.ctx) else "előzményes")}
    if rc >= REVIEW_MIN and ra is not None:
        score = min(rq, ra, rc)
        if both_trivial:
            if exact:
                F.add(scope, "sample_exact_trivial", loc_a, loc_b, 1.0, "pontos minta-egyezés (kérdés, válasz, előzmény), rövid szöveg",
                      "review", "triviális, pontosan ismétlődő minta (pl. köszönés): a hasonlóság nem dönt, de a pontos ismétlődés felülvizsgálandó", comps)
            return
        st = similarity_status(score, exact, strict)
        if st is None:
            return
        if st == "reject" and dv:
            st, why = "review", "deklarált változat (közös split_group): ismétlődő tanítási minta, dokumentált eltérő képesség kell"
        elif st == "reject":
            why = ("pontosan ismétlődő tanítási minta (kérdés, válasz és releváns előzmény azonos): elutasítás vagy javítás" if exact
                   else "a minta-hasonlóság (min. kérdés/válasz/előzmény) a 0,95 határ fölött van: alapból elutasítás")
        else:
            why = "a minta-hasonlóság (min. kérdés/válasz/előzmény) a 0,90 határ fölött van: felülvizsgálat"
        F.add(scope, "sample_exact" if exact else "sample_near", loc_a, loc_b, score,
              "min(kérdés, válasz, előzmény) összevont karakter-arány (SequenceMatcher, autojunk=False)", st, why, comps)
        if scope == "sample":
            F.link(recs[sa.owner].idx, recs[sb.owner].idx, "sample_overlap", score)
        return
    if sa.qlen >= MIN_PARTIAL_CHARS and sb.qlen >= MIN_PARTIAL_CHARS:
        if rc < REVIEW_MIN:
            ftype = "same_qa_different_context" if ra is not None else "same_question_different_context"
            why = ("azonos kérdés és válasz eltérő előzménnyel: részleges szövegegyezés, külön tanítási minta"
                   if ra is not None else "azonos kérdés eltérő előzménnyel: részleges szövegegyezés, nem ismétlődő tanítási minta")
        else:
            ftype, why = "same_question_context_different_answer", "azonos kérdés és előzmény eltérő válasszal: nem duplikátum, de következetlenségre utalhat"
        F.add(scope, ftype, loc_a, loc_b, rq, "kérdés-hasonlóság (összevont karakter-arány)", "info", why, comps)


def scan_samples(samples_a, samples_b, same_list, prefilter, strict, stats, F, recs, export_rows, lo_i=0, hi_i=None):
    """A kérdés-hossz ablakával párosít; same_list esetén csak a i<j párok, azonos beszélgetés kihagyva."""
    order = sorted(range(len(samples_b)), key=lambda x: (samples_b[x].qlen, x))
    lens = [samples_b[x].qlen for x in order]
    hi_i = len(samples_a) if hi_i is None else hi_i
    for i in range(lo_i, hi_i):
        sa = samples_a[i]
        if sa.qlen == 0:
            continue
        if prefilter:
            wlo, whi = len_window(sa.qlen, REVIEW_MIN)
            p0, p1 = bisect.bisect_left(lens, wlo), bisect.bisect_right(lens, whi)
            cand = order[p0:p1]
        else:
            cand = order
        for j in cand:
            if same_list and (j <= i or samples_b[j].owner == sa.owner):
                continue
            evaluate_sample_pair(sa, samples_b[j], prefilter, strict, stats, F, recs, export_rows)


def scan_shared_answers(samples_a, samples_b, same_list, prefilter, stats, F, recs, export_rows):
    """Részleges egyezés: azonos (>=0,95) hosszabb válasz eltérő kérdéssel."""
    order = sorted(range(len(samples_b)), key=lambda x: (samples_b[x].alen, x))
    lens = [samples_b[x].alen for x in order]
    for i, sa in enumerate(samples_a):
        if sa.alen < MIN_DECISION_CHARS:
            continue
        if prefilter:
            wlo, whi = len_window(sa.alen, REJECT_MIN)
            cand = order[bisect.bisect_left(lens, wlo):bisect.bisect_right(lens, whi)]
        else:
            cand = order
        for j in cand:
            sb = samples_b[j]
            if same_list and (j <= i or sb.owner == sa.owner):
                continue
            if sb.alen < MIN_DECISION_CHARS:
                continue
            ra = bounded_ratio(sa.a, sb.a, sa.alen, sb.alen, sa.avec, sb.avec, REJECT_MIN, prefilter, stats)
            if ra is None:
                continue
            rq = bounded_ratio(sa.q, sb.q, sa.qlen, sb.qlen, sa.qvec, sb.qvec, REVIEW_MIN, False, Stats())
            if rq is not None:
                continue                       # azonos kérdés esetét a minta-szintű ellenőrzés már kezelte
            scope = "export" if "te1" in (sa.kind, sb.kind) else "sample"
            la = loc_conv(recs[sa.owner], sa.turn) if sa.kind == "conv" else loc_export(sa, export_rows[sa.owner]["id"])
            lb = loc_conv(recs[sb.owner], sb.turn) if sb.kind == "conv" else loc_export(sb, export_rows[sb.owner]["id"])
            F.add(scope, "shared_answer_different_question", la, lb, ra, "válasz-hasonlóság (összevont karakter-arány)", "info",
                  "a válasz szövege (>= 0,95) más kérdéshez is szerepel: részleges szövegegyezés, nem ismétlődő tanítási minta", None)


# ---------------------------------------------------------------------------
# csoportosítás
# ---------------------------------------------------------------------------

def add_structural_links(recs, F):
    by_persona, by_group = {}, {}
    for r in recs:
        if r.persona:
            by_persona.setdefault(r.persona, []).append(r)
        if r.group:
            by_group.setdefault(r.group, []).append(r)
    for persona, members in sorted(by_persona.items()):
        for k in range(1, len(members)):
            F.link(members[0].idx, members[k].idx, "persona", None)
        if len(members) > PERSONA_MAX:
            F.add("group", "persona_reuse_exceeds_limit", loc_conv(members[0]), loc_conv(members[-1]), None,
                  f"ugyanaz a persona ({persona}) {len(members)} beszélgetésben", "review",
                  f"egy persona legfeljebb {PERSONA_MAX} beszélgetésben szerepelhet (terv 4.3)", {"persona": persona, "members": [m.id for m in members]})
    for group, members in sorted(by_group.items()):
        for k in range(1, len(members)):
            F.link(members[0].idx, members[k].idx, "declared_group", None)
        if len(members) > DECLARED_GROUP_MAX:
            F.add("group", "declared_group_too_large", loc_conv(members[0]), loc_conv(members[-1]), None,
                  f"a deklarált csoport ({group}) {len(members)} beszélgetésből áll", "review",
                  f"a tervezett változat-csoport 2-{DECLARED_GROUP_MAX} elemű", {"split_group": group, "members": [m.id for m in members]})


def build_groups(recs, edges, F):
    parent = list(range(len(recs)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for ia, ib, _t, _s in edges:
        ra, rb = find(ia), find(ib)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)
    members = {}
    for r in recs:
        members.setdefault(find(r.idx), []).append(r)
    groups = {}
    for root, ms in members.items():
        ms.sort(key=lambda r: r.id)
        gid = "mtg_" + ms[0].id
        while gid in groups:                       # duplikált azonosítók esetén (duplicate_id) az ütközés feloldása
            gid += "+" + str(ms[0].idx)
        ids = {m.idx for m in ms}
        gedges = sorted(({"a": recs[a].id, "b": recs[b].id, "link": t, "score": s} for a, b, t, s in edges if a in ids and b in ids),
                        key=lambda e: (e["a"], e["b"], e["link"]))
        declared = sorted({m.group for m in ms if m.group})
        groups[gid] = {"members": [m.id for m in ms], "size": len(ms), "edges": gedges, "declared_split_groups": declared,
                       "_idx": sorted(ids)}
    # ugyanaz az azonosító több rekordon (duplicate_id): a csoportkulcs ütközik -> egyértelműsítés
    for gid, g in groups.items():
        if g["size"] > MAX_GROUP_SIZE:
            weakest = sorted((e for e in g["edges"] if e["score"] is not None), key=lambda e: e["score"])[:3]
            F.add("group", "group_too_large", {"source": "group", "record": gid}, {"source": "group", "record": gid}, None,
                  "egyszeres kötésű csoportosítás", "review",
                  f"a csoport {g['size']} tagú (> {MAX_GROUP_SIZE}): a láncolt hasonlóság összevonhatott nem közeli beszélgetéseket; a leggyengébb élek jelölve",
                  {"members": g["members"], "weakest_edges": weakest})
        if len(g["declared_split_groups"]) > 1:
            F.add("group", "declared_groups_merged", {"source": "group", "record": gid}, {"source": "group", "record": gid}, None,
                  "deklarált split_group összevetés", "info",
                  "a számított csoport több deklarált split_group-ot egyesít: az MT-2 a SZÁMÍTOTT csoportot használja",
                  {"declared_split_groups": g["declared_split_groups"], "members": g["members"]})
    gid_by_idx = {}
    for gid, g in groups.items():
        for rid_idx in g["_idx"]:
            gid_by_idx[rid_idx] = gid
        del g["_idx"]
    return groups, gid_by_idx


# ---------------------------------------------------------------------------
# kivételek
# ---------------------------------------------------------------------------

class ExceptionsError(Exception):
    exit_code = EXIT_EXCEPTIONS


def apply_exceptions(findings, entries, known_ids):
    """Dokumentált kivételek: a megadott pár megadott típusú találatát `accepted_with_exception` státuszra állítja.
    duplicate_id és a nyers pontos beszélgetés-másolat nem menthető fel. Elavult/érvénytelen bejegyzés hiba."""
    applied = []
    for n, e in enumerate(entries):
        where = f"kivétel #{n + 1}"
        if not isinstance(e, dict) or set(e) - {"a", "b", "waive", "reason", "reviewer"} or not {"a", "b", "waive", "reason"} <= set(e):
            raise ExceptionsError(f"{where}: a bejegyzés kulcsai: a, b, waive, reason (opcionális: reviewer)")
        if not isinstance(e["reason"], str) or len(e["reason"].strip()) < 15:
            raise ExceptionsError(f"{where}: a reason legalább 15 karakteres, konkrét indoklás kell")
        if not isinstance(e["waive"], list) or not e["waive"] or not all(isinstance(t, str) for t in e["waive"]):
            raise ExceptionsError(f"{where}: a waive nem üres típuslista")
        if "*" in e["waive"] and len(e["waive"]) > 1:
            raise ExceptionsError(f"{where}: a \"*\" nem keverhető konkrét típusokkal")
        bad = sorted(set(e["waive"]) & NON_WAIVABLE)
        if bad:
            raise ExceptionsError(f"{where}: nem menthető fel: {', '.join(bad)}")
        for side in ("a", "b"):
            if e[side] not in known_ids:
                raise ExceptionsError(f"{where}: ismeretlen azonosító: {e[side]!r} (elavult kivétel?)")
        pair = {e["a"], e["b"]}
        for ftype in e["waive"]:
            hits = [f for f in findings if (f["type"] == ftype or (ftype == "*" and f["type"] not in NON_WAIVABLE))
                    and {f["a"]["record"], f["b"]["record"]} == pair and f["status"] in BLOCKING]
            if not hits:
                raise ExceptionsError(f"{where}: nincs blokkoló '{ftype}' találat a(z) {e['a']} - {e['b']} párra (elavult vagy téves kivétel)")
            for f in hits:
                f["status_before_exception"] = f["status"]
                f["status"] = "accepted_with_exception"
                f["exception"] = {"reason": e["reason"].strip(), "reviewer": e.get("reviewer")}
            by_type = {}
            for f in hits:
                by_type[f["type"]] = by_type.get(f["type"], 0) + 1
            for t, n_hits in sorted(by_type.items()):
                applied.append({"a": e["a"], "b": e["b"], "type": t, "findings": n_hits, "waive_token": ftype})
    return applied


# ---------------------------------------------------------------------------
# futtatás (API) és jelentés
# ---------------------------------------------------------------------------

def run_dedupe(recs, export_rows=None, prefilter=True, strict=False, exceptions=None):
    """A teljes ellenőrzés a betöltött rekordokon. recs: Rec lista (idx = sorszám), export_rows: TE-1 sorok."""
    t0 = time.perf_counter()
    timing = {}
    F, stats = Findings(), Stats()
    export_rows = export_rows or []
    export_ids = {r["id"] for r in export_rows}
    check_duplicate_ids(recs, export_ids, F)

    t = time.perf_counter()
    conv_stats = Stats()
    linked = set()
    done = check_conversations(recs, prefilter, strict, F, conv_stats, linked)
    check_message_overlap(recs, done, linked, F)
    check_paraphrase_variants(recs, done, linked, F)
    timing["conversation_level"] = round(time.perf_counter() - t, 3)

    t = time.perf_counter()
    cs = [s for r in recs for s in build_conv_samples(r)]
    es = build_export_samples(export_rows)
    timing["sample_preparation"] = round(time.perf_counter() - t, 3)

    t = time.perf_counter()
    sample_stats = Stats()
    scan_samples(cs, cs, True, prefilter, strict, sample_stats, F, recs, export_rows)
    if es:
        scan_samples(cs, es, False, prefilter, strict, sample_stats, F, recs, export_rows)
    timing["sample_level"] = round(time.perf_counter() - t, 3)

    t = time.perf_counter()
    ans_stats = Stats()
    scan_shared_answers(cs, cs, True, prefilter, ans_stats, F, recs, export_rows)
    if es:
        scan_shared_answers(cs, es, False, prefilter, ans_stats, F, recs, export_rows)
    timing["shared_answer_scan"] = round(time.perf_counter() - t, 3)

    add_structural_links(recs, F)
    groups, gid_by_idx = build_groups(recs, F.edges, F)
    applied = []
    if exceptions:
        applied = apply_exceptions(F.items, exceptions, {r.id for r in recs} | export_ids)

    order = {"reject": 0, "review": 1, "accepted_with_exception": 2, "info": 3}
    F.items.sort(key=lambda f: (order.get(f["status"], 9), f["scope"], f["type"], f["a"]["record"], f["b"]["record"],
                                f["a"].get("turn") if f["a"].get("turn") is not None else -1,
                                f["b"].get("turn") if f["b"].get("turn") is not None else -1))
    for n, f in enumerate(F.items, 1):
        f["finding_id"] = "f%04d" % n

    blocking, conv_blocked = {}, set()
    for f in F.items:
        if f["status"] in BLOCKING:
            for side in ("a", "b"):
                if f[side]["source"] == "conversation":
                    blocking.setdefault((f[side]["file"], f[side]["line"]), []).append(f["finding_id"])
                    if f["scope"] == "conversation":
                        conv_blocked.add((f[side]["file"], f[side]["line"]))
    records = []
    for r in recs:
        key = (r.file, r.line)
        b = blocking.get(key, [])
        records.append({"record": r.id, "file": r.file, "line": r.line, "group_id": gid_by_idx.get(r.idx),
                        "conversation_decision": "blocked" if key in conv_blocked else "no_conversation_level_block",
                        "progression": "blocked" if b else "clear_of_duplicate_findings",
                        "blocking_findings": sorted(set(b))})
    in_groups = sum(1 for g in groups.values() if g["size"] >= 2 for _ in g["members"])
    by_status, by_type = {}, {}
    for f in F.items:
        by_status[f["status"]] = by_status.get(f["status"], 0) + 1
        k = f["type"] + "/" + f["status"]
        by_type[k] = by_type.get(k, 0) + 1
    counters = {"conversation_pairs": conv_stats.d, "sample_pairs": sample_stats.d, "shared_answer_pairs": ans_stats.d,
                "conversation_records": len(recs), "conversation_samples": len(cs), "export_samples": len(es)}
    timing["total"] = round(time.perf_counter() - t0, 3)
    summary = {
        "records": len(recs), "findings_total": len(F.items), "findings_by_status": dict(sorted(by_status.items())),
        "findings_by_type_status": dict(sorted(by_type.items())),
        "blocked_records": sum(1 for r in records if r["progression"] == "blocked"),
        "clear_records": sum(1 for r in records if r["progression"] != "blocked"),
        "groups": len(groups), "groups_with_2_or_more": sum(1 for g in groups.values() if g["size"] >= 2),
        "largest_group": max((g["size"] for g in groups.values()), default=0),
        "records_in_multi_member_groups": in_groups,
        "variant_share": round(in_groups / len(recs), 4) if recs else 0.0,
        "variant_share_plan_limit": VARIANT_SHARE_PLAN,
        "variant_share_over_plan": bool(recs and in_groups / len(recs) > VARIANT_SHARE_PLAN),
        "exceptions_applied": applied,
    }
    return {"findings": F.items, "groups": groups, "records": records, "summary": summary, "counters": counters,
            "timing_seconds": timing}


# ---------------------------------------------------------------------------
# bemenet, kimenet
# ---------------------------------------------------------------------------

class InputFileError(Exception):
    exit_code = EXIT_INPUT


class InvalidRecordsError(Exception):
    exit_code = EXIT_INVALID


class ChangedInputError(Exception):
    exit_code = EXIT_CHANGED_DURING


def load_conversation_files(paths, mode, bank, masker):
    recs, infos, invalid = [], [], []
    for file_idx, path in enumerate(paths):
        if not os.path.isfile(path):
            raise InputFileError(f"A beszélgetés-fájl nem található: {path}")
        raw = te1.read_bytes(path)
        info = {"path": te1.rel_path(path), "sha256": te1.sha256_bytes(raw), "bytes": len(raw), "records": 0}
        for line_no, line in enumerate(raw.split(b"\n"), 1):
            line = line[:-1] if line.endswith(b"\r") else line
            if not line.strip():
                continue
            try:
                obj = json.loads(line.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise InputFileError(f"Hibás JSON sor: {te1.rel_path(path)}:{line_no} ({exc})")
            if not isinstance(obj, dict) or not isinstance(obj.get("id"), str):
                raise InputFileError(f"A sor nem beszélgetés-rekord (nincs id): {te1.rel_path(path)}:{line_no}")
            errs = [i for i in mt1.validate_record(obj, mode, bank) if i.severity == "error"]
            if errs:
                invalid.append(f"{te1.rel_path(path)}:{line_no} {obj['id']}: " + ", ".join(sorted({e.code for e in errs})))
                continue
            recs.append(make_rec(len(recs), obj, te1.rel_path(path), file_idx, line_no, te1.sha256_bytes(line), masker))
            info["records"] += 1
        infos.append(info)
    if invalid:
        raise InvalidRecordsError("Nem turns-validált rekord(ok), a duplikáció-ellenőrzés nem értelmezhető rajtuk (MT-1): "
                                  + "; ".join(invalid[:10]) + (" ..." if len(invalid) > 10 else ""))
    if not recs:
        raise InputFileError("A bemeneti fájlokban nincs rekord.")
    return recs, infos


def file_sha_map(paths):
    return {p: te1.sha256_file(p) for p in paths}


def write_tsv(path, header, rows):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\t".join(header) + "\n")
        for r in rows:
            f.write("\t".join("" if v is None else str(v) for v in r) + "\n")


def run_from_files(conv_paths, out_dir, mode, te1_export=None, exceptions_path=None, name_bank_path=None,
                   run_name=None, prefilter=True, name_normalization=True, strict=False):
    for p in conv_paths:
        if not os.path.isfile(p):
            raise InputFileError(f"A beszélgetés-fájl nem található: {p}")
    try:
        out_abs = None
        for p in conv_paths:
            out_abs = te1.check_out_dir(out_dir, os.path.dirname(os.path.abspath(p)))
        if te1_export:
            out_abs = te1.check_out_dir(out_dir, te1_export)
    except te1.OutputPathError as exc:
        raise OutputError(str(exc))
    bank_path = name_bank_path or mt1.DEFAULT_NAME_BANK
    try:
        bank = mt1.load_name_bank(bank_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise InputFileError(f"A névtár nem olvasható: {exc}")
    masker = NameMasker(bank) if name_normalization else None
    before = file_sha_map(conv_paths)
    recs, infos = load_conversation_files(conv_paths, mode, bank, masker)

    export_rows, export_info = [], None
    if te1_export:
        try:
            manifest, manifest_sha, export_rows = te2.load_te1_export(te1_export)
        except te2.Te1ExportError as exc:
            raise Te1InputError(str(exc))
        excl = manifest.get("exclusion_list", {}).get("entries", [])
        export_info = {"run_dir": te1.rel_path(te1_export), "manifest_sha256": manifest_sha,
                       "export_file_sha256": manifest["outputs"]["export_file"]["sha256"],
                       "index_file_sha256": manifest["outputs"]["index_file"]["sha256"],
                       "rows": len(export_rows), "rows_excluded_by_te1": len(excl),
                       "te1_git_commit": manifest.get("git_commit")}

    exceptions, exc_info = None, None
    if exceptions_path:
        try:
            raw = te1.read_bytes(exceptions_path)
            exceptions = json.loads(raw.decode("utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ExceptionsError(f"A kivétel-fájl nem olvasható/érvénytelen JSON: {exc}")
        if not isinstance(exceptions, list):
            raise ExceptionsError("A kivétel-fájl JSON lista kell legyen.")
        exc_info = {"path": te1.rel_path(exceptions_path), "sha256": te1.sha256_bytes(raw), "entries": len(exceptions)}

    result = run_dedupe(recs, export_rows, prefilter=prefilter, strict=strict, exceptions=exceptions)
    if file_sha_map(conv_paths) != before:
        raise ChangedInputError("A bemeneti beszélgetés-fájl(ok) a futás közben megváltoztak (sha256 eltérés).")

    stamp = run_name or datetime.datetime.now(datetime.timezone.utc).strftime("mt3_%Y%m%dT%H%M%SZ")
    if not re.match(r"^[A-Za-z0-9._-]+$", stamp):
        raise OutputError(f"Érvénytelen futásnév: {stamp!r}")
    run_dir = os.path.join(out_abs, stamp)
    if os.path.exists(run_dir):
        raise OutputError(f"A futás-mappa már létezik, nem írom felül: {run_dir}")
    os.makedirs(run_dir)

    report = {
        "tool": "tools/multiturn_dedupe.py", "tool_version": TOOL_VERSION, "status": "completed",
        "created_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "git_commit": te1.git_commit(), "python": sys.version.split()[0],
        "config": {
            "mode": mode, "decision_rules": {"exact": "reject", "review_min": REVIEW_MIN, "reject_min": REJECT_MIN,
                                             "comparison": ">" if strict else ">=", "handbook_strict": strict},
            "grouping": {"group_min": GROUP_MIN, "paraphrase_min": PARAPHRASE_MIN, "max_group_size": MAX_GROUP_SIZE,
                         "linkage": "single (tranzitív lezárás)", "group_id": "mtg_<a csoport lexikografikusan legkisebb rekordazonosítója>"},
            "min_decision_chars": MIN_DECISION_CHARS,
            "similarity": "difflib.SequenceMatcher(None, a, b, autojunk=False) egyező-karakter arány, 2*M/(|a|+|b|); a = a korábbi rekord",
            "normalization": {"nfc": True, "typographic_quotes_dashes": True, "list_markers_removed": True, "casefold": True,
                              "punctuation_to_space": True, "name_masking": bool(name_normalization)},
            "prefilter": {"enabled": prefilter, "guarantee": "hossz- és karakter-multiset felső korlát: bizonyítottan pontos, csak a küszöb alatti párokat hagyja ki (nem közelítő)"},
        },
        "inputs": {"conversation_files": infos, "te1_export": export_info,
                   "name_bank": {"path": te1.rel_path(bank_path), "sha256": te1.sha256_file(bank_path)}, "exceptions": exc_info},
        "timing_seconds": result["timing_seconds"], "counters": result["counters"], "summary": result["summary"],
        "findings": result["findings"], "groups": result["groups"], "records": result["records"],
        "limitations": LIMITATIONS, "disclaimer": DISCLAIMER,
        "training_ready": False, "content_verified": False,
    }
    partial = os.path.join(run_dir, "dedupe_report.json.partial")
    with open(partial, "w", encoding="utf-8", newline="\n") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
        f.write("\n")
    write_tsv(os.path.join(run_dir, "findings.tsv"),
              ["finding_id", "status", "scope", "type", "a_record", "a_turn", "b_record", "b_turn", "score", "at_boundary", "reason"],
              [(f["finding_id"], f["status"], f["scope"], f["type"], f["a"]["record"], f["a"].get("turn"), f["b"]["record"],
                f["b"].get("turn"), f["score"], f["at_boundary"], f["reason"]) for f in result["findings"]])
    write_tsv(os.path.join(run_dir, "record_status.tsv"), ["record", "group_id", "progression", "conversation_decision", "blocking_findings"],
              [(r["record"], r["group_id"], r["progression"], r["conversation_decision"], ",".join(r["blocking_findings"])) for r in result["records"]])
    with open(os.path.join(run_dir, "groups.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump({"tool_version": TOOL_VERSION, "inputs": infos, "group_id_rule": report["config"]["grouping"]["group_id"],
                   "groups": result["groups"]}, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(partial, os.path.join(run_dir, "dedupe_report.json"))
    report["run_dir"] = run_dir
    return report


class OutputError(Exception):
    exit_code = EXIT_OUTPUT


class Te1InputError(Exception):
    exit_code = EXIT_TE1


def verify_report(report_path):
    """A jelentésben rögzített bemenetek (fájlok, TE-1 export, névtár, kivételek) ellenőrzőösszegének újraellenőrzése."""
    with open(report_path, "r", encoding="utf-8") as f:
        rep = json.load(f)
    problems = []

    def check(rel, want, label):
        path = rel if os.path.isabs(rel) else os.path.join(te1.REPO_ROOT, rel)
        if not os.path.isfile(path):
            problems.append(f"{label}: hiányzik: {rel}")
        elif te1.sha256_file(path) != want:
            problems.append(f"{label}: megváltozott: {rel}")

    for info in rep["inputs"]["conversation_files"]:
        check(info["path"], info["sha256"], "beszélgetés-fájl")
    exp = rep["inputs"].get("te1_export")
    if exp:
        base = exp["run_dir"] if os.path.isabs(exp["run_dir"]) else os.path.join(te1.REPO_ROOT, exp["run_dir"])
        for name, key in ((te1.MANIFEST_FILE, "manifest_sha256"), (te1.EXPORT_FILE, "export_file_sha256"), (te1.INDEX_FILE, "index_file_sha256")):
            check(os.path.join(base, name), exp[key], "TE-1 export")
    check(rep["inputs"]["name_bank"]["path"], rep["inputs"]["name_bank"]["sha256"], "névtár")
    if rep["inputs"].get("exceptions"):
        check(rep["inputs"]["exceptions"]["path"], rep["inputs"]["exceptions"]["sha256"], "kivétel-fájl")
    return problems


def _main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description="MT-3: többfordulós beszélgetések duplikáció-ellenőrzése és csoportosítása "
                                            "(NEM elfogadás, NEM training-ready).")
    p.add_argument("--mode", choices=["dataset", "fixture"])
    p.add_argument("--conversations", nargs="+", help="Beszélgetés-fájl(ok) (turns-validált bemenet, MT-1).")
    p.add_argument("--out-dir", help="Kimeneti szülőmappa (a futás új almappába kerül).")
    p.add_argument("--te1-export", default=None, help="TE-1 export futás-mappa az egyfordulós példákkal való összevetéshez.")
    p.add_argument("--exceptions", default=None, help="Dokumentált kivételek JSON fájlja.")
    p.add_argument("--name-bank", default=None)
    p.add_argument("--run-name", default=None)
    p.add_argument("--no-prefilter", action="store_true", help="Teljes összehasonlítás előszűrés nélkül (referencia mód).")
    p.add_argument("--no-name-normalization", action="store_true")
    p.add_argument("--handbook-strict", action="store_true", help="A 0,90/0,95 határ szó szerinti '>' értelmezése (alapból '>=').")
    p.add_argument("--verify-report", default=None, help="Egy korábbi jelentés bemeneteinek újraellenőrzése.")
    a = p.parse_args(argv)

    if a.verify_report:
        try:
            problems = verify_report(a.verify_report)
        except (OSError, json.JSONDecodeError, KeyError) as exc:
            print(f"HIBA: a jelentés nem olvasható: {exc}", file=sys.stderr)
            return EXIT_INPUT
        if problems:
            for pr in problems:
                print(f"MEGVÁLTOZOTT BEMENET: {pr}", file=sys.stderr)
            return EXIT_CHANGED_AFTER
        print("A jelentés bemenetei változatlanok (ellenőrzőösszegek egyeznek).")
        return 0
    if not (a.mode and a.conversations and a.out_dir):
        p.error("--mode, --conversations és --out-dir kötelező (vagy --verify-report)")

    try:
        rep = run_from_files(a.conversations, a.out_dir, a.mode, a.te1_export, a.exceptions, a.name_bank, a.run_name,
                             not a.no_prefilter, not a.no_name_normalization, a.handbook_strict)
    except (InputFileError, InvalidRecordsError, Te1InputError, ExceptionsError, OutputError, ChangedInputError) as exc:
        print(f"HIBA ({type(exc).__name__}): {exc}", file=sys.stderr)
        return exc.exit_code
    s = rep["summary"]
    print(f"MT-3 futás kész: {rep['run_dir']}")
    print(f"Rekordok: {s['records']} | találat: {s['findings_total']} {s['findings_by_status']} | blokkolt rekord: {s['blocked_records']} "
          f"| csoport: {s['groups']} (2+ tagú: {s['groups_with_2_or_more']}, legnagyobb: {s['largest_group']}) | idő: {rep['timing_seconds']['total']} mp")
    for f in rep["findings"]:
        if f["status"] in BLOCKING:
            print(f"  {f['status'].upper()} {f['finding_id']} {f['type']} {f['a']['record']} - {f['b']['record']} "
                  f"(pontszám: {f['score']}): {f['reason']}")
    print(DISCLAIMER)
    return 1 if s["blocked_records"] or any(f["status"] in BLOCKING for f in rep["findings"]) else 0


if __name__ == "__main__":
    sys.exit(_main())
