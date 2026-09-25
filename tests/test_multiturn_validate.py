"""
MF-AI-Zero - MT-0/MT-1 teszt: tools/multiturn_validate.py, tools/multiturn_name_bank.json,
tests/fixtures/multiturn/valid_conversations.jsonl.

FONTOS: mesterséges, kicsi tesztadatot használ (id: `mtfx_...`, meta.fixture: true); ez NEM az 1000
beszélgetéses csomag része, a valódi csomag adatai még nem léteznek. A teszt nem tanít semmit.

Mit bizonyít:
  - a fixture-ök (MT-0) érvényesek fixture módban, és dataset módban elutasítottak (nem keveredhetnek
    a valódi csomagba);
  - minden szerkezeti és tartalmi szabálynak van legalább egy elbukó tesztje (egy változtatás = egy szabály);
  - MINDEN üzenet vizsgált: a hiba vagy személyes adat kizárólag egy KÖZBENSŐ üzenetben is
    elbukik az új ellenőrzőn, miközben a RÉGI validátor a rekordot (és a fájlt) átengedi;
  - a jelentés külön mutatja a régi-validátor-kompatibilis és a turns-validált állapotot, és a
    beszélgetés-, üzenet- és mintaszámot külön számolja;
  - a névtár és a névfelismerés (jóváhagyott/tiltott/deklarált/teljes név) viselkedése.
Nem bizonyít: tartalmi helyességet, training-ready állapotot.

Futtatás:
    python -m unittest tests.test_multiturn_validate
    python tests/test_multiturn_validate.py
"""

import copy
import glob
import json
import os
import subprocess
import sys
import tempfile
import unittest

TOOLS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools")
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, TOOLS_DIR)

import dataset_validate as legacy  # noqa: E402
import multiturn_validate as mt  # noqa: E402

TOOL_PATH = os.path.join(TOOLS_DIR, "multiturn_validate.py")
FIXTURE_FILE = os.path.join(REPO_ROOT, "tests", "fixtures", "multiturn", "valid_conversations.jsonl")
BANK = mt.load_name_bank()


def read_text(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def load_fixtures():
    return [json.loads(l) for l in read_text(FIXTURE_FILE).splitlines() if l.strip()]


def errors(rec, mode="fixture"):
    return [i for i in mt.validate_record(rec, mode, BANK) if i.severity == "error"]


def warnings(rec, mode="fixture"):
    return [i for i in mt.validate_record(rec, mode, BANK) if i.severity == "warning"]


def codes(issues):
    return {i.code for i in issues}


def fixture(n=2):
    return copy.deepcopy(load_fixtures()[n - 1])


def set_text(rec, idx, text):
    rec["turns"][idx]["text"] = text
    if idx == 0:
        rec["instruction"] = text
    if idx == len(rec["turns"]) - 1:
        rec["output"] = text
    return rec


class FixtureTests(unittest.TestCase):
    def test_fixtures_are_valid_in_fixture_mode_without_any_issue(self):
        recs = load_fixtures()
        self.assertEqual(len(recs), 5)
        for r in recs:
            issues = mt.validate_record(r, "fixture", BANK)
            self.assertEqual([i for i in issues], [], r["id"])

    def test_fixtures_are_rejected_in_dataset_mode_so_they_cannot_join_the_package(self):
        for r in load_fixtures():
            c = codes(errors(r, "dataset"))
            self.assertIn("bad_id", c)
            self.assertIn("meta_fixture_mismatch", c)

    def test_fixture_ids_never_match_the_dataset_pattern_and_are_marked(self):
        for r in load_fixtures():
            self.assertTrue(mt.ID_FIXTURE_RE.match(r["id"]))
            self.assertFalse(mt.ID_DATASET_RE.match(r["id"]))
            self.assertTrue(r["meta"]["fixture"])
            self.assertEqual(r["source"], "test_fixture")

    def test_no_multiturn_dataset_files_exist_and_fixtures_live_outside_data(self):
        self.assertTrue(os.path.abspath(FIXTURE_FILE).startswith(os.path.join(REPO_ROOT, "tests")))
        for kind in ("raw", "clean", "rejected"):
            self.assertEqual(glob.glob(os.path.join(REPO_ROOT, "data", kind, "*multiturn*")), [],
                             "az 1000 beszélgetéses csomag adatai még nem léteznek")

    def test_dataset_mode_accepts_a_dataset_shaped_record(self):
        r = fixture(1)
        r["id"] = "multiturn_0001"
        r["meta"].pop("fixture")
        r["source"] = "claude_generated"
        self.assertEqual(mt.validate_record(r, "dataset", BANK), [])
        self.assertIn("meta_fixture_mismatch", codes(errors(r, "fixture")))
        self.assertIn("bad_id", codes(errors(r, "fixture")))

    def test_fixture_covers_the_planned_families_and_registers(self):
        recs = load_fixtures()
        self.assertEqual({r["meta"]["family"] for r in recs}, {"F1", "F3", "F4", "F5", "F7"})
        self.assertEqual({r["meta"]["register"] for r in recs}, {"tegezo", "magazo"})
        self.assertEqual({len(r["turns"]) // 2 for r in recs}, {3, 4})


def structural_cases():
    def top_extra(r): r["extra"] = 1
    def drop(field): return lambda r: r.pop(field)
    def setf(field, value):
        def f(r): r[field] = value
        return f
    def meta_set(key, value):
        def f(r): r["meta"][key] = value
        return f
    def meta_del(key): return lambda r: r["meta"].pop(key)
    def turn_set(i, key, value):
        def f(r): r["turns"][i][key] = value
        return f

    def swap_roles(r):
        r["turns"][2]["role"], r["turns"][3]["role"] = "assistant", "user"

    def drop_last(r): r["turns"].pop()
    def drop_first(r): r["turns"].pop(0)
    def two_exchanges(r):
        r["turns"] = r["turns"][:4]
        r["meta"]["n_exchanges"] = 2
        r["meta"]["depends"] = [d for d in r["meta"]["depends"] if d["turn"] < 4]
        r["output"] = r["turns"][-1]["text"]

    def nine_exchanges(r):
        base = r["turns"][:]
        while len(r["turns"]) < 18:
            r["turns"].append({"role": "user" if len(r["turns"]) % 2 == 0 else "assistant",
                               "text": "Kiegészítő üzenet száma %d, rendben." % len(r["turns"])})
        r["meta"]["n_exchanges"] = 9
        r["output"] = r["turns"][-1]["text"]

    def add_ex(r): r["meta"]["depends"].append({"turn": 3, "on": [0], "depth": 1})

    return [
        ("unknown_field", top_extra, "unknown_field"),
        ("missing_field_meta", drop("meta"), "missing_field"),
        ("missing_field_turns", drop("turns"), "missing_field"),
        ("bad_id", setf("id", "multiturn_1"), "bad_id"),
        ("bad_id_upper", setf("id", "MTFX_X"), "bad_id"),
        ("bad_category", setf("category", "simple_qa"), "bad_category"),
        ("instruction_empty", setf("instruction", " "), "bad_type"),
        ("input_nonempty", setf("input", "valami"), "derived_input_nonempty"),
        ("difficulty", setf("difficulty", "nehéz"), "bad_difficulty"),
        ("quality_notes_empty", setf("quality_notes", ""), "bad_type"),
        ("source_empty", setf("source", ""), "bad_type"),
        ("tags_prefix", setf("tags", ["magyar", "tobbfordulos", "instruction_core", "felhasznaloi_javitas"]), "tags_invalid"),
        ("tags_too_short", setf("tags", ["magyar", "instruction_core", "tobbfordulos"]), "tags_invalid"),
        ("tags_uppercase", setf("tags", ["magyar", "instruction_core", "tobbfordulos", "Felhasznaloi"]), "tags_invalid"),
        ("tags_family_mismatch", setf("tags", ["magyar", "instruction_core", "tobbfordulos", "pontositas"]), "tag_family_mismatch"),
        ("tags_unknown_family_slug", setf("tags", ["magyar", "instruction_core", "tobbfordulos", "valami_mas"]), "tag_family_mismatch"),
        ("tags_unknown_slug_and_family", lambda r: (r["meta"].update(family="F0"), r.update(tags=["magyar", "instruction_core", "tobbfordulos", "valami_mas"])), "tags_invalid"),
        ("meta_not_object", setf("meta", []), "meta_not_object"),
        ("meta_unknown_key", meta_set("extra", 1), "meta_unknown_key"),
        ("meta_missing_domain", meta_del("domain"), "meta_missing"),
        ("meta_missing_depends", meta_del("depends"), "meta_missing"),
        ("meta_family_invalid", meta_set("family", "F0"), "meta_family_invalid"),
        ("meta_skills_empty", meta_set("skills", []), "meta_skills_invalid"),
        ("meta_skills_unknown", meta_set("skills", ["felhasznaloi_javitas", "nincs_ilyen"]), "meta_skills_invalid"),
        ("meta_skills_missing_primary", meta_set("skills", ["visszautalas"]), "meta_skills_invalid"),
        ("meta_skills_duplicate", meta_set("skills", ["felhasznaloi_javitas", "felhasznaloi_javitas"]), "meta_skills_invalid"),
        ("meta_split_group", meta_set("split_group", "g1"), "meta_split_group_invalid"),
        ("meta_persona", meta_set("persona", "person1"), "meta_persona_invalid"),
        ("meta_domain", meta_set("domain", "politika"), "meta_domain_invalid"),
        ("meta_persona_names_unapproved", meta_set("persona_names", ["Béla"]), "meta_persona_names_invalid"),
        ("meta_persona_names_duplicate", meta_set("persona_names", ["Bence", "Bence"]), "meta_persona_names_invalid"),
        ("meta_register", meta_set("register", "kozvetlen"), "meta_register_invalid"),
        ("meta_flag", meta_set("user_typos", "nem"), "meta_flag_invalid"),
        ("meta_fixture_false_in_fixture_mode", meta_set("fixture", False), "meta_fixture_mismatch"),
        ("meta_n_exchanges", meta_set("n_exchanges", 5), "meta_n_exchanges_mismatch"),
        ("depends_not_list", meta_set("depends", "nincs"), "meta_depends_not_list"),
        ("depends_extra_key", meta_set("depends", [{"turn": 3, "on": [0], "depth": 1, "x": 1}]), "meta_depends_entry"),
        ("depends_user_turn", meta_set("depends", [{"turn": 2, "on": [0], "depth": 1}]), "meta_depends_turn"),
        ("depends_out_of_range", meta_set("depends", [{"turn": 99, "on": [0], "depth": 1}]), "meta_depends_turn"),
        ("depends_duplicate_turn", add_ex, "meta_depends_duplicate_turn"),
        ("depends_on_empty", meta_set("depends", [{"turn": 3, "on": [], "depth": 1}]), "meta_depends_on"),
        ("depends_on_future", meta_set("depends", [{"turn": 3, "on": [3], "depth": 1}]), "meta_depends_on"),
        ("depends_on_duplicate", meta_set("depends", [{"turn": 3, "on": [0, 0], "depth": 1}]), "meta_depends_on"),
        ("depends_wrong_depth", meta_set("depends", [{"turn": 3, "on": [0, 2], "depth": 2}]), "meta_depends_depth"),
        ("depends_zero_depth", meta_set("depends", [{"turn": 3, "on": [2], "depth": 0}]), "meta_depends_depth"),
        ("turns_not_list", setf("turns", "szöveg"), "turns_not_list"),
        ("turn_extra_key", turn_set(1, "extra", 1), "turn_keys"),
        ("role_invalid", turn_set(1, "role", "system"), "role_invalid"),
        ("role_order", swap_roles, "role_order"),
        ("first_not_user", drop_first, "first_not_user"),
        ("last_not_assistant", drop_last, "last_not_assistant"),
        ("odd_message_count", drop_last, "odd_message_count"),
        ("two_exchanges", two_exchanges, "exchange_count"),
        ("nine_exchanges", nine_exchanges, "exchange_count"),
        ("text_not_string", turn_set(1, "text", 5), "text_not_string"),
        ("text_empty", turn_set(1, "text", "   "), "text_empty"),
        ("text_not_trimmed", turn_set(1, "text", " Elől szóköz."), "text_not_trimmed"),
        ("text_newline", turn_set(3, "text", "Két\nsor lett ebből."), "text_newline"),
        ("text_control_char", turn_set(3, "text", "Vezérlő\x0bkarakter itt."), "text_control_char"),
        ("text_tab", turn_set(3, "text", "Tabulátor\titt van."), "text_control_char"),
        ("text_line_separator", turn_set(3, "text", "Sorelválasztó itt van."), "text_control_char"),
        ("user_too_long", turn_set(2, "text", "Hosszú kérés. " * 30), "user_too_long"),
        ("assistant_too_long", turn_set(3, "text", "Hosszú válasz, sok szóval. " * 25), "assistant_too_long"),
        ("derived_instruction", setf("instruction", "Másik kérdés?"), "derived_instruction_mismatch"),
        ("derived_output", setf("output", "Másik válasz, ami nem az utolsó."), "derived_output_mismatch"),
    ]


class StructuralRuleTests(unittest.TestCase):
    def test_every_structural_rule_has_a_failing_case(self):
        for name, mutate, expected in structural_cases():
            with self.subTest(case=name):
                r = fixture(2)
                mutate(r)
                errs = errors(r)
                self.assertIn(expected, codes(errs), f"{name}: {sorted(codes(errs))}")
                self.assertTrue(errs)                 # a rekord ettől nem lehet turns-validált

    def test_every_documented_error_code_is_exercised_somewhere(self):
        exercised = {c for _n, _m, c in structural_cases()}
        # a tartalmi és név-kódok külön osztályokban vannak lefedve
        structural_codes = {"not_object", "unknown_field", "missing_field", "bad_id", "bad_category", "bad_type",
                            "derived_input_nonempty", "bad_difficulty", "tags_invalid", "tag_family_mismatch",
                            "meta_not_object", "meta_unknown_key", "meta_missing", "meta_family_invalid",
                            "meta_skills_invalid", "meta_split_group_invalid", "meta_persona_invalid",
                            "meta_domain_invalid", "meta_persona_names_invalid", "meta_register_invalid",
                            "meta_flag_invalid", "meta_fixture_mismatch", "meta_n_exchanges_mismatch",
                            "meta_depends_not_list", "meta_depends_entry", "meta_depends_turn",
                            "meta_depends_duplicate_turn", "meta_depends_on", "meta_depends_depth",
                            "turns_not_list", "turn_keys", "role_invalid", "role_order", "first_not_user",
                            "last_not_assistant", "odd_message_count", "exchange_count", "text_not_string",
                            "text_empty", "text_not_trimmed", "text_newline", "text_control_char",
                            "user_too_long", "assistant_too_long", "derived_instruction_mismatch",
                            "derived_output_mismatch"}
        missing = structural_codes - exercised - {"not_object"}
        self.assertEqual(missing, set(), "kód teszteset nélkül")

    def test_non_object_record(self):
        self.assertEqual(codes(errors([1, 2])), {"not_object"})
        self.assertEqual(codes(errors("szöveg")), {"not_object"})

    def test_valid_records_have_no_error_with_meaningful_variations(self):
        r = fixture(1)
        r["meta"]["user_typos"] = True
        r["meta"]["sensitive_area"] = False
        self.assertEqual(errors(r), [])
        r = fixture(5)                                    # nincs név, üres persona_names
        self.assertEqual(r["meta"]["persona_names"], [])
        self.assertEqual(errors(r), [])


CONTENT_CASES = [
    # (név, üzenet-index, szerep, új szöveg, várt kód)
    ("email_user", 2, "user", "Nyolc vendég lesz, a húgom címe anna.kiss@example.com, oda küldd.", "content_personal_data_suspected"),
    ("phone_assistant", 3, "assistant", "Hívd fel a szervizt a 06 20 123 4567 számon, ők pontosan megmondják.", "content_personal_data_suspected"),
    ("password_user", 2, "user", "A jelszó: hunter2 és ezzel lépek be minden oldalra.", "content_dangerous_content_suspected"),
    ("api_key_assistant", 3, "assistant", "Használd ezt: api_key=ABCD1234EFGH és minden működni fog.", "content_dangerous_content_suspected"),
    ("english_assistant", 3, "assistant", "Yes, the you are right and this is what we have.", "content_english_mixing"),
    ("garbled_user", 2, "user", "Nyolc vendég lesz, de a kkkkkkkk zzzzzzz xyzqwrtp nem világos.", "content_garbled_output"),
    ("repeated_user", 2, "user", "Neeeeeeeeem, ez így nem jó nekem semmiképp.", "content_repeated_char_run"),
    ("overclaim_assistant", 3, "assistant", "Nyugodj meg, mindent tudok és sosem tévedek ezekben.", "content_overclaiming"),
    ("too_short_assistant", 3, "assistant", "Igen.", "content_output_too_short"),
    ("identity_assistant", 3, "assistant", "Az MF-AI projekt szerint ezt így kell csinálni.", "identity_mention"),
    ("identity_user_nexora", 2, "user", "Ezt a Nexora rendszerben láttam, igaz?", "identity_mention"),
    ("url_user", 2, "user", "Itt van a lap: www.pelda.hu, nézd meg és mondd el.", "url_or_domain"),
    ("digits_assistant", 3, "assistant", "A rendelési szám 1234567890, ezt add meg a szervizben.", "long_digit_run"),
    ("label_user", 2, "user", "Írd le így: AI: rendben, és folytasd tovább.", "role_label_in_text"),
    ("label_assistant", 3, "assistant", "A válasz kezdete user: kérdés lenne, de ez csak példa.", "role_label_in_text"),
    ("blocked_given_name", 2, "user", "A nagybátyám, Béla is jön a vendégségbe.", "name_not_approved"),
    ("full_name_surname_first", 3, "assistant", "Kovács Réka nevén foglalj, úgy egyszerűbb lesz.", "full_name_pattern"),
    ("full_name_given_first", 3, "assistant", "Réka Kovács nevén foglalj, úgy egyszerűbb lesz.", "full_name_pattern"),
    ("undeclared_approved_name", 2, "user", "A barátnőm, Anna is velünk jön a szülinapra.", "name_not_declared"),
]

# ezek a hibák a régi validátor számára ÁTLÁTHATATLANOK, ha nem az első user / utolsó assistant üzenetben vannak
MIDDLE_ONLY_LEGACY_BLIND = {"content_personal_data_suspected", "content_dangerous_content_suspected",
                            "content_english_mixing", "content_garbled_output", "content_repeated_char_run",
                            "content_overclaiming", "content_output_too_short"}


class ContentRuleTests(unittest.TestCase):
    def test_content_rules_fire_on_intermediate_messages_with_exact_path(self):
        for name, idx, role, text, expected in CONTENT_CASES:
            with self.subTest(case=name):
                r = fixture(1)                       # 6 üzenet: az 1-4. index KÖZBENSŐ
                self.assertEqual(r["turns"][idx]["role"], role)
                self.assertNotIn(idx, (0, len(r["turns"]) - 1))
                set_text(r, idx, text)
                errs = [e for e in errors(r) if e.code == expected]
                self.assertTrue(errs, f"{name}: {sorted(codes(errors(r)))}")
                self.assertTrue(any(e.path == f"turns[{idx}].text" for e in errs), [e.path for e in errs])

    def test_error_only_in_an_intermediate_message_is_invisible_to_the_old_validator(self):
        """A kérés kulcseset: a hiba/személyes adat KIZÁRÓLAG egy közbenső üzenetben van."""
        with tempfile.TemporaryDirectory() as tmp:
            for name, idx, role, text, expected in CONTENT_CASES:
                if expected not in MIDDLE_ONLY_LEGACY_BLIND:
                    continue
                with self.subTest(case=name):
                    r = fixture(1)
                    set_text(r, idx, text)
                    # 1) a régi validátor a rekordot elfogadja (üres problémalista)
                    self.assertEqual(legacy.validate_row(r, 1, set()), [], "a régi validátor átengedi a rekordot")
                    # 2) fájl-szinten is: nincs elutasított sor, érvényes sornak számít
                    p = os.path.join(tmp, name + ".jsonl")
                    with open(p, "w", encoding="utf-8", newline="\n") as f:
                        f.write(json.dumps(r, ensure_ascii=False) + "\n")
                    res = legacy.validate_file(p)
                    self.assertEqual((len(res["valid_rows"]), len(res["rejected_rows"])), (1, 0))
                    self.assertTrue(mt.legacy_compatible(r))
                    # 3) az új ellenőrző elutasítja, a pontos üzenetnél
                    fr = mt.validate_file(p, "fixture", BANK)
                    entry = fr["records"][0]
                    self.assertTrue(entry["legacy_validator_compatible"])
                    self.assertFalse(entry["turns_validated"])
                    self.assertEqual(fr["summary"]["legacy_compatible_but_not_turns_validated"], 1)
                    self.assertEqual(fr["summary"]["turns_validated"], 0)
                    self.assertTrue(any(i["code"] == expected and i["path"] == f"turns[{idx}].text"
                                        for i in entry["issues"]))

    def test_contrast_the_same_pii_in_the_first_or_last_message_is_caught_by_both(self):
        for idx in (0, 5):
            with self.subTest(idx=idx):
                r = fixture(1)
                text = ("Szia! Anna vagyok, a címem anna.kiss@example.com, ide várom a választ." if idx == 0
                        else "Küldd a választ ide: 06 20 123 4567, ott elérsz, Réka.")
                set_text(r, idx, text)
                self.assertNotEqual(legacy.validate_row(r, 1, set()), [], "a régi validátor az első/utolsó üzenetet látja")
                self.assertTrue(errors(r))

    def test_personal_data_only_in_quality_notes_is_caught(self):
        r = fixture(1)
        r["quality_notes"] = "Jegyzet, kapcsolat: anna.kiss@example.com"
        self.assertIn("quality_notes", {e.path for e in errors(r) if e.code == "content_personal_data_suspected"})
        r = fixture(1)
        r["quality_notes"] = "Ez az MF-AI csomag jegyzete."
        self.assertIn("identity_mention", codes(errors(r)))

    def test_short_user_messages_are_fine_but_short_assistant_messages_are_not(self):
        r = fixture(2)
        set_text(r, 2, "Igen.")
        self.assertNotIn("content_output_too_short", codes(errors(r)))
        r = fixture(2)
        set_text(r, 3, "Rendben.")
        self.assertIn("content_output_too_short", codes(errors(r)))

    def test_role_label_word_boundaries_do_not_over_trigger(self):
        r = fixture(1)
        set_text(r, 2, "Nyolc vendég lesz, Kai: az unokatestvérem is hoz süteményt, ez csak egy név.")
        self.assertNotIn("role_label_in_text", codes(errors(r)))

    def test_legacy_guards_still_apply_to_each_message_once_per_code(self):
        r = fixture(1)
        set_text(r, 2, "Írj a mia@example.com vagy a kata@example.com címre, mindkettő jó.")
        c = [e for e in errors(r) if e.code == "content_personal_data_suspected" and e.path == "turns[2].text"]
        self.assertEqual(len(c), 1, "üzenetenként egy kód egyszer")


class NameCheckTests(unittest.TestCase):
    def test_bank_is_well_formed(self):
        a, g, s, p = (BANK[k] for k in ("approved_given_names", "blocked_given_names", "blocked_surnames",
                                        "allowed_proper_nouns"))
        self.assertGreaterEqual(len(a), 150)
        for lst in (a, g, s, p):
            self.assertEqual(len(lst), len(set(lst)), "duplikált bejegyzés")
            self.assertTrue(all(x[0].isupper() for x in lst))
        self.assertEqual(set(a) & set(g), set())
        self.assertEqual(set(a) & set(s), set())
        self.assertEqual(set(g) & set(s), set())
        self.assertEqual((set(a) | set(g) | set(s)) & set(p), set())

    def test_inflected_approved_names_are_recognised(self):
        for text, name in [("Rékának", "Réka"), ("Katával", "Kata"), ("Bencével", "Bence"), ("Péterrel", "Péter"),
                           ("Zsolttal", "Zsolt"), ("Ádámot", "Ádám"), ("Annát", "Anna"), ("Ákosnak", "Ákos")]:
            with self.subTest(token=text):
                errs, _w, used = mt.check_names(f"Ma beszéltem {text} a dologról.", BANK, declared=set())
                self.assertEqual([c for c, _m in errs], ["name_not_declared"], text)
                self.assertEqual(used, {name})
                errs, _w, _u = mt.check_names(f"Ma beszéltem {text} a dologról.", BANK, declared={name})
                self.assertEqual(errs, [])

    def test_common_words_are_not_mistaken_for_names(self):
        for word in ("Pálinka", "Edény", "Simonyi", "Tibornak"):
            errs, _w, used = mt.check_names(f"Ma {word} volt szó.", BANK, declared=set())
            if word == "Tibornak":
                self.assertEqual(used, {"Tibor"})
            else:
                self.assertEqual((errs, used), ([], set()), word)

    def test_places_and_unknown_capitalized_words(self):
        errs, warns, _u = mt.check_names("Ma Szegedről indulok Debrecenbe, aztán Pistike is jön.", BANK, set())
        self.assertEqual(errs, [])
        self.assertEqual([m for c, m in warns if "Pistike" in m], [f"nagybetűs szó mondat közben, átolvasásra: 'Pistike'"])
        self.assertFalse(any("Szeged" in m or "Debrecen" in m for _c, m in warns))
        # mondat eleji nagybetű nem gyanús
        errs, warns, _u = mt.check_names("Pistike is jön. Holnap Nóra sem ér rá.", BANK, {"Nóra"})
        self.assertEqual(warns, [], "mondat eleji nagybetű és deklarált név nem gyanús")
        self.assertEqual(errs, [])

    def test_warning_only_conditions_do_not_invalidate_the_record(self):
        r = fixture(1)
        set_text(r, 2, "Nyolc vendég lesz, a húgom, Panna és Pistike is benne van.")
        self.assertEqual(errors(r), [])
        self.assertIn("capitalized_token_review", codes(warnings(r)))
        r = fixture(1)
        r["meta"]["persona_names"] = ["Réka", "Panna", "Ákos"]
        self.assertEqual(errors(r), [])
        self.assertIn("persona_name_unused", codes(warnings(r)))
        r = fixture(5)
        r["meta"]["depends"] = []
        self.assertEqual(errors(r), [])
        r = fixture(1)
        r["meta"]["depends"] = []
        self.assertEqual(errors(r), [])
        self.assertIn("family_expects_depends", codes(warnings(r)))
        r = fixture(3)
        r["meta"]["depends"] = [{"turn": 3, "on": [2], "depth": 1}]
        self.assertIn("family_expects_depends", codes(warnings(r)))       # F7: nincs 2 mélységű visszatérés
        r = fixture(1)
        r["turns"][5]["text"] = r["turns"][3]["text"]
        r["output"] = r["turns"][5]["text"]
        self.assertIn("duplicate_assistant_message", codes(warnings(r)))


class FileLevelAndCountTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = self._tmp.name

    def tearDown(self):
        self._tmp.cleanup()

    def write(self, name, lines):
        p = os.path.join(self.tmp, name)
        with open(p, "wb") as f:
            f.write(("\n".join(lines) + "\n").encode("utf-8"))
        return p

    def test_fixture_file_summary_counts_are_separate_and_correct(self):
        res = mt.validate_file(FIXTURE_FILE, "fixture", BANK)
        s = res["summary"]
        recs = load_fixtures()
        n_msg = sum(len(r["turns"]) for r in recs)
        self.assertEqual((s["records"], s["turns_validated"], s["legacy_validator_compatible"]), (5, 5, 5))
        self.assertEqual(s["conversations"], 5)
        self.assertEqual(s["messages"], n_msg)
        self.assertEqual(s["training_samples"], n_msg // 2)
        self.assertEqual(s["training_samples_first_turn"], 5)
        self.assertEqual(s["training_samples_history_dependent"], n_msg // 2 - 5)
        self.assertEqual(s["legacy_compatible_but_not_turns_validated"], 0)
        self.assertEqual((n_msg, n_msg // 2), (36, 18))

    def test_counts_only_include_turns_validated_records(self):
        good, bad = fixture(1), fixture(2)
        bad["turns"][2]["text"] = "Írd a pelda@example.com címre."
        p = self.write("k.jsonl", [json.dumps(good, ensure_ascii=False), json.dumps(bad, ensure_ascii=False)])
        s = mt.validate_file(p, "fixture", BANK)["summary"]
        self.assertEqual((s["records"], s["turns_validated"], s["records_with_errors"]), (2, 1, 1))
        self.assertEqual((s["conversations"], s["messages"], s["training_samples"]), (1, 6, 3))
        self.assertEqual(s["legacy_validator_compatible"], 2)
        self.assertEqual(s["legacy_compatible_but_not_turns_validated"], 1)
        self.assertEqual(s["counted_over"], "csak a turns-validált rekordok")

    def test_file_issues_duplicates_and_blank_lines(self):
        a = json.dumps(fixture(1), ensure_ascii=False)
        p = self.write("d.jsonl", [a, "", "{ez nem json}", "[1,2]", a])
        res = mt.validate_file(p, "fixture", BANK)
        self.assertEqual([i["code"] for i in res["file_issues"]], ["invalid_json"])
        codes_by_line = {r["line"]: {i["code"] for i in r["issues"] if i["severity"] == "error"} for r in res["records"]}
        self.assertEqual(codes_by_line[5], {"duplicate_id"})
        self.assertEqual(codes_by_line[4], {"not_object"})
        self.assertEqual(res["summary"]["turns_validated"], 1)

    def test_summary_status_fields_are_never_conflated(self):
        bad = fixture(1)
        bad["turns"][2]["text"] = "A szám 06 20 123 4567 lesz a titkos kód."
        p = self.write("s.jsonl", [json.dumps(bad, ensure_ascii=False)])
        entry = mt.validate_file(p, "fixture", BANK)["records"][0]
        self.assertTrue(entry["legacy_validator_compatible"])
        self.assertFalse(entry["turns_validated"])
        self.assertIn("legacy_validator_compatible", entry)
        self.assertIn("turns_validated", entry)


class CliTests(unittest.TestCase):
    def cli(self, *args):
        env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
        return subprocess.run([sys.executable, TOOL_PATH, *args], capture_output=True, text=True,
                              encoding="utf-8", env=env)

    def test_valid_fixture_run_and_disclaimer(self):
        r = self.cli(FIXTURE_FILE, "--mode", "fixture")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("turns-validált: 5", r.stdout)
        self.assertIn("régi-validátor-kompatibilis: 5", r.stdout)
        self.assertIn("üzenet: 36", r.stdout)
        self.assertIn("tanítási minta: 18", r.stdout)
        self.assertIn("NEM tartalmi ellenőrzés, NEM training-ready", r.stdout)

    def test_dataset_mode_rejects_fixtures_with_exit_code_1(self):
        r = self.cli(FIXTURE_FILE, "--mode", "dataset")
        self.assertEqual(r.returncode, 1)
        self.assertIn("bad_id", r.stdout)
        self.assertIn("meta_fixture_mismatch", r.stdout)
        self.assertIn("turns-validált: 0", r.stdout)

    def test_usage_errors_and_json_report(self):
        self.assertEqual(self.cli("nincs_ilyen.jsonl", "--mode", "fixture").returncode, 2)
        self.assertEqual(self.cli(FIXTURE_FILE).returncode, 2)                       # --mode kötelező
        with tempfile.TemporaryDirectory() as tmp:
            bad_bank = os.path.join(tmp, "b.json")
            with open(bad_bank, "w", encoding="utf-8") as f:
                f.write('{"approved_given_names": "nem lista"}')
            self.assertEqual(self.cli(FIXTURE_FILE, "--mode", "fixture", "--name-bank", bad_bank).returncode, 2)
            empty = os.path.join(tmp, "ures.jsonl")
            with open(empty, "w", encoding="utf-8") as f:
                f.write("\n")
            self.assertEqual(self.cli(empty, "--mode", "fixture").returncode, 1)     # nincs rekord: nem lehet "sikeres"
            rep = os.path.join(tmp, "riport.json")
            r = self.cli(FIXTURE_FILE, "--mode", "fixture", "--json", rep)
            self.assertEqual(r.returncode, 0)
            data = json.loads(read_text(rep))
            self.assertEqual(data["results"][0]["summary"]["turns_validated"], 5)
            self.assertIn("NEM training-ready", data["disclaimer"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
