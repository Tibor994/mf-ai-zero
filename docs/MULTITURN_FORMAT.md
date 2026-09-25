# Többfordulós (`multiturn`) beszélgetés-formátum — MT-0 specifikáció, v1

Ez a dokumentum a 7. csomag (1000 többfordulós beszélgetés) rekord-formátumát rögzíti. **Csak formátum**: az 1000 beszélgetés adatai még nem léteznek, a tanítás nem indult. A szabályokat a `tools/multiturn_validate.py` (MT-1) ellenőrzi; a névtár a `tools/multiturn_name_bank.json`; a tesztadat a `tests/fixtures/multiturn/valid_conversations.jsonl`.

## 1. Alapelvek

* **Egy példa = egy teljes beszélgetés** = egy JSONL sor. A cél 1000 beszélgetés (800/100/100 felosztás csoportonként, lásd `data/reports/multiturn_package7_plan.md`).
* Az üzenetek **sorrendjét és szerepeit a `turns` tömb őrzi**. A beszélgetés atomi: a felosztás és a duplikáció-ellenőrzés beszélgetés/csoport szinten történik.
* A 9 meglévő mező megmarad (a régi eszközök ne omoljanak össze), de azok **származtatottak**; a régi validátor sikere **nem** minősíti ellenőrzöttnek a `turns` tartalmát (lásd 8. szakasz).
* Az üzenetek egysorosak: nincs újsor, tabulátor, vezérlő- vagy sorelválasztó karakter. Ez teszi lehetővé, hogy a későbbi renderelések (`User:/AI:` blokkok, üres sorral elválasztva) ne okozzanak téves blokkhatárt.

## 2. Rekord

```json
{"id": "multiturn_0001", "category": "multiturn",
 "instruction": "<az első user-üzenet szövege>", "input": "", "output": "<az utolsó assistant-üzenet szövege>",
 "tags": ["magyar", "instruction_core", "tobbfordulos", "felhasznaloi_javitas"],
 "difficulty": "medium", "quality_notes": "...", "source": "claude_generated",
 "turns": [{"role": "user", "text": "..."}, {"role": "assistant", "text": "..."}, "..."],
 "meta": {"family": "F4", "skills": ["felhasznaloi_javitas", "elozmeny_koveteles"], "n_exchanges": 4,
          "split_group": "g0001", "persona": "p001", "persona_names": ["Bence"], "domain": "utazas",
          "depends": [{"turn": 3, "on": [0, 2], "depth": 1}],
          "register": "tegezo", "user_typos": false, "sensitive_area": false}}
```

| Mező | Szabály |
|---|---|
| `id` | `dataset` módban `multiturn_NNNN` (4 számjegy); `fixture` módban `mtfx_<kisbetű/szám/_>` |
| `category` | pontosan `multiturn` |
| `instruction` | **egyezik** az első user-üzenettel |
| `input` | üres string |
| `output` | **egyezik** az utolsó assistant-üzenettel |
| `tags` | ASCII snake_case; az első három `magyar`, `instruction_core`, `tobbfordulos`; a negyedik a `meta.family` slugja; további címke opcionális |
| `difficulty` | `easy` / `medium` / `hard` |
| `quality_notes`, `source` | nem üres string (a `quality_notes`-ra is lefutnak a személyes adat/veszélyes tartalom szűrők) |
| `turns` | lista, lásd 3. szakasz |
| `meta` | lásd 4. szakasz; ismeretlen kulcs hiba |
| további felső szintű mező | hiba (`unknown_field`) |

## 3. `turns`

* Elemei pontosan `{"role", "text"}` kulcsúak. A szerepek **felváltva** követik egymást, `user`-rel kezdődnek és `assistant`-tal végződnek (`role_order`, `first_not_user`, `last_not_assistant`, `odd_message_count`).
* **3–8 váltás** (1 váltás = 1 user + 1 assistant üzenet), azaz 6–16 üzenet.
* Üzenet-szöveg: string, nem üres, **nyírt** (nincs kezdő/záró szóköz), **nincs újsor/CR/tabulátor/vezérlő/sorelválasztó karakter**, user ≤ 300 karakter, assistant ≤ 600 karakter; az assistant-üzenet legalább 3 szó (a projekt meglévő `output` szabálya).
* A szövegben nem szerepelhet `User:` / `AI:` felirat (sor közben sem), MF-AI/Nexora/Nextora említés, URL/domain, 8+ jegyű számsor, e-mail/telefon-szerű minta.

## 4. `meta`

| Kulcs | Kötelező | Szabály |
|---|---|---|
| `family` | igen | `F1`…`F9` (lásd 5.) |
| `skills` | igen | nem üres, egyedi lista az ismert készség-slugokból; tartalmazza a család elsődleges slugját |
| `n_exchanges` | igen | egyezik a `turns` hosszából számolt váltásszámmal |
| `split_group` | igen | `g0000` alakú; az összetartozó változatok azonos csoportot kapnak (a felosztás egysége) |
| `persona` | igen | `p000` alakú |
| `persona_names` | igen | a beszélgetésben szereplő **jóváhagyott** keresztnevek listája (lehet üres) |
| `domain` | igen | `vasarlas`, `utazas`, `fozes`, `tanulas`, `munka`, `otthon`, `egeszseg_sport`, `technologia`, `szabadido`, `ugyintezes` |
| `depends` | igen | lista (lehet üres), lásd lent |
| `register` | nem | `tegezo` / `magazo` |
| `user_typos`, `sensitive_area` | nem | logikai |
| `fixture` | módfüggő | `fixture` módban igaz kell; `dataset` módban nem lehet igaz |

**`depends`** — előzmény-függés annotáció egy assistant-fordulóra: `{"turn": t, "on": [i, ...], "depth": d}`.
* `turn`: az assistant-üzenet indexe a `turns`-ben (0-tól; páratlan);
* `on`: a `turn` előtti üzenetek indexei (nem üres, egyedi), amelyekre a válasz épül;
* `depth = t//2 − min(i//2 for i in on)`, és legalább 1 (0 mélység nem előzmény-függés). Ez határozza meg, hogy a válasz hány váltásnyival korábbi tartalomra épül: a futásidejű előzmény ma csak az **1 utolsó váltást** adja (`src/memory.py`), a mélység ≥ 2 minták csak összefoglalós (R3) vagy teljes előzményes (R2) rendereléssel tanítható értelmesen.

## 5. Családok és készségek

| Család | Slug | Cél az 1000-ben |
|---|---|---|
| F1 | `elozmeny_koveteles` | 150 |
| F2 | `visszautalas` | 130 |
| F3 | `pontositas` | 130 |
| F4 | `felhasznaloi_javitas` | 130 |
| F5 | `valtozo_keres` | 110 |
| F6 | `temavaltas` | 90 |
| F7 | `temavaltas_visszateres` | 100 |
| F8 | `tobblepeses_feladat` | 110 |
| F9 | `bizonytalansag_tobbfordulo` | 50 |

(Figyelmeztetés, nem hiba: az F1, F2, F4, F5, F7, F8 család előzmény-függő fordulatot vár, az F7 legalább 2 mélységű visszatérést.)

## 6. Módok és tesztadat elkülönítése

* `dataset`: a valódi csomag. `mtfx_` azonosítójú vagy `meta.fixture: true` rekord itt **hibát** ad.
* `fixture`: a tesztadat (`tests/fixtures/multiturn/`, id `mtfx_…`, `meta.fixture: true`, `source: test_fixture`). Ezek **nem részei az 1000 beszélgetéses csomagnak**, nem kerülnek `data/` alá, tanításra nem használhatók; a tesztek ellenőrzik, hogy `data/raw|clean|rejected` alatt nincs `multiturn` fájl.

## 7. Számolás (külön jelentendő mennyiségek)

| Mennyiség | Definíció |
|---|---|
| Beszélgetés | egy rekord (a cél mértékegysége) |
| Üzenet | a `turns` elemeinek száma (user + assistant) |
| Tanítási minta | egy assistant-fordulóra adott cél, előzménnyel: **váltásonként 1**; ebből beszélgetésenként 1 az első fordulóé (előzmény nélkül), a többi előzmény-függő |

Az MT-1 összegzése ezt külön és csak a `turns-validált` rekordokra számolja.

## 8. Ellenőrzés és állapotok

A régi `dataset_validate.py` nem alkalmas: nincs kategória-fehérlista, extra mezőt nem utasít el, és csak a 9 régi mezőt látja, így a közbenső üzenetek hibái észrevétlenek. Az állapotok **külön** szerepelnek, egyik sem helyettesíti a másikat:

| Állapot | Jelentés | Ki adja |
|---|---|---|
| `legacy_validator_compatible` | a 9 régi mezőre a régi validátor átengedi (csak szerkezeti kompatibilitás) | `dataset_validate.validate_row` |
| `turns_validated` | az MT-1 minden szabálya hibátlan (nincs `error` súlyú probléma) | `multiturn_validate.py` |
| duplikáció-ellenőrzött, tartalmilag átolvasott, exportálható | későbbi feladatok (MT-3, kézi átolvasás, MT-4) | — |
| `training-ready` | csak kifejezett felhasználói döntéssel | felhasználó |

**MT-1 szabálykódok** (`error`, ha nincs jelölve):
* szerkezet: `not_object`, `unknown_field`, `missing_field`, `bad_id`, `bad_category`, `bad_type`, `bad_difficulty`, `derived_input_nonempty`, `derived_instruction_mismatch`, `derived_output_mismatch`, `tags_invalid`, `tag_family_mismatch`, `duplicate_id` (fájlon belül);
* `meta`: `meta_not_object`, `meta_unknown_key`, `meta_missing`, `meta_family_invalid`, `meta_skills_invalid`, `meta_n_exchanges_mismatch`, `meta_split_group_invalid`, `meta_persona_invalid`, `meta_persona_names_invalid`, `meta_domain_invalid`, `meta_register_invalid`, `meta_flag_invalid`, `meta_fixture_mismatch`, `meta_depends_not_list`, `meta_depends_entry`, `meta_depends_turn`, `meta_depends_duplicate_turn`, `meta_depends_on`, `meta_depends_depth`;
* `turns`: `turns_not_list`, `turn_keys`, `role_invalid`, `role_order`, `first_not_user`, `last_not_assistant`, `odd_message_count`, `exchange_count`, `text_not_string`, `text_empty`, `text_not_trimmed`, `text_newline`, `text_control_char`, `user_too_long`, `assistant_too_long`;
* tartalom **üzenetenként** (a közbenső fordulókra is): a projekt meglévő szűrései a `dataset_validate.validate_row` importálásával (`content_personal_data_suspected`, `content_dangerous_content_suspected`, `content_english_mixing`, `content_garbled_output`, `content_repeated_char_run`, `content_overclaiming`, `content_output_too_short` csak assistant-üzenetre), továbbá `identity_mention`, `url_or_domain`, `long_digit_run`, `role_label_in_text`, és a névszabályok: `name_not_approved`, `full_name_pattern`, `name_not_declared`; a `quality_notes` mezőre is;
* figyelmeztetés (nem blokkoló): `capitalized_token_review`, `duplicate_assistant_message`, `persona_name_unused`, `family_expects_depends`.

## 9. Kitalált személyes adatok és a névtár

* Minden személy **kitalált**: a szövegben csak a névtár (`approved_given_names`, ≥150) keresztnevei szerepelhetnek, önmagukban, és a `meta.persona_names`-ben deklarálva. Tiltott: a névtárban nem szereplő ismert keresztnév (`blocked_given_names`), keresztnév + vezetéknév minta (`blocked_surnames`), valós közszereplő, valós kisvállalkozás, teljes cím, telefonszám, e-mail, azonosító, URL.
* **Korlát:** a névfelismerés lista- és mintaalapú biztonsági háló (ragozott alakok szűk végződéslistával), nem bizonyíték arra, hogy egy szövegben nincs valós személy neve. A mondat közbeni ismeretlen nagybetűs szavakat figyelmeztetésként jelzi átolvasásra. A tartalmi átolvasás nem helyettesíthető.

## 10. Renderelések (későbbi feladat, MT-4)

A tanítószöveg-renderelést a kanonikus rekordból az MT-4 exportáló készíti (R1: a cél előtti 1 váltás, a `src/memory.py` konstansaival; R3: összefoglalós; R2: teljes előzmény). Ez a specifikáció nem módosítja a tanító- és chat kódot.

## 11. Ismert korlátok

* Az MT-1 formátum- és szűrőellenőrzés: nem ítéli meg, hogy a válasz **tartalmilag** helyes, természetes vagy előzmény-hű; a `depends` annotáció helyességét (hogy a válasz valóban az előzményre épül) kézi átolvasás ellenőrzi.
* A duplikáció és a felosztás (MT-3, MT-2) még nincs implementálva.
* A karakter-LSTM képessége hosszú kontextus használatára nem bizonyított.
