"""
MF-AI-Zero - v1.7.4 dataset foundation: JSONL validátor.

CÉL: mielőtt egy külső forrásból (Gemini/ChatGPT/Claude generálta, vagy
kézzel írt) JSONL adatcsomagot BÁRMILYEN formában felhasználnánk (tanítás,
minőségi mintavétel, stb.), ez a modul sor-szinten ellenőrzi, hogy a
tartalom biztonságos és szerkezetileg helyes-e. Ez a modul CSAK ELLENŐRIZ
és REPORTOL - SOHA nem töröl, nem módosít, nem ír felül semmilyen forrás-
fájlt, és NEM indít tanítást.

Elvárt JSONL séma soronként:
    {
      "id": "egyedi-string",
      "category": "pl. simple_qa/explanation/typo_correction/...",
      "instruction": "a feladat/kérdés szövege",
      "input": "opcionális kiegészítő bemenet (lehet üres string)",
      "output": "az elvárt válasz szövege",
      "tags": ["cimke1", "cimke2"],
      "difficulty": "easy" | "medium" | "hard",
      "quality_notes": "szabad szöveges megjegyzés (lehet üres string)",
      "source": "pl. gemini/chatgpt/claude/manual"
    }

Használat parancssorból:
    python tools/dataset_validate.py data/raw/gemini_batch1.jsonl

Használat modulként:
    from dataset_validate import validate_file, validate_row
"""

import argparse
import json
import os
import re
import sys

SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
sys.path.insert(0, SRC_DIR)
from evaluator import _has_garbled_token, _has_repeated_char_run  # noqa: E402

REQUIRED_FIELDS = [
    "id", "category", "instruction", "input", "output",
    "tags", "difficulty", "quality_notes", "source",
]
ALLOWED_DIFFICULTIES = {"easy", "medium", "hard"}

MIN_OUTPUT_WORDS = 3
MAX_OUTPUT_CHARS = 1500

# JSON szabvány szerint EGYETLEN karakter engedélyezett escape-elt formában
# szerepelhet közvetlenül a backslash után (\uXXXX-en kívül): " \ / b f n r t
# - minden más (pl. a felhasználó által is említett "simple\_qa") ÉRVÉNYTELEN
# JSON escape, még akkor is, ha néhány laza parser lenyeli.
_VALID_JSON_ESCAPE_CHARS = set('"\\/bfnrtu')
_ESCAPE_RE = re.compile(r"\\(.)")

# v1.7.4 - konzervatív, kézzel karbantartott listák (NEM ML-alapú
# nyelvfelismerés/szótár - lásd docs/NEXORA_DATASET_GUIDE.md a korlátokról).
_ENGLISH_STOPWORDS = {
    # FONTOS: "is" SZÁNDÉKOSAN NINCS a listában - a magyarban ez egy
    # nagyon gyakori, önálló szó ("is" = "is/also/too", pl. "én is"),
    # ide véve rengeteg hamis találatot adna.
    "the", "are", "was", "were", "and", "you", "what", "how",
    "this", "that", "with", "have", "will", "would", "should",
    "please", "thanks", "hello", "yes",
}
_TECHNICAL_ALLOWLIST = {
    "python", "html", "css", "json", "jsonl", "api", "function", "class",
    "import", "javascript", "js", "http", "https", "url", "id", "app",
    "flask", "git", "github", "markdown", "csv", "log", "ai", "llm",
}
_PERSONAL_DATA_PATTERNS = [
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"), "email_cím-szerű minta"),
    (re.compile(r"\b(?:\+?\d{1,3}[\s-]?)?(?:\d{2,4}[\s-]?){3,4}\b"), "telefonszám-szerű minta"),
    (re.compile(r"\b\d{4}-\d{2}-\d{2}\b.{0,20}(?:szület|birth)", re.IGNORECASE), "születési dátum-szerű minta"),
]
_DANGEROUS_CONTENT_PATTERNS = [
    (re.compile(r"(?i)\b(api[_-]?key|secret[_-]?key|jelszó|password|access[_-]?token)\s*[:=]\s*\S+"), "kulcs/jelszó-szerű minta"),
    (re.compile(r"(?i)\bAKIA[0-9A-Z]{16}\b"), "AWS-kulcs-szerű minta"),
    (re.compile(r"(?i)-----BEGIN (?:RSA |EC )?PRIVATE KEY-----"), "privát kulcs blokk"),
]
_OVERCLAIMING_PATTERNS = [
    "olyan okos, mint a chatgpt", "emberi szintű intelligencia", "tökéletesen ért mindent",
    "mindent tudok", "sosem tévedek", "jobb vagyok, mint bármelyik ai",
    "öntudatra ébredtem", "valódi érzéseim vannak", "élő lény vagyok",
]


class ValidationIssue:
    """Egy sor egy konkrét problémája - a `code` géppel is értelmezhető,
    az `auto_fixable` jelzi, hogy ez a fajta hiba elvileg gépi javításra
    alkalmas-e (NEM jelenti azt, hogy ez a modul automatikusan javítja -
    csak egy útmutató jelzés a kézi átnézéshez, lásd docs/NEXORA_DATASET_GUIDE.md)."""

    def __init__(self, code, message, auto_fixable=False):
        self.code = code
        self.message = message
        self.auto_fixable = auto_fixable

    def to_dict(self):
        return {"code": self.code, "message": self.message, "auto_fixable": self.auto_fixable}


def find_invalid_escapes(raw_line):
    """A NYERS (még nem JSON-ná parse-olt) sorszöveget vizsgálja - ez adja
    a leghasznosabb hibaüzenetet a leggyakoribb, ténylegesen megfigyelt
    hibára: egy AI-generátor felesleges backslash-t tesz egy aláhúzás elé
    (pl. "simple\\_qa" a helyes "simple_qa" helyett)."""
    return [m.group(0) for m in _ESCAPE_RE.finditer(raw_line) if m.group(1) not in _VALID_JSON_ESCAPE_CHARS]


_WORD_TOKEN_RE = re.compile(r"[^\W\d_]+", re.UNICODE)


def _contains_english_mixing(text):
    # FONTOS: Unicode-tudatos szótokenizálás (nem csak A-Za-z!) - egy
    # sima ASCII-mintázat az ékezetes magyar szavakat (pl.
    # "hasonlítható") az ékezetek mentén FÉLBEVÁGNÁ, és a köztük maradt
    # véletlenszerű ASCII-töredék (pl. "...l[í]that[ó]...") hamisan
    # egyezhetne egy angol szóval - ez volt az első verzió valódi hibája.
    tokens = _WORD_TOKEN_RE.findall(text or "")
    for token in tokens:
        low = token.lower()
        if low in _ENGLISH_STOPWORDS and low not in _TECHNICAL_ALLOWLIST:
            return low
    return None


def _contains_personal_data(text):
    for pattern, label in _PERSONAL_DATA_PATTERNS:
        if pattern.search(text or ""):
            return label
    return None


def _contains_dangerous_content(text):
    for pattern, label in _DANGEROUS_CONTENT_PATTERNS:
        if pattern.search(text or ""):
            return label
    return None


def _contains_overclaiming(text):
    low = (text or "").lower()
    for phrase in _OVERCLAIMING_PATTERNS:
        if phrase in low:
            return phrase
    return None


def validate_row(row, row_number, seen_ids):
    """Egy MÁR JSON-ná parse-olt sor (dict) ellenőrzése. Visszaad egy
    ValidationIssue listát (üres, ha a sor teljesen rendben van). A
    `seen_ids` egy a hívó által fenntartott halmaz - ide adjuk hozzá az
    id-t, hogy a hívó a TELJES fájlon belüli duplikációt tudja követni."""
    issues = []

    if not isinstance(row, dict):
        return [ValidationIssue("not_an_object", f"A(z) {row_number}. sor nem egy JSON objektum.")]

    missing = [f for f in REQUIRED_FIELDS if f not in row]
    if missing:
        issues.append(ValidationIssue(
            "missing_fields", f"Hiányzó mező(k): {', '.join(missing)}.", auto_fixable=False,
        ))
        # a hiányzó mezők miatt a további, mező-specifikus ellenőrzések
        # nagy része félrevezető lenne - itt megállunk ennél a sornál.
        return issues

    row_id = row.get("id")
    if not isinstance(row_id, str) or not row_id.strip():
        issues.append(ValidationIssue("empty_id", "Az 'id' mező üres vagy nem string."))
    elif row_id in seen_ids:
        issues.append(ValidationIssue("duplicate_id", f"Duplikált id a fájlon belül: '{row_id}'.", auto_fixable=False))
    else:
        seen_ids.add(row_id)

    if not isinstance(row.get("category"), str) or not row["category"].strip():
        issues.append(ValidationIssue("empty_category", "A 'category' mező üres vagy nem string."))

    if not isinstance(row.get("instruction"), str) or not row["instruction"].strip():
        issues.append(ValidationIssue("empty_instruction", "Az 'instruction' mező üres vagy nem string."))

    output = row.get("output")
    if not isinstance(output, str) or not output.strip():
        issues.append(ValidationIssue("empty_output", "Az 'output' mező üres vagy nem string."))
        output = ""

    if not isinstance(row.get("tags"), list):
        issues.append(ValidationIssue("tags_not_list", "A 'tags' mezőnek listának kell lennie.", auto_fixable=True))

    if row.get("difficulty") not in ALLOWED_DIFFICULTIES:
        issues.append(ValidationIssue(
            "invalid_difficulty",
            f"A 'difficulty' csak {sorted(ALLOWED_DIFFICULTIES)} lehet, nem '{row.get('difficulty')}'.",
        ))

    if not isinstance(row.get("source"), str) or not row["source"].strip():
        issues.append(ValidationIssue("empty_source", "A 'source' mező üres vagy nem string."))

    stripped_output = output.strip()
    if stripped_output:
        word_count = len(stripped_output.split())
        if word_count < MIN_OUTPUT_WORDS:
            issues.append(ValidationIssue("output_too_short", f"Az output túl rövid ({word_count} szó)."))
        if len(stripped_output) > MAX_OUTPUT_CHARS:
            issues.append(ValidationIssue(
                "output_too_long", f"Az output túl hosszú ({len(stripped_output)} karakter, max. {MAX_OUTPUT_CHARS}).",
            ))
        if _has_repeated_char_run(stripped_output):
            issues.append(ValidationIssue("repeated_char_run", "Zagyva, ismétlődő karaktersorozat az outputban."))
        if _has_garbled_token(stripped_output):
            issues.append(ValidationIssue("garbled_output", "Torz/értelmetlen szó (magánhangzó nélküli token) az outputban."))

        mixed_word = _contains_english_mixing(stripped_output)
        if mixed_word:
            issues.append(ValidationIssue(
                "english_mixing", f"Nyilvánvaló angol keveredés az outputban (pl. \"{mixed_word}\"), "
                "nem technikai szó.", auto_fixable=True,
            ))

        overclaim = _contains_overclaiming(stripped_output)
        if overclaim:
            issues.append(ValidationIssue(
                "overclaiming", f"Túl magabiztos/valótlan Nexora-állítás az outputban (\"{overclaim}\").",
            ))

    for field_name in ("instruction", "input", "output", "quality_notes"):
        field_value = row.get(field_name)
        if isinstance(field_value, str):
            personal = _contains_personal_data(field_value)
            if personal:
                issues.append(ValidationIssue(
                    "personal_data_suspected", f"Személyes adatra utaló minta a(z) '{field_name}' mezőben: {personal}.",
                ))
            dangerous = _contains_dangerous_content(field_value)
            if dangerous:
                issues.append(ValidationIssue(
                    "dangerous_content_suspected", f"Veszélyes tartalomra utaló minta a(z) '{field_name}' mezőben: {dangerous}.",
                ))

    return issues


def validate_file(path):
    """Beolvas egy JSONL fájlt és soronként ellenőrzi. Visszaad egy dict-et:
    {"valid_rows": [...], "rejected_rows": [...], "line_count": N}

    valid_rows: [{"row_number", "row"}], rejected_rows: [{"row_number",
    "id", "issues": [...]}] - a hibás sorok SOHA nem törlődnek/módosulnak,
    csak besorolásra kerülnek."""
    valid_rows = []
    rejected_rows = []
    seen_ids = set()
    line_count = 0

    with open(path, "r", encoding="utf-8") as f:
        for line_number, raw_line in enumerate(f, start=1):
            stripped_line = raw_line.rstrip("\n\r")
            if not stripped_line.strip():
                continue
            line_count += 1

            escape_problems = find_invalid_escapes(stripped_line)
            if escape_problems:
                rejected_rows.append({
                    "row_number": line_number,
                    "id": None,
                    "issues": [ValidationIssue(
                        "invalid_escape",
                        f"Érvénytelen JSON escape-szekvenciá(k): {', '.join(sorted(set(escape_problems)))} "
                        "- pl. \"simple\\_qa\" helyett \"simple_qa\" kell.",
                        auto_fixable=True,
                    ).to_dict()],
                })
                continue

            try:
                row = json.loads(stripped_line)
            except json.JSONDecodeError as exc:
                rejected_rows.append({
                    "row_number": line_number,
                    "id": None,
                    "issues": [ValidationIssue("invalid_json", f"Nem valid JSON: {exc}").to_dict()],
                })
                continue

            issues = validate_row(row, line_number, seen_ids)
            if issues:
                rejected_rows.append({
                    "row_number": line_number,
                    "id": row.get("id") if isinstance(row, dict) else None,
                    "issues": [issue.to_dict() for issue in issues],
                })
            else:
                valid_rows.append({"row_number": line_number, "row": row})

    return {"valid_rows": valid_rows, "rejected_rows": rejected_rows, "line_count": line_count}


def _main():
    parser = argparse.ArgumentParser(description="MF-AI-Zero dataset JSONL validátor.")
    parser.add_argument("path", help="A validálandó .jsonl fájl elérési útja.")
    args = parser.parse_args()

    result = validate_file(args.path)
    print(f"Beolvasott sorok: {result['line_count']}")
    print(f"Érvényes sorok: {len(result['valid_rows'])}")
    print(f"Elutasított sorok: {len(result['rejected_rows'])}")
    for rejected in result["rejected_rows"]:
        codes = ", ".join(issue["code"] for issue in rejected["issues"])
        print(f"  sor {rejected['row_number']} (id={rejected['id']}): {codes}")

    sys.exit(1 if result["rejected_rows"] else 0)


if __name__ == "__main__":
    _main()
