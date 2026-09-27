"""
MF-AI-Zero - MT-2: csoportokat egyben tartó, reprodukálható train/validation/test felosztás a többfordulós beszélgetésekre.

CÉL: a `tools/multiturn_validate.py` (MT-1) szerint turns-validált, az MT-3 (`tools/multiturn_dedupe.py`) által
ellenőrzött és csoportosított beszélgetésekből kijelöli, melyik beszélgetés melyik részbe kerül (terv: 800/100/100),
úgy, hogy egy csoport SOHA nem szakad szét. Nem generál adatot, nem tanít, nem ír felül és nem töröl forrásadatot,
és NEM állít training-ready állapotot: a kijelölés technikai előkészítés (`split_approved: false`), a jóváhagyás külön
felhasználói döntés.

ALAPELVEK
  * A felosztási egység a SZÁMÍTOTT csoport (MT-3 `mtg_...`), nem a deklarált `meta.split_group`. Az egység az MT-3
    csoportjaiból áll, amelyeket az MT-2 még összevon a dokumentált kivétellel (`accepted_with_exception`) felmentett
    párokkal is (ezek szöveges közelsége dokumentáltan tudott, ezért egy részben maradnak). Az MT-3 csoportjai már
    tartalmazzák a deklarált `split_group` és `persona` kapcsolatokat; ezt az MT-2 külön ellenőrzi.
  * Egy beszélgetés összes váltása, mintája és minden változata ugyanabba a részbe kerül.
  * A csoport-integritás fontosabb a pontos darabszámnál: ha a cél nem érhető el, az eltérést jelenti, csoportot nem vág szét.
  * Fel nem oldott MT-3 `reject`/`review` (haladási tiltás), az ilyen tagot tartalmazó csoport, a kizárási listán vagy
    kizárás-jelöléssel szereplő rekord NEM kerül kijelölésre (`held_back`), okkal jelentve.
  * Az MT-3 jelentésnek AKTUÁLISNAK kell lennie: ugyanazok a fájlok/ellenőrzőösszegek/rekordok, ugyanaz az MT-3 eszköz
    (verzió és a fájl ellenőrzőösszege), a bemenetek (TE-1 export, névtár, kivételek) változatlanok. Elavult jelentés
    hibával áll meg; régi eredményt az eszköz nem használ újra csendben.
  * Reprodukálható: az eredmény csak a bemenetektől, a beállításoktól és a `--seed` értéktől függ (nem a bemeneti fájlok
    vagy rekordok sorrendjétől), nem használ Python `random` modult, sem hash-véletlenítést; sha256-alapú sorrend.
  * A TE-1 exporttal talált kapcsolatokat (`export_links.json`) a későbbi TE-3 egyeztetéshez megőrzi; a részek közötti,
    csoportot nem kötő átfedések listázva vannak (`cross_split_overlaps.tsv`), így nincs "észrevétlen" átfedés.

ALGORITMUS (részletesen: docs/MULTITURN_SPLIT.md)
  1. egységek képzése (MT-3 csoportok + kivétel-párok egyesítése); visszatartások (blokkolt, kizárt);
  2. cél-darabszámok: a `--targets` (alap 800,100,100); ha a kijelölhető darabszám eltér, legnagyobb maradékos arányos
     skálázás (a jelentés mindkettőtől mutatja az eltérést);
  3. a 2+ tagú egységekre pontos (bitkészletes) dinamikus programozás: a validation/test darabszám lehető legkisebb eltéréssel
     elérhető részhalmaza; a konkrét választás sha256-alapú, determinisztikus sorrendben és súlyozott bejárással;
  4. az 1 tagú egységek (töltelék) kitöltik a hiányt;
  5. rétegzés (család, hosszsáv, domain, "nehéz"): azonos méretű egységek cseréje a részek között (a darabszám és a csoportok
     érintetlenek), a `--min-hard-test` minimum figyelembevételével;
  6. független ellenőrzés (nincs szétvágott csoport, nincs kijelölt blokkolt/kizárt rekord, stb.).

Használat:
    python tools/multiturn_split.py --mode dataset|fixture --conversations <f1.jsonl> [...] --mt3-report <dedupe_report.json>
        --out-dir <mappa> [--te1-export <TE-1 futás-mappa>] [--exclusions <lista>] [--targets 800,100,100]
        [--seed <szöveg>] [--min-hard-test auto|<szám>] [--no-stratify] [--allow-no-te1-comparison]
        [--name-bank <json>] [--run-name <név>]
    python tools/multiturn_split.py --verify-manifest <split_manifest.json>

Kilépési kódok: 0 kész, teljes és pontos; 1 kész, de figyelmet kér (visszatartott rekord, eltérés a célszámtól, teljesületlen
"nehéz" minimum, nincs TE-1 összevetés); 2 argumentumhiba; 10 bemeneti fájl hiba; 11 nem turns-validált rekord; 12 TE-1 export hiba;
13 kizárási lista hiba; 14 kimeneti útvonal hiba; 15 elavult/nem egyező MT-3 jelentés vagy megváltozott bemenet;
16 a bemenet a futás közben megváltozott; 17 a belső ellenőrzés hibát talált (nincs kimenet); 18 a manifest újraszámolással nem reprodukálható.
"""

import argparse
import datetime
import hashlib
import json
import math
import os
import re
import sys
import time
from collections import Counter

import dataset_export_chat_text as te2
import dataset_export_train as te1
import multiturn_dedupe as dd
import multiturn_validate as mt1

TOOL_VERSION = "mt2-1.0"
SPLITS = ("train", "validation", "test")
DEFAULT_TARGETS = (800, 100, 100)
DEFAULT_SEED = "mf-mt2-1"
PLAN_TOLERANCE = 0.02             # a terv: +-2% a csoportméret miatt (az összes tervezett darabszám arányában)
HARD_FAMILIES = {"F4", "F7"}      # felhasználói javítás, témavisszatérés
HARD_DEPTH = 2                    # előzmény-mélység >= 2
MIN_HARD_TEST_SHARE = 0.30        # a terv: legalább 30 "nehéz" a 100 teszt-beszélgetésből
LENGTH_BANDS = (("3-4", 3, 4), ("5-6", 5, 6), ("7-8", 7, 8))
FEATURES = ("family", "length", "domain", "hard")
MAX_PASSES = 40
HARD_PENALTY = 10.0
MT3_TOOL = "tools/multiturn_dedupe.py"
MT3_MIN_MAJOR = 2
EXCLUSION_ID_RE = re.compile(r"^[a-z][a-z0-9_]*$")

# az export-kapcsolatok besorolása (TE-3 egyeztetéshez)
DUPLICATE_LIKE = {"sample_exact", "sample_near", "sample_near_short", "sample_name_swapped", "sample_at_boundary"}
PARTIAL_OVERLAP = {"same_qa_different_context", "same_question_different_context",
                   "same_question_context_different_answer", "shared_answer_different_question"}

EXIT_ATTENTION = 1
EXIT_INPUT, EXIT_INVALID, EXIT_TE1, EXIT_EXCLUSIONS, EXIT_OUTPUT = 10, 11, 12, 13, 14
EXIT_STALE, EXIT_CHANGED_DURING, EXIT_VERIFY, EXIT_NOT_REPRODUCIBLE = 15, 16, 17, 18

DISCLAIMER = ("A felosztás technikai kijelölés: NEM jóváhagyott felosztás, NEM tartalmi ellenőrzés, NEM training-ready. "
              "A csoportok az MT-3 szöveges hasonlóságán alapulnak (nem bizonyított jelentésazonosság): az MT-3 által nem jelzett "
              "tartalmi átfedés részek között is előfordulhat. A tanításhoz a felosztást és a tartalmi ellenőrzést külön jóvá kell hagyni.")
LIMITATIONS = [
    "A csoportok az MT-3 szöveges hasonlóságán és a deklarált split_group/persona kapcsolatokon alapulnak: az átfogalmazott vagy jelentésben azonos, de szövegben eltérő beszélgetések (a kísérleti heurisztikán kívül) külön csoportba, így külön részbe kerülhetnek.",
    "A részek közötti szöveges átfedést az MT-3 jelzései alapján listázza (`cross_split_overlaps.tsv`); az információ-szintű (részleges) átfedések nem kötnek csoportot, csak jelentve vannak.",
    "A rétegzés legjobb szándékú (csoportmérethez kötött, azonos méretű egységek cseréje): kis mintán vagy sok nagy csoportnál a részek összetétele eltérhet az arányostól; az eltérés a manifestben látható. A csoport-integritás mindig előbbre való.",
    "A TE-1 exporttal talált kapcsolatokat az MT-3 jelentésből veszi át; a TE-3 (egyfordulós adat felosztása) még nem létezik, ezért a kapcsolatok egyeztetése későbbi feladat.",
    "A kizárási lista és a `quality_notes` kizárás-jelölés tartalmi döntéseit az eszköz nem értékeli, csak betartja: a TE-1 kizárt sorok tartalma a hasonlósági összevetés referenciájából hiányzik.",
]


class SplitError(Exception):
    exit_code = EXIT_INPUT


class InputFileError(SplitError):
    exit_code = EXIT_INPUT


class InvalidRecordsError(SplitError):
    exit_code = EXIT_INVALID


class Te1InputError(SplitError):
    exit_code = EXIT_TE1


class ExclusionsError(SplitError):
    exit_code = EXIT_EXCLUSIONS


class OutputError(SplitError):
    exit_code = EXIT_OUTPUT


class StaleReportError(SplitError):
    exit_code = EXIT_STALE


class ChangedInputError(SplitError):
    exit_code = EXIT_CHANGED_DURING


class VerificationError(SplitError):
    exit_code = EXIT_VERIFY


class NotReproducibleError(SplitError):
    exit_code = EXIT_NOT_REPRODUCIBLE


# ---------------------------------------------------------------------------
# determinisztikus sorrend és "véletlen" (sha256, nem a Python random modul)
# ---------------------------------------------------------------------------

def hkey(seed, label):
    return hashlib.sha256(f"{seed}|{label}".encode("utf-8")).hexdigest()


def unit_float(seed, label):
    """[0, 1) közötti determinisztikus szám sha256-ból (platform- és verziófüggetlen)."""
    return int(hkey(seed, label)[:13], 16) / float(16 ** 13)


def parse_targets(text):
    try:
        parts = [int(x) for x in str(text).replace(";", ",").split(",")]
    except ValueError:
        raise argparse.ArgumentTypeError("a --targets három egész szám vesszővel: pl. 800,100,100")
    if len(parts) != 3 or any(p < 0 for p in parts) or sum(parts) < 1:
        raise argparse.ArgumentTypeError("a --targets három nemnegatív egész (train,validation,test), az összeg legalább 1")
    return tuple(parts)


def scaled_ideal(total, targets):
    """Legnagyobb maradékos arányos darabszámok: a `total` darabot a `targets` arányában osztja (egész számokkal)."""
    s = sum(targets)
    if total == s:
        return list(targets)
    base = [total * t // s for t in targets]
    rem = [total * t % s for t in targets]
    for i in sorted(range(3), key=lambda k: (-rem[k], k))[:total - sum(base)]:
        base[i] += 1
    return base


# ---------------------------------------------------------------------------
# bemenetek: beszélgetések, kizárási lista, MT-3 jelentés
# ---------------------------------------------------------------------------

def file_sha_map(paths):
    return {p: te1.sha256_file(p) for p in paths}


def length_band(n_exchanges):
    for name, lo, hi in LENGTH_BANDS:
        if lo <= n_exchanges <= hi:
            return name
    return "other"


def load_conversations(paths, mode, bank):
    """MT-1 szerint turns-validált rekordok (a hibás bemenet hibával áll meg, ugyanúgy, mint az MT-3-nál).
    Egy rekord kulcsa a (fájl, sor); a sor ellenőrzőösszege a sor bájtjaiból (CR/LF nélkül) készül, mint az MT-3-nál."""
    records, infos, invalid = [], [], []
    for path in paths:
        if not os.path.isfile(path):
            raise InputFileError(f"A beszélgetés-fájl nem található: {path}")
        raw = te1.read_bytes(path)
        rel = te1.rel_path(path)
        info = {"path": rel, "sha256": te1.sha256_bytes(raw), "bytes": len(raw), "records": 0}
        for line_no, line in enumerate(raw.split(b"\n"), 1):
            line = line[:-1] if line.endswith(b"\r") else line
            if not line.strip():
                continue
            try:
                obj = json.loads(line.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise InputFileError(f"Hibás JSON sor: {rel}:{line_no} ({exc})")
            if not isinstance(obj, dict) or not isinstance(obj.get("id"), str):
                raise InputFileError(f"A sor nem beszélgetés-rekord (nincs id): {rel}:{line_no}")
            errs = [i for i in mt1.validate_record(obj, mode, bank) if i.severity == "error"]
            if errs:
                invalid.append(f"{rel}:{line_no} {obj['id']}: " + ", ".join(sorted({e.code for e in errs})))
                continue
            meta, turns = obj["meta"], obj["turns"]
            depth = max((d["depth"] for d in meta["depends"]), default=0)
            records.append({
                "index": len(records), "id": obj["id"], "file": rel, "line": line_no, "line_sha256": te1.sha256_bytes(line),
                "family": meta["family"], "domain": meta["domain"], "split_group": meta["split_group"], "persona": meta["persona"],
                "n_exchanges": len(turns) // 2, "messages": len(turns), "depth_max": depth,
                "hard": depth >= HARD_DEPTH or meta["family"] in HARD_FAMILIES,
                "marker": te1.EXCLUSION_NOTE_MARKER in obj["quality_notes"],
            })
            info["records"] += 1
        infos.append(info)
    if invalid:
        raise InvalidRecordsError("Nem turns-validált rekord(ok), a felosztás nem értelmezhető rajtuk (MT-1): "
                                  + "; ".join(invalid[:10]) + (" ..." if len(invalid) > 10 else ""))
    if not records:
        raise InputFileError("A bemeneti fájlokban nincs rekord.")
    keys = [(r["file"], r["line"]) for r in records]
    if len(set(keys)) != len(keys):
        raise InputFileError("Ugyanaz a fájl többször szerepel a bemenetek között.")
    return records, infos


def load_exclusions(path):
    """Kizárási lista (TE-1 alakú sorok: `azonosító | ok | szükséges felülvizsgálat`), pontos azonosítókkal."""
    if not os.path.isfile(path):
        raise ExclusionsError(f"A kizárási lista nem található: {path}")
    try:
        raw = te1.read_bytes(path)
        text = raw.decode("utf-8-sig")
    except (OSError, UnicodeDecodeError) as exc:
        raise ExclusionsError(f"A kizárási lista nem olvasható (UTF-8): {path} ({exc})")
    entries, seen = [], {}
    for line_no, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = [p.strip() for p in line.split(" | ", 2)]
        if len(parts) != 3 or not all(parts):
            raise ExclusionsError(f"Hibás kizárási sor ({path}:{line_no}): 'azonosító | ok | szükséges felülvizsgálat' várt")
        rid, reason, review = parts
        if not EXCLUSION_ID_RE.match(rid):
            raise ExclusionsError(f"Nem szabályos azonosító a kizárási listában ({path}:{line_no}): {rid!r} (csak pontos azonosító, wildcard nem)")
        if rid in seen:
            raise ExclusionsError(f"Duplikált azonosító a kizárási listában: {rid!r} ({path}:{seen[rid]} és :{line_no})")
        seen[rid] = line_no
        entries.append({"id": rid, "reason": reason, "review": review})
    if not entries:
        raise ExclusionsError(f"A kizárási lista nem tartalmaz bejegyzést: {path}")
    return entries, te1.sha256_bytes(raw)


def _major(version):
    m = re.match(r"^mt3-(\d+)\.", str(version))
    return int(m.group(1)) if m else -1


def load_mt3_report(report_path, conv_infos, records, mode, te1_export_dir=None, allow_no_te1=False):
    """Az MT-3 jelentés beolvasása és aktualitás-ellenőrzése. Bármilyen eltérés -> StaleReportError (nincs csendes újrahasznosítás)."""
    if not os.path.isfile(report_path):
        raise InputFileError(f"Az MT-3 jelentés nem található: {report_path}")
    try:
        raw = te1.read_bytes(report_path)
        rep = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise StaleReportError(f"Az MT-3 jelentés nem olvasható/érvénytelen JSON: {exc}")
    problems = []
    for key in ("tool", "tool_version", "status", "config", "inputs", "records", "groups", "findings", "summary"):
        if key not in rep:
            problems.append(f"hiányzó kulcs a jelentésben: {key}")
    if problems:
        raise StaleReportError("Az MT-3 jelentés nem értelmezhető: " + "; ".join(problems))
    if rep["tool"] != MT3_TOOL:
        problems.append(f"nem MT-3 jelentés (tool={rep['tool']!r})")
    if rep["status"] != "completed":
        problems.append(f"a jelentés státusza {rep['status']!r} (várt: completed)")
    if rep.get("training_ready") is not False or rep.get("content_verified") is not False:
        problems.append("a jelentés training_ready/content_verified értéke nem false")
    if _major(rep["tool_version"]) < MT3_MIN_MAJOR:
        problems.append(f"az MT-3 verzió ({rep['tool_version']}) a felülvizsgált döntési szabályok előtti: futtasd újra az MT-3-at")
    elif rep["tool_version"] != dd.TOOL_VERSION:
        problems.append(f"az MT-3 jelentés verziója ({rep['tool_version']}) nem egyezik a jelenlegi eszközével ({dd.TOOL_VERSION}): futtasd újra az MT-3-at")
    want_sha = te1.sha256_file(os.path.abspath(dd.__file__))
    if rep.get("tool_sha256") != want_sha:
        problems.append("az MT-3 jelentés nem az MT-3 eszköz jelenlegi fájljával készült (tool_sha256 eltér vagy hiányzik): futtasd újra az MT-3-at")
    cfg = rep["config"]
    if cfg.get("mode") != mode:
        problems.append(f"az MT-3 jelentés módja ({cfg.get('mode')!r}) nem egyezik a kért móddal ({mode!r})")
    rules = cfg.get("decision_rules", {})
    if rules.get("review_min") != dd.REVIEW_MIN or rules.get("reject_min") != dd.REJECT_MIN or cfg.get("grouping", {}).get("group_min") != dd.GROUP_MIN:
        problems.append("az MT-3 jelentés döntési/csoportosítási küszöbei nem egyeznek az eszközéivel")
    if cfg.get("declared_split_group_overrides_decision") is not False:
        problems.append("az MT-3 jelentés nem azt a szabályt rögzíti, hogy a deklarált csoport nem írja felül a döntést")
    # a bemenetek (fájlok, TE-1 export, névtár, kivétel-fájl) változatlansága
    try:
        changed = dd.verify_report(report_path)
    except (OSError, json.JSONDecodeError, KeyError) as exc:
        raise StaleReportError(f"Az MT-3 jelentés bemeneteinek ellenőrzése nem sikerült: {exc}")
    problems.extend(changed)
    # ugyanazok a beszélgetés-fájlok és rekordok
    rep_files = {(f["path"], f["sha256"]) for f in rep["inputs"]["conversation_files"]}
    our_files = {(i["path"], i["sha256"]) for i in conv_infos}
    if rep_files != our_files:
        problems.append("az MT-3 jelentés más beszélgetés-fájlokra (útvonal/ellenőrzőösszeg) készült, mint a felosztás bemenete")
    rep_records = {}
    for r in rep["records"]:
        rep_records[(r["file"], r["line"])] = r
    our = {(r["file"], r["line"]): r for r in records}
    if set(rep_records) != set(our):
        problems.append("az MT-3 jelentés rekordkészlete nem egyezik a felosztás bemenetével")
    else:
        for key, r in our.items():
            e = rep_records[key]
            if e.get("line_sha256") != r["line_sha256"] or e.get("record") != r["id"]:
                problems.append(f"az MT-3 jelentés rekordja eltér a bemenettől: {key[0]}:{key[1]}")
                break
            if not e.get("group_id"):
                problems.append(f"csoport nélküli rekord az MT-3 jelentésben: {key[0]}:{key[1]} ({r['id']})")
                break
    # TE-1 összevetés
    exp = rep["inputs"].get("te1_export")
    if exp is None and not allow_no_te1:
        problems.append("az MT-3 jelentés nem tartalmaz TE-1 export összevetést: a részek közötti átfedés az egyfordulós adattal szemben nem vizsgált "
                        "(futtasd újra az MT-3-at --te1-export értékkel, vagy kifejezetten --allow-no-te1-comparison)")
    if exp is not None and te1_export_dir is not None:
        if te1.rel_path(te1_export_dir) != exp["run_dir"]:
            problems.append("a megadott TE-1 export nem az, amelyre az MT-3 jelentés készült")
    if exp is None and te1_export_dir is not None:
        problems.append("TE-1 exportot adtál meg, de az MT-3 jelentés nélküle készült: az összevetés nem történt meg")
    if problems:
        raise StaleReportError("Elavult vagy nem egyező MT-3 jelentés: " + "; ".join(problems))
    return rep, {"path": te1.rel_path(report_path), "sha256": te1.sha256_bytes(raw), "tool_version": rep["tool_version"],
                 "tool_sha256": rep["tool_sha256"], "created_utc": rep.get("created_utc"), "git_commit": rep.get("git_commit"),
                 "records": len(rep["records"]), "groups": len(rep["groups"]), "blocked_records": rep["summary"]["blocked_records"],
                 "comparison": cfg["decision_rules"].get("comparison")}


def load_te1_reference(rep, te1_export_dir):
    """A TE-1 export azonosítói és a kizárt sorok azonosítói (nyomonkövetéshez, azonosító-ütközés vizsgálathoz)."""
    exp = rep["inputs"].get("te1_export")
    if exp is None:
        return None
    run_dir = te1_export_dir or (exp["run_dir"] if os.path.isabs(exp["run_dir"]) else os.path.join(te1.REPO_ROOT, exp["run_dir"]))
    try:
        manifest, manifest_sha, rows = te2.load_te1_export(run_dir)
    except te2.Te1ExportError as exc:
        raise Te1InputError(str(exc))
    if manifest_sha != exp["manifest_sha256"]:
        raise StaleReportError("A TE-1 export manifestje nem egyezik az MT-3 jelentésben rögzítettel.")
    excluded = [e["id"] for e in manifest.get("exclusion_list", {}).get("entries", [])]
    return {"run_dir": exp["run_dir"], "manifest_sha256": manifest_sha, "rows": len(rows), "row_ids": {r["id"] for r in rows},
            "excluded_ids": excluded, "export_file_sha256": exp["export_file_sha256"], "index_file_sha256": exp["index_file_sha256"]}


# ---------------------------------------------------------------------------
# egységek, visszatartások
# ---------------------------------------------------------------------------

class UnionFind:
    def __init__(self, items):
        self.parent = {x: x for x in items}

    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[max(ra, rb)] = min(ra, rb)


def build_units(records, rep, exclusions, te1_ref):
    """Egységek (felosztási csoportok) és visszatartások. Visszaad: (units, held, checks)
    units: {unit_id: {"members": [rec], "assignable": [rec], "mt3_groups": [...], "merged": bool}}
    held: {rec_index: {"reasons": [...], "findings": [...]}}"""
    key_of = {(r["file"], r["line"]): r for r in records}
    entry = {(e["file"], e["line"]): e for e in rep["records"]}
    gid_of = {r["index"]: entry[(r["file"], r["line"])]["group_id"] for r in records}
    # a jelentés csoport-tagságának önellenőrzése
    by_gid = {}
    for r in records:
        by_gid.setdefault(gid_of[r["index"]], []).append(r)
    for gid, ms in by_gid.items():
        want = sorted(rep["groups"].get(gid, {}).get("members", []))
        if sorted(m["id"] for m in ms) != want:
            raise StaleReportError(f"Az MT-3 jelentés csoportjai nem egyeznek a rekordok csoport-azonosítóival ({gid})")
    for gid in rep["groups"]:
        if gid not in by_gid:
            raise StaleReportError(f"Az MT-3 jelentés olyan csoportot tartalmaz, amelynek nincs rekordja a bemenetben: {gid}")
    # a deklarált split_group és persona kapcsolatnak benne kell lennie az MT-3 csoportokban
    for label, attr in (("split_group", "split_group"), ("persona", "persona")):
        seen = {}
        for r in records:
            v = r[attr]
            if not v:
                continue
            if v in seen and gid_of[seen[v]["index"]] != gid_of[r["index"]]:
                raise StaleReportError(f"Az MT-3 csoportok nem tartalmazzák a közös {label} ({v}) kapcsolatát: {seen[v]['id']} - {r['id']} (elavult jelentés?)")
            seen.setdefault(v, r)
    # egyesítés a dokumentált kivétellel felmentett párokkal
    uf = UnionFind(list(by_gid))
    merged_pairs = []
    for f in rep["findings"]:
        if f.get("status") != "accepted_with_exception":
            continue
        a, b = f["a"], f["b"]
        if a.get("source") == "conversation" and b.get("source") == "conversation":
            ka, kb = (a["file"], a["line"]), (b["file"], b["line"])
            if ka in key_of and kb in key_of and gid_of[key_of[ka]["index"]] != gid_of[key_of[kb]["index"]]:
                uf.union(gid_of[key_of[ka]["index"]], gid_of[key_of[kb]["index"]])
                merged_pairs.append((key_of[ka]["id"], key_of[kb]["id"], f.get("type")))
    unit_members = {}
    for gid, ms in by_gid.items():
        unit_members.setdefault(uf.find(gid), {"mt3_groups": [], "members": []})
        unit_members[uf.find(gid)]["mt3_groups"].append(gid)
        unit_members[uf.find(gid)]["members"].extend(ms)
    units = {}
    for root, u in unit_members.items():
        u["mt3_groups"].sort()
        uid = u["mt3_groups"][0]
        u["members"].sort(key=lambda r: (r["id"], r["file"], r["line"]))
        u["merged"] = len(u["mt3_groups"]) > 1
        units[uid] = u
    # visszatartások
    held = {}

    def hold(r, reason, findings=None):
        h = held.setdefault(r["index"], {"reasons": [], "findings": []})
        if reason not in h["reasons"]:
            h["reasons"].append(reason)
        for fid in findings or []:
            if fid not in h["findings"]:
                h["findings"].append(fid)

    excl_ids = {e["id"]: e for e in (exclusions or [])}
    known = {r["id"] for r in records}
    unknown = sorted(set(excl_ids) - known)
    if unknown:
        raise ExclusionsError("A kizárási lista olyan azonosítót tartalmaz, amely nincs a bemenetben (elavult lista?): " + ", ".join(unknown))
    te1_excluded = set(te1_ref["excluded_ids"]) if te1_ref else set()
    for uid, u in units.items():
        blocked = [r for r in u["members"] if entry[(r["file"], r["line"])]["progression"] == "blocked"]
        for r in u["members"]:
            e = entry[(r["file"], r["line"])]
            if e["progression"] == "blocked":
                hold(r, "mt3_blocked", e.get("blocking_findings"))
            elif blocked:
                hold(r, "group_has_blocked_member", [fid for b in blocked for fid in entry[(b["file"], b["line"])].get("blocking_findings", [])])
            if r["id"] in excl_ids:
                hold(r, "excluded_list")
            if r["marker"]:
                hold(r, "excluded_marker")
            if te1_ref and r["id"] in te1_excluded:
                hold(r, "id_collides_with_te1_excluded_row")
    for uid, u in units.items():
        u["assignable"] = [r for r in u["members"] if r["index"] not in held]
    return units, held, {"merged_pairs": merged_pairs, "excluded_list_ids": sorted(excl_ids)}


# ---------------------------------------------------------------------------
# a kijelölés: dinamikus programozás + rétegzés (tiszta függvények)
# ---------------------------------------------------------------------------

def unit_features(members):
    c = Counter()
    for r in members:
        c["family:" + r["family"]] += 1
        c["length:" + length_band(r["n_exchanges"])] += 1
        c["domain:" + r["domain"]] += 1
        c["hard:" + ("hard" if r["hard"] else "routine")] += 1
    return c


def best_fill(a, b, s1, ideal):
    """Az 1 tagú egységekből (töltelék) a validation/test részbe kerülő (x, y) darabszám, ha a 2+ tagú egységekből
    már a (validation) és b (test) van. A három eltérés (train, validation, test) abszolút összegének PONTOS minimuma:
    a célfüggvény konvex és szakaszonként lineáris, ezért a minimum a töréspont-egyenesek metszéspontjai (és a háromszög
    csúcsai) között van. Döntetlennél a kisebb legnagyobb eltérés, majd a kisebb (x, y) nyer."""
    n_train, n_val, n_test = ideal
    total = sum(ideal)
    x0, y0, z0 = n_val - a, n_test - b, total - a - b - n_train      # a három töréspont-egyenes (x=x0, y=y0, x+y=z0) egy pontban, (x0, y0)-nál metszi egymást
    cands = [(0, 0), (0, y0), (0, s1), (0, z0), (x0, 0), (s1, 0), (z0, 0), (x0, y0), (x0, s1 - x0), (s1 - y0, y0)]
    best = None
    for x, y in cands:
        if x < 0 or y < 0 or x + y > s1:
            continue
        devs = (abs(total - (a + x) - (b + y) - n_train), abs(a + x - n_val), abs(b + y - n_test))
        cand = (sum(devs), max(devs), x, y)
        if best is None or cand < best:
            best = cand
    return best[2], best[3], best[0]


def _dp_choose_counts(multi, ideal, s1):
    """A 2+ tagú egységekből választható (validation, test) darabszám-pár közül a legkisebb eltérésűt adja (a töltelékkel együtt).
    A bitkészlet: reach[a] bitjei a lehetséges test-darabszámok. Az (ideális + legnagyobb egység) korlát nem veszít optimumot:
    a korláton túli egység a train részbe téve az összeltérést nem növeli."""
    n_train, n_val, n_test = ideal
    maxs = max((u["size"] for u in multi), default=0)
    cap_v, cap_t = n_val + maxs, n_test + maxs
    mask = (1 << (cap_t + 1)) - 1
    reach = [0] * (cap_v + 1)
    reach[0] = 1
    for u in multi:
        s = u["size"]
        new = list(reach)
        for a in range(cap_v + 1):
            r = reach[a]
            if not r:
                continue
            new[a] |= (r << s) & mask                  # test
            if a + s <= cap_v:
                new[a + s] |= r                        # validation
        reach = new
    total = sum(ideal)
    multi_total = sum(u["size"] for u in multi)
    best = None
    for a in range(cap_v + 1):
        r = reach[a]
        if not r:
            continue
        for b in range(cap_t + 1):
            if not (r >> b) & 1:
                continue
            x, y, cost = best_fill(a, b, s1, ideal)
            devs = (abs(total - (a + x) - (b + y) - n_train), abs(a + x - n_val), abs(b + y - n_test))
            # döntetlennél a több tagú egységek arányos részesedése (különben a csoportok mind a train részbe kerülnének)
            prop = abs(a * total - n_val * multi_total) + abs(b * total - n_test * multi_total)
            cand = (cost, max(devs), prop, a, b)
            if best is None or cand < best:
                best = cand
    return best[3], best[4], cap_v, cap_t


def assign_units(units, ideal, seed, stratify=True, min_hard_test=0):
    """Egységek kijelölése részekhez. units: [{"id","size","feats": Counter}], ideal: (train, validation, test) darabszámok,
    összegük az egységek méretének összege. Visszaad: (assignment {id: split}, info). Csoportot nem vág szét."""
    total = sum(u["size"] for u in units)
    if sum(ideal) != total:
        raise ValueError("az ideális darabszámok összege nem egyezik a kijelölhető rekordok számával")
    n_train, n_val, n_test = ideal
    rank = {u["id"]: k for k, u in enumerate(sorted(units, key=lambda u: (hkey(seed, "order|" + u["id"]), u["id"])))}
    ordered = sorted(units, key=lambda u: rank[u["id"]])
    multi = [u for u in ordered if u["size"] >= 2]
    singles = [u for u in ordered if u["size"] == 1]
    assign = {}
    info = {"multi_units": len(multi), "single_units": len(singles)}
    if not units:
        return assign, dict(info, dp_target=None, stratification=None)
    a_star, b_star, cap_v, cap_t = _dp_choose_counts(multi, ideal, len(singles))
    info["dp_target"] = {"validation_from_multi": a_star, "test_from_multi": b_star}
    m = len(multi)
    can = [None] * (m + 1)
    can[m] = [0] * (cap_v + 1)
    can[m][a_star] = 1 << b_star
    for i in range(m - 1, -1, -1):
        s, nxt = multi[i]["size"], can[i + 1]
        cur = [0] * (cap_v + 1)
        for a in range(cap_v + 1):
            v = nxt[a] | (nxt[a] >> s)
            if a + s <= cap_v:
                v |= nxt[a + s]
            cur[a] = v
        can[i] = cur
    if m and not (can[0][0] & 1):
        raise VerificationError("belső hiba: a dinamikus programozás célállapota nem érhető el")
    a = b = 0
    weights = {"train": max(n_train, 0) + 1e-9, "validation": max(n_val, 0) + 1e-9, "test": max(n_test, 0) + 1e-9}
    for i, u in enumerate(multi):
        s, nxt = u["size"], can[i + 1]
        options = []
        if (nxt[a] >> b) & 1:
            options.append("train")
        if a + s <= cap_v and (nxt[a + s] >> b) & 1:
            options.append("validation")
        if b + s <= cap_t and (nxt[a] >> (b + s)) & 1:
            options.append("test")
        if not options:
            raise VerificationError("belső hiba: nincs érvényes választás a dinamikus programozás bejárásában")
        tot = sum(weights[o] for o in options)
        x, acc, pick = unit_float(seed, "walk|" + u["id"]) * tot, 0.0, options[-1]
        for o in options:
            acc += weights[o]
            if x < acc:
                pick = o
                break
        assign[u["id"]] = pick
        if pick == "validation":
            a += s
        elif pick == "test":
            b += s
    x_need, y_need, _cost = best_fill(a, b, len(singles), ideal)
    for k, u in enumerate(singles):
        assign[u["id"]] = "test" if k < y_need else ("validation" if k < y_need + x_need else "train")
    info["stratification"] = stratify_assignment(units, assign, ideal, rank, min_hard_test) if stratify else None
    return assign, info


def stratify_assignment(units, assign, ideal, rank, min_hard_test):
    """Azonos méretű egységek cseréje a részek között a jellemzők (család, hosszsáv, domain, nehéz) arányosabb eloszlásáért.
    A darabszám és az egységek érintetlenek. Determinisztikus. Visszaad: {loss_before, loss_after, swaps, passes}."""
    total = sum(u["size"] for u in units)
    by_id = {u["id"]: u for u in units}
    size = dict(zip(SPLITS, ideal))
    tot = Counter()
    for u in units:
        tot.update(u["feats"])
    exp = {s: {k: tot[k] * size[s] / total for k in tot} for s in SPLITS}
    cnt = {s: Counter() for s in SPLITS}
    members = {s: [] for s in SPLITS}
    for uid, s in assign.items():
        cnt[s].update(by_id[uid]["feats"])
        members[s].append(uid)
    for s in SPLITS:
        members[s].sort(key=lambda uid: rank[uid])
    sig = {u["id"]: tuple(sorted(u["feats"].items())) for u in units}

    def cell(s, k, obs):
        e = exp[s][k]
        return (obs - e) ** 2 / max(e, 1.0)

    def pen(h):
        return HARD_PENALTY * max(0, min_hard_test - h) ** 2

    def loss():
        v = sum(cell(s, k, cnt[s][k]) for s in SPLITS for k in tot)
        return v + pen(cnt["test"]["hard:hard"])

    before = loss()
    swaps = passes = 0
    for passes in range(1, MAX_PASSES + 1):
        improved = False
        for A in ("test", "validation"):
            for uid in list(members[A]):
                fu = by_id[uid]["feats"]
                best = None
                for B in SPLITS:
                    if B == A:
                        continue
                    seen_sig = set()                                       # azonos jellemzőjű egység azonos deltát ad: elég az elsőt vizsgálni
                    for vid in members[B]:
                        if by_id[vid]["size"] != by_id[uid]["size"] or sig[vid] in seen_sig:
                            continue
                        seen_sig.add(sig[vid])
                        fv = by_id[vid]["feats"]
                        delta = 0.0
                        for k in set(fu) | set(fv):
                            d = fv.get(k, 0) - fu.get(k, 0)
                            if d:
                                delta += cell(A, k, cnt[A][k] + d) - cell(A, k, cnt[A][k])
                                delta += cell(B, k, cnt[B][k] - d) - cell(B, k, cnt[B][k])
                        dh = fv.get("hard:hard", 0) - fu.get("hard:hard", 0)
                        if dh:
                            if A == "test":
                                delta += pen(cnt["test"]["hard:hard"] + dh) - pen(cnt["test"]["hard:hard"])
                            elif B == "test":
                                delta += pen(cnt["test"]["hard:hard"] - dh) - pen(cnt["test"]["hard:hard"])
                        if delta < -1e-9 and (best is None or delta < best[0] - 1e-12):
                            best = (delta, B, vid)
                if best:
                    _d, B, vid = best
                    fv = by_id[vid]["feats"]
                    cnt[A].subtract(fu)
                    cnt[A].update(fv)
                    cnt[B].subtract(fv)
                    cnt[B].update(fu)
                    members[A][members[A].index(uid)] = vid
                    members[B][members[B].index(vid)] = uid
                    members[A].sort(key=lambda x: rank[x])
                    members[B].sort(key=lambda x: rank[x])
                    assign[uid], assign[vid] = B, A
                    swaps += 1
                    improved = True
        if not improved:
            break
    return {"enabled": True, "loss_before": round(before, 6), "loss_after": round(loss(), 6), "swaps": swaps, "passes": passes}


# ---------------------------------------------------------------------------
# statisztika, kapcsolatok, ellenőrzés
# ---------------------------------------------------------------------------

def split_stats(assigned, unit_of):
    """Részenkénti darabszámok: beszélgetés, üzenet, minta (első fordulós és előzmény-függő külön), eloszlások."""
    out = {}
    for s in SPLITS:
        rs = [r for r in assigned if r["split"] == s]
        units = {unit_of[r["index"]] for r in rs}
        unit_sizes = Counter(unit_of[r["index"]] for r in rs)
        samples = sum(r["n_exchanges"] for r in rs)
        out[s] = {
            "conversations": len(rs), "messages": sum(r["messages"] for r in rs),
            "samples_total": samples, "samples_first_turn": len(rs), "samples_history_dependent": samples - len(rs),
            "units": len(units), "units_multi_member": sum(1 for n in unit_sizes.values() if n >= 2),
            "hard": sum(1 for r in rs if r["hard"]),
            "family": dict(sorted(Counter(r["family"] for r in rs).items())),
            "length": dict(sorted(Counter(length_band(r["n_exchanges"]) for r in rs).items())),
            "domain": dict(sorted(Counter(r["domain"] for r in rs).items())),
        }
    return out


def cross_split_overlaps(rep, key_of, split_of, unit_of):
    """Az MT-3 jelzései közül azok a rekordpárok, amelyek különböző részbe kerültek (csoportot nem kötő átfedések)."""
    out = []
    for f in rep["findings"]:
        if f["scope"] not in ("conversation", "sample"):
            continue
        a, b = f["a"], f["b"]
        if a.get("source") != "conversation" or b.get("source") != "conversation":
            continue
        ka, kb = (a["file"], a["line"]), (b["file"], b["line"])
        if ka not in key_of or kb not in key_of:
            continue
        ra, rb = key_of[ka], key_of[kb]
        sa, sb = split_of.get(ra["index"]), split_of.get(rb["index"])
        if sa is None or sb is None or sa == sb:
            continue
        out.append({"finding_id": f["finding_id"], "type": f["type"], "status": f["status"], "score": f["score"],
                    "level": "decision" if f["status"] in ("reject", "review", "accepted_with_exception") else "info",
                    "a": ra["id"], "a_turn": a.get("turn"), "a_split": sa, "a_unit": unit_of[ra["index"]],
                    "b": rb["id"], "b_turn": b.get("turn"), "b_split": sb, "b_unit": unit_of[rb["index"]],
                    "at_boundary": f.get("at_boundary", False)})
    out.sort(key=lambda o: (o["level"] != "decision", o["type"], o["a"], o["b"], o["finding_id"]))
    return out


def build_export_links(rep, key_of, split_of, unit_of, held):
    """A TE-1 exporttal talált kapcsolatok (TE-3 egyeztetéshez): melyik beszélgetés-csoport melyik részbe került."""
    links, rows = [], {}
    for f in rep["findings"]:
        if f["scope"] != "export":
            continue
        conv, exp = (f["a"], f["b"]) if f["a"].get("source") == "conversation" else (f["b"], f["a"])
        if conv.get("source") != "conversation" or exp.get("source") != "te1_export":
            continue
        r = key_of.get((conv["file"], conv["line"]))
        if r is None:
            continue
        strength = "duplicate_like" if f["type"] in DUPLICATE_LIKE else "partial_overlap"
        split = split_of.get(r["index"])
        link = {"finding_id": f["finding_id"], "type": f["type"], "status": f["status"], "score": f["score"], "strength": strength,
                "conversation_record": r["id"], "conversation_turn": conv.get("turn"), "unit": unit_of[r["index"]],
                "conversation_split": split if split else "held_back", "te1_row": exp["record"],
                "te1_source": {"file": exp.get("file"), "line": exp.get("line")}}
        links.append(link)
        row = rows.setdefault(exp["record"], {"links": 0, "splits": set(), "units": set(), "pending_units": set()})
        row["links"] += 1
        if strength == "duplicate_like":
            if split:
                row["splits"].add(split)
                row["units"].add(unit_of[r["index"]])
            else:
                row["pending_units"].add(unit_of[r["index"]])
    links.sort(key=lambda l: (l["strength"] != "duplicate_like", l["te1_row"], l["conversation_record"], l["conversation_turn"] or 0, l["finding_id"]))
    te1_rows, conflicts = {}, []
    for rid, row in sorted(rows.items()):
        splits = sorted(row["splits"])
        te1_rows[rid] = {"links": row["links"], "required_split": splits[0] if len(splits) == 1 else None, "conflict": len(splits) > 1,
                         "assigned_units": sorted(row["units"]), "pending_units": sorted(row["pending_units"])}
        if len(splits) > 1:
            conflicts.append({"te1_row": rid, "splits": splits, "units": sorted(row["units"])})
    summary = {"links": len(links), "duplicate_like": sum(1 for l in links if l["strength"] == "duplicate_like"),
               "partial_overlap": sum(1 for l in links if l["strength"] == "partial_overlap"),
               "te1_rows_linked": len(te1_rows), "te1_rows_with_required_split": sum(1 for v in te1_rows.values() if v["required_split"]),
               "conflicts": len(conflicts), "links_to_held_back_conversations": sum(1 for l in links if l["conversation_split"] == "held_back")}
    return {"note": ("A TE-3 (egyfordulós adat felosztása) még nem létezik. A `duplicate_like` kapcsolatú TE-1 sort a TE-3-nak abba a részbe kell "
                     "tennie, amelybe a kapcsolódó beszélgetés-csoport került (`required_split`), különben a közeli másolat részek között oszlik meg; "
                     "a `partial_overlap` csak tájékoztató. Ellentmondás (`conflict`) esetén döntés kell. A visszatartott beszélgetéshez kötött sor "
                     "(`pending_units`) függőben van."),
            "summary": summary, "te1_rows": te1_rows, "conflicts": conflicts, "links": links}


def verify_split(records, rep, assign_by_index, held, unit_of, exclusions, key_of):
    """Független ellenőrzés a nyers adatokon (nem az algoritmus köztes szerkezetein)."""
    entry = {(e["file"], e["line"]): e for e in rep["records"]}
    checks = {}
    ids = set(assign_by_index) | set(held)
    checks["all_records_accounted_for"] = ids == {r["index"] for r in records} and not (set(assign_by_index) & set(held))
    checks["held_back_have_reasons"] = all(h["reasons"] for h in held.values())
    checks["no_unit_split_across_parts"] = all(len({assign_by_index[i] for i in assign_by_index if unit_of[i] == u}) == 1
                                               for u in {unit_of[i] for i in assign_by_index})
    gid_of = {r["index"]: entry[(r["file"], r["line"])]["group_id"] for r in records}
    checks["mt3_groups_not_split"] = all(len({assign_by_index[i] for i in assign_by_index if gid_of[i] == g}) == 1
                                         for g in {gid_of[i] for i in assign_by_index})
    for name, attr in (("declared_split_groups_not_split", "split_group"), ("personas_not_split", "persona")):
        seen, ok = {}, True
        for r in records:
            if r["index"] in assign_by_index and r[attr]:
                if seen.setdefault(r[attr], assign_by_index[r["index"]]) != assign_by_index[r["index"]]:
                    ok = False
        checks[name] = ok
    ok_edges, ok_exc, ok_dec = True, True, True
    ids_to_idx = {}
    for r in records:
        ids_to_idx.setdefault(r["id"], []).append(r["index"])
    for g in rep["groups"].values():
        for e in g["edges"]:
            ia, ib = ids_to_idx.get(e["a"], []), ids_to_idx.get(e["b"], [])
            if len(ia) == 1 and len(ib) == 1 and ia[0] in assign_by_index and ib[0] in assign_by_index:
                if assign_by_index[ia[0]] != assign_by_index[ib[0]]:
                    ok_edges = False
    for f in rep["findings"]:
        a, b = f["a"], f["b"]
        if a.get("source") == "conversation" and b.get("source") == "conversation" and f["scope"] in ("conversation", "sample"):
            ka, kb = (a["file"], a["line"]), (b["file"], b["line"])
            if ka in key_of and kb in key_of:
                ia, ib = key_of[ka]["index"], key_of[kb]["index"]
                if ia in assign_by_index and ib in assign_by_index and assign_by_index[ia] != assign_by_index[ib]:
                    if f["status"] == "accepted_with_exception":
                        ok_exc = False
                    if f["status"] in ("reject", "review"):
                        ok_dec = False
    checks["mt3_edges_not_split"] = ok_edges
    checks["exception_pairs_not_split"] = ok_exc
    checks["no_unresolved_finding_pair_across_parts"] = ok_dec
    blocked_units = {unit_of[r["index"]] for r in records if entry[(r["file"], r["line"])]["progression"] == "blocked"}
    checks["no_blocked_record_assigned"] = not any(entry[(r["file"], r["line"])]["progression"] == "blocked" and r["index"] in assign_by_index
                                                   for r in records)
    checks["no_blocked_group_member_assigned"] = not any(unit_of[i] in blocked_units for i in assign_by_index)
    excl = {e["id"] for e in exclusions or []}
    checks["no_excluded_record_assigned"] = not any((r["id"] in excl or r["marker"]) and r["index"] in assign_by_index for r in records)
    return checks


# ---------------------------------------------------------------------------
# a teljes számítás (kimenet írása nélkül)
# ---------------------------------------------------------------------------

def compute_split(records, rep, exclusions, te1_ref, targets, seed, stratify, min_hard_test):
    t0 = time.perf_counter()
    units, held, extra = build_units(records, rep, exclusions, te1_ref)
    unit_of = {}
    for uid, u in units.items():
        for r in u["members"]:
            unit_of[r["index"]] = uid
    assignable_units = [{"id": uid, "size": len(u["assignable"]), "feats": unit_features(u["assignable"])}
                        for uid, u in sorted(units.items()) if u["assignable"]]
    n_assignable = sum(u["size"] for u in assignable_units)
    ideal = scaled_ideal(n_assignable, targets)
    hard_total = sum(1 for u in units.values() for r in u["assignable"] if r["hard"])
    if min_hard_test == "auto":
        min_hard = min(hard_total, math.ceil(MIN_HARD_TEST_SHARE * ideal[2] - 1e-9))
        min_hard_note = "auto: a teszt-darabszám 30%-a (a terv: legalább 30 a 100-ból), legfeljebb a kijelölhető nehéz beszélgetések száma"
    else:
        min_hard, min_hard_note = int(min_hard_test), "megadott"
    assign_units_map, info = assign_units(assignable_units, ideal, seed, stratify=stratify, min_hard_test=min_hard)

    split_of = {}
    for uid, s in assign_units_map.items():
        for r in units[uid]["assignable"]:
            split_of[r["index"]] = s
    for r in records:
        r["split"] = split_of.get(r["index"])
    key_of = {(r["file"], r["line"]): r for r in records}
    checks = verify_split(records, rep, split_of, held, unit_of, exclusions, key_of)
    stats_counts = split_stats([r for r in records if r["split"]], unit_of)
    checks["split_counts_match_assignment"] = all(stats_counts[s]["conversations"] == sum(1 for v in split_of.values() if v == s) for s in SPLITS)
    failed = sorted(k for k, v in checks.items() if not v)
    if failed:
        raise VerificationError("A belső ellenőrzés hibát talált: " + ", ".join(failed))

    achieved = {s: stats_counts[s]["conversations"] for s in SPLITS}
    tol = math.ceil(PLAN_TOLERANCE * sum(targets) - 1e-9)
    deviation = {
        "planned_targets": dict(zip(SPLITS, targets)), "planned_total": sum(targets), "assignable_records": n_assignable,
        "scaled_from_planned": n_assignable != sum(targets), "ideal_counts": dict(zip(SPLITS, ideal)), "achieved": achieved,
        "vs_ideal": {s: achieved[s] - ideal[i] for i, s in enumerate(SPLITS)},
        "vs_planned": {s: achieved[s] - targets[i] for i, s in enumerate(SPLITS)},
        "exact_ideal_reached": all(achieved[s] == ideal[i] for i, s in enumerate(SPLITS)),
        "plan_tolerance_abs": tol, "within_plan_tolerance": all(abs(achieved[s] - targets[i]) <= tol for i, s in enumerate(SPLITS)),
    }
    hard_test = stats_counts["test"]["hard"]
    hard_info = {"definition": f"előzmény-mélység >= {HARD_DEPTH} vagy család in {sorted(HARD_FAMILIES)}", "min_hard_test": min_hard,
                 "min_hard_note": min_hard_note, "hard_in_test": hard_test, "hard_assignable_total": hard_total, "satisfied": hard_test >= min_hard}
    by_feature = {f: {s: {} for s in SPLITS} for f in FEATURES}
    for s in SPLITS:
        by_feature["family"][s] = stats_counts[s]["family"]
        by_feature["length"][s] = stats_counts[s]["length"]
        by_feature["domain"][s] = stats_counts[s]["domain"]
        by_feature["hard"][s] = {"hard": stats_counts[s]["hard"], "routine": stats_counts[s]["conversations"] - stats_counts[s]["hard"]}

    held_out = []
    unit_split = {uid: assign_units_map.get(uid) for uid in units}
    for idx in sorted(held):
        r = records[idx]
        h = held[idx]
        held_out.append({"id": r["id"], "file": r["file"], "line": r["line"], "line_sha256": r["line_sha256"], "unit": unit_of[idx],
                         "reasons": h["reasons"], "mt3_findings": sorted(h["findings"]),
                         "reserved_split": unit_split.get(unit_of[idx])})
    overlaps = cross_split_overlaps(rep, key_of, split_of, unit_of)
    links = build_export_links(rep, key_of, split_of, unit_of, held)
    unit_sizes = Counter(len(u["members"]) for u in units.values())
    by_reason = Counter(reason for h in held.values() for reason in h["reasons"])
    assignment = [{"id": r["id"], "file": r["file"], "line": r["line"], "line_sha256": r["line_sha256"], "unit": unit_of[r["index"]],
                   "split": r["split"]} for r in records if r["split"]]
    assignment.sort(key=lambda a: (a["file"], a["line"]))
    unit_out = {}
    for uid, u in sorted(units.items()):
        unit_out[uid] = {"members": [r["id"] for r in u["members"]], "assigned": [r["id"] for r in u["assignable"]],
                         "split": unit_split.get(uid), "mt3_groups": u["mt3_groups"], "merged_by_mt2": u["merged"],
                         "declared_split_groups": sorted({r["split_group"] for r in u["members"] if r["split_group"]}),
                         "personas": sorted({r["persona"] for r in u["members"] if r["persona"]})}
    canon = "\n".join(f"{r['file']}:{r['line']}:{r['id']}\t{r['split'] or 'HELD_BACK'}" for r in sorted(records, key=lambda r: (r["file"], r["line"])))
    groups_canon = "\n".join(f"{uid}\t{','.join(u['members'])}" for uid, u in sorted(unit_out.items()))
    warnings = []
    if not deviation["exact_ideal_reached"]:
        warnings.append("a kijelölt darabszám eltér az ideálistól (csoport-integritás előbbre való): lásd deviation")
    if deviation["scaled_from_planned"]:
        warnings.append(f"a kijelölhető darabszám ({n_assignable}) nem egyezik a terv összegével ({sum(targets)}): arányosan skálázott cél-darabszámok")
    if held_out:
        warnings.append(f"{len(held_out)} rekord visszatartva (nem kijelölt): lásd held_back")
    if not hard_info["satisfied"]:
        warnings.append("a teszt-részben a \"nehéz\" beszélgetések száma a minimum alatt van")
    if any(o["level"] == "decision" for o in overlaps):
        warnings.append("döntési szintű MT-3 találat része részek közt van (nem várt)")
    return {
        "units": units, "unit_of": unit_of, "held": held_out, "assignment": assignment, "unit_out": unit_out, "stats": stats_counts,
        "deviation": deviation, "hard": hard_info, "by_feature": by_feature, "stratification": info.get("stratification"),
        "dp": info.get("dp_target"), "overlaps": overlaps, "export_links": links, "checks": checks, "warnings": warnings,
        "unit_size_histogram": {str(k): v for k, v in sorted(unit_sizes.items())}, "held_by_reason": dict(sorted(by_reason.items())),
        "assignment_sha256": hashlib.sha256(canon.encode("utf-8")).hexdigest(), "groups_sha256": hashlib.sha256(groups_canon.encode("utf-8")).hexdigest(),
        "merged_pairs": extra["merged_pairs"], "ideal": ideal, "n_assignable": n_assignable, "records_split": split_of,
        "compute_seconds": round(time.perf_counter() - t0, 3),
    }


# ---------------------------------------------------------------------------
# fájl-alapú futtatás, kimenetek
# ---------------------------------------------------------------------------

def write_tsv(path, header, rows):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\t".join(header) + "\n")
        for r in rows:
            f.write("\t".join("" if v is None else str(v) for v in r) + "\n")


def _dump(path, obj):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")


def prepare(conv_paths, mode, mt3_report, te1_export=None, exclusions_path=None, name_bank_path=None, allow_no_te1=False):
    """A bemenetek betöltése és ellenőrzése (kimenet nélkül). Visszaad a számításhoz szükséges mindent."""
    for p in conv_paths:
        if not os.path.isfile(p):
            raise InputFileError(f"A beszélgetés-fájl nem található: {p}")
    if not os.path.isfile(mt3_report):
        raise InputFileError(f"Az MT-3 jelentés nem található: {mt3_report}")
    bank_path = name_bank_path or mt1.DEFAULT_NAME_BANK
    try:
        bank = mt1.load_name_bank(bank_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise InputFileError(f"A névtár nem olvasható: {exc}")
    before = file_sha_map(list(conv_paths) + [mt3_report])
    records, infos = load_conversations(conv_paths, mode, bank)
    rep, rep_info = load_mt3_report(mt3_report, infos, records, mode, te1_export, allow_no_te1)
    te1_ref = load_te1_reference(rep, te1_export)
    exclusions, excl_info = None, None
    if exclusions_path:
        exclusions, sha = load_exclusions(exclusions_path)
        excl_info = {"path": te1.rel_path(exclusions_path), "sha256": sha, "entries": len(exclusions)}
    return {"records": records, "infos": infos, "rep": rep, "rep_info": rep_info, "te1_ref": te1_ref, "exclusions": exclusions,
            "excl_info": excl_info, "bank_path": bank_path, "before": before, "mt3_path": mt3_report, "conv_paths": list(conv_paths)}


def run_from_files(conv_paths, out_dir, mode, mt3_report, te1_export=None, exclusions_path=None, targets=DEFAULT_TARGETS,
                   seed=DEFAULT_SEED, stratify=True, min_hard_test="auto", allow_no_te1=False, name_bank_path=None, run_name=None):
    for p in list(conv_paths) + [mt3_report]:
        if not os.path.isfile(p):
            raise InputFileError(f"A bemeneti fájl nem található: {p}")
    try:
        out_abs = None
        for p in list(conv_paths) + [mt3_report]:
            out_abs = te1.check_out_dir(out_dir, os.path.dirname(os.path.abspath(p)))
        if te1_export:
            out_abs = te1.check_out_dir(out_dir, te1_export)
    except te1.OutputPathError as exc:
        raise OutputError(str(exc))
    prep = prepare(conv_paths, mode, mt3_report, te1_export, exclusions_path, name_bank_path, allow_no_te1)
    res = compute_split(prep["records"], prep["rep"], prep["exclusions"], prep["te1_ref"], targets, seed, stratify, min_hard_test)
    if file_sha_map(list(conv_paths) + [mt3_report]) != prep["before"]:
        raise ChangedInputError("A bemeneti fájl(ok) vagy az MT-3 jelentés a futás közben megváltoztak (sha256 eltérés).")
    stamp = run_name or datetime.datetime.now(datetime.timezone.utc).strftime("mt2_%Y%m%dT%H%M%SZ")
    if not re.match(r"^[A-Za-z0-9._-]+$", stamp):
        raise OutputError(f"Érvénytelen futásnév: {stamp!r}")
    run_dir = os.path.join(out_abs, stamp)
    if os.path.exists(run_dir):
        raise OutputError(f"A futás-mappa már létezik, nem írom felül: {run_dir}")
    os.makedirs(run_dir)

    records = prep["records"]
    outputs = {}

    def register(name):
        p = os.path.join(run_dir, name)
        outputs[name] = {"sha256": te1.sha256_file(p), "bytes": os.path.getsize(p)}

    write_tsv(os.path.join(run_dir, "assignment.tsv"), ["record", "split", "unit", "family", "n_exchanges", "hard", "file", "line", "line_sha256"],
              [(r["id"], r["split"], res["unit_of"][r["index"]], r["family"], r["n_exchanges"], int(r["hard"]), r["file"], r["line"], r["line_sha256"])
               for r in sorted(records, key=lambda r: (r["file"], r["line"])) if r["split"]])
    register("assignment.tsv")
    write_tsv(os.path.join(run_dir, "held_back.tsv"), ["record", "unit", "reasons", "mt3_findings", "reserved_split", "file", "line"],
              [(h["id"], h["unit"], ",".join(h["reasons"]), ",".join(h["mt3_findings"]), h["reserved_split"], h["file"], h["line"]) for h in res["held"]])
    register("held_back.tsv")
    write_tsv(os.path.join(run_dir, "groups.tsv"), ["unit", "split", "members", "assigned", "mt3_groups", "merged_by_mt2"],
              [(uid, u["split"], ",".join(u["members"]), ",".join(u["assigned"]), ",".join(u["mt3_groups"]), int(u["merged_by_mt2"]))
               for uid, u in sorted(res["unit_out"].items())])
    register("groups.tsv")
    for s in SPLITS:
        with open(os.path.join(run_dir, f"ids_{s}.txt"), "w", encoding="utf-8", newline="\n") as f:
            for r in sorted((r for r in records if r["split"] == s), key=lambda r: (r["file"], r["line"])):
                f.write(r["id"] + "\n")
        register(f"ids_{s}.txt")
    write_tsv(os.path.join(run_dir, "cross_split_overlaps.tsv"),
              ["level", "type", "status", "score", "a", "a_turn", "a_split", "b", "b_turn", "b_split", "at_boundary", "finding_id"],
              [(o["level"], o["type"], o["status"], o["score"], o["a"], o["a_turn"], o["a_split"], o["b"], o["b_turn"], o["b_split"],
                o["at_boundary"], o["finding_id"]) for o in res["overlaps"]])
    register("cross_split_overlaps.tsv")
    _dump(os.path.join(run_dir, "export_links.json"), res["export_links"])
    register("export_links.json")

    if not prep["te1_ref"]:
        res["warnings"].append("a felosztás TE-1 export összevetés nélküli MT-3 jelentésre épül: a részek közötti átfedés az egyfordulós adattal szemben nem vizsgált")
    te1_info = None
    if prep["te1_ref"]:
        t = prep["te1_ref"]
        te1_info = {"run_dir": t["run_dir"], "manifest_sha256": t["manifest_sha256"], "export_file_sha256": t["export_file_sha256"],
                    "index_file_sha256": t["index_file_sha256"], "rows": t["rows"], "excluded_rows": sorted(t["excluded_ids"])}
    overlaps_by = Counter((o["level"], o["a_split"] + "|" + o["b_split"]) for o in res["overlaps"])
    manifest = {
        "tool": "tools/multiturn_split.py", "tool_version": TOOL_VERSION, "status": "completed",
        "created_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "git_commit": te1.git_commit(), "python": sys.version.split()[0],
        "config": {
            "mode": mode, "seed": seed, "targets": dict(zip(SPLITS, targets)), "ideal_counts": dict(zip(SPLITS, res["ideal"])),
            "stratify": stratify, "stratify_features": list(FEATURES), "min_hard_test": res["hard"]["min_hard_test"],
            "hard_definition": res["hard"]["definition"], "length_bands": [b[0] for b in LENGTH_BANDS],
            "algorithm": "egységek (MT-3 csoportok + kivétel-párok) -> 2+ tagú egységekre bitkészletes DP a validation/test darabszámra -> sha256-súlyozott bejárás -> 1 tagú töltelék -> azonos méretű egységek cseréje a rétegzésért",
            "ordering": "sha256(seed|egység-azonosító); nem a bemeneti sorrend; nincs Python random",
            "unit": "MT-3 számított csoport (mtg_...), a dokumentált kivétellel felmentett párokkal egyesítve; nem a deklarált split_group",
            "held_back_policy": {"blocked_record": "az egész egység visszatartva (mt3_blocked / group_has_blocked_member)",
                                 "excluded": "csak a rekord (kizárási lista, quality_notes jelölés, TE-1 kizárt azonosító); a csoporttársak kijelölhetők, a rekord `reserved_split` értéket kap",
                                 "unresolved_review_reject_is_never_assigned": True},
            "plan_tolerance": PLAN_TOLERANCE, "allow_no_te1_comparison": bool(allow_no_te1),
        },
        "inputs": {"conversation_files": prep["infos"], "mt3_report": prep["rep_info"], "te1_export": te1_info, "exclusions": prep["excl_info"],
                   "name_bank": {"path": te1.rel_path(prep["bank_path"]), "sha256": te1.sha256_file(prep["bank_path"])}},
        "counts": {"records_read": len(records), "assignable": res["n_assignable"], "assigned": len(res["assignment"]),
                   "held_back": len(res["held"]), "held_back_by_reason": res["held_by_reason"], "units": len(res["unit_out"]),
                   "units_multi_member": sum(1 for u in res["unit_out"].values() if len(u["members"]) >= 2),
                   "units_merged_by_mt2": sum(1 for u in res["unit_out"].values() if u["merged_by_mt2"]), "unit_size_histogram": res["unit_size_histogram"]},
        "splits": res["stats"], "deviation": res["deviation"], "hard_test": res["hard"],
        "stratification": {"result": res["stratification"], "dp_choice": res["dp"], "by_feature": res["by_feature"]},
        "cross_split": {"pairs_total": len(res["overlaps"]), "by_level_and_parts": {f"{k[0]}:{k[1]}": v for k, v in sorted(overlaps_by.items())},
                        "decision_level_pairs": sum(1 for o in res["overlaps"] if o["level"] == "decision"), "file": "cross_split_overlaps.tsv"},
        "export_links": dict(res["export_links"]["summary"], file="export_links.json"),
        "assignment_sha256": res["assignment_sha256"], "groups_sha256": res["groups_sha256"],
        "assignment": res["assignment"], "units": res["unit_out"], "held_back": res["held"],
        "merged_by_exception": [{"a": a, "b": b, "type": t} for a, b, t in res["merged_pairs"]],
        "verification": res["checks"], "outputs": outputs, "timing_seconds": {"compute": res["compute_seconds"]},
        "warnings": res["warnings"], "limitations": LIMITATIONS, "disclaimer": DISCLAIMER,
        "training_ready": False, "content_verified": False, "split_approved": False,
    }
    partial = os.path.join(run_dir, "split_manifest.json.partial")
    _dump(partial, manifest)
    os.replace(partial, os.path.join(run_dir, "split_manifest.json"))
    manifest["run_dir"] = run_dir
    return manifest


def _resolve(rel):
    return rel if os.path.isabs(rel) else os.path.join(te1.REPO_ROOT, rel)


def verify_manifest(manifest_path):
    """A manifest bemeneteinek és kimeneteinek ellenőrzőösszege, majd újraszámolás ugyanazokból a bemenetekből és beállításokból:
    a kijelölés azonosságának ellenőrzése (reprodukálhatóság). Visszaad: (problems_changed, problems_not_reproducible)."""
    with open(manifest_path, "r", encoding="utf-8") as f:
        m = json.load(f)
    changed = []

    def check(rel, want, label):
        path = _resolve(rel)
        if not os.path.isfile(path):
            changed.append(f"{label}: hiányzik: {rel}")
        elif te1.sha256_file(path) != want:
            changed.append(f"{label}: megváltozott: {rel}")

    for info in m["inputs"]["conversation_files"]:
        check(info["path"], info["sha256"], "beszélgetés-fájl")
    check(m["inputs"]["mt3_report"]["path"], m["inputs"]["mt3_report"]["sha256"], "MT-3 jelentés")
    if m["inputs"].get("exclusions"):
        check(m["inputs"]["exclusions"]["path"], m["inputs"]["exclusions"]["sha256"], "kizárási lista")
    check(m["inputs"]["name_bank"]["path"], m["inputs"]["name_bank"]["sha256"], "névtár")
    base = os.path.dirname(os.path.abspath(manifest_path))
    for name, o in m["outputs"].items():
        p = os.path.join(base, name)
        if not os.path.isfile(p):
            changed.append(f"kimenet hiányzik: {name}")
        elif te1.sha256_file(p) != o["sha256"]:
            changed.append(f"kimenet megváltozott: {name}")
    if changed:
        return changed, []
    cfg = m["config"]
    exp = m["inputs"].get("te1_export")
    try:
        prep = prepare([_resolve(i["path"]) for i in m["inputs"]["conversation_files"]], cfg["mode"], _resolve(m["inputs"]["mt3_report"]["path"]),
                       _resolve(exp["run_dir"]) if exp else None, _resolve(m["inputs"]["exclusions"]["path"]) if m["inputs"].get("exclusions") else None,
                       _resolve(m["inputs"]["name_bank"]["path"]), cfg.get("allow_no_te1_comparison", False))
    except StaleReportError as exc:
        return [f"elavult MT-3 jelentés: {exc}"], []
    res = compute_split(prep["records"], prep["rep"], prep["exclusions"], prep["te1_ref"], tuple(cfg["targets"][s] for s in SPLITS), cfg["seed"],
                        cfg["stratify"], cfg["min_hard_test"])
    bad = []
    if res["assignment_sha256"] != m["assignment_sha256"]:
        bad.append("a kijelölés újraszámolva eltér a manifestben rögzítettől")
    if res["groups_sha256"] != m["groups_sha256"]:
        bad.append("a csoportok újraszámolva eltérnek a manifestben rögzítettől")
    return [], bad


def _main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description="MT-2: csoportokat egyben tartó, reprodukálható felosztás (NEM jóváhagyott, NEM training-ready).")
    p.add_argument("--mode", choices=["dataset", "fixture"])
    p.add_argument("--conversations", nargs="+", help="Beszélgetés-fájl(ok): ugyanazok, mint az MT-3 futásban.")
    p.add_argument("--mt3-report", help="Az MT-3 dedupe_report.json (aktuális, mt3-2.x).")
    p.add_argument("--out-dir", help="Kimeneti szülőmappa (a futás új almappába kerül).")
    p.add_argument("--te1-export", default=None, help="TE-1 export futás-mappa (ugyanaz, mint az MT-3 futásban).")
    p.add_argument("--exclusions", default=None, help="Kizárási lista beszélgetés-azonosítókra (azonosító | ok | felülvizsgálat).")
    p.add_argument("--targets", type=parse_targets, default=DEFAULT_TARGETS, help="train,validation,test darabszám (alap: 800,100,100).")
    p.add_argument("--seed", default=DEFAULT_SEED)
    p.add_argument("--min-hard-test", default="auto", help="A teszt-részben a \"nehéz\" beszélgetések minimuma: auto (30%%) vagy szám.")
    p.add_argument("--no-stratify", action="store_true", help="Kikapcsolja a rétegző cserét (csak a darabszám-optimalizálás).")
    p.add_argument("--allow-no-te1-comparison", action="store_true", help="Elfogad TE-1 összevetés nélküli MT-3 jelentést (figyelmeztetéssel).")
    p.add_argument("--name-bank", default=None)
    p.add_argument("--run-name", default=None)
    p.add_argument("--verify-manifest", default=None, help="Egy korábbi manifest bemeneteinek/kimeneteinek ellenőrzése és újraszámolása.")
    a = p.parse_args(argv)

    if a.verify_manifest:
        try:
            changed, bad = verify_manifest(a.verify_manifest)
        except (OSError, json.JSONDecodeError, KeyError) as exc:
            print(f"HIBA: a manifest nem olvasható: {exc}", file=sys.stderr)
            return EXIT_INPUT
        except SplitError as exc:
            print(f"HIBA ({type(exc).__name__}): {exc}", file=sys.stderr)
            return exc.exit_code
        for pr in changed:
            print(f"MEGVÁLTOZOTT BEMENET/KIMENET: {pr}", file=sys.stderr)
        for pr in bad:
            print(f"NEM REPRODUKÁLHATÓ: {pr}", file=sys.stderr)
        if changed:
            return EXIT_STALE
        if bad:
            return EXIT_NOT_REPRODUCIBLE
        print("A manifest bemenetei és kimenetei változatlanok, az újraszámolt kijelölés azonos.")
        return 0
    if not (a.mode and a.conversations and a.mt3_report and a.out_dir):
        p.error("--mode, --conversations, --mt3-report és --out-dir kötelező (vagy --verify-manifest)")
    if a.min_hard_test != "auto" and not re.match(r"^\d+$", a.min_hard_test):
        p.error("a --min-hard-test 'auto' vagy nemnegatív egész")
    try:
        m = run_from_files(a.conversations, a.out_dir, a.mode, a.mt3_report, a.te1_export, a.exclusions, a.targets, a.seed,
                           not a.no_stratify, a.min_hard_test, a.allow_no_te1_comparison, a.name_bank, a.run_name)
    except SplitError as exc:
        print(f"HIBA ({type(exc).__name__}): {exc}", file=sys.stderr)
        return exc.exit_code
    c, d = m["counts"], m["deviation"]
    print(f"MT-2 futás kész: {m['run_dir']}")
    print(f"Rekord: {c['records_read']} | kijelölt: {c['assigned']} | visszatartott: {c['held_back']} | egység: {c['units']} (2+ tagú: {c['units_multi_member']})")
    for s in SPLITS:
        st = m["splits"][s]
        print(f"  {s:10} beszélgetés {st['conversations']:5} (ideális {d['ideal_counts'][s]}, terv {d['planned_targets'][s]}) | üzenet {st['messages']} | "
              f"minta {st['samples_total']} (első fordulós {st['samples_first_turn']}, előzmény-függő {st['samples_history_dependent']}) | nehéz {st['hard']}")
    for w in m["warnings"]:
        print("  FIGYELEM:", w)
    print(DISCLAIMER)
    attention = bool(c["held_back"] or not d["exact_ideal_reached"] or not m["hard_test"]["satisfied"]
                     or m["cross_split"]["decision_level_pairs"] or a.allow_no_te1_comparison)
    return EXIT_ATTENTION if attention else 0


if __name__ == "__main__":
    sys.exit(_main())
