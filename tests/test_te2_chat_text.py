"""
MF-AI-Zero - TE-2 teszt: tools/dataset_export_chat_text.py (TE-1 export -> User:/AI: előkészítő szöveg).

FONTOS: ez a teszt NEM tanít modellt. A régi betöltő (src/train_chat.py) függvényeit csak
importálja és a kiírt szövegre hívja (load_text, split_train_val, build_vocab, encode); a
tesztadat mesterséges, ideiglenes mappákban jön létre, a valós data/clean fájlokat csak OLVASSA.

Mit bizonyít:
  - a blokkformátum pontosan a dokumentált (instruction, input új sorban ha nem üres, teljes válasz);
  - a veszteségmentesen át nem adható sorok (többsoros instruction, üres sor, sor eleji
    User:/AI: felirat, CR, vezérlőkarakter, üres mező...) NEM kerülnek a szövegbe, hanem
    okkal, névvel felsorolva visszatartottak; a sor közbeni említés átmegy és jelzést kap;
  - csak érvényes, sikeres TE-1 exportból dolgozik (manifest, ellenőrzőösszegek, maradék fájlok);
  - a kizárás újra érvényesül (kizárt azonosító, jelölt sor, megváltozott lista, megváltozott forrás);
  - kimeneti/visszaolvasásos és régi-betöltős ellenőrzés hibát jelez; hiba után nincs érvényes export;
  - a valós adaton 4494 blokk, 0 visszatartott, a hat kizárt sor és blokkjaik hiányoznak.
Nem bizonyít: tartalmi helyességet, training-ready állapotot, train/val/test felosztást.

Futtatás:
    python -m unittest tests.test_te2_chat_text
    python tests/test_te2_chat_text.py
"""

import glob
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

TOOLS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools")
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, TOOLS_DIR)

import dataset_export_chat_text as te2  # noqa: E402
import dataset_export_train as te1  # noqa: E402

TOOL_PATH = os.path.join(TOOLS_DIR, "dataset_export_chat_text.py")
MARK = "Státusz: teszt; " + te1.EXCLUSION_NOTE_MARKER + ", amíg a felülvizsgálat nem történik meg."

EXPECTED_EXCLUDED = [
    "uncertainty_source_request_0220", "uncertainty_source_request_0602", "uncertainty_source_request_0829",
    "uncertainty_source_request_0849", "uncertainty_source_request_0864", "uncertainty_source_request_0898",
]


def read_bytes(path):
    with open(path, "rb") as f:
        return f.read()


def read_text(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def write_text(path, text):
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)


def file_hashes(paths):
    return {p: hashlib.sha256(read_bytes(p)).hexdigest() for p in paths}


def row(row_id, instruction="Mi a fény?", inp="", output="A fény elektromágneses sugárzás.", marked=False,
        category="simple_qa"):
    return {"id": row_id, "category": category, "instruction": instruction, "input": inp, "output": output,
            "tags": ["magyar"], "difficulty": "easy", "quality_notes": MARK if marked else "rendben", "source": "teszt"}


def write_jsonl(path, rows):
    with open(path, "wb") as f:
        for r in rows:
            f.write((json.dumps(r, ensure_ascii=False) + "\n").encode("utf-8"))


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = self._tmp.name
        self.clean = os.path.join(self.tmp, "clean")
        self.te1_out = os.path.join(self.tmp, "te1")
        self.te2_out = os.path.join(self.tmp, "te2")
        os.makedirs(self.clean)
        self.listfile = os.path.join(self.tmp, "exclusions.txt")
        write_text(self.listfile, "# teszt\nx_excl_0001 | ok | felülvizsgálat\n")

    def tearDown(self):
        self._tmp.cleanup()

    def base_rows(self, extra=()):
        rows = [row("x_a_%04d" % i, "Kérdés %d?" % i, "", "Válasz a(z) %d. kérdésre, ékezetekkel: árvíztűrő." % i)
                for i in range(1, 11)]
        rows.append(row("x_a_0011", "Összegezd a szöveget.", "Első sor.\nMásodik sor.", "Két sor összegzése.",
                        category="summary"))
        rows.append(row("x_excl_0001", "Kizárt kérdés?", "", "Kizárt válasz, amely nem kerülhet be.", marked=True))
        rows.extend(extra)
        return rows

    def make_te1(self, rows=None, run_name="te1run", extra=()):
        rows = rows if rows is not None else self.base_rows(extra)
        self.clean_file = os.path.join(self.clean, "a_clean.jsonl")
        write_jsonl(self.clean_file, rows)
        m = te1.run_export(self.te1_out, input_dir=self.clean, exclusions_path=self.listfile, run_name=run_name)
        self.te1_dir = m["run_dir"]
        return self.te1_dir

    def run_te2(self, te1_dir=None, **kw):
        kw.setdefault("run_name", "te2run")
        return te2.run_te2(te1_dir or self.te1_dir, self.te2_out, **kw)

    def chat_text(self, name="te2run"):
        return read_text(os.path.join(self.te2_out, name, te2.CHAT_FILE))

    def rewrite_manifest(self, mutate, run_dir=None):
        p = os.path.join(run_dir or self.te1_dir, te1.MANIFEST_FILE)
        m = json.loads(read_text(p))
        mutate(m)
        write_text(p, json.dumps(m, ensure_ascii=False, indent=2, sort_keys=True) + "\n")

    def refresh_te1_hashes(self, run_dir=None):
        """A manifest ellenőrzőösszegeit a fájlok jelenlegi állapotához igazítja (ügyes hamisítás szimulálása)."""
        d = run_dir or self.te1_dir

        def mut(m):
            for key, name in (("export_file", te1.EXPORT_FILE), ("index_file", te1.INDEX_FILE)):
                raw = read_bytes(os.path.join(d, name))
                m["outputs"][key]["sha256"] = hashlib.sha256(raw).hexdigest()
        self.rewrite_manifest(mut, d)


class FormatAndRoundTripTests(Base):
    def test_exact_block_format_and_traceability(self):
        files = [os.path.join(self.clean, "a_clean.jsonl")]
        self.make_te1()
        before = file_hashes(files)
        m = self.run_te2()
        self.assertEqual(before, file_hashes(files), "a clean forrás megváltozott")
        text = self.chat_text()
        self.assertTrue(text.startswith("User: Kérdés 1?\nAI: Válasz a(z) 1. kérdésre, ékezetekkel: árvíztűrő.\n\n"))
        # az input az instruction után, új sorban; a többsoros input megmarad
        self.assertIn("User: Összegezd a szöveget.\nElső sor.\nMásodik sor.\nAI: Két sor összegzése.\n\n", text)
        self.assertTrue(text.endswith("AI: Két sor összegzése.\n\n") and not text.endswith("\n\n\n"))
        self.assertNotIn("Kizárt", text)
        self.assertEqual(text.count("\n\n"), 11)                      # 11 blokk, mindegyik után üres sor
        self.assertEqual(m["counts"]["blocks_written"], 11)
        self.assertEqual(m["counts"]["rows_withheld"], 0)
        self.assertTrue(m["counts"]["all_rows_carried"])
        self.assertEqual(m["counts"]["blocks_with_input"], 1)
        self.assertEqual(m["counts"]["blocks_with_multiline_input"], 1)
        idx = read_text(os.path.join(self.te2_out, "te2run", te2.INDEX_FILE)).splitlines()
        self.assertEqual(idx[0].split("\t"), ["block_no", "id", "category", "source_file", "source_line",
                                              "row_sha256", "block_sha256", "block_chars", "flags"])
        self.assertEqual([l.split("\t")[1] for l in idx[1:]],
                         ["x_a_%04d" % i for i in range(1, 12)])
        te1_idx = read_text(os.path.join(self.te1_dir, te1.INDEX_FILE)).splitlines()[1:]
        self.assertEqual([l.split("\t")[3] for l in te1_idx], [l.split("\t")[5] for l in idx[1:]],
                         "a blokk-index sor-sha256-ja egyezik a TE-1 indexszel")
        self.assertNotIn("x_excl_0001", "".join(idx))

    def test_manifest_is_honest_and_no_split_is_created(self):
        self.make_te1()
        m = self.run_te2()
        self.assertEqual(sorted(os.listdir(os.path.join(self.te2_out, "te2run"))),
                         sorted([te2.CHAT_FILE, te2.INDEX_FILE, te2.WITHHELD_FILE, te2.MANIFEST_FILE]))
        mf = json.loads(read_text(os.path.join(self.te2_out, "te2run", te2.MANIFEST_FILE)))
        self.assertEqual(mf["status"], "ok")
        self.assertFalse(mf["training_ready"])
        self.assertFalse(mf["content_verified"])
        self.assertFalse(mf["split_assigned"])
        self.assertIn("NEM train/validation/test felosztás", mf["scope_disclaimer"])
        self.assertEqual(mf["te1_export"]["manifest_sha256"],
                         hashlib.sha256(read_bytes(os.path.join(self.te1_dir, te1.MANIFEST_FILE))).hexdigest())
        self.assertEqual(mf["checks"]["legacy_loader_check"], "performed")
        self.assertEqual(mf["checks"]["clean_source_recheck"], "performed")
        self.assertEqual(mf["exclusion_recheck"]["excluded_ids"], ["x_excl_0001"])
        self.assertEqual(mf["outputs"]["chat_file"]["sha256"],
                         hashlib.sha256(read_bytes(os.path.join(self.te2_out, "te2run", te2.CHAT_FILE))).hexdigest())
        self.assertEqual(mf["outputs"]["chat_file"]["blocks"], 11)
        self.assertEqual(mf["warnings"], [])
        self.assertEqual(m["legacy_loader_check"]["loader_pair_count_user_colon_space"], 11)

    def test_edge_cases_that_are_carried_losslessly(self):
        extras = [
            row("x_e_0001", "Tipp: mi ez?", "User\nAI\nAI 2024", "Kai: 5, tehát semmi különös."),
            row("x_e_0002", "Mit jelent az AI: mesterséges intelligencia?", "", "Az AI: rövidítés. A User: szó itt csak idézet."),
            row("x_e_0003", "Tabulátor\tés szóköz  ", "  behúzott sor\n\tmásik", "Válasz záró szóközzel  "),
            row("x_e_0004", "Emoji és unicode?", "", "Ez őrizze meg: ő, ű, „idézet”, – gondolatjel, 😀."),
            row("x_e_0005", "Többsoros válasz?", "", "Első sor.\nMásodik sor, egyetlen újsorral."),
        ]
        self.make_te1(extra=extras)
        m = self.run_te2()
        text = self.chat_text()
        self.assertEqual(m["counts"]["rows_withheld"], 0)
        self.assertIn("User: Tipp: mi ez?\nUser\nAI\nAI 2024\nAI: Kai: 5, tehát semmi különös.\n\n", text)
        self.assertIn("User: Tabulátor\tés szóköz  \n  behúzott sor\n\tmásik\nAI: Válasz záró szóközzel  \n\n", text)
        self.assertIn("AI: Első sor.\nMásodik sor, egyetlen újsorral.\n\n", text)
        self.assertIn("😀", text)
        self.assertEqual(m["counts"]["blocks_with_inline_role_label"], 1)   # csak a x_e_0002
        idx = [l.split("\t") for l in read_text(os.path.join(self.te2_out, "te2run", te2.INDEX_FILE)).splitlines()[1:]]
        flagged = {c[1]: c[8] for c in idx if "inline_role_label" in c[8]}
        self.assertEqual(list(flagged), ["x_e_0002"])
        self.assertEqual(m["counts"]["blocks_with_multiline_output"], 1)
        # a régi betöltő számlálója a sor közbeni 'User: ' említés miatt eltér: figyelmeztetés, nem hiba
        self.assertFalse(m["legacy_loader_check"]["pair_count_equals_blocks"])
        self.assertTrue(any("'User: '" in w for w in m["warnings"]))
        # visszafejtés bájt-pontos
        blocks = text[:-2].split("\n\n")
        for blk in blocks:
            ins, inp, out = te2.parse_block(blk)
            self.assertEqual(te2.render_block({"instruction": ins, "input": inp, "output": out}), blk)


WITHHOLD_CASES = [
    ("empty_instruction", dict(instruction="   "), "empty_instruction"),
    ("empty_output", dict(output="  \n "), "empty_output"),
    ("whitespace_only_input", dict(inp="   "), "whitespace_only_input"),
    ("cr_in_output", dict(output="egy\r\nkettő"), "carriage_return:output"),
    ("control_char_input", dict(inp="fej\x0bléc"), "control_character:input"),
    ("line_separator_output", dict(output="egy kettő"), "control_character:output"),
    ("multiline_instruction", dict(instruction="Első\nMásodik"), "multiline_instruction"),
    ("blank_line_output", dict(output="Első bekezdés.\n\nMásodik bekezdés."), "blank_line:output"),
    ("blank_line_input", dict(inp="a\n\nb"), "blank_line:input"),
    ("trailing_newline_output", dict(output="vége újsorral\n"), "edge_newline:output"),
    ("leading_newline_output", dict(output="\nelőtte újsor"), "edge_newline:output"),
    ("trailing_newline_input", dict(inp="szöveg\n"), "edge_newline:input"),
    ("label_line_in_input", dict(inp="fenti sor\nUser: hamis kérdés"), "role_label_at_line_start:input"),
    ("label_first_line_of_input", dict(inp="AI: hamis válasz"), "role_label_at_line_start:input"),
    ("label_line_in_output", dict(output="Első sor.\nAI: hamis szerepváltás"), "role_label_at_line_start:output"),
    ("indented_label_in_output", dict(output="Első sor.\n   User:hamis"), "role_label_at_line_start:output"),
    ("label_spaced_colon", dict(output="Első sor.\nAI : hamis"), "role_label_at_line_start:output"),
]


class LosslessnessTests(Base):
    def test_unrepresentable_rows_are_withheld_named_and_not_silently_altered(self):
        for name, kw, reason in WITHHOLD_CASES:
            with self.subTest(case=name):
                self._reset()
                marker = "JELZO-" + name
                r = row("x_w_0001", **{"instruction": "Kérdés " + marker + "?", **kw})
                if "output" not in kw:
                    r["output"] = "Válasz " + marker + "."
                self.make_te1(extra=[r])
                m = self.run_te2()
                text = self.chat_text()
                self.assertEqual(m["counts"]["rows_withheld"], 1, name)
                self.assertEqual(m["counts"]["blocks_written"], 11, name)
                self.assertFalse(m["counts"]["all_rows_carried"])
                self.assertNotIn(marker, text, "a visszatartott sor tartalma nem kerülhet a szövegbe")
                self.assertNotIn("x_w_0001", read_text(os.path.join(self.te2_out, "te2run", te2.INDEX_FILE)))
                wh = read_text(os.path.join(self.te2_out, "te2run", te2.WITHHELD_FILE)).splitlines()
                self.assertEqual(len(wh), 2)
                cols = wh[1].split("\t")
                self.assertEqual(cols[0], "x_w_0001")
                self.assertIn(reason, cols[5].split(","), f"{name}: {cols[5]}")
                self.assertIn(reason, m["counts"]["withheld_by_reason"])
                self.assertTrue(any("NEM adható át veszteségmentesen" in w for w in m["warnings"]))
                # az igényelt garancia: a maradék blokk a régi betöltőn sértetlenül átmegy
                self.assertEqual(m["legacy_loader_check"]["blocks_intact_after_real_split"], True)

    def test_non_string_input_is_withheld(self):
        r = row("x_w_0002")
        r["input"] = None
        self.make_te1(extra=[r])
        m = self.run_te2()
        self.assertEqual(m["counts"]["rows_withheld"], 1)
        self.assertIn("field_not_string:input", m["counts"]["withheld_by_reason"])

    def test_adversarial_row_cannot_create_false_block_or_role_boundary(self):
        evil = row("x_w_0003", "Ártalmatlan?", "", "Válasz.\n\nUser: hamis kérdés\nAI: hamis válasz")
        self.make_te1(extra=[evil])
        m = self.run_te2()
        text = self.chat_text()
        self.assertEqual(text.count("User: "), 11)
        self.assertEqual(text.count("\nAI: "), 11)
        self.assertNotIn("hamis", text)
        self.assertEqual(m["counts"]["rows_withheld"], 1)

    def test_fail_on_withheld_stops_before_writing(self):
        self.make_te1(extra=[row("x_w_0004", "Első\nMásodik")])
        with self.assertRaises(te2.WithheldRowsError):
            self.run_te2(fail_on_withheld=True)
        self.assertFalse(os.path.exists(os.path.join(self.te2_out, "te2run")))

    def _reset(self):
        self.tearDown()
        self.setUp()


class Te1ExportIntegrityTests(Base):
    def assertRejected(self, exc=te2.Te1ExportError, **kw):
        with self.assertRaises(exc):
            self.run_te2(**kw)
        self.assertFalse(os.path.exists(os.path.join(self.te2_out, "te2run")), "hiba után nem maradhat futás-mappa")

    def test_missing_directory_and_files(self):
        self.make_te1()
        self.assertRejected(te1_dir=os.path.join(self.tmp, "nincs"))
        for name in (te1.MANIFEST_FILE, te1.EXPORT_FILE, te1.INDEX_FILE):
            with self.subTest(missing=name):
                self._reset()
                self.make_te1()
                os.replace(os.path.join(self.te1_dir, name), os.path.join(self.te1_dir, name + ".elmozgatva"))
                self.assertRejected()

    def test_failed_or_partial_export_is_refused(self):
        self.make_te1()
        write_text(os.path.join(self.te1_dir, te1.FAILED_FILE), "hiba\n")
        self.assertRejected()
        self._reset()
        self.make_te1()
        write_text(os.path.join(self.te1_dir, te1.EXPORT_FILE + ".partial"), "")
        self.assertRejected()

    def test_manifest_claims_are_checked(self):
        cases = {
            "status": lambda m: m.update(status="failed"),
            "tool": lambda m: m.update(tool="mas/eszkoz.py"),
            "version": lambda m: m.update(tool_version="x-1"),
            "training_ready": lambda m: m.update(training_ready=True),
            "content_verified": lambda m: m.update(content_verified=True),
            "checks_false": lambda m: m["checks"].update(counts_balance=False),
            "missing_counts": lambda m: m.pop("counts"),
            "export_sha": lambda m: m["outputs"]["export_file"].update(sha256="0" * 64),
            "index_sha": lambda m: m["outputs"]["index_file"].update(sha256="f" * 64),
            "rows_exported": lambda m: m["counts"].update(rows_exported=99),
            "unbalanced": lambda m: m["counts"].update(rows_read=100),
            "entries_count": lambda m: m["exclusion_list"].update(entries=[]),
        }
        for name, mut in cases.items():
            with self.subTest(case=name):
                self._reset()
                self.make_te1()
                self.rewrite_manifest(mut)
                self.assertRejected()

    def test_tampered_export_or_index_is_refused(self):
        self.make_te1()
        p = os.path.join(self.te1_dir, te1.EXPORT_FILE)
        write_text(p, read_text(p).replace("Kérdés 1?", "Kérdés X?"))
        self.assertRejected()                                       # sha256 eltér a manifesttől
        self._reset()
        self.make_te1()
        p = os.path.join(self.te1_dir, te1.INDEX_FILE)
        write_text(p, read_text(p) + "x_a_9999\tf\t1\t" + "0" * 64 + "\n")
        self.assertRejected()

    def test_balanced_but_wrong_row_counts_are_refused(self):
        self.make_te1()

        def mut(m):
            m["counts"]["rows_exported"] += 1
            m["counts"]["rows_read"] += 1                              # az egyensúly-ellenőrzés így nem bukik el
        self.rewrite_manifest(mut)
        self.assertRejected()

    def test_consistent_but_wrong_index_is_refused(self):
        self.make_te1()
        p = os.path.join(self.te1_dir, te1.INDEX_FILE)
        lines = read_text(p).splitlines()
        lines[1], lines[2] = lines[2], lines[1]                     # két azonosító felcserélve
        write_text(p, "\n".join(lines) + "\n")
        self.refresh_te1_hashes()                                   # a manifest összegei a hamisított fájlhoz igazítva
        self.assertRejected()

    def test_row_sha_mismatch_in_index_is_refused(self):
        self.make_te1()
        p = os.path.join(self.te1_dir, te1.INDEX_FILE)
        lines = read_text(p).splitlines()
        cols = lines[1].split("\t")
        cols[3] = "0" * 64
        lines[1] = "\t".join(cols)
        write_text(p, "\n".join(lines) + "\n")
        self.refresh_te1_hashes()
        self.assertRejected()

    def _reset(self):
        self.tearDown()
        self.setUp()


class ExclusionRecheckTests(Base):
    def _add_row_consistently(self, obj):
        """Egy sort hamisan a TE-1 exportba tesz úgy, hogy a manifest összegei és darabszámai is egyeznek."""
        d = self.te1_dir
        line = json.dumps(obj, ensure_ascii=False)
        with open(os.path.join(d, te1.EXPORT_FILE), "ab") as f:
            f.write((line + "\n").encode("utf-8"))
        with open(os.path.join(d, te1.INDEX_FILE), "ab") as f:
            f.write((obj["id"] + "\tx\t1\t" + hashlib.sha256(line.encode("utf-8")).hexdigest() + "\n").encode("utf-8"))

        def mut(m):
            m["counts"]["rows_read"] += 1
            m["counts"]["rows_exported"] += 1
            m["outputs"]["export_file"]["rows"] += 1
            m["outputs"]["index_file"]["rows"] += 1
        self.rewrite_manifest(mut)
        self.refresh_te1_hashes()

    def test_excluded_id_in_export_is_caught_even_with_consistent_hashes(self):
        self.make_te1()
        self._add_row_consistently(row("x_excl_0001", marked=True))
        with self.assertRaises(te2.ExclusionCheckError) as ctx:
            self.run_te2()
        self.assertIn("KIZÁRT azonosító", str(ctx.exception))
        self.assertFalse(os.path.exists(os.path.join(self.te2_out, "te2run")))

    def test_marked_row_in_export_is_caught(self):
        self.make_te1()
        self._add_row_consistently(row("x_ujabb_0001", marked=True))
        with self.assertRaises(te2.ExclusionCheckError) as ctx:
            self.run_te2()
        self.assertIn("Kizárás-jelölésű", str(ctx.exception))

    def test_list_changed_after_te1_export_means_stale_export(self):
        self.make_te1()
        with open(self.listfile, "a", encoding="utf-8") as f:
            f.write("x_a_0003 | ok | felülvizsgálat\n")
        with self.assertRaises(te2.ExclusionCheckError) as ctx:
            self.run_te2()
        self.assertIn("elavult export", str(ctx.exception))

    def test_list_entry_removed_after_te1_export_is_caught(self):
        self.make_te1()
        write_text(self.listfile, "# üres lett\n")
        with self.assertRaises(te2.ExclusionCheckError):
            self.run_te2()

    def test_list_missing_or_malformed_is_caught(self):
        self.make_te1()
        os.replace(self.listfile, self.listfile + ".x")
        with self.assertRaises(te2.ExclusionCheckError):
            self.run_te2()
        write_text(self.listfile, "csak egy mező\n")
        with self.assertRaises(te2.ExclusionCheckError):
            self.run_te2()

    def test_source_changed_after_te1_export_is_caught_unless_recheck_is_explicitly_skipped(self):
        self.make_te1()
        with open(self.clean_file, "ab") as f:
            f.write((json.dumps(row("x_a_0099"), ensure_ascii=False) + "\n").encode("utf-8"))
        with self.assertRaises(te2.ExclusionCheckError):
            self.run_te2()
        m = self.run_te2(clean_recheck=False, run_name="skipped")
        self.assertEqual(m["checks"]["clean_source_recheck"], "skipped")
        self.assertEqual(m["checks"]["excluded_blocks_absent_from_output"], "skipped")
        self.assertTrue(any("NEM futott le" in w for w in m["warnings"]))
        self.assertFalse(m["training_ready"])

    def test_source_deleted_after_te1_export_is_caught(self):
        self.make_te1()
        os.replace(self.clean_file, self.clean_file + ".x")
        with self.assertRaises(te2.ExclusionCheckError):
            self.run_te2()

    def test_excluded_row_source_line_mismatch_is_caught(self):
        self.make_te1()

        def mut(m):
            m["exclusion_list"]["entries"][0]["row_sha256"] = "0" * 64
        self.rewrite_manifest(mut)
        with self.assertRaises(te2.ExclusionCheckError) as ctx:
            self.run_te2()
        self.assertIn("forrássora", str(ctx.exception))


class OutputPathTests(Base):
    def test_protected_and_bad_paths(self):
        self.make_te1()
        for name in ("clean", "raw", "rejected"):
            with self.subTest(name=name):
                with self.assertRaises(te2.OutputPathError):
                    te2.run_te2(self.te1_dir, os.path.join(REPO_ROOT, "data", name, "te2"), run_name="r")
                self.assertFalse(os.path.exists(os.path.join(REPO_ROOT, "data", name, "te2")))
        with self.assertRaises(te2.OutputPathError):
            te2.run_te2(self.te1_dir, os.path.join(self.te1_dir, "belul"), run_name="r")
        with self.assertRaises(te2.OutputPathError):
            self.run_te2(run_name="../kifelé")

    def test_no_overwrite(self):
        self.make_te1()
        self.run_te2()
        with self.assertRaises(te2.OutputPathError):
            self.run_te2()


class VerificationTests(Base):
    def test_corrupted_rendering_is_caught_by_roundtrip(self):
        self.make_te1()
        real = te2.render_block

        def corrupt(obj):
            return real(obj)[:-1] if obj["id"] == "x_a_0003" else real(obj)

        with mock.patch.object(te2, "render_block", corrupt):
            with self.assertRaises(te2.VerificationError):
                self.run_te2()
        d = os.path.join(self.te2_out, "te2run")
        self.assertTrue(os.path.exists(os.path.join(d, te2.FAILED_FILE)))
        self.assertFalse(os.path.exists(os.path.join(d, te2.CHAT_FILE)), "hibás export nem kaphat végleges nevet")
        self.assertFalse(os.path.exists(os.path.join(d, te2.MANIFEST_FILE)))
        self.assertTrue(os.path.exists(os.path.join(d, te2.CHAT_FILE + ".partial")))

    def test_excluded_block_in_output_is_caught(self):
        self.make_te1()
        real = te2.check_exclusions

        def sneaky(manifest, rows, exclusions_path=None, clean_recheck=True):
            source, live, rc = real(manifest, rows, exclusions_path, clean_recheck)
            # a "kizárt" sor forrásaként egy exportált sor szerepel -> a blokkja ott van a kimenetben
            source["x_excl_0001"] = rows[0]["line_bytes"]
            return source, live, rc

        with mock.patch.object(te2, "check_exclusions", sneaky):
            with self.assertRaises(te2.VerificationError) as ctx:
                self.run_te2()
        self.assertIn("KIZÁRT", str(ctx.exception))

    def test_legacy_loader_detects_block_merge_or_split(self):
        p = os.path.join(self.tmp, "rossz.txt")
        blocks = ["User: a\nAI: b", "User: c\nAI: d"]
        write_text(p, "User: a\nAI: b\n\n\nUser: c\nAI: d\n\n")      # három újsor: a betöltő felosztása eltér
        with self.assertRaises(te2.VerificationError):
            te2.legacy_loader_check(p, read_text(p), blocks)

    def test_legacy_check_can_be_skipped_only_explicitly_and_is_recorded(self):
        self.make_te1()
        m = self.run_te2(legacy_check=False)
        self.assertEqual(m["checks"]["legacy_loader_check"], "skipped")
        self.assertFalse(m["legacy_loader_check"]["performed"])
        self.assertTrue(any("kompatibilitás-ellenőrzés NEM futott le" in w for w in m["warnings"]))
        self.assertFalse(m["training_ready"])


class CliTests(Base):
    def cli(self, *args):
        env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
        return subprocess.run([sys.executable, TOOL_PATH, *args], capture_output=True, text=True,
                              encoding="utf-8", env=env)

    def test_success_and_exit_codes(self):
        self.make_te1()
        r = self.cli("--te1-export", self.te1_dir, "--out-dir", self.te2_out, "--run-name", "c1")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("blokk: 11", r.stdout)
        self.assertIn("NEM train/validation/test felosztás", r.stdout)
        r = self.cli("--te1-export", os.path.join(self.tmp, "nincs"), "--out-dir", self.te2_out)
        self.assertEqual(r.returncode, te2.CODE_INPUT)
        r = self.cli("--te1-export", self.te1_dir, "--out-dir", os.path.join(self.te1_dir, "x"))
        self.assertEqual(r.returncode, te2.CODE_OUTPUT)
        with open(self.listfile, "a", encoding="utf-8") as f:
            f.write("x_a_0003 | ok | felül\n")
        r = self.cli("--te1-export", self.te1_dir, "--out-dir", self.te2_out, "--run-name", "c2")
        self.assertEqual(r.returncode, te2.CODE_EXCLUSION)
        self.assertIn("elavult export", r.stderr)

    def test_fail_on_withheld_exit_code(self):
        self.make_te1(extra=[row("x_w_0001", "Első\nMásodik")])
        r = self.cli("--te1-export", self.te1_dir, "--out-dir", self.te2_out, "--fail-on-withheld")
        self.assertEqual(r.returncode, te2.CODE_WITHHELD)

    def test_no_switch_can_turn_the_exclusion_off(self):
        self.make_te1()
        for flag in ("--no-exclusions", "--skip-exclusions", "--ignore-exclusions", "--split"):
            with self.subTest(flag=flag):
                r = self.cli("--te1-export", self.te1_dir, "--out-dir", self.te2_out, flag)
                self.assertEqual(r.returncode, 2)
                self.assertIn("unrecognized", r.stderr)
        self.assertFalse(os.path.exists(self.te2_out))


@unittest.skipUnless(os.path.isdir(os.path.join(REPO_ROOT, "data", "clean")), "nincs data/clean")
class RealDataAcceptanceTests(unittest.TestCase):
    """Valós clean adat -> TE-1 -> TE-2. Csak OLVAS, kimenet ideiglenes mappába."""

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.clean_files = sorted(glob.glob(os.path.join(REPO_ROOT, "data", "clean", "*.jsonl")))
        cls.before = file_hashes(cls.clean_files)
        m1 = te1.run_export(os.path.join(cls._tmp.name, "te1"), run_name="real1")
        cls.te1_dir = m1["run_dir"]
        cls.m2 = te2.run_te2(cls.te1_dir, os.path.join(cls._tmp.name, "te2"), run_name="real2")
        cls.run_dir = cls.m2["run_dir"]

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_counts_and_no_withheld_rows(self):
        c = self.m2["counts"]
        self.assertEqual((c["rows_in"], c["blocks_written"], c["rows_withheld"]), (4494, 4494, 0))
        self.assertTrue(c["all_rows_carried"])
        self.assertEqual(c["blocks_by_category"], {"explanation": 1000, "noisy_input": 500, "simple_qa": 1000,
                                                   "step_by_step": 500, "summary": 500,
                                                   "uncertainty_source_request": 994})
        self.assertEqual(self.m2["warnings"], [])

    def test_independent_recount_of_the_text(self):
        text = read_text(os.path.join(self.run_dir, te2.CHAT_FILE))
        self.assertEqual(text.count("\n\n"), 4494, "pontosan blokkonként egy üres sor: nincs üres sor a tartalomban")
        self.assertEqual(text.count("User: "), 4494)
        self.assertEqual(text.count("\nAI: "), 4494)
        self.assertTrue(text.endswith("\n\n") and not text.endswith("\n\n\n"))
        self.assertNotIn("\r", text)
        n_input = n_multi = 0
        for f in self.clean_files:
            for line in read_bytes(f).replace(b"\r\n", b"\n").split(b"\n"):
                if line.strip():
                    o = json.loads(line.decode("utf-8"))
                    if o["id"] in EXPECTED_EXCLUDED:
                        continue
                    if o["input"] != "":
                        n_input += 1
                        n_multi += "\n" in o["input"]
        self.assertEqual((self.m2["counts"]["blocks_with_input"], self.m2["counts"]["blocks_with_multiline_input"]),
                         (n_input, n_multi))

    def test_six_excluded_rows_and_their_blocks_are_absent(self):
        text = read_text(os.path.join(self.run_dir, te2.CHAT_FILE))
        index_ids = [l.split("\t")[1] for l in
                     read_text(os.path.join(self.run_dir, te2.INDEX_FILE)).splitlines()[1:]]
        te1_ids = [l.split("\t")[0] for l in read_text(os.path.join(self.te1_dir, te1.INDEX_FILE)).splitlines()[1:]]
        self.assertEqual(index_ids, te1_ids)
        self.assertEqual(len(set(index_ids)), 4494)
        found = 0
        for f in self.clean_files:
            for line in read_bytes(f).replace(b"\r\n", b"\n").split(b"\n"):
                if not line.strip():
                    continue
                o = json.loads(line.decode("utf-8"))
                if o["id"] in EXPECTED_EXCLUDED:
                    found += 1
                    self.assertNotIn(o["id"], index_ids)
                    block = "User: " + o["instruction"] + ("\n" + o["input"] if o["input"] else "") + "\nAI: " + o["output"]
                    self.assertNotIn(block, text, o["id"])
        self.assertEqual(found, 6)

    def test_legacy_loader_processed_the_file_without_training(self):
        lc = self.m2["legacy_loader_check"]
        self.assertTrue(lc["performed"])
        self.assertTrue(lc["blocks_intact_after_real_split"])
        self.assertTrue(lc["all_characters_encodable"])
        self.assertTrue(lc["pair_count_equals_blocks"])
        self.assertEqual(lc["loader_pair_count_user_colon_space"], 4494)
        self.assertEqual(lc["diagnostic_split_train_blocks"] + lc["diagnostic_split_val_blocks"], 4494)

    def test_output_is_only_preparatory_and_sources_untouched(self):
        self.assertEqual(sorted(os.listdir(self.run_dir)),
                         sorted([te2.CHAT_FILE, te2.INDEX_FILE, te2.WITHHELD_FILE, te2.MANIFEST_FILE]))
        self.assertFalse(self.m2["training_ready"])
        self.assertFalse(self.m2["content_verified"])
        self.assertFalse(self.m2["split_assigned"])
        self.assertEqual(self.before, file_hashes(self.clean_files), "a clean fájlok megváltoztak")


if __name__ == "__main__":
    unittest.main(verbosity=2)
