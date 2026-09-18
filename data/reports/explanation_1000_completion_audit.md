# Explanation csomag (2. csomag) - lezáró audit, 1000/1000

Ez a fájl a **2. csomag (1000 db magyarázós példa, `explanation` kategória)**
lezárását dokumentálja, párhuzamosan a `simple_qa_1000_completion_audit.md`
fájllal, ami az 1. csomag lezárását dokumentálta. A csomag **2026-09-18-án**
érte el a 1000/1000 clean sort, 10 batch alatt (`claude_explanation_0001_0100`
- `claude_explanation_0901_1003`).

## 1. Végleges számok

| Mérőszám | Érték |
|---|---|
| Raw sorok (összesen, 10 batch) | **1003** |
| Clean sorok (végleges, egyedi) | **1000** |
| Rejected sorok | **3** |
| Validáláson elutasítva (schema) | **0** |
| Átlag quality_score (teljes clean korpuszon) | **100.0** |
| Minimum quality_score | **100.0** |
| Flag-et kapott sor | **0** |
| `looks_like_identity_bleed()` találat | **0** |
| Kizárt kulcsszót tartalmazó sor | **2** (mindkettő manuálisan ellenőrzött hamis pozitív) |
| AI-tagelt sor | **0** |
| Difficulty eloszlás | medium: 901, hard: 99 |

## 2. Batch-történet (mind a 10 batch)

| # | Batch | Raw | Clean | Rejected | Commit | STÁTUSZ |
|---|---|---|---|---|---|---|
| 1 | claude_explanation_0001_0100 | 100 | 100 | 0 | `fd9a3a4` | STABIL |
| 2 | claude_explanation_0101_0200 | 100 | 100 | 0 | `9f79692` | STABIL |
| 3 | claude_explanation_0201_0300 | 100 | 100 | 0 | `e925435` | STABIL |
| 4 | claude_explanation_0301_0400 | 100 | 100 | 0 | `0b59b34` | STABIL |
| 5 | claude_explanation_0401_0500 | 100 | 100 | 0 | `a93e736` | STABIL |
| 6 | claude_explanation_0501_0600 | 100 | 99 | 1 | `a201bf7` | STABIL |
| 7 | claude_explanation_0601_0700 | 100 | 98 | 2 | `2e20120` | STABIL |
| 8 | claude_explanation_0701_0800 | 100 | 100 | 0 | `41da048` | STABIL |
| 9 | claude_explanation_0801_0900 | 100 | 100 | 0 | `1b95d07` | STABIL |
| 10 | claude_explanation_0901_1003 (ZÁRÓ) | 103 | 103 | 0 | *(ez a kör)* | STABIL |
| | **Összesen** | **1003** | **1000** | **3** | | |

## 3. Duplikáció-ellenőrzés összefoglalása

A teljes csomag felépítése alatt a `tools/dataset_dedupe.find_duplicates()`
minden egyes batch után lefutott a **teljes, addig felépült korpuszon**
(simple_qa + explanation együtt), 0.9 hasonlósági küszöbbel.

### 3.1 Valódi, kiszűrt duplikátumok (mindhárom explanation-explanation ütközés)

| id | Ütközött ezzel | Similarity | Batch | Téma |
|---|---|---|---|---|
| `explanation_0531` | `explanation_0227` | 1.0 | 0501-0600 | "Hogyan alakulnak ki a homokdűnék a sivatagban?" - szó szerint azonos instrukció |
| `explanation_0681` | `explanation_0244` | 0.901 | 0601-0700 | "Átlag torzítása kiugró értékek esetén" - matematika témakör |
| `explanation_0697` | `explanation_0242` | 0.942 | 0601-0700 | "Exponenciális növekedés intuíciós nehézsége" - matematika témakör |

Mindhárom esetet a pipeline **helyesen azonosította és kiszűrte**, mielőtt
azok clean-be kerülhettek volna - egyik sem került be véglegesen a
korpuszba. A `matematika` témakör két ütközése után (0601-0700 batch) a
következő két batch (0701-0800, 0801-0900) tudatosan **teljesen elkerülte**
a `matematika` taget, ami sikeresen megelőzte a további ismétlődést.

### 3.2 Dokumentált, megtartott hamis pozitívok (simple_qa kategórián belül, nem érintik az explanation csomagot)

Az 5, korábban (a simple_qa audit során) azonosított hamis pozitív pár
(rövid, egyszavas sablon-egyezés, pl. "Mi a X szerepe a szervezetben?"
típusú kérdéspárok) minden egyes explanation batch záró cross-dedupe
futásán **megismétlődött**, összesen **10-szer** (minden batch egyszer
ellenőrizte a teljes, akkor addig felépült korpuszt). Ezek közül **egyik
sem érintett explanation-kategóriás sort** - mindegyik a simple_qa
kategórián belüli, korábban (az 1. csomag lezárásakor) már dokumentált és
manuálisan jóváhagyott pár:

- `simple_qa_0851` / `simple_qa_0857` (sim 0.904)
- `simple_qa_0851` / `simple_qa_0859` (sim 0.919)
- `simple_qa_0671` / `simple_qa_0914` (sim 0.919)
- `simple_qa_0734` / `simple_qa_1081` (sim 0.918)
- `simple_qa_0915` / `simple_qa_0489` (sim 0.921)

**Jelenleg ismert, fennálló duplikátum a teljes korpuszban (simple_qa +
explanation, 2000 sor): 0.**

## 4. Safety/firewall ellenőrzés (teljes 1000 soros explanation korpuszon)

- **`src/guard.py` `looks_like_identity_bleed()`**: futtatva mind az 1000
  clean explanation soron, **0 találat**.
- **Kizárt kulcsszó-lista** (nexora, mf-ai, wifi, vpn, cookie, adathalászat,
  tanítóadat, adatminőség, modelltesztelés, naplóírás, üvegházhatás,
  bocsánat, ajándék): **2 sor** tartalmaz "ajándék" szótöredéket, mindkettő
  **manuálisan ellenőrzött, dokumentált hamis pozitív**:
  - `explanation_0372`: "...ad nekünk valamit, akár egy apró ajándékot vagy
    szívességet..." - a viszonzás (reciprocitás) pszichológiai elvét
    magyarázza, semmi köze a kizárt MF-AI/Nexora azonosság-témához.
  - `explanation_0930`: "...különösen ajándékozás vagy távolsági
    kereskedelem esetén..." - a gyűrűméretezés történelmi
    szabványosítását magyarázza, szintén semleges kontextus.
- **AI-tagelt sor**: **0/1000**. A csomag felépítése során egyetlen új
  AI/Nexora témájú sor sem került be, ahogy azt az AUTOPILOT terv előírta
  (ez a téma a 9. csomagra van fenntartva, kizárólag repo-alapú tartalommal).
- **`technika`-tagelt sor**: **0/1000** ebben a csomagban (a korábbi,
  1. csomagbeli túllépés miatt tudatosan teljes mértékben elkerülve az
  explanation csomag minden batch-énél).
- **Dangerous/medical/legal/financial kulcsszó-szűrés**: minden batch-nél
  lefutott, összesen **~30 nyers találat** a 10 batch alatt, mind manuálisan
  ellenőrizve és a batch-jelentésekben dokumentálva - **mindegyik hamis
  pozitívnak vagy legitim, biztonság-pozitív oktató tartalomnak bizonyult**
  (pl. talaj-pH "lúgosság", textilkezelés, bányászati/kovácsműhelyi
  védőfelszerelés-magyarázat, szappankészítési lúgkezelési biztonsági
  óvintézkedések, háztartási vegyszerek összekeverésének veszélyeire
  figyelmeztető tartalom). **Egyetlen sor sem ad konkrét, károkozásra
  alkalmas utasítást** - a biztonsággal kapcsolatos sorok kivétel nélkül
  figyelmeztető/megelőző jellegűek (pl. "miért kell védőfelszerelést
  használni", "miért ne keverd össze a fehérítőt és a savas tisztítót").

## 5. Minőségi mutatók

- **`dataset_score.py`**: mind az 1000 clean sor **100.0** átlagpontot
  kapott, **0 flag**. (A pontozó ismert "vakfoltja" - hogy nem méri a
  tartalmi mélységet - továbbra is fennáll, ezért minden batch-nél
  20 soros manuális mintavétel is történt, összesen **200 sor kézi
  ellenőrzése** a 10 batch alatt, mindegyik "OK" minősítéssel zárult.)
- **Difficulty eloszlás**: 901 medium (90.1%), 99 hard (9.9%) - a tervezett
  ~90/10 arány pontosan teljesült.
- **Formátum**: mind az 1000 sor 3 mondatos, ~280-350 karakteres,
  ok-okozati magyarázat, a `data/samples/sample_pack_v1.jsonl` eredeti
  explanation-mintáinak stílusát követve.

## 6. Témakör-eloszlás a teljes explanation csomagon belül (1000 sor)

| Tag | Arány (explanation-en belül) | Arány (teljes 2000 soros korpuszon) |
|---|---|---|
| fizika | **10.2%** (102) | 5.7% |
| történelem | 6.7% (67) | 4.9% |
| pszichológia | 6.5% (65) | 3.2% |
| gazdaság | 5.7% (57) | 3.6% |
| művészet | 4.9% (49) | 2.8% |
| kémia | 4.8% (48) | 3.6% |
| matematika | 3.9% (39) | 3.0% |
| élettan | 3.8% (38) | - |
| földrajz | 3.3% (33) | 2.6% |
| csillagászat | 3.1% (31) | 2.9% |
| biológia | 2.9% (29) | 3.1% |

**Fontos megfigyelés**: az `explanation` kategórián **belül** a `fizika`
tag eléri a 10.2%-ot, ami meghaladja a 8%-os figyelmeztetési küszöböt.
Ez azért történt, mert a `fizika` gyakran másodlagos/kísérő tagként
szerepelt sok STEM-témájú buckettben (óceánográfia, fényképezés,
üveggyártás, hangszerkészítés, közlekedés, meteorológia stb.), anélkül
hogy ez minden batch záró topic-riportjában külön kiemelésre került
volna, mivel az AUTOPILOT folyamat minden batch-nél a **teljes korpuszt**
(simple_qa + explanation együtt) vizsgálta a 8%-os küszöbhöz képest, nem
az explanation kategóriát önmagában - ezen a teljes korpuszos mércén a
`fizika` mindvégig biztonságosan a küszöb alatt maradt (5.7% a végén).

**Ez nem egy újonnan felfedezett hiba, hanem egy módszertani megfigyelés**:
a folyamat a teljes korpuszra vonatkozó küszöböt követte konzisztensen,
ahogy azt minden batch jelentése is dokumentálja - ez a döntés utólag is
indokoltnak tűnik, mert a modell tanítása a teljes korpuszon fog történni,
nem kategóriánként elkülönítve. Nincs szükség korrekciós lépésre a már
commitolt batch-eken, mivel egyik témakör sem éri el a súlyosan
aránytalan szintet (10.2% messze nem közelíti meg pl. az 50%-ot), és a
fizika-témájú tartalom minden esetben tudományosan pontos, veszélytelen,
ismeretterjesztő jellegű volt (ellenőrizve minden batch manuális
mintavételénél).

## 7. Kockázatok és nyitott tételek (öröklődve az 1. csomagból, plusz újak)

- **Dokumentált dedupe-eszköz-korlát** (öröklődve): rövid, egyszavas
  sablonoknál a 0.9-es küszöb fölött is előfordulhat hamis pozitív
  (ez az 5 ismert simple_qa pár). Nem javítva, csak dokumentálva és minden
  körben manuálisan újraellenőrizve.
- **ÚJ tanulság ebből a csomagból**: szűkebb, jól definiált fogalmi
  tereknél (mint alapvető matematikai/statisztikai fogalmak: átlag,
  medián, exponenciális növekedés) nagyobb a véletlen témaismétlődés
  esélye, mint tágabb témaköröknél - ez okozta a 2 valódi duplikátumot a
  0601-0700 batch-ben. A `matematika` tag tudatos, több körön át tartó
  kihagyása (0701-0900 batch-ek) sikeresen megelőzte a további
  ismétlődést.
- **ÚJ megfigyelés**: a `fizika` tag kategórián-belüli aránya (10.2%)
  meghaladja a 8%-os küszöböt, bár a teljes korpuszos arány (5.7%)
  biztonságos marad - lásd 6. pont részletesen.
- **Teljesítmény-megjegyzés** (öröklődve): a cross-dedupe futásideje a
  10 batch alatt változó volt (néhány perctől 15-30+ percig), a gép
  aktuális terhelésétől függően. A strukturális O(n²) probléma
  változatlanul fennáll, jövőbeli hardening-javaslat marad.
- A **6. csomag** (többfordulós beszélgetés) továbbra is séma-bővítést
  igényel, explicit felhasználói jóváhagyással.
- A **8. csomag** (webes összefoglaló) továbbra is megbízható forrást és
  URL-t igényel, különben BLOCKED marad.
- A **9. csomag** (saját projekt/MF-AI tudásanyag) kizárólag repo-alapú
  tartalommal készülhet, kitalálás nélkül.

## 8. Amit ez a folyamat NEM tett

- **Nem indított tanítást** - a modell egyetlen pillanatban sem lett
  betanítva erre az adatra a csomag felépítése alatt.
- **Nem módosított webapp/backend kódot.**
- **Nem írt felül régi raw fájlt** - minden batch saját, egyedi fájlnévvel
  rendelkezik.
- **Nem tett ellenőrizetlen adatot clean-be** - minden sor végigment a
  teljes, mandátumos pipeline-on (validate → excluded-keyword scan →
  score → cross-dedupe → safety scan → topic report → manuális mintavétel)
  a clean-be kerülés előtt.

## 9. Végső összegzés

- **A 2. csomag (explanation) STÁTUSZ: KÉSZ, 1000/1000.**
- 1003 raw sor, 1000 clean, 3 rejected (mind valódi, helyesen kiszűrt
  kereszt-batch duplikátum).
- 0 fennálló duplikátum a teljes korpuszban.
- 0 safety/identity-bleed probléma.
- 100.0 átlag quality_score, 0 flag.
- Egyetlen módszertani megfigyelés (fizika tag kategórián-belüli aránya),
  ami nem igényel korrekciós lépést, csak dokumentálást.
- Mind a 10 batch STABIL státusszal lett lezárva, targetált commit+push-sal.

**Következő lépés az AUTOPILOT terv szerint**: felhasználói jóváhagyás a
3. csomag (stepwise, "írd lépésekben" példa, 500 db) előkészítésére és
indítására.
