"""
MF-AI-Zero - v1.7 biztonságos fájlszerkesztés (file_editor).

CÉL: a v1.6-ban már feltöltött, KIZÁRÓLAG a szerver folyamat-memóriájában
élő szöveges fájlrekordokon lehessen módosítást végezni - de csak
explicit, felhasználó által jóváhagyott, előnézetezett (diff) formában.
Az AI SOHA nem dönt automatikusan a tartalom megváltoztatásáról, és ez a
modul SOHA nem ír a szerver fájlrendszerére - ugyanaz az elv, mint a
file_reader.py-nál: a "fájl" itt is csak egy, a hívó (web/app.py)
folyamat-memóriájában élő dict, sosem egy valódi lemez-elérési út.

FOLYAMAT (mindig ebben a sorrendben, kihagyás nélkül - a tényleges
állapotkezelést, azaz a pending_edits tárolást és az apply előtti
"nem változott-e a fájl azóta" ellenőrzést a hívó fél, web/app.py végzi):
  1. build_edit_plan() - egy STRUKTURÁLT (NEM szabad szöveges, NEM
     AI-generált), determinisztikus műveletből (replace_all /
     find_replace / append) kiszámolja az új tartalmat és egy
     diff-előnézetet, de MÉG NEM alkalmazza - ez csak egy "terv", amit
     a hívó egy pending_edits tárban tárol, fájlonként legfeljebb egyet.
  2. A user a diff előnézet alapján dönt: KÜLÖN, explicit hívással
     fogadja el (web/app.py POST /api/files/edit/apply), vagy elveti
     (POST /api/files/edit/clear).
  3. Alkalmazás egyszer visszavonható (web/app.py POST /api/files/edit/
     undo) - az előző tartalom egy rövid ideig (a következő
     szerkesztésig/törlésig) megmarad.

BIZTONSÁGI SZABÁLYOK:
  - Csak a v1.6 file_reader.py által MÁR elfogadott (kiterjesztés-
    whitelist, nem blokkolt fájlnév, nem bináris) fájlrekordot lehet
    szerkeszteni - validate_editable_file() ÚJRA elvégzi ezt az
    ellenőrzést (védelem a mélyben, arra az esetre, ha a hívó egy
    elavult/hibás rekordot adna át).
  - Csak HÁROM, előre definiált, determinisztikus műveletet enged:
    teljes tartalom csere, keresés-csere, szöveg hozzáfűzése - SOSEM
    fogad el szabad szöveges "szerkesztési utasítást", amit egy AI
    generálna/értelmezne (az AI ITT semmilyen tartalmi döntést nem hoz).
  - Ha a tervezett új tartalom üres, változatlan, vagy túllépné a
    file_reader.MAX_FILE_SIZE méretlimitet, a terv elutasításra kerül.
  - A diff-előnézet mérete korlátozott (MAX_DIFF_LINES) - egy irreálisan
    nagy módosítás előnézete is kezelhető marad a UI-ban.
"""

import difflib
import uuid
from datetime import datetime

from file_reader import (
    MAX_FILE_SIZE,
    is_extension_allowed,
    is_name_blocked,
    looks_binary,
)

SUPPORTED_OPERATIONS = {"replace_all", "find_replace", "append"}
MAX_DIFF_LINES = 400


class EditValidationError(Exception):
    """Egy szerkesztési terv elutasításának oka - a `code` géppel is
    értelmezhető, a `message` már emberi olvasásra kész magyar szöveg."""

    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


def validate_editable_file(file_record):
    """Újra elvégzi a v1.6 file_reader biztonsági ellenőrzéseit a
    fájlrekord NEVÉRE és TARTALMÁRA - védelem a mélyben, hogy egy
    szerkesztés soha ne érinthessen olyan fájlt, ami feltöltéskor sem
    lenne elfogadható (pl. időközben módosult/elavult rekord)."""
    if not file_record:
        raise EditValidationError("file_not_found", "A fájl nem található vagy már törölve lett.")
    name = file_record.get("name", "")
    if not is_extension_allowed(name):
        raise EditValidationError("unsupported_type", "Ez a fájltípus nem szerkeszthető.")
    if is_name_blocked(name):
        raise EditValidationError(
            "blocked_filename",
            "Ez a fájlnév érzékeny adatra utal, ezért biztonsági okból nem szerkeszthető.",
        )
    content = file_record.get("content") or ""
    if looks_binary(content.encode("utf-8", errors="replace")):
        raise EditValidationError("binary_not_supported", "Bináris tartalmú fájlt nem lehet szerkeszteni.")


def _require_str_field(operation, field, allow_empty=False):
    value = operation.get(field)
    if not isinstance(value, str) or (not allow_empty and not value):
        raise EditValidationError(
            "missing_field", f"A(z) '{field}' mező kötelező és nem lehet üres."
        )
    return value


def apply_operation(original_content, operation):
    """Tiszta, determinisztikus függvény: a jelenlegi fájltartalomból és
    egy STRUKTURÁLT (nem szabad szöveges) műveletből kiszámolja az új
    tartalmat. Nem ír semmit sehova, csak visszaadja az eredményt."""
    if not isinstance(operation, dict):
        raise EditValidationError("invalid_operation", "Érvénytelen szerkesztési kérés.")

    op_type = operation.get("type")
    if op_type not in SUPPORTED_OPERATIONS:
        allowed = ", ".join(sorted(SUPPORTED_OPERATIONS))
        raise EditValidationError(
            "unknown_operation", f"Ismeretlen művelet. Támogatott típusok: {allowed}."
        )

    if op_type == "replace_all":
        new_content = _require_str_field(operation, "new_content", allow_empty=True)
        summary = "Teljes tartalom cseréje"
        return new_content, summary

    if op_type == "find_replace":
        find = _require_str_field(operation, "find")
        replace = _require_str_field(operation, "replace", allow_empty=True)
        count = operation.get("count")
        if count is not None and (not isinstance(count, int) or count <= 0):
            raise EditValidationError("invalid_operation", "A 'count' mezőnek pozitív egész számnak kell lennie.")
        if find not in original_content:
            preview = find if len(find) <= 60 else find[:57] + "..."
            raise EditValidationError(
                "find_not_found", f"A keresett szöveg nem található a fájlban: \"{preview}\""
            )
        occurrences = original_content.count(find)
        new_content = original_content.replace(find, replace, count if count else -1)
        applied = min(count, occurrences) if count else occurrences
        find_preview = find if len(find) <= 40 else find[:37] + "..."
        replace_preview = replace if len(replace) <= 40 else replace[:37] + "..."
        summary = f"Keresés-csere: \"{find_preview}\" -> \"{replace_preview}\" ({applied} találat)"
        return new_content, summary

    # op_type == "append"
    text = _require_str_field(operation, "text")
    separator = "" if original_content.endswith("\n") or not original_content else "\n"
    new_content = original_content + separator + text
    summary = "Szöveg hozzáfűzése a fájl végéhez"
    return new_content, summary


def build_diff(old_content, new_content, file_name):
    """Unified diff formátumú, méretben korlátozott (MAX_DIFF_LINES)
    előnézet - a user ez alapján dönt, mielőtt bármi alkalmazásra
    kerülne."""
    # difflib nem tesz sortörést a diff-sorok közé, ha az eredeti tartalom
    # nem \n-re végződik (pl. egysoros fájl) - ez a "\n" hozzáfűzés csak a
    # diff SZÁMÍTÁSÁHOZ/MEGJELENÍTÉSÉHEZ történik, a tényleges tartalmat
    # (old_content/new_content) nem módosítja.
    old_lines = old_content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)
    if old_lines and not old_lines[-1].endswith("\n"):
        old_lines[-1] += "\n"
    if new_lines and not new_lines[-1].endswith("\n"):
        new_lines[-1] += "\n"
    diff_lines = list(difflib.unified_diff(
        old_lines, new_lines,
        fromfile=f"{file_name} (jelenlegi)",
        tofile=f"{file_name} (javasolt)",
    ))
    truncated = len(diff_lines) > MAX_DIFF_LINES
    if truncated:
        diff_lines = diff_lines[:MAX_DIFF_LINES]
    diff_text = "".join(diff_lines)
    if truncated:
        diff_text += "\n... (a diff túl nagy, csak az első {} sor látszik)".format(MAX_DIFF_LINES)
    return diff_text, truncated


def build_edit_plan(file_record, operation):
    """A teljes, biztonságos terv-építés: validál, kiszámolja az új
    tartalmat, ellenőrzi a méretet/változást, és elkészíti a
    diff-előnézetet. NEM alkalmaz semmit - a visszaadott dict-et a hívó
    (web/app.py) tárolja el "pending" (még jóvá nem hagyott) tervként."""
    validate_editable_file(file_record)

    old_content = file_record.get("content") or ""
    new_content, operation_summary = apply_operation(old_content, operation)

    if new_content == old_content:
        raise EditValidationError("no_changes", "A módosítás nem változtatna semmit a fájlon.")
    if not new_content.strip():
        raise EditValidationError("empty_result", "A módosítás után a fájl üres lenne - ez nem engedélyezett.")
    new_size = len(new_content.encode("utf-8"))
    if new_size > MAX_FILE_SIZE:
        raise EditValidationError(
            "edit_too_large",
            f"A módosított fájl túl nagy lenne ({new_size:,} bájt, max. {MAX_FILE_SIZE:,} bájt engedélyezett).",
        )

    diff_text, diff_truncated = build_diff(old_content, new_content, file_record.get("name", "fájl"))

    return {
        "id": uuid.uuid4().hex[:12],
        "file_id": file_record["id"],
        "file_name": file_record.get("name"),
        "operation_type": operation.get("type"),
        "operation_summary": operation_summary,
        "diff": diff_text,
        "diff_truncated": diff_truncated,
        "old_content": old_content,
        "new_content": new_content,
        "old_size": len(old_content.encode("utf-8")),
        "new_size": new_size,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }


def public_edit_plan(plan):
    """A terv "publikus" (API-válaszba szánt) nézete - a TELJES régi/új
    tartalom NEM kerül bele (a diff már úgyis megmutatja a lényeget),
    csak a metaadat + diff-előnézet."""
    if not plan:
        return None
    return {k: v for k, v in plan.items() if k not in ("old_content", "new_content")}
