# Első FELÜGYELT step_by_step batch - step_by_step 0001-0100

**ÚJ PROTOKOLL, első alkalmazása**: ez az első batch az új "ChatGPT raw
producer + Claude/Nextora validator" munkamódszerben. A `data/inbox/
chatgpt/chatgpt_step_by_step_0001_0100_raw.jsonl` fájlt **RAW CANDIDATE**
státuszban kezeltük, nem clean adatként, és a teljes kötelező pipeline-on
átfuttattuk.

## 0. A ChatGPT raw candidate fájl ellenőrzésének eredménye

A `data/inbox/chatgpt/chatgpt_step_by_step_0001_0100_raw.jsonl` fájl
**100%-ban elutasításra került schema validálás során**:

- **Valid sorok**: 0 / 100
- **Ok**: minden egyes sorból hiányzott a kötelező `quality_notes` és
  `source` mező (a projekt 9 mezős szabvány sémájához képest: `id,
  category, instruction, input, output, tags, difficulty, quality_notes,
  source`).
- **További strukturális eltérés**: az `input` mező objektum típusú volt
  (`{"Current": null}`) a projektben egységesen használt string típus
  (`""`) helyett.
- Ez **egy rendszerszintű, minden sort egyformán érintő hibaminta** volt
  (nem véletlenszerű, soronkénti probléma), ami arra utal, hogy a
  ChatGPT/Dispatch producer jelenlegi kimeneti sablonja nem illeszkedik a
  projekt JSONL sémájához.
- **Ellentmondás a beküldött állítással**: a beküldő üzenet azt állította,
  hogy "kötelező mezők megvannak: igen" - ez a validálás alapján **téves
  volt**. Ez konkrét, megerősítő példa arra, miért szükséges, hogy a
  ChatGPT/Dispatch raw kimenete SOHA ne kerüljön automatikusan clean-be,
  és miért kell minden állítást a tényleges pipeline-nal, nem a producer
  saját önellenőrzésével igazolni.
- **Egyik sor sem lett auto-javítva vagy "megmentve"** - a validator az
  `auto_fixable: False` jelzést adta a hiányzó mezőkre, és a Claude/
  Nextora validator szerep lényege éppen az, hogy nem old fel
  strukturális hibákat saját belátása szerint. A teljes 100 sor a
  `data/rejected/chatgpt_step_by_step_0001_0100_rejected.jsonl` fájlba
  került, `reason: "schema_invalid_missing_fields"` jelöléssel, a teljes
  eredeti sor megőrzésével (forrásmegőrzés céljából).
- **Ez a fájl NEM számít a step_by_step csomag clean vagy raw
  statisztikájába** - külön, `chatgpt_` prefix alatt van nyilvántartva,
  megkülönböztetve a `claude_` prefixű, ténylegesen validált batch-ektől.

## 1. A pótló Claude-generált batch

Mivel a ChatGPT raw candidate 0 clean sort eredményezett, a teljes
100 soros célt **Claude-generált tartalommal pótoltuk**, ugyanazon a
teljes, kötelező pipeline-on átfuttatva, mint minden korábbi batch.

- Forrás: **Claude-generált**, 100 db, kézzel megírt, majd a teljes
  meglévő pipeline-nal ellenőrzött sor.
- `category`: `step_by_step`, `source`: `synthetic_claude`.
- Ez az **első batch a 3. csomagban** (cél: 500 db "írd lépésekben"
  példa).
- **Ez továbbra is TESZT kör** - a modellt NEM tanítottuk erre az adatra,
  webapp/backend kód nem változott.

### 1.1 Számok

| Mérőszám | Érték |
|---|---|
| Raw sorok (Claude-generált) | 100 |
| Validáláson elfogadva | 100 |
| Validáláson elutasítva | 0 |
| Batchen belüli dedupe (id/instruction/output) | 0 találat |
| Kereszt-batch **jelzett** (0.9 fölötti) egyezés (teljes 2000 soros korpuszon) | 5 |
| Ebből az ÚJ step_by_step batch-et érintő | **0** |
| **Végleges clean sorok** | **100** |
| **Rejected sorok** (Claude batch-en belül) | **0** |
| Átlag quality_score | **100.0** |
| Flag-et kapott sor | 0 |
| Difficulty eloszlás | easy: 67, medium: 28, hard: 5 |
| Formátum-ellenőrzés (számozott lépések, 4-6 lépés, "lépés" szó az instrukcióban) | 100/100 megfelelt |

### 1.2 Ellenőrzési lépések (teljes pipeline)

#### Schema validate
Mind a 100 sor strukturálisan érvényes (`tools/dataset_validate.py`).

#### Magyar nyelvi/formátum ellenőrzés
Egyedi szkriptes ellenőrzés: minden output 4-6 számozott lépést
tartalmaz, "1."-gyel kezdődik, 100-700 karakter hosszú, minden
instrukció tartalmazza a "lépés" szót. **100/100 sor megfelelt, 0
eltérés.**

#### Batchen belüli dedupe
`tools/dataset_dedupe.find_duplicates()` a 100 soron belül: **0 id-,
0 instruction-, 0 output-duplikátum.**

#### Kizárt témák explicit ellenőrzése
**0 találat.** AI-tagelt sor: **0/100**.

#### Teljes korpuszos cross-dedupe (a TELJES 2000 soros meglévő korpusz +
    ez a 100 sor, 0.9 küszöb, összesen 2100 sor)

A dedupe **5 db 0.9 fölötti instruction-hasonlósági egyezést** jelzett,
mind az öt a **korábban már dokumentált, megtartott simple_qa hamis
pozitívok pontos megismétlődése**:

| kept | duplicate | similarity |
|---|---|---|
| simple_qa_0851 | simple_qa_0857 | 0.904 |
| simple_qa_0851 | simple_qa_0859 | 0.919 |
| simple_qa_0671 | simple_qa_0914 | 0.919 |
| simple_qa_0734 | simple_qa_1081 | 0.918 |
| simple_qa_0915 | simple_qa_0489 | 0.921 |

**Az ÚJ step_by_step_0001-0100 batch egyik sora sem szerepel egyik
jelzésben sem.**

#### `tools/dataset_topic_report.py`

**A teljes, egyesített korpuszon** (1000 simple_qa + 1000 explanation +
100 step_by_step = 2100 sor): legmagasabb tag fizika 5.4%. **Túl-
reprezentált tagek: NINCS.**

A batch önmagában (100 sor) 10 témablokkra oszlik (háztartás, konyha,
utazás, tanulás, kommunikáció/ügyintézés, kertészet, sport, munka,
gazdaság/költségvetés, etikett) - ezen belül a `tervezés` (21%) és
`kommunikáció` (19%) tag természetesen magasabb arányú, mert sok
step_by_step feladat lényegénél fogva tervezési vagy kommunikációs
jellegű. Ez az arány a teljes korpuszon belül elenyésző (2100 sorból
100 az egész batch).

#### `dataset_score.py`
Mind a 100 sor **100/100** pontot kapott, flag nélkül.

#### Safety/firewall ellenőrzés
- **`src/guard.py` `looks_like_identity_bleed()`**: **0 találat**.
- **Kiegészítő kulcsszó-szűrés**: **3 nyers találat**, mindhárom
  manuálisan ellenőrizve és **hamis pozitívnak** bizonyult:
  - "ajándék" (`step_by_step_0096`: "Vigyél egy kisebb ajándékot vagy
    figyelmességet" - vendégségi etikett, semleges).
  - "adag" (`step_by_step_0020`: "Oszd el kisebb, egy adagos
    tárolókba" - ételfagyasztás, konyhai adag, nem gyógyszeradag).
  - "kezelés" (`step_by_step_0057`: "...a probléma súlyosságához illő,
    kíméletes megoldást... a kezelés után" - növényi kártevő kezelése,
    nem orvosi).
- **Pénzügyi/gazdaság blokk (81-90) külön is átnézve**: minden sor
  általános, felelős háztartási költségvetés-tervezési gyakorlati
  tanács, egyik sem ad konkrét befektetési vagy pénzügyi terméktanácsot,
  és nem tartalmaz "garantált" vagy hasonló túlígérő megfogalmazást.

### 1.3 Manuális mintavételes tartalmi átnézés (20 sor, minden témablokkból 2)

| id | Instruction | Értékelés |
|---|---|---|
| step_by_step_0001 | Írd le lépésekben, hogyan takaríts ki hatékonyan egy szobát kevés idő alatt. | Gyakorlati, veszélytelen. OK. |
| step_by_step_0009 | Írd le lépésekben, hogyan lehet beosztani egy zsúfolt szombati napot. | Gyakorlati, veszélytelen. OK. |
| step_by_step_0012 | Írd lépésekben, hogyan tervezd meg egy hétre előre az étkezéseidet. | Gyakorlati, jó minőségű. OK. |
| step_by_step_0020 | Írd lépésekben, hogyan fagyaszd le megfelelően a maradék ételt. | Veszélytelen élelmiszer-tárolási tanács. OK. |
| step_by_step_0024 | Írd lépésekben, hogyan tervezd meg egy hosszabb autóutat. | Gyakorlati, biztonságtudatos. OK. |
| step_by_step_0030 | Írd lépésekben, hogyan tervezd meg egy gyalogtúra útvonalát biztonságosan. | Biztonságtudatos, veszélytelen. OK. |
| step_by_step_0036 | Írd lépésekben, hogyan oldj meg hatékonyan egy nehéz matematikai feladatot. | Semleges tanulási módszer. OK. |
| step_by_step_0040 | Írd lépésekben, hogyan tarts fenn motivációt egy hosszabb tanulási folyamat során. | Semleges, pozitív. OK. |
| step_by_step_0044 | Írd lépésekben, hogyan mondj le udvariasan egy meghívásról. | Semleges, gyakorlati. OK. |
| step_by_step_0048 | Írd lépésekben, hogyan tárgyalj a bérleti szerződésed feltételeiről. | Semleges, nem ad konkrét jogi tanácsot. OK. |
| step_by_step_0053 | Írd le lépésekben, hogyan vess el magokat egy kerti ágyásba. | Gyakorlati, veszélytelen. OK. |
| step_by_step_0057 | Írd le lépésekben, hogyan azonosítsd és kezeld a leggyakoribb növényi kártevőket. | Kertészeti, nem orvosi. OK. |
| step_by_step_0061 | Írd le lépésekben, hogyan kezdj el biztonságosan futni. | Biztonságtudatos. OK. |
| step_by_step_0067 | Írd le lépésekben, hogyan gyógyulj fel megfelelően egy enyhébb izomlázból. | Általános, nem orvosi diagnózis/kezelés. OK. |
| step_by_step_0075 | Írd le lépésekben, hogyan kezeld hatékonyan az egyszerre érkező sürgős feladatokat. | Gyakorlati, munkahelyi. OK. |
| step_by_step_0079 | Írd le lépésekben, hogyan csökkentsd a halogatás mértékét munka közben. | Semleges pszichológiai tanács. OK. |
| step_by_step_0083 | Írd lépésekben, hogyan kezdj el rendszeresen megtakarítani. | Általános, nem konkrét befektetési tanács. OK. |
| step_by_step_0087 | Írd le lépésekben, hogyan készülj fel pénzügyileg egy váratlan kiadásra. | Általános, felelős tanács. OK. |
| step_by_step_0091 | Írd le lépésekben, hogyan viselkedj udvariasan egy hivatalos vacsorán. | Semleges etikett. OK. |
| step_by_step_0099 | Írd le lépésekben, hogyan reagálj udvariasan, ha valaki elfelejti a nevedet. | Semleges, barátságos. OK. |

**Eredmény: 20/20 sor megfelelt.**

## 2. Fájlok

- ChatGPT raw candidate (megőrizve, forrásként): `data/inbox/chatgpt/chatgpt_step_by_step_0001_0100_raw.jsonl` (100 sor, NEM clean)
- ChatGPT candidate rejected: `data/rejected/chatgpt_step_by_step_0001_0100_rejected.jsonl` (100 sor, schema hiba miatt)
- Claude raw (pótlás): `data/raw/claude_step_by_step_0001_0100_raw.jsonl` (100 sor)
- Clean: `data/clean/claude_step_by_step_0001_0100_clean.jsonl` (100 sor)
- Rejected (Claude batch): `data/rejected/claude_step_by_step_0001_0100_rejected.jsonl` (0 sor)

## 3. Regressziós teszt
`tests/test_v1_7_4_dataset_foundation.py` - **minden teszt sikeres, STÁTUSZ:
STABIL**.

## 4. Amit ez a kör NEM tett

- **Nem indított tanítást.**
- **Nem módosított webapp/backend kódot.**
- **Nem nyúlt a régi clean fájlokhoz.**
- **Nem bízott meg automatikusan a ChatGPT raw candidate-ban** - minden
  sort a tényleges pipeline validált, a producer saját önellenőrzési
  állítása helyett.
- **Nem javította automatikusan a ChatGPT raw candidate strukturális
  hibáit** - a hiányzó mezőket nem pótolta, mert az `auto_fixable: False`
  jelzés és a validator/tűzfal szerep lényege ezt kizárja.

---

## Végső összegzés

- ChatGPT raw candidate: 100 sor beküldve, **0 clean** (100% schema
  elutasítás, rendszerszintű hibaminta: hiányzó `quality_notes`/`source`
  mező, rossz `input` típus).
- Claude pótló generálás: 100 raw → **100 clean, 0 rejected**.
- Kereszt-batch duplikátumok száma: **0** (mind az öt jelzés a korábbi
  simple_qa hamis pozitívok megismétlődése).
- Átlag quality_score: **100.0**.
- Safety: 0 identity-bleed, 3 hamis pozitív kulcsszótalálat, mind
  ellenőrizve.
- 20 soros manuális mintavétel eredménye: **20/20 megfelelt**.
- **Egyedi clean step_by_step sorok jelenleg összesen: 100 / 500.**
- **Hiányzik még a 3. csomag céljához: 400 sor.**

**STÁTUSZ: STABIL.**

**Visszajelzés a ChatGPT/Dispatch producer felé (a jövőbeli batch-ek
javításához)**: a raw candidate fájlnak tartalmaznia kell a
`quality_notes` (rövid, egy mondatos magyar leírás, mit tanít a sor) és
`source` (pl. `"chatgpt_dispatch"`) mezőket minden sorban, és az `input`
mezőnek üres string (`""`) típusúnak kell lennie objektum helyett, hogy
megfeleljen a projekt JSONL sémájának.
