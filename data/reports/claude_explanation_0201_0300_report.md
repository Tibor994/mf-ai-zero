# Harmadik FELÜGYELT Claude-generált "magyarázós példa" batch - explanation 0201-0300

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
| Kereszt-batch **jelzett** (0.9 fölötti) egyezés (teljes 1300 soros korpuszon) | 5 |
| Ebből az ÚJ explanation batch-et érintő | **0** |
| **Végleges clean sorok** | **100** |
| **Rejected sorok** | **0** |
| Átlag quality_score | **100.0** |
| Flag-et kapott sor | 0 |
| Difficulty eloszlás | medium: 90, hard: 10 |

## 2. Ellenőrzési lépések (teljes pipeline)

### 2.1 Schema validate
Mind a 100 sor strukturálisan érvényes.

### 2.2 Kizárt témák explicit ellenőrzése
A kizárt kifejezések egyikére sem volt találat. AI-tagelt sor: **0/100**.
`technika`-tagelt sor: **0/100** (a korábbi túllépés óta tudatosan
kerülve).

### 2.3 Teljes korpuszos cross-dedupe (a TELJES 1200 soros meglévő korpusz +
    ez a 100 sor, 0.9 küszöb, összesen 1300 sor)

A dedupe 5 db 0.9 fölötti egyezést jelzett, de **mind az öt a korábban már
dokumentált, megtartott simple_qa hamis pozitívok megismétlődése** - egyik
sem érinti ezt vagy bármelyik korábbi explanation batch-et.

### 2.4 `tools/dataset_topic_report.py`

**A teljes, egyesített korpuszon** (1000 simple_qa + 300 explanation =
1300 sor):

| Tag | 1200 sornál (előző kör) | **1300 sornál (most)** |
|---|---|---|
| technika | 7.6% (91) | **7.0% (91)** - tovább csökken |
| iskola | 5.9% (71) | 5.5% (71) |
| matematika (ÚJ) | - | 3.2% (42) |
| földrajz (bővült) | 2.2% (27) | 3.0% (39) |
| jog (ÚJ) | - | 2.4% (31) |
| életmód (bővült) | - | 2.4% (31) |
| művészet (ÚJ) | - | ~1.5% (kb. 20) |

**Túlreprezentált tagek: NINCS.**

### 2.5 `dataset_score.py`
Mind a 100 sor **100/100** pontot kapott, flag nélkül.

### 2.6 Safety/firewall ellenőrzés
- **`src/guard.py` `looks_like_identity_bleed()`**: **0 találat**.
- **Kiegészítő kulcsszó-szűrés**: **3 nyers találat**, mindhárom
  manuálisan ellenőrizve és **hamis pozitívnak** bizonyult:
  - "kezelés" (`explanation_0289`, `explanation_0298` - "stresszkezelési
    technikák", általános pszichológiai megküzdés, nem orvosi kezelés).
  - "garantál" (`explanation_0243`, "A valószínűségi szemlélet **nem** ad
    garantált választ" - negált, óvatosságra intő megfogalmazás).
- **Jogi blokk (201-220) külön is átnézve**: minden sor SEMLEGES,
  ismeretterjesztő jogi fogalommagyarázat, egyik sem ad konkrét jogi
  tanácsot az olvasó saját helyzetére.
- **Életmódi blokk (281-300) külön is átnézve**: minden sor ÁLTALÁNOS,
  nem-klinikai élettani mechanizmus-magyarázat, egyik sem ad orvosi
  diagnózist vagy kezelési utasítást.

## 3. Manuális mintavételes tartalmi átnézés (20 sor, minden témablokkból 4)

| id | Instruction | Értékelés |
|---|---|---|
| explanation_0202 | Hogyan működik az ártatlanság vélelme a jogrendszerben? | Pontos, semleges jogi alapelv. OK. |
| explanation_0207 | Miért fontos a magánélethez való jog? | Kiegyensúlyozott alapjogi magyarázat. OK. |
| explanation_0213 | Miért fontos a gyermekek jogainak külön védelme? | Semleges, nem politizáló magyarázat. OK. |
| explanation_0219 | Miért fontos az esküdtszéki rendszer egyes jogrendszerekben? | Semleges, nem egyoldalú. OK. |
| explanation_0223 | Hogyan keletkeznek a kanyonok? | Pontos geológiai magyarázat. OK. |
| explanation_0230 | Miért különböznek a partvonalak jellege egymástól? | Pontos földrajzi mechanizmus. OK. |
| explanation_0236 | Miért van vulkanikus tevékenység bizonyos földrajzi területeken? | Pontos, tudományosan helyes. OK. |
| explanation_0240 | Miért fontosak a hegyláncok az éghajlat alakításában egy régióban? | Pontos éghajlattani magyarázat. OK. |
| explanation_0244 | Miért félrevezető lehet az átlag önmagában, kiugró értékek esetén? | Pontos statisztikai magyarázat. OK. |
| explanation_0249 | Hogyan működik az optimalizálás elve egy korlátozott erőforrás esetén? | Semleges, gyakorlati matematikai elv. OK. |
| explanation_0255 | Hogyan segít a logikai érvelés az ellentmondások felismerésében? | Pontos logikai fogalom. OK. |
| explanation_0260 | Miért segít a probléma kisebb részekre bontása a megoldásban? | Gyakorlati, veszélytelen tanács. OK. |
| explanation_0263 | Miért fontos a negatív tér (üres tér) egy kompozícióban? | Pontos design-elv. OK. |
| explanation_0269 | Miért érezzük vonzónak a szimmetrikus formákat és arcokat? | Tudományosan megalapozott, nem túlzó. OK. |
| explanation_0274 | Hogyan befolyásolja a betűtípus megválasztása egy szöveg érzékelt hangulatát? | Pontos tipográfiai elv. OK. |
| explanation_0279 | Miért érezzük vonzónak a természetes formákat és mintázatokat a designban? | Pontos, tudományos alapú magyarázat. OK. |
| explanation_0283 | Miért fontos a változatos mozgásforma a testi egészség szempontjából? | Általános, nem orvosi tanács. OK. |
| explanation_0289 | Miért fontos a stressz-szint kezelése a hosszú távú jóllét szempontjából? | Kiegyensúlyozott, nem klinikai. OK. |
| explanation_0294 | Hogyan hat a képernyőidő csökkentése lefekvés előtt az elalvásra? | Általános, nem orvosi javaslat. OK. |
| explanation_0299 | Miért fontos a rendszeres testmozgás a csontok egészsége szempontjából? | Általános élettani magyarázat, nem diagnózis. OK. |

**Eredmény: 20/20 sor megfelelt.**

## 4. Fájlok

- Raw: `data/raw/claude_explanation_0201_0300_raw.jsonl` (100 sor)
- Clean: `data/clean/claude_explanation_0201_0300_clean.jsonl` (100 sor)
- Rejected: `data/rejected/claude_explanation_0201_0300_rejected.jsonl` (0 sor)

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
- Kereszt-batch duplikátumok száma: **0** (mind a korábbi simple_qa hamis
  pozitívok megismétlődése)
- Átlag quality_score: **100.0**
- Topic report (röviden): batch önmagában 5 témakörre fókuszált (jogi/
  etikai alapfogalmak, földrajzi/geológiai mechanizmusok, matematikai/
  logikai gondolkodás, művészet/design elvei, élettani/egészséges
  szokások mechanizmusai); a `technika` tag tovább csökkent (7.6%->7.0%),
  **nincs túlreprezentált tag**.
- 20 soros manuális mintavétel eredménye: **20/20 megfelelt**.
- **Egyedi clean explanation sorok jelenleg összesen: 300 / 1000.**
- **Hiányzik még a 2. csomag céljához: 700 sor.**

**STÁTUSZ: STABIL.**
