# Ötödik FELÜGYELT Claude-generált "magyarázós példa" batch - explanation 0401-0500

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
| Kereszt-batch **jelzett** (0.9 fölötti) egyezés (teljes 1500 soros korpuszon) | 5 |
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
üvegházhatás, bocsánat, ajándék) **0 találat**.

AI-tagelt sor: **0/100**. `technika`-tagelt sor: **0/100**.

### 2.3 Teljes korpuszos cross-dedupe (a TELJES 1400 soros meglévő korpusz +
    ez a 100 sor, 0.9 küszöb, összesen 1500 sor)

A dedupe **5 db 0.9 fölötti instruction-hasonlósági egyezést** jelzett,
`id_duplicates`: 0, `output_duplicates`: 0. Mind az öt jelzés a **korábban
már dokumentált, megtartott simple_qa hamis pozitívok pontos
megismétlődése** - egyik sem érinti ezt vagy bármelyik korábbi
explanation batch-et:

| kept | duplicate | similarity | Megjegyzés |
|---|---|---|---|
| simple_qa_0851 | simple_qa_0857 | 0.904 | Korábbról ismert hamis pozitív. |
| simple_qa_0851 | simple_qa_0859 | 0.919 | Korábbról ismert hamis pozitív. |
| simple_qa_0671 | simple_qa_0914 | 0.919 | Korábbról ismert hamis pozitív. |
| simple_qa_0734 | simple_qa_1081 | 0.918 | Korábbról ismert hamis pozitív (kémiai fogalompár). |
| simple_qa_0915 | simple_qa_0489 | 0.921 | Korábbról ismert hamis pozitív. |

**Az ÚJ explanation_0401-0500 batch egyik sora sem szerepel egyik
jelzésben sem.**

### 2.4 `tools/dataset_topic_report.py`

**A teljes, egyesített korpuszon** (1000 simple_qa + 500 explanation =
1500 sor):

| Tag | 1400 sornál (előző kör) | **1500 sornál (most)** |
|---|---|---|
| technika | 6.5% (91) | **6.1% (91)** - tovább csökken |
| iskola | 5.1% (71) | **4.7% (71)** - tovább csökken |
| biológia | 4.2% (59) | **3.9% (59)** - tovább csökken (0 új sor) |
| sport (ÚJ) | - | 3.4% (51) |
| nyelv (ÚJ) | - | 3.3% (50) |
| zene (bővült) | - | 3.2% (48) |
| pszichológia (bővült) | 3.0% (42) | 3.1% (47) |
| építészet (ÚJ) | - | ~1.3% (kb. 21) |
| közlekedés (ÚJ) | - | ~1.5% (kb. 22) |

**Túlreprezentált tagek: NINCS** (legmagasabb: technika 6.1%, jóval a
8%-os küszöb alatt).

Ez a batch 5 teljesen új témablokkot vezetett be (nyelvészet,
közlekedés/infrastruktúra mechanizmusok, sporttudomány/mozgásélettan,
zeneelmélet/hangtan, építészet/mérnöki alapelvek) - tudatosan elkerülve
a `technika`, `iskola` és `biológia` tageket, amik a legmagasabb arányú
tagok voltak az előző kör után.

### 2.5 `dataset_score.py`
Mind a 100 sor **100/100** pontot kapott, flag nélkül.

### 2.6 Safety/firewall ellenőrzés
- **`src/guard.py` `looks_like_identity_bleed()`**: **0 találat**.
- **Kiegészítő kulcsszó-szűrés**: **3 nyers találat**, mindhárom
  manuálisan ellenőrizve és **hamis pozitívnak** bizonyult:
  - "kezelés" (`explanation_0425`: "Hogyan működik a vasúti sínek
    hőtágulásának **kezelése**?" - mérnöki/műszaki kezelés, nem orvosi).
  - "kezelés" (`explanation_0460`: "...nem helyettesíti a súlyosabb
    hangulati nehézségek szakszerű **kezelését**" - felelős, negált
    disclaimer, nem orvosi tanács).
  - "garantál" (`explanation_0478`: "...ez a fajta átvitel **nem**
    automatikus vagy **garantált**" - negált, óvatosságra intő
    megfogalmazás).
- **Fogyasztói/sport/egészség-közeli sorok külön is átnézve** (449, 457,
  460): mindegyik általános, nem-klinikai, felelősen megfogalmazott
  gyakorlati tanács vagy mechanizmus-magyarázat, egyik sem ad orvosi
  diagnózist vagy kezelési utasítást.

## 3. Manuális mintavételes tartalmi átnézés (20 sor, minden témablokkból 4)

| id | Instruction | Értékelés |
|---|---|---|
| explanation_0402 | Hogyan tanulja meg egy kisgyerek az anyanyelvét ilyen gyorsan? | Pontos nyelvelsajátítási magyarázat. OK. |
| explanation_0407 | Miért nehéz szó szerint lefordítani egy nyelvi kifejezést egy másik nyelvre? | Semleges, pontos fordítástudományi fogalom. OK. |
| explanation_0412 | Hogyan hat a nyelv a gondolkodásunkra (a nyelvi relativitás elve)? | Tudományosan óvatos, vitatott elméletet jelzi. OK. |
| explanation_0417 | Miért van annyi kölcsönszó a legtöbb nyelvben? | Pontos nyelvtörténeti magyarázat. OK. |
| explanation_0423 | Hogyan tartja fenn egy repülőgép a magasságát repülés közben? | Pontos fizikai magyarázat. OK. |
| explanation_0426 | Miért van szükség féktávolságra, és miért nő ez a sebesség növekedésével nem egyenes arányban? | Pontos, gyakorlati fizikai összefüggés. OK. |
| explanation_0431 | Hogyan segítenek a ABS fékrendszerek a járművek irányíthatóságának megőrzésében? | Pontos műszaki magyarázat. OK. |
| explanation_0438 | Miért fontos a légellenállás csökkentése egy jármű tervezésénél? | Pontos aerodinamikai magyarázat. OK. |
| explanation_0442 | Hogyan javul az állóképesség rendszeres edzés hatására? | Pontos élettani magyarázat, nem orvosi tanács. OK. |
| explanation_0446 | Hogyan hat az alvás a sportteljesítményre és a regenerálódásra? | Kiegyensúlyozott, általános élettani magyarázat. OK. |
| explanation_0448 | Hogyan hat a magas légköri nyomású (magashegyi) környezet a sportteljesítményre? | Pontos élettani magyarázat. OK. |
| explanation_0456 | Hogyan hat a stressz-hormonok szintje a sportteljesítményre? | Kiegyensúlyozott, nem klinikai magyarázat. OK. |
| explanation_0462 | Hogyan hoz létre egy hangszer eltérő hangszínt (timbre) ugyanazon a hangmagasságon? | Pontos akusztikai magyarázat. OK. |
| explanation_0466 | Hogyan alakult ki a nyugati zenében használt hangolási rendszer (pl. a 12 hangú skála)? | Pontos, összetettebb zeneelméleti fogalom. OK. |
| explanation_0471 | Miért hat ránk érzelmileg ennyire erősen a zene, annak ellenére, hogy "csak" hangokból áll? | Tudományosan megalapozott, nem túlzó. OK. |
| explanation_0478 | Hogyan hat a zenei képzés a gyermekek egyéb kognitív képességeire? | Óvatos, nem túlígérő megfogalmazás. OK. |
| explanation_0483 | Miért fontos az alapozás egy épület tervezésénél? | Pontos mérnöki magyarázat. OK. |
| explanation_0485 | Miért fontos a földrengésbiztos tervezés bizonyos földrajzi területeken? | Pontos, összetettebb mérnöki fogalom. OK. |
| explanation_0492 | Hogyan működik egy modern felhőkarcoló belső vázszerkezete? | Pontos szerkezettani magyarázat. OK. |
| explanation_0497 | Miért fontos a rezgéscsillapítás egy híd tervezésénél? | Pontos, összetettebb fizikai/mérnöki fogalom. OK. |

**Eredmény: 20/20 sor megfelelt.**

## 4. Fájlok

- Raw: `data/raw/claude_explanation_0401_0500_raw.jsonl` (100 sor)
- Clean: `data/clean/claude_explanation_0401_0500_clean.jsonl` (100 sor)
- Rejected: `data/rejected/claude_explanation_0401_0500_rejected.jsonl` (0 sor)

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
  fókuszált (nyelvészet, közlekedés/infrastruktúra mechanizmusok,
  sporttudomány/mozgásélettan, zeneelmélet/hangtan, építészet/mérnöki
  alapelvek) - tudatosan elkerülve a `technika`, `iskola` és `biológia`
  tageket; a teljes 1500 soros korpuszon **nincs túlreprezentált tag**
  (legmagasabb: technika 6.1%, tovább csökkenő trend).
- 20 soros manuális mintavétel eredménye: **20/20 megfelelt**.
- **Egyedi clean explanation sorok jelenleg összesen: 500 / 1000.**
- **Hiányzik még a 2. csomag céljához: 500 sor.**

**STÁTUSZ: STABIL.**
