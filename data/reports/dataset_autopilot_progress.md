# Nexora Zero Dataset Autopilot - haladáskövetés

Ez a fájl az AUTOPILOT v2 (szigorú felügyelt mód) folyamat állapotát követi.
**Minden batch után frissül.** Nem tartalmaz commit/push/tanítás-előzményt
azon túl, ami ténylegesen megtörtént - ez egy élő állapotjelentés, nem terv.

## Globális célösszesítő (a jóváhagyott, teljes 17 000 soros terv, 10 csomag)

**A korábbi csomagok kezdő adagjainak elkészülte nem jelenti a kibővített céljuk teljesülését.** (A régi 9 csomagos, 4900 soros roadmap számozása és célja nem irányadó; a lenti csomag-szakaszok a kezdő adagok története.)

| # | Csomag | Terv | Clean (tény) | Teljesítés | Hiányzik | Státusz |
|---|---|---|---|---|---|---|
| 1 | Magyar hétköznapi tudás (simple_qa) | 3000 | 1000 | 33,3% | 2000 | kezdő adag kész, auditált; **cél nem teljesült** |
| 2 | Magyarázós/tanítós válaszok (explanation) | 3000 | 1000 | 33,3% | 2000 | kezdő adag kész; **cél nem teljesült** |
| 3 | Lépésenkénti feladatmegoldás (step_by_step) | 2000 | 500 | 25,0% | 1500 | kezdő adag kész; **cél nem teljesült** |
| 4 | Összegzés és átfogalmazás (summary) | 2000 | 500 | 25,0% | 1500 | kezdő adag kész; **cél nem teljesült** |
| 5 | Hibás felhasználói szöveg értése (noisy_input) | 2000 | 500 | 25,0% | 1500 | kezdő adag kész; **cél nem teljesült** |
| 6 | Bizonytalanság / forráskérés (uncertainty_source_request) | 1000 | 1000 (6 kizárt) | 100% (darabszám) | 0 | **korlátozott lezárás**, nem teljesen ellenőrzött, nem training-ready |
| 7 | Többfordulós beszélgetés (multiturn) | 1000 | 0 | 0% | 1000 | csak terv (`multiturn_package7_plan.md`); nem kezdődött |
| 8 | Személyiség/stílus adaptáció | 1000 | 0 | 0% | 1000 | nem kezdődött |
| 9 | Safety/határok | 1000 | 0 | 0% | 1000 | nem kezdődött |
| 10 | Nextora saját tudás | 1000 | 0 | 0% | 1000 | nem kezdődött (repo-alapú, kitalálás tilos) |
| | **Összesen** | **17 000** | **4500** | **26,5%** | **12 500** | |

**TE-1 (kész, `v1.13.18`):** `tools/dataset_export_train.py` + `tests/test_te1_dataset_export.py` (35 teszt): a kizárási lista tényleges érvényesítése (6 sor kizárva, 4494 exportálható), visszakövethető manifesttel; a clean fájlok változatlanok. **Nem** tartalmi ellenőrzés és **nem** training-ready. A jelenlegi tanító (`train_chat.py`) nem olvassa az exportot; TE-2 (tanítószöveg-konverzió) és a többfordulós MT-0…MT-5 feladatok jóváhagyásra várnak. Riport: `data/reports/te1_export_report.md`.

**TE-2, MT-0, MT-1 (kész, `v1.13.19`):** `tools/dataset_export_chat_text.py` (TE-1 exportból előkészítő `User:/AI:` szöveg, veszteségmentesség-őrzéssel, a tényleges `train_chat` függvényekkel tanítás nélkül ellenőrizve; valós adaton 4494 blokk, 0 visszatartott; NEM felosztás), `docs/MULTITURN_FORMAT.md` + `tools/multiturn_name_bank.json` + `tests/fixtures/multiturn/` (5 mesterséges tesztbeszélgetés, nem az 1000-es csomag része), `tools/multiturn_validate.py` (minden üzenetet vizsgál; a régi-validátor-kompatibilis és a turns-validált állapot külön; közbenső üzenetben lévő hibát a régi validátor átenged, az MT-1 elutasít). 100 új teszt sikeres; mutációs vizsgálat: MT-1 33/33, TE-2 lényegében teljes. Technikai kompatibilitás (egyfordulós): igazolt; tartalmi ellenőrzés: nincs lezárva; tanítási engedély: nincs. Riport: `data/reports/te2_mt01_report.md`. Következő: MT-3 (beszélgetés-szintű duplikáció és csoportképzés).

**MT-3 (kész, `v1.13.20`):** `tools/multiturn_dedupe.py` + `tests/test_multiturn_dedupe.py` (59 teszt) + `docs/MULTITURN_DEDUPE.md`: azonosító-, beszélgetés-, minta- (előzménnyel) és a TE-1 export (4494 példa) elleni duplikáció-ellenőrzés, részleges egyezés külön a valóban ismétlődő tanítási mintától, reprodukálható csoportazonosító (`mtg_<legkisebb rekordazonosító>`, egyszeres kötés, láncolt hasonlóság egy csoport), kivétel-mechanizmus, bemenet-ellenőrzőösszegek. A kézikönyvi 0,90/0,95 szabályok változatlanok (parancssorból nem módosíthatók); a mérőszám: SequenceMatcher egyező-karakter arány normalizált szövegen (nem jelentés-azonosság); a megfeleltetések (`>=`/`>`, rövid minta, paraphrase-heurisztika) jóváhagyásra várnak. Előszűrés bizonyítottan pontos, a teljes összehasonlítással azonos; szintetikus 1050 beszélgetés vs 4494 export: 60,1 mp; mutáció 46/46. Elkülönített tesztadat; valódi többfordulós adat nincs; nem training-ready. Riport: `data/reports/mt3_report.md`. Következő: MT-2, MT-4, MT-5, TE-3, tartalmi lezárás; az első 100 beszélgetés generálása csak jóváhagyással.

**MT-3 revízió (mt3-2.0, `v1.13.21`) és MT-2 (kész, `v1.13.22`):** az MT-3 a felhasználó öt döntése szerint módosult: szigorú `>` határ alapból (`--inclusive-boundaries` a régi `>=`), a pontos ismétlődő minta hossztól függetlenül `reject`, a rövid szöveg hasonlósági kivétele és a paraphrase-heurisztika kísérleti `review`, a névsemlegesített egyezés kiegészítő `review` (eredeti szöveg megőrizve), a közös `split_group` nem írja felül a döntést, reject-szintű kivételhez dokumentált `capability` kell; 75 teszt, 82/82 mutáns. MT-2 (`tools/multiturn_split.py`, 70 teszt, 83/83 mutáns, `docs/MULTITURN_SPLIT.md`): az MT-3 számított csoportjaira és aktuális jelentésére (verzió, eszköz-sha256, sor-sha256) épülő, csoportot sosem szétvágó, sha256-alapú, sorrendtől független felosztás; blokkolt rekord/csoport és kizárt rekord nem kerül kijelölésre; pontos darabszám-optimalizálás; `export_links.json` a TE-3-hoz; `--verify-manifest` újraszámolással; 1000 mesterséges beszélgetésre 800/100/100 pontosan (0 szétvágott csoport, 2,6 mp). A felosztás NEM jóváhagyott, nem training-ready. Riport: `data/reports/mt2_report.md`. Következő: MT-4 (jóváhagyással), MT-5, TE-3, tartalmi lezárás; az első 50 beszélgetés generálása csak kifejezett jóváhagyással (a nyitó váltásokat változtatni kell: az azonos nyitó minta `reject`).

**MT-4 (kész, `v1.13.23`):** `tools/multiturn_export.py` (mt4-1.0, 70 teszt, 114/114 mutáns, `docs/MULTITURN_EXPORT.md`): az MT-2 manifest (és bemenetei) ellenőrzése, elavult/hiányos/megváltozott bemenetnél hiba; részenként bájt-pontos kanonikus beszélgetések + R1 (futásidő-hű, `memory.build_prompt_context` importálva) és R2 (teljes előzmény) minták; R3 nem készül (arany összefoglaló és döntés kell); csonkolás és nem ábrázolható előzmény-függés mintánként jelölve; a kizárt/visszatartott/blokkolt rekordok és a hat TE-1 kizárás (azonosító és szöveg) függetlenül ellenőrzött; lemezről visszaolvasás; tesztadat `fixture_` előtaggal, jelölővel; a státuszok (split_approved/content_verified/training_ready) változatlanul false. 1000 mesterséges beszélgetésre 14,8 mp. Riport: `data/reports/mt4_report.md`. Következő: MT-5 (jóváhagyással; előtte döntés: R1 vagy R2, ablak-hossz), TE-3, tartalmi lezárás.

**MT-5 (kész, `v1.13.24`):** `src/train_multiturn.py` (mt5-1.0, 83 teszt, 75 mutánsból 74 elbukik + 1 dokumentált, indokolt ekvivalens, `docs/MULTITURN_TRAIN.md`): elkülönített, kísérleti többfordulós betöltő — **kizárólag betöltés és száraz futás, tanítás nincs** (nincs `.backward()`/`.step()`/`torch.save`, AST-vizsgálattal igazolva). Az MT-4 exportot ellenőrzi (érvényesség, ellenőrzőösszeg, felosztás, azonosítók, a hat TE-1 kizárás), elavult/megváltozott bemenetnél hiba. R2 (teljes előzmény) az elsődleges betöltési próba, R1 (futásidő-hű, csonkolás-jelöléssel) külön összehasonlító próba, R3 nem készül. Nincs véletlen ablakolás: egy köteg-sor egy minta-határ, beszélgetések nem folynak össze, rejtett állapot nem öröklődik kötegek/sorok között. A célmaszk a `target` karaktertartományból, két független módon ellenőrizve. A szótár kizárólag a train/R2 részből épül; a validation/test ismeretlen karakterei dokumentáltan, utólagos bővítés nélkül kezelve. Explicit `--max-chars` fölötti minta visszatartva jelentéssel, nem csonkítva. Egy FRISS, tanítatlan próba-modellel csak alak-/futás-ellenőrzés. A fixture export kizárólag kifejezett tesztmódban fogadható el. A státuszok (split_approved/content_verified/training_ready) változatlanul false. **1000 mesterséges beszélgetésen mért, kiemelt korlát:** a minták 100%-a — R1-ben ÉS R2-ben is — meghaladja a jelenlegi betanított modell 64 karakteres kontextusát (a legrövidebb R1-minta is ≥160 karakter); ez a modell architektúrájának/tanításának korlátja, nem a betöltő hibája, és a sikeres betöltés nem bizonyítja a hosszú kontextus tényleges megtanulását. Riport: `data/reports/mt5_report.md`. Következő: a modell kontextushosszának kérdése + a tanítás bemenetének (R1/R2) kiválasztása, TE-3, tartalmi lezárás; az első 50 beszélgetés generálása csak kifejezett jóváhagyással.

## 1. csomag (simple_qa) - LEZÁRVA, 1000/1000

**Az 1000 db egyszerű magyar kérdés-válasz célcsomag 2026-09-18-án
elkészült.** Lezáró audit: `data/reports/simple_qa_1000_completion_
audit.md`. A csomag STABIL, témakör-arányosan kiegyensúlyozott,
duplikátummentes állapotban van (legmagasabb tag-arány: 7.1%, AI: 4.4%).

| Batch | Raw | Clean | Rejected | Kereszt-dup | Avg score | Commit | STÁTUSZ |
|---|---|---|---|---|---|---|---|
| deepseek 0151-0200 | 50 | 50 | 0 | 0 | 100.0 | 6d6cd28 | STABIL |
| deepseek 0201-0250 | 50 | 50 | 0 | 0 | 100.0 | 6d6cd28 | STABIL |
| deepseek 0251-0300 | 50 | 49 | 1* | 1 (audit-kor talalt) | 100.0 | f44436d | STABIL |
| deepseek 0301-0350 | 50 | 46 | 4 | 4 | 100.0 | a25e2d3 | STABIL |
| deepseek 0351-0400 | 50 | 48 | 2 | 2 | 100.0 | 0c9940f | STABIL |
| deepseek 0401-0450 | 50 | 49 | 1 | 1 | 100.0 | e24a613 | STABIL |
| deepseek 0451-0500 | 50 | 50 | 0 | 0 | 100.0 | abb5aa7 | STABIL |
| claude 0501-0550 | 50 | 50 | 0 | 0 | 100.0 | b1ac64a | STABIL |
| claude 0551-0650 | 100 | 100 | 0 | 0 | 100.0 | b3aae9d | STABIL |
| claude 0651-0750 | 100 | 99 | 1 | 1 | 100.0 | 85e903c | STABIL |
| claude 0751-0850 | 100 | 100 | 0 | 0 | 100.0 | 7bb51b3 | STABIL |
| claude 0851-0950 | 100 | 100 | 0 | 0 valódi (4 jelzett, hamis pozitív) | 100.0 | 4b62f6f | STABIL |
| claude 0951-1050 | 100 | 100 | 0 | 0 új (4 régi jelzés megismétlődött) | 100.0 | 3f7b5d8 | STABIL |
| claude 1051-1159 (ZÁRÓ) | 109 | 109 | 0 | 0 valódi (1 új + 4 régi, mind hamis pozitív) | 100.0 | d5670d9 | STABIL |

*A deepseek 0251-0300 rejected sora retroaktívan, a pipeline-hardening
körben lett hozzáadva (`simple_qa_0283`, duplikátum a `simple_qa_0185`-tel).

## 2. csomag (explanation) - LEZÁRVA, 1000/1000

**Az 1000 db magyarázós példa célcsomag 2026-09-18-án elkészült.** Lezáró
audit: `data/reports/explanation_1000_completion_audit.md`. A csomag
STABIL, témakör-arányosan kiegyensúlyozott (a teljes korpuszon belül
nincs túlreprezentált tag), 0 fennálló duplikátummal (1003 raw, 3
rejected - mind valódi, helyesen kiszűrt kereszt-batch duplikátum).

### Batch-történet

| Batch | Raw | Clean | Rejected | Kereszt-dup | Avg score | Commit | STÁTUSZ |
|---|---|---|---|---|---|---|---|
| claude explanation 0001-0100 | 100 | 100 | 0 | 0 (5 régi simple_qa jelzés ismétlődött) | 100.0 | fd9a3a4 | STABIL |
| claude explanation 0101-0200 | 100 | 100 | 0 | 0 (5 régi simple_qa jelzés ismétlődött) | 100.0 | 9f79692 | STABIL |
| claude explanation 0201-0300 | 100 | 100 | 0 | 0 (5 régi simple_qa jelzés ismétlődött, egyiket sem érintve) | 100.0 | e925435 | STABIL |
| claude explanation 0301-0400 | 100 | 100 | 0 | 0 (5 régi simple_qa jelzés ismétlődött, egyiket sem érintve) | 100.0 | 0b59b34 | STABIL |
| claude explanation 0401-0500 | 100 | 100 | 0 | 0 (5 régi simple_qa jelzés ismétlődött, egyiket sem érintve) | 100.0 | a93e736 | STABIL |
| claude explanation 0501-0600 | 100 | 99 | 1 | 1 VALÓDI (explanation_0531 vs 0227, sim=1.0) + 5 régi simple_qa jelzés ismétlődött | 100.0 | a201bf7 | STABIL |
| claude explanation 0601-0700 | 100 | 98 | 2 | 2 VALÓDI (explanation_0681 vs 0244, sim=0.901; explanation_0697 vs 0242, sim=0.942) + 5 régi simple_qa jelzés ismétlődött | 100.0 | 2e20120 | STABIL |
| claude explanation 0701-0800 | 100 | 100 | 0 | 0 (5 régi simple_qa jelzés ismétlődött, egyiket sem érintve - a `matematika` tag tudatos kihagyása megelőzte az ismételt témaütközést) | 100.0 | 41da048 | STABIL |
| claude explanation 0801-0900 | 100 | 100 | 0 | 0 (5 régi simple_qa jelzés ismétlődött, egyiket sem érintve) | 100.0 | 1b95d07 | STABIL |
| **claude explanation 0901-1003 (ZÁRÓ)** | **103** | **103** | **0** | **0 (5 régi simple_qa jelzés ismétlődött, egyiket sem érintve)** | **100.0** | **cc97984** | **STABIL** |

**Egyedi clean explanation sorok: 1000 / 1000 (100%). A 2. CSOMAG KÉSZ.**

**Megjegyzés az 0601-0700 batch-ről**: ez már a MÁSODIK eset, hogy
explanation-explanation kereszt-batch duplikátum fordult elő, és
mindkét eset ebben a batch-ben a `matematika` témakörben történt
(átlag/kiugró érték, illetve exponenciális növekedés - mindkettő
majdnem szó szerint megegyezett egy korábbi, 0201-0300 batch-beli
sorral). **Tanulság a jövőbeli batch-ekre**: a szűkebb, jól definiált
fogalmi terekben (mint alapvető matematikai/statisztikai fogalmak)
nagyobb a véletlen témaismétlődés esélye, mint a tágabb témaköröknél -
érdemes explicit ellenőrizni a korábbi batch-ek tartalomlistáját egy
adott tag újbóli használata előtt.

**Megjegyzés az 0501-0600 batch-ről**: ez volt az első alkalom, hogy egy
explanation-kategóriás sor ténylegesen ütközött egy korábbi explanation
batch-csel (`explanation_0531` "Hogyan alakulnak ki a homokdűnék a
sivatagban?" - szó szerint ugyanaz az instrukció, mint a korábbi
`explanation_0227`-é). A pipeline pontosan felismerte (similarity 1.0,
ami egyértelműen megkülönböztethető a rövid-sablon hamis pozitívoktól,
amik sosem érik el az 1.0-t) és kiszűrte, mielőtt clean-be került volna.
Ez megerősíti, hogy a mandátumos cross-dedupe lépés ténylegesen működik
és szükséges, nem csak formalitás.

### Fontos formátumi eltérés
Az `explanation` kategória hosszabb (3 mondatos, ~280-350 karakteres),
ok-okozati magyarázatokat tartalmaz, `medium`/`hard` difficulty-vel - ez
szándékos eltérés a `simple_qa` 1-2 mondatos, kizárólag `easy` stílusától,
a `data/samples/sample_pack_v1.jsonl` explanation-mintáit követve.

## 3. csomag ("írd lépésekben" / step_by_step) - batch-történet

**ÚJ PROTOKOLL 2026-09-18-tól: ChatGPT raw producer + Claude/Nextora
validator.** A ChatGPT/Dispatch mostantól segíthet raw candidate JSONL
fájlok gyártásában a `data/inbox/chatgpt/` mappában, de ezek SOHA nem
számítanak automatikusan clean adatnak - Claude/Nextora minden sort a
teljes, kötelező pipeline-on (schema validate → nyelvi/formátum
ellenőrzés → batchen belüli dedupe → teljes korpuszos cross-dedupe →
topic report → quality score → safety/firewall → manuális mintavétel)
átfuttat, mielőtt bármi clean-be kerülhetne.

| Batch | Forrás | Raw | Clean | Rejected | Commit | STÁTUSZ |
|---|---|---|---|---|---|---|
| chatgpt_step_by_step_0001_0100 | ChatGPT/Dispatch raw candidate | 100 | **0** | 100 (schema_invalid_missing_fields) | *(nincs commit, csak rejected)* | ELUTASÍTVA schema-hiba miatt |
| claude_step_by_step_0001_0100 (pótlás) | Claude-generált | 100 | 100 | 0 | c3e21c4 | STABIL |
| chatgpt_step_by_step_0101_0200 | ChatGPT/Dispatch raw candidate (2. próbálkozás) | 100 | **0** | 100 (schema_invalid_missing_fields **+ duplikált tartalom**) | *(nincs commit, csak rejected)* | ELUTASÍTVA schema-hiba ÉS duplikált tartalom miatt |
| claude_step_by_step_0101_0200 (pótlás) | Claude-generált | 100 | 100 | 2* | 2477737 | STABIL |
| chatgpt_step_by_step_0201_0300 | ChatGPT/Dispatch raw candidate (3. próbálkozás, "szigorított") | 100 | **0** | 100 (templated_low_diversity_content) | *(nincs commit, csak rejected)* | ELUTASÍTVA sablon-alapú tartalom miatt (séma OK) |
| claude_step_by_step_0201_0300 (pótlás) | Claude-generált | 100 | 100 | 0 | d313580 | STABIL |
| chatgpt_step_by_step_0301_0400 | ChatGPT/Dispatch raw candidate (4. próbálkozás) | 100 | **0** | 100 (schema personal_data_suspected [hamis riasztás] + templated_low_diversity_content; 3 sor kizárt téma) | *(nincs commit, csak rejected)* | ELUTASÍTVA |
| claude_step_by_step_0301_0400 (pótlás) | Claude-generált | 100 | 100 | 0 | b4d0b93 | STABIL |
| **claude_step_by_step_0401_0500 (záró, közvetlen Claude)** | Claude-generált (nincs ChatGPT raw; a producer 0/400 clean után) | **100** | **100** | **0** | 33c374d | **STABIL** |

*A Claude batch 2 sora (`step_by_step_0174`, `0176`) a kizárt `wifi`
témalista miatt lett elutasítva és pótolva ugyanazon a batch-en belül -
lásd részletesen a batch report-ban.

**Egyedi clean step_by_step sorok: 500 / 500 (100%) - a 3. csomag KÉSZ.**
**Következő lépés: a 4. csomag (Összegzés példa, 500 sor) előkészítése - csak a felhasználó jóváhagyása után.**

### Első pilot tanulság (ChatGPT/Dispatch producer)
A ChatGPT raw candidate 100%-ban elutasításra került séma-hiba miatt:
minden sorból hiányzott a `quality_notes` és `source` mező, és az
`input` mező objektum típusú volt (`{"Current": null}`) a szükséges
string típus (`""`) helyett. Ez egy **rendszerszintű, minden sort
egyformán érintő hibaminta** volt, nem véletlenszerű zaj - konkrét,
javítható visszajelzés a producer kimeneti sablonjához. A Claude/
Nextora validator **nem javította automatikusan** a hiányzó mezőket,
mert ez ellentmondana a tűzfal szerepnek - helyette a teljes 100 sort
elutasította, és a hiányt saját, validált generálással pótolta.
Részletek: `data/reports/claude_step_by_step_0001_0100_report.md`.

### Második pilot tanulság (ChatGPT/Dispatch producer) - SÚLYOSABB PROBLÉMA
A második ChatGPT raw candidate batch (`chatgpt_step_by_step_0101_0200`)
technikailag "javított" mezőkkel érkezett (az `input` már string típus,
`quality_notes` mező jelen van), de **két komoly probléma is
felszínre került**:
1. A `source` mező **továbbra is hiányzott** minden sorból - ugyanaz a
   hiba, mint az első pilotnál, nem lett javítva.
2. **Sokkal súlyosabb**: mind a 100 sor `instruction`/`output` tartalma
   **szó szerint megegyezett** az első, már elutasított batch
   tartalmával - csak az `id` mezők lettek átszámozva, és minden sorhoz
   ugyanaz a generikus `quality_notes` boilerplate szöveg került
   ("Egyedi, hétköznapi, lépésenkénti magyar példa." - ironikus módon,
   mert a tartalom éppen NEM volt egyedi).
Ez arra utal, hogy a producer jelenleg **nem genuinly új tartalmat
generál batch-enként**, hanem ugyanazt a mintakészletet küldi be
újraszámozva. Ez egy strukturálisabb, a puszta séma-formátumnál mélyebb
probléma a producer folyamatában, amit orvosolni kell, mielőtt egy
harmadik próbálkozás érdemi lenne. Részletek:
`data/reports/claude_step_by_step_0101_0200_report.md`.

### Kizárt téma találat a Claude saját generálásában (önellenőrzés sikere)
A `claude_step_by_step_0101_0200` batch generálása közben a Claude/
Nextora validator **saját magával szemben is** alkalmazta a kizárt
témalistát: 2 saját generálású sor ("otthoni wifi hálózat védelme",
"nyilvános wifi biztonságos használata") a `wifi` kizárt kulcsszó miatt
lett eltávolítva és alternatív digitális biztonsági témával pótolva,
mielőtt clean-be kerülhetett volna. Ez megerősíti, hogy a validator
szerep nem csak a külső (ChatGPT) forrásra, hanem a saját generálásra is
egyformán szigorúan vonatkozik.

### Harmadik pilot tanulság (ChatGPT/Dispatch producer) - séma javult, ÚJ mélyebb probléma
A harmadik ChatGPT raw candidate batch (`chatgpt_step_by_step_0201_0300`)
egy "szigorított" verzió volt, és **valódi javulást mutatott a
séma-formátum terén**: mind a 100 sor átment a schema validáláson
(a `source` mező végre jelen volt, az `input` mező helyesen string
típusú és üres). Nincs átfedés a korábbi két, már elutasított
batch-csel sem.

Azonban egy **új, mélyebb tartalmi probléma** került elő: mind a 100
sor outputja pontosan **14 rigid sablon** egyikéből származott, ahol
csak az 1. lépés (és a témanév) változott soronként, a 2-5. lépések
szó szerint azonosak voltak minden, ugyanazt a sablont használó sor
között. A beküldő "különböző témakörök száma: 14" állítása technikailag
igaz volt, de félrevezető módon pozitívumként lett feltüntetve, holott
ez valójában azt jelentette, hogy csak 14 genuinly egyedi tartalom
létezett 100 helyett. A `quality_notes` mező is hasonló sablon-alapú
volt: technikailag minden sorban egyedi string (a témanév miatt), de
tartalmilag ugyanazt a mondatsablont követte mindegyik.

A formális `dataset_dedupe.py` output-hasonlósági ellenőrzés (0.9
küszöb) **34 sort objektíven duplikátumként jelzett**, de ez csak egy
alsó becslés volt a valódi, sablon-alapú redundanciára - a validator
**mind a 100 sort elutasította** minőségi alapon, nem csak a formálisan
jelzett 34-et, mert a mögöttes tartalom-generálási módszer nem felelt
meg a "genuinly egyedi, témaspecifikus tartalom" követelménynek.

**Összegzés**: a producer séma-formátuma most már megbízható, de a
tartalomgenerálási módszer (jelenleg sablon + kulcsszó-behelyettesítés)
további fejlesztést igényel, mielőtt egy negyedik próbálkozás
elfogadható eredményt hozhatna. Részletek:
`data/reports/claude_step_by_step_0201_0300_report.md`.

### Negyedik pilot tanulság (ChatGPT/Dispatch producer)
A negyedik raw candidate (`chatgpt_step_by_step_0301_0400`) ismét 0 clean
sort adott. A schema validator mind a 100 sort elutasította
`personal_data_suspected` jelzéssel, de ez **hamis riasztás**: a
`quality_notes` sablonmondat minden sorban tartalmazza a `0301-0400`
tartományt, ami illeszkedik a telefonszám-regexre. A tartalom a 3.
próbálkozás finomított sablonja: lépésenként a különböző szövegek száma
100 / 14 / 14 / **1** / **1**, vagyis a 4. és 5. lépés egyetlen azonos
mondat minden soron. A formális output-dedupe már csak 18 sort jelez (3.
körben 34), miközben a tartalmi redundancia lényegében változatlan - a
mechanikus szűrő egyre kevésbé fogja meg, ezért a lépésenkénti
szövegszámlálás hasznos kiegészítő ellenőrzés. 3 sor kizárt témát is
tartalmazott (`wifi`, `ajándék`, `bocsánat`); hard nehézségű sor nem volt.
A Claude-pótlás lépésenként 100/100/100/100/100 különböző szöveget
tartalmaz. Részletek: `data/reports/claude_step_by_step_0301_0400_report.md`.

### Ötödik (záró) batch - közvetlen Claude-generálás
A `step_by_step_0401_0500` batch a felhasználó utasítására ChatGPT raw
candidate nélkül, közvetlenül Claude-generálással készült (a producer a
négy próbálkozásból 0 clean sort adott). 100/100 clean, 0 rejected,
lépésenként 100/100/100/100/100 különböző szöveg, 20/20 manuális minta.
A kereszt-dedupe a teljes 2500 soros N×N futtatás helyett (55 perc után
sem ért véget, leállítva) **célzott új-vs-korpusz** ellenőrzéssel történt:
0 találat 0.9 felett, a régi-régi párokat a korábbi batch-ek futásai már
lefedték. Részletek: `data/reports/claude_step_by_step_0401_0500_report.md`.

**Tanulság a hátralévő csomagokra:** a teljes N×N cross-dedupe a 2500 soros
korpuszon már nem praktikus (>55 perc); a következő csomagoknál a
célzott (csak új sorok a korpusz ellen, `quick_ratio` előszűréssel)
módszer az alapértelmezett, a `tools/dataset_cross_dedupe.py` ilyen
irányú átdolgozása külön, jóváhagyott feladat lehet.

## 4. csomag (summary / összegzés) - batch-történet

Közvetlenül Claude-generált (nincs ChatGPT raw candidate), kitalált, általános magyar tartalommal:
nincs valós személy/magánadat, webes forrás, szerzői jogvédett szöveg vagy MF-AI-projekttény.
Minden batch 10 tartalmi típus x 10 sor, `tags` = `magyar`, `összefoglalás`, tartalmi típus, téma.

| Batch | Forrás | Raw | Clean | Rejected | Commit | STÁTUSZ |
|---|---|---|---|---|---|---|
| claude_summary_0001_0100 | Claude-generált | 100 | **100** | 0 | a875dbf | STABIL |
| **claude_summary_0101_0200** | Claude-generált | 100 | **100** | 0 | 9cbfcae | **STABIL** |
| **claude_summary_0201_0300** | Claude-generált | 100 | **100** | 0 | 8490240 | **STABIL** |
| **claude_summary_0301_0400** | Claude-generált | 100 | **100** | 0 | 665d010 | **STABIL** |
| **claude_summary_0401_0500** | Claude-generált | 100 | **100** | 0 | 328aff5 | **STABIL** |
| **final audit/fix round** (0001-0500) | audit | - | 500 audit, 139 sor javítva | - | (commit után) | **STABIL** |

**Egyedi clean summary sorok: 500 / 500 (100%) - a 4. csomag KÉSZ.** Következő lépés: külön jóváhagyású summary final audit/fix round (lásd alább), majd az 5. csomag.

### Első batch tanulságai (summary)
- A meglévő eszközök (validate/dedupe/score) nem mérik az input-output hűséget és a tömörséget, ezért
  egy ideiglenes `check_summary.py` ellenőrző (nem a repóban; a `tools/` alá emelése külön jóváhagyás kérdése) (szótő-összevetés, számnév-ellenőrzés, output/input arány, 6 szavas
  másolás-arány, instruction-mondatszám konzisztencia) egészíti ki; a kézi mintavétel marad az
  elsődleges hűség-ellenőrzés.
- Első nekifutásra hat lista-sor outputja hosszabb volt az inputnál (nem összegzés), és csak 49
  különböző instruction-szöveg volt a 100 sorra; mindkettő javítva (lásd a batch reportot).
- Az outputok mind egy mondatosak: a következő batchekben 2 mondatos outputok is legyenek.
- A kereszt-dedupe célzott (új sorok vs. a teljes clean korpusz) módszerrel készül.
- Részletek: `data/reports/claude_summary_0001_0100_report.md`.

### Második batch tanulságai (summary 0101-0200)
- Az outputok vegyesek: 50 egymondatos + 50 kétmondatos; az instruction mondatszáma mindig egyezik az outputtal (ellenőrző: 0 ellentmondás).
- Tömörség: minden output rövidebb az inputnál (max. arány 0.77), szó szerinti másolás max. 0.32; a 0.5 fölötti másolás-arányú sort (0129) átfogalmaztam.
- A 20 soros kézi mintából 3 sor jelentéstorzítása/hedge-vesztése derült ki (0124, 0133, 0153) és 1 kihagyott fő lényeg (0191); mind javítva. A mintavétel mérete a következő batchekben növelendő (30-40 sor) vagy teljes kézi átolvasás javasolt.
- Az instruction 100/100 egyedi, de 29 kézzel írt mondatvázból épül; a 3-5. batchhez további kézzel írt megfogalmazás javasolt.
- A `summary` csomagot jelölő `összefoglalás` tag aránya 7.4% a korpuszban; a következő batchnél átlépi a 8%-os topic-report küszöböt. Ez kategória-jelölő tag, nem témaszaturáció; a topic report tag-kezelése külön jóváhagyandó.
- Mérési műtermék: ha a batch clean másolata már létezik, a kereszt-dedupe-nak ki kell zárnia azt (különben saját magával ütközik); a scriptek ezt kezelik.
- Részletek: `data/reports/claude_summary_0101_0200_report.md`.

### Harmadik batch tanulságai (summary 0201-0300)
- Manuális mintavétel 40 sorra emelve (mind a 10 típusból 4): 3 kisebb hiba (0209, 0246, 0281), a 2. batch mintájában 3/20 volt.
- Új, erősített hűség-ellenőrző (ideiglenes `fidelity_check.py`, nem a repóban): hedge- és hivatkozás-megőrzés, tagadás, ellentétpár-felcserélés, idő- és számszó-eltérés, számmegőrzés. Valódi találat: 2 hedge-vesztés (0213, 0216); a többi jelzés egyenértékű megfogalmazás. A jelentésbeli torzítást (pl. 0209 "míg" vs "majd") csak a kézi átolvasás fogta meg.
- Instruction: mind a 100 kézzel írt; az első kézzel írt készlet 96%-ban nevezte meg a mondatszámot és 25 sor "Két mondatban"-nal kezdődött, ezért kétszer újraírtam. Végállapot: 100/100 egyedi, 56 különböző kétszavas nyitás, 54% mondatszámos, 45% kérdő / 55% felszólító, 1 sor "Foglald össze"-val.
- Tömörség: max. arány 0.84 (egy sor), kétmondatosnál 0.79; a szorosabbra fogalmazott sorok: 0266, 0253, 0274, 0239, 0237.
- Az `összefoglalás` tag aránya 10.7% (300/2800): várható, a csomagot jelölő kategória-tag, a kérés szerint csak dokumentálva, témaszaturációként nem kezelve.
- Részletek: `data/reports/claude_summary_0201_0300_report.md`.

### Negyedik batch tanulságai (summary 0301-0400)
- Erősített hűség-ellenőrzés (ideiglenes `fidelity_check2.py`, nem a repóban): védett hedge-csoportok megőrzése, hivatkozás, *érdemes -> tény*, tagadás, ellentétpár, idő-/számszó. Végállapot: LOST 0, ADDED 0, ADVICE->FACT 0; 90 / 100 input tartalmaz védett fenntartó szót. Az első futás 3 hedge-vesztést (0344, 0363, 0380) és 5 túl magas output/input arányt (0357, 0371, 0327, 0331, 0380) jelzett.
- A csoportszintű ellenőrző nem látta a *legtöbb* (0326), a *legalább* (0372), az *általában* elcsúszó hatókörét (0390) és a szabály gyengülését (0382); ezeket szószintű lista, kézi olvasás és a tagadás-átnézés (0364, 0388) találta meg. Összesen 11 tartalmi javítás clean előtt.
- Manuális mintavétel 40 sor (blokkonként a 2., 5., 7., 10. sor): 5 javítást igényelt (0362, 0382, 0390, 0397, 0372), a 3. batchben 3 volt 40-ből.
- A tömörség javítása az 5 sornál az input bővítésével történt (semleges mondat), nem az output szorosabbra fogalmazásával; ezt a report jelzi.
- 31 `quality_notes` megfogalmazás átírva (elgépelések, nehézkes szerkezetek).
- Instruction: 100 kézzel írt, egyedi, 67 kétszavas nyitás (3. batch: 56); a mondatszám-megnevezés 71%-ra nőtt (3. batch: 54%) és 9 sor kezdődik "Foglald össze"-val; a záró batchnél érdemes kevesebb mondatszám-előírás és több szituációs instruction.
- Az `összefoglalás` tag aránya 13.8% (400/2900): várható, a csomagot jelölő kategória-tag, a kérés szerint csak dokumentálva.
- **Nyitott, nem javított tétel**: az 1-3. batchen visszamérve a szigorúbb ellenőrző *érdemes -> tény* gyanút ad (1. batch: 0016, 0027, 0061, 0073, 0090; 2.: 0175, 0185; 3.: 0239, 0273, 0277, 0279) és további hedge-vesztés jelzéseket (18 / 18 / 9, részben legitim kihagyás). Külön jóváhagyott javítási kör dönthet róla.
- Részletek: `data/reports/claude_summary_0301_0400_report.md`.

### Ötödik (záró) batch tanulságai (summary 0401-0500)
- Az összes korábbi észrevétel érvényesítve: 50/50 egy- és kétmondatos output blokkonként 5-5, output mindig rövidebb az inputnál (max. 0.79), új tény nélkül; mind az 5 batch 10 típus x 10 sor.
- Szigorított fenntartás-ellenőrzés (ideiglenes `fidelity_check3.py` + szószintű `word_drops.py`, nem a repóban): új *valószínű* és *nem biztos* csoport. 99/100 input tartalmaz védett fenntartást; végállapotban 0 valódi vesztés, 0 *érdemes -> tény*. Az első futás 7 valódi vesztést jelzett (0424, 0446, 0459, 0468, 0473, 0481, 0494), a szószintű átnézés további 5-öt (0438, 0423, 0456, 0499, 0463), a 40 soros minta 2-t (0447, 0464). Összesen 15 tartalmi javítás, ebből 5 az input oldalán.
- Instruction: 55 újraírás után 100/100 egyedi, témaspecifikus; 28% nevezi meg a mondatszámot (előző batch: 71%), 0 sor kezdődik "Foglald össze"-val (előző: 9), 79 különböző kétszavas nyitás, 100 különböző téma-címke. A kérdő forma aránya 55%.
- quality_notes: az első változat merev felsorolás volt pontatlanságokkal, mind a 100 át lett írva természetes mondatokra és az outputtal egyeztetve.
- Manuális mintavétel 40 sor (blokkonként a 2. és 4. egymondatos, a 2. és 4. kétmondatos sor): 2 javítás.
- Kereszt-dedupe a 2900 meglévő sor ellen 0 találat; regressziós teszt STABIL; topic report: `összefoglalás` 500/3000 = 16.7% (várható, csak dokumentálva).
- **Csomagszintű mérés (500 sor)**: 500 egyedi id/instruction/input/output/quality_notes, 0 hiányzó id, 300 egymondatos + 200 kétmondatos output, 0 output-pár >= 0.9. **Viszont 37 sablonszerű instruction-pár >= 0.9** (68 sor, mind az 0001-0200 tartományban), amit a batchenkénti dedupe (instruction+input) nem jelzett.
- **Nyitott (nem javított) tételek az 1-3. batchben**: 11 *érdemes -> tény* sor (0016, 0027, 0061, 0073, 0090, 0175, 0185, 0239, 0273, 0277, 0279), 44 hedge-jelzés (18 / 18 / 8, részben legitim kihagyás), 37 sablonos instruction-pár. **Külön final summary audit/fix round javasolt** (jóváhagyás kell).
- Részletek és package státusz: `data/reports/claude_summary_0401_0500_report.md`.

### Summary final audit/fix round (v1.11.5-dataset-audit)
- Riport: `data/reports/summary_final_audit_fix_report.md`. A `step_by_step` audit mintájára az 500 sor teljes csomagszintű ellenőrzése: ID-folytonosság, schema, dedupe, kereszt-dedupe, instruction-párok, nyitások, tömörség, hűség, fenntartások, safety, identity bleed, URL/személyes adat, quality_notes.
- A három nyitott tétel lezárva: 11 *érdemes -> tény* sor: 10 valódi (javítva), 1 hamis pozitív; 44 hedge-jelzés: 15 valódi (javítva), 29 hamis pozitív (indoklással, módosítatlanul); 37 instruction-pár (68 sor): 115 instruction átírva témaspecifikusra, 0 pár >= 0.85 maradt.
- További 14 sor a három lista mellett futtatott szűrőkből (szószintű, tagadás-, számnév-, ellentétpár-, modális-alak ellenőrzés + 40 soros véletlen minta). Összesen 139 clean sor módosult (38 output, 115 instruction, 14 mindkettő); a `raw` fájlok érintetlenek (raw != clean: 53 / 78 / 8 sor a 0001-0300 tartományban).
- Végállapot: 500/500 valid, 0 missing, 0 extra, 0 kereszt-duplikátum, output mindig rövidebb az inputnál, szigorított hedge-ellenőrző 0 valódi vesztés, 0 *érdemes -> tény*, 500 egyedi quality_notes; regressziós teszt STABIL. Korlát: 56 sor az 1-3. batchben soronkénti átolvasás nélkül (0 egyedi találat a 40 soros véletlen mintában), az 1-2. batch maradék (egymástól < 0.85) generikus instructionjei.

## 5. csomag (noisy_input / hibás user szöveg -> javított szöveg) - batch-történet

Közvetlenül Claude-generált, kitalált, hétköznapi magyar felhasználói üzenetek zajos (elírt, ékezet nélküli, beszélt, rövidítéses,
szóközhibás, hibás ragos, telefonos, indulatos, szleng, kusza) és természetes javított változata. `category: noisy_input`,
`source: synthetic_claude_magyar`, `tags` = `magyar`, `zajos bemenet`, zajtípus, téma.

| Batch | Forrás | Raw | Clean | Rejected | Commit | STÁTUSZ |
|---|---|---|---|---|---|---|
| **claude_noisy_input_0001_0100** | Claude-generált | 100 | **100** | 0 | 5fd5522 | **STABIL** |
| **claude_noisy_input_0101_0200** | Claude-generált | 100 | **100** | 0 | c83c96c | **STABIL** |
| **claude_noisy_input_0201_0300** | Claude-generált | 100 | **100** | 0 | 479857b | **STABIL** |
| **claude_noisy_input_0301_0400** | Claude-generált | 100 | **100** | 0 | fb5feeb | **STABIL** |
| **claude_noisy_input_0401_0500** | Claude-generált | 100 | **100** | 0 | 06be754 | **STABIL** |

**Egyedi clean noisy_input sorok: 500 / 500 (100%) - az 5. csomag kész és auditált (záró audit: v1.12.6-dataset-audit).**

### Első batch tanulságai (noisy_input 0001-0100)
- **Sémadöntés (azóta jóváhagyva: az `instruction` mező marad)**: a megadott mezőlistában nincs `instruction`, a repó validátora kötelezően kéri. A validátor változatlan; az `instruction` mező 29 kézzel írt, nem helyesírás-javító feladatmegfogalmazással van kitöltve. Ha nem kell, a következő batch előtt külön jóváhagyással a validátorral együtt távolítható el.
- 11 zajtípus (8-10 sor), 50 téma, id-k típusokat vegyesen; az output megtartja a user hangját (haverom, meg, jó fej, a franc), nem hivatalos, nem válasz a kérdésre.
- A teljes átolvasás 7 sort javíttatott clean előtt: 4 sor csak nagybetű/írásjel-zajt tartalmazott (valós szóalak-zaj hozzáadva), 3 outputban eltolódott a szándék (0015, 0049, 0067).
- Ellenőrzők (ideiglenes `noisy_check.py`, nem a repóban): ismeretlen-szó arány input -> output 0.266 -> 0.175, formai zajmarker az outputban 0, szándékmegőrzés 0.84 / 0.82, kereszt-dedupe a 3000 sor ellen 0 találat, 0 PII/URL/identity bleed/erős káromkodás.
- Következő batch: a valódi zaj szórásának növelése (kevert zajtípusok, több téma), az `instruction` mező sorsáról szóló döntés után.
- Részletek: `data/reports/claude_noisy_input_0001_0100_report.md`.

### Második batch tanulságai (noisy_input 0101-0200)
- Az 1. batch korlátai javítva: minden sor 2-3 zajtípust kap (76 sor 3, 24 sor 2), 0 csak formai sor (1. batch: 9), 100 különböző téma (1. batch: 50), közlekedési téma 12, főzés/háztartás 3 sor.
- Több telefonos gyorsgépelés-jellegű hiba (billentyű-szomszédos betűk, összeírt szavak, ékezet nélkül, kisbetűs kezdés, írásjel nélküli vég) és több beszélt nyelvi szerkezet (*hát, izé, asszem, figyu, ja, ugye, vagy mi*); az output megtartja a hangot és nem válaszol.
- Ellenőrzők (ideiglenes `noisy_check2.py`, `noisy_extra.py`, `gen_noisy_batch2.py`, nem a repóban): ismeretlen-szó arány input -> output 0.284 -> 0.143, formai zajmarker az outputban 0, szándékmegőrzés 0.67 / 0.67 (ékezet nélküli inputok torzítják, kézzel átnézve rendben), kereszt-dedupe a 3000 sor ellen 0 találat, 0 PII/URL/identity bleed/erős káromkodás, átlag score 99.9 (0114: `low_instruction_overlap`, 90).
- Az összeállítás közben javítva: 21% közlekedési téma -> 9 sor lecserélve; egy instruction 9 sorban ismétlődött -> legfeljebb 4; 2 output formai jelölő (*?!*); 7 pontatlan zajcímke; a *kszi* -> *köszi*, a *na ja szóval* megtartva, egy felesleges rag-átírás visszavonva.
- Korlát: a szándékmegőrzési mutató az ékezet nélküli inputoknál torzít; a zaj szintetikus; 83 kisbetűs kezdésű input (a 3. batchben több rendesen tagolt, kevés hibás üzenet is kell).
- Részletek: `data/reports/claude_noisy_input_0101_0200_report.md`.

### Harmadik batch tanulságai (noisy_input 0201-0300)
- Cél a 2. batch túlzott szétesettségének kiegyensúlyozása: 63 nagybetűs kezdésű input (2. batch: 17), 83 sorban legfeljebb 3 javított szóalak (2. batch: 14), a kisbetűs + írásjel nélküli input 34 sor (2. batch: 81); 2-3 zajtípus soronként (60 sor 3), 100 új téma (közlekedés 1, főzés/háztartás 1).
- Az output megtartja a hangot (*kéne, tök, suli, vagy mi, hisz, figyi*), nem hivatalos, nem válasz; szándékmegőrzés 0.91 / 0.88 (2. batch: 0.67 / 0.67), ismeretlen-szó arány 0.187 -> 0.151, átlag score 100.0, kereszt-dedupe a 3200 sor ellen 0 találat.
- **Ellenőrző-hiba felfedezve**: a 2. batch kereszt-dedupe-ja a `noisy_input` nevű fájlokat kihagyta, így az 1. batchhez nem volt összevetve; utólag futtatva (3100 sor) 0 találat. A 3. batchnél már az 1-2. batch is a korpusz része.
- Az összeállítás közben javítva: csak formai sor -> valódi hiba (*furnak*), 2 zajcímke (`0217`, `0270`), érzékeny kulcsszó (*beteg*) kivéve, 2 hibás output-javítás (*elázott*, *vegyem-e meg*).
- Nyitott: a topic report a `zajos bemenet` tagre 9.1%-ot jelez (a csomag jelölő címkéje, 500 sornál kb. 15%), a `beszélt nyelv` címke 5 sorban gyenge bizonyítékú, nincs billentyű-szomszédos betűhiba ebben a batchben.
- Részletek: `data/reports/claude_noisy_input_0201_0300_report.md`.

### Negyedik batch tanulságai (noisy_input 0301-0400)
- A 3. batch iránya megtartva (84 nagybetűs kezdésű input, 94 sorban legfeljebb 3 javított szóalak, szándékmegőrzés 0.93 / 0.91, a kisbetűs + írásjel nélküli input csak 16 sor), négy típus erősítve: indulatos 16, kusza mondat 17, enyhe szleng 28, félreütött kérdés 28 összes címke (3. batch: 5 / 4 / 4 / 3). 100 új téma (közlekedés 0), 2-3 zajtípus (87 sor 3), minden sorban valódi szóalak-szintű javítás, átlag score 100.0, kereszt-dedupe a 3300 sor ellen 0 találat.
- Az összeállítás közben javítva: 4 gyenge sor (nem volt szóalak-hiba) + 1 sor, ahol az output mondatot hagyott el; 3 zajcímke; az *akksi* -> *akku*; egy félreérthető input/output (*vki ráérne esetleg*); zavaros quality_notes-részek.
- Korlát: a címkék részben stílust jelölnek (87 sor 3 címkével, de átlag 1.7 javított szóalak / sor); a `beszélt nyelv` címke 5 sorban gyenge bizonyítékú; nincs billentyű-szomszédos betűhiba és közlekedési téma; a `zajos bemenet` tag a topic reportban 11.8% (a csomag jelölő címkéje, 500 sornál kb. 15%).
- Részletek: `data/reports/claude_noisy_input_0301_0400_report.md`.

### Ötödik, záró batch tanulságai (noisy_input 0401-0500)
- A 4. batch iránya megtartva (szándékmegőrzés 0.91 / 0.91, 89 nagybetűs kezdésű input, 11 formátlan sor, 91 sorban legfeljebb 3 javított szóalak, 93 sor 3 zajtípussal, 100 új téma). Új zajfajták a kérésre: 80 sor billentyű-szomszédos elütéssel (magyar QWERTZ, 82 db), 7 sor *o*/*0* tévesztéssel számokban, 12 összeírt és 4 szétírt szó (*nemtom, mivan, vala mi, ki csit*).
- Összes címke: szleng 25, félreütött kérdés 23, indulatos 21, kusza mondat 16; *ékezet nélkül* csak 3 sor. Kereszt-dedupe a 3400 sor ellen 0 találat, átlag score 100.0, regressziós teszt STABIL.
- Csomag-szintű ellenőrzés (500 sor egyben): 500/500 valid, 0 id/instruction/output duplikátum, input-input/output-output/instruction+input >= 0.9 páronként 0, id-k 0001-0500 hézag nélkül, 447 téma, 149 instruction, easy 225 / medium 175 / hard 100.
- Az összeállítás közben javítva: 3 gyenge sor (csak vessző/pont), 2 gyenge zajcímke. Korlátok: 6 sorban a javítás számjegy- vagy szóhatár-javítás (`0402, 0404, 0407, 0450, 0457, 0472`); a címkék részben stílust jelölnek; a `beszélt nyelv`, `hibás ragozás`, `rövidítés` címke ebben a batchben kevés; a `zajos bemenet` tag a topic reportban 14.3%.
- **Javasolt következő lépés: az 5. csomag záró audit/fix köre** (csomag-szintű címke- és arány-egyensúly, ismétlődő fordulatok - *szval* 60 inputban, *tök* 63 outputban -, a 2. batch report 3000/3100 sor pontosítása, a 6 tágabb értelmezésű sor, a `zajos bemenet` tag kezelése), csak a felhasználó jóváhagyásával.
- Részletek: `data/reports/claude_noisy_input_0401_0500_report.md`.

### 5. csomag záró audit/fix kör (noisy_input 0001-0500)
- Verdikt: **STABIL**, 500 / 500 clean, 0 rejected, átlag score 100.0, regressziós teszt STABIL; teljes clean korpusz 3500 sor.
- Csomagszinten ellenőrizve és rendben: ID-folytonosság, schema, input != output, dedupe (batchen belül és 500 sor egyben), cross-dedupe (500 noisy vs 3000 nem-noisy + noisy-noisy páronként: 0 találat), PII/URL/e-mail/telefon/MF-AI/Nextora (0), safety, quality_notes egyediség (500/500).
- Javítva (csak clean, raw változatlan; 219 sor): 7 formai 1. batch sor -> betűszintű hiba; `szval` 60 -> 21 sorban (17 elütés-forma, 22 `úgyhogy`); `tök` 57 -> 34 sorban; 32 sor zajcímkéje (12 `beszélt nyelv`-levétel `úgyhogy`-soron, 6+2 gyenge `beszélt nyelv`, 4 alaptalan `rövidítés`, 1 `kérdés`, 7 új címke a formai soroknál); 16 jegyzet-idézet; `0452` (hasonló sor); `0114` instruction (score 100); `difficulty` csomag-szinten újrarangolva (153 sor).
- A hat emberi értelmezést igénylő sor (`0402, 0404, 0407, 0450, 0457, 0472`) elfogadva (szóhatár- és o/0-javítás). A 2. batch report cross-dedupe-pontosítása (3000 vs 3100 sor) külön szakaszban dokumentálva, az adatot nem érintette.
- Nem blokkoló megfigyelések: az „egy elütés + hiányzó írásjel” szerkezet a sorok 39%-a; `szóval` 13.6%; 11 halvány `beszélt nyelv` címke; `hibás ragozás`/`rövidítés` ritka az 5. batchben; `zajos bemenet` tag 14.3% (jelölőcímke, nem javítva).
- Részletek: `data/reports/noisy_input_final_audit_fix_report.md`.

## Minőségi trendek (folyamatosan frissül)

### AI/Nexora témakör-arány (audit óta követve)
| Ellenőrzési pont | Összes sor | AI-tagelt | Arány |
|---|---|---|---|
| Audit (0151-0500) | 343 | 44 | 12.8% |
| Hardening után (0151-0500, javítva) | 342 | 44 | 12.9% |
| +claude 0501-0550 | 392 | 44 | 11.2% |
| +claude 0551-0650 | 492 | 44 | 8.9% |
| +claude 0651-0750 | 591 | 44 | 7.4% |
| +claude 0751-0850 | 691 | 44 | 6.4% |
| +claude 0851-0950 | 791 | 44 | 5.6% |
| +claude 0951-1050 | 891 | 44 | 4.9% |
| +claude 1051-1159 (1. csomag ZÁRÓ) | 1000 | 44 | 4.4% |
| +explanation 0001-0100 | 1100 | 44 | 4.0% |
| +explanation 0101-0200 | 1200 | 44 | 3.7% |
| +explanation 0201-0300 | 1300 | 44 | 3.4% |
| +explanation 0301-0400 | 1400 | 44 | 3.1% |
| +explanation 0401-0500 | 1500 | 44 | 2.9% |
| +explanation 0501-0600 (clean, 99 új) | 1599 | 44 | 2.8% |
| +explanation 0601-0700 (clean, 98 új) | 1697 | 44 | 2.6% |
| +explanation 0701-0800 (clean, 100 új) | 1797 | 44 | 2.4% |
| +explanation 0801-0900 (clean, 100 új) | 1897 | 44 | 2.3% |
| **+explanation 0901-1003 (ZÁRÓ, clean, 103 új) - 2. csomag KÉSZ** | **2000** | **44** | **2.2%** |

A stratégia (0 új AI/Nexora-sor minden Claude-batch-ben, a 9. csomagig)
bizonyítottan működik - az arány minden körben csökken. A 2. csomag
lezárásakor (2000 sor) az AI/Nexora arány 12.8%-ról 2.2%-ra csökkent az
audit óta - ez a trend folytatódik a fennmaradó csomagoknál is, egészen
a 9. csomagig, ami az egyetlen tervezett hely az AI/Nexora témájú
tartalom (kizárólag repo-alapú) bővítésére.

### iskola / technika / biológia tag-arány (2025-09 óta figyelt trend)
| Ellenőrzési pont | iskola | technika | biológia |
|---|---|---|---|
| +claude 0851-0950 | 9.0% (71) | 9.0% (71) | - |
| +claude 0951-1050 | 8.0% (71) | 8.0% (71) | - |
| +claude 1051-1159 (1. csomag ZÁRÓ, 1000 sor) | 7.1% (71) | 7.1% (71) | - |
| +explanation 0001-0100 (1100 sor) | 6.5% (71) | 8.3% (91) - túllépte | - |
| +explanation 0101-0200 (1200 sor) | 5.9% (71) | 7.6% (91) - korrigálva | - |
| +explanation 0201-0300 (1300 sor) | 5.5% (71) | 7.0% (91) | 4.2% (55) |
| +explanation 0301-0400 (1400 sor) | 5.1% (71) | 6.5% (91) | 4.2% (59) |
| +explanation 0401-0500 (1500 sor) | 4.7% (71) | 6.1% (91) | 3.9% (59) |
| +explanation 0501-0600 (1599 sor, clean) | 4.4% (71) | 5.7% (91) | 3.7% (59) |
| +explanation 0601-0700 (1697 sor, clean) | 4.2% (71) | 5.4% (91) | 3.5% (59) |
| +explanation 0701-0800 (1797 sor, clean, 0 új matematika/biológia sor) | 4.0% (71) | 5.1% (91) | 3.3% (60) |
| +explanation 0801-0900 (1897 sor, clean, 1 új biológia sor) | 3.7% (71) | 4.8% (91) | 3.2% (61) |
| **+explanation 0901-1003 (2000 sor, ZÁRÓ, 0 új technika/iskola/biológia/matematika sor)** | **3.5% (71)** | **4.5% (91)** | **3.1% (62)** |

A `technika` tag korábbi enyhe túllépését (8.3%) a következő batch-ek
tudatos, alacsony/0 db `technika`-sort tartalmazó tervezése sikeresen
korrigálta és tovább csökkentette, egészen 4.5%-ig a 2. csomag zárásakor.
Az `iskola` tag hasonlóan 7.1%-ról 3.5%-ra csökkent a csomag felépítése
alatt. A `biológia` tag tudatos, minimális használata (csak elvétve,
1-1 sor egy-egy batch-ben) tartotta ezt is lapos, csökkenő trenden
(4.2%-ról 3.1%-ra). Ez megerősíti, hogy a tudatos téma-rotáció stratégia
az explanation csomag teljes felépítése alatt konzisztensen működött.

### Kereszt-batch duplikátumok (összesen, a projekt indulása óta)
- audit-kor talált, retroaktívan javított: 1 (`simple_qa_0185`/`0283`)
- import közben talált és javított (batch4-7): 7
- claude 0651-0750 batch-nél talált és javított: 1 (`simple_qa_0401`/`0692`)
- claude 0851-0950 batch-nél **jelzett, de hamis pozitívnak bizonyult**: 4
  (dedupe-eszköz-korlát: rövid, egyszavas sablonoknál a 0.9-es küszöb
  fölött is előfordulhat véletlen szöveg-egyezés teljesen eltérő tartalom
  mellett)
- claude 1051-1159 batch-nél: 1 ÚJ jelzés (`simple_qa_0734`/`1081`,
  sim=0.918), szintén hamis pozitív
- explanation 0001-0100, 0101-0200, 0201-0300, 0301-0400, 0401-0500,
  0501-0600, 0601-0700, 0701-0800, 0801-0900 és 0901-1003 (ZÁRÓ)
  batch-eknél: a régi 5 jelzés minden körben megismétlődött
- **explanation 0501-0600 batch-nél: 1 ÚJ, VALÓDI duplikátum**
  (`explanation_0531` vs `explanation_0227`, sim=1.0, azonos
  instrukció - "homokdűnék kialakulása") - felismerve és kiszűrve
  rejected-be.
- **explanation 0601-0700 batch-nél: 2 ÚJ, VALÓDI duplikátum**
  (`explanation_0681` vs `explanation_0244`, sim=0.901, "átlag kiugró
  értékek"; `explanation_0697` vs `explanation_0242`, sim=0.942,
  "exponenciális növekedés") - mindkettő a `matematika` témakörben,
  felismerve és kiszűrve rejected-be.
- **A 2. csomag (explanation) teljes záró mérlege: 1003 raw, 1000 clean,
  3 rejected** - mindhárom rejected sor valódi, helyesen kiszűrt
  kereszt-batch duplikátum volt. Részletek:
  `data/reports/explanation_1000_completion_audit.md`.
- **Jelenleg ismert, fennálló duplikátum a teljes korpuszban (2000 sor):
  0** (mindhárom explanation-explanation eset helyesen ki lett szűrve,
  mielőtt clean-be került volna).

## Nyitott tételek / kockázatok

- **Módszertani megfigyelés (nem hiba, csak dokumentálva)**: az
  `explanation` kategórián BELÜL (a másik kategóriák nélkül nézve) a
  `fizika` tag aránya 10.2%-ra nőtt, meghaladva a 8%-os küszöböt, mert
  a `fizika` gyakran másodlagos/kísérő tag volt sok STEM-bucketben. A
  TELJES korpuszon (simple_qa + explanation együtt, amit a folyamat
  minden batch-nél ténylegesen vizsgált) ez az arány mindvégig biztonságos
  maradt (5.7% a zárás után). Lásd részletesen:
  `data/reports/explanation_1000_completion_audit.md` 6. pont.
- **Szűkebb fogalmi terek (mint matematika) témaismétlődési kockázata**:
  bebizonyosodott, hogy jól definiált, kisebb fogalomkörű témáknál
  (alapvető matematikai/statisztikai fogalmak) nagyobb a véletlen
  ismétlődés esélye - lásd a 0601-0700 batch két duplikátumát. Ezt a
  tanulságot a jövőbeli csomagoknál (3-9) is érdemes alkalmazni: új
  batch tervezésekor át kell tekinteni a korábban már lefedett,
  szűk fogalmi témákat.
- **Dokumentált dedupe-eszköz-korlát**: rövid, egyszavas sablonoknál a
  0.9-es küszöb fölött is előfordulhat hamis pozitív. Jövőbeli
  hardening-javaslat: az `instruction_duplicates` kategóriánál vegye
  figyelembe az `output` hasonlóságát is.
- A **6. csomag** (többfordulós beszélgetés) JSONL séma-bővítést igényel -
  a jelenlegi séma egyfordulós. Ezt a felhasználónak explicit jóvá kell
  hagynia, mielőtt a 6. csomag elindul.
- A **8. csomag** (webes összefoglaló) csak megbízható forrással és URL-lel
  indulhat - ha nincs ilyen, a csomag BLOCKED.
- A **9. csomag** (saját projekt/MF-AI tudásanyag) kizárólag a repo/
  dokumentumok alapján készülhet, kitalálás nélkül.
- A `dataset_score.py` scorer dokumentált vakfoltja (nem méri a tartalmi
  mélységet) továbbra is fennáll - minden batch-nél a manuális mintavétel
  pótolja ezt.
- **Teljesítmény-megjegyzés**: a teljes korpuszos cross-dedupe futásideje
  korábban 15-30+ percig is elhúzódott (1000-1300 soron, részben a gép
  aktuális terhelése miatt). A 0301-0400 és 0401-0500 batch-eknél (1400,
  majd 1500 sor) a futás mindkétszer gyorsan lefutott, de ez
  valószínűleg a gép aktuális terhelésétől függ, nem a módszer alapvető
  javulásától - a strukturális O(n²) probléma továbbra is fennáll.
  Ahogy a korpusz tovább nő a hátralévő csomagokkal, érdemes lesz a
  cross-dedupe logikát hatékonyabbra cserélni (pl. csak az új sorokat
  futtatni a régiek ellen, ne teljes N×N összehasonlítást).

## 6. csomag - Bizonytalanság / forráskérés (instruction_core, cél 1000 sor) - batch-történet

Az új, bővített 17 000 soros instruction core szerint ez a **6. csomag** (a felhasználó pontosítása); a régi 4900 soros roadmap számozása ennél a csomagnál nem irányadó. Címkék: `bizonytalansag`, `forraskeres`, `nem_kamuzik`, `instruction_core`. A roadmap 6. csomagja (többfordulós beszélgetés, séma-bővítés) ettől független, nem indult.

| Batch | Forrás | Raw | Clean | Rejected | Commit | STÁTUSZ |
|---|---|---|---|---|---|---|
| `claude_uncertainty_source_request_0001_0100` | Claude-generált | 100 | **100** | 0 | b9018dd | **STABIL** |
| `claude_uncertainty_source_request_0101_0200` | Claude-generált | 100 | **100** | 0 | 2374937 | **STABIL** |
| `claude_uncertainty_source_request_0201_0300` | Claude-generált | 100 | **100** | 0 | 4aa79ba | **STABIL** |
| `claude_uncertainty_source_request_0301_0400` | Claude-generált | 100 | **100** | 0 | 668eae8 | **STABIL** |
| `claude_uncertainty_source_request_0401_0500` | Claude-generált | 100 | **100** | 0 | 9a35cc5 | **STABIL** |
| `claude_uncertainty_source_request_0501_0600` | Claude-generált | 100 | **100** | 0 | dfa7ba3 | **STABIL** |
| `claude_uncertainty_source_request_0601_0700` | Claude-generált | 100 | **100** | 0 | a9d089e | **STABIL** |
| `claude_uncertainty_source_request_0701_0800` | Claude-generált | 100 | **100** | 0 | 80c87c1 | **STABIL** |
| `claude_uncertainty_source_request_0801_0900` | Claude-generált | 100 | **100** | 0 | a066b3c (+ javítás cc9be38) | **STABIL** |
| `claude_uncertainty_source_request_0901_1000` | Claude-generált | 100 | **100** | 0 | d398f86 | **STABIL** |

Csomag: **1000 / 1000** (KÉSZ; completion audit: `data/reports/uncertainty_source_request_1000_completion_audit.md`).

- 0001-0100: 6 mód (20/16/16/16/16/16), 79 különböző téma-címke, 9 sor bemásolt szöveggel; schema 100/100, score 100.0, dedupe 0, kereszt-dedupe 0, safety 0, STABIL.
- 0101-0200: 7 mód (16/14/14/15/14/14 + **13 kontraszt-sor = 13%** magabiztos válasszal, mód-címke `kontraszt_magabiztos`), 100 különböző téma-címke, 5 sor bemásolt szöveggel; schema 100/100, score 100.0, dedupe 0, kereszt-dedupe a 3600 sorral 0, safety 0, STABIL. *általában* 26 -> 5, *nézd meg* 35 -> 5 sor.
- 0201-0300: 7 mód (15/14/14/14/14/15 + **14 kontraszt-sor = 14%**, ebből **13 összetettebb**, 2 bemásolt adatos), 100 különböző téma-címke, 6 sor bemásolt szöveggel; új területek: oktatás/iskola/kollégium 35, telefon/app/közösségi média 19, időjárás/sport 15, ügyintézés/jog/pénz/egészség 12, háztartás/vásárlás 11, utazás 8; bankkártya/jegyár/nyitvatartás 0. Schema 100/100, score 100.0, dedupe 0, kereszt-dedupe a 3700 sorral 0, safety 0, STABIL. *általában* 1, *nézd meg* 3, *segítek* 3.
- Clean előtt javítva (0201-0300): 2 a 0101-0200 batchével azonos instruction, 2 sablon- vagy tartalmi átfedés a korpusszal (köztük egy kontraszt-sor cseréje), nyitás-koncentráció (*Mert* 7 -> 3, *Ezt nem* 4 -> 1), ismétlődő fordulatok (*függ* 25 -> 15), nyelvtani hibák.
- Nyitott (0201-0300): a jelölő címkék (`instruction_core`, `bizonytalansag`, `forraskeres`, `nem_kamuzik`) a 3800 soros korpuszban 7.9%, a következő batch után átlépik a topic report 8%-os küszöbét; kontraszt-sorok változatosabb formái; *hivatalos* koncentráció.
- 0301-0400: 7 mód (15/14/14/14/14/15 + **14 kontraszt-sor = 14%**, ebből **10 hibás előfeltevést javító**, `hibas_elofeltevesjavitas` címkével), 100 különböző téma-címke, 5 sor bemásolt szöveggel; témák: telefon/app/technika 20, háztartás 17, ügyintézés/jog/pénz/egészség 15, utazás 11, sport 9, időjárás 8, közösségi média 8, vásárlás 6, hétköznapi félreértés 5, oktatás 1 (előző batchben 35). Schema 100/100, score 100.0, dedupe 0, kereszt-dedupe a 3800 sorral 0, safety 0, STABIL. *hivatalos* 0, *általában* 1, *nézd meg* 4.
- Clean előtt javítva (0301-0400): 4 kereszt-dedupe találat a `simple_qa` sorokkal (2 pontos egyezés), nyitás-koncentráció (*Ezt nem* 7 -> 1, *Nem,* nyitás a hibás előfeltevés sorokon 7 -> 1), nyelvtani hibák, *hivatalos* 14 -> 0.
- Topic report kivétel (0301-0400): a négy jelölő címke (`instruction_core`, `bizonytalansag`, `forraskeres`, `nem_kamuzik`) a 3900 soros korpuszban 10.3%, `[FIGYELEM]` jelzéssel; a felhasználó döntése szerint csomagjelölők, kivételként dokumentálva a riportban, adat és eszköz változatlan.
- Nyitott (0301-0400): igaz előfeltevésű (megerősítő) kontraszt-sorok, tényellenőrzés a magabiztos állításokra, a `hibas_elofeltevesjavitas` címke jövője, *érdemes* 9 sor, előzetes összevetés a `simple_qa` sablonokkal.
- 0401-0500: 7 mód (15/14/14/14/14/15 + **14 kontraszt-sor = 14%**: **6 hibás előfeltevést javító** (`hibas_elofeltevesjavitas`), **4 igaz előfeltevést megerősítő** (`igaz_elofeltevesmegerosites`), 4 hétköznapi tanács), 100 különböző téma-címke, 5 sor bemásolt szöveggel; témák: telefon/app/technika 20, ügyintézés/jog/pénz/egészség 16, háztartás 15, vásárlás 12, sport 12, utazás 11, közösségi média 8, hétköznapi félreértés 5, időjárás 1; `Mit tegyek, ha…?` instruction 0. Schema 100/100, score 100.0, dedupe 0, kereszt-dedupe a 3900 sorral 0, safety 0, STABIL. *érdemes* 5, *függ* 6, *nézd meg* 3.
- Clean előtt javítva (0401-0500): 1 batchen belüli azonos instruction, 1 validátor-elutasítás (`0439`, `garbled_output`: az *https* token), nyitás-koncentráció, *Ha megírod* 8 -> 4, nyelvtani hibák.
- Topic report kivétel (0401-0500): a négy jelölő címke (`instruction_core`, `bizonytalansag`, `forraskeres`, `nem_kamuzik`) a 4000 soros korpuszban 12.5%, `[FIGYELEM]` jelzéssel; csomagjelölők, kivételként dokumentálva a riportban, adat és eszköz változatlan.
- Nyitott (0401-0500): előfeltevéses sorok sablonszerűsége (részben igaz sorok kellenek), emberi tényellenőrzés a riportban felsorolt közismert állításokra, az `igaz_elofeltevesmegerosites` címke jóváhagyása, *szolgáltató* 17 / *kérdezd* 16 / *ezért* 27 sor, egészség/jog/pénz átnézés.
- 0501-0600: 7 mód (15/14/14/14/14/15 + **14 kontraszt-sor = 14%**: 3 hibás előfeltevést javító (`hibas_elofeltevesjavitas`), 3 igaz előfeltevést megerősítő (`igaz_elofeltevesmegerosites`), **4 részben igaz előfeltevést pontosító** (`reszben_igaz_elofeltevespontositas`), 4 hétköznapi tanács; nyitott kérdésformák, zárt *Ha…, akkor…?* 0), 100 különböző téma-címke, 9 sor bemásolt szöveggel; témák: telefon/app/technika 21, háztartás 17, ügyintézés/jog/pénz/egészség 15, utazás 12, sport 11, vásárlás 11, közösségi média 5, hétköznapi félreértés 4, időjárás 4; oktatás 0; `Mit tegyek, ha…?` instruction 0. Schema 100/100, score 100.0, dedupe 0, kereszt-dedupe a 4000 sorral 0, safety 0, STABIL. *szolgáltató* 0, *kérdezd* 0, *ezért* 6, *érdemes* 4, *függ* 6, *nézd meg* 1.
- Clean előtt javítva (0501-0600): 2 azonos instruction (`Van ebben igazság?`, egyezett az 5. batch `0412` sorával), *ezért* 20 -> 6, *nézd meg* 5 -> 1, nyelvtani hibák.
- Topic report kivétel (0501-0600): a négy jelölő címke (`instruction_core`, `bizonytalansag`, `forraskeres`, `nem_kamuzik`) a 4100 soros korpuszban 14.6%, `[FIGYELEM]` jelzéssel; csomagjelölők, kivételként dokumentálva a riportban, adat és eszköz változatlan.
- Nyitott (0501-0600): az előfeltevéses kérdések zárt jellege (implicit előfeltevésű sorok kellenek), emberi tényellenőrzés a riportban felsorolt közismert állításokra (különösen `0506`, `0518`, `0541`, `0542`, `0545`), az új `reszben_igaz_elofeltevespontositas` címke jóváhagyása, egészség/jog/pénz átnézés, *pontos* 19 / *ellenőrizd* 7 sor.
- 0601-0700: 7 mód (15/14/14/14/14/15 + **14 kontraszt-sor = 14%**: 4 hibás előfeltevést javító, 4 igaz előfeltevést megerősítő, 3 részben igaz előfeltevést pontosító, 3 egyértelműen megoldható hétköznapi feladat plusz címke nélkül; mind a 14 nyitott, természetes forma, zárt `Ha…, akkor…?` szerkezet 0), 100 különböző téma-címke. Schema 100/100, score 100.0, dedupe 0, saját kereszt-dedupe a 4100 sorral 0, safety 0, STABIL.
- Az 5. batch (`0501-0600`) `0506, 0518, 0541, 0542, 0545` sorának tényellenőrzése (WebSearch, elsődleges/hivatalos forrásokkal: Red Cross, CDC, Mayo Clinic, NASM/PMC, Runners Connect/Healthline): mind az 5 állítás megerősítve, két nyitott árnyaló megjegyzéssel (`0506`, `0518`), a clean fájl nem módosult.
- Clean előtt javítva (0601-0700): 1 ékezetes kind-tag, mód-eloszlás hiánya (`kitalalas_elutasitasa` 12 -> 14, 2 új sor), nyitás-koncentráció (`Ezt nem ismerem, és…` 3 -> 1 szó szerinti ismétlés, `Nézd meg…` 5 -> 3).
- Topic report kivétel (0601-0700): a négy jelölő címke a 4200 soros korpuszban 16.7%, `[FIGYELEM]` jelzéssel; csomagjelölők, kivételként dokumentálva a riportban, adat és eszköz változatlan.
- Nyitott (0601-0700): `0518` pontosítási lehetőség (nagyobb étkezés utáni várakozási idő), `0506` tudományos árnyalás (rövid, teljes rutinba ágyazott statikus nyújtás), az `ellenorzesi_ut` mód sablon-ismétlődése, a `gen_usr7.py` / `usr_check7.py` scriptek a tools/ alá emelése (nem történt meg), egészség-közeli sorok nagyobb mennyiségnél külön átnézést igényelnek.
- Célzott javítás (`v1.13.8-dataset-fix`): az 5. batch (`0501-0600`) `0518` sorát a Mayo Clinic art-20045506 forrás alapján pontosítottam (nagyobb étkezés utáni várakozás 1-2 óráról 3-4 órára javítva), csak a clean fájlban, a raw változatlan. A `0506` sort ellenőriztem, nem igényelt javítást. A `0541` és `0542` sort korábban már ellenőriztem és megerősítettem.
- Kérdésforma-besorolás pontosítása (0601-0700): a korábbi riport „ugye?” és „Ez így igaz?” sorokat tévesen nyitottnak jelölt; a pontosított kritérium szerint 10/14 valóban nyitott (a minimum 8 továbbra is teljesül), adatmódosítás nem szükséges, csak a riport-besorolás javult.
- 0701-0800: 7 mód (15/14/14/14/14/15 + **14 kontraszt-sor = 14%**: 5 hibás előfeltevést javító, 4 igaz előfeltevést megerősítő, 2 részben igaz előfeltevést pontosító, 3 egyértelműen megoldható hétköznapi feladat; mind a 14 nyitott a pontosított kritérium szerint). Az új kontraszt-állításokat a clean elfogadás előtt WebSearch-csel ellenőriztem (Harvard Health, Johns Hopkins, Wine Spectator, Cleveland Clinic, Chargie, AAP/Pediatrics, FAA, US EPA/Nature, Sleep Foundation, CDC); a részletek a batch riportjában. Az `ellenorzesi_ut` mód mondatszerkezete változatos: 15 sorból csak 2 „Hogyan/Honnan” kezdésű, a többi felszólító vagy bemásolt helyzetet idéző forma. Schema 100/100, score 100.0, dedupe 0, saját kereszt-dedupe a 4200 sorral 0, safety 0, STABIL.
- Clean előtt javítva (0701-0800): 3 hiányzó mód-sor pótlása, 1 ékezetes kind-tag, nyitás-koncentráció (`Ezt nem ismerem, és…` 8 -> 3), 2 nyelvtani hiba.
- Topic report kivétel (0701-0800): a négy jelölő címke a 4300 soros korpuszban 18.6%, `[FIGYELEM]` jelzéssel; csomagjelölők, kivételként dokumentálva a riportban, adat és eszköz változatlan.
- Nyitott (0701-0800): `0743` témarokonság az 5. batch `0663` sorával (0.727, a 0.9-es küszöb alatt), az `fp_ingyenes_app_haszna` kontraszt-állítás nem kapott dedikált külső forrást (közismert üzleti modell), a `gen_usr8.py`/`usr_check8.py` scriptek tools/ alá emelése (nem történt meg), egészség-közeli és jogi-pénzügyi sorok (34, ebből 9 hard) nagyobb mennyiségnél külön átnézést igényelnek.
- Célzott javítás (második, `v1.13.10-dataset-fix`, commit `e97ba92`): az 5. batch (`0501-0600`) `0518` sorát ismét pontosítottam, mert a korábbi javítás után is szerepelt benne egy, a Mayo Clinic cikkben (`art-20045506`) nem szereplő „fél óra” szabály a gyors harapnivalóra; a cikk erre nem ad számszerű időt, csak azt írja, hogy sokan közvetlenül edzés előtt is esznek, ez egyéni megítélés kérdése. A nagyobb/kisebb étkezésre vonatkozó 3-4/1-3 órás ablak (ami a forrásban ténylegesen szerepel) változatlan maradt. Csak a clean fájlban, a raw változatlan. A `0506` sort újra ellenőriztem, új tartalmi indok nem merült fel, nem módosítottam.
- Célzott javítás: a 8. batch (`0701-0800`) `0708` (`fp_ingyenes_app_haszna`) sorának „a legtöbb ingyenes alkalmazás… bevételt termel” állítását „sok”-ra szűkítettem, mert erre a többségi állításra nincs elsődleges forrás, csak a bevételi mechanizmusok (hirdetés, adatelemzés, prémium funkció) tényleges létezésére. Forrás: Google Play Console hivatalos monetizációs dokumentációja; Statista (az appok túlnyomó többsége ingyenes, de ez önmagában nem igazolja, hogy mindegyik bevételt is termel). Csak a clean fájlban, a raw változatlan.
- `0743` (8. batch) és `0663` (7. batch, `0601-0700`, NEM az 5. batch, ahogy a korábbi riport tévesen írta) teljes tartalmi összehasonlítása: mindkettő `kitalalas_elutasitasa` diagnózis-elutasítás, de eltérő adattípus (numerikus labor vs. leíró gyerektünet), eltérő alany (felnőtt saját magáról vs. szülő a gyerekéről) és eltérő sürgősségi keretezés — mindkét sor tartalmi indokkal megtartva, adatmódosítás nem történt.
- A 8. batch 34 egészség-közeli/jogi/pénzügyi sorának manuális átnézése pótolva és az automatikus jelzéstől explicit elkülönítve: a 8 hard sor (`0701, 0714, 0724, 0735, 0743, 0759, 0778, 0786`) és a fennmaradó 26 könnyebb/közepes sor teljes szövegét elolvasva egyikük sem ad diagnózist, személyes jogi verdiktet vagy konkrét befektetési tanácsot. A korábbi riport 9 hard sort jelentett, az újrafuttatás 8-at ad — az eltérés gyökere nincs pontosan visszavezetve (valószínűleg apró regex-eltérés a két futás között), ez csak az automatikus számlálást érinti.
- 0801-0900: 7 mód (14 kontraszt + 14/14/15/14/14/15 a hat alapmód között: `valtozo_adat`, `forras_nelkul_nem_tudhato`, `pontositas_kell`, `altalanos_valasz_ellenorzessel`, `kitalalas_elutasitasa`, `ellenorzesi_ut`). **14 kontraszt-sor = 14%**: 4 hibás előfeltevést javító, 4 igaz előfeltevést megerősítő, 3 részben igaz előfeltevést pontosító, 3 egyértelműen megoldható hétköznapi feladat; mind a 14 nyitott a pontosított („ugye?”/„Ez így igaz?” = zárt) kritérium szerint. Az 8 új kontraszt-állítást WebSearch-csel ellenőriztem (Cornell/ScienceDaily, McGill, Detour/Sugarcreek Coffee, Mueller & Oppenheimer, Harvard Health, Sleep Foundation, Cochrane, Rutgers/Scientific American, Stanford Medicine/Cleveland Clinic). Az `ellenorzesi_ut` mód 15 új, korábban nem használt helyzetet ír le (bérleti kaució, használtautó-hirdetés, vámkezelési SMS, befektetési influencer, piramisjáték, tartozás-hívás, tech support hívás, nyereményes e-mail, használt telefon, albérlet, uccai adománygyűjtő, kriptotőzsde, örökség-email, üdülési jog, előlegkérő állás). Schema 100/100, score 100.0, dedupe 0, saját kereszt-dedupe a 4300 sorral 0, safety 0, STABIL.
- Clean előtt javítva (0801-0900): 2 quality_notes-ütközés (egyforma szöveg), 1 ékezetes kind-tag, 1 nyelvtani hiba (`a esküvőmre` -> `az esküvőmre`), az összes mód nyitó-mondatának tudatos, előzetes változatossá tétele (nem utólagos javítás igényelt).
- Topic report kivétel (0801-0900): a négy jelölő címke a 4400 soros korpuszban 20.4%, `[FIGYELEM]` jelzéssel; csomagjelölők, kivételként dokumentálva a riportban, adat és eszköz változatlan.
- 0901-1000 (záró batch): 7 mód (**14 kontraszt** + valtozo_adat 12, forras_nelkul 16, pontositas 15, altalanos 15, kitalalas 16, ellenorzesi_ut 12 = 100; csomagszintű célelosztás 144/144/144/144/147/152 + 125 kontraszt). 14 kontraszt-sor: 4 hibás, 4 igaz, 3 részben igaz, 3 megoldható; 12/14 nyitott („ugye?” és „Igaz, hogy…?” = zárt). Az ellenorzesi_ut mód 12 nem csalás jellegű helyzet. Témák a 900 sor lefedettségi térképe alapján (tudásbeli határ, mértékegység-többértelműség, informatikai ellenőrzés, háztartás). Forrás: NASA, NWS, USGS, NOAA (2), Smithsonian, EPA, hongkongi CFS, The Conversation, National Honey Board (közvetlenül olvasva), részletek keresési összefoglalókból. Schema 100/100, score 100.0, dedupe 0, keresztduplikáció a 4400 sorral 0, regresszió STABIL. Riport: `data/reports/claude_uncertainty_source_request_0901_1000_report.md`.
- Megszakadt teljes korpuszos futás: a `tools/dataset_cross_dedupe.py data/clean` 11+ óra után kimenet nélkül leállítva (a 4400 sorra ~5-6 óra becsülhető: az eredeti tool 1500 soron 39 percig futott); helyette szakaszolt, azonos szemantikájú (matematikailag pontos elő-szűrésű) N×N futás, 4500 sor, 27 mp, 7 talált pár mind simple_qa/step_by_step csomagban; ekvivalencia igazolva. A korábbi „elakadt” minősítés nem volt igazolt.
- Audit-javítások (`v1.13.12-dataset-fix`, commit `cc9be38`): 10 sor (0864 szabálysértési elévülés 6 hónap/2 év, 0829, 0849, 0898 fékbetét mérföld/km, 0816, 0787, 0842 csere, 0641 tartalmi egyedisítés, 0317/0782 notes). Csak clean, raw változatlan.
- Completion audit (1000 sor): darabszám/azonosító/séma/biztonság/duplikáció (0,9 fölött 0) kész; hard sorok (127) teljes szövegű átnézése kész; forrásellenőrzés részleges (K 13 / Ö 24 / R 28 / A-D 59 a 125 kontraszt-soron); kontraszt-arány 12,5%, ebből 74 valódi előfeltevés-alapú. A 34 sor / 9 hard eltérés oka: két különböző mennyiség (batch-szintű hard 9 vs. kulcsszavas halmazon belüli hard 7-8); a 34-es szám nem reprodukálható. Riport: `data/reports/uncertainty_source_request_1000_completion_audit.md`.
- Nyitott (nem blokkoló, 6. csomag): válaszsablon „…és azt sem tudom, melyik…” 49 sor, „Hogyan ellenőrizzem…” 29 sor az ellenorzesi_ut módban; 39 előtag nélküli kontraszt-sor újracímkézése; 0506 árnyalás; Ö-forrású állítások közvetlen újraolvasása, jogi számok jogászi ellenőrzése; független emberi/szakértői átnézés; 7 más-csomagi ≥0,9 pár (simple_qa, step_by_step) tartalmi értékelése; scratchpad szkriptek tools/ alá emelése csak külön jóváhagyással.
- 2. audit-kör (`v1.13.15-dataset-fix` 24094fd, `v1.13.16-dataset-audit`): 125 kontraszt-sor soronkénti besorolása (P 36 / P* 18 / N 4 / N* 2 / O 1 / C 15 / D 39 / E 10), 123 kulcsszavas sor elolvasva (8 javítva), 30 sor forrás-igazítva (raw változatlan, 4500 sor változatlan), 6 sor kizárva a tanításból felülvizsgálatig (0220, 0829, 0849, 0864, 0602, 0898; lista: `data/reports/audit_evidence/uncertainty_source_request_1000/training_exclusion_pending_review.txt`), 0506 lezárva, 7 hasonlósági pár mind megtartva (kimenet-hasonlóság 0,02-0,27), 49+30 sablon-sor nem változott, gyorsított N×N ellenőrzés reprodukálható (audit_evidence/…/code, README, data_version), végső N×N 7 pár / 0 output / 0 id. STÁTUSZ: KORLÁTOZOTT LEZÁRÁS (nem teljesen ellenőrzött, NEM training-ready); tanításra jelölt halmaz 4494/4500, a 6 kizárt sor kihagyása csak dokumentált, technikailag nem kikényszerített (kötelező tanítás előtti feladat TE-1). Új adatcsomag és tanítás nem indult. Jelentés: `data/reports/uncertainty_source_request_1000_audit2_closure.md`.
- Topic report kivétel (0901-1000): a négy jelölő címke a 4500 soros korpuszban 22.2%, `[FIGYELEM]` jelzéssel; csomagjelölők, kivételként dokumentálva, adat és eszköz változatlan.
- Clean előtt javítva (0101-0200): kereszt-duplikátum (`0105` = `simple_qa_0507`), batch-közi hasonlóság (`0126`), nyitás-koncentráció, ismétlődő fordulatok (*érdemes*, *segítek*, *ha megírod*), nyelvtani hibák.
- Nyitott: kontraszt-sorok összetettebb változata, kontraszt-sorok címke-szemantikája (`bizonytalansag` tag kontraszt-soron is), tényellenőrzés a magabiztos állításokra, egészség/jog/pénz átnézés nagyobb mennyiségnél.
- Riportok: `data/reports/claude_uncertainty_source_request_0001_0100_report.md`, `data/reports/claude_uncertainty_source_request_0101_0200_report.md`, `data/reports/claude_uncertainty_source_request_0201_0300_report.md`, `data/reports/claude_uncertainty_source_request_0301_0400_report.md`, `data/reports/claude_uncertainty_source_request_0401_0500_report.md`, `data/reports/claude_uncertainty_source_request_0501_0600_report.md`, `data/reports/claude_uncertainty_source_request_0601_0700_report.md`, `data/reports/claude_uncertainty_source_request_0701_0800_report.md`, `data/reports/claude_uncertainty_source_request_0801_0900_report.md`, `data/reports/claude_uncertainty_source_request_0901_1000_report.md`, `data/reports/uncertainty_source_request_1000_completion_audit.md`.

## Utolsó frissítés
Az MT-4 (renderelés és exportálás kizárási szűrővel) elkészült és tesztelt (`data/reports/mt4_report.md`). Állapotok külön: technikai működés (tesztelt, STABIL a mesterséges/szintetikus bemenetekre és a valódi TE-1 exportra), export (elkészítve, nem jóváhagyott), tartalmi ellenőrzés (nyitott), tanítási engedély (nincs; training_ready: false mindenhol). Valódi többfordulós adat és a 7-10. csomag adata nem létezik; új adatgenerálás és tanítás nem indult. A 6. csomag: KORLÁTOZOTT LEZÁRÁS. Teljes clean korpusz: 4500 sor; TE-1 export: 4494. Következő lépés: csak a felhasználó külön jóváhagyásával (MT-5).
