"""
MF-AI-Zero - v1.7.4 dataset foundation: duplikátum-kereső.

CÉL: egy MÁR validált JSONL fájlon belül megtalálni a duplikátumokat -
HÁROM szempont szerint:
  1. id alapján (pontos egyezés)
  2. instruction hasonlóság alapján (közel azonos kérdés/feladat)
  3. output hasonlóság alapján (közel azonos válasz)

Ez a modul SOHA nem törli/módosítja a forrásfájlt - csak REPORTOL, és
opcionálisan (dedupe_rows()) egy DEDUPLIKÁLT LISTÁT ad vissza a hívónak
(pl. dataset_import.py-nak), a döntés, hogy ezt hova írjuk, a hívóé.

A hasonlóság-vizsgálat a Python beépített difflib.SequenceMatcher-ét
használja (ugyanaz az elv, mint src/file_editor.py diff-előnézeténél) -
NINCS külső függőség, NINCS ML-alapú embedding.

Használat parancssorból:
    python tools/dataset_dedupe.py data/clean/batch1.jsonl

Használat modulként:
    from dataset_dedupe import find_duplicates, dedupe_rows
"""

import argparse
import difflib
import json

DEFAULT_SIMILARITY_THRESHOLD = 0.9


def _similarity(a, b):
    if not a or not b:
        return 0.0
    return difflib.SequenceMatcher(None, a, b).ratio()


def _load_rows(path):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line_number, raw_line in enumerate(f, start=1):
            stripped = raw_line.strip()
            if not stripped:
                continue
            try:
                row = json.loads(stripped)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                rows.append({"row_number": line_number, "row": row})
    return rows


def find_duplicates(entries, similarity_threshold=DEFAULT_SIMILARITY_THRESHOLD):
    """entries: [{"row_number", "row"}, ...] (pl. _load_rows() vagy
    dataset_validate.validate_file()["valid_rows"] kimenete).

    Visszaad egy dict-et:
      {"id_duplicates": [...], "instruction_duplicates": [...],
       "output_duplicates": [...]}
    Mindegyik lista elemei: {"kept": row_number, "duplicate": row_number,
    "id"/"similarity": ...} - a "kept" mindig a fájlban KORÁBBAN
    szereplő sor, a "duplicate" a későbbi (ez csak egy JAVASLAT arra,
    melyiket érdemes megtartani - a hívó dönt)."""
    id_seen = {}
    id_duplicates = []
    instruction_duplicates = []
    output_duplicates = []

    seen_instructions = []
    seen_outputs = []

    for entry in entries:
        row_number = entry["row_number"]
        row = entry["row"]
        row_id = row.get("id")
        instruction = (row.get("instruction") or "").strip()
        task_input = (row.get("input") or "").strip()
        # FONTOS: a "feladat" hasonlóságát az instruction+input PÁR adja,
        # NEM az instruction önmagában - sok kategóriánál (pl.
        # typo_correction, summary) szándékosan UGYANAZ az instruction-
        # SABLON ismétlődik ("Javítsd ki az elgépelést..."), és csak az
        # input hordozza a ténylegesen eltérő feladatot. Ha csak az
        # instruction-t hasonlítanánk, minden ilyen (legitim, KÜLÖNBÖZŐ)
        # sort tévesen duplikátumnak jelezné.
        task_text = f"{instruction} || {task_input}"
        output = (row.get("output") or "").strip()

        if row_id is not None:
            if row_id in id_seen:
                id_duplicates.append({"kept": id_seen[row_id], "duplicate": row_number, "id": row_id})
            else:
                id_seen[row_id] = row_number

        for prev_number, prev_text in seen_instructions:
            sim = _similarity(task_text, prev_text)
            if sim >= similarity_threshold:
                instruction_duplicates.append({"kept": prev_number, "duplicate": row_number, "similarity": round(sim, 3)})
                break
        if task_text.strip(" |"):
            seen_instructions.append((row_number, task_text))

        for prev_number, prev_text in seen_outputs:
            sim = _similarity(output, prev_text)
            if sim >= similarity_threshold:
                output_duplicates.append({"kept": prev_number, "duplicate": row_number, "similarity": round(sim, 3)})
                break
        if output:
            seen_outputs.append((row_number, output))

    return {
        "id_duplicates": id_duplicates,
        "instruction_duplicates": instruction_duplicates,
        "output_duplicates": output_duplicates,
    }


def dedupe_rows(entries, similarity_threshold=DEFAULT_SIMILARITY_THRESHOLD):
    """Visszaadja az entries listát a duplikátumok (bármelyik szempont
    szerint jelzettek) NÉLKÜL, plusz magát a duplikátum-reportot -
    (kept_entries, report). Ez SOHA nem írja felül a forrásfájlt - a
    hívó dönti el, hogy a kept_entries-t hova menti."""
    report = find_duplicates(entries, similarity_threshold)
    duplicate_row_numbers = {d["duplicate"] for d in report["id_duplicates"]}
    duplicate_row_numbers |= {d["duplicate"] for d in report["instruction_duplicates"]}
    duplicate_row_numbers |= {d["duplicate"] for d in report["output_duplicates"]}
    kept_entries = [e for e in entries if e["row_number"] not in duplicate_row_numbers]
    return kept_entries, report


def _main():
    parser = argparse.ArgumentParser(description="MF-AI-Zero dataset duplikátum-kereső.")
    parser.add_argument("path", help="A vizsgálandó .jsonl fájl elérési útja.")
    parser.add_argument("--threshold", type=float, default=DEFAULT_SIMILARITY_THRESHOLD,
                         help=f"Hasonlósági küszöb (0-1, alapértelmezés: {DEFAULT_SIMILARITY_THRESHOLD}).")
    args = parser.parse_args()

    entries = _load_rows(args.path)
    report = find_duplicates(entries, args.threshold)

    print(f"Beolvasott sorok: {len(entries)}")
    print(f"id-duplikátumok: {len(report['id_duplicates'])}")
    for d in report["id_duplicates"]:
        print(f"  id={d['id']}: megtartva sor {d['kept']}, duplikátum sor {d['duplicate']}")
    print(f"instruction-hasonlóság duplikátumok: {len(report['instruction_duplicates'])}")
    for d in report["instruction_duplicates"]:
        print(f"  megtartva sor {d['kept']}, duplikátum sor {d['duplicate']} (hasonlóság={d['similarity']})")
    print(f"output-hasonlóság duplikátumok: {len(report['output_duplicates'])}")
    for d in report["output_duplicates"]:
        print(f"  megtartva sor {d['kept']}, duplikátum sor {d['duplicate']} (hasonlóság={d['similarity']})")


if __name__ == "__main__":
    _main()
