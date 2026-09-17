# Harmadik FELÜGYELT Claude-generált próba batch - simple_qa 0651-0750

- Forrás: **Claude-generált**, 100 db, kézzel megírt, majd a teljes meglévő
  pipeline-nal ellenőrzött sor. Az **1000 db egyszerű magyar kérdés-válasz
  célcsomag** (roadmap 1. csomag) folytatása - harmadik lépés a 0501-0550
  és 0551-0650 próbák után, ez már az AUTOPILOT v2 folyamat első batch-e.
- `source` mező: `synthetic_claude`.
- **Ez továbbra is TESZT kör** - a modellt NEM tanítottuk erre az adatra,
  webapp/backend kód nem változott.

## 1. Számok

| Mérőszám | Érték |
|---|---|
| Raw sorok | 100 |
| Validáláson elfogadva | 100 |
| Validáláson elutasítva | 0 |
| Kereszt-batch duplikátumként kiszűrve | **1** |
| **Végleges clean sorok** | **99** |
| **Rejected sorok** | **1** |
| Átlag quality_score | **100.0** |
| Flag-et kapott sor | 0 |

## 2. Ellenőrzési lépések (teljes pipeline)

### 2.1 Schema validate (`dataset_validate.py`)
Mind a 100 sor strukturálisan érvényes: helyes JSON, minden kötelező mező
jelen van, nincs escape-hiba, garbled/repeated-char minta, angol keveredés,
overclaiming.

### 2.2 Magyar nyelvi/formátum ellenőrzés
A validátor beépített ellenőrzésein túl minden sor 1-2 mondatos, természetes
magyar nyelvű - manuálisan is megerősítve a 3. pont mintavételénél.

### 2.3 Kizárt témák explicit ellenőrzése
A kizárt kifejezések (`nexora`, `mf-ai`, `wifi`/`wi-fi`, `vpn`, `cookie`,
`adathalász`, `tanítóadat`, `adatminőség`, `modelltesztelés`, `naplóírás`,
`üvegházhatás`, `bocsánat`, `ajándék`) egyikére sem volt találat
**(0/13 kizárt kifejezés, 0 érintett sor)**. AI-tagelt sor: **0/100**.

### 2.4 Batchen belüli dedupe
A batch saját 100 sora között nem volt 0.9 fölötti egyezés.

### 2.5 Teljes korpuszos cross-dedupe (a TELJES 492 soros meglévő korpusz +
    ez a 100 sor, 0.9 küszöb)
**1 valódi duplikátum található és javítva**:
- `simple_qa_0692` ("Mi a különbség a grillezés és a sütés között?") <->
  `simple_qa_0401` ("Mi a különbség a főzés és a sütés között?",
  `deepseek_simple_qa_0401_0450_clean.jsonl`) - **hasonlóság: 0.915**.
  Mindkét sor ugyanazt a mondatsablont ("Mi a különbség X és a sütés
  között?") használja, ÉS mindkét kifejtés lényegében ugyanúgy magyarázza
  a "sütés" oldalát (zárt térben, száraz hővel/sütőben) - ez valódi
  tartalmi átfedés, nem csak sablon-egyezés.
- **Kezelés**: a korábbi (`simple_qa_0401`) maradt a clean fájlban, az új
  (`simple_qa_0692`) átkerült a rejected fájlba, a megszokott sémával
  (`reason: duplicate_cross_batch`, `matched_id`, `matched_source`,
  `similarity`).
- **Javítás utáni ellenőrzés**: 0 fennmaradó duplikátum a 99 clean sorral
  újra futtatva.

### 2.6 `tools/dataset_topic_report.py`

**A batch önmagában** (99 sor, most ÖT ÚJ témakörre fókuszálva, tudatosan
kerülve az iskola/technika/sport további bővítését - lásd 5. pont):

| Tag | Darab | Arány |
|---|---|---|
| érzelmek | 20 | 20.2% |
| konyha | 19 | 19.2% |
| gazdaság | 13 | 13.1% |
| kert | 12 | 12.1% |
| fizika | 8 | 8.1% |
| jog | 7 | 7.1% |
| *(...további 8 tag, egyenként 2-6 sor)* | | |

**A teljes, egyesített korpuszon** (492 régi + 99 új = 591 sor):

| Tag | 492 sornál (előző kör) | **591 sornál (most)** |
|---|---|---|
| AI | 8.9% (44) | **7.4% (44)** - ELŐSZÖR ESETT 8% ALÁ, mert megint 0 új AI-sor jött, miközben a nevező nőtt |
| iskola | 14.4% (71) | 12.0% (71) - csökkent, mert nem bővült tovább |
| technika | 14.2% (70) | 11.8% (70) - csökkent, mert nem bővült tovább |
| konyha (ÚJ figyelendő) | 4.4% (26)* | 4.4% (26) - stabil, még messze a küszöb alatt |

*A konyha tag már a 0651-0750 előtt is létezett (7+10=17 sor korábban),
most 19 új sorral bővült - a teljes korpuszban 26 sor, 4.4%, messze a 8%-os
küszöb alatt, nem kritikus.

**Kiemelt eredmény: az AI/Nexora arány első alkalommal esett 8% alá** (a
formális "túlreprezentált" riasztási küszöb alatt van), a tervezett,
tudatos hígítási stratégia folyamatos alkalmazásának köszönhetően - lásd
`dataset_roadmap_0501_5000.md` 3. pont.

### 2.7 `dataset_score.py`
Mind a 99 megmaradt sor **100/100** pontot kapott, flag nélkül.

### 2.8 Safety/firewall ellenőrzés
- **`src/guard.py` `looks_like_identity_bleed()`** mind a 100 output-ra
  (a javítás előtt) lefuttatva - **0 találat**.
- **Kiegészítő kulcsszó-szűrés** (veszélyes/orvosi/jogi/pénzügyi-ígéret/
  személyesadat/telefonszám-minta): **1 nyers találat** ("lúg" -
  `simple_qa_0740`, "Mi az a savasság (pH)?") - manuálisan ellenőrizve:
  **hamis pozitív**, tisztán kémiai (pH-skála) definíció, nem veszélyes
  anyaggal kapcsolatos utasítás.
- **Jogi/gazdasági alapfogalmak (0671-0690) külön is átnézve**: minden sor
  SEMLEGES DEFINÍCIÓ ("mit jelent X"), egyik sem tartalmaz jogi vagy
  pénzügyi ÍGÉRETET (nincs "garantáltan megéri", "biztosan növekszik"
  típusú megfogalmazás).
- **Érzelmi/kapcsolati témák (0651-0670) külön is átnézve**: mind
  ÁLTALÁNOS, támogató jellegű tanács, egyik sem ad klinikai diagnózist
  vagy pszichológiai kezelési javaslatot.

## 3. Manuális mintavételes tartalmi átnézés (20 sor, minden témablokkból 4)

| id | Instruction | Értékelés |
|---|---|---|
| simple_qa_0652 | Mit tegyek, ha féltékeny vagyok? | Támogató, nem diagnosztikus tanács. OK. |
| simple_qa_0658 | Mit tegyek, ha úgy érzem, senki nem ért meg? | Általános, nem klinikai megfogalmazás. OK. |
| simple_qa_0665 | Hogyan kezeljem, ha kudarc ér? | Reális, nem túlígérő tanács. OK. |
| simple_qa_0670 | Mit tegyek, ha nehéz döntés előtt állok, ami másokat is érint? | Semleges döntéshozatali tanács. OK. |
| simple_qa_0672 | Mi az az infláció? | Pontos, semleges közgazdasági definíció, nincs ígéret. OK. |
| simple_qa_0678 | Mi az a GDP? | Pontos definíció. OK. |
| simple_qa_0684 | Mi az a szabadalom? | Pontos jogi definíció, nem ad jogi tanácsot. OK. |
| simple_qa_0689 | Mi a jog és az erkölcs közötti különbség? | Semleges, filozófiailag korrekt megkülönböztetés. OK. |
| simple_qa_0693 | Hogyan válasszak érett gyümölcsöt? | Gyakorlati, veszélytelen tanács. OK. |
| simple_qa_0700 | Mi az a marinálás? | Pontos konyhai fogalommagyarázat. OK. |
| simple_qa_0707 | Hogyan főzzek tökéletes lágy tojást? | Konkrét, veszélytelen recepttipp. OK. |
| simple_qa_0710 | Mi az a fermentálás? | Pontos, tudományosan helyes magyarázat. OK. |
| simple_qa_0713 | Mi a különbség az egynyári és az évelő növény között? | Pontos botanikai fogalom. OK. |
| simple_qa_0717 | Hogyan szoktassak egy kiskutyát szobatisztaságra? | Általános, humánus nevelési tanács. OK. |
| simple_qa_0722 | Hogyan kezdjek el barkácsolni otthon? | Veszélytelen, gyakorlati kezdő tanács. OK. |
| simple_qa_0730 | Miért fontos a talaj forgatása kertészkedéskor? | Pontos kertészeti magyarázat. OK. |
| simple_qa_0733 | Mi az az atom? | Pontos fizikai/kémiai definíció. OK. |
| simple_qa_0741 | Mi a különbség a rovar és a pók között? | Pontos állattani definíció. OK. |
| simple_qa_0744 | Mi az a DNS, egyszerűen megfogalmazva? | Pontos, egyszerűsített, de nem félrevezető biológiai magyarázat. OK. |
| simple_qa_0750 | Mi a tudományos módszer lényege? | Pontos, semleges tudományfilozófiai magyarázat. OK. |

**Eredmény: 20/20 sor megfelelt.**

## 4. Fájlok

- Raw: `data/raw/claude_simple_qa_0651_0750_raw.jsonl` (100 sor)
- Clean: `data/clean/claude_simple_qa_0651_0750_clean.jsonl` (99 sor)
- Rejected: `data/rejected/claude_simple_qa_0651_0750_rejected.jsonl` (1 sor)

## 5. Stratégiai megjegyzés: témaválasztás

Ez a batch tudatosan **öt teljesen új témakört** célzott (érzelmek/emberi
kapcsolatok, gazdaság/jog alapfogalmak, konyha/receptek, kert/állattartás/
barkácsolás, tudomány alapfogalmak), és **szándékosan nem bővítette** az
iskola/technika/sport kategóriákat - pontosan a `claude_simple_qa_0551_0650
_report.md` 2.4 pontjában megfogalmazott előretekintő javaslat szerint. Az
eredmény jól látszik: iskola és technika aránya CSÖKKENT (14.4%->12.0%,
illetve 14.2%->11.8%) a nagyobb nevező miatt, miközben egyetlen ilyen
témájú sor sem került be.

## 6. Regressziós teszt
A meglévő `tests/test_v1_7_4_dataset_foundation.py` - **minden teszt
sikeres, STÁTUSZ: STABIL**.

## 7. Amit ez a kör NEM tett

- **Nem indított tanítást.**
- **Nem módosított webapp/backend kódot.**
- **Nem nyúlt a régi (0151-0650) clean fájlokhoz** (a `simple_qa_0401`
  sort csak OLVASTA az összehasonlításhoz, nem módosította).

---

## Végső összegzés

- Raw sorok száma: **100**
- Clean sorok száma: **99**
- Rejected sorok száma: **1**
- Kereszt-batch duplikátumok száma: **1** (javítva - `simple_qa_0692`
  eltávolítva, `simple_qa_0401`-gyel 0.915 hasonlóság)
- Átlag quality_score: **100.0**
- Topic report (röviden): batch önmagában 5 új témakörre fókuszált
  (érzelmek, gazdaság, konyha, kert, tudomány); a teljes korpuszra vetítve
  az **AI/Nexora arány első alkalommal 8% alá esett (7.4%)**, iskola és
  technika aránya is tovább csökkent.
- 20 soros manuális mintavétel eredménye: **20/20 megfelelt**.
- **Egyedi clean simple_qa sorok jelenleg összesen: 591**
  (492 korábbi + 99 új ebből a batch-ből).
- **Hiányzik még az 1000 db simple_qa célhoz: 409 sor.**

**STÁTUSZ: STABIL.**
