"""
MF-AI-Zero - MT-5: többfordulós tanító BETÖLTŐ (kísérleti, elkülönített modul) - CSAK betöltés és száraz futás.

EZ A MODUL NEM TANÍT. Optimalizáló lépés, gradiens-visszaterjesztés, modellparaméter-frissítés vagy
"betanított" checkpoint mentése NINCS benne (nincs is ilyen kódág: a `--dry-run` kapcsoló kötelező, és
más futási mód nem létezik). A tényleges tanítás megindítása külön, kifejezett felhasználói jóváhagyást
és külön feladatot igényel.

EZ A MODUL ELKÜLÖNÍTETT, KÍSÉRLETI MEGVALÓSÍTÁS:
  - a meglévő v0.7 `train_chat.py`, a `chat.py`/`guard.py`/`router.py` stabil lánc, a `src/memory.py`
    (futásidejű előzmény) és a webapp/backend **nem módosul**; ez a modul semelyiket nem importálja és
    nem hívja meg. A `config.py`-t és a `model.py` `CharLSTM` osztályát **csak olvassa** (megosztott
    architektúra-definíció, nem "a tanító" maga).
  - a `tools/` alatti MT-1..MT-4 eszközöket **nem importálja** (nincs `sys.path`-csavarás a `tools/`
    felé): az MT-4 export érvényességét ÖNÁLLÓAN, saját (kisebb, célzott) ellenőrzéssel vizsgálja -
    ez szándékos elkülönítés, nem a teljes MT-4-logika megkettőzése.

BEMENET: egy MT-4 `export_manifest.json` és a hozzá tartozó `samples_<rész>_<mód>.jsonl` fájlok
(`tools/multiturn_export.py`, mt4-1.x). A `--mode` kifejezett, és egyeznie kell az export
`data_kind`/`fixture` jelölésével: **fixture (tesztadat) export kizárólag `--mode fixture` mellett
fogadható el**; `--mode dataset` mellett egy fixture export elutasítva (és fordítva). Sérült
(ellenőrzőösszeg-eltérés), hiányos vagy elavult (rossz eszköz/verzió/státusz, a hat kizárás nem
ellenőrzött) bemenettel a betöltés hibával megáll.

RENDERELÉSI MÓD (a felhasználó döntése): **R2 (teljes előzmény) az elsődleges** betöltési próba -
veszteségmentes, a mintahatárt és a célválaszhoz szükséges teljes előzményt megőrzi. **R1 (futásidő-hű)
külön, összehasonlító próba** - a csonkolási és az előzményvesztési jelölések (MT-4 `history_truncation`,
`dependency`) megőrződnek és a jelentésben külön szerepelnek. **R3 nincs** (nem is létezik export-oldalon).
Egyik mód betöltése sem jelent tanítási jóváhagyást bármelyikre.

ABLAKOLÁS HELYETT MINTAHATÁR: a meglévő `train_chat.get_batch()` a teljes szöveget összefűzi és
64 karakteres VÉLETLEN ablakokat vág ki belőle (ablakhatáron átnyúlva, beszélgetések között is). Ez a
modul EZT NEM TESZI: minden tanítási minta (MT-4 `text` mezője) **egyben, a saját határain belül** kerül
kódolásra és kötegelésre; a köteg egy sora mindig pontosan EGY minta (egy beszélgetés egy célfordulója,
a hozzá tartozó előzménnyel), amelyet SOSEM fűz össze másik beszélgetés szövegével, és a kötegben lévő
sorok az LSTM-en át egymástól függetlenek (minden előrefutás nulla kezdő rejtett állapottal indul - lásd
`build_probe_model`/`forward_check` - és a kötegek KÖZÖTT sincs átvitt állapot: rejtett állapotot ez a
modul sosem ad tovább egyik hívásból a következőbe).

CÉLMASZK: a veszteség-maszk az MT-4 minta `target` mezőjéből (a célválasz karaktertartománya a renderelt
szövegben) származik, NEM heurisztikából. Az előzmény, az aktuális kérdés és a kitöltés (padding) sosem
része a célnak - ezt a `build_target_mask`/`verify_mask_alignment` és a hozzá tartozó tesztek igazolják.

HOSSZKORLÁT: a `--max-chars` (explicit, alapból `DEFAULT_MAX_CHARS` = 4096 karakter, lásd lentebb) fölötti
mintát a betöltő **nem csonkítja csendben**: kihagyja a kötegelésből, és okkal (a mért hosszal együtt)
jelenti (a jelentés `withheld_oversized` mezője, `sample_lengths.tsv`). Ez KÍSÉRLETI, dokumentált
védőkorlát, nem tartalmi ítélet.

KOMPATIBILITÁSI KORLÁT (külön a hosszkorláttól): a `CharLSTM` (LSTM) architektúra elméletileg tetszőleges
hosszú sorozatot fogad (nincs rögzített kontextusablak, mint egy Transformernél); ezt egy FRISS
(véletlen inicializált, tanítatlan) próba-modellel, előrefutással és veszteség-számítással ellenőrzi ez a
modul (`forward_check`) - ez az ELŐREFUTÁS SIKERE, nem tanulás bizonyítéka. A jelenleg BETANÍTOTT v0.7
modell viszont mindvégig `config.seq_length` (jelenleg 64) karakteres véletlen ablakokon tanult, folytonos
állapotátvitel nélkül - tényleges, TANULT tapasztalata ennél hosszabb, összefüggő kontextusra nincs. A
jelentés ezt a két dolgot (architektúra vs. tanult tapasztalat) külön mezőben, külön szöveggel jelzi, és
**a sikeres betöltés/előrefutás önmagában NEM bizonyítja a hosszú kontextus tényleges megtanulását**.

Használat:
    python src/train_multiturn.py --export-manifest <export_manifest.json> --mode dataset|fixture \\
        --out-dir <mappa> --dry-run [--modes R2,R1] [--max-chars 4096] [--batch-size 16]
        [--allow-no-te1-comparison] [--run-name <név>]
    python src/train_multiturn.py --verify-report <dryrun_report.json>

Kilépési kódok: 0 kész, nincs visszatartott/hibás minta; 1 kész, de figyelmet kér (visszatartott
(túl hosszú) minta, ismeretlen karakter a validation/test részen, előrefutási hiba); 2 argumentumhiba;
10 bemeneti fájl hiba; 11 sérült/ellenőrzőösszeg-eltérő export; 12 elavult/nem megfelelő export (eszköz,
verzió, státusz, mód/fixture eltérés, hiányzó kizárás-ellenőrzés); 13 kimeneti útvonal hiba;
14 belső önellenőrzés hibát talált (nincs véglegesített jelentés); 15 elutasított kérés (hiányzó
`--dry-run`, ismeretlen renderelési mód, R3 kérése).
"""

import argparse
import datetime
import hashlib
import json
import os
import re
import statistics
import sys
import time

import torch
import torch.nn.functional as F

import config
from model import CharLSTM

TOOL_VERSION = "mt5-1.0"
MT4_TOOL = "tools/multiturn_export.py"
SPLITS = ("train", "validation", "test")
SUPPORTED_MODES = ("R1", "R2")
PRIMARY_MODE = "R2"
SECONDARY_MODE = "R1"
DEFAULT_MODES = (PRIMARY_MODE, SECONDARY_MODE)
DEFAULT_MAX_CHARS = 4096
DEFAULT_BATCH_SIZE = 16
REPORT_FILE = "dryrun_report.json"
LENGTHS_FILE = "sample_lengths.tsv"
FIXTURE_MARKER_FILE = "FIXTURE_TEST_DATA_NOT_FOR_TRAINING.txt"

EXIT_ATTENTION = 1
EXIT_INPUT, EXIT_INVALID, EXIT_STALE, EXIT_OUTPUT, EXIT_VERIFY, EXIT_REFUSED = 10, 11, 12, 13, 14, 15

DISCLAIMER = (
    "Ez a betöltő NEM tanít: nincs optimalizáló lépés, gradiens-visszaterjesztés, paraméterfrissítés vagy "
    "betanított modell mentése. A jelentés a betöltés, a kódolás, a kötegelés és a maszkok ellenőrzésének "
    "eredménye. A sikeres betöltés/előrefutás nem bizonyítja a hosszú kontextus tényleges megtanulását, és "
    "nem jelenti sem az R1, sem az R2 mód tanítási jóváhagyását. A split_approved/content_verified/"
    "training_ready állapotokat ez a modul sosem állítja igazra; a forrás-export ezen mezőit változatlanul "
    "veszi át."
)
LIMITATIONS = [
    "A célmaszk az MT-4 `target` mezőjéből származik: ha az MT-4 renderelése hibás lenne, ez a modul azt nem tudja észrevenni (csak a saját, belső illeszkedését ellenőrzi, nem a renderelés tartalmi helyességét).",
    "A hosszkorlát (`--max-chars`) fölötti minták visszatartása KÍSÉRLETI, technikai védőkorlát: nem tartalmi ítélet, és az alapérték nem kalibrált valódi többfordulós adaton (mert az még nem létezik).",
    "Az előrefutási ellenőrzés egy FRISS, véletlen inicializált próba-modellel történik (a jelenlegi architektúra méreteivel), NEM a betanított v0.7 checkpointtal: a kiszámított veszteség-érték emiatt tartalmilag értelmezhetetlen, csak az alak/futás helyességének jelzésére szolgál.",
    "A `CharLSTM` architektúra elméletileg tetszőleges hosszú sorozatot fogad; ez nem jelenti azt, hogy egy ténylegesen tanított modell meg is tanulja használni a hosszú kontextust - ehhez tényleges tanítás és kiértékelés kellene, ami ennek a modulnak nem feladata.",
    "Az erőforrás-mérés a kódolt tenzorok becsült mérete és a mért futásidő (ezen a gépen, egy CPU-s, egyszeri futás); nem profilozott csúcsmemória, és más gépen/terhelésnél eltérhet.",
    "Az ismeretlen karakterek kezelése (validation/test) a train-szótárhoz képest történik; ha a train rész maga sem fedi le a nyelv teljes karakterkészletét, ez sok ismeretlen karaktert eredményezhet - ez a szótárépítés, nem a betöltő korlátja.",
    "Valódi többfordulós adaton (a fixture teszteken túl) ez a modul nem futott, mert ilyen adat még nem létezik.",
]


class TrainMultiturnError(Exception):
    exit_code = EXIT_INPUT


class InputFileError(TrainMultiturnError):
    exit_code = EXIT_INPUT


class InvalidExportError(TrainMultiturnError):
    exit_code = EXIT_INVALID


class StaleExportError(TrainMultiturnError):
    exit_code = EXIT_STALE


class OutputError(TrainMultiturnError):
    exit_code = EXIT_OUTPUT


class VerificationError(TrainMultiturnError):
    exit_code = EXIT_VERIFY


class RefusedError(TrainMultiturnError):
    exit_code = EXIT_REFUSED


# ---------------------------------------------------------------------------
# alap segédfüggvények (önállóan, a tools/ eszközök importálása nélkül)
# ---------------------------------------------------------------------------

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def read_bytes(path):
    with open(path, "rb") as f:
        return f.read()


def rel_path(path):
    ap = os.path.abspath(path)
    try:
        rp = os.path.relpath(ap, config.BASE_DIR)
    except ValueError:
        return ap.replace("\\", "/")
    if rp.startswith(".."):
        return ap.replace("\\", "/")
    return rp.replace("\\", "/")


def _read_jsonl(path):
    out = []
    with open(path, "rb") as f:
        raw = f.read()
    for line in raw.split(b"\n"):
        if line.strip():
            out.append(json.loads(line.decode("utf-8")))
    return out


def check_out_dir(out_dir, export_run_dir):
    out_abs = os.path.abspath(out_dir)
    data_dir = os.path.join(config.BASE_DIR, "data")
    for name in ("clean", "raw", "rejected", "inbox"):
        protected = os.path.join(data_dir, name)
        if out_abs == protected or out_abs.startswith(protected + os.sep):
            raise OutputError(f"A kimeneti mappa nem lehet a védett data/{name} alatt: {out_abs}")
    in_abs = os.path.abspath(export_run_dir)
    if out_abs == in_abs or out_abs.startswith(in_abs + os.sep):
        raise OutputError(f"A kimeneti mappa nem lehet a bemeneti (MT-4 export) mappa alatt: {out_abs}")
    return out_abs


# ---------------------------------------------------------------------------
# 1) az MT-4 export betöltése és önálló ellenőrzése
# ---------------------------------------------------------------------------

def load_export(manifest_path, mode, allow_no_te1_comparison=False):
    """Az MT-4 export_manifest.json beolvasása és ellenőrzése. Visszaad: (manifest, run_dir, manifest_sha256).
    Sérült/hiányos -> InvalidExportError; elavult/nem megfelelő (eszköz, verzió, státusz, mód, kizárás) ->
    StaleExportError; mód/fixture ütközés -> RefusedError."""
    if mode not in ("dataset", "fixture"):
        raise RefusedError("A --mode értéke dataset vagy fixture kell legyen.")
    if not os.path.isfile(manifest_path):
        raise InputFileError(f"Az MT-4 export manifest nem található: {manifest_path}")
    run_dir = os.path.dirname(os.path.abspath(manifest_path))
    raw = read_bytes(manifest_path)
    try:
        m = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InvalidExportError(f"Az MT-4 export manifest nem érvényes JSON: {exc}")
    if not isinstance(m, dict):
        raise InvalidExportError("Az MT-4 export manifest nem JSON objektum.")
    need = ("tool", "tool_version", "status", "data_kind", "fixture", "training_data", "statuses", "config",
            "splits", "conversations", "outputs", "exclusion_guard", "training_ready", "content_verified",
            "split_approved", "withheld")
    missing = [k for k in need if k not in m]
    if missing:
        raise InvalidExportError("Az MT-4 export manifest hiányos, hiányzó kulcsok: " + ", ".join(missing))
    if os.path.isfile(os.path.join(run_dir, "FAILED.txt")) or any(n.endswith(".partial") for n in os.listdir(run_dir)):
        raise InvalidExportError(f"Az MT-4 export nem sikeres (FAILED.txt vagy .partial maradék): {run_dir}")
    if m["tool"] != MT4_TOOL:
        raise StaleExportError(f"Nem MT-4 export manifest (tool={m['tool']!r}).")
    if not str(m["tool_version"]).startswith("mt4-"):
        raise StaleExportError(f"Ismeretlen MT-4 verzió: {m['tool_version']!r}.")
    if m["status"] != "completed":
        raise StaleExportError(f"Az export státusza {m['status']!r} (várt: completed).")
    for flag in ("training_ready", "content_verified", "split_approved"):
        if m[flag] is not False or m["statuses"].get(flag) is not False:
            raise StaleExportError(f"Az export {flag} állapota nem false: ilyen bemenetet ez a modul nem fogad el.")
    if bool(m["fixture"]) != (mode == "fixture") or m["data_kind"] != mode:
        raise RefusedError(
            f"A kért mód ({mode!r}) nem egyezik az export adatfajtájával (data_kind={m['data_kind']!r}, "
            f"fixture={m['fixture']!r}): a fixture (tesztadat) export kizárólag --mode fixture mellett fogadható el, "
            f"és fordítva.")
    if not m["exclusion_guard"].get("performed", False) and not allow_no_te1_comparison:
        raise StaleExportError(
            "Az export kizárás-ellenőrzése (a hat TE-1 kizárás) nem történt meg (TE-1 összevetés nélküli MT-4 "
            "export): futtasd újra az MT-4-et TE-1 exporttal, vagy kifejezetten --allow-no-te1-comparison.")
    # kimeneti fájlok ellenőrzőösszege (sérülés/elavulás felismerése)
    problems = []
    for name, o in m["outputs"].items():
        p = os.path.join(run_dir, name)
        if not os.path.isfile(p):
            problems.append(f"hiányzó fájl: {name}")
        elif sha256_file(p) != o["sha256"] or os.path.getsize(p) != o["bytes"]:
            problems.append(f"megváltozott fájl: {name}")
    if m["fixture"] and not os.path.isfile(os.path.join(run_dir, FIXTURE_MARKER_FILE)):
        problems.append(f"hiányzó tesztadat-jelölő fájl: {FIXTURE_MARKER_FILE}")
    if problems:
        raise InvalidExportError("Sérült vagy megváltozott MT-4 export: " + "; ".join(problems))
    # a manifest saját listáinak belső egysége (csoport-tagság helyett itt csak darabszám/azonosító-egyezés)
    for s in SPLITS:
        conv_ids = [c["id"] for c in m["conversations"] if c["split"] == s]
        if len(conv_ids) != m["splits"][s]["conversations"]:
            raise InvalidExportError(f"Az export {s} részének beszélgetés-száma nem egyezik a `conversations` listával.")
        if len(set(conv_ids)) != len(conv_ids):
            raise InvalidExportError(f"Az export {s} részében ismétlődő beszélgetés-azonosító van.")
    return m, run_dir, sha256_bytes(raw)


def load_samples(manifest, run_dir, split, mode):
    """Egy rész/mód minta-fájljának beolvasása, darabszám- és azonosító-ellenőrzéssel a manifest ellen.
    Visszaad: a minta-rekordok listáját (a JSONL sorrendjében)."""
    if mode not in manifest["splits"][split]["samples"]:
        raise InvalidExportError(f"Az export nem tartalmazza a(z) {split}/{mode} mintafájlt.")
    info = manifest["splits"][split]["samples"][mode]
    path = os.path.join(run_dir, info["file"])
    if not os.path.isfile(path):
        raise InputFileError(f"Hiányzó mintafájl: {path}")
    rows = _read_jsonl(path)
    if len(rows) != info["total"]:
        raise InvalidExportError(f"A(z) {info['file']} sorainak száma ({len(rows)}) nem egyezik a manifesttel ({info['total']}).")
    known_ids = {c["id"] for c in manifest["conversations"] if c["split"] == split}
    seen = set()
    for n, r in enumerate(rows, 1):
        if r.get("split") != split or r.get("mode") != mode:
            raise InvalidExportError(f"{info['file']}:{n} a split/mode mező nem egyezik a fájllal.")
        if r.get("data_kind") != manifest["data_kind"] or r.get("fixture") is not manifest["fixture"]:
            raise InvalidExportError(f"{info['file']}:{n} a data_kind/fixture jelölés nem egyezik az exporttal.")
        cid = r.get("conversation_id")
        if cid not in known_ids:
            raise InvalidExportError(f"{info['file']}:{n} ismeretlen vagy más részhez tartozó beszélgetés-azonosító: {cid!r}.")
        sid = r.get("sample_id")
        if sid in seen or sid != f"{cid}#{mode}#{r.get('target_turn')}":
            raise InvalidExportError(f"{info['file']}:{n} hibás vagy ismétlődő sample_id: {sid!r}.")
        seen.add(sid)
        tgt = r.get("target") or {}
        if not (isinstance(tgt.get("start"), int) and isinstance(tgt.get("end"), int) and 0 <= tgt["start"] < tgt["end"] <= len(r.get("text", ""))):
            raise InvalidExportError(f"{info['file']}:{n} érvénytelen target karaktertartomány: {tgt!r}.")
    per_conv = {}
    for r in rows:
        per_conv.setdefault(r["conversation_id"], 0)
        per_conv[r["conversation_id"]] += 1
    for c in manifest["conversations"]:
        if c["split"] == split:
            want = c["exchanges"]
            if per_conv.get(c["id"], 0) != want:
                raise InvalidExportError(f"A(z) {c['id']} beszélgetés {split}/{mode} mintáinak száma ({per_conv.get(c['id'], 0)}) nem egyezik a fordulószámmal ({want}).")
    return rows


# ---------------------------------------------------------------------------
# 2) szótár, kódolás (a karakter-pozíciók megőrzésével), célmaszk
# ---------------------------------------------------------------------------

def build_vocab(train_primary_samples):
    """A szótár KIZÁRÓLAG a train rész elsődleges (R2) mintáinak renderelt szövegéből épül (a teljes,
    címkékkel együtt renderelt szöveg karakterei - ugyanúgy, mint a meglévő train_chat.build_vocab() a
    saját, egyfordulós formátumán). Két FENNTARTOTT azonosító kerül a szótár MÖGÉ (nem a megfigyelt
    karakterek közé, tehát nem "bővíti" a train-szótárat): `<UNK>` az ismeretlen (validation/test-only)
    karakterekhez, `<PAD>` a kötegelési kitöltéshez."""
    chars = sorted({ch for s in train_primary_samples for ch in s["text"]})
    stoi = {ch: i for i, ch in enumerate(chars)}
    itos = {i: ch for i, ch in enumerate(chars)}
    unk_id, pad_id = len(chars), len(chars) + 1
    return {"stoi": stoi, "itos": itos, "unk_id": unk_id, "pad_id": pad_id,
            "base_vocab_size": len(chars), "vocab_size": len(chars) + 2}


def encode_text(text, vocab):
    """Szöveg -> id-lista, POZÍCIÓTARTÓAN (egy karakter, egy id - a meglévő CharTokenizer.encode ezzel
    szemben KIHAGYJA az ismeretlen karaktereket, ami eltolná a célmaszk pozícióit; ezért ez a modul saját
    kódolást használ, nem a tokenizer.py-t). Az ismeretlen karakterek `unk_id`-t kapnak. Visszaad:
    (id-lista, az ismeretlen karakterek pozíciói)."""
    stoi, unk_id = vocab["stoi"], vocab["unk_id"]
    ids, unknown = [], []
    for i, ch in enumerate(text):
        if ch in stoi:
            ids.append(stoi[ch])
        else:
            ids.append(unk_id)
            unknown.append(i)
    return ids, unknown


def build_target_mask(text_len, target_start, target_end):
    """Veszteség-maszk a (bemenet=ids[:-1], cél=ids[1:]) eltolt párra: mask[i] pontosan akkor 1,0, ha az
    i. cél-pozíció (amely az eredeti szöveg (i+1). karakterét jósolja) a [target_start, target_end)
    tartományba esik - vagyis a célválasz része. Az előzmény, az aktuális kérdés és a (kötegeléskor
    hozzáadott) kitöltés sosem esik ebbe a tartományba, ezért sosem kap 1,0-t."""
    n = max(0, text_len - 1)
    lo = max(0, target_start - 1)
    hi = min(n, max(lo, target_end - 1))
    mask = [0.0] * n
    for i in range(lo, hi):
        mask[i] = 1.0
    return mask


def verify_mask_alignment(text, mask, target_start, target_end):
    """FÜGGETLEN önellenőrzés (nem a build_target_mask belső logikáját ismétli meg): a maszk 1,0
    pozícióiból visszaszámolt karakter-tartomány pontosan [target_start, target_end) kell legyen. (A
    kimaszkolt predikciók által jósolt karaktereket ezután NEM kell külön összevetni a target-szöveggel:
    mindkettő ugyanannak a `text`-nek ugyanazon indexeiből épül, a pozíció-egyezésből a karakter-egyezés
    matematikailag következik - egy külön második ellenőrzés soha nem buktathatna el semmit, amit az első
    már nem buktatott el.) Visszaad: (ok: bool, ok esetén None, egyébként hibaüzenet)."""
    on = [i for i, v in enumerate(mask) if v]
    if not on:
        if target_start >= target_end:
            return True, None
        return False, "üres maszk, de a target nem üres"
    predicted_positions = [i + 1 for i in on]
    if predicted_positions != list(range(target_start, target_end)):
        return False, f"a maszk pozíciói ({predicted_positions[0]}..{predicted_positions[-1]}) nem [target_start,target_end)=[{target_start},{target_end})"
    return True, None


# ---------------------------------------------------------------------------
# 3) minta-előkészítés (hosszkorlát, kódolás, maszk) és kötegelés
# ---------------------------------------------------------------------------

def prepare_sample(sample, vocab, max_chars):
    """Egy minta kódolása és maszkolása, önellenőrzéssel. Visszaad: (prepared | None, reason | None).
    `reason` akkor nem None, ha a minta KIHAGYVA (túl hosszú, vagy - védekezésképp - túl rövid egy
    bemenet/cél párhoz); ilyenkor a minta NEM kerül csendben csonkításra, hanem visszatartva jelentve van."""
    text = sample["text"]
    length = len(text)
    if length > max_chars:
        return None, f"túl hosszú: {length} > --max-chars {max_chars}"
    if length < 2:
        return None, f"túl rövid ({length} karakter) egy bemenet/cél párhoz"
    tgt = sample["target"]
    ok, why = verify_mask_alignment(text, build_target_mask(length, tgt["start"], tgt["end"]), tgt["start"], tgt["end"])
    if not ok:
        raise VerificationError(f"{sample['sample_id']}: a célmaszk önellenőrzése hibát talált: {why}")
    ids, unknown = encode_text(text, vocab)
    mask = build_target_mask(length, tgt["start"], tgt["end"])
    input_ids, target_ids = ids[:-1], ids[1:]
    if not (len(input_ids) == len(target_ids) == len(mask)):
        raise VerificationError(f"{sample['sample_id']}: a bemenet/cél/maszk hossza nem egyezik.")
    if abs(sum(mask) - (tgt["end"] - tgt["start"])) > 1e-9:
        raise VerificationError(f"{sample['sample_id']}: a maszk összege nem a célválasz hosszával egyezik.")
    return {
        "sample_id": sample["sample_id"], "conversation_id": sample["conversation_id"], "unit": sample.get("unit"),
        "split": sample["split"], "mode": sample["mode"], "input_ids": input_ids, "target_ids": target_ids,
        "mask": mask, "length": len(input_ids), "char_length": length, "unknown_count": len(unknown),
        "unknown_chars": sorted({text[i] for i in unknown}),
    }, None


def make_batches(prepared, batch_size, pad_id):
    """A (kihagyás után megmaradt) minták kötegelése a FÁJLBAN szereplő sorrendben (determinisztikus,
    nem véletlenszerű). Egy köteg sora PONTOSAN egy minta - sosem két minta összefűzve; a rövidebb sorok
    jobbról `pad_id`-vel (bemenet/cél) és 0,0-val (maszk) vannak kitöltve a köteg leghosszabb mintájáig, a
    kitöltés sosem kap 1,0-s maszkot (a target span mindig az eredeti, ki nem töltött hosszon belül van)."""
    batches = []
    for i in range(0, len(prepared), batch_size):
        chunk = prepared[i:i + batch_size]
        max_len = max(p["length"] for p in chunk)
        input_ids = [p["input_ids"] + [pad_id] * (max_len - p["length"]) for p in chunk]
        target_ids = [p["target_ids"] + [pad_id] * (max_len - p["length"]) for p in chunk]
        mask = [p["mask"] + [0.0] * (max_len - p["length"]) for p in chunk]
        batches.append({
            "sample_ids": [p["sample_id"] for p in chunk], "conversation_ids": [p["conversation_id"] for p in chunk],
            "lengths": [p["length"] for p in chunk], "max_len": max_len,
            "input_ids": torch.tensor(input_ids, dtype=torch.long), "target_ids": torch.tensor(target_ids, dtype=torch.long),
            "mask": torch.tensor(mask, dtype=torch.float32),
        })
    return batches


# ---------------------------------------------------------------------------
# 4) előrefutási (kompatibilitási) próba - FRISS, tanítatlan modellel, gradiens nélkül
# ---------------------------------------------------------------------------

def build_probe_model(vocab_size):
    """Egy FRISS (véletlen inicializált, TANÍTATLAN) próba-modell, a jelenlegi (config.py-beli)
    architektúra-méretekkel. Ez NEM a betanított v0.7 checkpoint, és ezt a modul sosem menti el."""
    return CharLSTM(vocab_size=vocab_size, embedding_dim=config.embedding_dim, hidden_size=config.hidden_size,
                    num_layers=config.num_layers, dropout=config.dropout)


@torch.no_grad()
def forward_check(model, batch, vocab_size):
    """Egy köteg előrefutása és a maszkolt veszteség kiszámítása - KIZÁRÓLAG alak-/futás-ellenőrzésre
    (nincs .backward(), nincs optimizer, nincs mentés). Minden hívás a saját, nulla kezdő rejtett
    állapotával indul (hidden=None); a modul sosem ad tovább rejtett állapotot egyik hívásból a
    következőbe, sem kötegen belül (a batch-dimenzió az LSTM-ben eleve független sorokat jelent), sem
    kötegek között."""
    model.eval()
    try:
        logits, _ = model(batch["input_ids"], hidden=None)
    except RuntimeError as exc:
        return {"success": False, "error": str(exc)}
    per_token = F.cross_entropy(logits.reshape(-1, vocab_size), batch["target_ids"].reshape(-1), reduction="none")
    mask_flat = batch["mask"].reshape(-1)
    denom = mask_flat.sum()
    loss = (per_token * mask_flat).sum() / denom if denom.item() > 0 else torch.tensor(0.0)
    return {"success": True, "logits_shape": list(logits.shape), "masked_loss": float(loss.item()),
            "target_tokens": int(denom.item())}


# ---------------------------------------------------------------------------
# 5) hossz-/erőforrás-statisztika
# ---------------------------------------------------------------------------

def percentile(sorted_values, p):
    """Determinisztikus percentilis (0<=p<=100) egy már rendezett listán: a legközelebbi (lefelé kerekített)
    rangú elem - a `round()` "bankár-kerekítése" (49,5 -> 50, nem 49) itt szándékosan kerülve van, hogy a
    p=50 mindig a klasszikus alsó-medián indexet adja páros elemszámnál is."""
    if not sorted_values:
        return None
    if len(sorted_values) == 1:
        return sorted_values[0]
    idx = min(len(sorted_values) - 1, max(0, int(p / 100.0 * (len(sorted_values) - 1))))
    return sorted_values[idx]


def length_stats(lengths):
    if not lengths:
        return {"count": 0}
    s = sorted(lengths)
    return {"count": len(s), "min": s[0], "max": s[-1], "mean": round(statistics.mean(s), 2),
            "median": statistics.median(s), "p90": percentile(s, 90), "p99": percentile(s, 99)}


def estimate_batch_bytes(prepared):
    """A kódolt (bemenet+cél: int64, maszk: float32) tenzorok BECSÜLT mérete (nem profilozott csúcsmemória)."""
    return sum(p["length"] * (8 + 8 + 4) for p in prepared)


# ---------------------------------------------------------------------------
# 6) a teljes száraz futás
# ---------------------------------------------------------------------------

def _dump(path, obj):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")


def _write_tsv(path, header, rows):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\t".join(header) + "\n")
        for r in rows:
            f.write("\t".join("" if v is None else str(v) for v in r) + "\n")


def file_sha_map(paths):
    return {p: sha256_file(p) for p in paths}


def over_trained_context_count(kept):
    """Azon megtartott minták száma, amelyek bemenet-hossza SZIGORÚAN meghaladja a jelenlegi modell
    tanított kontextusát (config.seq_length); a küszöbön PONTOSAN álló minta még a tanított kontextuson
    belül van, nem számít "túl hosszúnak" (külön függvény, hogy ez a határeset önmagában tesztelhető
    legyen, a teljes száraz futás lefuttatása nélkül)."""
    return sum(1 for p in kept if p["length"] > config.seq_length)


def run_dry_run(manifest_path, mode, out_dir, modes=DEFAULT_MODES, max_chars=DEFAULT_MAX_CHARS,
                batch_size=DEFAULT_BATCH_SIZE, allow_no_te1_comparison=False, run_name=None):
    modes = tuple(modes)
    if not modes or len(set(modes)) != len(modes):
        raise RefusedError("A --modes nem lehet üres vagy ismétlődő.")
    for md in modes:
        if md not in SUPPORTED_MODES:
            raise RefusedError(f"Ismeretlen vagy nem támogatott renderelési mód: {md!r} (R3 nincs; támogatott: {', '.join(SUPPORTED_MODES)}).")
    if PRIMARY_MODE not in modes:
        raise RefusedError(f"Az elsődleges mód ({PRIMARY_MODE}) nélkül nem építhető szótár; add hozzá a --modes listához.")

    manifest, run_dir, manifest_sha = load_export(manifest_path, mode, allow_no_te1_comparison)
    fixture = manifest["fixture"]
    stamp = run_name or (("fixture_mt5_" if fixture else "mt5_") + datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    if not re.match(r"^[A-Za-z0-9._-]+$", stamp):
        raise OutputError(f"Érvénytelen futásnév: {stamp!r}")
    if fixture and not stamp.startswith("fixture_"):
        raise RefusedError("Tesztadat (fixture) száraz futásának mappája `fixture_` előtagú kell legyen.")
    if not fixture and stamp.lower().startswith("fixture"):
        raise RefusedError("Valódi adat száraz futásának mappája nem kezdődhet `fixture` előtaggal.")
    out_abs = check_out_dir(out_dir, run_dir)
    this_run_dir = os.path.join(out_abs, stamp)
    if os.path.exists(this_run_dir):
        raise OutputError(f"A futás-mappa már létezik, nem írom felül: {this_run_dir}")

    dep_paths = [manifest_path] + [os.path.join(run_dir, n) for n in manifest["outputs"]]
    before = file_sha_map(dep_paths)

    t0 = time.perf_counter()
    samples = {s: {} for s in SPLITS}
    for s in SPLITS:
        for md in modes:
            samples[s][md] = load_samples(manifest, run_dir, s, md)
    load_seconds = round(time.perf_counter() - t0, 3)

    vocab = build_vocab(samples["train"][PRIMARY_MODE])

    per_split_mode, batches_by_split_mode, forward_results = {}, {}, {}
    timing = {"load_seconds": load_seconds, "encode_seconds": {}, "batch_seconds": {}, "forward_seconds": {}}
    for s in SPLITS:
        for md in modes:
            t = time.perf_counter()
            kept, withheld = [], []
            for r in samples[s][md]:
                prep, reason = prepare_sample(r, vocab, max_chars)
                if prep is None:
                    withheld.append({"sample_id": r["sample_id"], "conversation_id": r["conversation_id"],
                                     "char_length": len(r["text"]), "reason": reason})
                else:
                    kept.append(prep)
            timing["encode_seconds"][f"{s}/{md}"] = round(time.perf_counter() - t, 3)
            t = time.perf_counter()
            batches = make_batches(kept, batch_size, vocab["pad_id"])
            timing["batch_seconds"][f"{s}/{md}"] = round(time.perf_counter() - t, 3)
            batches_by_split_mode[(s, md)] = batches
            unk_total = sum(p["unknown_count"] for p in kept)
            unk_chars = sorted({ch for p in kept for ch in p["unknown_chars"]})
            per_split_mode[(s, md)] = {
                "kept": kept, "withheld": withheld,
                "length_stats_kept": length_stats([p["char_length"] for p in kept]),
                "length_stats_withheld": length_stats([w["char_length"] for w in withheld]),
                "unknown_chars_total": unk_total, "unknown_chars_distinct": unk_chars,
                "over_trained_context": over_trained_context_count(kept),
                "estimated_encoded_bytes": estimate_batch_bytes(kept),
            }

    torch.manual_seed(config.seed)   # determinisztikus próba-modell: ismételt futásnál a jelentés (a maszkolt veszteséggel együtt) reprodukálható
    probe_model = build_probe_model(vocab["vocab_size"])
    for (s, md), batches in batches_by_split_mode.items():
        t = time.perf_counter()
        results = [forward_check(probe_model, b, vocab["vocab_size"]) for b in batches]
        timing["forward_seconds"][f"{s}/{md}"] = round(time.perf_counter() - t, 3)
        forward_results[(s, md)] = results

    if file_sha_map(dep_paths) != before:
        raise InvalidExportError("A bemeneti export a futás közben megváltozott (ellenőrzőösszeg-eltérés).")

    os.makedirs(this_run_dir)
    lengths_rows = []
    for (s, md), info in per_split_mode.items():
        for p in info["kept"]:
            lengths_rows.append((s, md, p["sample_id"], p["conversation_id"], p["char_length"], 1, "", p["unknown_count"]))
        for w in info["withheld"]:
            lengths_rows.append((s, md, w["sample_id"], w["conversation_id"], w["char_length"], 0, w["reason"], ""))
    _write_tsv(os.path.join(this_run_dir, LENGTHS_FILE),
              ["split", "mode", "sample_id", "conversation_id", "char_length", "kept", "reason", "unknown_count"], lengths_rows)

    splits_report = {}
    for s in SPLITS:
        splits_report[s] = {}
        for md in modes:
            info = per_split_mode[(s, md)]
            fr = forward_results[(s, md)]
            splits_report[s][md] = {
                "kept": len(info["kept"]), "withheld_oversized": len(info["withheld"]),
                "withheld_reasons": info["withheld"],
                "length_stats_kept_chars": info["length_stats_kept"], "length_stats_withheld_chars": info["length_stats_withheld"],
                "unknown_chars_total_occurrences": info["unknown_chars_total"], "unknown_chars_distinct": info["unknown_chars_distinct"],
                "batches": len(batches_by_split_mode[(s, md)]), "batch_size": batch_size,
                "forward_pass_successes": sum(1 for r in fr if r["success"]), "forward_pass_failures": [r for r in fr if not r["success"]],
                "samples_over_trained_context_chars": info["over_trained_context"],
                "samples_over_trained_context_pct": round(100.0 * info["over_trained_context"] / len(info["kept"]), 1) if info["kept"] else 0.0,
                "estimated_encoded_bytes": info["estimated_encoded_bytes"],
            }
    all_withheld = sum(len(per_split_mode[(s, md)]["withheld"]) for s in SPLITS for md in modes)
    all_unknown = sum(per_split_mode[(s, md)]["unknown_chars_total"] for s in SPLITS for md in modes)
    all_forward_failures = sum(len(forward_results[(s, md)]) - sum(1 for r in forward_results[(s, md)] if r["success"]) for s in SPLITS for md in modes)
    warnings = []
    if all_withheld:
        warnings.append(f"{all_withheld} minta a --max-chars ({max_chars}) fölötti, visszatartva (lásd sample_lengths.tsv).")
    if all_unknown:
        warnings.append(f"{all_unknown} ismeretlen (train-szótáron kívüli) karakter-előfordulás a validation/test (vagy R1) mintákban.")
    if all_forward_failures:
        warnings.append(f"{all_forward_failures} köteg előrefutása sikertelen (kompatibilitási hiba, lásd forward_pass_failures).")
    if not allow_no_te1_comparison and manifest["exclusion_guard"].get("performed") is not True:
        warnings.append("az export kizárás-ellenőrzése nem történt meg")

    report = {
        "tool": "src/train_multiturn.py", "tool_version": TOOL_VERSION, "status": "completed",
        "created_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "python": sys.version.split()[0],
        "torch_version": torch.__version__,
        "purpose": ("technikai próba mesterséges tesztadaton - NEM tanítóadat" if fixture else "csak betöltés és száraz futás - NEM tanítás"),
        "data_kind": manifest["data_kind"], "fixture": fixture,
        "config": {
            "mode": mode, "modes": list(modes), "primary_mode": PRIMARY_MODE, "secondary_mode": SECONDARY_MODE if SECONDARY_MODE in modes else None,
            "unsupported_modes": {"R3": "nem létezik export-oldalon (MT-4 nem készíti); ez a modul sem állítja elő"},
            "max_chars": max_chars, "batch_size": batch_size,
            "windowing": "nincs véletlen ablakolás; egy minta = egy köteg-sor, a mintahatáron belül, összefűzés nélkül",
            "hidden_state": "minden előrefutás nulla kezdő rejtett állapottal indul; kötegek között nincs átvitt állapot",
            "vocab_source": f"kizárólag a train/{PRIMARY_MODE} minták renderelt szövege; UNK és PAD két fenntartott, a megfigyelt karakterektől külön id",
            "probe_model": {"embedding_dim": config.embedding_dim, "hidden_size": config.hidden_size, "num_layers": config.num_layers,
                            "dropout": config.dropout, "trained": False, "saved": False},
            "trained_model_effective_context_chars": config.seq_length,
        },
        "inputs": {"export_manifest": {"path": rel_path(manifest_path), "sha256": manifest_sha, "run_dir": rel_path(run_dir),
                                       "tool_version": manifest["tool_version"]},
                   "te1_exclusion_check_performed": manifest["exclusion_guard"].get("performed", False)},
        "vocab": {"base_vocab_size": vocab["base_vocab_size"], "vocab_size": vocab["vocab_size"], "unk_id": vocab["unk_id"], "pad_id": vocab["pad_id"]},
        "splits": splits_report,
        "timing_seconds": timing,
        "counts": {"withheld_oversized_total": all_withheld, "unknown_char_occurrences_total": all_unknown, "forward_pass_failures_total": all_forward_failures},
        "outputs": {},
        "warnings": warnings, "limitations": LIMITATIONS, "disclaimer": DISCLAIMER,
        "training_ready": False, "content_verified": False, "split_approved": False,
        "statuses_from_export": {k: manifest["statuses"][k] for k in ("split_approved", "content_verified", "training_ready")},
    }
    partial = os.path.join(this_run_dir, REPORT_FILE + ".partial")
    _dump(partial, report)
    outputs = {}
    for name in (LENGTHS_FILE,):
        p = os.path.join(this_run_dir, name)
        outputs[name] = {"sha256": sha256_file(p), "bytes": os.path.getsize(p)}
    report["outputs"] = outputs
    _dump(partial, report)
    problems = verify_dry_run_report(partial, this_run_dir)
    if problems:
        with open(os.path.join(this_run_dir, "FAILED.txt"), "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(problems) + "\n")
        raise VerificationError("A belső önellenőrzés hibát talált: " + "; ".join(problems[:10]))
    os.replace(partial, os.path.join(this_run_dir, REPORT_FILE))
    report["run_dir"] = this_run_dir
    return report


def verify_dry_run_report(report_path, run_dir=None):
    """A kiírt jelentés és a mellékelt TSV önellenőrzése a lemezről (nem a memóriabeli állapotból).
    Visszaad: problémák listája (üres: rendben)."""
    problems = []
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            rep = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        return [f"a jelentés nem olvasható: {exc}"]
    run_dir = run_dir or os.path.dirname(os.path.abspath(report_path))
    for flag in ("training_ready", "content_verified", "split_approved"):
        if rep.get(flag) is not False:
            problems.append(f"a jelentés {flag} értéke nem false")
    for name, o in rep.get("outputs", {}).items():
        p = os.path.join(run_dir, name)
        if not os.path.isfile(p):
            problems.append(f"hiányzó kimeneti fájl: {name}")
        elif sha256_file(p) != o["sha256"] or os.path.getsize(p) != o["bytes"]:
            problems.append(f"megváltozott kimeneti fájl: {name}")
    lengths_path = os.path.join(run_dir, LENGTHS_FILE)
    if os.path.isfile(lengths_path):
        with open(lengths_path, encoding="utf-8") as f:
            lines = [l for l in f.read().split("\n") if l.strip()]
        rows = lines[1:]
        kept_by = {}
        withheld_by = {}
        for line in rows:
            parts = line.split("\t")
            split, md, kept = parts[0], parts[1], parts[5]
            key = (split, md)
            if kept == "1":
                kept_by[key] = kept_by.get(key, 0) + 1
            else:
                withheld_by[key] = withheld_by.get(key, 0) + 1
        for s, by_mode in rep.get("splits", {}).items():
            for md, info in by_mode.items():
                key = (s, md)
                if kept_by.get(key, 0) != info["kept"]:
                    problems.append(f"a {s}/{md} kept-száma nem egyezik a sample_lengths.tsv-vel")
                if withheld_by.get(key, 0) != info["withheld_oversized"]:
                    problems.append(f"a {s}/{md} withheld-száma nem egyezik a sample_lengths.tsv-vel")
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
    p = argparse.ArgumentParser(description="MT-5: többfordulós tanító betöltő - KIZÁRÓLAG betöltés és száraz futás (tanítás nincs).")
    p.add_argument("--export-manifest", help="Az MT-4 export_manifest.json.")
    p.add_argument("--mode", choices=["dataset", "fixture"], help="Az adat fajtája; egyeznie kell az export data_kind/fixture jelölésével.")
    p.add_argument("--out-dir", help="Kimeneti szülőmappa (a futás új almappába kerül).")
    p.add_argument("--dry-run", action="store_true", help="Kötelező: jelenleg csak száraz futás létezik (nincs tanítási kódág).")
    p.add_argument("--modes", type=_parse_modes, default=DEFAULT_MODES, help="Renderelési módok, vesszővel (alap: R2,R1; R3 nincs).")
    p.add_argument("--max-chars", type=int, default=DEFAULT_MAX_CHARS, help=f"Explicit hosszkorlát karakterben (alap: {DEFAULT_MAX_CHARS}).")
    p.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    p.add_argument("--allow-no-te1-comparison", action="store_true")
    p.add_argument("--run-name", default=None)
    p.add_argument("--verify-report", default=None, help="Egy korábbi dryrun_report.json ellenőrzése a lemezről.")
    a = p.parse_args(argv)

    if a.verify_report:
        problems = verify_dry_run_report(a.verify_report)
        if problems:
            for pr in problems:
                print(f"HIBA: {pr}", file=sys.stderr)
            return EXIT_VERIFY
        print("A jelentés a lemezről visszaolvasva rendben van.")
        return 0
    if not (a.export_manifest and a.mode and a.out_dir):
        p.error("--export-manifest, --mode és --out-dir kötelező (vagy --verify-report)")
    if not a.dry_run:
        print("HIBA: jelenleg kizárólag a --dry-run mód létezik (nincs tanítási kódág); add meg a --dry-run kapcsolót.", file=sys.stderr)
        return EXIT_REFUSED
    try:
        rep = run_dry_run(a.export_manifest, a.mode, a.out_dir, a.modes, a.max_chars, a.batch_size,
                          a.allow_no_te1_comparison, a.run_name)
    except TrainMultiturnError as exc:
        print(f"HIBA ({type(exc).__name__}): {exc}", file=sys.stderr)
        return exc.exit_code
    print(f"MT-5 száraz futás kész: {rep['run_dir']}")
    print(f"Adat: {rep['data_kind']} | szótár: {rep['vocab']['base_vocab_size']} karakter (+UNK+PAD) | módok: {', '.join(rep['config']['modes'])}")
    for s in SPLITS:
        for md in rep["config"]["modes"]:
            info = rep["splits"][s][md]
            print(f"  {s}/{md}: kept {info['kept']} | visszatartott {info['withheld_oversized']} | kötegek {info['batches']} "
                  f"| előrefutás OK {info['forward_pass_successes']}/{info['batches']} | > {config.seq_length} kar. {info['samples_over_trained_context_pct']}%")
    for w in rep["warnings"]:
        print("  FIGYELEM:", w)
    print(DISCLAIMER)
    return EXIT_ATTENTION if rep["warnings"] else 0


if __name__ == "__main__":
    sys.exit(_main())
