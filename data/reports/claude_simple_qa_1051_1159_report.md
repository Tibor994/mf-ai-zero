# Nyolcadik, ZÁRÓ FELÜGYELT Claude-generált próba batch - simple_qa 1051-1159

- Forrás: **Claude-generált**, 109 db, kézzel megírt, majd a teljes meglévő
  pipeline-nal ellenőrzött sor. Ez a batch **PONTOSAN 1000-re zárja** az
  **1000 db egyszerű magyar kérdés-válasz célcsomagot** (roadmap 1.
  csomag) - az AUTOPILOT v2 folyamat ötödik és egyben záró batch-e ebben
  a csomagban.
- `source` mező: `synthetic_claude`.
- **Ez továbbra is TESZT kör** - a modellt NEM tanítottuk erre az adatra,
  webapp/backend kód nem változott.

## 1. Számok

| Mérőszám | Érték |
|---|---|
| Raw sorok | 109 |
| Validáláson elfogadva | 109 |
| Validáláson elutasítva | 0 |
| Kereszt-batch **jelzett** (0.9 fölötti) egyezés (összesen az 1000 soros korpuszon) | 5 |
| Ebből az ÚJ 1051-1159 batch-et érintő | **1** (manuálisan ellenőrizve: hamis pozitív) |
| Ebből a KORÁBBAN már ellenőrzött, megismétlődő | 4 |
| **Végleges clean sorok** | **109** |
| **Rejected sorok** | **0** |
| Átlag quality_score | **100.0** |
| Flag-et kapott sor | 0 |

## 2. Ellenőrzési lépések (teljes pipeline)

### 2.1 Schema validate
Mind a 109 sor strukturálisan érvényes.

### 2.2 Kizárt témák explicit ellenőrzése
A kizárt kifejezések egyikére sem volt találat. AI-tagelt sor: **0/109**.

### 2.3 Teljes korpuszos cross-dedupe (a TELJES 891 soros meglévő korpusz +
    ez a 109 sor, 0.9 küszöb, összesen PONTOSAN 1000 sor)

A dedupe 5 db 0.9 fölötti egyezést jelzett:
- **4 db a korábban már dokumentált, megtartott hamis pozitív** (lásd
  `claude_simple_qa_0851_0950_report.md`), amik minden jövőbeli
  teljes-korpuszos futtatásnál újra jelentkeznek, mert szándékosan nem
  lettek eltávolítva - ez várt, nem új probléma.
- **1 ÚJ, ezt a batch-et érintő jelzés**:
  `simple_qa_0734` ("Mi a különbség a keverék és a vegyület között?",
  korábbi batch) vs `simple_qa_1081` ("Mi a különbség az elem és a
  vegyület között?", ez a batch) - hasonlóság: 0.918.

  **Manuális ellenőrzés**: mindkét sor a "Mi a különbség a ___ és a
  vegyület között?" sablont használja, DE a tartalom egyértelműen
  különböző - az egyik a KEVERÉK/VEGYÜLET (fizikai szétválaszthatóság
  kontra kémiai kötés) fogalompárt magyarázza, a másik az ELEM/VEGYÜLET
  (egyfajta atom kontra többféle atom kémiai kötése) fogalompárt. Ez
  **ugyanaz a jelenség**, amit a 0851-0950 batch reportja már
  dokumentált: rövid, egy szót variáló sablonoknál a 0.9-es küszöb
  fölött is előfordulhat hamis pozitív. **Nem távolítottam el egyik sort
  sem** - mindkettő valódi, önálló kémiai fogalompár-magyarázat.

**Összesen tehát: 0 valódi (tartalmilag átfedő) duplikátum ebben a
batch-ben is.**

### 2.4 `tools/dataset_topic_report.py`

**A teljes, egyesített korpuszon, PONTOSAN 1000 sornál**:

| Tag | 891 sornál (előző kör) | **1000 sornál (most, ZÁRÓ állapot)** |
|---|---|---|
| iskola | 8.0% (71) | **7.1% (71)** |
| technika | 8.0% (71) | **7.1% (71)** |
| AI | 4.9% (44) | **4.4% (44)** |
| sportszabályok (bővült) | 2.2% (20) | 4.2% (42) |
| biológia (bővült) | 2.0% (17) | 3.3% (33) |
| matematika (ÚJ) | - | 2.2% (22) |
| kémia (bővült) | - | 2.5% (25) |
| nyelv (bővült) | 0.3% (3) | 2.6% (26) |

**Túlreprezentált tagek: NINCS** (ez már a harmadik egymást követő
batch-nél is így van, lásd 0951-1050 report). A **legmagasabb** tag-arány
a végleges, 1000 soros korpuszban is csak **7.1%** (iskola és technika) -
messze a 8%-os riasztási küszöb alatt. Az AI/Nexora arány a kiindulási
12.8%-ról (audit) **4.4%-ra** csökkent.

### 2.5 `dataset_score.py`
Mind a 109 sor **100/100** pontot kapott, flag nélkül.

### 2.6 Safety/firewall ellenőrzés
- **`src/guard.py` `looks_like_identity_bleed()`**: **0 találat**.
- **Kiegészítő kulcsszó-szűrés**: **1 nyers találat** ("lúg" -
  `simple_qa_1086`, "Mi az a pH-semleges anyag?") - manuálisan
  ellenőrizve: **hamis pozitív**, tiszta kémiai (pH-semlegesség)
  definíció, ugyanaz a minta, mint a korábbi "savasság (pH)" sornál.
- **Kémia blokk (1073-1094) külön is átnézve**: mind tankönyvi jellegű,
  veszélytelen definíció (elem, reakció, oldat, katalizátor, korrózió,
  égés), egyik sem ad utasítást veszélyes kémiai kísérlet elvégzésére.

## 3. Manuális mintavételes tartalmi átnézés (20 sor, minden témablokkból 4)

| id | Instruction | Értékelés |
|---|---|---|
| simple_qa_1058 | Mi a Pitagorasz-tétel lényege? | Pontos matematikai tétel. OK. |
| simple_qa_1063 | Mi a különbség a racionális és az irracionális szám között? | Pontos matematikai fogalom. OK. |
| simple_qa_1072 | Miért hasznos a fejszámolás a mindennapokban? | Gyakorlati, semleges tanács. OK. |
| simple_qa_1075 | Mi a különbség a kémiai reakció és a fizikai változás között? | Pontos kémiai fogalom. OK. |
| simple_qa_1081 | Mi a különbség az elem és a vegyület között? | **Cross-dedupe jelezte 0734-gyel (0.918), manuálisan ellenőrizve: hamis pozitív.** OK. |
| simple_qa_1090 | Mi az égés kémiai szempontból? | Tankönyvi, veszélytelen kémiai leírás. OK. |
| simple_qa_1096 | Mi a jégkorong alapszabálya? | Pontos sportszabály. OK. |
| simple_qa_1105 | Mi a különbség a nyári és a téli olimpiai játékok sportágai között? | Semleges fogalom. OK. |
| simple_qa_1111 | Mi a cél a magasugrásban? | Pontos sportfogalom. OK. |
| simple_qa_1117 | Mi a különbség az anyanyelv és az idegen nyelv között? | Pontos nyelvészeti fogalom. OK. |
| simple_qa_1122 | Mi az a jelnyelv? | Tisztelettudó, pontos leírás. OK. |
| simple_qa_1126 | Miért nehezebb felnőttként új nyelvet tanulni, mint gyermekként? | Tudományosan megalapozott, nem túlzó állítás. OK. |
| simple_qa_1134 | Mi az az idiómakifejezés (szólás)? | Pontos nyelvészeti fogalom. OK. |
| simple_qa_1139 | Mi az az ökoszisztéma? | Pontos ökológiai fogalom. OK. |
| simple_qa_1143 | Miért fontos a biodiverzitás egy adott területen? | Pontos, semleges magyarázat. OK. |
| simple_qa_1147 | Mi a kölcsönösen előnyös szimbiózis egy gyakori példája? | Pontos biológiai fogalom. OK. |
| simple_qa_1151 | Mi okozhatja egy faj kihalásának veszélyét? | Tényszerű, nem ijesztgető. OK. |
| simple_qa_1154 | Mi a különbség a természetes szelekció és a mesterséges szelekció között? | Pontos biológiai fogalom. OK. |
| simple_qa_1157 | Mi a rovarok szerepe a beporzásban? | Pontos ökológiai szerep. OK. |
| simple_qa_1159 | Miért fontos a természetes élőhelyek megőrzése? | Semleges, nem elfogult környezeti érv. OK. |

**Eredmény: 20/20 sor megfelelt.**

## 4. Fájlok

- Raw: `data/raw/claude_simple_qa_1051_1159_raw.jsonl` (109 sor)
- Clean: `data/clean/claude_simple_qa_1051_1159_clean.jsonl` (109 sor)
- Rejected: `data/rejected/claude_simple_qa_1051_1159_rejected.jsonl` (0 sor)

## 5. Regressziós teszt
`tests/test_v1_7_4_dataset_foundation.py` - **minden teszt sikeres, STÁTUSZ:
STABIL**.

## 6. Amit ez a kör NEM tett

- **Nem indított tanítást.**
- **Nem módosított webapp/backend kódot.**
- **Nem nyúlt a régi (0151-0950) clean fájlokhoz.**

---

## Végső összegzés

- Raw sorok száma: **109**
- Clean sorok száma: **109**
- Rejected sorok száma: **0**
- Kereszt-batch duplikátumok száma: **0 valódi** (1 új jelzés, hamis
  pozitívnak bizonyult; 4 korábbi jelzés megismétlődött, változatlanul)
- Átlag quality_score: **100.0**
- Topic report (röviden): batch önmagában 5 témakörre fókuszált
  (matematika, kémia, sportszabályok bővítve, nyelvtudomány bővítve,
  biológia/ökológia bővítve); a teljes, PONTOSAN 1000 soros korpuszon
  **továbbra sincs túlreprezentált tag**, a legmagasabb (iskola/technika)
  is csak 7.1%.
- 20 soros manuális mintavétel eredménye: **20/20 megfelelt**.
- **Egyedi clean simple_qa sorok jelenleg összesen: 1000.**
- **Hiányzik még az 1000 db simple_qa célhoz: 0 - A CÉLKITŰZÉS TELJESÜLT.**

**STÁTUSZ: STABIL.**

**Az 1. csomag (1000 db egyszerű magyar kérdés-válasz) ezzel TELJES.**
A következő lépés az AUTOPILOT utasítás szerint a
`data/reports/simple_qa_1000_completion_audit.md` rész-audit elkészítése.
