# Második FELÜGYELT summary batch - summary 0101-0200

A 4. csomag (Összegzés példa, cél: 500 clean sor) **második 100 sora**. A batch közvetlenül
Claude-generált, kitalált, általános magyar tartalommal (nincs valós személy/magánadat, webes forrás,
szerzői jogvédett szöveg, MF-AI-projekttény, veszélyes tanács vagy biztos orvosi/jogi/pénzügyi állítás).
Az ügyintézési és biztosítási szövegek "általában" fenntartással szerepelnek, és az output megtartja ezt.

## 0. Az 1. batch tapasztalatából adódó új követelmények és teljesülésük

| Követelmény | Teljesülés |
|---|---|
| Vegyesen 1 és 2 mondatos output | **50 egymondatos / 50 kétmondatos**, minden blokkban 4-6 kétmondatos |
| A 2 mondatos output is tömör | kétmondatos: max. 42 szó, átlagos output/input arány 0.62, max. 0.77 |
| Ne legyen hosszabb az inputnál | 0 sor, ahol az output >= input; legmagasabb arány 0.77 (nincs 0.85 fölött) |
| Ne adjon hozzá új tényt | nincs új szám, név; kézi hűség-ellenőrzés (lásd 2. és 3. fejezet) |
| Ne torzítsa az input jelentését | 3 mintában talált torzítást javítottam clean előtt (lásd 2. fejezet) |
| Ne legyen sablonos instruction | 100 / 100 egyedi, 29 különböző mondatváz, egy váz legfeljebb 7 alkalommal; a mondatszám-előírás (egy/két mondat) mindig egyezik az outputtal |
| `quality_notes` egyedi és konkrét | 100 / 100 egyedi, hossz 54-130 karakter, nincs ismétlődő nyitás, a megemlített mondatszám egyezik az outputtal |

## 1. Felépítés és számok

10 tartalmi típus x 10 sor (az 1. batch témáitól eltérő témákkal):

| ID tartomány | Típus | Címke | Kétmondatos sor |
|---|---|---|---|
| 0101-0110 | hétköznapi történet | `hétköznapi történet` | 5 |
| 0111-0120 | tanulási szöveg | `tanulási szöveg` | 4 |
| 0121-0130 | projektjegyzet | `projektjegyzet` | 5 |
| 0131-0140 | ügyintézés | `ügyintézés` | 5 |
| 0141-0150 | technikai magyarázat | `technikai magyarázat` | 5 |
| 0151-0160 | rövid cikk (kitalált helyi hír) | `rövid cikk` | 5 |
| 0161-0170 | beszélgetésrészlet (A/B, szerepjelölés, név nélkül) | `beszélgetés` | 5 |
| 0171-0180 | lista összefoglalása | `lista` | 5 |
| 0181-0190 | hosszabb magyarázat rövidítése | `hosszabb magyarázat` | 5 |
| 0191-0200 | döntési helyzet | `döntési helyzet` | 6 |

`tags` = `["magyar", "összefoglalás", <tartalmi típus>, <téma>]`. `difficulty` az input szószáma szerint
(leghosszabb 10 = hard, következő 30 = medium, a többi easy).

| Mérőszám | Érték |
|---|---|
| Raw sorok | 100 |
| Schema validáció (`dataset_validate.py`) | 100 / 100 valid |
| Batchen belüli dedupe (id / instruction+input / output, 0.9) | 0 / 0 / 0 |
| Kereszt-dedupe a 2600 meglévő clean sor ellen (id / instruction / output, >= 0.9, minden találat) | 0 / 0 / 0 |
| **Végleges clean** | **100** |
| **Rejected** | **0** |
| Átlag quality_score | **100.0 / 100** |
| Difficulty | easy 60, medium 30, hard 10 |
| Egyedi instruction / input / output / quality_notes | 100 / 100 / 100 / 100 |
| Input szószám (min / medián / max) | 24 / 42 / 66 |
| Output szószám (min / medián / max) | 12 / 26 / 42 |
| Egymondatos outputok: sor / max. szó / output-input arány (átl., max) | 50 / 30 / 0.59, 0.77 |
| Kétmondatos outputok: sor / max. szó / output-input arány (átl., max) | 50 / 42 / 0.62, 0.77 |
| Szó szerinti másolás (6 szavas egyezés az inputtal, max) | 0.32 (nincs 0.5 fölötti) |
| Identity bleed / saját projekt említés / URL, e-mail | 0 / 0 / 0 |
| Számjegy a szövegekben | 0 (a számok betűvel) |
| Topic report (2700 soros korpusz) | legmagasabb tag az `összefoglalás` 7.4%, ezt követi a `fizika` 4.3%; túlreprezentált (8%) téma-tag nincs |
| Teljes clean korpusz | 2700 sor, 2700 egyedi id (1000 simple_qa, 1000 explanation, 500 step_by_step, 200 summary) |

## 2. Ellenőrzési lépések (a kért pipeline szerint)

1. **Generálás**: 100 sor 5 részben (20-20), külön generátor-szkripttel; az instruction a kimenet
   mondatszámához igazodik, és a script minden instructiont összevet a meglévő korpusszal (nincs egyezés).
2. **Schema**: `dataset_validate.py` 100/100; saját mezőellenőrzés (9 kötelező mező, `category`, `source`,
   `difficulty`, nem üres `input`/`output`, `tags` fejléc, nincs számtartomány a `quality_notes`-ban).
3. **Summary forma és magyar nyelv**: az output nem üres, ponttal végződik, 1-2 mondatos; ékezetes
   karakterek, angol szavak, kódolási hiba, egyenes idézőjel, dupla szóköz, névelő-hiba, szóismétlés
   heurisztikák. Hét jelzés (az inputokban: *az volt*, *az pedig*, *az már*, *Az jó*, *az jól*, *az legyen*) **helyes
   magyar** (mutató névmás), tehát hamis pozitívak.
4. **Input-output hűség**: szótő-összevetés (a 4 legtöbb eltérést mutató sort - `0169`, `0173`, `0185`, `0191` -
   kézzel újraolvastam), számnév-ellenőrzés (az outputban lévő számnevek mind szerepelnek az inputban; az 5
   jelzés ragozási különbség: *két hétben/hétig*, *két rétegben/kétrétegű*, *ketten/két*, *első hetén/héten*,
   *egyik-másik/két módszer*), új szám/név hiánya, és kézi ellenőrzés a 20 soros mintán.
5. **Tömörség**: output < input minden sorban; arányok és szószámok az 1. fejezetben.
6. **Batch dedupe**: id 0, instruction+input 0, output 0.
7. **Kereszt-dedupe teljes korpusz ellen**: az új 100 sor a 2600 meglévő clean sorral szemben (minden
   találatot vizsgálva, `quick_ratio` előszűréssel, ami matematikailag ekvivalens a teljes `ratio()`-val):
   0 találat. (A teljes N×N futás a 2600+ soros korpuszon nem praktikus; a célzott új-vs-korpusz módszer
   az alapértelmezett.)
8. **Safety/firewall**: identity bleed 0; saját projekt/modellnév 0; URL, e-mail 0; kizárt témák 0. A
   kulcsszó-találatok hétköznapiak vagy biztonságpozitívak: `betegség`/`orvos` (0133 orvosi igazolás mint
   *csatolható* irat; 0164 iskolai hiányzás), `biztosít` (0150 biztosíték), `áram` (0141/0142/0150/0182
   elektromos áram), `vegyszer` (0138: veszélyes hulladék kizárása lomtalanításból), `biztosan` (0108: nem
   szedtek gombát, mert nem ismerték biztosan), `mindig` (0150 ugyanolyan biztosítékot kell betenni),
   `kölcsön` (kölcsönkapott/kölcsönzött tárgyak). Biztos állítás, ígéret vagy veszélyes útmutatás nincs.
9. **Quality score**: 100.0 / 100, minden sor 100.
10. **Manuális mintavétel**: 20 sor (mind a 10 típusból 2), input és output egymás mellett (3. fejezet).
11. **Clean/rejected/report**: clean 100, rejected 0 (üres fájl), ez a report; **progress** frissítve.

### Önkorrekciók a felülvizsgálat során (mind clean előtt)

- **Szó szerinti másolás**: a `0129` output 6 szavas egyezése 0.53 volt (az 1. batchben a max. 0.29) - az
  input első mondatát követte; átfogalmaztam. Öt sor (`0121`, `0129`, `0133`, `0169`, `0171`) output/input
  aránya 0.78-0.81 volt, ezeket szorosabbra fogalmaztam (azóta max. 0.77).
- **Jelentéstorzítás/új tény** (kézi mintavételből): `0124` ("felesleges holmi került ki" -> "kidobtak": az
  input nem mondja, hogy kidobták), `0133` (az orvosi igazolás *csatolható*, nem kötelező), `0153` ("elérheti a
  harmincöt fokot" -> a lehetőség jellegét megtartva: "akár harmincöt fokos hőség is lehet").
- **Kihagyott fő lényeg**: `0191` - a telefonjavítás hátránya (a szerelő szerint az akkumulátor hamar
  lemerülhet) hiányzott az outputból; pótoltam.
- **Szerepjelölés félreolvashatósága**: `0161` és `0162` outputja "A ..."-val kezdődött, ami a szerepjelölést
  (A) határozott névelőnek olvashatóvá tette; átfogalmaztam ("A és B ...", "Az egyik szomszéd ...").
- **Írás közben javított hibák**: `0119` (elliptikus mondat), `0152` (tíz kerékpáros kölcsönző -> tíz
  kerékpárral), `0178` (érdemes vinni), `0160` (input által nem állított ok-okozati kapcsolat elhagyva),
  `0199` (kétmondatosra bontva az olvashatóságért), `0142` ("érdemes" fenntartás megtartva).
- **Instruction-sablonosság**: az első generálás ~14 mondatvázból dolgozott (20 sor azonos szerkezettel); a vázakat
  bővítettem, a kiosztást körforgásra cseréltem (29 használt váz, max. 7 ismétlés). Két megfogalmazást
  átírtam: "Mit közöl az alább közölt cikk?" (szóismétlés) és "Mit állít az itt olvasható lista?" (egy lista nem
  *állít*), az utóbbi váz most "... fő mondanivalóját".
- **Mérési műtermék, nem adathiba**: egy közbenső kereszt-dedupe-futás id-ütközést és 1.0 hasonlóságot
  jelzett, mert a batch már létrehozott clean másolata is a korpuszba esett (a script saját magával
  hasonlított). A scripteket úgy javítottam, hogy a batch saját fájlját kizárják; a végleges futás 0 találat.
- **Ellenőrző script**: a mondatszám-konzisztencia vizsgálat kiterjesztve az "egyetlen mondat", "egymondatos"
  és "kétmondatos" alakokra.

## 3. Manuális mintavétel (20 sor, mind a 10 típusból 2)

Input és output egymás mellett elolvasva; a `0124`, `0133`, `0153` sort a mintavétel után javítottam és
újraolvastam. Az instructionöket a végleges generálás után mind a 100 sorra átolvastam.

| id | Típus | Mondat | Értékelés |
|---|---|---|---|
| summary_0101 | történet | 1 | Kulcskeresés: keresés, lelőhely, új szokás. OK. |
| summary_0108 | történet | 2 | Gombanézegetés: a nem szedés indoka és az utólagos azonosítás. OK. |
| summary_0113 | tanulás | 1 | Negatív számok: definíció, példa, számegyenes. OK. |
| summary_0116 | tanulás | 2 | Időzónák: ok és következmény két mondatban. OK. |
| summary_0121 | projekt | 1 | Ballagási dekoráció: kész és hátralévő munkák (tömörítve). OK. |
| summary_0124 | projekt | 2 | Padlásrendezés: a kész kipakolás és a nyitott döntés, határidővel (javított). OK. |
| summary_0133 | ügyintézés | 1 | Hiányzásigazolás: az orvosi igazolás csatolhatósága megőrizve (javított). OK. |
| summary_0136 | ügyintézés | 2 | Postai átirányítás: fogalom, kérés, díj, meghosszabbítás. OK. |
| summary_0141 | technika | 1 | Érintőképernyő: elv és a kesztyű korlátja. OK. |
| summary_0146 | technika | 2 | Hőszigetelés: a légzsák-elv, a vastagság és a nyílászárók. OK. |
| summary_0153 | cikk | 1 | Hőségriasztás: "akár" hedge és a hatósági kérések (javított). OK. |
| summary_0156 | cikk | 2 | Új buszjárat: előny, aggodalom, próbaidő. OK. |
| summary_0161 | beszélgetés | 1 | Közös ebéd: szavazás és rendelési idő; a szerepek egyértelműek (javított). OK. |
| summary_0164 | beszélgetés | 2 | Dolgozat-haladék: ok, határidő és elfogadás. OK. |
| summary_0171 | lista | 1 | Hétvégi teendők napok szerint. OK. |
| summary_0178 | lista | 2 | Piknik: csoportosított tartalom és a napvédelem feltételes tétele. OK. |
| summary_0181 | hosszú magyarázat | 1 | Szelektív gyűjtés: a fogalom és a kiöblítés indoka. OK. |
| summary_0188 | hosszú magyarázat | 2 | Szobanövény-öntözés: ujjas próba, gyakoriság, lyukas cserép. OK. |
| summary_0193 | döntés | 1 | Busz vagy kerékpár: az előnyök-hátrányok és a vegyes terv. OK. |
| summary_0196 | döntés | 2 | Város vagy falu: két opció szempontjai és a hétvégi próba. OK. |

**Eredmény: 20/20 megfelelt** (a három javított sor a javítás után).

## 4. Megfigyelések és korlátok (őszinte értékelés)

- **Az instruction még mindig mondatváz-alapú.** 100 / 100 egyedi és 29 különböző szerkezet van, de a
  szerkezetek kézzel írt vázakból épülnek (plusz 6 határozó és 2 főnévalak). A 3-5. batchhez érdemes
  további, kézzel írt megfogalmazásokat hozzáadni; a "teljes mértékben nem sablonos" célt ez a batch csak
  közelíti.
- **A hűség-ellenőrzés továbbra is részben heurisztika**: az új tényt jelzi, a jelentésbeli torzítást a
  kézi átnézés fogja meg (20 mintasor + a jelzett és javított sorok). Az összes 100 sor soronkénti
  újraolvasása nem történt meg ebben a körben; a mintavétel 3 torzítást talált 20 sorból, ami arra utal,
  hogy a nem mintázott 80 sorban is maradhat kisebb pontatlanság. A 3-5. batchnél érdemes a mintát növelni
  (30-40 sorra) vagy teljes kézi átolvasást végezni.
- **Az `összefoglalás` tag aránya 7.4%** a teljes korpuszban, a 8% küszöb alatt, de a következő batchnél
  átlépi (300 / 2800 = 10.7%). Ez a csomagot jelölő, kategória-jellegű tag (mint a `magyar`), nem
  témaszaturáció, de a topic report figyelmeztetni fog rá; a tag kezelése (kategória-tagként való
  kihagyás a jelentésből) külön, jóváhagyandó lépés.
- **Az ellenőrző script (`check_summary.py`) továbbra sem része a repónak** (ideiglenes munkakönyvtár); a
  `tools/` alá emelése külön jóváhagyás kérdése.
- Az 1. batch tanulsága teljesült: a mondatszám vegyes, a beszélgetés- és döntés-típus kevésbé zsúfolt.

## 5. Fájlok

- Raw: `data/raw/claude_summary_0101_0200_raw.jsonl` (100 sor)
- Clean: `data/clean/claude_summary_0101_0200_clean.jsonl` (100 sor)
- Rejected: `data/rejected/claude_summary_0101_0200_rejected.jsonl` (0 sor, üres fájl)
- Report: `data/reports/claude_summary_0101_0200_report.md`

## 6. Regressziós teszt

`tests/test_v1_7_4_dataset_foundation.py` - minden teszt sikeres, **STÁTUSZ: STABIL**.

## 7. Amit ez a kör NEM tett

- Nem indított tanítást, nem módosított webapp/backend kódot, nem törölt és nem írt felül semmit.
- Nem készítette el a summary 0201-0500 sorait (külön jóváhagyásra várnak).
- Nem használt webes forrást, nem másolt szerzői jogvédett szöveget, nem használt ChatGPT raw jelöltet.
- Nem emelte a `check_summary.py`-t a repóba, és nem módosította a topic report tag-kezelését.

---

## Végső összegzés

- Claude batch: 100 sor, **100 clean / 0 rejected**, átlag score 100.0.
- Vegyes output: 50 egymondatos + 50 kétmondatos; mind rövidebb az inputnál (max. arány 0.77).
- Összes clean summary: **200 / 500**; hiányzik: **300**.
- Teljes clean korpusz: **2700 sor** (1000 simple_qa + 1000 explanation + 500 step_by_step + 200 summary).

**STÁTUSZ: STABIL.**
