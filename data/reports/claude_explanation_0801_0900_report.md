# Kilencedik FELÜGYELT Claude-generált "magyarázós példa" batch - explanation 0801-0900

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
| Kereszt-batch **jelzett** (0.9 fölötti) egyezés (teljes 1897 soros korpuszon) | 5 |
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
A kizárt kifejezések listáján **0 találat**. AI-tagelt sor: **0/100**.
`technika`-tagelt sor: **0/100**. `matematika`-tagelt sor: **0/100**
(tudatosan elkerülve, az előző kör tanulsága alapján).

### 2.3 Teljes korpuszos cross-dedupe (a TELJES 1797 soros meglévő korpusz +
    ez a 100 sor, 0.9 küszöb, összesen 1897 sor)

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

**Az ÚJ explanation_0801-0900 batch egyik sora sem szerepel egyik
jelzésben sem.**

### 2.4 `tools/dataset_topic_report.py`

**A teljes, egyesített korpuszon** (1000 simple_qa + 897 explanation =
1897 sor): legmagasabb tag: fizika 5.4%, technika 4.8% (tovább csökken),
iskola 3.7% (tovább csökken), biológia 3.2% (tovább csökken, csak 1 új
sor ebben a batch-ben, mellékesen az integrált növényvédelem/beporzók
témánál). **Túlreprezentált tagek: NINCS.**

Ez a batch 5 teljesen új témablokkot vezetett be (mezőgazdaság/
növénytermesztés, bányászat, kerámia/agyagművesség, üveggyártás/
üvegfúvás, illatszerek/parfümkészítés) - tudatosan elkerülve a
`technika`, `iskola`, `biológia` és `matematika` tageket.

### 2.5 `dataset_score.py`
Mind a 100 sor **100/100** pontot kapott, flag nélkül.

### 2.6 Safety/firewall ellenőrzés
- **`src/guard.py` `looks_like_identity_bleed()`**: **0 találat**.
- **Kiegészítő kulcsszó-szűrés**: **7 nyers találat**, mindegyik
  manuálisan ellenőrizve és **hamis pozitívnak** bizonyult:
  - "lúg" (`explanation_0806`: "talaj savasságának vagy
    **lúgosságának** mértéke" - talaj pH, nem veszélyes vegyszer).
  - "vegyszer" (`explanation_0807`: "...ahelyett hogy kizárólag
    **vegyszerekre** támaszkodnánk" / "minimalizálja a **vegyszeres
    kezelések** szükségességét" - integrált növényvédelem, ami
    kifejezetten a vegyszerfüggőség CSÖKKENTÉSÉRŐL szól, biztonság-
    pozitív tartalom).
  - "kezelés" (`explanation_0802, 0817, 0828, 0835`: rendre talaj-,
    betakarítás utáni, víz- és hulladékkezelés - mezőgazdasági/
    bányászati/környezeti kontextus, egyik sem orvosi).
- **Mezőgazdaság és bányászat blokkok külön is átnézve**: minden sor
  gyakorlati, veszélytelen ismeretterjesztés, egyik sem ad konkrét
  vegyszerhasználati vagy robbanóanyag-kezelési utasítást az olvasónak.

## 3. Manuális mintavételes tartalmi átnézés (20 sor, minden témablokkból 4)

| id | Instruction | Értékelés |
|---|---|---|
| explanation_0801 | Miért fontos a vetésforgó alkalmazása a mezőgazdaságban? | Pontos, veszélytelen agronómiai elv. OK. |
| explanation_0807 | Miért fontos az integrált védekezés elve? | Semleges, vegyszerhasználat-csökkentő szemlélet. OK. |
| explanation_0812 | Hogyan hat a talaj mikrobiális élete a növények egészségére? | Elvontabb, tudományos fogalom. OK. |
| explanation_0818 | Hogyan hat a monokultúrás termesztés hosszú távon? | Elvontabb, semleges környezeti fogalom. OK. |
| explanation_0822 | Hogyan biztosítják a bányászok a szellőztetést? | Pontos biztonságtechnikai magyarázat. OK. |
| explanation_0825 | Miért fontos a por elleni védekezés a bányászati munkahelyeken? | Biztonsági, munkavédelmi, veszélytelen. OK. |
| explanation_0833 | Miért nehéz pontosan megbecsülni egy lelőhely mennyiségét? | Elvontabb, tudományosan óvatos. OK. |
| explanation_0836 | Hogyan alakult ki a bányászati biztonsági előírások szerepe? | Semleges, történelmi. OK. |
| explanation_0841 | Hogyan alakítja át az égetés a nyers agyagot? | Pontos kémiai-fizikai magyarázat. OK. |
| explanation_0848 | Miért nehéz pontosan reprodukálni egy ősi kerámiatárgy mázát? | Elvontabb, tudományos fogalom. OK. |
| explanation_0856 | Miért nehéz pontosan előre jelezni, hogyan reagál egy adott máz? | Elvontabb, tapasztalati tudás fogalma. OK. |
| explanation_0860 | Miért fontos a modern ipari kerámiák szerepe? | Semleges, ismeretterjesztő. OK. |
| explanation_0861 | Hogyan alakul át a homok üveggé? | Pontos kémiai magyarázat. OK. |
| explanation_0864 | Miért nehéz pontosan megjósolni az olvadt üveg állagát? | Elvontabb, tapasztalati fogalom. OK. |
| explanation_0873 | Hogyan hat az üveg kémiai összetétele a hőállóságára? | Elvontabb, kémiailag pontos. OK. |
| explanation_0878 | Miért fontos az üveg újrahasznosításának kihívása? | Semleges, környezeti. OK. |
| explanation_0882 | Miért illékonyabbak egyes illatanyagok, mint mások? | Pontos kémiai magyarázat. OK. |
| explanation_0885 | Hogyan alakult ki a szintetikus illatanyagok szerepe? | Elvontabb, semleges. OK. |
| explanation_0889 | Hogyan befolyásolja az illatok érzékelése az emlékek felidézését? | Tudományosan megalapozott, nem túlzó. OK. |
| explanation_0897 | Hogyan hat a molekuláris szerkezet finom változása egy illatanyag jellegére? | Elvontabb, kémiailag pontos. OK. |

**Eredmény: 20/20 sor megfelelt.**

## 4. Fájlok

- Raw: `data/raw/claude_explanation_0801_0900_raw.jsonl` (100 sor)
- Clean: `data/clean/claude_explanation_0801_0900_clean.jsonl` (100 sor)
- Rejected: `data/rejected/claude_explanation_0801_0900_rejected.jsonl` (0 sor)

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
- Topic report: 5 vadonatúj témakör (mezőgazdaság, bányászat, kerámia,
  üveggyártás, illatszerek), nincs túlreprezentált tag a teljes 1897
  soros korpuszon (legmagasabb: fizika 5.4%).
- 20 soros manuális mintavétel eredménye: **20/20 megfelelt**.
- **Egyedi clean explanation sorok jelenleg összesen: 897 / 1000.**
- **Hiányzik még a 2. csomag céljához: 103 sor.**

**STÁTUSZ: STABIL.** A következő, záró batch (`explanation_0901_1003`,
103 sor) zárja le a 2. csomagot pontosan 1000/1000-en.
