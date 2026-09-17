# Dataset audit - simple_qa 0151-0500 (7 DeepSeek batch)

Ez az audit **nem módosított semmilyen adat- vagy kódfájlt**. Kizárólag a meglévő
`data/raw/`, `data/clean/`, `data/rejected/` és `data/reports/` állományokat elemzi,
a `tools/dataset_validate.py`, `tools/dataset_dedupe.py`, `tools/dataset_score.py`
eszközök újrafuttatásával és kiegészítő, ad hoc Python elemzésekkel.

## 1. Számok

| Mérőszám | Érték |
|---|---|
| Vizsgált batch-ek | 7 db (0151-0200, 0201-0250, 0251-0300, 0301-0350, 0351-0400, 0401-0450, 0451-0500) |
| Összes raw sor | 350 (7 × 50) |
| Összes clean sor (jelenlegi állapot) | 343 |
| Összes rejected sor | 7 |
| ...ebből validáláson elutasítva | 0 |
| ...ebből kereszt-batch duplikátumként kiszűrve (import közben) | 7 (batch4: 4, batch5: 2, batch6: 1) |
| **Auditban újonnan talált, még ELTÁVOLÍTATLAN kereszt-batch duplikátum** | **1 pár** (lásd 2.2) |
| Jelenlegi egyedi clean sorok (a fenti 1 pár figyelembevételével) | ~342 |
| Átlag quality_score minden batch-ben | 100.0 |
| Output hossz (karakter) | min 86, medián 130, max 233 |
| Outputok 80 karakter alatt | 0 |

Batch-enkénti clean/rejected bontás:

| Batch | Clean sor | Rejected sor |
|---|---|---|
| 0151-0200 | 50 | 0 |
| 0201-0250 | 50 | 0 |
| 0251-0300 | 50 | 0 |
| 0301-0350 | 46 | 4 |
| 0351-0400 | 48 | 2 |
| 0401-0450 | 49 | 1 |
| 0451-0500 | 50 | 0 |

## 2. Elemzés

### 2.1 Témakörök eloszlása

343 clean sor össz. 30+ különböző tag mentén oszlik meg (a `magyar` tag mindenhol
jelen van, azt kihagyva). Top tagek:

| Tag | Előfordulás | Arány |
|---|---|---|
| AI | 44 | 12.8% |
| iskola | 40 | 11.7% |
| technika | 40 | 11.7% |
| egészség | 21 | 6.1% |
| háztartás | 14 | 4.1% |
| hétköznapi élet | 10 | 2.9% |
| sport | 10 | 2.9% |
| földrajz | 9 | 2.6% |
| kommunikáció | 8 | 2.3% |
| illem | 8 | 2.3% |
| otthoni biztonság | 8 | 2.3% |
| önfejlesztés | 7 | 2.0% |
| konyha | 7 | 2.0% |
| vásárlás | 7 | 2.0% |
| ügyintézés | 6 | 1.7% |

A maradék 15+ tag (életmód, társadalom, közlekedés, utazás, produktivitás, stb.)
2-6 előfordulás között szóródik. Összességében a témakör-lefedettség **széles és
életszerű** (háztartás, egészség, iskola, közlekedés, ügyintézés, illem), ami jó
alap egy általános magyar chat asszisztenshez - de az `AI` tag kiugróan magas
aránya (lásd 2.3) torzítja a képet.

### 2.2 Túlismételt témák

**Kritikus, korábban nem észlelt lelet:** a hivatalos `find_duplicates()` eszközt
(0.9 küszöb) most **először futtattam le retroaktívan a batch 1-3 (0151-0300)
együttesén** - ezt a keresztellenőrzést a korábbi importok csak a 4. batch-től
(0301-0350) kezdve vezették be, így az első 3 batch soha nem lett egymás ellen
ellenőrizve. Az eredmény egy valódi, eddig észrevétlen duplikátum:

- `simple_qa_0185` ("Hogyan csökkentsem a stresszt?", batch 0151-0200)
- `simple_qa_0283` ("Hogyan csökkentsem a napi stresszt?", batch 0251-0300)
- instruction hasonlóság: **0.932** (a 0.9-es küszöb felett)
- mindkét output ugyanazt a három tanácsot adja lényegében azonos sorrendben
  (rövid szünetek tartása, mozgás/légzés, feladatok kisebb részekre bontása)

Ez azt jelenti, hogy a jelenlegi 343 "clean" sorból **1 pár valójában tartalmi
duplikátum**, amit a korábbi importok pipeline-hibája miatt nem szűrt ki semmi.
**Ezt a duplikátumot ez az audit szándékosan NEM távolította el** (a feladat
hatóköre csak audit+terv, nincs adatmódosítás) - ezt explicit follow-up
feladatként javaslom.

Emellett egy **szemantikai (tartalmi, de 0.9 alatti szöveghasonlóságú) ismétlődés**
is jól látszik az AI/Nexora témájú soroknál - lásd 2.3.

Ezen kívül nincs más kimutatható tematikus túltelítettség: a nem-AI témák (iskola,
technika, egészség, háztartás, stb.) minden batch-ben változatos, konkrét,
egymástól ténylegesen különböző kérdéseket tartalmaznak.

### 2.3 AI/Nexora témák túlzott ismétlése

Ez a legerősebb minőségi lelet. A 44 `AI`-tagelt sor (a teljes korpusz 12.8%-a)
vizsgálata megmutatja, hogy **szinte minden batch záró szakasza egy azonos,
kb. 9-10 elemű "meta-kérdés" készletet ismétel meg**, csak enyhén átfogalmazva:

| Alaptéma | Ismétlődő variánsok (id-k) |
|---|---|
| Mi a Nexora Zero célja/rendeltetése? | 0191, 0343 (+ rokon: 0196 "mire készíthető fel", 0294 "mire képezhető") |
| Mi a tanítóadat / mit jelent? | 0193, 0241 |
| Hogyan ellenőrzik a tanítóadat/válaszok minőségét? | 0197, 0247, 0348, 0393 |
| Mitől jó/pontos/természetes egy AI válasz? | 0198, 0242, 0248 |
| Miért fontos a címkézés? | 0199, 0249, 0297 |
| Hogyan fejlesztik/optimalizálják a Nexora Zerót? | 0194, 0246, 0294, 0350 |
| Hogyan mérik/tesztelik a modell teljesítményét? | 0295, 0298, 0342, 0397 |
| Biztonságos-e / etikus-e az AI válasza? | 0299, 0394, 0399 |
| Hogyan használható az AI a mindennapokban? | 0391, 0392, 0396, 0398 |

Ezek a párok/csoportok **0.9 alatti szöveghasonlósággal** rendelkeznek (eltérő
megfogalmazás), ezért a hivatalos dedupe őket jogosan NEM vette ki - önmagukban
egyik válasz sem hibás vagy duplikátum a szó szoros értelmében. A probléma inkább
**tartalmi-arányossági**: a korpusz egy viszonylag szűk, önreferenciális
("mi az AI/mi a Nexora/hogyan teszteled magad") témakört aránytalanul sokszor jár
körbe ahhoz képest, hogy hasznos, végfelhasználói tudást ad-e. Egy éles chat
felhasználó számára ez a 44 sor gyakorlatilag 9-10 tényleges kérdést fed le
44-szeres szóismétléssel.

**Javaslat:** a jövőbeli batch-ekben az AI/Nexora témát erősen limitálni kell
(pl. batch-enként max. 2-3 sor, nem 8-10), és a jelenlegi 44 sorból érdemes lenne
egy külön, later feladatként egy manuális szűrést végezni, ami a fenti 9
alaptémánként csak 1-2 legjobb megfogalmazású sort tart meg.

### 2.4 Gyenge vagy túl általános válaszok

Az output hosszeloszlás (86-233 karakter, medián 130) nem mutat "csonka" vagy
info-mentes választ - nincs 80 karakter alatti sor. Egy célzott hedge-kifejezés
keresés (`"attól függ"`, `"sok mindentől függ"`, `"nem lehet egyértelműen"`, stb.)
mindössze **1 találatot** adott (`simple_qa_0184`, szomjúság/vizelet szín témában),
és az ott indokolt, jogos epistemikus óvatosság, nem kitérő általánosítás.

**Fontos módszertani megfigyelés:** a `quality_score` **mind a 343 sorban 100.0**
- azaz a jelenlegi `dataset_score.py` **soha nem büntetett egyetlen sort sem**
ezen a korpuszon. Ez két dolgot jelenthet egyszerre: (a) DeepSeek kimenete
valóban következetesen jó minőségű volt, VAGY (b) a scorer nem érzékeny a
"strukturálisan rendben van, de tartalmilag sekély/túl általános" hibatípusra -
csak mechanikus jegyeket (tiltott kifejezés, elgépelés-minta, hossz) néz. A
100%-os egyhangúság önmagában gyanús jel: egy valóban változatos, 343 soros,
emberi/AI-generált korpuszban statisztikailag valószínűtlen, hogy szó szerint
nulla sor kapjon bármilyen levonást. Ez arra utal, hogy **a scorer jelenlegi
formájában nem alkalmas tartalmi mélység/általánosság mérésére**, csak
mechanikus szűrésre.

### 2.5 Magyar nyelvi/stílus hibák

A 7 import-kör során összesen 3 nyelvi/stílus jellegű javítás történt (batch1: nem
volt ilyen jellegű a mostani mintában; batch6: "Zárjad el" -> "Zárd el"; batch7:
"A hitel pénzt kérsz..." -> alany-állítmány egyeztetés javítása), ezeken kívül a
jelen audit során futtatott kiegészítő keresés (hedge-kifejezések, tipikus
elgépelés-minták) **nem talált további, korábban észrevétlen nyelvi hibát** a 343
clean sorban. A `dataset_validate.py` beépített `find_invalid_escapes` és
karaktergarbling-ellenőrzése (`_has_garbled_token`) minden batch-ben 0 találatot
adott.

### 2.6 Veszélyes vagy pontatlan tanácsok

A batch7 import során már kijavított olajtűz-tanács (nedves ruha helyett tűzoltó
takaró) volt eddig az egyetlen ténylegesen veszélyes tanács a korpuszban. Ez az
audit egy kiegészítő kulcsszó-keresést futtatott (gyógyszer, adag, áramütés,
mérgezés, vegyszer, gáz, elektromos, sav, lúg) az összes clean soron: **5 találat**
(leégett vacsora, vízkő eltávolítás, elromlott fűtés, üvegházhatás, villámlás
keletkezése) - ezek mindegyike **semleges/nem veszélyes** témájú (háztartási
hétköznapi tanács vagy tiszta ismeretterjesztő definíció), egyik sem tartalmaz
kockázatos instrukciót. **Nem talált új veszélyes tanácsot** ez az audit a már
javított olajtűz-eseten túl.

### 2.7 Train-ready-e a dataset jelenlegi állapotában?

**Részlegesen igen, de NEM ajánlott azonnali tanítás anélkül, hogy a 2.2 és 2.3
pontban leírt problémákat rendeznénk.** Indoklás:

- Strukturálisan (validator szinten) a korpusz makulátlan: 0 elutasított sor 350
  raw sorból.
- Nyelvi/biztonsági szempontból tiszta: a 3 ismert korábbi hiba javítva, az audit
  nem talált újat.
- **DE**: legalább 1 tényleges tartalmi duplikátum van benne felderítetlenül
  (0185/0283), és az AI/Nexora témakör aránytalanul (12.8%) túlreprezentált,
  méghozzá erősen ismétlődő, önreferenciális kérdésekkel - ha ez így megy be a
  tanításba, a modell felül fogja reprezentálni a "mi vagyok én/hogyan mérnek
  engem" témát a hasznos, mindennapi tudáshoz képest.
- A `quality_score` 100%-os egyhangúsága azt jelzi, hogy a jelenlegi automata
  minőség-ellenőrzés **nem tud különbséget tenni "jó" és "kiváló" válasz között**
  - emberi mintavételes átnézés nélkül nem garantálható, hogy a train szettbe
    csak valóban erős példák kerülnek.

**Javasolt lépés tanítás előtt:** (1) távolítsuk el a 0185/0283 duplikátum egyikét,
(2) manuálisan válogassuk le az AI/Nexora 44 sort 12-15 sorra a 2.3-as táblázat
alapján, (3) csak ez után vágjuk train/eval splitre a `dataset_split.py`
eszközzel. Ezek explicit adatmódosítások, ezért **ezt az audit kört nem hajtja
végre** - külön jóváhagyást igényelnek.

## 3. A pipeline elégséges-e egy Claude-alapú önálló generálás+önellenőrzés
   ciklushoz?

### 3.1 Amit a dogfooding során bebizonyítottan megtalált a pipeline

A projekt eddigi élete során a validator/dedupe/scorer eszközök **saját magukat
tesztelve, valós adaton, több hibát is felszínre hoztak és ezek javításra
kerültek**:

1. Angol-keveredés detektor hamis pozitívjai (kétszer is) - ASCII-only regex
   ékezetes szavakat vágott szét, angol stopword-del véletlenül egyezőt találva.
2. Dedupe instruction-only hamis pozitívja - azonos sablon+eltérő input sorokat
   (pl. typo_correction minták) tévesen duplikátumnak jelzett.
3. `generic_template` túl tág kifejezéslista - jogos, epistemikusan őszinte
   `uncertain_lookup` válaszokat büntetett.
4. **(Ezen audit során talált, még nyitott)** batch1-3 kereszt-ellenőrzési rés -
   a cross-batch dedupe csak a 4. importtól kezdve futott a teljes korpuszon,
   így egy valódi duplikátum (0185/0283) átcsúszott.

### 3.2 Értékelés

**Jelenlegi státusz: a pipeline hasznos, deterministic alapréteg, de ÖNMAGÁBAN
NEM elég megbízható egy felügyelet nélküli, Claude-generálja-Claude-ellenőrzi
ciklushoz.** Indoklás:

- **Erősség**: a validator strukturális szinten megbízhatóan nullára szűr (0
  hiba/350 sor eddig), a dedupe 0.9 küszöbön empirikusan jól kalibrált (a
  kiegészítő alacsonyabb-küszöbű ellenőrzések ismételten megerősítették, hogy 
  0.55-0.89 tartományban a "egyezések" túlnyomó többsége ártalmatlan mondatsablon-
  átfedés, nem tartalmi duplikátum).
- **Gyengeség 1 - önellenőrzés vakfoltja**: ha ugyanaz a rendszer (Claude) generál
  ÉS validál, a validátor jelenlegi tervezése (kulcsszó/regex/similarity alapú)
  nem véd az ellen, hogy a generátor és a scorer **ugyanazt a vakfoltot** ossza
  meg - pl. a `quality_score` 100%-os egyhangúsága azt mutatja, a scorer nem
  méri a tartalmi mélységet/változatosságot, csak mechanikus jegyeket.
- **Gyengeség 2 - a kereszt-batch dedupe eddig soha nem volt automatikus/kötelező
  lépés**, hanem minden importkörben egy egyedi, kézzel írt szkript hívta meg
  ad hoc. Ez pont a batch1-3 rést okozta - ha Claude önállóan generálna sok
  batch-et gyorsan egymás után, egy hasonló, formalizálatlan lépés könnyen
  kimaradhatna.
- **Gyengeség 3 - nincs témakör-arányossági korlát**: semmi a pipeline-ban nem
  állítja meg azt, hogy egy adott tag (pl. `AI`) batch-ről batch-re
  aránytalanul felülreprezentálva legyen - ez emberi felügyelet nélkül könnyen
  súlyosbodna, különösen ha Claude maga választja a témákat.

### 3.3 Javasolt (NEM implementált) új eszközök a self-generate+self-validate
   biztonságosabbá tételéhez

- **`tools/dataset_crossdedupe.py`** - a jelenlegi ad hoc, egyszer-használatos
  import-szkriptekben megismételt kereszt-batch dedupe logikát egy állandó,
  minden importnál KÖTELEZŐEN lefutó, a TELJES `data/clean/` korpuszt átfogó
  eszközzé formalizálná (nem csak "amit a user az adott körben kér" - hanem
  minden körben automatikusan).
- **`tools/dataset_topic_report.py`** - tag/téma-eloszlás jelentés generátor
  (a most kézzel futtatott `Counter`-alapú elemzés állandósítása), egy
  beépített arányossági riasztással (pl. figyelmeztetés, ha egy tag aránya
  > 8-10% a teljes korpuszban).
- **Szigorúbb, "Claude self-audit" validációs profil** a `dataset_score.py`
  mellé - amely nem csak mechanikus jegyeket (tiltott kifejezés, hossz,
  garbled token), hanem tartalmi változatosságot is mérne, pl. az új sor és a
  már meglévő, azonos tag-ű sorok közötti szemantikai hasonlóságot (nem csak
  szó szerinti string-hasonlóságot) - ez explicit fejlesztési munkát igényelne,
  jelenleg nincs ilyen komponens.
- **Kötelező "batch quota" mechanizmus** témánként (pl. max N sor/tag egy adott
  méretű batch-ben), hogy a 2.3-as pontban leírt AI/Nexora-túlsúly típusú
  probléma strukturálisan ne fordulhasson elő újra.

## 4. Terv a következő nagy dataset-csomagokhoz (TERV, NEM implementáció)

A user által kért 9 csomag, javasolt fájlnév-konvencióval, kategória/tag
sémával és folyamat-ajánlással. Egyik csomag generálása sem indult el ebben a
körben.

| # | Csomag | Db | Javasolt fájlnév-prefix | Kategória (`category` mező) | Megjegyzés |
|---|---|---|---|---|---|
| 1 | Egyszerű magyar kérdés-válasz | 1000 | `simple_qa_batch2_*` | `simple_qa` | Folytatás a 0501-es id-től; a 2.3 pont alapján AI/Nexora aránya ≤5% legyen |
| 2 | Magyarázós példa | 1000 | `explanation_*` | `explanation` | Fogalom-magyarázatok, "hogyan működik X" jellegű |
| 3 | "Írd lépésekben" példa | 500 | `stepwise_*` | `stepwise` (új kategória) | Számozott lépéslistát váró instrukciók |
| 4 | Összegzés példa | 500 | `summary_*` | `summary` | Hosszabb bemenet -> tömör kivonat |
| 5 | Hibás user szöveg -> javított szöveg | 500 | `typo_correction_batch2_*` | `typo_correction` | A meglévő minta (sample_pack) sémáját követve |
| 6 | Hosszabb, többfordulós beszélgetés | 300 | `multiturn_*` | `multiturn` (új kategória, több `instruction`/`output` pár egy rekordban) | Séma-kiterjesztést igényel (jelenlegi validator egy-fordulós rekordokra épül) |
| 7 | "Nem tudom biztosan, nézzünk utána" példa | 300 | `uncertain_lookup_batch2_*` | `uncertain_lookup` | Épít a meglévő sample_pack mintára; a `generic_template` szűrő már ki lett hangolva erre |
| 8 | Webes forrásból készült összefoglaló | 300 | `web_summary_*` | `web_summary` (új kategória) | Forrás-attribúció kérdés (a `source` mező kitöltése kötelező legyen) |
| 9 | Saját projekt/MF-AI témájú tudásanyag | 500 | `project_knowledge_*` | `project_knowledge` (új kategória) | Ez lényegében az AI/Nexora témakör - a 2.3 lelet miatt itt KÜLÖN, korlátozott helyen kapjon teret, ne szivárogjon szét az összes többi csomagba |

**Folyamat-ajánlás minden jövőbeli csomaghoz** (a most feltárt hibák alapján):
1. Minden import kössön be a `tools/dataset_crossdedupe.py` (3.3 pont) TELJES
   korpusz elleni futtatásába - ne csak "korábbi batch-ek" ellen, hanem a
   projekt aktuális teljes `data/clean/` állománya ellen, elejétől kezdve.
2. Kisebb sub-batch-ekben generálni (50-100 soros egységek), hogy egy hibás
   köteg felfedezése ne 500-1000 sort érintsen egyszerre.
3. Minden csomagnál explicit tag-arányossági ellenőrzés (3.3 pont) - egyetlen
   tag se haladja meg a csomagon belüli kb. 8-10%-ot.
4. A 8. csomagnál (webes forrás) különös figyelem a forrás-hitelesség és
   szerzői jogi kérdésekre - ez explicit user-jóváhagyást igényel a forrás-
   válogatás módszerét illetően, mielőtt bármi generálódna.
5. A 6. csomagnál (multiturn) először a JSONL séma kiterjesztését kell
   megtervezni és jóváhagyatni, mielőtt bármilyen adat készülne hozzá.

## 5. Egyéb, audit közben talált nyitott tétel

- **`data/reports/deepseek_simple_qa_0251_0300_report.md` soha nem lett
  commitolva** - a `git status` ezt a fájlt a mai napig `??` (untracked)
  státuszban mutatja. A user korábban nem adott külön "commitold és pushold"
  utasítást erre a konkrét batch-re. Ez nem adatintegritási probléma (a fájl a
  lemezen megvan, tartalma helyes), csak repo-higiéniai rés - jelzem, de ez az
  audit kör nem javítja unilaterálisan.

## 6. Végső státusz

**STÁTUSZ: STABIL** (audit-szinten - semmilyen fájl nem sérült, nem indult
tanítás, nem történt adat- vagy kódmódosítás), **de a dataset maga jelenleg
NEM "tanítás-kész" javítás nélkül** - lásd 2.7 pont a 2 konkrét, ajánlott
(de itt nem végrehajtott) javító lépéssel (duplikátum-eltávolítás,
AI/Nexora-arány csökkentése).

**Biztonságos-e most áttérni Claude-alapú automata batch generálásra és
önellenőrzésre?**

**Nem, még nem teljesen - részleges igen, felügyelettel.** A pipeline
(validator+dedupe+scorer) bizonyítottan jó alapréteg, ami a dogfooding során
több valós hibát is helyesen felszínre hozott saját magán - ez erős érv
mellette. Ugyanakkor ez az audit is talált egy olyan hibát (batch1-3
kereszt-ellenőrzési rés), ami pont abból a mintázatból fakadt, hogy a
kereszt-batch dedupe minden körben egy kézzel, ad hoc módon meghívott lépés
volt, nem egy kötelezően lefutó, formalizált rész - ez a kockázat egy
Claude-vezérelt, gyorsabb ütemű, felügyelet nélküli generálási ciklusban
felerősödne, nem csökkenne. Emellett a `quality_score` 100%-os egyhangúsága
azt mutatja, a jelenlegi scorer nem alkalmas arra, hogy egyedül eldöntse, egy
Claude-generálta sor valóban jó-e, vagy csak mechanikusan hibátlan.

**Javasolt átmenet**: a 3.3 pontban vázolt két eszköz (formalizált
`dataset_crossdedupe.py`, `dataset_topic_report.py` arányossági riasztással)
megvalósítása és egy kis (pl. 50-100 soros) próba-kör lefuttatása Claude
generálással + a jelenlegi pipeline-nal + emberi (user) mintavételes átnézéssel,
mielőtt bármilyen nagyobb (1000+ soros) csomagra rátérnénk teljesen felügyelet
nélkül.

---
**FONTOS: ez az audit kör NEM indított tanítást, NEM generált új adatot és NEM
módosított webapp/backend kódot - kizárólag a meglévő adatok elemzését és egy
tervdokumentumot tartalmaz.**
