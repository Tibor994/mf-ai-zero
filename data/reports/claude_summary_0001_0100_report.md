# Első FELÜGYELT summary batch - summary 0001-0100

Ez a 4. csomag (Összegzés példa, cél: 500 clean sor) **első 100 sora**. A batch közvetlenül
Claude-generált (a csomag indításakor nem volt ChatGPT raw candidate), és a teljes pipeline-on átment.

## 0. A csomag szabályai és a batch felépítése

- `category`: `summary`, `source`: `synthetic_claude`, `input`: mindig magyar szöveg, amit össze kell
  foglalni; `output`: az input rövid, pontos összegzése, új tény nélkül.
- **Csak kitalált, általános tartalom**: nincs valós személy, valós magánadat, webes forrásból vett
  vagy szerzői jogvédett szöveg, nincs MF-AI/Nexora-projekttény, nincs veszélyes tanács, és nincs biztos
  orvosi/jogi/pénzügyi állítás (az ügyintézési és biztosítási szövegek óvatosan, "általában"
  megfogalmazással szerepelnek, és az output is megtartja ezt a fenntartást). Az egyetlen név-jellegű elem
  földrajzi vagy történelmi köznév (Duna, Budapest, Atlanti-óceán, Gutenberg).
- 10 tartalmi típus x 10 sor:

| ID tartomány | Típus | Címke |
|---|---|---|
| 0001-0010 | hétköznapi történet | `hétköznapi történet` |
| 0011-0020 | tanulási szöveg | `tanulási szöveg` |
| 0021-0030 | projektjegyzet | `projektjegyzet` |
| 0031-0040 | ügyintézés | `ügyintézés` |
| 0041-0050 | technikai magyarázat | `technikai magyarázat` |
| 0051-0060 | rövid cikk (kitalált helyi hír) | `rövid cikk` |
| 0061-0070 | beszélgetésrészlet (A/B vagy szerepjelölés, név nélkül) | `beszélgetés` |
| 0071-0080 | lista összefoglalása | `lista` |
| 0081-0090 | hosszabb magyarázat rövidítése | `hosszabb magyarázat` |
| 0091-0100 | döntési helyzet | `döntési helyzet` |

- `tags` = `["magyar", "összefoglalás", <tartalmi típus>, <téma>]` - stabil belső, magyar címkelista.
- `difficulty`: az input szószáma alapján (leghosszabb 10 = `hard`, következő 30 = `medium`, a többi `easy`).
- `quality_notes`: soronként egyedi, konkrét leírás arról, mi került az összegzésbe és mi maradt ki.

## 1. Számok

| Mérőszám | Érték |
|---|---|
| Raw sorok | 100 |
| Schema validáció (`dataset_validate.py`) | 100 / 100 valid |
| Batchen belüli dedupe (id / instruction+input / output, 0.9) | 0 / 0 / 0 |
| Kereszt-dedupe a 2500 meglévő clean sor ellen (id / instruction / output, >= 0.9) | 0 / 0 / 0 |
| **Végleges clean** | **100** |
| **Rejected** | **0** |
| Átlag quality_score | **100.0 / 100** |
| Difficulty | easy 60, medium 30, hard 10 |
| Egyedi instruction / input / output / quality_notes | 100 / 100 / 100 / 100 |
| Input szószám (min / medián / max) | 26 / 40 / 66 |
| Output szószám (min / medián / max) | 13 / 26 / 36 |
| Legmagasabb output/input arány | 0.82 (nincs sor 0.85 fölött, nincs sor, ahol az output >= input) |
| Szó szerinti másolás (6 szavas egyezés az inputtal, max) | 0.29 (nincs 0.5 fölötti) |
| Identity bleed / saját projekt említés / URL, e-mail | 0 / 0 / 0 |
| Számjegy a szövegekben | 0 (a számok betűvel) |
| Topic report (2600 soros korpusz) | legmagasabb tag `fizika` 4.4%, az `összefoglalás` 3.8%; túlreprezentált (8%) tag nincs |
| Teljes clean korpusz | 2600 sor, 2600 egyedi id (1000 simple_qa, 1000 explanation, 500 step_by_step, 100 summary) |

## 2. Ellenőrzési lépések (a kért 11 lépés szerint)

1. **Generálás külön batch-ként**: 100 sor 5 részben (20-20), külön generátor-szkripttel.
2. **Schema**: `dataset_validate.py` 100/100; saját mezőellenőrzés: 9 kötelező mező, `category`,
   `source`, `difficulty` érvényes, nem üres `input`/`output`, `tags` a `magyar` és `összefoglalás`
   címkével kezdődik, nincs számtartomány a `quality_notes`-ban (a validator ezt telefonszámnak olvassa).
3. **Magyar nyelv**: automatikus heurisztikák (ékezetes karakterek, angol szavak, kódolási hiba,
   egyenes idézőjel, dupla szóköz, névelő-hiba, szóismétlés). Négy jelzés (`0008` "az nem", `0046`
   "az SSD", `0062` "Az jó") **helyes magyar** (mutató névmás, illetve az "SSD" kiejtése miatt "az"), tehát
   hamis pozitívak.
4. **Input-output hűség**: (a) az output tartalmi szótöveinek összevetése az inputtal - a 300 hiányzó tövet
   átnéztem: ragozási vagy körülíró különbség (*bírja/tovább*, *hétvégén/hét végén*, *késői/késett*), nem új
   tény; a legtöbb eltérést mutató 3 sort (`0023`, `0053`, `0089`) kézzel újraolvastam; (b) az outputban
   szereplő számnevek mind szerepelnek az inputban; (c) az output nem tartalmaz új számjegyet vagy nevet;
   (d) kézi ellenőrzés a 20 soros mintán és minden szerkesztés közben javított soron.
5. **Batch dedupe**: id 0, instruction+input 0, output 0. A dedupe az `instruction || input` párt
   hasonlítja, ezért a hasonló feladat-megfogalmazás nem ad hamis találatot.
6. **Teljes korpuszos kereszt-dedupe**: az új 100 sor a 2500 meglévő clean sor ellen (minden találatot
   vizsgálva, `quick_ratio` előszűréssel, ami matematikailag ekvivalens a teljes `ratio()`-val): **0
   találat**. (A teljes N×N futtatás a 2500+ soros korpuszon már nem praktikus, lásd a progress-fájl
   "Tanulság a hátralévő csomagokra" jegyzetét; a célzott új-vs-korpusz módszer az alapértelmezett.)
7. **Safety/firewall**: identity bleed 0; saját projekt/modellnév 0; URL, e-mail 0; kizárt témák
   (`wifi`, `vpn`, `cookie`, `ajándék`, `bocsánat`) 0. Kulcsszó-találatok mind hétköznapiak: `gyógyszer` (0009, "gyógyszertár"),
   `áram` (0047 elektromos áram; 0084 tengeri *áramlat*), `betegség` (0055, fák betegségei), `szikr` (0044,
   mikrohullámú sütő fém), `tűz` (0078, tűzgyújtási tilalom), `kölcsön` (0003/0004/0009), `biztosít`/
   `szerződés` (0039, óvatos, "általában"/"szerződéstől függően" megfogalmazással; 0084 "biztosít enyhébb
   telet"). Biztos állítás, ígéret vagy veszélyes útmutatás nincs.
8. **Quality score**: 100.0 / 100, minden sor 100.
9. **Manuális mintavétel**: 20 sor (mind a 10 típusból 2), input és output egymás mellett
   (3. fejezet).
10. **Clean/rejected/report**: clean 100, rejected 0 (üres fájl), ez a report.
11. **Progress**: a `dataset_autopilot_progress.md` frissítve (4. csomag: 100 / 500).

### Önkorrekciók a felülvizsgálat során (mind clean előtt)

- **Tömörség**: hat lista-sor (`0071`-`0074`, `0077`, `0079`) outputja hosszabb vagy egyenlő volt az inputnál,
  ez nem összegzés. A listák inputját részletesebbé tettem, az outputot tömörítettem; azóta nincs sor,
  ahol az output >= input, és a legmagasabb arány 0.82.
- **Hűség**: `0055` (a gazdák permetezése nem *következménye* volt a betegségeknek az inputban),
  `0087` ("leghatékonyabb" erősebb volt, mint az input "érdemes"), `0002` (félreérthető "késő órája"),
  `0007` (az input feltételes "ha a hét végéig nem működik" állítása), `0065` és `0067` (tanács helyett
  megtörténtként írt esemény) - mind javítva.
- **Sablonosság**: eleinte csak 49 különböző instruction-szöveg volt a 100 sorra; típusonként 10
  megfogalmazásra bővítettem, most 100 / 100 egyedi.
- **Instruction-output konzisztencia**: több instruction "két mondatban" / "három mondatban" összegzést
  kért, az output viszont egy mondat volt. A szigorú mondatszámot előíró megfogalmazásokat semlegesre
  cseréltem, és az ellenőrző script mostantól vizsgálja: 0 ellentmondás. A `0027` (kerékpártúra-tájékoztató)
  "Mi kész, és mi van hátra?" kérése státuszjegyzetre való volt, ezt is kicseréltem.
- **Duplikált instruction** két típus között ("egy-két mondatban a következő szöveget") - megszüntetve.

## 3. Manuális mintavétel (20 sor, mind a 10 típusból 2)

| id | Típus | Értékelés |
|---|---|---|
| summary_0002 | történet | Buszlekésés: minden fő esemény megvan, új tény nincs. OK. |
| summary_0008 | történet | Kacsaetetés: a tanács és az ígéret megmaradt. OK. |
| summary_0013 | tanulás | Ragozó nyelv: definíció és következmény, a példák nélkül. OK. |
| summary_0019 | tanulás | Súrlódás: két hatás megtartva, a nagyságot befolyásoló tényezők kimaradtak. OK. |
| summary_0023 | projekt | Konyhafelújítás: kész és hátralévő lépések, költségkeret. OK. |
| summary_0027 | projekt | Kerékpártúra: létszám, táv, figyelmeztetés, elmaradás. OK (a kérés megfogalmazása azóta cserélve). |
| summary_0033 | ügyintézés | Számlareklamáció: "általában harminc napon belül" fenntartás megtartva. OK. |
| summary_0039 | ügyintézés | Biztosítói kárbejelentés: "általában" és "szerződéstől függően" megőrizve. OK. |
| summary_0044 | technika | Mikrohullámú sütő: mechanizmus és figyelmeztetés. OK (a kérés mondatszáma azóta cserélve). |
| summary_0047 | technika | LED: hőtermelés, energia, színhőmérséklet. OK. |
| summary_0053 | cikk | Piaci szabály: két ellentétes árusi vélemény kiegyensúlyozva. OK. |
| summary_0057 | cikk | Uszoda: nyitvatartás, indok, tanfolyam. OK. |
| summary_0065 | beszélgetés | Házi feladat: a kérés és a tanács külön kezelve. OK. |
| summary_0068 | beszélgetés | Nyaralás: két eltérő preferencia, halasztott döntés. OK. |
| summary_0073 | lista | Túrafelszerelés: mind a nyolc tétel megmaradt, magyarázat nélkül. OK. |
| summary_0078 | lista | Kirándulási szabályok: mind a négy szabály. OK. |
| summary_0084 | hosszú magyarázat | Áramlatok: a bizonytalanság ("kutatók még vizsgálják") megtartva. OK. |
| summary_0089 | hosszú magyarázat | Városi kertészkedés: lehetőség és öntözési többletigény. OK. |
| summary_0093 | döntés | Költözés és családi ebéd: a kompromisszum megvan. OK. |
| summary_0099 | döntés | Műhelybérlet vs. otthoni munka: szempontok és egyhónapos próba. OK. |

**Eredmény: 20/20 megfelelt.**

## 4. Megfigyelések és korlátok (őszinte értékelés)

- **Az output mind egy mondat** (100 / 100; pontosvesszővel tagolva). Ez a beszélgetés- és
  döntés-típusnál néha zsúfolt. A következő batchekben érdemes 2 mondatos outputokat is bevezetni
  a változatosság és a tanítási jel gazdagsága miatt.
- **A hűség-ellenőrzés részben heurisztika**: a szótő-összevetés és a számnév-ellenőrzés csak az új
  tényt jelzi, a jelentésbeli torzítást nem; azt a kézi átnézés (20 mintasor + a jelzett és a szerkesztés
  közben javított sorok) fogta meg. Az összes 100 sor kézi újraolvasása nem történt meg ebben a körben.
- **Az instruction-megfogalmazás közel sablonos** ("Foglald össze röviden ...") - ez a feladatfajta
  természetéből adódik; a batchen belül mind a 100 egyedi. A teljes 500 soros csomagban az egyediséget
  a következő batcheknél új megfogalmazások bevezetésével kell tartani.
- **Az ellenőrző script nem része a repónak.** A hűség/tömörség/mondatszám-ellenőrzést végző
  `check_summary.py` ideiglenes munkakönyvtárban készült (a repo `tools/` mappáját ez a batch nem
  módosította). Ha a következő batch-ekhez tartós eszköz kell, a `tools/` alá emelése külön,
  jóváhagyandó lépés.
- **A beszélgetés-típus szerepjelölése** (A/B, Vásárló/Eladó) szándékosan névtelen, hogy ne legyen
  személyes adat.

## 5. Fájlok

- Raw: `data/raw/claude_summary_0001_0100_raw.jsonl` (100 sor)
- Clean: `data/clean/claude_summary_0001_0100_clean.jsonl` (100 sor)
- Rejected: `data/rejected/claude_summary_0001_0100_rejected.jsonl` (0 sor, üres fájl)
- Report: `data/reports/claude_summary_0001_0100_report.md`

## 6. Regressziós teszt

`tests/test_v1_7_4_dataset_foundation.py` - minden teszt sikeres, **STÁTUSZ: STABIL**.

## 7. Amit ez a kör NEM tett

- Nem indított tanítást, nem módosított webapp/backend kódot, nem törölt és nem írt felül semmit.
- Nem készítette el a summary 0101-0500 sorait (a következő batch-ek külön jóváhagyásra várnak).
- Nem használt webes forrást, nem másolt szerzői jogvédett szöveget, nem használt ChatGPT raw jelöltet.

---

## Végső összegzés

- Claude batch: 100 sor, **100 clean / 0 rejected**, átlag score 100.0.
- Összes clean summary: **100 / 500**; hiányzik: **400**.
- Teljes clean korpusz: **2600 sor** (1000 simple_qa + 1000 explanation + 500 step_by_step + 100 summary).

**STÁTUSZ: STABIL.**
