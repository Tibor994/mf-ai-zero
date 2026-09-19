# Negyedik FELÜGYELT step_by_step batch - step_by_step 0301-0400

## 0. A ChatGPT raw candidate fájl ellenőrzésének eredménye (negyedik próbálkozás)

A `data/inbox/chatgpt/chatgpt_step_by_step_0301_0400_raw.jsonl` fájlt
**RAW CANDIDATE** státuszban kezeltük. A beküldő önellenőrzési listáját
(minden pont "OK") itt sem fogadtuk el: minden állítást a tényleges
pipeline-nal ellenőriztünk.

### Eredmények

| Ellenőrzés | Eredmény |
|---|---|
| Schema validate (`dataset_validate.py`) | **0 / 100 valid** |
| Schema hiba oka | `personal_data_suspected` a `quality_notes` mezőben ("telefonszám-szerű minta"), `auto_fixable: False`, mind a 100 soron |
| Batchen belüli dedupe | id: 0, instruction: 0, **output: 18** (0.9 küszöb) |
| Átfedés a korábbi 3 elutasított ChatGPT batch-csel | **0** |
| Korpuszos kereszt-átfedés (clean adattal) | nem releváns, mert a sorok nem jutottak tovább a schema lépésen |
| Kizárt témák kulcsszó-találat | **3 sor**: `0346` (`wifi`), `0388` (`ajándék`), `0400` (`bocsánat`) |
| Identity bleed | 0 |
| Difficulty eloszlás | easy: 36, medium: 64, **hard: 0** |

### A schema hiba pontos természete (őszinte értékelés)
A `personal_data_suspected` jelzés **nem valódi személyes adat**: a
`quality_notes` sablonmondat minden sorban tartalmazza a `0301-0400`
tartományt (pl. "Egyedi 0301-0400 jelölt a(z) ... témában"), és ez a
minta illeszkedik a validator telefonszám-regexére. Ez tehát a producer
sablonjának mellékhatása, nem adatvédelmi incidens. A validator ezt
`auto_fixable: False` jelzéssel látta el, és **a producer fájlját nem
javítjuk** - a validator/tűzfal szerep lényege, hogy nem old fel
strukturális jelzéseket saját belátás szerint.

### A tartalmi probléma: továbbra is sablon, csak finomabb
A "különböző témakörök száma: 14" állítás itt is pontosan azt a
struktúrát takarja, ami a 3. próbálkozásnál: 14 sablon-csoport.
Lépésenként megszámolva, hány különböző szöveg fordul elő a 100 soron:

| Lépés | Különböző szövegek száma (100 sorból) |
|---|---|
| 1. lépés | 100 (az instrukció puszta újrafogalmazása: "Nevezd meg pontosan a helyzetet: ...") |
| 2. lépés | **14** |
| 3. lépés | **14** |
| 4. lépés | **1** ("Ellenőrizd közben, hogy a megoldás illik-e a körülményekhez.") |
| 5. lépés | **1** ("A végén rögzítsd az eredményt, és döntsd el, kell-e további teendő.") |

Vagyis a 100 output tényleges, témaspecifikus tartalma **legfeljebb 14
darab kétlépéses egység**; a 4. és 5. lépés **egyetlen, szó szerint
azonos mondat mind a 100 soron**. A `quality_notes` mező ismét
fill-in-the-blank sablon (csak a témacsoport neve és a helyzet van
behelyettesítve). Ez a 3. próbálkozás sablonos megközelítésének
finomított változata: a formális dedupe most már csak 18 sort jelez
(a 3. körben 34-et), tehát a mechanikus szűrő egyre kevésbé fogja meg,
miközben a tartalmi redundancia lényegében változatlan.

### Döntés
**Mind a 100 sor elutasítva**, `reason` lista:
`schema_invalid_personal_data_suspected_false_alarm`,
`templated_low_diversity_content`, illetve a 3 érintett soron
`excluded_topic_wifi` / `excluded_topic_ajándék` / `excluded_topic_bocsánat`.
Fájl: `data/rejected/chatgpt_step_by_step_0301_0400_rejected.jsonl`.
Egyik sor sem lett javítva, és egyik sem került clean-be.

### Visszajelzés a ChatGPT/Dispatch producer felé (negyedik kör)
1. **Ne tegyél sorszám-tartományt (pl. `0301-0400`) a `quality_notes`
   mezőbe** - a validator telefonszámnak olvassa.
2. **A 4. és 5. lépés nem lehet minden sorban ugyanaz a mondat.** A
   témaspecifikus lépések száma soronként 5, nem 2. Egy 100 soros
   batch-ben mind az 5 lépés szövege soronként eltérő kell legyen
   (a Claude-batch-ben ez 100/100/100/100/100).
3. A kizárt témák (`wifi`, `vpn`, `cookie`, `ajándék`, `bocsánat`, ...)
   a producer oldalán is szűrendők, mert a 3 találat mutatja: a lista
   nem érvényesül.
4. `hard` nehézségű sor egy sem volt - a difficulty eloszlás sem
   egyezik a projekt korábbi 60/30/10-es mintájával.

## 1. A pótló Claude-generált batch

- Forrás: **Claude-generált**, 100 db, kézzel megírt, egyedi, majd a
  teljes pipeline-nal ellenőrzött sor.
- `category`: `step_by_step`, `source`: `synthetic_claude`.
- 10 új témablokk (egyszerű otthoni javítások, autós alapfeladatok, házi
  tartósítás és sütés, írás és fogalmazás, telefonos fényképezés/videó,
  természetjárás, nyilvános beszéd, felkészülés szélsőséges időjárásra,
  közösségi rendezvény szervezése, idős családtag támogatása) - egyik
  sem ismétli az előző három Claude batch (0001-0300) témáit.

### 1.1 Számok

| Mérőszám | Érték |
|---|---|
| Raw sorok (Claude-generált) | 100 |
| Validáláson elfogadva | 100 |
| Batchen belüli dedupe (id / instruction / output) | 0 / 0 / 0 |
| Kereszt-batch jelzés (teljes 2300 soros korpusz + 100, összesen 2400) | 6, **mind korábbi** |
| Ebből az ÚJ batch-et érintő | **0** |
| **Végleges clean** | **100** |
| **Rejected** (Claude batch) | **0** |
| Átlag quality_score | **100.0** |
| Flag | 0 |
| Difficulty | easy: 63, medium: 29, hard: 8 |
| Különböző szöveg lépésenként (1..5. lépés, 100 sorból) | **100 / 100 / 100 / 100 / 100** |
| Egyedi quality_notes | 100 / 100 |

### 1.2 Ellenőrzési lépések

- **Schema**: 100/100.
- **Nyelvi/formátum**: minden output 4-6 számozott lépés, "1."-gyel
  kezdődik, 100-700 karakter, az instrukció tartalmazza a "lépés" szót:
  100/100.
- **Kereszt-dedupe**: a 6 jelzés az 5 korábbról ismert `simple_qa` hamis
  pozitív, plusz a már korábban commitolt és ellenőrzött
  `step_by_step_0227`/`0229` pár (0.9). Az új batch egyik sora sem
  szerepel.
- **Topic report** (teljes 2400 soros korpusz): legmagasabb tag `fizika`
  4.7%; túlreprezentált tag nincs.
- **Safety**: identity bleed 0; kizárt téma 0. Két kulcsszó-találat,
  mindkettő ellenőrzött hamis pozitív: `0307` ("...vegyszer **nélkül**"
  - biztonság-pozitív keretezés) és `0329` ("adagokban" - kenyér
  szeletelve fagyasztása).
- **Önkorrekció a felülvizsgálat során**: a manuális átnézés két saját
  sor szövegezési hibáját találta meg, ezeket még clean előtt javítottam:
  `step_by_step_0392` ("Vedd fel a szőnyegek csúszós alsó szegélyét" -
  félreérthető, helyette "Szedd fel a csúszós, laza szőnyegeket...") és
  `step_by_step_0380` (zivatar: a vitatott "guggolj le" tanács helyett
  "menj minél távolabb a magas tárgyaktól és a víztől, és ne feküdj le a
  földre"). A javítás után a két sor schema/score értéke változatlan, és
  a hasonlósága a korpusz többi sorához 0.70 (instruction) / 0.35
  (output) alatt van.
- **Biztonság-érzékeny sorok külön átnézve** (otthoni javítás, autó,
  időjárás, túra): a 0302 (falfúrás) a vezetékek ellenőrzését írja elő,
  a 0301 a víz elzárását, a 0312 (kerékcsere) a biztonságos megállást,
  a 0374 a nyílt láng kerülését. Egyik sor sem tartalmaz hálózati
  feszültséggel végzett munkát vagy károkozásra alkalmas útmutatást.

### 1.3 Manuális mintavétel (20 sor, minden témablokkból 2)

| id | Értékelés |
|---|---|
| step_by_step_0302 | Falfúrás: a vezetékek ellenőrzését az 1. lépés kéri. OK. |
| step_by_step_0308 | Csempecsere, védőszemüveg említve. OK. |
| step_by_step_0312 | Kerékcsere, a biztonságos megállás az 1. lépés. OK. |
| step_by_step_0314 | Téli felkészítés, gyakorlati. OK. |
| step_by_step_0324 | Kovászos uborka, konyhai hagyományos eljárás. OK. |
| step_by_step_0329 | Kenyértárolás, veszélytelen. OK. |
| step_by_step_0333 | Kérvény, semleges, nem ad jogi tanácsot. OK. |
| step_by_step_0338 | Jegyzőkönyv, tényszerű. OK. |
| step_by_step_0343 | Éjszakai telefonfotózás. OK. |
| step_by_step_0347 | Mozgó téma fotózása. OK. |
| step_by_step_0352 | Térkép és iránytű, pontos. OK. |
| step_by_step_0359 | Eltévedés: megállás, majd segélyszolgálat hívása. OK. |
| step_by_step_0362 | Lámpaláz, általános, nem klinikai. OK. |
| step_by_step_0366 | Online felszólalás. OK. |
| step_by_step_0372 | Áramkimaradás, elemlámpa gyertya helyett. OK. |
| step_by_step_0374 | Fagyvédelem, nyílt láng kerülése. OK. |
| step_by_step_0380 | Zivatar (javított változat). OK. |
| step_by_step_0385 | Rendezvény-költségvetés, általános. OK. |
| step_by_step_0392 | Elesés elleni otthon (javított változat). OK. |
| step_by_step_0399 | Ápolói túlterheltség, szakemberhez irányít. OK. |

**Eredmény: 20/20 megfelelt.**

## 2. Fájlok

- ChatGPT raw candidate (megőrizve, forrásként): `data/inbox/chatgpt/chatgpt_step_by_step_0301_0400_raw.jsonl` (NEM clean)
- ChatGPT rejected: `data/rejected/chatgpt_step_by_step_0301_0400_rejected.jsonl` (100 sor)
- Claude raw: `data/raw/claude_step_by_step_0301_0400_raw.jsonl` (100 sor)
- Clean: `data/clean/claude_step_by_step_0301_0400_clean.jsonl` (100 sor)
- Rejected (Claude): `data/rejected/claude_step_by_step_0301_0400_rejected.jsonl` (0 sor)

## 3. Regressziós teszt
`tests/test_v1_7_4_dataset_foundation.py` - minden teszt sikeres, STÁTUSZ: STABIL.

## 4. Amit ez a kör NEM tett
- Nem indított tanítást, nem módosított webapp/backend kódot, nem törölt semmit.
- Nem javította a ChatGPT raw fájlt, és nem fogadott el belőle egyetlen sort sem.

---

## Végső összegzés

- ChatGPT raw: 100 beküldve, **0 clean**, **100 rejected**.
- Claude-pótlás szükséges volt: **igen**, 100 sor, 100 clean / 0 rejected.
- Összes eddigi clean step_by_step: **400 / 500**; hiányzik: **100**.

**STÁTUSZ: STABIL.**
