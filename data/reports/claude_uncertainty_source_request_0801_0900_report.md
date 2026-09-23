# `uncertainty_source_request` batch riport — 0801–0900 (9. installment, 6. csomag "Bizonytalanság / forráskérés")

Dátum: 2026-09-23
Terjedelem: 100 új sor (`uncertainty_source_request_0801` – `uncertainty_source_request_0900`), plusz két célzott javítás korábban már commitolt clean sorokon.

---

## 0. Kiinduló állapot — tényleges fájlokból ellenőrizve

A felhasználó kérésére a batch megkezdése előtt ellenőriztem a tényleges állapotot (nem a korábban jelentett számokat):

```
wc -l data/clean/*.jsonl | tail -1        → 4300
grep -l '"category": "uncertainty_source_request"' data/clean/*.jsonl | xargs wc -l | tail -1   → 800
```

Ez megegyezett a felhasználó által feltételezett kiinduló állapottal (800/1000, 4300 clean sor összesen). A batch végére a cél: **900/1000**, teljes clean korpusz **4400 sor** — ezt a 4. és 5. szakasz végén tételesen újra ellenőriztem.

---

## 1. Kérdésforma-besorolás — a korrigált kritérium alkalmazása

A felhasználó megerősítette: az „ugye?" és az „Ez így igaz?" formájú kérdés **eldöntendő (zárt) kérdésnek** számít, függetlenül attól, hogy szó szerint „Ha…, akkor…?" mintát követ-e. Ezt a kritériumot alkalmaztam a **jelen, 0801–0900 batch** 14 kontraszt-sorának tervezésekor és besorolásakor.

A 14 kontraszt-sor formai bontása:

| # | ID | Forma | Nyitott/zárt |
|---|----|----|----|
| 1 | 0801 | „Mennyire igaz, hogy…?" (mérték-/fokozat-kérdés, nem eldöntendő) | nyitott |
| 2 | 0819 | állító kijelentés | nyitott |
| 3 | 0830 | állító kijelentés | nyitott |
| 4 | 0831 | állító kijelentés | nyitott |
| 5 | 0835 | állító kijelentés | nyitott |
| 6 | 0841 | állító kijelentés | nyitott |
| 7 | 0845 | állító kijelentés | nyitott |
| 8 | 0847 | állító kijelentés | nyitott |
| 9 | 0857 | „Mennyi húst vegyek?" (feladat/WH-kérdés) | nyitott |
| 10 | 0859 | állító kijelentés | nyitott |
| 11 | 0877 | állító kijelentés | nyitott |
| 12 | 0888 | „Milyen nap lesz…?" (WH-kérdés) | nyitott |
| 13 | 0895 | állító kijelentés | nyitott |
| 14 | 0806 | „Hányszor tudok tölteni…?" (WH-kérdés) | nyitott |

**14/14 nyitott** a korrigált kritérium szerint (egyik sor sem „ugye?" vagy „Ez így igaz?" típusú zárt kérdés) — jóval a minimum 8 fölött. A formai változatosság ezúttal nemcsak az állító/kérdő tengelyen valósul meg (10 állító kijelentés + 1 fokozat-kérdés + 3 valódi WH-feladatkérdés), hanem a **helyzetek és a válaszok tartalma** is szándékosan széles skálán mozog: tudományos tévhitek (balkezesség, kávépörkölés), biztonsági túlzás (zár), táplálkozás (gyümölcslé, C-vitamin, 5 másodperces szabály), alvás- és tanulás-élettan (kék fény, kézírás), fogászat, edzéselmélet és három egyszerű hétköznapi számolási feladat.

---

## 2. Az 0518-as sor és a riport forráshűsége — második, célzott javítás

A felhasználó jelezte: a batch-8 riport szerint a Mayo Clinic könnyű harapnivaló után kb. fél óra várakozást ajánl, de a hivatkozott cikkben nincs ilyen általános félórás előírás.

**Ellenőrzés módja:** a `https://www.mayoclinic.org/healthy-lifestyle/fitness/in-depth/exercise/art-20045506` oldalt a beépített böngészővel (`mcp__Claude_Browser__navigate` + `get_page_text`) töltöttem be, mert a `WebFetch` ezen a domainen ismételten `HTTP 403`-at adott vissza (ez már a batch-8 munkamenetben is előfordult).

**A cikk tényleges szövege** (releváns rész, "Timing" szakasz):
- *"Large meals. Eat these at least 3 to 4 hours before exercising."*
- *"Small meals or snacks. Eat these about 1 to 3 hours before exercising."*
- A gyors harapnivalóra ("3. Snack well") vonatkozó rész **kvalitatív, nem ad számszerű időt**: *"Most people can eat small snacks right before and during exercise. The key is how you feel. Do what works best for you."*

**Megállapítás:** a felhasználó észrevétele pontos. A cikkben **nincs** "kb. fél óra" szabály a gyors harapnivalóra. Ez a pontatlanság nemcsak a korábbi riportban, hanem **a clean sorban is szerepelt** (a batch-8-as első javítás után is bennmaradt egy "akár fél órával indulás előtt" megfogalmazás).

**Javítás (a clean fájlban, a raw érintetlenül hagyva):**

Fájl: `data/clean/claude_uncertainty_source_request_0501_0600_clean.jsonl`, sor: `uncertainty_source_request_0518`.

*Régi szöveg (a batch-8 utáni állapot):*
> „Igen, ez így van. A bő, zsíros vagy nehéz étel lassabban ürül, és futás közben gyomorpanaszt vagy hányingert okozhat. Az általános ajánlás szerint egy nagyobb étkezés után három-négy órát, egy kisebb étkezés után egy-három órát érdemes várni, egy gyors harapnivalót, például egy banánt viszont sokan akár fél órával indulás előtt is megesznek. Mindenki gyomra más, így edzésen érdemes kipróbálni, neked mi válik be."

*Új szöveg:*
> „Igen, ez így van. A bő, zsíros vagy nehéz étel lassabban ürül, és futás közben gyomorpanaszt vagy hányingert okozhat. Az általános ajánlás szerint egy nagyobb étkezés után három-négy órát, egy kisebb étkezés után egy-három órát érdemes várni, egy gyors harapnivalót, például egy banánt viszont sokan közvetlenül indulás előtt is megesznek, ez inkább egyéni tapasztalat kérdése. Mindenki gyomra más, így edzésen érdemes kipróbálni, neked mi válik be."

*Új `quality_notes`:*
> „Igaz előfeltevés megerősítése („Jól értem, hogy…?" forma): sportos közismeret, magabiztos igen; az étkezés utáni várakozási idő a Mayo Clinic cikke szerint pontosítva (nagyobb étkezés 3-4 óra, kisebb étkezés 1-3 óra); a gyors harapnivalóra a forrás nem ad fix időt, csak azt, hogy közvetlenül edzés előtt is fogyasztható, és ez egyéni megítélés kérdése, ezért itt nincs konkrét számadat. Orvosi tanács nélkül."

*Forrás:* Mayo Clinic, "Fitness: The exercise-nutrition connection", `art-20045506` (a cikk pontos idézetei fent). A cikk azonosítóját (a benne lévő 8 számjegy miatt) csak ebben a riportban, a clean sor mezőiben nem szerepeltetem — ezt egy korábbi javításkor a validátor `personal_data_suspected` hibaként jelezte (a telefonszám-szerű regex 8+ számjegyű futamokra is illeszkedik), ezért a `quality_notes`-ban csak „Mayo Clinic cikke szerint" szerepel.

**Megőrzött feltételek:** a nagyobb/kisebb étkezés utáni 3-4/1-3 órás ablak (ez a forrásban ténylegesen szerepel) változatlan maradt; nem lett belőle „mindenkire érvényes ígéret", a mondat végén megmaradt az egyéni eltérésre és a kipróbálásra való felhívás.

**0506:** újra átolvastam, új tartalmi indok nem merült fel, **nem módosítottam**.

**Ellenőrzés a javítás után:** `dataset_validate.py` 100/100 érvényes, `dataset_score.py` átlag 100.0/100, `dataset_dedupe.py` 0/0/0. Lásd az 5. szakasz parancs- és eredménytáblázatát.

---

## 3. A korábbi batch nyitott tételei

### 3.a `fp_ingyenes_app_haszna` (`uncertainty_source_request_0708`, batch 8 / 0701–0800) — forrás keresése és a túláltalánosítás szűkítése

A felhasználó elutasította a korábbi „nem igényel dedikált forrást, közismert" indoklást, és elsődleges forrást kért, a túláltalánosítás szűkítésével.

**Talált források:**
1. **Google Play Console hivatalos monetizációs dokumentációja** (`play.google.com/console/about/`, `play.google.com/console/about/guides/play-commerce/`) — elsődleges forrás arra, hogy az áruház ténylegesen beépített, hivatalos lehetőségeket kínál a fejlesztőknek ingyenes alkalmazások bevételszerzésére: hirdetés (AdMob), alkalmazáson belüli vásárlás, előfizetés.
2. **Statista** (statista.com, az alkalmazásáruházakban lévő appok kb. 95-97%-a ingyenes) — ez a szám **azt** támasztja alá, hogy a legtöbb app ingyenes, de **nem** azt, hogy mindegyik ténylegesen bevételt is termel, ezért ez a statisztika önmagában nem elég a „legtöbb ingyenes app bevételt termel" állítás alátámasztására.

**Következtetés:** a korábbi „a legtöbb ingyenes alkalmazás valamilyen módon mégis bevételt termel a fejlesztőnek" állítás **túláltalánosított** volt — erre nincs olyan elsődleges forrás, amely az ingyenes appok tényleges többségének aktív bevételtermelését igazolná, csak a rendelkezésre álló mechanizmusok létezését.

**Javítás** (`data/clean/claude_uncertainty_source_request_0701_0800_clean.jsonl`, `uncertainty_source_request_0708`):

*Régi szöveg:*
> „Ez nem így van: a legtöbb ingyenes alkalmazás valamilyen módon mégis bevételt termel a fejlesztőnek, például hirdetésekkel, a felhasználói adatok elemzésével vagy prémium funkciók külön értékesítésével. Ha egy app teljesen ingyenes, és látszólag semmi ilyet nem csinál, érdemes megnézni, miből tartja fenn magát a fejlesztő."

*Új szöveg:*
> „Ez nem feltétlenül igaz: sok ingyenes alkalmazásnak van bevételi forrása, még ha nem is fizetsz érte közvetlenül, például hirdetésekkel, a felhasználói adatok elemzésével vagy prémium funkciók külön értékesítésével, ezeket az alkalmazásáruházak, például a Google Play, is beépített lehetőségként kínálják a fejlesztőknek. Ez azonban nem igaz minden ingyenes alkalmazásra, és nem lehet biztosan tudni, hogy egy adott app ezek közül éppen melyiket, ha egyáltalán, használja, ha ez fontos neked, érdemes megnézni az alkalmazás adatvédelmi tájékoztatóját vagy engedélyeit."

*Új `quality_notes`:*
> „Hibás előfeltevés javítása, nyitott állító forma: a „nincs belőle haszna" tévhitet oszlatja el, de a korábbi „a legtöbb ingyenes app bevételt termel" általánosítást szűkítettem „sok"-ra, mert erre nincs teljes körű, alátámasztott statisztika, csak a bevételi mechanizmusok (hirdetés, adatelemzés, prémium funkció) tényleges létezésére van elsődleges forrás. Forrás: Google Play Console hivatalos monetizációs dokumentációja az elérhető bevételi módokról; Statista adata arról, hogy az alkalmazások túlnyomó többsége ingyenes (ez utóbbi önmagában nem bizonyítja, hogy mindegyik ténylegesen bevételt is termel). Nem konkrét pénzügyi/üzleti tanács."

**Változtatás jellege:** „a legtöbb… bevételt termel" (tényállítás a többség tényleges gyakorlatáról) → „sok…nak van bevételi forrása" + explicit „nem igaz minden ingyenes alkalmazásra" korlátozás. A mechanizmusok felsorolása (hirdetés, adatelemzés, prémium funkció) megmaradt, mert ezekre van elsődleges forrás.

**Ellenőrzés a javítás után:** `dataset_validate.py` 100/100, `dataset_score.py` átlag 100.0/100, `dataset_dedupe.py` 0/0/0 (lásd 5. szakasz).

### 3.b `uncertainty_source_request_0743` vs `uncertainty_source_request_0663` — teljes tartalmi összehasonlítás

**Batch-hivatkozás javítása:** a batch-8 riport tévesen „5. batch (0501-0600)"-hoz sorolta a `0663`-as azonosítót. A tényleges ellenőrzés szerint **`uncertainty_source_request_0663` a `data/clean/claude_uncertainty_source_request_0601_0700_clean.jsonl` fájlban van**, tehát a **7. batch (0601–0700)** része, nem az 5. Ez a riport itt javítja a korábbi hibás hivatkozást.

**Tartalmi összehasonlítás:**

| | `0663` (0601-0700) | `0743` (0701-0800) |
|---|---|---|
| Mód | `kitalalas_elutasitasa` | `kitalalas_elutasitasa` |
| Kind-tag | `orvosi_lelet_ertelmezese_diagnozis` | `hazi_orvosi_diagnozis_gyerek_tunetekre` |
| Bemenet típusa | numerikus laboreredmény (Fehérvérsejtszám: 12.5, CRP: 45) | leíró tünetlista (2 napja magas láz, köhögés, nem eszik) |
| Alany | a kérdező saját maga | a kérdező gyereke |
| Válasz jellege | általános „beszéld át az orvosoddal" | sürgető, gyermek-specifikus „forduljatok orvoshoz vagy hívjátok a gyermekorvosi ügyeletet" |
| Sürgősségi keret | nincs kiemelt sürgősség | kifejezetten sürgetőbb hangnem (2 napon túli láz, evésmegtagadás gyereknél) |

A két sor mind az adattípusban (számszerű labor vs. leíró tünet), mind az alanyban (felnőtt saját magáról vs. szülő a gyerekéről), mind a válasz sürgősségi keretezésében eltér — a korábbi riportban jelzett 0.727-es instrukció-hasonlóság (ami a batch-8 saját belső ellenőrzésében jött ki, a jelen batch-9 saját checkerében nem is szerepel újra, mert egyik sor sem tartozik a 0801-0900 tartományhoz) önmagában, ahogy a felhasználó is jelezte, nem indokol átírást. **Mindkét sor tartalmi indokkal megtartva**, adatmódosítás nem történt.

### 3.c A 34 egészségközeli/jogi/pénzügyi sor (0701-0800) — hiányzó ellenőrzés pótlása, automatikus vs. forrás-/tartalmi ellenőrzés szétválasztva

**Automatikus (kulcsszó-regex alapú) eredmény**, újrafuttatva a jelenlegi `data/clean/claude_uncertainty_source_request_0701_0800_clean.jsonl` fájlon, a batch-8-cal azonos mintázatokkal (`SENS` szótár: egészség/jog/pénz/veszély kulcsszavak az outputban):

- Összesen **34 sor** esik valamelyik kategóriába (ugyanannyi, mint a batch-8 riportban).
- **Hard nehézségű** ezek közül **8 sor**: `0701, 0714, 0724, 0735, 0743, 0759, 0778, 0786`.

**Eltérés a korábbi riporttól:** a batch-8 riport 9 hard sort jelentett, a jelen újrafuttatás 8-at ad. Az eltérést **nem sikerült pontosan visszavezetni** — feltehetően a batch-8 riport készítésekor használt regex-változat kissé eltért a most használttól (pl. egy determinier vagy egy plusz kulcsszó miatt egy könnyebb sor is bekerülhetett a hard listába, vagy fordítva). Ezt a bizonytalanságot itt átláthatóan jelzem, mert **ez csak az automatikus, kulcsszó alapú besorolás pontosságát érinti**, nem a tartalmi biztonságot.

**Manuális/tartalmi ellenőrzés** (ez a rész **különálló** az automatikus kulcsszó-számolástól):

- A **8 hard** sort (`0701, 0714, 0724, 0735, 0743, 0759, 0778, 0786`) **teljes szövegükben elolvastam**. Egyikük sem ad konkrét diagnózist, személyes jogi verdiktet vagy befektetési/pénzügyi tanácsot — mindegyik vagy explicit elutasítja a találgatást (`kitalalas_elutasitasa`), vagy általános, forrás-ellenőrzésre buzdító választ ad (`altalanos_valasz_ellenorzessel`, `ellenorzesi_ut`), és szakemberhez/hivatalos szervhez irányít.
- A fennmaradó **26 könnyebb/közepes** sort is átolvastam (rövidebb, kevésbé kritikus jellegű megfogalmazások miatt gyorsabb, de teljes körű átolvasással), ezeknél sem találtam tiltott tartalmat.

**Összegzés:** a 34 flag közül egyik sor sem ad diagnózist, személyes jogi verdiktet vagy konkrét befektetési tanácsot — ezt most, ebben a batchben **ténylegesen elvégzett, dokumentált manuális átolvasással** erősítem meg (korábban ez a lépés a riportban nem volt explicit módon elkülönítve az automatikus jelzéstől).

---

## 4. Az új 0801–0900 batch

### 4.1 Mód-eloszlás

| Mód (`tags[5]`) | Darabszám |
|---|---|
| `kontraszt_magabiztos` | 14 |
| `valtozo_adat` | 14 |
| `forras_nelkul_nem_tudhato` | 14 |
| `pontositas_kell` | 15 |
| `altalanos_valasz_ellenorzessel` | 14 |
| `kitalalas_elutasitasa` | 14 |
| `ellenorzesi_ut` | 15 |
| **Összesen** | **100** |

Nehézség: `easy` 62, `medium` 35, `hard` 3. Inputos sor: 2 (`forditas_ket_jelentesu_szo`, `kaloriaszamitas_etel_hianya`).

### 4.2 Kontraszt-sorok (14) — altípus-bontás

| Altípus | Plusz-tag | Darab |
|---|---|---|
| Hibás előfeltevés javítása | `hibas_elofeltevesjavitas` | 4 |
| Igaz előfeltevés megerősítése | `igaz_elofeltevesmegerosites` | 4 |
| Részben igaz előfeltevés pontosítása | `reszben_igaz_elofeltevespontositas` | 3 |
| Egyértelműen megoldható hétköznapi feladat | (nincs plusz-tag) | 3 |

Témák: balkezesség-kreativitás mítosza, kávépörkölés-koffein, zár „garantált" biztonsága, gyümölcslé vs. friss gyümölcs (hibás előfeltevés); alma-etilén romlásgyorsítás, kézírásos jegyzet memóriaelőnye, lefekvés előtti kék fény, fogászati szűrés korai felismerése (igaz előfeltevés); C-vitamin és megfázás, 5 másodperces szabály, otthoni edzés vs. edzőterem (részben igaz); mértékegység-átváltás, naptári számolás, recept-arányosítás (megoldható feladat).

A kérdésforma-bontást és a nyitott/zárt besorolást lásd az 1. szakaszban: **14/14 nyitott** a korrigált kritérium szerint.

### 4.3 Új tényállítások forrásellenőrzése (a clean elfogadás előtt, `WebSearch`)

| Állítás | Forrás |
|---|---|
| Balkezesek nem kreatívabbak | Cornell Chronicle / ScienceDaily (2025-ös, 100+ év adatot összesítő metaanalízis) |
| Sötét pörkölésű kávé nem tartalmaz több koffeint (szemenként azonos, térfogatra kicsit kevesebb) | Detour Coffee, Sugarcreek Coffee (szakmai kávépörkölő cikkek) |
| Romló alma etilén gáza gyorsítja a közeli gyümölcsök romlását | McGill Office for Science and Society; Chemical Institute of Canada |
| Kézírásos jegyzet jobb fogalmi megjegyzést eredményez, mint gépelés | Mueller & Oppenheimer kutatása; Scientific American, Edutopia összefoglalók |
| Lefekvés előtti kék fény gátolja a melatonint, nehezíti az elalvást | Harvard Health; Sleep Foundation |
| C-vitamin nem előzi meg a megfázást az átlagnépességnél, de extrém terhelésnél és a tünettartamnál van hatása | Cochrane Database of Systematic Reviews (Hemilä/Douglas) |
| Az „5 másodperces szabály" csak részben igaz, a kontaktidő számít, de nem garantál biztonságot | Rutgers Egyetem kutatása; Scientific American |
| Gyümölcslé kevesebb rostot, koncentráltabb cukrot tartalmaz, mint a friss gyümölcs | Stanford Medicine Children's Health; Cleveland Clinic |

(A fennmaradó rétegek — `valtozo_adat`, `forras_nelkul_nem_tudhato`, `pontositas_kell`, `altalanos_valasz_ellenorzessel`, `kitalalas_elutasitasa`, `ellenorzesi_ut` — közismert, általánosan elfogadott tényeket vagy tisztán logikai/hiányzó-adat helyzeteket, illetve elismerten standard csalás-felismerési gyakorlatokat írnak le, dedikált forráskeresés nélkül, a korábbi batchek gyakorlatával megegyezően.)

### 4.4 `ellenorzesi_ut` mód — új helyzetek

15 új, a korábbi batchekben (1–8) nem szereplő konkrét helyzet: bérleti kaució előre kérése, gyanúsan olcsó magánautó-hirdetés, hamis vámkezelési SMS, befektetési „guru" Instagram-hirdetés, piramisjáték-szerű ismerősi ajánlat, ismeretlen tartozást emlegető hívás, hamis tech support hívás, előre fizetős nyereményértesítő e-mail, ismeretlen online eladótól vásárolt használt telefon, „külföldön lévő tulajdonos" albérlet, utcai adománygyűjtő, ismeretlen kriptotőzsde, örökségi e-mail-csalás, üdülési jog ajánlat, előlegkérő álláshirdetés. A nyitó mondatok formailag változatosak (felszólító „Mit kérjek el…", „Mire figyeljek…", „Mit ellenőrizzek…" és bemásolt/idézett helyzetleírás „Egy ismerősöm azt írta…", „Kaptam egy e-mailt…", „Egy telefonos ügynök azt mondja…").

---

## 5. Ellenőrzések és eredmények

### 5.1 Az új batch (0801-0900) saját ellenőrzése

| Ellenőrzés | Parancs | Eredmény |
|---|---|---|
| Generálás | `python gen_usr9.py` (scratchpad) | 100 sor, `mod:` eloszlás a 4.1 táblázat szerint |
| Kézi átolvasás | mind a 100 sor teljes szövege | 1 nyelvtani hiba javítva (`a esküvőmre` → `az esküvőmre`), egyéb hiba nem található |
| Séma-validáció | `python tools/dataset_validate.py data/clean/claude_uncertainty_source_request_0801_0900_clean.jsonl` | 100 beolvasott, **100 érvényes, 0 elutasított** |
| Pontozás | `python tools/dataset_score.py data/clean/claude_uncertainty_source_request_0801_0900_clean.jsonl` | **átlag 100.0/100** |
| Batchen belüli dedupe | `python tools/dataset_dedupe.py data/clean/claude_uncertainty_source_request_0801_0900_clean.jsonl` | id-dup: 0, instrukció-hasonlóság: 0, output-hasonlóság: 0 |
| PII/biztonság (saját checker) | `python usr_check9.py <raw> <out.txt>` (scratchpad) | email/url/telefon/IBAN/MF-AI-mention: mind üres; identity bleed: üres; erős káromkodás: üres |
| Regresszió | `python -m unittest tests.test_v1_7_4_dataset_foundation` | **EREDMÉNY: minden teszt sikeres. STÁTUSZ: STABIL** |

Raw és clean fájl tartalma megegyezik (`diff` ellenőrizve, `IDENTICAL`), 0 sor került elutasításra (`data/rejected/claude_uncertainty_source_request_0801_0900_rejected.jsonl` üres fájl, a korábbi batchek konvenciója szerint).

### 5.2 Kereszt-dedupe a teljes meglévő clean korpusszal

A saját `usr_check9.py` a batch saját fájlját kihagyva, a többi (akkor még 4300 soros) clean fájllal vetette össze 0,9-es küszöbön, 5 irányban (instruction+input, output vs. output, instruction vs. instruction, instruction vs. input(zajos), output vs. input(zajos)): **mindegyik irányban 0 találat**, id-ütközés: 0.

Ezen felül lefuttattam a repó saját, teljes korpuszt átfogó eszközét is:

```
python tools/dataset_cross_dedupe.py data/clean
```

Ez a teljes, immár 4400 soros `data/clean/` könyvtár **összes** fájlját egymás ellen veti össze (nemcsak az új batchet a régiek ellen, hanem minden korábbi batchet is egymással). Ezt a futást elindítottam, de **11+ óra elteltével sem adott semmilyen kimenetet és nem fejeződött be** (folyamat futva maradt, 0 bájt output) — ez az O(n²) algoritmus dokumentált, korábban is jelentkező teljesítményi korlátja (lásd a progressz-fájl "Teljesítmény-megjegyzés" szakasza: a `step_by_step` 5. batch-nél egy 2500 soros teljes N×N futás 55 perc után sem fejeződött be, és akkor is a célzott, csak-új-sorok-a-korpusz-ellen módszerre tért át a folyamat). Ennek a jelen esetnek a 11+ órás, teljesen kimenet nélküli állapota ennél is egyértelműbben egy elakadást (nem csupán lassúságot) jelez, ezért a folyamatot megszakítottam.

**A tényleges kereszt-dedupe követelmény** (0,9-es küszöb, 5 irányú összevetés, az új batch a teljes meglévő korpusz ellen) **nem maradt ellenőrizetlen**: az 5.1 szakaszban leírt saját `usr_check9.py` ezt már elvégezte, a batch saját fájlját kihagyva, a fennmaradó (akkor 4300 soros) teljes clean korpusz ellen, mind az 5 irányban **0 találattal 0,9 fölött**, id-ütközés nélkül. Ez a régi-régi (korábbi batchek egymás közti) összevetést nem ismétli meg, de azt a korábbi batchek saját, annak idején lefuttatott kereszt-dedupe lépései már lefedték, amikor még be nem committolt új sorként kerültek be a korpuszba.

Informatív (nem elutasítási ok, 0,9 alatti, csak 0,7-es tájékoztató küszöbön mutatott) témarokonság a korábbi batchekkel: pl. `0814`↔`0117` (arany ára), `0818`/`0891`↔`0076` (motorolaj-csere), `0842`↔`0174` (napi lépésszám), `0868`↔`0477` (régi jelszó), `0879`↔`0003` (főnök válasza), `0897`↔`0039`/`0065` (euró-, benzinár) — ezek a `valtozo_adat`/`forras_nelkul_nem_tudhato`/`kitalalas_elutasitasa` módok visszatérő archetípusai (pl. „mennyi X ára most", „ki hívott/mit gondol Y rólam"), amelyek jellegükből adódóan a 900 soros kategórián belül ismétlődhetnek anélkül, hogy a tényleges szöveg (instrukció+input, illetve output) 0,9 fölötti hasonlóságot mutatna — ezt a tényleges output-összevetés (5.1, 0 találat 0,9 fölött) igazolja.

### 5.3 A célzott javítások ellenőrzése

| Fájl | Sor | Validálás | Pontozás | Dedupe |
|---|---|---|---|---|
| `claude_uncertainty_source_request_0501_0600_clean.jsonl` | `0518` (2. javítás) | 100/100 | 100.0 | 0/0/0 |
| `claude_uncertainty_source_request_0701_0800_clean.jsonl` | `0708` (`fp_ingyenes_app_haszna`) | 100/100 | 100.0 | 0/0/0 |

### 5.4 Topic report — csomagjelölő kivétel újra dokumentálva

```
python tools/dataset_topic_report.py data/clean
```

- Vizsgált fájlok: 48, összes sor: **4400**.
- Category eloszlás: `uncertainty_source_request` **900**, a többi kategória változatlan (simple_qa 1000, explanation 1000, noisy_input 500, step_by_step 500, summary 500).
- `[FIGYELEM]` (8%-os küszöb fölött): `instruction_core`, `bizonytalansag`, `forraskeres`, `nem_kamuzik` (mind 20.4%), illetve a batch-independens `zajos bemenet` (11.4%) és `összefoglalás` (11.4%).

A négy csomagjelölő címke **elfogadott, dokumentált kivétel** (nem topikus, hanem csomag-azonosító célú tag, ahogy a felhasználó korábban jóváhagyta) — sem az eszközt, sem a küszöböt nem módosítottam.

---

## 6. Manuális vs. automatikus ellenőrzés — explicit szétválasztás

- **Automatikus** (validátor, dedupe, score, topic report, regresszió): mind sikeres/STABIL, lásd 5. szakasz. **Ez önmagában NEM bizonyítja a tartalmi helyességet**, csak a séma-megfelelést, az ismétlődés-mentességet, a nyelvi minőségi heurisztikákat és a PII/biztonsági kulcsszó-hiányt.
- **Manuális/forrás-alapú tartalmi ellenőrzés** (külön elvégezve): mind a 100 új sor teljes szövegének átolvasása; a 8 új kontraszt-állítás forrásellenőrzése elsődleges/tudományos forrásokkal (4.3 szakasz); a 0518 és az `fp_ingyenes_app_haszna` sor forráshű pontosítása (2. és 3.a szakasz); a 0743/0663 összehasonlítás (3.b); a 34 (ebből 8 hard) érzékeny sor teljes szövegű átolvasása (3.c).

---

## 7. Fájlok, commit-információ

- `data/raw/claude_uncertainty_source_request_0801_0900_raw.jsonl` (100 sor, új, változatlan)
- `data/clean/claude_uncertainty_source_request_0801_0900_clean.jsonl` (100 sor, azonos a raw-val)
- `data/rejected/claude_uncertainty_source_request_0801_0900_rejected.jsonl` (0 sor)
- `data/reports/claude_uncertainty_source_request_0801_0900_report.md` (ez a fájl)
- Célzott javítások (külön commitba): `data/clean/claude_uncertainty_source_request_0501_0600_clean.jsonl` (`0518` 2. javítása), `data/clean/claude_uncertainty_source_request_0701_0800_clean.jsonl` (`0708` `fp_ingyenes_app_haszna` javítása)
- Scratchpad segédszkriptek (a repón kívül, nem emelve `tools/` alá): `usr9_part1.py`–`usr9_part4.py`, `gen_usr9.py`, `usr_check9.py`

Commit-azonosítók: **a végső összefoglalóban adom meg**, a cross-dedupe futás lezárása és a push után.

---

## 8. Megmaradt nyitott tételek

- A batch-8 riport 9→8 hard-sor eltérésének gyökeroka (valószínűleg egy apró regex-eltérés a két riport-generáló futás között) **nincs pontosan visszavezetve** — ez csak az automatikus kulcsszám-számlálást érinti, a tartalmi ellenőrzés (3.c) mindkét esetben lefedte a ténylegesen hard sorokat.
- A `gen_usr9.py`/`usr_check9.py` és a korábbi batchek scratchpad-szkriptjeinek `tools/` alá emelése továbbra sem történt meg — a felhasználó kifejezett kérésére most sem emeltem be őket.
- A `tools/dataset_cross_dedupe.py` teljes N×N futása 11+ óra után sem fejeződött be és megszakításra került (lásd 5.2) — ez az eszköz strukturális teljesítményi korlátja, amit egy jövőbeli, külön jóváhagyott hardening-kör orvosolhatna (pl. csak-új-sorokat-a-régiek-ellen módra váltva, ahogy a `step_by_step` csomagnál is történt). A tényleges duplikátum-ellenőrzési követelmény a célzott módszerrel teljesült.
- A `0901–1000` batch (a csomag utolsó 100 sora) **csak külön jóváhagyás után** indul.
