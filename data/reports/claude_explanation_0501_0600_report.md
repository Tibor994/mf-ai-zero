# Hatodik FELÜGYELT Claude-generált "magyarázós példa" batch - explanation 0501-0600

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
| Kereszt-batch **jelzett** (0.9 fölötti) egyezés (teljes 1600 soros korpuszon) | 6 |
| Ebből az ÚJ explanation batch-et érintő, **valódi** duplikátum | **1** |
| Ebből hamis pozitív (régi simple_qa jelzés ismétlődése) | 5 |
| **Végleges clean sorok** | **99** |
| **Rejected sorok** | **1** |
| Átlag quality_score | **100.0** |
| Flag-et kapott sor | 0 |
| Difficulty eloszlás (clean) | medium: 89, hard: 10 |

## 2. Ellenőrzési lépések (teljes pipeline)

### 2.1 Schema validate
Mind a 100 sor strukturálisan érvényes (`tools/dataset_validate.py`).

### 2.2 Kizárt témák explicit ellenőrzése
A kizárt kifejezések listáján (nexora, mf-ai, wifi, vpn, cookie,
adathalászat, tanítóadat, adatminőség, modelltesztelés, naplóírás,
üvegházhatás, bocsánat, ajándék) **0 találat**.

AI-tagelt sor: **0/100**. `technika`-tagelt sor: **0/100**.

### 2.3 Teljes korpuszos cross-dedupe (a TELJES 1500 soros meglévő korpusz +
    ez a 100 sor, 0.9 küszöb, összesen 1600 sor)

A dedupe **6 db 0.9 fölötti instruction-hasonlósági egyezést** jelzett,
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

**Egy ÚJ, VALÓDI duplikátum is előkerült ebben a körben** - ez az első
olyan eset, ahol egy explanation-kategóriás sor ténylegesen ütközött egy
korábbi explanation batch-csel:

| kept | duplicate | similarity | Megjegyzés |
|---|---|---|---|
| explanation_0227 | explanation_0531 | **1.0** | **VALÓDI duplikátum.** Mindkét sor instruction szövege szó szerint azonos: "Hogyan alakulnak ki a homokdűnék a sivatagban?" (`explanation_0227`, batch 3, `földrajz` tag, 2026-09-korábban commitolva a `e925435` commitban) vs `explanation_0531` (ez a batch, `geológia` tag). A két output szövege eltérő megfogalmazású, de tartalmilag ugyanazt a jelenséget írja le ugyanarra a kérdésre - manuálisan ellenőrizve, **valódi tartalmi átfedés**, nem a rövid-sablon hamis pozitív mintázat esete (ott a hasonlóság sosem érte el az 1.0-t). |

**Döntés**: `explanation_0531` **eltávolítva** a clean-ből, átkerült a
`rejected` fájlba `reason: "duplicate_cross_batch"`, `matched_id:
"explanation_0227"`, `similarity: 1.0` adatokkal. A `explanation_0227`
(korábbi, már commitolt sor) változatlan marad.

**Ez az első genuine explanation-kategóriás duplikátum a projekt
történetében** - a korábbi 3 explanation batch (0001-0300, majd 0301-0500)
egyike sem ütközött se egymással, se a simple_qa korpusszal.

### 2.4 `tools/dataset_topic_report.py`

**A teljes, egyesített korpuszon** (1000 simple_qa + 599 explanation clean
= 1599 sor, a duplikátum kizárásával):

| Tag | 1500 sornál (előző kör) | **~1599 sornál (most)** |
|---|---|---|
| technika | 6.1% (91) | **5.7% (91)** - tovább csökken |
| iskola | 4.7% (71) | **4.4% (71)** - tovább csökken |
| biológia | 3.9% (59) | **3.7% (59)** - tovább csökken (0 új sor) |
| fizika (bővült) | 2.7% (40) | 4.2% (68) |
| gazdaság (bővült) | 2.9% (44) | 4.0% (64) |
| meteorológia (ÚJ) | - | ~1.3% (kb. 20) |
| geológia (ÚJ) | - | ~1.2% (kb. 19, a duplikátum nélkül) |
| művészet (bővült) | - | ~2.9% (47) |

**Túlreprezentált tagek: NINCS** (legmagasabb: technika 5.7%, jóval a
8%-os küszöb alatt).

Ez a batch 5 teljesen új témablokkot vezetett be (meteorológia,
geológia/földtudomány, festészet/vizuális művészet technikák,
pénz/gazdaságtörténet, mindennapi fizika jelenségek) - tudatosan
elkerülve a `technika`, `iskola` és `biológia` tageket.

### 2.5 `dataset_score.py`
Mind a 100 sor **100/100** pontot kapott, flag nélkül (a duplikátum
kiszűrése a dedupe lépésben történt, nem a score-nál).

### 2.6 Safety/firewall ellenőrzés
- **`src/guard.py` `looks_like_identity_bleed()`**: **0 találat**.
- **Kiegészítő kulcsszó-szűrés**: **2 nyers találat**, mindkettő
  manuálisan ellenőrizve és **hamis pozitívnak** bizonyult:
  - "lúg" (`explanation_0540`: "Egyes kőzetek, mint a mészkő,
    **lúgosabb** talajt eredményeznek" - talajkémiai pH-fogalom, nem
    veszélyes vegyszer).
  - "kezelés" (`explanation_0552`: "...a fényforrás következetes
    **kezelése** az egész kompozícióban" - művészeti/technikai
    kezelés, nem orvosi).
- **Gazdaság blokk (561-580) külön is átnézve**: minden sor semleges,
  ismeretterjesztő gazdaságtani fogalommagyarázat, egyik sem ad
  konkrét befektetési vagy pénzügyi tanácsot az olvasó saját
  helyzetére (pl. `explanation_0576` a diverzifikációt kifejezetten
  "nem befektetési tanácsként" jelöli).

## 3. Manuális mintavételes tartalmi átnézés (20 sor, minden témablokkból 4)

| id | Instruction | Értékelés |
|---|---|---|
| explanation_0502 | Miért látunk szivárványt eső után napsütésben? | Pontos fényszóródási magyarázat. OK. |
| explanation_0507 | Hogyan alakul ki egy hurrikán vagy trópusi ciklon? | Pontos meteorológiai mechanizmus. OK. |
| explanation_0512 | Miért nehéz pontosan előre jelezni egy adott hely csapadékmennyiségét? | Tudományosan óvatos, elvontabb fogalom. OK. |
| explanation_0517 | Hogyan befolyásolja a városi környezet a helyi hőmérsékletet? | Pontos, összetettebb fogalom. OK. |
| explanation_0522 | Miért törnek ki a vulkánok? | Pontos geológiai magyarázat. OK. |
| explanation_0528 | Miért mozognak a kontinensek (lemeztektonika)? | Pontos, összetettebb geológiai fogalom. OK. |
| explanation_0533 | Hogyan lehet a kőzetrétegek vizsgálatából következtetni a Föld múltbeli történetére? | Elvontabb, tudományos fogalom. OK. |
| explanation_0536 | Miért van annyi kőolaj és földgáz bizonyos földtani rétegekben? | Semleges, tudományos magyarázat. OK. |
| explanation_0541 | Hogyan hoz létre mélységérzetet egy festő egy sík vásznon (perspektíva)? | Pontos képzőművészeti technika. OK. |
| explanation_0550 | Miért hat ránk vizuálisan kellemesnek az aranymetszés aránya egy kompozícióban? | Tudományosan óvatos megfogalmazás. OK. |
| explanation_0559 | Hogyan alakult ki az absztrakt művészet? | Semleges művészettörténeti magyarázat. OK. |
| explanation_0564 | Miért csökken egy valuta vásárlóereje idővel (infláció)? | Pontos, elvontabb gazdaságtani fogalom. OK. |
| explanation_0570 | Miért fontos a megtakarítás és a befektetés közötti különbség megértése? | Semleges, nem konkrét tanácsként megfogalmazva. OK. |
| explanation_0576 | Miért fontos a diverzifikáció egy befektetési portfólióban? | Explicit "nem tanácsként" jelölve. OK. |
| explanation_0578 | Miért fontos a bizalom szerepe egy modern pénzügyi rendszerben? | Semleges, ismeretterjesztő. OK. |
| explanation_0581 | Miért csúszik a jég, míg más szilárd felületek nem? | Pontos fizikai magyarázat. OK. |
| explanation_0585 | Miért nem esünk le a Föld túloldalán élő emberekre? | Elvontabb, jól magyarázott fogalom. OK. |
| explanation_0593 | Miért nehéz gyorsan megállítani egy nagy sebességgel mozgó, nehéz tárgyat? | Pontos fizikai magyarázat. OK. |
| explanation_0597 | Miért nem lehet egy tárgyat a fénysebességnél gyorsabbra gyorsítani? | Elvontabb, tudományosan pontos fogalom. OK. |
| explanation_0600 | Hogyan érzékeljük a hőmérsékletet, ha az valójában a molekulák mozgási energiáját méri? | Pontos, összetettebb élettani-fizikai magyarázat. OK. |

**Eredmény: 20/20 sor megfelelt** (a mintavétel nem tartalmazta a
kizárt `explanation_0531` sort).

## 4. Fájlok

- Raw: `data/raw/claude_explanation_0501_0600_raw.jsonl` (100 sor)
- Clean: `data/clean/claude_explanation_0501_0600_clean.jsonl` (99 sor)
- Rejected: `data/rejected/claude_explanation_0501_0600_rejected.jsonl` (1 sor)

## 5. Regressziós teszt
`tests/test_v1_7_4_dataset_foundation.py` - **minden teszt sikeres, STÁTUSZ:
STABIL**.

## 6. Amit ez a kör NEM tett

- **Nem indított tanítást.**
- **Nem módosított webapp/backend kódot.**
- **Nem nyúlt a régi clean fájlokhoz** (az `explanation_0227` sor a
  korábbi `claude_explanation_0201_0300_clean.jsonl` fájlban
  változatlanul megmaradt - csak az ÚJ, ütköző sor került kizárásra).

---

## Végső összegzés

- Raw sorok száma: **100**
- Clean sorok száma: **99**
- Rejected sorok száma: **1** (`explanation_0531`, valódi duplikátum az
  `explanation_0227` sorral szemben, similarity 1.0)
- Kereszt-batch duplikátumok száma: **1 valódi** (a fenti) + 5 korábbi
  simple_qa hamis pozitív megismétlődése
- Átlag quality_score: **100.0**
- Topic report (röviden): batch önmagában 5 vadonatúj témakörre
  fókuszált (meteorológia, geológia/földtudomány, festészet/vizuális
  művészet technikák, pénz/gazdaságtörténet, mindennapi fizika
  jelenségek) - tudatosan elkerülve a `technika`, `iskola` és
  `biológia` tageket; a teljes ~1599 soros korpuszon **nincs
  túlreprezentált tag** (legmagasabb: technika 5.7%, tovább csökkenő
  trend).
- 20 soros manuális mintavétel eredménye: **20/20 megfelelt**.
- **Egyedi clean explanation sorok jelenleg összesen: 599 / 1000.**
- **Hiányzik még a 2. csomag céljához: 401 sor.**

**STÁTUSZ: STABIL** (a felfedezett duplikátum a mandátumos pipeline
által pontosan a tervezett módon lett kiszűrve, mielőtt clean-be
került volna - ez a folyamat helyes működését igazolja, nem egy
probléma jele).
