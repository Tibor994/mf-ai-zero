# Negyedik FELÜGYELT Claude-generált próba batch - simple_qa 0751-0850

- Forrás: **Claude-generált**, 100 db, kézzel megírt, majd a teljes meglévő
  pipeline-nal ellenőrzött sor. Az **1000 db egyszerű magyar kérdés-válasz
  célcsomag** folytatása - az AUTOPILOT v2 folyamat második batch-e.
- `source` mező: `synthetic_claude`.
- **Ez továbbra is TESZT kör** - a modellt NEM tanítottuk erre az adatra,
  webapp/backend kód nem változott.

## 1. Számok

| Mérőszám | Érték |
|---|---|
| Raw sorok | 100 |
| Validáláson elfogadva | 100 |
| Validáláson elutasítva | 0 |
| Kereszt-batch duplikátumként kiszűrve | **0** |
| **Végleges clean sorok** | **100** |
| **Rejected sorok** | **0** |
| Átlag quality_score | **100.0** |
| Flag-et kapott sor | 0 |

## 2. Ellenőrzési lépések (teljes pipeline)

### 2.1 Schema validate
Mind a 100 sor strukturálisan érvényes.

### 2.2 Kizárt témák explicit ellenőrzése
A kizárt kifejezések (`nexora`, `mf-ai`, `wifi`/`wi-fi`, `vpn`, `cookie`,
`adathalász`, `tanítóadat`, `adatminőség`, `modelltesztelés`, `naplóírás`,
`üvegházhatás`, `bocsánat`, `ajándék`) egyikére sem volt találat. AI-tagelt
sor: **0/100**.

### 2.3 Batchen belüli dedupe
0 egyezés a 100 sor között.

### 2.4 Teljes korpuszos cross-dedupe (a TELJES 591 soros meglévő korpusz +
    ez a 100 sor, 0.9 küszöb, összesen 691 sor)
**0 duplikátum.** A batch öt vadonatúj témakörre (sportszabályok,
gasztronómia, zene, programozás, utazás-logisztika) fókuszált, amelyek a
korábbi korpusztól tartalmilag jól elkülönülnek - a nulla találat ezt
numerikusan is megerősíti.

### 2.5 `tools/dataset_topic_report.py`

**A batch önmagában** (100 sor, 5×20 új témakör):

| Tag | Darab | Arány |
|---|---|---|
| sportszabályok | 20 | 20.0% |
| gasztronómia | 20 | 20.0% |
| zene | 20 | 20.0% |
| programozás | 20 | 20.0% |
| utazás | 20 | 20.0% |

**A teljes, egyesített korpuszon** (591 régi + 100 új = 691 sor):

| Tag | 591 sornál (előző kör) | **691 sornál (most)** |
|---|---|---|
| AI | 7.4% (44) | **6.4% (44)** - tovább csökkent |
| iskola | 12.0% (71) | 10.3% (71) - tovább csökkent |
| technika | 11.8% (70) | 10.1% (70) - tovább csökkent |

**Az AI/Nexora arány folyamatosan, minden körben csökken** (12.9% -> 11.2%
-> 8.9% -> 7.4% -> **6.4%**), az iskola/technika arány is tovább mérséklődik
- mindkettő a tudatos, más témákra fókuszáló batch-tervezés eredménye.
Fontos: a `sport` tagtól tudatosan megkülönböztetett `sportszabályok` tag
(20 sor) elkerüli, hogy a már amúgy is jelentős `sport` kategória (26 sor)
tovább koncentrálódjon egyetlen témán belül - ez utólag pontosabb
topic-riportot is eredményez.

### 2.6 `dataset_score.py`
Mind a 100 sor **100/100** pontot kapott, flag nélkül.

### 2.7 Safety/firewall ellenőrzés
- **`src/guard.py` `looks_like_identity_bleed()`**: **0 találat**.
- **Kiegészítő kulcsszó-szűrés**: **2 nyers találat** ("adag" -
  `simple_qa_0780` "tapas... apró adagokban", `simple_qa_0783` "rizottó...
  adagolt lével") - mindkettő manuálisan ellenőrizve **hamis pozitívnak**
  bizonyult, tisztán élelmiszer-adagolási/főzési kontextus, nem
  gyógyszeradaggal kapcsolatos.
- **Jogi/utazási témák (0831-0850) külön is átnézve**: mind SEMLEGES
  definíció vagy gyakorlati tanács, egyik sem ad konkrét jogi ígéretet
  (pl. vízumszerzés garantálása) vagy pénzügyi ígéretet.

## 3. Manuális mintavételes tartalmi átnézés (20 sor, minden témablokkból 4)

| id | Instruction | Értékelés |
|---|---|---|
| simple_qa_0753 | Hogyan lehet pontot szerezni kosárlabdában? | Pontos sportszabály. OK. |
| simple_qa_0758 | Mi az a maraton? | Pontos definíció. OK. |
| simple_qa_0765 | Mi a különbség a súlyemelés és a testépítés között? | Pontos, semleges sportfogalom. OK. |
| simple_qa_0769 | Mi az a sportszerűség? | Pontos etikai fogalom. OK. |
| simple_qa_0772 | Mi az a curry? | Pontos gasztronómiai definíció. OK. |
| simple_qa_0777 | Mi a különbség a ramen és a pho leves között? | Pontos, kulturálisan korrekt magyarázat. OK. |
| simple_qa_0782 | Mi az a kimchi? | Pontos, veszélytelen ételleírás. OK. |
| simple_qa_0790 | Mi az a street food? | Semleges fogalommagyarázat. OK. |
| simple_qa_0793 | Mi a különbség a dallam és a ritmus között? | Pontos zeneelméleti fogalom. OK. |
| simple_qa_0798 | Mi az a metronóm? | Pontos zenei eszköz-leírás. OK. |
| simple_qa_0803 | Mi a különbség az akusztikus és az elektromos gitár között? | Pontos, technikailag korrekt. OK. |
| simple_qa_0810 | Mi az az akkord a zenében? | Pontos zeneelméleti definíció. OK. |
| simple_qa_0811 | Mi az az algoritmus? | Pontos, közérthető informatikai fogalom. OK. |
| simple_qa_0817 | Mi a különbség a szoftver és a hardver között? | Pontos alapfogalom. OK. |
| simple_qa_0822 | Mi az az adatbázis, egyszerűen megfogalmazva? | Pontos, egyszerűsített magyarázat. OK. |
| simple_qa_0827 | Mi a különbség a nyílt forráskódú és a zárt forráskódú szoftver között? | Semleges, pontos fogalom. OK. |
| simple_qa_0831 | Mi az a vízum? | Pontos, semleges definíció, nincs jogi ígéret. OK. |
| simple_qa_0838 | Miért érdemes utazási biztosítást kötni külföldi útra? | Semleges indoklás, NEM pénzügyi ígéret. OK. |
| simple_qa_0845 | Mi a különbség a vámmentes és a vámköteles termék között? | Pontos, semleges vámfogalom. OK. |
| simple_qa_0848 | Miért hasznos néhány alapkifejezést megtanulni az adott ország nyelvén utazás előtt? | Kulturálisan érzékeny, semleges tanács. OK. |

**Eredmény: 20/20 sor megfelelt.**

## 4. Fájlok

- Raw: `data/raw/claude_simple_qa_0751_0850_raw.jsonl` (100 sor)
- Clean: `data/clean/claude_simple_qa_0751_0850_clean.jsonl` (100 sor)
- Rejected: `data/rejected/claude_simple_qa_0751_0850_rejected.jsonl` (0 sor)

## 5. Regressziós teszt
`tests/test_v1_7_4_dataset_foundation.py` - **minden teszt sikeres, STÁTUSZ:
STABIL**.

## 6. Amit ez a kör NEM tett

- **Nem indított tanítást.**
- **Nem módosított webapp/backend kódot.**
- **Nem nyúlt a régi (0151-0750) clean fájlokhoz.**

---

## Végső összegzés

- Raw sorok száma: **100**
- Clean sorok száma: **100**
- Rejected sorok száma: **0**
- Kereszt-batch duplikátumok száma: **0**
- Átlag quality_score: **100.0**
- Topic report (röviden): batch önmagában 5 vadonatúj témakörre fókuszált
  (sportszabályok, gasztronómia, zene, programozás, utazás-logisztika); a
  teljes korpuszra vetítve az **AI/Nexora arány tovább csökkent 7.4%-ról
  6.4%-ra**, iskola/technika is tovább mérséklődött (10.3%/10.1%).
- 20 soros manuális mintavétel eredménye: **20/20 megfelelt**.
- **Egyedi clean simple_qa sorok jelenleg összesen: 691**
  (591 korábbi + 100 új ebből a batch-ből).
- **Hiányzik még az 1000 db simple_qa célhoz: 309 sor.**

**STÁTUSZ: STABIL.**
