"""
MF-AI-Zero - TE-1 teszt: tools/dataset_export_train.py (kizárás-érvényesítő clean-export).

FONTOS: ez a teszt NEM tanít, NEM generál adatot, és a data/clean fájlokat csak OLVASSA
(a valós-adatos részekben a forrásfájlok sha256-ját a futás előtt és után is összeveti).
Az export kimenete mindig ideiglenes mappába kerül.

Mit bizonyít:
  - a listán szereplő sorok kimaradnak, az engedélyezettek megmaradnak (bájt-hűen);
  - a kizárt sorok a clean fájlokban megmaradnak (a forrás változatlan);
  - hiányzó/üres/hibás/duplikált/nem egyértelmű/elgépelt kizárási lista, hiányos lista
    (kizárás-jelölésű sor a listán kívül), hibás forrás- vagy kimeneti útvonal, kimenetbe
    szivárgó kizárt sor, futás közben módosuló forrás: egyértelmű hibával megáll;
  - a valós adaton pontosan a hat kizárt sor marad ki, 4494 sor exportálódik.
Nem bizonyít: tartalmi helyességet, training-ready állapotot.

Futtatás:
    python -m unittest tests.test_te1_dataset_export
    python tests/test_te1_dataset_export.py
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

import dataset_export_train as te1  # noqa: E402

TOOL_PATH = os.path.join(TOOLS_DIR, "dataset_export_train.py")
MARK = "Státusz (audit 2): teszt; " + te1.EXCLUSION_NOTE_MARKER + ", amíg a felülvizsgálat nem történik meg."

# a valós adaton kizárt hat sor - a lista szándékos módosítása esetén EZT is tudatosan frissíteni kell
EXPECTED_EXCLUDED = [
    "uncertainty_source_request_0220",
    "uncertainty_source_request_0602",
    "uncertainty_source_request_0829",
    "uncertainty_source_request_0849",
    "uncertainty_source_request_0864",
    "uncertainty_source_request_0898",
]


def row(row_id, marked=False, category="simple_qa", text="Ékezetes próba: árvíztűrő tükörfúrógép"):
    return {"id": row_id, "category": category, "instruction": "Kérdés " + row_id, "input": "",
            "output": text + " " + row_id, "tags": ["magyar"], "difficulty": "easy",
            "quality_notes": MARK if marked else "rendben", "source": "teszt"}


def write_jsonl(path, rows, eol="\n", trailing=True):
    lines = [json.dumps(r, ensure_ascii=False) for r in rows]
    data = eol.join(lines) + (eol if trailing else "")
    with open(path, "wb") as f:
        f.write(data.encode("utf-8"))


def read_bytes(path):
    with open(path, "rb") as f:
        return f.read()


def read_text(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def file_hashes(paths):
    return {p: hashlib.sha256(read_bytes(p)).hexdigest() for p in paths}


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = self._tmp.name
        self.clean = os.path.join(self.tmp, "clean")
        self.out = os.path.join(self.tmp, "out")
        os.makedirs(self.clean)
        self.listfile = os.path.join(self.tmp, "exclusions.txt")

    def tearDown(self):
        self._tmp.cleanup()

    def corpus(self):
        write_jsonl(os.path.join(self.clean, "a_clean.jsonl"),
                    [row("pkg_a_0001"), row("pkg_a_0002", marked=True), row("pkg_a_0003")])
        write_jsonl(os.path.join(self.clean, "b_clean.jsonl"),
                    [row("pkg_b_0001", category="summary"), row("pkg_b_0002", marked=True, category="summary"),
                     row("pkg_b_0003", category="summary")], eol="\r\n")
        return sorted(glob.glob(os.path.join(self.clean, "*.jsonl")))

    def write_list(self, lines):
        with open(self.listfile, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(lines) + "\n")

    def good_list(self):
        self.write_list(["# megjegyzés", "", "pkg_a_0002 | jogi állítás | jogi átnézés",
                         "pkg_b_0002 | forrás hiányzik | forrás megnyitása"])

    def run_export(self, **kw):
        kw.setdefault("input_dir", self.clean)
        kw.setdefault("exclusions_path", self.listfile)
        kw.setdefault("run_name", "run1")
        return te1.run_export(self.out, **kw)

    def read_out(self, name="run1", fn=te1.EXPORT_FILE):
        return read_bytes(os.path.join(self.out, name, fn))


class HappyPathTests(Base):
    def test_excluded_rows_leave_allowed_rows_stay_and_sources_untouched(self):
        files = self.corpus()
        self.good_list()
        before = file_hashes(files)
        m = self.run_export()
        self.assertEqual(before, file_hashes(files), "a forrásfájlok megváltoztak")
        self.assertEqual(m["counts"]["rows_read"], 6)
        self.assertEqual(m["counts"]["rows_excluded"], 2)
        self.assertEqual(m["counts"]["rows_exported"], 4)
        out_ids = [json.loads(l)["id"] for l in self.read_out().decode("utf-8").splitlines()]
        self.assertEqual(out_ids, ["pkg_a_0001", "pkg_a_0003", "pkg_b_0001", "pkg_b_0003"])
        self.assertNotIn("pkg_a_0002", out_ids)
        self.assertNotIn("pkg_b_0002", out_ids)
        # a kizárt sor a clean fájlban megmaradt
        self.assertIn(b"pkg_a_0002", read_bytes(files[0]))
        self.assertIn(b"pkg_b_0002", read_bytes(files[1]))

    def test_export_lines_are_byte_faithful_including_crlf_source(self):
        files = self.corpus()
        self.good_list()
        self.run_export()
        src_lines = []
        for f in files:
            for l in read_bytes(f).replace(b"\r\n", b"\n").split(b"\n"):
                if l and b"_0002" not in l:
                    src_lines.append(l)
        out_lines = [l for l in self.read_out().split(b"\n") if l]
        self.assertEqual(out_lines, src_lines)
        self.assertNotIn(b"\r", self.read_out())
        self.assertIn("árvíztűrő".encode("utf-8"), self.read_out())

    def test_manifest_is_traceable_and_honest(self):
        files = self.corpus()
        self.good_list()
        self.run_export()
        m = json.loads(read_text(os.path.join(self.out, "run1", te1.MANIFEST_FILE)))
        self.assertEqual(m["status"], "ok")
        self.assertFalse(m["content_verified"])
        self.assertFalse(m["training_ready"])
        self.assertIn("NEM tartalmi ellenőrzés", m["scope_disclaimer"])
        self.assertEqual({i["path"].split("/")[-1] for i in m["input_files"]}, {"a_clean.jsonl", "b_clean.jsonl"})
        by = {i["path"].split("/")[-1]: i for i in m["input_files"]}
        self.assertEqual(by["a_clean.jsonl"]["rows_read"], 3)
        self.assertEqual(by["a_clean.jsonl"]["excluded_ids"], ["pkg_a_0002"])
        self.assertEqual(by["b_clean.jsonl"]["crlf_lines"], 3)
        self.assertEqual(m["counts"]["exported_by_category"], {"simple_qa": 2, "summary": 2})
        self.assertEqual(m["counts"]["excluded_by_category"], {"simple_qa": 1, "summary": 1})
        ex = {e["id"]: e for e in m["exclusion_list"]["entries"]}
        self.assertEqual(set(ex), {"pkg_a_0002", "pkg_b_0002"})
        self.assertEqual(ex["pkg_a_0002"]["source_line"], 2)
        self.assertEqual(ex["pkg_a_0002"]["reason"], "jogi állítás")
        self.assertEqual(len(ex["pkg_a_0002"]["row_sha256"]), 64)
        self.assertEqual(m["outputs"]["export_file"]["sha256"],
                         hashlib.sha256(self.read_out()).hexdigest())
        self.assertTrue(all(m["checks"].values()))
        idx = self.read_out(fn=te1.INDEX_FILE).decode("utf-8").splitlines()
        self.assertEqual(len(idx), 1 + 4)
        self.assertEqual(idx[0].split("\t"), ["id", "source_file", "source_line", "row_sha256"])

    def test_listed_row_without_marker_is_only_a_warning(self):
        self.corpus()
        self.write_list(["pkg_a_0002 | ok | felülvizsgálat", "pkg_b_0002 | ok | felülvizsgálat",
                         "pkg_a_0001 | ok | felülvizsgálat"])
        m = self.run_export()
        self.assertEqual(m["counts"]["rows_excluded"], 3)
        self.assertEqual(len(m["warnings"]), 1)
        self.assertIn("pkg_a_0001", m["warnings"][0])

    def test_second_run_never_overwrites(self):
        self.corpus()
        self.good_list()
        self.run_export()
        with self.assertRaises(te1.OutputPathError):
            self.run_export()


class ExclusionListErrorTests(Base):
    def assertExclusionError(self, **kw):
        self.corpus()
        with self.assertRaises(te1.ExclusionListError):
            self.run_export(**kw)
        self.assertFalse(os.path.exists(os.path.join(self.out, "run1")), "hiba után nem maradhat futás-mappa")

    def test_missing_list(self):
        self.assertExclusionError(exclusions_path=os.path.join(self.tmp, "nincs.txt"))

    def test_empty_list_stops(self):
        self.write_list(["# csak megjegyzés", ""])
        self.assertExclusionError()

    def test_empty_list_stops_even_without_marked_rows(self):
        # jelölés nélküli corpus: itt csak az üres-lista szabály állhat az export útjába
        write_jsonl(os.path.join(self.clean, "a_clean.jsonl"), [row("pkg_a_0001"), row("pkg_a_0003")])
        self.write_list(["# üres", ""])
        with self.assertRaises(te1.ExclusionListError) as ctx:
            self.run_export()
        self.assertIn("nem tartalmaz egyetlen bejegyzést sem", str(ctx.exception))
        self.assertFalse(os.path.exists(os.path.join(self.out, "run1")))

    def test_malformed_lines(self):
        for bad in ["pkg_a_0002", "pkg_a_0002 | csak ok", "pkg_a_0002|ok|felül", "pkg_a_0002 |  | felül",
                    "pkg_a_0002 | ok |  "]:
            with self.subTest(line=bad):
                self.write_list([bad, "pkg_b_0002 | ok | felül"])
                self.assertExclusionError()
                self._reset()

    def test_ambiguous_or_unsafe_ids(self):
        for bad in ["pkg_a_*", "pkg_a", "PKG_A_0002", "pkg a 0002", "pkg_a_0002-0003", "pkg_a_2", "pkg_a_0002;"]:
            with self.subTest(id=bad):
                self.write_list([bad + " | ok | felül", "pkg_b_0002 | ok | felül"])
                self.assertExclusionError()
                self._reset()

    def test_duplicate_id_in_list(self):
        self.write_list(["pkg_a_0002 | ok | felül", "pkg_a_0002 | ok | felül", "pkg_b_0002 | ok | felül"])
        self.assertExclusionError()

    def test_typo_id_not_in_corpus(self):
        self.write_list(["pkg_a_0002 | ok | felül", "pkg_b_0002 | ok | felül", "pkg_a_0099 | ok | felül"])
        self.assertExclusionError()

    def test_id_ambiguous_in_corpus(self):
        self.corpus()
        write_jsonl(os.path.join(self.clean, "c_clean.jsonl"), [row("pkg_a_0002", marked=True)])
        self.good_list()
        with self.assertRaises(te1.ExclusionListError) as ctx:
            self.run_export()
        self.assertIn("Nem egyértelmű", str(ctx.exception))

    def test_marked_row_missing_from_list_cannot_be_unexcluded_silently(self):
        self.write_list(["pkg_a_0002 | ok | felül"])      # pkg_b_0002 kimaradt a listáról
        self.corpus()
        with self.assertRaises(te1.ExclusionListError) as ctx:
            self.run_export()
        self.assertIn("pkg_b_0002", str(ctx.exception))
        self.assertIn("NINCS a kizárási listán", str(ctx.exception))

    def test_empty_list_bypass_flag_is_explicit_and_does_not_hide_marked_rows(self):
        self.write_list(["# üres"])
        self.corpus()                                        # a corpusban jelölt sorok vannak
        with self.assertRaises(te1.ExclusionListError):
            self.run_export(allow_empty=True)
        self.tearDown()
        self.setUp()
        write_jsonl(os.path.join(self.clean, "a_clean.jsonl"), [row("pkg_a_0001"), row("pkg_a_0003")])
        self.write_list(["# üres"])
        m = self.run_export(allow_empty=True)
        self.assertTrue(m["exclusion_list"]["allow_empty"])
        self.assertEqual(m["counts"]["rows_excluded"], 0)

    def _reset(self):
        self.tearDown()
        self.setUp()


class SourceAndOutputErrorTests(Base):
    def test_non_clean_directory_refused(self):
        raw = os.path.join(self.tmp, "raw")
        os.makedirs(raw)
        write_jsonl(os.path.join(raw, "x_raw.jsonl"), [row("pkg_a_0001")])
        self.write_list(["pkg_a_0001 | ok | felül"])
        with self.assertRaises(te1.SourceDataError):
            te1.run_export(self.out, input_dir=raw, exclusions_path=self.listfile, run_name="r")

    def test_invalid_json_line_reports_file_and_line(self):
        self.corpus()
        with open(os.path.join(self.clean, "a_clean.jsonl"), "ab") as f:
            f.write(b"{ez nem json}\n")
        self.good_list()
        with self.assertRaises(te1.SourceDataError) as ctx:
            self.run_export()
        self.assertIn("a_clean.jsonl:4", str(ctx.exception))

    def test_duplicate_non_excluded_id_stops(self):
        self.corpus()
        write_jsonl(os.path.join(self.clean, "c_clean.jsonl"), [row("pkg_a_0001")])
        self.good_list()
        with self.assertRaises(te1.SourceDataError):
            self.run_export()

    def test_out_dir_inside_input_dir_refused(self):
        self.corpus()
        self.good_list()
        with self.assertRaises(te1.OutputPathError):
            te1.run_export(os.path.join(self.clean, "export"), input_dir=self.clean,
                           exclusions_path=self.listfile, run_name="r")

    def test_out_dir_in_protected_repo_data_refused(self):
        self.corpus()
        self.good_list()
        for name in ("clean", "raw", "rejected"):
            with self.subTest(name=name):
                with self.assertRaises(te1.OutputPathError):
                    te1.run_export(os.path.join(REPO_ROOT, "data", name, "te1"), input_dir=self.clean,
                                   exclusions_path=self.listfile, run_name="r")
                self.assertFalse(os.path.exists(os.path.join(REPO_ROOT, "data", name, "te1")))

    def test_invalid_run_name_refused(self):
        self.corpus()
        self.good_list()
        with self.assertRaises(te1.OutputPathError):
            self.run_export(run_name="../kifelé")


class VerificationTests(Base):
    def test_leaking_excluded_row_is_caught_by_output_reread(self):
        files = self.corpus()
        self.good_list()
        real_filter = te1.filter_rows

        def leaky(rows, entries):
            kept, excluded = real_filter(rows, entries)
            return kept + excluded[:1], excluded          # egy kizárt sor "szivárog" a kimenetbe

        with mock.patch.object(te1, "filter_rows", leaky):
            with self.assertRaises(te1.VerificationError) as ctx:
                self.run_export()
        self.assertIn("KIZÁRT azonosító", str(ctx.exception))
        run_dir = os.path.join(self.out, "run1")
        self.assertTrue(os.path.exists(os.path.join(run_dir, te1.FAILED_FILE)))
        self.assertFalse(os.path.exists(os.path.join(run_dir, te1.MANIFEST_FILE)), "hibás exporthoz nem lehet manifest")
        self.assertFalse(os.path.exists(os.path.join(run_dir, te1.EXPORT_FILE)), "hibás export nem kaphat végleges nevet")
        self.assertTrue(os.path.exists(os.path.join(run_dir, te1.EXPORT_FILE + ".partial")))

    def test_leak_with_balanced_counts_is_still_caught(self):
        self.corpus()
        self.good_list()
        real_filter = te1.filter_rows

        def swapped(rows, entries):
            kept, excluded = real_filter(rows, entries)
            # egy engedélyezett sor "kizártnak", egy kizárt sor "engedettnek" látszik: az összeg egyezik
            return kept[:-1] + excluded[:1], excluded[1:] + kept[-1:]

        with mock.patch.object(te1, "filter_rows", swapped):
            with self.assertRaises(te1.VerificationError) as ctx:
                self.run_export()
        self.assertIn("KIZÁRT azonosító", str(ctx.exception))
        self.assertNotIn("nem egyeznek", str(ctx.exception))

    def test_unfiltered_export_is_caught(self):
        self.corpus()
        self.good_list()
        with mock.patch.object(te1, "filter_rows", lambda rows, entries: (list(rows), [])):
            with self.assertRaises(te1.VerificationError):
                self.run_export()

    def test_source_modified_during_run_is_caught(self):
        files = self.corpus()
        self.good_list()
        real_write = te1.write_outputs

        def tampering(kept, run_dir):
            with open(files[0], "ab") as f:
                f.write(b"\n")
            return real_write(kept, run_dir)

        with mock.patch.object(te1, "write_outputs", tampering):
            with self.assertRaises(te1.VerificationError) as ctx:
                self.run_export()
        self.assertIn("megváltoztak", str(ctx.exception))

    def test_output_line_differing_from_source_is_caught(self):
        self.corpus()
        self.good_list()
        real_write = te1.write_outputs

        def corrupting(kept, run_dir):
            export_p, index_p = real_write(kept, run_dir)
            data = read_bytes(export_p).replace("Kérdés".encode("utf-8"), "Kérdes".encode("utf-8"), 1)
            with open(export_p, "wb") as f:
                f.write(data)
            return export_p, index_p

        with mock.patch.object(te1, "write_outputs", corrupting):
            with self.assertRaises(te1.VerificationError):
                self.run_export()


class CliTests(Base):
    def cli(self, *args):
        env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
        return subprocess.run([sys.executable, TOOL_PATH, *args], capture_output=True, text=True,
                              encoding="utf-8", env=env)

    def test_success_exit_code_and_disclaimer(self):
        self.corpus()
        self.good_list()
        r = self.cli("--input-dir", self.clean, "--exclusions", self.listfile, "--out-dir", self.out, "--run-name", "c1")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("kizárt: 2", r.stdout)
        self.assertIn("NEM training-ready", r.stdout)

    def test_error_exit_codes(self):
        self.corpus()
        r = self.cli("--input-dir", self.clean, "--exclusions", os.path.join(self.tmp, "nincs.txt"), "--out-dir", self.out)
        self.assertEqual(r.returncode, te1.CODE_EXCLUSION)
        self.assertIn("HIBA", r.stderr)
        self.good_list()
        r = self.cli("--input-dir", os.path.join(self.tmp, "raw"), "--exclusions", self.listfile, "--out-dir", self.out)
        self.assertEqual(r.returncode, te1.CODE_SOURCE)
        r = self.cli("--input-dir", self.clean, "--exclusions", self.listfile, "--out-dir", os.path.join(self.clean, "x"))
        self.assertEqual(r.returncode, te1.CODE_OUTPUT)

    def test_there_is_no_way_to_switch_the_exclusion_off(self):
        self.corpus()
        self.good_list()
        for flag in ("--no-exclusions", "--skip-exclusions", "--ignore-exclusions"):
            with self.subTest(flag=flag):
                r = self.cli("--input-dir", self.clean, "--exclusions", self.listfile, "--out-dir", self.out, flag)
                self.assertEqual(r.returncode, 2)
                self.assertIn("unrecognized", r.stderr)
        self.assertFalse(os.path.exists(self.out))


@unittest.skipUnless(os.path.isdir(os.path.join(REPO_ROOT, "data", "clean")), "nincs data/clean")
class RealDataAcceptanceTests(unittest.TestCase):
    """A valós clean adaton: pontosan a hat kizárt sor marad ki. Csak OLVAS."""

    @classmethod
    def setUpClass(cls):
        cls.clean_files = sorted(glob.glob(os.path.join(REPO_ROOT, "data", "clean", "*.jsonl")))
        cls.before = file_hashes(cls.clean_files)
        cls.all_ids = []
        for f in cls.clean_files:
            for l in read_bytes(f).split(b"\n"):
                if l.strip():
                    cls.all_ids.append(json.loads(l.decode("utf-8"))["id"])

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self._tmp.cleanup()

    def export(self, **kw):
        return te1.run_export(self._tmp.name, run_name="real", **kw)

    def test_default_list_excludes_exactly_the_six_rows(self):
        m = self.export()
        self.assertEqual(m["counts"]["rows_read"], 4500)
        self.assertEqual(m["counts"]["rows_excluded"], 6)
        self.assertEqual(m["counts"]["rows_exported"], 4494)
        self.assertEqual(sorted(e["id"] for e in m["exclusion_list"]["entries"]), EXPECTED_EXCLUDED)
        out_ids = [json.loads(l)["id"] for l in read_text(os.path.join(m["run_dir"], te1.EXPORT_FILE)).splitlines()]
        self.assertEqual(len(out_ids), 4494)
        self.assertEqual(len(set(out_ids)), 4494)
        for ex in EXPECTED_EXCLUDED:
            self.assertNotIn(ex, out_ids)
        self.assertEqual(set(out_ids), set(self.all_ids) - set(EXPECTED_EXCLUDED),
                         "az engedélyezett sorok pontosan a nem kizárt sorok")
        self.assertEqual(m["warnings"], [])
        self.assertFalse(m["training_ready"])
        self.assertFalse(m["content_verified"])

    def test_clean_files_untouched_and_excluded_rows_still_there(self):
        self.export()
        self.assertEqual(self.before, file_hashes(self.clean_files), "a clean fájlok megváltoztak")
        present = set(self.all_ids)
        for ex in EXPECTED_EXCLUDED:
            self.assertIn(ex, present, "a kizárt sort nem szabad törölni a clean állományból")
        self.assertEqual(len(self.all_ids), 4500)

    def test_list_missing_one_of_the_six_is_rejected(self):
        lines = [l for l in read_text(te1.DEFAULT_EXCLUSIONS).splitlines()
                 if not l.startswith("uncertainty_source_request_0864")]
        p = os.path.join(self._tmp.name, "gyenge_lista.txt")
        with open(p, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        with self.assertRaises(te1.ExclusionListError) as ctx:
            self.export(exclusions_path=p)
        self.assertIn("uncertainty_source_request_0864", str(ctx.exception))

    def test_empty_list_is_rejected_on_real_data_even_with_bypass_flag(self):
        p = os.path.join(self._tmp.name, "ures.txt")
        with open(p, "w", encoding="utf-8") as f:
            f.write("# üres\n")
        with self.assertRaises(te1.ExclusionListError):
            self.export(exclusions_path=p)
        with self.assertRaises(te1.ExclusionListError):
            self.export(exclusions_path=p, allow_empty=True)

    def test_list_with_typo_is_rejected(self):
        text = read_text(te1.DEFAULT_EXCLUSIONS).replace(
            "uncertainty_source_request_0898", "uncertainty_source_request_0989")
        p = os.path.join(self._tmp.name, "elgepelt.txt")
        with open(p, "w", encoding="utf-8") as f:
            f.write(text)
        with self.assertRaises(te1.ExclusionListError):
            self.export(exclusions_path=p)

    def test_default_list_pins_expected_ids(self):
        entries, _ = te1.parse_exclusion_list(te1.DEFAULT_EXCLUSIONS)
        self.assertEqual(sorted(e["id"] for e in entries), EXPECTED_EXCLUDED)


if __name__ == "__main__":
    unittest.main(verbosity=2)
