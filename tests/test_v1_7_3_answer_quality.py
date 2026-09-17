"""
MF-AI-Zero - v1.7.3 file-summary + answer-quality stabilizáló kör tesztje
(src/file_reader.py fájltípus-elemzők, src/evaluator.py torz-szó
felismerés, src/guard.py kimeneti minőség-őr).

Öt rész:
  1. file_reader.py fájltípus-elemzők (analyze_html/css/js/python/json/
     markdown) - determinisztikus, reguláris kifejezéses felismerés.
  2. build_file_answer() valódi, tartalom-alapú összefoglalót ad minden
     támogatott típusra (nem csak név/típus/méret), sosem "talál ki"
     olyat, amit nem lát a fájlban.
  3. evaluator.py - torz szó (magánhangzó nélküli token) és ismétlődő
     karakter-sorozat felismerése, ÚJ flag-ek.
  4. guard.py integráció valódi modellel + monkeypatch-elt (mesterségesen
     torzra kényszerített) chat.respond-dal: a kimeneti minőség-őr 1x
     retry-t próbál, majd KONTROLLÁLT fallback-re vált - fájl-alapúra,
     ha van aktív fájl (a nyers modell SOSEM írhatja felül a biztos
     fájl-alapú választ), különben egy kézzel írt, biztos mondatra.
  5. web/app.py smoke teszt: valódi fájl-kérdések ("összefoglalnád ezt a
     fájlt?", "mi ez a html fájl?", "milyen funkciók vannak ebben a js
     fájlban?", "mit csinál ez a python fájl?"), és a v1.6/v1.7/v1.7.2
     regressziók (üres/túl nagy/tiltott/nem támogatott fájl, file editor
     preview/apply/undo, "+" gyorsmenü UI elemek) változatlanok.

Futtatás:
    python tests/test_v1_7_3_answer_quality.py
"""

import io
import os
import sys
import tempfile

SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "web")
sys.path.insert(0, SRC_DIR)

from file_reader import (  # noqa: E402
    analyze_css,
    analyze_html,
    analyze_js,
    analyze_json,
    analyze_markdown,
    analyze_python,
    build_file_answer,
    build_file_record,
    is_file_question,
)
from evaluator import evaluate_reply  # noqa: E402

FAILURES = []


def check(label, condition):
    status = "OK" if condition else "FAIL"
    print(f"  [{status}] {label}")
    if not condition:
        FAILURES.append(label)


# ---------------------------------------------------------------------------
# 1) fájltípus-elemzők
# ---------------------------------------------------------------------------
print("--- file_reader.py fájltípus-elemzők ---")

HTML_SAMPLE = (
    "<html><head><title>Nexora Zero demo oldal</title>"
    "<link rel=\"stylesheet\" href=\"style.css\"><script src=\"app.js\"></script></head>"
    "<body><h1>Udvozlunk</h1><h2>Rolunk</h2><form><button>Kuldes</button></form></body></html>"
)
html_info = analyze_html(HTML_SAMPLE)
check("analyze_html felismeri a title-t", html_info["title"] == "Nexora Zero demo oldal")
check("analyze_html felismeri a címsorokat", "Udvozlunk" in html_info["headings"] and "Rolunk" in html_info["headings"])
check("analyze_html felismeri a CSS-t", "CSS-stílus" in html_info["features"])
check("analyze_html felismeri a JS-t", "JavaScript-kód" in html_info["features"])
check("analyze_html felismeri az űrlapot/gombot", "űrlap" in html_info["features"] and "gomb" in html_info["features"])

CSS_SAMPLE = "body { color: red; background-color: #fff; } .header { font-size: 20px; } @media (max-width: 600px) { .header { font-size: 14px; } }"
css_info = analyze_css(CSS_SAMPLE)
check("analyze_css megszámolja a szabályokat", css_info["selector_count"] == 3)
check("analyze_css felismeri a @media szabályt", css_info["has_media"] is True)
check("analyze_css megszámolja a szín-beállításokat", css_info["color_count"] == 2)

JS_SAMPLE = "function greet(name) { console.log(name); }\nconst handleClick = (e) => { fetch('/api/data'); };\ndocument.addEventListener('click', handleClick);"
js_info = analyze_js(JS_SAMPLE)
check("analyze_js felismeri a függvényeket", "greet" in js_info["functions"] and "handleClick" in js_info["functions"])
check("analyze_js felismeri az eseménykezelőt", "click" in js_info["events"])
check("analyze_js felismeri a fetch API-hívást", "fetch" in js_info["apis"])

PY_SAMPLE = "import os\nfrom flask import Flask\n\nclass Widget:\n    pass\n\ndef main():\n    pass\n\n@app.route('/api/health')\ndef health():\n    pass\n"
py_info = analyze_python(PY_SAMPLE)
check("analyze_python felismeri az osztályt", "Widget" in py_info["classes"])
check("analyze_python felismeri a függvényeket", "main" in py_info["functions"] and "health" in py_info["functions"])
check("analyze_python felismeri a route-ot", "/api/health" in py_info["routes"])
check("analyze_python felismeri az importokat", "os" in py_info["imports"])

json_info_valid = analyze_json('{"name": "Nexora", "version": 1}')
check("analyze_json érvényes objektumot ismer fel", json_info_valid["valid"] and json_info_valid["kind"] == "objektum"
      and set(json_info_valid["keys"]) == {"name", "version"})
json_info_invalid = analyze_json("{ez nem json")
check("analyze_json hibás JSON-t helyesen jelez", json_info_invalid["valid"] is False)

md_info = analyze_markdown("# Cim\n## Alcim\nSzoveg itt.\n")
check("analyze_markdown felismeri a címsorokat", md_info["headings"] == ["Cim", "Alcim"])


# ---------------------------------------------------------------------------
# 2) build_file_answer() - valódi, tartalom-alapú összefoglaló
# ---------------------------------------------------------------------------
print("\n--- build_file_answer() tartalom-alapú összefoglaló ---")

html_rec = build_file_record("index.html", HTML_SAMPLE.encode("utf-8"))
html_answer = build_file_answer(html_rec)
check("HTML válasz megemlíti, hogy weboldal", "weboldal" in html_answer.lower())
check("HTML válasz megemlíti a title-ból sejthető nevet", "Nexora Zero demo oldal" in html_answer)
check("HTML válasz megemlíti a felismert elemeket (CSS/JS/űrlap/gomb)",
      "CSS-stílus" in html_answer and "JavaScript-kód" in html_answer)
check("HTML válasz NEM csak metaadat - tartalmaz strukturális infót is",
      "Felismerhető fő részek" in html_answer or "Tartalmaz:" in html_answer)
check("HTML válasz NEM töri össze a fájlnevet ('index.html' megmarad, nincs 'index. Html')",
      "index.html" in html_answer and "index. Html" not in html_answer)

css_rec = build_file_record("style.css", CSS_SAMPLE.encode("utf-8"))
css_answer = build_file_answer(css_rec)
check("CSS válasz megemlíti a stílusszabályok számát", "3 stílusszabályt" in css_answer)
check("CSS válasz megemlíti a reszponzív szabályt", "Reszponzív" in css_answer)

js_rec = build_file_record("app.js", JS_SAMPLE.encode("utf-8"))
js_answer = build_file_answer(js_rec)
check("JS válasz megemlíti a felismert függvényeket", "greet" in js_answer and "handleClick" in js_answer)
check("JS válasz megemlíti az eseménykezelőt", "click" in js_answer)

py_rec = build_file_record("main.py", PY_SAMPLE.encode("utf-8"))
py_answer = build_file_answer(py_rec)
check("Python válasz megemlíti az osztályt/függvényeket", "Widget" in py_answer and "main" in py_answer)
check("Python válasz megemlíti a webes végpontot", "/api/health" in py_answer)

json_rec = build_file_record("data.json", b'{"name": "Nexora", "version": 1, "active": true}')
json_answer = build_file_answer(json_rec)
check("JSON válasz megemlíti a kulcsokat", "name" in json_answer and "version" in json_answer)

md_rec = build_file_record("notes.md", b"# Cim\n## Alcim\nSzoveg itt.\n")
md_answer = build_file_answer(md_rec)
check("Markdown válasz megemlíti a címsorokat", "Cim" in md_answer and "Alcim" in md_answer)

# üres tartalom - őszinte válasz, nem hallucinál
empty_rec = build_file_record("ures.txt", b"nemures")
empty_rec["content"] = "   "
check("üres tartalmú fájlnál őszinte, nem generál kitalált tartalmat",
      "üresnek tűnik" in build_file_answer(empty_rec))

# olyan HTML, amiben semmi felismerhető nincs - NEM talál ki semmit
minimal_html_rec = build_file_record("min.html", b"<html><body>x</body></html>")
minimal_answer = build_file_answer(minimal_html_rec)
check("minimál HTML-nél nem állít olyat, amit nem lát (nincs title/heading/feature)",
      "Nagyon egyszerű" in minimal_answer)


# ---------------------------------------------------------------------------
# 3) evaluator.py - torz szó / ismétlődő karakter felismerés
# ---------------------------------------------------------------------------
print("\n--- evaluator.py torz-szó felismerés ---")

score_ok, flags_ok = evaluate_reply("kérdés", "Ez egy teljesen rendben lévő magyar válasz.", "general_chat")
check("normál válasznál nincs garbled_token/repeated_char_run flag",
      "garbled_token" not in flags_ok and "repeated_char_run" not in flags_ok)

score_garbled, flags_garbled = evaluate_reply("kérdés", "Ez egy szvmnt torz szó teszt.", "general_chat")
check("magánhangzó nélküli torz szónál garbled_token flag", "garbled_token" in flags_garbled)
check("garbled_token flag csökkenti a pontszámot", score_garbled < 100)

score_rep, flags_rep = evaluate_reply("kérdés", "Ez egy aaaaaaa ismétlődő teszt.", "general_chat")
check("4+ ismétlődő karakternél repeated_char_run flag", "repeated_char_run" in flags_rep)

score_valid_word, flags_valid_word = evaluate_reply("kérdés", "Ez egy hosszabb, de teljesen valós magyar szó.", "general_chat")
check("hosszú, de valódi (magánhangzót tartalmazó) szó NEM triggereli a garbled_token-t",
      "garbled_token" not in flags_valid_word)


# ---------------------------------------------------------------------------
# 4) guard.py integráció - kimeneti minőség-őr (monkeypatch-elt torz válasszal)
# ---------------------------------------------------------------------------
print("\n--- Integrációs teszt: guard.py kimeneti minőség-őr ---")

import torch  # noqa: E402

import chat  # noqa: E402
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

    active_file = build_file_record("index.html", HTML_SAMPLE.encode("utf-8"))

    original_respond = chat.respond
    call_count = {"n": 0}

    def forced_garbled_respond(*args, **kwargs):
        call_count["n"] += 1
        return "Ez egy szvmnt torz valasz mindig."

    try:
        chat.respond = forced_garbled_respond

        reply, intent, model_used, sentence_info, guard_info = guarded_route_and_respond(
            general_model, instruction_model, "Mesélj valamit magadról általánosságban!", temperature=0.6,
            active_file=active_file,
        )
        check("kényszerített torz válasznál (van aktív fájl) guard_triggered=True", guard_info["guard_triggered"] is True)
        check("kényszerített torz válasznál retry_count=1 (1x újrapróbálkozott)", guard_info["retry_count"] == 1)
        check("kényszerített torz válasznál fallback_used=True", guard_info["fallback_used"] is True)
        check("a torz LSTM-szöveg SOSEM jut ki a userhez", "szvmnt" not in reply)
        check("a fallback fájl-alapú (file_answer_used=True), mert van aktív fájl",
              guard_info["file_answer_used"] is True)
        check("a végső válasz PONTOSAN a determinisztikus build_file_answer() kimenete",
              reply == build_file_answer(active_file))
        check("legfeljebb 2x hívta meg a modellt (1 eredeti + 1 retry, nem több)", call_count["n"] == 2)

        call_count["n"] = 0
        reply2, _, _, _, guard_info2 = guarded_route_and_respond(
            general_model, instruction_model, "Mesélj valamit magadról általánosságban!", temperature=0.6,
            active_file=None,
        )
        check("kényszerített torz válasznál (NINCS aktív fájl) fallback_used=True", guard_info2["fallback_used"] is True)
        check("a torz LSTM-szöveg ekkor sem jut ki a userhez", "szvmnt" not in reply2)
        check("aktív fájl nélkül a fallback egy kézzel írt, biztos mondat",
              reply2 == "Erről egyelőre nem tudok ennél pontosabb választ adni.")
    finally:
        chat.respond = original_respond

    # --- v1.7.2 regresszió: is_file_question() esetén továbbra is a kis
    # LSTM-et teljesen megkerüli, nem csak akkor lép be, ha a modell rosszat ad ---
    reply3, _, _, _, guard_info3 = guarded_route_and_respond(
        general_model, instruction_model, "Mit tud ez a fájl?", temperature=0.6,
        active_file=active_file,
    )
    check("v1.7.2 regresszió - egyértelmű fájl-kérdésnél is_file_question út (file_answer_used=True)",
          guard_info3["file_answer_used"] is True)
    check("v1.7.2 regresszió - a válasz pontosan build_file_answer() kimenete",
          reply3 == build_file_answer(active_file))
else:
    print(f"  (kihagyva - nincs candidate A modell: {candidate_a_path})")


# ---------------------------------------------------------------------------
# 5) web/app.py smoke teszt
# ---------------------------------------------------------------------------
print("\n--- web/app.py smoke teszt (valódi fájl-kérdések + regresszió) ---")

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

    resp_html = client.post("/api/files/upload", data={"file": (io.BytesIO(HTML_SAMPLE.encode("utf-8")), "page.html")},
                             content_type="multipart/form-data")
    html_file_id = resp_html.get_json()["file"]["id"]

    resp_js = client.post("/api/files/upload", data={"file": (io.BytesIO(JS_SAMPLE.encode("utf-8")), "app.js")},
                           content_type="multipart/form-data")
    js_file_id = resp_js.get_json()["file"]["id"]

    resp_py = client.post("/api/files/upload", data={"file": (io.BytesIO(PY_SAMPLE.encode("utf-8")), "main.py")},
                           content_type="multipart/form-data")
    py_file_id = resp_py.get_json()["file"]["id"]

    QUESTIONS = [
        (html_file_id, "Mit tud ez a fájl?", "weboldal"),
        (html_file_id, "Összefoglalnád ezt a fájlt?", "weboldal"),
        (html_file_id, "Mi ez a html fájl?", "weboldal"),
        (js_file_id, "Milyen funkciók vannak ebben a js fájlban?", "greet"),
        (py_file_id, "Mit csinál ez a python fájl?", "Widget"),
    ]
    for file_id, question, expect_substring in QUESTIONS:
        resp = client.post("/api/chat", json={"message": question, "file_id": file_id, "temperature": 0.6, "sentences": 4})
        data = resp.get_json()
        check(f"'{question}' -> 200", resp.status_code == 200)
        check(f"'{question}' -> indicators.file_answer_used=True", data["indicators"].get("file_answer_used") is True)
        check(f"'{question}' -> a válasz tényleg tartalom-specifikus ('{expect_substring}' szerepel benne)",
              expect_substring in data["reply"])

    # --- v1.6/v1.7/v1.7.2 regresszió ---
    resp_empty = client.post("/api/files/upload", data={"file": (io.BytesIO(b""), "empty.txt")},
                              content_type="multipart/form-data")
    check("v1.6 regresszió - üres fájl elutasítva", resp_empty.status_code == 400
          and resp_empty.get_json()["error_code"] == "empty_file")

    resp_large = client.post("/api/files/upload", data={"file": (io.BytesIO(b"a" * 250000), "big.txt")},
                              content_type="multipart/form-data")
    check("v1.6 regresszió - túl nagy fájl elutasítva", resp_large.status_code == 413)

    resp_blocked = client.post("/api/files/upload", data={"file": (io.BytesIO(b"titok"), "secret_kulcs.txt")},
                                content_type="multipart/form-data")
    check("v1.6 regresszió - tiltott fájlnév elutasítva", resp_blocked.status_code == 400
          and resp_blocked.get_json()["error_code"] == "blocked_filename")

    resp_unsupported = client.post("/api/files/upload", data={"file": (io.BytesIO(b"x"), "kep.png")},
                                    content_type="multipart/form-data")
    check("v1.6 regresszió - nem támogatott típus elutasítva", resp_unsupported.status_code == 400
          and resp_unsupported.get_json()["error_code"] == "unsupported_type")

    resp_preview = client.post("/api/files/edit/preview", json={
        "file_id": html_file_id, "operation": {"type": "find_replace", "find": "Udvozlunk", "replace": "Szia"},
    })
    check("v1.7 regresszió - edit preview -> 200", resp_preview.status_code == 200)
    plan_id = resp_preview.get_json()["plan"]["id"]

    resp_apply = client.post("/api/files/edit/apply", json={"file_id": html_file_id, "plan_id": plan_id})
    check("v1.7 regresszió - edit apply -> 200", resp_apply.status_code == 200)

    resp_undo = client.post("/api/files/edit/undo", json={"file_id": html_file_id})
    check("v1.7 regresszió - edit undo -> 200, visszaállítja az eredetit",
          resp_undo.status_code == 200 and "Udvozlunk" in resp_undo.get_json()["file"]["summary"])

    resp_active = client.post("/api/chat", json={"message": "Mit tud ez a fájl?", "file_id": html_file_id,
                                                  "temperature": 0.6, "sentences": 4})
    check("v1.7.2 regresszió - indicators.file_name jelen van", resp_active.get_json()["indicators"].get("file_name") == "page.html")

    resp_page = client.get("/")
    page_text = resp_page.get_data(as_text=True)
    check("v1.7.2 regresszió - '+' gyorsmenü UI elemek megmaradtak", 'id="plus-menu-btn"' in page_text
          and 'id="plus-menu-files"' in page_text)
    check("v1.7.2 regresszió - 'Nexora Zero' fejléc megmaradt", "Nexora" in page_text)

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
