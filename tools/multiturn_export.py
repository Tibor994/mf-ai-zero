"""
MF-AI-Zero - MT-4: felosztott, ellenőrzött többfordulós beszélgetések renderelése és exportálása kizárási szűrővel.

CÉL: az MT-2 felosztás-manifestjéből (és az általa rögzített, MT-1-validált, MT-3-ellenőrzött bemenetekből) elkülönített
train / validation / test exportot készít: (1) a beszélgetések kanonikus, bájt-pontos másolata részenként, (2) a beszélgetésekből
képzett tanítási minták renderelve (R1 futásidő-hű, R2 teljes előzmény), (3) teljes visszakövethetőség és visszaolvasásos
ellenőrzés. Nem tanít, nem generál adatot, nem ír felül forrásadatot vagy korábbi exportot, és NEM állít training-ready,
content_verified vagy split_approved állapotot: az export sikere ezeket nem változtatja (a felsőbb manifestek érintetlenek).

ALAPELVEK
  * Csak aktuális, teljes, érintetlen bemenet: az MT-2 manifestet az `multiturn_split.verify_manifest` ellenőrzi (bemenetek,
    kimenetek, MT-3 jelentés aktualitása, a kijelölés újraszámolása), ezen felül a manifest belső egységességét (kijelölés
    ellenőrzőösszege, csoport-tagság, darabszámok) és a státusz-mezőket (mind `false`) az MT-4 külön. Elavult, hiányos vagy
    megváltozott bemenetnél egyértelmű hibával (15-ös kód) megáll.
  * Csak a kijelölt (MT-2 `assignment`) beszélgetések kerülhetnek az exportba. Visszatartott, kizárási listás, kizárás-jelölésű,
    fel nem oldott MT-3 `reject`/`review` státuszú rekord vagy blokkolt tagot tartalmazó csoport soha; az MT-4 ezt az MT-3
    jelentésből és a kizárási listából függetlenül is ellenőrzi. A hat TE-1 kizárás érvényben marad: a TE-1 export kizárt sorainak
    szövege (azonos, szóközre nyírt szöveg) egyetlen exportált üzenetben sem szerepelhet, az azonosító sem ütközhet.
  * Nincs csendes átírás vagy csonkítás. A kanonikus másolat a forrássor bájtjai (ellenőrzőösszeggel). A renderelt minták
    üzenetenként jelzik, hogy teljesek-e; a veszteséges renderelés (R1: az előzmény a `memory.build_prompt_context` szerint
    80/120 karakterre vágva; mélyebb előzmény-függés nem ábrázolható) mintánként és összesítve, indoklással szerepel.
    A veszteségmentesen nem ábrázolható beszélgetés visszatartva (`withheld.tsv`), okkal.
  * Az R1 előtag bájt-pontosan a `src/memory.py` `build_prompt_context` kimenete: a függvény importálva van (nem másolva);
    a `src/memory.py` nem módosul (ellenőrzőösszege a manifestben).
  * R3 (összefoglaló-előzmény) nem állítható elő: kézi „arany” összefoglaló és döntés kell (terv 3.2, D-1); kérése hiba.
  * A tesztadat (`fixture` mód) nem exportálható észrevétlenül valódi tanítóadatként: a mód kifejezett, egyeznie kell az MT-2
    manifest módjával, a futás-mappa neve `fixture_` előtagú, minden minta `fixture: true` és `data_kind: fixture`, a mappában
    jelölő fájl van, a manifest `training_data: false`.
  * Visszakövethető: minden minta rögzíti a forrásfájlt, sort, sor-ellenőrzőösszeget, a beszélgetést és a célfordulót; az
    `export_index.tsv` és a `conversation_index.tsv` soronként mutatja.
  * Az export a lemezről visszaolvasva ellenőrzött (tartalom, szerepek, beszélgetéshatárok, részek szétválasztása, kizárások),
    mielőtt a manifest véglegesedik; utólag a `--verify-export` újra elvégzi.

Használat:
    python tools/multiturn_export.py --mode dataset|fixture --mt2-manifest <split_manifest.json> --out-dir <mappa>
        [--modes R1,R2] [--allow-no-te1-comparison] [--run-name <név>]
    python tools/multiturn_export.py --verify-export <export_manifest.json>

Kilépési kódok: 0 kész, teljes; 1 kész, de figyelmet kér (visszatartott beszélgetés, TE-1 összevetés nélküli bemenet); 2 argumentumhiba;
10 bemeneti fájl hiba; 11 nem turns-validált rekord; 12 TE-1 export hiba; 13 kizárás megsértése; 14 kimeneti útvonal hiba;
15 elavult/hiányos/megváltozott bemenet; 16 a bemenet a futás közben megváltozott; 17 a visszaolvasásos ellenőrzés hibát talált
(nincs véglegesített export); 18 elutasított kérés (mód, nem támogatott renderelés, tesztadat-védelem).
"""

import argparse
import datetime
import hashlib
import importlib.util
import json
import os
import re
import sys
import time
from collections import Counter

import dataset_export_chat_text as te2
import dataset_export_train as te1
import multiturn_split as ms
import multiturn_validate as mt1

TOOL_VERSION = "mt4-1.0"
SPLITS = ms.SPLITS
SUPPORTED_MODES = ("R1", "R2")
DEFAULT_MODES = ("R1", "R2")
MEMORY_PATH = os.path.join(te1.REPO_ROOT, "src", "memory.py")
MT2_TOOL = "tools/multiturn_split.py"
LABEL_USER, LABEL_AI = "User: ", "AI: "
MANIFEST_FILE = "export_manifest.json"
FAILED_FILE = "FAILED.txt"
FIXTURE_MARKER_FILE = "FIXTURE_TEST_DATA_NOT_FOR_TRAINING.txt"
CONVERSATION_INDEX = "conversation_index.tsv"
EXPORT_INDEX = "export_index.tsv"
WITHHELD_FILE = "withheld.tsv"
RUN_NAME_RE = re.compile(r"^[A-Za-z0-9._-]+$")

R3_REASON = ("az R3 (összefoglaló-előzmény) kézi „arany” összefoglalót igényel, amely nem létezik, és használatáról külön döntés kell "
             "(terv 3.2 és D-1); ezért nem állítható elő, és nem is közelíthető automatikus szövegvágással")

EXIT_ATTENTION = 1
EXIT_INPUT, EXIT_INVALID, EXIT_TE1, EXIT_EXCLUSION, EXIT_OUTPUT = 10, 11, 12, 13, 14
EXIT_STALE, EXIT_CHANGED_DURING, EXIT_VERIFY, EXIT_REFUSED = 15, 16, 17, 18

DISCLAIMER = ("Az export technikai előkészítés: NEM jóváhagyott felosztás, NEM tartalmi ellenőrzés, NEM training-ready. Az export sikere a "
              "split_approved, content_verified és training_ready állapotokat nem változtatja (a felsőbb manifestek érintetlenek, értékük false). "
              "A tesztadat (fixture) exportja nem tanítóadat.")
LIMITATIONS = [
    "Az R1 az előzményt a futásidő promptja szerint (a legutolsó váltás, User ≤ 80 / AI ≤ 120 karakterre vágva) adja: a hosszabb üzenetek előzménybeli szövege csonkolt (a csonkolás mintánként jelölve), és a mélység ≥ 2 előzmény-függés R1-gyel nem ábrázolható; ilyenkor az R2 (teljes előzmény) az igazi ábrázolás.",
    "Az R2 a teljes előzményt adja, de a jelenlegi futásidő ezt nem nyújtja (D-1); a karakter-LSTM tanításkori ablaka (seq_length = 64) ennél sokkal rövidebb, ezért a hosszú R2 minták használata az MT-5 és a külön jóváhagyás kérdése.",
    "Az R3 nem készül (kézi összefoglaló és döntés kell).",
    "A `User: `/`AI: ` címkék és az elválasztók a renderelés részei; a beszélgetések egysoros üzenetei ezért egyértelműen visszaolvashatók. Az egységesítést (NFC stb.) az export nem végez: a szöveg a forrás bájtjaival azonos.",
    "A kizárt TE-1 sorok elleni védelem pontos (nyírt) szövegegyezésre vonatkozik; átfogalmazott vagy részleges átfedést nem talál.",
    "A visszaolvasásos ellenőrzés a formátum és a forrás megfelelését igazolja, nem a tartalom minőségét.",
]


class ExportError(Exception):
    exit_code = EXIT_INPUT


class InputFileError(ExportError):
    exit_code = EXIT_INPUT


class InvalidRecordsError(ExportError):
    exit_code = EXIT_INVALID


class Te1InputError(ExportError):
    exit_code = EXIT_TE1


class ExclusionViolationError(ExportError):
    exit_code = EXIT_EXCLUSION


class OutputError(ExportError):
    exit_code = EXIT_OUTPUT


class StaleInputError(ExportError):
    exit_code = EXIT_STALE


class ChangedInputError(ExportError):
    exit_code = EXIT_CHANGED_DURING


class VerificationError(ExportError):
    exit_code = EXIT_VERIFY


class RefusedError(ExportError):
    exit_code = EXIT_REFUSED


class Unrenderable(Exception):
    """A beszélgetés vagy minta veszteségmentesen nem ábrázolható."""


# ---------------------------------------------------------------------------
# a futásidő-hű előtag forrása: src/memory.py (importálva, nem másolva)
# ---------------------------------------------------------------------------

_MEMORY = None


def memory_module():
    global _MEMORY
    if _MEMORY is None:
        if not os.path.isfile(MEMORY_PATH):
            raise InputFileError(f"A futásidő-hű előtag forrása nem található: {MEMORY_PATH}")
        spec = importlib.util.spec_from_file_location("mf_src_memory", MEMORY_PATH)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _MEMORY = mod
    return _MEMORY


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# renderelés
# ---------------------------------------------------------------------------

def renderable_problems(texts):
    """Miért nem ábrázolható veszteségmentesen a beszélgetés a `User:`/`AI:` blokk-formában (üres lista: ábrázolható).
    Az MT-1 ezeket már kizárja; az MT-4 védekezésképp újra ellenőrzi, és nem javít át semmit."""
    problems = []
    for i, t in enumerate(texts):
        if not isinstance(t, str) or not t:
            problems.append(f"{i}. üzenet: üres vagy nem szöveg")
            continue
        if t != t.strip():
            problems.append(f"{i}. üzenet: a szélén szóköz/újsor van (a renderelés nem átírhatja)")
        bad = mt1._forbidden_char(t)
        if bad is not None:
            problems.append(f"{i}. üzenet: sortörő vagy vezérlő karakter (U+{ord(bad):04X}) — a blokk-forma egyértelműen nem olvasható vissza")
    return problems


def _seg(role, turn, kind, start, end, source_text, rendered_text):
    return {"role": role, "turn": turn, "kind": kind, "start": start, "end": end, "complete": rendered_text == source_text}


def render_r2(texts, t):
    """R2: a teljes beszélgetés a célig (a `t` indexű assistant-üzenetig), `User: `/`AI: ` címkékkel, blokkonként `\\n\\n`-nel."""
    parts, segs, pos = [], [], 0
    for i in range(t + 1):
        role = "user" if i % 2 == 0 else "assistant"
        label = LABEL_USER if role == "user" else LABEL_AI
        parts.append(label)
        pos += len(label)
        start = pos
        parts.append(texts[i])
        pos += len(texts[i])
        kind = "target" if i == t else ("current" if i == t - 1 else "context")
        segs.append(_seg(role, i, kind, start, pos, texts[i], texts[i]))
        sep = "\n" if role == "user" else ("\n\n" if i < t else "")
        parts.append(sep)
        pos += len(sep)
    return "".join(parts), segs


_CONTEXT_RE = re.compile(r"^User: ([^\n]*)\nAI: ([^\n]*)\n\n$")


def render_r1(texts, t):
    """R1 (futásidő-hű): a cél előtti utolsó váltás a `memory.build_prompt_context` szerint (importált függvény), majd a teljes
    aktuális kérés és a teljes cél. Az előzmény a függvény szerint csonkolt lehet; ezt a szegmensek `complete` jelzője mutatja."""
    mem = memory_module()
    history = [(texts[i], texts[i + 1]) for i in range(0, t - 1, 2)]
    ctx = mem.build_prompt_context(history) if history else ""
    if history and not ctx:
        raise Unrenderable("a memory.build_prompt_context üres előzményt adott (üres üzenet?)")
    parts, segs, pos = [], [], 0
    if history:
        m = _CONTEXT_RE.match(ctx)
        if not m:
            raise Unrenderable("a memory.build_prompt_context kimenete nem a várt `User: …\\nAI: …\\n\\n` alak")
        u_r, a_r = m.group(1), m.group(2)
        u_start = len(LABEL_USER)
        a_start = u_start + len(u_r) + 1 + len(LABEL_AI)
        segs.append(_seg("user", t - 3, "context", u_start, u_start + len(u_r), texts[t - 3], u_r))
        segs.append(_seg("assistant", t - 2, "context", a_start, a_start + len(a_r), texts[t - 2], a_r))
        parts.append(ctx)
        pos = len(ctx)
    cur_start = pos + len(LABEL_USER)
    parts.append(LABEL_USER + texts[t - 1] + "\n" + LABEL_AI)
    segs.append(_seg("user", t - 1, "current", cur_start, cur_start + len(texts[t - 1]), texts[t - 1], texts[t - 1]))
    tgt_start = cur_start + len(texts[t - 1]) + 1 + len(LABEL_AI)
    parts.append(texts[t])
    segs.append(_seg("assistant", t, "target", tgt_start, tgt_start + len(texts[t]), texts[t], texts[t]))
    return "".join(parts), segs


def render(mode, texts, t):
    if mode == "R1":
        return render_r1(texts, t)
    if mode == "R2":
        return render_r2(texts, t)
    raise RefusedError(f"Nem támogatott renderelés: {mode}" + (f" — {R3_REASON}" if mode == "R3" else ""))


def parse_rendered(text):
    """A renderelt szöveg független visszaolvasása: [(role, szöveg), ...]. ValueError, ha nem a várt blokk-alak."""
    msgs = []
    for block in text.split("\n\n"):
        lines = block.split("\n")
        if len(lines) != 2 or not lines[0].startswith(LABEL_USER) or not lines[1].startswith(LABEL_AI):
            raise ValueError("a blokk nem `User: …\\nAI: …` alakú")
        msgs.append(("user", lines[0][len(LABEL_USER):]))
        msgs.append(("assistant", lines[1][len(LABEL_AI):]))
    return msgs


def dependency_info(depends, t, segs):
    """A `meta.depends` bejegyzés lefedettsége a renderelésben: mely forrás-üzenetek szerepelnek a mintában."""
    entry = depends.get(t)
    if entry is None:
        return None
    present = {s["turn"] for s in segs}
    missing = sorted(i for i in entry["on"] if i not in present)
    return {"on": list(entry["on"]), "depth": entry["depth"], "covered": not missing, "missing": missing}


def depends_map(obj):
    out = {}
    for d in obj["meta"]["depends"]:
        out[d["turn"]] = {"on": list(d["on"]), "depth": d["depth"]}
    return out


def build_samples(conv, mode, split, data_kind, fixture):
    """Egy beszélgetés összes mintája egy renderelési módban (assistant-fordulónként egy). conv: {obj, entry, ...}."""
    obj, entry = conv["obj"], conv["entry"]
    texts = [t["text"] for t in obj["turns"]]
    depends = depends_map(obj)
    out = []
    for t in range(1, len(texts), 2):
        text, segs = render(mode, texts, t)
        for s in segs:                                     # önellenőrzés: a `complete` jelző és a szegmens tényleges tartalma egyezik
            if s["complete"] != (text[s["start"]:s["end"]] == texts[s["turn"]]):
                raise Unrenderable("a szegmens határai nem egyeznek a renderelt szöveggel")
        dep = dependency_info(depends, t, segs)
        content_complete = all(s["complete"] for s in segs)
        truncation = [{"turn": s["turn"], "role": s["role"], "original_chars": len(texts[s["turn"]]), "rendered_chars": s["end"] - s["start"],
                       "lost_chars": len(texts[s["turn"]]) - (s["end"] - s["start"] - 3)}      # a "..." jelölő nem az eredeti szöveg
                      for s in segs if not s["complete"]]
        tgt = segs[-1]
        out.append({
            "sample_id": f"{obj['id']}#{mode}#{t}", "mode": mode, "split": split, "conversation_id": obj["id"], "unit": entry["unit"],
            "exchange": t // 2 + 1, "n_exchanges": len(texts) // 2, "first_turn": t == 1, "current_user_turn": t - 1, "target_turn": t,
            "text": text, "messages": segs, "target": {"start": tgt["start"], "end": tgt["end"]},
            "content_complete": content_complete, "dependency": dep,
            "lossless": content_complete and (dep is None or dep["covered"]),
            "history_truncation": truncation,
            "family": obj["meta"]["family"], "domain": obj["meta"]["domain"],
            "data_kind": data_kind, "fixture": fixture,
            "source": {"file": entry["file"], "line": entry["line"], "line_sha256": entry["line_sha256"]},
        })
    return out


# ---------------------------------------------------------------------------
# bemenetek: az MT-2 manifest ellenőrzése
# ---------------------------------------------------------------------------

def _resolve(rel):
    return rel if os.path.isabs(rel) else os.path.join(te1.REPO_ROOT, rel)


def file_sha_map(paths):
    return {p: te1.sha256_file(p) for p in paths}


def check_mt2_structure(m):
    """Az MT-2 manifest belső egységessége (a `verify_manifest` a bemeneteket és kimeneteket ellenőrzi, a manifest saját
    listáit nem): kijelölés- és csoport-ellenőrzőösszeg, tagság, darabszámok, státusz-mezők. Hibák listája."""
    problems = []
    need = ("tool", "tool_version", "status", "config", "inputs", "counts", "splits", "assignment", "units", "held_back",
            "assignment_sha256", "groups_sha256", "verification", "outputs", "training_ready", "content_verified", "split_approved")
    for k in need:
        if k not in m:
            problems.append(f"hiányzó kulcs az MT-2 manifestben: {k}")
    if problems:
        return problems
    if m["tool"] != MT2_TOOL:
        problems.append(f"nem MT-2 manifest (tool={m['tool']!r})")
    if not str(m["tool_version"]).startswith("mt2-"):
        problems.append(f"ismeretlen MT-2 verzió: {m['tool_version']!r}")
    if m["status"] != "completed":
        problems.append(f"az MT-2 manifest státusza {m['status']!r} (várt: completed)")
    for flag in ("training_ready", "content_verified", "split_approved"):
        if m[flag] is not False:
            problems.append(f"az MT-2 manifest {flag} értéke nem false: az MT-4 nem fogad el jóváhagyást állító bemenetet, és nem is állít ilyet")
    if not isinstance(m["verification"], dict) or not m["verification"] or not all(v is True for v in m["verification"].values()):
        problems.append("az MT-2 manifest ellenőrzései nem mind igazak")
    for key in ("conversation_files", "mt3_report", "te1_export", "exclusions", "name_bank"):
        if key not in m["inputs"]:
            problems.append(f"hiányzó bemenet-bejegyzés az MT-2 manifestben: {key}")
    if problems:
        return problems
    # a kijelölés és a csoportok ellenőrzőösszege a manifest saját listáiból
    rows = []
    for a in m["assignment"]:
        for k in ("id", "file", "line", "line_sha256", "unit", "split"):
            if k not in a:
                return problems + [f"hiányos kijelölés-bejegyzés az MT-2 manifestben (hiányzó kulcs: {k})"]
        if a["split"] not in SPLITS:
            problems.append(f"ismeretlen rész a kijelölésben: {a['split']!r} ({a['id']})")
        rows.append((a["file"], a["line"], a["id"], a["split"]))
    for h in m["held_back"]:
        for k in ("id", "file", "line", "reasons"):
            if k not in h:
                return problems + [f"hiányos visszatartás-bejegyzés az MT-2 manifestben (hiányzó kulcs: {k})"]
        rows.append((h["file"], h["line"], h["id"], "HELD_BACK"))
    keys = [(r[0], r[1]) for r in rows]
    if len(set(keys)) != len(keys):
        problems.append("egy rekord kijelölve és visszatartva is szerepel, vagy duplikált fájl:sor az MT-2 manifestben")
    canon = "\n".join(f"{f}:{ln}:{i}\t{s}" for f, ln, i, s in sorted(rows, key=lambda r: (r[0], r[1])))
    if hashlib.sha256(canon.encode("utf-8")).hexdigest() != m["assignment_sha256"]:
        problems.append("az MT-2 manifest kijelölés-listája nem egyezik a rögzített assignment_sha256-tal (a lista megváltoztatva?)")
    groups_canon = "\n".join(f"{uid}\t{','.join(u['members'])}" for uid, u in sorted(m["units"].items()))
    if hashlib.sha256(groups_canon.encode("utf-8")).hexdigest() != m["groups_sha256"]:
        problems.append("az MT-2 manifest csoport-tagsága nem egyezik a rögzített groups_sha256-tal")
    by_unit = {}
    for a in m["assignment"]:
        by_unit.setdefault(a["unit"], set()).add(a["split"])
        u = m["units"].get(a["unit"])
        if u is None or a["id"] not in u.get("assigned", []) or u.get("split") != a["split"]:
            problems.append(f"a kijelölés és a csoport-tagság ellentmond: {a['id']} ({a['unit']})")
    for uid, splits in by_unit.items():
        if len(splits) != 1:
            problems.append(f"az MT-2 manifest szerint a(z) {uid} csoport több részbe esik: {sorted(splits)}")
    if m["counts"].get("assigned") != len(m["assignment"]) or m["counts"].get("held_back") != len(m["held_back"]):
        problems.append("az MT-2 manifest darabszámai nem egyeznek a listákkal")
    for s in SPLITS:
        n = sum(1 for a in m["assignment"] if a["split"] == s)
        if m["splits"].get(s, {}).get("conversations") != n:
            problems.append(f"az MT-2 manifest {s} részének darabszáma nem egyezik a kijelöléssel")
    return problems


def load_mt2(manifest_path, mode):
    """Beolvasás és teljes ellenőrzés. Visszaad (manifest, sha256)."""
    if not os.path.isfile(manifest_path):
        raise InputFileError(f"Az MT-2 manifest nem található: {manifest_path}")
    try:
        raw = te1.read_bytes(manifest_path)
        m = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise StaleInputError(f"Az MT-2 manifest nem olvasható/érvénytelen JSON: {exc}")
    if not isinstance(m, dict):
        raise StaleInputError("Az MT-2 manifest nem JSON objektum.")
    problems = check_mt2_structure(m)
    if problems:
        raise StaleInputError("Hiányos, sérült vagy nem megfelelő MT-2 manifest: " + "; ".join(problems))
    try:
        changed, bad = ms.verify_manifest(manifest_path)
    except ms.SplitError as exc:
        raise StaleInputError(f"Az MT-2 manifest bemeneteinek ellenőrzése nem sikerült ({type(exc).__name__}): {exc}")
    except (OSError, json.JSONDecodeError, KeyError) as exc:
        raise StaleInputError(f"Az MT-2 manifest ellenőrzése nem sikerült: {exc}")
    if changed or bad:
        raise StaleInputError("Elavult vagy megváltozott bemenet az MT-2 manifest szerint: " + "; ".join(changed + bad))
    if m["config"].get("mode") != mode:
        raise RefusedError(f"A kért mód ({mode!r}) nem egyezik az MT-2 manifest módjával ({m['config'].get('mode')!r}): tesztadat és valódi adat "
                           f"exportja nem keverhető; add meg a helyes --mode értéket")
    return m, te1.sha256_bytes(raw)


def load_sources(m, mode):
    """A kijelölt beszélgetések forrássorai: bájt-pontos sor, ellenőrzőösszeg az MT-2 manifest szerint, MT-1 érvényesség.
    Visszaad: (conversations a kijelölés sorrendjében, fájl-információk)."""
    infos = m["inputs"]["conversation_files"]
    paths = [_resolve(i["path"]) for i in infos]
    bank_path = _resolve(m["inputs"]["name_bank"]["path"])
    try:
        bank = mt1.load_name_bank(bank_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise InputFileError(f"A névtár nem olvasható: {exc}")
    try:
        records, _finfo = ms.load_conversations(paths, mode, bank)
    except ms.InvalidRecordsError as exc:
        raise InvalidRecordsError(str(exc))
    except ms.InputFileError as exc:
        raise InputFileError(str(exc))
    valid = {(r["file"], r["line"]): r for r in records}
    lines_cache, file_order = {}, {}
    for idx, (info, path) in enumerate(zip(infos, paths)):
        raw = te1.read_bytes(path)
        lines_cache[info["path"]] = raw.split(b"\n")
        file_order[info["path"]] = idx
    convs = []
    for a in m["assignment"]:
        key = (a["file"], a["line"])
        if a["file"] not in lines_cache or key not in valid:
            raise StaleInputError(f"A kijelölt beszélgetés nem található a forrásban: {a['id']} ({a['file']}:{a['line']})")
        if a["line"] < 1 or a["line"] > len(lines_cache[a["file"]]):
            raise StaleInputError(f"A kijelölt sor a forrásfájlon kívül van: {a['file']}:{a['line']}")
        line = lines_cache[a["file"]][a["line"] - 1]
        line = line[:-1] if line.endswith(b"\r") else line
        if te1.sha256_bytes(line) != a["line_sha256"] or valid[key]["line_sha256"] != a["line_sha256"]:
            raise StaleInputError(f"A forrássor ellenőrzőösszege nem egyezik az MT-2 manifesttel: {a['id']} ({a['file']}:{a['line']})")
        obj = json.loads(line.decode("utf-8"))
        if obj["id"] != a["id"]:
            raise StaleInputError(f"A forrássor azonosítója nem egyezik: {a['id']} ({a['file']}:{a['line']})")
        convs.append({"entry": a, "line": line, "obj": obj, "file_idx": file_order[a["file"]]})
    convs.sort(key=lambda c: (c["file_idx"], c["entry"]["line"]))
    return convs, infos


def check_te1_exclusions(m, convs, allow_no_te1):
    """A hat TE-1 kizárás érvényben tartása: a kizárt sorok azonosítója nem ütközhet, szövegük (nyírva) egyetlen exportált
    üzenetben sem szerepelhet. Visszaad: (te1_info | None, excluded_text_hashes, warnings)."""
    exp = m["inputs"].get("te1_export")
    if exp is None:
        if not allow_no_te1:
            raise StaleInputError("Az MT-2 manifest TE-1 export összevetés nélküli: a hat kizárás érvényessége így nem ellenőrizhető "
                                  "(futtasd újra az MT-3/MT-2-t a TE-1 exporttal, vagy kifejezetten --allow-no-te1-comparison)")
        return None, [], ["nincs TE-1 export: a hat kizárás elleni szöveg- és azonosító-védelem nem futott"]
    try:
        te1_manifest, te1_sha, rows = te2.load_te1_export(_resolve(exp["run_dir"]))
    except te2.Te1ExportError as exc:
        raise Te1InputError(str(exc))
    if te1_sha != exp["manifest_sha256"]:
        raise StaleInputError("A TE-1 export manifestje nem egyezik az MT-2 manifestben rögzítettel.")
    try:
        excluded_source, live, recheck = te2.check_exclusions(te1_manifest, rows)
    except te2.ExclusionCheckError as exc:
        raise StaleInputError(f"A TE-1 kizárások ellenőrzése nem sikerült: {exc}")
    excluded_ids = sorted(excluded_source)
    if excluded_ids != sorted(exp["excluded_rows"]):
        raise StaleInputError("A TE-1 export kizárt sorai nem egyeznek az MT-2 manifestben rögzítettel.")
    clash = sorted(set(excluded_ids) & {c["entry"]["id"] for c in convs})
    if clash:
        raise ExclusionViolationError("A beszélgetés azonosítója egy TE-1 kizárt sor azonosítójával ütközik: " + ", ".join(clash))
    owner = {}
    for rid, raw in excluded_source.items():
        row = json.loads(raw.decode("utf-8"))
        for k in ("instruction", "input", "output"):
            v = str(row.get(k, "")).strip()
            if v:
                owner.setdefault(sha256_text(v), (rid, k))
    for c in convs:
        for i, t in enumerate(c["obj"]["turns"]):
            hit = owner.get(sha256_text(t["text"].strip()))
            if hit:
                raise ExclusionViolationError(f"A TE-1-ben kizárt {hit[0]} sor ({hit[1]}) szövege szerepel a(z) {c['entry']['id']} beszélgetés "
                                              f"{i}. üzenetében ({t['role']}): a kizárás érvényben marad")
    return ({"run_dir": exp["run_dir"], "manifest_sha256": te1_sha, "excluded_rows": excluded_ids, "rows": len(rows),
             "exclusion_list_sha256": live["sha256"], "source_rows_verified": recheck.get("excluded_source_rows_verified", 0)},
            sorted(owner), [])


def check_exclusions_and_status(m, convs, mode, allow_no_te1):
    """A kizárt, elutasított és fel nem oldott státuszú rekordok kizárása az exportból - függetlenül az MT-2 kijelölésétől.
    Visszaad: (te1_info, excluded_text_hashes, warnings)."""
    exported = {(c["entry"]["file"], c["entry"]["line"]): c for c in convs}
    ids = {c["entry"]["id"] for c in convs}
    for h in m["held_back"]:
        if (h["file"], h["line"]) in exported or h["id"] in ids:
            raise ExclusionViolationError(f"Visszatartott rekord kerülne az exportba: {h['id']} ({', '.join(h['reasons'])})")
    excl = m["inputs"].get("exclusions")
    if excl:
        path = _resolve(excl["path"])
        try:
            entries, sha = ms.load_exclusions(path)
        except ms.ExclusionsError as exc:
            raise StaleInputError(f"A kizárási lista nem érvényes: {exc}")
        if sha != excl["sha256"]:
            raise StaleInputError("A kizárási lista megváltozott az MT-2 futás óta.")
        hit = sorted(e["id"] for e in entries if e["id"] in ids)
        if hit:
            raise ExclusionViolationError("Kizárási listás beszélgetés kerülne az exportba: " + ", ".join(hit))
    marked = sorted(c["entry"]["id"] for c in convs if te1.EXCLUSION_NOTE_MARKER in str(c["obj"].get("quality_notes", "")))
    if marked:
        raise ExclusionViolationError("Kizárás-jelölésű beszélgetés kerülne az exportba: " + ", ".join(marked))
    te1_info, hashes, warnings = check_te1_exclusions(m, convs, allow_no_te1)
    # az MT-3 jelentés függetlenül: minden exportált rekord tiszta, a csoportja sem tartalmaz blokkolt tagot
    rep_path = _resolve(m["inputs"]["mt3_report"]["path"])
    try:
        rep = json.loads(te1.read_bytes(rep_path).decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise StaleInputError(f"Az MT-3 jelentés nem olvasható: {exc}")
    if rep.get("status") != "completed" or rep.get("training_ready") is not False or rep.get("content_verified") is not False:
        raise StaleInputError("Az MT-3 jelentés nem lezárt vagy státusz-mezői nem false.")
    rec = {(r["file"], r["line"]): r for r in rep["records"]}
    blocked_groups = {r["group_id"] for r in rep["records"] if r["progression"] == "blocked"}
    for key, c in exported.items():
        r = rec.get(key)
        if r is None or r["record"] != c["entry"]["id"]:
            raise StaleInputError(f"Az exportált rekord nincs az MT-3 jelentésben: {c['entry']['id']}")
        if r["progression"] == "blocked":
            raise ExclusionViolationError(f"Fel nem oldott MT-3 reject/review státuszú rekord kerülne az exportba: {r['record']}")
        if r["group_id"] in blocked_groups:
            raise ExclusionViolationError(f"Blokkolt tagot tartalmazó csoport rekordja kerülne az exportba: {r['record']} ({r['group_id']})")
    return te1_info, hashes, warnings


# ---------------------------------------------------------------------------
# az export felépítése és kiírása
# ---------------------------------------------------------------------------

def jdump(obj):
    return json.dumps(obj, ensure_ascii=False)


def build_export(convs, modes, data_kind, fixture):
    """Beszélgetések és minták részenként; a nem ábrázolhatók külön listában. Visszaad: (per_split, withheld)."""
    per_split = {s: {"convs": [], "samples": {m: [] for m in modes}} for s in SPLITS}
    withheld = []
    for c in convs:
        e = c["entry"]
        texts = [t["text"] for t in c["obj"]["turns"]]
        problems = renderable_problems(texts)
        built = {}
        if not problems:
            try:
                for mode in modes:
                    built[mode] = build_samples(c, mode, e["split"], data_kind, fixture)
            except Unrenderable as exc:
                problems.append(str(exc))
        if problems:
            withheld.append({"id": e["id"], "split": e["split"], "unit": e["unit"], "file": e["file"], "line": e["line"],
                             "reason": "nem ábrázolható veszteségmentesen: " + "; ".join(problems)})
            continue
        per_split[e["split"]]["convs"].append(c)
        for mode in modes:
            per_split[e["split"]]["samples"][mode].extend(built[mode])
    return per_split, withheld


def write_tsv(path, header, rows):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\t".join(header) + "\n")
        for r in rows:
            f.write("\t".join("" if v is None else str(v) for v in r) + "\n")


def split_stats(per_split, modes):
    out = {}
    for s in SPLITS:
        convs = per_split[s]["convs"]
        st = {"conversations": len(convs), "messages": sum(len(c["obj"]["turns"]) for c in convs),
              "units": len({c["entry"]["unit"] for c in convs}),
              "canonical_file": f"canonical_{s}.jsonl", "samples": {}}
        for mode in modes:
            sm = per_split[s]["samples"][mode]
            st["samples"][mode] = {
                "file": f"samples_{s}_{mode}.jsonl", "total": len(sm), "first_turn": sum(1 for x in sm if x["first_turn"]),
                "history_dependent": sum(1 for x in sm if not x["first_turn"]),
                "lossless": sum(1 for x in sm if x["lossless"]), "not_lossless": sum(1 for x in sm if not x["lossless"]),
                "content_truncated": sum(1 for x in sm if not x["content_complete"]),
                "dependency_not_covered": sum(1 for x in sm if x["dependency"] is not None and not x["dependency"]["covered"]),
                "history_chars_lost": sum(t["lost_chars"] for x in sm for t in x["history_truncation"]),
                "messages_truncated": sum(len(x["history_truncation"]) for x in sm),
            }
        out[s] = st
    return out


def check_run_name(stamp, fixture):
    """A futás-mappa neve elkülöníti a tesztadatot a valódi exporttól: fixture mód `fixture_` előtag, valódi módban tilos."""
    if not RUN_NAME_RE.match(stamp):
        raise OutputError(f"Érvénytelen futásnév: {stamp!r}")
    if fixture and not stamp.startswith("fixture_"):
        raise RefusedError("Tesztadat (fixture) exportjának futás-mappája `fixture_` előtagú kell legyen (tesztadat nem keverhető a valódi exporttal).")
    if not fixture and stamp.lower().startswith("fixture"):
        raise RefusedError("Valódi adat exportjának futás-mappája nem kezdődhet `fixture` előtaggal.")
    return stamp


def run_export(mt2_manifest, out_dir, mode, modes=DEFAULT_MODES, allow_no_te1=False, run_name=None):
    if mode not in ("dataset", "fixture"):
        raise RefusedError("A --mode értéke dataset vagy fixture kell legyen.")
    modes = tuple(modes)
    if not modes or len(set(modes)) != len(modes):
        raise RefusedError("A --modes nem lehet üres vagy ismétlődő.")
    for md in modes:
        if md == "R3":
            raise RefusedError(f"Az R3 nem állítható elő: {R3_REASON}")
        if md not in SUPPORTED_MODES:
            raise RefusedError(f"Ismeretlen renderelés: {md!r} (támogatott: {', '.join(SUPPORTED_MODES)})")
    memory_module()
    if not os.path.isfile(mt2_manifest):
        raise InputFileError(f"Az MT-2 manifest nem található: {mt2_manifest}")
    m, m_sha = load_mt2(mt2_manifest, mode)
    dep_paths = [mt2_manifest] + [_resolve(i["path"]) for i in m["inputs"]["conversation_files"]] + [_resolve(m["inputs"]["mt3_report"]["path"])]
    before = file_sha_map(dep_paths)
    fixture = mode == "fixture"
    data_kind = "fixture" if fixture else "dataset"
    convs, infos = load_sources(m, mode)
    te1_info, excluded_hashes, warnings = check_exclusions_and_status(m, convs, mode, allow_no_te1)
    for c in convs:                                                       # az MT-1 mód-védelem: a rekord jelölése egyezik a móddal
        if bool(c["obj"]["meta"].get("fixture")) != fixture:
            raise RefusedError(f"A rekord fixture-jelölése nem egyezik a móddal: {c['entry']['id']}")
    stamp = check_run_name(run_name or (("fixture_mt4_" if fixture else "mt4_") + datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")), fixture)
    try:
        out_abs = None
        guards = {os.path.dirname(p) for p in dep_paths}
        if m["inputs"].get("te1_export"):
            guards.add(_resolve(m["inputs"]["te1_export"]["run_dir"]))
        for g in sorted(guards):
            out_abs = te1.check_out_dir(out_dir, g)
    except te1.OutputPathError as exc:
        raise OutputError(str(exc))
    run_dir = os.path.join(out_abs, stamp)
    if os.path.exists(run_dir):
        raise OutputError(f"A futás-mappa már létezik, nem írom felül: {run_dir}")

    t0 = time.perf_counter()
    per_split, withheld = build_export(convs, modes, data_kind, fixture)
    stats = split_stats(per_split, modes)
    if file_sha_map(dep_paths) != before:
        raise ChangedInputError("Az MT-2 manifest, a beszélgetés-fájlok vagy az MT-3 jelentés a futás közben megváltozott (sha256 eltérés).")
    os.makedirs(run_dir)
    outputs = {}
    try:
        outputs = write_outputs(run_dir, per_split, withheld, modes, fixture)
        mem_sha = te1.sha256_file(MEMORY_PATH)
        mem = memory_module()
        manifest = {
            "tool": "tools/multiturn_export.py", "tool_version": TOOL_VERSION, "status": "completed",
            "created_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "git_commit": te1.git_commit(), "python": sys.version.split()[0],
            "data_kind": data_kind, "fixture": fixture, "training_data": False,
            "purpose": ("technikai próba mesterséges tesztadaton — NEM tanítóadat" if fixture else "előkészített export; nem tanítási engedély"),
            "statuses": {"split_approved": m["split_approved"], "content_verified": m["content_verified"], "training_ready": m["training_ready"],
                         "note": "az MT-2 manifest értékei változatlanul; az export sikere ezeket nem változtatja, a felsőbb manifestek érintetlenek",
                         "exportable": True},
            "config": {"mode": mode, "modes": list(modes), "unsupported_modes": {"R3": R3_REASON}, "splits": list(SPLITS),
                       "ordering": "a forrásfájlok MT-2 manifest szerinti sorrendje, azon belül sorrend; részenként külön fájl; az üzenetek sorrendje és szerepe változatlan",
                       "sample_rule": "assistant-fordulónként egy minta; R1: az utolsó előző váltás a memory.build_prompt_context szerint + teljes aktuális kérés + teljes cél; R2: a teljes beszélgetés a célig",
                       "label_format": "User: <szöveg>\\nAI: <szöveg>, blokkok között \\n\\n", "sample_id": "<beszélgetés>#<mód>#<célforduló>"},
            "render_reference": {"module": "src/memory.py", "sha256": mem_sha, "function": "build_prompt_context",
                                 "max_prompt_user_chars": mem.MAX_PROMPT_USER_CHARS, "max_prompt_reply_chars": mem.MAX_PROMPT_REPLY_CHARS,
                                 "imported_not_copied": True},
            "inputs": {"mt2_manifest": {"path": te1.rel_path(mt2_manifest), "sha256": m_sha, "tool_version": m["tool_version"],
                                        "assignment_sha256": m["assignment_sha256"], "groups_sha256": m["groups_sha256"], "mode": m["config"]["mode"]},
                       "conversation_files": infos, "mt3_report": m["inputs"]["mt3_report"], "te1_export": te1_info,
                       "exclusions": m["inputs"].get("exclusions"), "name_bank": m["inputs"]["name_bank"]},
            "exclusion_guard": {"te1_excluded_rows": (te1_info or {}).get("excluded_rows", []), "excluded_text_sha256": excluded_hashes,
                                "performed": te1_info is not None,
                                "rule": "a TE-1-ben kizárt sorok (instruction, input, output) nyírt szövege egyetlen exportált üzenetben sem szerepelhet; az azonosító nem ütközhet",
                                "held_back_from_mt2": len(m["held_back"])},
            "splits": stats,
            "expected_from_mt2": {s: {"conversations": m["splits"][s]["conversations"], "messages": m["splits"][s]["messages"],
                                      "samples_total": m["splits"][s]["samples_total"]} for s in SPLITS},
            "conversations": [{"id": c["entry"]["id"], "split": c["entry"]["split"], "unit": c["entry"]["unit"], "canonical_line": k + 1,
                               "exchanges": len(c["obj"]["turns"]) // 2, "messages": len(c["obj"]["turns"]),
                               "source": {"file": c["entry"]["file"], "line": c["entry"]["line"], "line_sha256": c["entry"]["line_sha256"]}}
                              for s in SPLITS for k, c in enumerate(per_split[s]["convs"])],
            "withheld": withheld, "outputs": outputs, "timing_seconds": {"render_and_write": round(time.perf_counter() - t0, 3)},
            "warnings": warnings + ([f"{len(withheld)} beszélgetés veszteségmentesen nem ábrázolható, visszatartva: lásd withheld.tsv"] if withheld else []),
            "limitations": LIMITATIONS, "disclaimer": DISCLAIMER,
            "training_ready": False, "content_verified": False, "split_approved": False,
        }
        partial = os.path.join(run_dir, MANIFEST_FILE + ".partial")
        with open(partial, "w", encoding="utf-8", newline="\n") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
            f.write("\n")
        problems = verify_export(partial, check_sources=True)
        if problems:
            raise VerificationError("A visszaolvasásos ellenőrzés hibát talált: " + "; ".join(problems[:10]) + (" ..." if len(problems) > 10 else ""))
        if file_sha_map(dep_paths) != before:
            raise ChangedInputError("A bemenet a kiírás közben megváltozott (sha256 eltérés).")
        os.replace(partial, os.path.join(run_dir, MANIFEST_FILE))
    except ExportError as exc:
        with open(os.path.join(run_dir, FAILED_FILE), "w", encoding="utf-8", newline="\n") as f:
            f.write(f"{type(exc).__name__}: {exc}\n")
        raise
    manifest["run_dir"] = run_dir
    return manifest


def write_outputs(run_dir, per_split, withheld, modes, fixture):
    outputs = {}

    def reg(name):
        p = os.path.join(run_dir, name)
        outputs[name] = {"sha256": te1.sha256_file(p), "bytes": os.path.getsize(p)}

    conv_rows, idx_rows = [], []
    for s in SPLITS:
        with open(os.path.join(run_dir, f"canonical_{s}.jsonl"), "wb") as f:
            for c in per_split[s]["convs"]:
                f.write(c["line"] + b"\n")
        reg(f"canonical_{s}.jsonl")
        for k, c in enumerate(per_split[s]["convs"]):
            e = c["entry"]
            conv_rows.append((e["id"], s, e["unit"], k + 1, len(c["obj"]["turns"]) // 2, len(c["obj"]["turns"]), e["file"], e["line"], e["line_sha256"]))
        for mode in modes:
            name = f"samples_{s}_{mode}.jsonl"
            with open(os.path.join(run_dir, name), "w", encoding="utf-8", newline="\n") as f:
                for n, smp in enumerate(per_split[s]["samples"][mode], 1):
                    f.write(jdump(smp) + "\n")
                    idx_rows.append((smp["sample_id"], s, mode, smp["conversation_id"], smp["unit"], smp["exchange"], smp["current_user_turn"],
                                     smp["target_turn"], int(smp["first_turn"]), int(smp["lossless"]), len(smp["history_truncation"]),
                                     "" if smp["dependency"] is None else int(smp["dependency"]["covered"]), smp["source"]["file"],
                                     smp["source"]["line"], smp["source"]["line_sha256"], name, n, sha256_text(smp["text"]), len(smp["text"])))
            reg(name)
    write_tsv(os.path.join(run_dir, CONVERSATION_INDEX),
              ["conversation", "split", "unit", "canonical_line", "exchanges", "messages", "source_file", "source_line", "source_line_sha256"], conv_rows)
    reg(CONVERSATION_INDEX)
    write_tsv(os.path.join(run_dir, EXPORT_INDEX),
              ["sample_id", "split", "mode", "conversation", "unit", "exchange", "current_user_turn", "target_turn", "first_turn", "lossless",
               "truncated_messages", "dependency_covered", "source_file", "source_line", "source_line_sha256", "samples_file", "samples_line",
               "text_sha256", "text_chars"], idx_rows)
    reg(EXPORT_INDEX)
    write_tsv(os.path.join(run_dir, WITHHELD_FILE), ["conversation", "split", "unit", "source_file", "source_line", "reason"],
              [(w["id"], w["split"], w["unit"], w["file"], w["line"], w["reason"]) for w in withheld])
    reg(WITHHELD_FILE)
    if fixture:
        with open(os.path.join(run_dir, FIXTURE_MARKER_FILE), "w", encoding="utf-8", newline="\n") as f:
            f.write("Ez az export MESTERSÉGES TESZTADATBÓL készült (fixture mód): technikai próba, NEM tanítóadat.\n"
                    "Tanításra, MT-5 betöltésre vagy bármilyen valódi felhasználásra nem használható.\n")
        reg(FIXTURE_MARKER_FILE)
    return outputs


# ---------------------------------------------------------------------------
# visszaolvasásos ellenőrzés a lemezről
# ---------------------------------------------------------------------------

def _read_lines(path):
    raw = te1.read_bytes(path)
    parts = raw.split(b"\n")
    if parts and parts[-1] == b"":
        parts.pop()
    return parts


def verify_export(manifest_path, check_sources=True):
    """A kiírt export ellenőrzése a lemezről: fájlok és ellenőrzőösszegek; kanonikus sorok a forrással; minták független
    visszaparse-olása a kanonikus beszélgetésekkel; szegmens-határok; részek szétválasztása; kizárások; státuszok; tesztadat-jelölés.
    Visszaad: problémák listája (üres: rendben)."""
    problems = []
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            man = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        return [f"az export manifest nem olvasható: {exc}"]
    run_dir = os.path.dirname(os.path.abspath(manifest_path))
    for key in ("tool", "status", "outputs", "conversations", "splits", "config", "data_kind", "fixture", "training_ready",
                "content_verified", "split_approved", "statuses", "exclusion_guard", "inputs"):
        if key not in man:
            return [f"hiányzó kulcs az export manifestben: {key}"]
    if man["tool"] != "tools/multiturn_export.py" or man["status"] != "completed":
        problems.append("az export manifest nem a MT-4 eszköz lezárt kimenete")
    for flag in ("training_ready", "content_verified", "split_approved"):
        if man[flag] is not False or man["statuses"].get(flag) is not False:
            problems.append(f"az export {flag} állapota nem false")
    if man.get("training_data") is not False:
        problems.append("az export manifest training_data értéke nem false")
    leftovers = sorted(n for n in os.listdir(run_dir) if n == FAILED_FILE)
    if leftovers:
        problems.append("az export mappában FAILED.txt van")
    modes = list(man["config"]["modes"])
    fixture = bool(man["fixture"])
    if (man["data_kind"] == "fixture") != fixture:
        problems.append("a data_kind és a fixture jelölés ellentmond")
    marker = os.path.join(run_dir, FIXTURE_MARKER_FILE)
    if fixture != os.path.isfile(marker):
        problems.append("a tesztadat-jelölő fájl megléte nem egyezik a fixture jelöléssel")
    if fixture and not os.path.basename(run_dir).startswith("fixture_"):
        problems.append("tesztadat export futás-mappája nem `fixture_` előtagú")
    for name, o in man["outputs"].items():
        p = os.path.join(run_dir, name)
        if not os.path.isfile(p):
            problems.append(f"hiányzó kimeneti fájl: {name}")
        elif te1.sha256_file(p) != o["sha256"] or os.path.getsize(p) != o["bytes"]:
            problems.append(f"a kimeneti fájl megváltozott: {name}")
    if problems:
        return problems
    excluded_hashes = set(man["exclusion_guard"]["excluded_text_sha256"])
    mem = memory_module()

    # kanonikus beszélgetések
    canon = {}
    order_ok = {}
    file_order = {i["path"]: n for n, i in enumerate(man["inputs"]["conversation_files"])}
    for s in SPLITS:
        lines = _read_lines(os.path.join(run_dir, f"canonical_{s}.jsonl"))
        expected = [c for c in man["conversations"] if c["split"] == s]
        if len(lines) != len(expected):
            problems.append(f"a canonical_{s}.jsonl sorainak száma ({len(lines)}) nem egyezik a manifesttel ({len(expected)})")
            continue
        last = (-1, -1)
        for k, (line, entry) in enumerate(zip(lines, expected)):
            line_c = line[:-1] if line.endswith(b"\r") else line
            if te1.sha256_bytes(line_c) != entry["source"]["line_sha256"]:
                problems.append(f"a kanonikus sor nem egyezik a forrássor ellenőrzőösszegével: {entry['id']}")
            try:
                obj = json.loads(line_c.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                problems.append(f"a kanonikus sor nem érvényes JSON: {entry['id']}")
                continue
            if obj.get("id") != entry["id"] or entry["canonical_line"] != k + 1:
                problems.append(f"a kanonikus sor azonosítója vagy sorszáma nem egyezik: {entry['id']}")
                continue
            if entry["id"] in canon:
                problems.append(f"a beszélgetés több részben is szerepel: {entry['id']}")
            texts = [t["text"] for t in obj["turns"]]
            roles = [t["role"] for t in obj["turns"]]
            if roles != ["user" if i % 2 == 0 else "assistant" for i in range(len(roles))] or len(roles) % 2:
                problems.append(f"a szerepek sorrendje nem user/assistant váltakozás: {entry['id']}")
            if obj["meta"].get("fixture") is not fixture:
                problems.append(f"a rekord meta.fixture jelölése nem egyezik az exporttal: {entry['id']}")
            for i, tx in enumerate(texts):
                if sha256_text(tx.strip()) in excluded_hashes:
                    problems.append(f"kizárt TE-1 sor szövege az exportban: {entry['id']} ({i}. üzenet)")
            key = (file_order.get(entry["source"]["file"], -1), entry["source"]["line"])
            if key < last:
                problems.append(f"a beszélgetések sorrendje nem a forrás sorrendje: {entry['id']}")
            last = key
            canon[entry["id"]] = {"obj": obj, "texts": texts, "split": s, "entry": entry, "n": len(texts) // 2}
            if obj["meta"]["n_exchanges"] != len(texts) // 2:
                problems.append(f"a meta.n_exchanges nem egyezik a fordulók számával: {entry['id']}")
    if len(canon) != len(man["conversations"]):
        problems.append("a kanonikus beszélgetések száma nem egyezik a manifesttel")
    # a források (a kijelölés és az érintetlenség)
    if check_sources:
        seen_files = {}
        for c in man["conversations"]:
            src = c["source"]
            path = _resolve(src["file"])
            if src["file"] not in seen_files:
                if not os.path.isfile(path):
                    problems.append(f"a forrásfájl hiányzik: {src['file']}")
                    seen_files[src["file"]] = None
                    continue
                seen_files[src["file"]] = te1.read_bytes(path).split(b"\n")
            lines = seen_files[src["file"]]
            if lines is None:
                continue
            if src["line"] < 1 or src["line"] > len(lines):
                problems.append(f"a forrássor nem létezik: {src['file']}:{src['line']}")
                continue
            ln = lines[src["line"] - 1]
            ln = ln[:-1] if ln.endswith(b"\r") else ln
            if te1.sha256_bytes(ln) != src["line_sha256"]:
                problems.append(f"a forrássor megváltozott: {src['file']}:{src['line']}")
    # minták
    per_conv_targets = {}
    seen_ids = set()
    idx_expected = []
    for s in SPLITS:
        for mode in modes:
            name = f"samples_{s}_{mode}.jsonl"
            lines = _read_lines(os.path.join(run_dir, name))
            prev_key = None
            for n, line in enumerate(lines, 1):
                try:
                    smp = json.loads(line.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    problems.append(f"{name}:{n} nem érvényes JSON")
                    continue
                cid = smp.get("conversation_id")
                c = canon.get(cid)
                if c is None or c["split"] != s or smp.get("split") != s:
                    problems.append(f"{name}:{n} a minta beszélgetése nincs ebben a részben: {cid}")
                    continue
                if smp.get("mode") != mode or smp.get("data_kind") != man["data_kind"] or smp.get("fixture") is not fixture:
                    problems.append(f"{name}:{n} a mód vagy a tesztadat-jelölés nem egyezik")
                if smp["sample_id"] in seen_ids or smp["sample_id"] != f"{cid}#{mode}#{smp['target_turn']}":
                    problems.append(f"{name}:{n} hibás vagy ismétlődő sample_id: {smp['sample_id']}")
                seen_ids.add(smp["sample_id"])
                t = smp["target_turn"]
                texts = c["texts"]
                if t % 2 != 1 or t >= len(texts) or smp["current_user_turn"] != t - 1 or smp["exchange"] != t // 2 + 1 or smp["n_exchanges"] != c["n"] \
                        or smp["first_turn"] != (t == 1):
                    problems.append(f"{name}:{n} a fordulóindexek nem egyeznek a beszélgetéssel: {smp['sample_id']}")
                    continue
                key = (c["entry"]["canonical_line"], t)
                if prev_key is not None and key <= prev_key:
                    problems.append(f"{name}:{n} a minták sorrendje nem a beszélgetés/forduló sorrend")
                prev_key = key
                per_conv_targets.setdefault((mode, cid), []).append(t)
                if smp["source"] != c["entry"]["source"] or smp["unit"] != c["entry"]["unit"]:
                    problems.append(f"{name}:{n} a visszakövetési adat nem egyezik a beszélgetéssel: {smp['sample_id']}")
                try:
                    parsed = parse_rendered(smp["text"])
                except ValueError as exc:
                    problems.append(f"{name}:{n} a minta szövege nem olvasható vissza: {exc}")
                    continue
                roles_ok = [r for r, _ in parsed] == ["user" if i % 2 == 0 else "assistant" for i in range(len(parsed))]
                if not roles_ok:
                    problems.append(f"{name}:{n} a minta szerepei nem váltakoznak")
                    continue
                tail_ok = [tx for _r, tx in parsed[-2:]] == texts[t - 1:t + 1]
                if not tail_ok:
                    problems.append(f"{name}:{n} az aktuális kérés vagy a cél nem egyezik a forrással: {smp['sample_id']}")
                if mode == "R2":
                    if [tx for _r, tx in parsed] != texts[:t + 1]:
                        problems.append(f"{name}:{n} az R2 szöveg nem a teljes forrás-előzmény: {smp['sample_id']}")
                else:
                    want_len = 2 if t == 1 else 4
                    if len(parsed) != want_len:
                        problems.append(f"{name}:{n} az R1 minta üzenetszáma nem {want_len}: {smp['sample_id']}")
                    history = [(texts[i], texts[i + 1]) for i in range(0, t - 1, 2)]
                    expect_ctx = mem.build_prompt_context(history) if history else ""
                    if not smp["text"].startswith(expect_ctx):
                        problems.append(f"{name}:{n} az R1 előtag nem egyezik a memory.build_prompt_context kimenetével: {smp['sample_id']}")
                    if len(parsed) == 4:
                        for (rr, got), src_i in zip(parsed[:2], (t - 3, t - 2)):
                            src_text = texts[src_i]
                            lim = mem.MAX_PROMPT_USER_CHARS if rr == "user" else mem.MAX_PROMPT_REPLY_CHARS
                            if got != src_text and not (got.endswith("...") and src_text.startswith(got[:-3]) and len(got) <= lim):
                                problems.append(f"{name}:{n} az R1 előzmény nem a forrás bájt-pontos vagy jelölt csonkolása: {smp['sample_id']}")
                # szegmensek
                segs = smp["messages"]
                want_turns = list(range(t + 1)) if mode == "R2" else ([t - 3, t - 2, t - 1, t] if t > 1 else [t - 1, t])
                if [g["turn"] for g in segs] != want_turns:
                    problems.append(f"{name}:{n} a szegmensek forduló-indexei nem egyeznek: {smp['sample_id']}")
                expect_text, expect_segs = render(mode, texts, t)
                if smp["text"] != expect_text or segs != expect_segs:
                    problems.append(f"{name}:{n} a minta nem egyezik a kanonikus beszélgetésből újrarenderelttel: {smp['sample_id']}")
                for g in segs:
                    frag = smp["text"][g["start"]:g["end"]]
                    want = texts[g["turn"]]
                    if g["complete"] != (frag == want):
                        problems.append(f"{name}:{n} a szegmens `complete` jelzője hibás: {smp['sample_id']} ({g['turn']}. üzenet)")
                    if g["role"] != ("user" if g["turn"] % 2 == 0 else "assistant"):
                        problems.append(f"{name}:{n} a szegmens szerepe hibás: {smp['sample_id']}")
                    if not g["complete"] and not (frag.endswith("...") and want.startswith(frag[:-3])):
                        problems.append(f"{name}:{n} a nem teljes szegmens nem jelölt csonkolás: {smp['sample_id']}")
                    if g["kind"] == "target" and (smp["target"]["start"], smp["target"]["end"]) != (g["start"], g["end"]):
                        problems.append(f"{name}:{n} a cél-szegmens nem egyezik a target mezővel")
                    if g["kind"] in ("current", "target") and not g["complete"]:
                        problems.append(f"{name}:{n} az aktuális kérés vagy a cél nem teljes: {smp['sample_id']}")
                tgt = smp["text"][smp["target"]["start"]:smp["target"]["end"]]
                if tgt != texts[t]:
                    problems.append(f"{name}:{n} a target span nem a teljes cél-üzenet: {smp['sample_id']}")
                content_complete = all(g["complete"] for g in segs)
                present = {g["turn"] for g in segs}
                dep = c["obj"]["meta"]["depends"]
                dentry = next((d for d in dep if d["turn"] == t), None)
                if (dentry is None) != (smp["dependency"] is None):
                    problems.append(f"{name}:{n} a dependency jelölés nem egyezik a meta.depends-szel: {smp['sample_id']}")
                covered = True
                if dentry is not None and smp["dependency"] is not None:
                    missing = sorted(i for i in dentry["on"] if i not in present)
                    covered = not missing
                    if smp["dependency"] != {"on": list(dentry["on"]), "depth": dentry["depth"], "covered": covered, "missing": missing}:
                        problems.append(f"{name}:{n} a dependency lefedettség hibás: {smp['sample_id']}")
                if smp["content_complete"] != content_complete or smp["lossless"] != (content_complete and covered):
                    problems.append(f"{name}:{n} a lossless jelzés hibás: {smp['sample_id']}")
                if mode == "R2" and not smp["lossless"]:
                    problems.append(f"{name}:{n} az R2 minta nem veszteségmentes: {smp['sample_id']}")
                if len(smp["history_truncation"]) != sum(1 for g in segs if not g["complete"]):
                    problems.append(f"{name}:{n} a csonkolás-lista nem egyezik a szegmensekkel: {smp['sample_id']}")
                for g in segs:
                    if sha256_text(smp["text"][g["start"]:g["end"]].strip()) in excluded_hashes:
                        problems.append(f"kizárt TE-1 sor szövege a mintában: {smp['sample_id']}")
                idx_expected.append((smp["sample_id"], s, mode, cid, smp["unit"], smp["exchange"], smp["current_user_turn"], t, int(smp["first_turn"]),
                                     int(smp["lossless"]), len(smp["history_truncation"]),
                                     "" if smp["dependency"] is None else int(smp["dependency"]["covered"]), smp["source"]["file"],
                                     smp["source"]["line"], smp["source"]["line_sha256"], name, n, sha256_text(smp["text"]), len(smp["text"])))
    for cid, c in canon.items():
        for mode in modes:
            got = per_conv_targets.get((mode, cid), [])
            if got != list(range(1, 2 * c["n"], 2)):
                problems.append(f"a(z) {cid} beszélgetés {mode} mintái hiányosak vagy hibás sorrendűek: {got}")
    # indexek
    idx_lines = _read_lines(os.path.join(run_dir, EXPORT_INDEX))
    rows = [ln.decode("utf-8").split("\t") for ln in idx_lines[1:]]
    if len(rows) != len(idx_expected):
        problems.append("az export_index.tsv sorainak száma nem egyezik a mintákkal")
    else:
        for got, want in zip(rows, idx_expected):
            if got != ["" if v is None else str(v) for v in want]:
                problems.append(f"az export_index.tsv sora nem egyezik a mintával: {want[0]}")
                break
    conv_lines = _read_lines(os.path.join(run_dir, CONVERSATION_INDEX))
    if len(conv_lines) - 1 != len(man["conversations"]):
        problems.append("a conversation_index.tsv sorainak száma nem egyezik a manifesttel")
    # darabszámok
    for s in SPLITS:
        st = man["splits"][s]
        if st["conversations"] != sum(1 for c in canon.values() if c["split"] == s) or st["messages"] != sum(len(c["texts"]) for c in canon.values() if c["split"] == s):
            problems.append(f"a manifest {s} részének beszélgetés-/üzenetszáma nem egyezik")
        for mode in modes:
            want = sum(c["n"] for c in canon.values() if c["split"] == s)
            if st["samples"][mode]["total"] != want or st["samples"][mode]["first_turn"] != st["conversations"]:
                problems.append(f"a manifest {s}/{mode} mintaszáma nem egyezik a képlettel")
    if len(man["withheld"]) == 0:
        for s in SPLITS:
            exp = man["expected_from_mt2"][s]
            st = man["splits"][s]
            if (exp["conversations"], exp["messages"]) != (st["conversations"], st["messages"]):
                problems.append(f"az export {s} része nem egyezik az MT-2 manifest darabszámaival")
            for mode in modes:
                if exp["samples_total"] != st["samples"][mode]["total"]:
                    problems.append(f"az export {s}/{mode} mintaszáma nem egyezik az MT-2 manifest mintaszámával")
    return problems


# ---------------------------------------------------------------------------
# parancssor
# ---------------------------------------------------------------------------

def _parse_modes(text):
    return tuple(x.strip().upper() for x in text.split(",") if x.strip())


def _main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description="MT-4: felosztott többfordulós beszélgetések renderelése és exportálása kizárási szűrővel "
                                            "(NEM tanítási engedély, NEM training-ready).")
    p.add_argument("--mode", choices=["dataset", "fixture"], help="Az adat fajtája: dataset (valódi) vagy fixture (tesztadat); egyeznie kell az MT-2 manifest módjával.")
    p.add_argument("--mt2-manifest", help="Az MT-2 split_manifest.json.")
    p.add_argument("--out-dir", help="Kimeneti szülőmappa (a futás új almappába kerül).")
    p.add_argument("--modes", type=_parse_modes, default=DEFAULT_MODES, help="Renderelések, vesszővel: R1,R2 (R3 nem támogatott).")
    p.add_argument("--allow-no-te1-comparison", action="store_true", help="Elfogad TE-1 összevetés nélküli MT-2 manifestet (figyelmeztetéssel).")
    p.add_argument("--run-name", default=None)
    p.add_argument("--verify-export", default=None, help="Egy korábbi export manifestjének visszaolvasásos ellenőrzése.")
    a = p.parse_args(argv)

    if a.verify_export:
        try:
            problems = verify_export(a.verify_export)
        except (OSError, json.JSONDecodeError, KeyError) as exc:
            print(f"HIBA: az export nem olvasható: {exc}", file=sys.stderr)
            return EXIT_INPUT
        except ExportError as exc:
            print(f"HIBA ({type(exc).__name__}): {exc}", file=sys.stderr)
            return exc.exit_code
        if problems:
            for pr in problems:
                print(f"HIBA: {pr}", file=sys.stderr)
            return EXIT_VERIFY
        print("Az export a lemezről visszaolvasva rendben van (tartalom, szerepek, beszélgetéshatárok, részek, kizárások, státuszok).")
        return 0
    if not (a.mode and a.mt2_manifest and a.out_dir):
        p.error("--mode, --mt2-manifest és --out-dir kötelező (vagy --verify-export)")
    try:
        man = run_export(a.mt2_manifest, a.out_dir, a.mode, a.modes, a.allow_no_te1_comparison, a.run_name)
    except ExportError as exc:
        print(f"HIBA ({type(exc).__name__}): {exc}", file=sys.stderr)
        return exc.exit_code
    print(f"MT-4 export kész: {man['run_dir']}")
    print(f"Adat: {man['data_kind']} | modes: {', '.join(man['config']['modes'])} | visszatartott (nem ábrázolható): {len(man['withheld'])}")
    for s in SPLITS:
        st = man["splits"][s]
        line = f"  {s:10} beszélgetés {st['conversations']:5} | üzenet {st['messages']}"
        for mode in man["config"]["modes"]:
            sm = st["samples"][mode]
            line += f" | {mode}: {sm['total']} minta (első fordulós {sm['first_turn']}, előzmény-függő {sm['history_dependent']}, veszteségmentes {sm['lossless']})"
        print(line)
    for w in man["warnings"]:
        print("  FIGYELEM:", w)
    print(DISCLAIMER)
    return EXIT_ATTENTION if man["warnings"] else 0


if __name__ == "__main__":
    sys.exit(_main())
