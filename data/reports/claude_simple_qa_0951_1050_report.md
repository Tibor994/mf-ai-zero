# Hetedik FELÜGYELT Claude-generált próba batch - simple_qa 0951-1050

- Forrás: **Claude-generált**, 100 db, kézzel megírt, majd a teljes meglévő
  pipeline-nal ellenőrzött sor. Az **1000 db egyszerű magyar kérdés-válasz
  célcsomag** folytatása - az AUTOPILOT v2 folyamat negyedik batch-e.
  Ezzel a batch-csel a csomag 891/1000-nél áll - a záráshoz még egy 109
  soros batch szükséges (lásd 7. pont).
- `source` mező: `synthetic_claude`.
- **Ez továbbra is TESZT kör** - a modellt NEM tanítottuk erre az adatra,
  webapp/backend kód nem változott.

## 1. Számok

| Mérőszám | Érték |
|---|---|
| Raw sorok | 100 |
| Validáláson elfogadva | 100 |
| Validáláson elutasítva | 0 |
| Kereszt-batch **jelzett** (0.9 fölötti) egyezés | 4 (mind a MEGLÉVŐ, korábbi batch-nél már ellenőrzött és megtartott 4 hamis pozitív - lásd 2.3) |
| Ebből az ÚJ 0951-1050 batch-et érintő | **0** |
| **Végleges clean sorok** | **100** |
| **Rejected sorok** | **0** |
| Átlag quality_score | **100.0** |
| Flag-et kapott sor | 0 |

## 2. Ellenőrzési lépések (teljes pipeline)

### 2.1 Schema validate
Mind a 100 sor strukturálisan érvényes.

### 2.2 Kizárt témák explicit ellenőrzése
A kizárt kifejezések egyikére sem volt találat. AI-tagelt sor: **0/100**.

### 2.3 Teljes korpuszos cross-dedupe (a TELJES 791 soros meglévő korpusz +
    ez a 100 sor, 0.9 küszöb, összesen 891 sor)

A dedupe 4 db 0.9 fölötti egyezést jelzett - de mind a négy **PONTOSAN
UGYANAZ a négy pár**, amit a `claude_simple_qa_0851_0950_report.md` már
részletesen dokumentált és manuálisan hamis pozitívnak minősített
(`simple_qa_0851`/`0857`, `simple_qa_0851`/`0859`, `simple_qa_0671`/
`0914`, `simple_qa_0489`/`0915`). Ez várható volt: mivel ezeket a sorokat
szándékosan NEM távolítottuk el (mert a tartalmuk valóban különböző),
minden jövőbeli teljes-korpuszos dedupe-futás újra jelezni fogja őket -
ez NEM új probléma, hanem a korábbi, dokumentált döntés következetes
megismétlődése.

**A most hozzáadott 100 sor (0951-1050) egyikét sem érintette egyetlen
jelzés sem** - explicit ellenőrizve, hogy egyik jelzett párban sincs
`claude_simple_qa_0951_1050_clean.jsonl` forrású sor.

### 2.4 `tools/dataset_topic_report.py`

**A teljes, egyesített korpuszon** (791 régi + 100 új = 891 sor) - **ELSŐ
ALKALOMMAL EGYETLEN TAG SINCS a 8%-os küszöb fölött**:

| Tag | 791 sornál (előző kör) | **891 sornál (most)** |
|---|---|---|
| iskola | 9.0% (71) | **8.0% (71)** - pontosan a küszöbön, nem fölötte |
| technika | 9.0% (71) | **8.0% (71)** - pontosan a küszöbön, nem fölötte |
| AI | 5.6% (44) | **4.9% (44)** - tovább csökkent |
| történelem (ÚJ, bővült) | 1.0% (9) | 3.4% (30) |
| csillagászat (bővült) | 0.8% (7) | 3.0% (27) |

**Túlreprezentált tagek: NINCS.** Ez az AUTOPILOT v2 folyamat eddigi
legjobb eredménye - a hét egymást követő, tudatosan diverzifikált
Claude-batch (AI/Nexora nélkül, folyamatosan új témákra fókuszálva)
teljesen orvosolta az eredeti audit által feltárt témakör-koncentrációs
problémát (lásd `dataset_audit_0151_0500.md` 2.3 pont, ahol az AI tag
12.8%-on állt).

### 2.5 `dataset_score.py`
Mind a 100 sor **100/100** pontot kapott, flag nélkül.

### 2.6 Safety/firewall ellenőrzés
- **`src/guard.py` `looks_like_identity_bleed()`**: **0 találat**.
- **Kiegészítő kulcsszó-szűrés** (a táplálkozástudományi blokk miatt az
  orvosi lista `kezelés` szóval kiegészítve): **0 találat mindenhol**.
- **Táplálkozástudományi blokk (0971-0990) külön is átnézve**: mind
  SEMLEGES, tankönyvi jellegű definíció (mi a fehérje, mi a vitamin, mi a
  kalória, stb.), egyik sem ad diétás tanácsot, fogyókúrás ígéretet vagy
  orvosi javaslatot.

## 3. Manuális mintavételes tartalmi átnézés (20 sor, minden témablokkból 4)

| id | Instruction | Értékelés |
|---|---|---|
| simple_qa_0953 | Mi az a fekete lyuk? | Pontos csillagászati definíció. OK. |
| simple_qa_0960 | Mi az a Naprendszer? | Pontos alapfogalom. OK. |
| simple_qa_0966 | Mi az a fényév? | Pontos mértékegység-definíció. OK. |
| simple_qa_0970 | Mi a különbség a meteor és a meteorit között? | Pontos, tudományosan helyes. OK. |
| simple_qa_0973 | Mi az a vitamin? | Semleges tápanyag-definíció, nincs diétás ígéret. OK. |
| simple_qa_0977 | Mi az a kalória? | Semleges energiamérték-definíció. OK. |
| simple_qa_0985 | Mi az a probiotikum, egyszerűen megfogalmazva? | Óvatos megfogalmazás ("azt feltételezik"), nem túlígérő. OK. |
| simple_qa_0989 | Mi az anyagcsere, egyszerűen megfogalmazva? | Semleges élettani fogalom. OK. |
| simple_qa_0994 | Ki volt Gutenberg, és miért fontos? | Pontos, semleges történelmi tény. OK. |
| simple_qa_0998 | Mi volt a hidegháború? | Semleges, nem elfogult politikai magyarázat. OK. |
| simple_qa_1003 | Mi volt az írás feltalálásának jelentősége? | Pontos történelmi jelentőség. OK. |
| simple_qa_1009 | Mi volt a hieroglifa? | Pontos, tényszerű. OK. |
| simple_qa_1013 | Mi a különbség a fekete-fehér és a színes fotózás hatása között? | Semleges, esztétikai magyarázat. OK. |
| simple_qa_1020 | Mi a fényképezőgép rekesznyílása? | Pontos fotós alapfogalom. OK. |
| simple_qa_1024 | Mi a filmzene szerepe egy filmben? | Pontos, semleges magyarázat. OK. |
| simple_qa_1029 | Mi a különbség a stílus és a műfaj egy filmben? | Pontos filmes fogalom. OK. |
| simple_qa_1033 | Mi a különbség a klasszikus és a modern építészeti stílus között? | Semleges, nem értékítéletes. OK. |
| simple_qa_1038 | Mi a fenntartható építészet elve? | Semleges fogalommagyarázat. OK. |
| simple_qa_1042 | Mi a hagyományos teaszertartás Japánban? | Tisztelettudó, tényszerű kulturális leírás. OK. |
| simple_qa_1049 | Miért érdemes tisztelettel közeledni más kultúrák szokásaihoz? | Pozitív, nyitottságra ösztönző, nem sztereotipizáló. OK. |

**Eredmény: 20/20 sor megfelelt.**

## 4. Fájlok

- Raw: `data/raw/claude_simple_qa_0951_1050_raw.jsonl` (100 sor)
- Clean: `data/clean/claude_simple_qa_0951_1050_clean.jsonl` (100 sor)
- Rejected: `data/rejected/claude_simple_qa_0951_1050_rejected.jsonl` (0 sor)

## 5. Regressziós teszt
`tests/test_v1_7_4_dataset_foundation.py` - **minden teszt sikeres, STÁTUSZ:
STABIL**.

## 6. Amit ez a kör NEM tett

- **Nem indított tanítást.**
- **Nem módosított webapp/backend kódot.**
- **Nem nyúlt a régi (0151-0950) clean fájlokhoz.**

## 7. Következő lépés az 1. csomag lezárásához

A csomag jelenlegi állása: **891/1000**. A pontos 1000-es cél eléréséhez
egy **109 soros záró batch** szükséges: `simple_qa_1051_1159`. Ez a batch
zárná le az 1. csomagot, ami után a `data/reports/
simple_qa_1000_completion_audit.md` rész-audit elkészítése következik az
AUTOPILOT utasítás szerint.

---

## Végső összegzés

- Raw sorok száma: **100**
- Clean sorok száma: **100**
- Rejected sorok száma: **0**
- Kereszt-batch duplikátumok száma: **0 új** (a 4 korábban jelzett, hamis
  pozitívnak minősített pár változatlanul, megőrizve maradt, ez a batch
  egyiket sem érintette)
- Átlag quality_score: **100.0**
- Topic report (röviden): batch önmagában 5 vadonatúj/bővített témakörre
  fókuszált (csillagászat, táplálkozástudomány, történelem, fotózás/film,
  építészet+néprajz); a teljes korpuszra vetítve **ELSŐ ALKALOMMAL egyetlen
  tag sincs a 8%-os riasztási küszöb fölött** - az AI/Nexora arány 4.9%-ra
  csökkent, iskola/technika pontosan 8.0%-on áll.
- 20 soros manuális mintavétel eredménye: **20/20 megfelelt**.
- **Egyedi clean simple_qa sorok jelenleg összesen: 891**
  (791 korábbi + 100 új ebből a batch-ből).
- **Hiányzik még az 1000 db simple_qa célhoz: 109 sor.**

**STÁTUSZ: STABIL.**
