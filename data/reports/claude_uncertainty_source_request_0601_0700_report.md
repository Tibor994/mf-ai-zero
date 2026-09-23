# Hetedik uncertainty_source_request batch - uncertainty_source_request_0601-0700

**Verdikt: STABIL.** 100 sor, **100 clean / 0 rejected**, `category: uncertainty_source_request`, a **6. csomag (Bizonytalanság / forráskérés)** hetedik batchje az új, bővített 17 000 soros `instruction_core`-ban.

## 0. Kiinduló állapot ellenőrzése a tényleges fájlokból

A munka megkezdése előtt a fájlokból (nem a korábbi jelentésből) számoltam meg a sorokat:

```bash
wc -l data/clean/*.jsonl | tail -1
grep -l '"category": "uncertainty_source_request"' data/clean/*.jsonl | xargs wc -l | tail -1
```

Eredmény: **teljes clean korpusz 4100 sor**, ebből **`uncertainty_source_request` 600 sor**. Ez megegyezik a jelentett állapottal. A batch után: **700 / 1000** a 6. csomagban, teljes clean korpusz **4200 sor** — ezt a 6. fejezetben ugyanígy, a fájlokból újraszámolva igazolom.

## 1. A kérés követelményei és teljesülésük

| Követelmény | Teljesülés |
|---|---|
| 100 új sor, cél 700/1000, korpusz 4200 | 100 sor, folytonos id `0601`-`0700`; a fájlokból újraszámolva **700/1000**, **4200 sor** (6. fejezet) |
| Maradjon 14 kontraszt-példa, elegendő infóval a határozott válaszhoz | **14 sor**, mindegyikben a válaszhoz szükséges adat a kérdésben/inputban benne van, egyik sem marad nyitott bizonytalanságban |
| Legyen köztük hibás előfeltevés javítása, igaz előfeltevés megerősítése, részben igaz pontosítása, egyértelműen megoldható hétköznapi feladat | **4 hibás** + **4 igaz** + **3 részben igaz** + **3 egyértelműen megoldható** = 14 (2. fejezet) |
| A 14-ből legalább 8 nyitott, természetes kérdés/kérés, a feltételezés a megfogalmazásból derüljön ki | **14/14** nyitott (0 zárt *Ha…, akkor/azzal…?* szerkezet); formák: állító mondat, *ugye?*, *Ez így igaz?*, egyenes kérdés, számolási kérés (2.1-2.4) |
| Ne minden példa egy állítás igazságát kérdezze; ne legyen kötelező Igen/Nem/Részben válaszkezdés | 3 sor egyáltalán nem állítás-igazságot kérdez (számolási/időbecslési feladat); a válaszok nyitása változatos: *Ez tévhit…*, *Ez nem feltétlenül igaz…*, *A jelerősség csak…*, *Ez nem következik automatikusan…*, *Igen, ez alapvető…*, *Ez nagyrészt igaz…*, *Van ebben igazság…*, *Reggel 7 órakor…*, *50 dekagrammot…*; „Igen”-nel csak 4, „Ez nagyrészt/Van ebben igazság” jellegű nyitással 3 sor kezdődik |
| A határozott válasz tartalmazza a feltételeket és kivételeket; a pontosság előbbre való a fenntartó szavak mechanikus kerülésénél | lásd 2.1-2.4 példák (pl. repülő üzemmód: kivétel a wifi/Bluetooth; méz: kivétel a nedvesség); a *függ* és hasonló szavak ott maradtak, ahol tartalmilag indokoltak (10 sor, 3. fejezet) |
| Fő mód `kontraszt_magabiztos`; kiegészítő címkék `hibas_elofeltevesjavitas`, `igaz_elofeltevesmegerosites`, `reszben_igaz_elofeltevespontositas`, csak tartalmilag megfelelő sorokon; nincs új címke | teljesült; **nem vezettem be új címkét**; a 3 „egyértelműen megoldható” sor szándékosan nem kap plusz címkét, mert nem előfeltevés-javítás/megerősítés/pontosítás (3. fejezet) |
| Csomagjelölő címkék kivétele a topic reportban dokumentálva, a küszöböt nem módosítom | 5. fejezet; az eszköz és a küszöb változatlan |
| Az 5. batch `0506, 0518, 0541, 0542, 0545` sorának tényellenőrzése, forrásokkal, dokumentált eredménnyel, nyers fájl felülírása nélkül | 4. fejezet: mind az 5 állítás megbízható elsődleges forrásokkal ellenőrizve; nincs hiba, egy sornál (`0506`) árnyaló megjegyzés; a régi `data/clean/claude_uncertainty_source_request_0501_0600_clean.jsonl` fájlt **nem módosítottam** |
| Séma-, dedupe-, safety- és regressziós ellenőrzés lefuttatása, valódi eredményekkel | 6. fejezet; parancsok és eredmények szó szerint |
| Azonosítók ellenőrzése, mind a 100 sor végigolvasva | igen (7. fejezet, 1-2. pont) |
| A szabályokat ne módosítsam, hogy egy sor átmenjen | nem módosítottam a validátort, a dedupe-, score- vagy topic report eszközt |
| Gépi ellenőrzés és nyitott tartalmi kérdés elkülönítve a riportban | 6. és 8. fejezet |
| Reprodukáláshoz szükséges parancsok és eszközverziók | 6. fejezet |
| A repón kívüli ellenőrző scriptek ne kerüljenek be önálló eszközként | a `gen_usr7.py` és `usr_check7.py` a scratchpadban maradt, **nem emeltem be a `tools/` alá** |
| Tanítás, webapp, backend, validátor nem módosul; progress fájl a szabály szerint | 9. fejezet |
| Commit csak stabil állapot után | 9. fejezet: commit hash, állapot |
| `0701_0800` batch nem indul | nem indítottam el |

## 2. A 14 kontraszt-sor

### 2.1. Hibás előfeltevést javító (4 sor, `hibas_elofeltevesjavitas`)

| id | Forma | A felhasználó állítása | A modell javítása |
|---|---|---|---|
| `0698` | állító mondat | a böngészési előzmények törlésétől felgyorsul a gép | *Ez tévhit*: legfeljebb a böngészőt gyorsítja, a gép egészét nem; a valódi lassulási okokat nevezi meg |
| `0617` | állító mondat | aki nem posztol, az nem is használja az oldalt | *Ez nem feltétlenül igaz*: a csendes olvasás is valódi használat |
| `0686` | állító mondat | a wifi jelerősségből pontosan tudható a letöltési sebesség | elkülöníti a jelerősséget és a sebességet, mérési módot ad |
| `0700` | állító mondat | a „természetes összetevő” felirat miatt a termék biztosan egészségesebb | *Ez nem következik automatikusan*; az összetevőlista és a tápértéktáblázat összevetését javasolja |

### 2.2. Igaz előfeltevést megerősítő (4 sor, `igaz_elofeltevesmegerosites`)

| id | Forma | A felhasználó állítása | A modell megerősítése |
|---|---|---|---|
| `0669` | állító mondat | bemelegítés nélkül nagyobb eséllyel húzódik meg az izom | *Ez így igaz*, indoklással |
| `0658` | egyenes kérdés | a gyerekülés jelentősen csökkenti a sérülés kockázatát | *Igen*, gyakorlati kiegészítéssel (méretezés, beszerelés) |
| `0687` | visszakérdező mondat | a rendszeres fogkefecsere jobban tisztán tartja a fogat | *Igen*, konkrét gyakorisággal (kb. háromhavonta) |
| `0678` | *Ez így igaz?* kérdés | az UV-szűrős szemüveg véd a nap károsító hatásától | *Igen*, az UV400 jelölés megnevezésével |

### 2.3. Részben igaz előfeltevést pontosító (3 sor, `reszben_igaz_elofeltevespontositas`)

| id | Forma | A felhasználó állítása | A modell pontosítása |
|---|---|---|---|
| `0647` | *ugye?* visszakérdezés | a repülő üzemmód miatt semmilyen jelet nem bocsát ki a telefon | *Nagyrészt igaz, de nem teljesen*: a wifi/Bluetooth külön maradhat bekapcsolva |
| `0642` | állító mondat | a mézet sosem kell hűtőbe tenni, mert nem romlik meg soha | *Nagyrészt igaz*; a nedvesség okozta kivételt is megnevezi |
| `0602` | állító mondat | egy fokkal lejjebb vett éjszakai fűtéstől jelentősen csökken a számla | *Van ebben igazság*, de a „jelentősen” túlzás egyetlen fokra és egy éjszakára |

### 2.4. Egyértelműen megoldható hétköznapi feladat (3 sor, plusz címke nélkül)

| id | Feladat | Válasz |
|---|---|---|
| `0636` | 3×399 Ft tej + 550 Ft kenyér összesen mennyi | 1747 Ft, levezetéssel |
| `0659` | 23 órakor lefekve, 8 óra alvás után mikor kell ébredni | 7 óra |
| `0692` | fél kiló liszt hány dkg | 50 dkg |

Ez a 3 sor nem előfeltevést javít vagy erősít meg, hanem a megadott adatokból egyértelműen kiszámolható választ ad; ezért a kérés szerint **nem kaptak** kiegészítő címkét, csak a `kontraszt_magabiztos` fő módot.

**Nyitottság**: mind a 14 sor nyitott, természetes forma; zárt *Ha…, akkor/azzal…?* szerkezet **egy sincs** közöttük (a kérés minimum 8-at várt el). A válaszok nyitása változatos, nincs kötelező Igen/Nem/Részben-kezdés: „Igen” 4, „Ez nagyrészt igaz / Van ebben igazság” jellegű 3, „Ez tévhit / Ez nem következik automatikusan / Ez nem feltétlenül igaz” jellegű 4, számítási eredmény 3 sorban.

## 3. A többi 86 sor: mód-eloszlás

| Mód-címke | Sor | Jellemző témák |
|---|---|---|
| `valtozo_adat` | 15 | mobil percdíj, webshop-akció, zöldhulladék, egyetemi kurzus létszáma, pénzváltó árrés, uszodafelújítás, troli érkezése, étteremi szabad asztal, töltőállomás díja, gyógyszerkészlet, forgalmi dugó, előfizetési próbaidő, kriptoárfolyam, konditerem zsúfoltsága, kiadó lakás elérhetősége |
| `forras_nelkul_nem_tudhato` | 14 | régi osztálytárs lakhelye, szomszéd autójának ára, iskolaépület kora, barát fizetése, örökbefogadott kutya előélete, focicsapat alapítása, kolléganő szabadsága, gyerekkori lakás alaprajza, koncertlétszám, tanár nyugdíjba vonulása, e-mail olvasottsága, szülők házának építési költsége, utcai zenész neve, tavalyi kerti termés |
| `pontositas_kell` | 14 | tárgy nélküli kérdések (*Mit szólsz hozzá?*, *Jó ez a választás?*, *Mennyi idő kell hozzá?*, *Kell ehhez engedélyt kérni?*, *Melyik a gyorsabb megoldás?*, *Hol találom meg ezt?*, *Előnyös nekem ez az ajánlat?*, *Hogyan mondjam el neki?*, *Mennyibe kerül ez körülbelül?*, *Kivel beszéljek erről?*, *Ez normális, hogy ennyi idő alatt történt?*, *Jól van ez így megfogalmazva?*, *Melyik méret kell nekem?*, *Van értelme folytatni?*) |
| `altalanos_valasz_ellenorzessel` | 14 | szobai zajcsökkentés, első állásinterjú, szobanövény-gondozás, gyerek zsebpénze, kerékpár lopás elleni védelme, első konyhakert, költséghatékony utazás, macska új lakáshoz szoktatása, sötét hálószoba, iskolai projektmunka időbeosztása, alvási ritmus helyreállítása, régi fabútor felújítása, gyalogos közlekedésbiztonság, kutya autós utaztatása |
| `kitalalas_elutasitasa` | 14 | kvízválaszok kitalálása, közös költség elhallgatása hirdetésben, laboreredményből diagnózis, hamis szemtanú-vallomás, hamis betegségindok, pontatlan időpont panaszban, kitalált családi gyógymód, kitalált közös történet, házi feladat helyette megoldása áltatással, hamis munkaviszony-időtartam, gyerekrajz felnőttkénti bemutatása, mások gondolatainak kitalálása, saját bor alkoholtartalmának kitalálása, sportmérkőzés eredményének garantálása |
| `ellenorzesi_ut` | 15 | állásajánlat, garancia érvényessége, gyógynövénytea-állítás (bemásolt fórumszöveg), használt hangszer eredetisége, kvízalkalmazás adatgyűjtése, online árverés, régi pénzérme értéke, adóvisszatérítést ígérő hívás, iskolai alapítványi kérés, útlezárási hír (bemásolt), kézműves termék eredetisége, diákkedvezmény jogosultsága, kölcsönkért szerszám állapota, diákhitel-ajánlat átláthatósága, használt könyv hiánytalansága |

A `Mit tegyek, ha…?` mintázat **0** instructionben szerepel; a `simple_qa`-val a kereszt-dedupe 0.9-es küszöbén **0** a találat (lásd 6. fejezet).

## 4. Az 5. batch (`0501-0600`) öt sorának tényellenőrzése

A `data/clean/claude_uncertainty_source_request_0501_0600_clean.jsonl` fájlt **nem módosítottam**; ez a fejezet csak dokumentálja az ellenőrzés eredményét. Az ellenőrzést `WebSearch` segítségével végeztem, 2026-09-23-án, öt keresés eredménye alapján.

| id | Ellenőrzött állítás (az output szövegéből) | Felhasznált forrás | Eredmény |
|---|---|---|---|
| `0506` | „A bemelegítés fontos, a hosszú, egy helyben tartott nyújtás edzés előtt viszont nem bizonyítottan véd a sérüléstől.” | [Dynamic Warm-ups Play Pivotal Role in Athletic Performance and Injury Prevention (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC12034053/); [Is Static Stretching Effective for Injury Prevention? (NASM)](https://blog.nasm.org/fitness/is-static-stretching-the-best-strategy-for-injury-prevention-and-performance-enhancement) | **Megerősítve.** A szakirodalom szerint a statikus nyújtás önmagában nem csökkenti bizonyítottan a sérülés kockázatát, a dinamikus bemelegítés hatékonyabb. **Árnyalás**: a NASM-összefoglaló szerint a 45 másodpercnél rövidebb statikus nyújtás egy teljes bemelegítő rutinba ágyazva, magas intenzitású tevékenységnél akár csökkentheti is a sérülés kockázatát. Az eredeti sor kifejezetten a „hosszú, egy helyben tartott” nyújtásról beszél, ami ezzel az árnyalással is összhangban marad, javítást nem igényel. |
| `0518` | „A bő, zsíros vagy nehéz étel lassabban ürül... Egy nagyobb étkezés után érdemes megvárni egy-két órát, előtte elég egy kisebb, könnyű harapnivaló, például egy banán.” | [What to Eat Before Running (Runners Connect)](https://runnersconnect.net/what-to-eat-before-a-run/); [How long to wait after eating to run (Healthline)](https://www.healthline.com/health/fitness-exercise/how-long-to-wait-after-eating-to-run) | **Megerősítve, kisebb pontosítási lehetőséggel.** A sportegészségügyi ajánlások szerint nagy étkezés után 3-4 órát, kis étkezés után 1-2 órát, könnyű nassolnivaló (pl. banán) után 30-60 percet érdemes várni. Az „egy-két óra” egy nagyobb étkezésre az általános ajánlásoknál (3-4 óra) valamivel rövidebb, ez inkább csak közepes étkezésre pontos; ez nem téves állítás, de a következő batchben pontosabb lenne „két-négy órát” írni nagyobb étkezésre. Ezt **nem javítottam a nyers fájlban**, csak itt jelzem. |
| `0541` | „Szólítsd meg, és nézd meg, reagál-e. Ha nem, vagy ha nem lélegzik rendesen, hívd azonnal a 112-t... Ne hagyd magára.” | [Unresponsive and not breathing: learn first aid (British Red Cross)](https://www.redcross.org.uk/first-aid/learn-first-aid/unresponsive-and-not-breathing); [First Aid Steps (American Red Cross)](https://www.redcross.org/take-a-class/first-aid/performing-first-aid/first-aid-steps) | **Megerősítve.** A Vöröskereszt hivatalos elsősegély-lépései pontosan ezt a sorrendet írják elő: reagálás ellenőrzése, segélyhívás, légzés ellenőrzése, az ügyeletes utasításainak követése, az érintett magára hagyásának elkerülése. Javítást nem igényel. |
| `0542` | „Napközben zárd le az ablakokat és húzd le a redőnyt, este pedig szellőztess... Ha szédülsz, hányingered van... hűvös helyre kell menni, és szükség esetén orvost hívni.” | [Heat and People without Air Conditioning (CDC)](https://www.cdc.gov/heat-health/risk-factors/heat-and-low-income.html) | **Megerősítve.** A CDC ajánlása szerint napközben zárt ablak és sötétítés, este szellőztetés a bevált gyakorlat, a felsorolt tünetek (szédülés, hányinger) valóban hőségi rosszullét jelei, amelyeknél hűvös helyre menés és szükség esetén orvosi segítség javasolt. Javítást nem igényel. |
| `0545` | „Süllyedéskor és emelkedéskor nyelj, ásíts vagy rágj rágógumit... Cukorka szopogatása is segíthet, és ne aludj el az ereszkedés alatt.” | [Airplane ear - Symptoms & causes (Mayo Clinic)](https://www.mayoclinic.org/diseases-conditions/airplane-ear/symptoms-causes/syc-20351701) | **Megerősítve.** A Mayo Clinic pontosan ezeket a módszereket ajánlja (nyelés, ásítás, rágógumi, cukorka, ébren maradás süllyedéskor/emelkedéskor), és súlyos esetben orvosi segítséget javasol, amivel az eredeti sor záró mondata is összhangban van. Javítást nem igényel. |

**Összegzés**: mind az 5 állítás megbízható, elsődleges vagy hivatalos forrással alátámasztható, egyik sem tartalmaz téves tényt. Egy sornál (`0506`) egy tudományos árnyalás, egy másiknál (`0518`) egy pontosítási lehetőség merült fel, de egyik sem indokol javítást a meglévő szövegben; ezeket a jövőbeli batchekhez szóló megjegyzésként rögzítem, **nyitott, nem lezárt tételként**. A `data/clean/claude_uncertainty_source_request_0501_0600_clean.jsonl` fájlt emiatt nem módosítottam.

## 5. Topic report kivétel dokumentálása

A `tools/dataset_topic_report.py` a 4200 soros korpuszra:

| Tag | Sor | Arány | Jelzés |
|---|---|---|---|
| `instruction_core` | 700 | 16.7% | `[FIGYELEM]` |
| `bizonytalansag` | 700 | 16.7% | `[FIGYELEM]` |
| `forraskeres` | 700 | 16.7% | `[FIGYELEM]` |
| `nem_kamuzik` | 700 | 16.7% | `[FIGYELEM]` |
| `zajos bemenet` | 500 | 11.9% | `[FIGYELEM]` (korábbi csomagból, ehhez a batchhez nem kapcsolódik) |
| `összefoglalás` | 500 | 11.9% | `[FIGYELEM]` (korábbi csomagból, ehhez a batchhez nem kapcsolódik) |

**Döntés (a korábbi felhasználói jóváhagyás alapján, most is megerősítve):** a négy jelölő címke ennél a csomagnál **csomagjelölő**, nem tematikai jellegű: a `uncertainty_source_request` kategória minden során rajta van, ezért a küszöb átlépése **nem tematikai túlsúlyhiba**. A `[FIGYELEM]` jelzés ezekre elfogadott, **kivételként dokumentálva**. Az eszköz kódját és a 8%-os küszöböt **nem módosítottam**.

## 6. Ellenőrzések: parancsok, eredmények, reprodukálhatóság

Környezet: Windows, Python a `C:\Users\Lenovo\AppData\Local\Python\pythoncore-3.14-64` alól (a `torch` import alatt egy ártalmatlan NumPy-hiányra figyelmeztető `UserWarning` jelenik meg minden futásnál, ez a kimenetekben szűrve van). A parancsokat a `C:\Users\Lenovo\OneDrive\Dokumentumok\MF-AI-Zero` gyökérből futtattam, `PYTHONIOENCODING=utf-8 PYTHONUTF8=1` környezeti változókkal.

```bash
# kiinduló allapot a fajlokbol
wc -l data/clean/*.jsonl | tail -1
grep -l '"category": "uncertainty_source_request"' data/clean/*.jsonl | xargs wc -l | tail -1

# sema-validacio (repobeli eszkoz, valtoztatas nelkul)
python tools/dataset_validate.py data/clean/claude_uncertainty_source_request_0601_0700_clean.jsonl

# dedupe (batchen beluli es sajat fajlon beluli)
python tools/dataset_dedupe.py data/clean/claude_uncertainty_source_request_0601_0700_clean.jsonl

# quality score
python tools/dataset_score.py data/clean/claude_uncertainty_source_request_0601_0700_clean.jsonl

# regresszios teszt
python -m unittest tests.test_v1_7_4_dataset_foundation

# topic report a teljes clean konyvtarra
python tools/dataset_topic_report.py data/clean
```

A batchen belüli hasonlóság és a teljes korpusz elleni kereszt-dedupe (id, instruction+input, output, instruction-instruction, instruction-input, output-input, 0.9-es küszöb) a scratchpadban lévő `usr_check7.py` saját, nem repóbeli scripttel készült (a `usr_check6.py` egyenes módosítása, kizárólag `difflib.SequenceMatcher`-t és a repóbeli `src/guard.py` moduljának `looks_like_identity_bleed` függvényét használja); ezt **nem emeltem be** a `tools/` alá, a kérés szerint önálló eszközfejlesztésként.

| Ellenőrzés | Eredmény |
|---|---|
| `dataset_validate.py` | Beolvasott sorok: 100, Érvényes sorok: **100**, Elutasított sorok: **0** |
| `dataset_dedupe.py` | Beolvasott sorok: 100, id-duplikátumok: **0**, instruction-hasonlóság duplikátumok: **0**, output-hasonlóság duplikátumok: **0** |
| `dataset_score.py` | Átlagos pontszám: **100.0/100** (100 sor) |
| `tests.test_v1_7_4_dataset_foundation` | minden teszt sikeres, **STÁTUSZ: STABIL** |
| Saját kereszt-dedupe a 4100 meglévő clean sor ellen (5 összevetés, 0.9 küszöb) | **0/0/0/0/0** találat, **0** id-ütközés |
| Saját batchen belüli összevetés (instruction/output, 0.6 küszöb) | 5 pár, legnagyobb 0.68 (`0618`/`0680`, két különböző „valódi-e” ellenőrzési kérdés), >= 0.9: **0** |
| Instruction-hasonlóság a teljes korpusszal (0.7 küszöb, tájékoztató, nem hibajelzés) | 16 találat, mind témarokonság (pl. `0680` „online árverés valódi-e” ~ korábbi „online kupon érvényes-e” 0.815); tartalmi ütközés egyikben sincs |
| Safety (e-mail, URL, telefonszám, azonosító/IBAN, MF-AI/Nextora, `guard.looks_like_identity_bleed`, önbemutatkozás-jel, angol stopword, erős káromkodás) | mind **0** |

## 7. Kézi átolvasás és javítások

1. **Azonosítók**: `0601`-`0700` folytonos, hézag és ismétlődés nélkül (ellenőrizve a `usr_check7.py` saját id-folytonossági tesztjével).
2. **Teljes átolvasás**: mind a 100 sort (kérdés, bemásolt szöveg, válasz) egymás mellett végigolvastam két körben.
3. **Javított hibák az első vázlathoz képest**:
   - **Séma**: két kind-címke (`kerekpar_lopás_elleni_vedelem`) ékezetes karaktert tartalmazott, ez sértette az ASCII snake_case szabályt; `kerekpar_lopas_elleni_vedelem`-re javítva.
   - **Mód-eloszlás**: az első összeállításban a `kitalalas_elutasitasa` módból csak 12 sor volt a tervezett 14 helyett; két új sort írtam (`0652` hamis szemtanú-vallomás, `0633` kitalált családi gyógymód egészségügyi témában), hogy a mód-eloszlás megegyezzen a korábbi batchekével (15/14/14/14/14/15).
   - **Nyitás-koncentráció**: az „Ezt nem ismerem, és…” kezdet 3 sorban szó szerint ismétlődött; 2 sort átfogalmaztam (`0668`, `0688`); a „Nézd meg…” kezdet is 5-ről 3-ra csökkent (`0662`, `0674` átfogalmazva).
4. **Nem kellett javítani**: a validátor, a dedupe és a score a nyers fájlon is 100/100, illetve 100.0 eredményt adott már az első teljes futáskor; hibás/elutasított sor nem volt.

## 8. Nyitott tartalmi kérdések (nem gépi hiba, hanem mérlegelést igénylő tétel)

1. **`0518` pontosítási lehetőség**: a „nagyobb étkezés után egy-két óra” a szakirodalmi ajánlásoknál (3-4 óra) rövidebb; nem téves, de a következő batchben pontosabb megfogalmazás javasolt (lásd 4. fejezet).
2. **`0506` tudományos árnyalás**: rövid, teljes bemelegítésbe ágyazott statikus nyújtás egyes újabb közlemények szerint segíthet is; az eredeti szöveg (hosszú, egy helyben tartott nyújtás) ezzel nem ütközik, de a témát a jövőben érdemes frissen tartani, ha újabb összefoglaló jelenik meg.
3. **Sablon-ismétlődés az `ellenorzesi_ut` módban**: az „Hogyan ellenőrizzem, hogy … valódi-e?” szerkezet ebben és a korábbi batchekben is gyakori (lásd a 0.7-0.8-as informatív hasonlósági találatok, 6. fejezet); tartalmilag nem ütköznek, de a következő batchben érdemes más mondatszerkezetet is használni ebben a módban.
4. **Séma-bővítés eszközkérdése**: a `usr_check7.py` és a `gen_usr7.py` a repón kívül maradt; ha a jövőben a `tools/` alá kerülnének, az emberi jóváhagyást igényel (ezt a kört a kérés szerint nem tettem meg).
5. **Egészség-közeli sorok** (`0603`, `0663`, `0667`, `0672`, `0687`, `0693`): mindegyik tanács- vagy diagnózis nélküli, de nagyobb mennyiségnél külön egészségügyi-biztonsági átnézést igényelnek, ahogy az előző batchek riportjai is jelezték.

## 9. Fájlok, commit, állapot

- Raw: `data/raw/claude_uncertainty_source_request_0601_0700_raw.jsonl` (100 sor)
- Clean: `data/clean/claude_uncertainty_source_request_0601_0700_clean.jsonl` (100 sor)
- Rejected: `data/rejected/claude_uncertainty_source_request_0601_0700_rejected.jsonl` (0 sor, üres fájl)
- Report: `data/reports/claude_uncertainty_source_request_0601_0700_report.md`

Nem indítottam tanítást, nem módosítottam webapp/backend kódot, validátort, dedupe-, score- vagy topic report eszközt. Nem töröltem és nem írtam felül más batch fájljait, beleértve az 5. batch clean fájlját is. A helyi `data/reports/dataset_autopilot_progress.md` a meglévő szabály szerint frissült, de nem lett commitolva. Nem kezdtem el az `uncertainty_source_request_0701_0800` batchet.

**STÁTUSZ: STABIL.**
