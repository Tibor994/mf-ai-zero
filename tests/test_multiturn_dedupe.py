"""
MF-AI-Zero - MT-3 teszt: tools/multiturn_dedupe.py (többfordulós duplikáció-ellenőrzés és csoportosítás).

FONTOS: kizárólag mesterséges tesztadatot használ (tests/fixtures/multiturn/ fixture-ök átalakított másolatai,
`mtfx_` azonosítóval, fixture móddal, ideiglenes mappákban); ez NEM része az 1000 beszélgetéses csomagnak, és
a valódi datasettet nem érinti. A valós adatos rész (RealExportAcceptanceTests) a TE-1 exportot csak OLVASSA.
A teszt nem tanít semmit.

Célzott esetek: pontos másolat; ismétlődő azonosító; névcserés (kiegészítő jelzés) és átfogalmazott (kísérleti
jelzés) változat; közös köszönés eltérő feladattal; azonos kérdés eltérő előzménnyel; felcserélt szerepek és
üzenetsorrend; láncolt csoportképzés; meglévő (TE-1) exporttal való egyezés; hibás és időközben megváltozott
bemenet; határértékek (alapból szigorú ">" 0,90 / 0,95; `--inclusive-boundaries`: ">="); rövid szövegek (pontos
egyezés rövidségtől függetlenül reject, hasonlóság csak review); a közös split_group nem írja felül a döntést;
az előszűrés egyezése a teljes összehasonlítással; kivételek (reject-szinten dokumentált `capability` kell);
jelentés-mezők; parancssor.

Futtatás:
    python -m unittest tests.test_multiturn_dedupe
    python tests/test_multiturn_dedupe.py
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
from unittest import mock

TOOLS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools")
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, TOOLS_DIR)

import dataset_export_train as te1  # noqa: E402
import multiturn_dedupe as dd  # noqa: E402
import multiturn_validate as mt  # noqa: E402

TOOL_PATH = os.path.join(TOOLS_DIR, "multiturn_dedupe.py")
FIXTURE_FILE = os.path.join(REPO_ROOT, "tests", "fixtures", "multiturn", "valid_conversations.jsonl")
BANK = mt.load_name_bank()
MASKER = dd.NameMasker(BANK)
MARK = "Státusz: teszt; " + te1.EXCLUSION_NOTE_MARKER + ", amíg a felülvizsgálat nem történik meg."


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


def fx(n):
    with open(FIXTURE_FILE, encoding="utf-8") as f:
        return copy.deepcopy([json.loads(l) for l in f if l.strip()][n - 1])


def relabel(rec, rid, group, persona):
    rec["id"], rec["meta"]["split_group"], rec["meta"]["persona"] = rid, group, persona
    return rec


def set_texts(rec, texts):
    for i, t in enumerate(texts):
        rec["turns"][i]["text"] = t
    rec["instruction"], rec["output"] = texts[0], texts[-1]
    return rec


def texts_of(rec):
    return [t["text"] for t in rec["turns"]]


def swap_names(rec, mapping):
    new = [t["text"] for t in rec["turns"]]
    for old, nw in mapping.items():
        new = [t.replace(old, nw) for t in new]
    set_texts(rec, new)
    rec["meta"]["persona_names"] = [mapping.get(n, n) for n in rec["meta"]["persona_names"]]
    return rec


def prepend_exchange(rec, user, assistant):
    rec["turns"] = [{"role": "user", "text": user}, {"role": "assistant", "text": assistant}] + rec["turns"]
    rec["meta"]["n_exchanges"] += 1
    rec["meta"]["depends"] = [{"turn": d["turn"] + 2, "on": [i + 2 for i in d["on"]], "depth": d["depth"]}
                              for d in rec["meta"]["depends"]]
    rec["instruction"] = user
    return rec


def pad(rec, filler):
    return set_texts(rec, [t["text"] + " " + filler[i % len(filler)] for i, t in enumerate(rec["turns"])])


NAMES = BANK["approved_given_names"]
NAMES_A, NAMES_B = NAMES[0:6], NAMES[6:12]


def name_tail(given):
    return " Ott lesz: " + ", ".join(given[:-1]) + " és " + given[-1] + "."


def name_heavy(rec, given, rid, group, persona):
    """Minden üzenet végére egy névlista kerül: két ilyen beszélgetés nyers hasonlósága < 0,90, névsemlegesítve 1,0."""
    set_texts(rec, [t["text"] + name_tail(given) for t in rec["turns"]])
    rec["meta"]["persona_names"] = sorted(set(rec["meta"]["persona_names"]) | set(given))
    return relabel(rec, rid, group, persona)


PARAPHRASE_001 = [
    "Üdv! A nevem Réka, a húgom szülinapjára holnap tortát készítek, és azt szeretném tudni, mennyi lisztre lesz szükségem.",
    "Üdv, Réka! Egy szokásos 24 centiméteres tortához kb. 250 gramm liszt szükséges. Hányan lesznek a vendégek?",
    "Összesen nyolcan, a húgom, Panna is közéjük tartozik.",
    "Nyolc személyre elegendő ez a 24 centiméteres torta, ha nem túl vastag szeleteket vágsz. Nagyobb szeletekhez másfélszeres mennyiséggel érdemes számolni.",
    "Tehát mennyi lisztet kell vásárolnom, hogy mindenképp elég legyen?",
    "Másfélszeres adagnál körülbelül 375 gramm liszt kell, ezért egy fél kilós zacskó bőven elég, Réka.",
]
FILLER_1 = ["Egyébként ezt csak úgy megjegyzem a rend kedvéért.", "Biztos, ami biztos, ezt jó tudni előre is.",
            "Ez így egyszerűbb lesz mindannyiunknak.", "Ha kérdés adódik közben, bátran szólj majd."]
FILLER_2 = ["Mellesleg ezt érdemes még külön átgondolni később.", "Természetesen erre később is visszatérhetünk bármikor.",
            "Nyugodtan hagyd rá az időt, semmi sürgős.", "Szükség esetén persze mindent újra átnézünk együtt."]
BREAD = [  # más téma, azonos kérdés a 4. üzenetnél, mint a 001 fixture-ben
    "Sziasztok! Bence vagyok, vasárnapra kenyeret szeretnék sütni, de még sosem csináltam.",
    "Szia, Bence! Kezdőknek jó a sima, kovász nélküli élesztős kenyér, ahhoz liszt, víz, só és egy kis élesztő kell.",
    "Rendben, egy kilós cipót szeretnék.",
    "Egy kilós cipóhoz nagyjából 600 gramm liszt, 400 milliliter víz, két teáskanál só és egy kocka friss élesztő szokásos.",
    "Akkor mennyi lisztet vegyek, hogy biztosan jusson?",
    "Ha a receptet másfélszeresre növelnéd, egy egykilós zacskó liszt biztosan elég lesz, Bence.",
]


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

    def load(self, files):
        recs, infos = dd.load_conversation_files(files, "fixture", BANK, MASKER)
        return recs

    def dedupe(self, recs, export_rows=None, **kw):
        loaded = self.load([self.write_convs(recs)])
        return dd.run_dedupe(loaded, export_rows or [], **kw)

    @staticmethod
    def kinds(res):
        return {(f["type"], f["status"]) for f in res["findings"]}

    @staticmethod
    def of_type(res, ftype):
        return [f for f in res["findings"] if f["type"] == ftype]

    @staticmethod
    def status_of(res, rid):
        return next(r for r in res["records"] if r["record"] == rid)


class NormalizationTests(unittest.TestCase):
    def test_format_markers_quotes_and_separators_do_not_distort_the_comparison(self):
        n = dd.normalize
        self.assertEqual(n("„Szia!” — mondta; 1. Öblítsd le… 2) Töröld szárazra.\n- Kend meg • újra"), "szia mondta öblítsd le töröld szárazra kend meg újra")
        self.assertEqual(n("Nyolc  főre?\t\n Igen."), n("nyolc főre igen"))
        self.assertEqual(n("A torta 24 centis, 250 gramm."), "a torta 24 centis 250 gramm", "a számok megmaradnak")
        self.assertNotEqual(n("kér"), n("ker"), "az ékezetek különbségnek számítanak")
        self.assertEqual(n("Szia _ világ"), "szia világ")

    def test_names_are_masked_only_with_a_masker_and_keep_other_capitals(self):
        self.assertEqual(dd.normalize("Réka és Panna Szegedről jön.", MASKER), "név és név szegedről jön")
        self.assertEqual(dd.normalize("Réka és Panna", None), "réka és panna")
        self.assertEqual(dd.normalize("Rékának adtam Katával.", MASKER), "név adtam név", "ragozott név is maszkolódik")
        self.assertEqual(dd.normalize("Pálinka Edény", MASKER), "pálinka edény", "közönséges szót nem maszkol")

    def test_role_tags_and_labels_are_not_part_of_the_compared_text(self):
        # a beszélgetés-szöveg összehasonlítása üzenetenként, címkék nélkül történik: a User:/AI: felirat nem szerepel
        self.assertEqual(dd.normalize("Szia!"), dd.normalize("  szia  "))


class MatchCharsTests(unittest.TestCase):
    def test_match_chars_is_autojunk_free_and_symmetric_in_count_for_simple_cases(self):
        a = ("ab" * 100) + "c" * 100
        b = ("ba" * 100) + "c" * 100
        from difflib import SequenceMatcher
        want = sum(x.size for x in SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks())
        got_junk = sum(x.size for x in SequenceMatcher(None, a, b, autojunk=True).get_matching_blocks())
        self.assertEqual(dd.match_chars(a, b), want)
        self.assertNotEqual(want, got_junk, "a teszt-szöveg olyan, hogy az autojunk eltérést okozna")
        self.assertEqual(dd.match_chars("", "abc"), 0)
        self.assertEqual(dd.ratio_of(dd.match_chars("abcd", "abcd"), 4, 4), 1.0)
        self.assertEqual(dd.ratio_of(0, 0, 0), 1.0)


class ExactAndIdTests(Base):
    def test_exact_copy_is_rejected_and_grouped(self):
        a = fx(1)
        b = relabel(copy.deepcopy(a), "mtfx_copy_001", "g8001", "p801")
        res = self.dedupe([a, b])
        f = self.of_type(res, "exact_conversation")
        self.assertEqual(len(f), 1)
        self.assertEqual((f[0]["status"], f[0]["score"]), ("reject", 1.0))
        self.assertEqual({f[0]["a"]["record"], f[0]["b"]["record"]}, {"mtfx_valid_001", "mtfx_copy_001"})
        for rid in ("mtfx_valid_001", "mtfx_copy_001"):
            self.assertEqual(self.status_of(res, rid)["progression"], "blocked")
        self.assertEqual(res["records"][0]["group_id"], res["records"][1]["group_id"])

    def test_exact_copy_stays_rejected_even_if_declared_as_variants(self):
        a = fx(1)
        b = relabel(copy.deepcopy(a), "mtfx_copy_002", a["meta"]["split_group"], a["meta"]["persona"])
        res = self.dedupe([a, b])
        self.assertEqual([f["status"] for f in self.of_type(res, "exact_conversation")], ["reject"])

    def test_duplicate_id_same_file_and_across_files(self):
        a = fx(1)
        b = copy.deepcopy(fx(2))
        b["id"] = a["id"]                                               # ugyanaz az azonosító, más tartalom
        res = self.dedupe([a, b])
        dup = self.of_type(res, "duplicate_id")
        self.assertEqual([(f["status"], f["details"]["scope_detail"]) for f in dup], [("reject", "same_file")])
        files = [self.write_convs([a], "x.jsonl"), self.write_convs([b], "y.jsonl")]
        res = dd.run_dedupe(self.load(files), [])
        dup = self.of_type(res, "duplicate_id")
        self.assertEqual([(f["status"], f["details"]["scope_detail"]) for f in dup], [("reject", "across_files")])
        self.assertEqual(len(res["groups"]), 2, "az ütköző azonosítójú rekordok csoportkulcsa is egyedi")
        self.assertEqual(len({r["group_id"] for r in res["records"]}), 2)

    def test_id_collision_with_te1_export_row(self):
        rows = [{"id": "mtfx_valid_002", "obj": {"instruction": "Valami más kérdés?", "input": "", "output": "Más válasz, elég hosszan megfogalmazva."},
                 "source_file": "x", "source_line": 1}]
        res = self.dedupe([fx(2)], rows)
        dup = self.of_type(res, "duplicate_id")
        self.assertEqual([(f["status"], f["details"]["scope_detail"]) for f in dup], [("reject", "vs_te1_export")])

    def test_duplicate_id_and_exact_copy_cannot_be_waived(self):
        a = fx(1)
        b = relabel(copy.deepcopy(a), "mtfx_copy_003", "g8003", "p803")
        for ftype in ("exact_conversation", "duplicate_id"):
            with self.assertRaises(dd.ExceptionsError):
                dd.apply_exceptions(self.dedupe([a, b])["findings"],
                                    [{"a": "mtfx_valid_001", "b": "mtfx_copy_003", "waive": [ftype],
                                      "reason": "Ez az indoklás elég hosszú, de nem menthető fel."}], {"mtfx_valid_001", "mtfx_copy_003"})


class VariantTests(Base):
    def test_name_swapped_copy_is_decided_on_the_original_text_not_on_the_masked_one(self):
        a = fx(1)
        b = swap_names(relabel(fx(1), "mtfx_names_001", "g8002", "p802"), {"Réka": "Anna", "Panna": "Lilla"})
        self.assertNotEqual(texts_of(a), texts_of(b))
        res = self.dedupe([a, b])                                        # a névsemlegesítés be van kapcsolva (alap), mégsem az dönt
        self.assertEqual(self.of_type(res, "exact_after_normalization"), [], "a névcsere nem 'pontos egyezés'")
        self.assertEqual(self.of_type(res, "exact_conversation"), [])
        near = self.of_type(res, "near_conversation")
        self.assertEqual([f["status"] for f in near], ["reject"])
        self.assertTrue(dd.REJECT_MIN < near[0]["score"] < 1.0, near[0]["score"])
        self.assertEqual(self.of_type(res, "name_swapped_match") + self.of_type(res, "sample_name_swapped"), [],
                         "a nyers nézeten már döntés-szintű a találat: nincs külön kiegészítő jelzés")
        self.assertEqual(res["records"][0]["group_id"], res["records"][1]["group_id"])
        raw = dd.load_conversation_files([self.write_convs([a, b], "raw.jsonl")], "fixture", BANK, None)[0]
        off = dd.run_dedupe(raw, [])
        pick = lambda r: sorted((f["type"], f["status"], f["score"]) for f in r["findings"] if f["scope"] != "group")
        self.assertEqual(pick(res), pick(off), "a névsemlegesítés kikapcsolása nem változtat a nyers nézeten hozott döntésen")

    def test_formatting_only_difference_is_exact_after_normalization_and_cannot_be_waived(self):
        a = fx(1)
        b = set_texts(relabel(fx(1), "mtfx_fmt_001", "g8003", "p803"), [t.lower() for t in texts_of(a)])
        res = self.dedupe([a, b])
        f = self.of_type(res, "exact_after_normalization")
        self.assertEqual([(x["status"], x["score"]) for x in f], [("reject", 1.0)])
        self.assertEqual(self.of_type(res, "exact_conversation"), [], "a nyers szöveg különbözik")
        self.assertEqual({x["status"] for x in self.of_type(res, "sample_exact")}, {"reject"})
        for ftype in ("exact_after_normalization", "sample_exact"):
            with self.assertRaises(dd.ExceptionsError):
                dd.apply_exceptions(res["findings"], [{"a": "mtfx_valid_001", "b": "mtfx_fmt_001", "waive": [ftype],
                                                       "reason": "Ez az indoklás elég hosszú, de nem menthető fel.",
                                                       "capability": "Dokumentált, eltérő képességet tanít (állítólag)."}],
                                    {"mtfx_valid_001", "mtfx_fmt_001"})

    def make_name_heavy_pair(self, group_b="g8006"):
        return (name_heavy(fx(1), NAMES_A, "mtfx_nh_a", "g8005", "p805"),
                name_heavy(fx(1), NAMES_B, "mtfx_nh_b", group_b, "p806"))

    def test_name_masked_match_is_a_supplementary_review_signal_that_keeps_the_original_text(self):
        a, b = self.make_name_heavy_pair()
        recs = self.load([self.write_convs([a, b], "premise.jsonl")])
        raw_s = dd.conv_pair_score(recs[0], recs[1], False, dd.Stats(), floor=0.0, rep="raw")
        msk_s = dd.conv_pair_score(recs[0], recs[1], False, dd.Stats(), floor=0.0, rep="msk")
        self.assertTrue(dd.GROUP_MIN <= raw_s <= dd.REVIEW_MIN, raw_s)
        self.assertEqual(msk_s, 1.0, "a feltevés: névsemlegesítve azonos, nyersen a 0,90 határ alatt")
        self.assertEqual(recs[0].raw, texts_of(a), "az eredeti szöveg a betöltött rekordban változatlan")
        res = dd.run_dedupe(recs, [])
        f = self.of_type(res, "name_swapped_match")
        self.assertEqual([(x["status"], x["score"]) for x in f], [("review", 1.0)])
        det = f[0]["details"]
        self.assertTrue(det["experimental_supplementary"])
        self.assertEqual(det["masked_score"], 1.0)
        self.assertLessEqual(det["raw_score"], dd.REVIEW_MIN)
        self.assertTrue(set(NAMES_A) <= set(det["names_a"]) and set(NAMES_B) <= set(det["names_b"]))
        self.assertGreaterEqual(len(det["differing_original_messages"]), 1)
        for d in det["differing_original_messages"]:
            self.assertEqual(d["text_a"], texts_of(a)[d["message"]], "az eredeti szöveg szerepel a jelentésben")
            self.assertEqual(d["text_b"], texts_of(b)[d["message"]])
        self.assertIn("puszta névcsere nem új képesség", f[0]["reason"])
        self.assertEqual(self.of_type(res, "exact_after_normalization"), [])
        self.assertEqual([(x["status"]) for x in self.of_type(res, "near_variant")], ["info"], "a nyers nézeten csak csoportosító jelzés van")
        samples = self.of_type(res, "sample_name_swapped")
        self.assertEqual(len(samples), 3)
        self.assertEqual({x["status"] for x in samples}, {"review"})
        for x in samples:
            t = x["a"]["turn"]
            self.assertEqual(x["details"]["original_a"], {"question": texts_of(a)[t - 1], "answer": texts_of(a)[t]})
            self.assertEqual(x["details"]["original_b"], {"question": texts_of(b)[t - 1], "answer": texts_of(b)[t]})
            self.assertLess(x["details"]["raw_score"], dd.REVIEW_MIN + 1e-9)
        self.assertEqual({x["status"] for x in res["findings"] if x["type"] in ("name_swapped_match", "sample_name_swapped")}, {"review"},
                         "a kiegészítő jelzés sosem utasít el automatikusan és sosem fogad el")
        self.assertEqual({r["progression"] for r in res["records"]}, {"blocked"})
        self.assertEqual(res["records"][0]["group_id"], res["records"][1]["group_id"])
        self.assertIn("name_swapped", {e["link"] for g in res["groups"].values() for e in g["edges"]})
        self.assertEqual(res["summary"]["experimental_signals"]["name_supplementary"], 4)

    def test_name_supplementary_signal_is_off_without_name_normalization_and_skipped_for_name_free_pairs(self):
        a, b = self.make_name_heavy_pair()
        raw = dd.load_conversation_files([self.write_convs([a, b], "off.jsonl")], "fixture", BANK, None)[0]
        res = dd.run_dedupe(raw, [])
        self.assertEqual([f for f in res["findings"] if f["status"] in ("reject", "review")], [])
        self.assertEqual(res["counters"]["name_supplementary_pass"]["conversation_pairs"]["pairs_considered"], 0)
        free = [PrefilterEquivalenceTests.rec(i, ["Egy alap mondat szám %d." % k for k in range(4)]) for i in range(3)]
        res = dd.run_dedupe(free, [])
        self.assertEqual(res["counters"]["name_supplementary_pass"]["conversation_pairs"]["pairs_considered"], 0,
                         "név nélküli beszélgetéseken a kiegészítő menet nem fut")
        self.assertEqual(res["summary"]["experimental_signals"]["name_supplementary"], 0)

    def test_conversation_level_name_signal_links_the_pair_on_its_own(self):
        recs = [PrefilterEquivalenceTests.rec(i, ["Egy alap mondat szám %d." % k for k in range(4)], masker=MASKER) for i in range(2)]
        F, Fm = dd.Findings(), dd.Findings()
        loc = {"source": "conversation", "record": "syn_000", "file": "syn", "line": 1}
        Fm.add("conversation", "exact_after_normalization", loc, dict(loc, record="syn_001", line=2), 1.0, "m", "reject", "r", pair=("conv", 0, 1))
        added = dd.merge_name_signals(F, Fm, recs, {}, [], [])
        self.assertEqual(added, 1)
        self.assertEqual([(f["type"], f["status"], f["score"]) for f in F.items], [("name_swapped_match", "review", 1.0)])
        self.assertEqual(F.edges, [(0, 1, "name_swapped", 1.0)], "a mintaszintű jelzés nélkül is összekapcsolja a beszélgetéseket")
        self.assertEqual(F.items[0]["details"]["masked_score"], 1.0)

    def test_shared_split_group_does_not_override_the_duplicate_decision(self):
        names = {"Réka": "Anna", "Panna": "Lilla"}
        seen = {}
        for declared in (False, True):
            a = fx(1)
            group = a["meta"]["split_group"] if declared else "g8005"
            b = swap_names(relabel(fx(1), "mtfx_names_010", group, a["meta"]["persona"] if declared else "p805"), names)
            res = self.dedupe([a, b])
            near = self.of_type(res, "near_conversation")
            self.assertEqual([(f["status"], f["details"]["declared_variant"]) for f in near], [("reject", declared)])
            self.assertGreater(near[0]["score"], dd.REJECT_MIN)
            self.assertNotIn("deklarált", near[0]["reason"], "a deklarált csoport nem szerepel felmentő indokként")
            sample_status = {f["status"] for f in res["findings"] if f["type"] in ("sample_exact", "sample_near")}
            self.assertIn("reject", sample_status, res["summary"]["findings_by_type_status"])
            self.assertLessEqual(sample_status, {"reject", "review"}, "nincs lefokozás: a minta-találat a saját pontszáma szerint reject/review")
            for f in res["findings"]:
                if f["type"] in ("sample_exact", "sample_near"):
                    self.assertEqual(f["status"], dd.similarity_status(f["score"], f["type"] == "sample_exact"), f["details"])
            self.assertEqual({r["progression"] for r in res["records"]}, {"blocked"})
            seen[declared] = sorted((f["type"], f["status"], f["score"]) for f in res["findings"] if f["scope"] != "group")
        self.assertEqual(seen[False], seen[True], "a döntés ugyanaz a deklarált csoporttal és anélkül")

    def test_declared_variant_with_exact_or_formatting_only_copy_stays_reject(self):
        a = fx(1)
        b = set_texts(relabel(fx(1), "mtfx_decl_001", a["meta"]["split_group"], a["meta"]["persona"]), [t.lower() for t in texts_of(a)])
        res = self.dedupe([a, b])
        self.assertEqual([(f["type"], f["status"]) for f in self.of_type(res, "exact_after_normalization")], [("exact_after_normalization", "reject")])
        self.assertTrue(self.of_type(res, "exact_after_normalization")[0]["details"]["declared_variant"])
        self.assertEqual({f["status"] for f in self.of_type(res, "sample_exact")}, {"reject"})

    def test_paraphrase_is_review_grouped_and_shows_the_char_threshold_mismatch(self):
        a = fx(1)
        b = set_texts(relabel(fx(1), "mtfx_para_001", "g8004", "p804"), PARAPHRASE_001)
        res = self.dedupe([a, b])
        f = self.of_type(res, "probable_paraphrase_variant")
        self.assertEqual([x["status"] for x in f], ["review"])
        self.assertTrue(f[0]["details"]["heuristic"])
        self.assertTrue(f[0]["details"]["experimental"], "a heurisztika kísérletiként van jelölve")
        self.assertIn("KÍSÉRLETI", f[0]["reason"])
        self.assertIn("nem helyettesíti a tartalmi átolvasást", f[0]["reason"])
        self.assertEqual(res["summary"]["experimental_signals"]["paraphrase_heuristic"], 1)
        self.assertGreaterEqual(f[0]["score"], dd.PARAPHRASE_MIN)
        # a karakter-alapú (0,90/0,95) határok átfogalmazásnál nem értelmezhetők: nincs near_conversation találat
        self.assertEqual([t for t in self.kinds(res) if t[0] in ("near_conversation", "near_variant")], [])
        st = dd.Stats()
        recs = self.load([self.write_convs([a, b], "p.jsonl")])
        pooled = dd.conv_pair_score(recs[0], recs[1], False, st, floor=0.0)
        self.assertLess(pooled, dd.GROUP_MIN)
        self.assertGreater(pooled, 0.5, "a karakter-arány részleges átfedést mutat, de a döntési határok alatt marad")
        self.assertEqual(res["records"][0]["group_id"], res["records"][1]["group_id"])
        self.assertIn("paraphrase_heuristic", {e["link"] for g in res["groups"].values() for e in g["edges"]})

    def test_unrelated_fixture_conversations_produce_no_findings(self):
        recs = [fx(n) for n in range(1, 6)]
        res = self.dedupe(recs)
        self.assertEqual(res["findings"], [])
        self.assertTrue(all(r["progression"] == "clear_of_duplicate_findings" for r in res["records"]))
        self.assertEqual(len(res["groups"]), 5)


class RolePreservationApiTests(unittest.TestCase):
    def test_conversation_score_is_zero_when_the_roles_at_the_same_index_differ(self):
        def rec(idx, roles):
            obj = {"id": f"r{idx}", "turns": [{"role": r, "text": "ugyanaz a szöveg %d szám" % i * 3} for i, r in enumerate(roles)],
                   "meta": {"depends": []}}
            return dd.make_rec(idx, obj, "f", 0, idx + 1, "x", None)

        a = rec(0, ["user", "assistant", "user", "assistant"])
        same = rec(1, ["user", "assistant", "user", "assistant"])
        swapped = rec(2, ["assistant", "user", "assistant", "user"])
        self.assertEqual(dd.conv_pair_score(a, same, False, dd.Stats(), floor=0.0), 1.0)
        self.assertEqual(dd.conv_pair_score(a, swapped, False, dd.Stats(), floor=0.0), 0.0)
        self.assertEqual(dd.conv_pair_score(a, swapped, True, dd.Stats()), 0.0, "a szűrő és a teljes összehasonlítás egyezik")


class GreetingAndContextTests(Base):
    GREETING = ("Szia!", "Szia! Miben segíthetek?")

    def test_shared_greeting_does_not_make_the_conversation_a_duplicate_but_the_identical_sample_is_rejected(self):
        a = prepend_exchange(relabel(fx(1), "mtfx_greet_a", "g8010", "p810"), *self.GREETING)
        b = prepend_exchange(relabel(fx(5), "mtfx_greet_b", "g8011", "p811"), *self.GREETING)
        res = self.dedupe([a, b])
        conv_level = [f for f in res["findings"] if f["scope"] == "conversation"]
        self.assertEqual(conv_level, [], "közös köszönés önmagában nem tesz duplikálttá egy beszélgetést")
        exact = self.of_type(res, "sample_exact")
        self.assertEqual([(f["status"], f["a"]["turn"], f["b"]["turn"]) for f in exact], [("reject", 1, 1)],
                         "a teljes (üres előzménnyel együtt) azonos minta rövidségtől függetlenül reject")
        self.assertTrue(exact[0]["details"]["short_text"])
        self.assertEqual(exact[0]["score"], 1.0)
        self.assertIn("rövidségtől függetlenül", exact[0]["reason"])
        self.assertEqual({r["conversation_decision"] for r in res["records"]}, {"no_conversation_level_block"})
        self.assertEqual({r["progression"] for r in res["records"]}, {"blocked"}, "a minta-szintű elutasítás haladási tiltás")
        self.assertEqual(len({r["group_id"] for r in res["records"]}), 2, "a köszönés nem csoportosít")
        with self.assertRaises(dd.ExceptionsError):
            dd.apply_exceptions(res["findings"], [{"a": "mtfx_greet_a", "b": "mtfx_greet_b", "waive": ["sample_exact"],
                                                   "reason": "Ez az indoklás elég hosszú, de nem menthető fel.",
                                                   "capability": "Dokumentált, eltérő képességet tanít (állítólag)."}],
                                {"mtfx_greet_a", "mtfx_greet_b"})

    def test_short_identical_sample_with_identical_history_is_rejected_at_any_position(self):
        a = prepend_exchange(relabel(fx(1), "mtfx_hist_a", "g8014", "p814"), *self.GREETING)
        b = prepend_exchange(relabel(fx(5), "mtfx_hist_b", "g8015", "p815"), *self.GREETING)
        for r, thanks in ((a, "Köszi!"), (b, "Köszi!")):
            r["turns"] = r["turns"][:2] + [{"role": "user", "text": thanks}, {"role": "assistant", "text": "Nincs mit, szívesen!"}] + r["turns"][2:]
            r["meta"]["n_exchanges"] += 1
            r["meta"]["depends"] = [{"turn": d["turn"] + 2, "on": [i + 2 if i >= 2 else i for i in d["on"]], "depth": d["depth"]}
                                    for d in r["meta"]["depends"]]
        res = self.dedupe([a, b])
        exact = self.of_type(res, "sample_exact")
        self.assertEqual([(f["status"], f["a"]["turn"], f["b"]["turn"]) for f in exact], [("reject", 1, 1), ("reject", 3, 3)],
                         "az azonos előzményű rövid minta a 2. váltásnál is pontos egyezés")
        self.assertTrue(all(f["details"]["short_text"] for f in exact))
        self.assertEqual(exact[1]["details"]["context_kind"], "előzményes")

    def test_a_pair_is_short_when_either_side_is_short(self):
        stub = BoundaryAndDecisionTests.stub_recs()
        sa = BoundaryAndDecisionTests.sample(0, "a" * 30, "c" * 29)              # 59 karakter: rövid
        sb = BoundaryAndDecisionTests.sample(1, "a" * 31, "c" * 29)              # 60 karakter: nem rövid; a hasonlóság 0,98 > 0,95
        self.assertTrue(sa.raw.trivial and not sb.raw.trivial)
        for prefilter in (True, False):
            F = dd.Findings()
            dd.evaluate_sample_pair(sa, sb, "raw", prefilter, False, dd.Stats(), F, stub, [])
            self.assertEqual([(f["type"], f["status"]) for f in F.items], [("sample_near_short", "review")],
                             "a rövid oldal miatt a hasonlóság nem utasít el automatikusan")
            self.assertGreater(F.items[0]["score"], dd.REJECT_MIN)

    def test_short_similar_sample_is_review_only_as_a_documented_experimental_exception(self):
        stub = BoundaryAndDecisionTests.stub_recs()
        sa = BoundaryAndDecisionTests.sample(0, "hány nap van egy hétben", "egy hétben hét nap van")
        sb = BoundaryAndDecisionTests.sample(1, "hány nap van egy évben", "egy évben hét nap van")
        self.assertTrue(sa.raw.trivial and sb.raw.trivial)
        for inclusive in (False, True):
            for prefilter in (True, False):
                F = dd.Findings()
                dd.evaluate_sample_pair(sa, sb, "raw", prefilter, inclusive, dd.Stats(), F, stub, [])
                self.assertEqual([(f["type"], f["status"]) for f in F.items], [("sample_near_short", "review")])
                self.assertTrue(F.items[0]["details"]["experimental_short_text_exception"])
                self.assertTrue(F.items[0]["details"]["short_text"])
                self.assertIn("KÍSÉRLETI", F.items[0]["reason"])
                self.assertGreater(F.items[0]["score"], 0.90)
                self.assertEqual(F.edges, [], "a rövid hasonlóság nem csoportosít")
        # ugyanez hosszú szövegen 0,95 fölött reject: a rövid szöveg kivétele sosem utasít el automatikusan
        long_q = "a" * 96 + "b" * 4
        F = dd.Findings()
        dd.evaluate_sample_pair(BoundaryAndDecisionTests.sample(0, long_q, "válasz " * 10), BoundaryAndDecisionTests.sample(1, long_q[:-4] + "cccc", "válasz " * 10),
                                "raw", True, False, dd.Stats(), F, stub, [])
        self.assertEqual([(f["type"], f["status"]) for f in F.items], [("sample_near", "reject")])

    def test_same_question_different_history_is_only_partial_overlap(self):
        a = fx(1)
        b = set_texts(relabel(fx(1), "mtfx_hist_001", "g8012", "p812"), BREAD)
        b["meta"]["persona_names"] = ["Bence"]
        res = self.dedupe([a, b])
        info = self.of_type(res, "same_question_different_context")
        self.assertEqual([(f["status"], f["a"]["turn"], f["b"]["turn"]) for f in info], [("info", 5, 5)])
        self.assertLess(info[0]["details"]["context"], 0.9)
        self.assertEqual([f for f in res["findings"] if f["status"] in ("reject", "review")], [])
        self.assertTrue(all(r["progression"] == "clear_of_duplicate_findings" for r in res["records"]))

    def test_same_question_and_same_context_is_a_duplicate_sample(self):
        a = fx(1)
        b = relabel(fx(1), "mtfx_hist_002", "g8013", "p813")
        b["turns"][5]["text"] = a["turns"][5]["text"]                   # ugyanaz a válasz
        b["turns"][1]["text"] = "Szia, Réka! Egy tipikus, 24 centis tortához úgy 250 gramm lisztet kell számolni. Hány főre készül?"
        b["instruction"] = a["instruction"]
        res = self.dedupe([a, b])
        exact = self.of_type(res, "sample_exact") + self.of_type(res, "sample_near")
        self.assertTrue(exact and all(f["status"] in ("review", "reject") for f in exact))
        self.assertEqual(self.of_type(res, "exact_conversation"), [])


class RoleAndOrderTests(Base):
    def test_role_swapped_copy_is_not_identical_but_flagged(self):
        a = fx(2)
        t = texts_of(a)
        swapped = [t[i ^ 1] for i in range(len(t))]                       # a user és assistant szövegek szerepet cserélnek
        b = set_texts(relabel(fx(2), "mtfx_swap_001", "g8020", "p820"), swapped)
        res = self.dedupe([a, b])
        self.assertEqual(self.of_type(res, "exact_conversation") + self.of_type(res, "exact_after_normalization"), [])
        f = self.of_type(res, "roles_swapped_messages")
        self.assertEqual([x["status"] for x in f], ["review"])
        self.assertGreater(f[0]["details"]["cross_role"], f[0]["details"]["same_pos"])
        self.assertEqual(res["records"][0]["group_id"], res["records"][1]["group_id"])
        # pozíció- és szerep-őrző pontszám alacsony: a szerepek jelentőségét megőrzi
        recs = self.load([self.write_convs([a, b], "r.jsonl")])
        self.assertLess(dd.conv_pair_score(recs[0], recs[1], False, dd.Stats(), floor=0.0), 0.5)

    def test_reordered_messages_are_not_identical_but_flagged(self):
        a = fx(2)
        t = texts_of(a)
        users = [t[0], t[2], t[4], t[6]]
        users = [users[2], users[3], users[0], users[1]]
        new = list(t)
        for k, u in enumerate(users):
            new[2 * k] = u
        b = set_texts(relabel(fx(2), "mtfx_order_001", "g8021", "p821"), new)
        res = self.dedupe([a, b])
        self.assertEqual(self.of_type(res, "exact_conversation") + self.of_type(res, "exact_after_normalization"), [])
        f = self.of_type(res, "messages_reordered")
        self.assertEqual([x["status"] for x in f], ["review"])
        self.assertEqual(res["records"][0]["group_id"], res["records"][1]["group_id"])

    def test_context_and_pooled_ratio_respect_roles_and_positions(self):
        same = [("user", "a" * 50), ("assistant", "b" * 50)]
        swapped_roles = [("assistant", "a" * 50), ("user", "b" * 50)]
        self.assertEqual(dd.pooled_ratio(same, same), 1.0)
        self.assertEqual(dd.pooled_ratio(same, swapped_roles), 0.0)
        self.assertEqual(dd.pooled_ratio(same, list(reversed(same))), 0.0)
        self.assertAlmostEqual(dd.pooled_ratio(same, same + [("user", "c" * 100)]), 2 / 3)     # párosítatlan üzenet a nevezőben
        self.assertEqual(dd.context_ratio((), ()), 1.0)
        self.assertEqual(dd.context_ratio((), tuple(same)), 0.0)


class ChainedGroupingTests(Base):
    def make_chain(self):
        a = relabel(fx(4), "mtfx_chain_a", "g8101", "p801")
        b = pad(relabel(fx(4), "mtfx_chain_b", "g8102", "p802"), FILLER_1)
        c = pad(pad(relabel(fx(4), "mtfx_chain_c", "g8103", "p803"), FILLER_1), FILLER_2)
        return a, b, c

    @staticmethod
    def stub_recs(ids, groups=None):
        out = []
        for i, rid in enumerate(ids):
            r = dd.Rec()
            r.idx, r.id, r.file, r.file_idx, r.line = i, rid, "f", 0, i + 1
            r.group = (groups or {}).get(rid)
            out.append(r)
        return out

    def test_single_linkage_unit_a_b_and_b_c_make_one_group_without_an_a_c_edge(self):
        recs = self.stub_recs(["r_a", "r_b", "r_c", "r_solo"])
        F = dd.Findings()
        groups, gid_by_idx = dd.build_groups(recs, [(0, 1, "near_conversation", 0.85), (1, 2, "near_conversation", 0.85)], F)
        self.assertEqual(gid_by_idx, {0: "mtg_r_a", 1: "mtg_r_a", 2: "mtg_r_a", 3: "mtg_r_solo"})
        g = groups["mtg_r_a"]
        self.assertEqual((g["members"], g["size"]), (["r_a", "r_b", "r_c"], 3))
        self.assertEqual({(e["a"], e["b"]) for e in g["edges"]}, {("r_a", "r_b"), ("r_b", "r_c")})
        self.assertEqual(F.items, [])

    def test_group_id_is_the_smallest_member_id_and_stable_when_larger_ids_join(self):
        base = dd.build_groups(self.stub_recs(["m_02", "m_05"]), [(0, 1, "x", 0.9)], dd.Findings())[0]
        grown = dd.build_groups(self.stub_recs(["m_02", "m_05", "m_09"]), [(0, 1, "x", 0.9), (1, 2, "x", 0.9)], dd.Findings())[0]
        self.assertEqual(list(base), ["mtg_m_02"])
        self.assertEqual(list(grown), ["mtg_m_02"])
        shifted = dd.build_groups(self.stub_recs(["m_01", "m_02", "m_05"]), [(1, 2, "x", 0.9), (0, 1, "x", 0.9)], dd.Findings())[0]
        self.assertEqual(list(shifted), ["mtg_m_01"], "kisebb azonosítójú tag csatlakozásakor a csoportazonosító változik (dokumentált)")

    def test_chained_similarity_in_real_records_forms_one_group(self):
        a, b, c = self.make_chain()
        recs = self.load([self.write_convs([a, b, c], "ch.jsonl")])
        st = dd.Stats()
        ab, bc, ac = (dd.conv_pair_score(recs[i], recs[j], False, st, floor=0.0) for i, j in ((0, 1), (1, 2), (0, 2)))
        self.assertTrue(0.80 <= ab < 0.90 and 0.80 <= bc < 0.90 and ac < 0.80, (ab, bc, ac))
        res = dd.run_dedupe(recs, [])
        self.assertEqual({r["group_id"] for r in res["records"]}, {"mtg_mtfx_chain_a"})
        g = res["groups"]["mtg_mtfx_chain_a"]
        self.assertEqual(g["members"], ["mtfx_chain_a", "mtfx_chain_b", "mtfx_chain_c"])
        near = {(e["a"], e["b"]) for e in g["edges"] if e["link"] == "near_conversation"}
        self.assertEqual(near, {("mtfx_chain_a", "mtfx_chain_b"), ("mtfx_chain_b", "mtfx_chain_c")},
                         "a pozíció-őrző közeli-változat él csak a szomszédok között van; a-c között legfeljebb a paraphrase-heurisztika köt")
        by_pair = {(f["a"]["record"], f["b"]["record"]): f for f in res["findings"] if f["scope"] == "conversation"}
        self.assertEqual(by_pair[("mtfx_chain_a", "mtfx_chain_b")]["status"], "info")
        self.assertEqual(by_pair[("mtfx_chain_b", "mtfx_chain_c")]["status"], "info")
        self.assertEqual(by_pair[("mtfx_chain_a", "mtfx_chain_c")]["type"], "probable_paraphrase_variant")
        self.assertEqual(res["summary"]["largest_group"], 3)

    def test_group_ids_are_reproducible_across_order_and_file_split(self):
        a, b, c = self.make_chain()
        d = relabel(fx(1), "mtfx_solo", "g8104", "p804")
        r1 = dd.run_dedupe(self.load([self.write_convs([a, b, c, d], "o1.jsonl")]), [])
        files = [self.write_convs([d, c], "o2a.jsonl"), self.write_convs([b, a], "o2b.jsonl")]
        r2 = dd.run_dedupe(self.load(files), [])
        m1 = {r["record"]: r["group_id"] for r in r1["records"]}
        m2 = {r["record"]: r["group_id"] for r in r2["records"]}
        self.assertEqual(m1, m2)
        self.assertEqual(m1["mtfx_solo"], "mtg_mtfx_solo")
        self.assertEqual(sorted(r1["groups"]), sorted(r2["groups"]))

    def test_oversized_group_is_reviewed_and_weakest_edges_are_shown(self):
        ids = [f"big_{k}" for k in range(7)]
        edges = [(k, k + 1, "near_conversation", 0.95 - 0.02 * k) for k in range(6)]
        F = dd.Findings()
        groups, _ = dd.build_groups(self.stub_recs(ids), edges, F)
        self.assertEqual(groups["mtg_big_0"]["size"], 7)
        big = [f for f in F.items if f["type"] == "group_too_large"]
        self.assertEqual([f["status"] for f in big], ["review"])
        weakest = big[0]["details"]["weakest_edges"]
        self.assertEqual([e["score"] for e in weakest], sorted(e["score"] for e in weakest))
        self.assertEqual(weakest[0]["score"], round(0.95 - 0.02 * 5, 6))
        ok = dd.Findings()
        dd.build_groups(self.stub_recs(ids[:5]), edges[:4], ok)
        self.assertEqual([f for f in ok.items if f["type"] == "group_too_large"], [], "az 5 tagú csoport még a határon belül van")

    def test_persona_and_declared_groups_link_and_are_limited(self):
        recs = [relabel(fx(n), f"mtfx_pers_{n}", "g8300", "p830") for n in (1, 2, 3, 4, 5)]
        res = self.dedupe(recs)
        self.assertEqual(len({r["group_id"] for r in res["records"]}), 1)
        kinds = self.kinds(res)
        self.assertIn(("persona_reuse_exceeds_limit", "review"), kinds)
        self.assertIn(("declared_group_too_large", "review"), kinds)
        self.assertNotIn(("group_too_large", "review"), kinds, "5 tagú csoport a határon belül van")
        self.assertEqual({e["link"] for e in next(iter(res["groups"].values()))["edges"]}, {"persona", "declared_group"})

    def test_computed_group_merging_several_declared_groups_is_reported(self):
        a, b, c = self.make_chain()
        res = self.dedupe([a, b, c])
        merged = self.of_type(res, "declared_groups_merged")
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["status"], "info")
        self.assertEqual(sorted(merged[0]["details"]["declared_split_groups"]), ["g8101", "g8102", "g8103"])
        self.assertTrue(res["summary"]["variant_share_over_plan"])


def shutil_rmtree(path):
    import shutil
    shutil.rmtree(path, ignore_errors=True)


class ExportComparisonTests(Base):
    def make_export(self, rows):
        clean = os.path.join(self.tmp, "clean")
        os.makedirs(clean, exist_ok=True)
        lst = os.path.join(self.tmp, "excl.txt")
        write_text(lst, "x_excl_0001 | ok | felülvizsgálat\n")
        data = [{"id": "x_a_%04d" % (i + 1), "category": "simple_qa", "instruction": q, "input": inp, "output": out,
                 "tags": ["magyar"], "difficulty": "easy", "quality_notes": "rendben", "source": "teszt"}
                for i, (q, inp, out) in enumerate(rows)]
        data.append({"id": "x_excl_0001", "category": "simple_qa", "instruction": "Kizárt kérdés?", "input": "",
                     "output": "Kizárt válasz, amely nem kerülhet be.", "tags": ["magyar"], "difficulty": "easy",
                     "quality_notes": MARK, "source": "teszt"})
        write_jsonl(os.path.join(clean, "a_clean.jsonl"), data)
        m = te1.run_export(os.path.join(self.tmp, "te1"), input_dir=clean, exclusions_path=lst, run_name="e1")
        return m["run_dir"]

    def test_match_with_existing_export_and_partial_overlaps(self):
        c5 = fx(5)
        t = texts_of(c5)
        rows = [
            (t[0], "", t[1]),                                             # az első fordulóval pontosan azonos példa
            (t[4], "", t[5]),                                              # egy előzményes fordulóval azonos kérdés+válasz
            ("Teljesen más kérdés, ami sehol nem szerepel a beszélgetésben?", "", t[3]),   # csak a válasz egyezik
            ("Mi a főváros Magyarországon, és mióta az?", "", "Budapest a főváros, hosszú története van ennek a városnak."),
        ]
        run_dir = self.make_export(rows)
        conv = self.write_convs([c5], "c5.jsonl")
        rep = dd.run_from_files([conv], self.out, "fixture", te1_export=run_dir, run_name="r1")
        by = {}
        for f in rep["findings"]:
            by.setdefault(f["type"], []).append(f)
        ex = by["sample_exact"]
        self.assertEqual([(f["status"], f["scope"], f["a"].get("turn"), f["b"]["record"]) for f in ex], [("reject", "export", 1, "x_a_0001")])
        self.assertEqual(ex[0]["b"]["source"], "te1_export")
        self.assertIn("file", ex[0]["b"])
        self.assertEqual([f["status"] for f in by["same_qa_different_context"]], ["info"])
        self.assertEqual(by["same_qa_different_context"][0]["a"]["turn"], 5)
        self.assertEqual([f["status"] for f in by["shared_answer_different_question"]], ["info"])
        self.assertEqual(rep["inputs"]["te1_export"]["rows"], 4)
        self.assertEqual(rep["summary"]["blocked_records"], 1)
        self.assertNotIn("x_excl_0001", json.dumps(rep["findings"]), "a kizárt sor nem szerepel az összevetésben")

    def test_near_matches_against_export_are_review_or_reject_by_score(self):
        c5 = fx(5)
        t = texts_of(c5)
        q, ans = t[0], t[1]
        swaps = [("keretösszeged", "költségkereted"), ("mire használnád", "mire szánnád"), ("például", "mondjuk"),
                 ("leginkább", "főként"), ("Ehhez", "Ahhoz"), ("néhány dolgot", "pár dolgot"), ("játékra", "gamingre")]
        seen = {}
        for n in range(len(swaps) + 1):
            out = ans
            for old, new in swaps[:n]:
                out = out.replace(old, new)
            run_dir = self.make_export([(q, "", out)])
            rep = dd.run_from_files([self.write_convs([c5], f"n{n}.jsonl")], os.path.join(self.tmp, f"o{n}"), "fixture",
                                    te1_export=run_dir, run_name="r")
            near = [f for f in rep["findings"] if f["type"] in ("sample_near", "sample_exact") and f["scope"] == "export"]
            for f in near:
                self.assertEqual(f["status"], dd.similarity_status(f["score"], f["type"] == "sample_exact"))
                seen.setdefault(f["status"], []).append(f["score"])
            shutil_rmtree(os.path.join(self.tmp, "clean"))
            shutil_rmtree(os.path.join(self.tmp, "te1"))
        self.assertIn("reject", seen)
        self.assertIn("review", seen, f"nincs 0,90-0,95 közötti eset: {seen}")
        self.assertTrue(all(0.90 < x <= 0.95 for x in seen["review"]), "alap: szigorú '>' szabály")
        self.assertTrue(all(x > 0.95 for x in seen["reject"]))

    def test_tampered_or_failed_te1_export_is_refused(self):
        run_dir = self.make_export([(texts_of(fx(5))[0], "", texts_of(fx(5))[1])])
        conv = self.write_convs([fx(5)], "c.jsonl")
        p = os.path.join(run_dir, te1.EXPORT_FILE)
        write_text(p, read_text(p).replace("Segítenél", "Segítesz"))
        with self.assertRaises(dd.Te1InputError):
            dd.run_from_files([conv], self.out, "fixture", te1_export=run_dir, run_name="bad")
        write_text(os.path.join(run_dir, te1.FAILED_FILE), "hiba\n")
        with self.assertRaises(dd.Te1InputError):
            dd.run_from_files([conv], self.out, "fixture", te1_export=run_dir, run_name="bad2")
        self.assertFalse(os.path.exists(os.path.join(self.out, "bad")))


class BoundaryAndDecisionTests(Base):
    @staticmethod
    def stub_recs():
        out = []
        for owner in (0, 1):
            r = dd.Rec()
            r.id, r.file, r.line, r.group, r.idx = f"stub_{owner}", "f", owner + 1, None, owner
            out.append(r)
        return out

    @staticmethod
    def sample(owner, q, a, ctx=()):
        s = dd.Sample()
        s.kind, s.owner, s.turn = "conv", owner, 1
        s.raw = dd.Unit(q, a, ctx)
        s.msk = s.raw
        s.has_names, s.src = False, None
        return s

    def evaluate(self, sa, sb, inclusive, prefilter=True):
        F = dd.Findings()
        dd.evaluate_sample_pair(sa, sb, "raw", prefilter, inclusive, dd.Stats(), F, self.stub_recs(), [])
        return F

    def test_decision_boundaries_default_is_the_literal_greater_than_and_inclusive_is_the_legacy_ge(self):
        cases = [  # pontszám, pontos egyezés?, alap (szigorú >), --inclusive-boundaries (>=)
            (0.89, False, None, None), (0.90, False, None, "review"), (0.9001, False, "review", "review"),
            (0.9499, False, "review", "review"), (0.95, False, "review", "reject"), (0.9501, False, "reject", "reject"),
            (1.0, True, "reject", "reject"), (0.5, True, "reject", "reject")]
        for score, exact, default, inclusive in cases:
            with self.subTest(score=score, exact=exact):
                self.assertEqual(dd.similarity_status(score, exact), default)
                self.assertEqual(dd.similarity_status(score, exact, False), default)
                self.assertEqual(dd.similarity_status(score, exact, True), inclusive)
        self.assertEqual((dd.REVIEW_MIN, dd.REJECT_MIN), (0.90, 0.95))
        self.assertTrue(dd.above(0.9001, 0.90) and not dd.above(0.90, 0.90) and dd.above(0.90, 0.90, True))

    def test_exact_message_ratios_at_the_boundaries_are_exactly_0_90_and_0_95(self):
        a90, b90 = "a" * 90 + "b" * 10, "a" * 90 + "c" * 10
        a95, b95 = "a" * 95 + "b" * 5, "a" * 95 + "c" * 5
        r90 = dd.ratio_of(dd.match_chars(a90, b90), 100, 100)
        r95 = dd.ratio_of(dd.match_chars(a95, b95), 100, 100)
        self.assertEqual((r90, r95), (0.9, 0.95))
        self.assertTrue(dd.at_boundary(r90) and dd.at_boundary(r95))
        self.assertFalse(dd.at_boundary(0.9002))

    def test_sample_level_boundary_values_default_inclusive_and_prefilter_parity(self):
        long_a = "válasz szöveg " * 8
        # (közös rész, eltérő rész, várt alap, várt inclusive), a kérdés 100 karakteres
        cases = [(90, 10, ("sample_at_boundary", "info", True), ("sample_near", "review", True)),
                 (91, 9, ("sample_near", "review", False), ("sample_near", "review", False)),
                 (95, 5, ("sample_near", "review", True), ("sample_near", "reject", True)),
                 (96, 4, ("sample_near", "reject", False), ("sample_near", "reject", False)),
                 (89, 11, None, None)]
        for same, diff, want_default, want_inclusive in cases:
            sa = self.sample(0, "a" * same + "b" * diff, long_a)
            sb = self.sample(1, "a" * same + "c" * diff, long_a)
            for inclusive, want in ((False, want_default), (True, want_inclusive)):
                outs = []
                for prefilter in (True, False):
                    F = self.evaluate(sa, sb, inclusive, prefilter)
                    outs.append([(f["type"], f["status"], f["at_boundary"]) for f in F.items])
                with self.subTest(ratio=same / 100, inclusive=inclusive):
                    self.assertEqual(outs[0], outs[1], "az előszűrés és a teljes összehasonlítás azonos")
                    self.assertEqual(outs[0], [] if want is None else [want])

    def test_exact_sample_is_reject_at_every_length_and_with_or_without_history(self):
        hist = (("user", "korábbi kérdés szöveg"), ("assistant", "korábbi válasz szöveg"))
        pairs = [("szia", "szia miben segíthetek", (), True), ("a" * 80, "válasz " * 10, (), False),
                 ("k", "v", hist, True), ("b" * 80, "c" * 80, hist, False)]
        for q, a, ctx, short in pairs:
            for inclusive in (False, True):
                F = self.evaluate(self.sample(0, q, a, ctx), self.sample(1, q, a, ctx), inclusive)
                with self.subTest(q=q[:8], history=bool(ctx), inclusive=inclusive):
                    self.assertEqual([(f["type"], f["status"], f["score"], f["details"]["short_text"]) for f in F.items],
                                     [("sample_exact", "reject", 1.0, short)])
        F = self.evaluate(self.sample(0, "szia", "szia miben segíthetek", ()), self.sample(1, "szia", "szia miben segíthetek", hist), False)
        self.assertEqual(F.items, [], "azonos kérdés+válasz eltérő előzménnyel nem azonos minta (és a rövid kérdés nem is jelez)")

    def test_identical_question_and_answer_with_slightly_different_history_is_near_not_exact(self):
        hist_a = (("user", "a" * 88 + "b" * 12), ("assistant", "x" * 40))
        hist_b = (("user", "a" * 88 + "c" * 12), ("assistant", "x" * 40))
        for inclusive in (False, True):
            F = self.evaluate(self.sample(0, "k" * 60, "v" * 60, hist_a), self.sample(1, "k" * 60, "v" * 60, hist_b), inclusive)
            self.assertEqual([(f["type"], f["status"]) for f in F.items], [("sample_near", "review")], f"inclusive={inclusive}")
            self.assertAlmostEqual(F.items[0]["score"], 256 / 280, places=6)
            self.assertLess(F.items[0]["score"], 1.0)

    def test_short_samples_never_auto_reject_by_similarity_and_never_auto_accept(self):
        q95a, q95b = "a" * 19 + "b", "a" * 19 + "c"                    # 0,95 arány, rövid minta
        for inclusive in (False, True):
            F = self.evaluate(self.sample(0, q95a, "ok ok"), self.sample(1, q95b, "ok ok"), inclusive)
            self.assertEqual([(f["type"], f["status"]) for f in F.items], [("sample_near_short", "review")], f"inclusive={inclusive}")
        q90a, q90b = "a" * 9 + "b", "a" * 9 + "c"                       # pontosan 0,90
        F = self.evaluate(self.sample(0, q90a, "ok ok"), self.sample(1, q90b, "ok ok"), False)
        self.assertEqual([(f["type"], f["status"], f["at_boundary"]) for f in F.items], [("sample_at_boundary", "info", True)])
        F = self.evaluate(self.sample(0, q90a, "ok ok"), self.sample(1, q90b, "ok ok"), True)
        self.assertEqual([(f["type"], f["status"]) for f in F.items], [("sample_near_short", "review")])

    def test_conversation_boundary_ratio_stays_a_group_link_only_at_exactly_0_90_by_default(self):
        recs = [PrefilterEquivalenceTests.rec(0, ["a" * 90 + "b" * 10] * 4), PrefilterEquivalenceTests.rec(1, ["a" * 90 + "c" * 10] * 4)]
        for inclusive, want in ((False, ("near_variant", "info")), (True, ("near_conversation", "review"))):
            res = dd.run_dedupe(recs, [], inclusive=inclusive)
            conv = [(f["type"], f["status"], f["score"], f["at_boundary"]) for f in res["findings"] if f["scope"] == "conversation"]
            self.assertEqual(conv, [(want[0], want[1], 0.9, True)], f"inclusive={inclusive}")
            self.assertEqual(res["records"][0]["group_id"], res["records"][1]["group_id"], "a határértéken a csoportosítás megmarad")

class PrefilterEquivalenceTests(unittest.TestCase):
    WORDS = ("torta liszt kenyér vonat jegy telefon töltő akkumulátor szabadság levél menetrend farmer folt tárhely kamera videó "
             "vendég szelet recept sütő élesztő olcsó drága hétvége péntek szombat diák kedvezmény foglalás indulás").split()

    @classmethod
    def rec(cls, idx, texts, group=None, persona=None, masker=None):
        obj = {"id": f"syn_{idx:03d}", "turns": [{"role": "user" if i % 2 == 0 else "assistant", "text": t} for i, t in enumerate(texts)],
               "meta": {"split_group": group, "persona": persona, "depends": []}}
        return dd.make_rec(idx, obj, "syn", 0, idx + 1, "x", masker)

    @classmethod
    def sentence(cls, rng, n):
        return " ".join(rng.choice(cls.WORDS) for _ in range(n)).capitalize() + "."

    @classmethod
    def corpus(cls, seed):
        rng = random.Random(seed)
        bases = [[cls.sentence(rng, rng.randint(5, 14)) for _ in range(rng.choice((4, 6)))] for _ in range(7)]
        recs, k = [], 0
        for b in bases:
            recs.append(cls.rec(k, b)); k += 1
            for noise in (0.0, 0.05, 0.12, 0.25):                         # a küszöbök körüli zajszintek
                v = []
                for t in b:
                    w = t.split()
                    for _ in range(int(len(w) * noise)):
                        w[rng.randrange(len(w))] = rng.choice(cls.WORDS)
                    v.append(" ".join(w))
                recs.append(cls.rec(k, v)); k += 1
        rows = []
        for i, r in enumerate(recs[:20]):
            obj = {"instruction": r.raw[0], "input": "", "output": r.raw[1]}
            rows.append({"id": f"x_{i:04d}", "obj": obj, "source_file": "syn", "source_line": i + 1})
        joined = lambda given: ", ".join(given[:-1]) + " és " + given[-1]
        ans = "Nyolc főre nagyjából 375 gramm liszt kell nekik együtt."
        rows.append({"id": "x_named", "obj": {"instruction": joined(NAMES_A) + " mennyi lisztet vegyenek a tortához?", "input": "", "output": ans},
                     "source_file": "syn", "source_line": 99})
        # a beszélgetés első fordulója az exportsorral névsemlegesítve azonos, nyersen nem (más nevek)
        recs.append(cls.rec(k, [joined(NAMES_B) + " mennyi lisztet vegyenek a tortához?", ans] + [cls.sentence(rng, 9) for _ in range(4)], masker=MASKER)); k += 1
        nh = [cls.sentence(rng, 8) for _ in range(6)]                       # névlistás pár: nyersen < 0,90, névsemlegesítve azonos
        recs.append(cls.rec(k, [t + name_tail(NAMES_A) for t in nh], masker=MASKER)); k += 1
        recs.append(cls.rec(k, [t + name_tail(NAMES_B) for t in nh], masker=MASKER)); k += 1
        b90, b95 = "a" * 90 + "b" * 10, "d" * 95 + "e" * 5                    # külön ábécé: nincs keresztpár
        recs.append(cls.rec(k, [b90] * 4)); k += 1
        recs.append(cls.rec(k, [b90.replace("b", "c")] * 4)); k += 1
        recs.append(cls.rec(k, [b95] * 4)); k += 1
        recs.append(cls.rec(k, [b95.replace("e", "f")] * 4)); k += 1
        return recs, rows

    @staticmethod
    def signature(res):
        return json.dumps([res["findings"], res["groups"], res["records"]], ensure_ascii=False, sort_keys=True)

    @classmethod
    def setUpClass(cls):
        cls.results = {}
        for seed in (1, 2):
            for inclusive in (False, True):
                recs, rows = cls.corpus(seed)
                fast = dd.run_dedupe(recs, rows, prefilter=True, inclusive=inclusive, masker=MASKER)
                recs2, rows2 = cls.corpus(seed)
                full = dd.run_dedupe(recs2, rows2, prefilter=False, inclusive=inclusive, masker=MASKER)
                cls.results[(seed, inclusive)] = (recs, fast, full)

    def test_prefilter_gives_identical_findings_to_full_comparison(self):
        for (seed, inclusive), (recs, fast, full) in self.results.items():
            with self.subTest(seed=seed, inclusive=inclusive):
                self.assertEqual(self.signature(fast), self.signature(full))
                self.assertGreater(len(fast["findings"]), 5, "a zajos másolatok találatokat adnak: a teszt nem üres")
                for level in ("conversation_pairs", "sample_pairs"):
                    c, cf = fast["counters"][level], full["counters"][level]
                    self.assertGreater(c["pruned_length"] + c["pruned_multiset"], 0, level)
                    self.assertLess(c["full_comparisons"], c["pairs_considered"], level)
                    self.assertEqual(cf["pruned_length"] + cf["pruned_multiset"], 0)
                    self.assertEqual(cf["full_comparisons"], cf["pairs_considered"])
                for level in ("conversation_pairs", "sample_pairs"):        # a kiegészítő (névsemleges) menet is fut és a teljes módban minden párt összevet
                    nf = full["counters"]["name_supplementary_pass"][level]
                    self.assertGreater(nf["pairs_considered"], 0, level)
                    if level == "conversation_pairs":
                        n, named = len(recs), sum(1 for r in recs if r.has_names)
                        self.assertGreater(named, 0)
                        self.assertLessEqual(nf["pairs_considered"], n * (n - 1) // 2 - (n - named) * (n - named - 1) // 2,
                                             "csak a nevet tartalmazó beszélgetést érintő párok mennek a névsemleges menetbe")
                    self.assertEqual(nf["full_comparisons"], nf["pairs_considered"])
                    self.assertLess(fast["counters"]["name_supplementary_pass"][level]["full_comparisons"], nf["pairs_considered"])

    def test_boundary_pairs_default_strict_and_inclusive_are_found_by_both_modes(self):
        want = {False: [(0.9, "near_variant", "info"), (0.95, "near_conversation", "review")],
                True: [(0.9, "near_conversation", "review"), (0.95, "near_conversation", "reject")]}
        for (seed, inclusive), (recs, fast, full) in self.results.items():
            for name, res in (("prefilter", fast), ("full", full)):
                with self.subTest(seed=seed, inclusive=inclusive, mode=name):
                    planted = {f"syn_{i:03d}" for i in range(len(recs) - 4, len(recs))}
                    near = [f for f in res["findings"] if f["scope"] == "conversation" and f["at_boundary"]
                            and {f["a"]["record"], f["b"]["record"]} <= planted]
                    self.assertEqual(sorted((round(f["score"], 4), f["type"], f["status"]) for f in near), want[inclusive])

    def test_sample_boundaries_of_the_planted_pairs_follow_the_comparison_mode(self):
        for (seed, inclusive), (recs, fast, full) in self.results.items():
            planted = {f"syn_{i:03d}" for i in range(len(recs) - 4, len(recs))}
            got = sorted({(f["type"], f["status"]) for f in fast["findings"] if f["scope"] == "sample" and f["at_boundary"]
                          and f["type"] in ("sample_near", "sample_at_boundary") and {f["a"]["record"], f["b"]["record"]} <= planted})
            with self.subTest(seed=seed, inclusive=inclusive):
                if inclusive:
                    self.assertEqual(got, [("sample_near", "reject"), ("sample_near", "review")])
                else:
                    self.assertEqual(got, [("sample_at_boundary", "info"), ("sample_near", "review")])

    def test_name_swapped_pair_is_found_identically_by_both_modes(self):
        for (seed, inclusive), (recs, fast, full) in self.results.items():
            for name, res in (("prefilter", fast), ("full", full)):
                with self.subTest(seed=seed, inclusive=inclusive, mode=name):
                    conv = [f for f in res["findings"] if f["type"] == "name_swapped_match"]
                    self.assertEqual([(f["status"], f["score"]) for f in conv], [("review", 1.0)])
                    swapped = [f for f in res["findings"] if f["type"] == "sample_name_swapped"]
                    self.assertEqual(sorted(f["scope"] for f in swapped), ["export", "sample", "sample", "sample"])
                    self.assertEqual({f["status"] for f in swapped}, {"review"})

    def test_inclusive_and_default_runs_differ_only_by_the_boundary_decisions(self):
        recs, strict, _full = self.results[(1, False)]
        _recs, loose, _full2 = self.results[(1, True)]
        self.assertNotEqual(self.signature(strict), self.signature(loose))
        key = lambda res: {(f["type"], f["a"]["record"], f["b"]["record"]): f["status"] for f in res["findings"] if not f["at_boundary"]}
        self.assertEqual(key(strict), key(loose), "a nem határértéken lévő találatok azonosak")

    def test_findings_cover_all_decision_types_so_the_equivalence_is_meaningful(self):
        types = {(f["type"], f["status"]) for _r, fast, _f in self.results.values() for f in fast["findings"]}
        self.assertIn(("near_conversation", "reject"), types)
        self.assertTrue({"review", "info"} & {s for _t, s in types})
        self.assertTrue(any(t == "sample_near" or t == "sample_exact" for t, _s in types))
        self.assertIn(("name_swapped_match", "review"), types)


class InputAndChangeTests(Base):
    def test_invalid_json_and_invalid_records_and_missing_files_are_refused(self):
        p = self.write_convs([fx(1)], "ok.jsonl")
        with open(p, "ab") as f:
            f.write(b"{ez nem json}\n")
        with self.assertRaises(dd.InputFileError) as ctx:
            dd.run_from_files([p], self.out, "fixture", run_name="a")
        self.assertIn("ok.jsonl:2", str(ctx.exception))
        bad = fx(2)
        bad["turns"][2]["text"] = "Írj a valaki@example.com címre, ott elérsz."
        p2 = self.write_convs([fx(1), bad], "bad.jsonl")
        with self.assertRaises(dd.InvalidRecordsError) as ctx:
            dd.run_from_files([p2], self.out, "fixture", run_name="b")
        self.assertIn("content_personal_data_suspected", str(ctx.exception))
        with self.assertRaises(dd.InputFileError):
            dd.run_from_files([os.path.join(self.tmp, "nincs.jsonl")], self.out, "fixture", run_name="c")
        p3 = os.path.join(self.conv_dir, "ures.jsonl")
        write_text(p3, "\n")
        with self.assertRaises(dd.InputFileError):
            dd.run_from_files([p3], self.out, "fixture", run_name="d")
        with self.assertRaises(dd.InvalidRecordsError):          # dataset módban a fixture-ök nem érvényesek
            dd.run_from_files([self.write_convs([fx(1)], "fx.jsonl")], self.out, "dataset", run_name="e")
        self.assertFalse(os.path.exists(self.out), "hiba után nem jön létre futás-mappa")

    def test_input_changed_during_the_run_is_detected(self):
        p = self.write_convs([fx(1), fx(2)], "live.jsonl")
        real = dd.run_dedupe

        def tampering(recs, *a, **kw):
            with open(p, "ab") as f:
                f.write(b"\n")
            return real(recs, *a, **kw)

        with mock.patch.object(dd, "run_dedupe", tampering):
            with self.assertRaises(dd.ChangedInputError):
                dd.run_from_files([p], self.out, "fixture", run_name="x")
        self.assertFalse(os.path.exists(os.path.join(self.out, "x")))

    def test_verify_report_detects_later_changes_to_any_input(self):
        c5 = fx(5)
        export_dir = ExportComparisonTests.make_export(self, [(texts_of(c5)[0], "", texts_of(c5)[1])])
        conv = self.write_convs([fx(1), c5], "v.jsonl")
        rep = dd.run_from_files([conv], self.out, "fixture", te1_export=export_dir, run_name="v1")
        report_path = os.path.join(rep["run_dir"], "dedupe_report.json")
        self.assertEqual(dd.verify_report(report_path), [])
        self.assertEqual(dd._main(["--verify-report", report_path]), 0)
        original = read_bytes(conv)
        with open(conv, "ab") as f:
            f.write(b"\n")
        problems = dd.verify_report(report_path)
        self.assertTrue(any("beszélgetés-fájl" in x for x in problems))
        self.assertEqual(dd._main(["--verify-report", report_path]), dd.EXIT_CHANGED_AFTER)
        with open(conv, "wb") as f:
            f.write(original)
        self.assertEqual(dd.verify_report(report_path), [])
        p = os.path.join(export_dir, te1.EXPORT_FILE)
        write_text(p, read_text(p) + " ")
        self.assertTrue(any("TE-1 export" in x for x in dd.verify_report(report_path)))

    def test_output_path_guards_and_no_overwrite(self):
        p = self.write_convs([fx(1)], "g.jsonl")
        with self.assertRaises(dd.OutputError):
            dd.run_from_files([p], os.path.join(self.conv_dir, "belul"), "fixture", run_name="a")
        for name in ("clean", "raw", "rejected"):
            with self.assertRaises(dd.OutputError):
                dd.run_from_files([p], os.path.join(REPO_ROOT, "data", name, "mt3"), "fixture", run_name="a")
            self.assertFalse(os.path.exists(os.path.join(REPO_ROOT, "data", name, "mt3")))
        dd.run_from_files([p], self.out, "fixture", run_name="once")
        with self.assertRaises(dd.OutputError):
            dd.run_from_files([p], self.out, "fixture", run_name="once")
        with self.assertRaises(dd.OutputError):
            dd.run_from_files([p], self.out, "fixture", run_name="../kifelé")

    def test_source_files_are_never_modified(self):
        p = self.write_convs([fx(1), fx(2)], "ro.jsonl")
        before = hashlib.sha256(read_bytes(p)).hexdigest()
        dd.run_from_files([p], self.out, "fixture", run_name="ro")
        self.assertEqual(before, hashlib.sha256(read_bytes(p)).hexdigest())


class ExceptionsTests(Base):
    CAPABILITY = "Más névcsoportot és más kapcsolatot tanít: a felhasználó nem a húgáról, hanem a barátjáról beszél."
    REASON = "Tervezett változat: a szereplők kapcsolata megváltozik, ezért a feladat eltérő."

    def setUp(self):
        super().setUp()
        a = fx(1)
        self.a = a
        # deklarált változat (közös split_group), nyersen a 0,95 határ fölött: reject
        self.b = swap_names(relabel(fx(1), "mtfx_names_009", a["meta"]["split_group"], a["meta"]["persona"]), {"Réka": "Anna", "Panna": "Lilla"})
        self.conv = self.write_convs([a, self.b], "ex.jsonl")

    def write_exc(self, entries, name="exc.json"):
        p = os.path.join(self.tmp, name)
        write_text(p, json.dumps(entries, ensure_ascii=False))
        return p

    def entry(self, **kw):
        e = {"a": "mtfx_valid_001", "b": "mtfx_names_009", "waive": ["*"], "reason": self.REASON, "capability": self.CAPABILITY,
             "reviewer": "teszt"}
        e.update(kw)
        return e

    def test_reject_level_exception_needs_a_documented_capability_and_the_shared_group_is_no_reason(self):
        base = dd.run_dedupe(self.load([self.conv]), [])
        self.assertIn("reject", {f["status"] for f in base["findings"] if f["scope"] in ("conversation", "sample")})
        for name, e in (("no_capability", {k: v for k, v in self.entry().items() if k != "capability"}),
                        ("short_capability", self.entry(capability="rövid")),
                        ("group_as_reason", {k: v for k, v in self.entry(reason="Ugyanabban a split_group csoportban vannak, ezért változatok.").items()
                                             if k != "capability"})):
            with self.subTest(case=name):
                with self.assertRaises(dd.ExceptionsError) as ctx:
                    dd.run_from_files([self.conv], self.out, "fixture", exceptions_path=self.write_exc([e], name + ".json"), run_name=name)
                self.assertIn("capability", str(ctx.exception))
                self.assertFalse(os.path.exists(os.path.join(self.out, name)))
        rep = dd.run_from_files([self.conv], self.out, "fixture", exceptions_path=self.write_exc([self.entry()]), run_name="ok")
        waived = [f for f in rep["findings"] if f["status"] == "accepted_with_exception"]
        self.assertTrue(waived)
        self.assertIn("reject", {f["status_before_exception"] for f in waived})
        self.assertEqual({f["exception"]["capability"] for f in waived}, {self.CAPABILITY})
        self.assertEqual({f["exception"]["reason"] for f in waived}, {self.REASON})
        self.assertEqual(rep["summary"]["blocked_records"], 0)
        self.assertEqual(rep["inputs"]["exceptions"]["entries"], 1)
        self.assertIn("near_conversation", {x["type"] for x in rep["summary"]["exceptions_applied"]})
        self.assertEqual(rep["records"][0]["group_id"], rep["records"][1]["group_id"], "a kivétel a csoportosítást nem szünteti meg")

    def test_exception_is_explicit_per_type_and_does_not_silence_other_findings(self):
        rep = dd.run_from_files([self.conv], self.out, "fixture", exceptions_path=self.write_exc([self.entry(waive=["near_conversation"])]), run_name="e2")
        left = [x for x in rep["findings"] if x["status"] in ("reject", "review")]
        self.assertTrue(left and all(x["type"] != "near_conversation" for x in left))
        self.assertEqual(rep["summary"]["blocked_records"], 2, "a megnevezetlen minta-szintű találatok továbbra is blokkolnak")

    def test_review_level_exception_needs_only_a_documented_reason(self):
        a, b = VariantTests.make_name_heavy_pair(self)
        conv = self.write_convs([a, b], "nh.jsonl")
        entry = {"a": "mtfx_nh_a", "b": "mtfx_nh_b", "waive": ["*"], "reason": self.REASON}
        rep = dd.run_from_files([conv], self.out, "fixture", exceptions_path=self.write_exc([entry], "nh.json"), run_name="nh")
        waived = [f for f in rep["findings"] if f["status"] == "accepted_with_exception"]
        self.assertEqual({f["type"] for f in waived}, {"name_swapped_match", "sample_name_swapped"})
        self.assertEqual({f["status_before_exception"] for f in waived}, {"review"})
        self.assertEqual({f["exception"]["capability"] for f in waived}, {None})
        self.assertEqual(rep["summary"]["blocked_records"], 0)
        left = [x for x in rep["findings"] if x["status"] in ("reject", "review")]
        self.assertEqual(left, [])

    def test_non_waivable_findings_stay_blocking_even_with_a_capability(self):
        a = fx(1)
        copy_ = relabel(copy.deepcopy(a), "mtfx_copy_004", "g8004", "p804")
        fmt = set_texts(relabel(fx(1), "mtfx_fmt_002", "g8007", "p807"), [t.lower() for t in texts_of(a)])
        res = self.dedupe([a, copy_, fmt])
        known = {"mtfx_valid_001", "mtfx_copy_004", "mtfx_fmt_002"}
        self.assertEqual(dd.NON_WAIVABLE, {"duplicate_id", "exact_conversation", "exact_after_normalization", "sample_exact"})
        for ftype in sorted(dd.NON_WAIVABLE):
            with self.subTest(type=ftype):
                with self.assertRaises(dd.ExceptionsError) as ctx:
                    dd.apply_exceptions(res["findings"], [self.entry(a="mtfx_valid_001", b="mtfx_copy_004", waive=[ftype])], known)
                self.assertIn("nem menthető fel", str(ctx.exception))
        with self.assertRaises(dd.ExceptionsError):                     # a "*" a nem menthető típusokat nem érinti: nincs mit felmenteni
            dd.apply_exceptions(res["findings"], [self.entry(a="mtfx_valid_001", b="mtfx_fmt_002")], known)
        self.assertEqual({f["status"] for f in res["findings"] if f["type"] in dd.NON_WAIVABLE}, {"reject"})

    def test_invalid_stale_or_unwaivable_exceptions_stop_the_run(self):
        good = self.entry(waive=["near_conversation"])
        cases = {
            "short_reason": dict(good, reason="rövid"),
            "unknown_id": dict(good, b="mtfx_nincs"),
            "no_such_finding": dict(good, waive=["messages_reordered"]),
            "star_mixed": dict(good, waive=["*", "near_conversation"]),
            "star_same_record": dict(good, b="mtfx_valid_001", waive=["*"]),
            "non_waivable": dict(good, waive=["duplicate_id"]),
            "non_waivable_sample": dict(good, waive=["sample_exact"]),
            "missing_capability": {k: v for k, v in good.items() if k != "capability"},
            "extra_key": dict(good, extra=1),
            "empty_waive": dict(good, waive=[]),
        }
        for name, e in cases.items():
            with self.subTest(case=name):
                with self.assertRaises(dd.ExceptionsError) as ctx:
                    dd.run_from_files([self.conv], self.out, "fixture", exceptions_path=self.write_exc([e], name + ".json"), run_name=name)
                if name == "unknown_id":
                    self.assertIn("ismeretlen azonosító", str(ctx.exception))
                self.assertFalse(os.path.exists(os.path.join(self.out, name)))
        with self.assertRaises(dd.ExceptionsError):
            dd.run_from_files([self.conv], self.out, "fixture", exceptions_path=self.write_exc({"nem": "lista"}, "obj.json"), run_name="o")
        write_text(os.path.join(self.tmp, "hibas.json"), "{nem json")
        with self.assertRaises(dd.ExceptionsError):
            dd.run_from_files([self.conv], self.out, "fixture", exceptions_path=os.path.join(self.tmp, "hibas.json"), run_name="h")


class ReportTests(Base):
    def test_every_finding_has_the_required_traceable_fields_and_the_run_is_traceable(self):
        a = fx(1)
        b = swap_names(relabel(fx(1), "mtfx_rep_001", "g8401", "p841"), {"Réka": "Anna", "Panna": "Lilla"})
        c = set_texts(relabel(fx(1), "mtfx_rep_002", "g8402", "p842"), PARAPHRASE_001)
        d = relabel(prepend_exchange(fx(5), *GreetingAndContextTests.GREETING), "mtfx_rep_003", "g8403", "p843")
        e = relabel(prepend_exchange(fx(2), *GreetingAndContextTests.GREETING), "mtfx_rep_004", "g8404", "p844")
        conv = self.write_convs([a, b, c, d, e], "rep.jsonl")
        rep = dd.run_from_files([conv], self.out, "fixture", run_name="rep1")
        self.assertGreaterEqual(len(rep["findings"]), 3)
        for f in rep["findings"]:
            self.assertIn("finding_id", f)
            for side in ("a", "b"):
                self.assertIn("record", f[side])
                self.assertIn("source", f[side])
            if f["scope"] in ("sample", "export"):
                self.assertTrue(f["a"].get("turn") is not None or f["a"]["source"] == "te1_export")
            self.assertIn(f["status"], ("reject", "review", "info", "accepted_with_exception"))
            self.assertTrue(f["type"] and f["method"] and f["reason"])
            self.assertIn("score", f)
        conv_scores = [f for f in rep["findings"] if f["scope"] == "conversation" and f["score"] is not None]
        self.assertTrue(conv_scores)
        gids = {r["group_id"] for r in rep["records"]}
        self.assertTrue(all(r["group_id"] for r in rep["records"]))
        self.assertIn(rep["records"][0]["group_id"], rep["groups"])
        self.assertEqual(rep["inputs"]["conversation_files"][0]["sha256"], hashlib.sha256(read_bytes(conv)).hexdigest())
        self.assertEqual(rep["inputs"]["conversation_files"][0]["records"], 5)
        self.assertIn("total", rep["timing_seconds"])
        self.assertGreaterEqual(rep["timing_seconds"]["total"], 0.0)
        self.assertFalse(rep["training_ready"])
        self.assertFalse(rep["content_verified"])
        self.assertEqual(rep["tool_version"], dd.TOOL_VERSION)
        self.assertEqual(rep["tool_sha256"], te1.sha256_file(dd.__file__), "az MT-2 ebből ismeri fel az elavult (más kóddal készült) jelentést")
        self.assertIn("NEM training-ready", rep["disclaimer"])
        self.assertEqual(rep["config"]["decision_rules"]["review_min"], 0.9)
        self.assertEqual(rep["config"]["decision_rules"]["reject_min"], 0.95)
        self.assertEqual(rep["config"]["decision_rules"]["comparison"], ">", "alap: a kézikönyv szó szerinti 'fölött' szabálya")
        self.assertFalse(rep["config"]["decision_rules"]["inclusive_boundaries"])
        self.assertFalse(rep["config"]["declared_split_group_overrides_decision"])
        exp = rep["config"]["experimental"]
        self.assertEqual(exp["short_text_exception"]["min_chars"], 60)
        self.assertEqual(exp["paraphrase_heuristic"]["min_jaccard"], 0.35)
        self.assertTrue(exp["name_masked_signal"]["enabled"])
        self.assertIn("capability", json.dumps(rep["config"]["exceptions_policy"]))
        self.assertEqual(set(rep["config"]["exceptions_policy"]["non_waivable"]),
                         {"duplicate_id", "exact_conversation", "exact_after_normalization", "sample_exact"})
        limits = " ".join(rep["limitations"])
        self.assertIn("hiánya nem bizonyít egyediséget", limits)
        self.assertIn("puszta névcsere nem új képesség", limits)
        self.assertIn("KÍSÉRLETI", limits)
        self.assertIn("kísérleti jelzések", rep["disclaimer"])
        self.assertIn("autojunk=False", rep["config"]["similarity"])
        self.assertTrue(rep["config"]["normalization"]["name_masking"])
        self.assertEqual(sorted(os.listdir(rep["run_dir"])), ["dedupe_report.json", "findings.tsv", "groups.json", "record_status.tsv"])
        self.assertEqual(len(gids), len(rep["groups"]))
        self.assertGreater(len(rep["limitations"]), 3)
        tsv = read_text(os.path.join(rep["run_dir"], "findings.tsv")).splitlines()
        self.assertEqual(len(tsv), 1 + len(rep["findings"]))

    def test_runs_are_deterministic(self):
        recs = [fx(1), swap_names(relabel(fx(1), "mtfx_det", "g8501", "p851"), {"Réka": "Anna", "Panna": "Lilla"}), fx(3)]
        r1 = dd.run_from_files([self.write_convs(recs, "d.jsonl")], self.out, "fixture", run_name="d1")
        r2 = dd.run_from_files([self.write_convs(recs, "d.jsonl")], self.out, "fixture", run_name="d2")
        for key in ("findings", "groups", "records", "summary", "counters"):
            self.assertEqual(json.dumps(r1[key], sort_keys=True), json.dumps(r2[key], sort_keys=True), key)

    def test_records_carry_the_sha256_of_their_source_line_for_the_split_tool(self):
        conv = self.write_convs([fx(1), fx(2), fx(3)], "sha.jsonl")
        rep = dd.run_from_files([conv], self.out, "fixture", run_name="sha")
        lines = [l for l in read_bytes(conv).split(b"\n") if l.strip()]
        self.assertEqual([r["line_sha256"] for r in rep["records"]], [hashlib.sha256(l).hexdigest() for l in lines])
        self.assertEqual([r["line"] for r in rep["records"]], [1, 2, 3])

    def test_inclusive_boundaries_flag_reaches_the_decision_logic_from_run_from_files(self):
        conv = self.write_convs([fx(1), fx(2)], "inc.jsonl")
        seen = []
        real = dd.run_dedupe

        def spy(recs, *a, **kw):
            seen.append(kw.get("inclusive"))
            return real(recs, *a, **kw)

        with mock.patch.object(dd, "run_dedupe", spy):
            dd.run_from_files([conv], self.out, "fixture", run_name="i1")
            dd.run_from_files([conv], self.out, "fixture", run_name="i2", inclusive_boundaries=True)
        self.assertEqual(seen, [False, True])

    def test_progression_is_blocking_only_and_never_deletes(self):
        a = fx(1)
        b = relabel(copy.deepcopy(a), "mtfx_copy_009", "g8502", "p852")
        conv = self.write_convs([a, b], "blk.jsonl")
        before = read_bytes(conv)
        rep = dd.run_from_files([conv], self.out, "fixture", run_name="blk")
        self.assertEqual({r["progression"] for r in rep["records"]}, {"blocked"})
        self.assertEqual(read_bytes(conv), before, "az elutasítás nem forrásadat-törlés")
        self.assertEqual(len([l for l in read_text(conv).splitlines() if l.strip()]), 2)


class CliTests(Base):
    def cli(self, *args):
        env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
        return subprocess.run([sys.executable, TOOL_PATH, *args], capture_output=True, text=True, encoding="utf-8", env=env)

    def test_exit_codes(self):
        clean = self.write_convs([fx(1), fx(2)], "clean.jsonl")
        r = self.cli("--mode", "fixture", "--conversations", clean, "--out-dir", self.out, "--run-name", "c1")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("NEM training-ready", r.stdout)
        dup = self.write_convs([fx(1), relabel(fx(1), "mtfx_copy_010", "g8601", "p861")], "dup.jsonl")
        r = self.cli("--mode", "fixture", "--conversations", dup, "--out-dir", self.out, "--run-name", "c2")
        self.assertEqual(r.returncode, 1)
        self.assertIn("REJECT", r.stdout)
        self.assertEqual(self.cli("--mode", "fixture", "--conversations", os.path.join(self.tmp, "nincs.jsonl"), "--out-dir", self.out).returncode, dd.EXIT_INPUT)
        self.assertEqual(self.cli("--mode", "dataset", "--conversations", clean, "--out-dir", self.out, "--run-name", "c3").returncode, dd.EXIT_INVALID)
        self.assertEqual(self.cli("--mode", "fixture", "--conversations", clean, "--out-dir", self.out, "--run-name", "c1").returncode, dd.EXIT_OUTPUT)
        self.assertEqual(self.cli("--mode", "fixture", "--conversations", clean, "--out-dir", self.out, "--run-name", "c4",
                                  "--te1-export", os.path.join(self.tmp, "nincs")).returncode, dd.EXIT_TE1)
        bad = os.path.join(self.tmp, "kiv.json")
        write_text(bad, "[]x")
        self.assertEqual(self.cli("--mode", "fixture", "--conversations", clean, "--out-dir", self.out, "--run-name", "c5",
                                  "--exceptions", bad).returncode, dd.EXIT_EXCEPTIONS)
        self.assertEqual(self.cli("--mode", "fixture").returncode, 2)
        self.assertEqual(self.cli("--verify-report", os.path.join(self.tmp, "nincs.json")).returncode, dd.EXIT_INPUT)

    def test_optional_switches_are_recorded_in_the_report(self):
        p = self.write_convs([fx(1), fx(2)], "sw.jsonl")
        r = self.cli("--mode", "fixture", "--conversations", p, "--out-dir", self.out, "--run-name", "sw",
                     "--no-prefilter", "--no-name-normalization", "--inclusive-boundaries")
        self.assertEqual(r.returncode, 0, r.stderr)
        rep = json.loads(read_text(os.path.join(self.out, "sw", "dedupe_report.json")))
        self.assertFalse(rep["config"]["prefilter"]["enabled"])
        self.assertFalse(rep["config"]["normalization"]["name_masking"])
        self.assertFalse(rep["config"]["experimental"]["name_masked_signal"]["enabled"])
        self.assertEqual(rep["config"]["decision_rules"]["comparison"], ">=")
        self.assertTrue(rep["config"]["decision_rules"]["inclusive_boundaries"])
        r = self.cli("--mode", "fixture", "--conversations", p, "--out-dir", self.out, "--run-name", "sw2")
        rep2 = json.loads(read_text(os.path.join(self.out, "sw2", "dedupe_report.json")))
        self.assertEqual(rep2["config"]["decision_rules"]["comparison"], ">")
        self.assertTrue(rep2["config"]["experimental"]["name_masked_signal"]["enabled"])

    def test_name_supplementary_signal_through_the_cli_and_its_switch(self):
        a, b = VariantTests.make_name_heavy_pair(self)
        p = self.write_convs([a, b], "nh.jsonl")
        r = self.cli("--mode", "fixture", "--conversations", p, "--out-dir", self.out, "--run-name", "n1")
        self.assertEqual(r.returncode, 1, r.stderr)
        self.assertIn("name_swapped_match", r.stdout)
        self.assertIn("REVIEW", r.stdout)
        r = self.cli("--mode", "fixture", "--conversations", p, "--out-dir", self.out, "--run-name", "n2", "--no-name-normalization")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_verify_report_exit_code_after_change(self):
        p = self.write_convs([fx(1), fx(2)], "vv.jsonl")
        r = self.cli("--mode", "fixture", "--conversations", p, "--out-dir", self.out, "--run-name", "v")
        self.assertEqual(r.returncode, 0)
        rp = os.path.join(self.out, "v", "dedupe_report.json")
        self.assertEqual(self.cli("--verify-report", rp).returncode, 0)
        with open(p, "ab") as f:
            f.write(b"\n")
        r = self.cli("--verify-report", rp)
        self.assertEqual(r.returncode, dd.EXIT_CHANGED_AFTER)
        self.assertIn("MEGVÁLTOZOTT BEMENET", r.stderr)

    def test_thresholds_cannot_be_changed_from_the_command_line(self):
        p = self.write_convs([fx(1)], "th.jsonl")
        for flag in ("--review-min", "--reject-min", "--threshold", "--group-min", "--no-decision", "--handbook-strict"):
            with self.subTest(flag=flag):
                r = self.cli("--mode", "fixture", "--conversations", p, "--out-dir", self.out, flag, "0.99")
                self.assertEqual(r.returncode, 2)
                self.assertIn("unrecognized", r.stderr)
        self.assertFalse(os.path.exists(self.out))


@unittest.skipUnless(os.path.isdir(os.path.join(REPO_ROOT, "data", "clean")), "nincs data/clean")
class RealExportAcceptanceTests(unittest.TestCase):
    """A valódi TE-1 export (4494 példa) mint referencia; a beszélgetések mesterséges tesztadatok."""

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.clean_files = sorted(glob.glob(os.path.join(REPO_ROOT, "data", "clean", "*.jsonl")))
        cls.before = {p: hashlib.sha256(read_bytes(p)).hexdigest() for p in cls.clean_files}
        m = te1.run_export(os.path.join(cls._tmp.name, "te1"), run_name="real1")
        cls.export_dir = m["run_dir"]
        os.makedirs(os.path.join(cls._tmp.name, "convs"))
        cls.conv_path = os.path.join(cls._tmp.name, "convs", "convs.jsonl")
        # egy valódi exportált példa első fordulóként (kérdés+válasz), a MT-1 szűrőin átmenő sor kiválasztásával
        chosen = None
        with open(os.path.join(cls.export_dir, te1.EXPORT_FILE), encoding="utf-8") as f:
            for line in f:
                o = json.loads(line)
                if o["category"] == "simple_qa" and o["input"] == "" and 20 < len(o["instruction"]) < 120 and 60 < len(o["output"]) < 300:
                    probe = set_texts(fx(1), [o["instruction"], o["output"]] + BREAD[2:])
                    probe["meta"]["persona_names"] = ["Bence"]
                    if not [i for i in mt.validate_record(probe, "fixture", BANK) if i.severity == "error"]:
                        chosen = (o, probe)
                        break
        cls.row, cls.planted = chosen
        cls.planted["id"] = "mtfx_real_planted"
        cls.planted["meta"]["split_group"], cls.planted["meta"]["persona"] = "g8701", "p871"
        write_jsonl(cls.conv_path, [fx(n) for n in range(1, 6)] + [cls.planted])
        cls.rep = dd.run_from_files([cls.conv_path], os.path.join(cls._tmp.name, "mt3"), "fixture", te1_export=cls.export_dir, run_name="real")

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_reference_is_the_real_export_and_excludes_the_six_rows(self):
        e = self.rep["inputs"]["te1_export"]
        self.assertEqual((e["rows"], e["rows_excluded_by_te1"]), (4494, 6))
        text = json.dumps(self.rep["findings"], ensure_ascii=False)
        for rid in ("uncertainty_source_request_0220", "uncertainty_source_request_0898"):
            self.assertNotIn(rid, text)
        self.assertEqual(self.rep["counters"]["export_samples"], 4494)

    def test_planted_copy_of_a_real_export_example_is_found_with_source_location(self):
        ex = [f for f in self.rep["findings"] if f["type"] == "sample_exact" and f["scope"] == "export"]
        self.assertEqual(len(ex), 1, [f["type"] for f in self.rep["findings"]])
        f = ex[0]
        self.assertEqual((f["status"], f["a"]["record"], f["a"]["turn"], f["b"]["record"]), ("reject", "mtfx_real_planted", 1, self.row["id"]))
        self.assertIn("clean", f["b"]["file"])
        self.assertGreaterEqual(f["b"]["line"], 1)
        blocked = {r["record"] for r in self.rep["records"] if r["progression"] == "blocked"}
        self.assertEqual(blocked, {"mtfx_real_planted"})

    def test_unmodified_fixtures_alone_match_nothing_in_the_real_export(self):
        clean_conv = os.path.join(self._tmp.name, "convs", "only_fixtures.jsonl")
        write_jsonl(clean_conv, [fx(n) for n in range(1, 6)])
        rep = dd.run_from_files([clean_conv], os.path.join(self._tmp.name, "mt3b"), "fixture", te1_export=self.export_dir, run_name="fixtures_only")
        self.assertEqual([f for f in rep["findings"] if f["status"] in ("reject", "review")], [])
        self.assertEqual(rep["summary"]["blocked_records"], 0)

    def test_real_data_and_export_are_untouched(self):
        self.assertEqual(self.before, {p: hashlib.sha256(read_bytes(p)).hexdigest() for p in self.clean_files})
        for kind in ("raw", "clean", "rejected", "inbox"):
            self.assertEqual(glob.glob(os.path.join(REPO_ROOT, "data", kind, "**", "*multiturn*"), recursive=True), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
