# 5. csomag záró audit/fix report - noisy_input_0001-0500

**Verdikt: STABIL.** A `noisy_input` csomag **500 / 500 clean, 0 rejected** maradt. Az audit 219 sor metaadatát/szövegét finomította (ebből 62 sor input/output szövege, 132 sor csak `difficulty`), egy sort sem kellett elvetni, és egy sor sem került át a `rejected` alá.
A javítások kizárólag a `data/clean/claude_noisy_input_*_clean.jsonl` fájlokban történtek; a **raw fájlok változatlanok** (`git status`/`git diff` a `data/raw` alatt: 0 változás), nem törlődött semmi, tanítás nem indult, webapp/backend kód nem módosult.

## 0. Hatókör és módszer

- Vizsgált anyag: mind az 5 clean fájl (`0001_0100` ... `0401_0500`), 500 sor; a keresztellenőrzéshez a teljes clean korpusz (3500 sor: 3000 nem-noisy + 500 noisy).
- Az audit szkriptjei (`pkg_audit1-3.py`, `pkg_cross.py`, `fix_pkg.py`, `finalize_pkg.py`) a repón kívül vannak (scratchpad); a `tools/` alá emelésük külön jóváhagyandó. Az összes változtatás előtt az öt clean fájlról mentés készült, a változáslista a mentés és a végleges fájlok különbségéből lett levezetve (7. fejezet).
- Elv: ami mérhető hiba volt (hiányzó szóalak-javítás, alaptalan címke, hibás jegyzet-idézet, túl hasonló sor), azt javítottam; ami mintázat-koncentráció volt (`szval`, `tök`, `szóval`), azt mérséklem, de a felhasználó hangját nem írom át; ami a csomag tervezéséből fakad (a `zajos bemenet` jelölőcímke aránya, az 1. batch egy-címkés sémája), azt dokumentálom.

## 1. Csomagszintű ellenőrzések: előtte és utána

| Ellenőrzés | Audit előtt | Audit után |
|---|---|---|
| ID folytonosság | `noisy_input_0001`-`0500` hézag nélkül, 500 egyedi | változatlan |
| Schema (`dataset_validate.py`, fájlonként és 500 sor egyben) | 500 / 500 valid | **500 / 500 valid**, 0 rejected |
| Mezősorrend, `category`, `source`, `tags[0:2]` | mind az 500 sorban azonos | változatlan |
| `input` != `output` | 500 / 500 | 500 / 500 |
| Valódi szóalak-szintű javítás soronként | **7 sor nélküle** (1. batch: `0006, 0023, 0031, 0037, 0047, 0053, 0069`, csak szóköz/írásjel/nagybetű), 5 sor csak szóhatár-, 3 sor csak számjegy-javítással | **0 sor nélküle**: 492 sor betűszintű javítással, 5 sor csak szóhatár-, 3 sor csak számjegy-javítással (2.5. fejezet) |
| Dedupe batchen belül (id / instruction+input / output) | 0 / 0 / 0 mind az 5 batchen | 0 / 0 / 0; a 500 sor egyben (`dataset_dedupe.py`): 0 / 0 / 0 |
| Páronkénti összevetés a csomagon belül (input-input, output-output, instruction+input, input-output >= 0.9) | 0 találat | 0 találat |
| Cross-dedupe a teljes tiszta korpusszal (500 noisy vs 3000 nem-noisy sor; instruction+input, output, input-input, input-output >= 0.9; id-ütközés) | 0 / 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 / 0 |
| PII / URL / e-mail / telefonszám / azonosító / MF-AI / Nextora / identity bleed | 0 | 0 (6. fejezet) |
| `quality_notes` egyediség | 500 / 500 egyedi, 0 üres, 0 pár >= 0.85 hasonlósággal | változatlan |
| `quality_notes` idézet-konzisztencia (a jegyzetben idézett szó szerepel-e a sorban) | 26 nem talált idézet | **9** (mind jelölés, nem hiba: `-re/-be`, `...`, `hogy…?`) |
| Quality score | átlag 99.98 (a `0114` 90: `low_instruction_overlap`) | **100.0 / 100** mind az 500 sorra |
| Zajcímkék bizonyíték nélkül (szkript, kézi átnézéssel) | lásd 2.3-2.4 | lásd 2.3-2.4 |
| Túl hasonló sorpár (input vagy output >= 0.7) | 2 pár (`0344`/`0452`) | **0 pár** (legnagyobb 0.693: `0446`/`0479`) |
| `difficulty` következetesség | batchen belüli rangsor (batchenként 45/35/20) | csomag-szintű rangsor (össz. 225 / 175 / 100), 153 sor változott |
| Regressziós teszt | STABIL | **STABIL** |

## 2. Külön vizsgált tételek

### 2.1. `szval` (60 input)

**Megfigyelés**: a `szval` -> `szóval` pár volt a csomag legismétlődőbb javítása (54 sor), és a koncentráció batchenként nőtt (1./2./3./4./5.: 1 / 0 / 6 / 19 / 34 input). Az ötödik batchben minden harmadik input ugyanazt a rövidítést tartalmazta. A `, szval` szerkezet ráadásul azonos mondatszerkezetet is jelent (`X, szval Y`).
**Döntés és javítás** (csak clean): a 60 sorból
- 21 sorban marad a `szval` (a hiteles, valódi rövidülés; ennek a mintának a jelenléte fontos);
- 17 sorban a szóalak más, valós elütés-formát kapott (`szoval`, `szóvl`, `szóvsl`, `szóavl`), a javított output ugyanaz (`szóval`): `0225, 0281, 0308, 0322, 0339, 0364, 0400, 0405, 0410, 0423, 0433, 0443, 0453, 0462, 0465, 0478, 0486`;
- 22 sorban a mondatkötő maga változott (`szval` -> `úgyhogy`, elütött formákban: `úgyhpgy`, `úgyhgy`, `ugyhogy`, `úgyhoggy`; az output `úgyhogy`): `0306, 0315, 0316, 0329, 0330, 0382, 0401, 0415, 0416, 0425, 0426, 0437, 0438, 0444, 0446, 0454, 0467, 0476, 0479, 0480, 0488, 0496`. Ezeknél a `beszélt nyelv` címke bizonyítékát újra megvizsgáltam: 12 sorban nem maradt más beszélt fordulat, ott a címke lekerült (`0330, 0382, 0401, 0425, 0426, 0438, 0444, 0446, 0454, 0467, 0476, 0479`).
- A két olyan sor, ahol az `úgyhogy`-csere után a sor egyetlen bizonyítékkal alátámasztható címkéje is elveszett volna (`0281`, `0405`), visszakerült elütés-formára.
- A `quality_notes` mindenhol az új szóalakot idézi.

**Eredmény**: `szval` input 60 -> **21** (4.2%); `szóval` output 90 -> **68** (13.6%); mondatközi `, szóval` 84 -> 62. Az egyedi javítás-párok koncentrációja csökkent (`szval->szóval` 54 -> 19, új: `úgyhpgy/úgyhgy/úgyhoggy/ugyhogy->úgyhogy` összesen 22, `szoval->szóval` 14).
**Megmaradó megfigyelés**: a `szóval` így is 68 outputban szerepel (13.6%); a kötőszó természetes, ezért a hangot nem írtam át tovább.

### 2.2. `tök` (57 output)

**Megfigyelés**: a `tök` mint fokozó a 3-5. batchre koncentrálódott (0 / 0 / 7 / 25 / 25 sor az outputban), a `tök jó` önmagában 20 sor. Az 57 sorból 54 `enyhe szleng` címkéjű, vagyis a 68 szleng-címkés sor 79%-ában ez volt a szleng-szó (a többi: *cuki, ciki, menő, para, suli, kaja...*).
**Javítás** (csak clean, input+output+jegyzet együtt, felváltva minden második jelölt): 23 sorban a `tök <melléknév>` fokozó `marha` (X-címkés sorokban), `brutál` (X-címkés sorokban) vagy `nagyon` (nem-X sorokban) lett: `0225, 0243, 0307, 0315, 0320, 0332, 0340, 0365, 0370, 0382, 0384, 0391, 0401, 0411, 0416, 0418, 0424, 0435, 0438, 0453, 0464, 0478, 0489`. A kifejezés többi része, a hang és a szándék nem változott (pl. `tök cuki` -> `marha cuki`, `tök jó` -> `brutál jó`). A `tök hülyeség`, `tök elegem van`, `tök sietve` típusú, nem-melléknévi használatot nem cseréltem.
**Eredmény**: `tök` output 57 -> **34** sor (6.8%; a szleng-címkés sorok 79% -> 49%-ában); a szleng-címke bizonyítéka minden érintett sorban megmaradt (`marha`, `brutál`, `cuki`, `ciki`, `menő`).
**Megjegyzés**: a `brutál`/`marha` enyhe szleng, erős káromkodás nincs.

### 2.3. `beszélt nyelv` címke gyengén megalapozott sorai

Az első futás 19 sort jelzett bizonyíték nélkül (`0115, 0123, 0135, 0138, 0144, 0167, 0170, 0181, 0183, 0186, 0187, 0188, 0240, 0259, 0277, 0305, 0317, 0318, 0411`). Soronként átnéztem:

| Döntés | Sorok |
|---|---|
| Címke marad (beszélt fordulat van: *kéne, tesóm, suli, az is bejött, Nekem legalábbis mindig, kaját, ez nem fura, szólj neki nehogy…*) | `0115, 0123, 0135, 0167, 0170, 0183, 0188, 0259, 0277, 0305, 0317` (11) |
| `beszélt nyelv` levéve, a maradék címkék elegendők | `0138` (Q, A), `0181` (S, A), `0187` (G, A), `0240` (R, S), `0318` (Q, E), `0411` (X, E) (6) |
| `beszélt nyelv` lecserélve, mert volt evidenciája az írásjel-hibának | `0144` (A, S), `0186` (A, S) (2) |

Emellett a `szval`->`úgyhogy` csere után 12 sorról került le a címke (2.1). A `beszélt nyelv` címke összes előfordulása **152 -> 132** (batchenként 9 / 38 / 36 / 27 / 22).
**Megmaradó korlát**: a maradék 11 sorban a beszélt fordulat halvány (pl. *az is bejött*); ezeket nem vettem le, mert van hétköznapi, beszélt elem, de nem a legerősebb bizonyítékú sorok.

### 2.4. `hibás ragozás` és `rövidítés` címkék jelenléte / hiánya

| Címke | 1. | 2. | 3. | 4. | 5. batch | Összesen (előtte -> utána) |
|---|---|---|---|---|---|---|
| hibás ragozás | 9 | 5 | 16 | 6 | **1** | 37 -> 37 |
| rövidítés | 9 | 17 (21) | 29 | 11 | **0** | 70 -> 66 |

- **hibás ragozás**: a 37 címkézett sorból mind a 37-ben valódi rag/névelő-javítás van (a szkript 10-et bizonyíték nélkülinek jelzett, de mind valódi: *Debrecenre -> Debrecenbe, hangszerre -> hangszeren, a igazgatóhoz -> az igazgatóhoz*); címke nélküli valódi rag-javítás nincs (a 2 jelölt, `0289` és `0333`, elütés, nem rag). A 4. és főleg az 5. batchben a típus szinte hiányzik (6 / 1 sor), de az 1-3. batch együtt 30 sort ad; a csomag egészében 7.4%.
- **rövidítés**: 4 sor bizonyíték nélküli címkéje lekerült (`0109, 0128, 0189` és `0173` -> `szóköz- és írásjelhiba`; ezekben nincs `kb/pl/vmi/vki/h`), így 70 -> 66. Az 5. batchben 0 sor a típus (a `nemtom/nemtudom` típusú összeírásokat a `szóköz- és írásjelhiba`, az `asszem` típusúakat a `beszélt nyelv` címke fedi). A címke nélküli rövidítés-tokenes 16 sor közül 5 az 1. batch egy-címkés sora, 11 pedig 3-címkés sor, ahol a rövidítés az `S` vagy `B` alá esik; ezeket nem címkéztem át.
- **Döntés**: új sort a csomag nem vehet fel (500 / 500 fix); a két típus hiányát a batchek közti eloszlás-korlátként dokumentálom, nem hibaként.

### 2.5. A hat emberi értelmezést igénylő sor

Az automatikus mérő (`noisy_extra.py`: csak betűszintű elütés/ékezet) ezeket „csak formainak” jelezte. Az audit szigorú definíciója: *legalább egy token különbözik kisbetűsítés és írásjelek nélkül, és a különbség lehet betű, ékezet, szóhatár vagy számjegy*. Mindegyik hat sor megfelel; a javítás valódi szóalak-javítás, és a batch pontosan ezeket a típusokat kérte (összeírt/szétírt szó, *o*/*0* tévesztés).

| Sor | Input -> output (a lényeges javítás) | Döntés |
|---|---|---|
| `0402` | *Van vala mi amit…* -> *Van valami, amit…* (szétírt szó összeírva) | **Elfogadva**: szóhatár-javítás, a felhasználó hangja és tartalma változatlan |
| `0407` | *Ma el kezdtem…* -> *Ma elkezdtem…* (szétírt szó összeírva); a *nem tom* szándékosan marad | **Elfogadva** |
| `0450` | *mivan ha…? nemtudom* -> *Mi van, ha…? Nem tudom* (két összeírt szó szétválasztva) | **Elfogadva** |
| `0404` | *5o kilométert*, *2o volt* -> *50*, *20* (kisbetűs *o* a nulla helyett) | **Elfogadva**: számjegy-tévesztés, a kért *o*/*0* fajta |
| `0457` | *2ooo forint* -> *2000 forint* | **Elfogadva** |
| `0472` | *1o üzenetet* -> *10 üzenetet* | **Elfogadva** |

A hat sort **nem módosítottam** (nem tettem beléjük külön betűszintű elütést sem: ez a tanítóadat éppen a szóhatár- és karaktertévesztés-hibát hivatott mutatni). Az 1. batch két hasonló sora (`0022`, `0071`: összeragadt *Amosógép*, *akövetkező*, *Ittvárok*) ugyanezen az alapon **elfogadva**.
A mérőszám-korlátot ezzel együtt rögzítem: az `extra` mérő és az audit-mérő különbsége pontosan ez a 8 sor.

### 2.6. A 2. batch report cross-dedupe pontosítása (reportpontosítás, NEM adatjavítás)

- **Mi volt a pontatlanság?** A 2. batch reportja (`claude_noisy_input_0101_0200_report.md`, Számok tábla, 3. fejezet 7. pontja és a Végső összegzés) „3000 meglévő clean sor” ellen jelezte a keresztellenőrzést. Az akkori ellenőrző a fájlnevekben `noisy_input`-ot tartalmazó összes fájlt kihagyta, ezért a 2. batch az **1. noisy batchhez (100 sor) nem lett hasonlítva**; a helyes referencia 3100 sor lett volna (3000 nem-noisy + 1. batch).
- **Mit tettem?** (a) A 3. batch fejlesztésekor a 2. batchet utólag a 3100 sor ellen is lefuttattam: 0 találat. (b) A záró auditban a **teljes noisy csomag mind az 500 sora** a 3000 nem-noisy sorral szemben és noisy-noisy páronként (id; instruction+input, output, input-input, input-output >= 0.9) is lefutott: **0 találat, 0 id-ütközés**, az audit előtt és után is. (c) A 2. batch reportját **nem írtam át**, hanem a végére egy „Utólagos pontosítás” szakaszt fűztem, az eredeti szöveg érintetlen. A pontosítás tartalma dokumentált: a 2. batch adata nem érintett, csak a report megnevezett referencia-sorszáma volt hiányos.
- Az 1. batch reportja (3000 sor) pontos volt; a 3-5. batch reportjai a helyes korpusz-méreteket (3200 / 3300 / 3400) használják.

## 3. További megtalált és javított tételek

| # | Tétel | Javítás | Sorok |
|---|---|---|---|
| 3.1 | **1. batch: 7 kizárólag formai sor** (dupla szóköz, szóköz írásjel előtt, csupa nagybetű): nincs valódi szóalak-hiba, ami az 5. csomagtól elvárt | valódi, természetes betűszintű hiba került az inputba (*szerelöt, zsirfoltot, vacsotára, nyomtstóm, rendeswn, kölcsönadtsm, hajszáritót*), az output és a formai zaj változatlan, a quality_notes és a címkék (+`elgépelés`/`ékezet nélkül`) frissítve | `0006, 0023, 0031, 0037, 0047, 0053, 0069` |
| 3.2 | **quality_notes idézet nem szerepel a sorban** (26 jelzés; ebből 16 valódi eltérés) | az idézeteket a tényleges input/output szavaira igazítottam (pl. `0241`: *elfelejtetem* -> *felejtetem*; `0138`, `0154`, `0169`, `0171`, `0181` idézete a tényleges mondatszerkezetre) | `0027, 0129, 0134, 0137, 0138, 0154, 0169, 0171, 0181, 0203, 0241, 0291, 0378, 0458, 0465, 0479` |
| 3.3 | **Túl hasonló sorpár**: `0344` és `0452` (input 0.76, output 0.76: *Nem látta valaki a X-t? Az előbb még itt volt…*) | a `0452` második mondata átfogalmazva (*Tegnap még a fiókban volt, most meg sehol.*), az elütés (*fiókbsn*) és a többi javítás megmaradt | `0452` |
| 3.4 | **Alaptalan zajcímke** | lásd 2.3-2.4; ezen felül a `0176` `kérdés félreütésekkel` címkéje lekerült (nem kérdés) | `0176` (és a 2.3-2.4 sorai) |
| 3.5 | **Egyetlen 100 alatti quality score** (`0114`, 90: `low_instruction_overlap`) | az instruction a soron olyan feladatmegfogalmazásra cserélve, amelynek van szó-átfedése az outputtal (*Írd le hibátlanul, hogy mit üzent a felhasználó, ugyanazon a hangon.*); a tartalom nem változott | `0114` |
| 3.6 | **`difficulty` batchenként relatív volt** (a 2. batch *easy* sorai nehezebbek, mint a 4. batch *medium* sorai) | csomag-szintű rangsor ugyanazzal a képlettel (karakter-eltérés + hossz + zajtípus-szám), 100 hard / 175 medium / 225 easy; összesen 153 sor változott (ebből 132 sorban ez volt az egyetlen változás) | 153 sor (a tartalom nem változott) |

A 3.6 miatt a korábbi batch-reportok „easy 45 / medium 35 / hard 20” batchenkénti számai a clean fájlokra már nem érvényesek; a raw fájlok az eredeti eloszlást őrzik. A jelenlegi batchenkénti eloszlás (`easy / medium / hard`): 1. batch 80 / 14 / 6, 2. batch 13 / 27 / 60, 3. batch 45 / 39 / 16, 4. batch 49 / 38 / 13, 5. batch 38 / 57 / 5.

## 4. Tag- és címkeegyensúly (a clean fájlokban, audit után)

| Zajtípus (összes címke) | 1. | 2. | 3. | 4. | 5. | Összesen | Előtte |
|---|---|---|---|---|---|---|---|
| elgépelés | 14 | 17 | 43 | 72 | 85 | **231** | 226 |
| szóköz- és írásjelhiba | 8 | 14 | 48 | 50 | 45 | **165** | 162 |
| ékezet nélkül | 11 | 83 | 39 | 18 | 3 | **154** | 152 |
| telefonos gyors gépelés | 9 | 44 | 32 | 11 | 41 | **137** | 137 |
| beszélt nyelv | 9 | 38 | 36 | 27 | 22 | **132** | 152 |
| kérdés félreütésekkel | 9 | 26 | 3 | 28 | 23 | **89** | 90 |
| rövidítés | 9 | 17 | 29 | 11 | 0 | **66** | 70 |
| enyhe szleng | 10 | 1 | 4 | 28 | 25 | **68** | 68 |
| indulatos, laza stílus | 9 | 12 | 5 | 16 | 21 | **63** | 63 |
| hosszabb kusza mondat | 10 | 12 | 4 | 17 | 16 | **59** | 59 |
| hibás ragozás | 9 | 5 | 16 | 6 | 1 | **37** | 37 |

- **Zajtípus-szám soronként** (audit után): 1. batch 93 sor 1 típus + 7 sor 2 típus (az utóbbi a 3.1 javítás); 2-5. batch: 2-3 típus (3 típus: 69 / 59 / 84 / 82 sor). A `tags` hossza ennek megfelelően 4-5 (1. batch) és 5-6 (2-5. batch).
- **Elsődleges típus (`tags[2]`)**: telefonos 71, kérdés 60, indulatos 54, kusza 52, szleng 51, beszélt nyelv 44, elgépelés 44, ékezet nélkül 44, rövidítés 30, szóköz/írásjel 27, ragozás 23 - kiegyensúlyozott, egy típus sem dominál.
- **Téma**: 447 különböző téma 500 sorban; az 1. batch 50 témát használt 100 sorra (*főzés* 9, *közlekedés* 6, *lakóközösség* 5, *telefon* 5, *háztartási gép* 5), a 2-5. batch témái mind egyediek. Ez a batch-szintű tervezés következménye, nem hiba.
- **Instruction**: 150 különböző szöveg, legfeljebb 4 sorban egy-egy; egyikük sem hasonlít 0.9 fölött.
- **`zajos bemenet` tag: 100% (500 / 500 sor), a teljes korpuszban 14.3% (500 / 3500)**. Ez a csomag jelölőcímkéje, ezért a topic report `[FIGYELEM]` jelzése önmagában **nem hiba**. Nem módosítottam, és a `tools/dataset_topic_report.py` kezelése (pl. jelölőcímkék kizárása a túlreprezentáltság-számításból) külön jóváhagyandó.

## 5. Ismétlődő fordulatok és hasonló minták

| Vizsgálat | Eredmény |
|---|---|
| Input-input / output-output páros hasonlóság >= 0.9 | 0 |
| >= 0.7 | 2 pár -> **0** (legnagyobb 0.693: `0446`/`0479`, *Köszönöm/Köszi mindenkinek…, szóval legközelebb…*) |
| >= 0.6 | 8 -> 6 pár |
| `nem tudom, hogy` (3-gram) | 41 input (8.2%), 49 output: természetes, nem módosítottam |
| Nyitó szó | *A* 106 sor (21%), *Ma* 23, *Holnap* 20: természetes hétköznapi nyitányok |
| `szerintem` | 35 sor, ebből 22 a 3. batchben (22%): batch-koncentráció, dokumentálva |
| `kéne` | 15 sor, ebből 12 a 3. batchben: dokumentálva |
| Egyetlen szóalak-javítás + írásjel a sor teljes javítása | 195 / 500 sor (39%; batchenként 30 / 2 / 43 / 67 / 53) |
| Leggyakoribb egyedi javítás | *es->és* 24, *kb->körülbelül* 19, *szval->szóval* 19 (60 volt), *mar->már* 18, *vmi->valami* 14, *szoval->szóval* 14, *vki->valaki* 11 |

**Értékelés**: a mintázat-koncentráció fő forrásai (`szval`, `tök`) csökkentve lettek. A megmaradó fő korlát szerkezeti: a 3-5. batch sorainak nagy része „egy elütés + hiányzó írásjelek” típusú, és a javítások kis száma (átlag 1.6-2.1 szóalak/sor a 3-5. batchben, 2.3 az 1., 4.0 a 2. batchben) azt jelenti, hogy a csomag kevés „erősen zajos” példát tartalmaz (a 2. batch és részben az 1. batch adja). Ez a felhasználó által kért irány (kevés szétesett input) következménye, ezért nem javítás tárgya, de az arányt a felhasználásnál (súlyozás) érdemes figyelembe venni.

## 6. Safety, PII, identity bleed

- E-mail, URL, telefonszám, irányítószám/cím, személyazonosító-minta, MF-AI / Nextora / Nexora említés: **0** mind az 500 sorban (input, output, instruction, quality_notes, tags); `guard.looks_like_identity_bleed`: 0.
- Erős káromkodás / gyűlölet szókincs: 0. Egyetlen enyhe kifejezés (`0078`: *Ki a franc hagyta itt…*, a franc = enyhe kifejezés, az 1. batch óta dokumentált); enyhe indulatszavak: *úristen, a fene, hülye program, tök gáz*.
- Érzékeny téma kulcsszavak (orvosi, jogi, pénzügyi, politika/vallás, szex/fegyver/drog/alkohol, erőszak): a szkript 7 találatot jelzett (`láz` az *eláztak/elázott* szavakban, `adó` az *eladónak* és *előadó* szavakban, `bor` a *szobor* szóban, `isten` az *Úristen* felkiáltásban), **mind téves illesztés**, tényleges érzékeny tartalom nincs.
- Pénzösszeg szerepel 3 sorban (`0210`: 1000 forint közös virágra, `0253`: 12 ezer lépés, `0457`: 2000 forint zsebpénz), pénzügyi tanács nincs.
- Tulajdonnév-szerű szavak: csak földrajzi nevek (Balaton, Duna, Debrecen, Mecsek, Börzsöny, Mátra); személynév nincs.
- Kérdések (pl. *milyen hajszárítót érdemes venni*, *madáreleség*, *filctoll-folt*) az inputban maradnak; az outputban **nincs rájuk válasz vagy tanács**.

## 7. Változáslista (audit előtt -> után)

| Kategória | Sor | Érintett mezők | Azonosítók |
|---|---|---|---|
| Formai sor -> betűszintű hiba (1. batch) | 7 | input, quality_notes, tags | `0006, 0023, 0031, 0037, 0047, 0053, 0069` |
| `szval` -> elütés-forma | 17 | input, quality_notes | `0225, 0281, 0308, 0322, 0339, 0364, 0400, 0405, 0410, 0423, 0433, 0443, 0453, 0462, 0465, 0478, 0486` |
| `szval` -> `úgyhogy` | 22 | input, output, quality_notes (+ tags 12 sorban) | `0306, 0315, 0316, 0329, 0330, 0382, 0401, 0415, 0416, 0425, 0426, 0437, 0438, 0444, 0446, 0454, 0467, 0476, 0479, 0480, 0488, 0496` |
| ebből `beszélt nyelv` címke levéve | 12 | tags | `0330, 0382, 0401, 0425, 0426, 0438, 0444, 0446, 0454, 0467, 0476, 0479` |
| `tök` -> `marha` / `brutál` / `nagyon` | 23 | input, output, quality_notes | `0225, 0243, 0307, 0315, 0320, 0332, 0340, 0365, 0370, 0382, 0384, 0391, 0401, 0411, 0416, 0418, 0424, 0435, 0438, 0453, 0464, 0478, 0489` |
| Címke-javítás (nem a fentiekből) | 13 | tags | `0109, 0128, 0138, 0144, 0173, 0176, 0181, 0186, 0187, 0189, 0240, 0318, 0411` |
| quality_notes idézet javítás (csak jegyzet) | 12 | quality_notes | `0027, 0129, 0134, 0137, 0154, 0169, 0171, 0203, 0241, 0291, 0378, 0458` |
| Hasonló sor átfogalmazása | 1 | input, output, quality_notes | `0452` |
| Instruction csere (score) | 1 | instruction | `0114` |
| `difficulty` újrarangolás | 153 | difficulty | (csomag-szintű rangsor; a lista a mentés és a végleges fájl különbsége) |
| **Összes érintett sor** | **219** | ebből 62 sorban input/output szöveg változott | |

## 8. Nyitott tételek és nem blokkoló megfigyelések

Blokkoló nyitott tétel **nincs**. Az alábbiak dokumentált, nem blokkoló megfigyelések:

1. **Az „egy elütés + hiányzó írásjelek” szerkezet** a sorok 39%-a (195 sor); a csomag ezzel is stabil, de a `noisy_input` súlyozásánál érdemes ezt figyelembe venni. Javítása új sorokkal lenne lehetséges, ez az 500 / 500 lezárása után külön döntés.
2. **`szóval` 13.6%, `szerintem` (3. batch 22%), `kéne` (3. batch 12 sor)**: batch-koncentráció, a hangot nem írtam át tovább.
3. **11 sor `beszélt nyelv` címkéje halvány** (2.3); a címkék hibánkénti annotációnak nem tekinthetők, főleg az `indulatos`, `enyhe szleng`, `kérdés`, `kusza mondat` típusok stílust jelölnek.
4. **`hibás ragozás` (5. batch: 1) és `rövidítés` (5. batch: 0)** a legutóbbi batchekben ritka, a csomag egészében 7.4% és 13.2%.
5. **`zajos bemenet` tag 14.3%** a teljes korpuszban: jelölőcímke, nem javítottam (kezelése külön jóváhagyás).
6. **Az 1. batch tag-szerkezete** kissé más (egy zajtípus/sor, 4 tag; a 3.1 javítás miatt 7 sor 5 tag); a 2-5. batch 2-3 zajtípust használ.
7. **A korábbi batch-reportok számai** (difficulty-eloszlás, `szval`/`tök`/`beszélt nyelv` számok) az audit előtti állapotot mutatják; ez a report a végleges. A 2. batch reportja pontosító szakaszt kapott (2.6).
8. **A hat, emberi értelmezést igénylő sor** elfogadva (2.5); az `extra` mérő és az audit-mérő különbsége ez a 8 sor.
9. **Az ellenőrző scriptek** a repón kívül vannak.

## 9. Fájlok és amit ez a kör NEM tett

- Módosított clean fájlok: `data/clean/claude_noisy_input_0001_0100_clean.jsonl` ... `..._0401_0500_clean.jsonl` (mind 100 sor); módosított report: `data/reports/claude_noisy_input_0101_0200_report.md` (pontosító szakasz hozzáfűzve); új report: `data/reports/noisy_input_final_audit_fix_report.md` (ez a fájl).
- **Nem** módosította a raw fájlokat, a rejected fájlokat, a validátort, a topic reportot, a webapp/backend kódot; nem törölt semmit; nem indított tanítást; nem kezdte el a 6-9. csomagot.
- A helyi `dataset_autopilot_progress.md` frissült (szándékosan nincs commitolva, mint korábban).

---

## Végső összegzés

- **Az 5. csomag (noisy_input) végleges: 500 / 500 clean, 0 rejected**, átlag score 100.0 (mind az 500 sor 100), regressziós teszt STABIL.
- **Teljes clean korpusz: 3500 sor** (1000 simple_qa, 1000 explanation, 500 step_by_step, 500 summary, 500 noisy_input).
- Csomagszinten ellenőrizve: ID-folytonosság, schema, `input != output`, minden sorban valódi szóalak-szintű javítás (492 betűszintű, 5 szóhatár, 3 számjegy), dedupe (batchen belül és 500 sor egyben), cross-dedupe a 3000 nem-noisy sorral és noisy-noisy párokra (0 találat), PII/URL/e-mail/telefon/MF-AI/Nextora (0), safety, quality_notes egyediség (500 / 500) és idézet-konzisztencia, ismétlődő fordulatok, tag- és címkeegyensúly, hasonló minták.
- Javítva (csak clean): 7 formai sor -> betűszintű hiba, `szval` 60 -> 21, `tök` 57 -> 34, 32 sor zajcímkéje, 16 jegyzet idézete, 1 túl hasonló sor, 1 alacsony score, `difficulty` csomag-szinten. A 2. batch report cross-dedupe-pontosítása külön dokumentálva (2.6), az adat nem érintett.
- **Nyitott tétel:** blokkoló nincs; nem blokkoló megfigyelések a 8. fejezetben.
- **A 6. csomag** (hosszabb, többfordulós beszélgetés) az 5. csomag oldaláról **indulhat, csak külön felhasználói jóváhagyással**; a roadmap szerint a 6. csomaghoz eleve séma-bővítés jóváhagyása is kell (a 7-9. csomag további jóváhagyásokat igényel: forrás, repo-alapú tudásanyag).

**STÁTUSZ: STABIL.**
