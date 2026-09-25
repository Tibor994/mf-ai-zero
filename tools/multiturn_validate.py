"""
MF-AI-Zero - MT-1: a többfordulós (`turns`) beszélgetés-formátum külön ellenőrzője.

CÉL: a `docs/MULTITURN_FORMAT.md` (MT-0) szerinti beszélgetés-rekordok ellenőrzése MINDEN
üzenetre, a közbenső fordulókra is. A régi `tools/dataset_validate.py` erre nem alkalmas:
nincs kategória-fehérlista, az extra mezőket nem utasítja el, és csak a 9 régi mezőt látja
(instruction = az első user-üzenet, output = az utolsó assistant-üzenet), így egy közbenső
üzenetben lévő személyes adat vagy hiba észrevétlen maradna. Az itteni eredmény két,
KÜLÖN állapotot mutat, és egyik sem helyettesíti a másikat:
    legacy_validator_compatible - a 9 régi mezőre a régi validátor átengedi (csak szerkezeti kompatibilitás)
    turns_validated             - az MT-1 minden szabálya hibátlan (nincs `error` súlyú probléma)
A `turns_validated` sem tartalmi ellenőrzés, és nem training-ready állapot.

MIT VIZSGÁL (kód -> hatókör):
  szerkezet: ismeretlen/hiányzó mező, id-minta (mód szerint), category, tags, difficulty, source,
    turns (lista, szerep-kulcsok, user->assistant váltakozás, első=user, utolsó=assistant,
    3-8 váltás), üzenet-szöveg (nem üres, nyírt, nincs újsor/vezérlőkarakter, hosszkorlát),
    származtatott mezők (instruction/input/output) egyezése, meta (család, készségek,
    n_exchanges, split_group, persona, domain, depends, fixture-jelölés).
  tartalom, ÜZENETENKÉNT (közbenső fordulók is): a projekt meglévő szűrései a
    dataset_validate.validate_row importálásával (személyes adat, veszélyes tartalom, angol
    keveredés, torz szó, ismétlődő karakter, túlállítás; az assistant-üzenet 3 szó alatt),
    + saját szabályok: MF-AI/Nexora említés, URL/domain, 8+ jegyű számsor, User:/AI: felirat
    a szövegben, névtár (nem jóváhagyott keresztnév, teljes név-minta, nem deklarált név).
  figyelmeztetések (nem blokkolók): mid-mondat nagybetűs szó átolvasásra, ismétlődő
    assistant-üzenet, deklarált de nem szereplő név, a család várható `depends` bejegyzése.

MÓDOK: `dataset` (valódi csomag: id `multiturn_NNNN`, meta.fixture nem lehet igaz) és
`fixture` (tesztadat: id `mtfx_...`, meta.fixture igaz kell). A tesztadat így nem keveredhet
az 1000 beszélgetéses csomagba.

Használat:
    python tools/multiturn_validate.py <fájl.jsonl> [...] --mode dataset|fixture
        [--name-bank <json>] [--json <riport.json>]

Kilépési kódok: 0 minden rekord turns-validált; 1 van hibás rekord/fájlhiba; 2 argumentum- vagy fájlhiba.
A tesztadat kicsi és mesterséges; a valódi 1000 beszélgetés még nem létezik.
"""

import argparse
import json
import os
import re
import sys
import unicodedata

import dataset_validate as legacy   # a régi validátor: csak importálva, módosítás nélkül

TOOL_VERSION = "mt1-1.0"
TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_NAME_BANK = os.path.join(TOOLS_DIR, "multiturn_name_bank.json")

TOP_FIELDS = ["id", "category", "instruction", "input", "output", "tags", "difficulty",
              "quality_notes", "source", "turns", "meta"]
FAMILIES = {
    "F1": "elozmeny_koveteles", "F2": "visszautalas", "F3": "pontositas", "F4": "felhasznaloi_javitas",
    "F5": "valtozo_keres", "F6": "temavaltas", "F7": "temavaltas_visszateres", "F8": "tobblepeses_feladat",
    "F9": "bizonytalansag_tobbfordulo",
}
SKILLS = set(FAMILIES.values())
DOMAINS = {"vasarlas", "utazas", "fozes", "tanulas", "munka", "otthon", "egeszseg_sport", "technologia",
           "szabadido", "ugyintezes"}
META_REQUIRED = ["family", "skills", "n_exchanges", "split_group", "persona", "persona_names", "domain", "depends"]
META_OPTIONAL = ["register", "user_typos", "sensitive_area", "fixture"]
REQUIRED_TAG_PREFIX = ["magyar", "instruction_core", "tobbfordulos"]
FAMILIES_EXPECTING_DEPENDS = {"F1", "F2", "F4", "F5", "F7", "F8"}

MIN_EXCHANGES, MAX_EXCHANGES = 3, 8
USER_MAX_CHARS, ASSISTANT_MAX_CHARS = 300, 600

ID_DATASET_RE = re.compile(r"^multiturn_[0-9]{4}$")
ID_FIXTURE_RE = re.compile(r"^mtfx_[a-z0-9_]+$")
GROUP_RE = re.compile(r"^g[0-9]{4}$")
PERSONA_RE = re.compile(r"^p[0-9]{3}$")
TAG_RE = re.compile(r"^[a-z0-9_]+$")
LABEL_RE = re.compile(r"(?i)(?<![a-z0-9])(?:user|ai)\s*:")
IDENTITY_RE = re.compile(r"(?i)mf[\s-]?ai|nexora|nextora")
URL_RE = re.compile(r"(?i)(?:https?://|www\.|\b[a-z0-9-]+\.(?:hu|com|org|net|eu|io|info)\b)")
LONG_DIGITS_RE = re.compile(r"\d{8,}")
TOKEN_RE = re.compile(r"[^\W\d_]+")

# jelölt nevek ragozott alakjai (a végződések szűk listája; ez NEM teljes magyar morfológia)
NAME_SUFFIXES = {
    "t", "ot", "at", "et", "öt", "nak", "nek", "val", "vel", "tal", "tel", "rel", "ral", "mal", "mel",
    "sal", "sel", "lal", "lel", "ról", "ről", "tól", "től", "hoz", "hez", "höz", "ban", "ben", "ba", "be",
    "on", "en", "ön", "n", "ra", "re", "ig", "ért", "ként", "é", "ék", "nál", "nél", "ból", "ből",
}
LENGTHEN = {"a": "á", "e": "é"}

CONTENT_IGNORED_FOR_USER = {"output_too_short", "output_too_long"}


class Issue:
    __slots__ = ("severity", "code", "path", "message")

    def __init__(self, severity, code, path, message):
        self.severity, self.code, self.path, self.message = severity, code, path, message

    def to_dict(self):
        return {"severity": self.severity, "code": self.code, "path": self.path, "message": self.message}

    def __repr__(self):
        return f"{self.severity}:{self.code}@{self.path}"


def load_name_bank(path=DEFAULT_NAME_BANK):
    with open(path, encoding="utf-8") as f:
        bank = json.load(f)
    for key in ("approved_given_names", "blocked_given_names", "blocked_surnames", "allowed_proper_nouns"):
        if not isinstance(bank.get(key), list) or not all(isinstance(x, str) and x for x in bank[key]):
            raise ValueError(f"A névtár {key!r} listája hibás: {path}")
    return bank


# ---------------------------------------------------------------------------
# névfelismerés (biztonsági háló, nem bizonyíték)
# ---------------------------------------------------------------------------

def _name_matches(token, name):
    if token == name:
        return True
    stems = [name]
    if name[-1] in LENGTHEN:
        stems.append(name[:-1] + LENGTHEN[name[-1]])
    return any(token.startswith(stem) and token[len(stem):] in NAME_SUFFIXES for stem in stems)


def _best_match(token, groups):
    """groups: [(kind, [names])] elsőbbségi sorrendben; a leghosszabb egyező név nyer."""
    best = None
    for kind, names in groups:
        for name in names:
            if _name_matches(token, name) and (best is None or len(name) > len(best[1])):
                best = (kind, name)
    return best


def _sentence_initial(text, pos):
    prev = text[:pos].rstrip()
    return (not prev) or prev[-1] in ".!?…:;„\"”“(»«-–—"


def check_names(text, bank, declared):
    """Visszaad (errors, warnings, used_approved) - errors/warnings: [(code, message)]."""
    approved = bank["approved_given_names"]
    groups = [("approved", approved), ("blocked_given", bank["blocked_given_names"]),
              ("surname", bank["blocked_surnames"]), ("allowed", bank["allowed_proper_nouns"])]
    errors, warnings, used = [], [], set()
    toks = []
    for m in TOKEN_RE.finditer(text):
        tok = m.group(0)
        if len(tok) < 2 or not tok[0].isupper() or tok.isupper():
            toks.append(None)
            continue
        toks.append((m.start(), m.end(), tok, _best_match(tok, groups)))
    for item in toks:
        if item is None:
            continue
        start, _end, tok, match = item
        if match is None:
            if not _sentence_initial(text, start):
                warnings.append(("capitalized_token_review", f"nagybetűs szó mondat közben, átolvasásra: {tok!r}"))
        elif match[0] == "approved":
            used.add(match[1])
            if match[1] not in declared:
                errors.append(("name_not_declared", f"jóváhagyott, de nem deklarált név a meta.persona_names-ben: {tok!r}"))
        elif match[0] == "blocked_given":
            errors.append(("name_not_approved", f"nem jóváhagyott keresztnév: {tok!r}"))
    prev = None
    for item in toks:
        if item is not None and prev is not None:
            (s1, e1, t1, m1), (s2, e2, t2, m2) = prev, item
            kinds = {m1[0] if m1 else None, m2[0] if m2 else None}
            if text[e1:s2] == " " and "surname" in kinds and kinds & {"approved", "blocked_given"}:
                errors.append(("full_name_pattern", f"teljes név-minta (keresztnév + vezetéknév): {t1} {t2}"))
        prev = item
    return errors, warnings, used


# ---------------------------------------------------------------------------
# rekord-ellenőrzés
# ---------------------------------------------------------------------------

def _is_int(x):
    return isinstance(x, int) and not isinstance(x, bool)


def _forbidden_char(text):
    for ch in text:
        if unicodedata.category(ch) in ("Cc", "Zl", "Zp"):
            return ch
    return None


def _legacy_content_issues(instruction, output, quality_notes="rendben"):
    row = {"id": "mt#msg", "category": "multiturn", "instruction": instruction, "input": "", "output": output,
           "tags": [], "difficulty": "easy", "quality_notes": quality_notes, "source": "mt1"}
    return legacy.validate_row(row, 1, set())


def check_depends(depends, n_turns, issues):
    if not isinstance(depends, list):
        issues.append(Issue("error", "meta_depends_not_list", "meta.depends", "a depends nem lista"))
        return
    seen = set()
    for k, d in enumerate(depends):
        p = f"meta.depends[{k}]"
        if not isinstance(d, dict) or set(d) != {"turn", "on", "depth"}:
            issues.append(Issue("error", "meta_depends_entry", p, "a bejegyzés pontosan a turn/on/depth kulcsokat tartalmazza"))
            continue
        t, on, depth = d["turn"], d["on"], d["depth"]
        if not _is_int(t) or t < 0 or t >= n_turns or t % 2 == 0:
            issues.append(Issue("error", "meta_depends_turn", p, f"a turn ({t!r}) nem érvényes assistant-üzenet index"))
            continue
        if t in seen:
            issues.append(Issue("error", "meta_depends_duplicate_turn", p, f"a turn ({t}) többször szerepel"))
        seen.add(t)
        if (not isinstance(on, list) or not on or not all(_is_int(j) for j in on) or len(set(on)) != len(on)
                or any(j < 0 or j >= t for j in on)):
            issues.append(Issue("error", "meta_depends_on", p, "az on nem üres, egyedi, a turn előtti indexek listája"))
            continue
        want = t // 2 - min(j // 2 for j in on)
        if not _is_int(depth) or depth < 1 or depth != want:
            issues.append(Issue("error", "meta_depends_depth", p,
                                f"a depth ({depth!r}) nem egyezik a számítottal ({want}); előzmény-függés legalább 1 váltásnyi kell"))


def validate_record(rec, mode, bank):
    """Egy rekord összes ellenőrzése. Visszaad: list[Issue]."""
    issues = []
    add = lambda sev, code, path, msg: issues.append(Issue(sev, code, path, msg))  # noqa: E731
    if mode not in ("dataset", "fixture"):
        raise ValueError("mode: 'dataset' vagy 'fixture'")
    if not isinstance(rec, dict):
        return [Issue("error", "not_object", "", "a rekord nem JSON objektum")]

    unknown = sorted(set(rec) - set(TOP_FIELDS))
    missing = [f for f in TOP_FIELDS if f not in rec]
    for f in unknown:
        add("error", "unknown_field", f, f"ismeretlen felső szintű mező: {f}")
    for f in missing:
        add("error", "missing_field", f, f"hiányzó mező: {f}")
    if missing:
        return issues

    # --- egyszerű mezők
    rid = rec["id"]
    id_re = ID_DATASET_RE if mode == "dataset" else ID_FIXTURE_RE
    if not isinstance(rid, str) or not id_re.match(rid):
        add("error", "bad_id", "id", f"az id nem felel meg a(z) {mode} mód mintájának ({id_re.pattern}): {rid!r}")
    if rec["category"] != "multiturn":
        add("error", "bad_category", "category", "a category értéke 'multiturn' kell legyen")
    for f in ("instruction", "output"):
        if not isinstance(rec[f], str) or not rec[f].strip():
            add("error", "bad_type", f, f"a(z) {f} nem üres string")
    if rec["input"] != "":
        add("error", "derived_input_nonempty", "input", "az input mezője üres string kell legyen")
    if not isinstance(rec["quality_notes"], str) or not rec["quality_notes"].strip():
        add("error", "bad_type", "quality_notes", "a quality_notes nem üres string")
    if not isinstance(rec["source"], str) or not rec["source"].strip():
        add("error", "bad_type", "source", "a source nem üres string")
    if rec["difficulty"] not in legacy.ALLOWED_DIFFICULTIES:
        add("error", "bad_difficulty", "difficulty", f"a difficulty csak {sorted(legacy.ALLOWED_DIFFICULTIES)} lehet")

    # --- meta
    meta = rec["meta"]
    fam = None
    declared = set()
    n_turns_for_depends = None
    if not isinstance(meta, dict):
        add("error", "meta_not_object", "meta", "a meta nem objektum")
        meta = {}
    else:
        for k in sorted(set(meta) - set(META_REQUIRED) - set(META_OPTIONAL)):
            add("error", "meta_unknown_key", f"meta.{k}", f"ismeretlen meta-kulcs: {k}")
        for k in META_REQUIRED:
            if k not in meta:
                add("error", "meta_missing", f"meta.{k}", f"hiányzó meta-kulcs: {k}")
        fam = meta.get("family")
        if "family" in meta and fam not in FAMILIES:
            add("error", "meta_family_invalid", "meta.family", f"ismeretlen család: {fam!r}")
            fam = None
        skills = meta.get("skills")
        if "skills" in meta:
            if (not isinstance(skills, list) or not skills or len(set(map(str, skills))) != len(skills)
                    or not all(isinstance(s, str) and s in SKILLS for s in skills)):
                add("error", "meta_skills_invalid", "meta.skills", "a skills nem üres, egyedi, ismert készség-slugok listája")
            elif fam and FAMILIES[fam] not in skills:
                add("error", "meta_skills_invalid", "meta.skills", "a skills nem tartalmazza a család elsődleges készségét")
        if "split_group" in meta and (not isinstance(meta["split_group"], str) or not GROUP_RE.match(meta["split_group"])):
            add("error", "meta_split_group_invalid", "meta.split_group", "a split_group alakja g0000")
        if "persona" in meta and (not isinstance(meta["persona"], str) or not PERSONA_RE.match(meta["persona"])):
            add("error", "meta_persona_invalid", "meta.persona", "a persona alakja p000")
        if "domain" in meta and meta["domain"] not in DOMAINS:
            add("error", "meta_domain_invalid", "meta.domain", f"ismeretlen domain: {meta['domain']!r}")
        pn = meta.get("persona_names")
        if "persona_names" in meta:
            if (not isinstance(pn, list) or len(set(map(str, pn))) != len(pn)
                    or not all(isinstance(n, str) for n in pn)):
                add("error", "meta_persona_names_invalid", "meta.persona_names", "a persona_names egyedi stringek listája")
            else:
                bad = [n for n in pn if n not in bank["approved_given_names"]]
                if bad:
                    add("error", "meta_persona_names_invalid", "meta.persona_names",
                        "nem jóváhagyott keresztnév a deklarációban: " + ", ".join(bad))
                declared = {n for n in pn if n in bank["approved_given_names"]}
        if "register" in meta and meta["register"] not in ("tegezo", "magazo"):
            add("error", "meta_register_invalid", "meta.register", "a register 'tegezo' vagy 'magazo'")
        for k in ("user_typos", "sensitive_area", "fixture"):
            if k in meta and not isinstance(meta[k], bool):
                add("error", "meta_flag_invalid", f"meta.{k}", f"a(z) {k} logikai érték")
        is_fixture = meta.get("fixture") is True
        if mode == "fixture" and not is_fixture:
            add("error", "meta_fixture_mismatch", "meta.fixture", "fixture módban a meta.fixture igaz kell legyen")
        if mode == "dataset" and is_fixture:
            add("error", "meta_fixture_mismatch", "meta.fixture", "tesztadat (meta.fixture) nem kerülhet a valódi csomagba")

    # --- tags
    tags = rec["tags"]
    if not isinstance(tags, list) or not all(isinstance(t, str) and TAG_RE.match(t) for t in tags):
        add("error", "tags_invalid", "tags", "a tags ASCII snake_case stringek listája")
    else:
        if tags[:3] != REQUIRED_TAG_PREFIX or len(tags) < 4:
            add("error", "tags_invalid", "tags", f"a tags első három eleme {REQUIRED_TAG_PREFIX}, a negyedik a család slugja")
        elif fam and tags[3] != FAMILIES[fam]:
            add("error", "tag_family_mismatch", "tags", "a tags negyedik eleme nem egyezik a meta.family slugjával")
        elif tags[3] not in SKILLS:
            add("error", "tags_invalid", "tags", "a tags negyedik eleme nem ismert család-slug")

    # --- turns
    turns = rec["turns"]
    messages = []   # (index, role, text) csak az érvényes szerkezetű üzenetekre
    if not isinstance(turns, list):
        add("error", "turns_not_list", "turns", "a turns nem lista")
    else:
        n = len(turns)
        n_turns_for_depends = n
        for i, t in enumerate(turns):
            p = f"turns[{i}]"
            if not isinstance(t, dict) or set(t) != {"role", "text"}:
                add("error", "turn_keys", p, "az üzenet pontosan a role és text kulcsokat tartalmazza")
                continue
            role, text = t["role"], t["text"]
            want_role = "user" if i % 2 == 0 else "assistant"
            if role not in ("user", "assistant"):
                add("error", "role_invalid", f"{p}.role", f"ismeretlen szerep: {role!r}")
            elif role != want_role:
                add("error", "role_order", f"{p}.role", f"a(z) {i}. üzenet szerepe {want_role} kellene legyen, de {role}")
            if not isinstance(text, str):
                add("error", "text_not_string", f"{p}.text", "az üzenet szövege nem string")
                continue
            if not text.strip():
                add("error", "text_empty", f"{p}.text", "üres üzenet")
                continue
            if text != text.strip():
                add("error", "text_not_trimmed", f"{p}.text", "az üzenet elején/végén szóköz vagy újsor van")
            if "\n" in text or "\r" in text:
                add("error", "text_newline", f"{p}.text", "az üzenet nem tartalmazhat újsort")
            bad = _forbidden_char(text.replace("\n", "").replace("\r", ""))
            if bad is not None:
                add("error", "text_control_char", f"{p}.text", f"vezérlő/sorelválasztó karakter az üzenetben: U+{ord(bad):04X}")
            limit = USER_MAX_CHARS if role == "user" else ASSISTANT_MAX_CHARS
            if role in ("user", "assistant") and len(text) > limit:
                add("error", f"{role}_too_long", f"{p}.text", f"az üzenet {len(text)} karakter (max. {limit})")
            messages.append((i, role, text))
        if n == 0 or turns and isinstance(turns[0], dict) and turns[0].get("role") != "user":
            add("error", "first_not_user", "turns[0]", "az első üzenet user szerepű kell legyen")
        if n and isinstance(turns[-1], dict) and turns[-1].get("role") != "assistant":
            add("error", "last_not_assistant", f"turns[{n - 1}]", "az utolsó üzenet assistant szerepű kell legyen")
        if n % 2 == 1:
            add("error", "odd_message_count", "turns", "a beszélgetés nem teljes váltásokból áll (páratlan üzenetszám)")
        ex = n // 2
        if ex < MIN_EXCHANGES or ex > MAX_EXCHANGES:
            add("error", "exchange_count", "turns", f"{ex} váltás; megengedett: {MIN_EXCHANGES}-{MAX_EXCHANGES}")
        if isinstance(meta, dict) and "n_exchanges" in meta and meta["n_exchanges"] != ex:
            add("error", "meta_n_exchanges_mismatch", "meta.n_exchanges",
                f"a meta.n_exchanges ({meta['n_exchanges']!r}) nem egyezik a turns-ből számolttal ({ex})")
        first_user = next((t["text"] for t in turns if isinstance(t, dict) and t.get("role") == "user"), None)
        last_assistant = next((t["text"] for t in reversed(turns)
                               if isinstance(t, dict) and t.get("role") == "assistant"), None)
        if isinstance(rec["instruction"], str) and first_user is not None and rec["instruction"] != first_user:
            add("error", "derived_instruction_mismatch", "instruction", "az instruction nem egyezik az első user-üzenettel")
        if isinstance(rec["output"], str) and last_assistant is not None and rec["output"] != last_assistant:
            add("error", "derived_output_mismatch", "output", "az output nem egyezik az utolsó assistant-üzenettel")

    if n_turns_for_depends is not None and "depends" in meta:
        check_depends(meta["depends"], n_turns_for_depends, issues)

    # --- tartalom, üzenetenként (közbenső fordulók is)
    used_names = set()
    seen_assistant = {}
    for i, role, text in messages:
        p = f"turns[{i}].text"
        codes = set()
        if role == "assistant":
            found = _legacy_content_issues("Kérdés.", text)
        else:
            found = _legacy_content_issues(text, text)
        for li in found:
            if role == "user" and li.code in CONTENT_IGNORED_FOR_USER:
                continue
            if li.code in codes:
                continue
            codes.add(li.code)
            add("error", "content_" + li.code, p, li.message)
        if IDENTITY_RE.search(text):
            add("error", "identity_mention", p, "MF-AI/Nexora/Nextora említés (identitás-szivárgás)")
        if URL_RE.search(text):
            add("error", "url_or_domain", p, "URL vagy domain-szerű minta az üzenetben")
        if LONG_DIGITS_RE.search(text):
            add("error", "long_digit_run", p, "8+ jegyű számsor az üzenetben (személyes adat gyanúja)")
        if LABEL_RE.search(text):
            add("error", "role_label_in_text", p, "User:/AI: felirat az üzenet szövegében")
        errs, warns, used = check_names(text, bank, declared)
        used_names |= used
        for code, msg in errs:
            add("error", code, p, msg)
        for code, msg in warns:
            add("warning", code, p, msg)
        if role == "assistant":
            if text in seen_assistant:
                add("warning", "duplicate_assistant_message", p, f"az üzenet megegyezik a turns[{seen_assistant[text]}] üzenettel")
            seen_assistant.setdefault(text, i)
    for li in _legacy_content_issues("Kérdés.", "rendben rendben rendben",
                                     rec["quality_notes"] if isinstance(rec["quality_notes"], str) else "rendben"):
        add("error", "content_" + li.code, "quality_notes", li.message)
    if isinstance(rec["quality_notes"], str) and IDENTITY_RE.search(rec["quality_notes"]):
        add("error", "identity_mention", "quality_notes", "MF-AI/Nexora/Nextora említés a jegyzetben")
    for name in sorted(declared - used_names):
        add("warning", "persona_name_unused", "meta.persona_names", f"deklarált, de a szövegben nem szereplő név: {name}")

    if fam in FAMILIES_EXPECTING_DEPENDS and isinstance(meta.get("depends"), list):
        dep = [d for d in meta["depends"] if isinstance(d, dict) and _is_int(d.get("depth"))]
        if not dep:
            add("warning", "family_expects_depends", "meta.depends",
                f"a(z) {fam} család előzmény-függő fordulatot vár (nincs depends bejegyzés)")
        elif fam == "F7" and not any(d["depth"] >= 2 for d in dep):
            add("warning", "family_expects_depends", "meta.depends", "az F7 család legalább 2 mélységű visszatérést vár")
    return issues


def legacy_compatible(rec, line_no=1):
    """A régi validátor a 9 régi mezőre (csak szerkezeti kompatibilitás)."""
    try:
        return len(legacy.validate_row(rec, line_no, set())) == 0
    except Exception:   # pragma: no cover - védekező: a régi validátor váratlan bemenetre
        return False


# ---------------------------------------------------------------------------
# fájl-ellenőrzés és jelentés
# ---------------------------------------------------------------------------

def validate_file(path, mode, bank):
    result = {"file": path, "mode": mode, "tool_version": TOOL_VERSION, "file_issues": [], "records": []}
    seen_ids = {}
    with open(path, "rb") as f:
        raw = f.read()
    for line_no, line in enumerate(raw.split(b"\n"), 1):
        line = line[:-1] if line.endswith(b"\r") else line
        if not line.strip():
            continue
        try:
            rec = json.loads(line.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            result["file_issues"].append({"severity": "error", "code": "invalid_json", "path": f"line {line_no}",
                                          "message": f"hibás JSON: {exc}"})
            continue
        issues = validate_record(rec, mode, bank)
        rid = rec.get("id") if isinstance(rec, dict) else None
        if isinstance(rid, str):
            if rid in seen_ids:
                issues.append(Issue("error", "duplicate_id", "id", f"duplikált id (első előfordulás: {seen_ids[rid]}. sor)"))
            seen_ids.setdefault(rid, line_no)
        errors = [i for i in issues if i.severity == "error"]
        turns = rec.get("turns") if isinstance(rec, dict) else None
        n_msg = len(turns) if isinstance(turns, list) else 0
        entry = {
            "line": line_no, "id": rid,
            "legacy_validator_compatible": legacy_compatible(rec, line_no) if isinstance(rec, dict) else False,
            "turns_validated": not errors,
            "errors": len(errors), "warnings": len(issues) - len(errors),
            "messages": n_msg, "exchanges": n_msg // 2,
            "issues": [i.to_dict() for i in issues],
        }
        result["records"].append(entry)
    recs = result["records"]
    ok = [r for r in recs if r["turns_validated"]]
    result["summary"] = {
        "records": len(recs),
        "turns_validated": len(ok),
        "legacy_validator_compatible": sum(1 for r in recs if r["legacy_validator_compatible"]),
        "legacy_compatible_but_not_turns_validated": sum(
            1 for r in recs if r["legacy_validator_compatible"] and not r["turns_validated"]),
        "records_with_errors": len(recs) - len(ok),
        "file_errors": len(result["file_issues"]),
        "warnings": sum(r["warnings"] for r in recs),
        # a három mennyiség KÜLÖN szerepel; a tanítási minta = egy assistant-fordulóra adott cél
        "conversations": len(ok),
        "messages": sum(r["messages"] for r in ok),
        "training_samples": sum(r["exchanges"] for r in ok),
        "training_samples_first_turn": len(ok),
        "training_samples_history_dependent": sum(r["exchanges"] - 1 for r in ok),
        "counted_over": "csak a turns-validált rekordok",
    }
    return result


DISCLAIMER = ("A 'turns-validált' állapot csak formátum- és szűrő-ellenőrzés: NEM tartalmi ellenőrzés, "
              "NEM training-ready, és a régi validátor sikere nem helyettesíti.")


def _main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="MT-1: többfordulós (turns) beszélgetés-ellenőrző.")
    parser.add_argument("files", nargs="+", help="Ellenőrzendő .jsonl fájl(ok).")
    parser.add_argument("--mode", required=True, choices=["dataset", "fixture"])
    parser.add_argument("--name-bank", default=DEFAULT_NAME_BANK)
    parser.add_argument("--json", default=None, help="Részletes riport JSON fájlba.")
    args = parser.parse_args(argv)
    try:
        bank = load_name_bank(args.name_bank)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"HIBA: a névtár nem olvasható: {exc}", file=sys.stderr)
        return 2
    results, exit_code = [], 0
    for path in args.files:
        if not os.path.isfile(path):
            print(f"HIBA: a fájl nem található: {path}", file=sys.stderr)
            return 2
        res = validate_file(path, args.mode, bank)
        results.append(res)
        s = res["summary"]
        print(f"Fájl: {path} (mód: {args.mode})")
        print(f"Rekordok: {s['records']} | turns-validált: {s['turns_validated']} | régi-validátor-kompatibilis: "
              f"{s['legacy_validator_compatible']} (ebből NEM turns-validált: {s['legacy_compatible_but_not_turns_validated']}) "
              f"| hibás rekord: {s['records_with_errors']} | fájl-hiba: {s['file_errors']} | figyelmeztetés: {s['warnings']}")
        print(f"Beszélgetés: {s['conversations']} | üzenet: {s['messages']} | tanítási minta: {s['training_samples']} "
              f"(első fordulós: {s['training_samples_first_turn']}, előzmény-függő: {s['training_samples_history_dependent']}) "
              f"- {s['counted_over']}")
        for fi in res["file_issues"]:
            print(f"  FÁJL-HIBA {fi['path']}: {fi['code']}: {fi['message']}")
        for r in res["records"]:
            for i in r["issues"]:
                if i["severity"] == "error":
                    print(f"  HIBA {r['id']} {i['path']}: {i['code']}: {i['message']}")
        if s["records_with_errors"] or s["file_errors"] or not s["records"]:
            exit_code = 1
    print(DISCLAIMER)
    if args.json:
        with open(args.json, "w", encoding="utf-8", newline="\n") as f:
            json.dump({"tool_version": TOOL_VERSION, "disclaimer": DISCLAIMER, "results": results}, f,
                      ensure_ascii=False, indent=2)
            f.write("\n")
    return exit_code


if __name__ == "__main__":
    sys.exit(_main())
