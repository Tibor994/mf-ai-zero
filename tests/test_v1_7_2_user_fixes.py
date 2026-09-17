"""
MF-AI-Zero - v1.7.2 user-test fixes teszt: "+" gyorsfeltöltés UX + a
determinisztikus fájl-válasz minőségjavítás (src/file_reader.py,
src/guard.py, web/app.py, web/templates/index.html).

Négy rész:
  1. file_reader.is_file_question() - determinisztikus, kulcsszó-alapú
     felismerés: mikor kérdez a user egyértelműen a fájlról.
  2. file_reader.build_file_answer() - a determinisztikus fájl-válasz
     tartalmazza a nevet/típust/méretet/típus-leírást/tartalmi részletet,
     SOSEM tör össze fájlnevet/kiterjesztést (nincs "index. Html"-szerű
     hiba), üres file_record esetén őszinte választ ad.
  3. guard.py integráció valódi modellel: ha aktív fájl + fájl-kérdés,
     a végső válasz PONTOSAN build_file_answer() kimenete (a kis LSTM
     EZEN a körön nem fut/nem befolyásolja a szöveget), guard_info.
     file_answer_used=True; ha NEM fájl-kérdés, a normál (LSTM-alapú)
     válaszadás változatlan marad.
  4. web/app.py smoke teszt: /api/chat indicators.file_answer_used,
     a renderelt főoldal tartalmazza az új "+" gyorsmenü elemeit és az
     alapértelmezett "Nexora Zero" fejlécet, a v1.6/v1.7 fájl API-k
     (upload/blocked-name/edit preview-apply-undo) változatlanul
     működnek.

Futtatás:
    python tests/test_v1_7_2_user_fixes.py
"""

import io
import os
import sys
import tempfile

SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "web")
sys.path.insert(0, SRC_DIR)

from file_reader import (  # noqa: E402
    build_file_answer,
    build_file_record,
    is_file_question,
)

FAILURES = []


def check(label, condition):
    status = "OK" if condition else "FAIL"
    print(f"  [{status}] {label}")
    if not condition:
        FAILURES.append(label)


# ---------------------------------------------------------------------------
# 1) is_file_question() - determinisztikus felismerés
# ---------------------------------------------------------------------------
print("--- file_reader.is_file_question() ---")

POSITIVE_CASES = [
    "Mit tud ez a fájl?",
    "Mit tud ez a fajl?",  # ékezet nélkül is
    "Mi van a feltöltött fájlban?",
    "Miről szól a fájl?",
    "Foglald össze a fájlt!",
    "Mit tartalmaz a fájl?",
    "Milyen fájl ez?",
    "Elemezd a dokumentumot!",
    "Mutasd meg a fájl tartalmát!",
]
for text in POSITIVE_CASES:
    check(f"'{text}' -> fájl-kérdésnek ismerve fel", is_file_question(text))

NEGATIVE_CASES = [
    "Szia, hogy vagy?",
    "Hány éves vagy?",
    "Mit gondolsz erről?",
    "Milyen az idő ma?",
    "Jegyezd meg, hogy szeretem a teát.",
    "Írj 3 mondatot az erőről.",
]
for text in NEGATIVE_CASES:
    check(f"'{text}' -> NEM fájl-kérdés", not is_file_question(text))


# ---------------------------------------------------------------------------
# 2) build_file_answer() - determinisztikus, sose "hallucinál"
# ---------------------------------------------------------------------------
print("\n--- file_reader.build_file_answer() ---")

TYPE_CASES = [
    ("index.html", b"<html><body><h1>Cim</h1></body></html>", ".html", "HTML dokumentum"),
    ("style.css", b"body { color: red; }", ".css", "CSS"),
    ("app.js", b"console.log('hi');", ".js", "JavaScript"),
    ("main.py", b"print('hello')", ".py", "Python"),
    ("data.json", b'{"a": 1}', ".json", "JSON"),
    ("notes.md", b"# Cim\nSzoveg", ".md", "Markdown"),
    ("plain.txt", b"sima szoveg", ".txt", "szöveges"),
]
for filename, content, ext, expect_keyword in TYPE_CASES:
    record = build_file_record(filename, content)
    answer = build_file_answer(record)
    check(f"{filename} válasz tartalmazza a fájlnevet", filename in answer)
    check(f"{filename} válasz tartalmazza a kiterjesztést (\"{ext}\")", ext in answer)
    check(f"{filename} válasz típus-specifikus leírást ad ({expect_keyword})", expect_keyword in answer)
    check(f"{filename} válasz tartalmaz tartalmi részletet", "Tartalmából" in answer or "üresnek" in answer)

empty_record = build_file_record("ures.txt", b"nem ures")
empty_record["content"] = ""
empty_answer = build_file_answer(empty_record)
check("üres tartalmú fájlnál őszintén jelzi, nem hallucinál", "üresnek tűnik" in empty_answer)

none_answer = build_file_answer(None)
check("build_file_answer(None) őszinte, nem dob hibát", "nincs aktív" in none_answer)

# konkrét regressziós eset: a v1.7.2-t megelőzően a response_style
# utófeldolgozás "index.html" -> "index. Html"-lé törte a nevet
html_record = build_file_record("index.html", b"<html></html>")
html_answer = build_file_answer(html_record)
check("'index.html' pontosan megmarad (nincs 'index. Html' törés)",
      "index.html" in html_answer and "index. Html" not in html_answer)


# ---------------------------------------------------------------------------
# 3) guard.py integráció - valódi modellel
# ---------------------------------------------------------------------------
print("\n--- Integrációs teszt: guarded_route_and_respond() determinisztikus fájl-válasszal ---")

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

    active_file = build_file_record(
        "index.html",
        b"<html><body><h1>Nexora Zero demo</h1><p>Ez egy teszt weboldal.</p></body></html>",
    )

    reply, intent, model_used, sentence_info, guard_info = guarded_route_and_respond(
        general_model, instruction_model, "Mit tud ez a fájl?", temperature=0.6,
        active_file=active_file,
    )
    expected = build_file_answer(active_file)
    check("fájl-kérdésnél guard_info.file_answer_used=True", guard_info["file_answer_used"] is True)
    check("fájl-kérdésnél a válasz PONTOSAN a determinisztikus build_file_answer() kimenete "
          "(a kis LSTM nem befolyásolta a szöveget)", reply == expected)
    check("fájl-kérdésnél guard_info.file_used is True is megmarad (v1.6 kompatibilitás)",
          guard_info["file_used"] is True)

    reply2, _, _, _, guard_info2 = guarded_route_and_respond(
        general_model, instruction_model, "Szia, hogy vagy?", temperature=0.6,
        active_file=active_file,
    )
    check("NEM fájl-kérdésnél guard_info.file_answer_used=False (normál LSTM-válasz)",
          guard_info2["file_answer_used"] is False)
    check("NEM fájl-kérdésnél a válasz NEM a determinisztikus sablon", reply2 != build_file_answer(active_file))

    reply3, _, _, _, guard_info3 = guarded_route_and_respond(
        general_model, instruction_model, "Mit tud ez a fájl?", temperature=0.6,
        active_file=None,
    )
    check("fájl-kérdésnél, ha NINCS aktív fájl, file_answer_used=False (dormant, nem hibázik)",
          guard_info3["file_answer_used"] is False)
else:
    print(f"  (kihagyva - nincs candidate A modell: {candidate_a_path})")


# ---------------------------------------------------------------------------
# 4) web/app.py smoke teszt
# ---------------------------------------------------------------------------
print("\n--- web/app.py smoke teszt (indicators.file_answer_used, UI elemek, v1.6/v1.7 regresszió) ---")

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
        data={"file": (io.BytesIO(b"<html><body><h1>Cim</h1></body></html>"), "page.html")},
        content_type="multipart/form-data",
    )
    file_id = resp_upload.get_json()["file"]["id"]
    check("v1.6 upload smoke - HTML fájl feltöltve", resp_upload.status_code == 200)

    resp_chat = client.post("/api/chat", json={
        "message": "Mit tud ez a fájl?", "file_id": file_id, "temperature": 0.6, "sentences": 4,
    })
    check("POST /api/chat fájl-kérdéssel -> 200", resp_chat.status_code == 200)
    chat_data = resp_chat.get_json()
    check("indicators.file_answer_used=True", chat_data["indicators"].get("file_answer_used") is True)
    check("a válasz tartalmazza a fájlnevet ('page.html')", "page.html" in chat_data["reply"])
    check("a válasz tartalmazza a HTML-specifikus leírást", "HTML dokumentum" in chat_data["reply"])

    resp_chat_normal = client.post("/api/chat", json={
        "message": "Szia, hogy vagy?", "file_id": file_id, "temperature": 0.6, "sentences": 4,
    })
    check("nem fájl-kérdésnél indicators.file_answer_used=False",
          resp_chat_normal.get_json()["indicators"].get("file_answer_used") is False)

    # --- v1.6 regresszió: blokkolt/túl nagy/nem támogatott fájl továbbra is elutasítva ---
    resp_blocked = client.post(
        "/api/files/upload",
        data={"file": (io.BytesIO(b"titok"), "secret_kulcs.txt")},
        content_type="multipart/form-data",
    )
    check("v1.6 regresszió - blokkolt fájlnév továbbra is elutasítva",
          resp_blocked.status_code == 400 and resp_blocked.get_json()["error_code"] == "blocked_filename")

    resp_unsupported = client.post(
        "/api/files/upload",
        data={"file": (io.BytesIO(b"binaris"), "kep.png")},
        content_type="multipart/form-data",
    )
    check("v1.6 regresszió - nem támogatott típus továbbra is elutasítva",
          resp_unsupported.status_code == 400 and resp_unsupported.get_json()["error_code"] == "unsupported_type")

    # --- v1.7 regresszió: fájlszerkesztés preview/apply/undo továbbra is működik ---
    resp_preview = client.post("/api/files/edit/preview", json={
        "file_id": file_id, "operation": {"type": "find_replace", "find": "Cim", "replace": "Cím2"},
    })
    check("v1.7 regresszió - edit preview -> 200", resp_preview.status_code == 200)
    plan_id = resp_preview.get_json()["plan"]["id"]

    resp_apply = client.post("/api/files/edit/apply", json={"file_id": file_id, "plan_id": plan_id})
    check("v1.7 regresszió - edit apply -> 200", resp_apply.status_code == 200)

    resp_undo = client.post("/api/files/edit/undo", json={"file_id": file_id})
    check("v1.7 regresszió - edit undo -> 200, visszaállítja az eredetit",
          resp_undo.status_code == 200 and "Cim" in resp_undo.get_json()["file"]["summary"])

    # --- UI: renderelt főoldal tartalmazza az új "+" gyorsmenüt és a Nexora Zero fejlécet ---
    resp_page = client.get("/")
    page_text = resp_page.get_data(as_text=True)
    check("a főoldal tartalmazza a '+' gyorsmenü gombot", 'id="plus-menu-btn"' in page_text)
    check("a főoldal tartalmazza a gyorsmenüt", 'id="plus-menu"' in page_text)
    check("a gyorsmenüben van 'Fájlok' aktív elem", 'id="plus-menu-files"' in page_text and "📎 Fájlok" in page_text)
    check("a gyorsmenüben a Képek/Videók/Bővítmények 'hamarosan'/disabled",
          page_text.count("hamarosan") >= 3 and page_text.count("disabled") >= 3)
    check("a gyors-feltöltési hibaüzenet helye jelen van", 'id="quick-upload-error"' in page_text)
    check("az aktív fájl chip helye jelen van (v1.6/v1.7-ből megmaradt)", 'id="active-file-row"' in page_text)
    check("a régi, részletes Fájlok panel megmaradt haladó nézetnek", 'id="files-panel"' in page_text
          and "Fájlok (részletes)" in page_text)
    check("a fejléc alapból 'Nexora Zero'-t mutat, nem 'MF-AI-ZERO'-t/'v0.6 webes chat'-et",
          "Nexora" in page_text and "Zero" in page_text and "v0.6 webes chat" not in page_text)
    check("a <title> tag VÁLTOZATLANUL 'MF-AI-Zero Chat' marad (brand_name nem változott, csak a fejléc szövege)",
          "<title>MF-AI-Zero Chat</title>" in page_text)

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
