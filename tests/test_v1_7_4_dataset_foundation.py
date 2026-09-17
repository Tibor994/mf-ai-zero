"""
MF-AI-Zero - v1.7.4 dataset foundation teszt (tools/dataset_validate.py,
tools/dataset_dedupe.py, tools/dataset_score.py, tools/dataset_split.py,
tools/dataset_import.py).

FONTOS: ez a modul NEM tanít semmit és NEM generál nagy tanítóadatot -
kizárólag a validáló/dedupe/pontozó/split/import ESZKÖZÖKET teszteli,
apró, a teszt saját maga által létrehozott, ideiglenes JSONL fájlokon.

Nyolc rész:
  1. valid JSONL sor elfogadása
  2. invalid JSON sor elutasítása
  3. hiányzó mező elutasítása
  4. escape-hiba felismerése (pl. "simple\\_qa")
  5. duplikált id felismerése
  6. üres/túl rövid output felismerése, garbled/repeated-char felismerés
  7. dataset_dedupe.py (id / instruction+input / output hasonlóság)
  8. dataset_score.py, dataset_split.py, dataset_import.py (clean/
     rejected/report fájlok létrejönnek), és a data/samples/
     sample_pack_v1.jsonl teljes egészében valid.

Futtatás:
    python tests/test_v1_7_4_dataset_foundation.py
"""

import json
import os
import sys
import tempfile

TOOLS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools")
REPO_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, TOOLS_DIR)

from dataset_validate import validate_file, validate_row, find_invalid_escapes  # noqa: E402
from dataset_dedupe import find_duplicates, dedupe_rows  # noqa: E402
from dataset_score import score_row  # noqa: E402
from dataset_split import split_rows  # noqa: E402
from dataset_import import import_file  # noqa: E402

FAILURES = []


def check(label, condition):
    status = "OK" if condition else "FAIL"
    print(f"  [{status}] {label}")
    if not condition:
        FAILURES.append(label)


def _write_jsonl(lines):
    """Ideiglenes .jsonl fájlt ír (nyers szöveg-sorokból, NEM json.dumps-
    ból - így szándékosan hibás/escape-elt sorokat is bele tudunk tenni),
    visszaadja az elérési utat."""
    fd, path = tempfile.mkstemp(suffix=".jsonl")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        for line in lines:
            f.write(line + "\n")
    return path


VALID_ROW = {
    "id": "row-001", "category": "simple_qa", "instruction": "Mi Magyarorszag fovarosa?",
    "input": "", "output": "Magyarorszag fovarosa Budapest.", "tags": ["geo"],
    "difficulty": "easy", "quality_notes": "", "source": "manual",
}


# ---------------------------------------------------------------------------
# 1) valid JSONL elfogadva
# ---------------------------------------------------------------------------
print("--- 1) valid JSONL sor elfogadása ---")

path = _write_jsonl([json.dumps(VALID_ROW, ensure_ascii=False)])
result = validate_file(path)
check("1 valid sor -> 1 elfogadva, 0 elutasítva", len(result["valid_rows"]) == 1 and len(result["rejected_rows"]) == 0)
os.remove(path)


# ---------------------------------------------------------------------------
# 2) invalid JSON elutasítva
# ---------------------------------------------------------------------------
print("\n--- 2) invalid JSON sor elutasítása ---")

path = _write_jsonl(["{ez nem valid json"])
result = validate_file(path)
check("szintaktikailag hibás JSON sor -> elutasítva", len(result["rejected_rows"]) == 1)
check("a hiba oka 'invalid_json'", result["rejected_rows"][0]["issues"][0]["code"] == "invalid_json")
os.remove(path)


# ---------------------------------------------------------------------------
# 3) hiányzó mező elutasítva
# ---------------------------------------------------------------------------
print("\n--- 3) hiányzó mező elutasítása ---")

incomplete_row = dict(VALID_ROW)
del incomplete_row["input"]
del incomplete_row["source"]
path = _write_jsonl([json.dumps(incomplete_row, ensure_ascii=False)])
result = validate_file(path)
check("hiányzó mezőjű sor -> elutasítva", len(result["rejected_rows"]) == 1)
check("a hiba oka 'missing_fields', felsorolja a hiányzó mezőket",
      result["rejected_rows"][0]["issues"][0]["code"] == "missing_fields"
      and "input" in result["rejected_rows"][0]["issues"][0]["message"]
      and "source" in result["rejected_rows"][0]["issues"][0]["message"])
os.remove(path)


# ---------------------------------------------------------------------------
# 4) escape-hiba felismerése
# ---------------------------------------------------------------------------
print("\n--- 4) 'simple\\\\_qa' escape-hiba felismerése ---")

bad_escape_row = dict(VALID_ROW)
bad_escape_row["category"] = "simple_qa"
raw_line = json.dumps(bad_escape_row, ensure_ascii=False).replace('"simple_qa"', '"simple\\_qa"')
check("a teszt-sor valóban tartalmazza a hibás escape-et", "\\_qa" in raw_line)
path = _write_jsonl([raw_line])
result = validate_file(path)
check("'simple\\\\_qa' escape-hibás sor -> elutasítva", len(result["rejected_rows"]) == 1)
check("a hiba oka 'invalid_escape', és auto_fixable=True",
      result["rejected_rows"][0]["issues"][0]["code"] == "invalid_escape"
      and result["rejected_rows"][0]["issues"][0]["auto_fixable"] is True)
os.remove(path)

check("find_invalid_escapes() közvetlenül is felismeri a \\\\_ mintát",
      find_invalid_escapes('{"category": "simple\\_qa"}') == ["\\_"])
check("find_invalid_escapes() a helyes (nem escape-elt) sort NEM jelzi hibásnak",
      find_invalid_escapes('{"category": "simple_qa"}') == [])
check("find_invalid_escapes() a VALID JSON escape-eket (\\\\n, \\\\\") nem jelzi hibásnak",
      find_invalid_escapes('{"a": "sor1\\nsor2", "b": "id\\u00e9zet: \\"sz\\u00f6veg\\""}') == [])


# ---------------------------------------------------------------------------
# 5) duplikált id felismerése
# ---------------------------------------------------------------------------
print("\n--- 5) duplikált id felismerése ---")

row_a = dict(VALID_ROW)
row_b = dict(VALID_ROW)
row_b["instruction"] = "Egy teljesen más kérdés."
row_b["output"] = "Egy teljesen más válasz szöveg itt."
path = _write_jsonl([json.dumps(row_a, ensure_ascii=False), json.dumps(row_b, ensure_ascii=False)])
result = validate_file(path)
check("azonos id-jú 2. sor -> elutasítva", len(result["valid_rows"]) == 1 and len(result["rejected_rows"]) == 1)
check("a hiba oka 'duplicate_id'", result["rejected_rows"][0]["issues"][0]["code"] == "duplicate_id")
os.remove(path)


# ---------------------------------------------------------------------------
# 6) üres/túl rövid output, garbled/repeated-char felismerés
# ---------------------------------------------------------------------------
print("\n--- 6) üres/túl rövid output, garbled/repeated-char felismerés ---")

empty_output_row = dict(VALID_ROW)
empty_output_row["id"] = "row-empty"
empty_output_row["output"] = ""
issues = validate_row(empty_output_row, 1, set())
check("üres output -> 'empty_output' hiba", any(i.code == "empty_output" for i in issues))

short_output_row = dict(VALID_ROW)
short_output_row["id"] = "row-short"
short_output_row["output"] = "Ok."
issues = validate_row(short_output_row, 1, set())
check("túl rövid (1 szavas) output -> 'output_too_short' figyelmeztetés",
      any(i.code == "output_too_short" for i in issues))

long_output_row = dict(VALID_ROW)
long_output_row["id"] = "row-long"
long_output_row["output"] = "Hosszú szöveg. " * 200
issues = validate_row(long_output_row, 1, set())
check("túl hosszú output -> 'output_too_long' hiba", any(i.code == "output_too_long" for i in issues))

garbled_row = dict(VALID_ROW)
garbled_row["id"] = "row-garbled"
garbled_row["output"] = "Ez egy szvmnt torz valasz itt."
issues = validate_row(garbled_row, 1, set())
check("torz/magánhangzó nélküli szó -> 'garbled_output' hiba", any(i.code == "garbled_output" for i in issues))

repeated_row = dict(VALID_ROW)
repeated_row["id"] = "row-repeated"
repeated_row["output"] = "Ez egy aaaaaaa ismétlődő karakteres válasz."
issues = validate_row(repeated_row, 1, set())
check("ismétlődő karaktersorozat -> 'repeated_char_run' hiba", any(i.code == "repeated_char_run" for i in issues))

bad_difficulty_row = dict(VALID_ROW)
bad_difficulty_row["id"] = "row-diff"
bad_difficulty_row["difficulty"] = "nagyon_nehez"
issues = validate_row(bad_difficulty_row, 1, set())
check("érvénytelen difficulty -> 'invalid_difficulty' hiba", any(i.code == "invalid_difficulty" for i in issues))

overclaim_row = dict(VALID_ROW)
overclaim_row["id"] = "row-overclaim"
overclaim_row["output"] = "Olyan okos vagyok, mint a ChatGPT, mindent tudok."
issues = validate_row(overclaim_row, 1, set())
check("túlzó Nexora-állítás -> 'overclaiming' hiba", any(i.code == "overclaiming" for i in issues))

# regresszió: a valóban magyar, ékezetes szöveg NEM okoz hamis angol-keveredést
hungarian_row = dict(VALID_ROW)
hungarian_row["id"] = "row-hu"
hungarian_row["output"] = "Ez nem hasonlítható a nagy rendszerekhez, de igyekszem hasznos lenni."
issues = validate_row(hungarian_row, 1, set())
check("ékezetes magyar szöveg (pl. 'hasonlítható') NEM ad hamis english_mixing találatot",
      not any(i.code == "english_mixing" for i in issues))


# ---------------------------------------------------------------------------
# 7) dataset_dedupe.py
# ---------------------------------------------------------------------------
print("\n--- 7) dataset_dedupe.py ---")

entries = [
    {"row_number": 1, "row": {"id": "d1", "instruction": "Kérdés A", "input": "", "output": "Ez itt az első válasz szövege, budapesti témával."}},
    {"row_number": 2, "row": {"id": "d2", "instruction": "Kérdés A", "input": "", "output": "Teljesen más, hosszabb kifejtésű válasz, ami a tanulásról szól."}},
    {"row_number": 3, "row": {"id": "d1", "instruction": "Kérdés C", "input": "", "output": "Harmadik, önálló témájú válasz a programozásról."}},
    {"row_number": 4, "row": {"id": "d4", "instruction": "Javítsd ki!", "input": "hany eves vagy", "output": "Nincs valódi életkorom, hiszen program vagyok."}},
    {"row_number": 5, "row": {"id": "d5", "instruction": "Javítsd ki!", "input": "mit tudsz csinalni amugy", "output": "Tudok beszélgetni és emlékezni a beszélgetésen belül."}},
]
dup_report = find_duplicates(entries)
check("id-duplikátum felismerve (d1 kétszer)", len(dup_report["id_duplicates"]) == 1
      and dup_report["id_duplicates"][0]["duplicate"] == 3)
check("azonos instruction+input -> hasonlósági duplikátum felismerve (sor 1 és 2)",
      any(d["duplicate"] == 2 for d in dup_report["instruction_duplicates"]))
check("azonos instruction-SABLON, DE eltérő input -> NEM duplikátum (sor 4 és 5)",
      not any(d["duplicate"] == 5 for d in dup_report["instruction_duplicates"]))

kept_entries, _ = dedupe_rows(entries)
kept_row_numbers = {e["row_number"] for e in kept_entries}
check("dedupe_rows() kiszűri a duplikátumokat, megtartja az egyedieket",
      3 not in kept_row_numbers and 2 not in kept_row_numbers
      and 1 in kept_row_numbers and 4 in kept_row_numbers and 5 in kept_row_numbers)


# ---------------------------------------------------------------------------
# 8) dataset_score.py, dataset_split.py, dataset_import.py, minta-csomag
# ---------------------------------------------------------------------------
print("\n--- 8) dataset_score.py / dataset_split.py / dataset_import.py / minta-csomag ---")

score, flags = score_row(VALID_ROW)
check("egy jó minőségű sor magas quality_score-t kap", score >= 90 and not flags)

score_bad, flags_bad = score_row({**VALID_ROW, "output": "Ez egy szvmnt torz valasz."})
check("torz szavú output alacsonyabb quality_score-t kap", score_bad < score and "garbled_token" in flags_bad)

rows_for_split = (
    [{"category": "simple_qa", "id": f"sq{i}"} for i in range(10)]
    + [{"category": "explanation", "id": f"ex{i}"} for i in range(3)]
)
train1, eval1 = split_rows(rows_for_split, train_ratio=0.9, seed=42)
train2, eval2 = split_rows(rows_for_split, train_ratio=0.9, seed=42)
check("split létrejön (train+eval lefedi az összes sort)", len(train1) + len(eval1) == len(rows_for_split))
check("split determinisztikus (ugyanaz a seed -> ugyanaz az eredmény)",
      [r["id"] for r in train1] == [r["id"] for r in train2])
check("split kategóriánként arányos (mindkét kategóriából jut eval-ba is)",
      any(r["category"] == "simple_qa" for r in eval1) and any(r["category"] == "explanation" for r in eval1))

# --- teljes import-folyamat: clean/rejected/report fájlok tényleg létrejönnek ---
with tempfile.TemporaryDirectory() as tmp_dir:
    clean_dir = os.path.join(tmp_dir, "clean")
    rejected_dir = os.path.join(tmp_dir, "rejected")
    reports_dir = os.path.join(tmp_dir, "reports")

    raw_lines = [
        json.dumps(VALID_ROW, ensure_ascii=False),
        json.dumps({**VALID_ROW, "id": "row-002", "instruction": "Másik kérdés", "output": "Másik válasz szöveg itt."}, ensure_ascii=False),
        "{ez nem valid json",
        json.dumps({**VALID_ROW, "id": "row-004", "output": ""}, ensure_ascii=False),
    ]
    raw_path = _write_jsonl(raw_lines)
    summary = import_file(raw_path, clean_dir=clean_dir, rejected_dir=rejected_dir, reports_dir=reports_dir)

    check("import_file() összegzése helyes számokat ad (2 elfogadva, 2 elutasítva)",
          summary["accepted_count"] == 2 and summary["rejected_count"] == 2)
    check("clean fájl ténylegesen létrejön és a várt sorszámot tartalmazza",
          os.path.exists(summary["clean_path"]) and sum(1 for _ in open(summary["clean_path"], encoding="utf-8")) == 2)
    check("rejected fájl ténylegesen létrejön", os.path.exists(summary["rejected_path"]))
    check("rejected report JSON ténylegesen létrejön és tartalmazza a hiba-okokat",
          os.path.exists(summary["rejected_report_path"]))
    with open(summary["rejected_report_path"], encoding="utf-8") as f:
        rejected_report = json.load(f)
    check("rejected report minden eleme tartalmazza a kért mezőket (sor, id, ok, auto-javíthatóság)",
          all({"row_number", "id", "reason_code", "reason_message", "auto_fixable", "needs_manual_review"} <= set(r.keys())
              for r in rejected_report))
    check("summary report fájl ténylegesen létrejön", os.path.exists(summary["summary_path"]))

    clean_rows = [json.loads(line) for line in open(summary["clean_path"], encoding="utf-8")]
    check("a clean fájl sorai tartalmazzák a quality_score mezőt", all("quality_score" in r for r in clean_rows))

    os.remove(raw_path)

# --- a data/samples/sample_pack_v1.jsonl minta-csomag teljes egészében valid ---
sample_pack_path = os.path.join(REPO_ROOT, "data", "samples", "sample_pack_v1.jsonl")
check("data/samples/sample_pack_v1.jsonl létezik", os.path.exists(sample_pack_path))
sample_result = validate_file(sample_pack_path)
check("a minta-csomag MINDEN sora valid (0 elutasítva)", len(sample_result["rejected_rows"]) == 0)
check("a minta-csomag 10-20 sort tartalmaz, ahogy kérve volt",
      10 <= len(sample_result["valid_rows"]) <= 20)
sample_categories = {entry["row"]["category"] for entry in sample_result["valid_rows"]}
check("a minta-csomag lefedi mind az 5 kért kategóriát",
      sample_categories == {"simple_qa", "explanation", "typo_correction", "summary", "uncertain_lookup"})
sample_dup_report = find_duplicates(sample_result["valid_rows"])
check("a minta-csomagban nincs semmilyen duplikátum",
      not sample_dup_report["id_duplicates"] and not sample_dup_report["instruction_duplicates"]
      and not sample_dup_report["output_duplicates"])


# ---------------------------------------------------------------------------
print(f"\n{'=' * 60}")
if FAILURES:
    print(f"EREDMÉNY: {len(FAILURES)} teszt megbukott:")
    for f in FAILURES:
        print(f"  - {f}")
    print("STÁTUSZ: NEM STABIL")
else:
    print("EREDMÉNY: minden teszt sikeres.")
    print("STÁTUSZ: STABIL")
print("=" * 60)

if __name__ == "__main__":
    sys.exit(1 if FAILURES else 0)
