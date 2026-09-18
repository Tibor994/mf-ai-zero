# Második FELÜGYELT Claude-generált "magyarázós példa" batch - explanation 0101-0200

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
| Kereszt-batch **jelzett** (0.9 fölötti) egyezés (teljes 1200 soros korpuszon) | 5 |
| Ebből az ÚJ explanation batch-et érintő | **0** |
| **Végleges clean sorok** | **100** |
| **Rejected sorok** | **0** |
| Átlag quality_score | **100.0** |
| Flag-et kapott sor | 0 |
| Difficulty eloszlás | medium: 90, hard: 10 |

## 2. Stratégiai megjegyzés: `technika` tag korrekció

Az előző batch (`explanation_0001_0100`) reportja jelezte, hogy a
`technika` tag 8.3%-ra túllépte a küszöböt. **Ez a batch tudatosan 0 db
`technika`-tagelt sort tartalmazott** - explicit ellenőrizve validáláskor.
Az eredmény: a `technika` arány a teljes, most már 1200 soros korpuszon
**visszaesett 7.6%-ra**, a küszöb alá. Ez megerősíti, hogy a tudatos
téma-rotáció stratégia (ami a simple_qa csomagnál is bevált) az
explanation csomagnál is működik.

## 3. Ellenőrzési lépések (teljes pipeline)

### 3.1 Schema validate
Mind a 100 sor strukturálisan érvényes.

### 3.2 Kizárt témák explicit ellenőrzése
A kizárt kifejezések egyikére sem volt találat. AI-tagelt sor: **0/100**.
`technika`-tagelt sor: **0/100** (szándékosan).

### 3.3 Teljes korpuszos cross-dedupe (a TELJES 1100 soros meglévő korpusz +
    ez a 100 sor, 0.9 küszöb, összesen 1200 sor)

A dedupe 5 db 0.9 fölötti egyezést jelzett, de **mind az öt a korábban már
dokumentált, megtartott simple_qa hamis pozitívok megismétlődése** - egyik
sem érinti sem ezt, sem az előző explanation batch-et. A hosszabb,
elaboráltabb explanation-stílus ismét jól elkülönült minden korábbi
tartalomtól.

### 3.4 `tools/dataset_topic_report.py`

**A teljes, egyesített korpuszon** (1000 simple_qa + 200 explanation =
1200 sor):

| Tag | 1100 sornál (előző kör) | **1200 sornál (most)** |
|---|---|---|
| technika | 8.3% (91) - túllépte | **7.6% (91)** - vissza a küszöb alá |
| iskola | 6.5% (71) | 5.9% (71) |
| biológia (bővült) | 3.0% (33) | 4.5% (54) |
| AI | 4.0% (44) | 3.7% (44) |
| nyelv (bővült) | 2.4% (26) | 2.5% (30) |
| pszichológia (ÚJ) | - | 1.7% (20) |
| etológia (ÚJ) | - | 1.7% (20) |
| kultúra (ÚJ) | - | 1.4% (17) |

**Túlreprezentált tagek: NINCS.**

### 3.5 `dataset_score.py`
Mind a 100 sor **100/100** pontot kapott, flag nélkül.

### 3.6 Safety/firewall ellenőrzés
- **`src/guard.py` `looks_like_identity_bleed()`**: **0 találat**.
- **Kiegészítő kulcsszó-szűrés**: **3 nyers találat**, mindhárom manuálisan
  ellenőrizve és **hamis pozitívnak** bizonyult:
  - "mérgez" (`explanation_0145`, "mérgező anyagok" - állati védekező
    mechanizmus biológiai leírása, nem mérgezésre való utasítás).
  - "vegyszer" (`explanation_0198`, "vegyszerek hatására" - a beporzó
    rovarok pusztulásának környezeti oka, nem vegyszerhasználati
    utasítás).
  - "kezelés" (`explanation_0105`, "könnyebbé teszi annak kezelését" - egy
    probléma "kezelése" hétköznapi értelemben, nem orvosi kezelés).
- **Pszichológiai blokk (101-120) külön is átnézve**: mind ÁLTALÁNOS,
  nem-klinikai mechanizmus-magyarázat, egyik sem ad diagnózist vagy
  terápiás tanácsot.
- **Kulturális/társadalmi blokk (121-140) külön is átnézve**: mind
  semleges, nem sztereotipizáló, kiegyensúlyozott megfogalmazás.

## 4. Manuális mintavételes tartalmi átnézés (20 sor, minden témablokkból 4)

| id | Instruction | Értékelés |
|---|---|---|
| explanation_0103 | Miért nehéz koncentrálni sok egyidejű inger között? | Semleges, nem-klinikai figyelmi mechanizmus. OK. |
| explanation_0110 | Hogyan alakul ki az önbizalom egy adott területen? | Pozitív, nem túlígérő pszichológiai magyarázat. OK. |
| explanation_0114 | Hogyan alakul ki egy előítélet? | Kiegyensúlyozott, nem stigmatizáló magyarázat. OK. |
| explanation_0119 | Miért segít a tervezés csökkenteni a szorongást egy feladat előtt? | Általános, nem klinikai tanács. OK. |
| explanation_0123 | Hogyan terjed el egy pletyka vagy hír egy közösségben? | Semleges társadalmi mechanizmus. OK. |
| explanation_0129 | Hogyan hat egymásra a nyelv és a gondolkodás? | Tudományos óvatossággal megfogalmazott. OK. |
| explanation_0134 | Miért fontos a kulturális örökség megőrzése? | Semleges, nem egyoldalú érv. OK. |
| explanation_0138 | Miért hatnak ránk a történetek és mítoszok olyan erősen? | Pontos, kulturálisan érzékeny magyarázat. OK. |
| explanation_0142 | Miért fontos a genetikai sokféleség egy populáción belül? | Pontos biológiai magyarázat. OK. |
| explanation_0146 | Miért fontosak a ragadozók egy ökoszisztéma egyensúlyában? | Pontos ökológiai mechanizmus. OK. |
| explanation_0154 | Miért képesek egyes állatok álcázni magukat a környezetükhöz? | Pontos evolúciós magyarázat. OK. |
| explanation_0159 | Hogyan hat a klímaváltozás az állatok élőhelyére és viselkedésére? | Tényszerű, nem alarmista. OK. |
| explanation_0163 | Miért oldódik fel a só a vízben? | Pontos kémiai magyarázat. OK. |
| explanation_0169 | Miért nehezebb felmelegíteni a vizet, mint sok más anyagot? | Pontos fizikai magyarázat. OK. |
| explanation_0174 | Hogyan alakul ki a felületi feszültség a vízen? | Pontos fizikai magyarázat. OK. |
| explanation_0180 | Hogyan alakul ki a hőmérsékleti egyensúly két különböző hőmérsékletű tárgy között? | Pontos, hétköznapi példával. OK. |
| explanation_0183 | Hogyan kommunikálnak egymással a méhek egy kaptáron belül? | Pontos etológiai magyarázat. OK. |
| explanation_0189 | Hogyan alkalmazkodnak az állatok a városi környezethez? | Semleges, tényszerű magyarázat. OK. |
| explanation_0195 | Hogyan érzékelik a denevérek a környezetüket sötétben? | Pontos, tudományosan helyes. OK. |
| explanation_0200 | Miért fontos a fajok viselkedésének megfigyelése a természetvédelemben? | Pozitív, nem elfogult természetvédelmi érv. OK. |

**Eredmény: 20/20 sor megfelelt.**

## 5. Fájlok

- Raw: `data/raw/claude_explanation_0101_0200_raw.jsonl` (100 sor)
- Clean: `data/clean/claude_explanation_0101_0200_clean.jsonl` (100 sor)
- Rejected: `data/rejected/claude_explanation_0101_0200_rejected.jsonl` (0 sor)

## 6. Regressziós teszt
`tests/test_v1_7_4_dataset_foundation.py` - **minden teszt sikeres, STÁTUSZ:
STABIL**.

## 7. Amit ez a kör NEM tett

- **Nem indított tanítást.**
- **Nem módosított webapp/backend kódot.**
- **Nem nyúlt a régi clean fájlokhoz.**

---

## Végső összegzés

- Raw sorok száma: **100**
- Clean sorok száma: **100**
- Rejected sorok száma: **0**
- Kereszt-batch duplikátumok száma: **0** (mind a korábbi simple_qa hamis
  pozitívok megismétlődése)
- Átlag quality_score: **100.0**
- Topic report (röviden): batch önmagában 5 témakörre fókuszált
  (pszichológiai/viselkedési mechanizmusok, kulturális/nyelvi/társadalmi
  mechanizmusok, biológiai/ökológiai mechanizmusok, fizikai/kémiai
  alapjelenségek, állattani/etológiai mechanizmusok); a `technika` tag
  korábbi enyhe túllépését sikeresen korrigálta (8.3%->7.6%), **nincs
  túlreprezentált tag**.
- 20 soros manuális mintavétel eredménye: **20/20 megfelelt**.
- **Egyedi clean explanation sorok jelenleg összesen: 200 / 1000.**
- **Hiányzik még a 2. csomag céljához: 800 sor.**

**STÁTUSZ: STABIL.**
