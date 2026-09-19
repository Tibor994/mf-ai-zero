# Ötödik, záró FELÜGYELT step_by_step batch - step_by_step 0401-0500

Ez a batch **lezárja a 3. csomagot (step_by_step): 500 / 500 clean**.

## 0. Miért Claude-generált a batch

A ChatGPT/Dispatch raw producer a négy próbálkozásából (0001-0100,
0101-0200, 0201-0300, 0301-0400) egyetlen clean sort sem adott
(4 x 100 elutasítva, részletek a korábbi batch-riportokban). A felhasználó
utasítására ez az utolsó batch **közvetlenül Claude-generált**, ChatGPT
raw candidate nélkül. Ugyanazon a teljes pipeline-on ment át, mint minden
korábbi batch.

- `category`: `step_by_step`, `source`: `synthetic_claude`.
- 100 db kézzel megírt, egyedi sor, 10 új témablokk x 10 sor. Egyik sem
  ismétli az előző négy Claude batch (0001-0400) témáit:
  lakásdekoráció és berendezés (0401-0410), számítógép mindennapi
  használata (0411-0420), szolgáltatások igénybevétele (0421-0430),
  külföldi utazás előkészítése (0431-0440), iratok és dokumentumok
  rendszerezése (0441-0450), olvasási szokás (0451-0460), társasjátékok és
  játékest (0461-0470), italkészítés otthon (0471-0480), gyerekekkel a
  mindennapokban (0481-0490), kézműves alkotás (0491-0500).

## 1. Számok

| Mérőszám | Érték |
|---|---|
| Raw sorok (Claude-generált) | 100 |
| Schema validáció (`dataset_validate.py`) | 100 / 100 valid |
| Batchen belüli dedupe (id / instruction / output, 0.9) | 0 / 0 / 0 |
| Kereszt-dedupe az eddigi 2400 clean sor ellen (id / instruction / output) | 0 / 0 / 0 |
| **Végleges clean** | **100** |
| **Rejected** | **0** |
| Átlag quality_score | **100.0 / 100** |
| Difficulty | easy: 63, medium: 28, hard: 9 |
| Különböző szöveg lépésenként (1..5. lépés, 100 sorból) | **100 / 100 / 100 / 100 / 100** |
| Egyedi instruction / quality_notes | 100 / 100 |
| Output hossz (karakter) | 199 - 412 |
| Identity bleed | 0 |
| Topic report (teljes 2500 soros korpusz) | legmagasabb tag `fizika` 4.5%; túlreprezentált tag (8%) nincs |
| Teljes clean korpusz | 2500 sor, 2500 egyedi id |

## 2. Ellenőrzési lépések

- **Schema**: 100/100.
- **Nyelvi/formátum**: minden output pontosan 5 számozott lépés
  ("1." ... "5."), "1."-gyel kezdődik, 100-700 karakter közötti, az
  instrukció tartalmazza a "lépés" szót, `input` üres string,
  `category` és `source` a megszabott: 100/100.
- **Minden lépés eltérő**: lépésenként 100/100/100/100/100 különböző szöveg
  (a ChatGPT 4. próbálkozásánál ez 100/14/14/1/1 volt). Nincs sablon
  4./5. lépés.
- **Batchen belüli dedupe**: id 0, instruction 0, output 0.
- **Kereszt-dedupe**: az új 100 sor mind az eddigi 2400 clean sorral
  összevetve (id + instruction||input + output, hasonlóság >= 0.9): **0
  találat**. Ez a célzott ellenőrzés a `dataset_dedupe.py` hasonlósági
  logikáját használja, de minden találatot megvizsgál (az eredeti csak az
  első találatnál áll meg, tehát ez szigorúbb). A `quick_ratio` /
  `real_quick_ratio` előszűrés csak felső korlátot alkalmaz, ezért az
  eredmény azonos egy teljes `ratio()` számítással.
  - **Megjegyzés az eljárásról (őszinte)**: a teljes 2500 x 2500-as
    N×N kereszt-dedupe futtatását elindítottam, de ~55 perc után sem
    fejeződött be (az O(n²) költség a korpusszal nő), ezért leállítottam.
    A teljes futás az új sorokon felül csak a **régi-régi** párokat vizsgálná
    újra, amelyeket a korábbi batch-ek kereszt-dedupe futásai már
    ellenőriztek (a 6 ismert hamis pozitív: 5 simple_qa pár és
    `step_by_step_0227`/`0229`). Az új batch-et érintő összes pár a célzott
    ellenőrzésben szerepelt.
- **Két módosított sor külön ellenőrzése**: a `0479` (max instruction
  hasonlóság 0.69, output 0.33) és a `0492` (0.76 / 0.28) a végső szöveggel
  is a korpusz többi sorától jól elkülönül.
- **Safety kulcsszó-átnézés**: minden találat hamis pozitív, kézzel
  ellenőrizve: a "kés" a *később / késő / készít* szavakban (0411, 0412,
  ... több sor), a "tűz" a *tűzz ki* igében (0500), az "orvos" az
  *orvoslására* szóban (0422, hétköznapi értelemben: helyzet megoldása), a
  "bank" a *bankodat* szóban (0432), a "gyógyszereket" csak a
  kézipoggyász-csomagolásnál (0437, semleges). Kizárt téma (`wifi`, `vpn`,
  `cookie`, `ajándék`, `bocsánat`) 0. Egyenes idézőjel a szövegekben 0;
  sorszám-tartomány a `quality_notes`-ban 0.
- **Önkorrekció a felülvizsgálat során** (mind clean előtt):
  - `0429`: nyelvtani hiba ("mennyi az felmondási idő" -> "mennyi a
    felmondási idő").
  - `0457`: értelmetlen 5. lépés kicserélve ("Használd a beépített
    keresőt, ha egy korábban olvasott részletet szeretnél megtalálni.").
  - `0492`: a papírhajó hajtogatása pontatlan volt (négyzet alakú
    lapból indult); javítva téglalap alakú lapra, a valódi menetnek
    megfelelően.
  - `0479`: a bodzaszörp áztatása "hűvös helyen" volt; élelmiszer-
    biztonsági okból "a hűtőben"-re javítva.
- **Biztonság-érzékeny sorok külön átnézve** (pénzügyi/jogi/egészségügyi
  szomszédos témák): `0433` (utasbiztosítás) általános szempontlista,
  konkrét termékajánlás vagy ígéret nélkül; `0447` (adózási iratok)
  gyűjtési rutint ír le, a végén szakemberhez irányít, adótanácsot nem
  ad; `0431` (úti okmányok) hivatalos forrás/ellenőrzés; `0486`
  (kisgyerek dührohama) általános nevelési tanács, nem klinikai;
  `0445` (iratmegsemmisítés) védi a személyes adatot; `0497` (mozaik)
  védőszemüveget és kesztyűt ír elő. Egyik sor sem tartalmaz veszélyes,
  személyes adatot kérő vagy jogi/orvosi/pénzügyi ígéretet tartalmazó
  útmutatást. Saját projekt/MF-AI tény: nincs kitalálva (0 sor).

## 3. Manuális mintavétel (20 sor, mind a 10 témablokkból 2)

Mindet a nyers fájlból újraolvasva, teljes szöveggel ellenőrizve.

| id | Értékelés |
|---|---|
| step_by_step_0402 | Színpaletta: próbafoltok, napszakok. OK. |
| step_by_step_0408 | Tükör: szemmagasság, biztonságos rögzítés tiplivel. OK. |
| step_by_step_0412 | PDF mentése. OK. |
| step_by_step_0417 | Védelem ellenőrzése: frissítés, vírusvédelem, átvizsgálás. OK. |
| step_by_step_0424 | Autóhiba leírása szerelőnek; írásos árajánlat. OK. |
| step_by_step_0429 | Előfizetés lemondása (javított változat). OK. |
| step_by_step_0433 | Utasbiztosítás: általános szempontok. OK. |
| step_by_step_0437 | Kézipoggyász: folyadékszabály, okmányok. OK. |
| step_by_step_0445 | Iratmegsemmisítés: adatvédelem. OK. |
| step_by_step_0447 | Adózási iratok: gyűjtés, szakemberhez irányít. OK. |
| step_by_step_0455 | Könyvklub indítása. OK. |
| step_by_step_0459 | Nehéz szöveg megértése. OK. |
| step_by_step_0464 | Sakkfelállítás: helyes (bástya, ló, futó, királynő a saját színén). OK. |
| step_by_step_0468 | Együttműködő játék, a csendesebbek bevonása. OK. |
| step_by_step_0473 | Házi limonádé. OK. |
| step_by_step_0479 | Szörpfőzés (javított: hűtőben áztatás, steril üveg). OK. |
| step_by_step_0486 | Kisgyerek dührohama: nyugodt, általános. OK. |
| step_by_step_0489 | Képernyőhasználati szabályok. OK. |
| step_by_step_0492 | Papírhajó (javított változat). OK. |
| step_by_step_0497 | Mozaik: védőfelszerelés említve. OK. |

**Eredmény: 20/20 megfelelt.**

## 4. Fájlok

- Claude raw: `data/raw/claude_step_by_step_0401_0500_raw.jsonl` (100 sor)
- Clean: `data/clean/claude_step_by_step_0401_0500_clean.jsonl` (100 sor)
- Rejected: `data/rejected/claude_step_by_step_0401_0500_rejected.jsonl` (0 sor, üres fájl)
- Riport: `data/reports/claude_step_by_step_0401_0500_report.md`

## 5. Regressziós teszt

`tests/test_v1_7_4_dataset_foundation.py` - minden teszt sikeres,
STÁTUSZ: STABIL.

## 6. Amit ez a kör NEM tett

- Nem indított tanítást, nem módosított webapp/backend kódot, nem törölt
  semmit, nem írt felül régi raw fájlt.
- Nem futtatta végig a teljes N×N kereszt-dedupe-ot (lásd 2. pont, leállítva
  ~55 perc után; helyette célzott új-vs-korpusz ellenőrzés).
- Nem készített külön step_by_step completion auditot (nem kérték), és nem
  kezdte el a 4. csomagot.

---

## Végső összegzés

- ChatGPT raw: ebben a batch-ben nem volt (közvetlenül Claude-generált).
- Claude batch: 100 sor, **100 clean / 0 rejected**.
- Összes step_by_step clean: **500 / 500**; hiányzik: **0**.
- Teljes clean korpusz: **2500 sor** (1000 simple_qa + 1000 explanation + 500 step_by_step).

**STÁTUSZ: STABIL.**
