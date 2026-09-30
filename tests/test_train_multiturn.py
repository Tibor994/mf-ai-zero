"""
MF-AI-Zero - MT-5 teszt: src/train_multiturn.py (többfordulós tanító BETÖLTŐ - csak betöltés és száraz futás).

FONTOS: ez a teszt NEM tanít semmit, és a betöltő maga sem tartalmaz tanítási kódágat (nincs `--train`
opció, a `--dry-run` kötelező). Kizárólag mesterséges tesztadatot használ: a `tests/test_multiturn_split.py`
generátorával készült beszélgetéseket egy teljes MT-3 -> MT-2 -> MT-4 csővezetéken keresztül futtatja,
`mtfx_syn_NNNN` azonosítóval, `meta.fixture: true`, `fixture_` előtagú export- és száraz futás-mappákkal;
ez NEM része az 1000 beszélgetéses csomagnak, tanításra nem használható, a valódi datasetet nem érinti.
Valódi többfordulós adaton (mert még nincs) nem futott; a valódi TE-1 exportot csak a beágyazott
csővezeték-lépés (MT-3/MT-2/MT-4) olvassa, ha a teszt kifejezetten kéri.

Célzott esetek: célmaszk illeszkedése a bemenethez és az eltolt célokhoz (context/aktuális kérdés/kitöltés
sosem cél); szótár kizárólag a train/R2 mintákból, UNK/PAD nem bővíti utólag; ismeretlen karakterek
dokumentált kezelése; hosszkorlát fölötti minta visszatartása jelentéssel, nem csonkítás; kötegelés
(egy sor = egy minta, beszélgetések nem folynak össze, rejtett állapot nem öröklődik kötegek/sorok között);
előrefutási (kompatibilitási) próba egy friss, tanítatlan modellel; erőforrás-/hossz-mérés; elavult/sérült/
hiányos export felismerése; a fixture export kizárólag kifejezett tesztmódban fogadható el; kimeneti
mappa-védelem; visszaolvasásos önellenőrzés; parancssor.

Futtatás:
    python -m unittest tests.test_train_multiturn
    python tests/test_train_multiturn.py
"""

import copy
import hashlib
import json
import os
import shutil
import subprocess
import sys
import unittest
from unittest import mock

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(TESTS_DIR, ".."))
TOOLS_DIR = os.path.join(REPO_ROOT, "tools")
SRC_DIR = os.path.join(REPO_ROOT, "src")
sys.path.insert(0, TOOLS_DIR)
sys.path.insert(0, TESTS_DIR)
sys.path.insert(0, SRC_DIR)

import dataset_export_train as te1  # noqa: E402
import multiturn_export as mx  # noqa: E402
import test_multiturn_split as S  # noqa: E402  (a mesterséges beszélgetés-generátor és a csővezeték-segédek)
import config  # noqa: E402
import train_multiturn as mt5  # noqa: E402
from model import CharLSTM  # noqa: E402
import torch  # noqa: E402

TOOL_PATH = os.path.join(SRC_DIR, "train_multiturn.py")


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


# ---------------------------------------------------------------------------
# csővezeték: mesterséges beszélgetések -> MT-3 -> MT-2 -> MT-4 export
# ---------------------------------------------------------------------------

class Pipeline(S.Base):
    def mt4(self, recs, targets=(24, 3, 3), modes=("R2", "R1"), run_name=None, **kw):
        man2, conv, report = self.pipeline(recs, targets=targets, **kw)
        self._n += 1
        man4 = mx.run_export(os.path.join(man2["run_dir"], "split_manifest.json"), self.out, "fixture",
                             modes=modes, run_name=run_name or f"fixture_e{self._n}")
        return man4, man2, conv, report

    def copy_export(self, name):
        dst = os.path.join(self.tmp, "copies", "fixture_" + name)
        shutil.copytree(self.man4["run_dir"], dst)
        return dst

    def copy_mt5(self, name):
        dst = os.path.join(self.tmp, "mt5copies", "fixture_" + name)
        shutil.copytree(self.man5["run_dir"], dst)
        return dst


class SharedPipeline(Pipeline):
    """setUpClass: egy közös mesterséges csővezeték (MT-3 -> MT-2 -> MT-4 -> MT-5 száraz futás); a legtöbb
    teszt ebből olvas (nem módosítja)."""

    @classmethod
    def setUpClass(cls):
        self = cls("write_convs")
        self.setUp()
        cls.base = self
        recs = S.corpus(40, seed=301)
        S.link(recs[0], group="g5001"), S.link(recs[1], group="g5001")
        cls.man4, cls.man2, cls.conv, cls.report = self.mt4(recs, targets=(32, 4, 4), run_name="fixture_shared")
        cls.export_manifest = os.path.join(cls.man4["run_dir"], "export_manifest.json")
        cls.man5 = mt5.run_dry_run(cls.export_manifest, "fixture", self.out, run_name="fixture_shared5")
        cls.run_dir = cls.man5["run_dir"]
        cls.report_path = os.path.join(cls.run_dir, mt5.REPORT_FILE)

    @classmethod
    def tearDownClass(cls):
        cls.base.tearDown()

    def dryrun(self, run_name, **kw):
        kw.setdefault("mode", "fixture")
        mode = kw.pop("mode")
        return mt5.run_dry_run(self.export_manifest, mode, self.base.out, run_name=run_name, **kw)


# ---------------------------------------------------------------------------
# tiszta függvények: célmaszk, kódolás, hossz-statisztika
# ---------------------------------------------------------------------------

class TargetMaskTests(unittest.TestCase):
    def test_mask_covers_exactly_the_target_span_and_nothing_before_or_after(self):
        text = "User: kerdes\nAI: cel"
        start, end = text.index("cel"), len(text)
        mask = mt5.build_target_mask(len(text), start, end)
        self.assertEqual(len(mask), len(text) - 1)
        on = [i for i, v in enumerate(mask) if v]
        predicted_chars = [text[i + 1] for i in on]
        self.assertEqual("".join(predicted_chars), text[start:end])
        # az előzmény/aktuális kérdés (start előtt) és a szöveg végén túli (itt nincs, de az utolsó predikció is a cél)
        self.assertTrue(all(v == 0.0 for v in mask[: start - 1]))

    def test_mask_alignment_matches_the_shifted_input_target_arrays(self):
        vocab = mt5.build_vocab([{"text": "abcABCdefDEF vlaszcl123"}])
        text = "abcABCdefDEF vlaszcl123"
        start, end = 13, len(text)
        ids, _unknown = mt5.encode_text(text, vocab)
        input_ids, target_ids = ids[:-1], ids[1:]
        mask = mt5.build_target_mask(len(text), start, end)
        # bemenet-illeszkedés: a teljes (nem maszkolt) bemenet-tömb visszafejtve pontosan a szöveg utolsó
        # karakter nélküli része (az input mindenhol, nem csak a cél alatt, a saját pozíciójának karaktere)
        self.assertEqual("".join(vocab["itos"][i] for i in input_ids), text[:-1])
        self.assertEqual("".join(vocab["itos"][i] for i in target_ids), text[1:])
        # célilleszkedés: a maszkkal kiválasztott ELTOLT célok pontosan a célválasz-tartomány karakterei
        decoded_target_chars = [vocab["itos"][target_ids[i]] for i, v in enumerate(mask) if v]
        self.assertEqual("".join(decoded_target_chars), text[start:end])

    def test_padding_and_history_never_get_a_target_mask(self):
        sample = {"sample_id": "x#R2#1", "conversation_id": "c", "unit": "u", "split": "train", "mode": "R2",
                  "text": "User: hosszu kerdes szoveg\nAI: valasz"}
        target = {"start": sample["text"].index("AI: ") + 4, "end": len(sample["text"])}
        sample["target"] = target
        vocab = mt5.build_vocab([sample])
        prep, reason = mt5.prepare_sample(sample, vocab, max_chars=1000)
        self.assertIsNone(reason)
        # a padding-gal kiegészített (kötegelt) maszk is csak a cél-tartományban 1,0
        batch = mt5.make_batches([prep, dict(prep, sample_id="y", length=prep["length"] + 5,
                                             input_ids=prep["input_ids"] + [vocab["pad_id"]] * 5,
                                             target_ids=prep["target_ids"] + [vocab["pad_id"]] * 5,
                                             mask=prep["mask"] + [0.0] * 5)], batch_size=2, pad_id=vocab["pad_id"])[0]
        row0_mask = batch["mask"][0].tolist()
        self.assertTrue(all(v == 0.0 for v in row0_mask[len(prep["mask"]):]), "a kitöltés sosem kap célmaszkot")
        self.assertEqual(sum(row0_mask), target["end"] - target["start"])

    def test_verify_mask_alignment_catches_a_shifted_or_wrong_mask(self):
        text = "User: k\nAI: cel12"
        start, end = text.index("cel12"), len(text)
        good = mt5.build_target_mask(len(text), start, end)
        ok, why = mt5.verify_mask_alignment(text, good, start, end)
        self.assertTrue(ok, why)
        shifted = [0.0] + good[:-1]
        ok, why = mt5.verify_mask_alignment(text, shifted, start, end)
        self.assertFalse(ok)
        self.assertIn("nem [target_start,target_end)", why)
        wrong_range = mt5.build_target_mask(len(text), start - 1, end - 1)
        ok, why = mt5.verify_mask_alignment(text, wrong_range, start, end)
        self.assertFalse(ok)

    def test_verify_mask_alignment_flags_a_wrongly_empty_mask_but_accepts_a_correctly_empty_one(self):
        text = "abcdef"
        # nem üres cél (2,4), de teljesen üres maszk: hiba, nem "véletlenül jó"
        ok, why = mt5.verify_mask_alignment(text, [0.0] * (len(text) - 1), 2, 4)
        self.assertFalse(ok)
        self.assertIn("üres maszk", why)
        # üres cél (start == end): az üres maszk itt HELYES (nincs mit jósolni)
        ok2, why2 = mt5.verify_mask_alignment(text, [0.0] * (len(text) - 1), 3, 3)
        self.assertTrue(ok2, why2)
        self.assertIsNone(why2)

    def test_build_target_mask_stays_within_bounds_even_for_a_target_not_at_the_end_of_the_text(self):
        # az MT-4 minden renderelt szövege a célválasszal ér véget (target_end == len(text)); ez a teszt
        # SZÁNDÉKOSAN megsérti ezt a feltevést, hogy a build_target_mask alsó/felső korlátja önmagában (a
        # "target mindig a végén van" véletlen egybeesésétől függetlenül) is helyes legyen
        text = "abcdefghij"                     # 10 karakter
        mask = mt5.build_target_mask(len(text), 3, 6)     # a cél a KÖZEPÉN van, nem a végén
        self.assertEqual(len(mask), len(text) - 1)
        ok, why = mt5.verify_mask_alignment(text, mask, 3, 6)
        self.assertTrue(ok, why)
        self.assertEqual(sum(mask), 3)
        self.assertTrue(all(v == 0.0 for v in mask[6:]), "a cél utáni rész sosem kap maszkot")

    def test_build_target_mask_never_indexes_past_its_own_array_for_an_out_of_range_target(self):
        # védekező eset: ha egy (elvileg már korábban kiszűrt) target_end túlmutatna a szövegen, a
        # függvény ne dobjon IndexError-t, és a maszk hossza maradjon a szöveggel konzisztens
        text = "abcdef"
        mask = mt5.build_target_mask(len(text), 2, len(text) + 50)
        self.assertEqual(len(mask), len(text) - 1)
        self.assertEqual(mask[-1], 1.0)

    def test_prepare_sample_raises_on_a_self_inconsistent_target(self):
        vocab = mt5.build_vocab([{"text": "abcdef"}])
        bad = {"sample_id": "s", "conversation_id": "c", "unit": "u", "split": "train", "mode": "R2",
              "text": "abcdef", "target": {"start": 2, "end": 4}}
        with mock.patch.object(mt5, "build_target_mask", lambda *a, **k: [0.0] * 5):
            with self.assertRaises(mt5.VerificationError):
                mt5.prepare_sample(bad, vocab, max_chars=100)

    def test_prepare_sample_raises_when_verify_mask_alignment_itself_reports_a_problem(self):
        # itt a build_target_mask VALÓDI marad (a maszk összege ténylegesen egyezni fog a célhosszal,
        # tehát a KÉSŐBBI összeg-önellenőrzés önmagában NEM buktatná el ezt a mintát) - kizárólag a
        # verify_mask_alignment mockolt (False) visszatérése alapján kell a `prepare_sample`-nak elállnia
        vocab = mt5.build_vocab([{"text": "abcdef"}])
        sample = {"sample_id": "s", "conversation_id": "c", "unit": "u", "split": "train", "mode": "R2",
                 "text": "abcdef", "target": {"start": 2, "end": 4}}
        with mock.patch.object(mt5, "verify_mask_alignment", lambda *a, **k: (False, "mesterséges hiba")):
            with self.assertRaises(mt5.VerificationError) as ctx:
                mt5.prepare_sample(sample, vocab, max_chars=100)
        self.assertIn("mesterséges hiba", str(ctx.exception))

    def test_prepare_sample_raises_when_the_encoded_arrays_have_mismatched_lengths(self):
        # a verify_mask_alignment-et "átengedjük" (mockolva), hogy KIZÁRÓLAG a hosszegyeztetés-önellenőrzést
        # vizsgáljuk - a build_target_mask ekkor egy rossz (túl rövid) maszkot ad, amit az input/target
        # tömbök hosszához kellene, de nem fog illeszkedni
        vocab = mt5.build_vocab([{"text": "abcdef"}])
        sample = {"sample_id": "s", "conversation_id": "c", "unit": "u", "split": "train", "mode": "R2",
                 "text": "abcdef", "target": {"start": 2, "end": 4}}
        with mock.patch.object(mt5, "verify_mask_alignment", lambda *a, **k: (True, None)), \
                mock.patch.object(mt5, "build_target_mask", lambda *a, **k: [0.0, 1.0]):
            with self.assertRaises(mt5.VerificationError) as ctx:
                mt5.prepare_sample(sample, vocab, max_chars=100)
        self.assertIn("hossza nem egyezik", str(ctx.exception))

    def test_prepare_sample_withholds_a_pathologically_short_text_instead_of_crashing(self):
        # a load_samples elméletileg átengedhet egy 1 karakteres (teljes egészében cél) szöveget (start=0,
        # end=1 érvényes target); ez a bemenet/cél pár szempontjából értelmezhetetlenül rövid - a betöltő
        # ezt is jelentve visszatartja, nem próbálja meg "valahogy" feldolgozni
        vocab = mt5.build_vocab([{"text": "a"}])
        sample = {"sample_id": "s#R2#1", "conversation_id": "c", "unit": "u", "split": "train", "mode": "R2",
                 "text": "a", "target": {"start": 0, "end": 1}}
        prep, reason = mt5.prepare_sample(sample, vocab, max_chars=100)
        self.assertIsNone(prep)
        self.assertIn("túl rövid", reason)

    def test_prepare_sample_raises_when_the_mask_sum_disagrees_with_the_target_length(self):
        vocab = mt5.build_vocab([{"text": "abcdef"}])
        sample = {"sample_id": "s", "conversation_id": "c", "unit": "u", "split": "train", "mode": "R2",
                 "text": "abcdef", "target": {"start": 2, "end": 4}}
        with mock.patch.object(mt5, "verify_mask_alignment", lambda *a, **k: (True, None)), \
                mock.patch.object(mt5, "build_target_mask", lambda *a, **k: [0.0] * 5):
            with self.assertRaises(mt5.VerificationError) as ctx:
                mt5.prepare_sample(sample, vocab, max_chars=100)
        self.assertIn("összege nem", str(ctx.exception))


class VocabAndEncodingTests(unittest.TestCase):
    def test_vocab_is_built_only_from_the_given_samples_text(self):
        vocab = mt5.build_vocab([{"text": "abcab"}, {"text": "xyz"}])
        self.assertEqual(sorted(vocab["stoi"]), ["a", "b", "c", "x", "y", "z"])
        self.assertEqual(vocab["base_vocab_size"], 6)
        self.assertEqual(vocab["unk_id"], 6)
        self.assertEqual(vocab["pad_id"], 7)
        self.assertEqual(vocab["vocab_size"], 8)
        self.assertNotIn(vocab["unk_id"], vocab["itos"])  # az UNK/PAD nem "megfigyelt karakter": nincs itos-bejegyzése

    def test_encode_preserves_character_positions_unlike_the_existing_tokenizer(self):
        vocab = mt5.build_vocab([{"text": "ab"}])
        ids, unknown = mt5.encode_text("azb", vocab)
        self.assertEqual(len(ids), 3, "minden karakter egy id-t kap, az ismeretlen sem esik ki")
        self.assertEqual(ids[1], vocab["unk_id"])
        self.assertEqual(unknown, [1])

    def test_unknown_characters_are_reported_not_added_to_the_vocabulary(self):
        vocab = mt5.build_vocab([{"text": "kutya"}])
        before = dict(vocab["stoi"])
        ids, unknown = mt5.encode_text("kutyamacska", vocab)
        self.assertEqual(vocab["stoi"], before, "a szótár nem bővül a kódolás során")
        self.assertEqual(sorted({"kutyamacska"[i] for i in unknown}), sorted(set("macska") - set("kutya")))


class LengthStatsTests(unittest.TestCase):
    def test_percentile_is_deterministic_and_matches_known_values(self):
        data = list(range(1, 101))
        self.assertEqual(mt5.percentile(data, 0), 1)
        self.assertEqual(mt5.percentile(data, 100), 100)
        self.assertEqual(mt5.percentile(data, 50), 50)
        self.assertIsNone(mt5.percentile([], 50))
        self.assertEqual(mt5.percentile([7], 90), 7)

    def test_length_stats_reports_the_expected_summary(self):
        st = mt5.length_stats([10, 20, 30, 40, 50])
        self.assertEqual((st["count"], st["min"], st["max"], st["mean"], st["median"]), (5, 10, 50, 30.0, 30))
        self.assertEqual(mt5.length_stats([])["count"], 0)

    def test_estimate_batch_bytes_is_a_simple_deterministic_formula(self):
        prepared = [{"length": 10}, {"length": 5}]
        self.assertEqual(mt5.estimate_batch_bytes(prepared), 10 * 20 + 5 * 20)

    def test_over_trained_context_count_excludes_a_sample_exactly_at_the_threshold(self):
        # egy minta PONTOSAN a modell tanított kontextusán (config.seq_length) NEM számít "túl hosszúnak" -
        # csak az azt SZIGORÚAN meghaladó; ez a határeset a valódi (mesterséges) csővezeték-adaton szinte
        # sosem fordul elő véletlenül, ezért itt közvetlenül, kézzel megkonstruálva ellenőrizzük
        kept = [{"length": config.seq_length}, {"length": config.seq_length + 1}, {"length": config.seq_length - 1}]
        self.assertEqual(mt5.over_trained_context_count(kept), 1)
        self.assertEqual(mt5.over_trained_context_count([]), 0)


# ---------------------------------------------------------------------------
# kötegelés: egy sor = egy minta, beszélgetések nem folynak össze, állapot nem öröklődik
# ---------------------------------------------------------------------------

class BatchingIsolationTests(unittest.TestCase):
    def make_prepared(self, sample_id, text, conv_id="c1"):
        vocab = self.vocab
        target = {"start": max(1, len(text) - 3), "end": len(text)}
        s = {"sample_id": sample_id, "conversation_id": conv_id, "unit": "u", "split": "train", "mode": "R2",
            "text": text, "target": target}
        prep, reason = mt5.prepare_sample(s, vocab, max_chars=1000)
        self.assertIsNone(reason)
        return prep

    def setUp(self):
        self.vocab = mt5.build_vocab([{"text": "abcdefghijklmnop ABCDEFGH"}])

    def test_a_batch_row_is_exactly_one_sample_never_a_concatenation(self):
        p1 = self.make_prepared("s1#R2#1", "abcdefgh", "c1")
        p2 = self.make_prepared("s2#R2#1", "abcdefghijklmnop", "c2")
        batch = mt5.make_batches([p1, p2], batch_size=2, pad_id=self.vocab["pad_id"])[0]
        self.assertEqual(batch["input_ids"].shape[0], 2)
        self.assertEqual(batch["sample_ids"], ["s1#R2#1", "s2#R2#1"])
        self.assertEqual(batch["conversation_ids"], ["c1", "c2"])
        # a rövidebb sor a hosszabbig kitöltve, de a valódi tartalma (a saját hosszáig) változatlan
        self.assertEqual(batch["input_ids"][0, : p1["length"]].tolist(), p1["input_ids"])
        self.assertTrue(all(v == self.vocab["pad_id"] for v in batch["input_ids"][0, p1["length"]:].tolist()))

    def test_batches_never_exceed_the_requested_size_and_keep_file_order(self):
        prepared = [self.make_prepared(f"s{i}#R2#1", "abcdefgh" * (i + 1), f"c{i}") for i in range(5)]
        batches = mt5.make_batches(prepared, batch_size=2, pad_id=self.vocab["pad_id"])
        self.assertEqual([len(b["sample_ids"]) for b in batches], [2, 2, 1])
        self.assertEqual([sid for b in batches for sid in b["sample_ids"]], [p["sample_id"] for p in prepared])

    def test_two_rows_in_one_batch_give_the_same_result_as_two_separate_forward_passes(self):
        torch.manual_seed(1234)
        model = mt5.build_probe_model(self.vocab["vocab_size"])
        p1 = self.make_prepared("s1#R2#1", "abcdefghij", "c1")
        p2 = self.make_prepared("s2#R2#1", "klmnop AB", "c2")
        joint = mt5.make_batches([p1, p2], batch_size=2, pad_id=self.vocab["pad_id"])[0]
        r1 = mt5.make_batches([p1], batch_size=1, pad_id=self.vocab["pad_id"])[0]
        r2 = mt5.make_batches([p2], batch_size=1, pad_id=self.vocab["pad_id"])[0]
        model.eval()
        with torch.no_grad():
            logits_joint, _ = model(joint["input_ids"], hidden=None)
            logits_1, _ = model(r1["input_ids"], hidden=None)
            logits_2, _ = model(r2["input_ids"], hidden=None)
        self.assertTrue(torch.allclose(logits_joint[0, : p1["length"]], logits_1[0]), "az 1. sor független a 2. sortól")
        self.assertTrue(torch.allclose(logits_joint[1, : p2["length"]], logits_2[0]), "a 2. sor független az 1. sortól")

    def test_forward_check_never_carries_hidden_state_between_calls(self):
        torch.manual_seed(99)
        model = mt5.build_probe_model(self.vocab["vocab_size"])
        pA = self.make_prepared("a#R2#1", "abcdefgh", "cA")
        pB = self.make_prepared("b#R2#1", "ijklmnop", "cB")
        batchA = mt5.make_batches([pA], batch_size=1, pad_id=self.vocab["pad_id"])[0]
        batchB = mt5.make_batches([pB], batch_size=1, pad_id=self.vocab["pad_id"])[0]
        first = mt5.forward_check(model, batchB, self.vocab["vocab_size"])
        mt5.forward_check(model, batchA, self.vocab["vocab_size"])          # egy "korábbi" hívás közbeékelve
        second = mt5.forward_check(model, batchB, self.vocab["vocab_size"])
        self.assertEqual(first["masked_loss"], second["masked_loss"], "a B köteg eredménye független attól, hogy előtte futott-e az A köteg")

    def test_forward_check_reports_a_runtime_error_instead_of_crashing(self):
        vocab = self.vocab
        p = self.make_prepared("s#R2#1", "abcdefgh", "c1")
        batch = mt5.make_batches([p], batch_size=1, pad_id=vocab["pad_id"])[0]

        class Boom(torch.nn.Module):
            def forward(self, x, hidden=None):
                raise RuntimeError("teszt hiba")

        result = mt5.forward_check(Boom(), batch, vocab["vocab_size"])
        self.assertEqual(result, {"success": False, "error": "teszt hiba"})

    def test_forward_check_computes_loss_only_over_masked_target_tokens(self):
        vocab = self.vocab
        p = self.make_prepared("s#R2#1", "abcdefghijklmnop", "c1")
        batch = mt5.make_batches([p], batch_size=1, pad_id=vocab["pad_id"])[0]
        model = mt5.build_probe_model(vocab["vocab_size"])
        result = mt5.forward_check(model, batch, vocab["vocab_size"])
        self.assertTrue(result["success"])
        self.assertEqual(result["target_tokens"], int(sum(p["mask"])))
        self.assertGreater(result["masked_loss"], 0.0)

    def test_forward_check_loss_is_the_masked_average_not_a_plain_average_over_all_positions(self):
        import torch.nn.functional as F
        vocab = self.vocab
        p = self.make_prepared("s#R2#1", "abcdefghijklmnop", "c1")
        batch = mt5.make_batches([p], batch_size=1, pad_id=vocab["pad_id"])[0]
        torch.manual_seed(7)
        model = mt5.build_probe_model(vocab["vocab_size"])
        model.eval()
        with torch.no_grad():
            logits, _ = model(batch["input_ids"], hidden=None)
            per_token = F.cross_entropy(logits.reshape(-1, vocab["vocab_size"]), batch["target_ids"].reshape(-1), reduction="none")
            mask_flat = batch["mask"].reshape(-1)
            expected_masked = float(((per_token * mask_flat).sum() / mask_flat.sum()).item())
            plain_average = float(per_token.mean().item())
        result = mt5.forward_check(model, batch, vocab["vocab_size"])
        self.assertAlmostEqual(result["masked_loss"], expected_masked, places=5)
        self.assertNotAlmostEqual(result["masked_loss"], plain_average, places=5,
                                  msg="a teszt-eset úgy lett választva, hogy a két érték ténylegesen eltérjen")


# ---------------------------------------------------------------------------
# export betöltés és ellenőrzés: elavult/sérült/hiányos bemenet, fixture-védelem
# ---------------------------------------------------------------------------

class LoadExportValidationTests(Pipeline):
    def setUp(self):
        super().setUp()
        recs = S.corpus(15, seed=311)
        self.man4, self.man2, self.conv, self.report = self.mt4(recs, targets=(12, 2, 1), run_name="fixture_base")
        self.manifest_path = os.path.join(self.man4["run_dir"], "export_manifest.json")

    def assertRefused(self, exc_type, needle=None, **kw):
        with self.assertRaises(exc_type) as ctx:
            mt5.load_export(**kw)
        if needle:
            self.assertIn(needle, str(ctx.exception))
        return ctx.exception

    def test_a_valid_export_loads_cleanly(self):
        m, run_dir, sha256 = mt5.load_export(self.manifest_path, "fixture")
        self.assertEqual(m["tool"], "tools/multiturn_export.py")
        self.assertEqual(run_dir, os.path.dirname(self.manifest_path))
        self.assertEqual(sha256, sha(self.manifest_path))

    def test_missing_or_corrupt_manifest_is_refused(self):
        self.assertRefused(mt5.InputFileError, manifest_path=os.path.join(self.tmp, "nincs.json"), mode="fixture")
        junk = os.path.join(self.tmp, "junk.json")
        cases = {"nem json": "érvényes JSON", "[]": "nem JSON objektum", "{}": "hiányzó kulcsok"}
        for text, needle in cases.items():
            with open(junk, "w", encoding="utf-8") as f:
                f.write(text)
            self.assertRefused(mt5.InvalidExportError, needle, manifest_path=junk, mode="fixture")

    def test_wrong_mode_argument_is_refused(self):
        # a saját, egyértelmű üzenetét kérjük (nem azt, amit a KÉSŐBBI data_kind/fixture-egyeztetés adna: egy
        # ismeretlen mód string ott is elakadna, de más, kevésbé pontos üzenettel - ez a korai ellenőrzés
        # önmagában nem "felesleges", épp ez a teszt bizonyítja, hogy a saját útján buk el)
        self.assertRefused(mt5.RefusedError, "dataset vagy fixture kell legyen", manifest_path=self.manifest_path, mode="valami")

    def test_data_kind_fixture_mismatch_is_refused_in_both_directions(self):
        exc = self.assertRefused(mt5.RefusedError, manifest_path=self.manifest_path, mode="dataset")
        self.assertIn("kizárólag --mode fixture", str(exc))
        exc2 = self.assertRefused(mt5.RefusedError, manifest_path=self.manifest_path, mode="valami_meg_ez_sem")
        self.assertIsInstance(exc2, mt5.RefusedError)

    def test_a_manifest_level_data_kind_forgery_is_still_caught_at_the_sample_level(self):
        # a manifest data_kind/fixture mezőjét meghamisítva a load_export (mode="dataset" mellett) átengedi,
        # de a mintafájlok SOROK szintjén tárolt (a manifesttel most már ellentétes) fixture jelölését a
        # load_samples külön ellenőrzi - a hamisítás így sem marad észrevétlen, csak egy réteggel lejjebb bukik el
        p = self.copy_export("forged")
        mp = os.path.join(p, "export_manifest.json")
        man = read_json(mp)
        man.update(data_kind="dataset", fixture=False)
        write_json(mp, man)
        manifest, run_dir, _s = mt5.load_export(mp, "dataset")
        with self.assertRaises(mt5.InvalidExportError) as ctx:
            mt5.load_samples(manifest, run_dir, "train", "R2")
        self.assertIn("data_kind/fixture", str(ctx.exception))

    def test_a_forged_non_fixture_manifest_refuses_a_fixture_prefixed_run_name(self):
        # a load_export önmagában (lásd test_a_manifest_level_data_kind_forgery_is_still_caught_at_the_sample_level)
        # átengedi a data_kind/fixture mezők meghamisítását mode="dataset" mellett - ez a teszt azt bizonyítja,
        # hogy a run_dry_run STAMP-ellenőrzése ezt FÜGGETLENÜL is elkapja, ha a (hamisított) "valódi" adathoz
        # `fixture` előtagú futásnevet adnánk: ez a valódi MT-5 pipeline-on (ahol minden teszt-beszélgetés
        # meta.fixture=true) szándékosan nem érhető el máshogy, mint egy közvetlenül szerkesztett manifesttel
        p = self.copy_export("forged_prefix")
        mp = os.path.join(p, "export_manifest.json")
        man = read_json(mp)
        man.update(data_kind="dataset", fixture=False)
        write_json(mp, man)
        with self.assertRaises(mt5.RefusedError) as ctx:
            mt5.run_dry_run(mp, "dataset", self.out, run_name="fixture_should_not_be_allowed")
        self.assertIn("nem kezdődhet", str(ctx.exception))
        self.assertFalse(os.path.exists(os.path.join(self.out, "fixture_should_not_be_allowed")))

    def test_wrong_tool_or_version_or_status_is_refused(self):
        for field, value, needle in (("tool", "tools/mas.py", "Nem MT-4"), ("tool_version", "mt3-1.0", "Ismeretlen MT-4"), ("status", "failed", "státusza")):
            with self.subTest(field=field):
                p = self.copy_export(field)
                mp = os.path.join(p, "export_manifest.json")
                man = read_json(mp)
                man[field] = value
                write_json(mp, man)
                self.assertRefused(mt5.StaleExportError, needle, manifest_path=mp, mode="fixture")

    def test_a_status_flag_claiming_readiness_is_refused(self):
        for flag in ("training_ready", "content_verified", "split_approved"):
            with self.subTest(flag=flag):
                p = self.copy_export("flag_" + flag)
                mp = os.path.join(p, "export_manifest.json")
                man = read_json(mp)
                man[flag] = True
                write_json(mp, man)
                self.assertRefused(mt5.StaleExportError, flag, manifest_path=mp, mode="fixture")
                man2 = read_json(mp)
                man2[flag] = False
                man2["statuses"][flag] = True
                write_json(mp, man2)
                self.assertRefused(mt5.StaleExportError, manifest_path=mp, mode="fixture")

    def test_missing_or_changed_output_file_is_refused(self):
        p = self.copy_export("delete")
        os.remove(os.path.join(p, "canonical_train.jsonl"))
        self.assertRefused(mt5.InvalidExportError, "hiányzó fájl", manifest_path=os.path.join(p, "export_manifest.json"), mode="fixture")
        p = self.copy_export("flip")
        with open(os.path.join(p, "canonical_train.jsonl"), "ab") as f:
            f.write(b" ")
        self.assertRefused(mt5.InvalidExportError, "megváltozott fájl", manifest_path=os.path.join(p, "export_manifest.json"), mode="fixture")

    def test_failed_or_partial_leftover_is_refused(self):
        p = self.copy_export("failed")
        with open(os.path.join(p, "FAILED.txt"), "w", encoding="utf-8") as f:
            f.write("hiba\n")
        self.assertRefused(mt5.InvalidExportError, manifest_path=os.path.join(p, "export_manifest.json"), mode="fixture")
        p2 = self.copy_export("partial")
        with open(os.path.join(p2, "export_manifest.json.partial"), "w", encoding="utf-8") as f:
            f.write("{}")
        self.assertRefused(mt5.InvalidExportError, manifest_path=os.path.join(p2, "export_manifest.json"), mode="fixture")

    def test_missing_fixture_marker_file_is_refused(self):
        p = self.copy_export("nomarker")
        mp = os.path.join(p, "export_manifest.json")
        os.remove(os.path.join(p, mx.FIXTURE_MARKER_FILE))
        man = read_json(mp)
        del man["outputs"][mx.FIXTURE_MARKER_FILE]
        write_json(mp, man)
        self.assertRefused(mt5.InvalidExportError, "jelölő", manifest_path=mp, mode="fixture")

    def test_exclusion_check_not_performed_needs_an_explicit_flag(self):
        recs = S.corpus(10, seed=312)
        man2, conv, report = self.pipeline(recs, targets=(8, 1, 1), export_dir=None, allow_no_te1=True, run_name="noexp")
        man4 = mx.run_export(os.path.join(man2["run_dir"], "split_manifest.json"), self.out, "fixture", allow_no_te1=True, run_name="fixture_noexp")
        mp = os.path.join(man4["run_dir"], "export_manifest.json")
        self.assertRefused(mt5.StaleExportError, "kizárás-ellenőrzése", manifest_path=mp, mode="fixture")
        m, run_dir, s = mt5.load_export(mp, "fixture", allow_no_te1_comparison=True)
        self.assertFalse(m["exclusion_guard"]["performed"])

    def test_missing_conversations_list_is_refused(self):
        # a hiányzó kulcs / sérült conversations lista is elavultnak számít
        p = self.copy_export("nolist")
        mp = os.path.join(p, "export_manifest.json")
        man = read_json(mp)
        del man["conversations"]
        write_json(mp, man)
        self.assertRefused(mt5.InvalidExportError, manifest_path=mp, mode="fixture")

    def test_conversations_list_count_disagreeing_with_the_splits_summary_is_refused(self):
        # a `conversations` lista megvan, a kulcsok is megvannak - csak a train rész darabszáma nem egyezik
        # a `splits.train.conversations` összegzéssel (a `conversations` lista egy eleme törölve, a `splits`
        # összegzés érintetlen), így KIZÁRÓLAG ez az ellenőrzés buktathatja el
        p = self.copy_export("countmismatch")
        mp = os.path.join(p, "export_manifest.json")
        man = read_json(mp)
        victim = next(i for i, c in enumerate(man["conversations"]) if c["split"] == "train")
        man["conversations"].pop(victim)
        write_json(mp, man)
        self.assertRefused(mt5.InvalidExportError, "beszélgetés-száma nem egyezik", manifest_path=mp, mode="fixture")

    def test_a_duplicate_conversation_id_within_a_split_is_refused(self):
        # a duplikátumot hozzáadjuk a listához, a `splits.train.conversations` összegzést pedig a listával
        # együtt növeljük, hogy KIZÁRÓLAG az azonosító-egyediség ellenőrzése buktathassa el (a darabszám-
        # egyeztetés magában rendben lenne)
        p = self.copy_export("dupconv")
        mp = os.path.join(p, "export_manifest.json")
        man = read_json(mp)
        victim = next(c for c in man["conversations"] if c["split"] == "train")
        man["conversations"].append(dict(victim))
        man["splits"]["train"]["conversations"] += 1
        write_json(mp, man)
        self.assertRefused(mt5.InvalidExportError, "ismétlődő beszélgetés-azonosító", manifest_path=mp, mode="fixture")

    def test_a_sample_file_missing_from_disk_but_not_listed_in_outputs_is_refused(self):
        # ha egy mintafájl szerepel az `outputs` ellenőrzőösszeg-listában, a load_export már ott elbuktatja
        # a hiányzó fájlt (lásd test_missing_or_changed_output_file_is_refused); itt szándékosan KIHAGYJUK az
        # `outputs`-ból, hogy kizárólag a load_samples SAJÁT fájl-ellenőrzését teszteljük
        p = self.copy_export("filemissing")
        mp = os.path.join(p, "export_manifest.json")
        man = read_json(mp)
        fname = man["splits"]["train"]["samples"]["R2"]["file"]
        del man["outputs"][fname]
        write_json(mp, man)
        os.remove(os.path.join(p, fname))
        manifest, run_dir, _s = mt5.load_export(mp, "fixture")
        with self.assertRaises(mt5.InputFileError):
            mt5.load_samples(manifest, run_dir, "train", "R2")


class SampleFileValidationTests(Pipeline):
    def setUp(self):
        super().setUp()
        recs = S.corpus(15, seed=321)
        self.man4, self.man2, self.conv, self.report = self.mt4(recs, targets=(12, 2, 1), run_name="fixture_samples")
        self.manifest, self.run_dir, _sha = mt5.load_export(os.path.join(self.man4["run_dir"], "export_manifest.json"), "fixture")

    def tamper_and_load(self, name, fn):
        p = self.copy_export(name)
        mp = os.path.join(p, "export_manifest.json")
        # a manifest saját ellenőrzőösszegeit a lecserélt fájlhoz igazítjuk, hogy a load_export átengedje,
        # és a hiba a mintafájl-ellenőrzésnél (load_samples), ne az ellenőrzőösszeg-ellenőrzésnél jelentkezzen
        man = read_json(mp)
        fname = "samples_train_R2.jsonl"
        path = os.path.join(p, fname)
        lines = read_bytes(path).decode("utf-8").split("\n")
        rows = [json.loads(l) for l in lines if l.strip()]
        fn(rows)
        new = "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n"
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(new)
        man["outputs"][fname] = {"sha256": sha(path), "bytes": os.path.getsize(path)}
        write_json(mp, man)
        manifest, run_dir, _s = mt5.load_export(mp, "fixture")
        return manifest, run_dir

    def assertSampleError(self, name, fn, needle):
        manifest, run_dir = self.tamper_and_load(name, fn)
        with self.assertRaises(mt5.InvalidExportError) as ctx:
            mt5.load_samples(manifest, run_dir, "train", "R2")
        self.assertIn(needle, str(ctx.exception))

    def test_wrong_split_or_mode_field_is_refused(self):
        self.assertSampleError("split", lambda rows: rows[0].update(split="test"), "split/mode")
        self.assertSampleError("mode", lambda rows: rows[0].update(mode="R1"), "split/mode")

    def test_wrong_data_kind_or_fixture_flag_is_refused(self):
        self.assertSampleError("kind", lambda rows: rows[0].update(data_kind="dataset"), "data_kind/fixture")
        self.assertSampleError("fix", lambda rows: rows[0].update(fixture=False), "data_kind/fixture")

    def test_unknown_or_cross_split_conversation_id_is_refused(self):
        other = next(c["id"] for c in self.manifest["conversations"] if c["split"] != "train")
        self.assertSampleError("otherid", lambda rows: rows[0].update(conversation_id=other), "ismeretlen vagy más részhez")
        self.assertSampleError("madeupid", lambda rows: rows[0].update(conversation_id="mtfx_syn_9999"), "ismeretlen vagy más részhez")

    def test_bad_or_duplicate_sample_id_is_refused(self):
        self.assertSampleError("badid", lambda rows: rows[0].update(sample_id=rows[0]["sample_id"] + "x"), "hibás vagy ismétlődő")
        self.assertSampleError("dupid", lambda rows: rows.__setitem__(1, dict(rows[1], sample_id=rows[0]["sample_id"])), "hibás vagy ismétlődő")

    def test_invalid_target_range_is_refused(self):
        self.assertSampleError("targetneg", lambda rows: rows[0]["target"].update(start=-1), "érvénytelen target")
        self.assertSampleError("targetorder", lambda rows: rows[0]["target"].update(start=rows[0]["target"]["end"]), "érvénytelen target")
        self.assertSampleError("targetover", lambda rows: rows[0]["target"].update(end=len(rows[0]["text"]) + 10), "érvénytelen target")

    def test_wrong_sample_count_for_a_conversation_is_refused(self):
        # a manifest saját `exchanges` mezőjét torzítjuk (a mintafájlt nem), így pontosan a fordulószám-
        # egyeztetés bukik el, nem a korábbi (sorszám-/azonosító-) ellenőrzések valamelyike
        p = self.copy_export("badcount")
        mp = os.path.join(p, "export_manifest.json")
        man = read_json(mp)
        victim = next(c for c in man["conversations"] if c["split"] == "train")
        victim["exchanges"] += 1
        write_json(mp, man)
        manifest, run_dir, _s = mt5.load_export(mp, "fixture")
        with self.assertRaises(mt5.InvalidExportError) as ctx:
            mt5.load_samples(manifest, run_dir, "train", "R2")
        self.assertIn("fordulószámmal", str(ctx.exception))

    def test_row_count_mismatch_with_the_manifest_is_refused(self):
        p = self.copy_export("extraline")
        mp = os.path.join(p, "export_manifest.json")
        path = os.path.join(p, "samples_train_R2.jsonl")
        with open(path, "a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps({"sample_id": "extra"}, ensure_ascii=False) + "\n")
        man = read_json(mp)
        man["outputs"]["samples_train_R2.jsonl"] = {"sha256": sha(path), "bytes": os.path.getsize(path)}
        write_json(mp, man)
        manifest, run_dir, _s = mt5.load_export(mp, "fixture")
        with self.assertRaises(mt5.InvalidExportError) as ctx:
            mt5.load_samples(manifest, run_dir, "train", "R2")
        self.assertIn("sorainak száma", str(ctx.exception))

    def test_a_missing_render_mode_is_reported_clearly(self):
        with self.assertRaises(mt5.InvalidExportError) as ctx:
            mt5.load_samples(self.manifest, self.run_dir, "train", "R3")
        self.assertIn("R3", str(ctx.exception))


# ---------------------------------------------------------------------------
# hosszkorlát: nem csendes csonkítás, hanem jelentett visszatartás
# ---------------------------------------------------------------------------

class OversizeAndWithholdTests(SharedPipeline):
    def test_a_generous_default_limit_withholds_nothing_in_the_shared_pipeline(self):
        self.assertEqual(self.man5["counts"]["withheld_oversized_total"], 0)
        self.assertEqual(self.man5["warnings"], [])

    def test_a_small_limit_withholds_the_longer_samples_with_a_reason_not_a_silent_truncation(self):
        # a tényleges hosszokat a közös exportból olvassuk, hogy a vágási határ a generátortól függetlenül a
        # "néhány visszatartva, a többi megtartva" esetet adja
        manifest, run_dir, _s = mt5.load_export(self.export_manifest, "fixture")
        all_lengths = sorted(len(r["text"]) for s in mt5.SPLITS for md in ("R2", "R1") for r in mt5.load_samples(manifest, run_dir, s, md))
        cutoff = all_lengths[len(all_lengths) // 2]
        self.assertGreater(cutoff, 0)
        rep = self.dryrun("fixture_smalllimit", max_chars=cutoff)
        self.assertGreater(rep["counts"]["withheld_oversized_total"], 0)
        self.assertLess(rep["counts"]["withheld_oversized_total"], sum(rep["splits"][s][md]["kept"] + rep["splits"][s][md]["withheld_oversized"]
                                                                        for s in mt5.SPLITS for md in rep["config"]["modes"]))
        self.assertTrue(any("max-chars" in w for w in rep["warnings"]))
        for s in mt5.SPLITS:
            for md in rep["config"]["modes"]:
                for w in rep["splits"][s][md]["withheld_reasons"]:
                    self.assertIn("túl hosszú", w["reason"])
                    self.assertGreater(w["char_length"], cutoff)
        tsv = read_bytes(os.path.join(rep["run_dir"], mt5.LENGTHS_FILE)).decode("utf-8").splitlines()
        withheld_rows = [l for l in tsv[1:] if l.split("\t")[5] == "0"]
        self.assertEqual(len(withheld_rows), rep["counts"]["withheld_oversized_total"])

    def test_unknown_character_warning_is_emitted_when_some_sample_has_a_character_outside_the_train_vocabulary(self):
        # a train/R2-ból épített szótár SOSEM tartalmazhat "ismeretlen" karaktert saját magára nézve, ezért
        # az ismeretlen-karakter figyelmeztetést csak úgy lehet mesterségesen, de valósághűen kiváltani, ha a
        # build_vocab eredményéből egy, a szövegekben ténylegesen előforduló karaktert utólag eltávolítunk
        real_build_vocab = mt5.build_vocab

        def shrink(samples_list):
            v = real_build_vocab(samples_list)
            removed = v["itos"][0]
            v["stoi"] = {k: val for k, val in v["stoi"].items() if k != removed}
            return v

        with mock.patch.object(mt5, "build_vocab", side_effect=shrink):
            rep = self.dryrun("fixture_unkwarn")
        self.assertGreater(rep["counts"]["unknown_char_occurrences_total"], 0)
        self.assertTrue(any("ismeretlen" in w for w in rep["warnings"]))

    def test_forward_pass_failure_warning_is_emitted_and_counted_when_the_probe_model_cannot_run(self):
        class FailingModel:
            def eval(self):
                pass

            def __call__(self, *a, **k):
                raise RuntimeError("mesterséges kompatibilitási hiba")

        with mock.patch.object(mt5, "build_probe_model", lambda *a, **k: FailingModel()):
            rep = self.dryrun("fixture_fwdfail")
        self.assertGreater(rep["counts"]["forward_pass_failures_total"], 0)
        self.assertTrue(any("köteg előrefutása" in w for w in rep["warnings"]))

    def test_withheld_and_kept_never_overlap_and_together_cover_every_sample(self):
        rep = self.dryrun("fixture_coverage", max_chars=200)
        manifest, run_dir, _s = mt5.load_export(self.export_manifest, "fixture")
        for s in mt5.SPLITS:
            for md in rep["config"]["modes"]:
                total = len(mt5.load_samples(manifest, run_dir, s, md))
                self.assertEqual(rep["splits"][s][md]["kept"] + rep["splits"][s][md]["withheld_oversized"], total)


# ---------------------------------------------------------------------------
# erőforrás-/kompatibilitási jelentés
# ---------------------------------------------------------------------------

class ReportContentTests(SharedPipeline):
    def test_vocab_matches_a_direct_recount_from_the_train_R2_samples(self):
        manifest, run_dir, _s = mt5.load_export(self.export_manifest, "fixture")
        train_r2 = mt5.load_samples(manifest, run_dir, "train", "R2")
        want = sorted({ch for r in train_r2 for ch in r["text"]})
        self.assertEqual(self.man5["vocab"]["base_vocab_size"], len(want))

    def test_train_r2_never_has_unknown_characters_by_construction(self):
        self.assertEqual(self.man5["splits"]["train"]["R2"]["unknown_chars_total_occurrences"], 0)

    def test_counts_and_length_stats_match_an_independent_recount_from_the_tsv(self):
        rows = read_bytes(os.path.join(self.run_dir, mt5.LENGTHS_FILE)).decode("utf-8").splitlines()[1:]
        by_key = {}
        for line in rows:
            split, mode, _sid, _cid, length, kept, _reason, _unk = line.split("\t")
            by_key.setdefault((split, mode), {"kept": [], "withheld": []})
            (by_key[(split, mode)]["kept"] if kept == "1" else by_key[(split, mode)]["withheld"]).append(int(length))
        for s in mt5.SPLITS:
            for md in self.man5["config"]["modes"]:
                info = self.man5["splits"][s][md]
                got = by_key.get((s, md), {"kept": [], "withheld": []})
                self.assertEqual(info["kept"], len(got["kept"]))
                self.assertEqual(info["withheld_oversized"], len(got["withheld"]))
                self.assertEqual(info["length_stats_kept_chars"]["count"], len(got["kept"]))

    def test_compatibility_percentage_is_computed_against_config_seq_length(self):
        for s in mt5.SPLITS:
            for md in self.man5["config"]["modes"]:
                info = self.man5["splits"][s][md]
                manifest, run_dir, _s2 = mt5.load_export(self.export_manifest, "fixture")
                rows = mt5.load_samples(manifest, run_dir, s, md)
                over = sum(1 for r in rows if len(r["text"]) - 1 > config.seq_length)
                self.assertEqual(info["samples_over_trained_context_chars"], over)
                if info["kept"]:
                    self.assertAlmostEqual(info["samples_over_trained_context_pct"], round(100.0 * over / info["kept"], 1), places=1)

    def test_forward_pass_ran_once_per_batch_and_all_succeeded_on_the_probe_model(self):
        for s in mt5.SPLITS:
            for md in self.man5["config"]["modes"]:
                info = self.man5["splits"][s][md]
                self.assertEqual(info["forward_pass_successes"], info["batches"])
                self.assertEqual(info["forward_pass_failures"], [])

    def test_resource_and_timing_fields_are_present_and_non_negative(self):
        t = self.man5["timing_seconds"]
        for key in ("load_seconds",):
            self.assertGreaterEqual(t[key], 0.0)
        for bucket in ("encode_seconds", "batch_seconds", "forward_seconds"):
            self.assertTrue(t[bucket])
            self.assertTrue(all(v >= 0.0 for v in t[bucket].values()))
        for s in mt5.SPLITS:
            for md in self.man5["config"]["modes"]:
                self.assertGreaterEqual(self.man5["splits"][s][md]["estimated_encoded_bytes"], 0)

    def test_repeated_runs_are_deterministic_including_the_probe_models_loss(self):
        r1 = self.dryrun("fixture_det1")
        r2 = self.dryrun("fixture_det2")
        drop = ("created_utc", "run_dir", "outputs", "timing_seconds")  # az időmérés értelemszerűen fut-specifikus, nem determinisztikus
        d1 = {k: v for k, v in r1.items() if k not in drop}
        d2 = {k: v for k, v in r2.items() if k not in drop}
        self.assertEqual(json.dumps(d1, sort_keys=True), json.dumps(d2, sort_keys=True))

    def test_statuses_are_taken_from_the_export_unchanged_and_never_set_true(self):
        for flag in ("training_ready", "content_verified", "split_approved"):
            self.assertIs(self.man5[flag], False)
            self.assertIs(self.man5["statuses_from_export"][flag], False)
        self.assertIn("NEM tanít", self.man5["disclaimer"])
        self.assertGreater(len(self.man5["limitations"]), 3)
        self.assertEqual(self.man5["config"]["primary_mode"], "R2")
        self.assertIn("R3", self.man5["config"]["unsupported_modes"])


# ---------------------------------------------------------------------------
# renderelési mód, tesztadat-védelem, kimeneti mappa
# ---------------------------------------------------------------------------

class ModeAndOutputTests(SharedPipeline):
    def test_r3_and_unknown_and_empty_or_duplicate_mode_lists_are_refused(self):
        for modes, needle in ((("R3",), "R3"), (("R9",), "Ismeretlen"), ((), "üres"), (("R2", "R2"), "ismétlődő"), (("R1",), "Az elsődleges")):
            with self.subTest(modes=modes):
                with self.assertRaises(mt5.RefusedError) as ctx:
                    self.dryrun("fixture_badmodes", modes=modes)
                if needle:
                    self.assertIn(needle, str(ctx.exception))
                self.assertFalse(os.path.exists(os.path.join(self.base.out, "fixture_badmodes")))

    def test_real_data_mode_refuses_a_fixture_export_and_a_dataset_named_run_folder_is_required(self):
        with self.assertRaises(mt5.RefusedError):
            self.dryrun("mt5_should_not_happen", mode="dataset")
        self.assertFalse(os.path.exists(os.path.join(self.base.out, "mt5_should_not_happen")))
        with self.assertRaises(mt5.RefusedError):
            self.dryrun("mt5_realnamed")                                  # fixture adat, de nem fixture_ előtagú mappa
        self.assertFalse(os.path.exists(os.path.join(self.base.out, "mt5_realnamed")))

    def test_output_paths_are_guarded_and_never_overwrite(self):
        # MT-5 egyetlen közvetlen bemenete az MT-4 export (a beszélgetés-/MT-3-fájlokat nem olvassa közvetlenül,
        # ezért csak az export saját mappája ellen véd - ez szándékosan szűkebb, mint az MT-4 többmappás védelme)
        with self.assertRaises(mt5.OutputError):
            mt5.run_dry_run(self.export_manifest, "fixture", os.path.join(self.man4["run_dir"], "belul"), run_name="fixture_belul")
        for name in ("clean", "raw", "rejected", "inbox"):
            with self.assertRaises(mt5.OutputError):
                mt5.run_dry_run(self.export_manifest, "fixture", os.path.join(REPO_ROOT, "data", name, "mt5"), run_name="fixture_x")
            self.assertFalse(os.path.exists(os.path.join(REPO_ROOT, "data", name, "mt5")))
        with self.assertRaises(mt5.OutputError):
            self.dryrun("fixture_shared5")                                # már létezik (setUpClass hozta létre)
        with self.assertRaises(mt5.OutputError):
            self.dryrun("fixture_../kifelé")

    def test_upstream_export_files_are_never_modified(self):
        before = {p: sha(os.path.join(self.man4["run_dir"], p)) for p in self.man4["outputs"]}
        self.dryrun("fixture_untouched_check")
        after = {p: sha(os.path.join(self.man4["run_dir"], p)) for p in self.man4["outputs"]}
        self.assertEqual(before, after)

    def test_a_single_mode_run_only_processes_that_mode(self):
        rep = self.dryrun("fixture_r2only", modes=("R2",))
        self.assertEqual(rep["config"]["modes"], ["R2"])
        self.assertIsNone(rep["config"]["secondary_mode"])
        self.assertEqual(sorted(os.listdir(rep["run_dir"])), sorted([mt5.REPORT_FILE, mt5.LENGTHS_FILE]))
        lines = read_bytes(os.path.join(rep["run_dir"], mt5.LENGTHS_FILE)).decode("utf-8").splitlines()
        self.assertFalse(any(l.split("\t")[1] == "R1" for l in lines[1:]))

    def test_vocab_is_built_from_the_primary_r2_samples_even_when_r2_is_not_the_last_listed_mode(self):
        # a `--modes` alapértelmezett sorrendje (R2, R1) miatt "az utolsó felsorolt mód" ÉS "az elsődleges
        # (R2) mód" ÉPPEN ELTÉR egymástól - ez a teszt közvetlenül azt figyeli meg, MELYIK minták kerülnek
        # a build_vocab hívásába (a mode mezőjük alapján), nem csak a végeredmény szótár méretét (ami R1/R2
        # azonos karakterkészlete miatt véletlenül egyezhetne akkor is, ha rossz módból épülne)
        captured = {}
        real_build_vocab = mt5.build_vocab

        def spy(samples_list):
            captured["samples"] = samples_list
            return real_build_vocab(samples_list)

        with mock.patch.object(mt5, "build_vocab", side_effect=spy):
            self.dryrun("fixture_vocabmode")
        self.assertTrue(captured["samples"], "a build_vocab-ot meg kellett hívni")
        self.assertTrue(all(r["mode"] == "R2" for r in captured["samples"]))


# ---------------------------------------------------------------------------
# a bemenet a futás közben megváltozik; visszaolvasásos önellenőrzés
# ---------------------------------------------------------------------------

class ChangedDuringRunAndVerifyTests(SharedPipeline):
    def test_input_changed_during_the_run_is_detected(self):
        target = os.path.join(self.man4["run_dir"], "canonical_train.jsonl")
        original = read_bytes(target)
        real = mt5.forward_check

        def tampering(*a, **kw):
            with open(target, "ab") as f:
                f.write(b" ")
            return real(*a, **kw)

        try:
            with mock.patch.object(mt5, "forward_check", tampering):
                with self.assertRaises(mt5.InvalidExportError):
                    self.dryrun("fixture_during")
        finally:
            with open(target, "wb") as f:
                f.write(original)
        self.assertFalse(os.path.exists(os.path.join(self.base.out, "fixture_during")))

    def test_a_pristine_report_verifies_clean(self):
        self.assertEqual(mt5.verify_dry_run_report(self.report_path), [])
        self.assertEqual(mt5._main(["--verify-report", self.report_path]), 0)

    def test_changed_status_flag_in_the_report_is_detected(self):
        p = self.copy_mt5("statusflag")
        rp = os.path.join(p, mt5.REPORT_FILE)
        man = read_json(rp)
        man["training_ready"] = True
        write_json(rp, man)
        problems = mt5.verify_dry_run_report(rp)
        self.assertTrue(any("training_ready" in x for x in problems))

    def test_changed_output_file_in_the_report_is_detected(self):
        p = self.copy_mt5("changedtsv")
        with open(os.path.join(p, mt5.LENGTHS_FILE), "ab") as f:
            f.write(b"\n")
        problems = mt5.verify_dry_run_report(os.path.join(p, mt5.REPORT_FILE))
        self.assertTrue(any("megváltozott" in x for x in problems))

    def test_counts_that_disagree_with_the_tsv_are_detected(self):
        p = self.copy_mt5("countmismatch")
        rp = os.path.join(p, mt5.REPORT_FILE)
        man = read_json(rp)
        man["splits"]["train"]["R2"]["kept"] += 1
        write_json(rp, man)
        problems = mt5.verify_dry_run_report(rp)
        self.assertTrue(any("kept-száma" in x for x in problems))

    def test_withheld_count_disagreeing_with_the_tsv_is_detected(self):
        # KÜLÖN a kept-számtól: a withheld_oversized mezőt hamisítjuk, a kept-et érintetlenül hagyva, hogy
        # kizárólag a withheld-önellenőrzés buktassa el, ne a (már máshol tesztelt) kept-ellenőrzés
        p = self.copy_mt5("withheldmismatch")
        rp = os.path.join(p, mt5.REPORT_FILE)
        man = read_json(rp)
        man["splits"]["train"]["R2"]["withheld_oversized"] += 1
        write_json(rp, man)
        problems = mt5.verify_dry_run_report(rp)
        self.assertTrue(any("withheld-száma" in x for x in problems))

    def test_a_missing_output_file_is_detected_distinctly_from_a_changed_one(self):
        p = self.copy_mt5("missingfile")
        os.remove(os.path.join(p, mt5.LENGTHS_FILE))
        problems = mt5.verify_dry_run_report(os.path.join(p, mt5.REPORT_FILE))
        self.assertTrue(any("hiányzó kimeneti fájl" in x for x in problems))
        self.assertFalse(any("megváltozott kimeneti fájl" in x for x in problems))

    def test_verification_failure_during_the_run_leaves_a_failed_marker_and_no_final_report(self):
        with mock.patch.object(mt5, "verify_dry_run_report", lambda *a, **k: ["mesterséges hiba"]):
            with self.assertRaises(mt5.VerificationError):
                self.dryrun("fixture_failverify")
        run = os.path.join(self.base.out, "fixture_failverify")
        self.assertTrue(os.path.isfile(os.path.join(run, "FAILED.txt")))
        self.assertFalse(os.path.exists(os.path.join(run, mt5.REPORT_FILE)))


# ---------------------------------------------------------------------------
# parancssor
# ---------------------------------------------------------------------------

class CliTests(SharedPipeline):
    def cli(self, *args):
        env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
        return subprocess.run([sys.executable, TOOL_PATH, *args], capture_output=True, text=True, encoding="utf-8", env=env)

    def test_missing_dry_run_flag_is_refused_without_touching_the_output_dir(self):
        r = self.cli("--export-manifest", self.export_manifest, "--mode", "fixture", "--out-dir", self.base.out, "--run-name", "fixture_nodry")
        self.assertEqual(r.returncode, mt5.EXIT_REFUSED)
        self.assertIn("--dry-run", r.stderr)
        self.assertFalse(os.path.exists(os.path.join(self.base.out, "fixture_nodry")))

    def test_exit_codes_through_a_real_process(self):
        r = self.cli("--export-manifest", self.export_manifest, "--mode", "fixture", "--out-dir", self.base.out, "--dry-run", "--run-name", "fixture_cli")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("NEM tanít", r.stdout)
        self.assertIn("train/R2", r.stdout)
        r2 = self.cli("--export-manifest", self.export_manifest, "--mode", "fixture", "--out-dir", self.base.out, "--dry-run", "--run-name", "fixture_cli")
        self.assertEqual(r2.returncode, mt5.EXIT_OUTPUT)
        self.assertEqual(self.cli("--export-manifest", os.path.join(self.tmp, "nincs.json"), "--mode", "fixture", "--out-dir", self.base.out,
                                  "--dry-run").returncode, mt5.EXIT_INPUT)
        self.assertEqual(self.cli("--mode", "fixture").returncode, 2)
        p = os.path.join(self.base.out, "fixture_cli", mt5.REPORT_FILE)
        self.assertEqual(self.cli("--verify-report", p).returncode, 0)

    def test_cli_returns_the_attention_exit_code_when_the_report_has_warnings(self):
        # a megosztott csővezetéken az alapértelmezett --max-chars mellett NINCS figyelmeztetés (lásd
        # test_exit_codes_through_a_real_process: sikeres futás -> kilépési kód 0) - ez a teszt szándékosan
        # nagyon kicsi --max-chars értékkel legalább egy visszatartás-figyelmeztetést kényszerít ki, hogy az
        # ATTENTION kilépési kódot (nem a "nincs figyelmeztetés" véletlen egybeesését 0-val) ellenőrizhessük
        r = self.cli("--export-manifest", self.export_manifest, "--mode", "fixture", "--out-dir", self.base.out,
                     "--dry-run", "--run-name", "fixture_cliattn", "--max-chars", "5")
        self.assertEqual(r.returncode, mt5.EXIT_ATTENTION, r.stdout + r.stderr)
        self.assertIn("FIGYELEM", r.stdout)

    def test_verify_report_exit_code_after_tampering_through_the_cli(self):
        r = self.cli("--export-manifest", self.export_manifest, "--mode", "fixture", "--out-dir", self.base.out, "--dry-run", "--run-name", "fixture_cli2")
        self.assertEqual(r.returncode, 0)
        p = os.path.join(self.base.out, "fixture_cli2", mt5.LENGTHS_FILE)
        with open(p, "ab") as f:
            f.write(b"\n")
        rp = os.path.join(self.base.out, "fixture_cli2", mt5.REPORT_FILE)
        r2 = self.cli("--verify-report", rp)
        self.assertEqual(r2.returncode, mt5.EXIT_VERIFY)
        self.assertIn("HIBA", r2.stderr)


# ---------------------------------------------------------------------------
# a v0.7 lánc és a webapp/backend/memory érintetlensége
# ---------------------------------------------------------------------------

class ExistingChainUntouchedTests(unittest.TestCase):
    def test_train_chat_and_model_and_memory_source_files_are_unmodified_by_this_module(self):
        import ast
        tree = ast.parse(open(mt5.__file__, encoding="utf-8").read())
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(n.name for n in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
        self.assertNotIn("train_chat", imported)
        self.assertNotIn("chat", imported)
        self.assertNotIn("guard", imported)
        self.assertNotIn("memory", imported)
        self.assertIn("model", imported)          # a CharLSTM osztályt megosztja, csak olvassa
        self.assertIn("config", imported)

    def test_train_multiturn_has_no_training_loop_no_optimizer_and_no_checkpoint_saving(self):
        # AST-alapú (nem szöveges) keresés: a docstring PRÓZÁJA szándékosan említi ezeket a fogalmakat (hogy
        # elmagyarázza a hiányukat), egy nyers szöveges `in` keresés ezért hamis pozitívot adna; a tényleges
        # KÓD (Call/Attribute csomópontok) viszont nem tartalmazhatja őket.
        import ast
        tree = ast.parse(open(mt5.__file__, encoding="utf-8").read())
        forbidden = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr in ("backward", "step"):
                forbidden.append(node.attr)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                    and node.func.attr == "save" and isinstance(node.func.value, ast.Name) and node.func.value.id == "torch":
                forbidden.append("torch.save(...)")
        self.assertEqual(forbidden, [], f"tiltott kód-mintázat találva: {forbidden} (nincs tanítási kódág)")
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(n.name for n in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
        self.assertFalse(any("optim" in m for m in imported), imported)


if __name__ == "__main__":
    unittest.main(verbosity=2)
