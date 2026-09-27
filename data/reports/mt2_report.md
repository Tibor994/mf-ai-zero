# MT-3 revízió (mt3-2.0) és MT-2 (csoport-tudatos felosztás) — jelentés

Dátum: 2026-09-27. Eszközök: `tools/multiturn_dedupe.py` (**mt3-2.0**, revideálva) és `tools/multiturn_split.py` (**mt2-1.0**, új). Tesztek: `tests/test_multiturn_dedupe.py` (75), `tests/test_multiturn_split.py` (70). Dokumentáció: `docs/MULTITURN_DEDUPE.md`, `docs/MULTITURN_SPLIT.md`. Bizonyítékok: `data/reports/audit_evidence/mt3_dedupe/`, `data/reports/audit_evidence/mt2_split/`.

Nem történt tanítás és nem készült valódi tanítóadat vagy valódi többfordulós beszélgetés. A tanító-, chat-, webapp/backend-kód, a `src/` és a korábbi eszközök (`tools/dataset_*.py`, TE-1, TE-2, MT-1) **nem módosultak**; a `git diff` csak az MT-3 eszközt, tesztjét, dokumentációját és a bizonyítékokat érinti, az MT-2 fájlok újak. A hat kizárás érvényben maradt (TE-1: 4500 sor beolvasva, 6 kizárva, 4494 exportálva — a valódi exporttal futó tesztek is ezt ellenőrzik). Semmilyen adat nem lett training-ready; a felosztás **nem jóváhagyott** (`split_approved: false`).

## 0. A kiinduló állapot ellenőrzése a tényleges repóval

| Állítás | Ellenőrzés | Eredmény |
|---|---|---|
| a legutóbbi commit `d252935` (`v1.13.20-mt3-dedupe`) | `git log`, `git rev-parse HEAD origin/main` | egyezik (HEAD = origin/main) |
| 4500 clean sor, 6 kizárt, 4494 exportált | a `data/clean/*.jsonl` sorainak megszámolása; a TE-1 export a valódi adaton | **4500**; **6 kizárva, 4494 exportálva** (a mérések és a valós-export tesztek is így futottak) |
| valódi többfordulós adat nincs | `data/raw|clean|rejected|inbox` alatt `*multiturn*` | **nincs** (tesztelt: mind az MT-3, mind az MT-2 valós-adatos tesztje ellenőrzi) |
| a korábbi eszközök működése | TE-1 35, TE-2 36, MT-1 29 teszt; `tests.test_v1_7_4_dataset_foundation` | mind OK, STABIL |

Eltérés a kérés és a repó között nem volt; az elnevezés („Nextora”) a kérésben, a repóban „Nexora”/„MF-AI-Zero” szerepel (az MT-1 mindkét írásmódot elutasítja a beszélgetés-szövegben).

## A. Az MT-3 revíziója a döntéseid szerint (mt3-2.0)

Az öt megfeleltetést az általad megadott szabályok szerint módosítottam; a kézikönyvi számok (0,90 / 0,95) változatlanok, parancssorból nem módosíthatók.

| # | A döntésed | Az eszközben (mt3-2.0) | Tesztelés |
|---|---|---|---|
| 1 | **küszöbhatárok**: szó szerinti „fölött”, pontos egyezés külön szabály; régi eszközök változatlanok | alap: szigorú `>` (0,90 fölött `review`, 0,95 fölött `reject`); a pontosan 0,90 → `near_variant` (beszélgetés) / `sample_at_boundary` (minta) `info`, a pontosan 0,95 → `review`; a pontos egyezés külön szabály (`reject`); a régi `>=` határt csak a `--inclusive-boundaries` adja (a `--handbook-strict` megszűnt); a jelentés `config.decision_rules.comparison` értéke rögzíti | igazságtábla (0,89 / 0,90 / 0,9001 / 0,9499 / 0,95 / 0,9501 / pontos) mindkét módban; minta-szint 0,89–0,96 mindkét módban, előszűrővel és a nélkül; beszélgetés-szint pontosan 0,90 mindkét módban; **előszűrt és teljes összehasonlítás azonos** 2 seed × 2 mód mellett is (a 0,90/0,95 határra tervezett párokkal) |
| 2 | **rövid szövegek**: a hasonlósági kivétel dokumentált, kísérleti megoldás; a közös köszönés nem teszi duplikálttá a beszélgetést; a teljes, előzménnyel együtt azonos minta hossztól függetlenül elutasítandó; bizonytalan → `review` haladási tiltással | pontos azonos minta (kérdés, válasz **és** előzmény) hossztól függetlenül `sample_exact` `reject` (nem menthető fel); a 60 karakter alatti hasonlóság (`sample_near_short`) csak `review` (bármelyik oldal rövid elég), sosem `reject`, pontosan 0,90-nél `info`; a rövid találat csoportot nem köt; a beszélgetés-szint független (`conversation_decision` nem `blocked`) | pontos minta mind a négy esetben (rövid/hosszú × előzménnyel/anélkül); rövid hasonló 0,95 és 0,98 fölött is csak `review`; azonos kérdés+válasz kissé eltérő előzménnyel nem pontos; közös köszönés két beszélgetésben: beszélgetés-szint nulla találat, minta-szint `reject`; a rövid találat nem csoportosít |
| 3 | **átfogalmazás**: a 0,35-ös szóátfedés kiegészítő, kísérleti `review`-jelzés; nem helyettesíti az átolvasást; hiánya nem bizonyít egyediséget; a 8/10 csak a konkrét tesztkészletre | megmaradt; `details.experimental: true`, a jelzés szövege „KÍSÉRLETI … nem helyettesíti a tartalmi átolvasást”; `summary.experimental_signals` számolja; a `config.experimental`, a korlátok és a `docs/MULTITURN_DEDUPE.md` 4. szakasza rögzíti | a jelzés tulajdonságai, számlálása és a jelentés-mezők tesztelve |
| 4 | **névcsere**: a névsemlegesített egyezés kiegészítő jelzés; az eredeti szöveg megmarad; a szereplők/kapcsolatok változása dokumentálandó; puszta névcsere nem új képesség | a döntés az **eredeti (névvel együtti)** szövegen születik; a névsemleges menet csak a nevet tartalmazó párokon fut, és csak akkor ad `name_swapped_match` / `sample_name_swapped` **`review`** jelzést, ha a nyers nézeten nincs döntési szintű találat; sosem `reject`/elfogadás; a jelzés rögzíti a nyers és a névsemleges pontszámot, a neveket és az **eredeti** üzeneteket; a jelzés szövege: a puszta névcsere nem új képesség, javítás vagy dokumentált indok kell | nyersen 0,95 fölötti névcserés másolat: a nyers nézeten `reject`, nincs kettős jelzés; névlistás pár (nyersen 0,84, névsemlegesítve 1,0): jelzés `review`, az eredeti szövegek betűre azonosak a jelentésben; `--no-name-normalization`; név nélküli pároknál a menet nem fut; előszűrt = teljes összehasonlítás a névsemleges menetre is |
| 5 | **deklarált változatok**: a közös `split_group` nem írja felül a döntést; > 0,95 csak dokumentált tartalmi indokkal kaphat kivételt; nyers pontos másolat `reject`; a csoportazonosító nem felmentés | a lefokozás **megszűnt**; a deklarált változat is `reject` (`details.declared_variant` csak tájékoztató); reject-szintű felmentéshez kötelező a dokumentált `capability` mező (≥ 15 karakter), review-szinten elég a `reason`; nem menthető fel: `duplicate_id`, `exact_conversation`, `exact_after_normalization`, `sample_exact`; a `"*"` ezeket nem érinti | deklarált és nem deklarált változat azonos döntést kap (mind a beszélgetés-, mind a minta-szinten); `capability` nélkül, rövid `capability`-vel, csoportra hivatkozó indokkal hiba; a négy nem menthető típus `capability` mellett is hibát ad; a kivétel a csoportosítást nem szünteti meg |

**Az MT-2 miatt szükséges, kérdezés nélküli kiegészítés (nem döntés-módosítás):** az MT-3 jelentés most rögzíti az MT-3 eszköz fájljának ellenőrzőösszegét (`tool_sha256`) és rekordonként a forrássor ellenőrzőösszegét (`line_sha256`), mert az MT-2 ezekre támaszkodva ismeri fel az elavult jelentést.

**Mérések és bizonyítékok (mt3-2.0):**
* Tesztek: **75** (volt 59). Mutációs vizsgálat: **82 mutáns, mind elbukik** — az első futásban 81-ből 77 bukott el, a 4 túlélő miatt 4 új teszt készült (konverzáció-szintű névcsere-jelzés csoportosít önmagában; a pár rövid, ha bármelyik oldal rövid; azonos kérdés+válasz kissé eltérő előzménnyel közeli, nem pontos minta; a névsemleges menet csak a nevet tartalmazó párokat érinti), az új `tool_sha256` mutánssal együtt 82/82 (`mutation_results_mt3_v2.txt`).
* Futásidő (1050 szintetikus beszélgetés a valódi 4494 példás exporttal szemben, egy folyamat, **ugyanazon a gépen egymás után mérve**): mt3-1.0 **89,0 mp**, mt3-2.0 **97,9 mp** (+10%; ebből a kiegészítő névsemleges menet 4,4 mp). Az összehasonlított párok száma azonos (550 705 beszélgetés-pár, 9,43 M minta-pár). A korábbi jelentésben szereplő 60,1 mp más géphelyzetben készült, a két érték nem összehasonlítható.
* Beültetett esetek (mt3-2.0, ugyanaz a szintetikus terhelés): pontos másolat 10/10, normalizálás utáni másolat 10/10, közeli változat 10/10, exportált példával azonos első forduló 10/10, átfogalmazás-szerű változat **8/10 — ez csak erre a konkrét szintetikus tesztkészletre vonatkozik**, a heurisztika hiánya nem bizonyít egyediséget.
* Frissített bizonyítékok: `demo_scenarios.jsonl` és `demo_scenarios_report.json` (15 mesterséges forgatókönyv, köztük névlistás pár, deklarált változat, közös köszönés), `fixtures_vs_real_export_report.json` (5 fixture a valódi exporttal szemben: 0 találat, 0 blokkolt rekord), `benchmark_results_1000_mt3v2.json` és a vele azonos munkamenetben mért `…_mt3v1_same_session.json`.

**Új megfigyelés a kísérleti heurisztikáról (szintetikus adaton mérve):** véletlenszerű, szűk szókincsű beszélgetéseken a 0,35-ös szóátfedés hamis pozitívot ad. 150 mesterséges beszélgetésnél (valós magyar szavakból összeállított értelmetlen mondatok) 536 szavas szókincs mellett **52** párra jelzett és 33 beszélgetést blokkolt; 2291 szavas szókincs mellett **0** találat. A valódi beszélgetéseken a viselkedés ismeretlen; ezért marad a jelzés csak `review`, és ezért használ az MT-2 tesztkorpusza a nagyobb szókincset. Az érték újrakalibrálandó, ha valódi adat lesz.

**Amire figyelni kell (a döntéseid közvetlen következménye):** két beszélgetés azonos nyitó váltása (pl. „Szia!” / „Szia! Miben segíthetek?”) mintaszinten `reject`, és nem menthető fel. A generálásnál a nyitó váltásokat változtatni kell; enélkül az első batchekben tömeges blokkolás várható.

## B. MT-2 — csoport-tudatos, reprodukálható felosztás

**Fájlok (mind új):** `tools/multiturn_split.py`, `tests/test_multiturn_split.py`, `tests/fixtures/multiturn/synthetic_vocabulary.txt` (2191 gyakori magyar szó a mesterséges tesztadathoz), `docs/MULTITURN_SPLIT.md`, `data/reports/audit_evidence/mt2_split/`.

**Működés röviden** (részletesen: `docs/MULTITURN_SPLIT.md`): bemenet az MT-1-validált beszélgetés-fájlok és az **aktuális** MT-3 jelentés; az egység az MT-3 **számított** csoportja (kiegészítve a dokumentált kivétellel felmentett párokkal); a 2+ tagú egységekre pontos, bitkészletes dinamikus programozás adja a legkisebb eltérésű validation/test darabszámot, az 1 tagú egységek pontos minimumú kitöltéssel egészítik ki; a konkrét kijelölés sha256-alapú, a bemeneti sorrendtől független; a rétegzés (család, hosszsáv, domain, „nehéz”) azonos méretű egységek cseréje; a végén független ellenőrzés fut a nyers adaton.

| A kérésed | Megvalósítás | Teszt |
|---|---|---|
| minden forduló egy részben; csoport egy részbe | az egység oszthatatlan; a kimenet-ellenőrzés a manifestből, az MT-3-tól függetlenül is újraszámolható | csoport-integritás deklarált csoportra, persona-hármasra, 5 tagú váltakozó (deklarált–persona) láncra, 12 tagú csoportra; sok csoport a kis részekhez képest; 6 különböző seed |
| MT-3-mal kötött és terv szerinti persona-változatok együtt | az MT-3 csoportjait használja; a deklarált `split_group` és `persona` kapcsolatot külön ellenőrzi (elvágott kapcsolat = elavult jelentés); a kivétellel felmentett párt egy egységbe vonja | lásd fent; rövid, kivétellel felmentett pár egy egységbe kerül akkor is, ha az MT-3 nem kötötte össze |
| TE-1 exporttal talált kapcsolatok megőrzése a TE-3-hoz; nincs észrevétlen átfedés részek között | `export_links.json` (kapcsolat-erősség, `required_split`, ütközés, függő egység) és `cross_split_overlaps.tsv` (az MT-3 minden, részek között megosztott párosa); döntési szintű, részek között megosztott fel nem oldott páros belső hiba | egységtesztek (ütközés, függő, fordított sorrend); valós MT-3 jelentéssel részleges átfedés és kivétellel felmentett egyezés; a `tsv` pontosan egyezik a nyers újraszámolással |
| fel nem oldott review/reject és kizárt rekord nem kerül kijelölésre | MT-3 blokkolt rekord → **az egész egység** visszatartva; kizárási lista, `quality_notes` kizárás-jelölés, TE-1 kizárt azonosító-ütközés → a rekord visszatartva (a csoporttárs kijelölhető, a rekord `reserved_split`-et kap); mind okkal, a `held_back.tsv`-ben | blokkolt pár + persona-társ, fel nem oldott review, felmentett review, kizárási lista (hibás formák is), jelölés, azonosító-ütközés, minden rekord blokkolt |
| a csoport-integritás előbbre való a pontos darabszámnál; eltérés jelentése | a DP a legkisebb összeltérést adja; nem elérhető cél esetén `deviation` (terv és ideális ellen), figyelmeztetés, 1-es kilépési kód; a cél skálázása legnagyobb maradékkal | 4×3 tagú csoport 8/2/2-re: eltérés 4, minden rész 3 többszöröse; nagy csoport a train részbe; **brute-force összevetés 60 véletlen kis példán** (a DP optimuma egyezik); a `best_fill` 400 véletlen esetben pontos minimum |
| bemenetek, beállítások, csoport-tagság, kijelölés ellenőrzőösszege | `split_manifest.json`: bemenetek sha256 (beszélgetés-fájlok, MT-3 jelentés és eszköz, TE-1 export, kizárási lista, névtár), beállítások, egységek tagsága, rekordonként fájl/sor/sor-sha256/egység/rész, `assignment_sha256`, `groups_sha256`, kimeneti fájlok sha256 | tartalom-ellenőrzés; `--verify-manifest` a bemeneteket és kimeneteket ellenőrzi, majd **újraszámolja a kijelölést** és összeveti (15: változás, 18: nem reprodukálható) |
| megváltozott bemenet vagy elavult MT-3 jelentés nem használható csendben | az MT-3 jelentés verziója, az eszköz fájljának sha256-ja, a küszöbök, a bemenetek, a fájlok és rekordok (sor-sha256), a csoport-tagság önkonzisztenciája, a TE-1 összevetés megléte ellenőrzött; futás közbeni változás 16-os hiba | régi verzió, hiányzó/hibás `tool_sha256`, elvágott csoport, más fájl, hiányzó rekord, sor-sha, megváltozott export, TE-1 nélküli jelentés (csak kifejezett kapcsolóval, figyelmeztetéssel), futás közbeni változás |
| csoport-elválasztás, ismételhetőség, kizárások, nem elérhető darabszám tesztelése | lásd fent | ismételt futás azonos; más rekord-/fájlsorrend azonos; más seed más kijelölés, azonos darabszám; nincs Python `random`/hash-véletlenítés (`PYTHONHASHSEED` teszt) |

**Mérés (1000 mesterséges beszélgetés, a valódi 4494 példás TE-1 exporttal szemben; `audit_evidence/mt2_split/`):**

| Mutató | Tiszta korpusz | Beültetett blokkolt másolatokkal (12) és 6 kizárt beszélgetéssel |
|---|---|---|
| bemenet | 1000 beszélgetés, 853 egység (95 többtagú), 0 MT-3 blokkolt rekord | 1012 beszélgetés, 24 blokkolt rekord |
| kijelölt / visszatartott | 1000 / 0 | 970 / 42 (24 `mt3_blocked`, 12 `group_has_blocked_member`, 6 `excluded_list`) |
| részek (beszélgetés) | **800 / 100 / 100** — pontosan a terv | 776 / 97 / 97 — az arányosan skálázott ideális darabszám, pontosan teljesítve (a tervtől −24/−3/−3, jelezve) |
| üzenet (train / val / test) | 8486 / 1074 / 1052 | 8214 / 1032 / 1032 |
| minta (train / val / test), ebből első fordulós + előzmény-függő | 4243 / 537 / 526 (800+3443, 100+437, 100+426) | 4107 / 516 / 516 |
| szétvágott egység (független ellenőrzés) | **0** | **0** |
| részek közötti átfedés-pár | 0 | 0 |
| „nehéz” beszélgetés a teszt részben (minimum 30) | 40 | 39 (a minimum 30) |
| rétegzési veszteség (χ²-szerű) | 38,4 → 0,36 (59 csere) | 38,0 → 0,51 |
| futásidő | MT-3 125 mp; MT-2 10 mp (számítás 2,6 mp) | MT-3 129 mp; MT-2 11 mp |
| ismételhetőség | második futás azonos; más seed más kijelölés, azonos darabszámmal; `--verify-manifest` újraszámolva rendben | ugyanez |

A beültetett esetben mind a 12 másolat és eredetijük, valamint a másolatok persona-társai visszatartva, a 6 kizárt beszélgetés sem szerepel a kijelölésben, a maradékra arányosan skálázott cél teljesült.

**Tesztek és mutációs vizsgálat:** `tests.test_multiturn_split`: **70 teszt OK** (~2,5 perc; többségük valódi TE-1 export és valódi MT-3 futás a mesterséges beszélgetéseken). Mutációs vizsgálat: **83 mutáns, mind elbukik**. Az első futásban 82-ből 77 bukott el; 5 túlélő maradt: négy valódi teszthiány (a kizárási lista hibaüzenetének tartalma; a közös deklarált csoport kapcsolatának elvágása az MT-3 jelentésben; a rögzített TE-1 manifest-ellenőrzőösszeg közvetlen ellenőrzése; a maradékos skálázás döntetlen-szabálya) — ezekre új teszt készült; egy pedig **egyenértékű mutáns** volt (a `best_fill` három töréspont-egyenese mindig ugyanabban a pontban metszi egymást, ezért a jelölt-lista redundáns elemet is tartalmazott): a jelölt-listát egyszerűsítettem, így a mutáns már nem egyenértékű, és elbukik. Az új TE-1-figyelmeztetés mutánsával együtt 83/83 (`mutation_results.txt`).

**Regresszió:** `tests.test_multiturn_dedupe` + `test_multiturn_split` + `test_multiturn_validate` + `test_te1_dataset_export` + `test_te2_chat_text`: **245 teszt OK** (`-W error::ResourceWarning` mellett is); `tests.test_v1_7_4_dataset_foundation`: STABIL.

## C. Milyen bemeneten történt az ellenőrzés

* **Mesterséges tesztadat** (a valódi 1000 beszélgetés nem létezik): az MT-3 fixture-ökből átalakított beszélgetések és a `tests/test_multiturn_split.py` generátorával valós magyar szavakból összeállított **értelmetlen mondatok** (`mtfx_syn_NNNN`, `meta.fixture: true`), MT-1-validálva fixture módban. Ezek szerkezetileg érvényesek, de tartalmilag nem beszélgetések; az 1000 beszélgetéses csomagba nem számítanak, tanításra nem használhatók.
* A **valódi TE-1 export** (4494 példa, a hat kizárás érvényesítve) mint referencia, csak olvasva; a `data/` a tesztek előtt és után bájtra azonos, `*multiturn*` fájl nincs.
* **Valódi többfordulós adaton nem futott**, mert nincs.

## D. Pontosan mire vonatkozik a STABIL minősítés

**STABIL** = a `tools/multiturn_dedupe.py` (mt3-2.0) és a `tools/multiturn_split.py` (mt2-1.0) **működése** a fenti mesterséges és szintetikus bemeneteken és a valódi TE-1 exporttal szemben: a tesztek (75 + 70; az összes új eszköz-tesztkészlet 245) sikeresek, a mutációs vizsgálatok (82/82 és 83/83), az előszűrés a teljes összehasonlítással azonos, a bemenet-védelmek, az elavult-jelentés felismerése, a determinizmus és a kimenetek visszakövethetősége működnek; a foundation regresszió STABIL. **Nem vonatkozik** valódi többfordulós adat minőségére, tartalmi helyességre, természetességre, a kijelölt felosztás jóváhagyására, az 1000 beszélgetés bármelyikének elfogadására, a kísérleti heurisztikák valódi adaton való pontosságára, vagy training-ready állapotra.

## E. Ami bizonytalan vagy nyitott

* A kísérleti jelzések (rövid szöveg, paraphrase, névsemleges) valódi adaton nem mértek; a paraphrase-küszöb hamis pozitívot adhat szűk szókincsű szövegen (lásd A. rész).
* A csoportok szöveges hasonlóságon és deklarált kapcsolatokon alapulnak: a jelentésben azonos, de szövegben eltérő beszélgetések külön csoportba, így külön részbe kerülhetnek; az információ-szintű átfedések csak listázva vannak (nem kötnek csoportot).
* A visszatartási szabály konzervatív: egy blokkolt rekord az egész csoportját visszatartja. Sok blokkolt rekordnál a kijelölhető darabszám jelentősen csökkenhet; ilyenkor a cél arányosan skálázott (jelezve).
* A rétegzés legjobb szándékú lokális keresés; kis mintán vagy sok nagy csoportnál az összetétel eltérhet az arányostól (a csoport-integritás előbbre való).
* A „nehéz” jelző definíciója (előzmény-mélység ≥ 2 vagy család F4/F7) az én értelmezésem a tervből; a 30/100 minimum a teszt-darabszám 30%-ára skálázódik.
* A TE-3 (egyfordulós adat felosztása) még nem létezik; az `export_links.json` kapcsolatai a TE-3 majdani egyeztetését készítik elő.
* A TE-1 kizárt hat sor tartalma nincs benne a hasonlósági referenciában (csak azonosító-ütközést vizsgálunk).
* Ha az MT-3 eszköz bármely módosul, a jelentést újra kell futtatni az MT-2 előtt (a `tool_sha256` miatt): ez szándékos védelem, de fejlesztés közben kényelmetlen.

## F. A következő konkrét lépés és a tanítás előtt még hiányzó feladatok

**Következő lépés (a te döntésedre):** az **MT-4** (`tools/multiturn_export.py`: renderelés és exportálás kizárási szűrővel, csak a felosztott, MT-1-validált és MT-3-ellenőrzött bemenetből) jóváhagyása — ez az MT-2 manifesztre épül. A 7. csomag adatgenerálása (az első 50 beszélgetés) továbbra is külön, kifejezett jóváhagyást kér; a nyitó váltások változatosságára (A. rész) ekkor figyelni kell.

**A tanítás előtt még hiányzik:**
* **MT-4** — renderelés (R1/R3/R2) és exportálás kizárási szűrővel; a képzett minták száma; a csoport egy részbe kerül.
* **MT-5** — többfordulós tanító betöltő (csak betöltés és száraz futás), mintánkénti kódolás, veszteség-maszk; a v0.7 tanító érintetlen.
* **TE-3** — az 1–6. csomag egyfordulós adatának globális, csoport-/közeli-változat-tudatos felosztása (a TE-2 export nem oszt fel); az `export_links.json` kapcsolatait figyelembe véve.
* **Nyitott tartalmi ellenőrzések:** a 6. csomag korlátozott lezárása (6 kizárt sor: `0220`, `0829`, `0849`, `0864` jogi átnézésre, `0602`, `0898` forrásra vár); 10 nem forrásolt E-sor; 7 hedge-elt, forrás nélküli szám; 39 előtag nélküli kontraszt-sor újracímkézése; 14 ismétlődő `kind` címke; **független emberi/szakértői átolvasás** az egész korpuszra; az 1–5. csomag kibővített céljának tartalmi lefedettségi auditja; a 7–10. csomag (és az 1–5. csomag hiányzó adatának) generálása külön jóváhagyással.
* **D-1** — a futásidejű előzmény-mélység (1 váltás) és az R3 „arany összefoglaló” döntése (webapp/backend módosítás csak külön jóváhagyással).
* A felosztás jóváhagyása és a tanítás megindításának kifejezett engedélye.
