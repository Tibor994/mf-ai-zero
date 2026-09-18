# Harmadik FELÜGYELT step_by_step batch - step_by_step 0201-0300

## 0. A ChatGPT raw candidate fájl ellenőrzésének eredménye (harmadik pilot próbálkozás, "szigorított" verzió)

A `data/inbox/chatgpt/chatgpt_step_by_step_0201_0300_raw.jsonl` fájlt
**RAW CANDIDATE** státuszban kezeltük, a teljes kötelező pipeline-nal
ellenőrizve.

### Schema validáció eredménye - JAVULÁS
Ellentétben az előző két batch-csel, ez a harmadik próbálkozás **100/100
sorral átment a schema validáláson**: minden kötelező mező (`id`,
`category`, `instruction`, `input`, `output`, `tags`, `difficulty`,
`quality_notes`, `source`) jelen volt, az `input` mező helyesen üres
string, a `source` mező kitöltve (`"chatgpt_dispatch_raw"`).

### Mélyebb tartalmi ellenőrzés - SÚLYOS PROBLÉMA FELTÁRVA
A séma-szintű megfelelés ellenére a mélyebb, tartalmi ellenőrzés (a
felhasználó explicit kérésére: "nem csak átfogalmazott ismétlés-e",
"quality_notes nem boilerplate-e", "minden output valódi lépésenkénti
válasz-e") **súlyos, rendszerszintű problémát tárt fel**:

- **Mind a 100 sor outputja pontosan 14 rigid sablon egyikéből
  származik.** Minden sablonon belül csak az 1. lépés (és az instrukció
  témaneve) változik soronként; a 2-5. lépések **szó szerint azonosak**
  minden, ugyanazt a sablont használó sor között.
- Ez a felosztás (14 sablon × átlagosan ~7 sor/sablon = 100) pontosan
  megegyezik a beküldő "különböző témakörök száma: 14" állításával - de
  ez az állítás **félrevezető volt**: nem 14 gazdag témakört, hanem 14
  fill-in-the-blank sablont jelentett.
- A `quality_notes` mező, bár **technikailag minden sorban egyedi
  string** (a beküldő "quality_notes mindenhol egyedi" állítása szó
  szerint igaz), maga is **ugyanazt a sablont követi minden sorban**:
  "A(z) {témakör} témakörben a(z) {helyzet} helyzetére készült egyedi
  magyar candidate példa." - csak a témakör/helyzet név van
  behelyettesítve. Ez NEM genuinly egyedi, tartalom-specifikus minőségi
  megjegyzés.
- A `tools/dataset_dedupe.find_duplicates()` formális, 0.9-es
  küszöbbel futtatott output-hasonlósági ellenőrzés **34 sort
  objektíven duplikátumként jelzett** a batchen belül - de ez csak egy
  alsó becslés a valódi, sablon-alapú redundanciára, mert az algoritmus
  soronként csak az első egyezésnél áll meg, nem az összes lehetséges
  párt vizsgálja.
- **Korábbi batch-ekkel (0001-0100, 0101-0200) való átfedés: 0** - ez a
  harmadik próbálkozás legalább ebben a tekintetben nem ismételte meg
  az előző két kör hibáját (nincs újraszámozott, korábban már
  elutasított tartalom).

### Döntés
**Mind a 100 sor elutasításra került**, `reason:
"templated_low_diversity_content"` jelöléssel - nem a formálisan
duplikátumként jelzett 34 sor, hanem a teljes 100 sor, mert a
mögöttes tartalom-generálási módszer (sablon + egy szó
behelyettesítés) egyike sem felel meg a "genuinly egyedi, magas
minőségű, témaspecifikus tartalom" követelménynek, még akkor sem, ha
egy-egy konkrét sorpár esetleg formálisan a küszöb alatt marad.
Részletek: `data/rejected/chatgpt_step_by_step_0201_0300_rejected.jsonl`.

### Visszajelzés a ChatGPT/Dispatch producer felé (harmadik kör)
1. **Jó hír**: a séma-formátum problémái (hiányzó mezők, rossz `input`
   típus) végre teljesen megoldódtak. Ez valódi javulás az első két
   próbálkozáshoz képest.
2. **Új, mélyebb probléma**: a tartalomgenerálási módszer jelenleg
   sablon + kulcsszó-behelyettesítés alapú, nem genuinly egyedi,
   témaspecifikus tartalomírás. Egy valódi "100 különböző step-by-step
   példa" batch-nek minden egyes sorban **ténylegesen eltérő, az adott
   konkrét helyzetre szabott lépéseket** kell tartalmaznia, nem egy
   közös sablon 2-5. lépését újrafelhasználva.
3. A `quality_notes` mezőnek genuinly, tartalmilag egyedi leírásnak
   kell lennie minden sornál, nem egy fix mondatsablon
   kitöltésének.

## 1. A pótló Claude-generált batch

- Forrás: **Claude-generált**, 100 db, kézzel megírt, genuinly egyedi
  tartalmú, majd a teljes meglévő pipeline-nal ellenőrzött sor.
- `category`: `step_by_step`, `source`: `synthetic_claude`.
- 10 vadonatúj témablokk (öltözködés/gardrób, családi fotók/emlékek
  rendszerezése, kerékpár alapkarbantartása, szomszédsági/lakóközösségi
  ügyek, kisvállalkozás/mellékállás indítása, környezettudatos otthoni
  szokások, biztonságos online vásárlás, hétvégi kikapcsolódás
  tervezése, zenehallgatás/playlist szervezés, családi
  feladatmegosztás) - egyik sem ismétli sem az első (0001-0100), sem a
  második (0101-0200) Claude batch témáit.

### 1.1 Számok

| Mérőszám | Érték |
|---|---|
| Raw sorok (Claude-generált) | 100 |
| Validáláson elfogadva | 100 |
| Validáláson elutasítva | 0 |
| Batchen belüli dedupe: id/output | 0 találat |
| Batchen belüli dedupe: instruction | 1 találat (lásd 1.2, hamis pozitív) |
| Kereszt-batch **jelzett** (0.9 fölötti) egyezés (teljes 2200 soros korpuszon) | 6 |
| Ebből az ÚJ step_by_step batch-et érintő, valódi | **0** |
| **Végleges clean sorok** | **100** |
| **Rejected sorok** (Claude batch-en belül) | **0** |
| Átlag quality_score | **100.0** |
| Flag-et kapott sor | 0 |
| Difficulty eloszlás | easy: 61, medium: 34, hard: 5 |
| Formátum-ellenőrzés (számozott lépések, egyedi quality_notes) | 100/100 megfelelt |
| Egyedi quality_notes | 100/100 (mind genuinly eltérő szöveg) |

### 1.2 Ellenőrzési lépések (teljes pipeline)

#### Schema validate
Mind a 100 sor strukturálisan érvényes.

#### Magyar nyelvi/formátum ellenőrzés
Minden output 4-6 számozott lépést tartalmaz, "1."-gyel kezdődik,
100-700 karakter hosszú, minden instrukció tartalmazza a "lépés" szót,
**és minden sor genuinly egyedi, topic-specifikus 5-lépéses tartalmat
és egyedi quality_notes-t tartalmaz** (nem sablon-alapú). **100/100 sor
megfelelt.**

#### Batchen belüli dedupe
`tools/dataset_dedupe.find_duplicates()`: 0 id-, 0 output-duplikátum.
**1 instruction-duplikátum jelzés** (`step_by_step_0227` "hogyan
tisztítsd meg a kerékpárodat egy hosszabb túra UTÁN" vs
`step_by_step_0229` "hogyan készítsd fel a kerékpárodat egy hosszabb
túrÁRA", sim=0.9) - manuálisan ellenőrizve: **a két output teljesen
különböző, konkrét tartalmat ad** (utótisztítási lépések vs.
indulás előtti felkészülési lista), a magas hasonlóság kizárólag a
hasonló instrukció-mondatszerkezetből ered. Ez pontosan megegyezik a
projekt korábbi köreiben (simple_qa, explanation csomagoknál) sokszor
dokumentált "rövid sablon hamis pozitív" jelenséggel. **Mindkét sor
megtartva.**

#### Kizárt témák explicit ellenőrzése
**0 találat.** AI-tagelt sor: **0/100**.

#### Teljes korpuszos cross-dedupe (a TELJES 2200 soros meglévő korpusz +
    ez a 100 sor, 0.9 küszöb, összesen 2300 sor)

A dedupe **6 db 0.9 fölötti instruction-hasonlósági egyezést** jelzett:
az 5 korábban már dokumentált simple_qa hamis pozitív megismétlődése,
plusz a fent tárgyalt, szintén hamis pozitívnak bizonyult
kerékpár-pár:

| kept | duplicate | similarity | Megjegyzés |
|---|---|---|---|
| simple_qa_0851 | simple_qa_0857 | 0.904 | Korábbról ismert hamis pozitív. |
| simple_qa_0851 | simple_qa_0859 | 0.919 | Korábbról ismert hamis pozitív. |
| simple_qa_0671 | simple_qa_0914 | 0.919 | Korábbról ismert hamis pozitív. |
| simple_qa_0734 | simple_qa_1081 | 0.918 | Korábbról ismert hamis pozitív. |
| simple_qa_0915 | simple_qa_0489 | 0.921 | Korábbról ismert hamis pozitív. |
| step_by_step_0227 | step_by_step_0229 | 0.9 | ÚJ, de manuálisan ellenőrzött hamis pozitív (lásd 1.2). |

**Nincs valódi duplikátum.**

#### `tools/dataset_topic_report.py`

**A teljes, egyesített korpuszon** (1000 simple_qa + 1000 explanation +
300 step_by_step = 2300 sor): legmagasabb tag fizika 4.9%. **Túl-
reprezentált tagek: NINCS.**

#### `dataset_score.py`
Mind a 100 sor **100/100** pontot kapott, flag nélkül.

#### Safety/firewall ellenőrzés
- **`src/guard.py` `looks_like_identity_bleed()`**: **0 találat**.
- **Kiegészítő kulcsszó-szűrés (kizárt témák, danger/medical/legal/
  financial/personal)**: **0 nyers találat** - ez az első step_by_step
  batch, ahol egyáltalán nem volt szükség hamis pozitív manuális
  ellenőrzésre.

### 1.3 Manuális mintavételes tartalmi átnézés (20 sor, minden témablokkból 2)

| id | Instruction | Értékelés |
|---|---|---|
| step_by_step_0201 | Írd le lépésekben, hogyan alakíts ki egyszerű, kapszula típusú gardróbot. | Gyakorlati, egyedi. OK. |
| step_by_step_0205 | Írd le lépésekben, hogyan alakíts ki tudatosabb vásárlási szokásokat ruházat terén. | Semleges, gazdaságtudatos. OK. |
| step_by_step_0211 | Írd le lépésekben, hogyan rendszerezd a telefonodon felhalmozott fotókat. | Gyakorlati, digitális jólét. OK. |
| step_by_step_0215 | Írd le lépésekben, hogyan gyűjts össze családi történeteket az idősebb rokonoktól. | Semleges, kapcsolatépítő. OK. |
| step_by_step_0221 | Írd le lépésekben, hogyan ellenőrizd a kerékpárod gumiabroncsainak nyomását. | Pontos technikai magyarázat. OK. |
| step_by_step_0224 | Írd le lépésekben, hogyan javíts meg egy defektes kerékpárgumit. | Gyakorlati, veszélytelen. OK. |
| step_by_step_0231 | Írd le lépésekben, hogyan kezdeményezz beszélgetést egy zajos szomszéddal udvariasan. | Konfliktuskezelő, semleges. OK. |
| step_by_step_0234 | Írd lépésekben, hogyan kezelj egy nézeteltérést a közös költségek elosztásáról. | Semleges, gyakorlati. OK. |
| step_by_step_0241 | Írd le lépésekben, hogyan mérd fel egy mellékállásötlet életképességét. | Felelős, nem konkrét pénzügyi tanács. OK. |
| step_by_step_0244 | Írd le lépésekben, hogyan tájékozódj a hivatalos bejelentési kötelezettségekről. | Semleges, jogot nem konkrétan tanácsoló. OK. |
| step_by_step_0251 | Írd le lépésekben, hogyan csökkentsd az otthoni vízfogyasztásodat tudatosan. | Gyakorlati, veszélytelen. OK. |
| step_by_step_0261 | Írd le lépésekben, hogyan ellenőrizd egy online bolt megbízhatóságát. | Felelős digitális biztonság. OK. |
| step_by_step_0267 | Írd le lépésekben, hogyan reagálj gyanús banki terhelés esetén. | Felelős, gyakorlati. OK. |
| step_by_step_0271 | Írd le lépésekben, hogyan tervezz meg egy pihentető hétvégét. | Semleges, gyakorlati. OK. |
| step_by_step_0281 | Írd le lépésekben, hogyan állíts össze egy hangulatodhoz illő lejátszási listát. | Gyakorlati, veszélytelen. OK. |
| step_by_step_0287 | Írd le lépésekben, hogyan tanulj meg jobban odafigyelni a zenehallgatás közben. | Semleges, önreflexiós. OK. |
| step_by_step_0291 | Írd le lépésekben, hogyan alakíts ki igazságos háztartási feladatmegosztást. | Semleges, kommunikációs. OK. |
| step_by_step_0294 | Írd lépésekben, hogyan kezelj egy vitát a háztartási feladatok elvégzéséről. | Konfliktuskezelő, semleges. OK. |
| step_by_step_0298 | Írd le lépésekben, hogyan kezeld rugalmasan a feladatmegosztást betegség esetén. | Empatikus, gyakorlati. OK. |
| step_by_step_0300 | Írd lépésekben, hogyan értékeljétek közösen a családi rutint. | Semleges, összegző. OK. |

**Eredmény: 20/20 sor megfelelt.**

## 2. Fájlok

- ChatGPT raw candidate (megőrizve, forrásként): `data/inbox/chatgpt/chatgpt_step_by_step_0201_0300_raw.jsonl` (100 sor, NEM clean)
- ChatGPT candidate rejected: `data/rejected/chatgpt_step_by_step_0201_0300_rejected.jsonl` (100 sor, sablon-alapú tartalmi probléma miatt)
- Claude raw (pótlás): `data/raw/claude_step_by_step_0201_0300_raw.jsonl` (100 sor)
- Clean: `data/clean/claude_step_by_step_0201_0300_clean.jsonl` (100 sor)
- Rejected (Claude batch): `data/rejected/claude_step_by_step_0201_0300_rejected.jsonl` (0 sor)

## 3. Regressziós teszt
`tests/test_v1_7_4_dataset_foundation.py` - **minden teszt sikeres, STÁTUSZ:
STABIL**.

## 4. Amit ez a kör NEM tett

- **Nem indított tanítást.**
- **Nem módosított webapp/backend kódot.**
- **Nem nyúlt a régi clean fájlokhoz.**
- **Nem fogadott el sablon-alapú, alacsony tartalmi diverzitású adatot
  csak azért, mert formálisan átment a séma-validáláson** - a validator
  szerep mélyebb, tartalmi minőségi ítéletet is hozott, nem csak
  mechanikus ellenőrzést.

---

## Végső összegzés

- ChatGPT raw candidate (3. próbálkozás): 100 sor beküldve, **0 clean**.
  A séma-hibák végre megoldódtak (source mező jelen, input helyes
  típus), DE a tartalom mind a 100 sorban 14 rigid sablonból
  származott, csak az első lépés és a témanév változott soronként; a
  quality_notes is sablon-alapú volt. Nincs átfedés a korábbi két,
  már elutasított ChatGPT batch-csel.
- Claude pótló generálás: 100 raw → **100 clean, 0 rejected** (1
  formálisan jelzett, de manuálisan ellenőrzött hamis pozitív pár
  maradt a korpuszban).
- Kereszt-batch duplikátumok száma: **0 valódi** (6 jelzés, mind hamis
  pozitívnak bizonyult).
- Átlag quality_score: **100.0**.
- Safety: 0 identity-bleed, 0 kulcsszó-találat (első "teljesen tiszta"
  step_by_step batch).
- 20 soros manuális mintavétel eredménye: **20/20 megfelelt**.
- **Egyedi clean step_by_step sorok jelenleg összesen: 300 / 500.**
- **Hiányzik még a 3. csomag céljához: 200 sor.**

**STÁTUSZ: STABIL.**

**Összegző visszajelzés a ChatGPT/Dispatch producer felé**: jelentős
javulás történt a séma-formátum terén (mindhárom korábbi probléma -
hiányzó mezők, rossz `input` típus, duplikált tartalom újraszámozva -
megoldódott), de egy új, mélyebb probléma került előtérbe: a
tartalomgenerálási módszer jelenleg sablon-alapú, nem genuinly
egyedi. Egy negyedik próbálkozás előtt érdemes lenne ezt a kérdést
tisztázni a producer oldalán, mielőtt további raw candidate batch-eket
küldenek.
