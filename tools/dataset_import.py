"""
MF-AI-Zero - v1.7.4 dataset foundation: import-folyamat (orchestrátor).

CÉL: ez a modul fűzi össze a teljes, biztonságos "nyers JSONL -> tiszta,
felhasználható adat" folyamatot, EGYETLEN paranccsal:

    python tools/dataset_import.py data/raw/gemini_batch1.jsonl

Lépések (ebben a sorrendben, mindegyik a hívó fél KIMENETÉRE épül, egyik
sem módosítja a FORRÁS fájlt):
  1. dataset_validate.validate_file() - szerkezeti/biztonsági ellenőrzés
  2. dataset_dedupe.dedupe_rows() - a validált sorokon belüli duplikátumok
     kiszűrése (id / instruction-hasonlóság / output-hasonlóság)
  3. dataset_score.score_row() - minden megmaradt sorra quality_score
  4. Kimenetek:
     - data/clean/<névalap>.jsonl        - elfogadott, deduplikált sorok
       (a quality_score bekerül a sor "quality_score" mezőjébe is)
     - data/rejected/<névalap>.jsonl     - a validáláson elbukott NYERS
       sorok (változatlanul, hogy kézzel visszanézhetők legyenek)
     - data/rejected/<névalap>_report.json - RÉSZLETES report: soronként
       a hiba oka, és hogy elvileg auto-javítható-e vagy kézi ellenőrzést
       igényel (lásd dataset_validate.ValidationIssue.auto_fixable)
     - data/reports/<névalap>_summary.json - összefoglaló: hány sor jött
       be, hány lett elfogadva/elutasítva/duplikátum, átlag quality_score

  FONTOS: ez a lépés MÉG NEM tanít semmit, és NEM ír train/eval split-et
  automatikusan - a split egy KÜLÖN, explicit lépés (lásd
  dataset_split.py), mert a user-nek előbb át kell néznie a clean/
  eredményt, mielőtt bármi "élesre" kerülne.

Használat modulként:
    from dataset_import import import_file
"""

import argparse
import json
import os
import sys

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS_DIR)

from dataset_dedupe import dedupe_rows  # noqa: E402
from dataset_score import score_row  # noqa: E402
from dataset_validate import validate_file  # noqa: E402

REPO_ROOT = os.path.join(TOOLS_DIR, "..")
DEFAULT_CLEAN_DIR = os.path.join(REPO_ROOT, "data", "clean")
DEFAULT_REJECTED_DIR = os.path.join(REPO_ROOT, "data", "rejected")
DEFAULT_REPORTS_DIR = os.path.join(REPO_ROOT, "data", "reports")


def import_file(path, clean_dir=DEFAULT_CLEAN_DIR, rejected_dir=DEFAULT_REJECTED_DIR,
                 reports_dir=DEFAULT_REPORTS_DIR, similarity_threshold=0.9, write_files=True):
    """Végrehajtja a teljes validate -> dedupe -> score folyamatot egy
    NYERS JSONL fájlon. Visszaad egy summary dict-et; write_files=True
    esetén (alapértelmezett) a clean/rejected/reports fájlokat is kiírja."""
    base_name = os.path.splitext(os.path.basename(path))[0]

    validation = validate_file(path)
    valid_entries = validation["valid_rows"]  # [{"row_number", "row"}]

    kept_entries, dedupe_report = dedupe_rows(valid_entries, similarity_threshold)

    scored_rows = []
    for entry in kept_entries:
        row = dict(entry["row"])
        score, flags = score_row(row)
        row["quality_score"] = score
        row["quality_flags"] = flags
        scored_rows.append(row)

    duplicate_count = len(valid_entries) - len(kept_entries)
    avg_score = round(sum(r["quality_score"] for r in scored_rows) / len(scored_rows), 1) if scored_rows else None

    summary = {
        "source_file": path,
        "line_count": validation["line_count"],
        "accepted_count": len(scored_rows),
        "rejected_count": len(validation["rejected_rows"]),
        "duplicate_count": duplicate_count,
        "average_quality_score": avg_score,
        "dedupe_report": dedupe_report,
    }

    if write_files:
        os.makedirs(clean_dir, exist_ok=True)
        os.makedirs(rejected_dir, exist_ok=True)
        os.makedirs(reports_dir, exist_ok=True)

        clean_path = os.path.join(clean_dir, f"{base_name}.jsonl")
        with open(clean_path, "w", encoding="utf-8") as f:
            for row in scored_rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")

        rejected_path = os.path.join(rejected_dir, f"{base_name}.jsonl")
        with open(rejected_path, "w", encoding="utf-8") as f:
            for rejected in validation["rejected_rows"]:
                f.write(json.dumps(rejected, ensure_ascii=False) + "\n")

        rejected_report_path = os.path.join(rejected_dir, f"{base_name}_report.json")
        report_rows = []
        for rejected in validation["rejected_rows"]:
            for issue in rejected["issues"]:
                report_rows.append({
                    "row_number": rejected["row_number"],
                    "id": rejected["id"],
                    "reason_code": issue["code"],
                    "reason_message": issue["message"],
                    "auto_fixable": issue["auto_fixable"],
                    "needs_manual_review": not issue["auto_fixable"],
                })
        with open(rejected_report_path, "w", encoding="utf-8") as f:
            json.dump(report_rows, f, ensure_ascii=False, indent=2)

        summary_path = os.path.join(reports_dir, f"{base_name}_summary.json")
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        summary["clean_path"] = clean_path
        summary["rejected_path"] = rejected_path
        summary["rejected_report_path"] = rejected_report_path
        summary["summary_path"] = summary_path

    return summary


def _main():
    parser = argparse.ArgumentParser(description="MF-AI-Zero dataset import (validate+dedupe+score).")
    parser.add_argument("path", help="A beolvasandó, NYERS .jsonl fájl elérési útja (pl. data/raw/...).")
    parser.add_argument("--similarity-threshold", type=float, default=0.9)
    args = parser.parse_args()

    summary = import_file(args.path, similarity_threshold=args.similarity_threshold)
    print(f"Beolvasott sorok: {summary['line_count']}")
    print(f"Elfogadva: {summary['accepted_count']}")
    print(f"Elutasítva (validálás): {summary['rejected_count']}")
    print(f"Duplikátum (kiszűrve): {summary['duplicate_count']}")
    print(f"Átlag quality_score: {summary['average_quality_score']}")
    print(f"Clean fájl: {summary.get('clean_path')}")
    print(f"Rejected fájl: {summary.get('rejected_path')}")
    print(f"Rejected report: {summary.get('rejected_report_path')}")
    print(f"Summary report: {summary.get('summary_path')}")


if __name__ == "__main__":
    _main()
