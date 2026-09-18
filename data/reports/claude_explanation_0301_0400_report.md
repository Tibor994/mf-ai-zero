# Negyedik FELÜGYELT Claude-generált "magyarázós példa" batch - explanation 0301-0400

- Forrás: **Claude-generált**, 100 db, kézzel megírt, majd a teljes meglévő
  pipeline-nal ellenőrzött sor. A **2. csomag (1000 db magyarázós példa)**
  folytatása.
- `category`: `explanation`, `source`: `synthetic_claude`.
- **Ez továbbra is TESZT kör** - a modellt NEM tanítottuk erre az adatra,
  webapp/backend kód nem változott.

## 1. Számok

| Mérőszám | Érték |
|---|---|
| Raw sorok | 100 |
| Validáláson elfogadva | 100 |
| Validáláson elutasítva | 0 |
| Kereszt-batch **jelzett** (0.9 fölötti) egyezés (teljes 1400 soros korpuszon) | 5 |
| Ebből az ÚJ explanation batch-et érintő | **0** |
| **Végleges clean sorok** | **100** |
| **Rejected sorok** | **0** |
| Átlag quality_score | **100.0** |
| Flag-et kapott sor | 0 |
| Difficulty eloszlás | medium: 90, hard: 10 |

## 2. Ellenőrzési lépések (teljes pipeline)

### 2.1 Schema validate
Mind a 100 sor strukturálisan érvényes (`tools/dataset_validate.py`).

### 2.2 Kizárt témák explicit ellenőrzése
A kizárt kifejezések listáján (nexora, mf-ai, wifi, vpn, cookie,
adathalászat, tanítóadat, adatminőség, modelltesztelés, naplóírás,
üvegházhatás, bocsánat, ajándék) **1 nyers találat** volt:
- "ajándék" (`explanation_0372`, "...ad nekünk valamit, akár egy apró
  ajándékot vagy szívességet...") - a viszonzás elvét (reciprocitás)
  magyarázó pszichológiai sor, semmilyen kapcsolatban nincs a kizárt
  MF-AI/Nexora azonosság-témával. **Hamis pozitív, megtartva.**

AI-tagelt sor: **0/100**. `technika`-tagelt sor: **0/100**.

### 2.3 Teljes korpuszos cross-dedupe (a TELJES 1300 soros meglévő korpusz +
    ez a 100 sor, 0.9 küszöb, összesen 1400 sor)

A dedupe **5 db 0.9 fölötti instruction-hasonlósági egyezést** jelzett,
`id_duplicates`: 0, `output_duplicates`: 0. Mind az öt jelzés a **korábban
már dokumentált, megtartott simple_qa hamis pozitívok pontos
megismétlődése** - egyik sem érinti ezt vagy bármelyik korábbi
explanation batch-et:

| kept | duplicate | similarity | Megjegyzés |
|---|---|---|---|
| simple_qa_0851 | simple_qa_0857 | 0.904 | Korábbról ismert hamis pozitív (rövid sablon, eltérő tartalom). |
| simple_qa_0851 | simple_qa_0859 | 0.919 | Korábbról ismert hamis pozitív. |
| simple_qa_0671 | simple_qa_0914 | 0.919 | Korábbról ismert hamis pozitív. |
| simple_qa_0734 | simple_qa_1081 | 0.918 | Korábbról ismert hamis pozitív (kémiai fogalompár). |
| simple_qa_0915 | simple_qa_0489 | 0.921 | Korábbról ismert hamis pozitív. |

**Az ÚJ explanation_0301-0400 batch egyik sora sem szerepel egyik
jelzésben sem.**

### 2.4 `tools/dataset_topic_report.py`

**A teljes, egyesített korpuszon** (1000 simple_qa + 400 explanation =
1400 sor):

| Tag | 1300 sornál (előző kör) | **1400 sornál (most)** |
|---|---|---|
| technika | 7.0% (91) | **6.5% (91)** - tovább csökken |
| iskola | 5.5% (71) | **5.1% (71)** - tovább csökken |
| biológia | 4.2% (55) | 4.2% (59) - lényegében stagnál |
| csillagászat (ÚJ) | - | 3.4% (47) |
| konyha (ÚJ) | - | 3.3% (46) |
| gazdaság (bővült) | 2.5% (32) | 3.1% (44) |
| pszichológia (ÚJ) | - | 3.0% (42) |

**Túlreprezentált tagek: NINCS** (legmagasabb: technika 6.5%, jóval a
8%-os küszöb alatt).

Ez a batch 5 teljesen új témablokkot vezetett be (filmes/elbeszélés-
elméleti mechanizmusok, gasztronómiai/kémiai főzési folyamatok,
csillagászati/űrkutatási mechanizmusok, fogyasztói pszichológia/
marketing-mechanizmusok semleges, ismeretterjesztő szemléletben,
állattartás/kisállat-viselkedés) - tudatosan elkerülve a `technika`,
`iskola` és `biológia` tageket, amik az előző kör legmagasabb arányú
tagjai voltak.

### 2.5 `dataset_score.py`
Mind a 100 sor **100/100** pontot kapott, flag nélkül.

### 2.6 Safety/firewall ellenőrzés
- **`src/guard.py` `looks_like_identity_bleed()`**: **0 találat**.
- **Kiegészítő kulcsszó-szűrés**: **3 nyers találat**, mindhárom
  manuálisan ellenőrizve és **hamis pozitívnak** bizonyult:
  - "adag" (`explanation_0302`: "A jó alkotók tudatosan **adagolják** a
    feszültséget" - elbeszélési tempó, nem gyógyszeradag).
  - "adag" (`explanation_0312`: "...fokozatosan, a cselekménybe ágyazva
    **adagolják** ezt az információt" - elbeszélési technika, nem
    gyógyszeradag).
  - "kezelés" (`explanation_0313`: "...a humor egy komoly történet
    feszültségének **kezelésére**" - elbeszélési hangulatkezelés, nem
    orvosi kezelés).
- **Fogyasztói pszichológia blokk (361-380) külön is átnézve**: minden
  sor a jelenség semleges, ismeretterjesztő leírását adja a
  **fogyasztó/megfigyelő szemszögéből** ("miért hatunk mi", "hogyan
  érzékeljük"), egyik sem ad utasítást arra, hogyan manipuláljunk
  vásárlókat - ez tudatosan így lett megfogalmazva a generálás során.

## 3. Manuális mintavételes tartalmi átnézés (20 sor, minden témablokkból 4)

| id | Instruction | Értékelés |
|---|---|---|
| explanation_0302 | Miért fontos a feszültség fenntartása egy történetben? | Pontos elbeszéléselméleti fogalom. OK. |
| explanation_0308 | Miért fontos a hangkulissza (háttérhangok) egy film vagy játék élményében? | Semleges, technikai magyarázat. OK. |
| explanation_0314 | Miért fontos a konzisztens szabályrendszer egy fantáziavilágban (worldbuilding)? | Pontos, összetettebb fogalom. OK. |
| explanation_0319 | Hogyan hat a történet befejezésének módja az egész mű megítélésére? | Kiegyensúlyozott elbeszélési elv. OK. |
| explanation_0322 | Hogyan működik a kelesztés a kenyérkészítésben? | Pontos biológiai-kémiai folyamat. OK. |
| explanation_0328 | Hogyan működik a pácolás a hús ízesítésében és puhításában? | Pontos, veszélytelen konyhai magyarázat. OK. |
| explanation_0334 | Hogyan működik a karamellizálás kémiai szempontból? | Pontos kémiai folyamat. OK. |
| explanation_0339 | Miért fontos a megfelelő keverési technika egy tészta elkészítésénél? | Gyakorlati, veszélytelen tanács. OK. |
| explanation_0343 | Hogyan hal meg egy csillag? | Tudományosan pontos, összetettebb fogalom. OK. |
| explanation_0348 | Miért nem tud a fény kiszabadulni egy fekete lyukból? | Pontos asztrofizikai magyarázat. OK. |
| explanation_0353 | Hogyan alakulnak ki a meteorrajok? | Pontos csillagászati mechanizmus. OK. |
| explanation_0359 | Hogyan hat a mikrogravitáció az emberi testre hosszabb űrutazás során? | Semleges élettani magyarázat, nem orvosi tanács. OK. |
| explanation_0362 | Hogyan befolyásolja a csomagolás a termékről alkotott benyomásunkat? | Semleges, fogyasztó-szemszögű pszichológiai magyarázat. OK. |
| explanation_0369 | Miért hatnak ránk erősebben a veszteségek, mint az ugyanolyan mértékű nyereségek? | Pontos, tudományosan megalapozott fogalom. OK. |
| explanation_0374 | Hogyan befolyásolja a "csoport" tagjának érzése a vásárlási döntéseinket? | Semleges, nem manipulatív útmutatás. OK. |
| explanation_0380 | Hogyan hat a hiány érzése (korlátozott mennyiség) a vágyunk erősségére egy termék iránt? | Semleges pszichológiai mechanizmus. OK. |
| explanation_0383 | Miért nyalogatja magát gyakran a macska? | Pontos, veszélytelen etológiai magyarázat. OK. |
| explanation_0387 | Miért van szüksége a legtöbb háziállatnak mentális stimulációra, nem csak fizikai mozgásra? | Gyakorlati, felelős állattartási elv. OK. |
| explanation_0392 | Hogyan tájékozódnak a macskák a sötétben ilyen jól? | Pontos élettani magyarázat. OK. |
| explanation_0398 | Hogyan érzékelik a kutyák a szagokat ennyivel érzékenyebben, mint az emberek? | Pontos élettani magyarázat. OK. |

**Eredmény: 20/20 sor megfelelt.**

## 4. Fájlok

- Raw: `data/raw/claude_explanation_0301_0400_raw.jsonl` (100 sor)
- Clean: `data/clean/claude_explanation_0301_0400_clean.jsonl` (100 sor)
- Rejected: `data/rejected/claude_explanation_0301_0400_rejected.jsonl` (0 sor)

## 5. Regressziós teszt
`tests/test_v1_7_4_dataset_foundation.py` - **minden teszt sikeres, STÁTUSZ:
STABIL**.

## 6. Amit ez a kör NEM tett

- **Nem indított tanítást.**
- **Nem módosított webapp/backend kódot.**
- **Nem nyúlt a régi clean fájlokhoz.**

---

## Végső összegzés

- Raw sorok száma: **100**
- Clean sorok száma: **100**
- Rejected sorok száma: **0**
- Kereszt-batch duplikátumok száma: **0** (mind az öt jelzés a korábbi
  simple_qa hamis pozitívok megismétlődése)
- Átlag quality_score: **100.0**
- Topic report (röviden): batch önmagában 5 vadonatúj témakörre
  fókuszált (filmes/elbeszéléselméleti mechanizmusok, gasztronómiai/
  kémiai főzési folyamatok, csillagászati/űrkutatási mechanizmusok,
  fogyasztói pszichológia/marketing-mechanizmusok semleges
  szemléletben, állattartás/kisállat-viselkedés) - tudatosan elkerülve
  a `technika`, `iskola` és `biológia` tageket; a teljes 1400 soros
  korpuszon **nincs túlreprezentált tag** (legmagasabb: technika 6.5%,
  tovább csökkenő trend).
- 20 soros manuális mintavétel eredménye: **20/20 megfelelt**.
- **Egyedi clean explanation sorok jelenleg összesen: 400 / 1000.**
- **Hiányzik még a 2. csomag céljához: 600 sor.**

**STÁTUSZ: STABIL.**
