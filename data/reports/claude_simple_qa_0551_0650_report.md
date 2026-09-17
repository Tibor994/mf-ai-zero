# Második FELÜGYELT Claude-generált próba batch - simple_qa 0551-0650

- Forrás: **Claude-generált**, 100 db, kézzel megírt, majd a teljes meglévő
  pipeline-nal ellenőrzött sor. Ez az **1000 db egyszerű magyar kérdés-válasz
  célcsomag** (lásd `data/reports/dataset_roadmap_0501_5000.md`, 1. csomag)
  folytatása, a korábbi 50 soros próba (0501-0550) után a második lépés.
- `source` mező: `synthetic_claude`.
- **Ez továbbra is TESZT kör** - a modellt NEM tanítottuk erre az adatra,
  nem történt commit/push, webapp/backend kód nem változott.

## 1. Számok

| Mérőszám | Érték |
|---|---|
| Raw sorok | 100 |
| Validáláson elfogadva | 100 |
| Validáláson elutasítva | 0 |
| Kereszt-batch duplikátumként kiszűrve | 0 |
| **Végleges clean sorok** | **100** |
| **Rejected sorok** | **0** |
| Átlag quality_score | **100.0** |
| Flag-et kapott sor | 0 |

## 2. Ellenőrzési lépések (teljes pipeline)

### 2.1 `dataset_validate.py`
Mind a 100 sor strukturálisan érvényes: helyes JSON, minden kötelező mező
jelen van, nincs escape-hiba, garbled/repeated-char minta, angol keveredés,
overclaiming, sem a validátor beépített személyesadat- vagy
veszélyestartalom-mintája (0 találat mindenhol).

### 2.2 Kizárt témák explicit ellenőrzése
A user által kifejezetten kizárt kifejezések (`nexora`, `mf-ai`, `wifi`/
`wi-fi`, `vpn`, `cookie`, `adathalász`, `tanítóadat`, `adatminőség`,
`modelltesztelés`, `naplóírás`, `üvegházhatás`, `bocsánat`, `ajándék`)
egyikére sem volt találat a 100 sor instruction+output szövegében
**(0/13 kizárt kifejezés, 0 érintett sor)**.

### 2.3 Kereszt-batch dedupe (a TELJES 392 soros meglévő korpusz + ez a
    100 sor, 0.9 küszöb)
**0 duplikátum** a teljes 492 soros egyesített korpuszon - sem a régi
0151-0550 anyaggal, sem a batch-en belül (100 sor egymás közt) nem volt
0.9 fölötti egyezés egyetlen id-, instruction+input-, vagy output-alapú
összevetésben sem. (Ez a futtatás a nagyobb korpuszméret miatt kb. 2-3
percig futott, de eredménye egyértelmű.)

### 2.4 `tools/dataset_topic_report.py`

**A batch önmagában** (100 sor, 5×20-as tudatos témablokk-szerkezet miatt
magas arányú tageket mutat - ez SZÁNDÉKOS):

| Tag | Darab | Arány |
|---|---|---|
| iskola | 20 | 20.0% |
| technika | 20 | 20.0% |
| sport | 16 | 16.0% |
| lakás | 6 | 6.0% |
| közlekedés | 6 | 6.0% |
| időjárás | 5 | 5.0% |
| *(...további 9 tag, egyenként 1-4 sor)* | | |

**A teljes, egyesített korpuszon** (392 régi + 100 új = 492 sor):

| Tag | 342 sornál | 392 sornál (előző kör) | **492 sornál (most)** |
|---|---|---|---|
| AI | 12.9% (44) | 11.2% (44) | **8.9% (44)** - tovább csökkent, mert megint 0 új AI-sor érkezett |
| iskola | 11.7% (40) | 13.0% (51) | 14.4% (71) - nőtt, de tartalmilag ellenőrzötten változatos (lásd 2.6) |
| technika | 11.7% (40) | 12.8% (50) | 14.2% (70) - nőtt, tartalmilag ellenőrzötten változatos |
| sport | 2.9% (10) | 2.6% (10) | 5.3% (26) - nőtt, még a 8%-os küszöb alatt |

**Az AI/Nexora arány folyamatosan csökken** (12.9% -> 11.2% -> 8.9%), pontosan
ahogy a hardening-terv célozta - **0 új AI/Nexora-tagelt sor** ebben a
batch-ben is, `nexora` kulcsszó-találat: 0/100.

**Előretekintő megjegyzés**: az `iskola` és `technika` tag arányának
folyamatos növekedése (most már 71, illetve 70 sor) miatt a KÖVETKEZŐ
Claude-generált simple_qa batch-eknél érdemes tudatosan MÁS témákra
fókuszálni, hogy ez a két kategória ne váljon a maga módján
túlreprezentálttá, ahogy korábban az AI is az volt - ez nem jelenlegi hiba,
csak egy figyelendő trend.

### 2.5 `dataset_score.py`
Mind a 100 sor **100/100** pontot kapott, flag nélkül - konzisztens a
korábbi próbával és a korábbi audit megfigyelésével (a scorer nem méri a
tartalmi mélységet, csak mechanikus hibákat szűr - lásd 2.7 pont).

### 2.6 Topic report tartalmi ellenőrzése (iskola/technika/sport)
Mivel mindhárom blokk (iskola, technika, sport) a batch-en belül is és a
teljes korpuszban is a 8%-os küszöb fölött van, manuálisan átnéztem mind a
100 sor instrukcióját (nem csak a mintát) annak megerősítésére, hogy
egyik blokk sem ismétel korábbi (0151-0550) vagy saját-batch-en-belüli
témát közeli megfogalmazásban:
- **iskola (20 sor)**: kizárólag ÚJ fogalmak (prímszám, mértékegység-
  átváltás, átlag/medián, terület/kerület, melléknév/jelző, összetett
  mondat, pomodoro technika, kritikus gondolkodás, stb.) - egyik sem a
  korábbi 51 iskola-sor átfogalmazása.
- **technika (20 sor)**: kizárólag ÚJ, a kizárt wifi/VPN/cookie/adathalász
  témákat és a korábbi (saját + DeepSeek) 50 technika-sort is elkerülő
  fogalmak (HDMI/USB, HD/4K, QR-kód, privát böngészés, feloldókód,
  billentyűzetkiosztás, stb.).
- **sport (16 sor)**: kizárólag ÚJ szempontok (sportcipő-választás, kardio
  vs. erősítő edzés, jóga kezdése, edzőterem-választás, versenyszorongás,
  stb.) - egyik sem a korábbi 0181-0340 tartományban lévő mozgás/egészség
  sorok átfogalmazása.

A kereszt-batch dedupe (2.3 pont) 0 találata numerikusan is megerősíti ezt
a manuális ellenőrzést.

### 2.7 Safety/firewall ellenőrzés
- **`src/guard.py` `looks_like_identity_bleed()`** mind a 100 output-ra
  lefuttatva (kategória: `simple_qa`) - **0 találat**.
- **Kiegészítő kulcsszó-szűrés** (veszélyes/orvosi/jogi/pénzügyi-ígéret/
  személyesadat-minták, valamint egy telefonszám-szerű minta regex) -
  **0 találat mindenhol**, egyetlen kategóriában sem (ellentétben az első
  próbával, ahol 3 hamis pozitív is volt - ezúttal egyik keresett minta
  sem fordult elő még szövegtöredékként sem).
- **Orvosi diagnózis-mentesség külön ellenőrizve** (a user explicit kérése
  szerint az egészség/sport blokknál): az `egészséges kapcsolatot az
  étellel` (0625), `elalvási szokások` (0616) és hasonló sorok kizárólag
  ÁLTALÁNOS, nem-diagnosztikus tanácsot adnak - egyik sem állít fel
  tünetalapú diagnózist vagy ígér gyógyhatást.

## 3. Manuális mintavételes tartalmi átnézés (20 sor, minden témablokkból 4)

| id | Instruction | Értékelés |
|---|---|---|
| simple_qa_0552 | Mire figyeljek egy albérleti szerződésnél? | Természetes, gyakorlati, nincs jogi ígéret (nem mond "jogilag garantált"-at, csak figyelmeztet). OK. |
| simple_qa_0559 | Hogyan viselkedjek zsúfolt tömegközlekedésen? | Illemtani tanács, semleges. OK. |
| simple_qa_0566 | Hogyan készüljek fel egy közelgő viharra? | Gyakorlati, veszélytelen felkészülési tanács. OK. |
| simple_qa_0569 | Mit tegyek, ha elakadok a liftben? | Nyugodt, biztonságos reakciót ír le, nincs pánikkeltés. OK. |
| simple_qa_0573 | Mi a különbség az átlag és a medián között? | Pontos matematikai fogalommagyarázat. OK. |
| simple_qa_0579 | Hogyan írjak jó fogalmazást? | Egyszerű, hasznos szerkezeti tanács. OK. |
| simple_qa_0586 | Mi a pomodoro technika? | Pontos, semleges módszertan-leírás. OK. |
| simple_qa_0589 | Mi az a valószínűség? | Pontos matematikai fogalommagyarázat. OK. |
| simple_qa_0593 | Mit tegyek, ha nem indul el egy alkalmazás? | Egyszerű, veszélytelen hibaelhárítás. OK. |
| simple_qa_0599 | Mi a különbség a nyilvános és a privát böngészés között? | Semleges fogalommagyarázat, nem ijesztgető adatvédelmi téma. OK. |
| simple_qa_0604 | Mit tegyek, ha véletlenül töröltem egy fontos fájlt? | Gyakorlati, veszélytelen tanács. OK. |
| simple_qa_0608 | Mit tegyek, ha a telefonom túlmelegszik? | Gyakorlati tanács, a végén reálisan szervizhez irányít, nem ígér házi "javítást" veszélyes módon. OK. |
| simple_qa_0612 | Mi a különbség a kardio és az erősítő edzés között? | Semleges sportfogalom-magyarázat, nincs orvosi ígéret. OK. |
| simple_qa_0616 | Milyen szokások segítenek a jobb elalvásban lefekvés előtt? | Általános szokás-tanács, NEM diagnózis vagy gyógymód. OK. |
| simple_qa_0624 | Mit tegyek, ha izgulok egy sportversenyen? | Reális, nem túlígérő tanács. OK. |
| simple_qa_0625 | Hogyan alakítsak ki egészséges kapcsolatot az étellel? | Óvatosan, NEM diagnosztikus vagy ítélkező megfogalmazás, általános szemléleti tanács. OK. |
| simple_qa_0634 | Mi a különbség a baktérium és a vírus között? | Pontos, tudományosan helyes biológiai magyarázat. OK. |
| simple_qa_0639 | Mi az a hagyomány? | Semleges kulturális fogalommagyarázat. OK. |
| simple_qa_0643 | Mi a különbség az ókor és a középkor között? | Pontos, semleges történelmi magyarázat. OK. |
| simple_qa_0649 | Mi a szennyezés fogalma? | Pontos környezeti fogalommagyarázat, nem ijesztgető. OK. |

**Eredmény: 20/20 sor megfelelt** - természetes magyar nyelv, 1-2 mondatos
válasz, nincs veszélyes/orvosi diagnózis/jogi/pénzügyi ígéret, nincs
személyes adat, nincs AI/Nexora/MF említés, nincs kizárt téma.

## 4. Fájlok

- Raw: `data/raw/claude_simple_qa_0551_0650_raw.jsonl` (100 sor)
- Clean: `data/clean/claude_simple_qa_0551_0650_clean.jsonl` (100 sor)
- Rejected: `data/rejected/claude_simple_qa_0551_0650_rejected.jsonl` (0 sor)

## 5. Regressziós teszt
A meglévő `tests/test_v1_7_4_dataset_foundation.py` (validator/dedupe/score/
split/import) - **minden teszt sikeres, STÁTUSZ: STABIL** - az új fájlok
nem okoztak regressziót.

## 6. Amit ez a kör NEM tett

- **Nem indított tanítást.**
- **Nem generált mást, csak ezt a 100 sort.**
- **Nem módosított webapp/backend kódot.**
- **Nem commitolt, nem pusholt.**
- **Nem nyúlt a régi (0151-0550) clean fájlokhoz.**

---

## Végső összegzés

- Raw sorok száma: **100**
- Clean sorok száma: **100**
- Rejected sorok száma: **0**
- Kereszt-batch duplikátumok száma: **0** (teljes 492 soros korpuszon ellenőrizve)
- Átlag quality_score: **100.0**
- Topic report (röviden): batch önmagában szándékosan témablokkolt (5×20:
  iskola, technika, sport a legmagasabb arányú, mind manuálisan is
  ellenőrizve tartalmi ismétlés nélkül); a teljes korpuszra vetítve az
  **AI/Nexora arány tovább csökkent 11.2%-ról 8.9%-ra**, miközben 0 új
  AI/Nexora-tagelt sor került be. Előretekintő megjegyzés: iskola és
  technika tag-aránya nő, a következő batch-eknél érdemes más témákra
  fókuszálni.
- 20 soros manuális mintavétel eredménye: **20/20 megfelelt**, nincs
  biztonsági/etikai/minőségi probléma, nincs orvosi diagnózis.
- **Egyedi clean simple_qa sorok jelenleg összesen: 492**
  (342 DeepSeek 0151-0500 + 50 Claude 0501-0550 + 100 Claude 0551-0650).
- **Hiányzik még az 1000 db simple_qa célhoz: 508 sor.**

**STÁTUSZ: STABIL.**

**Mehetnek-e a következő, hasonló méretű (vagy nagyobb) Claude-generált
simple_qa batch-ek?**

**Igen, mehetnek, felügyelt módban, ugyanezzel a pipeline-nal.** Két
egymást követő próba (50, majd 100 sor) mindkétszer nulla duplikátumot és
nulla biztonsági/kizárt-téma találatot produkált, és az AI/Nexora arány a
tervezettnek megfelelően, folyamatosan csökken. Egyetlen új figyelendő
pont merült fel (lásd 2.4): az iskola és technika tag-arány növekedése -
ez még nem probléma, de érdemes a következő batch-eknél tudatosan más
témákra (pl. a roadmap 2-9. csomagjaira) helyezni a hangsúlyt, hogy ne ez
a két kategória váljon a korpusz új, aránytalanul domináns témájává.

**FONTOS: ez a kör NEM indított tanítást, NEM módosított webapp/backend
kódot, és NEM commitolt/pusholt semmit - ez egy tesztadat, jóváhagyásra vár.**
