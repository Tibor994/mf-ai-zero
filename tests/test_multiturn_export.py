"""
MF-AI-Zero - MT-4 teszt: tools/multiturn_export.py (felosztott többfordulós beszélgetések renderelése és exportálása).

FONTOS: kizárólag mesterséges tesztadatot használ (a tests/test_multiturn_split.py generátora: valós szavakból összeállított
értelmetlen mondatok, `mtfx_syn_NNNN` azonosító, fixture mód, `meta.fixture: true`); ez NEM része az 1000 beszélgetéses csomagnak,
tanításra nem használható, a valódi datasettet nem érinti. A valós adatos rész (RealExportTests) a TE-1 exportot és a
`data/clean` fájlokat csak OLVASSA. A teszt nem tanít semmit.

Célzott esetek: az R1 előtag bájt-pontos egyezése a `src/memory.py` `build_prompt_context` kimenetével (importált függvény);
R2 teljes előzmény; szegmens-határok, csonkolás- és függés-jelölés; részenkénti szétválasztás; sorrend, szerepek, üzenetek teljes
tartalma, azonosítók; visszaolvasás lemezről; visszakövethetőség; kizárt/visszatartott/blokkolt rekord és a hat TE-1 kizárás;
elavult, hiányos, megváltozott bemenet; tesztadat-védelem; státuszok változatlansága; veszteségmentesen nem ábrázolható eset;
új kimeneti mappa, felülírás tilalma; determinizmus; parancssor.

Futtatás:
    python -m unittest tests.test_multiturn_export
    python tests/test_multiturn_export.py
"""

import contextlib
import copy
import glob
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
TOOLS_DIR = os.path.join(TESTS_DIR, "..", "tools")
REPO_ROOT = os.path.abspath(os.path.join(TESTS_DIR, ".."))
sys.path.insert(0, TOOLS_DIR)
sys.path.insert(0, TESTS_DIR)

import dataset_export_chat_text as te2  # noqa: E402
import dataset_export_train as te1  # noqa: E402
import multiturn_export as mx  # noqa: E402
import multiturn_split as ms  # noqa: E402
import test_multiturn_split as S  # noqa: E402  (a mesterséges beszélgetések generátora és a csővezeték-segédek)

TOOL_PATH = os.path.join(TOOLS_DIR, "multiturn_export.py")
MEMORY_FILE = os.path.join(REPO_ROOT, "src", "memory.py")
EXCLUDED_ANSWER = "Kizárt válasz, amely nem kerülhet be."          # az S.Base.export() kizárt sorának válasza


def read_bytes(path):
    with open(path, "rb") as f:
        return f.read()


def read_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write_json(path, obj):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")


def sha(path):
    return hashlib.sha256(read_bytes(path)).hexdigest()


def jsonl(path):
    return [json.loads(l) for l in read_bytes(path).decode("utf-8").split("\n") if l.strip()]


def source_lines(path):
    lines = read_bytes(path).split(b"\n")
    return [l[:-1] if l.endswith(b"\r") else l for l in lines]


def parse_independent(text):
    """A renderelt szöveg visszaolvasása az eszköz függvényétől függetlenül (más darabolási elv)."""
    out = []
    for block in text.split("\n\n"):
        head, ai = block.split("\nAI: ", 1)
        assert head.startswith("User: ")
        out.append(head[len("User: "):])
        out.append(ai)
    return out


@contextlib.contextmanager
def temporarily(path, new_bytes):
    old = read_bytes(path)
    with open(path, "wb") as f:
        f.write(new_bytes)
    try:
        yield
    finally:
        with open(path, "wb") as f:
            f.write(old)


def fresh_memory():
    """A `src/memory.py` külön betöltött példánya (a teszt saját referenciája az R1 előtaghoz)."""
    spec = importlib.util.spec_from_file_location("mf_test_memory", MEMORY_FILE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def scenario():
    """40 mesterséges beszélgetés + egy blokkolt másolat: deklarált pár, persona-hármas, kizárt, kizárás-jelölt, blokkolt csoport."""
    recs = S.corpus(40, seed=201)
    S.link(recs[0], group="g5001"), S.link(recs[1], group="g5001")
    for k in (2, 3, 4):
        S.link(recs[k], persona="p901")
    dup = S.copy_of(recs[5], "mtfx_syn_9005")                         # pontos másolat: az MT-3 reject, az MT-2 az egész csoportot visszatartja
    S.link(dup, group="g9005", persona="p905")
    S.link(recs[6], persona="p905")
    recs.append(dup)
    recs[11]["quality_notes"] = S.NOTES + " " + S.MARK
    return recs


HELD = {"mtfx_syn_0005", "mtfx_syn_9005", "mtfx_syn_0006", "mtfx_syn_0010", "mtfx_syn_0011"}


class SharedPipeline(unittest.TestCase):
    """setUpClass: egy kis mesterséges csővezeték (TE-1 export -> MT-3 -> MT-2) és egy MT-4 export; a tesztek ebből olvasnak."""

    @classmethod
    def setUpClass(cls):
        cls.base = S.Base("write_convs")
        cls.base.setUp()
        cls.recs = scenario()
        excl = os.path.join(cls.base.tmp, "excl_convs.txt")
        with open(excl, "w", encoding="utf-8", newline="\n") as f:
            f.write("mtfx_syn_0010 | tartalmi kifogás | felülvizsgálat\n")
        cls.excl = excl
        cls.man2, cls.conv, cls.report = cls.base.pipeline(cls.recs, targets=(28, 4, 4), exclusions_path=excl, run_name="p")
        cls.mt2_path = os.path.join(cls.man2["run_dir"], "split_manifest.json")
        cls.export_dir = cls.base.export_dir
        cls.up_paths = cls.upstream_paths()
        cls.up_before = {p: sha(p) for p in cls.up_paths}
        cls.man4 = mx.run_export(cls.mt2_path, cls.base.out, "fixture", run_name="fixture_shared")
        cls.run_dir = cls.man4["run_dir"]
        cls.man4_path = os.path.join(cls.run_dir, mx.MANIFEST_FILE)

    @classmethod
    def tearDownClass(cls):
        cls.base.tearDown()

    @classmethod
    def upstream_paths(cls):
        paths = [cls.mt2_path, cls.conv, cls.report, cls.excl]
        paths += [os.path.join(cls.man2["run_dir"], n) for n in cls.man2["outputs"]]
        paths += [os.path.join(cls.export_dir, n) for n in os.listdir(cls.export_dir)]
        return paths

    def export(self, run_name, mt2=None, mode="fixture", **kw):
        return mx.run_export(mt2 or self.mt2_path, self.base.out, mode, run_name=run_name, **kw)

    def copy_mt2(self, name):
        dst = os.path.join(self.base.tmp, "mt2copy_" + name)
        shutil.copytree(self.man2["run_dir"], dst)
        return os.path.join(dst, "split_manifest.json")

    def copy_export(self, name):
        dst = os.path.join(self.base.tmp, "copies", "fixture_" + name)
        shutil.copytree(self.run_dir, dst)
        return dst

    def source_objs(self):
        return {o["id"]: o for o in jsonl(self.conv)}


# ---------------------------------------------------------------------------
# renderelés (tiszta függvények)
# ---------------------------------------------------------------------------

def texts_of(n_ex, u_len=40, a_len=60):
    """Pontos hosszúságú, szóköz nélküli üzenetek (a határeseteknél a hossz nem torzulhat)."""
    return [(f"{'u' if i % 2 == 0 else 'a'}{i}" + "ab" * 400)[:(u_len if i % 2 == 0 else a_len)] for i in range(2 * n_ex)]


class RenderTests(unittest.TestCase):
    def setUp(self):
        self.mem = fresh_memory()

    def test_r1_prefix_is_byte_identical_to_memory_build_prompt_context(self):
        cases = [(80, 120), (81, 121), (79, 119), (200, 300), (5, 5), (300, 600)]
        for u_len, a_len in cases:
            with self.subTest(user=u_len, assistant=a_len):
                texts = texts_of(4, u_len, a_len)
                for t in (3, 5, 7):
                    text, segs = mx.render_r1(texts, t)
                    history = [(texts[i], texts[i + 1]) for i in range(0, t - 1, 2)]
                    prefix = self.mem.build_prompt_context(history)
                    self.assertTrue(text.startswith(prefix), (t,))
                    self.assertEqual(text, prefix + "User: " + texts[t - 1] + "\nAI: " + texts[t])
                    self.assertEqual(text[segs[-1]["start"]:segs[-1]["end"]], texts[t])

    def test_r1_follows_the_documented_trimming_rule_literally(self):
        u80, u81 = "u" * 80, "u" * 81
        a120, a121 = "a" * 120, "a" * 121
        texts = [u80, a120, "kérés", "válasz", "ismét", "megint"]
        text, segs = mx.render_r1(texts, 3)
        self.assertEqual(text, f"User: {u80}\nAI: {a120}\n\nUser: kérés\nAI: válasz")
        self.assertTrue(all(s["complete"] for s in segs), "pontosan a határon nincs csonkolás")
        texts = [u81, a121, "kérés", "válasz"]
        text, segs = mx.render_r1(texts, 3)
        self.assertEqual(text, f"User: {'u' * 77}...\nAI: {'a' * 117}...\n\nUser: kérés\nAI: válasz")
        self.assertEqual([s["complete"] for s in segs], [False, False, True, True])
        texts = ["x" * 76 + " y" + "z" * 10, "válasz", "kérés", "cél"]                  # a 77. karakter szóköz: a `rstrip` miatt rövidebb
        text, _ = mx.render_r1(texts, 3)
        self.assertTrue(text.startswith("User: " + "x" * 76 + "...\nAI:"))

    def test_r1_calls_the_imported_function_not_a_copy(self):
        texts = texts_of(3)
        mem = mx.memory_module()
        with mock.patch.object(mem, "build_prompt_context", lambda history: "User: MINTA\nAI: ELŐZMÉNY\n\n"):
            text, segs = mx.render_r1(texts, 3)
        self.assertTrue(text.startswith("User: MINTA\nAI: ELŐZMÉNY\n\nUser: "))
        self.assertEqual([s["complete"] for s in segs[:2]], [False, False], "a nem forrás-szöveg nem lehet `complete`")
        self.assertEqual(mx.MEMORY_PATH, MEMORY_FILE)
        self.assertEqual(os.path.abspath(mem.__file__), MEMORY_FILE)

    def test_r1_first_exchange_has_no_history_and_only_the_last_exchange_is_used(self):
        texts = texts_of(5)
        first, segs = mx.render_r1(texts, 1)
        self.assertEqual(first, "User: " + texts[0] + "\nAI: " + texts[1])
        self.assertEqual([s["turn"] for s in segs], [0, 1])
        text, segs = mx.render_r1(texts, 7)
        self.assertEqual([s["turn"] for s in segs], [4, 5, 6, 7], "csak a cél előtti utolsó váltás")
        self.assertNotIn(texts[0], text)

    def test_r2_is_the_full_history_up_to_the_target_and_reads_back_exactly(self):
        texts = texts_of(5, 300, 600)
        for t in (1, 3, 5, 9):
            text, segs = mx.render_r2(texts, t)
            self.assertEqual(parse_independent(text), texts[:t + 1])
            self.assertEqual(mx.parse_rendered(text), [("user" if i % 2 == 0 else "assistant", texts[i]) for i in range(t + 1)])
            self.assertTrue(all(s["complete"] for s in segs))
            self.assertEqual([s["turn"] for s in segs], list(range(t + 1)))
            self.assertEqual([s["kind"] for s in segs][-2:], ["current", "target"])
            for s in segs:
                self.assertEqual(text[s["start"]:s["end"]], texts[s["turn"]])
                self.assertEqual(s["role"], "user" if s["turn"] % 2 == 0 else "assistant")

    def test_texts_that_look_like_labels_or_end_with_dots_read_back_unchanged(self):
        tricky = ["User: AI: User:", "AI: válasz...", "Kettőspont: itt; és ott...", "Ékezetes őűúóéáí 😀 — „idézet”", "x", "…", "a.b", "AI:", "User:"]
        texts = [tricky[i % len(tricky)] for i in range(8)]
        for t in (1, 3, 5, 7):
            text, _ = mx.render_r2(texts, t)
            self.assertEqual(parse_independent(text), texts[:t + 1])
            self.assertEqual([m for _r, m in mx.parse_rendered(text)], texts[:t + 1])

    def test_parse_rendered_rejects_malformed_text(self):
        for bad in ("", "nincs címke", "User: a", "User: a\nAI: b\nextra", "AI: a\nUser: b", "User: a\nAI: b\n\nUser: c"):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    mx.parse_rendered(bad)

    def test_truncation_and_dependency_are_reported_not_hidden(self):
        texts = [("a" * 150), ("b" * 300), "kérés", "válasz", "újabb kérés", "újabb válasz"]
        conv = {"obj": {"id": "mtfx_x", "turns": [{"role": "user" if i % 2 == 0 else "assistant", "text": t} for i, t in enumerate(texts)],
                        "meta": {"family": "F1", "domain": "fozes", "depends": [{"turn": 3, "on": [0, 2], "depth": 2},
                                                                                  {"turn": 5, "on": [2, 3], "depth": 1}]}},
                "entry": {"id": "mtfx_x", "unit": "mtg_x", "file": "f.jsonl", "line": 1, "line_sha256": "0" * 64, "split": "train"}}
        r1 = mx.build_samples(conv, "R1", "train", "fixture", True)
        r2 = mx.build_samples(conv, "R2", "train", "fixture", True)
        self.assertEqual([s["target_turn"] for s in r1], [1, 3, 5])
        self.assertEqual([s["exchange"] for s in r1], [1, 2, 3])
        self.assertTrue(r1[0]["lossless"] and r1[0]["first_turn"] and r1[0]["dependency"] is None)
        s3 = r1[1]                                                               # a 3. fordulónál az előzmény csonkolt és a 0. üzenetre épül
        self.assertFalse(s3["lossless"] or s3["content_complete"])
        self.assertEqual(s3["dependency"], {"on": [0, 2], "depth": 2, "covered": True, "missing": []},
                         "az R1 az előző váltást (0,1) és a jelenlegi kérést (2) adja: a függés lefedett, de a tartalom csonkolt")
        self.assertEqual([(t["turn"], t["original_chars"], t["rendered_chars"], t["lost_chars"]) for t in s3["history_truncation"]],
                         [(0, 150, 80, 73), (1, 300, 120, 183)])
        s5 = r1[2]
        self.assertEqual(s5["dependency"], {"on": [2, 3], "depth": 1, "covered": True, "missing": []})
        deep = mx.build_samples(dict(conv, obj=dict(conv["obj"], meta=dict(conv["obj"]["meta"], depends=[{"turn": 5, "on": [0, 3], "depth": 3}]))),
                                "R1", "train", "fixture", True)[2]
        self.assertEqual(deep["dependency"], {"on": [0, 3], "depth": 3, "covered": False, "missing": [0]})
        self.assertFalse(deep["lossless"], "a mélyebb előzmény-függés R1-gyel nem ábrázolható: ezt jelzi, nem rejti el")
        self.assertTrue(all(s["lossless"] and not s["history_truncation"] for s in r2))
        self.assertEqual([s["dependency"]["covered"] for s in r2 if s["dependency"]], [True, True])

    def test_sample_count_formula_and_ids(self):
        rec = S.synth(3, 4, n_ex=6)
        conv = {"obj": rec, "entry": {"id": rec["id"], "unit": "mtg_u", "file": "f", "line": 1, "line_sha256": "1" * 64, "split": "test"}}
        for mode in ("R1", "R2"):
            samples = mx.build_samples(conv, mode, "test", "fixture", True)
            self.assertEqual(len(samples), rec["meta"]["n_exchanges"])
            self.assertEqual(sum(1 for s in samples if s["first_turn"]), 1)
            self.assertEqual([s["sample_id"] for s in samples], [f"{rec['id']}#{mode}#{t}" for t in range(1, 12, 2)])
            self.assertEqual({s["conversation_id"] for s in samples}, {rec["id"]})

    def test_renderable_problems_flag_what_cannot_be_read_back_and_never_repair_it(self):
        self.assertEqual(mx.renderable_problems(["rendben", "User: ez is rendben", "AI: ez is"]), [])
        for bad, needle in (("két\nsor", "sortörő"), ("kocsi\rvissza", "sortörő"), ("sor elválasztó", "sortörő"), ("vezérlő\x07karakter", "vezérlő"),
                            ("", "üres"), (" szóközzel kezdődik", "szóköz"), ("szóközzel végződik ", "szóköz")):
            with self.subTest(bad=bad):
                problems = mx.renderable_problems(["jó", bad])
                self.assertEqual(len(problems), 1, problems)
                self.assertIn("1. üzenet", problems[0])
                self.assertIn(needle, problems[0])

    def test_r3_and_unknown_renderings_are_refused_with_a_reason(self):
        with self.assertRaises(mx.RefusedError) as ctx:
            mx.render("R3", texts_of(3), 3)
        self.assertIn("arany", str(ctx.exception))
        with self.assertRaises(mx.RefusedError):
            mx.render("R9", texts_of(3), 3)

    def test_run_name_rules_separate_test_data_from_real_exports(self):
        self.assertEqual(mx.check_run_name("fixture_mt4_x", True), "fixture_mt4_x")
        self.assertEqual(mx.check_run_name("mt4_x", False), "mt4_x")
        for name, fixture in (("mt4_x", True), ("fixtureX", False), ("Fixture_x", False), ("../kifelé", True), ("szóköz van", False)):
            with self.subTest(name=name, fixture=fixture):
                with self.assertRaises(mx.ExportError):
                    mx.check_run_name(name, fixture)


# ---------------------------------------------------------------------------
# az export tartalma és szerkezete
# ---------------------------------------------------------------------------

class ExportContentTests(SharedPipeline):
    def splits_of_mt2(self):
        return {a["id"]: a["split"] for a in self.man2["assignment"]}

    def test_counts_match_the_mt2_manifest_and_the_sample_formula(self):
        man = self.man4
        self.assertEqual(man["withheld"], [])
        self.assertEqual(man["warnings"], [])
        src = self.source_objs()
        for s in mx.SPLITS:
            st = man["splits"][s]
            exp = self.man2["splits"][s]
            ids = [c["id"] for c in self.man2["assignment"] if c["split"] == s]
            self.assertEqual((st["conversations"], st["messages"]), (exp["conversations"], exp["messages"]))
            self.assertEqual(st["messages"], sum(len(src[i]["turns"]) for i in ids))
            for mode in ("R1", "R2"):
                sm = st["samples"][mode]
                self.assertEqual(sm["total"], exp["samples_total"])
                self.assertEqual(sm["total"], sum(src[i]["meta"]["n_exchanges"] for i in ids), "minta = assistant-fordulók száma")
                self.assertEqual((sm["first_turn"], sm["history_dependent"]), (exp["samples_first_turn"], exp["samples_history_dependent"]))
        self.assertEqual(sum(man["splits"][s]["conversations"] for s in mx.SPLITS), 36)

    def test_parts_are_separated_and_match_the_mt2_assignment_and_groups(self):
        want = self.splits_of_mt2()
        seen = {}
        for s in mx.SPLITS:
            canon_ids = [o["id"] for o in jsonl(os.path.join(self.run_dir, f"canonical_{s}.jsonl"))]
            for cid in canon_ids:
                self.assertNotIn(cid, seen, "egy beszélgetés csak egy részben szerepelhet")
                seen[cid] = s
            for mode in ("R1", "R2"):
                samples = jsonl(os.path.join(self.run_dir, f"samples_{s}_{mode}.jsonl"))
                self.assertEqual({x["conversation_id"] for x in samples}, set(canon_ids))
                self.assertEqual({x["split"] for x in samples}, {s})
        self.assertEqual(seen, want)
        by_unit = {}
        for a in self.man2["assignment"]:
            by_unit.setdefault(a["unit"], set()).add(seen[a["id"]])
        self.assertTrue(all(len(v) == 1 for v in by_unit.values()), "egy csoport minden mintája ugyanabban a részben")
        self.assertTrue(any(len(u["members"]) >= 2 for u in self.man2["units"].values()), "a teszt csoportokat is tartalmaz")

    def test_held_back_excluded_and_unresolved_records_are_absent_everywhere(self):
        self.assertEqual({h["id"] for h in self.man2["held_back"]}, HELD)
        blob = b"".join(read_bytes(os.path.join(self.run_dir, n)) for n in os.listdir(self.run_dir) if n != mx.MANIFEST_FILE and n != mx.WITHHELD_FILE)
        for rid in HELD:
            self.assertNotIn(rid.encode(), blob, rid)
        exported = {c["id"] for c in self.man4["conversations"]}
        self.assertEqual(exported & HELD, set())
        self.assertEqual(len(exported), 36)
        self.assertIn("mtfx_syn_0005", read_bytes(self.conv).decode())            # a forrásban megvan: az export nem törli/módosítja

    def test_order_roles_content_and_ids_are_preserved_byte_for_byte(self):
        src_lines = source_lines(self.conv)
        src_objs = self.source_objs()
        order = [json.loads(l)["id"] for l in src_lines if l.strip()]
        for s in mx.SPLITS:
            lines = [l for l in read_bytes(os.path.join(self.run_dir, f"canonical_{s}.jsonl")).split(b"\n") if l]
            ids = [json.loads(l)["id"] for l in lines]
            self.assertEqual(ids, [i for i in order if i in set(ids)], "a forrás sorrendje")
            for line in lines:
                obj = json.loads(line)
                self.assertIn(line, src_lines, "a kanonikus sor a forrássor bájt-pontos másolata")
                self.assertEqual(obj, src_objs[obj["id"]])
                self.assertEqual([t["role"] for t in obj["turns"]], ["user" if i % 2 == 0 else "assistant" for i in range(len(obj["turns"]))])

    def test_r2_samples_read_back_to_the_full_source_history(self):
        src = self.source_objs()
        n = 0
        for s in mx.SPLITS:
            for smp in jsonl(os.path.join(self.run_dir, f"samples_{s}_R2.jsonl")):
                texts = [t["text"] for t in src[smp["conversation_id"]]["turns"]]
                t = smp["target_turn"]
                self.assertEqual(parse_independent(smp["text"]), texts[:t + 1])
                self.assertTrue(smp["lossless"] and smp["content_complete"] and not smp["history_truncation"])
                self.assertEqual(smp["text"][smp["target"]["start"]:smp["target"]["end"]], texts[t])
                n += 1
        self.assertEqual(n, sum(self.man2["splits"][s]["samples_total"] for s in mx.SPLITS))

    def test_r1_samples_keep_current_request_and_target_whole_and_mark_every_truncation(self):
        src = self.source_objs()
        mem = fresh_memory()
        truncated = uncovered = 0
        for s in mx.SPLITS:
            for smp in jsonl(os.path.join(self.run_dir, f"samples_{s}_R1.jsonl")):
                texts = [t["text"] for t in src[smp["conversation_id"]]["turns"]]
                t = smp["target_turn"]
                got = parse_independent(smp["text"])
                self.assertEqual(got[-2:], texts[t - 1:t + 1], "az aktuális kérés és a cél teljes")
                history = [(texts[i], texts[i + 1]) for i in range(0, t - 1, 2)]
                expect_prefix = mem.build_prompt_context(history) if history else ""
                self.assertTrue(smp["text"].startswith(expect_prefix))
                for k, (msg, turn) in enumerate(zip(got[:-2], (t - 3, t - 2))):
                    seg = smp["messages"][k]
                    self.assertEqual((seg["turn"], seg["complete"]), (turn, msg == texts[turn]))
                    if msg != texts[turn]:
                        self.assertTrue(msg.endswith("...") and texts[turn].startswith(msg[:-3]))
                self.assertEqual(len(smp["history_truncation"]), sum(1 for m in smp["messages"] if not m["complete"]))
                truncated += bool(smp["history_truncation"])
                uncovered += bool(smp["dependency"] and not smp["dependency"]["covered"])
        st = {k: sum(self.man4["splits"][s]["samples"]["R1"][k] for s in mx.SPLITS) for k in ("content_truncated", "dependency_not_covered")}
        self.assertEqual((st["content_truncated"], st["dependency_not_covered"]), (truncated, uncovered))
        self.assertGreater(truncated, 0, "a mesterséges üzenetek hosszabbak a futásidő-korlátnál: az R1 csonkol, és ez jelölt")
        self.assertGreater(uncovered, 0, "van olyan minta, amelynek előzmény-függése R1-gyel nem ábrázolható")

    def test_lossless_counters_in_the_manifest_equal_a_recount(self):
        for s in mx.SPLITS:
            for mode in ("R1", "R2"):
                samples = jsonl(os.path.join(self.run_dir, f"samples_{s}_{mode}.jsonl"))
                sm = self.man4["splits"][s]["samples"][mode]
                self.assertEqual(sm["lossless"], sum(1 for x in samples if x["lossless"]))
                self.assertEqual(sm["lossless"] + sm["not_lossless"], sm["total"])
                self.assertEqual(sm["history_chars_lost"], sum(t["lost_chars"] for x in samples for t in x["history_truncation"]))
                if mode == "R2":
                    self.assertEqual(sm["not_lossless"], 0)

    def test_traceability_maps_every_sample_and_conversation_to_source_line_and_turn(self):
        src_lines = source_lines(self.conv)
        rows = [l.split("\t") for l in read_bytes(os.path.join(self.run_dir, mx.EXPORT_INDEX)).decode("utf-8").split("\n") if l][1:]
        head = read_bytes(os.path.join(self.run_dir, mx.EXPORT_INDEX)).decode("utf-8").split("\n")[0].split("\t")
        ids = set()
        for r in rows:
            d = dict(zip(head, r))
            self.assertNotIn(d["sample_id"], ids)
            ids.add(d["sample_id"])
            line = src_lines[int(d["source_line"]) - 1]
            self.assertEqual(hashlib.sha256(line).hexdigest(), d["source_line_sha256"])
            obj = json.loads(line)
            self.assertEqual(obj["id"], d["conversation"])
            t = int(d["target_turn"])
            self.assertEqual(obj["turns"][t]["role"], "assistant")
            smp = jsonl(os.path.join(self.run_dir, d["samples_file"]))[int(d["samples_line"]) - 1]
            self.assertEqual(smp["sample_id"], d["sample_id"])
            self.assertEqual(hashlib.sha256(smp["text"].encode("utf-8")).hexdigest(), d["text_sha256"])
            self.assertEqual(smp["source"], {"file": te1.rel_path(self.conv), "line": int(d["source_line"]), "line_sha256": d["source_line_sha256"]})
        self.assertEqual(len(rows), sum(2 * self.man2["splits"][s]["samples_total"] for s in mx.SPLITS), "két renderelés × a minták száma")
        crows = [l.split("\t") for l in read_bytes(os.path.join(self.run_dir, mx.CONVERSATION_INDEX)).decode("utf-8").split("\n") if l][1:]
        self.assertEqual(len(crows), 36)
        for r in crows:
            self.assertEqual(json.loads(src_lines[int(r[7]) - 1])["id"], r[0])

    def test_statuses_are_unchanged_and_fixture_data_is_marked_everywhere(self):
        man = self.man4
        for flag in ("split_approved", "content_verified", "training_ready"):
            self.assertIs(man[flag], False)
            self.assertIs(man["statuses"][flag], False)
            self.assertIs(read_json(self.mt2_path)[flag], False)
        self.assertIs(man["training_data"], False)
        self.assertEqual((man["data_kind"], man["fixture"]), ("fixture", True))
        self.assertIn("NEM tanítóadat", man["purpose"])
        self.assertTrue(os.path.isfile(os.path.join(self.run_dir, mx.FIXTURE_MARKER_FILE)))
        self.assertTrue(os.path.basename(self.run_dir).startswith("fixture_"))
        for s in mx.SPLITS:
            for mode in ("R1", "R2"):
                for smp in jsonl(os.path.join(self.run_dir, f"samples_{s}_{mode}.jsonl")):
                    self.assertEqual((smp["fixture"], smp["data_kind"]), (True, "fixture"))
        self.assertTrue(all(o.get("meta", {}).get("fixture") is True for s in mx.SPLITS
                            for o in jsonl(os.path.join(self.run_dir, f"canonical_{s}.jsonl"))))

    def test_upstream_files_and_earlier_exports_are_untouched(self):
        self.assertEqual({p: sha(p) for p in self.up_paths}, self.up_before)
        second = self.export("fixture_second")
        self.assertNotEqual(second["run_dir"], self.run_dir)
        self.assertEqual({p: sha(p) for p in self.up_paths}, self.up_before)
        self.assertEqual(self.man4["outputs"]["samples_train_R1.jsonl"]["sha256"], sha(os.path.join(self.run_dir, "samples_train_R1.jsonl")))
        self.assertEqual(hashlib.sha256(read_bytes(MEMORY_FILE)).hexdigest(), self.man4["render_reference"]["sha256"])

    def test_manifest_records_inputs_settings_and_render_reference(self):
        man = self.man4
        self.assertEqual(man["inputs"]["mt2_manifest"]["sha256"], sha(self.mt2_path))
        self.assertEqual(man["inputs"]["mt2_manifest"]["assignment_sha256"], self.man2["assignment_sha256"])
        self.assertEqual(man["inputs"]["conversation_files"][0]["sha256"], sha(self.conv))
        self.assertEqual(man["inputs"]["te1_export"]["excluded_rows"], ["x_excl_0001"])
        self.assertEqual(man["render_reference"]["module"], "src/memory.py")
        self.assertTrue(man["render_reference"]["imported_not_copied"])
        self.assertEqual((man["render_reference"]["max_prompt_user_chars"], man["render_reference"]["max_prompt_reply_chars"]), (80, 120))
        self.assertIn("R3", man["config"]["unsupported_modes"])
        self.assertEqual(man["config"]["modes"], ["R1", "R2"])
        self.assertTrue(man["exclusion_guard"]["performed"])
        self.assertEqual(len(man["exclusion_guard"]["excluded_text_sha256"]), 2, "a kizárt sor kérdése és válasza")
        self.assertEqual(man["exclusion_guard"]["held_back_from_mt2"], 5)
        for name, o in man["outputs"].items():
            self.assertEqual(o["sha256"], sha(os.path.join(self.run_dir, name)))
        self.assertGreater(len(man["limitations"]), 3)
        self.assertIn("NEM training-ready", man["disclaimer"])

    def test_written_export_reads_back_clean_from_disk(self):
        self.assertEqual(mx.verify_export(self.man4_path), [])
        self.assertEqual(mx._main(["--verify-export", self.man4_path]), 0)
        self.assertEqual(sorted(os.listdir(self.run_dir)),
                         sorted(["canonical_train.jsonl", "canonical_validation.jsonl", "canonical_test.jsonl", "conversation_index.tsv", "export_index.tsv",
                                 "export_manifest.json", "withheld.tsv", mx.FIXTURE_MARKER_FILE]
                                + [f"samples_{s}_{m}.jsonl" for s in mx.SPLITS for m in ("R1", "R2")]))

    def test_repeated_export_is_byte_identical(self):
        again = self.export("fixture_again")
        for name in self.man4["outputs"]:
            self.assertEqual(read_bytes(os.path.join(self.run_dir, name)), read_bytes(os.path.join(again["run_dir"], name)), name)
        self.assertEqual(self.man4["splits"], again["splits"])

    def test_single_mode_exports_only_that_rendering(self):
        r2 = self.export("fixture_r2only", modes=("R2",))
        self.assertEqual(r2["config"]["modes"], ["R2"])
        self.assertFalse(any("_R1" in n for n in os.listdir(r2["run_dir"])))
        self.assertEqual(mx.verify_export(os.path.join(r2["run_dir"], mx.MANIFEST_FILE)), [])
        r1 = self.export("fixture_r1only", modes=("R1",))
        self.assertTrue(all("R2" not in n for n in os.listdir(r1["run_dir"])))
        self.assertEqual(r1["splits"]["train"]["samples"]["R1"], self.man4["splits"]["train"]["samples"]["R1"])


# ---------------------------------------------------------------------------
# elavult, hiányos, megváltozott bemenet
# ---------------------------------------------------------------------------

class StaleInputTests(SharedPipeline):
    def assertStale(self, needle, mt2=None, **kw):
        with self.assertRaises(mx.StaleInputError) as ctx:
            self.export("fixture_stale", mt2=mt2, **kw)
        self.assertIn(needle, str(ctx.exception))
        self.assertFalse(os.path.exists(os.path.join(self.base.out, "fixture_stale")), "hiba után nincs futás-mappa")
        return ctx.exception

    def test_missing_manifest_and_unreadable_manifest(self):
        with self.assertRaises(mx.InputFileError):
            self.export("fixture_x", mt2=os.path.join(self.base.tmp, "nincs.json"))
        junk = os.path.join(self.base.tmp, "junk", "split_manifest.json")
        os.makedirs(os.path.dirname(junk))
        for text in ("nem json", "[]", "{}"):
            with open(junk, "w", encoding="utf-8") as f:
                f.write(text)
            with self.assertRaises(mx.StaleInputError):
                self.export("fixture_x", mt2=junk)

    def test_incomplete_or_altered_manifest_is_refused(self):
        m = read_json(self.mt2_path)
        for key in ("assignment", "units", "assignment_sha256", "held_back", "inputs", "verification"):
            with self.subTest(missing=key):
                p = self.copy_mt2("missing_" + key)
                bad = dict(m)
                del bad[key]
                write_json(p, bad)
                self.assertStale(key, mt2=p)
        p = self.copy_mt2("moved")                                        # egy beszélgetés áthelyezve a manifestben, a sha érintetlen
        bad = json.loads(json.dumps(m))
        a = next(x for x in bad["assignment"] if x["split"] == "train")
        a["split"] = "test"
        write_json(p, bad)
        self.assertStale("assignment_sha256", mt2=p)
        p = self.copy_mt2("groups")
        bad = json.loads(json.dumps(m))
        uid = next(iter(bad["units"]))
        bad["units"][uid]["members"] = bad["units"][uid]["members"] + ["mtfx_syn_9999"]
        write_json(p, bad)
        self.assertStale("groups_sha256", mt2=p)
        p = self.copy_mt2("counts")
        bad = json.loads(json.dumps(m))
        bad["counts"]["assigned"] += 1
        write_json(p, bad)
        self.assertStale("darabszám", mt2=p)
        p = self.copy_mt2("verification")
        bad = json.loads(json.dumps(m))
        bad["verification"]["no_unit_split_across_parts"] = False
        write_json(p, bad)
        self.assertStale("ellenőrzései nem mind igazak", mt2=p)
        p = self.copy_mt2("tool")
        bad = json.loads(json.dumps(m))
        bad["tool"] = "tools/mas.py"
        write_json(p, bad)
        self.assertStale("nem MT-2 manifest", mt2=p)

    def test_a_manifest_that_claims_approval_is_refused_and_the_export_never_grants_it(self):
        m = read_json(self.mt2_path)
        for flag in ("split_approved", "content_verified", "training_ready"):
            with self.subTest(flag=flag):
                p = self.copy_mt2("flag_" + flag)
                bad = dict(m, **{flag: True})
                write_json(p, bad)
                self.assertStale(flag, mt2=p)
        self.assertIs(self.man4["split_approved"] or self.man4["content_verified"] or self.man4["training_ready"], False)

    def test_changed_conversation_file_mt3_report_exclusions_and_te1_export_are_refused(self):
        with temporarily(self.conv, read_bytes(self.conv) + b"\n"):
            self.assertStale("megváltozott")
        with temporarily(self.report, read_bytes(self.report) + b" "):
            self.assertStale("MT-3 jelentés")
        with temporarily(self.excl, read_bytes(self.excl) + b"# megjegyzes\n"):
            self.assertStale("kizárási lista")
        export_file = os.path.join(self.export_dir, te1.EXPORT_FILE)
        with temporarily(export_file, read_bytes(export_file) + b" "):
            self.assertStale("TE-1")
        self.assertEqual({p: sha(p) for p in self.up_paths}, self.up_before, "a próbák után minden visszaállt")

    def test_changed_mt2_outputs_are_refused(self):
        p = self.copy_mt2("outputs")
        ids = os.path.join(os.path.dirname(p), "ids_test.txt")
        with open(ids, "a", encoding="utf-8") as f:
            f.write("mtfx_syn_9999\n")
        self.assertStale("kimenet megváltozott", mt2=p)

    def test_input_changed_during_the_run_is_detected(self):
        real = mx.build_export

        def tampering(*a, **kw):
            with open(self.conv, "ab") as f:
                f.write(b"\n")
            return real(*a, **kw)

        original = read_bytes(self.conv)
        try:
            with mock.patch.object(mx, "build_export", tampering):
                with self.assertRaises(mx.ChangedInputError):
                    self.export("fixture_during")
        finally:
            with open(self.conv, "wb") as f:
                f.write(original)
        self.assertFalse(os.path.exists(os.path.join(self.base.out, "fixture_during")))
        self.assertEqual({p: sha(p) for p in self.up_paths}, self.up_before)

    def test_source_line_that_no_longer_matches_the_manifest_is_refused(self):
        p = self.copy_mt2("linesha")
        m = read_json(p)
        m["assignment"][0]["line_sha256"] = "0" * 64
        write_json(p, m)
        self.assertStale("ellenőrzőösszege", mt2=p)

    def test_te1_comparison_is_required_unless_explicitly_allowed(self):
        base = S.Base("write_convs")
        base.setUp()
        try:
            recs = S.corpus(20, seed=210)
            conv = base.write_convs(recs, "n.jsonl")
            report = base.mt3([conv], export_dir=None)
            man2 = ms.run_from_files([conv], base.out, "fixture", report, targets=(16, 2, 2), allow_no_te1=True, run_name="nx")
            path = os.path.join(man2["run_dir"], "split_manifest.json")
            with self.assertRaises(mx.StaleInputError) as ctx:
                mx.run_export(path, base.out, "fixture", run_name="fixture_nx")
            self.assertIn("hat kizárás", str(ctx.exception))
            man4 = mx.run_export(path, base.out, "fixture", allow_no_te1=True, run_name="fixture_nx2")
            self.assertTrue(any("hat kizárás elleni" in w for w in man4["warnings"]))
            self.assertFalse(man4["exclusion_guard"]["performed"])
            self.assertIsNone(man4["inputs"]["te1_export"])
            self.assertEqual(mx.verify_export(os.path.join(man4["run_dir"], mx.MANIFEST_FILE)), [])
            self.assertEqual(mx._main(["--mode", "fixture", "--mt2-manifest", path, "--out-dir", base.out, "--allow-no-te1-comparison",
                                       "--run-name", "fixture_nx3"]), mx.EXIT_ATTENTION)
        finally:
            base.tearDown()


# ---------------------------------------------------------------------------
# kizárások: visszatartott, kizárt, blokkolt rekord és a hat TE-1 kizárás
# ---------------------------------------------------------------------------

class ExclusionTests(SharedPipeline):
    def fabricate(self, rid, split="train"):
        """Egy forrásbeli rekord exportra jelölt alakja (az MT-2 kijelölésétől függetlenül) a független ellenőrzések vizsgálatához."""
        for n, line in enumerate(source_lines(self.conv), 1):
            if line.strip() and json.loads(line)["id"] == rid:
                obj = json.loads(line)
                return {"entry": {"id": rid, "file": te1.rel_path(self.conv), "line": n, "line_sha256": hashlib.sha256(line).hexdigest(),
                                  "unit": "mtg_x", "split": split}, "line": line, "obj": obj, "file_idx": 0}
        raise AssertionError(rid)

    def guard(self, extra, allow_no_te1=False):
        m = read_json(self.mt2_path)
        convs, _infos = mx.load_sources(m, "fixture")
        return mx.check_exclusions_and_status(m, convs + extra, "fixture", allow_no_te1)

    def test_a_clean_selection_passes_the_independent_guard(self):
        info, hashes, warnings = self.guard([])
        self.assertEqual(info["excluded_rows"], ["x_excl_0001"])
        self.assertEqual(len(hashes), 2)
        self.assertEqual(warnings, [])

    def test_every_class_of_excluded_or_unresolved_record_is_refused_even_if_the_manifest_selected_it(self):
        cases = {"mtfx_syn_0005": "MT-2", "mtfx_syn_9005": "MT-2", "mtfx_syn_0006": "MT-2",       # blokkolt pár és csoporttársa: visszatartott
                 "mtfx_syn_0010": "MT-2", "mtfx_syn_0011": "MT-2"}                                # kizárási lista, kizárás-jelölés: visszatartott
        for rid in cases:
            with self.subTest(record=rid):
                with self.assertRaises(mx.ExclusionViolationError) as ctx:
                    self.guard([self.fabricate(rid)])
                self.assertIn(rid, str(ctx.exception))

    def test_independent_checks_catch_a_record_even_when_the_held_back_list_does_not_mention_it(self):
        m = read_json(self.mt2_path)
        convs, _ = mx.load_sources(m, "fixture")
        m2 = json.loads(json.dumps(m))
        m2["held_back"] = []                                                                     # az MT-2 lista „elfelejti” őket
        m2["inputs"]["exclusions"] = None
        for rid, needle in (("mtfx_syn_0011", "Kizárás-jelölésű"), ("mtfx_syn_0005", "MT-3 reject/review"), ("mtfx_syn_0006", "Blokkolt tagot")):
            with self.subTest(record=rid):
                with self.assertRaises(mx.ExclusionViolationError) as ctx:
                    mx.check_exclusions_and_status(m2, convs + [self.fabricate(rid)], "fixture", False)
                self.assertIn(needle, str(ctx.exception))
        m3 = json.loads(json.dumps(m))
        m3["held_back"] = []
        with self.assertRaises(mx.ExclusionViolationError) as ctx:                               # csak a kizárási lista mondja
            mx.check_exclusions_and_status(m3, convs + [self.fabricate("mtfx_syn_0010")], "fixture", False)
        self.assertIn("Kizárási listás", str(ctx.exception))

    def test_te1_excluded_row_ids_and_texts_are_refused(self):
        convs, _ = mx.load_sources(read_json(self.mt2_path), "fixture")
        for field, text in (("output", EXCLUDED_ANSWER), ("instruction", "Kizárt kérdés?")):
            with self.subTest(field=field):
                bad = copy.deepcopy(convs[0])
                bad["obj"]["turns"][1]["text"] = text
                with self.assertRaises(mx.ExclusionViolationError) as ctx:
                    mx.check_exclusions_and_status(read_json(self.mt2_path), [bad] + convs[1:], "fixture", False)
                self.assertIn("x_excl_0001", str(ctx.exception))
                self.assertIn(field, str(ctx.exception))
        bad = copy.deepcopy(convs[0])
        bad["obj"]["turns"][1]["text"] = "  " + EXCLUDED_ANSWER + " "                             # szóközzel nyírva is azonos
        with self.assertRaises(mx.ExclusionViolationError):
            mx.check_exclusions_and_status(read_json(self.mt2_path), [bad] + convs[1:], "fixture", False)
        clash = copy.deepcopy(convs[0])
        clash["entry"] = dict(clash["entry"], id="x_excl_0001")
        with self.assertRaises(mx.ExclusionViolationError) as ctx:
            mx.check_exclusions_and_status(read_json(self.mt2_path), [clash] + convs[1:], "fixture", False)
        self.assertIn("ütközik", str(ctx.exception))

    def test_a_conversation_containing_an_excluded_text_stops_the_whole_export(self):
        base = S.Base("write_convs")
        base.setUp()
        try:
            recs = S.corpus(24, seed=220)
            recs[7]["turns"][3]["text"] = EXCLUDED_ANSWER
            man2, conv, report = base.pipeline(recs, targets=(20, 2, 2), run_name="ex")
            with self.assertRaises(mx.ExclusionViolationError) as ctx:
                mx.run_export(os.path.join(man2["run_dir"], "split_manifest.json"), base.out, "fixture", run_name="fixture_ex")
            self.assertIn("mtfx_syn_0007", str(ctx.exception))
            self.assertEqual(ctx.exception.exit_code, mx.EXIT_EXCLUSION)
            self.assertFalse(os.path.exists(os.path.join(base.out, "fixture_ex")), "kizárt tartalommal nem jön létre export")
        finally:
            base.tearDown()

    def test_te1_export_list_that_disagrees_with_the_mt2_manifest_is_refused(self):
        p = self.copy_mt2("excluded_rows")
        m = read_json(p)
        m["inputs"]["te1_export"]["excluded_rows"] = ["x_mas_0001"]
        write_json(p, m)
        with self.assertRaises(mx.StaleInputError):
            self.export("fixture_x", mt2=p)


# ---------------------------------------------------------------------------
# veszteségmentesen nem ábrázolható esetek
# ---------------------------------------------------------------------------

class LosslessnessTests(SharedPipeline):
    def test_a_conversation_that_cannot_be_rendered_losslessly_is_withheld_with_a_reason_never_altered(self):
        victim = "mtfx_syn_0020"
        real = mx.renderable_problems
        target_texts = [t["text"] for t in self.source_objs()[victim]["turns"]]

        def fake(texts):
            return ["3. üzenet: sortörő karakter (teszt)"] if list(texts) == target_texts else real(texts)

        with mock.patch.object(mx, "renderable_problems", fake):
            man = self.export("fixture_withheld")
        run = man["run_dir"]
        self.assertEqual([w["id"] for w in man["withheld"]], [victim])
        self.assertIn("nem ábrázolható veszteségmentesen", man["withheld"][0]["reason"])
        self.assertTrue(any("veszteségmentesen nem ábrázolható" in w for w in man["warnings"]))
        blob = b"".join(read_bytes(os.path.join(run, n)) for n in os.listdir(run) if n not in (mx.MANIFEST_FILE, mx.WITHHELD_FILE))
        self.assertNotIn(victim.encode(), blob)
        tsv = read_bytes(os.path.join(run, mx.WITHHELD_FILE)).decode("utf-8")
        self.assertIn(victim, tsv)
        self.assertIn("sortörő", tsv)
        self.assertEqual(sum(man["splits"][s]["conversations"] for s in mx.SPLITS), 35)
        self.assertEqual(mx.verify_export(os.path.join(run, mx.MANIFEST_FILE)), [])

    def test_cli_signals_attention_when_something_was_withheld(self):
        real = mx.renderable_problems
        target_texts = [t["text"] for t in self.source_objs()["mtfx_syn_0021"]["turns"]]
        with mock.patch.object(mx, "renderable_problems", lambda texts: ["teszt"] if list(texts) == target_texts else real(texts)):
            code = mx._main(["--mode", "fixture", "--mt2-manifest", self.mt2_path, "--out-dir", self.base.out, "--run-name", "fixture_attention"])
        self.assertEqual(code, mx.EXIT_ATTENTION)

    def test_an_empty_r1_context_from_the_runtime_function_is_reported_not_papered_over(self):
        mem = mx.memory_module()
        with mock.patch.object(mem, "build_prompt_context", lambda history: ""):
            man = self.export("fixture_emptyctx", modes=("R1",))
        self.assertEqual(sum(man["splits"][s]["conversations"] for s in mx.SPLITS), 0)
        self.assertEqual(len(man["withheld"]), 36)
        self.assertTrue(all("üres előzményt" in w["reason"] for w in man["withheld"]))

    def test_r3_and_bad_mode_lists_are_refused_before_anything_is_written(self):
        for modes, needle in ((("R1", "R3"), "arany"), (("R3",), "arany"), (("R9",), "Ismeretlen"), ((), "üres"), (("R1", "R1"), "ismétlődő")):
            with self.subTest(modes=modes):
                with self.assertRaises(mx.RefusedError) as ctx:
                    self.export("fixture_badmodes", modes=modes)
                self.assertIn(needle, str(ctx.exception))
                self.assertFalse(os.path.exists(os.path.join(self.base.out, "fixture_badmodes")))
        self.assertEqual(mx._main(["--mode", "fixture", "--mt2-manifest", self.mt2_path, "--out-dir", self.base.out, "--modes", "R3"]), mx.EXIT_REFUSED)


# ---------------------------------------------------------------------------
# tesztadat-védelem, kimeneti mappa
# ---------------------------------------------------------------------------

class SeparationAndOutputTests(SharedPipeline):
    def test_test_data_cannot_be_exported_as_real_data_or_under_a_real_looking_name(self):
        with self.assertRaises(mx.RefusedError) as ctx:
            self.export("mt4_valodi", mode="dataset")
        self.assertIn("mód", str(ctx.exception))
        self.assertEqual(ctx.exception.exit_code, mx.EXIT_REFUSED)
        with self.assertRaises(mx.RefusedError) as ctx:
            self.export("mt4_valodi_nev")                                       # fixture adat, de nem `fixture_` előtagú mappa
        self.assertIn("fixture_", str(ctx.exception))
        self.assertFalse(os.path.exists(os.path.join(self.base.out, "mt4_valodi_nev")))
        self.assertFalse(os.path.exists(os.path.join(self.base.out, "mt4_valodi")))
        with self.assertRaises(mx.RefusedError):
            mx.run_export(self.mt2_path, self.base.out, "valami")

    def test_a_record_whose_fixture_flag_contradicts_the_mode_is_refused_at_export_time(self):
        convs, infos = mx.load_sources(read_json(self.mt2_path), "fixture")
        self.assertTrue(all(c["obj"]["meta"]["fixture"] is True for c in convs))
        bad = copy.deepcopy(convs)
        bad[3]["obj"]["meta"]["fixture"] = False
        with mock.patch.object(mx, "load_sources", lambda m, mode: (bad, infos)):
            with self.assertRaises(mx.RefusedError) as ctx:
                self.export("fixture_flagmismatch")
        self.assertIn("fixture-jelölése", str(ctx.exception))
        self.assertFalse(os.path.exists(os.path.join(self.base.out, "fixture_flagmismatch")))

    def test_output_paths_are_guarded_and_never_overwrite(self):
        for inside in (os.path.join(self.man2["run_dir"], "belul"), os.path.join(os.path.dirname(self.conv), "belul"),
                       os.path.join(self.export_dir, "belul")):
            with self.subTest(inside=inside):
                with self.assertRaises(mx.OutputError):
                    mx.run_export(self.mt2_path, inside, "fixture", run_name="fixture_belul")
        for name in ("clean", "raw", "rejected", "inbox"):
            with self.assertRaises(mx.OutputError):
                mx.run_export(self.mt2_path, os.path.join(REPO_ROOT, "data", name, "mt4"), "fixture", run_name="fixture_x")
            self.assertFalse(os.path.exists(os.path.join(REPO_ROOT, "data", name, "mt4")))
        with self.assertRaises(mx.OutputError):
            self.export("fixture_shared")                                       # már létezik: nem írja felül
        self.assertEqual(self.man4["outputs"]["canonical_train.jsonl"]["sha256"], sha(os.path.join(self.run_dir, "canonical_train.jsonl")))
        with self.assertRaises(mx.OutputError):
            self.export("fixture_../kifelé")

    def test_failed_verification_leaves_no_finalized_export(self):
        with mock.patch.object(mx, "verify_export", lambda *a, **k: ["teszt hiba"]):
            with self.assertRaises(mx.VerificationError) as ctx:
                self.export("fixture_failverify")
        self.assertEqual(ctx.exception.exit_code, mx.EXIT_VERIFY)
        run = os.path.join(self.base.out, "fixture_failverify")
        self.assertTrue(os.path.isfile(os.path.join(run, mx.FAILED_FILE)))
        self.assertFalse(os.path.exists(os.path.join(run, mx.MANIFEST_FILE)), "hibás export manifestje nem véglegesedik")
        self.assertNotEqual(mx._main(["--verify-export", os.path.join(run, mx.MANIFEST_FILE)]), 0)


# ---------------------------------------------------------------------------
# visszaolvasás: a hibás export lemezről felismerhető (akkor is, ha a manifest ellenőrzőösszege újra van írva)
# ---------------------------------------------------------------------------

class VerifyExportTests(SharedPipeline):
    def resign(self, run, names):
        p = os.path.join(run, mx.MANIFEST_FILE)
        man = read_json(p)
        for n in names:
            man["outputs"][n] = {"sha256": sha(os.path.join(run, n)), "bytes": os.path.getsize(os.path.join(run, n))}
        write_json(p, man)
        return p

    def tamper(self, name, files, fn, resign=True):
        run = self.copy_export(name)
        for f in files:
            path = os.path.join(run, f)
            data = read_bytes(path)
            new = fn(f, data)
            with open(path, "wb") as fh:
                fh.write(new)
        p = self.resign(run, files) if resign else os.path.join(run, mx.MANIFEST_FILE)
        return run, mx.verify_export(p)

    def assertDetected(self, problems, needle=None):
        self.assertTrue(problems, "a hiba nem lett észrevéve")
        if needle:
            self.assertTrue(any(needle in x for x in problems), (needle, problems[:5]))

    def test_a_pristine_copy_verifies(self):
        run = self.copy_export("pristine")
        self.assertEqual(mx.verify_export(os.path.join(run, mx.MANIFEST_FILE)), [])

    def test_changed_files_are_detected_by_checksum(self):
        _run, problems = self.tamper("flip", ["canonical_train.jsonl"], lambda f, d: d[:-2] + b"X\n", resign=False)
        self.assertDetected(problems, "megváltozott")
        run = self.copy_export("delete")
        os.remove(os.path.join(run, "samples_test_R2.jsonl"))
        self.assertDetected(mx.verify_export(os.path.join(run, mx.MANIFEST_FILE)), "hiányzó")

    def test_content_role_and_boundary_tampering_is_detected_even_with_a_re_signed_manifest(self):
        def edit_sample(fn, pick=lambda o: True):
            """A fájl első, a feltételnek megfelelő (3. sortól kezdődő) mintáját írja át."""
            def apply(f, data):
                lines = data.decode("utf-8").split("\n")
                for k in range(3, len(lines)):
                    if lines[k].strip() and pick(json.loads(lines[k])):
                        obj = json.loads(lines[k])
                        fn(obj)
                        lines[k] = json.dumps(obj, ensure_ascii=False)
                        return "\n".join(lines).encode("utf-8")
                raise AssertionError("nincs a feltételnek megfelelő minta")
            return apply

        def change_target(o):
            o["text"] = o["text"][:-1] + ("x" if o["text"][-1] != "x" else "y")

        def swap_roles(o):
            o["text"] = o["text"].replace("User: ", "@@").replace("AI: ", "User: ").replace("@@", "AI: ")

        def mark_complete(o):
            for g in o["messages"]:
                g["complete"] = True
            o["lossless"], o["content_complete"] = True, True

        def flip_fixture(o):
            o["fixture"] = False

        def other_conversation(o):
            o["conversation_id"] = "mtfx_syn_0030"

        def wrong_turn(o):
            o["target_turn"] += 2

        for name, fn, needle in (("target", change_target, ""), ("roles", swap_roles, ""), ("fixture", flip_fixture, "tesztadat"),
                                 ("otherconv", other_conversation, ""), ("turn", wrong_turn, "")):
            with self.subTest(tamper=name):
                _run, problems = self.tamper(name, ["samples_train_R2.jsonl"], edit_sample(fn))
                self.assertDetected(problems, needle or None)
        with self.subTest(tamper="complete"):
            _run, problems = self.tamper("complete", ["samples_train_R1.jsonl"], edit_sample(mark_complete, pick=lambda o: bool(o["history_truncation"])))
            self.assertDetected(problems)

    def test_dropped_swapped_or_reordered_records_are_detected(self):
        _run, problems = self.tamper("dropsample", ["samples_train_R1.jsonl"], lambda f, d: b"\n".join(d.split(b"\n")[:-2]) + b"\n")
        self.assertDetected(problems)
        _run, problems = self.tamper("dropconv", ["canonical_test.jsonl"], lambda f, d: b"\n".join(d.split(b"\n")[1:]))
        self.assertDetected(problems)

        def reorder(f, d):
            lines = [l for l in d.split(b"\n") if l]
            lines[0], lines[1] = lines[1], lines[0]
            return b"\n".join(lines) + b"\n"

        _run, problems = self.tamper("reorder", ["canonical_train.jsonl"], reorder)
        self.assertDetected(problems)

        def cross(f, d):                                                    # egy beszélgetés áthelyezve egy másik részbe
            return d

        run = self.copy_export("cross")
        train = read_bytes(os.path.join(run, "canonical_train.jsonl")).split(b"\n")
        test = read_bytes(os.path.join(run, "canonical_test.jsonl"))
        with open(os.path.join(run, "canonical_test.jsonl"), "wb") as f:
            f.write(test + train[0] + b"\n")
        with open(os.path.join(run, "canonical_train.jsonl"), "wb") as f:
            f.write(b"\n".join(train[1:]))
        self.assertDetected(mx.verify_export(self.resign(run, ["canonical_test.jsonl", "canonical_train.jsonl"])))

    def test_changed_canonical_content_is_detected_against_the_source_and_the_manifest(self):
        def edit_first(f, d):
            lines = d.split(b"\n")
            obj = json.loads(lines[0])
            obj["turns"][1]["text"] += " módosítva"
            lines[0] = json.dumps(obj, ensure_ascii=False).encode("utf-8")
            return b"\n".join(lines)

        _run, problems = self.tamper("canon", ["canonical_train.jsonl"], edit_first)
        self.assertDetected(problems, "ellenőrzőösszeg")

    def test_status_marker_and_leftover_tampering_is_detected(self):
        for flag in ("training_ready", "content_verified", "split_approved"):
            with self.subTest(flag=flag):
                run = self.copy_export("status_" + flag)
                p = os.path.join(run, mx.MANIFEST_FILE)
                man = read_json(p)
                man[flag] = True
                write_json(p, man)
                self.assertDetected(mx.verify_export(p), flag)
        run = self.copy_export("marker")
        os.remove(os.path.join(run, mx.FIXTURE_MARKER_FILE))
        p = os.path.join(run, mx.MANIFEST_FILE)
        man = read_json(p)
        del man["outputs"][mx.FIXTURE_MARKER_FILE]
        write_json(p, man)
        self.assertDetected(mx.verify_export(p), "jelölő")
        run = self.copy_export("failed")
        with open(os.path.join(run, mx.FAILED_FILE), "w", encoding="utf-8") as f:
            f.write("hiba\n")
        self.assertDetected(mx.verify_export(os.path.join(run, mx.MANIFEST_FILE)), "FAILED")
        run = self.copy_export("nofixture")                                    # tesztadat export nem `fixture_` mappában
        renamed = os.path.join(os.path.dirname(run), "mt4_valodi_kinezet")
        os.rename(run, renamed)
        self.assertDetected(mx.verify_export(os.path.join(renamed, mx.MANIFEST_FILE)), "fixture_")
        run = self.copy_export("training")
        p = os.path.join(run, mx.MANIFEST_FILE)
        man = read_json(p)
        man["training_data"] = True
        write_json(p, man)
        self.assertDetected(mx.verify_export(p), "training_data")

    def test_excluded_text_injected_into_the_export_is_detected(self):
        def inject(f, d):
            lines = d.split(b"\n")
            obj = json.loads(lines[0])
            obj["turns"][1]["text"] = EXCLUDED_ANSWER
            lines[0] = json.dumps(obj, ensure_ascii=False).encode("utf-8")
            return b"\n".join(lines)

        _run, problems = self.tamper("inject", ["canonical_train.jsonl"], inject)
        self.assertDetected(problems, "kizárt TE-1")

    def test_changed_source_is_detected_only_when_sources_are_checked(self):
        run = self.copy_export("source")
        p = os.path.join(run, mx.MANIFEST_FILE)
        with temporarily(self.conv, read_bytes(self.conv) + b"\n\n"):                      # üres sorok: a sorok tartalma nem változott
            self.assertEqual(mx.verify_export(p), [])
        first = source_lines(self.conv)
        edited = b"\n".join([first[0] + b" "] + first[1:])
        with temporarily(self.conv, edited):
            self.assertDetected(mx.verify_export(p), "forrássor megváltozott")
            self.assertEqual(mx.verify_export(p, check_sources=False), [], "forrás-ellenőrzés nélkül az export önmagában egységes")
        self.assertEqual(mx.verify_export(p), [])


# ---------------------------------------------------------------------------
# minden ellenőrzés a saját üzenetével: egy elrontás több ellenőrzést is elindíthat, ezért a teszt a KONKRÉT üzenet meglétét kéri
# (így egy ellenőrzés kihagyása akkor is látszik, ha egy másik ellenőrzés is jelez)
# ---------------------------------------------------------------------------

class CheckMessageTests(SharedPipeline):
    def resign(self, run, names):
        p = os.path.join(run, mx.MANIFEST_FILE)
        man = read_json(p)
        for n in names:
            man["outputs"][n] = {"sha256": sha(os.path.join(run, n)), "bytes": os.path.getsize(os.path.join(run, n))}
        write_json(p, man)
        return p

    def edit_manifest(self, name, fn):
        run = self.copy_export(name)
        p = os.path.join(run, mx.MANIFEST_FILE)
        man = read_json(p)
        fn(man)
        write_json(p, man)
        return mx.verify_export(p)

    def edit_sample(self, name, split, mode, fn, pick=lambda o: True, start=3):
        """A fájl első, a feltételnek megfelelő (a `start`. sortól) mintáját írja át; a manifest ellenőrzőösszege újra van írva."""
        run = self.copy_export(name)
        fname = f"samples_{split}_{mode}.jsonl"
        path = os.path.join(run, fname)
        lines = read_bytes(path).decode("utf-8").split("\n")
        for k in range(start, len(lines)):
            if lines[k].strip() and pick(json.loads(lines[k])):
                obj = json.loads(lines[k])
                fn(obj)
                lines[k] = json.dumps(obj, ensure_ascii=False)
                break
        else:
            raise AssertionError("nincs a feltételnek megfelelő minta")
        with open(path, "wb") as f:
            f.write("\n".join(lines).encode("utf-8"))
        return mx.verify_export(self.resign(run, [fname]))

    def assertHas(self, problems, needle):
        self.assertTrue(any(needle in p for p in problems), (needle, problems[:6]))

    @staticmethod
    def seg(o, kind):
        return next(g for g in o["messages"] if g["kind"] == kind)

    @staticmethod
    def flip(text, pos):
        return text[:pos] + ("X" if text[pos] != "X" else "Y") + text[pos + 1:]

    def other_split_id(self, split):
        return next(c["id"] for c in self.man4["conversations"] if c["split"] != split)

    def test_sample_level_checks_each_report_their_own_message(self):
        deep = lambda o: o["target_turn"] >= 3
        trunc = lambda o: bool(o["history_truncation"])

        def in_text(field_seg, fn_pos=lambda g: g["start"]):
            def apply(o):
                g = self.seg(o, field_seg)
                o["text"] = self.flip(o["text"], fn_pos(g))
            return apply

        def first_msg(o):
            g = o["messages"][0]
            o["text"] = self.flip(o["text"], g["start"])

        def junk_unmarked(o):
            g = o["messages"][0]
            o["text"] = o["text"][:g["start"]] + "Z" * (g["end"] - g["start"]) + o["text"][g["end"]:]
            g["complete"] = False

        def target_incomplete(o):
            g = self.seg(o, "target")
            o["text"] = self.flip(o["text"], g["start"])
            g["complete"] = False

        def excluded(o):
            mode = o["mode"]
            texts = [t["text"] for t in self.source_objs()[o["conversation_id"]]["turns"]]
            texts[0] = EXCLUDED_ANSWER
            text, segs = mx.render(mode, texts, o["target_turn"])
            o["text"], o["messages"] = text, segs
            o["target"] = {"start": segs[-1]["start"], "end": segs[-1]["end"]}

        def target_span(o):
            o["target"]["end"] -= 1

        cases = [
            ("split", "train", "R2", lambda o: o.update(conversation_id=self.other_split_id("train")), None, "nincs ebben a részben"),
            ("sampleid", "train", "R2", lambda o: o.update(sample_id=o["sample_id"] + "x"), None, "hibás vagy ismétlődő sample_id"),
            ("trace", "train", "R2", lambda o: o["source"].update(line=o["source"]["line"] + 1), None, "visszakövetési adat nem egyezik"),
            ("tail", "train", "R2", in_text("current"), deep, "az aktuális kérés vagy a cél nem egyezik a forrással"),
            ("r2hist", "train", "R2", first_msg, deep, "az R2 szöveg nem a teljes forrás-előzmény"),
            ("r1prefix", "train", "R1", first_msg, deep, "az R1 előtag nem egyezik a memory.build_prompt_context kimenetével"),
            ("r1hist", "train", "R1", first_msg, deep, "az R1 előzmény nem a forrás bájt-pontos vagy jelölt csonkolása"),
            ("segcomplete", "train", "R1", lambda o: o["messages"][0].update(complete=True), trunc, "`complete` jelzője hibás"),
            ("segunmarked", "train", "R1", junk_unmarked, deep, "nem teljes szegmens nem jelölt csonkolás"),
            ("curtarget", "train", "R2", target_incomplete, deep, "az aktuális kérés vagy a cél nem teljes"),
            ("span", "train", "R2", target_span, None, "target span nem a teljes cél-üzenet"),
            ("lossless", "train", "R2", lambda o: o.update(lossless=not o["lossless"]), None, "a lossless jelzés hibás"),
            ("r2lossless", "train", "R2", lambda o: o.update(lossless=False), None, "az R2 minta nem veszteségmentes"),
            ("excluded", "train", "R2", excluded, deep, "kizárt TE-1 sor szövege a mintában"),
            ("rerender", "train", "R2", lambda o: o.update(text=o["text"] + "!"), None, "újrarenderelttel"),
        ]
        for name, split, mode, fn, pick, needle in cases:
            with self.subTest(check=name):
                problems = self.edit_sample("chk_" + name, split, mode, fn, pick or (lambda o: True))
                self.assertHas(problems, needle)

    def test_sample_order_completeness_and_index_checks_report_their_own_message(self):
        run = self.copy_export("order")
        fname = "samples_train_R2.jsonl"
        path = os.path.join(run, fname)
        lines = read_bytes(path).decode("utf-8").split("\n")
        lines[3], lines[4] = lines[4], lines[3]
        with open(path, "wb") as f:
            f.write("\n".join(lines).encode("utf-8"))
        self.assertHas(mx.verify_export(self.resign(run, [fname])), "a minták sorrendje nem a beszélgetés/forduló sorrend")
        run = self.copy_export("missing_sample")
        path = os.path.join(run, fname)
        lines = read_bytes(path).decode("utf-8").split("\n")
        del lines[2]
        with open(path, "wb") as f:
            f.write("\n".join(lines).encode("utf-8"))
        self.assertHas(mx.verify_export(self.resign(run, [fname])), "hiányosak vagy hibás sorrendűek")
        run = self.copy_export("index")
        path = os.path.join(run, mx.EXPORT_INDEX)
        lines = read_bytes(path).decode("utf-8").split("\n")
        parts = lines[1].split("\t")
        parts[-1] = str(int(parts[-1]) + 1)
        lines[1] = "\t".join(parts)
        with open(path, "wb") as f:
            f.write("\n".join(lines).encode("utf-8"))
        self.assertHas(mx.verify_export(self.resign(run, [mx.EXPORT_INDEX])), "export_index.tsv sora nem egyezik")

    def test_manifest_level_checks_report_their_own_message(self):
        self.assertHas(self.edit_manifest("kind", lambda m: m.update(data_kind="dataset")), "data_kind és a fixture jelölés ellentmond")
        self.assertHas(self.edit_manifest("samplecount", lambda m: m["splits"]["train"]["samples"]["R2"].update(total=m["splits"]["train"]["samples"]["R2"]["total"] + 1)),
                       "mintaszáma nem egyezik a képlettel")
        self.assertHas(self.edit_manifest("mt2count", lambda m: m["expected_from_mt2"]["train"].update(conversations=m["expected_from_mt2"]["train"]["conversations"] + 1)),
                       "nem egyezik az MT-2 manifest darabszámaival")

    def test_canonical_level_checks_report_their_own_message(self):
        def edit_line(name, k, fn, split="train"):
            run = self.copy_export(name)
            fname = f"canonical_{split}.jsonl"
            path = os.path.join(run, fname)
            lines = read_bytes(path).split(b"\n")
            obj = json.loads(lines[k])
            fn(obj)
            lines[k] = json.dumps(obj, ensure_ascii=False).encode("utf-8")
            with open(path, "wb") as f:
                f.write(b"\n".join(lines))
            return mx.verify_export(self.resign(run, [fname]))

        def swap_roles(o):
            o["turns"][0]["role"], o["turns"][1]["role"] = "assistant", "user"

        self.assertHas(edit_line("roles", 0, swap_roles), "a szerepek sorrendje nem user/assistant váltakozás")
        self.assertHas(edit_line("recfixture", 0, lambda o: o["meta"].update(fixture=False)), "meta.fixture jelölése nem egyezik")
        # a sorrend: két beszélgetés cseréje a fájlban ÉS a manifestben, hogy csak a sorrend-ellenőrzés jelezzen
        run = self.copy_export("canon_order")
        fname = "canonical_train.jsonl"
        path = os.path.join(run, fname)
        lines = read_bytes(path).split(b"\n")
        lines[0], lines[1] = lines[1], lines[0]
        with open(path, "wb") as f:
            f.write(b"\n".join(lines))
        p = self.resign(run, [fname])
        man = read_json(p)
        train = [c for c in man["conversations"] if c["split"] == "train"]
        a, b = man["conversations"].index(train[0]), man["conversations"].index(train[1])
        man["conversations"][a], man["conversations"][b] = man["conversations"][b], man["conversations"][a]
        man["conversations"][a]["canonical_line"], man["conversations"][b]["canonical_line"] = 1, 2
        write_json(p, man)
        self.assertHas(mx.verify_export(p), "a beszélgetések sorrendje nem a forrás sorrendje")
        # egy beszélgetés két részben
        run = self.copy_export("dupconv")
        p = os.path.join(run, mx.MANIFEST_FILE)
        train_first = read_bytes(os.path.join(run, "canonical_train.jsonl")).split(b"\n")[0]
        with open(os.path.join(run, "canonical_test.jsonl"), "ab") as f:
            f.write(train_first + b"\n")
        man = read_json(p)
        entry = dict(next(c for c in man["conversations"] if c["split"] == "train"))
        n_test = sum(1 for c in man["conversations"] if c["split"] == "test")
        entry.update(split="test", canonical_line=n_test + 1)
        man["conversations"].append(entry)
        write_json(p, man)
        self.assertHas(mx.verify_export(self.resign(run, ["canonical_test.jsonl"])), "a beszélgetés több részben is szerepel")

    def test_input_level_checks_report_their_own_message(self):
        m = read_json(self.mt2_path)
        # MT-2 manifest belső egysége
        bad = json.loads(json.dumps(m))
        bad["splits"]["train"]["conversations"] += 1
        self.assertHas(mx.check_mt2_structure(bad), "részének darabszáma nem egyezik a kijelöléssel")
        bad = json.loads(json.dumps(m))
        bad["status"] = "failed"
        self.assertHas(mx.check_mt2_structure(bad), "státusza")
        bad = json.loads(json.dumps(m))
        unit = next(u for u, d in bad["units"].items() if len(d["assigned"]) >= 2)
        victim = next(a for a in bad["assignment"] if a["unit"] == unit)
        victim["split"] = next(s for s in mx.SPLITS if s != victim["split"])
        rows = [(a["file"], a["line"], a["id"], a["split"]) for a in bad["assignment"]] + [(h["file"], h["line"], h["id"], "HELD_BACK") for h in bad["held_back"]]
        canon = "\n".join(f"{f}:{ln}:{i}\t{s}" for f, ln, i, s in sorted(rows, key=lambda r: (r[0], r[1])))
        bad["assignment_sha256"] = hashlib.sha256(canon.encode("utf-8")).hexdigest()          # a sha egyezik: csak az egység-ellenőrzés jelezhet
        self.assertHas(mx.check_mt2_structure(bad), "több részbe esik")
        # forrás: az azonosító a sorral
        bad = json.loads(json.dumps(m))
        bad["assignment"][0]["id"] = "mtfx_syn_9998"
        with self.assertRaises(mx.StaleInputError) as ctx:
            mx.load_sources(bad, "fixture")
        self.assertIn("azonosítója nem egyezik", str(ctx.exception))
        # kizárási lista és TE-1 manifest ellenőrzőösszege, MT-3 jelentés
        convs, _ = mx.load_sources(m, "fixture")
        bad = json.loads(json.dumps(m))
        bad["inputs"]["exclusions"]["sha256"] = "0" * 64
        with self.assertRaises(mx.StaleInputError) as ctx:
            mx.check_exclusions_and_status(bad, convs, "fixture", False)
        self.assertIn("kizárási lista megváltozott", str(ctx.exception))
        bad = json.loads(json.dumps(m))
        bad["inputs"]["te1_export"]["manifest_sha256"] = "0" * 64
        with self.assertRaises(mx.StaleInputError) as ctx:
            mx.check_te1_exclusions(bad, convs, False)
        self.assertIn("manifestje nem egyezik", str(ctx.exception))
        rep = read_json(self.report)
        rep["status"] = "failed"
        bad_report = os.path.join(self.base.tmp, "report_failed.json")
        write_json(bad_report, rep)
        bad = json.loads(json.dumps(m))
        bad["inputs"]["mt3_report"] = dict(bad["inputs"]["mt3_report"], path=bad_report)
        with self.assertRaises(mx.StaleInputError) as ctx:
            mx.check_exclusions_and_status(bad, convs, "fixture", False)
        self.assertIn("nem lezárt", str(ctx.exception))
        stray = copy.deepcopy(convs[0])                                                      # az MT-3 jelentésben nem szereplő sor
        stray["entry"] = dict(stray["entry"], line=9999)
        with self.assertRaises(mx.StaleInputError) as ctx:
            mx.check_exclusions_and_status(m, convs + [stray], "fixture", False)
        self.assertIn("nincs az MT-3 jelentésben", str(ctx.exception))

    def test_the_held_back_rule_and_the_mode_choice_have_their_own_messages(self):
        m = read_json(self.mt2_path)
        convs, _ = mx.load_sources(m, "fixture")
        extra = ExclusionTests.fabricate(self, "mtfx_syn_0005")
        with self.assertRaises(mx.ExclusionViolationError) as ctx:
            mx.check_exclusions_and_status(m, convs + [extra], "fixture", False)
        self.assertIn("Visszatartott rekord kerülne az exportba", str(ctx.exception))
        with self.assertRaises(mx.RefusedError) as ctx:
            mx.run_export(self.mt2_path, self.base.out, "valami")
        self.assertIn("dataset vagy fixture kell legyen", str(ctx.exception), "a mód-választás saját üzenete, nem a manifest-egyezésé")

    def test_input_changed_while_writing_is_detected_after_the_read_back(self):
        original = read_bytes(self.conv)
        real = mx.verify_export

        def tampering(*a, **kw):
            with open(self.conv, "ab") as f:
                f.write(b"\n")
            return real(*a, **kw)

        try:
            with mock.patch.object(mx, "verify_export", tampering):
                with self.assertRaises(mx.ChangedInputError) as ctx:
                    self.export("fixture_during_write")
        finally:
            with open(self.conv, "wb") as f:
                f.write(original)
        self.assertIn("kiírás közben", str(ctx.exception))
        self.assertFalse(os.path.exists(os.path.join(self.base.out, "fixture_during_write", mx.MANIFEST_FILE)))

    def test_a_renderer_whose_segments_contradict_its_own_text_withholds_the_conversations_instead_of_exporting_them(self):
        real_r2 = mx.render_r2

        def inconsistent(texts, t):
            text, segs = real_r2(texts, t)
            if t >= 3:
                text = text[:segs[0]["start"]] + "Q" + text[segs[0]["start"] + 1:]
            return text, segs

        with mock.patch.object(mx, "render_r2", inconsistent):
            man = self.export("fixture_inconsistent", modes=("R2",))
        self.assertEqual(sum(man["splits"][s]["conversations"] for s in mx.SPLITS), 0)
        self.assertEqual(len(man["withheld"]), 36)
        self.assertTrue(all("szegmens határai nem egyeznek" in w["reason"] for w in man["withheld"]))
        self.assertEqual(mx.EXIT_ATTENTION, 1)
        self.assertTrue(man["warnings"])

    def test_a_renderer_bug_is_caught_by_the_independent_read_back_even_if_export_and_check_share_the_renderer(self):
        real_r2, real_r1 = mx.render_r2, mx.render_r1

        def bad_r2(texts, t):                                     # az első váltás kimarad, de a szegmensek önmagukban egységesek
            if t < 3:
                return real_r2(texts, t)
            text, segs = real_r2(texts[2:], t - 2)
            for g in segs:
                g["turn"] += 2
            return text, segs

        def bad_r1(texts, t):                                     # az előtag helyett a teljes előzmény kerül be
            return real_r2(texts, t) if t >= 3 else real_r1(texts, t)

        for name, target, mode in (("badr2", "render_r2", "R2"), ("badr1", "render_r1", "R1")):
            with self.subTest(renderer=name):
                fake = bad_r2 if mode == "R2" else bad_r1
                with mock.patch.object(mx, target, fake):
                    with self.assertRaises(mx.VerificationError) as ctx:
                        self.export("fixture_" + name, modes=(mode,))
                self.assertEqual(ctx.exception.exit_code, mx.EXIT_VERIFY)
                run = os.path.join(self.base.out, "fixture_" + name)
                self.assertFalse(os.path.exists(os.path.join(run, mx.MANIFEST_FILE)), "hibás renderelésű export nem véglegesedik")
                self.assertTrue(os.path.isfile(os.path.join(run, mx.FAILED_FILE)))


# ---------------------------------------------------------------------------
# parancssor
# ---------------------------------------------------------------------------

class CliTests(SharedPipeline):
    def cli(self, *args):
        env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
        return subprocess.run([sys.executable, TOOL_PATH, *args], capture_output=True, text=True, encoding="utf-8", env=env)

    def test_exit_codes_and_output_through_a_real_process(self):
        r = self.cli("--mode", "fixture", "--mt2-manifest", self.mt2_path, "--out-dir", self.base.out, "--run-name", "fixture_cli")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("NEM training-ready", r.stdout)
        self.assertIn("R1:", r.stdout)
        self.assertIn("train", r.stdout)
        p = os.path.join(self.base.out, "fixture_cli", mx.MANIFEST_FILE)
        self.assertEqual(self.cli("--verify-export", p).returncode, 0)
        self.assertEqual(self.cli("--mode", "fixture", "--mt2-manifest", self.mt2_path, "--out-dir", self.base.out, "--run-name", "fixture_cli").returncode,
                         mx.EXIT_OUTPUT)
        self.assertEqual(self.cli("--mode", "dataset", "--mt2-manifest", self.mt2_path, "--out-dir", self.base.out, "--run-name", "mt4_x").returncode,
                         mx.EXIT_REFUSED)
        self.assertEqual(self.cli("--mode", "fixture", "--mt2-manifest", os.path.join(self.base.tmp, "nincs.json"), "--out-dir", self.base.out).returncode,
                         mx.EXIT_INPUT)
        self.assertEqual(self.cli("--mode", "fixture").returncode, 2)
        with open(os.path.join(self.base.out, "fixture_cli", "canonical_train.jsonl"), "ab") as f:
            f.write(b"x")
        r = self.cli("--verify-export", p)
        self.assertEqual(r.returncode, mx.EXIT_VERIFY)
        self.assertIn("megváltozott", r.stderr)
        self.assertEqual(self.cli("--verify-export", os.path.join(self.base.tmp, "nincs.json")).returncode, mx.EXIT_VERIFY)

    def test_stale_input_gives_the_stale_exit_code_in_process(self):
        with temporarily(self.conv, read_bytes(self.conv) + b"\n"):
            self.assertEqual(mx._main(["--mode", "fixture", "--mt2-manifest", self.mt2_path, "--out-dir", self.base.out, "--run-name", "fixture_cli_stale"]),
                             mx.EXIT_STALE)
        self.assertFalse(os.path.exists(os.path.join(self.base.out, "fixture_cli_stale")))


# ---------------------------------------------------------------------------
# valós TE-1 export (csak olvasva): a hat kizárás érvényben marad
# ---------------------------------------------------------------------------

SIX = ["uncertainty_source_request_0220", "uncertainty_source_request_0602", "uncertainty_source_request_0829",
       "uncertainty_source_request_0849", "uncertainty_source_request_0864", "uncertainty_source_request_0898"]


@unittest.skipUnless(os.path.isdir(os.path.join(REPO_ROOT, "data", "clean")), "nincs data/clean")
class RealExportTests(unittest.TestCase):
    """A valódi TE-1 export (4494 példa, hat kizárt sor) mint referencia; a beszélgetések mesterséges tesztadatok."""

    @classmethod
    def setUpClass(cls):
        cls.base = S.Base("write_convs")
        cls.base.setUp()
        cls.clean_files = sorted(glob.glob(os.path.join(REPO_ROOT, "data", "clean", "*.jsonl")))
        cls.before = {p: sha(p) for p in cls.clean_files}
        cls.te1 = te1.run_export(os.path.join(cls.base.tmp, "te1real"), run_name="real")["run_dir"]
        cls.recs = S.corpus(30, seed=230)
        cls.man2, cls.conv, cls.report = cls.base.pipeline(cls.recs, targets=(24, 3, 3), export_dir=cls.te1, run_name="real")
        cls.mt2_path = os.path.join(cls.man2["run_dir"], "split_manifest.json")
        cls.man4 = mx.run_export(cls.mt2_path, cls.base.out, "fixture", run_name="fixture_real")
        cls.rows = {}
        for p in cls.clean_files:
            for line in read_bytes(p).decode("utf-8").split("\n"):
                if line.strip():
                    o = json.loads(line)
                    if o["id"] in SIX:
                        cls.rows[o["id"]] = o

    @classmethod
    def tearDownClass(cls):
        cls.base.tearDown()

    def test_the_six_exclusions_are_recorded_and_the_export_succeeds(self):
        e = self.man4["inputs"]["te1_export"]
        self.assertEqual(e["excluded_rows"], sorted(SIX))
        self.assertEqual(e["rows"], 4494)
        self.assertEqual(e["source_rows_verified"], 6)
        self.assertEqual(self.man4["exclusion_guard"]["te1_excluded_rows"], sorted(SIX))
        self.assertEqual(len(self.man4["exclusion_guard"]["excluded_text_sha256"]), 12, "6 sor × (kérdés, válasz)")
        self.assertEqual(self.man4["withheld"], [])
        self.assertEqual(mx.verify_export(os.path.join(self.man4["run_dir"], mx.MANIFEST_FILE)), [])
        blob = b"".join(read_bytes(os.path.join(self.man4["run_dir"], n)) for n in os.listdir(self.man4["run_dir"]) if n != mx.MANIFEST_FILE)
        for rid in SIX:
            self.assertNotIn(rid.encode(), blob)

    def test_each_of_the_six_excluded_rows_texts_is_refused_in_an_exported_conversation(self):
        m = read_json(self.mt2_path)
        convs, _ = mx.load_sources(m, "fixture")
        cached = te2.load_te1_export(self.te1)
        refused = 0
        with mock.patch.object(mx.te2, "load_te1_export", lambda d: cached):
            for rid in SIX:
                for field, idx in (("instruction", 0), ("output", 1)):
                    with self.subTest(row=rid, field=field):
                        bad = copy.deepcopy(convs[0])
                        bad["obj"]["turns"][idx]["text"] = self.rows[rid][field]
                        with self.assertRaises(mx.ExclusionViolationError) as ctx:
                            mx.check_exclusions_and_status(m, [bad] + convs[1:], "fixture", False)
                        self.assertIn(rid, str(ctx.exception))
                        refused += 1
        self.assertEqual(refused, 12)

    def test_real_data_and_export_are_untouched_and_no_multiturn_data_exists(self):
        self.assertEqual(self.before, {p: sha(p) for p in self.clean_files})
        for kind in ("raw", "clean", "rejected", "inbox"):
            self.assertEqual(glob.glob(os.path.join(REPO_ROOT, "data", kind, "**", "*multiturn*"), recursive=True), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
