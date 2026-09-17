# Első FELÜGYELT Claude-generált próba batch - simple_qa 0501-0550

- Forrás: **Claude-generált** (nem DeepSeek) - 50 db, kézzel megírt, majd a
  teljes meglévő pipeline-nal ellenőrzött sor.
- `source` mező: `synthetic_claude` (a user kérése szerint, megkülönböztetve
  a korábbi DeepSeek batch-ek `synthetic` értékétől).
- **Ez egy TESZT kör** - a modellt NEM tanítottuk erre az adatra, nem
  történt commit/push, webapp/backend kód nem változott.

## 1. Számok

| Mérőszám | Érték |
|---|---|
| Raw sorok | 50 |
| Validáláson elfogadva | 50 |
| Validáláson elutasítva | 0 |
| Kereszt-batch duplikátumként kiszűrve | 0 |
| **Végleges clean sorok** | **50** |
| **Rejected sorok** | **0** |
| Átlag quality_score | **100.0** |
| Flag-et kapott sor | 0 |

## 2. Ellenőrzési lépések (teljes pipeline)

### 2.1 `dataset_validate.py`
Mind az 50 sor strukturálisan érvényes: helyes JSON, minden kötelező mező
jelen van (`id, category, instruction, input, output, tags, difficulty,
quality_notes, source`), nincs escape-hiba, nincs garbled/repeated-char
minta, nincs angol keveredés, nincs overclaiming, nincs a validátor
beépített személyesadat- vagy veszélyestartalom-mintája (e-mail-szerű,
telefonszám-szerű, kulcs/jelszó-szerű minta - 0 találat).

### 2.2 Kereszt-batch dedupe (`tools/dataset_cross_dedupe.py` logikája,
    a TELJES 342 soros meglévő korpusz + ez az 50 sor, 0.9 küszöb)
**0 duplikátum** - sem a meglévő 0151-0500 korpusszal, sem a batch-en belül
(50 sor egymás közt) nem talált egyetlen 0.9 fölötti hasonlóságot sem, sem
id-, sem instruction+input-, sem output-alapon. A témák tudatos
elkerülése (lásd 5. pont, "korábbi témák elkerülése") ezt megerősítve
működött.

### 2.3 `tools/dataset_topic_report.py`

**A batch önmagában** (50 sor, 5×10-es tudatos témablokk-szerkezet miatt
természetesen magas arányú tageket mutat - ez SZÁNDÉKOS, nem hiba):

| Tag | Darab | Arány |
|---|---|---|
| iskola | 11 | 22.0% |
| ügyintézés | 10 | 20.0% |
| technika | 10 | 20.0% |
| munka | 6 | 12.0% |
| önfejlesztés | 4 | 8.0% |
| csillagászat | 3 | 6.0% |
| *(...további 8 tag, egyenként 1-2 sor)* | | |

**A teljes, egyesített korpuszon** (342 régi + 50 új = 392 sor) - ez a
lényegi mérőszám, nem az izolált batch:

| Tag | Régi arány (342) | Új arány (392) | Változás |
|---|---|---|---|
| AI | 12.9% (44 sor) | **11.2%** (44 sor) | **csökkent** - a batch 0 AI-sort adott hozzá, ez hígította az arányt |
| iskola | 11.7% (40 sor) | 13.0% (51 sor) | nőtt, de tartalmilag változatos (lásd audit 2.2 pont) |
| technika | 11.7% (40 sor) | 12.8% (50 sor) | nőtt, de tartalmilag változatos |
| ügyintézés | 1.8% (6 sor) | 4.1% (16 sor) | nőtt, de messze a 8%-os küszöb alatt |

**A batch pontosan a kívánt irányba mozdította el a korpuszt**: az
AI/Nexora arány csökkent, és egyetlen új sor sem kapott `AI` taget vagy
említette a "nexora" szót (`nexora` kulcsszó-találat: 0/50).

**Eszköz-korlát, amit ez a kör talált**: a `--keyword AI` opció
karakterlánc-alapú, NEM szóhatár-tudatos keresést végez - ezért 7 sornál
hamis pozitívot adott (a "iskolAI", "tanulmányAIdat", "visszaigazolÁst"...
helyesen: "iskol**ai**", "tanulmány**ai**dat", "visszaigazol**ás**t" - az "ai"
betűsorozat véletlenül előfordul bennük, NEM az "AI" szóról van szó).
Manuálisan ellenőrizve: **egyik találat sem valódi AI-említés** - a
mérvadó, megbízható jelző a **tag alapú számlálás** (0 `AI`-tagelt sor ebben
a batch-ben), nem ez a substring-keresés. Ez egy dokumentált korlátja a
`dataset_topic_report.py --keyword` funkciójának - jövőbeli javítás:
szóhatár-tudatos (`\b`) keresésre váltani rövid kulcsszavaknál.

### 2.4 `dataset_score.py`
Mind az 50 sor **100/100** pontot kapott, flag nélkül. Ez konzisztens az
audit korábbi megfigyelésével (a scorer nem bünteti a strukturálisan
hibátlan, de esetleg sekély tartalmat) - ezért ez a szám ÖNMAGÁBAN NEM
elég bizonyíték a tartalmi minőségre, lásd 2.6 pont (manuális átnézés).

### 2.5 Safety/firewall ellenőrzés
- **`src/guard.py` `looks_like_identity_bleed()`** mind az 50 output-ra
  lefuttatva (kategória: `simple_qa`, ami NEM identity kategória) - **0
  találat**. Egyik válasz sem tartalmazza véletlenül a Nexora/MF-AI-Zero
  identitás-mintázatot ("mf-ai-zero", "nulláról tanított", "saját,
  nulláról") - megerősíti, hogy a batch valóban AI/Nexora-mentes.
- **Kiegészítő kulcsszó-szűrés** (veszélyes/orvosi/jogi/pénzügyi-ígéret/
  személyesadat-minták): 3 nyers találat ("tűz", "gáz" szótöredékek), mind
  manuálisan ellenőrizve és **hamis pozitívnak** bizonyult:
  - `simple_qa_0533`, `simple_qa_0534`: "**tűz**z ki egy határidőt" /
    "kitűzése" - a "kitűz" (célt/határidőt kitűzni) ige, NEM tűzesettel
    kapcsolatos.
  - `simple_qa_0544`: "magma, **gáz**ok vagy hamu" - egy vulkanológiai
    ismeretterjesztő mondat része, nem veszélyes instrukció.
  - Orvosi, jogi, pénzügyi-ígéret és személyesadat-minta: **0 találat**
    mind az 50 sorban.

## 3. Manuális mintavételes tartalmi átnézés (10 sor, minden témablokkból 2)

| id | Instruction | Értékelés |
|---|---|---|
| simple_qa_0502 | Hogyan kérjek időpontot egy hivatalban? | Természetes, 2 mondatos, semleges gyakorlati tanács. Nincs ígéret, nincs veszély. OK. |
| simple_qa_0507 | Mit tegyek, ha elveszett a bankkártyám? | Biztonsági alaplépés (letiltás), NEM pénzügyi tanácsadás vagy ígéret. Természetes magyar. OK. |
| simple_qa_0513 | Hogyan kezeljem a vizsgadrukkot? | Enyhe, reális tanács, nincs orvosi/pszichológiai diagnózis vagy ígéret. OK. |
| simple_qa_0519 | Mit jelent a plágium? | Pontos, semleges fogalommagyarázat, nincs túlzás. OK. |
| simple_qa_0523 | Mit tegyek, ha megtelt a telefonom tárhelye? | Gyakorlati, veszélytelen tanács. OK. |
| simple_qa_0529 | Hogyan állítsam be, hogy ki láthatja a közösségi médiás bejegyzéseimet? | Adatvédelem-tudatosságot erősítő, de NEM ijesztgető vagy túlbiztosító tartalom. OK. |
| simple_qa_0533 | Mit tegyek, ha halogatok egy fontos feladatot? | Reális, nem-túlígérő önfejlesztési tanács. OK. |
| simple_qa_0538 | Hogyan alakítsak ki jó reggeli rutint? | Természetes, nem orvosi jellegű életmód-tanács. OK. |
| simple_qa_0542 | Miért van szökőév? | Pontos, egyszerű csillagászati magyarázat, nincs pontatlanság. OK. |
| simple_qa_0549 | Mi a különbség a monarchia és a köztársaság között? | Semleges, tényszerű definíció, nincs politikai állásfoglalás vagy elfogultság. OK. |

**Eredmény: 10/10 sor megfelelt** - természetes magyar nyelv, 1-2 mondatos
válasz, nincs veszélyes/orvosi/jogi/pénzügyi ígéret, nincs személyes adat,
nincs AI/Nexora/MF említés egyikben sem.

## 4. Fájlok

- Raw: `data/raw/claude_simple_qa_0501_0550_raw.jsonl` (50 sor)
- Clean: `data/clean/claude_simple_qa_0501_0550_clean.jsonl` (50 sor)
- Rejected: `data/rejected/claude_simple_qa_0501_0550_rejected.jsonl` (0 sor)

## 5. Betartott korlátok

- **Nincs AI/Nexora/MF téma**: 0 `AI`-tagelt sor, 0 "nexora" említés, 0
  identity-bleed találat.
- **Korábbi témák elkerülése**: a batch minden instrukcióját kézzel
  vetettem össze a 0151-0500 korpusz mind a 342 (javított) instrukciójával,
  MIELŐTT a tartalom elkészült volna - ezt a kereszt-batch dedupe (2.2 pont)
  0.9 küszöbön is megerősítette (0 találat). A `technika` blokk (0521-0530)
  külön is elkerülte a kifejezetten kizárt wifi/VPN/cookie/adathalászat
  sablonokat (screenshot, tárhely, Bluetooth-párosítás, alkalmazás vs.
  böngésző, stb. témák kerültek helyettük).
- **Nincs veszélyes tanács, orvosi/jogi/pénzügyi ígéret, személyes adat**:
  lásd 2.5 és 3. pont.
- **Természetes magyar, 1-2 mondat**: minden output erre lett tervezve, a
  scorer (`no_terminal_punctuation` flag hiánya) és a manuális mintavétel
  is megerősítette.

## 6. Amit ez a kör NEM tett

- **Nem indított tanítást** - a modell nem lett erre az adatra tanítva.
- **Nem generált mást, csak ezt az 50 sort.**
- **Nem módosított webapp/backend kódot.**
- **Nem commitolt, nem pusholt.**
- **Nem nyúlt a régi (0151-0500) clean fájlokhoz.**

---

## Végső összegzés

- Raw sorok száma: **50**
- Clean sorok száma: **50**
- Rejected sorok száma: **0**
- Kereszt-batch duplikátumok száma: **0**
- Átlag quality_score: **100.0**
- Topic report (röviden): a batch önmagában szándékosan témablokkolt (5×10),
  de a TELJES korpuszra vetítve **csökkentette** az AI/Nexora arányt
  (12.9% -> 11.2%), és 0 AI/Nexora-tagelt sort adott hozzá.
- 10 soros manuális mintavétel eredménye: **10/10 megfelelt**, nincs
  biztonsági/etikai/minőségi probléma.

**STÁTUSZ: STABIL.**

**Mehet-e utána egy 100 soros Claude-generált batch?**

**Igen, mehet - hasonló felügyelt módban.** Ez a próba pontosan igazolta,
amit a pipeline hardening kör feltételként megfogalmazott: a formalizált
kereszt-batch dedupe és a topic report ténylegesen működik egy új,
Claude-generált batch-nél is, és a batch tudatos téma-tervezéssel
(a tiltott témák előzetes kizárásával, a régi korpusz manuális
átvizsgálásával) nullára hozható a duplikáció és a témakör-torzítás
kockázata. **Egyetlen fenntartás továbbra is fennáll**: a scorer 100%-os
eredménye (2.4 pont) itt sem tekinthető önmagában elégségesnek - a manuális
mintavételes átnézés (jelenleg 10/50 = 20%-os lefedettség) maradjon
kötelező lépés a 100 soros próbánál is, ideális esetben hasonló arányban
vagy nagyobb mintán.

**FONTOS: ez a kör NEM indított tanítást, NEM módosított webapp/backend
kódot, és NEM commitolt/pusholt semmit - ez egy tesztadat, jóváhagyásra vár.**
