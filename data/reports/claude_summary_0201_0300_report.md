# Harmadik FELÜGYELT summary batch - summary 0201-0300

A 4. csomag (Összegzés példa, cél: 500 clean sor) **harmadik 100 sora**. Közvetlenül Claude-generált,
kitalált, általános magyar tartalom (nincs valós személy/magánadat, webes forrás, szerzői jogvédett szöveg,
MF-AI-projekttény, veszélyes tanács vagy biztos orvosi/jogi/pénzügyi állítás). Az ügyintézési és cikk-jellegű
szövegek "általában", "tájékoztató szerint", "a szervezők szerint" fenntartással szerepelnek, és az output
megtartja ezeket.

## 0. A 2. batch tapasztalatából adódó követelmények és teljesülésük

| Követelmény | Teljesülés |
|---|---|
| Nagyobb manuális mintavétel (30-40 sor) | **40 sor** (mind a 10 típusból 4: 2 egy- és 2 kétmondatos), soronként input és output egymás mellett elolvasva (5. fejezet) |
| Erősebb hűség-ellenőrzés | új automatikus ellenőrzés a szótő-összevetés mellé: hedge- és hivatkozás-megőrzés, tagadás, ellentétpár-felcserélés, idő- és számnév-eltérés, számmegőrzés (3. fejezet); minden jelzett sort kézzel átnéztem |
| Változatosabb, kézzel írt instruction, nem mondatváz-szagú | mind a 100 kézzel írt (nincs generátor); 100/100 egyedi, 56 különböző kétszavas nyitás, 1 sor kezdődik "Foglald össze"-val, 45% kérdő, 55% felszólító, 54% nevezi meg a mondatszámot |
| Vegyesen 1 és 2 mondatos output | **50 / 50**, minden blokkban pontosan 5 kétmondatos |
| A 2 mondatos output is tömör | kétmondatos: max. 41 szó, átlagos output/input arány 0.63, max. 0.79 |
| Az output ne legyen hosszabb az inputnál | 0 sor, ahol output >= input; legmagasabb arány 0.84 (egyetlen sor, a `0215`, rövid input miatt) |
| Ne adjon hozzá új tényt, ne torzítsa a jelentést | nincs új szám/név/időszó; 5 hedge-vesztés és 3 további torzítás javítva clean előtt (4. fejezet) |
| `quality_notes` egyedi és konkrét | 100 / 100 egyedi, egyik sem ismétlődő nyitású |
| Az `összefoglalás` tag aránya nőni fog: csak dokumentálni | 300 / 2800 = **10.7%** - ezt a csomagot jelölő, kategória-jellegű tagként dokumentálom, **nem** kezelem témaszaturációként; semmit nem módosítottam miatta |

## 1. Felépítés

10 tartalmi típus x 10 sor, az 1-2. batch témáitól eltérő új témákkal:

| ID tartomány | Típus | Címke | Kétmondatos sor |
|---|---|---|---|
| 0201-0210 | hétköznapi történet | `hétköznapi történet` | 5 |
| 0211-0220 | tanulási szöveg | `tanulási szöveg` | 5 |
| 0221-0230 | projektjegyzet | `projektjegyzet` | 5 |
| 0231-0240 | ügyintézés | `ügyintézés` | 5 |
| 0241-0250 | technikai magyarázat | `technikai magyarázat` | 5 |
| 0251-0260 | rövid cikk (kitalált helyi hír) | `rövid cikk` | 5 |
| 0261-0270 | beszélgetésrészlet (A/B vagy szerepjelölés, név nélkül) | `beszélgetés` | 5 |
| 0271-0280 | lista összefoglalása | `lista` | 5 |
| 0281-0290 | hosszabb magyarázat rövidítése | `hosszabb magyarázat` | 5 |
| 0291-0300 | döntési helyzet | `döntési helyzet` | 5 |

`tags` = `["magyar", "összefoglalás", <tartalmi típus>, <téma>]`. `difficulty` az input szószáma szerint
(leghosszabb 10 = hard, következő 30 = medium, a többi easy).

## 2. Számok

| Mérőszám | Érték |
|---|---|
| Raw sorok | 100 |
| Schema validáció (`dataset_validate.py`, raw és clean is) | 100 / 100 valid |
| Batchen belüli dedupe (id / instruction+input / output, 0.9) | 0 / 0 / 0 |
| Kereszt-dedupe a 2700 meglévő clean sor ellen (id / instruction / output, >= 0.9, minden találat) | 0 / 0 / 0 |
| **Végleges clean** | **100** |
| **Rejected** | **0** |
| Átlag quality_score | **100.0 / 100** |
| Difficulty | easy 60, medium 30, hard 10 |
| Egyedi instruction / input / output / quality_notes | 100 / 100 / 100 / 100 |
| Input szószám (min / medián / max) | 27 / 47 / 64 |
| Output szószám (min / medián / max) | 13 / 27 / 41 |
| Egymondatos outputok: sor / max. szó / output-input arány (átl., max) | 50 / 36 / 0.61, 0.84 |
| Kétmondatos outputok: sor / max. szó / output-input arány (átl., max) | 50 / 41 / 0.63, 0.79 |
| Szó szerinti másolás (6 szavas egyezés az inputtal, max) | 0.40 (`0228`; nincs 0.5 fölötti) |
| Instruction-mondatszám ellentmondás az outputtal | 0 |
| Identity bleed / saját projekt említés / URL, e-mail | 0 / 0 / 0 |
| Számjegy a szövegekben | 0 (a számok betűvel) |
| Topic report (2800 soros korpusz) | `összefoglalás` 10.7% (300 sor, várható, dokumentált), majd `fizika` 4.2%, `gazdaság` 3.9%; más túlreprezentált téma-tag nincs |
| Teljes clean korpusz | 2800 sor, 2800 egyedi id (1000 simple_qa, 1000 explanation, 500 step_by_step, 300 summary) |

## 3. Ellenőrzési lépések (a kért pipeline szerint)

1. **Generálás**: 100 sor 5 részben (20-20), külön szkripttel; az instructionök külön, kézzel írt készletből.
2. **Schema**: `dataset_validate.py` 100/100; saját mezőellenőrzés (9 kötelező mező, `category`, `source`,
   `difficulty`, nem üres `input`/`output`, `tags` fejléc, nincs számtartomány a `quality_notes`-ban).
3. **Summary forma és magyar nyelv**: az output nem üres, ponttal végződik, 1-2 mondatos; ékezetes karakterek,
   angol szavak, kódolási hiba, egyenes idézőjel, dupla szóköz, névelő-hiba, szóismétlés. A 7 jelzés mind az
   *inputokban* van (*az megoldhatja*, *az hangot*, *az volt*, *Az nekem*, *Az nem*, *az gyanús*, és az *Ennek az az
   oka* szerkezet), helyes magyar (mutató névmás).
4. **Input-output hűség (erősített)**: az alábbi automatikus ellenőrzések, mind a 100 soron; a jelzett sorokat
   kézzel átnéztem. A találatok a szükséges kézi átnézéshez adnak támpontot, nem automatikus elutasítást:
   - **Hedge-megőrzés** (*általában, jellemzően, gyakran, sokan/sokak, egyes; körülbelül, nagyjából, akár, legalább*):
     jelzett 8 sor; **2 valódi vesztés** (`0213` "általában", `0216` "gyakran") - javítva; a többi egyenértékű
     megfogalmazás (`0207` sokan -> sok, `0255` sokak -> a lakók egy része, `0256` egy része -> egyes) vagy
     mellékes, az outputban nem állított tény kihagyása (`0287`, `0289`, `0299`).
   - **Hivatkozás (*szerint*)**: 8 jelzés; mind rendben (a hivatkozás megmaradt vagy a párbeszéd szereplőjéhez
     kötött, pl. `0264` "a tanár szerint"); a `0209`/`0246`/`0262`/`0270` inputbeli "szerint" nem tulajdonítás.
   - **Tagadás**: az outputban új tagadás 0; a 19 sor, ahol az inputbeli tagadás nem szerepel az outputban, mind
     legitim tömörítés vagy pozitív átfogalmazás (*nem lépte túl -> megmaradt*, *nincs mozgás -> mozgás híján*).
   - **Ellentétpár-felcserélés**: 1 jelzés (`0292` "drágább" - az input "sokkal többe kerülne"), egyenértékű.
   - **Idő- és számszó**: az outputban idő- vagy számszó, ami az inputban nincs: 0 (egy hamis riasztás: `0278`
     *héten* = *első hét*); az inputbeli számok elhagyása 8 sorban (részletszám vagy példa), a döntő számok megmaradtak.
   - **Szótő-összevetés**: 1 sor >= 7 hiányzó tővel (`0209`), kézzel újraolvasva: körülírás, nem új tény.
5. **Tömörség**: output < input minden sorban; arányok és szószámok a 2. fejezetben.
6. **Batch dedupe**: id 0, instruction+input 0, output 0.
7. **Kereszt-dedupe teljes korpusz ellen**: az új 100 sor a 2700 meglévő clean sorral szemben (minden találatot
   vizsgálva, `quick_ratio` előszűréssel, ami matematikailag ekvivalens a teljes `ratio()`-val): 0 találat; a
   batch saját clean másolata ki van zárva. (A teljes N×N futás a 2700+ soros korpuszon nem praktikus.)
8. **Safety/firewall**: identity bleed 0; saját projekt/modellnév 0; URL, e-mail 0; kizárt témák 0. A
   kulcsszó-találatok hétköznapiak vagy biztonságpozitívak: `garant` (0281: a biztonságos oldal jele *nem
   garantálja* az eladó megbízhatóságát), `gyógyszer` (0273: csomaglista-tétel), `áram` (0204/0243/0249:
   elektromos áram, áramszünet), `biztosít` (0259: a szervezők biztosítják az anyagokat), `mindig` (0218: a pí
   állandó arány), `szerződés` (0236), `kölcsön` (0283). Biztos állítás, ígéret vagy veszélyes útmutatás nincs.
9. **Quality score**: 100.0 / 100, minden sor 100.
10. **Manuális mintavétel**: 40 sor, az 5. fejezet szerint.
11. **Clean/rejected/report**: clean 100, rejected 0 (üres fájl), ez a report; **progress** frissítve.

## 4. Önkorrekciók a felülvizsgálat során (mind clean előtt)

- **Erősített hűség-ellenőrző eredménye**: `0213` és `0216` outputjából kimaradt az input fenntartása
  (*általában*, *gyakran*) - pótoltam.
- **A 40 soros minta 3 (kisebb) találata**: `0209` ("szó nélkül evett, **míg** a legkisebb megjegyezte" - az input
  sorrendet ír, *majd*), `0246` (nyelvtani torzulás: *amekkorában*), `0281` (a "gyanús *lehet*" fenntartás
  elhalványult "gyanakodni"-ra). Mind javítva. Az előző batch mintájában 3 torzítás volt 20 sorból, most 3 kisebb
  hiba 40 sorból, és ezek már a hedge-ellenőrző utáni állapotban.
- **Írás közben javított túlállítás**: `0240` ("csak ajánlott küldeménnyel" - az input "általában"-t ír).
- **Tömörség**: a `0266` (0.86), `0253`, `0274`, `0239`, `0237` (0.83-0.85) output/input arányát szorosabbra
  fogalmaztam; azóta max. 0.84 (`0215`, ahol az input eleve rövid).
- **Köznyelvi "az" töltelék-névmás** az outputokban (`0205`, `0228`, `0236`, `0266`, `0293`, `0297`) - átfogalmazva.
- **Instruction**: az első kézzel írt készletben mind a 100 egyedi volt, de **96 sor nevezte meg a mondatszámot,
  25 sor "Két mondatban…"-nal kezdődött** (ez ugyanolyan mondatváz-szagú, mint a 2. batch generátora). Újraírtam
  kétszer: előbb a mondatszám-előírást ~felére csökkentettem és a nyitásokat változatossá tettem (de 89% lett
  a kérdő forma), majd ~45 kérdést felszólító igékre (*ismertesd, magyarázd el, vázold, fogalmazd meg, fejtsd ki,
  mutasd be, szedd össze*) cseréltem. Mind a 100 instructiont a saját szövege mellett végigolvastam
  (hozzárendelési hiba nincs), és 2 nehézkes megfogalmazást finomítottam (`0292`, `0300`).

## 5. Manuális mintavétel (40 sor, mind a 10 típusból 4)

Input és output egymás mellett elolvasva. A `0209`, `0246`, `0281` sort a mintavétel után javítottam. A
minta időpontjában az instructionök még az előző készletből valók voltak; azóta minden instructiont újra átolvastam.

| id | Típus | Mondat | Értékelés |
|---|---|---|---|
| summary_0201 | történet | 1 | Elveszett bőrönd: bejelentés, futár, hiánytalan. OK. |
| summary_0203 | történet | 1 | Lista nélküli vásárlás: pótló módszer, egy kimaradt tétel. OK. |
| summary_0202 | történet | 2 | Fára szorult macska: a helyzet és a létrás mentés. OK. |
| summary_0209 | történet | 2 | Kétszer sózott hús; "majd a legkisebb" (javított). OK. |
| summary_0213 | tanulás | 1 | Főnév és ige; "általában" pótolva. OK. |
| summary_0217 | tanulás | 1 | Őszi levélszínek: klorofill, rejtett színek, új piros. OK. |
| summary_0212 | tanulás | 2 | Kerekítés szabálya és haszna. OK. |
| summary_0216 | tanulás | 2 | Domborzati formák; "gyakran" pótolva. OK. |
| summary_0223 | projekt | 1 | Lépcsőházi polc első hete. OK. |
| summary_0227 | projekt | 1 | Nyári tábor: létszám, határidő, halasztási feltétel. OK. |
| summary_0224 | projekt | 2 | Csereklub: működés és első alkalom. OK. |
| summary_0230 | projekt | 2 | Receptgyűjtemény: hetven recept, hiányzó mennyiségek, cél. OK. |
| summary_0231 | ügyintézés | 1 | Diákbérlet: "általában", "a tájékoztató szerint" megőrizve. OK. |
| summary_0239 | ügyintézés | 1 | Óvodai beíratás: "általában" és a jelzés. OK. |
| summary_0232 | ügyintézés | 2 | Elveszett kulcs: "általában" a költségnél. OK. |
| summary_0236 | ügyintézés | 2 | Csomagváltás: "általában", "jellemzően". OK. |
| summary_0243 | technika | 1 | Ajtócsengő: áramkör, elektromágnes, hang. OK. |
| summary_0249 | technika | 1 | Napelemes számológép és tartalék elem. OK. |
| summary_0244 | technika | 2 | Digitális mérleg: elv és két pontossági feltétel. OK. |
| summary_0246 | technika | 2 | Tükörkép; nyelvtan javítva. OK. |
| summary_0251 | cikk | 1 | Új sétány; a csúszás a városvezetéshez kötve. OK. |
| summary_0255 | cikk | 1 | Parkolási fórum: két vélemény és a javaslatkérés. OK. |
| summary_0252 | cikk | 2 | Fagyriasztás; "szerint" a meteorológusokhoz kötve. OK. |
| summary_0256 | cikk | 2 | Menetrendváltozás: előny és aggodalom. OK. |
| summary_0263 | beszélgetés | 1 | Csúszó jelentés: B ajánlata és B vállalása. OK. |
| summary_0267 | beszélgetés | 1 | Mosogatás és szemétlevitel mint csere. OK. |
| summary_0264 | beszélgetés | 2 | Kirándulási befizetés; "általában" a tanár szerint. OK. |
| summary_0266 | beszélgetés | 2 | Cipőcsere: méret, szín, blokk (szorosabbra fogalmazva). OK. |
| summary_0271 | lista | 1 | Iskolakezdési szerek; darabszámok nélkül. OK. |
| summary_0273 | lista | 1 | Utazási lista, minden tétel megvan. OK. |
| summary_0274 | lista | 2 | Heti étlap és a bevásárlási sorrend (tömörítve). OK. |
| summary_0276 | lista | 2 | Nyári ruhatár és a világos, légáteresztő anyag indoka. OK. |
| summary_0281 | hosszú magyarázat | 1 | Online vásárlás; "gyanús lehet" és a nem-garancia. OK (javított). |
| summary_0287 | hosszú magyarázat | 1 | Piaci vásárlás négy tanácsa. OK. |
| summary_0284 | hosszú magyarázat | 2 | Napi tervezés: három teendő, tartalékidő, esti átnézés. OK. |
| summary_0288 | hosszú magyarázat | 2 | Türelem a gyerekekkel, a szabályok következetessége. OK. |
| summary_0291 | döntés | 1 | Házi feladat és játék: mérlegelés és ébresztős döntés. OK. |
| summary_0297 | döntés | 1 | Könyvek sorsa: idő és bevétel, adomány. OK. |
| summary_0292 | döntés | 2 | Kanapé vagy újrahuzat: két opció és árajánlat. OK. |
| summary_0300 | döntés | 2 | Zsúr helye; a szülők ideiglenes hajlama megőrizve. OK. |

**Eredmény: 40/40 megfelelt** (a három javított sor a javítás után). A 40 sor 40%-a a batchnek; a maradék 60 sort a
kézi átnézés nem érte el soronként, azokra az automatikus ellenőrzések (3. fejezet) vonatkoznak, és a jelzett
sorok mindegyikét kézzel is megnéztem.

## 6. Megfigyelések és korlátok (őszinte értékelés)

- **A hűség-ellenőrzés továbbra is heurisztika.** Az új ellenőrző jól jelezte a hedge-vesztést (2 valódi találat),
  de a jelentésbeli torzítást (pl. `0209` "míg" vs "majd") csak a kézi átolvasás fogta meg. A 40 soros mintában a
  hibák aránya (3/40) enyhén kedvezőbb, mint az előző batch mintájában (3/20), de nem lehet kizárni, hogy a nem
  mintázott 60 sorban is maradt kisebb pontatlanság.
- **Az instruction-készlet kézzel írt, de az új szerkezetek száma véges** (56 különböző nyitás, 12 sor "Írd le…"-vel
  kezdődik). A hátralévő 2 batchnél érdemes tovább bővíteni az igék és a szerkezetek körét.
- **A kétmondatos output határa 41 szó**: a tömörség megvan, de a 2. mondat gyakran felsorolás. A hosszabb
  magyarázat- és cikk-típusnál ez természetes.
- **Az `összefoglalás` tag aránya 10.7%** (300 / 2800), és a csomag lezárásakor 500 / 3000 = 16.7% lesz
  (ha közben más csomag nem bővül); ezt a kérésed szerint nem kezelem témaszaturációként, csak dokumentálom. A
  topic report ezt a taget minden futásnál jelezni fogja; a tag kategória-tagként való kezelése külön
  jóváhagyás kérdése.
- **Az ellenőrző scriptek (`check_summary.py`, `fidelity_check.py`) nem részei a repónak** (ideiglenes
  munkakönyvtár); a `tools/` alá emelésük külön jóváhagyandó lépés.

## 7. Fájlok

- Raw: `data/raw/claude_summary_0201_0300_raw.jsonl` (100 sor)
- Clean: `data/clean/claude_summary_0201_0300_clean.jsonl` (100 sor)
- Rejected: `data/rejected/claude_summary_0201_0300_rejected.jsonl` (0 sor, üres fájl)
- Report: `data/reports/claude_summary_0201_0300_report.md`

## 8. Regressziós teszt

`tests/test_v1_7_4_dataset_foundation.py` - minden teszt sikeres, **STÁTUSZ: STABIL**.

## 9. Amit ez a kör NEM tett

- Nem indított tanítást, nem módosított webapp/backend kódot, nem törölt és nem írt felül semmit.
- Nem készítette el a summary 0301-0500 sorait (külön jóváhagyásra várnak).
- Nem használt webes forrást, nem másolt szerzői jogvédett szöveget, nem használt ChatGPT raw jelöltet.
- Nem emelte a scripteket a repóba, és nem módosította a topic report tag-kezelését.

---

## Végső összegzés

- Claude batch: 100 sor, **100 clean / 0 rejected**, átlag score 100.0.
- Vegyes output: 50 egymondatos + 50 kétmondatos; mind rövidebb az inputnál (max. arány 0.84, kétmondatosnál 0.79).
- Instruction: 100 kézzel írt, egyedi, változatos; mondatszám-előírásuk mindig egyezik az outputtal.
- Manuális mintavétel: 40 sor, 40/40 megfelelt a 3 kisebb javítás után.
- Összes clean summary: **300 / 500**; hiányzik: **200**.
- Teljes clean korpusz: **2800 sor** (1000 simple_qa + 1000 explanation + 500 step_by_step + 300 summary).

**STÁTUSZ: STABIL.**
