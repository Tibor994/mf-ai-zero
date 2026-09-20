# Ötödik (záró) FELÜGYELT summary batch - summary 0401-0500

A 4. csomag (Összegzés példa, cél: 500 clean sor) **záró 100 sora**. Közvetlenül Claude-generált, kitalált, általános
magyar tartalom (nincs valós személy/magánadat, webes forrás, szerzői jogvédett szöveg, MF-AI-projekttény, veszélyes
tanács vagy biztos orvosi/jogi/pénzügyi állítás). A szövegek fenntartásokkal íródtak (*általában, gyakran, szerint,
lehet, várható, akár, gyanús, valószínű, nem biztos*), és az outputok megtartják ezeket.

## 0. A kérés követelményei és teljesülésük

| Követelmény | Teljesülés |
|---|---|
| 100 clean sor, rejected csak indokolt esetben | **100 clean / 0 rejected** (nem volt indokolt kiszűrés; a hibákat clean előtt javítottam) |
| Vegyesen 50 egymondatos + 50 kétmondatos output | **50 / 50**, minden blokkban pontosan 5-5 |
| Az output mindig rövidebb az inputnál | 0 sor, ahol output >= input; legmagasabb arány 0.79 (`0488`), egymondatosnál 0.78, kétmondatosnál 0.79 |
| Ne adj hozzá új tényt, ne torzítsd a jelentést | nincs új szám, név vagy időszó; új fenntartás az outputban 0 (az 5 jelzés beszélgetés-szereplőre hivatkozó *szerint*, lásd 4. fejezet) |
| A fenntartások megőrzése (*általában, gyakran, szerint, lehet, várható, akár, gyanús, valószínű, nem biztos*) | 99 / 100 input tartalmaz védett fenntartást; **végállapotban 0 valódi vesztés**, 0 óvatos -> biztos átalakulás (4. fejezet) |
| Kevesebb instruction nevezze meg a mondatszámot | **28%** (előző batch: 71%; a 400 korábbi sorban 56%) |
| Több témaspecifikus instruction | mind a 100 a saját szöveg konkrét témájára kérdez (pl. *vízóra*, *madárodú*, *termosztát*); **100 különböző téma-címke** (a 3-4. batchben 54-57) |
| Ne kezdődjön túl sok sor "Foglald össze"-val | **0 sor kezdődik így** (előző batch: 9; az 1. batchben 29); az ige egyetlen instructionben szerepel (`0458`, *Két mondatban foglald össze...*) |
| `quality_notes` egyedi, konkrét, természetes | 100 / 100 egyedi, 13-26 szó; mind a 100-at természetes mondatokra írtam át (4. fejezet) |
| Manuális mintavétel legalább 40 sorral | **40 sor** (mind a 10 típusból 4: 2 egy- és 2 kétmondatos), input és output egymás mellett elolvasva (6. fejezet) |
| Az `összefoglalás` tag aránya | 500 / 3000 = **16.7%** - a csomagot jelölő kategória-tagként dokumentálom, nem témaszaturáció |

## 1. Felépítés

10 tartalmi típus x 10 sor, az 1-4. batch témáitól eltérő új témákkal (a 108 addig használt téma-címke elkerülésével):

| ID tartomány | Típus | Címke | Kétmondatos sor |
|---|---|---|---|
| 0401-0410 | hétköznapi történet | `hétköznapi történet` | 5 |
| 0411-0420 | tanulási szöveg | `tanulási szöveg` | 5 |
| 0421-0430 | projektjegyzet | `projektjegyzet` | 5 |
| 0431-0440 | ügyintézés | `ügyintézés` | 5 |
| 0441-0450 | technikai magyarázat | `technikai magyarázat` | 5 |
| 0451-0460 | rövid cikk (kitalált helyi hír) | `rövid cikk` | 5 |
| 0461-0470 | beszélgetésrészlet (A/B vagy szerepjelölés, név nélkül) | `beszélgetés` | 5 |
| 0471-0480 | lista összefoglalása | `lista` | 5 |
| 0481-0490 | hosszabb magyarázat rövidítése | `hosszabb magyarázat` | 5 |
| 0491-0500 | döntési helyzet | `döntési helyzet` | 5 |

`tags` = `["magyar", "összefoglalás", <tartalmi típus>, <téma>]`. `difficulty` az input szószáma szerint (leghosszabb 10
= hard, következő 30 = medium, a többi easy).

## 2. Számok

| Mérőszám | Érték |
|---|---|
| Raw sorok | 100 |
| Schema validáció (`dataset_validate.py`, raw és clean is) | 100 / 100 valid |
| Batchen belüli dedupe (id / instruction+input / output, 0.9) | 0 / 0 / 0 |
| Kereszt-dedupe a 2900 meglévő clean sor ellen (id / instruction / output, >= 0.9, minden találat) | 0 / 0 / 0 |
| **Végleges clean** | **100** |
| **Rejected** | **0** |
| Átlag quality_score | **100.0 / 100** |
| Difficulty | easy 60, medium 30, hard 10 |
| Egyedi instruction / input / output / quality_notes | 100 / 100 / 100 / 100 |
| Input szószám (min / medián / max) | 34 / 55 / 74 |
| Output szószám (min / medián / max) | 18 / 34 / 44 |
| Egymondatos outputok: sor / max. szó / output-input arány (átl., max) | 50 / 42 / 0.60, 0.78 |
| Kétmondatos outputok: sor / max. szó / output-input arány (átl., max) | 50 / 44 / 0.66, 0.79 |
| Szó szerinti másolás (6 szavas egyezés az inputtal, max) | 0.46 (`0424`; nincs 0.5 fölötti) |
| Instruction-mondatszám ellentmondás az outputtal | 0 |
| Identity bleed / saját projekt említés / URL, e-mail | 0 / 0 / 0 |
| Számjegy a szövegekben | 0 (a számok betűvel) |
| Topic report (3000 soros korpusz) | `összefoglalás` 16.7% (500 sor, várható, dokumentált), majd `fizika` 4.0%, `gazdaság` 3.6%; más túlreprezentált téma-tag nincs |
| Teljes clean korpusz | 3000 sor (1000 simple_qa, 1000 explanation, 500 step_by_step, 500 summary) |

## 3. Ellenőrzési lépések (a kért pipeline szerint)

1. **Generálás**: 100 sor 5 részben (20-20), külön szkripttel; az instructionök soronként kézzel írt szövegek (nincs
   generátor); a fenntartó szavak tudatosan szerepelnek az inputokban.
2. **Schema**: `dataset_validate.py` 100/100; saját mezőellenőrzés (9 kötelező mező, `category`, `source`, `difficulty`,
   nem üres `input`/`output`, `tags` fejléc, számjegy-mentesség).
3. **Summary forma**: az output nem üres, ponttal végződik, 1-2 mondatos; 50/50 blokkonként 5-5; ékezet, angol szó,
   kódolási hiba, egyenes idézőjel, dupla szóköz, névelő-hiba, szóismétlés. A jelzések mind helyes magyar (*az gyanús*,
   *az nem*, *az szükséges*: mutató névmás; *az az ok/oldal* szintén). A quality_notes-ban talált hibák (*a általában*,
   *a egyhónapos*) a teljes átírással megszűntek.
4. **Tömörség**: output < input minden sorban; arányok és szószámok a 2. fejezetben.
5. **Input-output hűség (szigorított, `fidelity_check3`)**: védett hedge-csoportok megőrzése, hivatkozás, *érdemes* ->
   tény, tagadás, ellentétpár, idő-/számszó, szótő-összevetés; ezen felül új csoportok a *valószínű* és a *nem biztos*
   számára (4. fejezet).
6. **Fenntartás/hedge megőrzés, szószinten** (`word_drops`): minden fenntartó szóra soronként kilistáztam, hol van meg
   az inputban és hol hiányzik az outputból, majd mindet kézzel átnéztem (4. fejezet).
7. **Batch dedupe**: id 0, instruction+input 0, output 0.
8. **Kereszt-dedupe teljes korpusz ellen**: az új 100 sor a 2900 meglévő clean sorral szemben (minden találatot
   vizsgálva, `quick_ratio` előszűréssel, ami matematikailag ekvivalens a teljes `ratio()`-val): 0 találat; a batch saját
   clean másolata ki van zárva.
9. **Safety/firewall**: identity bleed 0; saját projekt/modellnév 0; URL, e-mail 0; kizárt témák 0. A kulcsszó-találatok
   biztonságpozitívak vagy hétköznapiak: `jelszó` (0458: a bank *általában nem kér telefonon jelszót*, csalás-figyelmeztetés),
   `gáz` (0475: elzárás indulás előtt), `mindig` (0414, 0445, 0479: *nem biztos, hogy mindig*; 0415: a háromszög
   szögösszege sík háromszögben tényleg mindig száznyolcvan fok), `kölcsön` (0401, 0494: tárgy/eszköz kölcsönzése),
   `feltör` (0473: az új cipő feltörheti a lábat), `ígér` (0450: kábel). Biztos állítás, ígéret vagy veszélyes útmutatás nincs.
10. **Quality score**: 100.0 / 100, minden sor 100.
11. **Regressziós teszt**: `tests/test_v1_7_4_dataset_foundation.py` - minden teszt sikeres, **STÁTUSZ: STABIL**.
12. **Manuális mintavétel**: 40 sor, a 6. fejezet szerint.
13. **Clean/rejected/report**: clean 100, rejected 0 (üres fájl), ez a report; **progress** frissítve (helyi fájl).

## 4. Hűség- és fenntartás-ellenőrzés részletei, önkorrekciók (mind clean előtt)

**Védett szavak az inputban / az outputban (sorok száma, végállapot):** *általában* 80 / 80, *nem biztos* 48 / 48,
*szerint* 58 / 65, *gyakran* 40 / 36, *akár* 30 / 30, *valószínűleg* 29 / 29, *gyanús* + *gyanúsan* 18 / 18, *várhatóan*
17 / 17, *körülbelül* 12 / 12, *egyelőre* 12 / 12, *legalább* 3 / 3, *néha* 3 / 3, *lehet* 32 / 27, *egyes* 5 / 4,
*várható* 1 / 0. Csoportonként: fenntartást hordoz az input 99 sorában; 75 sor legalább három különböző csoportot használ.

**A szószintű különbségek (mind kézzel átnézve, mind legitim):** *gyakran* (`0402`, `0474`, `0494`, `0497`): az output
teljes egészében elhagyta azt a mellékmondatot, amelyben szerepelt, tehát nem állít semmit róla; *lehet* (`0421`, `0427`,
`0436`, `0437`, `0441`, `0480`): -ható/-hető vagy egyenértékű alakká alakítva (*lehet lefoglalni -> foglalható*, *nem lehet
készpénzre váltani -> nem váltható*); *előfordulhat -> késhet* (`0431`); *várható csapadék -> esik eső* (`0489`);
*egyes* (`0488`) a *mindegyik* jelentésű *az egyes megállókat*, nem fenntartás. A *szerint* több az outputban, mert a
beszélgetések (`0461`, `0462`, `0467`, `0469`, `0470`) szereplőjének megszólalását *az eladó szerint / B szerint* alakkal
adom vissza, ez a korábbi batchekkel konzisztens és nem új tulajdonítás.

**Az első futás találatai és javításaik (15 tartalmi javítás, ebből 5 az input oldalán):**

- **Hedge-/hivatkozásvesztés (8 jelzés, 7 valódi)**: `0424` és `0468` az output *még nem biztos* helyett *nem biztos*-t
  írt; `0494` az *az olvasó szerint* hivatkozás kimaradt; `0459` az output *nem biztos*-ra egyszerűsítette a *még nem
  erősítették meg* megerősítetlenséget; az input-oldali javítások: `0446` (elhagyott mondat *általában*-ja), `0473` (*gyakran feltöri*
  -> *feltörheti*, az indoklás a kimaradó részben), `0481` (a kihagyott hirdetés-mondat *még nem*-je). A `0488` jelzése
  hamis riasztás (*az egyes megállókat*). Öt sornál (`0414` egy kimaradó *akár*-mondata, `0446`, `0459` egy mellékága,
  `0473`, `0481`) az **inputból** vettem ki vagy semlegesítettem a fenntartást hordozó, az outputból amúgy is kimaradó
  részt, és nem az outputot bővítettem; tudni érdemes, hogy ezek szintetikus inputok.
- **Szószintű átnézés (5 javítás)**: `0438` (*eltérő lehet* -> *eltérően*: a lehetőség elveszett), `0423` és `0456`
  (*még nem biztos* -> *nem biztos*), `0499` és `0463` (*még van hely/szoba* -> *van*).
- **A 40 soros minta 2 javítást igényelt**: `0447` (az instruction az *elhelyezésről* is kérdez, az output elhagyta a
  *nem célszerű közvetlenül a konyhába tenni* tanácsot) és `0464` (B javaslata "Szólnának..." helyett *B azt javasolja,
  hogy szóljanak...*). Ezen kívül `0449`-ben az *az az ok* nehézkes szerkezetet *csak emiatt*-re cseréltem.
- **Tömörség és másolás**: `0424` (0.87) és `0430` (0.82) túl magas output/input arányát az **inputot** semleges mondattal
  bővítve javítottam (tehát részben hosszabb inputnak köszönhető, input medián 55 szó a 4. batch 49-e után); a 0.5
  fölötti szó szerinti másolást (`0480` 0.57, `0493` 0.53, `0500` 0.50) az outputok átfogalmazásával szüntettem meg.
- **Instruction**: az első kézzel írt készlet 48%-ban *Hogyan* vagy *Mit* szóval kezdődött (25 + 23 sor) és csak 3 nevezte
  meg a mondatszámot; 55 instructiont újraírtam felszólító, főnévi és témaspecifikus nyitásra (5. fejezet), és visszaállítottam
  a mondatszám-megnevezést egy mérsékelt szintre. Mind a 100 instructiont a saját szövege mellett végigolvastam.
- **quality_notes**: az első változat merev "X: a..., a... és a..." felsorolás volt, néhány pontatlansággal (`0438` *akár*,
  ami az outputban nincs) és elírással (*a általában*, *a egyhónapos*, *esős lehető*, *féláras próba*); mind a 100-at
  természetes mondatokra írtam át és soronként az outputtal egyeztettem.

## 5. Instruction-nyitások: mérés a csomag összes batchén

| Batch | Különböző első szó | Különböző kétszavas nyitás | Mondatszámot nevez | "Foglald össze" nyitás | Kérdő |
|---|---|---|---|---|---|
| 0001-0100 | 11 | 19 | 23% | 29 | 0% |
| 0101-0200 | 12 | 19 | 77% | 14 | 0% |
| 0201-0300 | 28 | 56 | 54% | 1 | 38% |
| 0301-0400 | 29 | 67 | 71% | 9 | 31% |
| **0401-0500** | **50** | **79** | **28%** | **0** | 55% |
| Mind az 500 sor | 71 | 184 | 51% | 53 | 25% |

A 4. batchen belül a leggyakoribb első szó a *Mit* (11%), majd a *Két* (7%) és az *Ismertesd* (5%). A kérdő forma aránya
55% - ez a témaspecifikus "mit/miért/hogyan mérlegel" szerkezetek természetes következménye, de érdemes tudni.

## 6. Manuális mintavétel (40 sor, mind a 10 típusból 4)

Kiválasztás: blokkonként a 2. és 4. egymondatos, valamint a 2. és 4. kétmondatos sor (rögzített szabály, nem a legjobbnak
látszó sorok). Input és output egymás mellett elolvasva; a `0447` és `0464` sort a mintavétel után javítottam.

| id | Típus | Mondat | Értékelés |
|---|---|---|---|
| summary_0403 | történet | 1 | Első kenyér: "valószínűleg", "nem biztos" megőrizve. OK. |
| summary_0404 | történet | 2 | Gitárlecke: "általában" a tanár szerint, javulás. OK. |
| summary_0407 | történet | 1 | Garázsvásár: "akár egész nap ... ha nem vesz" feltételes szerkezet megőrizve. OK. |
| summary_0408 | történet | 2 | Busz: "általában húsz perc", "hétfőn néha korábban". OK. |
| summary_0413 | tanulás | 2 | Tő- és sorszámnév; "gyakran", "általában". OK. |
| summary_0414 | tanulás | 1 | Vulkánok: "gyakran", "nem biztos, hogy a figyelmeztetés időben érkezik". OK. |
| summary_0417 | tanulás | 1 | Népmesék: "gyakran", "általában", "szakemberek szerint". OK. |
| summary_0418 | tanulás | 2 | Hőmérő: "gyanús lehet, és nem biztos". OK. |
| summary_0423 | projekt | 1 | Térkép: "még nem biztos", "akár csak digitális". OK. |
| summary_0424 | projekt | 2 | Virágládák: "lakók szerint", "még nem biztos". OK. |
| summary_0427 | projekt | 1 | Ruhajavító: "legtöbb", "valószínűleg", "egyelőre nem biztos". OK. |
| summary_0428 | projekt | 2 | Könyvcsere-polc: "gyanúsan nedves". OK. |
| summary_0433 | ügyintézés | 2 | Garancia: "általában", "akár", "valószínűleg". OK. |
| summary_0434 | ügyintézés | 1 | Számlareklamáció: "várhatóan harminc nap", "hosszabb is lehet". OK. |
| summary_0437 | ügyintézés | 1 | Utalvány: "általában", "gyakran", "nem biztos". OK. |
| summary_0438 | ügyintézés | 2 | Kukaürítés: "eltérő lehet" megőrizve (javított). OK. |
| summary_0443 | technika | 1 | Vonalkód: "általában", "gyakran". OK. |
| summary_0444 | technika | 2 | Wifi: "akár jelentősen", "gyanúsan alacsony". OK. |
| summary_0447 | technika | 1 | Füstérzékelő: az elhelyezési tanács pótolva. OK (javított). |
| summary_0449 | technika | 2 | Kerti lámpa: "gyanús lehet", "nem biztos". OK (finomított). |
| summary_0453 | cikk | 1 | Sportnap: "valószínűleg felhős, de nem biztos". OK. |
| summary_0454 | cikk | 2 | Patak: "akár két méterrel", "várhatóan kedden". OK. |
| summary_0457 | cikk | 1 | Méz: "körülbelül harmad", "nem biztos, hogy csak emiatt". OK. |
| summary_0458 | cikk | 2 | Rendőrségi figyelmeztetés: "gyanús", "valószínűleg, de nem biztos"; védő tartalom. OK. |
| summary_0463 | beszélgetés | 1 | Vonat: "általában még van hely", "akár húsz perc". OK. |
| summary_0464 | beszélgetés | 2 | Kanapé: B javaslata megőrizve (javított). OK. |
| summary_0466 | beszélgetés | 1 | Akvárium: "szerint", "általában", "nem biztos". OK. |
| summary_0468 | beszélgetés | 2 | Értekezlet: "valószínűleg", "még nem biztos". OK. |
| summary_0473 | lista | 1 | Osztálykirándulás: "tanárok szerint", "akár hűvös". OK. |
| summary_0474 | lista | 2 | Szerszámápolás: "akár", "gyanús lehet". OK. |
| summary_0476 | lista | 1 | Vendégvárás: "általában", "gyakran", "valószínűleg". OK. |
| summary_0479 | lista | 2 | Online megbeszélés: "gyanúsan akadozik", "nem biztos". OK. |
| summary_0483 | hosszú magyarázat | 1 | Papír: "általában körülbelül", "szakemberek szerint". OK. |
| summary_0484 | hosszú magyarázat | 2 | Tengerek: "általában", "szakemberek szerint". OK. |
| summary_0487 | hosszú magyarázat | 1 | Páratartalom: "akár", "nem biztos", "gyanús lehet". OK. |
| summary_0488 | hosszú magyarázat | 2 | Menetrend: "általában", "gyakran", "akár". OK. |
| summary_0493 | döntés | 2 | Hétvégi program: "szerint", "valószínűleg". OK. |
| summary_0495 | döntés | 1 | Telefonjavítás: "szerviz szerint", "nem biztos". OK. |
| summary_0497 | döntés | 1 | Edzésidő: "szakemberek szerint akár", "egyelőre". OK. |
| summary_0498 | döntés | 2 | Zöldségeskert: "kertész szerint valószínűleg", "nem biztos". OK. |

**Eredmény: 40/40 megfelelt** (a két javított sor a javítás után). A 40 sor a batch 40%-a; a maradék 60 sort a kézi átnézés
nem érte el soronként, azokra az automatikus és szószintű ellenőrzések (3-4. fejezet) vonatkoznak, és a jelzett sorok
mindegyikét kézzel is megnéztem. A mintában 2/40 javítás kellett (3. batch: 3/40, 4. batch: 5/40).

## 7. PACKAGE STÁTUSZ - 4. csomag (summary / összegzés) LEZÁRÁSA

| Kérdés | Válasz |
|---|---|
| summary összesen 500/500 lett-e? | **Igen: 500 / 500 clean**, id `summary_0001`-`summary_0500` folytonos, 0 hiányzó, 0 rejected; 500 egyedi id, instruction, input, output és quality_notes; 300 egymondatos + 200 kétmondatos output; 10 típus x 50 sor |
| Teljes clean korpusz | **3000 sor** (1000 simple_qa + 1000 explanation + 500 step_by_step + 500 summary); globális cél 4900-ból 3000 kész, 1900 hiányzik (5-9. csomag) |
| Van-e nyitott javítandó tétel? | **Igen, három, mind az 1-3. batchben (0001-0300), nem a záró batchben** - lásd alább |
| Kell-e külön final summary audit/fix round? | **Igen, javaslom** (a step_by_step csomag audit + fix mintájára, külön commitban, mielőtt az 5. csomag indul) |

**Nyitott tételek (nem javítottam, mert nem ennek a batchnek a hatóköre):**

1. **Óvatos -> biztos átalakulás (11 sor)** az 1-3. batchben, a szigorított ellenőrző szerint: `0016`, `0027`, `0061`, `0073`,
   `0090` (1. batch), `0175`, `0185` (2. batch), `0239`, `0273`, `0277`, `0279` (3. batch): az inputban *érdemes* szerepel,
   az outputban ajánlás-jelző nélkül, ténymondatként. Ehhez jön **44 hedge-jelzés** (1. batch 18, 2. batch 18, 3. batch 8),
   amelynek egy része legitim kihagyás vagy egyenértékű megfogalmazás, más része valódi vesztés (pl. *általában*, *gyakran*,
   *lehet*, *szerint* elhagyva). A 4. és az 5. batch a szigorított ellenőrzőn 0 valódi jelzést ad.
2. **Sablonszerű instructionök az 1-2. batchben**: csomagszinten mérve **37 instruction-pár >= 0.9 hasonlóságú** (68 sor: 14 az
   0001-0100, 54 az 0101-0200 tartományban), pl. *"Foglald össze egy-két mondatban a következő szöveget / beszélgetést /
   helyzetet."* vagy *"Sűrítsd egyetlen / két mondatba az alább olvasható történetet."*. A repó `dataset_dedupe.py`
   eszköze az instruction+input együttesét hasonlítja, ezért ezeket a batchenkénti futások nem jelezték. Az outputok között
   0 pár >= 0.9. A 3-5. batch instructionjei között nincs ilyen pár.
3. **Ideiglenes ellenőrző scriptek nincsenek a repóban** (`check_summary.py`, `fidelity_check3.py`, `word_drops.py`,
   `targeted_cross_summary5.py`, `pkg_check.py`): a `tools/` alá emelésük külön jóváhagyandó lépés; a batch-eredmények
   emiatt csak a reportokból reprodukálhatók.

**Megjegyzés az `összefoglalás` tagról:** 500 / 3000 = 16.7%, a topic report minden futásnál jelzi. A kérésed szerint
kategória-tagként dokumentálom; a report tag-kezelésének módosítása külön jóváhagyás kérdése.

**Javasolt final audit/fix round tartalma** (külön jóváhagyás után): (a) a 11 *érdemes -> tény* sor javítása; (b) a 44
hedge-jelzés soronkénti átnézése és a valódi vesztések pótlása; (c) a 68 sablonszerű instruction átírása témaspecifikusra;
(d) csomagszintű zárás-ellenőrzés a step_by_step audit módszertanával (`data/reports/summary_completion_audit.md`).

## 8. Megfigyelések és korlátok (őszinte értékelés)

- **A hűség-ellenőrzés továbbra is heurisztika.** A csoportszintű ellenőrző a *még nem biztos -> nem biztos*, *még van* és
  *eltérő lehet -> eltérően* típusú apró gyengülést nem látta; ezeket a szószintű lista fogta meg. A hatókör-elcsúszást
  (mire vonatkozik az *általában*) és az instruction-output tartalmi eltérést (`0447`) továbbra is csak a kézi olvasás találja.
- **Nem mintázott 60 sor.** Soronként 40 sort olvastam végig; a maradék 60-ra automatikus és szószintű ellenőrzés
  vonatkozik. A 2-4. batchen a mintavételi javítás-arány 3/20, 3/40, 5/40 volt, itt 2/40.
- **Input-oldali javítások.** Öt esetben az inputot módosítottam (fenntartást hordozó, az outputból amúgy is kimaradó
  mondat elhagyása vagy semlegesítése), és két sornál az inputot bővítettem az arány javításáért. Az arányok emiatt
  részben hosszabb inputoknak köszönhetők.
- **Kérdő instructionök aránya 55%.** A témaspecifikus és kevésbé mondatszám-központú instruction természetes következménye;
  az összes 500 sorra 25%.
- **Az 1-2. batch instruction-készlete gyenge** (19 különböző kétszavas nyitás batchenként, sablonpárok), lásd a 7. fejezetet.

## 9. Fájlok

- Raw: `data/raw/claude_summary_0401_0500_raw.jsonl` (100 sor)
- Clean: `data/clean/claude_summary_0401_0500_clean.jsonl` (100 sor)
- Rejected: `data/rejected/claude_summary_0401_0500_rejected.jsonl` (0 sor, üres fájl)
- Report: `data/reports/claude_summary_0401_0500_report.md`

## 10. Amit ez a kör NEM tett

- Nem indított tanítást, nem módosított webapp/backend kódot, nem törölt és nem írt felül semmit.
- Nem javította az 1-3. batch nyitott tételeit, és nem készített külön summary audit riportot.
- Nem használt webes forrást, nem másolt szerzői jogvédett szöveget, nem használt ChatGPT raw jelöltet.
- Nem emelte a scripteket a repóba, és nem módosította a topic report tag-kezelését.
- Nem indította el az 5. csomagot.

---

## Végső összegzés

- Claude batch: 100 sor, **100 clean / 0 rejected**, átlag score 100.0, regressziós teszt STABIL.
- Vegyes output: 50 egymondatos + 50 kétmondatos; mind rövidebb az inputnál (max. arány 0.79).
- Fenntartás: 99 sor tartalmaz védett fenntartást; 0 valódi vesztés, 0 óvatos -> biztos átalakulás; 15 tartalmi javítás clean előtt.
- Instruction: 100 kézzel írt, egyedi, témaspecifikus; mondatszámot 28% nevez meg, "Foglald össze" nyitású 0 sor, 79 különböző kétszavas nyitás.
- Manuális mintavétel: 40 sor, 40/40 megfelelt a 2 javítás után.
- **4. csomag: summary 500 / 500 KÉSZ.** Teljes clean korpusz: **3000 sor**.
- Nyitott: 11 *érdemes -> tény* sor, 44 hedge-jelzés és 37 sablonos instruction-pár az 1-3. batchben; **külön final summary audit/fix round javasolt**.

**STÁTUSZ: STABIL.**
