# Hetedik FELÜGYELT Claude-generált "magyarázós példa" batch - explanation 0601-0700

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
| Kereszt-batch **jelzett** (0.9 fölötti) egyezés (teljes 1699 soros korpuszon) | 7 |
| Ebből az ÚJ explanation batch-et érintő, **valódi** duplikátum | **2** |
| Ebből hamis pozitív (régi simple_qa jelzés ismétlődése) | 5 |
| **Végleges clean sorok** | **98** |
| **Rejected sorok** | **2** |
| Átlag quality_score | **100.0** |
| Flag-et kapott sor | 0 |
| Difficulty eloszlás (clean) | medium: 88, hard: 10 |

## 2. Ellenőrzési lépések (teljes pipeline)

### 2.1 Schema validate
Mind a 100 sor strukturálisan érvényes (`tools/dataset_validate.py`).

### 2.2 Kizárt témák explicit ellenőrzése
A kizárt kifejezések listáján (nexora, mf-ai, wifi, vpn, cookie,
adathalászat, tanítóadat, adatminőség, modelltesztelés, naplóírás,
üvegházhatás, bocsánat, ajándék) **0 találat**.

AI-tagelt sor: **0/100**. `technika`-tagelt sor: **0/100**.

### 2.3 Teljes korpuszos cross-dedupe (a TELJES 1599 soros meglévő korpusz +
    ez a 100 sor, 0.9 küszöb, összesen 1699 sor)

A dedupe **7 db 0.9 fölötti instruction-hasonlósági egyezést** jelzett,
`id_duplicates`: 0, `output_duplicates`: 0.

**Öt jelzés a korábban már dokumentált, megtartott simple_qa hamis
pozitívok pontos megismétlődése** (egyik sem érinti az explanation
kategóriát):

| kept | duplicate | similarity | Megjegyzés |
|---|---|---|---|
| simple_qa_0851 | simple_qa_0857 | 0.904 | Korábbról ismert hamis pozitív. |
| simple_qa_0851 | simple_qa_0859 | 0.919 | Korábbról ismert hamis pozitív. |
| simple_qa_0671 | simple_qa_0914 | 0.919 | Korábbról ismert hamis pozitív. |
| simple_qa_0734 | simple_qa_1081 | 0.918 | Korábbról ismert hamis pozitív. |
| simple_qa_0915 | simple_qa_0489 | 0.921 | Korábbról ismert hamis pozitív. |

**Két ÚJ, VALÓDI duplikátum is előkerült ebben a körben** - a matematika
témablokk (681-700) két sora véletlenül ugyanazt a korábbi
`explanation_0201_0300` batch-ben (2. csomag, 3. körben) már megírt
témát ismételte meg, majdnem szó szerint azonos instrukcióval:

| kept | duplicate | similarity | Megjegyzés |
|---|---|---|---|
| explanation_0244 | explanation_0681 | 0.901 | **VALÓDI duplikátum.** Mindkettő az átlag kiugró értékek általi torzítását magyarázza, gyakorlatilag azonos "fizetés/jövedelem" példával és medián-javaslattal. |
| explanation_0242 | explanation_0697 | 0.942 | **VALÓDI duplikátum.** Mindkettő az exponenciális növekedés intuíciós alábecslését magyarázza, azonos "lineáris gondolkodás vs. exponenciális gyorsulás" érveléssel. |

Mindkét esetnél manuálisan összevetve a teljes szöveget: a megfogalmazás
szóhasználata eltér, de a tartalmi mag, a példák és a következtetés
gyakorlatilag megegyezik - **valódi tartalmi átfedés**, nem a rövid-sablon
hamis pozitív mintázat esete.

**Döntés**: `explanation_0681` és `explanation_0697` **eltávolítva** a
clean-ből, átkerültek a `rejected` fájlba `reason:
"duplicate_cross_batch"` jelöléssel, a megfelelő `matched_id` és
`similarity` adatokkal. A korábbi, már commitolt sorok
(`explanation_0242`, `explanation_0244`) változatlanok maradtak.

**Ez már a második eset, hogy egy explanation-kategóriás sor ütközött
egy korábbi explanation batch-csel** (az első az `explanation_0501_0600`
batch-nél volt). Mindkét esetben a `matematika` témakör érintett - ez
arra utal, hogy ennél a viszonylag szűkebb, definiált fogalmi térnél
(alapfogalmak, mint átlag/medián, exponenciális növekedés) nagyobb az
esélye a véletlen témaismétlődésnek, mint a tágabb témaköröknél. Jövőbeli
batch-eknél érdemes lesz explicit ellenőrizni a korábbi `matematika`-
tagelt sorok listáját, mielőtt új matematikai alapfogalom-témát
választanánk.

### 2.4 `tools/dataset_topic_report.py`

**A teljes, egyesített korpuszon** (1000 simple_qa + 697 explanation clean
= 1697 sor, a 2 duplikátum kizárásával):

| Tag | 1599 sornál (előző kör) | **~1697 sornál (most)** |
|---|---|---|
| technika | 5.7% (91) | **5.4% (91)** - tovább csökken |
| fizika (bővült) | 4.2% (68) | 4.8% (82) |
| iskola | 4.4% (71) | **4.2% (71)** - tovább csökken |
| gazdaság | 4.0% (64) | 3.8% (64) |
| matematika (bővült) | - | 3.7% (63) |
| pszichológia (bővült) | - | 3.6% (62) |
| biológia | 3.7% (59) | **3.5% (59)** - tovább csökken (0 új sor) |
| filozófia (ÚJ) | - | ~1.2% (kb. 20) |
| fényképezés (ÚJ) | - | ~1.2% (kb. 20) |
| játék (ÚJ) | - | ~1.2% (kb. 20) |
| időmérés (ÚJ) | - | ~1.2% (kb. 20) |

**Túlreprezentált tagek: NINCS** (legmagasabb: technika 5.4%, jóval a
8%-os küszöb alatt).

Ez a batch 5 teljesen új témablokkot vezetett be (filozófia/logika
alapfogalmak, fényképezés/optika, társasjátékok/játékelmélet stratégiai
elvei, időmérés/naptárak, statisztika/valószínűségszámítás mindennapi
alkalmazásai) - tudatosan elkerülve a `technika`, `iskola` és `biológia`
tageket.

### 2.5 `dataset_score.py`
Mind a 100 sor **100/100** pontot kapott, flag nélkül (a duplikátumok
kiszűrése a dedupe lépésben történt, nem a score-nál).

### 2.6 Safety/firewall ellenőrzés
- **`src/guard.py` `looks_like_identity_bleed()`**: **0 találat**.
- **Kiegészítő kulcsszó-szűrés**: **4 nyers találat**, mindegyik
  "garantál" kulcsszóra, manuálisan ellenőrizve és **hamis pozitívnak**
  bizonyult:
  - `explanation_0603`: "nem garantáltan igaz következtetésre" - negált,
    logikai/induktív érvelés fogalmát írja le.
  - `explanation_0643`: "a másik malom garantáltan bezáródik" -
    determinisztikus társasjáték-szabály leírása, nem valós ígéret.
  - `explanation_0656`: "a legjobb kimenetelt garantálja" - a minimax
    algoritmus formális, matematikai garancia-tulajdonságát írja le
    (játékelméleti szakkifejezés), nem jogi/pénzügyi túlígéret.
  - `explanation_0687`: "nem garantálja... a következtetés helyességét" -
    negált, statisztikai módszertani figyelmeztetés.
- **Filozófia blokk (601-620) külön is átnézve**: minden sor semleges,
  ismeretterjesztő logikai/ismeretelméleti fogalommagyarázat, egyik sem
  foglal állást vitatott etikai kérdésben, és egyik sem érinti vallási
  témát (ahogy az AUTOPILOT instrukciók kérik, a filozófia bucket
  tudatosan logikai/episztemológiai fogalmakra korlátozódott, elkerülve
  a vallásfilozófiát).

## 3. Manuális mintavételes tartalmi átnézés (20 sor, minden témablokkból 4)

| id | Instruction | Értékelés |
|---|---|---|
| explanation_0602 | Miért fontos a logikai érvelésben a premisszák és a következtetés megkülönböztetése? | Pontos logikai alapfogalom. OK. |
| explanation_0609 | Hogyan hat a megerősítési torzítás a mindennapi gondolkodásunkra? | Semleges, ismeretterjesztő. OK. |
| explanation_0612 | Miért nehéz filozófiai szempontból bizonyítani, hogy a külvilág valóban létezik? | Elvontabb, tudományosan óvatos fogalom. OK. |
| explanation_0618 | Miért nehéz filozófiailag megválaszolni, hogy mi teszi ugyanazzá a személyt idővel? | Elvontabb, semleges filozófiai kérdés. OK. |
| explanation_0622 | Miért fontos a rekeszérték (blende) beállítása egy fotó élességi mélységében? | Pontos fotós-technikai magyarázat. OK. |
| explanation_0627 | Hogyan hat a lencse fókusztávolsága a látószögre és a perspektívára? | Pontos optikai magyarázat. OK. |
| explanation_0632 | Miért fontos a szenzorméret egy kamera fényérzékenysége és képminősége szempontjából? | Pontos, technikai. OK. |
| explanation_0637 | Hogyan hat a diffrakció jelensége a képminőségre nagyon szűk rekesznél? | Elvontabb, összetettebb optikai fogalom. OK. |
| explanation_0641 | Miért fontos a középső mezők kontrollja a sakk nyitó szakaszában? | Pontos, veszélytelen stratégiai elv. OK. |
| explanation_0648 | Hogyan hat a Nash-egyensúly fogalma két racionális szereplő stratégiai döntéshozatalára? | Elvontabb, játékelméleti fogalom. OK. |
| explanation_0655 | Miért fontos a zugzwang fogalma a sakk végjátékában? | Pontos sakkelméleti fogalom. OK. |
| explanation_0658 | Hogyan hat a pszichológiai nyomás egy versenyszerű játékhelyzetben a döntéshozatalra? | Semleges, nem klinikai magyarázat. OK. |
| explanation_0661 | Miért van szükség szökőévre a naptárunkban? | Pontos csillagászati/naptári magyarázat. OK. |
| explanation_0666 | Hogyan alakult ki a hetes beosztás a naptárban? | Pontos, semleges történelmi magyarázat. OK. |
| explanation_0673 | Miért van szükség szökőmásodpercekre a hivatalos időmérésben? | Elvontabb, összetettebb fogalom. OK. |
| explanation_0680 | Hogyan hat a bioritmus a napi teljesítményünkre? | Semleges élettani magyarázat, nem orvosi tanács. OK. |
| explanation_0683 | Miért nem jelenti egy ritka betegség pozitív szűrési eredménye automatikusan azt, hogy valaki biztosan beteg? | Semleges, statisztikai (Bayes-tétel) magyarázat, nem orvosi diagnózis. OK. |
| explanation_0689 | Miért fontos a kontrollcsoport használata egy tudományos kísérletben? | Pontos módszertani magyarázat. OK. |
| explanation_0694 | Hogyan hat a túlélési torzítás a sikerről alkotott képünkre? | Elvontabb, pontos statisztikai fogalom. OK. |
| explanation_0700 | Hogyan hat a nagy számok törvénye a hosszú távú statisztikai előrejelzések megbízhatóságára? | Pontos, összetettebb statisztikai fogalom. OK. |

**Eredmény: 20/20 sor megfelelt** (a mintavétel nem tartalmazta a
kizárt `explanation_0681` és `explanation_0697` sorokat).

## 4. Fájlok

- Raw: `data/raw/claude_explanation_0601_0700_raw.jsonl` (100 sor)
- Clean: `data/clean/claude_explanation_0601_0700_clean.jsonl` (98 sor)
- Rejected: `data/rejected/claude_explanation_0601_0700_rejected.jsonl` (2 sor)

## 5. Regressziós teszt
`tests/test_v1_7_4_dataset_foundation.py` - **minden teszt sikeres, STÁTUSZ:
STABIL**.

## 6. Amit ez a kör NEM tett

- **Nem indított tanítást.**
- **Nem módosított webapp/backend kódot.**
- **Nem nyúlt a régi clean fájlokhoz** (az `explanation_0242` és
  `explanation_0244` sorok a korábbi
  `claude_explanation_0201_0300_clean.jsonl` fájlban változatlanul
  megmaradtak - csak az ÚJ, ütköző sorok kerültek kizárásra).

---

## Végső összegzés

- Raw sorok száma: **100**
- Clean sorok száma: **98**
- Rejected sorok száma: **2** (`explanation_0681` és `explanation_0697`,
  valódi duplikátumok a korábbi `explanation_0244` és `explanation_0242`
  sorokkal szemben)
- Kereszt-batch duplikátumok száma: **2 valódi** (a fentiek) + 5 korábbi
  simple_qa hamis pozitív megismétlődése
- Átlag quality_score: **100.0**
- Topic report (röviden): batch önmagában 5 vadonatúj témakörre
  fókuszált (filozófia/logika alapfogalmak, fényképezés/optika,
  társasjátékok/játékelmélet stratégiai elvei, időmérés/naptárak,
  statisztika/valószínűségszámítás) - tudatosan elkerülve a `technika`,
  `iskola` és `biológia` tageket; a teljes ~1697 soros korpuszon **nincs
  túlreprezentált tag** (legmagasabb: technika 5.4%, tovább csökkenő
  trend).
- 20 soros manuális mintavétel eredménye: **20/20 megfelelt**.
- **Egyedi clean explanation sorok jelenleg összesen: 697 / 1000.**
- **Hiányzik még a 2. csomag céljához: 303 sor.**

**STÁTUSZ: STABIL** (a felfedezett 2 duplikátum a mandátumos pipeline
által pontosan a tervezett módon lett kiszűrve, mielőtt clean-be
került volna - ez a folyamat helyes működését igazolja. Tanulság a
következő körökre: a `matematika` alapfogalom-témáknál explicit
ellenőrizni kell a korábbi batch-ek listáját a véletlen témaismétlődés
elkerülése érdekében.)
