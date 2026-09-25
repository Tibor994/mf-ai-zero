"""
MF-AI-Zero - TE-2: TE-1 exportból a JELENLEGI betöltő formátumú ("User:/AI:" blokkok) előkészítő szöveg.

CÉL: a `tools/dataset_export_train.py` (TE-1) által készített, kizárás-érvényesített export
egyfordulós soraiból olyan szövegfájlt készít, amelyet a meglévő `src/train_chat.py` betöltő
(üres sorral elválasztott `User: ...\\nAI: ...` blokkok) blokkhatár- és szerepkonfliktus nélkül
tud olvasni. ELŐKÉSZÍTŐ EXPORT: NEM tanít, NEM ír a tanító/chat kódba, és a teljes állományt
NEM jelöli ki tanítási résznek - a train/validation/test felosztás külön követelmény.

BLOKKFORMÁTUM (soronként egy sor egy blokk):
    User: <instruction>
    <input>            <- csak ha az input nem üres, új sorban, több sorosan is lehet
    AI: <output>
Minden blokkot pontosan egy üres sor ("\\n\\n") zár le (az utolsót is), így a régi betöltő
`text.split("\\n\\n")` felbontása pontosan a blokkokat adja, és a fájl összefűzése más blokkfájllal
sem olvaszt össze blokkokat. A fájl UTF-8, LF sorvégű.

VESZTESÉGMENTESSÉG (nincs csendes levágás/átírás): a mezők szövege bájtra azonosan kerül
a blokkba. Amit a formátum nem tud egyértelműen, veszteség nélkül hordozni, azt a sort
NEM írja a szövegfájlba, hanem a `withheld_rows.tsv` fájlban és a manifestben okkal
felsorolja. Ilyen ok: a mező üres/nem string; CR vagy vezérlő/sorelválasztó karakter;
az instruction többsoros (összemosódna az inputtal); a mezőben üres sor ("\\n\\n") van
(a régi betöltő ott vágna blokkot); a mező sorvégi/kezdő újsort tartalmaz; egy sor
"User:"/"AI:" felirattal KEZDŐDIK (téves szerephatár). A sor közben szereplő
"User:"/"AI:" említés nem okoz határt, ezért átmegy, de `inline_role_label` jelzést kap.

ELLENŐRZÉSEK (mind hibával áll meg, ha nem teljesül):
  - a TE-1 manifest sikeres (status ok, training_ready és content_verified false, minden
    ellenőrzés igaz), nincs FAILED.txt/.partial fájl, a train_candidates.jsonl és az
    export_index.tsv sha256-ja és sorszáma egyezik a manifesttel, a sor-sha256-ok egyeznek;
  - a kizárási lista jelenlegi tartalma megegyezik a manifestben rögzítettel (elavult
    export felismerése), a kizárt azonosítók és a kizárás-jelölésű sorok nincsenek az
    exportban; alapból a forrásfájlok sha256-ja és a kizárt sorok forrássora is egyezik
    (és a kizárt sorok blokkja nincs a kimenetben);
  - a kiírt szöveg lemezről visszaolvasva blokkra bontva és visszaparse-olva pontosan az
    eredeti instruction/input/output mezőket adja; a blokk-index visszakövethető;
  - alapból a TÉNYLEGES régi betöltő (src/train_chat.py load_text / split_train_val /
    build_vocab / encode) is feldolgozza a fájlt, modell tanítása nélkül: minden blokk
    sértetlen marad, minden karakter kódolható. (Ennek a felosztása csak diagnosztika,
    eldobjuk; NEM a train/val/test felosztás.)

Kimenet (új futás-mappa, soha nem ír felül):
    chat_blocks.txt, block_index.tsv, withheld_rows.tsv, manifest_te2.json

Használat:
    python tools/dataset_export_chat_text.py --te1-export <te1 futás-mappa> --out-dir <mappa>
        [--run-name <név>] [--exclusions <lista>] [--no-legacy-loader-check]
        [--no-clean-recheck] [--fail-on-withheld]

Kilépési kódok: 0 sikeres; 2 argumentumhiba; 20 TE-1 export hiba; 21 kizárási hiba/elavult export;
22 ellenőrzés sikertelen; 23 kimeneti útvonal hiba; 24 visszatartott sor (--fail-on-withheld).

NEM tartalmi ellenőrzés, NEM training-ready, NEM train/val/test felosztás.
"""

import argparse
import datetime
import hashlib
import json
import os
import re
import sys
import unicodedata

import dataset_export_train as te1

TOOL_VERSION = "te2-1.0"

CHAT_FILE = "chat_blocks.txt"
INDEX_FILE = "block_index.tsv"
WITHHELD_FILE = "withheld_rows.tsv"
MANIFEST_FILE = "manifest_te2.json"
FAILED_FILE = "FAILED.txt"

SRC_DIR = os.path.join(te1.REPO_ROOT, "src")

SCOPE_DISCLAIMER = (
    "Előkészítő export a jelenlegi betöltő formátumára. NEM tartalmi ellenőrzés, NEM training-ready "
    "állapot, és NEM train/validation/test felosztás; a tanítás indítása külön engedély."
)

CODE_INPUT = 20
CODE_EXCLUSION = 21
CODE_VERIFY = 22
CODE_OUTPUT = 23
CODE_WITHHELD = 24


class TE2Error(Exception):
    exit_code = 1


class Te1ExportError(TE2Error):
    exit_code = CODE_INPUT


class ExclusionCheckError(TE2Error):
    exit_code = CODE_EXCLUSION


class VerificationError(TE2Error):
    exit_code = CODE_VERIFY


class OutputPathError(TE2Error):
    exit_code = CODE_OUTPUT


class WithheldRowsError(TE2Error):
    exit_code = CODE_WITHHELD


# ---------------------------------------------------------------------------
# blokk-formátum: renderelés, visszaparse-olás, veszteségmentesség
# ---------------------------------------------------------------------------

USER_PREFIX = "User: "
AI_DELIMITER = "\nAI: "
BLOCK_SEPARATOR = "\n\n"
_LINE_LABEL_RE = re.compile(r"^\s*(?:User|AI)\s*:")
_INLINE_LABEL_RE = re.compile(r"(?<![A-Za-z0-9])(?:User|AI)\s*:")
FIELDS = ("instruction", "input", "output")


def render_block(obj):
    """Egy sor blokkja. Csak akkor hívható, ha block_reasons(obj) üres."""
    text = USER_PREFIX + obj["instruction"]
    if obj["input"] != "":
        text += "\n" + obj["input"]
    return text + AI_DELIMITER + obj["output"]


def parse_block(block):
    """A blokk visszafejtése (instruction, input, output) hármassá; ValueError, ha a blokk
    nem a dokumentált nyelvtan szerinti."""
    if not block.startswith(USER_PREFIX):
        raise ValueError("a blokk nem 'User: ' előtaggal kezdődik")
    cut = block.find(AI_DELIMITER)
    if cut == -1:
        raise ValueError("a blokkban nincs 'AI: ' sor")
    user_part = block[len(USER_PREFIX):cut]
    output = block[cut + len(AI_DELIMITER):]
    instruction, _sep, inp = user_part.partition("\n")
    return instruction, inp, output


def _has_forbidden_char(text):
    for ch in text:
        if ch in "\n\t":
            continue
        if ch == "\r" or unicodedata.category(ch) in ("Cc", "Zl", "Zp"):
            return ch
    return None


def block_reasons(obj):
    """A veszteségmentes átadást akadályozó okok listája (üres = átadható)."""
    reasons = []
    for f in FIELDS:
        if not isinstance(obj.get(f), str):
            reasons.append(f"field_not_string:{f}")
    if reasons:
        return reasons
    instruction, inp, output = obj["instruction"], obj["input"], obj["output"]
    if not instruction.strip():
        reasons.append("empty_instruction")
    if not output.strip():
        reasons.append("empty_output")
    if inp != "" and not inp.strip():
        reasons.append("whitespace_only_input")
    for f in FIELDS:
        v = obj[f]
        if "\r" in v:
            reasons.append(f"carriage_return:{f}")
        bad = _has_forbidden_char(v)
        if bad is not None and bad != "\r":
            reasons.append(f"control_character:{f}")
        if "\n\n" in v:
            reasons.append(f"blank_line:{f}")
        if v.startswith("\n") or v.endswith("\n"):
            reasons.append(f"edge_newline:{f}")
    if "\n" in instruction:
        reasons.append("multiline_instruction")
    for f in ("input", "output"):
        lines = obj[f].split("\n")
        # az output első sora az "AI: " után áll; az input minden sora új sor a blokkban
        check = lines if f == "input" else lines[1:]
        if any(_LINE_LABEL_RE.match(line) for line in check):
            reasons.append(f"role_label_at_line_start:{f}")
    # az instruction egyetlen sor, ezért csak a folytatósor-szabály releváns rá (nincs)
    return reasons


def block_flags(obj):
    flags = []
    if any(_INLINE_LABEL_RE.search(obj[f]) for f in FIELDS):
        flags.append("inline_role_label")
    if "\n" in obj["input"]:
        flags.append("multiline_input")
    if "\n" in obj["output"]:
        flags.append("multiline_output")
    if obj["input"] != "":
        flags.append("has_input")
    return flags


# ---------------------------------------------------------------------------
# TE-1 export beolvasása és ellenőrzése
# ---------------------------------------------------------------------------

def _resolve(path):
    return path if os.path.isabs(path) else os.path.join(te1.REPO_ROOT, path)


def _split_lines(raw):
    parts = raw.split(b"\n")
    if parts and parts[-1] == b"":
        parts.pop()
    return [p[:-1] if p.endswith(b"\r") else p for p in parts]


def load_te1_export(run_dir):
    """Ellenőrzi a TE-1 export sikerességét és épségét; visszaad (manifest, manifest_sha, rows).
    rows: dict(id, obj, line_bytes, row_sha256, source_file, source_line)."""
    run_dir = os.path.abspath(run_dir)
    if not os.path.isdir(run_dir):
        raise Te1ExportError(f"A TE-1 futás-mappa nem található: {run_dir}")
    for name in (te1.MANIFEST_FILE, te1.EXPORT_FILE, te1.INDEX_FILE):
        if not os.path.isfile(os.path.join(run_dir, name)):
            raise Te1ExportError(f"A TE-1 export hiányos, nincs {name}: {run_dir}")
    leftovers = sorted(n for n in os.listdir(run_dir) if n == te1.FAILED_FILE or n.endswith(".partial"))
    if leftovers:
        raise Te1ExportError(f"A TE-1 export nem sikeres (maradék fájlok: {', '.join(leftovers)}): {run_dir}")

    manifest_raw = te1.read_bytes(os.path.join(run_dir, te1.MANIFEST_FILE))
    try:
        manifest = json.loads(manifest_raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Te1ExportError(f"A TE-1 manifest nem érvényes JSON: {exc}")
    if not isinstance(manifest, dict):
        raise Te1ExportError("A TE-1 manifest nem JSON objektum.")

    problems = []
    if manifest.get("status") != "ok":
        problems.append(f"status={manifest.get('status')!r} (várt: 'ok')")
    if manifest.get("tool") != "tools/dataset_export_train.py":
        problems.append(f"nem TE-1 manifest (tool={manifest.get('tool')!r})")
    if not str(manifest.get("tool_version", "")).startswith("te1-"):
        problems.append(f"ismeretlen TE-1 verzió: {manifest.get('tool_version')!r}")
    if manifest.get("training_ready") is not False or manifest.get("content_verified") is not False:
        problems.append("a manifest training_ready/content_verified értéke nem false (ellentmond a TE-1 szerepének)")
    checks = manifest.get("checks")
    if not isinstance(checks, dict) or not checks or not all(v is True for v in checks.values()):
        problems.append("a manifest ellenőrzései nem mind igazak")
    for key in ("counts", "outputs", "exclusion_list", "input_files"):
        if key not in manifest:
            problems.append(f"hiányzó manifest-kulcs: {key}")
    if problems:
        raise Te1ExportError("Érvénytelen TE-1 manifest: " + "; ".join(problems))

    export_path = os.path.join(run_dir, te1.EXPORT_FILE)
    index_path = os.path.join(run_dir, te1.INDEX_FILE)
    export_raw = te1.read_bytes(export_path)
    index_raw = te1.read_bytes(index_path)
    out = manifest["outputs"]
    for label, raw, key in (("export", export_raw, "export_file"), ("index", index_raw, "index_file")):
        want = out.get(key, {}).get("sha256")
        if hashlib.sha256(raw).hexdigest() != want:
            raise Te1ExportError(f"A TE-1 {label}-fájl ellenőrzőösszege nem egyezik a manifesttel ({key}).")

    lines = _split_lines(export_raw)
    counts = manifest["counts"]
    if counts.get("rows_exported") != len(lines) or out["export_file"].get("rows") != len(lines):
        raise Te1ExportError(f"A TE-1 export sorszáma ({len(lines)}) nem egyezik a manifesttel.")
    if counts.get("rows_read") != counts.get("rows_exported", 0) + counts.get("rows_excluded", 0):
        raise Te1ExportError("A TE-1 manifest darabszámai nem egyensúlyban vannak.")
    if len(manifest["exclusion_list"].get("entries", [])) != counts.get("rows_excluded"):
        raise Te1ExportError("A TE-1 manifest kizárási bejegyzéseinek száma nem egyezik a kizárt sorok számával.")

    idx_lines = index_raw.decode("utf-8").splitlines()
    if not idx_lines or idx_lines[0].split("\t") != ["id", "source_file", "source_line", "row_sha256"]:
        raise Te1ExportError("A TE-1 export_index.tsv fejléce nem a várt.")
    idx_rows = [ln.split("\t") for ln in idx_lines[1:]]
    if len(idx_rows) != len(lines):
        raise Te1ExportError("A TE-1 export_index.tsv sorszáma nem egyezik az exporttal.")

    rows, seen = [], set()
    for pos, (line, idx) in enumerate(zip(lines, idx_rows)):
        try:
            obj = json.loads(line.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise Te1ExportError(f"A TE-1 export {pos + 1}. sora nem érvényes JSON.")
        if not isinstance(obj, dict) or not isinstance(obj.get("id"), str) or not obj["id"]:
            raise Te1ExportError(f"A TE-1 export {pos + 1}. sorának nincs érvényes 'id'-je.")
        if obj["id"] in seen:
            raise Te1ExportError(f"Duplikált azonosító a TE-1 exportban: {obj['id']}")
        seen.add(obj["id"])
        sha = hashlib.sha256(line).hexdigest()
        if len(idx) != 4 or idx[0] != obj["id"] or idx[3] != sha:
            raise Te1ExportError(f"A TE-1 index {pos + 1}. sora nem egyezik az export sorával ({obj['id']}).")
        rows.append({"id": obj["id"], "obj": obj, "line_bytes": line, "row_sha256": sha,
                     "source_file": idx[1], "source_line": int(idx[2])})
    return manifest, hashlib.sha256(manifest_raw).hexdigest(), rows


def check_exclusions(manifest, rows, exclusions_path=None, clean_recheck=True):
    """Kizárások újraellenőrzése; visszaad (excluded_rows_source, live_info, recheck_info).
    excluded_rows_source: {id: nyers forrássor-bájtok} (csak clean_recheck esetén)."""
    entries = manifest["exclusion_list"]["entries"]
    excluded_ids = {e["id"] for e in entries}
    if len(excluded_ids) != len(entries):
        raise ExclusionCheckError("A TE-1 manifest kizárási bejegyzései között duplikált azonosító van.")
    if not excluded_ids and not manifest["exclusion_list"].get("allow_empty"):
        raise ExclusionCheckError("A TE-1 manifest nem tartalmaz kizárást, és nem is engedélyezte az üres listát.")

    leaked = sorted(r["id"] for r in rows if r["id"] in excluded_ids)
    if leaked:
        raise ExclusionCheckError("KIZÁRT azonosító van a TE-1 exportban: " + ", ".join(leaked))
    marked = sorted(r["id"] for r in rows if te1.EXCLUSION_NOTE_MARKER in str(r["obj"].get("quality_notes", "")))
    if marked:
        raise ExclusionCheckError("Kizárás-jelölésű sor van a TE-1 exportban: " + ", ".join(marked))

    list_path = _resolve(exclusions_path or manifest["exclusion_list"]["path"])
    try:
        live_entries, live_sha = te1.parse_exclusion_list(
            list_path, allow_empty=bool(manifest["exclusion_list"].get("allow_empty")))
    except te1.ExclusionListError as exc:
        raise ExclusionCheckError(f"A kizárási lista most nem érvényes: {exc}")
    if live_sha != manifest["exclusion_list"].get("sha256") or {e["id"] for e in live_entries} != excluded_ids:
        raise ExclusionCheckError(
            "A kizárási lista megváltozott a TE-1 export óta (elavult export). Futtasd újra a TE-1-et.")
    live_info = {"path": te1.rel_path(list_path), "sha256": live_sha, "ids": sorted(excluded_ids)}

    excluded_source = {}
    recheck = {"performed": False}
    if clean_recheck:
        for info in manifest["input_files"]:
            path = _resolve(info["path"])
            if not os.path.isfile(path) or te1.sha256_file(path) != info["sha256"]:
                raise ExclusionCheckError(
                    f"A forrásfájl hiányzik vagy megváltozott a TE-1 export óta: {info['path']}. Futtasd újra a TE-1-et.")
        for e in entries:
            path = _resolve(e["source_file"])
            lines = _split_lines(te1.read_bytes(path))
            n = e["source_line"]
            if n < 1 or n > len(lines) or hashlib.sha256(lines[n - 1]).hexdigest() != e["row_sha256"]:
                raise ExclusionCheckError(f"A kizárt sor forrássora nem egyezik a manifesttel: {e['id']} ({e['source_file']}:{n}).")
            try:
                got_id = json.loads(lines[n - 1].decode("utf-8")).get("id")
            except (UnicodeDecodeError, json.JSONDecodeError):
                got_id = None
            if got_id != e["id"]:
                raise ExclusionCheckError(f"A forrássor azonosítója nem egyezik: {e['id']} ({e['source_file']}:{n}).")
            excluded_source[e["id"]] = lines[n - 1]
        recheck = {"performed": True, "source_files_sha256_verified": len(manifest["input_files"]),
                   "excluded_source_rows_verified": len(entries)}
    return excluded_source, live_info, recheck


# ---------------------------------------------------------------------------
# ellenőrzések a kiírt fájlon
# ---------------------------------------------------------------------------

def verify_chat_file(chat_path, blocks, emitted_rows, excluded_blocks):
    """Lemezről visszaolvasott szöveg: blokkhatárok, visszaparse-olás, kizárt blokkok hiánya."""
    raw = te1.read_bytes(chat_path)
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise VerificationError("A kiírt szövegfájl nem érvényes UTF-8.")
    problems = []
    if "\r" in text:
        problems.append("a kiírt szöveg CR karaktert tartalmaz")
    if not text.endswith(BLOCK_SEPARATOR) or text.endswith(BLOCK_SEPARATOR + "\n"):
        problems.append("a fájl nem pontosan egy záró üres sorral (\\n\\n) végződik")
    got_blocks = text[:-len(BLOCK_SEPARATOR)].split(BLOCK_SEPARATOR) if text else []
    if got_blocks != blocks:
        problems.append(f"a visszaolvasott blokkok nem egyeznek a kiírtakkal ({len(got_blocks)} vs {len(blocks)})")
    else:
        for i, (blk, row) in enumerate(zip(got_blocks, emitted_rows), 1):
            try:
                instruction, inp, output = parse_block(blk)
            except ValueError as exc:
                problems.append(f"a(z) {i}. blokk nem parse-olható ({exc}; {row['id']})")
                continue
            obj = row["obj"]
            if (instruction, inp, output) != (obj["instruction"], obj["input"], obj["output"]):
                problems.append(f"a(z) {i}. blokk visszafejtése eltér az eredeti sortól ({row['id']})")
    leaked = sorted(set(got_blocks) & set(excluded_blocks))
    if leaked:
        problems.append("KIZÁRT sor blokkja került a kimenetbe")
    if problems:
        raise VerificationError("A kimeneti ellenőrzés SIKERTELEN: " + "; ".join(problems[:5]))
    return text


def legacy_loader_check(chat_path, expected_text, blocks):
    """A TÉNYLEGES src/train_chat.py függvényeivel feldolgozza a fájlt (tanítás nélkül)."""
    if SRC_DIR not in sys.path:
        sys.path.insert(0, SRC_DIR)
    try:
        import config  # noqa: E402
        import train_chat  # noqa: E402
    except Exception as exc:  # pragma: no cover - környezetfüggő
        raise VerificationError(f"A régi betöltő (src/train_chat.py) nem importálható: {exc}")

    text = train_chat.load_text(chat_path)
    problems = []
    if text != expected_text:
        problems.append("a load_text() eredménye eltér a kiírt szövegtől (sorvég-átalakítás?)")
    loader_blocks = [b for b in text.split("\n\n") if b.strip()]
    if loader_blocks != blocks:
        problems.append("a régi betöltő blokkfelbontása (text.split('\\n\\n')) nem egyezik a kiírt blokkokkal")
    train_text, val_text = train_chat.split_train_val(text, config.val_split, config.seed)
    train_blocks = [b for b in train_text[:-1].split("\n\n") if b.strip()] if len(train_text) > 1 else []
    val_blocks = [b for b in val_text[:-1].split("\n\n") if b.strip()] if len(val_text) > 1 else []
    if sorted(train_blocks + val_blocks) != sorted(blocks):
        problems.append("a régi betöltő felosztása után a blokkok nem maradtak sértetlenek")
    stoi, _itos = train_chat.build_vocab(text)
    ids = train_chat.encode(text, stoi)
    if int(ids.numel()) != len(text) or set(text) != set(stoi):
        problems.append("nem minden karakter kódolható a betöltő szótárával")
    if problems:
        raise VerificationError("A régi betöltővel végzett kompatibilitás-ellenőrzés SIKERTELEN: " + "; ".join(problems))
    pairs = text.count("User: ")
    return {
        "performed": True,
        "loader": "src/train_chat.py (load_text, split_train_val, build_vocab, encode)",
        "text_chars": len(text),
        "loader_pair_count_user_colon_space": pairs,
        "pair_count_equals_blocks": pairs == len(blocks),
        "blocks_intact_after_real_split": True,
        "all_characters_encodable": True,
        "vocab_size": len(stoi),
        "diagnostic_split_train_blocks": len(train_blocks),
        "diagnostic_split_val_blocks": len(val_blocks),
        "seq_length": config.seq_length,
        "note": "A felosztás csak a betöltő feldolgozásának diagnosztikája, eldobva; NEM a train/validation/test felosztás. Tanítás nem történt.",
    }


# ---------------------------------------------------------------------------
# fő folyamat
# ---------------------------------------------------------------------------

def run_te2(te1_run_dir, out_dir, run_name=None, exclusions_path=None, legacy_check=True,
            clean_recheck=True, fail_on_withheld=False):
    try:
        out_abs = te1.check_out_dir(out_dir, te1_run_dir)
    except te1.OutputPathError as exc:
        raise OutputPathError(str(exc))

    manifest, manifest_sha, rows = load_te1_export(te1_run_dir)
    excluded_source, live_info, recheck = check_exclusions(manifest, rows, exclusions_path, clean_recheck)

    # renderelés + veszteségmentesség
    emitted, withheld = [], []
    for r in rows:
        reasons = block_reasons(r["obj"])
        if reasons:
            withheld.append((r, reasons))
        else:
            emitted.append(r)
    if fail_on_withheld and withheld:
        raise WithheldRowsError(f"{len(withheld)} sor nem adható át veszteségmentesen (pl. {withheld[0][0]['id']}: "
                                f"{', '.join(withheld[0][1])}); --fail-on-withheld miatt megállt.")
    if not emitted:
        raise VerificationError("Egyetlen sor sem adható át blokként (üres kimenet).")
    blocks = [render_block(r["obj"]) for r in emitted]
    text = "".join(blk + BLOCK_SEPARATOR for blk in blocks)

    excluded_blocks = set()
    for rid, line in excluded_source.items():
        obj = json.loads(line.decode("utf-8"))
        if not block_reasons(obj):
            excluded_blocks.add(render_block(obj))

    stamp = run_name or datetime.datetime.now(datetime.timezone.utc).strftime("te2_%Y%m%dT%H%M%SZ")
    if not re.match(r"^[A-Za-z0-9._-]+$", stamp):
        raise OutputPathError(f"Érvénytelen futásnév: {stamp!r}")
    run_dir = os.path.join(out_abs, stamp)
    if os.path.exists(run_dir):
        raise OutputPathError(f"A futás-mappa már létezik, nem írom felül: {run_dir}")
    os.makedirs(run_dir)

    chat_partial = os.path.join(run_dir, CHAT_FILE + ".partial")
    with open(chat_partial, "wb") as f:
        f.write(text.encode("utf-8"))
    try:
        verified_text = verify_chat_file(chat_partial, blocks, emitted, excluded_blocks)
        legacy = {"performed": False, "reason": "kikapcsolva (--no-legacy-loader-check)"}
        if legacy_check:
            legacy = legacy_loader_check(chat_partial, verified_text, blocks)
    except TE2Error as exc:
        with open(os.path.join(run_dir, FAILED_FILE), "w", encoding="utf-8", newline="\n") as f:
            f.write(str(exc) + "\n")
        raise

    chat_final = os.path.join(run_dir, CHAT_FILE)
    os.replace(chat_partial, chat_final)

    index_path = os.path.join(run_dir, INDEX_FILE)
    with open(index_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("block_no\tid\tcategory\tsource_file\tsource_line\trow_sha256\tblock_sha256\tblock_chars\tflags\n")
        for n, (r, blk) in enumerate(zip(emitted, blocks), 1):
            f.write("\t".join([str(n), r["id"], str(r["obj"].get("category") or "(nincs)"), r["source_file"],
                               str(r["source_line"]), r["row_sha256"],
                               hashlib.sha256(blk.encode("utf-8")).hexdigest(), str(len(blk)),
                               ",".join(block_flags(r["obj"]))]) + "\n")
    withheld_path = os.path.join(run_dir, WITHHELD_FILE)
    with open(withheld_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("id\tcategory\tsource_file\tsource_line\trow_sha256\treasons\n")
        for r, reasons in withheld:
            f.write("\t".join([r["id"], str(r["obj"].get("category") or "(nincs)"), r["source_file"],
                               str(r["source_line"]), r["row_sha256"], ",".join(reasons)]) + "\n")

    reason_counts = {}
    for _r, reasons in withheld:
        for reason in reasons:
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
    by_cat = {}
    for r in emitted:
        c = str(r["obj"].get("category") or "(nincs)")
        by_cat[c] = by_cat.get(c, 0) + 1
    flag_lists = [block_flags(r["obj"]) for r in emitted]
    warnings = []
    if withheld:
        warnings.append(f"{len(withheld)} sor NEM adható át veszteségmentesen, ezek nincsenek a szövegfájlban "
                        f"(lásd {WITHHELD_FILE}); az export ezért nem tartalmazza a TE-1 export összes sorát.")
    if legacy.get("performed") and not legacy.get("pair_count_equals_blocks"):
        warnings.append("A régi betöltő 'User: ' számlálója eltér a blokkok számától (sor közben szereplő 'User: ' említés).")
    if not legacy.get("performed"):
        warnings.append("A régi betöltővel végzett kompatibilitás-ellenőrzés NEM futott le.")
    if not recheck.get("performed"):
        warnings.append("A forrásfájlokkal végzett újraellenőrzés NEM futott le (--no-clean-recheck).")

    result = {
        "tool": "tools/dataset_export_chat_text.py",
        "tool_version": TOOL_VERSION,
        "status": "ok",
        "created_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "git_commit": te1.git_commit(),
        "python": sys.version.split()[0],
        "te1_export": {
            "run_dir": te1.rel_path(te1_run_dir),
            "manifest_sha256": manifest_sha,
            "tool_version": manifest.get("tool_version"),
            "git_commit": manifest.get("git_commit"),
            "export_file_sha256": manifest["outputs"]["export_file"]["sha256"],
            "index_file_sha256": manifest["outputs"]["index_file"]["sha256"],
            "rows": len(rows),
            "rows_excluded_by_te1": manifest["counts"]["rows_excluded"],
        },
        "exclusion_recheck": {"live_list": live_info, "clean_sources": recheck,
                              "excluded_ids": live_info["ids"],
                              "excluded_blocks_absent": True if recheck.get("performed") else "not_checked"},
        "format": {
            "block_grammar": "User: <instruction>[\\n<input>]\\nAI: <output>",
            "block_terminator": "\\n\\n (minden blokk után, az utolsó után is)", "encoding": "utf-8", "newline": "LF",
            "input_rendering": "az instruction után új sorban, ha nem üres; többsoros is lehet",
            "labels_in_content": "sor elején álló User:/AI: felirat visszatartást okoz; sor közbeni említés átmegy és inline_role_label jelzést kap",
        },
        "counts": {
            "rows_in": len(rows), "blocks_written": len(emitted), "rows_withheld": len(withheld),
            "all_rows_carried": not withheld,
            "withheld_by_reason": dict(sorted(reason_counts.items())),
            "blocks_by_category": dict(sorted(by_cat.items())),
            "blocks_with_input": sum(1 for fl in flag_lists if "has_input" in fl),
            "blocks_with_multiline_input": sum(1 for fl in flag_lists if "multiline_input" in fl),
            "blocks_with_multiline_output": sum(1 for fl in flag_lists if "multiline_output" in fl),
            "blocks_with_inline_role_label": sum(1 for fl in flag_lists if "inline_role_label" in fl),
        },
        "outputs": {
            "chat_file": {"path": CHAT_FILE, "sha256": te1.sha256_file(chat_final), "blocks": len(emitted),
                          "chars": len(text), "bytes": len(text.encode("utf-8"))},
            "index_file": {"path": INDEX_FILE, "sha256": te1.sha256_file(index_path), "rows": len(emitted)},
            "withheld_file": {"path": WITHHELD_FILE, "sha256": te1.sha256_file(withheld_path), "rows": len(withheld)},
        },
        "checks": {
            "te1_manifest_ok_and_file_checksums_match": True,
            "exclusion_list_unchanged_since_te1_export": True,
            "excluded_ids_and_marked_rows_absent_from_te1_export": True,
            "output_reread_blocks_roundtrip_to_source_fields": True,
            "excluded_blocks_absent_from_output": True if recheck.get("performed") else "skipped",
            "blocks_plus_withheld_equal_rows_in": len(emitted) + len(withheld) == len(rows),
            "legacy_loader_check": "performed" if legacy.get("performed") else "skipped",
            "clean_source_recheck": "performed" if recheck.get("performed") else "skipped",
        },
        "legacy_loader_check": legacy,
        "warnings": warnings,
        "content_verified": False,
        "training_ready": False,
        "split_assigned": False,
        "prepared_for": "előkészítő export a jelenlegi betöltő formátumára; a train/validation/test felosztás külön követelmény",
        "scope_disclaimer": SCOPE_DISCLAIMER,
    }
    manifest_partial = os.path.join(run_dir, MANIFEST_FILE + ".partial")
    with open(manifest_partial, "w", encoding="utf-8", newline="\n") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")
    os.replace(manifest_partial, os.path.join(run_dir, MANIFEST_FILE))
    result["run_dir"] = run_dir
    return result


def _main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(
        description="TE-2: TE-1 exportból előkészítő User:/AI: szövegfájl (NEM felosztás, NEM training-ready).")
    parser.add_argument("--te1-export", required=True, help="A TE-1 export futás-mappája.")
    parser.add_argument("--out-dir", required=True, help="A kimeneti szülőmappa (a futás új almappába kerül).")
    parser.add_argument("--run-name", default=None)
    parser.add_argument("--exclusions", default=None, help="Kizárási lista (alapból a manifestben rögzített útvonal).")
    parser.add_argument("--no-legacy-loader-check", action="store_true",
                        help="Kihagyja a régi betöltővel végzett ellenőrzést (a manifest jelzi).")
    parser.add_argument("--no-clean-recheck", action="store_true",
                        help="Kihagyja a forrásfájlok/kizárt sorok újraellenőrzését (a manifest jelzi).")
    parser.add_argument("--fail-on-withheld", action="store_true",
                        help="Hibával áll meg, ha bármely sor nem adható át veszteségmentesen.")
    args = parser.parse_args(argv)
    try:
        result = run_te2(args.te1_export, args.out_dir, args.run_name, args.exclusions,
                         legacy_check=not args.no_legacy_loader_check,
                         clean_recheck=not args.no_clean_recheck, fail_on_withheld=args.fail_on_withheld)
    except (TE2Error, te1.ExportError) as exc:
        print(f"HIBA ({type(exc).__name__}): {exc}", file=sys.stderr)
        return getattr(exc, "exit_code", 1)
    c = result["counts"]
    print(f"TE-2 export kész: {result['run_dir']}")
    print(f"TE-1 sorok: {c['rows_in']} | blokk: {c['blocks_written']} | visszatartott: {c['rows_withheld']}")
    for w in result["warnings"]:
        print(f"FIGYELMEZTETÉS: {w}")
    print(SCOPE_DISCLAIMER)
    return 0


if __name__ == "__main__":
    sys.exit(_main())
