# Első FELÜGYELT Claude-generált "magyarázós példa" batch - explanation 0001-0100

- Forrás: **Claude-generált**, 100 db, kézzel megírt, majd a teljes meglévő
  pipeline-nal ellenőrzött sor. Ez a **2. csomag (1000 db magyarázós
  példa)** első batch-e - az AUTOPILOT v2 folyamat folytatása az 1. csomag
  (1000 db simple_qa) sikeres lezárása után.
- `category`: `explanation` (a `data/samples/sample_pack_v1.jsonl`-ban már
  meglévő kategória sémáját követve).
- `source` mező: `synthetic_claude`.
- **Ez továbbra is TESZT kör** - a modellt NEM tanítottuk erre az adatra,
  webapp/backend kód nem változott.

## 1. Számok

| Mérőszám | Érték |
|---|---|
| Raw sorok | 100 |
| Validáláson elfogadva | 100 |
| Validáláson elutasítva | 0 |
| Kereszt-batch **jelzett** (0.9 fölötti) egyezés (teljes 1100 soros korpuszon) | 5 |
| Ebből az ÚJ explanation batch-et érintő | **0** |
| **Végleges clean sorok** | **100** |
| **Rejected sorok** | **0** |
| Átlag quality_score | **100.0** |
| Flag-et kapott sor | 0 |
| Difficulty eloszlás | medium: 90, hard: 10 |

## 2. Formátumi eltérés a simple_qa-hoz képest

A "magyarázós példa" (`explanation`) kategória - a `dataset_roadmap_
0501_5000.md` 1. pontja szerint - "fogalom-magyarázatok, 'hogyan működik
X' jellegű" tartalmat jelent, ezért ez a batch tudatosan **hosszabb,
3 mondatos, ok-okozati összefüggést kifejtő válaszokat** tartalmaz (átlag
~280-350 karakter), szemben a simple_qa 1-2 mondatos, ~86-299 karakteres
válaszaival. A `difficulty` mező is tudatosan `medium`/`hard` a
`sample_pack_v1.jsonl` explanation-mintáinak megfelelően (nem `easy`,
mint a simple_qa csomagnál volt).

## 3. Ellenőrzési lépések (teljes pipeline)

### 3.1 Schema validate
Mind a 100 sor strukturálisan érvényes.

### 3.2 Kizárt témák explicit ellenőrzése
A kizárt kifejezések (AI/Nexora/MF, wifi/VPN/cookie/adathalászat,
tanítóadat/adatminőség/modelltesztelés, naplóírás/üvegházhatás,
bocsánatkérés/ajándékozás) egyikére sem volt találat. AI-tagelt sor:
**0/100**.

### 3.3 Teljes korpuszos cross-dedupe (a TELJES 1000 soros simple_qa
    korpusz + ez a 100 sor, 0.9 küszöb, összesen 1100 sor)

A dedupe 5 db 0.9 fölötti egyezést jelzett, de **mind az öt pontosan a
korábban már dokumentált, megtartott hamis pozitív** (lásd
`claude_simple_qa_0851_0950_report.md` és `claude_simple_qa_1051_1159_
report.md`) - ezek kizárólag a régi simple_qa sorok között ismétlődnek.
**Az új explanation batch egyetlen sorát sem érintette semmilyen
jelzés.** Ez megerősíti, hogy a hosszabb, elaboráltabb explanation-stílus
jól elkülönül a simple_qa rövid, sablonosabb stílusától.

### 3.4 `tools/dataset_topic_report.py`

**A teljes, egyesített korpuszon** (1000 simple_qa + 100 explanation =
1100 sor):

| Tag | 1000 sornál (csak simple_qa) | **1100 sornál (most)** |
|---|---|---|
| technika | 7.1% (71) | **8.3% (91)** - FIGYELEM: túllépte a küszöböt |
| iskola | 7.1% (71) | 6.5% (71) |
| AI | 4.4% (44) | 4.0% (44) |
| gazdaság (bővült) | 1.3% (13) | 2.8% (31) |
| természet (ÚJ) | - | 2.1% (23) |

**Egy tag lépte túl a 8%-os küszöböt: `technika` (8.3%, 91 sor).** Ennek
oka, hogy ennek a batch-nek az 1-20. sora tudatosan "hogyan működik
mindennapi technológia" témára fókuszált, ami a meglévő 71 simple_qa
technika-sorra rakódott rá. **Ez egy valódi, de kismértékű (0.3%-os)
túllépés**, aminek tartalmi indoka van: a 20 új sor mind teljesen
különböző eszközt/technológiát magyaráz (hűtőszekrény, GPS, napelem,
zár, stb.), a cross-dedupe 0 találata is megerősíti, hogy nincs tartalmi
ismétlés. **Javaslat a következő explanation batch-hez**: kerülni kell a
`technika` tag további bővítését, amíg a nevező (a teljes korpusz) nem nő
elég nagyra ahhoz, hogy az arány visszaessen 8% alá - hasonlóan ahhoz,
ahogy az iskola/technika trend a simple_qa csomagnál is kezelve lett.

### 3.5 `dataset_score.py`
Mind a 100 sor **100/100** pontot kapott, flag nélkül.

### 3.6 Safety/firewall ellenőrzés
- **`src/guard.py` `looks_like_identity_bleed()`**: **0 találat**.
- **Kiegészítő kulcsszó-szűrés**: **2 nyers találat**, mindkettő manuálisan
  ellenőrizve és **hamis pozitívnak** bizonyult:
  - "adag" (`explanation_0098`, "nagy adagot" - étkezési adag/porció
    kontextus, nem gyógyszeradag).
  - "garantál" (`explanation_0048`, "Ez **nem** garantálja a sikert" -
    ez egy NEGÁLT, óvatosságra intő megfogalmazás, ami pont elkerüli a
    túlígérést, nem pénzügyi ígéret).
- **Gazdasági/pénzügyi blokk (41-60) külön is átnézve**: minden sor
  SEMLEGES mechanizmus-magyarázat, egyik sem ad konkrét befektetési vagy
  pénzügyi tanácsot/ígéretet.
- **Élettani blokk (61-80, 89, 98, 100) külön is átnézve**: minden sor
  ÁLTALÁNOS mechanizmus-magyarázat, egyik sem ad diagnózist vagy kezelési
  javaslatot.

## 4. Manuális mintavételes tartalmi átnézés (20 sor, minden témablokkból 4)

| id | Instruction | Értékelés |
|---|---|---|
| explanation_0003 | Hogyan működik a GPS helymeghatározás? | Pontos, technikailag korrekt magyarázat. OK. |
| explanation_0009 | Hogyan működik egy napelem? | Pontos fizikai mechanizmus. OK. |
| explanation_0016 | Hogyan emelkedik fel egy hőlégballon? | Pontos, jó analógiával. OK. |
| explanation_0022 | Hogyan keletkeznek a hegyek? | Pontos geológiai magyarázat. OK. |
| explanation_0031 | Miért látjuk kékesnek az eget napközben? | Pontos optikai magyarázat, jó mélységű. OK. |
| explanation_0038 | Hogyan keletkeznek a földrengések? | Pontos, nem ijesztgető magyarázat. OK. |
| explanation_0042 | Miért emelkednek az árak, ha nő a kereslet egy termék iránt? | Semleges közgazdasági mechanizmus, nincs ígéret. OK. |
| explanation_0047 | Hogyan alakul ki egy piaci monopólium? | Semleges, nem elfogult magyarázat. OK. |
| explanation_0052 | Miért fontos a központi bank függetlensége? | Kiegyensúlyozott, nem politikailag elfogult. OK. |
| explanation_0057 | Hogyan működik a biztosítási rendszer kockázatmegosztási elve? | Pontos, ígéret nélküli magyarázat. OK. |
| explanation_0062 | Miért alszunk éjszaka? | Élettanilag megalapozott, nem orvosi tanács. OK. |
| explanation_0066 | Miért gyorsul fel a szívverésünk testmozgás közben? | Pontos, semleges élettani magyarázat. OK. |
| explanation_0071 | Hogyan emlékszünk meg dolgokra hosszú távon? | Pontos, tudományosan megalapozott. OK. |
| explanation_0074 | Miért ásítunk? | Tudományos bizonytalanságot is jelző, nem túlígérő válasz. OK. |
| explanation_0081 | Miért ragad a méz? | Pontos kémiai-fizikai magyarázat. OK. |
| explanation_0086 | Miért pattan le a labda a földről? | Pontos mechanikai magyarázat. OK. |
| explanation_0091 | Miért törik meg a szívószál látszólag, ha vízbe tesszük? | Pontos optikai magyarázat. OK. |
| explanation_0094 | Miért fényesebbek a csillagok éjszaka, mint nappal? | Pontos csillagászati magyarázat. OK. |
| explanation_0097 | Miért kell várni néhány percet, mielőtt felvágjuk a frissen sült húst? | Veszélytelen, gyakorlati konyhai magyarázat. OK. |
| explanation_0100 | Miért érzünk feszültséget a fülünkben repülőgépen felszálláskor vagy leszálláskor? | Pontos élettani-fizikai magyarázat. OK. |

**Eredmény: 20/20 sor megfelelt.**

## 5. Fájlok

- Raw: `data/raw/claude_explanation_0001_0100_raw.jsonl` (100 sor)
- Clean: `data/clean/claude_explanation_0001_0100_clean.jsonl` (100 sor)
- Rejected: `data/rejected/claude_explanation_0001_0100_rejected.jsonl` (0 sor)

## 6. Regressziós teszt
`tests/test_v1_7_4_dataset_foundation.py` - **minden teszt sikeres, STÁTUSZ:
STABIL**.

## 7. Amit ez a kör NEM tett

- **Nem indított tanítást.**
- **Nem módosított webapp/backend kódot.**
- **Nem nyúlt a régi (simple_qa) clean fájlokhoz.**

---

## Végső összegzés

- Raw sorok száma: **100**
- Clean sorok száma: **100**
- Rejected sorok száma: **0**
- Kereszt-batch duplikátumok száma: **0** (a jelzett 5 mind a korábbi
  simple_qa hamis pozitívok megismétlődése, egyiket sem érintette ez a
  batch)
- Átlag quality_score: **100.0**
- Topic report (röviden): batch önmagában 5 témakörre fókuszált
  (mindennapi technológia, természeti jelenségek, társadalmi/gazdasági
  mechanizmusok, élettani mechanizmusok, hétköznapi jelenségek); a teljes
  1100 soros korpuszon **egy tag (`technika`) enyhén, 8.3%-ra túllépte a
  küszöböt** - dokumentálva, a következő explanation batch-nél kerülendő
  további bővítés.
- 20 soros manuális mintavétel eredménye: **20/20 megfelelt**.
- **Egyedi clean explanation sorok jelenleg összesen: 100 / 1000.**
- **Hiányzik még a 2. csomag (1000 db explanation) céljához: 900 sor.**

**STÁTUSZ: STABIL.**
