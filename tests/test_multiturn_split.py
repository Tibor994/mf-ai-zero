"""
MF-AI-Zero - MT-2 teszt: tools/multiturn_split.py (csoportokat egyben tartó, reprodukálható felosztás).

FONTOS: kizárólag mesterséges tesztadatot használ. A beszélgetéseket a teszt generálja (`mtfx_syn_NNNN`, fixture mód,
`meta.fixture: true`): valós magyar szavakból (tests/fixtures/multiturn/synthetic_vocabulary.txt) összeállított,
értelmetlen mondatok, amelyek az MT-1 szűrésén átmennek, de tartalmilag nem beszélgetések. Ez NEM része az 1000
beszélgetéses csomagnak, tanításra nem használható, a valódi datasetet nem érinti. A valós adatos rész
(RealExportPipelineTests) a TE-1 exportot csak OLVASSA. A teszt nem tanít semmit.

Célzott esetek: csoport-integritás (deklarált csoport, persona, láncolt kapcsolat, kivétellel felmentett pár); ismételhetőség
(bemeneti sorrend, fájlfelosztás, ismételt futás, seed); kizárások és visszatartások (MT-3 blokkolt rekord és csoportja, kizárási
lista, kizárás-jelölés); nem elérhető darabszám (csoport nem vágható szét, az eltérés jelentve); elavult vagy megváltozott MT-3
jelentés és bemenet; TE-1 exporttal talált kapcsolatok; részek közötti átfedések; manifest, kimenetek, parancssor.

Futtatás:
    python -m unittest tests.test_multiturn_split
    python tests/test_multiturn_split.py
"""

import copy
import glob
import hashlib
import itertools
import json
import os
import random
import subprocess
import sys
import tempfile
import unittest
from collections import Counter
from unittest import mock

TOOLS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools")
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, TOOLS_DIR)

import dataset_export_train as te1  # noqa: E402
import multiturn_dedupe as dd  # noqa: E402
import multiturn_split as ms  # noqa: E402
import multiturn_validate as mt  # noqa: E402

TOOL_PATH = os.path.join(TOOLS_DIR, "multiturn_split.py")
VOCAB_FILE = os.path.join(REPO_ROOT, "tests", "fixtures", "multiturn", "synthetic_vocabulary.txt")
BANK = mt.load_name_bank()
NOTES = "Mesterséges tesztfixture (MT-0): nem része az 1000 beszélgetéses csomagnak, tanításra nem használható."
DOMAINS = sorted(mt.DOMAINS)
FAMILIES = sorted(mt.FAMILIES)
MARK = "Státusz: teszt; " + te1.EXCLUSION_NOTE_MARKER + ", amíg a felülvizsgálat nem történik meg."
with open(VOCAB_FILE, encoding="utf-8") as _f:
    VOCAB = [w.strip() for w in _f if w.strip()]


def read_bytes(path):
    with open(path, "rb") as f:
        return f.read()


def read_text(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def write_text(path, text):
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)


def write_jsonl(path, rows):
    with open(path, "wb") as f:
        for r in rows:
            f.write((json.dumps(r, ensure_ascii=False) + "\n").encode("utf-8"))


def read_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# mesterséges beszélgetések (MT-1-érvényes, valós szavakból összeállított értelmetlen mondatok)
# ---------------------------------------------------------------------------

def _h(seed, label):
    return int(hashlib.sha256(f"{seed}|{label}".encode()).hexdigest()[:12], 16)


def _sentence(seed, label, n, question=False):
    words = [VOCAB[_h(seed, f"{label}|{k}") % len(VOCAB)] for k in range(n)]
    return " ".join(words).capitalize() + ("?" if question else ".")


def _synth_once(i, seed, salt, family, n_ex, hard):
    fam = family or FAMILIES[i % 9]
    n_ex = n_ex or (3, 4, 4, 5, 5, 6, 6, 7, 8)[_h(seed, f"nex{i}") % 9]
    turns = []
    for k in range(2 * n_ex):
        if k % 2 == 0:
            turns.append({"role": "user", "text": _sentence(seed, f"u{i}|{k}|{salt}", 8 + _h(seed, f"lu{i}{k}") % 7, question=(k % 4 == 0))})
        else:
            turns.append({"role": "assistant", "text": _sentence(seed, f"a{i}|{k}|{salt}", 12 + _h(seed, f"la{i}{k}") % 11)})
    is_hard = hard if hard is not None else (_h(seed, f"hard{i}") % 4 == 0)
    deps = []
    for t in range(3, 2 * n_ex, 2):
        d = 2 if (is_hard and t >= 5) else 1
        deps.append({"turn": t, "on": [t - 2 * d], "depth": d})
    return {
        "id": "mtfx_syn_%04d" % i, "category": "multiturn", "instruction": turns[0]["text"], "input": "", "output": turns[-1]["text"],
        "tags": ["magyar", "instruction_core", "tobbfordulos", mt.FAMILIES[fam]], "difficulty": "medium", "quality_notes": NOTES,
        "source": "test_fixture", "turns": turns,
        "meta": {"family": fam, "skills": [mt.FAMILIES[fam]], "n_exchanges": n_ex, "split_group": "g%04d" % (1000 + i),
                 "persona": "p%03d" % (i % 1000), "persona_names": [], "domain": DOMAINS[_h(seed, f"dom{i}") % 10],
                 "depends": deps, "register": "tegezo", "fixture": True},
    }


def synth(i, seed=1, family=None, n_ex=None, hard=None):
    """Determinisztikus, MT-1-érvényes beszélgetés; ritka érvénytelen mintánál más sózással újragenerálja."""
    for salt in range(20):
        rec = _synth_once(i, seed, salt, family, n_ex, hard)
        if not [e for e in mt.validate_record(rec, "fixture", BANK) if e.severity == "error"]:
            return rec
    raise AssertionError("nem sikerült érvényes mesterséges beszélgetést generálni")


def corpus(n, seed=1, start=0):
    return [synth(start + k, seed) for k in range(n)]


def link(rec, group=None, persona=None):
    if group:
        rec["meta"]["split_group"] = group
    if persona:
        rec["meta"]["persona"] = persona
    return rec


def copy_of(rec, new_id):
    r = copy.deepcopy(rec)
    r["id"] = new_id
    return r


def short_pair(seed):
    """Két beszélgetés rövid, közel azonos kezdő váltással (az MT-3 kísérleti rövid-szöveg kivétele: sample_near_short, review)."""
    a, b = synth(0, seed), synth(1, seed)
    for r, w in ((a, "hétben"), (b, "évben")):
        r["turns"][0]["text"] = f"Hány nap van egy {w}?"
        r["turns"][1]["text"] = f"Egy {w} hét nap van."
        r["instruction"] = r["turns"][0]["text"]
        errs = [e for e in mt.validate_record(r, "fixture", BANK) if e.severity == "error"]
        assert not errs, errs
    return a, b


# ---------------------------------------------------------------------------
# közös tesztkörnyezet: TE-1 export, MT-3 futás, MT-2 futás
# ---------------------------------------------------------------------------

class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = self._tmp.name
        self.out = os.path.join(self.tmp, "out")
        self.conv_dir = os.path.join(self.tmp, "convs")
        os.makedirs(self.conv_dir)
        self._n = 0

    def tearDown(self):
        self._tmp.cleanup()

    def write_convs(self, recs, name=None):
        self._n += 1
        p = os.path.join(self.conv_dir, name or f"c{self._n}.jsonl")
        write_jsonl(p, recs)
        return p

    def export(self, rows=None, name="e1"):
        """Kis TE-1 export (valódi TE-1 eszközzel), egy kizárt sorral."""
        clean = os.path.join(self.tmp, "src_" + name, "clean")           # a TE-1 csak "clean" nevű mappából exportál
        os.makedirs(clean, exist_ok=True)
        lst = os.path.join(self.tmp, f"excl_{name}.txt")
        write_text(lst, "x_excl_0001 | ok | felülvizsgálat\n")
        rows = rows or [("Egy kérdés szám 1 itt?", "", "Egy válasz szám 1, elég hosszú szöveg."), ("Egy kérdés szám 2 itt?", "", "Egy válasz szám 2, elég hosszú szöveg.")]
        data = [{"id": "x_a_%04d" % (i + 1), "category": "simple_qa", "instruction": q, "input": inp, "output": out,
                 "tags": ["magyar"], "difficulty": "easy", "quality_notes": "rendben", "source": "teszt"} for i, (q, inp, out) in enumerate(rows)]
        data.append({"id": "x_excl_0001", "category": "simple_qa", "instruction": "Kizárt kérdés?", "input": "",
                     "output": "Kizárt válasz, amely nem kerülhet be.", "tags": ["magyar"], "difficulty": "easy",
                     "quality_notes": MARK, "source": "teszt"})
        write_jsonl(os.path.join(clean, "a_clean.jsonl"), data)
        return te1.run_export(os.path.join(self.tmp, "te1_" + name), input_dir=clean, exclusions_path=lst, run_name=name)["run_dir"]

    def mt3(self, conv_paths, export_dir="default", exceptions=None, run_name=None):
        """MT-3 futás; visszaadja a dedupe_report.json útvonalát."""
        if export_dir == "default":
            export_dir = self.export(name="d%d" % (self._n + 1000))
        exc_path = None
        if exceptions is not None:
            exc_path = os.path.join(self.tmp, "exceptions_%d.json" % len(os.listdir(self.tmp)))
            write_text(exc_path, json.dumps(exceptions, ensure_ascii=False))
        self._n += 1
        rep = dd.run_from_files(list(conv_paths), os.path.join(self.tmp, "mt3"), "fixture", te1_export=export_dir, exceptions_path=exc_path,
                                run_name=run_name or f"m{self._n}")
        path = os.path.join(rep["run_dir"], "dedupe_report.json")
        self.ensure_tool_sha(path)
        self.export_dir = export_dir
        return path

    @staticmethod
    def ensure_tool_sha(path):
        j = read_json(path)
        if "tool_sha256" not in j:              # az MT-3 jelentés ezt a mezőt adja; itt csak a régi állapot kiegészítése
            j["tool_sha256"] = te1.sha256_file(dd.__file__)
            write_text(path, json.dumps(j, ensure_ascii=False, indent=2) + "\n")

    def pipeline(self, recs, targets=(80, 10, 10), exceptions=None, export_dir="default", **kw):
        conv = self.write_convs(recs)
        report = self.mt3([conv], export_dir, exceptions)
        self._n += 1
        kw.setdefault("run_name", f"s{self._n}")
        man = ms.run_from_files([conv], self.out, "fixture", report, te1_export=self.export_dir if export_dir else None,
                                targets=targets, **kw)
        return man, conv, report

    @staticmethod
    def splits_of(man):
        return {a["id"]: a["split"] for a in man["assignment"]}


def independent_split_check(test, man):
    """A manifestből, az MT-3 jelentéstől függetlenül újraszámolt csoport-integritás: minden egység egy részben."""
    by_unit = {}
    for a in man["assignment"]:
        by_unit.setdefault(a["unit"], set()).add(a["split"])
    test.assertTrue(all(len(v) == 1 for v in by_unit.values()), {k: v for k, v in by_unit.items() if len(v) != 1})


# ---------------------------------------------------------------------------
# tiszta függvények
# ---------------------------------------------------------------------------

class HelperTests(unittest.TestCase):
    def test_parse_targets_and_scaled_ideal(self):
        self.assertEqual(ms.parse_targets("800,100,100"), (800, 100, 100))
        self.assertEqual(ms.parse_targets("8; 1;1"), (8, 1, 1))
        for bad in ("1,2", "a,b,c", "-1,2,3", "0,0,0", "1,2,3,4"):
            with self.assertRaises(Exception, msg=bad):
                ms.parse_targets(bad)
        self.assertEqual(ms.scaled_ideal(1000, (800, 100, 100)), [800, 100, 100])
        self.assertEqual(ms.scaled_ideal(100, (800, 100, 100)), [80, 10, 10])
        self.assertEqual(ms.scaled_ideal(83, (800, 100, 100)), [67, 8, 8], "legnagyobb maradék: 66,4/8,3/8,3 -> a maradék az első helyre")
        self.assertEqual(sum(ms.scaled_ideal(97, (800, 100, 100))), 97)
        self.assertEqual(ms.scaled_ideal(0, (800, 100, 100)), [0, 0, 0])
        self.assertEqual(ms.scaled_ideal(2, (1, 1, 1)), [1, 1, 0], "azonos maradéknál a sorrend: train, validation, test")
        self.assertEqual(ms.scaled_ideal(1, (1, 1, 1)), [1, 0, 0])
        for total in range(0, 60):
            got = ms.scaled_ideal(total, (5, 3, 2))
            self.assertEqual(sum(got), total)
            self.assertTrue(all(abs(g - total * t / 10) < 1 for g, t in zip(got, (5, 3, 2))))

    def test_hash_order_is_deterministic_and_independent_of_python_hash_randomization(self):
        self.assertEqual(ms.hkey("s", "a"), hashlib.sha256(b"s|a").hexdigest())
        self.assertNotEqual(ms.hkey("s", "a"), ms.hkey("s2", "a"))
        vals = [ms.unit_float("seed", f"u{k}") for k in range(500)]
        self.assertTrue(all(0.0 <= v < 1.0 for v in vals))
        self.assertGreater(len(set(vals)), 490)
        self.assertTrue(0.35 < sum(vals) / len(vals) < 0.65)
        code = "import sys; sys.path.insert(0, %r); import multiturn_split as m; print(m.unit_float('seed', 'u7'))" % TOOLS_DIR
        outs = {subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=dict(os.environ, PYTHONHASHSEED=str(s))).stdout.strip()
                for s in (1, 2)}
        self.assertEqual(len(outs), 1)
        self.assertEqual(float(outs.pop()), ms.unit_float("seed", "u7"))

    def test_length_band_and_hard_definition(self):
        self.assertEqual([ms.length_band(n) for n in range(3, 9)], ["3-4", "3-4", "5-6", "5-6", "7-8", "7-8"])
        self.assertEqual(ms.length_band(9), "other")
        self.assertEqual(ms.HARD_DEPTH, 2)
        self.assertEqual(ms.HARD_FAMILIES, {"F4", "F7"})

    def test_best_fill_is_the_exact_minimum_of_the_total_deviation(self):
        rng = random.Random(3)
        for _ in range(400):
            total = rng.randint(1, 30)
            n_val, n_test = rng.randint(0, total), rng.randint(0, total)
            if n_val + n_test > total:
                continue
            ideal = (total - n_val - n_test, n_val, n_test)
            a, b = rng.randint(0, total), rng.randint(0, total)
            s1 = rng.randint(0, total)
            x, y, cost = ms.best_fill(a, b, s1, ideal)
            self.assertTrue(x >= 0 and y >= 0 and x + y <= s1)
            brute = min(abs(total - (a + i) - (b + j) - ideal[0]) + abs(a + i - n_val) + abs(b + j - n_test)
                        for i in range(s1 + 1) for j in range(s1 + 1 - i))
            self.assertEqual(cost, brute, (a, b, s1, ideal))


def make_units(sizes, prefix="u", families=None):
    units = []
    for i, s in enumerate(sizes):
        feats = Counter()
        for k in range(s):
            fam = (families or FAMILIES)[(i + k) % len(families or FAMILIES)]
            feats["family:" + fam] += 1
            feats["length:3-4"] += 1
            feats["domain:vasarlas"] += 1
            feats["hard:routine"] += 1
        units.append({"id": f"{prefix}{i:04d}", "size": s, "feats": feats})
    return units


def counts_of(units, assign):
    c = Counter()
    for u in units:
        c[assign[u["id"]]] += u["size"]
    return tuple(c[s] for s in ms.SPLITS)


def cost_of(counts, ideal):
    return sum(abs(a - b) for a, b in zip(counts, ideal))


class AssignUnitsTests(unittest.TestCase):
    def test_singles_only_hit_the_exact_counts_at_full_scale(self):
        units = make_units([1] * 1000)
        assign, info = ms.assign_units(units, (800, 100, 100), "seed", stratify=False)
        self.assertEqual(counts_of(units, assign), (800, 100, 100))
        self.assertEqual(set(assign.values()), set(ms.SPLITS))

    def test_groups_are_atomic_and_exact_counts_are_reached_when_attainable(self):
        rng = random.Random(11)
        sizes = [1] * 700 + [2] * 90 + [3] * 30 + [4] * 5 + [5] * 2
        rng.shuffle(sizes)
        units = make_units(sizes)
        total = sum(sizes)
        ideal = tuple(ms.scaled_ideal(total, (800, 100, 100)))
        assign, _ = ms.assign_units(units, ideal, "s1")
        self.assertEqual(counts_of(units, assign), ideal)
        self.assertEqual(set(assign), {u["id"] for u in units})

    def test_dp_reaches_the_brute_force_optimum_on_small_hard_instances(self):
        rng = random.Random(5)
        checked = 0
        for _ in range(60):
            sizes = [rng.choice((1, 2, 3, 4, 5)) for _ in range(rng.randint(2, 7))]
            total = sum(sizes)
            targets = (rng.randint(1, 8), rng.randint(0, 4), rng.randint(0, 4))
            ideal = tuple(ms.scaled_ideal(total, targets)) if sum(targets) else (total, 0, 0)
            units = make_units(sizes)
            assign, _ = ms.assign_units(units, ideal, "brute", stratify=False)
            got = cost_of(counts_of(units, assign), ideal)
            best = min(cost_of(tuple(sum(s for s, p in zip(sizes, placement) if p == k) for k in range(3)), ideal)
                       for placement in itertools.product(range(3), repeat=len(sizes)))
            self.assertEqual(got, best, (sizes, ideal))
            checked += 1
        self.assertEqual(checked, 60)

    def test_unattainable_counts_keep_groups_whole_and_report_the_smallest_deviation(self):
        units = make_units([3, 3, 3, 3])
        assign, _ = ms.assign_units(units, (8, 2, 2), "x", stratify=False)
        counts = counts_of(units, assign)
        self.assertEqual(cost_of(counts, (8, 2, 2)), 4, counts)
        self.assertTrue(all(c % 3 == 0 for c in counts), "csak egész csoportok: minden rész darabszáma a 3 többszöröse")
        self.assertEqual(sum(counts), 12)
        units = make_units([30] + [1] * 70)
        assign, _ = ms.assign_units(units, (80, 10, 10), "x")
        self.assertEqual(assign["u0000"], "train", "a nagy csoport nem fér a kisebb részbe: a train részbe kerül")
        self.assertEqual(counts_of(units, assign), (80, 10, 10))

    def test_result_does_not_depend_on_the_order_of_the_units(self):
        units = make_units([1] * 120 + [2] * 20 + [3] * 6)
        ideal = tuple(ms.scaled_ideal(sum(u["size"] for u in units), (8, 1, 1)))
        first, _ = ms.assign_units(units, ideal, "seedA")
        shuffled = list(units)
        random.Random(9).shuffle(shuffled)
        second, _ = ms.assign_units(shuffled, ideal, "seedA")
        self.assertEqual(first, second)
        third, _ = ms.assign_units(units, ideal, "seedB")
        self.assertNotEqual(first, third, "más seed más kijelölést ad")
        self.assertEqual(counts_of(units, third), ideal)

    def test_multi_member_units_are_shared_proportionally_among_the_parts(self):
        units = make_units([1] * 700 + [2] * 100)
        ideal = tuple(ms.scaled_ideal(900, (800, 100, 100)))
        assign, info = ms.assign_units(units, ideal, "prop", stratify=False)
        self.assertEqual(counts_of(units, assign), ideal)
        multi = Counter(assign[u["id"]] for u in units if u["size"] == 2)
        self.assertEqual(sum(multi.values()), 100)
        self.assertEqual(multi["validation"], 10, "a 200 többtagú rekord 22,2%-a: a 90 validation-rekordból 20 -> 10 pár")
        self.assertEqual(multi["test"], 10)
        self.assertEqual(info["dp_target"], {"validation_from_multi": 20, "test_from_multi": 20})

    def test_ideal_must_add_up(self):
        with self.assertRaises(ValueError):
            ms.assign_units(make_units([1, 1, 1]), (1, 1, 2), "s")
        assign, info = ms.assign_units([], (0, 0, 0), "s")
        self.assertEqual(assign, {})

    def test_stratification_only_swaps_equal_sized_units_and_lowers_the_loss(self):
        rng = random.Random(4)
        sizes = [1] * 160 + [2] * 20
        units = make_units(sizes)
        for u in units:
            fam = FAMILIES[rng.randrange(9)]
            u["feats"] = Counter({"family:" + fam: u["size"], "length:3-4": u["size"], "domain:vasarlas": u["size"],
                                  ("hard:hard" if rng.random() < 0.3 else "hard:routine"): u["size"]})
        total = sum(sizes)
        ideal = tuple(ms.scaled_ideal(total, (8, 1, 1)))
        plain, info0 = ms.assign_units(units, ideal, "st", stratify=False)
        strat, info1 = ms.assign_units(units, ideal, "st", stratify=True, min_hard_test=0)
        self.assertIsNone(info0["stratification"])
        s = info1["stratification"]
        self.assertLess(s["loss_after"], s["loss_before"])
        self.assertGreater(s["swaps"], 0)
        self.assertEqual(counts_of(units, plain), counts_of(units, strat), "a rétegzés a darabszámot nem változtatja")
        self.assertEqual(counts_of(units, strat), ideal)
        for uid, part in strat.items():          # a csere csak egész egységeket mozgat; a méret-megőrzés a darabszám-azonosságból is látszik
            self.assertIn(part, ms.SPLITS)

    def test_hard_minimum_is_pursued_when_hard_units_exist(self):
        units = make_units([1] * 100)
        for k, u in enumerate(units):
            u["feats"]["hard:routine"] = 0
            u["feats"]["hard:hard" if k % 5 == 0 else "hard:routine"] += 1
        ideal = (80, 10, 10)
        assign, info = ms.assign_units(units, ideal, "hard", min_hard_test=4)
        hard_test = sum(1 for u in units if assign[u["id"]] == "test" and u["feats"]["hard:hard"])
        self.assertGreaterEqual(hard_test, 4)
        self.assertEqual(counts_of(units, assign), ideal)


class RecordFeatureTests(Base):
    def test_hard_flag_length_band_and_counts_come_from_the_validated_records(self):
        recs = [synth(0, 5, family="F4", n_ex=3, hard=False), synth(1, 5, family="F1", n_ex=4, hard=False),
                synth(2, 5, family="F1", n_ex=6, hard=True), synth(3, 5, family="F7", n_ex=8, hard=False)]
        path = self.write_convs(recs)
        loaded, infos = ms.load_conversations([path], "fixture", BANK)
        self.assertEqual([r["hard"] for r in loaded], [True, False, True, True], "F4/F7 vagy mélység >= 2")
        self.assertEqual([r["depth_max"] for r in loaded], [1, 1, 2, 1])
        self.assertEqual([ms.length_band(r["n_exchanges"]) for r in loaded], ["3-4", "3-4", "5-6", "7-8"])
        self.assertEqual([(r["messages"], r["n_exchanges"]) for r in loaded], [(6, 3), (8, 4), (12, 6), (16, 8)])
        self.assertEqual([r["marker"] for r in loaded], [False] * 4)
        self.assertEqual([(r["file"], r["line"]) for r in loaded], [(infos[0]["path"], k) for k in (1, 2, 3, 4)])
        lines = read_bytes(path).split(b"\n")
        self.assertEqual([r["line_sha256"] for r in loaded], [hashlib.sha256(lines[k]).hexdigest() for k in range(4)])
        self.assertEqual(infos[0]["records"], 4)


class VerifySplitTests(Base):
    """A független ellenőrzés kifejezetten hibás kijelöléseken: minden szabály önállóan jelez."""

    def setUp(self):
        super().setUp()
        recs = corpus(30, seed=121)
        link(recs[0], group="g5001"), link(recs[1], group="g5001")                          # deklarált pár
        for k in (2, 3, 4):
            link(recs[k], persona="p901")                                                    # persona-hármas
        dup = copy_of(recs[5], "mtfx_syn_9005")
        link(dup, group="g9005", persona="p905")
        recs.append(dup)                                                                       # blokkolt pár (5, 9005)
        self.short_a, self.short_b = short_pair(122)
        self.short_a["id"], self.short_b["id"] = "mtfx_syn_7001", "mtfx_syn_7002"
        link(self.short_a, group="g7001", persona="p907"), link(self.short_b, group="g7002", persona="p908")     # a corpus() személyeitől független
        recs += [self.short_a, self.short_b]                                                   # kivétellel felmentett rövid pár
        self.recs = recs
        self.conv = self.write_convs(recs)
        exceptions = [{"a": "mtfx_syn_7001", "b": "mtfx_syn_7002", "waive": ["sample_near_short"], "reason": "Más mértékegységre kérdez: külön tanítási elem."}]
        self.report = self.mt3([self.conv], exceptions=exceptions)
        self.excl = [{"id": "mtfx_syn_0010", "reason": "ok", "review": "később"}]
        self.prep = ms.prepare([self.conv], "fixture", self.report, te1_export=self.export_dir)
        self.res = ms.compute_split(self.prep["records"], self.prep["rep"], self.excl, self.prep["te1_ref"], (24, 3, 3), "v", True, "auto")
        self.units, self.held, _e = ms.build_units(self.prep["records"], self.prep["rep"], self.excl, self.prep["te1_ref"])
        self.unit_of = self.res["unit_of"]
        self.key_of = {(r["file"], r["line"]): r for r in self.prep["records"]}
        self.idx = {r["id"]: r["index"] for r in self.prep["records"]}

    def verify(self, assign, rep=None, held=None):
        return ms.verify_split(self.prep["records"], rep or self.prep["rep"], assign, held if held is not None else self.held, self.unit_of, self.excl, self.key_of)

    def flipped(self, rid):
        a = dict(self.res["records_split"])
        a[self.idx[rid]] = next(s for s in ms.SPLITS if s != a[self.idx[rid]])
        return a

    @staticmethod
    def failing(checks):
        return sorted(k for k, v in checks.items() if not v)

    def test_the_computed_assignment_passes_every_check(self):
        self.assertEqual(self.failing(self.verify(self.res["records_split"])), [])
        self.assertEqual(set(self.res["records_split"]) & set(self.held), set())
        self.assertEqual({self.prep["records"][i]["id"] for i in self.held}, {"mtfx_syn_0005", "mtfx_syn_9005", "mtfx_syn_0010"})

    def test_a_split_declared_group_is_detected_by_the_group_checks(self):
        failed = self.failing(self.verify(self.flipped("mtfx_syn_0001")))
        for name in ("no_unit_split_across_parts", "mt3_groups_not_split", "declared_split_groups_not_split", "mt3_edges_not_split"):
            self.assertIn(name, failed)
        self.assertNotIn("personas_not_split", failed)
        self.assertNotIn("no_blocked_record_assigned", failed)

    def test_a_split_persona_is_detected(self):
        failed = self.failing(self.verify(self.flipped("mtfx_syn_0003")))
        self.assertIn("personas_not_split", failed)
        self.assertIn("mt3_groups_not_split", failed)
        self.assertNotIn("declared_split_groups_not_split", failed)

    def test_a_split_exception_pair_is_detected(self):
        failed = self.failing(self.verify(self.flipped("mtfx_syn_7002")))
        self.assertIn("exception_pairs_not_split", failed)
        self.assertIn("no_unit_split_across_parts", failed, "az MT-2 egy egységbe vonta a felmentett párt")
        self.assertNotIn("no_unresolved_finding_pair_across_parts", failed)

    def test_assigned_blocked_records_and_blocked_groups_are_detected(self):
        a = dict(self.res["records_split"])
        a[self.idx["mtfx_syn_0005"]] = "train"
        failed = self.failing(self.verify(a))
        self.assertIn("no_blocked_record_assigned", failed)
        self.assertIn("no_blocked_group_member_assigned", failed)
        self.assertIn("all_records_accounted_for", failed, "a rekord egyszerre kijelölt és visszatartott")

    def test_assigned_excluded_record_and_missing_records_are_detected(self):
        a = dict(self.res["records_split"])
        a[self.idx["mtfx_syn_0010"]] = "test"
        failed = self.failing(self.verify(a))
        self.assertIn("no_excluded_record_assigned", failed)
        a = dict(self.res["records_split"])
        a.pop(self.idx["mtfx_syn_0020"])
        self.assertIn("all_records_accounted_for", self.failing(self.verify(a)))
        held = {i: {"reasons": [], "findings": []} for i in self.held}
        self.assertIn("held_back_have_reasons", self.failing(self.verify(self.res["records_split"], held=held)))

    def test_an_unresolved_finding_between_assigned_records_in_different_parts_is_detected(self):
        rep = json.loads(json.dumps(self.prep["rep"]))
        recs = self.prep["records"]
        a = next(r for r in recs if r["id"] == "mtfx_syn_0020")
        b = next(r for r in recs if r["id"] == "mtfx_syn_0021")
        split = dict(self.res["records_split"])
        split[a["index"]], split[b["index"]] = "train", "test"
        loc = lambda r: {"source": "conversation", "record": r["id"], "file": r["file"], "line": r["line"], "turn": 1}
        rep["findings"].append({"finding_id": "fx", "scope": "sample", "type": "sample_near", "status": "review", "score": 0.93, "a": loc(a), "b": loc(b),
                                "at_boundary": False, "method": "m", "reason": "r"})
        failed = self.failing(self.verify(split, rep=rep))
        self.assertIn("no_unresolved_finding_pair_across_parts", failed)
        self.assertNotIn("exception_pairs_not_split", failed)


# ---------------------------------------------------------------------------
# integráció: a valódi MT-3 jelentéssel
# ---------------------------------------------------------------------------

class HappyPathTests(Base):
    def test_clean_corpus_is_split_exactly_with_full_traceability(self):
        recs = corpus(100, seed=7)
        man, conv, report = self.pipeline(recs, targets=(80, 10, 10))
        self.assertEqual(read_json(report)["summary"]["blocked_records"], 0, "feltevés: az MT-3 nem talál blokkoló jelzést")
        d = man["deviation"]
        self.assertEqual(d["achieved"], {"train": 80, "validation": 10, "test": 10})
        self.assertTrue(d["exact_ideal_reached"])
        self.assertFalse(d["scaled_from_planned"])
        self.assertEqual(man["counts"]["held_back"], 0)
        self.assertEqual(man["counts"]["assigned"], 100)
        self.assertTrue(all(man["verification"].values()), man["verification"])
        self.assertEqual(man["warnings"], [])
        self.assertFalse(man["training_ready"])
        self.assertFalse(man["content_verified"])
        self.assertFalse(man["split_approved"])
        self.assertIn("NEM jóváhagyott", man["disclaimer"])
        independent_split_check(self, man)
        by_split = self.splits_of(man)
        self.assertEqual(Counter(by_split.values()), Counter({"train": 80, "validation": 10, "test": 10}))
        # üzenet- és mintaszámok a bemenetből újraszámolva
        for s in ms.SPLITS:
            rs = [r for r in recs if by_split[r["id"]] == s]
            st = man["splits"][s]
            self.assertEqual(st["conversations"], len(rs))
            self.assertEqual(st["messages"], sum(len(r["turns"]) for r in rs))
            self.assertEqual(st["samples_total"], sum(r["meta"]["n_exchanges"] for r in rs))
            self.assertEqual(st["samples_first_turn"], len(rs))
            self.assertEqual(st["samples_history_dependent"], st["samples_total"] - len(rs))
        self.assertEqual(set(man["outputs"]), {"assignment.tsv", "held_back.tsv", "groups.tsv", "ids_train.txt", "ids_validation.txt", "ids_test.txt",
                                               "cross_split_overlaps.tsv", "export_links.json"})
        for name, o in man["outputs"].items():
            self.assertEqual(o["sha256"], hashlib.sha256(read_bytes(os.path.join(man["run_dir"], name))).hexdigest())
        ids = {s: read_text(os.path.join(man["run_dir"], f"ids_{s}.txt")).split() for s in ms.SPLITS}
        self.assertEqual({x: s for s, xs in ids.items() for x in xs}, by_split)
        self.assertEqual(sum(len(v) for v in ids.values()), 100)

    def test_default_targets_are_scaled_when_the_assignable_count_differs_from_the_plan(self):
        man, _c, _r = self.pipeline(corpus(50, seed=8), targets=ms.DEFAULT_TARGETS)
        d = man["deviation"]
        self.assertEqual(d["ideal_counts"], {"train": 40, "validation": 5, "test": 5})
        self.assertTrue(d["scaled_from_planned"])
        self.assertEqual(d["vs_planned"], {"train": -760, "validation": -95, "test": -95})
        self.assertFalse(d["within_plan_tolerance"])
        self.assertTrue(d["exact_ideal_reached"], "az arányosan skálázott cél pontosan teljesül")
        self.assertTrue(any("arányosan skálázott" in w for w in man["warnings"]))

    def test_stratification_balances_families_and_lowers_the_loss(self):
        man, _c, _r = self.pipeline(corpus(90, seed=9), targets=(72, 9, 9))
        s = man["stratification"]["result"]
        self.assertLess(s["loss_after"], s["loss_before"])
        for part in ("validation", "test"):
            fam = man["splits"][part]["family"]
            self.assertGreaterEqual(len(fam), 6, f"{part}: legalább 6 család szerepel a 9 beszélgetésben: {fam}")
            self.assertLessEqual(max(fam.values()), 2, fam)
        self.assertTrue(man["hard_test"]["satisfied"])
        self.assertGreaterEqual(man["splits"]["test"]["hard"], man["hard_test"]["min_hard_test"])
        self.assertEqual(man["config"]["stratify_features"], ["family", "length", "domain", "hard"])
        man2, _c2, _r2 = self.pipeline(corpus(90, seed=9), targets=(72, 9, 9), stratify=False, run_name="plain")
        self.assertIsNone(man2["stratification"]["result"])

    def test_hard_minimum_scales_with_the_test_size(self):
        man, _c, _r = self.pipeline(corpus(100, seed=7), targets=(80, 10, 10))
        h = man["hard_test"]
        self.assertEqual(h["min_hard_test"], min(h["hard_assignable_total"], 3), "a terv 30/100 -> 10 teszt-beszélgetésből 3")
        man2, _c2, _r2 = self.pipeline(corpus(100, seed=7), targets=(80, 10, 10), min_hard_test="5", run_name="h5")
        self.assertEqual(man2["hard_test"]["min_hard_test"], 5)
        self.assertGreaterEqual(man2["splits"]["test"]["hard"], 5)


# ---------------------------------------------------------------------------
# csoport-integritás
# ---------------------------------------------------------------------------

class GroupIntegrityTests(Base):
    def linked_corpus(self):
        recs = corpus(70, seed=21)
        # deklarált csoport, 2 és 3 tagú
        link(recs[0], group="g5001"), link(recs[1], group="g5001")
        link(recs[2], group="g5002"), link(recs[3], group="g5002"), link(recs[4], group="g5002")
        # persona-csoport (3 tagú), különböző deklarált csoportokkal
        for k in (10, 11, 12):
            link(recs[k], persona="p901")
        # láncolt kapcsolat: deklarált csoport - persona - deklarált csoport - persona - deklarált csoport (5 tagú)
        link(recs[20], group="g6001", persona="p911")
        link(recs[21], group="g6001", persona="p912")
        link(recs[22], group="g6002", persona="p912")
        link(recs[23], group="g6002", persona="p913")
        link(recs[24], group="g6003", persona="p913")
        return recs

    def test_declared_persona_and_chained_links_stay_in_one_part(self):
        recs = self.linked_corpus()
        man, conv, report = self.pipeline(recs, targets=(56, 7, 7))
        self.assertEqual(read_json(report)["summary"]["blocked_records"], 0)
        independent_split_check(self, man)
        by = self.splits_of(man)
        for ids in (("mtfx_syn_0000", "mtfx_syn_0001"), ("mtfx_syn_0002", "mtfx_syn_0003", "mtfx_syn_0004"), ("mtfx_syn_0010", "mtfx_syn_0011", "mtfx_syn_0012"),
                    tuple("mtfx_syn_%04d" % k for k in range(20, 25))):
            self.assertEqual(len({by[i] for i in ids}), 1, ids)
        chain = man["units"]["mtg_mtfx_syn_0020"]
        self.assertEqual(chain["members"], ["mtfx_syn_%04d" % k for k in range(20, 25)])
        self.assertEqual(sorted(chain["declared_split_groups"]), ["g6001", "g6002", "g6003"])
        self.assertEqual(man["counts"]["units_multi_member"], 4)
        self.assertEqual(man["counts"]["unit_size_histogram"], {"1": 70 - 13, "2": 1, "3": 2, "5": 1})
        self.assertEqual(man["counts"]["units"], 61)

    def test_the_unit_is_the_computed_group_not_the_declared_split_group(self):
        recs = corpus(30, seed=22)
        link(recs[0], persona="p950"), link(recs[1], persona="p950")           # különböző deklarált csoport, közös persona
        man, _c, report = self.pipeline(recs, targets=(24, 3, 3))
        rep = read_json(report)
        gids = {r["record"]: r["group_id"] for r in rep["records"]}
        self.assertEqual(gids["mtfx_syn_0000"], gids["mtfx_syn_0001"])
        self.assertNotEqual(recs[0]["meta"]["split_group"], recs[1]["meta"]["split_group"])
        by = self.splits_of(man)
        self.assertEqual(by["mtfx_syn_0000"], by["mtfx_syn_0001"])

    def test_many_groups_relative_to_the_small_parts_never_split_a_group(self):
        recs = corpus(60, seed=23)
        for k in range(0, 30, 3):                                      # 10 hármas csoport
            for j in range(3):
                link(recs[k + j], group="g7%03d" % k)
        man, conv, report = self.pipeline(recs, targets=(48, 6, 6))
        self.assertEqual(read_json(report)["summary"]["blocked_records"], 0)
        independent_split_check(self, man)
        for part in ("validation", "test"):
            n = man["splits"][part]["conversations"]
            self.assertEqual(n, 6)
        self.assertTrue(man["deviation"]["exact_ideal_reached"])

    def test_group_integrity_holds_for_many_seeds_and_orders(self):
        recs = self.linked_corpus()
        conv = self.write_convs(recs, "base.jsonl")
        report = self.mt3([conv])
        for k, seed in enumerate(("a", "b", "c", "d", "e", "f")):
            man = ms.run_from_files([conv], self.out, "fixture", report, te1_export=self.export_dir, targets=(56, 7, 7), seed=seed, run_name=f"seed{k}")
            independent_split_check(self, man)
            self.assertTrue(all(man["verification"].values()))
            self.assertEqual(man["deviation"]["achieved"], {"train": 56, "validation": 7, "test": 7})

    def test_exception_waived_pair_is_merged_into_one_unit_even_without_an_mt3_link(self):
        # két, rövid kezdő váltásban közel azonos beszélgetés: MT-3 sample_near_short (review, nem csoportosít) -> dokumentált kivétel
        a, b = short_pair(31)
        rest = corpus(30, seed=31, start=2)
        conv = self.write_convs([a, b] + rest)
        exceptions = [{"a": a["id"], "b": b["id"], "waive": ["sample_near_short"], "reason": "Más mértékegységre kérdez: a köznapi tudás eltérő eleme.", "reviewer": "teszt"}]
        report = self.mt3([conv], exceptions=exceptions)
        rep = read_json(report)
        self.assertEqual(rep["summary"]["blocked_records"], 0)
        gids = {r["record"]: r["group_id"] for r in rep["records"]}
        self.assertNotEqual(gids[a["id"]], gids[b["id"]], "az MT-3 a rövid hasonlóságot nem csoportosítja")
        prep = ms.prepare([conv], "fixture", report, te1_export=self.export_dir)
        units, held, extra = ms.build_units(prep["records"], prep["rep"], None, prep["te1_ref"])
        self.assertEqual(held, {})
        merged = [u for u in units.values() if u["merged"]]
        self.assertEqual(len(merged), 1)
        self.assertEqual({r["id"] for r in merged[0]["members"]}, {a["id"], b["id"]})
        self.assertEqual(extra["merged_pairs"], [(a["id"], b["id"], "sample_near_short")])
        man = ms.run_from_files([conv], self.out, "fixture", report, te1_export=self.export_dir, targets=(26, 3, 3), run_name="exc")
        by = self.splits_of(man)
        self.assertEqual(by[a["id"]], by[b["id"]])
        self.assertEqual(man["counts"]["units_merged_by_mt2"], 1)
        self.assertEqual(man["merged_by_exception"], [{"a": a["id"], "b": b["id"], "type": "sample_near_short"}])
        self.assertTrue(man["units"][min(gids[a["id"]], gids[b["id"]])]["merged_by_mt2"])


# ---------------------------------------------------------------------------
# visszatartások: blokkolt, csoport-tag, kizárt
# ---------------------------------------------------------------------------

class HeldBackTests(Base):
    def test_blocked_records_and_their_whole_group_are_never_assigned(self):
        recs = corpus(40, seed=41)
        dup = copy_of(recs[7], "mtfx_syn_9007")                              # pontos másolat: reject
        link(dup, group="g9999", persona="p808")
        link(recs[8], persona="p808")                                        # a másolat csoporttársa (közös persona)
        recs.append(dup)
        man, conv, report = self.pipeline(recs, targets=(30, 4, 4))
        rep = read_json(report)
        self.assertEqual(rep["summary"]["blocked_records"], 2, "az exact pár blokkolt; a 8. csak a csoport miatt kerül visszatartásra")
        held = {h["id"]: h for h in man["held_back"]}
        self.assertEqual(set(held), {"mtfx_syn_0007", "mtfx_syn_9007", "mtfx_syn_0008"})
        self.assertEqual(held["mtfx_syn_0007"]["reasons"], ["mt3_blocked"])
        self.assertEqual(held["mtfx_syn_9007"]["reasons"], ["mt3_blocked"])
        self.assertEqual(held["mtfx_syn_0008"]["reasons"], ["group_has_blocked_member"])
        self.assertTrue(held["mtfx_syn_0007"]["mt3_findings"])
        self.assertEqual(man["counts"]["held_back_by_reason"], {"group_has_blocked_member": 1, "mt3_blocked": 2})
        by = self.splits_of(man)
        self.assertTrue(set(held).isdisjoint(by))
        self.assertEqual(len(by), 38)
        self.assertEqual(man["counts"]["assignable"], 38)
        self.assertEqual(sum(man["deviation"]["achieved"].values()), 38)
        for s in ms.SPLITS:
            ids = read_text(os.path.join(man["run_dir"], f"ids_{s}.txt")).split()
            self.assertTrue(set(ids).isdisjoint(held))
        self.assertTrue(any("visszatartva" in w for w in man["warnings"]))
        tsv = read_text(os.path.join(man["run_dir"], "held_back.tsv")).splitlines()
        self.assertEqual(len(tsv), 1 + 3)

    def test_unresolved_review_findings_block_too_and_documented_exceptions_release_them(self):
        a, b = short_pair(42)
        recs = [a, b] + corpus(20, seed=42, start=2)
        man, _c, report = self.pipeline(recs, targets=(18, 2, 2))
        rep = read_json(report)
        self.assertIn(("sample_near_short", "review"), {(f["type"], f["status"]) for f in rep["findings"]})
        self.assertEqual({h["id"] for h in man["held_back"]}, {a["id"], b["id"]}, "a fel nem oldott review is visszatartást jelent")
        man2, _c2, report2 = self.pipeline(recs, targets=(18, 2, 2), run_name="released",
                                           exceptions=[{"a": a["id"], "b": b["id"], "waive": ["sample_near_short"], "reason": "Más mértékegységre kérdez: külön tanítási elem."}])
        self.assertEqual(man2["held_back"], [])
        self.assertEqual(man2["counts"]["assigned"], 22)

    def test_exclusion_list_holds_back_the_record_only_and_reserves_the_split_of_its_group(self):
        recs = corpus(40, seed=43)
        link(recs[3], persona="p777"), link(recs[4], persona="p777")
        excl = os.path.join(self.tmp, "excl.txt")
        write_text(excl, "# kizárt beszélgetés\nmtfx_syn_0003 | tartalmi kifogás | az 1. felülvizsgálat után\nmtfx_syn_0020 | másik ok | később\n")
        man, _c, _r = self.pipeline(recs, targets=(30, 4, 4), exclusions_path=excl)
        held = {h["id"]: h for h in man["held_back"]}
        self.assertEqual(set(held), {"mtfx_syn_0003", "mtfx_syn_0020"})
        self.assertEqual(held["mtfx_syn_0003"]["reasons"], ["excluded_list"])
        by = self.splits_of(man)
        self.assertIn("mtfx_syn_0004", by, "a csoporttárs kijelölhető")
        self.assertEqual(held["mtfx_syn_0003"]["reserved_split"], by["mtfx_syn_0004"], "a később felszabadított rekord ugyanabba a részbe kerülne")
        self.assertIsNone(held["mtfx_syn_0020"]["reserved_split"], "egyedüli tag: nincs foglalt rész")
        self.assertEqual(man["inputs"]["exclusions"]["entries"], 2)
        self.assertEqual(man["counts"]["assigned"], 38)
        self.assertEqual(man["counts"]["held_back_by_reason"], {"excluded_list": 2})

    def test_marker_in_quality_notes_holds_the_record_back(self):
        recs = corpus(30, seed=44)
        recs[5]["quality_notes"] = NOTES + " " + MARK
        errs = [e for e in mt.validate_record(recs[5], "fixture", BANK) if e.severity == "error"]
        self.assertEqual(errs, [], "feltevés: a jelölés a rekordot MT-1 szerint nem teszi érvénytelenné")
        man, _c, _r = self.pipeline(recs, targets=(24, 3, 2))
        held = {h["id"]: h["reasons"] for h in man["held_back"]}
        self.assertEqual(held, {"mtfx_syn_0005": ["excluded_marker"]})
        self.assertNotIn("mtfx_syn_0005", self.splits_of(man))

    def test_te1_excluded_row_id_collision_is_held_back(self):
        recs = corpus(12, seed=45)
        conv = self.write_convs(recs)
        report = self.mt3([conv])
        prep = ms.prepare([conv], "fixture", report, te1_export=self.export_dir)
        self.assertEqual(prep["te1_ref"]["excluded_ids"], ["x_excl_0001"])
        ref = dict(prep["te1_ref"], excluded_ids=["mtfx_syn_0002"])
        units, held, _e = ms.build_units(prep["records"], prep["rep"], None, ref)
        self.assertEqual({prep["records"][i]["id"]: h["reasons"] for i, h in held.items()}, {"mtfx_syn_0002": ["id_collides_with_te1_excluded_row"]})

    def test_invalid_exclusion_lists_stop_the_run(self):
        recs = corpus(12, seed=46)
        conv = self.write_convs(recs)
        report = self.mt3([conv])
        cases = {"unknown_id": ("mtfx_syn_0999 | ok | később\n", "nincs a bemenetben"),
                 "duplicate": ("mtfx_syn_0001 | ok | később\nmtfx_syn_0001 | ok | később\n", "Duplikált azonosító"),
                 "bad_line": ("mtfx_syn_0001 csak szöveg\n", "Hibás kizárási sor"),
                 "wildcard": ("mtfx_syn_* | ok | később\n", "Nem szabályos azonosító"),
                 "empty": ("# csak megjegyzés\n", "nem tartalmaz bejegyzést")}
        for name, (text, needle) in cases.items():
            with self.subTest(case=name):
                p = os.path.join(self.tmp, name + ".txt")
                write_text(p, text)
                with self.assertRaises(ms.ExclusionsError) as ctx:
                    ms.run_from_files([conv], self.out, "fixture", report, te1_export=self.export_dir, exclusions_path=p, run_name=name)
                self.assertIn(needle, str(ctx.exception))
                self.assertFalse(os.path.exists(os.path.join(self.out, name)))
        with self.assertRaises(ms.ExclusionsError):
            ms.run_from_files([conv], self.out, "fixture", report, te1_export=self.export_dir, exclusions_path=os.path.join(self.tmp, "nincs.txt"), run_name="x")

    def test_all_records_blocked_gives_an_empty_assignment_without_error(self):
        a = synth(0, 47)
        recs = [a, copy_of(a, "mtfx_syn_0001")]
        man, _c, _r = self.pipeline(recs, targets=(8, 1, 1))
        self.assertEqual(man["assignment"], [])
        self.assertEqual({h["id"] for h in man["held_back"]}, {"mtfx_syn_0000", "mtfx_syn_0001"})
        self.assertEqual(man["deviation"]["achieved"], {"train": 0, "validation": 0, "test": 0})
        self.assertTrue(all(man["verification"].values()))


# ---------------------------------------------------------------------------
# nem elérhető darabszám
# ---------------------------------------------------------------------------

class UnattainableCountsTests(Base):
    def test_groups_of_three_cannot_make_two_and_two_and_are_never_split(self):
        recs = corpus(12, seed=51)
        for k in range(0, 12, 3):
            for j in range(3):
                link(recs[k + j], group="g8%03d" % k)
        man, conv, report = self.pipeline(recs, targets=(8, 2, 2))
        self.assertEqual(read_json(report)["summary"]["blocked_records"], 0)
        d = man["deviation"]
        self.assertFalse(d["exact_ideal_reached"])
        self.assertEqual(d["ideal_counts"], {"train": 8, "validation": 2, "test": 2})
        self.assertEqual(sum(abs(v) for v in d["vs_ideal"].values()), 4, d)
        independent_split_check(self, man)
        for part in ms.SPLITS:
            self.assertEqual(man["splits"][part]["conversations"] % 3, 0)
        self.assertTrue(all(man["verification"].values()))
        self.assertTrue(any("eltér az ideálistól" in w for w in man["warnings"]))
        exact = self.pipeline(recs, targets=(6, 3, 3), run_name="attainable")[0]
        self.assertTrue(exact["deviation"]["exact_ideal_reached"])

    def test_a_huge_group_goes_to_train_and_the_small_parts_are_still_filled(self):
        recs = corpus(50, seed=52)
        for k in range(12):                       # 12 tagú lánc: felváltva közös deklarált csoport és közös persona (mindegyikből kettő)
            link(recs[k], group="g%04d" % (4000 + k // 2), persona="p%03d" % (600 + (k + 1) // 2))
        man, _c, report = self.pipeline(recs, targets=(40, 5, 5))
        self.assertEqual(read_json(report)["summary"]["blocked_records"], 0, "a 6 fölötti csoportméret csoport-szintű jelzés, nem rekord-blokkolás")
        self.assertEqual(man["counts"]["unit_size_histogram"], {"1": 38, "12": 1})
        big = next(u for u in man["units"].values() if len(u["members"]) == 12)
        self.assertEqual(big["split"], "train")
        self.assertEqual({man["deviation"]["achieved"][s] for s in ("validation", "test")}, {5})
        self.assertTrue(man["deviation"]["exact_ideal_reached"])
        independent_split_check(self, man)

    def test_cli_exit_code_signals_the_deviation(self):
        recs = corpus(12, seed=53)
        for k in range(0, 12, 3):
            for j in range(3):
                link(recs[k + j], group="g8%03d" % k)
        conv = self.write_convs(recs)
        report = self.mt3([conv])
        r = subprocess.run([sys.executable, TOOL_PATH, "--mode", "fixture", "--conversations", conv, "--mt3-report", report, "--out-dir", self.out,
                            "--te1-export", self.export_dir, "--targets", "8,2,2", "--run-name", "dev"], capture_output=True, text=True, encoding="utf-8",
                           env=dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1"))
        self.assertEqual(r.returncode, ms.EXIT_ATTENTION, r.stderr)
        self.assertIn("FIGYELEM", r.stdout)
        self.assertIn("NEM jóváhagyott", r.stdout)


# ---------------------------------------------------------------------------
# ismételhetőség
# ---------------------------------------------------------------------------

class ReproducibilityTests(Base):
    def test_same_inputs_same_assignment_and_manifest_verification(self):
        recs = corpus(60, seed=61)
        conv = self.write_convs(recs)
        report = self.mt3([conv])
        m1 = ms.run_from_files([conv], self.out, "fixture", report, te1_export=self.export_dir, targets=(48, 6, 6), run_name="r1")
        m2 = ms.run_from_files([conv], self.out, "fixture", report, te1_export=self.export_dir, targets=(48, 6, 6), run_name="r2")
        self.assertEqual(m1["assignment"], m2["assignment"])
        self.assertEqual(m1["assignment_sha256"], m2["assignment_sha256"])
        self.assertEqual(m1["groups_sha256"], m2["groups_sha256"])
        for name in ("assignment.tsv", "ids_train.txt", "ids_test.txt", "groups.tsv", "export_links.json"):
            self.assertEqual(read_bytes(os.path.join(m1["run_dir"], name)), read_bytes(os.path.join(m2["run_dir"], name)), name)
        mp = os.path.join(m1["run_dir"], "split_manifest.json")
        self.assertEqual(ms.verify_manifest(mp), ([], []))
        self.assertEqual(ms._main(["--verify-manifest", mp]), 0)

    def test_independent_of_record_order_and_file_split(self):
        recs = corpus(60, seed=62)
        link(recs[1], group="g5001"), link(recs[2], group="g5001")
        base_conv = self.write_convs(recs, "one.jsonl")
        base_report = self.mt3([base_conv])
        m1 = ms.run_from_files([base_conv], self.out, "fixture", base_report, te1_export=self.export_dir, targets=(48, 6, 6), run_name="o1")
        shuffled = list(recs)
        random.Random(5).shuffle(shuffled)
        files = [self.write_convs(shuffled[:25], "p1.jsonl"), self.write_convs(shuffled[25:], "p2.jsonl")]
        report2 = self.mt3(files)
        m2 = ms.run_from_files(files, self.out, "fixture", report2, te1_export=self.export_dir, targets=(48, 6, 6), run_name="o2")
        self.assertEqual(self.splits_of(m1), self.splits_of(m2), "a kijelölés nem függ a rekordok/fájlok sorrendjétől")
        self.assertEqual(sorted(m1["units"]), sorted(m2["units"]))

    def test_seed_changes_the_assignment_and_default_seed_is_recorded(self):
        recs = corpus(60, seed=63)
        conv = self.write_convs(recs)
        report = self.mt3([conv])
        a = ms.run_from_files([conv], self.out, "fixture", report, te1_export=self.export_dir, targets=(48, 6, 6), seed="alfa", run_name="a")
        b = ms.run_from_files([conv], self.out, "fixture", report, te1_export=self.export_dir, targets=(48, 6, 6), seed="beta", run_name="b")
        self.assertNotEqual(a["assignment_sha256"], b["assignment_sha256"])
        self.assertEqual(a["config"]["seed"], "alfa")
        self.assertEqual(a["deviation"]["achieved"], b["deviation"]["achieved"])
        c = ms.run_from_files([conv], self.out, "fixture", report, te1_export=self.export_dir, targets=(48, 6, 6), run_name="c")
        self.assertEqual(c["config"]["seed"], ms.DEFAULT_SEED)

    def test_verify_manifest_detects_changed_inputs_outputs_and_non_reproducible_assignment(self):
        recs = corpus(30, seed=64)
        conv = self.write_convs(recs)
        report = self.mt3([conv])
        man = ms.run_from_files([conv], self.out, "fixture", report, te1_export=self.export_dir, targets=(24, 3, 3), run_name="v1")
        mp = os.path.join(man["run_dir"], "split_manifest.json")
        # 1) kimenet átírva
        ids = os.path.join(man["run_dir"], "ids_test.txt")
        original = read_bytes(ids)
        write_text(ids, read_text(ids) + "mtfx_syn_9999\n")
        changed, bad = ms.verify_manifest(mp)
        self.assertTrue(any("kimenet megváltozott" in x for x in changed))
        self.assertEqual(ms._main(["--verify-manifest", mp]), ms.EXIT_STALE)
        with open(ids, "wb") as f:
            f.write(original)
        self.assertEqual(ms.verify_manifest(mp), ([], []))
        # 2) bemenet átírva
        before = read_bytes(conv)
        with open(conv, "ab") as f:
            f.write(b"\n")
        changed, bad = ms.verify_manifest(mp)
        self.assertTrue(any("beszélgetés-fájl" in x for x in changed))
        with open(conv, "wb") as f:
            f.write(before)
        # 3) az MT-3 jelentés megváltozott
        rb = read_bytes(report)
        write_text(report, read_text(report) + " ")
        changed, _bad = ms.verify_manifest(mp)
        self.assertTrue(any("MT-3 jelentés" in x for x in changed))
        with open(report, "wb") as f:
            f.write(rb)
        # 4) a rögzített kijelölés-ellenőrzőösszeg nem egyezik az újraszámolttal (nem reprodukálható)
        j = read_json(mp)
        j["assignment_sha256"] = "0" * 64
        write_text(mp, json.dumps(j, ensure_ascii=False, indent=2))
        changed, bad = ms.verify_manifest(mp)
        self.assertEqual(changed, [])
        self.assertTrue(any("kijelölés" in x for x in bad))
        self.assertEqual(ms._main(["--verify-manifest", mp]), ms.EXIT_NOT_REPRODUCIBLE)


# ---------------------------------------------------------------------------
# elavult / megváltozott MT-3 jelentés és bemenet
# ---------------------------------------------------------------------------

class StaleInputTests(Base):
    def setUp(self):
        super().setUp()
        self.recs = corpus(24, seed=71)
        link(self.recs[1], persona="p880"), link(self.recs[2], persona="p880")
        link(self.recs[5], group="g5500"), link(self.recs[6], group="g5500")
        self.conv = self.write_convs(self.recs, "s.jsonl")
        self.report = self.mt3([self.conv])

    def run_split(self, conv=None, report=None, **kw):
        kw.setdefault("te1_export", self.export_dir)
        return ms.run_from_files([conv or self.conv], self.out, "fixture", report or self.report, targets=(20, 2, 2), run_name=kw.pop("run_name", "st"), **kw)

    def patched_report(self, name, fn):
        j = read_json(self.report)
        fn(j)
        os.makedirs(os.path.join(self.tmp, "patched"), exist_ok=True)              # az out-mappa nem lehet a bemenet alatt
        p = os.path.join(self.tmp, "patched", name + "_report.json")
        write_text(p, json.dumps(j, ensure_ascii=False, indent=2))
        return p

    def assertStale(self, needle=None, **kw):
        with self.assertRaises(ms.StaleReportError) as ctx:
            self.run_split(**kw)
        if needle:
            self.assertIn(needle, str(ctx.exception))
        self.assertFalse(os.path.exists(os.path.join(self.out, "st")), "hiba után nincs futás-mappa")
        return ctx.exception

    def test_current_report_is_accepted(self):
        man = self.run_split()
        self.assertEqual(man["inputs"]["mt3_report"]["tool_version"], dd.TOOL_VERSION)
        self.assertEqual(man["inputs"]["mt3_report"]["sha256"], hashlib.sha256(read_bytes(self.report)).hexdigest())
        self.assertEqual(man["inputs"]["mt3_report"]["tool_sha256"], te1.sha256_file(dd.__file__))

    def test_input_changed_after_the_mt3_run_is_refused(self):
        with open(self.conv, "ab") as f:
            f.write(b"\n")
        self.assertStale("megváltozott")

    def test_report_made_for_other_conversation_content_is_refused(self):
        recs = corpus(24, seed=72)
        conv2 = self.write_convs(recs, "other.jsonl")
        self.assertStale("más beszélgetés-fájlokra", conv=conv2)

    def test_report_for_fewer_files_than_the_split_input_is_refused(self):
        extra = self.write_convs(corpus(3, seed=73, start=500), "extra.jsonl")
        with self.assertRaises(ms.StaleReportError):
            ms.run_from_files([self.conv, extra], self.out, "fixture", self.report, te1_export=self.export_dir, targets=(20, 2, 2), run_name="st")

    def test_old_tool_version_or_missing_or_wrong_tool_checksum_is_refused(self):
        p = self.patched_report("old", lambda j: j.update(tool_version="mt3-1.0"))
        self.assertStale("felülvizsgált döntési szabályok előtti", report=p)
        p = self.patched_report("newer", lambda j: j.update(tool_version="mt3-9.9"))
        self.assertStale("nem egyezik a jelenlegi eszközével", report=p)
        p = self.patched_report("nosha", lambda j: j.pop("tool_sha256"))
        self.assertStale("tool_sha256", report=p)
        p = self.patched_report("badsha", lambda j: j.update(tool_sha256="0" * 64))
        self.assertStale("tool_sha256", report=p)

    def test_report_status_mode_thresholds_and_flags_are_checked(self):
        for name, fn, needle in (
                ("status", lambda j: j.update(status="failed"), "státusza"),
                ("tool", lambda j: j.update(tool="tools/valami.py"), "nem MT-3 jelentés"),
                ("ready", lambda j: j.update(training_ready=True), "training_ready"),
                ("mode", lambda j: j["config"].update(mode="dataset"), "módja"),
                ("review", lambda j: j["config"]["decision_rules"].update(review_min=0.85), "küszöbei"),
                ("group_min", lambda j: j["config"]["grouping"].update(group_min=0.7), "küszöbei"),
                ("override", lambda j: j["config"].update(declared_split_group_overrides_decision=True), "felül")):
            with self.subTest(case=name):
                p = self.patched_report(name, fn)
                self.assertStale(needle, report=p)

    def test_record_set_line_checksum_or_group_tampering_is_refused(self):
        p = self.patched_report("norec", lambda j: j["records"].pop())
        self.assertStale("rekordkészlete", report=p)
        p = self.patched_report("linesha", lambda j: j["records"][3].update(line_sha256="0" * 64))
        self.assertStale("eltér a bemenettől", report=p)
        p = self.patched_report("nogroup", lambda j: j["records"][4].update(group_id=None))
        self.assertStale("csoport nélküli", report=p)

    def test_group_membership_and_declared_links_are_cross_checked(self):
        def drop_member(j):
            gid = next(iter(j["groups"]))
            j["groups"][gid]["members"] = j["groups"][gid]["members"][:-1] or ["mtfx_nincs"]

        p = self.patched_report("member", drop_member)
        self.assertStale("csoportjai nem egyeznek", report=p)

        def detach(victim_id):                   # a közös kapcsolatot elvágja: külön csoport-azonosítót ad az egyik tagnak
            def fn(j):
                victim = {r["record"]: r for r in j["records"]}[victim_id]
                old = victim["group_id"]
                j["groups"][old]["members"].remove(victim_id)
                j["groups"][old]["size"] -= 1
                victim["group_id"] = "mtg_" + victim_id
                j["groups"]["mtg_" + victim_id] = {"members": [victim_id], "size": 1, "edges": [], "declared_split_groups": []}
            return fn

        p = self.patched_report("persona", detach("mtfx_syn_0002"))
        self.assertStale("persona", report=p)
        p = self.patched_report("declared", detach("mtfx_syn_0006"))
        self.assertStale("split_group", report=p)

    def test_report_without_te1_comparison_needs_an_explicit_flag(self):
        conv = self.write_convs(corpus(20, seed=74), "n.jsonl")
        report = self.mt3([conv], export_dir=None)
        with self.assertRaises(ms.StaleReportError) as ctx:
            ms.run_from_files([conv], self.out, "fixture", report, targets=(16, 2, 2), run_name="nx")
        self.assertIn("TE-1 export összevetést", str(ctx.exception))
        man = ms.run_from_files([conv], self.out, "fixture", report, targets=(16, 2, 2), allow_no_te1=True, run_name="nx2")
        self.assertIsNone(man["inputs"]["te1_export"])
        self.assertTrue(man["config"]["allow_no_te1_comparison"])
        with self.assertRaises(ms.StaleReportError):                        # export megadva, de az MT-3 nélküle készült
            ms.run_from_files([conv], self.out, "fixture", report, te1_export=self.export(name="late"), targets=(16, 2, 2), allow_no_te1=True, run_name="nx3")

    def test_the_recorded_te1_manifest_checksum_is_compared_when_the_export_is_loaded(self):
        prep = ms.prepare([self.conv], "fixture", self.report, te1_export=self.export_dir)
        self.assertEqual(ms.load_te1_reference(prep["rep"], self.export_dir)["excluded_ids"], ["x_excl_0001"])
        tampered = json.loads(json.dumps(prep["rep"]))
        tampered["inputs"]["te1_export"]["manifest_sha256"] = "0" * 64
        with self.assertRaises(ms.StaleReportError) as ctx:
            ms.load_te1_reference(tampered, self.export_dir)
        self.assertIn("manifestje nem egyezik", str(ctx.exception))
        self.assertIsNone(ms.load_te1_reference({"inputs": {"te1_export": None}}, None))

    def test_te1_export_must_be_the_one_the_report_was_made_with(self):
        other = self.export(name="other")
        self.assertStale("nem az", te1_export=other)
        # az MT-3 jelentésben rögzített export megváltozott
        export_file = os.path.join(self.export_dir, te1.EXPORT_FILE)
        write_text(export_file, read_text(export_file) + " ")
        self.assertStale("TE-1 export")

    def test_invalid_or_missing_conversations_and_reports_have_their_own_errors(self):
        with self.assertRaises(ms.InputFileError):
            ms.run_from_files([os.path.join(self.tmp, "nincs.jsonl")], self.out, "fixture", self.report, te1_export=self.export_dir, run_name="x")
        with self.assertRaises(ms.InputFileError):
            ms.run_from_files([self.conv], self.out, "fixture", os.path.join(self.tmp, "nincs.json"), te1_export=self.export_dir, run_name="x")
        with self.assertRaises(ms.InvalidRecordsError):                     # dataset módban a fixture-ök nem érvényesek
            ms.run_from_files([self.conv], self.out, "dataset", self.report, te1_export=self.export_dir, run_name="x")
        bad = corpus(3, seed=75)
        bad[1]["turns"][2]["text"] = "Írj a valaki@example.com címre, ott elérsz."
        with self.assertRaises(ms.InvalidRecordsError):
            ms.run_from_files([self.write_convs(bad, "bad.jsonl")], self.out, "fixture", self.report, te1_export=self.export_dir, run_name="x")
        garbled = os.path.join(self.conv_dir, "garbled.jsonl")
        write_text(garbled, "{ez nem json}\n")
        with self.assertRaises(ms.InputFileError):
            ms.run_from_files([garbled], self.out, "fixture", self.report, te1_export=self.export_dir, run_name="x")
        self.assertFalse(os.path.exists(self.out))
        for name, text in (("junk_empty", "{}"), ("junk_list", "[]"), ("junk_text", "nem json")):
            os.makedirs(os.path.join(self.tmp, "patched"), exist_ok=True)
            junk = os.path.join(self.tmp, "patched", name + ".json")
            write_text(junk, text)
            with self.assertRaises(ms.StaleReportError, msg=name):
                ms.run_from_files([self.conv], self.out, "fixture", junk, te1_export=self.export_dir, run_name="x")

    def test_input_changed_during_the_run_is_detected(self):
        real = ms.compute_split

        def tampering(*a, **kw):
            with open(self.conv, "ab") as f:
                f.write(b"\n")
            return real(*a, **kw)

        with mock.patch.object(ms, "compute_split", tampering):
            with self.assertRaises(ms.ChangedInputError):
                self.run_split()
        self.assertFalse(os.path.exists(os.path.join(self.out, "st")))


# ---------------------------------------------------------------------------
# TE-1 exporttal talált kapcsolatok és részek közötti átfedések
# ---------------------------------------------------------------------------

def fake_finding(fid, scope, ftype, status, a, b, score=0.95):
    return {"finding_id": fid, "scope": scope, "type": ftype, "status": status, "score": score, "a": a, "b": b, "at_boundary": False,
            "method": "m", "reason": "r"}


def conv_loc(rec, turn=1):
    return {"source": "conversation", "record": rec["id"], "file": rec["file"], "line": rec["line"], "turn": turn}


def fake_records(n):
    return [{"index": i, "id": f"c{i}", "file": "f.jsonl", "line": i + 1} for i in range(n)]


class LinkAndOverlapUnitTests(unittest.TestCase):
    def test_export_links_carry_required_split_conflicts_and_pending_units(self):
        recs = fake_records(4)
        key_of = {(r["file"], r["line"]): r for r in recs}
        unit_of = {0: "u0", 1: "u1", 2: "u2", 3: "u3"}
        split_of = {0: "train", 1: "test", 2: "validation"}                   # a 3. beszélgetés visszatartott
        exp = lambda rid: {"source": "te1_export", "record": rid, "file": "data/clean/x.jsonl", "line": 7}
        rep = {"findings": [
            fake_finding("f1", "export", "sample_near", "accepted_with_exception", conv_loc(recs[0]), exp("x_a_0001")),
            fake_finding("f2", "export", "sample_near", "accepted_with_exception", conv_loc(recs[1]), exp("x_a_0001")),
            fake_finding("f3", "export", "sample_exact", "reject", conv_loc(recs[3]), exp("x_a_0002")),
            fake_finding("f4", "export", "same_qa_different_context", "info", conv_loc(recs[2], 5), exp("x_a_0003"), 0.93),
            fake_finding("f5", "export", "sample_near", "accepted_with_exception", exp("x_a_0004"), conv_loc(recs[2])),   # fordított sorrend
            fake_finding("f6", "sample", "sample_near", "review", conv_loc(recs[0]), conv_loc(recs[1])),                 # nem export-szintű
        ]}
        out = ms.build_export_links(rep, key_of, split_of, unit_of, {3: {}})
        s = out["summary"]
        self.assertEqual((s["links"], s["duplicate_like"], s["partial_overlap"], s["conflicts"], s["te1_rows_linked"]), (5, 4, 1, 1, 4))
        self.assertEqual(out["conflicts"], [{"te1_row": "x_a_0001", "splits": ["test", "train"], "units": ["u0", "u1"]}])
        self.assertTrue(out["te1_rows"]["x_a_0001"]["conflict"])
        self.assertIsNone(out["te1_rows"]["x_a_0001"]["required_split"])
        self.assertEqual(out["te1_rows"]["x_a_0004"]["required_split"], "validation")
        self.assertEqual(out["te1_rows"]["x_a_0002"]["pending_units"], ["u3"])
        self.assertIsNone(out["te1_rows"]["x_a_0002"]["required_split"])
        self.assertEqual(out["te1_rows"]["x_a_0003"]["required_split"], None, "a részleges átfedés nem követel részt")
        self.assertEqual(s["links_to_held_back_conversations"], 1)
        self.assertIn("TE-3", out["note"])
        first = out["links"][0]
        self.assertEqual(first["strength"], "duplicate_like")
        self.assertEqual(out["links"][-1]["strength"], "partial_overlap")

    def test_cross_split_overlaps_list_only_pairs_in_different_parts(self):
        recs = fake_records(5)
        key_of = {(r["file"], r["line"]): r for r in recs}
        unit_of = {i: f"u{i}" for i in range(5)}
        split_of = {0: "train", 1: "test", 2: "train", 3: "validation"}          # a 4. visszatartott
        rep = {"findings": [
            fake_finding("f1", "sample", "same_qa_different_context", "info", conv_loc(recs[0], 3), conv_loc(recs[1], 5), 0.92),
            fake_finding("f2", "sample", "shared_answer_different_question", "info", conv_loc(recs[0]), conv_loc(recs[2]), 0.97),       # azonos rész
            fake_finding("f3", "sample", "sample_near_short", "accepted_with_exception", conv_loc(recs[2]), conv_loc(recs[3]), 0.93),
            fake_finding("f4", "sample", "sample_at_boundary", "info", conv_loc(recs[0]), conv_loc(recs[4]), 0.9),                  # visszatartott
            fake_finding("f5", "export", "sample_near", "review", conv_loc(recs[0]), {"source": "te1_export", "record": "x", "file": "a", "line": 1}),
            fake_finding("f6", "group", "group_too_large", "review", {"source": "group", "record": "g"}, {"source": "group", "record": "g"}),
        ]}
        out = ms.cross_split_overlaps(rep, key_of, split_of, unit_of)
        self.assertEqual([(o["finding_id"], o["level"], o["a_split"], o["b_split"]) for o in out],
                         [("f3", "decision", "train", "validation"), ("f1", "info", "train", "test")])


class ExportLinksIntegrationTests(Base):
    def test_partial_overlap_with_the_export_is_listed_and_does_not_block(self):
        recs = corpus(30, seed=81)
        r = recs[4]                                                              # egy 5+. váltásos beszélgetés későbbi váltása: azonos kérdés és válasz, eltérő előzménnyel
        t = r["turns"]
        turn = 3
        row = (t[turn - 1]["text"], "", t[turn]["text"])
        # a hosszabb szöveg miatt a részleges átfedés (>= 30 karakteres kérdés) jelzett
        self.assertGreaterEqual(len(dd.normalize(row[0])), dd.MIN_PARTIAL_CHARS)
        man, conv, report = self.pipeline(recs, targets=(24, 3, 3), export_dir=self.export(rows=[row], name="ov"))
        rep = read_json(report)
        kinds = {(f["type"], f["status"]) for f in rep["findings"] if f["scope"] == "export"}
        self.assertTrue(kinds and all(s == "info" for _t, s in kinds), kinds)
        el = read_json(os.path.join(man["run_dir"], "export_links.json"))
        self.assertGreaterEqual(el["summary"]["partial_overlap"], 1)
        self.assertEqual(el["summary"]["duplicate_like"], 0)
        self.assertEqual({l["conversation_record"] for l in el["links"]}, {r["id"]})
        self.assertNotIn(r["id"], {h["id"] for h in man["held_back"]})
        self.assertEqual(man["export_links"]["file"], "export_links.json")

    def test_duplicate_like_link_with_a_documented_exception_gets_a_required_split(self):
        recs = corpus(30, seed=82)
        r = recs[6]
        q = r["turns"][0]["text"][:-2] + "x?"                                   # egyetlen karakter eltérés: ~0,99 hasonlóság
        row = (q, "", r["turns"][1]["text"])
        export_dir = self.export(rows=[row], name="dup")
        conv = self.write_convs(recs)
        report = self.mt3([conv], export_dir=export_dir)
        rep = read_json(report)
        near = [f for f in rep["findings"] if f["scope"] == "export" and f["status"] in ("reject", "review")]
        self.assertTrue(near and near[0]["type"] == "sample_near", [f["type"] for f in rep["findings"]])
        exceptions = [{"a": r["id"], "b": "x_a_0001", "waive": ["sample_near"], "reason": "Más témán belül tanít eltérő képességet ugyanezzel a kérdéssel.",
                       "capability": "A beszélgetés első fordulója a témát vezeti be, az egyfordulós példa csak tényt közöl."}]
        report2 = self.mt3([conv], export_dir=export_dir, exceptions=exceptions)
        man = ms.run_from_files([conv], self.out, "fixture", report2, te1_export=export_dir, targets=(24, 3, 3), run_name="dup")
        self.assertEqual(man["held_back"], [])
        by = self.splits_of(man)
        el = read_json(os.path.join(man["run_dir"], "export_links.json"))
        self.assertEqual(el["te1_rows"]["x_a_0001"]["required_split"], by[r["id"]])
        self.assertGreaterEqual(el["summary"]["duplicate_like"], 1)
        self.assertEqual(el["summary"]["conflicts"], 0)


class CrossSplitOverlapIntegrationTests(Base):
    def test_every_mt3_pair_finding_across_parts_is_listed_and_no_decision_level_pair_is_split(self):
        recs = corpus(40, seed=91)
        a, b = recs[3], recs[9]                      # azonos későbbi váltás (kérdés+válasz), eltérő előzmény
        b["turns"][3]["text"], b["turns"][2]["text"] = a["turns"][3]["text"], a["turns"][2]["text"]
        b["instruction"] = b["turns"][0]["text"]
        man, conv, report = self.pipeline(recs, targets=(32, 4, 4))
        rep = read_json(report)
        by = self.splits_of(man)
        key = {(r["file"], r["line"]): r["record"] for r in rep["records"]}
        want = set()
        for f in rep["findings"]:
            if f["scope"] in ("conversation", "sample") and f["a"]["source"] == "conversation" and f["b"]["source"] == "conversation":
                ia, ib = f["a"]["record"], f["b"]["record"]
                if ia in by and ib in by and by[ia] != by[ib]:
                    want.add(f["finding_id"])
        listed = {l.split("\t")[-1] for l in read_text(os.path.join(man["run_dir"], "cross_split_overlaps.tsv")).splitlines()[1:]}
        self.assertEqual(listed, want)
        self.assertEqual(man["cross_split"]["pairs_total"], len(want))
        self.assertEqual(man["cross_split"]["decision_level_pairs"], 0)
        self.assertTrue(man["verification"]["no_unresolved_finding_pair_across_parts"])


# ---------------------------------------------------------------------------
# kimenetek, útvonal-védelem, parancssor
# ---------------------------------------------------------------------------

class OutputAndCliTests(Base):
    def cli(self, *args):
        env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
        return subprocess.run([sys.executable, TOOL_PATH, *args], capture_output=True, text=True, encoding="utf-8", env=env)

    def setUp(self):
        super().setUp()
        self.recs = corpus(20, seed=101)
        self.conv = self.write_convs(self.recs, "cli.jsonl")
        self.report = self.mt3([self.conv])

    def base_args(self, name, *extra):
        return ["--mode", "fixture", "--conversations", self.conv, "--mt3-report", self.report, "--out-dir", self.out,
                "--te1-export", self.export_dir, "--targets", "16,2,2", "--run-name", name, *extra]

    def test_exit_codes(self):
        r = self.cli(*self.base_args("ok"))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("NEM jóváhagyott", r.stdout)
        self.assertIn("train", r.stdout)
        self.assertEqual(self.cli(*self.base_args("ok")).returncode, ms.EXIT_OUTPUT)
        self.assertEqual(self.cli("--mode", "fixture").returncode, 2)
        self.assertEqual(self.cli(*self.base_args("t", "--targets", "1,2")).returncode, 2)
        self.assertEqual(self.cli(*self.base_args("t2", "--min-hard-test", "sok")).returncode, 2)
        self.assertEqual(self.cli(*self.base_args("nf")[:2], "--conversations", os.path.join(self.tmp, "nincs.jsonl"), "--mt3-report", self.report,
                                  "--out-dir", self.out).returncode, ms.EXIT_INPUT)
        args = self.base_args("d1")
        args[args.index("fixture")] = "dataset"
        self.assertEqual(self.cli(*args).returncode, ms.EXIT_INVALID)
        self.assertEqual(self.cli(*self.base_args("x3", "--exclusions", os.path.join(self.tmp, "nincs.txt"))).returncode, ms.EXIT_EXCLUSIONS)
        with open(self.conv, "ab") as f:
            f.write(b"\n")
        self.assertEqual(self.cli(*self.base_args("stale")).returncode, ms.EXIT_STALE)
        self.assertEqual(self.cli("--verify-manifest", os.path.join(self.tmp, "nincs.json")).returncode, ms.EXIT_INPUT)

    def test_report_without_te1_comparison_warns_and_signals_attention_through_the_cli(self):
        conv = self.write_convs(corpus(20, seed=104), "nx.jsonl")
        report = self.mt3([conv], export_dir=None)
        args = ["--mode", "fixture", "--conversations", conv, "--mt3-report", report, "--out-dir", self.out, "--targets", "16,2,2"]
        self.assertEqual(self.cli(*args, "--run-name", "nx1").returncode, ms.EXIT_STALE)
        r = self.cli(*args, "--run-name", "nx2", "--allow-no-te1-comparison")
        self.assertEqual(r.returncode, ms.EXIT_ATTENTION, r.stdout + r.stderr)
        self.assertIn("TE-1 export összevetés nélküli", r.stdout)
        m = read_json(os.path.join(self.out, "nx2", "split_manifest.json"))
        self.assertTrue(any("TE-1 export összevetés nélküli" in w for w in m["warnings"]))
        self.assertEqual(m["counts"]["assigned"], 20)

    def test_verify_manifest_through_the_cli(self):
        self.assertEqual(self.cli(*self.base_args("vm")).returncode, 0)
        mp = os.path.join(self.out, "vm", "split_manifest.json")
        r = self.cli("--verify-manifest", mp)
        self.assertEqual(r.returncode, 0, r.stderr)
        with open(self.conv, "ab") as f:
            f.write(b"\n")
        r = self.cli("--verify-manifest", mp)
        self.assertEqual(r.returncode, ms.EXIT_STALE)
        self.assertIn("MEGVÁLTOZOTT", r.stderr)

    def test_output_path_guards_no_overwrite_and_sources_untouched(self):
        for inside in (os.path.join(self.conv_dir, "belul"), os.path.join(os.path.dirname(self.report), "belul")):
            with self.assertRaises(ms.OutputError):
                ms.run_from_files([self.conv], inside, "fixture", self.report, te1_export=self.export_dir, run_name="a")
        for name in ("clean", "raw", "rejected", "inbox"):
            with self.assertRaises(ms.OutputError):
                ms.run_from_files([self.conv], os.path.join(REPO_ROOT, "data", name, "mt2"), "fixture", self.report, te1_export=self.export_dir, run_name="a")
            self.assertFalse(os.path.exists(os.path.join(REPO_ROOT, "data", name, "mt2")))
        with self.assertRaises(ms.OutputError):
            ms.run_from_files([self.conv], os.path.join(self.export_dir, "belul"), "fixture", self.report, te1_export=self.export_dir, run_name="a")
        before = {p: hashlib.sha256(read_bytes(p)).hexdigest() for p in (self.conv, self.report)}
        ms.run_from_files([self.conv], self.out, "fixture", self.report, te1_export=self.export_dir, targets=(16, 2, 2), run_name="once")
        self.assertEqual(before, {p: hashlib.sha256(read_bytes(p)).hexdigest() for p in (self.conv, self.report)})
        with self.assertRaises(ms.OutputError):
            ms.run_from_files([self.conv], self.out, "fixture", self.report, te1_export=self.export_dir, targets=(16, 2, 2), run_name="once")
        with self.assertRaises(ms.OutputError):
            ms.run_from_files([self.conv], self.out, "fixture", self.report, te1_export=self.export_dir, run_name="../kifelé")
        self.assertEqual(sorted(os.listdir(os.path.join(self.out, "once"))),
                         sorted(["assignment.tsv", "held_back.tsv", "groups.tsv", "ids_train.txt", "ids_validation.txt", "ids_test.txt",
                                 "cross_split_overlaps.tsv", "export_links.json", "split_manifest.json"]))

    def test_manifest_records_inputs_settings_membership_and_assignment(self):
        man = ms.run_from_files([self.conv], self.out, "fixture", self.report, te1_export=self.export_dir, targets=(16, 2, 2), seed="egyedi", run_name="mf")
        m = read_json(os.path.join(man["run_dir"], "split_manifest.json"))
        self.assertEqual(m["tool_version"], ms.TOOL_VERSION)
        self.assertEqual(m["inputs"]["conversation_files"][0]["sha256"], hashlib.sha256(read_bytes(self.conv)).hexdigest())
        self.assertEqual(m["inputs"]["conversation_files"][0]["records"], 20)
        self.assertEqual(m["inputs"]["te1_export"]["excluded_rows"], ["x_excl_0001"])
        self.assertEqual(m["inputs"]["te1_export"]["rows"], 2)
        self.assertEqual(m["config"]["seed"], "egyedi")
        self.assertEqual(m["config"]["targets"], {"train": 16, "validation": 2, "test": 2})
        self.assertIn("nem a deklarált split_group", m["config"]["unit"])
        self.assertEqual(len(m["assignment"]), 20)
        first = m["assignment"][0]
        self.assertEqual(set(first), {"id", "file", "line", "line_sha256", "unit", "split"})
        self.assertEqual(m["units"][first["unit"]]["split"], first["split"])
        self.assertEqual(len(m["assignment_sha256"]), 64)
        self.assertTrue(any("TE-3" in l for l in m["limitations"]))
        self.assertFalse(m["training_ready"] or m["content_verified"] or m["split_approved"])
        canon = "\n".join(f"{a['file']}:{a['line']}:{a['id']}\t{a['split']}" for a in sorted(m["assignment"], key=lambda a: (a["file"], a["line"])))
        self.assertEqual(hashlib.sha256(canon.encode("utf-8")).hexdigest(), m["assignment_sha256"])

    def test_verification_failure_produces_no_output(self):
        recs = corpus(10, seed=102)
        conv = self.write_convs(recs, "vf.jsonl")
        report = self.mt3([conv])
        with mock.patch.object(ms, "verify_split", lambda *a, **k: {"all_records_accounted_for": False, "no_unit_split_across_parts": True}):
            with self.assertRaises(ms.VerificationError) as ctx:
                ms.run_from_files([conv], self.out, "fixture", report, te1_export=self.export_dir, targets=(8, 1, 1), run_name="vf")
        self.assertIn("all_records_accounted_for", str(ctx.exception))
        self.assertEqual(ctx.exception.exit_code, ms.EXIT_VERIFY)
        self.assertFalse(os.path.exists(os.path.join(self.out, "vf")))


# ---------------------------------------------------------------------------
# valós TE-1 export (csak olvasva) és a valódi adat érintetlensége
# ---------------------------------------------------------------------------

@unittest.skipUnless(os.path.isdir(os.path.join(REPO_ROOT, "data", "clean")), "nincs data/clean")
class RealExportPipelineTests(unittest.TestCase):
    """A valódi TE-1 export (4494 példa, 6 kizárt sor) mint referencia; a beszélgetések mesterséges tesztadatok."""

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.clean_files = sorted(glob.glob(os.path.join(REPO_ROOT, "data", "clean", "*.jsonl")))
        cls.before = {p: hashlib.sha256(read_bytes(p)).hexdigest() for p in cls.clean_files}
        m = te1.run_export(os.path.join(cls._tmp.name, "te1"), run_name="real1")
        cls.export_dir = m["run_dir"]
        os.makedirs(os.path.join(cls._tmp.name, "convs"))
        cls.conv = os.path.join(cls._tmp.name, "convs", "convs.jsonl")
        write_jsonl(cls.conv, corpus(40, seed=111))
        rep = dd.run_from_files([cls.conv], os.path.join(cls._tmp.name, "mt3"), "fixture", te1_export=cls.export_dir, run_name="real")
        cls.report = os.path.join(rep["run_dir"], "dedupe_report.json")
        Base.ensure_tool_sha(cls.report)
        cls.man = ms.run_from_files([cls.conv], os.path.join(cls._tmp.name, "mt2"), "fixture", cls.report, te1_export=cls.export_dir,
                                    targets=(32, 4, 4), run_name="real")

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_the_real_export_is_the_reference_and_the_six_excluded_rows_are_recorded(self):
        e = self.man["inputs"]["te1_export"]
        self.assertEqual(e["rows"], 4494)
        self.assertEqual(len(e["excluded_rows"]), 6)
        self.assertIn("uncertainty_source_request_0220", e["excluded_rows"])
        self.assertEqual(self.man["export_links"]["links"], 0, "a mesterséges beszélgetések nem egyeznek a valódi példákkal")
        self.assertEqual(self.man["counts"]["held_back"], 0)
        self.assertEqual(self.man["deviation"]["achieved"], {"train": 32, "validation": 4, "test": 4})
        self.assertEqual(ms.verify_manifest(os.path.join(self.man["run_dir"], "split_manifest.json")), ([], []))

    def test_real_data_and_export_are_untouched_and_no_multiturn_data_exists(self):
        self.assertEqual(self.before, {p: hashlib.sha256(read_bytes(p)).hexdigest() for p in self.clean_files})
        for kind in ("raw", "clean", "rejected", "inbox"):
            self.assertEqual(glob.glob(os.path.join(REPO_ROOT, "data", kind, "**", "*multiturn*"), recursive=True), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
