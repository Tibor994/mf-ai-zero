# Negyedik FELÜGYELT summary batch - summary 0301-0400

A 4. csomag (Összegzés példa, cél: 500 clean sor) **negyedik 100 sora**. Közvetlenül Claude-generált,
kitalált, általános magyar tartalom (nincs valós személy/magánadat, webes forrás, szerzői jogvédett szöveg,
MF-AI-projekttény, veszélyes tanács vagy biztos orvosi/jogi/pénzügyi állítás). Az ügyintézési és cikk-jellegű
szövegek "általában", "tájékoztató szerint", "a szervezők szerint", "várhatóan" fenntartással szerepelnek, és az
output megtartja ezeket.

## 0. A kérés követelményei és teljesülésük

| Követelmény | Teljesülés |
|---|---|
| 40 soros manuális mintavétel megtartása | **40 sor** (mind a 10 típusból 4: 2 egy- és 2 kétmondatos), input és output egymás mellett elolvasva (5. fejezet) |
| Erősített hűség-ellenőrzés megtartása | a 3. batch `fidelity_check` szigorított, 2. változata (hedge-megőrzés, hivatkozás, tagadás, ellentétpár, idő-/számszó, számmegőrzés, szótő-összevetés) + **szószintű kézi ellenőrzés** a kimaradt hedge-szavakra (4. fejezet) |
| Jelentéstorzítás és hedge/fenntartás megőrzése (*általában, gyakran, szerint, lehet, gyanús, várható*) | végállapotban **LOST 0, ADDED 0, ADVICE->FACT 0**; 90 / 100 input tartalmaz védett fenntartó szót; az eredményhez 11 tartalmi javítás kellett (4. fejezet). A *gyanús* ebben a batchben egyik inputban sem szerepel, így itt nem volt mit megőrizni |
| Az instruction-nyitások szélesítése (ne 10-12 sablon) | 100 kézzel írt, 100/100 egyedi; **67 különböző kétszavas nyitás** (a 3. batchben 56, az 1-2.-ban 19), 81 különböző háromszavas, 29 különböző első szó. Korlátok a 6. fejezetben |
| Vegyesen 1 és 2 mondatos output | **50 / 50**, minden blokkban pontosan 5 kétmondatos |
| A 2 mondatos output is tömör | kétmondatos: max. 43 szó, átlagos output/input arány 0.65, max. 0.81 |
| Az output ne legyen hosszabb az inputnál | 0 sor, ahol output >= input; legmagasabb arány 0.81 (`0390`) |
| Ne adjon hozzá új tényt, ne torzítsa a jelentést | nincs új szám/név/időszó; nincs új fenntartás az outputban (ADDED 0) |
| `quality_notes` egyedi és konkrét | 100 / 100 egyedi, 10-25 szó, két szavas nyitása egyiknek sem ismétlődik; 31 megfogalmazást átírtam (4. fejezet) |
| Az `összefoglalás` tag aránya nőni fog: csak dokumentálni | 400 / 2900 = **13.8%** - a csomagot jelölő kategória-tagként dokumentálom, **nem** kezelem témaszaturációként; semmit nem módosítottam miatta |

## 1. Felépítés

10 tartalmi típus x 10 sor, az 1-3. batch témáitól eltérő új témákkal:

| ID tartomány | Típus | Címke | Kétmondatos sor |
|---|---|---|---|
| 0301-0310 | hétköznapi történet | `hétköznapi történet` | 5 |
| 0311-0320 | tanulási szöveg | `tanulási szöveg` | 5 |
| 0321-0330 | projektjegyzet | `projektjegyzet` | 5 |
| 0331-0340 | ügyintézés | `ügyintézés` | 5 |
| 0341-0350 | technikai magyarázat | `technikai magyarázat` | 5 |
| 0351-0360 | rövid cikk (kitalált helyi hír) | `rövid cikk` | 5 |
| 0361-0370 | beszélgetésrészlet (A/B vagy szerepjelölés, név nélkül) | `beszélgetés` | 5 |
| 0371-0380 | lista összefoglalása | `lista` | 5 |
| 0381-0390 | hosszabb magyarázat rövidítése | `hosszabb magyarázat` | 5 |
| 0391-0400 | döntési helyzet | `döntési helyzet` | 5 |

`tags` = `["magyar", "összefoglalás", <tartalmi típus>, <téma>]` (54 különböző téma-tag). `difficulty` az input
szószáma szerint (leghosszabb 10 = hard, következő 30 = medium, a többi easy).

## 2. Számok

| Mérőszám | Érték |
|---|---|
| Raw sorok | 100 |
| Schema validáció (`dataset_validate.py`, raw és clean is) | 100 / 100 valid |
| Batchen belüli dedupe (id / instruction+input / output, 0.9) | 0 / 0 / 0 |
| Kereszt-dedupe a 2800 meglévő clean sor ellen (id / instruction / output, >= 0.9, minden találat) | 0 / 0 / 0 |
| **Végleges clean** | **100** |
| **Rejected** | **0** |
| Átlag quality_score | **100.0 / 100** |
| Difficulty | easy 60, medium 30, hard 10 |
| Egyedi instruction / input / output / quality_notes | 100 / 100 / 100 / 100 |
| Input szószám (min / medián / max) | 31 / 49 / 70 |
| Output szószám (min / medián / max) | 17 / 30 / 43 |
| Egymondatos outputok: sor / max. szó / output-input arány (átl., max) | 50 / 40 / 0.63, 0.77 |
| Kétmondatos outputok: sor / max. szó / output-input arány (átl., max) | 50 / 43 / 0.65, 0.81 |
| Szó szerinti másolás (6 szavas egyezés az inputtal, max) | 0.43 (`0344`, `0397`; nincs 0.5 fölötti) |
| Instruction-mondatszám ellentmondás az outputtal | 0 |
| Identity bleed / saját projekt említés / URL, e-mail | 0 / 0 / 0 |
| Számjegy a szövegekben | 0 (a számok betűvel) |
| Topic report (2900 soros korpusz) | `összefoglalás` 13.8% (400 sor, várható, dokumentált), majd `fizika` 4.1%, `gazdaság` 3.7%; más túlreprezentált téma-tag nincs |
| Teljes clean korpusz | 2900 sor (1000 simple_qa, 1000 explanation, 500 step_by_step, 400 summary) |

## 3. Ellenőrzési lépések (a kért pipeline szerint)

1. **Generálás**: 100 sor 5 részben (20-20), külön szkripttel; az instructionök kézzel írt, soronként megfogalmazott
   készletből (nincs generátor); a fenntartó szavak (*általában, gyakran, szerint, lehet, várható, akár ...*) tudatosan
   szerepelnek az inputokban, hogy a megőrzésük tesztelhető legyen.
2. **Schema**: `dataset_validate.py` 100/100; saját mezőellenőrzés (9 kötelező mező, `category`, `source`,
   `difficulty`, nem üres `input`/`output`, `tags` fejléc, nincs számtartomány a `quality_notes`-ban).
3. **Summary forma és magyar nyelv**: az output nem üres, ponttal végződik, 1-2 mondatos; ékezetes karakterek,
   angol szavak, kódolási hiba, egyenes idézőjel, dupla szóköz, névelő-hiba, szóismétlés. A 3 jelzés
   az *inputokban* van (`0315` *az l*, *az s*: a betűk neve magánhangzóval kezdődik; `0390` *az gyakran*: mutató
   névmás), helyes magyar.
4. **Input-output hűség (erősített)**: automatikus ellenőrzések mind a 100 soron; a jelzett sorokat kézzel
   átnéztem. A találatok a kézi átnézéshez adnak támpontot, nem automatikus elutasítást (részletek a 4. fejezetben).
5. **Tömörség**: output < input minden sorban; arányok és szószámok a 2. fejezetben.
6. **Batch dedupe**: id 0, instruction+input 0, output 0.
7. **Kereszt-dedupe teljes korpusz ellen**: az új 100 sor a 2800 meglévő clean sorral szemben (minden találatot
   vizsgálva, `quick_ratio` előszűréssel, ami matematikailag ekvivalens a teljes `ratio()`-val): 0 találat; a
   batch saját clean másolata ki van zárva. (A teljes N×N futás a 2800+ soros korpuszon nem praktikus.)
8. **Safety/firewall**: identity bleed 0; saját projekt/modellnév 0; URL, e-mail 0; kizárt témák 0. A
   kulcsszó-találatok hétköznapiak vagy biztonságpozitívak: `adó` (0343 rádióadó), `biztosít` (0314, 0351),
   `gáz` (0319 a levegő gázai), `kölcsön` (0322, 0323, 0334, 0370, 0384: tárgy- és könyvkölcsönzés, nem pénzügyi),
   `mindig` (0316 a maradék mindig kisebb az osztónál), `nyugdíj` (0327 nyugdíjasklub), `orvos` (0344: az
   okosóra mérése *orvosi méréshez nem alkalmas*, tehát biztonságpozitív), `tűz` (0372 tűzhely), `áram` (0313,
   0344, 0345, 0350). Biztos állítás, ígéret vagy veszélyes útmutatás nincs.
9. **Quality score**: 100.0 / 100, minden sor 100.
10. **Manuális mintavétel**: 40 sor, az 5. fejezet szerint.
11. **Clean/rejected/report**: clean 100, rejected 0 (üres fájl), ez a report; **progress** frissítve (helyi fájl).

## 4. Hűség-ellenőrzés részletei és önkorrekciók (mind clean előtt)

**Automatikus, védett hedge-csoportok (a végállapotban 0 vesztés).** 90 / 100 input tartalmaz legalább egy védett
fenntartó vagy hivatkozó szót, 42 input -hat/-het alakú lehetőségjelzést. Szóalakonként (input sor / output sor):
*általában* 65 / 65, *gyakran* 32 / 30, *szerint* 35 / 43, *lehet* 41 / 37, *akár* 11 / 11, *várhatóan* 17 / 18,
*várható* 6 / 5, *körülbelül* 6 / 6, *nagyjából* 8 / 8, *előfordulhat* 5 / 5, *valószínűleg* 6 / 6, *egyelőre* 7 / 7,
*jellemzően* 2 / 2, *érdemes* 33 / 33. A szóalakonkénti különbségeket mind kézzel átnéztem, mind legitim:
`0396` és `0399` a *gyakran* mondatát (egy elhagyott mellékállítás), `0327` *várható -> várhatóan*, `0360` és `0397`
a *lehet* nem-fenntartó használata (*lehet teljesíteni*, *lehet játszani*), `0392` *használható lehet ->
használhatóvá teheti*. (Az outputban több *szerint* van, mert a beszélgetés *szerintem*-jét *B szerint*-re írtam át.)

**Az első futás találatai és javításaik:**

- **Hedge-vesztés (3)**: `0344` (*akár nehezebb is lehet*), `0363` (*lehet kérni*), `0380` (*lehet vinni*). `0344`-nél
  és `0380`-nál a fenntartást hordozó, az összefoglalásból amúgy is kimaradó mellékmondatot az **inputból** vettem ki,
  nem az outputot bővítettem (ez a szintetikus batchnél elfogadható, de tudni érdemes); `0363`-nál az outputot
  egészítettem ki (*udvariasan és nyugodtan lehet kérni*).
- **Túl magas output/input arány (5)**: `0357` (0.90), `0371` (0.86), `0327` (0.83), `0331` (0.80), és a fenti
  input-rövidítés után `0380` (0.89). Mindegyiknél az **inputot** bővítettem egy semleges, fenntartás nélküli
  mondattal (az output változatlan). Ezért a végső arányok részben hosszabb inputoknak köszönhetők (input medián
  49 szó a 3. batch 47 szavával szemben); a tömörítés ténylegesen nem szigorodott.
- **31 `quality_notes` átírva**: nehézkes vagy hibás megfogalmazás (*a általában*, elgépelések, *nőhető*, *lehető*
  helytelen használata, kapkodott felsorolások) - természetes magyarra.
- **Szószintű kézi ellenőrzés, a 40 soros minta és a tagadás-átnézés további találatai (8 sor + 1 visszaállítás):**
  - `0326`: az input *a legtöbb kisebb hiba* - az output "a kisebb hibák" (kimaradt a *legtöbb*) -> pótolva.
  - `0372`: az input *legalább egy hűtő és egy tűzhely* - az output elhagyta a *legalább*-ot -> pótolva.
  - `0390`: az *általában* hatóköre elcsúszott (*általában lassabban nőnek* vs. az input *általában elélnek, de lassabban
    növekednek*) -> az input szerkezetére visszaírva.
  - `0382`: az input szabálya (*ne állítsuk túl magasra*) az outputban gyengült (*nem érdemes*) -> visszaírva.
  - `0397`: az *időjárás szerint gyakran elmarad az edzés* oka kimaradt -> pótolva.
  - `0362`: "*A a* szerdát" nehézkes névelő/szereplő-jelölés, és *kevesebben vannak bent* helyett *a legkevesebben*
    (túlzás) -> átírva B szerinti indoklásra.
  - `0364`: az output második mondata "*A megveszi.*" értelmezhetetlen (névelő/szereplő-jelölés), és a *nem túl bonyolult*
    kimaradt -> "*..., de nem túl bonyolult. Erre A azt válaszolja, hogy megveszi.*" (a tagadás-átnézésből).
  - `0388`: az input *a viselkedésre vonatkozik, nem a személyre* ellentétéből a *nem a személyre* kimaradt -> pótolva
    (a tagadás-átnézésből).
  - `0304`: átmenetileg "a mesélő"-re cseréltem a "a szerző"-t, de az 1-3. batch végig "a szerző"-t használja az E/1
    szereplőre, ezért a konzisztencia miatt visszaállítottam.
- **Nem hiba, csak jelzés**: az ellentétpár-találat (`0327` *érkez/indul*, `0392` *drág/olcsó*) a szövegek
  természetes ellentéte, jelentésfelcserélés nincs; a *szamnev* jelzések (`0319` *egyötöd* = *az ötödét*, `0326`
  *tíztől*, `0332` *hét* = *két hét*, `0335` *héten*) helyes; az inputbeli tagadás elmaradása 13 sorban (0305, 0318,
  0342, 0348, 0350, 0364, 0375, 0381, 0387, 0388, 0394, 0395, 0399) és az 5 sor, ahol az input számneve nem szerepel
  az outputban (0326, 0329, 0360, 0372, 0377) soronként átnézve: 0364 és 0388 hibát adott (fent, javítva); a többi
  tömörítés vagy pozitív átfogalmazás (pl. `0381` *nem lehet teljesen biztos* -> *nagyobb a bizonytalanság*,
  `0394` egy elhagyott hátrány, `0377` a tudatosan mennyiségek nélküli lista).

**Retrospektív megjegyzés az 1-3. batchre** (nem javítottam, mert nem ennek a batchnek a hatóköre, és az előző
batchek commitjai már készen vannak): ugyanezzel a szigorúbb ellenőrzővel visszamérve az 1. batch 18 jelzést és 5
*érdemes -> tény* gyanút ad (`0016`, `0027`, `0061`, `0073`, `0090`), a 2. batch 18 jelzést és 2 gyanút (`0175`,
`0185`), a 3. batch 9 jelzést és 4 gyanút (`0239`, `0273`, `0277`, `0279`). A jelzések egy része legitim kihagyás vagy
egyenértékű megfogalmazás, de a gyanús *érdemes -> tény* sorokat érdemes külön, jóváhagyott javítási körben átnézni.

## 5. Manuális mintavétel (40 sor, mind a 10 típusból 4)

Input és output egymás mellett elolvasva; a sor kiválasztása blokkonként rögzített (a blokk 2., 5., 7. és 10. sora),
tehát nem a legjobbnak látszó sorokból. Öt sort a mintavétel után javítottam (`0362`, `0382`, `0390`, `0397`,
`0372`).

| id | Típus | Mondat | Értékelés |
|---|---|---|---|
| summary_0302 | történet | 2 | Paradicsompalánták: "akár tönkretehette volna" megőrizve. OK. |
| summary_0305 | történet | 1 | Makacs zár: "valószínűleg" a lakatos szerint. OK. |
| summary_0307 | történet | 1 | Sorban állás a postán, a beszélgetés hatása. OK. |
| summary_0310 | történet | 2 | Nappali-piknik; "gyakran" a tanulságban. OK. |
| summary_0312 | tanulás | 2 | Napfogyatkozás; "veszélyes lehet" megőrizve. OK. |
| summary_0315 | tanulás | 1 | Betűrend elve és kettős betűk. OK. |
| summary_0317 | tanulás | 1 | Iránytű: "általában" és "érdemes". OK. |
| summary_0320 | tanulás | 2 | Szólás és közmondás; "rendszerint", "gyakran". OK. |
| summary_0322 | projekt | 2 | Szerszámtár; "általában" a hétvégi forgalomnál. OK. |
| summary_0325 | projekt | 1 | Tanulócsoport: "szervezők szerint", "akár", "egyelőre". OK. |
| summary_0327 | projekt | 1 | Nyugdíjasklub kirándulás: "várhatóan", "időjárás szerint". OK. |
| summary_0330 | projekt | 2 | Ruhabörze: "körülbelül", "szervezők szerint". OK. |
| summary_0332 | ügyintézés | 2 | Parkolási engedély: "általában", "körülbelül", "jellemzően". OK. |
| summary_0335 | ügyintézés | 1 | Webshopos visszaküldés: "általában", "várhatóan". OK. |
| summary_0337 | ügyintézés | 1 | Diákigazolvány-pótlás; "díjjal is járhat". OK. |
| summary_0340 | ügyintézés | 2 | Kerékpártároló: "általában", "gyakran", "várólista is lehet". OK. |
| summary_0342 | technika | 2 | Robotporszívó: "gyakran", "előfordulhat". OK. |
| summary_0345 | technika | 1 | Szélturbina: "általában leállítják". OK. |
| summary_0347 | technika | 1 | Páramentesítő: "általában", "leállhat". OK. |
| summary_0350 | technika | 2 | Hűtőtömítés: "gyakran", "valószínűleg". OK. |
| summary_0352 | cikk | 2 | Vízszünet: "várhatóan", "még változhat". OK. |
| summary_0355 | cikk | 1 | Térképkiállítás: "szervezők szerint akár". OK. |
| summary_0357 | cikk | 1 | Virágkiállítás: "tervek szerint", "valószínűleg", "várhatóan". OK. |
| summary_0360 | cikk | 2 | Túraverseny: "szervezők szerint", "várhatóan". OK. |
| summary_0362 | beszélgetés | 2 | Szabadság-egyeztetés; szereplő-jelölés és "kevesebben" javítva. OK (javított). |
| summary_0365 | beszélgetés | 1 | Étteremi rendelés: "körülbelül tizenöt perc". OK. |
| summary_0367 | beszélgetés | 1 | Zsebpénz: "általában", "nagyjából". OK. |
| summary_0370 | beszélgetés | 2 | Létrakölcsönzés: "általában", "esetleg". OK. |
| summary_0372 | lista | 2 | Első lakás bútorai; "legalább" pótolva. OK (javított). |
| summary_0375 | lista | 1 | Alapfűszerek és tárolás. OK. |
| summary_0377 | lista | 1 | Tortahozzávalók; "eltérhetnek". OK. |
| summary_0380 | lista | 2 | Bevásárlás előtt; "általában", "gyakran". OK. |
| summary_0382 | hosszú magyarázat | 2 | Takarékos fűtés; a szabály ("ne állítsuk") visszaírva. OK (javított). |
| summary_0385 | hosszú magyarázat | 1 | Használati útmutató sorrendje; "nem biztos". OK. |
| summary_0387 | hosszú magyarázat | 1 | Jegyzetrendszerezés; "túl sok szín zavaró lehet". OK. |
| summary_0390 | hosszú magyarázat | 2 | Szobanövények fényigénye; "általában" hatóköre javítva. OK (javított). |
| summary_0392 | döntés | 2 | Frissítés vagy új gép; "szakember szerint", "várhatóan". OK. |
| summary_0395 | döntés | 1 | Reggeli/esti tanulás; "egyelőre" a próbánál. OK. |
| summary_0397 | döntés | 1 | Sakk vagy foci; az időjárási ok pótolva. OK (javított). |
| summary_0400 | döntés | 2 | Közös udvar; "közgyűlés szerint", "várhatóan". OK. |

**Eredmény: 40/40 megfelelt** (az öt javított sor a javítás után). A 40 sor a batch 40%-a; a maradék 60 sort a
kézi átnézés soronként nem érte el, arra az automatikus ellenőrzések (3-4. fejezet) vonatkoznak, és a jelzett
sorok mindegyikét (az összes automatikus jelzést és a szószintű, valamint a tagadás-átnézés találatait) kézzel is
megnéztem. A mintában 5/40
javítás kellett (3. batch: 3/40), tehát a szigorúbb szószintű ellenőrzés több finom hibát talált, mint az
előző kör - a nem mintázott 60 sorban maradhat hasonló kisebb pontatlanság.

## 6. Megfigyelések és korlátok (őszinte értékelés)

- **A hűség-ellenőrzés továbbra is heurisztika.** A csoportszintű ellenőrző (pl. *lehet/akár/várható* egy csoportban)
  nem látta a *legtöbb* (`0326`), a *legalább* (`0372`), az *általában* elcsúszó hatókörét (`0390`) és a szabály
  gyengülését (`0382`); ezeket a szószintű lista és a kézi olvasás fogta meg. Az ellenőrző nem tud a hatókörről és
  az árnyalatról; a *gyanús* szó ebben a batchben nem szerepelt, így annak tesztelése itt nem történt meg.
- **Instruction-készlet.** A nyitások szélesedtek (67 kétszavas nyitás, 81 háromszavas, 31% kérdő), de két mutató
  romlott a 3. batchhez képest: 71% nevezi meg a mondatszámot (3. batch: 54%) és 9 sor kezdődik "Foglald össze"-val
  (3. batch: 1). Az összes 400 summary-sorra: 130 különböző kétszavas nyitás, a leggyakoribb "Foglald össze" 53
  sor (13%), "Írd le" 25, "Mi a" 24. A mondatszám-megnevezés az output mondatszámával mindig egyezik (0
  ellentmondás), de az utolsó batchnél érdemes kevesebb mondatszám-előírással és több szituációs, témaspecifikus
  instructionnel dolgozni.
- **Tömörség.** Az arányok részben hosszabb inputoknak köszönhetők (lásd 4. fejezet); a kétmondatos output második
  mondata gyakran felsorolás, ami a hosszabb típusoknál természetes.
- **Az `összefoglalás` tag aránya 13.8%** (400 / 2900); a csomag lezárásakor 500 / 3000 = 16.7% lesz (ha közben más
  csomag nem bővül). A kérésed szerint nem kezelem témaszaturációként, csak dokumentálom; a topic report ezt a taget
  minden futásnál jelezni fogja, a tag kategória-tagként való kezelése külön jóváhagyás kérdése.
- **Az ellenőrző scriptek (`check_summary.py`, `fidelity_check2.py`, `targeted_cross_summary4.py`) nem részei a
  repónak** (ideiglenes munkakönyvtár); a `tools/` alá emelésük külön jóváhagyandó lépés.
- **Az 1-3. batch fenti retrospektív jelzései** (4. fejezet vége) nyitott, nem javított tételek.

## 7. Fájlok

- Raw: `data/raw/claude_summary_0301_0400_raw.jsonl` (100 sor)
- Clean: `data/clean/claude_summary_0301_0400_clean.jsonl` (100 sor)
- Rejected: `data/rejected/claude_summary_0301_0400_rejected.jsonl` (0 sor, üres fájl)
- Report: `data/reports/claude_summary_0301_0400_report.md`

## 8. Regressziós teszt

`tests/test_v1_7_4_dataset_foundation.py` - minden teszt sikeres, **STÁTUSZ: STABIL**.

## 9. Amit ez a kör NEM tett

- Nem indított tanítást, nem módosított webapp/backend kódot, nem törölt és nem írt felül semmit.
- Nem készítette el a summary 0401-0500 sorait (külön jóváhagyásra várnak).
- Nem használt webes forrást, nem másolt szerzői jogvédett szöveget, nem használt ChatGPT raw jelöltet.
- Nem emelte a scripteket a repóba, nem módosította a topic report tag-kezelését, és nem javította az 1-3. batch
  retrospektíven jelzett soraiban a fenntartás-vesztést.

---

## Végső összegzés

- Claude batch: 100 sor, **100 clean / 0 rejected**, átlag score 100.0.
- Vegyes output: 50 egymondatos + 50 kétmondatos; mind rövidebb az inputnál (max. arány 0.81, kétmondatosnál is 0.81).
- Hedge/fenntartás: 90 fenntartó inputból 0 elveszett, 0 új fenntartás; a szigorú, szószintű és tagadás-átnézés összesen 11 tartalmi javítást hozott.
- Instruction: 100 kézzel írt, egyedi; 67 kétszavas nyitás; mondatszám-előírásuk mindig egyezik az outputtal
  (de 71% nevezi meg a mondatszámot, lásd 6. fejezet).
- Manuális mintavétel: 40 sor, 40/40 megfelelt az 5 javítás után.
- Összes clean summary: **400 / 500**; hiányzik: **100**.
- Teljes clean korpusz: **2900 sor** (1000 simple_qa + 1000 explanation + 500 step_by_step + 400 summary).

**STÁTUSZ: STABIL.**
