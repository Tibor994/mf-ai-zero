"""
MF-AI-Zero - v1.6 fájlfeltöltés + fájlolvasás teszt (src/file_reader.py,
src/guard.py, web/app.py).

Négy rész:
  1. file_reader.py egységtesztek: érvényes .txt/.md/.json/.py fájlok
     elfogadása, nem támogatott típus elutasítása, túl nagy fájl
     elutasítása, path-traversal-szerű fájlnév biztonságos kezelése,
     .env/secret jellegű fájlnév elutasítása, üres fájl elutasítása,
     bináris tartalom elutasítása.
  2. guard.py integráció: guarded_route_and_respond() active_file-lal
     hívva a guard_info dict tartalmazza a file_used/file_name/
     file_type/file_size/file_summary_used mezőket - valódi modellel.
  3. web/app.py smoke teszt: POST /api/files/upload (érvényes + hibás
     esetek), GET /api/files, POST /api/files/clear, POST /api/chat
     file_id-vel (indicators.file_context_used).
  4. compare_v09_guard.py-hoz hasonló elv: a file-kontextus réteg
     alapból "alvó" (dormant) - ha nincs active_file, semmilyen hatása
     nincs a promptra (ezt a meglévő compare_v09_guard.py smoke futása
     igazolja külön, mert ott sosem adunk át file_id-t).

Futtatás:
    python tests/test_v1_6_file_reader.py
"""

import os
import sys
import tempfile

SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "web")
sys.path.insert(0, SRC_DIR)

from file_reader import (  # noqa: E402
    ALLOWED_EXTENSIONS,
    MAX_FILE_SIZE,
    FileValidationError,
    build_file_prompt_context,
    build_file_record,
    build_file_summary,
    is_extension_allowed,
    is_name_blocked,
    looks_binary,
    public_file_record,
    sanitize_display_name,
    to_knowledge_candidate,
    validate_upload,
)

FAILURES = []


def check(label, condition):
    status = "OK" if condition else "FAIL"
    print(f"  [{status}] {label}")
    if not condition:
        FAILURES.append(label)


def expect_rejected(label, filename, raw_bytes, expected_code):
    try:
        validate_upload(filename, raw_bytes)
        check(label, False)
    except FileValidationError as exc:
        check(label, exc.code == expected_code)


# ---------------------------------------------------------------------------
# 1) file_reader.py egységtesztek
# ---------------------------------------------------------------------------
print("--- file_reader.py egységtesztek ---")

check("minden kért kiterjesztés engedélyezett",
      {".txt", ".md", ".json", ".jsonl", ".csv", ".py", ".js", ".html", ".css", ".log"} <= ALLOWED_EXTENSIONS)

for ext, sample in [
    (".txt", b"Ez egy sima szoveges fajl."),
    (".md", b"# Cim\n\nEgy kis markdown szoveg."),
    (".json", b'{"kulcs": "ertek"}'),
    (".py", b"print('hello')\n"),
]:
    name = f"minta{ext}"
    record = build_file_record(name, sample)
    check(f"{ext} fájl elfogadva és beolvasva", record["content"].startswith(sample.decode("utf-8")[:5]))
    check(f"{ext} fájl summary elkészült", isinstance(record["summary"], str) and len(record["summary"]) > 0)
    check(f"{ext} fájl record tartalmaz id/name/type/size mezőt", all(
        k in record for k in ("id", "name", "type", "size", "content", "summary", "uploaded_at")
    ))

expect_rejected("nem támogatott kiterjesztés (.exe) elutasítva", "program.exe", b"MZ...", "unsupported_type")
expect_rejected("nem támogatott kiterjesztés (.png) elutasítva", "kep.png", b"\x89PNG...", "unsupported_type")

big_content = b"a" * (MAX_FILE_SIZE + 1)
expect_rejected("túl nagy fájl elutasítva", "nagy.txt", big_content, "file_too_large")

expect_rejected("üres fájl elutasítva", "ures.txt", b"", "empty_file")

expect_rejected(".env fájl elutasítva (kiterjesztés miatt sem támogatott)", ".env", b"SECRET=1", "unsupported_type")
expect_rejected("secret_keys.json fájlnév elutasítva (blokkolt kulcsszó)", "secret_keys.json", b"{}", "blocked_filename")
expect_rejected("api_token.txt fájlnév elutasítva (blokkolt kulcsszó)", "api_token.txt", b"asd", "blocked_filename")
expect_rejected("jelszo_lista.txt fájlnév elutasítva (magyar kulcsszó: jelszo)", "jelszo_lista.txt", b"asd", "blocked_filename")

check("path-traversal fájlnév ('../../etc/passwd.txt') biztonságosan 'passwd.txt'-re csökken",
      sanitize_display_name("../../etc/passwd.txt") == "passwd.txt")
check("windows-stílusú path-traversal ('..\\\\..\\\\secrets.txt') is levágódik",
      sanitize_display_name("..\\..\\secrets.txt") == "secrets.txt")
check("path-traversal fájlnév végül átmegy a validáláson (mivel csak a fájlnév számít, nem a path)",
      is_extension_allowed(sanitize_display_name("../../etc/passwd.txt")))

check("bináris tartalom (NUL bájt) felismerve", looks_binary(b"valami\x00bin"))
check("érvénytelen UTF-8 bájtsorozat bináris tartalomnak számít", looks_binary(b"\xff\xfe\x00\x01"))
check("sima szöveg NEM bináris", not looks_binary(b"Ez sima szoveg ekezetekkel: arvizturo tukorfurogep."))
expect_rejected("bináris tartalmú .txt fájl elutasítva", "bin.txt", b"\x00\x01\x02", "binary_not_supported")

check("is_name_blocked felismeri a 'titok' szót ékezetes fájlnévben is (normalizálva)", is_name_blocked("üzleti_titok_árlista.txt"))
check("is_name_blocked NEM jelzi ártalmatlan fájlnévnél", not is_name_blocked("projekt_jegyzet.txt"))

summary = build_file_summary("minta.txt", "Egy sor szoveg.\nMasodik sor.")
check("build_file_summary tartalmazza a fájlnevet", "minta.txt" in summary)
check("build_file_summary tartalmaz sor/karakter infót", "sor" in summary and "karakter" in summary)

record = build_file_record("jegyzet.txt", "Kedvenc szinem a kek. A projekt neve MF-AI-Zero.".encode("utf-8"))
prompt_ctx = build_file_prompt_context(record)
check("build_file_prompt_context 'User:'/'AI:' natív formátumú", prompt_ctx.startswith("User:") and "AI:" in prompt_ctx)
check("build_file_prompt_context tartalmazza a fájl tartalmának kivonatát", "kek" in prompt_ctx or "MF-AI-Zero" in prompt_ctx)
check("build_file_prompt_context(None) üres string", build_file_prompt_context(None) == "")

candidate = to_knowledge_candidate(record)
check("to_knowledge_candidate JAVASOL egy tudásbázis-formátumú dict-et, de nem ment", isinstance(candidate, dict)
      and candidate.get("title") == "jegyzet.txt" and "content" in candidate)

public_record = public_file_record(record)
check("public_file_record NEM tartalmazza a teljes 'content'-et", "content" not in public_record)
check("public_file_record megtartja a metaadatokat", public_record.get("name") == "jegyzet.txt")


# ---------------------------------------------------------------------------
# 2) guard.py integráció - valódi modellel
# ---------------------------------------------------------------------------
print("\n--- Integrációs teszt: guarded_route_and_respond() active_file-lal, valódi modellel ---")

import torch  # noqa: E402

import config  # noqa: E402
from generate import load_model  # noqa: E402
from guard import guarded_route_and_respond  # noqa: E402

device = torch.device("cpu")
candidate_a_path = os.path.join(config.BASE_DIR, "models", "mf_ai_zero_chat_v0_8b_a.pt")

if os.path.exists(candidate_a_path):
    g_tuple = load_model(device, candidate_a_path)
    i_tuple = load_model(device, os.path.join(config.BASE_DIR, "models", "mf_ai_zero_chat_v0_7c.pt"))
    general_model = (*g_tuple[:3], device, g_tuple[3])
    instruction_model = (*i_tuple[:3], device, i_tuple[3])

    active_file = build_file_record("jegyzet.txt", "Kedvenc szinem a kek. A projekt neve MF-AI-Zero.".encode("utf-8"))

    reply, intent, model_used, sentence_info, guard_info = guarded_route_and_respond(
        general_model, instruction_model, "Mi van a feltöltött fájlban?", temperature=0.6,
        active_file=active_file,
    )
    check("active_file-lal hívva nem dob hibát, választ ad", isinstance(reply, str) and len(reply) > 0)
    check("guard_info tartalmazza a file_used/file_name/file_type/file_size/file_summary_used mezőket", all(
        k in guard_info for k in ("file_used", "file_name", "file_type", "file_size", "file_summary_used")
    ))
    check("guard_info.file_used=True, ha van active_file", guard_info["file_used"] is True)
    check("guard_info.file_name a feltöltött fájl neve", guard_info["file_name"] == "jegyzet.txt")
    check("guard_info.file_type a fájl kiterjesztése", guard_info["file_type"] == ".txt")

    reply2, _, _, _, guard_info2 = guarded_route_and_respond(
        general_model, instruction_model, "Mi van a feltöltött fájlban?", temperature=0.6,
        active_file=None,
    )
    check("active_file=None esetén file_used=False (alvó réteg, ha nincs aktív fájl)",
          guard_info2["file_used"] is False)

    reply3, _, _, _, guard_info3 = guarded_route_and_respond(
        general_model, instruction_model, "Mi van a feltöltött fájlban?", temperature=0.6,
        active_file=active_file, file_context_enabled=False,
    )
    check("file_context_enabled=False esetén file_used=False, még ha van is active_file",
          guard_info3["file_used"] is False)
else:
    print(f"  (kihagyva - nincs candidate A modell: {candidate_a_path})")


# ---------------------------------------------------------------------------
# 3) web/app.py smoke teszt
# ---------------------------------------------------------------------------
print("\n--- web/app.py smoke teszt (/api/files/*, /api/chat file_id-vel) ---")

sys.path.insert(0, WEB_DIR)
print("(web/app.py betöltése, ez eltarthat pár másodpercig)")
import app as webapp  # noqa: E402

with tempfile.TemporaryDirectory() as tmp_dir:
    webapp.cli_args.long_memory_store_path = os.path.join(tmp_dir, "memories.json")
    webapp.cli_args.knowledge_store_path = os.path.join(tmp_dir, "items.json")
    webapp.uploaded_files.clear()
    client = webapp.app.test_client()

    resp_no_file = client.post("/api/files/upload", data={}, content_type="multipart/form-data")
    check("POST /api/files/upload fájl nélkül -> 400", resp_no_file.status_code == 400)

    resp_upload = client.post(
        "/api/files/upload",
        data={"file": (tempfile_bytes := __import__("io").BytesIO(b"Kedvenc szinem a kek."), "notes.txt")},
        content_type="multipart/form-data",
    )
    check("POST /api/files/upload érvényes .txt fájllal -> 200", resp_upload.status_code == 200)
    upload_data = resp_upload.get_json()
    check("a válasz tartalmazza a file rekordot content nélkül", "file" in upload_data and "content" not in upload_data["file"])
    uploaded_id = upload_data["file"]["id"]

    resp_bad_ext = client.post(
        "/api/files/upload",
        data={"file": (__import__("io").BytesIO(b"binaris"), "kep.png")},
        content_type="multipart/form-data",
    )
    check("nem támogatott típusú fájl feltöltése -> 400, kulturált hibaüzenet",
          resp_bad_ext.status_code == 400 and "error" in resp_bad_ext.get_json())

    resp_blocked = client.post(
        "/api/files/upload",
        data={"file": (__import__("io").BytesIO(b"titok"), "secret.txt")},
        content_type="multipart/form-data",
    )
    check("blokkolt fájlnév feltöltése -> 400", resp_blocked.status_code == 400
          and resp_blocked.get_json().get("error_code") == "blocked_filename")

    resp_list = client.get("/api/files")
    check("GET /api/files -> 200, tartalmazza a feltöltött fájlt", resp_list.status_code == 200
          and any(f["id"] == uploaded_id for f in resp_list.get_json()["files"]))
    check("GET /api/files tartalmazza az allowed_extensions/max_file_size mezőket",
          "allowed_extensions" in resp_list.get_json() and "max_file_size" in resp_list.get_json())

    resp_chat_file = client.post("/api/chat", json={
        "message": "Mi van a feltöltött fájlban?", "file_id": uploaded_id,
        "temperature": 0.6, "sentences": 4,
    })
    check("POST /api/chat file_id-vel -> 200", resp_chat_file.status_code == 200)
    chat_data = resp_chat_file.get_json()
    check("indicators.file_context_used=True, ha volt aktív file_id", chat_data["indicators"].get("file_context_used") is True)
    check("indicators.file_name a feltöltött fájl neve", chat_data["indicators"].get("file_name") == "notes.txt")

    resp_chat_no_file = client.post("/api/chat", json={"message": "Hogy vagy?", "temperature": 0.6, "sentences": 4})
    check("POST /api/chat file_id NÉLKÜL -> indicators.file_context_used=False (alvó réteg)",
          resp_chat_no_file.get_json()["indicators"].get("file_context_used") is False)

    resp_clear_one = client.post("/api/files/clear", json={"id": uploaded_id})
    check("POST /api/files/clear (egy fájl id-val) -> 200, removed=True",
          resp_clear_one.status_code == 200 and resp_clear_one.get_json().get("removed") is True)

    resp_list_after = client.get("/api/files")
    check("törlés után a fájl már nincs a listában", not any(
        f["id"] == uploaded_id for f in resp_list_after.get_json()["files"]
    ))

    for name in ("teszt1.txt", "teszt2.txt"):
        client.post("/api/files/upload", data={"file": (__import__("io").BytesIO(b"tartalom"), name)},
                     content_type="multipart/form-data")
    resp_clear_all = client.post("/api/files/clear", json={})
    check("POST /api/files/clear (id nélkül) -> az összes fájlt törli", resp_clear_all.status_code == 200)
    resp_list_empty = client.get("/api/files")
    check("teljes törlés után a lista üres", resp_list_empty.get_json()["files"] == [])

    webapp.uploaded_files.clear()


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
