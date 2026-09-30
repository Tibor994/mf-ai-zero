# MT-5 — többfordulós tanító BETÖLTŐ (elkülönített, kísérleti) — jelentés

Dátum: 2026-09-30. Modul: `src/train_multiturn.py` (**mt5-1.0**, új). Tesztek: `tests/test_train_multiturn.py` (**83 teszt**). Dokumentáció: `docs/MULTITURN_TRAIN.md`. Bizonyítékok: `data/reports/audit_evidence/mt5_train/`.

**Ez a modul NEM tanít.** Nincs optimalizáló lépés, gradiens-visszaterjesztés, paraméterfrissítés vagy betanított checkpoint mentése — a `--dry-run` kapcsoló kötelező, más futási mód (pl. `--train`) nem létezik a kódban (AST-alapú teszt igazolja, hogy a forrás nem tartalmaz `.backward()`/`.step()`/`torch.save(...)` hívást és `optim` importot). A tényleges tanítás megindítása külön feladat és külön, kifejezett jóváhagyás.

A meglévő v0.7 `train_chat.py`, a `chat.py`/`guard.py`/`router.py` stabil lánc, a `src/memory.py` (futásidejű előzmény) és a webapp/backend **nem módosultak**; az MT-5 modul ezeket nem is importálja (teszttel igazolva). A `config.py`-t és a `model.py` `CharLSTM` osztályát csak olvassa. A `tools/` alatti MT-1..MT-4 eszközöket sem importálja: az MT-4 export érvényességét önállóan, saját ellenőrzéssel vizsgálja. Semmilyen adat nem lett training-ready; az export sikere/a száraz futás sikere a `split_approved`/`content_verified`/`training_ready` állapotokat nem változtatja (mind `false`, a forrás-export mezői érintetlenek).

## 0. A kiinduló állapot ellenőrzése a tényleges repóval

| Állítás | Ellenőrzés | Eredmény |
|---|---|---|
| a legutóbbi commit `cbd09fa` (`v1.13.23-mt4-export`) | `git log`, `git rev-parse HEAD origin/main` | egyezik (HEAD = origin/main) |
| 4500 clean sor, 6 kizárt, 4494 exportált | a valódi TE-1 export a méréshez használt csővezetékben | **4500 beolvasva, 6 kizárva, 4494 exportálva** |
| valódi többfordulós adat nincs | `data/raw\|clean\|rejected\|inbox` alatt `*multiturn*` | **nincs** (tesztelt) |
| a korábbi eszközök működése | TE-1 35, TE-2 36, MT-1 29, MT-3 75, MT-2 70, MT-4 70, MT-5 83 teszt együtt; `tests.test_v1_7_4_dataset_foundation` | mind OK, STABIL (398 teszt együtt, kilépési kód 0; a foundation teszt külön, saját kilépési kóddal STABIL) |

## A. A három kért döntés a megvalósításban

| # | A döntésed | Megvalósítás | Teszt |
|---|---|---|---|
| 1 | **R2 az elsődleges betöltési próba; R1 külön, összehasonlító próba, a csonkolási/előzményvesztési jelölések megőrzésével; egyik sem tanítási jóváhagyás; R3 most nem készül** | alapból mindkét mód (`--modes R2,R1`) betöltődik, kódolódik, kötegelődik, előrefutási próbán megy át; a jelentés `config.primary_mode`/`config.secondary_mode` mezője külön jelzi őket; a szótár kizárólag R2/train mintákból épül (R1 ugyanezt használja); minden R1 minta megőrzi az MT-4 `history_truncation`/`dependency` jelöléseit (a `char_length`, `content_complete`, a `samples_over_trained_context_*` mezőkön át is látszik); R3 kérése `RefusedError` (18-as kód, indoklással) | `test_r3_and_unknown_and_empty_or_duplicate_mode_lists_are_refused`; `test_forward_pass_ran_once_per_batch...`; a jelentés `unsupported_modes` mezője; a valódi export-mérésben R1 vs R2 külön statisztika |
| 2 | **Nincs véletlen ablakolás; a mintahatár és a célválaszhoz szükséges előzmény megmarad; a meglévő tanítót nem módosítottuk; a hossz és az erőforrásigény mérve; explicit hosszkorlát fölött visszatartás jelentéssel, nem csendes csonkítás; a jelenlegi modell kompatibilitási korlátja külön dokumentálva; a sikeres betöltés nem bizonyítja a hosszú kontextus megtanulását** | egy köteg-sor mindig pontosan egy MT-4 minta (`text` mező), a saját határain belül, összefűzés nélkül; a célmaszk az MT-4 `target` mezőjéből, két, egymástól független módon ellenőrizve (`build_target_mask` + `verify_mask_alignment`); `--max-chars` (explicit, alapból 4096) fölötti minta visszatartva, okkal és a mért hosszal (`withheld_oversized`, `sample_lengths.tsv`); a kompatibilitási próba egy FRISS, tanítatlan próba-modellel (a `config.py` architektúra-méreteivel) fut, a jelentés külön mezője (`samples_over_trained_context_pct`) mutatja, hányszorosan haladja meg a minta a BETANÍTOTT v0.7 modell tényleges (64 karakteres) tanult tapasztalatát; `train_chat.py`/`model.py` bájtra változatlan | `TargetMaskTests` (5), `BatchingIsolationTests` (6, köztük a köteg-izoláció és az állapot-nemöröklés közvetlen próbája), `OversizeAndWithholdTests` (3), `ReportContentTests.test_compatibility_percentage_is_computed_against_config_seq_length`; a valódi méréshez lásd C. szakasz |
| 3 | **A fixture export kizárólag kifejezett tesztmódban fogadható el; normál adatkezelési módban elutasítva** | a `--mode` kifejezett, kétirányúan egyeznie kell az export `data_kind`/`fixture` jelölésével (`load_export`); egy manifest-szintű hamisítás (a `data_kind` mező átírása) sem marad észrevétlen: a mintafájlok SOROK szintjén tárolt `fixture` jelölését a `load_samples` külön, függetlenül ellenőrzi | `test_data_kind_fixture_mismatch_is_refused_in_both_directions`; `test_a_manifest_level_data_kind_forgery_is_still_caught_at_the_sample_level`; `test_real_data_mode_refuses_a_fixture_export_and_a_dataset_named_run_folder_is_required` |

## B. A megvalósítás pontjai

| A kérésed | Megvalósítás | Teszt |
|---|---|---|
| MT-4 `export_manifest.json` + mintafájlok a bemenet | `--export-manifest`; a mintafájlokat a manifest `splits.<rész>.samples.<mód>.file` mezője alapján találja meg (nem külön `--train-path`/`--val-path`: ez a korábbi vázlathoz képesti, dokumentált eltérés, mert egyetlen forrás robusztusabb egy esetleg egymáshoz nem illő fájlpár-megadásnál) | `LoadExportValidationTests`, `SampleFileValidationTests` |
| érvényesség, ellenőrzőösszeg, felosztás, azonosítók, kizárások ellenőrzése; sérült/elavult bemenettel megállás | `load_export`: eszköz/verzió/státusz, a három státuszjelző (`training_ready` stb., a manifestben ÉS a `statuses` blokkban is), kimeneti fájlok ellenőrzőösszege/mérete, tesztadat-jelölő megléte, `conversations` lista belső egysége; `load_samples`: sor-/darabszám, split/mód/data_kind/fixture mező, ismert és a megfelelő részhez tartozó `conversation_id`, egyedi és helyes `sample_id`, érvényes `target` tartomány, beszélgetésenkénti mintaszám a `exchanges` mezővel | `LoadExportValidationTests` (11), `SampleFileValidationTests` (9) |
| a szótár kizárólag a train részből; a validation/test ismeretlen karakterei dokumentáltan, utólagos bővítés nélkül | `build_vocab` kizárólag a train/R2 mintákból; `UNK`/`PAD` két fenntartott, a megfigyelt karakterektől külön id; `encode_text` pozíciótartó (a meglévő `tokenizer.CharTokenizer`-rel ELLENTÉTBEN nem hagyja ki az ismeretlen karaktereket - ez eltolná a célmaszkot); a jelentés részenként/módonként számolja az ismeretlen előfordulásokat és a distinct karaktereket | `VocabAndEncodingTests` (3), `ReportContentTests.test_train_r2_never_has_unknown_characters_by_construction` |
| célmaszk a célválasz karaktertartományából; illeszkedés a bemenethez és az eltolt célokhoz; előzmény/kitöltés sosem cél | `build_target_mask` + FÜGGETLEN `verify_mask_alignment` (nem a maszkképző logikáját ismétli meg); a teszt közvetlenül dekódolja a bemenet- és cél-tömböt, és összeveti az eredeti szöveggel és a célválasszal; a kötegelt (kitöltött) maszk padding-régiója sosem `1,0` | `TargetMaskTests` (5) |
| beszélgetések nem folynak össze, nem örökölnek állapotot | egy köteg-sor egy minta; minden előrefutás `hidden=None`-nal indul; két, egy kötegben futtatott minta logitjai megegyeznek a külön-külön futtatottakéval; egy B köteg eredménye független attól, hogy előtte futott-e egy A köteg | `BatchingIsolationTests` (6) |
| a száraz futás ellenőrizze a betöltést, kódolást, kötegelést, maszkokat; NINCS optimalizáló lépés/paraméterfrissítés/mentés | `run_dry_run` a teljes csővezetéket lefuttatja egy FRISS próba-modellel (`torch.no_grad()`); a forrás AST-vizsgálattal igazoltan nem tartalmaz `.backward()`/`.step()`/`torch.save`-t | `ForwardCheckTests` (a `BatchingIsolationTests`-en belül, 3 teszt); `ExistingChainUntouchedTests` (2) |
| a split_approved/content_verified/training_ready ne módosuljon | a jelentés ezeket a forrás-exportból veszi át, változatlanul (mind `false`); a manifest saját, azonos nevű mezői is `false`-ra vannak kényszerítve (sosem lehet igazra állítani ezen a kódúton) | `ReportContentTests.test_statuses_are_taken_from_the_export_unchanged_and_never_set_true`; `LoadExportValidationTests.test_a_status_flag_claiming_readiness_is_refused` |

## C. Mérés (1000 mesterséges beszélgetés, a valódi 4494 példás TE-1 exporttal szemben)

`data/reports/audit_evidence/mt5_train/benchmark_train.py`, a teljes MT-3 → MT-2 → MT-4 → MT-5 csővezetéken:

| Mutató | Érték |
|---|---|
| beszélgetés (bemenet) | 1000 |
| MT-3 / MT-2 / MT-4 futásidő | 186,75 / 12,92 / 27,81 mp |
| **MT-5 száraz futás** (a teljes ellenőrzéssel, betöltéssel, kódolással, kötegeléssel és előrefutással) | **158,45 mp** |
| szótár mérete (train/R2, +UNK+PAD) | 68 (+UNK+PAD = 70) |
| minták (train/R2), ebből a betanított modell 64 karakteres kontextusán túli | 4234/4234 (**100%** — lásd a korlátot alább) |
| visszatartott (`--max-chars` alapérték, 4096) | 0 |
| kisebb, explicit `--max-chars` (641, a hosszak 70. percentilise) mellett néhány minta visszatartva (nem csendes csonkítás) | 3178/9598 minta, mindegyik jelentett okkal |
| ismételt futás determinisztikus (a próba-modell veszteségével együtt) | igen — a második futás jelentése bájtra azonos |
| visszaolvasásos önellenőrzés | tiszta (0 probléma) |
| az MT-4 export (felsőbb réteg) a futás után érintetlen | igen |

**Kiemelt korlát**: a `samples_over_trained_context_pct` MINDEN felosztásban és MINDKÉT módban (R2 és R1 is) 100% — 1000 beszélgetésen egyetlen minta bemenete sem fér bele a jelenlegi betanított modell 64 karakteres kontextusába (az R1, futásidő-hű módban is legalább 160 karakter a legrövidebb minta). Az előrefutás technikailag mindegyik kötegen sikeres (0 hiba), de ez egy FRISS, tanítatlan próba-modellel történt; ez NEM bizonyítja, hogy a valódi, betanított ellenőrzőpont ezen a hosszon jó minőségű választ adna — ez egy, a betöltőtől független, a modell architektúrájával/tanításával összefüggő KOMPATIBILITÁSI korlát (lásd I. szakasz).

Részletes, részenkénti/módonkénti statisztika: `data/reports/audit_evidence/mt5_train/bench_result_1000.json`.

## D. Tesztek és mutációs vizsgálat

**Tesztek:** `tests.test_train_multiturn`: **83 teszt OK** (~2,3 perc). Osztályok (a mutációs vizsgálat során +8 célzott, izoláló teszttel bővült): célmaszk/`prepare_sample` önellenőrzés (12), szótár/kódolás (3), hossz-statisztika (4), kötegelés/állapot-izoláció/előrefutás (7), export-betöltés érvényesítése (16), mintafájl-érvényesítése (8), hosszkorlát/visszatartás/figyelmeztetések (5), jelentés-tartalom (8), mód/kimenet-védelem (6), futás közbeni változás/visszaolvasás (8), parancssor (4), a meglévő lánc érintetlensége (2).

**Mutációs vizsgálat:** 75 mutáns, **74 elbukik**, 1 szándékosan elfogadott, indokolt ekvivalens túlélő (`forward_check_carries_hidden` — a `hidden=None` kifejezett argumentum eltávolítása a `CharLSTM.forward` saját alapértelmezése miatt bizonyíthatóan azonos viselkedésű, semmilyen teszttel meg nem különböztethető). Minden mutáns egy szándékosan elrontott szabály a modul másolatában (bemenet-ellenőrzés, célmaszk, szótárépítés, kötegelés, kompatibilitási próba, hossz-/visszatartás-jelentés, figyelmeztetések, kimenet-védelem, determinizmus, visszaolvasás, parancssor); a `tests.test_train_multiturn` `unittest -f` (első hibánál megáll) móddal fut ellene, 4 független, folyamatállapot/kilépési kód alapján követett háttérszeleten. Részletek: `data/reports/audit_evidence/mt5_train/mutation_results.txt`.

**Regresszió:** `tests.test_train_multiturn` + `test_multiturn_export` + `test_multiturn_split` + `test_multiturn_dedupe` + `test_multiturn_validate` + `test_te1_dataset_export` + `test_te2_chat_text`: **398 teszt OK** (529,8 mp, kilépési kód 0); `tests.test_v1_7_4_dataset_foundation`: STABIL (a szkript saját kilépési kódja 0).

## E. Milyen bemeneten történt az ellenőrzés

* **Mesterséges tesztadat**: a `tests/test_multiturn_split.py` generátora — valós magyar szavakból összeállított **értelmetlen mondatok** (`mtfx_syn_NNNN`, `meta.fixture: true`), a teljes MT-3 → MT-2 → MT-4 csővezetéken keresztül. Szerkezetileg érvényesek, de tartalmilag nem beszélgetések; az 1000 beszélgetéses csomagba nem számítanak, tanításra nem használhatók.
* A **valódi TE-1 export** (4494 példa, a hat kizárás érvényesítve) mint az MT-3/MT-2/MT-4 csővezeték referenciája, csak olvasva; a `data/` a mérés előtt és után bájtra azonos.
* **Valódi többfordulós adaton nem futott**, mert nincs.

## F. Pontosan mire vonatkozik a STABIL minősítés

**STABIL** = a `src/train_multiturn.py` (mt5-1.0) **működése** a fenti mesterséges/szintetikus bemeneteken: a 83 teszt, a mutációs vizsgálat (75 mutánsból 74 elbukik, 1 dokumentált ekvivalens) és a mérés (visszaolvasás, ismételhetőség, a felsőbb export érintetlensége) sikeres, a regresszió (398 teszt) és a foundation teszt is STABIL. **Nem vonatkozik**: valódi többfordulós adat minőségére; arra, hogy az R1 vagy az R2 alkalmas-e tényleges tanításra; a hosszú kontextus tényleges megtanulására (ezt a modul KIFEJEZETTEN nem állítja - csak a betöltés/kódolás/kötegelés/előrefutás technikai sikerét igazolja); arra, hogy a jelenlegi betanított modell (64 karakteres kontextus) képes lenne-e minőségi választ adni a mintákon (lásd a C. szakasz kiemelt korlátját - ez a modell architektúrájának/tanításának, nem a betöltőnek a korlátja); training-ready állapotra.

## G. Ami bizonytalan vagy nyitott

* A `--max-chars` alapértéke (4096) technikai, nem valódi adaton kalibrált védőkorlát.
* A kompatibilitási próba egy FRISS, véletlen inicializált modellel fut; a kiszámított veszteség-érték tartalmilag értelmezhetetlen (csak alak-/futás-ellenőrzés).
* Nem dönt abban, hogy a tényleges tanítás R1-et, R2-t, vagy mindkettőt használja-e, sem az ablak-/szekvenciahossz kezelésében: ez külön feladat és jóváhagyás.
* Az ismeretlen karakterek kezelése a train-szótárhoz képest történik; ha a train rész maga sem fedi le a nyelv teljes karakterkészletét, ez sok ismeretlen karaktert eredményezhet.
* Valódi többfordulós adaton (a fixture teszteken és a mesterséges mérésen túl) nem futott, mert még nincs.

## H. Mi kell az első 50 valódi tanítóbeszélgetéshez

Az MT-0, MT-1, MT-3 (jóváhagyott döntésekkel), MT-2, MT-4 és MT-5 technikai lánc **kész és tesztelt**. Az első 50 beszélgetés (`claude_multiturn_0001_0050`) elkészítéséhez:
1. **Kifejezett jóváhagyás** a generálás megkezdésére (az MT-6 kapu technikailag teljesült, de a generálás önmagában külön döntés).
2. **A nyitó váltások változatossága**: az MT-3 revideált szabálya szerint két beszélgetés azonos nyitó váltása mintaszinten `reject`, és nem menthető fel — ezt figyelembe kell venni a generálásnál.
3. A terv 7. szakasza szerinti összetétel (család-kvóták, hossz, téma, tervezett változat-párok) és a 6. szakasz ellenőrzései (séma, PII, tartalom, előzmény-függés, viselkedés, duplikáció, felosztás, eloszlás).
4. Utána a teljes kapu-lánc: MT-1 → MT-3 → MT-2 → MT-4 → (MT-5 dry-run, ha a tanítás bemenetének technikai próbájára is szükség van) → teljes kézi átolvasás → jelentés.

## I. A tanítás előtt még hiányzó feladatok

* **A tényleges tanítás bemenetének kiválasztása** (R1/R2, ablak-/szekvenciahossz-kezelés) és a tanítás megindításának kifejezett engedélye — ez MAGA a tanítás, nem az MT-5 száraz futás; külön feladat.
* **TE-3** — az 1–6. csomag egyfordulós adatának globális, csoport-/közeli-változat-tudatos felosztása (a TE-2 export nem oszt fel); az MT-2 `export_links.json` kapcsolatait figyelembe véve.
* **Nyitott tartalmi ellenőrzések:** a 6. csomag korlátozott lezárása (6 kizárt sor: `0220`, `0829`, `0849`, `0864` jogi átnézésre, `0602`, `0898` forrásra vár); 10 nem forrásolt E-sor; 7 hedge-elt, forrás nélküli szám; 39 előtag nélküli kontraszt-sor újracímkézése; 14 ismétlődő `kind` címke; **független emberi/szakértői átolvasás** az egész korpuszra; az 1–5. csomag kibővített céljának tartalmi lefedettségi auditja; a 7–10. csomag (és az 1–5. csomag hiányzó adatának) generálása külön jóváhagyással.
* **D-1** — a futásidejű előzmény-mélység (1 váltás) és az R3 „arany összefoglaló” döntése (webapp/backend módosítás csak külön jóváhagyással).
* Az első 50 beszélgetés generálása (MT-6 kapu) kifejezett jóváhagyással — a nyitó váltásokat változatosan kell megírni.
* A felosztás és az export jóváhagyása, és a tanítás kifejezett engedélye.
