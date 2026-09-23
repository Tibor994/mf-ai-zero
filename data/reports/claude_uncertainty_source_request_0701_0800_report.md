# Nyolcadik uncertainty_source_request batch - uncertainty_source_request_0701-0800

**Verdikt: STABIL.** 100 sor, **100 clean / 0 rejected**, `category: uncertainty_source_request`, a **6. csomag (Bizonytalanság / forráskérés)** nyolcadik batchje az új, bővített 17 000 soros `instruction_core`-ban.

## 0. Kiinduló állapot ellenőrzése a tényleges fájlokból

```bash
wc -l data/clean/*.jsonl | tail -1
grep -l '"category": "uncertainty_source_request"' data/clean/*.jsonl | xargs wc -l | tail -1
```

Eredmény: **teljes clean korpusz 4200 sor**, ebből **`uncertainty_source_request` 700 sor** — megegyezik a jelentett állapottal. A batch után: **800 / 1000** a 6. csomagban, teljes clean korpusz **4300 sor** (6. fejezet).

## 1. Az előző jelentés kérdésforma-besorolásának ellenőrzése (0601-0700)

A kérésnek megfelelően újraolvastam a `data/clean/claude_uncertainty_source_request_0601_0700_clean.jsonl` fájl mind a 14 kontraszt-sorát, és a **pontosított kritérium** szerint soroltam be: az „ugye?” és az „Ez így igaz?” **eldöntendő kérdés**, tehát **nem számít nyitottnak**; nyitottnak csak az állító mondat (kérdőjel nélkül) és a valódi, WH- vagy feladatkérő kérdés (mennyi, mikor, hány stb.) számít.

| id | Instruction (rövidítve) | Mondattípus | Nyitott? |
|---|---|---|---|
| `0602` | „…ezzel biztos jelentősen csökken majd a számlám.” | állító mondat | igen |
| `0617` | „Aki nem posztol…, az szerintem nem is használja igazán.” | állító mondat | igen |
| `0636` | „…Mennyibe kerül összesen?” | WH-kérdés (feladat) | igen |
| `0642` | „…mert nem romlik meg soha.” | állító mondat | igen |
| `0647` | „…szóval a telefonom most semmilyen jelet nem bocsát ki, **ugye?**” | eldöntendő (tag-kérdés) | **nem** |
| `0658` | „…tényleg jelentősen csökkenti a sérülés kockázatát autóbalesetnél?” | eldöntendő kérdés | **nem** |
| `0659` | „…hánykor kell felébrednem?” | WH-kérdés (feladat) | igen |
| `0669` | „Azt tanultuk edzésen, hogy…” | állító mondat | igen |
| `0678` | „…**Ez így igaz?**” | eldöntendő (tag-kérdés) | **nem** |
| `0686` | „…pontosan meg tudom majd mondani, mekkora lesz…” | állító mondat | igen |
| `0687` | „…ezzel tényleg jobban tisztán tartom a fogaimat?” | eldöntendő kérdés | **nem** |
| `0692` | „…Hány dkg lisztet mérjek ki?” | WH-kérdés (feladat) | igen |
| `0698` | „Azt hallottam, hogy…” | állító mondat | igen |
| `0700` | „…szóval ez biztos egészségesebb…” | állító mondat | igen |

**Eredmény: 10 nyitott, 4 zárt (eldöntendő) a pontosított kritérium szerint.** A 10 >= a kérésben előírt legalább 8-as minimumot, tehát **a korábbi riport állítása lényegében helytálló volt a végeredményt tekintve (>= 8 teljesült), de a besorolása pontatlan volt**: az „ugye?” és az „Ez így igaz?” sorokat tévesen nyitottnak minősítette. Mivel a tényleges nyitott darabszám (10) továbbra is meghaladja a minimumot, **a kérés szerint elegendő a riport pontosítása, adatmódosításra nincs szükség**; a `0601_0700` clean fájl e négy sora (`0647`, `0658`, `0678`, `0687`) tartalmilag helyes és változatlan marad, csak a besorolásuk módosul „zárt, eldöntendő kérdés”-re.

## 2. A `0501-0600` batch `0518` és `0506` sorának célzott lezárása

### 2.1. `0518` — javítva

Forrás: [Eating and exercise: 5 tips to maximize your workouts (Mayo Clinic, art-20045506)](https://www.mayoclinic.org/healthy-lifestyle/fitness/in-depth/exercise/art-20045506) (a cikk közvetlen lekérése 403-as hibát adott, ezért két különböző keresés eredményét vetettem össze, amelyek egyezően idézik a cikk tartalmát).

A Mayo Clinic cikke szerint: nagyobb étkezés után **legalább három-négy órát**, kisebb étkezés után **egy-három órát**, könnyű, alacsony rosttartalmú harapnivaló után pedig **kb. fél órát** érdemes várni edzés előtt.

| | Szöveg |
|---|---|
| **Régi (hibás)** | „Igen, ez így van. A bő, zsíros vagy nehéz étel lassabban ürül, és futás közben gyomorpanaszt vagy hányingert okozhat. **Egy nagyobb étkezés után érdemes megvárni egy-két órát**, előtte elég egy kisebb, könnyű harapnivaló, például egy banán. Mindenki gyomra más, így edzésen próbáld ki, mi válik be.” |
| **Új (javított)** | „Igen, ez így van. A bő, zsíros vagy nehéz étel lassabban ürül, és futás közben gyomorpanaszt vagy hányingert okozhat. **Az általános ajánlás szerint egy nagyobb étkezés után három-négy órát, egy kisebb étkezés után egy-három órát érdemes várni**, egy könnyű harapnivaló, például egy banán, viszont akár fél órával indulás előtt is elfogyasztható. Mindenki gyomra más, így edzésen érdemes kipróbálni, neked mi válik be.” |

**Indok**: a „nagyobb étkezés után egy-két óra” a forrás által javasolt 3-4 óránál rövidebb, tehát az eredeti szöveg egy általános útmutatást a valóságosnál megengedőbb, mindenkire érvényes ígéretté egyszerűsített. A javított szöveg különválasztja a nagyobb étkezést, a kisebb étkezést és a gyors harapnivalót, mindegyikhez a forrás szerinti időtartammal, és megtartja az egyéni eltérésre figyelmeztető záró mondatot. **Csak a `data/clean/claude_uncertainty_source_request_0501_0600_clean.jsonl` fájlt módosítottam, a megfelelő `data/raw/claude_uncertainty_source_request_0501_0600_raw.jsonl` fájlt nem.**

### 2.2. `0506` — ellenőrizve, nem módosítva

A meglévő mondat: „A bemelegítés fontos, a hosszú, egy helyben tartott nyújtás edzés előtt viszont nem bizonyítottan véd a sérüléstől.”

Forrás: [Dynamic Warm-ups Play Pivotal Role in Athletic Performance and Injury Prevention (PMC12034053)](https://pmc.ncbi.nlm.nih.gov/articles/PMC12034053/), [Is Static Stretching Effective for Injury Prevention? (NASM)](https://blog.nasm.org/fitness/is-static-stretching-the-best-strategy-for-injury-prevention-and-performance-enhancement).

A szakirodalom szerint a nyújtás önmagában nem csökkenti bizonyítottan a sérülés kockázatát, és a dinamikus bemelegítés hatékonyabb; a NASM-összefoglaló szerint a **45 másodpercnél rövidebb** statikus nyújtás egy teljes bemelegítő rutinba ágyazva még segíthet is magas intenzitású tevékenységnél. Az eredeti mondat kifejezetten a „**hosszú, egy helyben tartott**” nyújtásra vonatkozik, ez a feltétel megegyezik a forrás megkülönböztetésével (hosszú/statikus vs. rövid/dinamikus rutinba ágyazott), ezért **tartalmi indok a módosításra nincs**. A mondatot **nem módosítottam**, sem a clean, sem a raw fájlban.

### 2.3. Nyitva maradó tétel

Nincs olyan tényállítás egyik sorban sem, amelyet ne lehetett volna megbízható forrással ellenőrizni; mindkét sor lezárt (egy javítással, egy megerősítéssel). Nyitott tétel csak annyiban marad, hogy a `0518` javítás egy **stílusbeli** kompromisszum: a pontosabb megfogalmazás két számpárt tartalmaz (3-4 óra és 1-3 óra), ez kicsit hosszabb mondatot eredményezett; ez tartalmi szempontból szükséges volt, nem hiba.

## 3. Az új batch: `uncertainty_source_request_0701-0800`

### 3.1. A hét mód (`tags[5]`)

| Mód-címke | Sor |
|---|---|
| `valtozo_adat` | 15 |
| `forras_nelkul_nem_tudhato` | 14 |
| `pontositas_kell` | 14 |
| `altalanos_valasz_ellenorzessel` | 14 |
| `kitalalas_elutasitasa` | 14 |
| `ellenorzesi_ut` | 15 |
| `kontraszt_magabiztos` | 14 |

A mód-eloszlás kiegyensúlyozott, megegyezik a korábbi batchek 15/14/14/14/14/15/14 mintázatával.

### 3.2. A 14 kontraszt-sor és a kérdésforma-besorolás (a pontosított kritérium szerint, előre alkalmazva)

| id | Típus | Kérdésforma | Nyitott? | Rövid tartalom |
|---|---|---|---|---|
| `0708` | hibás előfeltevés (`fp_ingyenes_app_haszna`) | állító mondat | igen | ingyenes app haszontalansága – tévhit |
| `0753` | hibás előfeltevés (`fp_mikro_vitamin`) | állító mondat | igen | mikrohullám vitaminvesztés – tévhit |
| `0704` | hibás előfeltevés (`fp_gluten_mentes_egeszsegesebb`) | állító mondat | igen | gluténmentes = egészségesebb mindenkinek – tévhit |
| `0732` | hibás előfeltevés (`fp_bor_erleles`) | állító mondat | igen | minél tovább érlelik a bort, annál jobb – tévhit |
| `0707` | hibás előfeltevés (`fp_naptej_faktor_egesznap_ved`) | állító mondat | igen | magas faktor = egész napos védelem – tévhit |
| `0710` | igaz előfeltevés (`tp_biztonsagi_ov_turbulencia`) | állító mondat | igen | biztonsági öv és turbulencia |
| `0799` | igaz előfeltevés (`tp_szemetszelektalas_ujrahasznositas`) | állító mondat | igen | szelektív gyűjtés hatékonyabb |
| `0767` | igaz előfeltevés (`tp_alvashiany_koncentracio`) | állító mondat | igen | alváshiány rontja a koncentrációt |
| `0747` | igaz előfeltevés (`tp_szappanos_kezmosas_hatekonysaga`) | állító mondat | igen | szappanos kézmosás hatékonysága |
| `0773` | részben igaz (`rp_telefon_100szazalek_toltes`) | állító mondat | igen | 100%-os töltés és akkumulátor-öregedés |
| `0726` | részben igaz (`rp_biciklisisak_fejserules`) | állító mondat | igen | sisak csökkenti, de nem zárja ki a fejsérülést |
| `0748` | egyértelműen megoldható feladat | WH-kérdés | igen | vacsoraszámla négyfelé osztása |
| `0782` | egyértelműen megoldható feladat | WH-kérdés | igen | indulási idő + útidő |
| `0741` | egyértelműen megoldható feladat | WH-kérdés | igen | recept felezése |

**Mind a 14 sor nyitott** a pontosított kritérium szerint (0 „ugye?”, 0 „Ez így igaz?”, 0 zárt *Ha…, akkor…?*), jóval a kért legalább 8 fölött.

### 3.3. Fact-check az új kontraszt-sorok tényállításaira (a clean elfogadás előtt elvégezve)

| id | Fajta | Állítás | Forrás | Eredmény |
|---|---|---|---|---|
| `0753` | hibás előfeltevés | mikrohullámú főzés tönkreteszi a vitaminokat | [Does Microwave Cooking Destroy Nutrients? (News-Medical)](https://www.news-medical.net/health/Does-Microwave-Cooking-Destroy-Nutrients-What-Science-Shows.aspx), [Is microwave cooking nuking all the nutrients? (Popular Science)](https://www.popsci.com/health/do-microwaves-destroy-nutrients/) | Tévhit megerősítve: a rövidebb főzési idő és kevesebb víz miatt a mikrohullámú főzés sok zöldségnél jobban megőrzi a C-vitamint, mint a vízben főzés. |
| `0704` | hibás előfeltevés | gluténmentes étrend mindenkinek egészségesebb | [Ditch the Gluten, Improve Your Health? (Harvard Health)](https://www.health.harvard.edu/healthy-aging-and-longevity/ditch-the-gluten-improve-your-health), [Gluten-Free Diet: Is It Right for Me? (Johns Hopkins Medicine)](https://www.hopkinsmedicine.org/health/conditions-and-diseases/celiac-disease/what-is-a-glutenfree-diet) | Tévhit megerősítve: nincs bizonyíték egészségügyi előnyre lisztérzékenység nélkül, sőt rost- és tápanyaghiány kockázata is van. |
| `0732` | hibás előfeltevés | minél tovább érlelik a bort, annál jobb | [Is it true that all wine improves with age? (Wine Spectator)](https://www.winespectator.com/articles/is-it-true-that-all-wine-improves-with-age), [Does Wine Really Taste Better With Age? (ScienceABC)](https://www.scienceabc.com/eyeopeners/wine-really-age-better-age) | Tévhit megerősítve: a borok döntő többsége (becslések szerint akár 90%-a) az első évben a legjobb, csak kevés, magas tannin- vagy savtartalmú bor javul évekig. |
| `0707` | hibás előfeltevés | magas faktorszámú naptej egész napra véd, nem kell újra kenni | [How Often Should You Reapply Sunscreen? (Cleveland Clinic)](https://health.clevelandclinic.org/how-often-to-reapply-sunscreen), [How Often Should You Reapply Sunscreen? (Houston Methodist)](https://www.houstonmethodist.org/blog/articles/2024/may/how-often-should-you-reapply-sunscreen/) | Tévhit megerősítve: a faktorszám a kiszűrt UV-arányt jelzi, nem az időtartamot; minden faktornál kb. kétóránként, izzadás/fürdés után azonnal újra kell kenni. |
| `0773` | részben igaz | tartós 100%-os töltés hamar tönkreteszi az akkut | [Lithium-Ion Battery Degradation: The Complete Guide (Chargie)](https://chargie.org/lithium-ion-battery-degradation-guide/), [Charge Phone to 80%: Battery Health Truth (EcoFlow)](https://www.ecoflow.com/us/blog/charge-phone-battery-health) | Részben igazolva: a tartós 100%-os töltöttség valóban gyorsítja az öregedést, de ez évek alatti fokozatos kapacitásvesztés, nem hirtelen meghibásodás. |
| `0726` | részben igaz | a sisak teljesen kizárja a fejsérülést | [Helmet Use in Preventing Head Injuries (American Academy of Pediatrics, *Pediatrics*)](https://publications.aap.org/pediatrics/article/150/3/e2022058878/188764/Helmet-Use-in-Preventing-Head-Injuries-in), [Helmet Usage Reduces Serious Head Injury Without Decreasing Concussion (PubMed)](https://pubmed.ncbi.nlm.nih.gov/32932191/) | Részben igazolva: a sisak a súlyos fejsérülés kockázatát kutatásonként kb. felére-nyolcvanöt százalékára csökkenti, de nem zárja ki teljesen, és az agyrázkódás elleni hatása korlátozottabb. |
| `0710` | igaz előfeltevés | bekötött biztonsági öv csökkenti a turbulencia okozta sérülés esélyét | [Turbulence: Staying Safe (FAA)](https://www.faa.gov/travelers/fly_safe/turbulence) | Megerősítve: az FAA szerint a turbulenciás sérülések több mint 90%-a be nem kötött utasoknál történik. |
| `0799` | igaz előfeltevés | szelektíven gyűjtött hulladék nagyobb eséllyel kerül újrahasznosításra | [Best Practices: Source Separation (US EPA)](https://www.epa.gov/transforming-waste-tool/source-separation), [Recovery of plastic from mixed waste boosts recycling rates but affects quality (Nature)](https://www.nature.com/articles/d41586-026-01759-3) | Megerősítve: a forrásnál szétválogatott anyag tisztább és nagyobb eséllyel újrahasznosítható, mint a szennyezettebb, vegyesen gyűjtött hulladék. |
| `0767` | igaz előfeltevés | kevés alvás után nehezebb koncentrálni | [How Does Sleep Deprivation Affect the Brain? (Sleep Foundation)](https://www.sleepfoundation.org/sleep-deprivation/lack-of-sleep-and-cognitive-impairment), [Can Sleep Deprivation Affect Reaction Time? (Sleep Foundation)](https://www.sleepfoundation.org/sleep-deprivation/sleep-deprivation-and-reaction-time) | Megerősítve: az alváshiány rontja a figyelmet, a reakcióidőt és a döntéshozatalt. |
| `0747` | igaz előfeltevés | szappanos kézmosás hatékonyabb, mint a puszta vizes öblítés | [Handwashing Facts (CDC)](https://www.cdc.gov/clean-hands/data-research/facts-stats/index.html), [The Effect of Handwashing with Water or Soap on Bacterial Contamination of Hands (PMC)](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3037063/) | Megerősítve: egy tanulmány szerint a vizes öblítés 23%-ra, a szappanos mosás 8%-ra csökkentette a baktériumszámot. |
| `0708` | hibás előfeltevés | az ingyenes appnak nincs haszna a fejlesztőnek | — | Nem igényelt dedikált keresést: közismert, széles körben dokumentált üzleti modellekről van szó (hirdetés, felhasználói adat elemzése, freemium/prémium funkció), amelyek nyilvánosan és általánosan ismertek. |

A `0741`, `0748`, `0782` (egyértelműen megoldható feladatok) tisztán számítási/logikai állítások, ezeket a válaszban szereplő levezetéssel ellenőriztem (fejszámolással), külső forrás nem szükséges.

### 3.4. Bizonytalansági típusok témaváltozatossága

| Mód | Jellemző témák |
|---|---|
| `valtozo_adat` | könyvtári hosszabbítás, helyi buszmenetrend, munkahelyi ebédmenü, orvosi ügyelet, zenekari turnédátum, áramkimaradás oka, diákbérlet ára, piaci árukínálat, appfizetőssé válás, futóverseny nevezési díja, áramszolgáltatói tarifacsomag, iskolai nyílt nap, mobilos készülékcsere-akció, veszélyeshulladék-gyűjtőpont, taxidíj |
| `forras_nelkul_nem_tudhato` | barátnő új neve, ház előző tulajdonosa, kolléga születésnapja, saját régi tanulmányi átlag, régi falubeli kocsma neve, barát új telefonszáma, szomszéd költözésének oka, egyesületi taglétszám, régi versenyeredmény, háziállat életkora, talált tárgy tulajdonosa, munkatárs szakdolgozata, tanár munkahelye, kutya születésnapja |
| `pontositas_kell` | tárgy nélküli kérdések (*Megéri ez nekem?*, *Mit csináljak most?*, *Kinek higgyek?*, *Milyen színben kérjem?*, *Meddig várjak?*, *Milyen hosszan tartson?*, *Hova kéne mennem ezzel?*, *El kell hinnem ezt?*, *Melyik verzió a jobb?*, *El merjem küldeni?*, *Hány réteg kell rá?*, *Van ebben valami rossz?*, *Mennyit kellene gyakorolnom?*) |
| `altalanos_valasz_ellenorzessel` | pénzügyi alapok, gyerek olvasási kedve, lakás bérbeadása, kutya és medence, maratoni regeneráció, képernyőidő-korlátozás, biciklitúra tervezése, munkahelyi beilleszkedés, ház első megtekintése, kiskutya és macska bemutatása, egyedüli utazás, gyerek sötétfélelme, öntözőrendszer, kölyökkutya nevelése |
| `kitalalas_elutasitasa` | vizsgasiker-ígéret, kitalált kritikai visszhang, hamis levéldátum, hamis felelős a szobakárnál, hamis alapítási év, hamis márka-felsőfok, hamis futásteljesítmény, hamis versenytapasztalat, állatkínzás-vád bizonyíték nélkül, hamis csoportmunka-arány, hamis alibi, hamis orvosi felmentés, hamis díj a terméken, gyerektünetekből diagnózis |
| `ellenorzesi_ut` | társkereső profil hamissága, ingatlan tulajdonjoga, befektetési oldal ajánlása, kézműves mester megbízása, nyereményjáték-csalás, hiteligénylés ismeretlen cégtől, antik bútor eredete, jótékonysági SMS-akció, gyorstalpaló nyelvtanfolyam ígérete, banki adathalász üzenet, közösségi finanszírozás, ingyenes filmnézés-oldal, távmunka-szerződés, bio minősítés, önkéntes szervezet |

**Az `ellenorzesi_ut` mód mondatszerkezeti változatossága**: a 15 sorból csak 2 kezdődik „Hogyan…”/„Honnan…” igés kérdéssel, a többi 13 eltérő formájú: felszólító („Mit kérjek el…”, „Mit nézzek meg…”, „Mit ellenőrizzek…”, „Mire figyeljek…”), bemásolt/idézett helyzet („Egy ismerős azt írta…”, „Egy telefonos ügynök azt mondja…”, „Egy cég azt ígéri…”, „Kaptam egy üzenetet…”, „Egy weboldal ingyenes filmnézést ígér…”, „A boltban azt mondták…”, „Azt mondja az eladó…”), illetve „Mielőtt…, mit érdemes tudnom?” szerkezet. A felhasználói helyzetek is változatosak: társkeresés, ingatlan, befektetés, kézműves megbízás, nyereményjáték-csalás, hitelfelvétel, régiség, adománygyűjtés, nyelvtanfolyam, banki adathalászat, közösségi finanszírozás, streaming, munkaszerződés, élelmiszer-minősítés, önkéntesség — egyik sem ismétlődik a korábbi hét batch domináns „Hogyan ellenőrizzem, hogy X valódi-e?” mintázatából.

### 3.5. Formai döntések

- **`tags`**: minden sorban `["magyar", "instruction_core", "bizonytalansag", "forraskeres", "nem_kamuzik", <mód>, <téma>]`; a 11 előfeltevéses/pontosító soron nyolcadik elemként a megfelelő plusz címke (`hibas_elofeltevesjavitas` 5, `igaz_elofeltevesmegerosites` 4, `reszben_igaz_elofeltevespontositas` 2). A 3 egyértelműen megoldható feladat plusz címke nélkül maradt.
- **`input`**: 99 sorban üres, **1 sorban** bemásolt szöveg (gyerek tünetei, `0743`).
- **`difficulty`**: easy 56 / medium 35 / hard 9.
- **`quality_notes`**: soronként egyedi, a kontraszt-soroknál a kérdésformát is megnevezi.
- **Sorrend**: deterministikus keverés (seed 20261004).

## 4. Topic report kivétel dokumentálása

A `tools/dataset_topic_report.py` a 4300 soros korpuszra:

| Tag | Sor | Arány | Jelzés |
|---|---|---|---|
| `instruction_core` | 800 | 18.6% | `[FIGYELEM]` |
| `bizonytalansag` | 800 | 18.6% | `[FIGYELEM]` |
| `forraskeres` | 800 | 18.6% | `[FIGYELEM]` |
| `nem_kamuzik` | 800 | 18.6% | `[FIGYELEM]` |
| `zajos bemenet` | 500 | 11.6% | `[FIGYELEM]` (korábbi csomagból, ehhez a batchhez nem kapcsolódik) |
| `összefoglalás` | 500 | 11.6% | `[FIGYELEM]` (korábbi csomagból, ehhez a batchhez nem kapcsolódik) |

A négy jelölő címke ennél a csomagnál **csomagjelölő**, nem tematikai jellegű, a `uncertainty_source_request` kategória minden során rajta van, ezért a küszöb átlépése **nem tematikai túlsúlyhiba**. A `[FIGYELEM]` jelzés ezekre **kivételként dokumentálva**; az eszköz kódját és a 8%-os küszöböt **nem módosítottam**.

## 5. Ellenőrzések: parancsok, eredmények, reprodukálhatóság

Környezet: Windows, `PYTHONIOENCODING=utf-8 PYTHONUTF8=1`, a `C:\Users\Lenovo\OneDrive\Dokumentumok\MF-AI-Zero` gyökérből futtatva. A `torch` import alatti ártalmatlan NumPy-hiányra figyelmeztető `UserWarning` minden futásnál megjelenik, a kimenetekben szűrve van.

```bash
# kiinduló allapot a fajlokbol
wc -l data/clean/*.jsonl | tail -1
grep -l '"category": "uncertainty_source_request"' data/clean/*.jsonl | xargs wc -l | tail -1

# az 0518-as celzott javitas utan: a javitott clean fajl ellenorzese
python tools/dataset_validate.py data/clean/claude_uncertainty_source_request_0501_0600_clean.jsonl
python tools/dataset_score.py data/clean/claude_uncertainty_source_request_0501_0600_clean.jsonl

# az uj batch semaja
python tools/dataset_validate.py data/clean/claude_uncertainty_source_request_0701_0800_clean.jsonl

# dedupe
python tools/dataset_dedupe.py data/clean/claude_uncertainty_source_request_0701_0800_clean.jsonl

# quality score
python tools/dataset_score.py data/clean/claude_uncertainty_source_request_0701_0800_clean.jsonl

# regresszios teszt
python -m unittest tests.test_v1_7_4_dataset_foundation

# topic report a teljes clean konyvtarra
python tools/dataset_topic_report.py data/clean
```

A batchen belüli hasonlóság és a teljes korpusz elleni kereszt-dedupe (0.9 küszöb) a scratchpadbeli, nem repóbeli `usr_check8.py` scripttel készült (a `usr_check7.py` egyenes módosítása, `difflib.SequenceMatcher` és a repóbeli `src/guard.py: looks_like_identity_bleed`); ezt **nem emeltem be** a `tools/` alá.

| Ellenőrzés | Eredmény |
|---|---|
| `dataset_validate.py` (0501-0600, az `0518` javítás után) | Beolvasott sorok: 100, Érvényes sorok: **100**, Elutasított sorok: **0** |
| `dataset_score.py` (0501-0600, az `0518` javítás után) | Átlagos pontszám: **100.0/100** |
| `dataset_validate.py` (0701-0800) | Beolvasott sorok: 100, Érvényes sorok: **100**, Elutasított sorok: **0** |
| `dataset_dedupe.py` (0701-0800) | id-duplikátumok: **0**, instruction-hasonlóság duplikátumok: **0**, output-hasonlóság duplikátumok: **0** |
| `dataset_score.py` (0701-0800) | Átlagos pontszám: **100.0/100** |
| `tests.test_v1_7_4_dataset_foundation` | minden teszt sikeres, **STÁTUSZ: STABIL** |
| Saját kereszt-dedupe a 4200 meglévő clean sor ellen (5 összevetés, 0.9 küszöb) | **0/0/0/0/0** találat, **0** id-ütközés |
| Saját batchen belüli összevetés (instruction/output, 0.6 küszöb) | 3 pár, legnagyobb 0.64 (`0757`/`0775`, két különböző „Miért/Melyik” kérdés), >= 0.9: **0** |
| Instruction-hasonlóság a teljes korpusszal (0.7 küszöb, tájékoztató) | 1 találat (`0743` ~ az 5. batch `0663` sora, mindkettő laboreredmény-diagnózis elutasítás, de eltérő tünetleírással és értékekkel) |
| Safety (e-mail, URL, telefonszám, azonosító/IBAN, MF-AI/Nextora, `guard.looks_like_identity_bleed`, önbemutatkozás-jel, angol stopword, erős káromkodás) | mind **0** |

## 6. Kézi átolvasás és javítások

1. **Azonosítók**: `0701`-`0800` folytonos.
2. **Teljes átolvasás**: mind a 100 sort (kérdés, bemásolt szöveg, válasz) végigolvastam két körben.
3. **Javított hibák**:
   - Két hiányzó mód-sor pótlása az első vázlatban (`pontositas_kell` 13 -> 14: `mennyit_kellene_gyakorolnom`; `kitalalas_elutasitasa` 12 -> 14: `sajat_ceg_alapitasi_ev_hamisitasa`, `sajat_edzettsegi_szint_tulzasa_versenyen`) és egy `altalanos_valasz_ellenorzessel` sor (`elso_kolyokkutya_neveles`), hogy a mód-eloszlás megegyezzen a korábbi batchekével.
   - Egy ékezetes kind-tag (`helyi_futóverseny...`) ASCII snake_case-re javítva.
   - Nyitás-koncentráció: az „Ezt nem ismerem, és…” szó szerinti kezdet 8-ról 3-ra csökkent (5 sor átfogalmazva: `0705`, `0706`, `0733`, `0751`, `0777`).
   - Két nyelvtani hiba javítva: „megüsd magad vagy **elessz**” -> „…**elesel**” (`0710`); „az iratok másolatát külön **a** eredetitől” -> „…külön **az** eredetitől” (`0715`).
4. **Nem kellett javítani**: a validátor, a dedupe és a score a nyers fájlon is 100/100, illetve 100.0 eredményt adott már az utolsó javítási kör után; elutasított sor nem volt.

## 7. Nyitott tartalmi kérdések

1. **`0743`/`0663` témarokonság**: mindkét sor laboreredmény vagy tünetlista alapján kért diagnózist utasít el; a felhasznált adatok és megfogalmazás eltér (0.727 hasonlóság, a 0.9-es dedupe-küszöb alatt), de a következő batchekben érdemes más témát választani ehelyett.
2. **`fp_ingyenes_app_haszna` forrásolása**: ez az egyetlen kontraszt-állítás, amelyhez nem társítottam dedikált külső forrást, mert közismert üzleti modellről van szó; ha ez nem elég szigorú mérce, jelezd, és a következő batchben minden kontraszt-állításhoz keresek forrást, függetlenül a nyilvánvalóságtól.
3. **`0518` (előző batch) stílusa**: a javított mondat két időintervallum-párt tartalmaz, valamivel hosszabb, mint az eredeti; tartalmilag szükséges, de érdemes figyelni, hogy a jövőben ne halmozódjanak ilyen hosszabb kontraszt-mondatok.
4. **Egészség-közeli és jogi-pénzügyi sorok** (34 kulcsszavas sor, 9 `hard`): mindegyik tanács- vagy diagnózis nélküli, de nagyobb mennyiségnél külön szakmai átnézést igényelnek.
5. **Séma-bővítés eszközkérdése**: a `usr_check8.py`/`gen_usr8.py` a repón kívül maradt; a `tools/` alá emelésük külön jóváhagyást igényel, ezt a kört a kérés szerint nem tettem meg.

## 8. Fájlok, commitok, állapot

- **1. commit (célzott javítás)**: `data/clean/claude_uncertainty_source_request_0501_0600_clean.jsonl` (csak az `0518` sor módosítva; a megfelelő `data/raw/...` fájl változatlan).
- **2. commit (új batch)**:
  - Raw: `data/raw/claude_uncertainty_source_request_0701_0800_raw.jsonl` (100 sor)
  - Clean: `data/clean/claude_uncertainty_source_request_0701_0800_clean.jsonl` (100 sor)
  - Rejected: `data/rejected/claude_uncertainty_source_request_0701_0800_rejected.jsonl` (0 sor, üres fájl)
  - Report: `data/reports/claude_uncertainty_source_request_0701_0800_report.md` (ez a fájl, mindkét kört dokumentálja)

Nem indítottam tanítást, nem módosítottam webapp/backend kódot, validátort, dedupe-, score- vagy topic report eszközt. A helyi `data/reports/dataset_autopilot_progress.md` a meglévő szabály szerint frissült, de nem lett commitolva. Nem kezdtem el az `uncertainty_source_request_0801_0900` batchet.

**STÁTUSZ: STABIL.**
