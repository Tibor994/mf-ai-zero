"""
MF-AI-Zero - dataset pipeline hardening: TELJES korpuszos kereszt-batch
duplikátum-kereső.

CÉL: a tools/dataset_dedupe.py find_duplicates()-jét a data/clean/ ALATTI
ÖSSZES .jsonl fájl együttesén futtatja, egyetlen hívással - nem csak "az új
batch a korábbiak ellen" (ahogy az egyes DeepSeek importok korábbi, egyedi
szkriptjei tették), hanem MINDEN fájl MINDEN fájl ellen, egységesen.

Ezt egy 2026-09-i audit (data/reports/dataset_audit_0151_0500.md, 2.2 pont)
javasolta: kimutatta, hogy az első 3 DeepSeek batch (0151-0300) SOHA nem lett
egymás ellen ellenőrizve, mert a kereszt-batch dedupe csak a 4. importtól
kezdve lett bevezetve, ad hoc módon, egyedi importszkriptekben - így egy
valódi duplikátum (simple_qa_0185 / simple_qa_0283) észrevétlen maradt. Ez a
modul ezt formalizálja: egyetlen, ÁLLANDÓ, mindig a TELJES korpuszt átfogó,
könnyen újra-futtatható eszköz.

Ez a modul - a dataset_dedupe.py elvéhez híven - SOHA nem törli/módosítja a
forrásfájlokat, csak REPORTOL. A döntés, hogy egy talált duplikátumot hogyan
kezeljünk (melyiket tartjuk meg, hova kerüljön a másik), a hívóé.

Használat parancssorból:
    python tools/dataset_cross_dedupe.py data/clean

Használat modulként:
    from dataset_cross_dedupe import cross_dedupe_directory
"""

import argparse
import glob
import json
import os
import sys

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS_DIR)
from dataset_dedupe import DEFAULT_SIMILARITY_THRESHOLD, find_duplicates  # noqa: E402


def _load_all_clean_files(clean_dir):
    """Beolvassa a clean_dir ALATTI összes *.jsonl fájlt, ábécésorrendben
    (ez egyben import-sorrend is, mivel a fájlnevek id-tartományt kódolnak),
    és egy GLOBÁLIS, folytonos row_number-ekkel ellátott entries listát ad
    vissza, plusz egy row_number -> {file, line, id} meta dict-et."""
    files = sorted(glob.glob(os.path.join(clean_dir, "*.jsonl")))
    entries = []
    meta = {}
    global_row_number = 0
    for path in files:
        with open(path, "r", encoding="utf-8") as f:
            for local_line_number, raw_line in enumerate(f, start=1):
                stripped = raw_line.strip()
                if not stripped:
                    continue
                row = json.loads(stripped)
                global_row_number += 1
                entries.append({"row_number": global_row_number, "row": row})
                meta[global_row_number] = {
                    "file": os.path.basename(path),
                    "line": local_line_number,
                    "id": row.get("id"),
                }
    return entries, meta, files


def cross_dedupe_directory(clean_dir, similarity_threshold=DEFAULT_SIMILARITY_THRESHOLD):
    """Lefuttatja a find_duplicates()-t a clean_dir ALATTI TELJES korpuszon.

    Visszaad egy dict-et: {"total_rows", "files", "duplicates": [...]} - a
    "duplicates" lista minden eleme: {"category", "kept_id", "kept_file",
    "duplicate_id", "duplicate_file", "similarity"}."""
    entries, meta, files = _load_all_clean_files(clean_dir)
    report = find_duplicates(entries, similarity_threshold)

    duplicates = []
    for category, items in report.items():
        for d in items:
            kept_meta = meta[d["kept"]]
            dup_meta = meta[d["duplicate"]]
            duplicates.append({
                "category": category,
                "kept_id": kept_meta["id"],
                "kept_file": kept_meta["file"],
                "duplicate_id": dup_meta["id"],
                "duplicate_file": dup_meta["file"],
                "similarity": d.get("similarity"),
            })

    return {
        "total_rows": len(entries),
        "files": [os.path.basename(p) for p in files],
        "duplicates": duplicates,
    }


def _main():
    parser = argparse.ArgumentParser(
        description="MF-AI-Zero TELJES korpuszos kereszt-batch duplikátum-kereső.")
    parser.add_argument("clean_dir", help="A data/clean/ (vagy azzal egyenértékű) könyvtár elérési útja.")
    parser.add_argument("--threshold", type=float, default=DEFAULT_SIMILARITY_THRESHOLD,
                         help=f"Hasonlósági küszöb (0-1, alapértelmezés: {DEFAULT_SIMILARITY_THRESHOLD}).")
    args = parser.parse_args()

    result = cross_dedupe_directory(args.clean_dir, args.threshold)
    print(f"Vizsgált fájlok: {len(result['files'])}")
    for f in result["files"]:
        print(f"  - {f}")
    print(f"Összes sor a teljes korpuszban: {result['total_rows']}")
    print(f"Talált duplikátumok: {len(result['duplicates'])}")
    for d in result["duplicates"]:
        sim_text = f" (hasonlóság={d['similarity']})" if d["similarity"] is not None else ""
        print(f"  [{d['category']}] megtartva: {d['kept_id']} ({d['kept_file']}) <- duplikátum: "
              f"{d['duplicate_id']} ({d['duplicate_file']}){sim_text}")


if __name__ == "__main__":
    _main()
