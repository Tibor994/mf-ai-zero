# Dataset pipeline hardening - simple_qa 0151-0500

Ez a kör a `data/reports/dataset_audit_0151_0500.md` auditban feltárt problémákra
épül: **két új, állandó eszközt** vezet be, ezekkel **teljes körűen újra-
ellenőrzi** a jelenlegi 0151-0500 clean korpuszt, és **elvégzi a konkrét,
audit által javasolt javításokat** (duplikátum eltávolítás, túlismételt
AI/Nexora sorok megjelölése). **Nem indított tanítást, nem generált új
dataset sort, nem módosított webapp/backend kódot, és nem commitolt/pusholt
semmit** - minden változás csak a helyi munkakönyvtárban történt.

## 1. Új eszközök

### `tools/dataset_cross_dedupe.py`
A meglévő `tools/dataset_dedupe.py` `find_duplicates()`-jét futtatja a
`data/clean/` ALATTI **összes** `.jsonl` fájl együttesén, egyetlen hívással -
nem csak "az új batch a korábbiak ellen", ahogy az egyes DeepSeek importok
korábbi, egyedi szkriptjei tették. Ez formalizálja azt a lépést, aminek
hiánya a batch1-3 (0151-0300) közötti, korábban észrevétlen duplikátumot
okozta. SOHA nem módosít fájlt, csak reportol - `cross_dedupe_directory()`
függvényként is importálható.

### `tools/dataset_topic_report.py`
Egy `.jsonl` könyvtár teljes tag- és category-eloszlását számolja, és egy
konfigurálható küszöb (alapértelmezés: 8%) fölötti tageket "túlreprezentált"
jelzéssel látja el. Emellett tetszőleges kulcsszavak (pl. `nexora`) előfor-
dulását is számolja az instruction+output szövegben. SOHA nem módosít fájlt,
csak reportol - `topic_report()` függvényként is importálható.

Mindkét eszköz ugyanazt a mintát követi, mint a projekt többi `tools/
dataset_*.py` modulja: determinisztikus, szabályalapú, nincs ML/embedding-
függőség, parancssorból és modulként is használható.

## 2. Teljes körű újra-ellenőrzés eredményei (az eredeti, javítatlan állapoton)

### 2.1 Kereszt-batch dedupe (`dataset_cross_dedupe.py`, küszöb=0.9)

A teljes 343 soros korpuszon (7 fájl) futtatva, **pontosan 1 duplikátumot**
talált - ugyanazt, amit az audit manuálisan már azonosított:

```
[instruction_duplicates] megtartva: simple_qa_0185 (deepseek_simple_qa_0151_0200_clean.jsonl)
  <- duplikátum: simple_qa_0283 (deepseek_simple_qa_0251_0300_clean.jsonl) (hasonlóság=0.932)
```

**Más, eddig fel nem tárt duplikátumot NEM talált** a 0.9-es küszöbön - ez
megerősíti, hogy a batch4-7 importok kereszt-ellenőrzése (amikor már a
teljes korábbi korpusz ellen futott) helyesen működött, és a probléma
kizárólag a batch1-3 közötti, korábban soha le nem futtatott ellenőrzésből
fakadt.

### 2.2 Topic report (`dataset_topic_report.py`, küszöb=8%)

| Tag | Darab | Arány |
|---|---|---|
| AI | 44 | 12.8% |
| iskola | 40 | 11.7% |
| technika | 40 | 11.7% |
| egészség | 21 | 6.1% |
| háztartás | 14 | 4.1% |
| *(...további 25+ tag, mind 3% alatt)* | | |

**3 tag lépi túl a 8%-os küszöböt: AI, iskola, technika.** Mindhárom
esetet manuálisan mintavételeztem (lásd `iskola`/`technika` 10-10 soros
minta), és **csak az `AI` tag mutat valódi tartalmi túlismétlést**:

- Az `iskola` (40 sor) és a `technika` (40 sor) minden vizsgált sora
  **valóban különböző, konkrét, hasznos hétköznapi kérdés** (pl. iskola:
  "Hogyan jegyezzem meg a szorzótáblát?", "Mi a különbség a magánhangzó és
  a mássalhangzó között?"; technika: "Hogyan ismerjem fel az adathalász
  e-mailt?", "Mi az a VPN?") - a magas arány itt egyszerűen azt jelzi, hogy
  ez két gyakori, széles témakör, NEM azt, hogy a tartalom ismétlődő.
- Az `AI` tag (44 sor) ezzel szemben - lásd 2.3 pont - túlnyomórészt egy
  **szűk, önreferenciális kérdéskört ismétel** enyhén átfogalmazva.

**Tanulság a küszöb-alapú riasztáshoz:** a puszta arány-küszöb (8%) önmagában
NEM elég a tartalmi túlismétlés kimutatásához - hamis pozitívot ad széles,
legitim témáknál (iskola, technika). A `dataset_topic_report.py` ezért csak
egy ELSŐ SZŰRŐ, ami után manuális (vagy egy jövőbeli, tartalmi hasonlóságot
is néző) átvizsgálás szükséges - ez explicit korlátja a mostani eszköznek,
lásd 5. pont.

### 2.3 AI/Nexora arány ellenőrzés

- `AI` tag: 44/343 sor (audit után, a duplikátum-javítás UTÁN: 44/342 = 12.9%)
- `nexora` kulcsszó előfordulás (instruction+output): 9 sor

A 44 AI-tagelt sor tartalmi klaszterezése (azonos alapfogalom, eltérő
megfogalmazás) 9 visszatérő témát azonosított:

| Klaszter | Megtartott (első előfordulás) | Megjelölt ismétlések (`topic_flags`) |
|---|---|---|
| Nexora Zero célja/rendeltetése | simple_qa_0191 | 0196, 0294, 0343 |
| Mi a tanítóadat | simple_qa_0193 | 0241 |
| Tanítóadat/válaszok minőség-ellenőrzése | simple_qa_0197 | 0247, 0348, 0393 |
| Mitől jó/pontos/természetes egy AI válasz | simple_qa_0198 | 0242, 0248 |
| Címkézés fontossága | simple_qa_0199 | 0249, 0297 |
| Nexora/modell fejlesztése, magyarra optimalizálás | simple_qa_0194 | 0245, 0246, 0346, 0350 |
| Teljesítménymérés/tesztelés/kiértékelés | simple_qa_0295 | 0298, 0342, 0397 |
| AI válaszok biztonsága/etikája | simple_qa_0299 | 0394, 0399 |
| AI mindennapi használata/hibajavítás | simple_qa_0391 | 0392, 0396, 0398 |

**Összesen 23 sor lett megjelölve** (44-ből) - ezek nem törölt, hanem
**metaadattal ellátott** sorok (lásd 4.2 pont), a 21 fennmaradó AI-tagelt sor
(a 9 klaszter "első előfordulása" + a klaszterbe nem eső, valóban önálló
tartalmú sorok, pl. "Mi a különbség az AI és a hagyományos program között?",
"Hogyan tanul egy nyelvi modell?") változatlanul, jelölés nélkül maradt.

### 2.4 Scorer-diagnosztika

A gyanú (minden batch átlag quality_score = 100.0) megerősítést nyert:
a `dataset_score.py` `score_row()`-ját **frissen újra lefuttatva mind a 342
sorra**, a 9 lehetséges büntető flag közül **egyetlen egy sem tüzelt egyszer
sem** (`garbled_token`, `repeated_char_run`, `too_short`, `too_long`,
`english_mixing`, `overclaiming`, `no_terminal_punctuation`,
`generic_template`, `low_instruction_overlap` - mind 0 találat).

Egy szintetikus teszttel igazoltam, hogy ez **valódi vakfolt, nem csak "a
korpusz tényleg ilyen jó"**: a `{"instruction": "Mi a Nexora Zero célja?",
"output": "Ez egy AI projekt, ami hasznos szeretne lenni."}` - egy
nyilvánvalóan sekély, semmitmondó, de nyelvtanilag hibátlan válasz - szintén
**100/100 pontot kapott, flag nélkül**.

**Következtetés: a `dataset_score.py` jelenlegi formájában strukturálisan
képtelen tartalmi mélységet/általánosságot mérni** - csak explicit, mechanikus
hibamintákat szűr. Ez NEM hiba a kódban (a szabályok helyesen működnek arra,
amire tervezve lettek), hanem egy **tervezési korlát**, amit a scorer
KIBŐVÍTÉSE (nem javítása) oldana meg. **Ebben a körben a `dataset_score.py`-t
szándékosan NEM módosítottam** - ez explicit, külön jóváhagyást igénylő
lépés lenne (meglévő, már véglegesített sorok pontszámait változtatná meg),
ami túlmutat a mostani "audit javaslatai szerinti javítás" hatókörén. Lásd
5. pont a javasolt jövőbeli megoldásra.

## 3. Elvégzett konkrét javítások

### 3.1 Duplikátum eltávolítás
- `simple_qa_0283` (batch 0251-0300, "Hogyan csökkentsem a napi stresszt?")
  **kikerült** a `data/clean/deepseek_simple_qa_0251_0300_clean.jsonl`-ból
  (50 -> 49 sor).
- Bekerült a `data/rejected/deepseek_simple_qa_0251_0300_rejected.jsonl`-ba,
  ugyanazzal a sémával, mint a korábbi kereszt-batch duplikátumok:
  `{"row_number": 65, "id": "simple_qa_0283", "reason":
  "duplicate_cross_batch", "matched_id": "simple_qa_0185", "matched_source":
  "deepseek_simple_qa_0151_0200_clean.jsonl", "similarity": 0.932, "row": {...}}`.
- `simple_qa_0185` (a korábbi, batch 0151-0200-beli sor) változatlanul a
  clean fájlban maradt - ő a "megtartott" változat, a korábban is alkalmazott
  "kept = korábbi sor" konvenció szerint.
- Az eredeti `data/reports/deepseek_simple_qa_0251_0300_report.md` (a batch
  EREDETI import-riportja) **változatlan maradt** - ez egy időpont-hű
  történeti dokumentum, nem íródott újra. Ez a retroaktív javítás csak ebben
  az új riportban van dokumentálva.

### 3.2 Kereszt-batch dedupe megerősítése a javítás UTÁN
A `dataset_cross_dedupe.py`-t újra lefuttatva a javított (342 soros)
korpuszon: **0 duplikátum** - a javítás teljes és nem hagyott maga után
további rejtett egyezést.

### 3.3 AI/Nexora túlismétlések megjelölése
A 2.3 pontban azonosított 23 sor mindegyike kapott egy új,
**nem-kötelező, additív** mezőt: `"topic_flags": ["ai_nexora_overrepeated"]`.
Ez:
- **NEM törli, NEM módosítja** az eredeti `instruction`/`output`/
  `quality_score` tartalmat - a sorok érintetlenek maradnak, csak egy jelző
  metaadatot kapnak.
- **NEM kötelező mező** - a `tools/dataset_validate.py` `REQUIRED_FIELDS`
  listája nem tartalmazza, így a hiánya/jelenléte nem befolyásolja a
  validálást (ellenőrizve: mind a 342 sor továbbra is valid, lásd 4. pont).
- Célja, hogy egy jövőbeli `dataset_split.py` (train/eval vágás) vagy egy
  ember tudja **szándékosan kihagyni vagy alulsúlyozni** ezeket a sorokat a
  tanításnál, anélkül, hogy a nyers adat elveszne.

## 4. Állapot a javítások után

- **Validálás**: mind a 342 sor (7 fájl) újra lefuttatva `validate_file()`-
  on - **0 elutasítás**, minden sor szerkezetileg érvényes (a `topic_flags`
  extra mező nem okoz problémát).
- **Regressziós teszt**: a meglévő `tests/test_v1_7_4_dataset_foundation.py`
  (8 rész, minden korábbi validator/dedupe/score/split/import teszt) -
  **minden teszt sikeres, STÁTUSZ: STABIL** - az új eszközök és a fájl-
  módosítások nem okoztak regressziót.
- **Clean sorok száma**: 343 -> **342** (1 valódi duplikátum eltávolítva).
- **Megjelölt (de meg nem tartott) AI/Nexora sorok**: **23** (`topic_flags`
  mezővel).
- **Ismert kereszt-batch duplikátum a korpuszban**: **0**.

## 5. Újonnan feltárt, MÉG NYITOTT tétel: a 0251-0300 batch soha nem lett
   commitolva

Az audit korábban csak azt jelezte, hogy a `data/reports/
deepseek_simple_qa_0251_0300_report.md` nincs commitolva. Ez a kör
`git ls-files`-al ellenőrizve **egy súlyosabb, eddig fel nem tárt tényt**
talált: **a teljes 0251-0300 batch (raw + clean + rejected .jsonl fájlok is,
nem csak a riport) SOHA nem lett git-tracked** - egyik korábbi "commitold és
pushold" kör sem tartalmazta ezt a batch-et (a `v1.7.5-dataset-import` commit
csak a 0151-0200 és 0201-0250 batch-eket fedte le). A helyi lemezen a fájlok
megvannak és helyesek, de a GitHub-on jelenleg **nincs nyoma** a 0251-0300
batch-nek.

**Ez a kör ezt szándékosan NEM javította** (a TILOS lista kifejezetten
tiltja a commitolást/pusholást ebben a körben) - ezt explicit, külön
felhasználói jóváhagyást igénylő következő lépésként jelzem.

## 6. Javaslatok a következő hardening-körhöz (NEM implementálva most)

- **Tartalmi hasonlóságot is néző túlismétlés-detektor**: a
  `dataset_topic_report.py` jelenlegi arány-küszöbe (2.2 pont) hamis
  pozitívot ad széles, legitim témáknál - egy jövőbeli verzió a same-tag
  sorok EGYMÁS KÖZÖTTI (nem csak globális) `difflib` hasonlóságát is
  nézhetné, alacsonyabb (pl. 0.5-0.6) küszöbön, hogy automatikusan
  megtalálja az "AI"-hoz hasonló szűk, önreferenciális klasztereket anélkül,
  hogy minden magas arányú tag kézi átvizsgálást igényelne.
- **`dataset_score.py` tartalmi mélység-ellenőrzéssel bővítése**: a 2.4
  pontban igazolt vakfolt (sekély-de-hibátlan válasz = 100 pont) orvoslása
  - ez explicit, a meglévő pontszámokat megváltoztató lépés, külön
  jóváhagyást igényel.
- **Kötelező batch-quota mechanizmus** - lásd az audit 3.3 pontját,
  változatlanul érvényes javaslat.
- **A 0251-0300 batch git-commitolása** - lásd 5. pont, a legégetőbb
  konkrét follow-up.

---

## Végső státusz

**STÁTUSZ: STABIL.** A pipeline két új, tesztelt, determinisztikus eszközzel
bővült (`dataset_cross_dedupe.py`, `dataset_topic_report.py`), a teljes
0151-0500 korpusz újra-ellenőrzésre került, az egyetlen talált valódi hiba
(0185/0283 duplikátum) javítva lett, a 23 túlismételt AI/Nexora sor jelölve
lett (nem törölve), és a meglévő teljes regressziós teszt-suite továbbra is
100%-ban zöld. Nem történt tanítás, új adatgenerálás, webapp/backend
módosítás, commit vagy push.

**Biztonságos-e ezután egy felügyelt, Claude-generált 100-as batch
elindítása?**

**Igen, feltételesen biztonságos - felügyelt (nem teljesen önálló) módban.**
A mai kör pont a korábbi audit két legkonkrétabb aggályát oldotta meg
(formalizált teljes-korpuszos dedupe, mérhető arány-riasztás), és a
teszteredmények (0 fennmaradó duplikátum, működő topic-riasztás) igazolják,
hogy ezek a védvonalak most már a helyükön vannak egy 100 soros próbakörhöz.
**Ugyanakkor a scorer vakfoltja (2.4 pont) továbbra is fennáll** - egy
Claude-generált batch-nél a tartalmi mélység ellenőrzése emberi (felhasználói)
mintavételes átnézést igényel, az automata scorer önmagában NEM elég erre.
Javaslat: az első Claude-generált 100 soros próba-batch-nél (a) kötelezően
futtatni kell mindkét új eszközt a teljes korpuszon importáláskor, (b) a
`topic_flags` mechanizmust alkalmazni kell, ha a próba-batch is AI/Nexora
témát érint, és (c) a scorer 100%-os eredménye esetén NE tekintsük ezt
automatikus "jóváhagyásnak" - egy rövid emberi mintavételes átolvasás
ajánlott, amíg a 2.4 pontban jelzett scorer-bővítés meg nem történik.

**FONTOS: ez a kör NEM indított tanítást, NEM generált új dataset batch-et,
NEM módosított webapp/backend kódot, és NEM commitolt/pusholt semmit - csak
a meglévő pipeline-t és a meglévő 0151-0500 korpuszt javította/erősítette
meg, helyben.**
