"""
MF-AI-Zero - TE-1: kizárás-érvényesítő, visszakövethető clean-export (tools/).

CÉL: a data/clean/*.jsonl állományból egy SZŰRT, visszakövethető exportot készít,
amelyből a felülvizsgálatig kizárt sorok TÉNYLEGESEN kimaradnak. Eddig a kizárási
lista (training_exclusion_pending_review.txt) csak dokumentálva volt, kód nem
olvasta; ez az eszköz teszi kikényszeríthetővé.

MIT CSINÁL:
  - Szigorúan beolvassa a kizárási listát, és MEGÁLL egyértelmű hibával, ha a lista
    hiányzik, olvashatatlan, üres (kivéve kifejezett --allow-empty-exclusions),
    hibás formátumú sort, duplikált vagy nem szabályos azonosítót tartalmaz, vagy
    egy azonosító a clean sorok között nem pontosan EGYSZER szerepel.
  - Kétirányú konzisztencia: ha egy clean sor `quality_notes` mezője kizárási
    jelölést tartalmaz („a tanítási halmazból kizárandó”), de az azonosítója nincs a
    listán, az eszköz megáll (így egy sor észrevétlen kivétele a listából nem
    "oldja fel" a kizárást, és az üres lista sem kerüli meg).
  - A kizárt sorokat NEM törli, NEM módosítja a data/clean állományokban: csak
    olvassa őket; a futás előtt és után is ellenőrzi a forrásfájlok sha256-ját.
  - Kimenet (egy KÜLÖN, új futás-mappában, soha nem ír felül semmit):
      train_candidates.jsonl  - a nem kizárt sorok, EREDETI sorszöveggel (bájt-hűen)
      export_index.tsv        - azonosító, forrásfájl, forrássor, sor-sha256
      manifest.json           - forrásfájlok (sha256, sorszámok), a lista, a
                                kizárt sorok (fájl+sor+sha256), darabszámok,
                                ellenőrzések, git commit, figyelmeztetések
  - A kimenetet lemezről visszaolvasva külön ellenőrzi: nincs benne kizárt azonosító,
    a darabszámok kiegyenlítettek, minden sor sha256-ja egyezik a forrással. Hiba
    esetén a futás-mappa `.partial` fájlokkal és FAILED.txt-vel marad, manifest NÉLKÜL
    (a hiányzó manifest = érvénytelen export).

MIT NEM CSINÁL / MIT NEM BIZONYÍT:
  - NEM tartalmi ellenőrzés, NEM training-ready minősítés. Az export csak azt
    igazolja, hogy a lista érvényesült és a darabszámok visszakövethetők.
  - NEM tanít, NEM ír a src/ tanító- és chat-kódba, NEM konvertál chat-szöveggé
    (az R1/R2/R3 renderelés külön feladat), NEM olvas raw/rejected mappát.

Használat:
    python tools/dataset_export_train.py --out-dir data/train/te1_export
    python tools/dataset_export_train.py --out-dir <mappa> [--input-dir data/clean]
        [--exclusions <lista.txt>] [--run-name <név>] [--allow-empty-exclusions]

Kilépési kódok: 0 sikeres; 2 argumentumhiba (argparse); 10 kizárási lista hiba;
11 forrásadat-hiba; 12 kimeneti ellenőrzés sikertelen; 13 kimeneti útvonal hiba.
"""

import argparse
import datetime
import glob
import hashlib
import json
import os
import re
import subprocess
import sys

TOOL_VERSION = "te1-1.0"

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_INPUT_DIR = os.path.join(REPO_ROOT, "data", "clean")
DEFAULT_EXCLUSIONS = os.path.join(
    REPO_ROOT, "data", "reports", "audit_evidence", "uncertainty_source_request_1000",
    "training_exclusion_pending_review.txt",
)

# szigorú azonosító-minta: kisbetű/számjegy/aláhúzás, 4+ jegyű számmal a végén
# (nincs wildcard, előtag, tartomány, szóköz, nagybetű)
ID_RE = re.compile(r"^[a-z][a-z0-9_]*_[0-9]{4,}$")

# a kizárt sorok quality_notes mezőjében szereplő jelölés (lásd v1.13.15)
EXCLUSION_NOTE_MARKER = "a tanítási halmazból kizárandó"

EXPORT_FILE = "train_candidates.jsonl"
INDEX_FILE = "export_index.tsv"
MANIFEST_FILE = "manifest.json"
FAILED_FILE = "FAILED.txt"

SCOPE_DISCLAIMER = (
    "Ez az export a kizárási lista érvényesítését és a darabszámok visszakövethetőségét igazolja. "
    "NEM tartalmi ellenőrzés és NEM training-ready állapot."
)

CODE_EXCLUSION = 10
CODE_SOURCE = 11
CODE_VERIFY = 12
CODE_OUTPUT = 13


class ExportError(Exception):
    exit_code = 1


class ExclusionListError(ExportError):
    exit_code = CODE_EXCLUSION


class SourceDataError(ExportError):
    exit_code = CODE_SOURCE


class VerificationError(ExportError):
    exit_code = CODE_VERIFY


class OutputPathError(ExportError):
    exit_code = CODE_OUTPUT


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def read_bytes(path):
    with open(path, "rb") as f:
        return f.read()


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def rel_path(path):
    """Repóhoz képest relatív, / elválasztós útvonal (ha a repón kívül van, abszolút)."""
    ap = os.path.abspath(path)
    try:
        rp = os.path.relpath(ap, REPO_ROOT)
    except ValueError:
        return ap.replace("\\", "/")
    if rp.startswith(".."):
        return ap.replace("\\", "/")
    return rp.replace("\\", "/")


# ---------------------------------------------------------------------------
# 1) kizárási lista
# ---------------------------------------------------------------------------

def parse_exclusion_list(path, allow_empty=False):
    """Visszaad (entries, sha256). Minden nem üres, nem '#' sor pontosan
    'azonosító | ok | szükséges felülvizsgálat' alakú kell legyen."""
    if not os.path.isfile(path):
        raise ExclusionListError(f"A kizárási lista nem található: {path}")
    try:
        raw = read_bytes(path)
        text = raw.decode("utf-8-sig")
    except (OSError, UnicodeDecodeError) as exc:
        raise ExclusionListError(f"A kizárási lista nem olvasható (UTF-8): {path} ({exc})")

    entries = []
    seen = {}
    for line_no, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = [p.strip() for p in line.split(" | ", 2)]
        if len(parts) != 3 or not all(parts):
            raise ExclusionListError(
                f"Hibás kizárási sor ({path}:{line_no}): 'azonosító | ok | szükséges felülvizsgálat' "
                f"alak várható, mindhárom mező kitöltve. Sor: {stripped!r}"
            )
        row_id, reason, review = parts
        if not ID_RE.match(row_id):
            raise ExclusionListError(
                f"Nem szabályos vagy nem egyértelmű azonosító ({path}:{line_no}): {row_id!r}. "
                f"Csak pontos, kisbetűs azonosító engedélyezett (pl. uncertainty_source_request_0220), "
                f"wildcard, előtag, tartomány nem."
            )
        if row_id in seen:
            raise ExclusionListError(
                f"Duplikált azonosító a kizárási listában: {row_id!r} ({path}:{seen[row_id]} és :{line_no})."
            )
        seen[row_id] = line_no
        entries.append({"id": row_id, "reason": reason, "review": review, "line_no": line_no})

    if not entries and not allow_empty:
        raise ExclusionListError(
            f"A kizárási lista nem tartalmaz egyetlen bejegyzést sem: {path}. Üres listával csak a "
            f"kifejezett --allow-empty-exclusions kapcsolóval (és kizárás-jelölésű sorok nélkül) fut az export."
        )
    return entries, sha256_bytes(raw)


# ---------------------------------------------------------------------------
# 2) forrásfájlok
# ---------------------------------------------------------------------------

def list_source_files(input_dir):
    input_dir = os.path.abspath(input_dir)
    if os.path.basename(input_dir.rstrip("\\/")) != "clean":
        raise SourceDataError(
            f"Csak 'clean' nevű mappából exportálok (raw/rejected/inbox nem): {input_dir}"
        )
    if not os.path.isdir(input_dir):
        raise SourceDataError(f"A bemeneti mappa nem található: {input_dir}")
    files = sorted(glob.glob(os.path.join(input_dir, "*.jsonl")))
    if not files:
        raise SourceDataError(f"A bemeneti mappában nincs .jsonl fájl: {input_dir}")
    return files


def load_rows(files):
    """Minden nem üres sor JSON objektum, nem üres 'id'-vel. Visszaad (rows, file_infos).
    row: dict(source, line_no, line_bytes, line_sha256, obj, id, category)."""
    rows = []
    file_infos = []
    for path in files:
        raw = read_bytes(path)
        info = {"path": rel_path(path), "sha256": sha256_bytes(raw), "bytes": len(raw),
                "crlf_lines": raw.count(b"\r\n"), "blank_lines": 0, "rows_read": 0}
        parts = raw.split(b"\n")
        if parts and parts[-1] == b"":
            parts.pop()
        for line_no, line in enumerate(parts, 1):
            if line.endswith(b"\r"):
                line = line[:-1]
            if not line.strip():
                info["blank_lines"] += 1
                continue
            try:
                obj = json.loads(line.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise SourceDataError(f"Hibás JSON sor: {rel_path(path)}:{line_no} ({exc})")
            if not isinstance(obj, dict):
                raise SourceDataError(f"A sor nem JSON objektum: {rel_path(path)}:{line_no}")
            row_id = obj.get("id")
            if not isinstance(row_id, str) or not row_id.strip():
                raise SourceDataError(f"Hiányzó vagy üres 'id': {rel_path(path)}:{line_no}")
            rows.append({"source": rel_path(path), "line_no": line_no, "line_bytes": line,
                         "line_sha256": sha256_bytes(line), "obj": obj, "id": row_id,
                         "category": obj.get("category") or "(nincs)"})
            info["rows_read"] += 1
        file_infos.append(info)
    return rows, file_infos


def index_ids(rows):
    idx = {}
    for i, row in enumerate(rows):
        idx.setdefault(row["id"], []).append(i)
    return idx


# ---------------------------------------------------------------------------
# 3) kizárások érvényesítése
# ---------------------------------------------------------------------------

def match_exclusions(entries, rows, id_index):
    """Minden listabejegyzés pontosan egy clean sorra kell hogy mutasson."""
    for e in entries:
        hits = id_index.get(e["id"], [])
        if not hits:
            raise ExclusionListError(
                f"A kizárási lista azonosítója nem szerepel a clean sorok között: {e['id']!r} "
                f"(lista sor {e['line_no']}). Elgépelés vagy elavult bejegyzés? Az export leáll."
            )
        if len(hits) > 1:
            where = ", ".join(f"{rows[i]['source']}:{rows[i]['line_no']}" for i in hits)
            raise ExclusionListError(
                f"Nem egyértelmű kizárási azonosító: {e['id']!r} több sorban szerepel ({where})."
            )


def check_marker_consistency(entries, rows):
    """Kizárás-jelölésű sor, amely nincs a listán → hiba. A listán lévő, jelölés nélküli sor → figyelmeztetés."""
    listed = {e["id"] for e in entries}
    marked = [r["id"] for r in rows if EXCLUSION_NOTE_MARKER in str(r["obj"].get("quality_notes", ""))]
    unlisted = sorted(set(marked) - listed)
    if unlisted:
        raise ExclusionListError(
            "A következő clean sorok jelölése kizárást ír elő, de az azonosítójuk NINCS a kizárási listán "
            f"(a lista hiányos vagy egy bejegyzést kivettek): {', '.join(unlisted)}."
        )
    return [f"A listán szereplő {i} sor quality_notes mezője nem tartalmaz kizárás-jelölést."
            for i in sorted(listed - set(marked))]


def filter_rows(rows, entries):
    excluded_ids = {e["id"] for e in entries}
    kept = [r for r in rows if r["id"] not in excluded_ids]
    excluded = [r for r in rows if r["id"] in excluded_ids]
    return kept, excluded


# ---------------------------------------------------------------------------
# 4) kiírás és visszaolvasásos ellenőrzés
# ---------------------------------------------------------------------------

def write_outputs(kept, run_dir):
    export_partial = os.path.join(run_dir, EXPORT_FILE + ".partial")
    index_partial = os.path.join(run_dir, INDEX_FILE + ".partial")
    with open(export_partial, "wb") as f:
        for r in kept:
            f.write(r["line_bytes"] + b"\n")
    with open(index_partial, "w", encoding="utf-8", newline="\n") as f:
        f.write("id\tsource_file\tsource_line\trow_sha256\n")
        for r in kept:
            f.write(f"{r['id']}\t{r['source']}\t{r['line_no']}\t{r['line_sha256']}\n")
    return export_partial, index_partial


def verify_outputs(export_partial, index_partial, kept, excluded_ids, rows_read, rows_excluded):
    """Lemezről visszaolvasott kimenet ellenőrzése (a szűréstől függetlenül)."""
    problems = []
    if rows_read != len(kept) + rows_excluded:
        problems.append(f"a darabszámok nem egyeznek: beolvasott {rows_read} != exportált {len(kept)} + kizárt {rows_excluded}")

    raw = read_bytes(export_partial)
    lines = raw.split(b"\n")
    if lines and lines[-1] == b"":
        lines.pop()
    if len(lines) != len(kept):
        problems.append(f"a kimeneti fájl sorszáma {len(lines)}, a várt {len(kept)}")
    seen = set()
    leaked = []
    for pos, line in enumerate(lines):
        try:
            obj = json.loads(line.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            problems.append(f"a kimenet {pos + 1}. sora nem érvényes JSON")
            continue
        out_id = obj.get("id") if isinstance(obj, dict) else None
        if out_id in excluded_ids:
            leaked.append(out_id)
        if out_id in seen:
            problems.append(f"duplikált azonosító a kimenetben: {out_id}")
        seen.add(out_id)
        if pos < len(kept) and sha256_bytes(line) != kept[pos]["line_sha256"]:
            problems.append(f"a kimenet {pos + 1}. sora eltér a forrássortól ({kept[pos]['id']})")
    if leaked:
        problems.append("KIZÁRT azonosító került a kimenetbe: " + ", ".join(sorted(set(leaked))))

    with open(index_partial, "r", encoding="utf-8") as f:
        idx_lines = f.read().splitlines()
    idx_ids = [ln.split("\t")[0] for ln in idx_lines[1:]]
    if idx_ids != [r["id"] for r in kept]:
        problems.append("az export_index.tsv azonosítói nem egyeznek a kimeneti sorokkal")
    if excluded_ids & set(idx_ids):
        problems.append("KIZÁRT azonosító került az indexbe")

    if problems:
        raise VerificationError("A kimeneti ellenőrzés SIKERTELEN: " + "; ".join(problems))


def git_commit():
    try:
        out = subprocess.run(["git", "-C", REPO_ROOT, "rev-parse", "HEAD"], capture_output=True,
                             text=True, timeout=15)
        return out.stdout.strip() or None if out.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        return None


def check_out_dir(out_dir, input_dir):
    out_abs = os.path.abspath(out_dir)
    bad_parents = {"clean", "raw", "rejected", "inbox"}
    data_dir = os.path.join(REPO_ROOT, "data")
    for name in bad_parents:
        protected = os.path.join(data_dir, name)
        if out_abs == protected or out_abs.startswith(protected + os.sep):
            raise OutputPathError(f"A kimeneti mappa nem lehet a védett data/{name} alatt: {out_abs}")
    in_abs = os.path.abspath(input_dir)
    if out_abs == in_abs or out_abs.startswith(in_abs + os.sep):
        raise OutputPathError(f"A kimeneti mappa nem lehet a bemeneti mappa alatt: {out_abs}")
    return out_abs


# ---------------------------------------------------------------------------
# 5) fő folyamat
# ---------------------------------------------------------------------------

def run_export(out_dir, input_dir=DEFAULT_INPUT_DIR, exclusions_path=DEFAULT_EXCLUSIONS,
               run_name=None, allow_empty=False):
    """Visszaadja a manifest dict-et. Hibánál ExportError leszármazottat dob."""
    out_abs = check_out_dir(out_dir, input_dir)

    entries, list_sha = parse_exclusion_list(exclusions_path, allow_empty=allow_empty)
    files = list_source_files(input_dir)
    source_sha_before = {f: sha256_file(f) for f in files}
    rows, file_infos = load_rows(files)
    id_index = index_ids(rows)
    match_exclusions(entries, rows, id_index)
    dupes = sorted(i for i, pos in id_index.items() if len(pos) > 1)
    if dupes:
        raise SourceDataError(f"Duplikált azonosító a clean sorok között: {', '.join(dupes[:10])}"
                              + (" ..." if len(dupes) > 10 else ""))
    warnings = check_marker_consistency(entries, rows)

    kept, excluded = filter_rows(rows, entries)
    excluded_ids = {e["id"] for e in entries}

    stamp = run_name or datetime.datetime.now(datetime.timezone.utc).strftime("export_%Y%m%dT%H%M%SZ")
    if not re.match(r"^[A-Za-z0-9._-]+$", stamp):
        raise OutputPathError(f"Érvénytelen futásnév: {stamp!r}")
    run_dir = os.path.join(out_abs, stamp)
    if os.path.exists(run_dir):
        raise OutputPathError(f"A futás-mappa már létezik, nem írom felül: {run_dir}")
    os.makedirs(run_dir)

    export_partial, index_partial = write_outputs(kept, run_dir)
    try:
        verify_outputs(export_partial, index_partial, kept, excluded_ids, len(rows), len(excluded))
        source_sha_after = {f: sha256_file(f) for f in files}
        if source_sha_before != source_sha_after:
            raise VerificationError("A forrásfájlok a futás közben megváltoztak (sha256 eltérés).")
    except ExportError as exc:
        with open(os.path.join(run_dir, FAILED_FILE), "w", encoding="utf-8", newline="\n") as f:
            f.write(str(exc) + "\n")
        raise

    export_final = os.path.join(run_dir, EXPORT_FILE)
    index_final = os.path.join(run_dir, INDEX_FILE)
    os.replace(export_partial, export_final)
    os.replace(index_partial, index_final)

    by_cat, excl_by_cat = {}, {}
    for r in kept:
        by_cat[r["category"]] = by_cat.get(r["category"], 0) + 1
    for r in excluded:
        excl_by_cat[r["category"]] = excl_by_cat.get(r["category"], 0) + 1
    excl_by_id = {r["id"]: r for r in excluded}
    for info in file_infos:
        info["rows_excluded"] = sum(1 for r in excluded if r["source"] == info["path"])
        info["rows_exported"] = info["rows_read"] - info["rows_excluded"]
        info["excluded_ids"] = sorted(r["id"] for r in excluded if r["source"] == info["path"])

    manifest = {
        "tool": "tools/dataset_export_train.py",
        "tool_version": TOOL_VERSION,
        "status": "ok",
        "created_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "git_commit": git_commit(),
        "python": sys.version.split()[0],
        "input_dir": rel_path(input_dir),
        "input_files": file_infos,
        "exclusion_list": {
            "path": rel_path(exclusions_path),
            "sha256": list_sha,
            "allow_empty": bool(allow_empty),
            "entries": [
                {"id": e["id"], "reason": e["reason"], "review": e["review"], "list_line": e["line_no"],
                 "source_file": excl_by_id[e["id"]]["source"], "source_line": excl_by_id[e["id"]]["line_no"],
                 "row_sha256": excl_by_id[e["id"]]["line_sha256"]}
                for e in entries
            ],
        },
        "counts": {
            "rows_read": len(rows), "rows_excluded": len(excluded), "rows_exported": len(kept),
            "exported_by_category": dict(sorted(by_cat.items())),
            "excluded_by_category": dict(sorted(excl_by_cat.items())),
        },
        "outputs": {
            "export_file": {"path": EXPORT_FILE, "sha256": sha256_file(export_final), "rows": len(kept)},
            "index_file": {"path": INDEX_FILE, "sha256": sha256_file(index_final), "rows": len(kept)},
        },
        "checks": {
            "exclusion_ids_matched_exactly_once": True,
            "marker_consistency_no_unlisted_marked_rows": True,
            "source_ids_unique": True,
            "counts_balance": True,
            "output_reread_no_excluded_id": True,
            "output_lines_match_source_sha256": True,
            "source_files_unchanged_during_run": True,
        },
        "warnings": warnings,
        "notes": [
            "A file-szintű sha256 a fájl sorvégeitől (LF/CRLF) függ; a sor-szintű row_sha256 a sor bájtjaiból "
            "készül, sorvég nélkül, ezért platformfüggetlen.",
        ],
        "content_verified": False,
        "training_ready": False,
        "scope_disclaimer": SCOPE_DISCLAIMER,
    }
    manifest_partial = os.path.join(run_dir, MANIFEST_FILE + ".partial")
    with open(manifest_partial, "w", encoding="utf-8", newline="\n") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")
    os.replace(manifest_partial, os.path.join(run_dir, MANIFEST_FILE))
    manifest["run_dir"] = run_dir
    return manifest


def _main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(
        description="TE-1: kizárás-érvényesítő, visszakövethető clean-export (NEM tartalmi ellenőrzés, NEM training-ready).")
    parser.add_argument("--out-dir", required=True, help="A kimeneti szülőmappa (a futás új almappába kerül).")
    parser.add_argument("--input-dir", default=DEFAULT_INPUT_DIR, help="A 'clean' mappa (alapértelmezés: data/clean).")
    parser.add_argument("--exclusions", default=DEFAULT_EXCLUSIONS, help="A kizárási lista fájlja.")
    parser.add_argument("--run-name", default=None, help="A futás-mappa neve (alapértelmezés: időbélyeg).")
    parser.add_argument("--allow-empty-exclusions", action="store_true",
                        help="Kifejezetten engedélyezi az üres kizárási listát (a jelölés-konzisztencia ekkor is érvényes).")
    args = parser.parse_args(argv)

    try:
        manifest = run_export(args.out_dir, args.input_dir, args.exclusions, args.run_name,
                              args.allow_empty_exclusions)
    except ExportError as exc:
        print(f"HIBA ({type(exc).__name__}): {exc}", file=sys.stderr)
        return exc.exit_code

    c = manifest["counts"]
    print(f"Export kész: {manifest['run_dir']}")
    print(f"Beolvasott sorok: {c['rows_read']} | kizárt: {c['rows_excluded']} | exportált: {c['rows_exported']}")
    for e in manifest["exclusion_list"]["entries"]:
        print(f"  kizárva: {e['id']} ({e['source_file']}:{e['source_line']})")
    for w in manifest["warnings"]:
        print(f"FIGYELMEZTETÉS: {w}")
    print(SCOPE_DISCLAIMER)
    return 0


if __name__ == "__main__":
    sys.exit(_main())
