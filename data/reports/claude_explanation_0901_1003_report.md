# Tizedik, ZÁRÓ FELÜGYELT Claude-generált "magyarázós példa" batch - explanation 0901-1003

- Forrás: **Claude-generált**, 103 db, kézzel megírt, majd a teljes meglévő
  pipeline-nal ellenőrzött sor. Ez a **2. csomag (1000 db magyarázós
  példa) ZÁRÓ batch-e** - ezzel a csomag pontosan eléri az 1000/1000 clean
  sort (897 + 103 = 1000).
- `category`: `explanation`, `source`: `synthetic_claude`.
- **Ez továbbra is TESZT kör** - a modellt NEM tanítottuk erre az adatra,
  webapp/backend kód nem változott.

## 1. Számok

| Mérőszám | Érték |
|---|---|
| Raw sorok | 103 |
| Validáláson elfogadva | 103 |
| Validáláson elutasítva | 0 |
| Kereszt-batch **jelzett** (0.9 fölötti) egyezés (teljes 1897 soros korpusz + 103 sor = 2000 sor) | 5 |
| Ebből az ÚJ explanation batch-et érintő | **0** |
| **Végleges clean sorok** | **103** |
| **Rejected sorok** | **0** |
| Átlag quality_score | **100.0** |
| Flag-et kapott sor | 0 |
| Difficulty eloszlás | medium: 93, hard: 10 |

## 2. Ellenőrzési lépések (teljes pipeline)

### 2.1 Schema validate
Mind a 103 sor strukturálisan érvényes (`tools/dataset_validate.py`).

### 2.2 Kizárt témák explicit ellenőrzése
**1 találat** a kizárt lista "ajándék" tagjára (`explanation_0930`:
"...ajándékozás vagy távolsági kereskedelem esetén..." - gyűrűméretezés
történelmi szabványosítását magyarázza, semleges kontextus, semmi köze a
kizárt MF-AI/Nexora témához). **Hamis pozitív, megtartva.**

AI-tagelt sor: **0/103**. `technika`-tagelt sor: **0/103**.
`matematika`-tagelt sor: **0/103** (tudatosan elkerülve, folytatva az
előző két batch gyakorlatát).

### 2.3 Teljes korpuszos cross-dedupe (a TELJES 1897 soros meglévő korpusz +
    ez a 103 sor, 0.9 küszöb, összesen 2000 sor)

A dedupe **5 db 0.9 fölötti instruction-hasonlósági egyezést** jelzett,
`id_duplicates`: 0, `output_duplicates`: 0. Mind az öt jelzés a **korábban
már dokumentált, megtartott simple_qa hamis pozitívok pontos
megismétlődése**:

| kept | duplicate | similarity |
|---|---|---|
| simple_qa_0851 | simple_qa_0857 | 0.904 |
| simple_qa_0851 | simple_qa_0859 | 0.919 |
| simple_qa_0671 | simple_qa_0914 | 0.919 |
| simple_qa_0734 | simple_qa_1081 | 0.918 |
| simple_qa_0915 | simple_qa_0489 | 0.921 |

**Az ÚJ explanation_0901-1003 batch egyik sora sem szerepel egyik
jelzésben sem.** Mind a 103 sor clean-be kerülhetett, pontosan lezárva a
csomagot 1000/1000-en.

### 2.4 `tools/dataset_topic_report.py`

**A teljes, egyesített korpuszon** (1000 simple_qa + 1000 explanation =
2000 sor): legmagasabb tag fizika 5.7%, technika 4.5% (tovább csökkenő
trend a csomag egész felépítése alatt: 12.8%→...→4.5%). **Túlreprezentált
tagek: NINCS.**

Ez a batch 5 teljesen új témablokkot vezetett be (bőrfeldolgozás/cserzés,
ékszerészet/drágakőcsiszolás, szappan/tisztítószer-kémia, hangszerkészítés,
fűszerkereskedelem/fűszertörténet) - tudatosan elkerülve a `technika`,
`iskola`, `biológia` és `matematika` tageket.

### 2.5 `dataset_score.py`
Mind a 103 sor **100/100** pontot kapott, flag nélkül.

### 2.6 Safety/firewall ellenőrzés
- **`src/guard.py` `looks_like_identity_bleed()`**: **0 találat**.
- **Kiegészítő kulcsszó-szűrés**: **19 nyers találat** (a szappan/
  tisztítószer-kémia bucket miatt megnövekedett szám, mert az inherensen
  lúg-/vegyszerkémiáról szól), mindegyik manuálisan ellenőrizve:
  - "lúg"/"vegyszer" találatok (8 sor, 0944-0960): a szaponifikáció
    kémiáját írják le, beleértve **explicit, biztonság-pozitív
    figyelmeztető tartalmat** is (pl. `explanation_0952`: védőfelszerelés
    használatának indoklása lúgkezelésnél; `explanation_0960`: háztartási
    vegyszerek véletlen összekeverésének veszélyeire figyelmeztet). Egyik
    sor sem ad konkrét recepteket vagy mennyiségeket, ami károkozásra
    alkalmas lenne - kizárólag általános kémiai/biztonsági
    ismeretterjesztés.
  - "kezelés" találatok (5 sor): rendre bőrkondicionálás, drágakő-kezelés,
    vízkezelés, fűszerkezelés kontextusban - egyik sem orvosi.
  - "ajándék" (1 sor): lásd 2.2 pont.
  - "mérgez"/"adag" (2 sor): "mérgező gázokat termelhetnek" (vegyszer-
    összekeverés elleni figyelmeztetés) és "fűszerek adagolása" (konyhai
    kontextus) - egyik sem veszélyes útmutatás.
- **Szappan/vegyipar blokk (943-963) külön, kiemelt figyelemmel átnézve**
  a lúgkémiai tartalom miatt: minden sor **oktató jellegű, folyamatokat és
  okokat magyaráz, nem recepteket vagy pontos mennyiségeket ad meg**. A
  biztonsági vonatkozású sorok (0952, 0960) kifejezetten a veszélyek
  tudatosítását és a védekezést szolgálják, ami megfelel a korábban már
  jóváhagyott mintának (pl. kovácsműhelyi védőfelszerelés, bányászati
  robbantásbiztonsági tartalom).

## 3. Manuális mintavételes tartalmi átnézés (20 sor, minden témablokkból 4)

| id | Instruction | Értékelés |
|---|---|---|
| explanation_0901 | Miért kell a nyersbőrt cserzeni? | Pontos, veszélytelen kémiai-technikai magyarázat. OK. |
| explanation_0909 | Miért fontos a bőr rugalmasságának tesztelése? | Gyakorlati, minőségellenőrzési. OK. |
| explanation_0918 | Miért nehéz egyetlen objektív mércét találni a bőr minőségének megítélésére? | Elvontabb, semleges fogalom. OK. |
| explanation_0919 | Hogyan hat a bőr felhasználásának etikai kérdése az iparra? | Semleges, mindkét oldalt bemutató. OK. |
| explanation_0923 | Miért különböznek a drágakövek keménysége? | Pontos ásványtani magyarázat. OK. |
| explanation_0933 | Miért nehéz megkülönböztetni a szintetikus és természetes drágaköveket? | Elvontabb, tudományos fogalom. OK. |
| explanation_0937 | Miért fontos a drágakövek eredetének nyomon követhetősége? | Semleges, etikai kérdést kiegyensúlyozottan tárgyal. OK. |
| explanation_0944 | Miért nevezik a szappankészítést elszappanosításnak? | Pontos kémiai folyamat, receptek nélkül. OK. |
| explanation_0952 | Miért fontos a védőfelszerelés használata lúgkezelésnél? | Kifejezetten biztonság-pozitív figyelmeztető tartalom. OK. |
| explanation_0954 | Miért fontos a tisztítószerek biológiai lebonthatósága? | Semleges, környezeti. OK. |
| explanation_0960 | Miért fontos a tisztítószerek megfelelő tárolása? | Kifejezetten biztonság-pozitív, vegyszerkeveredés elleni figyelmeztetés. OK. |
| explanation_0964 | Miért nehéz megjósolni egy hegedű hangzását? | Elvontabb, tudományos fogalom. OK. |
| explanation_0972 | Miért fontos a hangszerkészítők tapasztalati tudása? | Elvontabb, semleges. OK. |
| explanation_0979 | Hogyan alakult ki a Stradivari hegedűk hírneve? | Tudományosan óvatos, nem túlzó. OK. |
| explanation_0984 | Miért voltak a fűszerek értékesek a történelemben? | Semleges, gazdaságtörténeti. OK. |
| explanation_0990 | Miért fontos a fűszerkereskedelmi monopóliumok megértése? | Semleges, nem egyoldalú történelmi elemzés. OK. |
| explanation_0998 | Miért fontos a fűszerek hamisítás elleni védelme? | Semleges, szabályozási. OK. |
| explanation_1000 | Miért fontos a fenntartható fűszertermesztés kérdése? | Semleges, mindkét szempontot bemutató. OK. |
| explanation_1002 | Miért fontos a fűszerek megfelelő adagolása? | Konyhai kontextus, veszélytelen. OK. |
| explanation_1003 | Hogyan foglalja össze a fűszerek története a ritkaság-érték elvét? | Elvontabb, összefoglaló gazdasági fogalom. OK. |

**Eredmény: 20/20 sor megfelelt.**

## 4. Fájlok

- Raw: `data/raw/claude_explanation_0901_1003_raw.jsonl` (103 sor)
- Clean: `data/clean/claude_explanation_0901_1003_clean.jsonl` (103 sor)
- Rejected: `data/rejected/claude_explanation_0901_1003_rejected.jsonl` (0 sor)

## 5. Regressziós teszt
`tests/test_v1_7_4_dataset_foundation.py` - **minden teszt sikeres, STÁTUSZ:
STABIL**.

## 6. Amit ez a kör NEM tett

- **Nem indított tanítást.**
- **Nem módosított webapp/backend kódot.**
- **Nem nyúlt a régi clean fájlokhoz.**

---

## Végső összegzés

- Raw sorok száma: **103**
- Clean sorok száma: **103**
- Rejected sorok száma: **0**
- Kereszt-batch duplikátumok száma: **0** (mind az öt jelzés a korábbi
  simple_qa hamis pozitívok megismétlődése)
- Átlag quality_score: **100.0**
- Topic report: 5 vadonatúj témakör (bőrfeldolgozás, ékszerészet,
  szappan/vegyipar, hangszerkészítés, fűszerkereskedelem), nincs
  túlreprezentált tag a teljes 2000 soros korpuszon.
- 20 soros manuális mintavétel eredménye: **20/20 megfelelt**.
- **Egyedi clean explanation sorok jelenleg összesen: 1000 / 1000. A 2.
  CSOMAG KÉSZ.**

**STÁTUSZ: STABIL.** Ez a batch zárja le a 2. csomagot. Részletes
lezáró audit: `data/reports/explanation_1000_completion_audit.md`.
