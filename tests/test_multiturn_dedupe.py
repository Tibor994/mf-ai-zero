"""
MF-AI-Zero - MT-3 teszt: tools/multiturn_dedupe.py (többfordulós duplikáció-ellenőrzés és csoportosítás).

FONTOS: kizárólag mesterséges tesztadatot használ (tests/fixtures/multiturn/ fixture-ök átalakított másolatai,
`mtfx_` azonosítóval, fixture móddal, ideiglenes mappákban); ez NEM része az 1000 beszélgetéses csomagnak, és
a valódi datasettet nem érinti. A valós adatos rész (RealExportAcceptanceTests) a TE-1 exportot csak OLVASSA.
A teszt nem tanít semmit.

Célzott esetek: pontos másolat; ismétlődő azonosító; névcserés és átfogalmazott változat; közös köszönés eltérő
feladattal; azonos kérdés eltérő előzménnyel; felcserélt szerepek és üzenetsorrend; láncolt csoportképzés;
meglévő (TE-1) exporttal való egyezés; hibás és időközben megváltozott bemenet; határértékek (0,90 / 0,95);
az előszűrés egyezése a teljes összehasonlítással; kivételek; jelentés-mezők; parancssor.

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
    def test_name_swapped_copy_is_exact_after_normalization(self):
        a = fx(1)
        b = swap_names(relabel(fx(1), "mtfx_names_001", "g8002", "p802"), {"Réka": "Anna", "Panna": "Lilla"})
        self.assertNotEqual(texts_of(a), texts_of(b))
        res = self.dedupe([a, b])
        f = self.of_type(res, "exact_after_normalization")
        self.assertEqual([(x["status"], x["score"]) for x in f], [("reject", 1.0)])
        self.assertEqual(self.of_type(res, "exact_conversation"), [])
        self.assertEqual(res["records"][0]["group_id"], res["records"][1]["group_id"])

    def test_name_swap_without_name_normalization_is_still_caught_by_similarity(self):
        a = fx(1)
        b = swap_names(relabel(fx(1), "mtfx_names_002", "g8002", "p802"), {"Réka": "Anna", "Panna": "Lilla"})
        loaded = self.load([self.write_convs([a, b])])
        raw = dd.load_conversation_files([self.write_convs([a, b], "raw.jsonl")], "fixture", BANK, None)[0]
        res = dd.run_dedupe(raw, [])
        f = self.of_type(res, "near_conversation")
        self.assertEqual(len(f), 1)
        self.assertGreaterEqual(f[0]["score"], 0.95)
        self.assertEqual(f[0]["status"], "reject")
        self.assertLess(f[0]["score"], 1.0)
        self.assertEqual(len(loaded), 2)

    def test_declared_variant_is_only_reviewed_never_silently_accepted(self):
        a = fx(1)
        b = swap_names(relabel(fx(1), "mtfx_names_003", a["meta"]["split_group"], a["meta"]["persona"]), {"Réka": "Anna", "Panna": "Lilla"})
        res = self.dedupe([a, b])
        f = self.of_type(res, "exact_after_normalization")
        self.assertEqual([x["status"] for x in f], ["review"])
        self.assertIn("deklarált változat", f[0]["reason"])
        self.assertEqual(self.status_of(res, "mtfx_names_003")["progression"], "blocked")
        samples = [f for f in res["findings"] if f["type"] in ("sample_exact", "sample_near")]
        self.assertTrue(samples)
        self.assertEqual({f["status"] for f in samples}, {"review"}, "deklarált változatnál a minta-találat is csak review")

    def test_declared_variant_above_reject_threshold_is_review_but_undeclared_is_reject(self):
        names = {"Réka": "Anna", "Panna": "Lilla"}
        for declared, want_conv, want_sample in ((False, "reject", "reject"), (True, "review", "review")):
            with self.subTest(declared=declared):
                a = fx(1)
                group = a["meta"]["split_group"] if declared else "g8005"
                b = swap_names(relabel(fx(1), "mtfx_names_010", group, a["meta"]["persona"] if declared else "p805"), names)
                raw = dd.load_conversation_files([self.write_convs([a, b], f"nm{declared}.jsonl")], "fixture", BANK, None)[0]   # névsemlegesítés nélkül
                res = dd.run_dedupe(raw, [])
                near = self.of_type(res, "near_conversation")
                self.assertEqual([(f["status"], f["details"]["declared_variant"]) for f in near], [(want_conv, declared)])
                self.assertGreaterEqual(near[0]["score"], dd.REJECT_MIN)
                self.assertEqual(("deklarált változat" in near[0]["reason"]), declared)
                sample_status = {f["status"] for f in res["findings"] if f["type"] in ("sample_exact", "sample_near")}
                if declared:
                    self.assertEqual(sample_status, {"review"}, res["summary"]["findings_by_type_status"])
                else:
                    self.assertIn("reject", sample_status, "deklarálatlan változatnál a 0,95 fölötti minta reject")
                    self.assertTrue(sample_status <= {"reject", "review"})
                self.tearDown()
                self.setUp()

    def test_paraphrase_is_review_grouped_and_shows_the_char_threshold_mismatch(self):
        a = fx(1)
        b = set_texts(relabel(fx(1), "mtfx_para_001", "g8004", "p804"), PARAPHRASE_001)
        res = self.dedupe([a, b])
        f = self.of_type(res, "probable_paraphrase_variant")
        self.assertEqual([x["status"] for x in f], ["review"])
        self.assertTrue(f[0]["details"]["heuristic"])
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

    def test_shared_greeting_with_different_tasks_is_not_a_duplicate_conversation(self):
        a = prepend_exchange(relabel(fx(1), "mtfx_greet_a", "g8010", "p810"), *self.GREETING)
        b = prepend_exchange(relabel(fx(5), "mtfx_greet_b", "g8011", "p811"), *self.GREETING)
        res = self.dedupe([a, b])
        conv_level = [f for f in res["findings"] if f["scope"] == "conversation"]
        self.assertEqual(conv_level, [], "közös köszönés önmagában nem tesz duplikálttá egy beszélgetést")
        trivial = self.of_type(res, "sample_exact_trivial")
        self.assertEqual([(f["status"], f["a"]["turn"], f["b"]["turn"]) for f in trivial], [("review", 1, 1)])
        self.assertIn("triviális", trivial[0]["reason"])
        self.assertEqual({r["conversation_decision"] for r in res["records"]}, {"no_conversation_level_block"})
        self.assertEqual(len({r["group_id"] for r in res["records"]}), 2, "a köszönés nem csoportosít")

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
                self.assertEqual(f["status"], dd.similarity_status(f["score"], f["type"] == "sample_exact", False))
                seen.setdefault(f["status"], []).append(round(f["score"], 3))
            shutil_rmtree(os.path.join(self.tmp, "clean"))
            shutil_rmtree(os.path.join(self.tmp, "te1"))
        self.assertIn("reject", seen)
        self.assertIn("review", seen, f"nincs 0,90-0,95 közötti eset: {seen}")
        self.assertTrue(all(0.90 <= x < 0.95 for x in seen["review"]))
        self.assertTrue(all(x >= 0.95 for x in seen["reject"]))

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
    def test_decision_boundaries_and_handbook_strict_variant(self):
        cases = [(0.89, False, None, None), (0.90, False, "review", None), (0.9001, False, "review", "review"),
                 (0.9499, False, "review", "review"), (0.95, False, "reject", "review"), (0.9501, False, "reject", "reject"),
                 (1.0, True, "reject", "reject"), (0.5, True, "reject", "reject")]
        for score, exact, ge_status, strict_status in cases:
            with self.subTest(score=score):
                self.assertEqual(dd.similarity_status(score, exact, False), ge_status)
                self.assertEqual(dd.similarity_status(score, exact, True), strict_status)

    def test_exact_message_ratios_at_the_boundaries_are_exactly_0_90_and_0_95(self):
        a90, b90 = "a" * 90 + "b" * 10, "a" * 90 + "c" * 10
        a95, b95 = "a" * 95 + "b" * 5, "a" * 95 + "c" * 5
        r90 = dd.ratio_of(dd.match_chars(a90, b90), 100, 100)
        r95 = dd.ratio_of(dd.match_chars(a95, b95), 100, 100)
        self.assertEqual((r90, r95), (0.9, 0.95))
        self.assertTrue(dd.at_boundary(r90) and dd.at_boundary(r95))
        self.assertFalse(dd.at_boundary(0.9002))

    def _sample(self, owner, q, a, kind="conv"):
        s = dd.Sample()
        s.kind, s.owner, s.turn = kind, owner, 1
        s.q, s.a, s.ctx = q, a, ()
        s.qlen, s.alen = len(q), len(a)
        s.qvec, s.avec = dd.char_vec(q), dd.char_vec(a)
        s.src = None
        return s

    def test_sample_level_boundaries_are_applied_with_and_without_strict_and_flagged(self):
        stub = []
        for owner in (0, 1):
            r = dd.Rec()
            r.id, r.file, r.line, r.group = f"stub_{owner}", "f", owner + 1, None
            r.idx = owner
            stub.append(r)
        base_a = "a" * 90 + "b" * 10
        long_a = "válasz szöveg " * 8
        for var, expect_ge, expect_strict in (("c" * 10, "review", None),):
            sa = self._sample(0, base_a, long_a)
            sb = self._sample(1, "a" * 90 + var, long_a)
            F = dd.Findings()
            dd.evaluate_sample_pair(sa, sb, True, False, dd.Stats(), F, stub, [])
            self.assertEqual([(f["type"], f["status"], f["at_boundary"]) for f in F.items], [("sample_near", expect_ge, True)])
            F = dd.Findings()
            dd.evaluate_sample_pair(sa, sb, True, True, dd.Stats(), F, stub, [])
            self.assertEqual([f["type"] for f in F.items], [] if expect_strict is None else ["sample_near"])
        sa = self._sample(0, "a" * 95 + "b" * 5, long_a)
        sb = self._sample(1, "a" * 95 + "c" * 5, long_a)
        F = dd.Findings()
        dd.evaluate_sample_pair(sa, sb, True, False, dd.Stats(), F, stub, [])
        self.assertEqual([(f["status"], f["at_boundary"]) for f in F.items], [("reject", True)])
        F = dd.Findings()
        dd.evaluate_sample_pair(sa, sb, True, True, dd.Stats(), F, stub, [])
        self.assertEqual([f["status"] for f in F.items], ["review"])

    def test_short_texts_are_not_decided_by_similarity(self):
        stub = []
        for owner in (0, 1):
            r = dd.Rec()
            r.id, r.file, r.line, r.group, r.idx = f"s{owner}", "f", 1, None, owner
            stub.append(r)
        sa, sb = self._sample(0, "hány nap van egy hétben", "hét nap"), self._sample(1, "hány nap van egy évben", "365 nap")
        F = dd.Findings()
        dd.evaluate_sample_pair(sa, sb, True, False, dd.Stats(), F, stub, [])
        self.assertEqual(F.items, [], "a rövid, nem pontosan azonos minta hasonlósága nem dönt (0,9 fölötti a q-arány)")
        self.assertGreaterEqual(dd.ratio_of(dd.match_chars(sa.q, sb.q), sa.qlen, sb.qlen), 0.9)


class PrefilterEquivalenceTests(unittest.TestCase):
    WORDS = ("torta liszt kenyér vonat jegy telefon töltő akkumulátor szabadság levél menetrend farmer folt tárhely kamera videó "
             "vendég szelet recept sütő élesztő olcsó drága hétvége péntek szombat diák kedvezmény foglalás indulás").split()

    @classmethod
    def rec(cls, idx, texts, group=None, persona=None):
        obj = {"id": f"syn_{idx:03d}", "turns": [{"role": "user" if i % 2 == 0 else "assistant", "text": t} for i, t in enumerate(texts)],
               "meta": {"split_group": group, "persona": persona, "depends": []}}
        return dd.make_rec(idx, obj, "syn", 0, idx + 1, "x", None)

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
        b90, b95 = "a" * 90 + "b" * 10, "d" * 95 + "e" * 5                    # külön ábécé: nincs keresztpár
        recs.append(cls.rec(k, [b90] * 4)); k += 1
        recs.append(cls.rec(k, [b90.replace("b", "c")] * 4)); k += 1
        recs.append(cls.rec(k, [b95] * 4)); k += 1
        recs.append(cls.rec(k, [b95.replace("e", "f")] * 4)); k += 1
        rows = []
        for i, r in enumerate(recs[:20]):
            obj = {"instruction": r.raw[0], "input": "", "output": r.raw[1]}
            rows.append({"id": f"x_{i:04d}", "obj": obj, "source_file": "syn", "source_line": i + 1})
        return recs, rows

    @staticmethod
    def signature(res):
        return json.dumps([res["findings"], res["groups"], res["records"]], ensure_ascii=False, sort_keys=True)

    @classmethod
    def setUpClass(cls):
        cls.results = {}
        for seed in (1, 2):
            recs, rows = cls.corpus(seed)
            fast = dd.run_dedupe(recs, rows, prefilter=True)
            recs2, rows2 = cls.corpus(seed)
            full = dd.run_dedupe(recs2, rows2, prefilter=False)
            cls.results[seed] = (recs, fast, full)

    def test_prefilter_gives_identical_findings_to_full_comparison(self):
        for seed, (recs, fast, full) in self.results.items():
            with self.subTest(seed=seed):
                self.assertEqual(self.signature(fast), self.signature(full))
                self.assertGreater(len(fast["findings"]), 5, "a zajos másolatok találatokat adnak: a teszt nem üres")
                for level in ("conversation_pairs", "sample_pairs"):
                    c, cf = fast["counters"][level], full["counters"][level]
                    self.assertGreater(c["pruned_length"] + c["pruned_multiset"], 0, level)
                    self.assertLess(c["full_comparisons"], c["pairs_considered"], level)
                    self.assertEqual(cf["pruned_length"] + cf["pruned_multiset"], 0)
                    self.assertEqual(cf["full_comparisons"], cf["pairs_considered"])

    def test_boundary_pairs_are_found_by_both_modes(self):
        for seed, (recs, fast, full) in self.results.items():
            for name, res in (("prefilter", fast), ("full", full)):
                with self.subTest(seed=seed, mode=name):
                    planted = {f"syn_{i:03d}" for i in range(len(recs) - 4, len(recs))}
                    near = [f for f in res["findings"] if f["type"] == "near_conversation" and f["at_boundary"]
                            and {f["a"]["record"], f["b"]["record"]} <= planted]
                    self.assertEqual(sorted(round(f["score"], 4) for f in near), [0.9, 0.95])
                    self.assertEqual(sorted(f["status"] for f in near), ["reject", "review"])

    def test_handbook_strict_applies_to_conversation_level_boundaries(self):
        recs, rows = self.corpus(1)
        planted = {f"syn_{i:03d}" for i in range(len(recs) - 4, len(recs))}
        for prefilter in (True, False):
            loose = dd.run_dedupe(recs, rows, prefilter=prefilter, strict=False)
            strict = dd.run_dedupe(recs, rows, prefilter=prefilter, strict=True)
            pick = lambda res: sorted((round(f["score"], 4), f["status"]) for f in res["findings"]
                                      if f["type"] == "near_conversation" and f["at_boundary"] and {f["a"]["record"], f["b"]["record"]} <= planted)
            self.assertEqual(pick(loose), [(0.9, "review"), (0.95, "reject")])
            self.assertEqual(pick(strict), [(0.95, "review")], "szó szerinti '>' : a 0,90 nem, a 0,95 csak review")
            self.assertTrue(strict["findings"] != loose["findings"])

    def test_findings_cover_all_decision_types_so_the_equivalence_is_meaningful(self):
        types = {(f["type"], f["status"]) for _r, fast, _f in self.results.values() for f in fast["findings"]}
        self.assertIn(("near_conversation", "reject"), types)
        self.assertTrue({"review", "info"} & {s for _t, s in types})
        self.assertTrue(any(t == "sample_near" or t == "sample_exact" for t, _s in types))


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
    def setUp(self):
        super().setUp()
        a = fx(1)
        self.a = a
        self.b = swap_names(relabel(fx(1), "mtfx_names_009", a["meta"]["split_group"], a["meta"]["persona"]), {"Réka": "Anna", "Panna": "Lilla"})
        self.conv = self.write_convs([a, self.b], "ex.jsonl")

    def write_exc(self, entries, name="exc.json"):
        p = os.path.join(self.tmp, name)
        write_text(p, json.dumps(entries, ensure_ascii=False))
        return p

    def test_documented_exception_waives_a_declared_variant_review(self):
        entry = {"a": "mtfx_valid_001", "b": "mtfx_names_009", "waive": ["*"],
                 "reason": "Tervezett névcserés változat: más névtárból vett név tanulása a cél.", "reviewer": "teszt"}
        rep = dd.run_from_files([self.conv], self.out, "fixture", exceptions_path=self.write_exc([entry]), run_name="e1")
        f = [x for x in rep["findings"] if x["type"] == "exact_after_normalization"]
        self.assertEqual([(x["status"], x["status_before_exception"]) for x in f], [("accepted_with_exception", "review")])
        self.assertIn("Tervezett névcserés", f[0]["exception"]["reason"])
        self.assertEqual(rep["summary"]["blocked_records"], 0)
        self.assertEqual(rep["inputs"]["exceptions"]["entries"], 1)
        self.assertIn("exact_after_normalization", {x["type"] for x in rep["summary"]["exceptions_applied"]})
        self.assertGreater(len(rep["summary"]["exceptions_applied"]), 1, "a pár minta-szintű találatai is felmentésre kerültek")
        self.assertEqual(rep["records"][0]["group_id"], rep["records"][1]["group_id"], "a kivétel a csoportosítást nem szünteti meg")

    def test_exception_is_explicit_per_type_and_does_not_silence_other_findings(self):
        entry = {"a": "mtfx_valid_001", "b": "mtfx_names_009", "waive": ["exact_after_normalization"],
                 "reason": "Tervezett névcserés változat: más névtárból vett név tanulása a cél."}
        rep = dd.run_from_files([self.conv], self.out, "fixture", exceptions_path=self.write_exc([entry]), run_name="e2")
        left = [x for x in rep["findings"] if x["status"] in ("reject", "review")]
        self.assertTrue(left and all(x["type"] != "exact_after_normalization" for x in left))
        self.assertEqual(rep["summary"]["blocked_records"], 2, "a megnevezetlen minta-szintű találatok továbbra is blokkolnak")

    def test_invalid_stale_or_unwaivable_exceptions_stop_the_run(self):
        good = {"a": "mtfx_valid_001", "b": "mtfx_names_009", "waive": ["exact_after_normalization"],
                "reason": "Elég hosszú, konkrét indoklás a változatról."}
        cases = {
            "short_reason": dict(good, reason="rövid"),
            "unknown_id": dict(good, b="mtfx_nincs"),
            "no_such_finding": dict(good, waive=["near_conversation"]),
            "star_mixed": dict(good, waive=["*", "exact_after_normalization"]),
            "star_non_waivable_pair": dict(good, a="mtfx_valid_001", b="mtfx_valid_001"),
            "non_waivable": dict(good, waive=["duplicate_id"]),
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
        self.assertIn("NEM training-ready", rep["disclaimer"])
        self.assertEqual(rep["config"]["decision_rules"]["review_min"], 0.9)
        self.assertEqual(rep["config"]["decision_rules"]["reject_min"], 0.95)
        self.assertEqual(rep["config"]["decision_rules"]["comparison"], ">=")
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
                     "--no-prefilter", "--no-name-normalization", "--handbook-strict")
        self.assertEqual(r.returncode, 0, r.stderr)
        rep = json.loads(read_text(os.path.join(self.out, "sw", "dedupe_report.json")))
        self.assertFalse(rep["config"]["prefilter"]["enabled"])
        self.assertFalse(rep["config"]["normalization"]["name_masking"])
        self.assertEqual(rep["config"]["decision_rules"]["comparison"], ">")
        self.assertTrue(rep["config"]["decision_rules"]["handbook_strict"])

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
        for flag in ("--review-min", "--reject-min", "--threshold", "--group-min", "--no-decision"):
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
