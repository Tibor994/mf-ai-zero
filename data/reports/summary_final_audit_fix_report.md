# summary csomag - záró audit és javítási kör (final audit/fix round)

A 4. csomag (Összegzés példa, `summary_0001`-`summary_0500`) lezáró auditja, a `step_by_step_completion_audit.md` mintájára,
kiegészítve az 5. batch reportjában jelzett három nyitott tétel soronkénti átvizsgálásával és javításával.

## Verdikt

**A summary csomag 500 / 500 sora STABIL.** Az audit a három nyitott tételt lezárta: a 11 *érdemes -> tény* gyanús sorból
10 valódi hiba volt (javítva), 1 hamis pozitív; a 44 hedge-jelzésből 15 valódi (javítva), 29 hamis pozitív (indoklással,
módosítatlanul); a 37 közel azonos instruction-pár (68 sor) és a maradék 0.85 fölötti párok (47 sor) miatt 115 instruction
lett átírva témaspecifikusra, így a csomagban már nincs 0.85 vagy annál hasonlóbb instruction-pár. Összesen **139 clean
sor** módosult (38 output, 115 instruction, 14 mindkettő). A `raw` fájlokhoz nem nyúltam. Nincs nyitott blokkoló tétel.

## 0. Rövid package státusz

| Kérdés | Válasz |
|---|---|
| summary 500 / 500 stabil-e? | **Igen** |
| Hány sort javítottam? | **139 clean sor**: 38 output-javítás (39 módosítás; ebből 12 ajánlás->tény, 23 fenntartás/hivatkozás, 4 jelentés/nyelvi), 115 instruction-átírás, 14 sor mindkettő |
| Hány false positive volt? | **29** a 44 hedge-jelzésből + **1** a 11 *érdemes* sorból + 12 *ADDED* sor (7 az 1-3. és 5 az 5. batchben; beszélgetés-szereplőre hivatkozó *szerint*, nem-hivatkozó *szerint* vagy egyenértékű *akár*) + 3 *új tagadás* (`0048`, `0117`, `0438`) + 1 *egyes* (`0488`) |
| Maradt-e nyitott tétel? | **Nincs blokkoló.** Dokumentált korlátok a 9. fejezetben (56 sor a 300-ból nem lett soronként átolvasva, az 1-2. batch maradék generikus instructionjei, scriptek a repón kívül) |
| STABIL vagy BLOCKED | **STABIL** |
| Teljes clean korpusz | **3000 sor** (1000 simple_qa + 1000 explanation + 500 step_by_step + 500 summary), 3000 egyedi id |
| Regressziós teszt | `tests/test_v1_7_4_dataset_foundation.py`: minden teszt sikeres, **STÁTUSZ: STABIL** |

## 1. A kért ellenőrzési pontok

Az ellenőrzések a végleges (javított) `data/clean/claude_summary_*_clean.jsonl` fájlokon futottak (500 sor).

| # | Ellenőrzés | Eredmény |
|---|---|---|
| 1 | `summary_0001`-`0500` ID folytonosság | **OK**: 500 egyedi id, `summary_0001`...`summary_0500` hézag nélkül, sorrendben |
| 2 | 500/500 schema valid | **OK**: `dataset_validate.py` 500/500 valid (az 5 fájlon külön is 100/100); a 9 kötelező mező, `category` = `summary`, `source` = `synthetic_claude` mind az 500 soron |
| 3 | 0 missing, 0 extra | **OK**: 0 hiányzó id, 0 többlet id; 10 típus x 50 sor; 300 egy- + 200 kétmondatos output; difficulty 300 easy / 150 medium / 50 hard |
| 4 | Batchen belüli dedupe | **OK**: mind az 5 batch külön 0 id-, 0 instruction+input-, 0 output-duplikátum (a batch reportok szerint); az 500 soros együttesen is 0 / 0 / 0 |
| 5 | Teljes korpusz cross-dedupe | **OK**: az 500 summary sor a korpusz többi 2500 sorával szemben (minden találat, `quick_ratio` előszűréssel): id-ütközés 0, instruction+input >= 0.9: 0, instruction >= 0.9: 0, output >= 0.9: 0 |
| 6 | Közel azonos instruction-párok | **Javítva**: a javítás előtt 37 pár >= 0.9 (68 sor), 104 pár >= 0.85 (121 sor); a javítás után **0 pár >= 0.85**, a legnagyobb hasonlóság 0.85 alatt (`0032`-`0083`); >= 0.8: 218 pár -> 19 pár (29 sor). A csomagszintű output-párok >= 0.9: 0 (a javítás előtt és után is) |
| 7 | Túl sablonos instruction nyitások | **Javítva** (4. fejezet): "Foglald össze" nyitás 53 -> 33 sor (10.6% -> 6.6%); "...alábbi/következő/lenti/mellékelt/itt olvasható" generikus keretek az 1-2. batchben 187 -> 68 sor; különböző kétszavas nyitás 184 -> 252; mondatszámot megnevező instruction 51% -> 42% |
| 8 | Output rövidebb-e az inputnál | **OK**: 0 sor, ahol output >= input; legmagasabb arány 0.84 (`0215`), egymondatosnál átl. 0.61, kétmondatosnál 0.64; output max. 44 szó |
| 9 | Új tény az outputban | **OK**: nincs új szám, név vagy időszó (a szótő-összevetésben a >= 7 hiányzó tövű 10 sor mind körülírás, kézzel átnézve: `0023`, `0053`, `0089`, `0169`, `0173`, `0185`, `0191`, `0209`, `0304`, `0480`); az egyetlen valódi bővülés az `ADDED` jelzések körében a beszélgetés-szereplőre hivatkozó *szerint* (hamis pozitív) |
| 10 | Jelentéstorzítás | **Javítva**: 4 sor jelentésbeli/nyelvi csúszás (`0038` *lehet -> kell*, `0061` érthetetlen *A még ma...*, `0118` kettős *és*, `0147` *mindkettőt ... leadni* az *elhasznált* nélkül); a véletlen minta 40 sorából 0 további csúszás |
| 11 | Fenntartások megmaradása (*általában, gyakran, szerint, lehet, várható, akár, gyanús, valószínű, nem biztos*) | **Javítva**: 23 fenntartás/hivatkozás-vesztés pótolva; a végállapotban a szigorított ellenőrző 5 batchen összesen 0 valódi vesztést jelez, a megmaradó jelzések (29 *LOST* és a 3.4 alatti *ADDED* sorok) mind hamis pozitívak a 3. fejezet szerint |
| 12 | *érdemes* vagy óvatos megfogalmazás tényállítássá alakítva | **Javítva**: 12 ajánlás->tény/kötelezettség módosítás (11-es lista: 10 sor + 2 további sor: `0086`, `0189`); végállapotban az `ADVICE->FACT` ellenőrző 1 hamis pozitívot jelez (`0061`, kérdés a párbeszédben) |
| 13 | Safety | **OK**: a kulcsszó-találatok mind hétköznapi vagy biztonságpozitív tartalmúak (`0044` fémtárgy a mikróban, `0078` tűzgyújtás tilos, `0138` veszélyes hulladék külön leadása, `0150` biztosíték cseréje ugyanolyan típusra, `0108` gombát nem szedtek, `0458` a bank nem kér jelszót); biztos orvosi/jogi/pénzügyi állítás, veszélyes útmutatás nincs (`0182` napelem: *csökkentheti*, `0039` biztosító: *általában*, *szerződéstől függően eltérhet*) |
| 14 | Identity bleed | **OK**: 0; saját projekt/modellnév említés 0 |
| 15 | URL / e-mail / személyes adat | **OK**: 0 URL, 0 e-mail cím, 0 telefonszám- vagy azonosítóminta; számjegy a szövegekben 0 (a számok betűvel) |
| 16 | quality_notes egyedi és konkrét | **OK**: 500 / 500 egyedi; 5-26 szó (medián 13); egyik sem ismétlődik az első 3 szavával; 0 pár >= 0.85 hasonlóság; a 38 output-javított sor quality_notes-át újraolvastam, mind pontos maradt; 0 nyelvi hibaminta (*a általában*, *lehető*, szóismétlés) |

Kiegészítő futások: `dataset_score.py` átlag 100.0 / 100 (500 sor); `check_summary` alap-, tömörség-, másolás-, nyelvi és mondatszám-konzisztencia
ellenőrzés 0 alap-hiba, 0 mondatszám-ellentmondás, szó szerinti másolás max. 0.46 (nincs 0.5 fölötti).

## 2. A 11 *érdemes* -> tényállítás gyanús sor

Ellenőrző: a szigorított `fidelity_check3` `ADVICE->FACT` szabálya (az inputban *érdemes*, az outputban ajánlás-jelző nélkül).
Minden sort az inputjával együtt kézzel olvastam el.

| id | Ítélet | Mi volt a gond / miért maradt | Javítás (`clean`) |
|---|---|---|---|
| 0016 | **valódi** | a *legkisebb közös többszörösüket érdemes nevezőnek választani* -> *...bővítünk* (tényszerű előírás) | *különbözőnél érdemes a legkisebb közös többszörösre bővíteni* |
| 0027 | **valódi** | *ott érdemes lassítani* -> *lassítani kell* (ajánlás -> kötelezettség) | *egy szűk földúton érdemes lassítani* |
| 0061 | hamis pozitív (*érdemes*) + nyelvi javítás | az *érdemes* a párbeszéd A kérdésében van (*Szerinted érdemes ma elmenni?*), nem tanács; viszont az output *A még ma a piacra megy* nehezen értelmezhető és a B véleményét elhagyta | teljes output újraírva: *B szerint ma jobb a piacra menni, mert holnapra esőt mondtak, ezért A most indul, B pedig paradicsomot és sajtot kér tőle, ha van.* |
| 0073 | **valódi** | *Túrafelszerelés, amit érdemes összecsomagolni* -> *...kell* | *A túrához érdemes ... összecsomagolni* |
| 0090 | **valódi** | *Ehelyett érdemes megvárni* -> *megvárjuk*; a *másik úgy érezheti, hogy nem hallgatják meg* (érezheti) -> *így érzi, hogy meghallgatják* | *hanem érdemes megvárni, amíg befejezi, különben a másik úgy érezheti, hogy nem hallgatják meg* |
| 0175 | **valódi** | *Ezeket érdemes egy dobozban tartani* -> *egy dobozban tartva* (a felsorolás részeként kötelezőnek hat) | *...kisfűrész kell, és érdemes őket egy dobozban tartani* |
| 0185 | **valódi** | *érdemes később elvégezni, vagy ha lehet, másra bízni* -> *későbbre vagy másra hagyjuk* (a *ha lehet* is elveszett) | *érdemes későbbre halasztani, vagy ha lehet, másra bízni* |
| 0239 | **valódi** | *érdemes előre jelezni* -> *előre jelezni* (kötelezőnek hat) | *akadályoztatás esetén pedig érdemes előre jelezni* |
| 0273 | **valódi** | *az indulás előtti napon érdemes megnézni ... lezárni* -> *az időjárást megnézni és a csapokat lezárni* | *érdemes megnézni az időjárást és lezárni a csapokat* |
| 0277 | **valódi** | *A helyet érdemes távol tartani a tévétől* -> *a tévétől távol* | *a helyet pedig érdemes a tévétől távol tartani* |
| 0279 | **valódi** | *A billentyűzetet és a képernyőt érdemes ... letörölni* -> *...kell ... letörlése mellett* | *a billentyűzetet és a képernyőt pedig érdemes puha ronggyal letörölni* |

Eredmény: **10 valódi (javítva), 1 hamis pozitív (`0061`, amelynél nyelvi javítás is történt)**.

## 3. A 44 hedge-jelzés

Ellenőrző: `fidelity_check3` `LOST` (az inputban védett fenntartó szó, az outputban a csoportjából egyik sincs), 1. batch 18, 2. batch 18,
3. batch 8 jelzés. Mindet az input mondatával és a teljes outputtal együtt olvastam el. **15 valódi vesztés (javítva), 29 hamis pozitív.**

### 3.1 0001-0100 (18 jelzés: 9 valódi, 9 hamis pozitív)

| id | Szó | Ítélet | Indoklás / javítás |
|---|---|---|---|
| 0004 | *esetleg* | hamis pozitív | a *ha esetleg újra esne* feltételes mellékág kimaradt; az output nem állít semmit, ami rá épülne |
| 0028 | *várhatóan* | hamis pozitív | *várhatóan a hónap végére készül el* -> *készülhet el* (-het alak, egyenértékű) |
| 0031 | *lehet* | hamis pozitív | a *helyben is ki lehet tölteni* mellékesség kimaradt; nem hordoz fenntartást |
| 0032 | *legalább* | **valódi** | *legalább egy nappal előbb* -> *egy nappal előbb*; pótolva: *érdemes legalább egy nappal előbb lemondani* |
| 0033 | *szerint* | **valódi** | *A szolgáltató honlapja szerint* hivatkozás elveszett; pótolva |
| 0035 | *szerint* | **valódi** | *Az iskola tájékoztatója szerint* elveszett; pótolva |
| 0038 | *lehet* | **valódi** | *e-mailben ... lehet megtenni* -> *kell jelenteni* (lehetőség -> kötelezettség); *lehet jelenteni*-re javítva |
| 0050 | *általában* | hamis pozitív | *a hatótávolság általában néhány méter* állítást az output teljesen elhagyta (csak *rövid hatótávolságú*), nem állít semmit |
| 0051 | *szerint* | **valódi** | *A könyvtár vezetője szerint* elveszett; pótolva |
| 0055 | *szerint* | **valódi** | *A szakemberek szerint* elveszett; pótolva |
| 0060 | *szerint* | **valódi** | *A vízmű szerint így kisebb a párolgás* hivatkozás elveszett; pótolva |
| 0063 | *lehet* | hamis pozitív | *nem lehet kisebb méretben megkapni?* a vásárló kérdése |
| 0074 | *általában* | **valódi** | *otthon általában csendesebb* -> *a nyugalom* (általános előnyként); pótolva: *az otthon általában nagyobb nyugalma* |
| 0080 | *általában* | hamis pozitív | az *általában a tulajdonos engedélye kell* indoklás kimaradt, az output csak a fenntartás nélküli *az átalakítás korlátozott*-at hozza (ez az inputban is fenntartás nélküli) |
| 0090 | *sokszor* | hamis pozitív | *a megszakítás sokszor rontja a kapcsolatot* állítás kimaradt; a sor más okból (`érdemes`, *érezheti*) javítva, lásd 2. fejezet |
| 0096 | *egyelőre* | **valódi** | *Egyelőre azt tervezik ...* -> *döntenek*; pótolva: *egyelőre a menetrend megnézése után döntenek* |
| 0098 | *szerint* | hamis pozitív | *A másik szerint...* -> *a másik szabad levegőn töltene időt* (a két fél nézete megkülönböztetve) |
| 0099 | *egyelőre* | hamis pozitív | *Egyelőre azt szeretné kipróbálni* -> *először egy hónapra bérelne* (egyenértékű); a sor más okból (*zavarhatja* -> *zavaró*) javítva |

### 3.2 0101-0200 (18 jelzés: 4 valódi, 14 hamis pozitív)

| id | Szó | Ítélet | Indoklás / javítás |
|---|---|---|---|
| 0116 | *gyakran* | **valódi** | *gyakran át kell állítania az óráját* -> *át kell állítani*; pótolva |
| 0116 | *egyes* | hamis pozitív | az *egyes helyeken éjfélkor sütne a nap* feltételes szemléltetés kimaradt |
| 0128 | *még nem* | hamis pozitív | *még nem találtunk megfelelő felületet* -> a kipróbált programok leírása (egyenértékű) |
| 0137 | *lehet* | hamis pozitív | *meg kell újítani, ezt a pénztárnál vagy az alkalmazásban lehet* -> *a pénztárnál vagy az alkalmazásban kell megújítani*: a két csatorna és a kötelezettség is megvan |
| 0139 | *lehet* | hamis pozitív | *csak előre egyeztetett időpontban lehet bemenni* -> *máskor csak időpontra* (egyenértékű) |
| 0152 | *szerint* | hamis pozitív | *A szervezők szerint a cél...* -> *A szervezők ... remélik* (a hivatkozás megmaradt) |
| 0153 | *szerint* | **valódi** | *A meteorológusok szerint* elveszett (a *várható -> lehet, akár* egyenértékű); pótolva |
| 0160 | *szerint*, *sokan* | hamis pozitív (2 jelzés) | a *szervezők szerint ... sokan csak hétvégén érnek rá* mondat az outputból teljesen kimaradt |
| 0170 | *gyakran* | hamis pozitív | *Milyen gyakran kell öntözni?* kérdőszó a vásárló kérdésében |
| 0172 | *szerint* | hamis pozitív | *a napi órarend szerint* nem hivatkozás |
| 0181 | *szerint* | hamis pozitív | *anyaga szerint* nem hivatkozás |
| 0185 | *lehet* | **valódi** | *vagy ha lehet, másra bízni* elveszett; pótolva (lásd 2. fejezet) |
| 0188 | *gyakori* | hamis pozitív | *a pontos gyakoriság* főnév, nem fenntartás |
| 0191 | *szerint* | **valódi** | *a szerelő szerint az akkumulátor lemerülhet* hivatkozás elveszett; pótolva |
| 0192 | *lehet* | hamis pozitív | *nem lehet vele úgy kirándulni* -> *kirándulásra nem vihető* (egyenértékű) |
| 0196 | *közel* | hamis pozitív | *közel van a munkahely* -> *közeli munkahely* |
| 0200 | *gyakran* | hamis pozitív | *attól tartanak, hogy ... gyakran foglalt lenne* -> *a foglaltságtól tart* (a *tart* fenntartás megmarad) |

### 3.3 0201-0300 (8 jelzés: 2 valódi, 6 hamis pozitív)

| id | Szó | Ítélet | Indoklás / javítás |
|---|---|---|---|
| 0216 | *közel* | **valódi** | *közel sík terület* -> *sík*; pótolva: *alacsony, közel sík* |
| 0231 | *lehet* | hamis pozitív | *igazolással lehet igényelni* -> *igazolás kell* (az *általában* megmaradt) |
| 0237 | *lehet* | hamis pozitív | *általában nem lehet visszatéríteni* -> *általában nem térül vissza* |
| 0252 | *egyes* | **valódi** | *Az utak egyes szakaszain síkosság is előfordulhat* -> *Az utakon*; pótolva |
| 0284 | *lehet* | hamis pozitív | *A terv nem lehet túl szoros ... kell időt hagyni* -> *hagyni kell időt* (egyenértékű) |
| 0287 | *általában* | hamis pozitív | *általában olcsóbb* állítás kimaradt, az output nem állít árat |
| 0289 | *gyakran* | hamis pozitív | *gyakran a legjobb élmények* megjegyzés kimaradt; a napi szabad idő tanácsa *érdemes*-szel megmaradt |
| 0299 | *gyakran* | hamis pozitív | *gyakran újat kellene venni* kimaradt (az output a szobanövényt választja); a sor más okból (*díszíthet*) javítva |

**Összesítés: 15 valódi (javítva) + 29 hamis pozitív = 44.**

### 3.4 Az `ADDED` és egyéb jelzések (hamis pozitívok, módosítatlanul)

| id | Jelzés | Indoklás |
|---|---|---|
| 0067, 0068, 0263, 0264, 0266 (+ 0461, 0462, 0467, 0469, 0470) | új *szerint* az outputban | beszélgetés-szereplő megszólalása (*B szerint ...*, *a csomag szerint*), az inputban a szereplő neve (*A:*, *B:*, *Eladó:*) áll |
| 0131 | új *szerint* | *a késés napjai szerint* nem hivatkozás (*a késés napjainak számától függ*) |
| 0153 | új *akár* | *elérheti a harmincöt fokot* -> *akár harmincöt fokos hőség is lehet* (egyenértékű; a sor a *szerint* miatt javítva) |
| 0048, 0117, 0438 | új tagadás | *ne legyen elavult* (a *különben elavult adatokat őrzünk* párja), *sem változik* (az *arány változatlan marad* párja), *ha nem ürítették ki* (*mégsem ürítették ki*) |
| 0488 | *egyes* | *az egyes megállókat* = *mindegyik megállót*, nem fenntartás |

## 4. A 37 közel azonos instruction-pár és a sablonos nyitások

**Ok.** Az 1-2. batchben (0001-0200) az instructionök típusonként rögzített keretek voltak (*"Foglald össze egy-két mondatban a következő
szöveget / beszélgetést / helyzetet."*, *"Sűrítsd egyetlen / két mondatba az alább olvasható történetet."*, *"Mi a lényege az alábbi X-nek? Foglald össze
röviden."*). Az inputokban különböztek, az instructionben csak egy főnév vagy a mondatszám. A `dataset_dedupe.py` az
instruction+input együttesét hasonlítja, ezért a batchenkénti futások nem jelezték; csomagszinten, csak az instruction-szövegre mérve látszott.

**Javítás (két kör, 115 instruction átírva a `clean` fájlokban):**

1. a 37 pár (>= 0.9) mind a 68 sora: 68 kézzel írt, a sor saját témájára és outputjára kérdező instruction (`INS` az 1. kör naplójában);
2. az így megmaradó 47 sor, amelyek még >= 0.85 hasonlósággal álltak párban (*"Mi a lényege az alábbi X-nek? Foglald össze röviden."* keretek): újabb 47 átírás.

Az átírás elvei: az instruction a sor konkrét témájára kérdez (*vízóra*, *hőszigetelés*, *biztosíték*...), változatos nyitással (*Mi, Hogyan, Milyen,
Ismertesd, Magyarázd el, Sorold fel, Kap-e...*); a mondatszám-megnevezés (*egy mondatban / két mondatban / egy-két mondatban*) csak akkor maradt, ha az output mondatszámával egyezik
(ellenőrző: 0 mondatszám-ellentmondás az 500 soron); az új instructionök mind egyediek és nem ütköznek a korpuszban. A teljes átírás a B függelékben.

| Mérőszám | Javítás előtt | Javítás után |
|---|---|---|
| Instruction-párok >= 0.9 / sorok | 37 pár / 68 sor | **0** |
| Instruction-párok >= 0.85 / sorok | 104 pár / 121 sor | **0** (legnagyobb hasonlóság < 0.85, `0032`-`0083`) |
| Instruction-párok >= 0.8 / sorok | 218 pár / 154 sor | 19 pár / 29 sor |
| Különböző kétszavas nyitás (500 sor) | 184 | **252** |
| "Foglald össze" nyitású instruction | 53 (10.6%) | **33 (6.6%)** |
| Mondatszámot megnevező instruction | 253 (51%) | 209 (42%) |
| Generikus deiktikus keret (*következő / alábbi / lenti / mellékelt / alább / itt olvasható*), 1. batch + 2. batch | 87 + 100 | 43 + 25 |
| Kérdő formájú instruction | 124 (25%) | 210 (42%) |

Batchenként (különböző kétszavas nyitás / "Foglald össze" nyitás / mondatszámot nevez):

| Batch | Előtte | Utána |
|---|---|---|
| 0001-0100 | 19 / 29 / 23% | 51 / 17 / 18% |
| 0101-0200 | 19 / 14 / 77% | 75 / 6 / 38% |
| 0201-0300, 0301-0400, 0401-0500 | 56 / 1 / 54%, 67 / 9 / 71%, 79 / 0 / 28% | változatlan |

**Ami nem lett átírva, és miért**: az 1-2. batch maradék, egymástól már 0.85 alatt eltérő generikus instructionjei (pl. *"Foglald össze röviden az alábbi
cikket."*, 43 + 25 sor). Ezek nem hibásak és nem duplikátumok, természetes feladat-megfogalmazások egy összegző adatkészletben; a "túl sablonos"
kifogás tárgya a szinte azonos párok voltak, ezek megszűntek. A maradék a 9. fejezetben, korlátként szerepel.

## 5. Az audit során talált, a listákon nem szereplő javítások

A három lista mellett három független szűrőt futtattam az 500 soron (lásd 8. fejezet), és ezek 14 további sort érintettek:

| id | Kategória | Mi volt a hiba | Javítás |
|---|---|---|---|
| 0023 | fenntartás | *A költségkeret eddig nem lépte túl* -> *a költségek ... kereten belül maradtak* (*eddig* elveszett) | *eddig a tervezett kereten belül maradtak* |
| 0029 | fenntartás | *kettő még bizonytalan* -> *kettő bizonytalan* | *kettő még bizonytalan* |
| 0030 | fenntartás | *a dátum még változhat* -> *a dátum változhat* | *a dátum még változhat* |
| 0059 | fenntartás | *néha előfordul, hogy egy-egy könyv sokáig áll* -> *sokáig a polcon marad* (*néha* elveszett) | *néha egy-egy könyv sokáig a polcon marad* |
| 0061 | nyelvi | lásd 2. fejezet | újraírva |
| 0086 | ajánlás->tény | *Évente egyszer érdemes átnézni* -> *évente át kell nézni* | *évente érdemes átnézni őket* |
| 0089 | fenntartás | *a legtöbb zöldségnek* -> *ehhez*, *kiszáradhat* -> *kiszárad* | *ehhez a legtöbb zöldségnek ... a doboz földje pedig gyorsan kiszáradhat* |
| 0099 | fenntartás | *zavarhatja a család mindennapjait* -> *a családot zavaró otthoni munka* (lehetőség -> tény) | *az olcsóbb otthoni munka (zavarhatja a családot)* |
| 0108 | fenntartás | *néhány közülük ehető lenne* -> *néhány ehető* (feltételes mód) | *néhány ehető lenne* |
| 0118 | fenntartás + nyelvi | *gyakran szerepelnek varázslatos lények* -> *varázslatos elemekkel teli*; a javítás után kettős *és* | *gyakran szerepelnek varázslatos elemek, többnyire a jó győz, ...* |
| 0147 | jelentés | *az elhasznált elemeket ... kell leadni* -> *mindkettőt ... kell leadni* | *az elhasznált elemeket gyűjtőhelyen kell leadni* |
| 0189 | ajánlás->tény | *Érdemes konkrétan fogalmazni* -> *konkrét kérdés kell* | *érdemes konkrétan kérdezni* |
| 0280 | fenntartás | *filmet is nézhetünk* -> *filmnézéssel* (lehetőség -> terv) | *filmet is nézhetnek* |
| 0299 | fenntartás | *sokáig díszíthet* -> *sokáig díszít* | *sokáig díszíthet* |

## 6. Amit az audit megerősített (nem módosítva)

- **Batch 4-5 (0301-0500)**: a szigorított ellenőrző 0 valódi vesztést, 0 *érdemes -> tény* átalakulást ad; a szószintű és modális ellenőrzés soraira (0301-0500) 0 javítás.
- **Ajánlás/óvatosság "lenne" feltételes mód**: a 0292, 0294, 0295, 0296, 0298, 0300 és társai döntési helyzeteknél a *lenne* -> jelen idejű előny/hátrány felsorolás a műfaj természetes tömörítése (a mérlegelés két opció tulajdonságait írja le), nem tényállítássá alakított óvatos állítás; módosítatlanul maradt.
- **`0071`**: *Az almát és a diót csak akkor vegyük meg, ha nem drágák* -> *csak akkor kell megvenni*: a bevásárlólista feltételes terve, nem ajánlás; módosítatlan.
- **`0137`, `0139`**: lásd 3.2.

## 7. Módosítatlan fájlok, nyomonkövethetőség

- `data/raw/claude_summary_*_raw.jsonl`: **nem módosítva** (a `git status` szerint csak a `clean` fájlok változtak). A `raw` és a `clean` így eltér: 0001-0100: 53 sor, 0101-0200: 78 sor, 0201-0300: 8 sor, 0301-0400 és 0401-0500: 0 sor (összesen 139 sor, megegyezik a módosított sorok számával). A javítás előtt mind az 5 batchen `raw` == `clean` volt.
- Minden javítás egy naplózó szkripttel készült, amely csere előtt ellenőrizte, hogy a régi szöveg pontosan egyszer szerepel az adott mezőben; a teljes régi -> új lista az A és B függelékben.
- A quality_notes és a `tags` nem módosult; a `source`, `difficulty`, `category` változatlan.

## 8. Módszer és a kézi átolvasás fedettsége

Automatikus (mind az 500 soron, a javítás előtt és után is): `dataset_validate`, `dataset_dedupe`, `dataset_score`, `check_summary` (forma, tömörség,
másolás, nyelv, safety, mondatszám), a szigorított `fidelity_check3` (védett hedge-csoportok, hivatkozás, *érdemes -> tény*, tagadás, ellentétpár, idő-/számszó,
szótő), a szószintű fenntartás-ellenőrzés (`word_drops`, minden fenntartó szóra soronként: input igen, output nem), a **modális-alak ellenőrzés** (az inputban -hat/-het/-ható/-hető vagy *lenne/volna/kellene*
alak, az outputban egy sem: 67 sor), csomagszintű instruction-, output- és quality_notes-hasonlóság, kereszt-dedupe a korpusz többi 2500 sora ellen.

Kézi átolvasás az 1-3. batchen: a listákon szereplő sorok, a három szűrő (szószintű, tagadás-elmaradás 52 sor, számnév-elmaradás 23 sor, ellentétpár/idő 15 sor,
modális-alak 67 sor) minden találata, a 68 + 47 instruction-sor, valamint egy **véletlen minta** a még nem látott sorokból (seed 20260921, 14 / 13 / 13 sor,
összesen 40 sor, teljes input és output egymás mellett). A minta 40 sorából 2 apró csúszás derült ki (`0108`, `0280`, *lenne*, *nézhetünk*), amelyeket a modális-alak ellenőrzés
függetlenül is jelzett, tehát a mintavétel nem talált olyat, amit az automatikus szűrők ne találtak volna (0 egyedi találat).

| Batch | Legalább az outputjával (és a jelzett inputmondattal) átnézett sor | Teljes input+output átolvasás (minta és listák) |
|---|---|---|
| 0001-0100 | 86 / 100 | a 11-es lista és a 18 hedge-jelzés sorai, valamint a minta |
| 0101-0200 | 92 / 100 | ugyanígy |
| 0201-0300 | 66 / 100 | ugyanígy |
| 0301-0400, 0401-0500 | a batch reportok szerinti 40 + 40 soros minta és a teljes szószintű ellenőrzés | - |

A 300 sorból **244 sort** néztem át az auditban valamilyen formában; **56 sor** (0001-0300 között) semelyik szűrőben és a mintában sem szerepelt, azokra az automatikus szűrők vonatkoznak (0 jelzés).

## 9. Korlátok és dokumentált, nem blokkoló tételek

1. **56 sor** az 1-3. batchben nem lett soronként átolvasva (lásd 8. fejezet). A 40 soros véletlen minta 0 egyedi találatot adott, ez alapján a maradék hibaaránya alacsony, de nem zérus.
2. **Maradék generikus instructionök** az 1-2. batchben (43 + 25 sor, mind egymástól < 0.85 hasonlóságú). Ez stílus, nem duplikáció; ha a jövő tréninganyaga igényli, külön körben átírhatók.
3. **A fenntartás-ellenőrzés heurisztika.** A csoportszintű ellenőrző nem látja a hatókör-elcsúszást; a szószintű lista és a modális-alak szűrő ezt jelentősen csökkenti, de kézi olvasást nem helyettesít.
4. **A `raw` és a `clean` eltér** 139 sorban (szándékos, dokumentált). A jövőbeli felhasználásnál a `clean` az irányadó.
5. **`összefoglalás` tag 16.7%** (500 / 3000): a csomagot jelölő kategória-tag; a topic report jelzi, a kezelése külön jóváhagyás.
6. **Az ellenőrző scriptek** (`check_summary.py`, `fidelity_check3.py`, `word_drops.py`, `cross_all.py`, `pkg_check.py`, a javító szkriptek) **a repón kívül** vannak; a `tools/` alá emelésük külön jóváhagyás kérdése.
7. **Az 1-5. batch reportjai** a saját idejük állapotában maradnak (a javítások előtti számokkal, pl. az 1-2. batch instruction-statisztikái); az aktuális állapotra ez a report az irányadó.

## 10. Regressziós teszt és korpusz

- `tests/test_v1_7_4_dataset_foundation.py`: minden teszt sikeres, **STÁTUSZ: STABIL**.
- `dataset_topic_report.py data/clean`: 3000 sor, 34 fájl; `összefoglalás` 500 (16.7%, várható, dokumentált), majd `fizika` 4.0%, `gazdaság` 3.6%; más túlreprezentált tag nincs.
- Teljes clean korpusz: **3000 sor, 3000 egyedi id** (1000 simple_qa + 1000 explanation + 500 step_by_step + 500 summary).

## 11. Amit ez a kör NEM tett

- Nem indított tanítást, nem módosított webapp/backend kódot, nem törölt és nem írt felül semmit (a `raw` fájlokhoz sem nyúlt).
- Nem kezdte el az 5. csomagot.
- Nem emelte a scripteket a repóba, és nem módosította a topic report tag-kezelését.
- Nem írta át az 1-2. batch maradék generikus instructionjeit (9. fejezet, 2. pont).

---

## Végső összegzés

- **summary 500 / 500: STABIL.**
- Javított sorok: **139** (38 output, 115 instruction, 14 mindkettő); output-javítások: 12 ajánlás->tény, 23 fenntartás/hivatkozás, 4 jelentés/nyelvi.
- Hamis pozitívok: **29** hedge-jelzés + **1** *érdemes*-sor + 12 *ADDED* sor + 3 új-tagadás + 1 *egyes* (mind módosítatlanul, indoklással).
- A nyitott tételek: 11 *érdemes* sor -> 10 javítva; 44 hedge-jelzés -> 15 javítva; 37 instruction-pár (68 sor) -> 0 pár >= 0.85 maradt (115 instruction átírva).
- Nyitott blokkoló tétel: **nincs**. Dokumentált korlát: 56 sor soronkénti átolvasás nélkül, az 1-2. batch maradék generikus instructionjei, scriptek a repón kívül.
- Teljes clean korpusz: **3000 sor**. Regressziós teszt: **STABIL**.

**STÁTUSZ: STABIL.**

---

## A függelék: output-javítások (régi -> új részlet)

| id | Kategória | Régi (részlet vagy teljes output) | Új |
|---|---|---|---|
| 0016 | ADVICE | különbözőnél a legkisebb közös többszörösre bővítünk. | különbözőnél érdemes a legkisebb közös többszörösre bővíteni. |
| 0023 | HEDGE | a költségek pedig a tervezett kereten belül maradtak. | a költségek pedig eddig a tervezett kereten belül maradtak. |
| 0027 | ADVICE | egy szűk földúton lassítani kell, | egy szűk földúton érdemes lassítani, |
| 0029 | HEDGE | kettő bizonytalan, három most kezdődik | kettő még bizonytalan, három most kezdődik |
| 0030 | HEDGE | de a dátum változhat, | de a dátum még változhat, |
| 0032 | HEDGE | ha nem tudunk elmenni, érdemes egy nappal előbb lemondani, | ha nem tudunk elmenni, érdemes legalább egy nappal előbb lemondani, |
| 0033 | HEDGE | A számlával kapcsolatos észrevételt írásban vagy az ügyfélportálon lehet jelezni az ügyfélazonosítóval | A szolgáltató honlapja szerint a számlával kapcsolatos észrevételt írásban vagy az ügyfélportálon lehet jelezni az ügyfélazonosítóval |
| 0035 | HEDGE | A beiratkozáshoz a gyermek születési anyakönyvi kivonata | Az iskola tájékoztatója szerint a beiratkozáshoz a gyermek születési anyakönyvi kivonata |
| 0038 | MEANING | e-mailben vagy a kihelyezett füzetben kell jelenteni | e-mailben vagy a kihelyezett füzetben lehet jelenteni |
| 0051 | HEDGE | és az első héten az átlagosnál több új tag iratkozott be. | és a könyvtár vezetője szerint az első héten az átlagosnál több új tag iratkozott be. |
| 0055 | HEDGE | Az esősebb tavasz vegyes hatású volt a gyümölcsösöknek: | A szakemberek szerint az esősebb tavasz vegyes hatású volt a gyümölcsösöknek: |
| 0059 | HEDGE | bár egy-egy könyv sokáig a polcon marad. | bár néha egy-egy könyv sokáig a polcon marad. |
| 0060 | HEDGE | mert így kisebb a párolgás és mindenkinek jut víz; | mert a vízmű szerint így kisebb a párolgás és mindenkinek jut víz; |
| 0061 | MEANING | A még ma a piacra megy, mert holnapra esőt mondtak, és B paradicsomot és sajtot kér tőle, ha van. | B szerint ma jobb a piacra menni, mert holnapra esőt mondtak, ezért A most indul, B pedig paradicsomot és sajtot kér tőle, ha van. |
| 0073 | ADVICE | A túrához bejárt cipő, esőkabát, víz, nasi, térkép, zseblámpa, elsősegély-csomag és napszemüveg kell. | A túrához érdemes bejárt cipőt, esőkabátot, vizet, nasit, térképet, zseblámpát, elsősegély-csomagot és napszemüveget összecsomagolni. |
| 0074 | HEDGE | a rugalmas időbeosztás és a nyugalom, | a rugalmas időbeosztás és az otthon általában nagyobb nyugalma, |
| 0086 | ADVICE | évente át kell nézni őket, | évente érdemes átnézni őket, |
| 0089 | HEDGE | ehhez sok fény és rendszeres öntözés kell, nyáron pedig a doboz földje gyorsabban kiszárad, ezért többet kell locsolni. | ehhez a legtöbb zöldségnek sok fény és rendszeres öntözés kell, a doboz földje pedig gyorsan kiszáradhat, ezért nyáron gyakrabban kell locsolni. |
| 0090 | ADVICE | és nem adunk gyors tanácsot, hanem megvárjuk, amíg befejezi, mert így érzi, hogy meghallgatják. | és nem adunk gyors tanácsot, hanem érdemes megvárni, amíg befejezi, különben a másik úgy érezheti, hogy nem hallgatják meg. |
| 0096 | HEDGE | és a menetrend megnézése után döntenek. | és egyelőre a menetrend megnézése után döntenek. |
| 0099 | HEDGE | és az olcsóbb, de a családot zavaró otthoni munka között | és az olcsóbb otthoni munka (zavarhatja a családot) között |
| 0108 | HEDGE | és kiderült, hogy néhány ehető, de nem kockáztattak. | és kiderült, hogy néhány ehető lenne, de nem kockáztattak. |
| 0116 | HEDGE | Távoli utazáskor ezért át kell állítani az órát. | Távoli utazáskor ezért gyakran át kell állítani az órát. |
| 0118 | HEDGE | A mese varázslatos elemekkel teli tanulságos történet, amelyben többnyire a jó győz, | A mese tanulságos történet, amelyben gyakran szerepelnek varázslatos elemek, és többnyire a jó győz, |
| 0118 | MEANING | amelyben gyakran szerepelnek varázslatos elemek, és többnyire a jó győz, és a népmesék | amelyben gyakran szerepelnek varázslatos elemek, többnyire a jó győz, és a népmesék |
| 0147 | MEANING | és mindkettőt gyűjtőhelyen kell leadni. | és az elhasznált elemeket gyűjtőhelyen kell leadni. |
| 0153 | HEDGE | A következő napokban több helyen akár harmincöt fokos hőség is lehet, | A meteorológusok szerint a következő napokban több helyen akár harmincöt fokos hőség is lehet, |
| 0175 | ADVICE | és kisfűrész kell, egy dobozban tartva. | és kisfűrész kell, és érdemes őket egy dobozban tartani. |
| 0185 | ADVICE | a kevésbé fontosakat pedig későbbre vagy másra hagyjuk. | a kevésbé fontosakat pedig érdemes későbbre halasztani, vagy ha lehet, másra bízni. |
| 0189 | ADVICE | A pontos válaszhoz konkrét kérdés kell, mert | A pontos válaszhoz érdemes konkrétan kérdezni, mert |
| 0191 | HEDGE | de az akkumulátor hamar lemerülhet, | de a szerelő szerint az akkumulátor hamar lemerülhet, |
| 0216 | HEDGE | A síkság alacsony és sík, | A síkság alacsony, közel sík, |
| 0239 | ADVICE | akadályoztatás esetén pedig előre jelezni. | akadályoztatás esetén pedig érdemes előre jelezni. |
| 0252 | HEDGE | Az utakon síkosság is előfordulhat, | Az utak egyes szakaszain síkosság is előfordulhat, |
| 0273 | ADVICE | az indulás előtti napon pedig az időjárást megnézni és a csapokat lezárni. | az indulás előtti napon pedig érdemes megnézni az időjárást és lezárni a csapokat. |
| 0277 | ADVICE | kell, a tévétől távol, hogy kevesebb legyen a zavaró tényező. | kell, a helyet pedig érdemes a tévétől távol tartani, hogy kevesebb legyen a zavaró tényező. |
| 0279 | ADVICE | kell, a billentyűzet és a képernyő puha ronggyal való letörlése mellett. | kell, a billentyűzetet és a képernyőt pedig érdemes puha ronggyal letörölni. |
| 0280 | HEDGE | esőben séta helyett filmnézéssel. | esőben pedig séta helyett filmet is nézhetnek. |
| 0299 | HEDGE | és sokáig díszít, bár gondozást kér. | és sokáig díszíthet, bár gondozást kér. |

Kategóriák: `ADVICE` = ajánlás (*érdemes*) tényállítássá/kötelezettséggé alakult; `HEDGE` = elveszett fenntartás vagy hivatkozás; `MEANING` = jelentésbeli csúszás vagy nyelvi érthetőség. A `0118` két lépésben javult (fenntartás, majd nyelvi); a `0061` és `0073` teljes outputja szerepel.

## B függelék: instruction-átírások (régi -> új)

| id | Régi instruction | Új instruction |
|---|---|---|
| 0004 | Foglald össze egy-két mondatban az alábbi szöveget. | Mi történt a szombati kerti sütögetéssel az eső miatt? Egy-két mondatban válaszolj. |
| 0009 | Sűrítsd egy-két mondatba az alábbi szöveget. | Mit kértek kölcsön az új szomszédok, és hogyan köszönték meg a segítséget? |
| 0013 | Mi a lényege az alábbi tananyagnak? Foglald össze röviden. | Miért szabadabb a magyar szórend? Egy mondatban magyarázd el a ragozó nyelv lényegét. |
| 0014 | Foglald össze egy mondatban a következő szöveget. | Mi az elosztott ismétlés, és mire a leghasznosabb? Egy mondatban válaszolj. |
| 0023 | Mi a projektjegyzet lényege? Foglald össze röviden. | Hol tart a konyhafelújítás, és mi jön a csempézés után? |
| 0033 | Mi a lényege az alábbi tájékoztatónak? Foglald össze röviden. | Hol és hogyan jelezhető a számlával kapcsolatos észrevétel, és mennyi idő a válaszadás? |
| 0034 | Foglald össze egy-két mondatban a következő szöveget. | Mi a teendő, ha a futár nem talált otthon, és meddig vehető át a csomag? |
| 0036 | Adj rövid összegzést az alábbi hivatalos leírásról. | Hogyan újítható meg a könyvtári tagság, és mi a teendő elveszett kártyánál? |
| 0037 | Mi a teendő a szöveg szerint? Foglald össze röviden. | Hogyan jelenthető be a vízóra állása, és mikor ellenőrizhet a szolgáltató? |
| 0038 | Sűrítsd egy-két mondatba az alábbi ügyintézési szöveget. | Hogyan jelenthető be a kiégett lépcsőházi lámpa a közös képviselőnek, és mi történik ezután? |
| 0041 | Készíts tömör összefoglalót a következő műszaki szövegről. | Mi öregíti a lítium-ion akkumulátort, és mit érdemes tenni ellene? |
| 0043 | Mi a lényege az alábbi magyarázatnak? Foglald össze röviden. | Hogyan nyomtat a tintasugaras nyomtató, és mi történik, ha sokáig áll? |
| 0044 | Foglald össze röviden a következő szöveget. | Hogyan melegít a mikrohullámú sütő, és mit nem szabad beletenni? |
| 0046 | Adj rövid összegzést az alábbi műszaki leírásról. | Miben különbözik a merevlemez és az SSD? |
| 0048 | Sűrítsd egy-két mondatba az alábbi magyarázatot. | Mit érdemes tudni az adatok biztonsági mentéséről? Egy-két mondatban válaszolj. |
| 0049 | Készíts tömör összefoglalót a következő technikai szövegről. | Hogyan keletkezik a vízkő, és hogyan előzhető meg vagy csökkenthető? |
| 0053 | Foglald össze egy mondatban az alábbi hírt. | Mit ír elő az új piaci szabály, és mit szólnak hozzá az árusok? Egy mondatban. |
| 0056 | Adj rövid összegzést a következő cikkről. | Mit jelent az új kerékpársáv a főutca üzleteinek, és mit mond a városvezetés? |
| 0058 | Sűrítsd egy-két mondatba az alábbi cikkrészletet. | Mit kell tudni a szombati parkbeli koncertről, és mi lesz rossz idő esetén? Egy-két mondatban. |
| 0059 | Készíts tömör összefoglalót a következő hírről. | Mit szólnak a helyiek a kisváros könyvcsere-szekrényéhez? |
| 0060 | Foglald össze röviden az alábbi cikket. | Mit kér a település a lakóktól a forró nyárban, és miért? |
| 0064 | Foglald össze egy-két mondatban a következő beszélgetést. | Miért tolják át a holnapi megbeszélést, és mit kell tennie B-nek? |
| 0066 | Adj rövid összegzést a következő párbeszédről. | Mikor adják vissza a dolgozatot, és mit tehet, aki javítani szeretne? |
| 0067 | Mi a beszélgetés lényege? Foglald össze röviden. | Mennyit főzzék a rizst a csomag és B tapasztalata szerint, és mit tanácsol B a keveréséről? |
| 0068 | Sűrítsd egy-két mondatba az alábbi párbeszédet. | Tengerpart vagy hegyek? Mit szeretnek A és B a nyaraláshoz, és mikor döntenek? Egy-két mondatban. |
| 0069 | Készíts tömör összefoglalót a következő beszélgetésről. | Mit tanácsol B a hibaüzenetet adó nyomtató ügyében? |
| 0070 | Foglald össze röviden az alábbi beszélgetést. | Melyik napra teszik át a tóhoz menést, és miért csak délutántól ér rá B? |
| 0073 | Mi a lista lényege? Foglald össze röviden. | Mit érdemes összecsomagolni egy túrára? |
| 0078 | Sűrítsd egy-két mondatba az alábbi felsorolást. | Milyen szabályokat kell betartani a kiránduláson? Egy-két mondatban. |
| 0079 | Készíts tömör összefoglalót a következő listáról. | Sorold fel tömören a tavaszi kerti teendőket. |
| 0080 | Foglald össze röviden az alábbi listát. | Milyen előnyei és hátrányai vannak a lakásbérlésnek? |
| 0081 | Foglald össze röviden a következő hosszabb szöveget. | Milyen tanácsokat kapunk az idegen nyelv hatékony tanulásához? |
| 0088 | Sűrítsd egy-két mondatba az alábbi hosszabb magyarázatot. | Mondd el tömören a hűtőszekrény havi tisztításának lépéseit. |
| 0093 | Mi a döntés lényege? Foglald össze röviden. | Hogyan oldja meg a szerző a szombati költözési segítség és a családi ebéd ütközését? |
| 0094 | Foglald össze egy-két mondatban a következő helyzetet. | Játszótér vagy közösségi ház legyen a régi iskolaépületből, és mi a következő lépés? |
| 0097 | Mik a szempontok a szöveg szerint? Foglald össze röviden. | Milyen szempontok szólnak a könyvtári esti nyitvatartás meghosszabbítása mellett és ellen? |
| 0098 | Sűrítsd egy-két mondatba az alábbi mérlegelést. | Mit döntött a pár a hétvégi pihenés és a szabad levegős program között? Egy-két mondatban. |
| 0099 | Készíts tömör összefoglalót a következő helyzetről. | Mit mérlegel a kézműves vállalkozó a műhelybérlet és az otthoni munka között? |
| 0100 | Foglald össze röviden a döntési helyzetet. | Milyen érvek szólnak az iskolai mobiltelefon-tilalom mellett és ellen? |
| 0101 | Foglald össze egy mondatban az alábbi történetet. | Hol találta meg végül a szerző a kulcsát, és mit változtatott azóta? |
| 0102 | Foglald össze két mondatban az alábbi történetet. | Két mondatban: mi történt a szerző esernyőjével, és hogyan segítettek a kollégák? |
| 0103 | Egy mondatban mondd el, miről szól a következő történet. | Egy mondatban: mi lett a szerző első, meg nem kelt kenyeréből? |
| 0104 | Két mondatban mondd el, miről szól a következő történet. | Hogyan szökött meg a család kutyája, és ki hozta haza? Két mondatban válaszolj. |
| 0105 | Készíts kétmondatos kivonatot a lenti történetről. | Miért késett az előadás a színházban, és hogyan enyhítették a várakozást? |
| 0106 | Készíts egymondatos kivonatot a lenti történetről. | Ki segített a szerzőnek a defektes kerékpárral, és hogyan hálálta meg? |
| 0108 | Mi derül ki az itt olvasható történetről? Foglald össze röviden. | Miért nem szedtek gombát az erdei kiránduláson, és mit tettek helyette? |
| 0109 | Sűrítsd egyetlen mondatba az alább olvasható történetet. | Egyetlen mondatban meséld el, mit láttak a kertben a család tagjai. |
| 0110 | Sűrítsd két mondatba az alább olvasható történetet. | Hogyan haladtak a szomszéd gyerekek az ötezer darabos kirakóval? |
| 0111 | Rövidítsd egyetlen mondatra a mellékelt tananyagot. | Hogyan keletkezik és terjed a hang, és miért nem terjed légüres térben? |
| 0112 | Rövidítsd két mondatra a mellékelt tananyagot. | Magyarázd el két mondatban, miért változik a Hold látszó alakja. |
| 0113 | Tömörítsd egyetlen mondatba az alábbi tanulási szöveget. | Egyetlen mondatban: mit jelentenek a negatív számok, és hol vannak a számegyenesen? |
| 0114 | Tömörítsd két mondatba az alábbi tanulási szöveget. | Mire jók a szinonimák, és mire kell figyelni a használatukkor? |
| 0115 | Mi derül ki a következő tanulási szövegről? Foglald össze röviden. | Mi a különbség a magma és a láva között a vulkánkitörésnél? |
| 0117 | Adj egy mondatos összegzést a lenti tanulási szövegről. | Mi az arány, és mi történik vele, ha az egész mennyiséget megkétszerezzük? Egy mondatban. |
| 0118 | Fogalmazd meg egy mondatban az itt olvasható tanulási szöveg fő mondanivalóját. | Mi jellemző a mesére mint műfajra? Egy mondatban válaszolj. |
| 0119 | Adj két mondatos összegzést a lenti tanulási szövegről. | Mi okozza az évszakok váltakozását? Két mondatban válaszolj. |
| 0120 | Mondd el újra, rövidebben, egy mondatban az alább olvasható tanulási szöveg tartalmát. | Miért nem tűnik el a só a vízben, és mi marad vissza a párolgás után? |
| 0121 | Adj tömör összefoglalót a mellékelt munkanaplóról. | Hogyan áll a ballagási dekoráció elkészítése, és mi van még hátra? |
| 0122 | Fogalmazd meg két mondatban az itt olvasható munkanapló fő mondanivalóját. | Ismertesd két mondatban a faültetési nap szervezését. |
| 0123 | Mondd el egy mondatban az alábbi projektjegyzet lényegét. | Hol tart a tölgyfa szekrény felújítása, és mi van még hátra? |
| 0124 | Mondd el újra, rövidebben, két mondatban az alább olvasható munkanapló tartalmát. | Mi készült el a padlás kipakolásából, és miről kell még dönteni? |
| 0125 | Mit közöl a következő projektjegyzet? Válaszolj egy mondatban. | Mikor rendelik meg a lakóközösség bicikli-tárolóját, és mitől függ? |
| 0126 | Foglald össze két mondatban a mellékelt munkanaplót. | Hogyan halad a családi fotóalbum digitalizálása, és mikorra lehet kész? Két mondatban. |
| 0127 | Mi a lenti projektjegyzet lényege? Foglald össze röviden. | Mit rendeztek át a gyerekszobában, és miért? |
| 0128 | Mondd el két mondatban az alábbi projektjegyzet lényegét. | Miért akadt el az online énekkurzus szervezése, és mi a terv? |
| 0129 | Foglald össze egy mondatban az itt olvasható projektjegyzetet. | Mennyi ruhát gyűjtöttek eddig, és mit fogadnak el? Egy mondatban. |
| 0130 | Mit közöl a következő projektjegyzet? Válaszolj két mondatban. | Mondd el két mondatban, hogyan készül a szombati házi mozi este. |
| 0131 | Egy mondatban mondd el, miről szól az alább olvasható tájékoztató. | Hogyan kell fizetni a könyvtári késedelmi díjat, és hogyan előzhető meg? |
| 0132 | Mi a lenti tájékoztató lényege? Foglald össze röviden. | Hogyan jelenthető be a szemétszállítási nap módosítása, és mi a teendő, ha nem változik a szállítás? |
| 0133 | Készíts egymondatos kivonatot a mellékelt tájékoztatóról. | Ki és hogyan igazolja a gyerek hiányzását az iskolában? |
| 0136 | Két mondatban mondd el, miről szól az alább olvasható tájékoztató. | Mi az a postai átirányítás, hogyan kérhető, és meddig érvényes? |
| 0138 | Készíts kétmondatos kivonatot a mellékelt tájékoztatóról. | Mikor és hogyan lehet lomot kitenni, és mit nem visznek el? |
| 0140 | Mi derül ki az alábbi ügyintézési leírásról? Foglald össze röviden. | Mit kínál az önkéntes kerékpár-regisztráció, és mit nem garantál? |
| 0141 | Tömörítsd egyetlen mondatba az itt olvasható technikai leírást. | Hogyan érzékeli az érintést a képernyő, és miért nem működik bizonyos kesztyűvel? |
| 0145 | Adj egy mondatos összegzést a mellékelt technikai leírásról. | Merre jár az e-mail a feladótól a címzettig, és mennyi ideig tart? |
| 0146 | Tömörítsd két mondatba az itt olvasható technikai leírást. | Hogyan működik a hőszigetelés, és mi korlátozza a hatását? |
| 0150 | Adj két mondatos összegzést a mellékelt technikai leírásról. | Hogyan véd a biztosíték, és mire kell vigyázni a cseréjénél? |
| 0153 | Mondd el egy mondatban az itt olvasható cikk lényegét. | Milyen hőségre számítanak a következő napokban, és mit kérnek a hatóságok? |
| 0155 | Mit közöl az alább olvasható cikk? Válaszolj egy mondatban. | Hogyan alakult az iskolai olvasóverseny, és ki nyert? |
| 0157 | Mi a mellékelt cikk lényege? Foglald össze röviden. | Mi újult meg a lakótelepi játszótéren, és mikor lesz a megnyitó? |
| 0158 | Mondd el két mondatban az itt olvasható cikk lényegét. | Mikor tart nyitva a termelői piac, és mit kérnek a szervezők a vásárlóktól? |
| 0160 | Mit közöl az alább olvasható cikk? Válaszolj két mondatban. | Milyen programokat kínál a múzeumi éjszaka, és hol kell regisztrálni? |
| 0161 | Egy mondatban mondd el, miről szól a következő beszélgetés. | Mit egyeztet A és B a közös ebédrendelésről? |
| 0162 | Mi a mellékelt párbeszéd lényege? Foglald össze röviden. | Mit mond az egyik szomszéd a lomtalanításról, és mi a teendő az elektromos készülékekkel? |
| 0163 | Készíts egymondatos kivonatot a lenti beszélgetésről. | Mit főznek vasárnapra, és miért lesz mégis kétféle leves? |
| 0164 | Foglald össze két mondatban az alábbi beszélgetést. | Kap-e haladékot a diák a dolgozat leadására, és meddig? Két mondatban. |
| 0166 | Két mondatban mondd el, miről szól a következő beszélgetés. | Kap-e asztalt a két fős vendég, és mit ajánlanak neki a várakozásra? |
| 0168 | Készíts kétmondatos kivonatot a lenti beszélgetésről. | Miért nem vihette el az olvasó az olaszországi útikönyvet, és mit tesz a könyvtáros? |
| 0170 | Mi derül ki az itt olvasható beszélgetésről? Foglald össze röviden. | Milyen növényt ajánl a kertész a rossz fényviszonyú nappalira, és hogyan kell öntözni? |
| 0171 | Tömörítsd egyetlen mondatba az alábbi listát. | Mit tervez a szerző szombatra és vasárnapra? Egyetlen mondatban. |
| 0173 | Mi derül ki a következő listáról? Foglald össze röviden. | Mi kell a szülinapi bulihoz? |
| 0175 | Adj egy mondatos összegzést a lenti listáról. | Mely szerszámok tartoznak az otthoni alapkészletbe, és hogyan érdemes tárolni őket? |
| 0176 | Tömörítsd két mondatba az alábbi listát. | Milyen lépésekből áll a szerző reggeli rutinja? Két mondatban. |
| 0177 | Fogalmazd meg egy mondatban az itt olvasható lista fő mondanivalóját. | Mi kerül az ünnepi vacsora étlapjára, és mit isznak a gyerekek? Egy mondatban. |
| 0179 | Mondd el újra, rövidebben, egy mondatban az alább olvasható lista tartalmát. | Milyen sorrendben végezzük a tavaszi nagytakarítást? |
| 0180 | Adj két mondatos összegzést a lenti listáról. | Mi kell a gyerekfoglalkozáshoz, és milyen legyen az olló és a ragasztó? |
| 0181 | Adj tömör összefoglalót a mellékelt magyarázatról. | Mit jelent a szelektív hulladékgyűjtés, és miért érdemes kiöblíteni az edényeket? |
| 0182 | Fogalmazd meg két mondatban az itt olvasható magyarázat fő mondanivalóját. | Hogyan működik a napelem, és mit tudni a költségéről és a hosszú távú megtakarításról? |
| 0183 | Mondd el egy mondatban az alábbi szöveg lényegét. | Milyen jegyzetelési módszereket említ a szöveg, és mit érdemes velük tenni? |
| 0184 | Mondd el újra, rövidebben, két mondatban az alább olvasható magyarázat tartalmát. | Mitől működik jól a csapatmunka? Két mondatban válaszolj. |
| 0185 | Mit közöl a következő szöveg? Válaszolj egy mondatban. | Mit jelent az időgazdálkodás, és mit tegyünk a kevésbé fontos feladatokkal? |
| 0186 | Foglald össze két mondatban a mellékelt magyarázatot. | Hogyan épül fel a hivatalos levél, és mit érdemes elküldés előtt tenni? |
| 0187 | Mi a lenti szöveg lényege? Foglald össze röviden. | Hogyan kell biztonságosan átkelni az úttesten gyalogosként? |
| 0188 | Mondd el két mondatban az alábbi szöveg lényegét. | Hogyan öntözzük helyesen a szobanövényeket? |
| 0189 | Foglald össze egy mondatban az itt olvasható szöveget. | Mitől lesz jó egy kérdés? Egy mondatban válaszolj. |
| 0190 | Mit közöl a következő szöveg? Válaszolj két mondatban. | Hogyan szellőztessünk helyesen, és mire figyeljünk a páraforrásoknál? |
| 0191 | Egy mondatban mondd el, miről szól az alább olvasható mérlegelés. | Javíttassa a telefonját, vagy vegyen újat? Egy mondatban: mit mérlegel a szerző? |
| 0192 | Mi a lenti mérlegelés lényege? Foglald össze röviden. | Kutya vagy macska legyen a családban? Mit mérlegelnek, és mit tesznek előbb? Két mondatban. |
| 0193 | Készíts egymondatos kivonatot a mellékelt mérlegelésről. | Busz vagy kerékpár: mit választ a szerző a munkába járáshoz? |
| 0195 | Foglald össze röviden az alábbi döntési helyzetet. | Hol tartsa a család a karácsonyi vacsorát, és mit döntöttek? |
| 0196 | Két mondatban mondd el, miről szól az alább olvasható mérlegelés. | Városban maradjon a pár, vagy költözzön faluba? Két mondatban mérlegeld, és mondd meg, mit lépnek előbb. |
| 0197 | Sűrítsd egyetlen mondatba a következő döntési helyzetet. | Melyik önkéntes lehetőséget választotta a szerző, és miért? |
| 0198 | Készíts kétmondatos kivonatot a mellékelt mérlegelésről. | Napközi vagy zeneiskola: mit mérlegelnek a szülők, és mit kérnek a gyerek kedvéért? |
| 0199 | Mi derül ki az alábbi döntési helyzetről? Foglald össze röviden. | Házi edzés vagy edzőterem: mit mérlegel a szerző, és mikor vált? |
| 0200 | Sűrítsd két mondatba a következő döntési helyzetet. | Milyen előnyt remél a közösségi ház a nagyterem kiadásától, és mitől tartanak? |
