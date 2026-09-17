"""
MF-AI-Zero - v1.7 biztonságos fájlszerkesztés teszt (src/file_editor.py,
web/app.py).

Három rész:
  1. file_editor.py egységtesztek: replace_all/find_replace/append
     műveletek, diff-előnézet, elutasítási okok (nincs változás, üres
     eredmény, túl nagy, ismeretlen művelet, hiányzó mező, keresett
     szöveg nem található, nem szerkeszthető - blokkolt fájlnév/nem
     támogatott típus/bináris tartalom), a régi tartalom SOHA nem
     módosul a terv elkészítésekor.
  2. web/app.py smoke teszt: POST /api/files/edit/preview (érvényes +
     hibás esetek), POST /api/files/edit/apply (érvényes, rossz
     plan_id, elavult terv, a fájl tartalma megváltozott az előnézet
     óta), POST /api/files/edit/clear, POST /api/files/edit/undo,
     GET /api/files jelzi a has_pending_edit/has_undo_available
     mezőket, /api/chat indicators.file_edit_pending.
  3. Regressziós ellenőrzés: a v1.6 fájlfeltöltés/olvasás API-k (upload/
     list/clear) és a /api/chat file_id-alapú fájlkontextusa változatlan
     marad - ez a modul NEM módosítja a file_reader.py-t vagy a guard.py
     fájlolvasási logikáját.

Futtatás:
    python tests/test_v1_7_file_editor.py
"""

import io
import os
import sys
import tempfile

SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "web")
sys.path.insert(0, SRC_DIR)

from file_reader import build_file_record  # noqa: E402
from file_editor import (  # noqa: E402
    EditValidationError,
    SUPPORTED_OPERATIONS,
    apply_operation,
    build_diff,
    build_edit_plan,
    public_edit_plan,
    validate_editable_file,
)

FAILURES = []


def check(label, condition):
    status = "OK" if condition else "FAIL"
    print(f"  [{status}] {label}")
    if not condition:
        FAILURES.append(label)


def expect_rejected(label, file_record, operation, expected_code):
    try:
        build_edit_plan(file_record, operation)
        check(label, False)
    except EditValidationError as exc:
        check(label, exc.code == expected_code)


# ---------------------------------------------------------------------------
# 1) file_editor.py egységtesztek
# ---------------------------------------------------------------------------
print("--- file_editor.py egységtesztek ---")

check("három, előre definiált determinisztikus művelet támogatott",
      SUPPORTED_OPERATIONS == {"replace_all", "find_replace", "append"})

rec = build_file_record("notes.txt", "Kedvenc szinem a kek. Ma szep ido van.".encode("utf-8"))
original_content = rec["content"]

plan = build_edit_plan(rec, {"type": "find_replace", "find": "kek", "replace": "zold"})
check("find_replace terv elkészül, tartalmazza a diff-et", "diff" in plan and "kek" in plan["diff"] and "zold" in plan["diff"])
check("find_replace operation_summary tartalmazza a találatok számát", "1 találat" in plan["operation_summary"])
check("find_replace új tartalma helyesen cserélt", plan["new_content"] == "Kedvenc szinem a zold. Ma szep ido van.")
check("a TERV ELKÉSZÍTÉSE nem módosítja az eredeti fájlrekordot", rec["content"] == original_content)

plan_append = build_edit_plan(rec, {"type": "append", "text": "Uj sor a vegen."})
check("append terv új tartalma a végén tartalmazza a hozzáfűzött szöveget",
      plan_append["new_content"].endswith("Uj sor a vegen."))
check("append terv operation_summary", "hozzáfűzése" in plan_append["operation_summary"])

plan_replace_all = build_edit_plan(rec, {"type": "replace_all", "new_content": "Teljesen uj tartalom."})
check("replace_all terv új tartalma pontosan a megadott szöveg",
      plan_replace_all["new_content"] == "Teljesen uj tartalom.")

public = public_edit_plan(plan)
check("public_edit_plan NEM tartalmazza old_content/new_content mezőket",
      "old_content" not in public and "new_content" not in public)
check("public_edit_plan megtartja a diff-et és metaadatokat",
      "diff" in public and public["file_id"] == rec["id"])

diff_text, truncated = build_diff("egy sor", "egy masik sor", "x.txt")
check("build_diff unified diff formátumú (---/+++ fejléc)", diff_text.startswith("--- x.txt"))
check("build_diff kis diffnél nem csonkol", not truncated)

# --- elutasítási okok ---
expect_rejected("nincs változás -> elutasítva", rec, {"type": "replace_all", "new_content": original_content}, "no_changes")
expect_rejected("üres eredmény -> elutasítva", rec, {"type": "replace_all", "new_content": "   "}, "empty_result")
expect_rejected("túl nagy eredmény -> elutasítva", rec, {"type": "replace_all", "new_content": "a" * 300000}, "edit_too_large")
expect_rejected("ismeretlen művelet típus -> elutasítva", rec, {"type": "delete_all"}, "unknown_operation")
expect_rejected("find_replace hiányzó 'find' mező -> elutasítva", rec, {"type": "find_replace", "replace": "x"}, "missing_field")
expect_rejected("find_replace nem található keresett szöveg -> elutasítva",
                 rec, {"type": "find_replace", "find": "nincsilyen", "replace": "x"}, "find_not_found")
expect_rejected("append hiányzó 'text' mező -> elutasítva", rec, {"type": "append"}, "missing_field")
expect_rejected("nem dict operation -> elutasítva", rec, "nem egy dict", "invalid_operation")

# --- nem szerkeszthető fájlok (védelem a mélyben) ---
blocked_rec = dict(rec)
blocked_rec["name"] = "titkos_kulcs.txt"
try:
    validate_editable_file(blocked_rec)
    check("blokkolt fájlnév -> validate_editable_file elutasítja", False)
except EditValidationError as exc:
    check("blokkolt fájlnév -> validate_editable_file elutasítja", exc.code == "blocked_filename")

unsupported_rec = dict(rec)
unsupported_rec["name"] = "kep.png"
try:
    validate_editable_file(unsupported_rec)
    check("nem támogatott kiterjesztés -> validate_editable_file elutasítja", False)
except EditValidationError as exc:
    check("nem támogatott kiterjesztés -> validate_editable_file elutasítja", exc.code == "unsupported_type")

missing_rec = None
try:
    validate_editable_file(missing_rec)
    check("hiányzó fájlrekord -> validate_editable_file elutasítja", False)
except EditValidationError as exc:
    check("hiányzó fájlrekord -> validate_editable_file elutasítja", exc.code == "file_not_found")

check("apply_operation append új sorba fűzi hozzá a szöveget, ha az eredeti nem \\n-re végződik",
      apply_operation("abc", {"type": "append", "text": "d"})[0] == "abc\nd")


# ---------------------------------------------------------------------------
# 2) web/app.py smoke teszt
# ---------------------------------------------------------------------------
print("\n--- web/app.py smoke teszt (/api/files/edit/*, has_pending_edit/has_undo_available, file_edit_pending) ---")

sys.path.insert(0, WEB_DIR)
print("(web/app.py betöltése, ez eltarthat pár másodpercig)")
import app as webapp  # noqa: E402

with tempfile.TemporaryDirectory() as tmp_dir:
    webapp.cli_args.long_memory_store_path = os.path.join(tmp_dir, "memories.json")
    webapp.cli_args.knowledge_store_path = os.path.join(tmp_dir, "items.json")
    webapp.uploaded_files.clear()
    webapp.pending_edits.clear()
    webapp.edit_undo_backups.clear()
    client = webapp.app.test_client()

    resp_upload = client.post(
        "/api/files/upload",
        data={"file": (io.BytesIO("Kedvenc szinem a kek. Ma szep ido van.".encode("utf-8")), "notes.txt")},
        content_type="multipart/form-data",
    )
    file_id = resp_upload.get_json()["file"]["id"]
    check("v1.6 upload smoke - fájl feltöltve", resp_upload.status_code == 200)

    # --- preview hibás esetek ---
    resp_missing_file = client.post("/api/files/edit/preview",
                                     json={"file_id": "nemletezik", "operation": {"type": "append", "text": "x"}})
    check("preview ismeretlen file_id -> 404", resp_missing_file.status_code == 404
          and resp_missing_file.get_json()["error_code"] == "file_not_found")

    resp_bad_op = client.post("/api/files/edit/preview", json={"file_id": file_id, "operation": "nem dict"})
    check("preview érvénytelen operation -> 400", resp_bad_op.status_code == 400)

    resp_no_find = client.post("/api/files/edit/preview",
                                json={"file_id": file_id, "operation": {"type": "find_replace", "find": "xyz123", "replace": "q"}})
    check("preview nem található keresett szöveg -> 400, find_not_found",
          resp_no_find.status_code == 400 and resp_no_find.get_json()["error_code"] == "find_not_found")

    # --- érvényes preview + apply ---
    resp_preview = client.post("/api/files/edit/preview",
                                json={"file_id": file_id, "operation": {"type": "find_replace", "find": "kek", "replace": "zold"}})
    check("érvényes preview -> 200, diff jelen van", resp_preview.status_code == 200 and "diff" in resp_preview.get_json()["plan"])
    plan_id = resp_preview.get_json()["plan"]["id"]

    resp_list_pending = client.get("/api/files")
    check("GET /api/files jelzi a has_pending_edit=True-t preview után",
          resp_list_pending.get_json()["files"][0]["has_pending_edit"] is True)

    resp_chat_pending = client.post("/api/chat", json={
        "message": "Szia!", "file_id": file_id, "temperature": 0.6, "sentences": 4,
    })
    check("/api/chat indicators.file_edit_pending=True, ha van függőben lévő terv az aktív fájlhoz",
          resp_chat_pending.get_json()["indicators"].get("file_edit_pending") is True)

    resp_apply_wrong_plan = client.post("/api/files/edit/apply", json={"file_id": file_id, "plan_id": "rossz_id"})
    check("apply rossz plan_id-vel -> 404, plan_not_found",
          resp_apply_wrong_plan.status_code == 404 and resp_apply_wrong_plan.get_json()["error_code"] == "plan_not_found")

    resp_apply = client.post("/api/files/edit/apply", json={"file_id": file_id, "plan_id": plan_id})
    check("apply érvényes plan_id-vel -> 200", resp_apply.status_code == 200)
    check("apply után a fájl tartalma frissült (summary tükrözi)",
          "zold" in resp_apply.get_json()["file"]["summary"])
    check("apply után a fájl rekord tartalmaz edited_at mezőt", "edited_at" in resp_apply.get_json()["file"])

    resp_list_after_apply = client.get("/api/files")
    files_after_apply = resp_list_after_apply.get_json()["files"][0]
    check("apply után has_pending_edit=False", files_after_apply["has_pending_edit"] is False)
    check("apply után has_undo_available=True", files_after_apply["has_undo_available"] is True)

    resp_chat_no_pending = client.post("/api/chat", json={
        "message": "Szia!", "file_id": file_id, "temperature": 0.6, "sentences": 4,
    })
    check("/api/chat indicators.file_edit_pending=False, ha nincs függőben lévő terv",
          resp_chat_no_pending.get_json()["indicators"].get("file_edit_pending") is False)

    # --- apply után elavult (ugyanaz a plan_id) apply -> plan_not_found ---
    resp_apply_again = client.post("/api/files/edit/apply", json={"file_id": file_id, "plan_id": plan_id})
    check("ugyanazt a tervet kétszer alkalmazni -> 404 (a pending_edits már törölve lett)",
          resp_apply_again.status_code == 404)

    # --- tartalom módosult a preview óta -> content_changed ---
    resp_preview2 = client.post("/api/files/edit/preview",
                                 json={"file_id": file_id, "operation": {"type": "append", "text": "ujsor"}})
    plan_id2 = resp_preview2.get_json()["plan"]["id"]
    webapp.uploaded_files[file_id]["content"] = "kozben mas valtoztatta meg"
    resp_apply_drift = client.post("/api/files/edit/apply", json={"file_id": file_id, "plan_id": plan_id2})
    check("a fájl tartalma megváltozott az előnézet óta -> 409, content_changed",
          resp_apply_drift.status_code == 409 and resp_apply_drift.get_json()["error_code"] == "content_changed")

    # --- undo ---
    webapp.uploaded_files[file_id]["content"] = "Kedvenc szinem a zold. Ma szep ido van."
    resp_undo = client.post("/api/files/edit/undo", json={"file_id": file_id})
    check("undo -> 200, visszaállítja az eredeti tartalmat",
          resp_undo.status_code == 200 and "kek" in resp_undo.get_json()["file"]["summary"])

    resp_undo_again = client.post("/api/files/edit/undo", json={"file_id": file_id})
    check("második undo (nincs több backup) -> 404, no_undo_available",
          resp_undo_again.status_code == 404 and resp_undo_again.get_json()["error_code"] == "no_undo_available")

    # --- clear (elvetés preview után, apply nélkül) ---
    client.post("/api/files/edit/preview",
                json={"file_id": file_id, "operation": {"type": "append", "text": "meg egy sor"}})
    resp_clear = client.post("/api/files/edit/clear", json={"file_id": file_id})
    check("edit/clear -> 200, removed=True", resp_clear.status_code == 200 and resp_clear.get_json()["removed"] is True)
    resp_list_after_clear = client.get("/api/files")
    check("clear után has_pending_edit=False", resp_list_after_clear.get_json()["files"][0]["has_pending_edit"] is False)

    # --- blokkolt fájlnév végpont-szinten sem szerkeszthető ---
    resp_blocked_upload = client.post(
        "/api/files/upload",
        data={"file": (io.BytesIO(b"titok"), "titkos_kulcs.txt")},
        content_type="multipart/form-data",
    )
    check("blokkolt fájlnevet fel sem lehet tölteni (v1.6 védelem érintetlen)", resp_blocked_upload.status_code == 400)

    # --- v1.6 regresszió: fájlok törlésekor a pending/undo állapot is törlődik ---
    client.post("/api/files/edit/preview",
                json={"file_id": file_id, "operation": {"type": "append", "text": "x"}})
    client.post("/api/files/clear", json={"id": file_id})
    check("fájl törlésekor a hozzá tartozó pending_edit is törlődik", file_id not in webapp.pending_edits)
    check("fájl törlésekor a hozzá tartozó edit_undo_backup is törlődik", file_id not in webapp.edit_undo_backups)

    webapp.uploaded_files.clear()
    webapp.pending_edits.clear()
    webapp.edit_undo_backups.clear()


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
