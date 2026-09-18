# Nyolcadik FELÜGYELT Claude-generált "magyarázós példa" batch - explanation 0701-0800

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
| Kereszt-batch **jelzett** (0.9 fölötti) egyezés (teljes 1797 soros korpuszon) | 5 |
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
`matematika`-tagelt sor: **0/100** (tudatosan elkerülve az előző batch
két duplikátumának tanulsága alapján).

### 2.3 Teljes korpuszos cross-dedupe (a TELJES 1697 soros meglévő korpusz +
    ez a 100 sor, 0.9 küszöb, összesen 1797 sor)

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
| simple_qa_0734 | simple_qa_1081 | 0.918 | Korábbról ismert hamis pozitív. |
| simple_qa_0915 | simple_qa_0489 | 0.921 | Korábbról ismert hamis pozitív. |

**Az ÚJ explanation_0701-0800 batch egyik sora sem szerepel egyik
jelzésben sem** - a `matematika` tag tudatos elkerülése (az előző
batch tanulsága nyomán) ezúttal sikeresen elkerülte az ismételt
témaütközést.

### 2.4 `tools/dataset_topic_report.py`

**A teljes, egyesített korpuszon** (1000 simple_qa + 797 explanation =
1797 sor):

| Tag | 1697 sornál (előző kör) | **1797 sornál (most)** |
|---|---|---|
| fizika (bővült) | 4.8% (82) | 5.3% (96) |
| technika | 5.4% (91) | **5.1% (91)** - tovább csökken |
| történelem (bővült) | 4.2% (53) | 4.2% (76) - számban nőtt, aránya stabil maradt |
| iskola | 4.2% (71) | **4.0% (71)** - tovább csökken |
| gazdaság | 3.8% (64) | 3.7% (66) |
| matematika | 3.7% (63) | 3.4% (61 - arányosan csökken, 0 új sor) |
| biológia | 3.5% (59) | **3.3% (60)** - tovább csökken arányosan |
| óceánográfia (ÚJ) | - | ~1.1% (kb. 20) |
| térképészet (ÚJ) | - | ~1.1% (kb. 20) |
| nyomdászat (ÚJ) | - | ~1.1% (kb. 20) |
| textilipar (ÚJ) | - | ~1.1% (kb. 20) |
| fémmegmunkálás (ÚJ) | - | ~1.1% (kb. 20) |

**Túlreprezentált tagek: NINCS** (legmagasabb: fizika 5.3%, jóval a
8%-os küszöb alatt).

Ez a batch 5 teljesen új témablokkot vezetett be (óceánográfia,
térképészet/kartográfia, nyomdászat/könyvtörténet, textilipar/szövés,
fémmegmunkálás/kovácsolás) - tudatosan elkerülve a `technika`, `iskola`,
`biológia` és (az előző kör tanulsága nyomán) a `matematika` tageket is.

### 2.5 `dataset_score.py`
Mind a 100 sor **100/100** pontot kapott, flag nélkül.

### 2.6 Safety/firewall ellenőrzés
- **`src/guard.py` `looks_like_identity_bleed()`**: **0 találat**.
- **Kiegészítő kulcsszó-szűrés**: **3 nyers találat**, mindhárom
  "kezelés" kulcsszóra, manuálisan ellenőrizve és **hamis pozitívnak**
  bizonyult:
  - `explanation_0756`: "...egy praktikus, gazdaságos mozgatható
    betűkészlet létrehozása és **kezelése**" - nyomdai betűkészlet
    kezelése, nem orvosi.
  - `explanation_0765`: "...gyűrődhetnek vagy zsugorodhatnak bizonyos
    **kezelések** hatására" - textilipari kezelés (vegyi/mechanikai
    feldolgozás), nem orvosi.
  - `explanation_0768`: "Miért fontos a textíliák elő**kezelése** (mint
    a fehérítés) a festés előtt?" - textilipari előkezelés, nem orvosi.
- **Nyomdászat blokk (751-754) külön is átnézve** (cenzúra és szerzői
  jog témák miatt): minden sor semleges, történelmi ismeretterjesztés,
  egyik sem foglal állást vitatott politikai kérdésben.
- **Térképészet blokk (732, 740) külön is átnézve** (országhatárok és
  térképtájolás politikai vonatkozásai miatt): mindkét sor semleges,
  tényszerű, nem foglal állást konkrét, aktuális határvitákban.

## 3. Manuális mintavételes tartalmi átnézés (20 sor, minden témablokkból 4)

| id | Instruction | Értékelés |
|---|---|---|
| explanation_0702 | Miért van árapály (dagály és apály)? | Pontos csillagászati/óceanográfiai magyarázat. OK. |
| explanation_0708 | Hogyan hat a globális óceáni keringési rendszer a Föld éghajlata szempontjából? | Elvontabb, tudományos fogalom. OK. |
| explanation_0712 | Miért nehéz pontosan feltérképezni a mélytengeri óceánfeneket? | Elvontabb, tudományosan pontos. OK. |
| explanation_0718 | Miért nehéz pontosan előre jelezni egy hurrikán útvonalát? | Tudományosan óvatos, pontos. OK. |
| explanation_0722 | Hogyan működik a Mercator-vetület? | Pontos térképészeti magyarázat. OK. |
| explanation_0727 | Miért különböznek a politikai és a domborzati térképek? | Semleges, ismeretterjesztő. OK. |
| explanation_0732 | Hogyan alakult ki a modern országhatárok ábrázolása? | Semleges, nem politizáló megfogalmazás. OK. |
| explanation_0733 | Miért nehéz egyetlen térképi vetülettel mindent megőrizni? | Elvontabb, matematikailag pontos. OK. |
| explanation_0741 | Hogyan forradalmasította a mozgatható betűs nyomtatás a tudás terjedését? | Pontos, semleges történelmi magyarázat. OK. |
| explanation_0748 | Miért nehéz pontosan rekonstruálni egyes ősi szövegek eredeti tartalmát? | Elvontabb, szövegkritikai fogalom. OK. |
| explanation_0751 | Hogyan hatott a cenzúra a nyomtatott könyvek terjesztésére? | Semleges, történelmi, nem egyoldalú. OK. |
| explanation_0754 | Miért fontos a szerzői jog fogalmának kialakulása? | Semleges jogtörténeti magyarázat. OK. |
| explanation_0763 | Hogyan különbözik a szövés a kötéstől szerkezetileg? | Pontos textilipari magyarázat. OK. |
| explanation_0771 | Hogyan alakult ki a mintás szövés technikája? | Elvontabb, technikatörténeti fogalom. OK. |
| explanation_0775 | Hogyan alakult ki a pamut szerepe a globális textilkereskedelemben? | Semleges, gazdaságtörténeti. OK. |
| explanation_0779 | Hogyan alakult ki a modern gyorsdivat modellje? | Semleges, mindkét oldalt érintő. OK. |
| explanation_0783 | Hogyan keletkezik a bronz ötvözet? | Pontos fémmegmunkálási magyarázat. OK. |
| explanation_0789 | Hogyan hatott a vaskohászat fejlődése a történelmi eszközök minőségére? | Semleges, történelmi. OK. |
| explanation_0797 | Hogyan hat a fémek kristályszerkezete a mechanikai tulajdonságaikra? | Elvontabb, tudományosan pontos. OK. |
| explanation_0798 | Miért fontos a védőfelszerelés használata kovácsműhelyben? | Gyakorlati, biztonsági, veszélytelen. OK. |

**Eredmény: 20/20 sor megfelelt.**

## 4. Fájlok

- Raw: `data/raw/claude_explanation_0701_0800_raw.jsonl` (100 sor)
- Clean: `data/clean/claude_explanation_0701_0800_clean.jsonl` (100 sor)
- Rejected: `data/rejected/claude_explanation_0701_0800_rejected.jsonl` (0 sor)

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
  simple_qa hamis pozitívok megismétlődése; a `matematika` tag tudatos
  elkerülése ezúttal megelőzte az előző körben tapasztalt
  témaismétlődést)
- Átlag quality_score: **100.0**
- Topic report (röviden): batch önmagában 5 vadonatúj témakörre
  fókuszált (óceánográfia, térképészet/kartográfia,
  nyomdászat/könyvtörténet, textilipar/szövés, fémmegmunkálás/
  kovácsolás) - tudatosan elkerülve a `technika`, `iskola`, `biológia`
  és `matematika` tageket; a teljes 1797 soros korpuszon **nincs
  túlreprezentált tag** (legmagasabb: fizika 5.3%, technika tovább
  csökkenő trend 5.1%).
- 20 soros manuális mintavétel eredménye: **20/20 megfelelt**.
- **Egyedi clean explanation sorok jelenleg összesen: 797 / 1000.**
- **Hiányzik még a 2. csomag céljához: 203 sor.**

**STÁTUSZ: STABIL.** A `matematika` tag tudatos kihagyása ebben a
körben sikeresen megelőzte az előző batch-ben tapasztalt véletlen
témaismétlődést - ez megerősíti az előző kör tanulságát: szűkebb,
jól definiált fogalmi tereknél érdemes egy-két kört kihagyni a
témaismétlődés kockázatának csökkentésére.
