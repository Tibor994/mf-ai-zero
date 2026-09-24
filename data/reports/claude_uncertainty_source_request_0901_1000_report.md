# `uncertainty_source_request` batch riport — 0901–1000 (10., záró installment, 6. csomag "Bizonytalanság / forráskérés")

Dátum: 2026-09-25
Terjedelem: 100 új sor (`uncertainty_source_request_0901` – `uncertainty_source_request_1000`). Ezzel a csomag 1000/1000 sorra egészült ki. A csomag teljes completion auditja külön riportban van: `data/reports/uncertainty_source_request_1000_completion_audit.md`. A batch mellett az audit közben talált tartalmi javítások külön commitba kerültek (lásd 6. szakasz).

**Fontos kezdő megjegyzés:** a 100-as automatikus pontszám és a sikeres séma-/dedupe-ellenőrzés önmagában nem bizonyítja a tartalmi helyességet. Ez a riport mindenhol külön jelöli az *automatikus ellenőrzések* és a *kézi/forrás-alapú ellenőrzések* eredményét.

---

## 0. Kiinduló állapot — tényleges fájlokból ellenőrizve

```
wc -l data/clean/*.jsonl | tail -1                                                    → 4400
grep -l '"category": "uncertainty_source_request"' data/clean/*.jsonl | xargs wc -l   → 900
git log --oneline -3                                                                   → a066b3c (batch 0801-0900), e97ba92 (célzott javítás), 80c87c1
```

Ez megegyezett a jóváhagyásban megadott állapottal (900 sor, 4400 clean sor, a legutóbbi javítás és batch commitja `e97ba92` és `a066b3c`). A batch és a javítások végén újra ellenőriztem: 1000 / 4500 (lásd 5. szakasz és az audit).

---

## 1. A megszakított duplikációellenőrzés tisztázása

### 1.1 Melyik teljes korpuszos futás szakadt meg

- Parancs: `python tools/dataset_cross_dedupe.py data/clean` (a repó meglévő, az összes clean fájlt egymás ellen összevető eszköze).
- Indítás: 2026-09-23, kb. 03:47 (helyi idő), 4400 soros korpuszon (a 0801–0900 batch clean fájljával együtt).
- Állapot: a folyamat háttérben futott, **kimenetet nem adott** (az eszköz csak a legvégén ír ki bármit), majd 11 óránál is hosszabb futás után (ellenőrzéskor 15:10) **általam leállításra került**. A korábbi jelentésemben ezt „elakadásnak” neveztem; ez **nem volt igazolt**. Amit ténylegesen tudok: az eszköz szűretlen `difflib.SequenceMatcher` összevetést végez minden sorpáron, és nem ír folyamatjelzést.
- Az időigény becslése ebben a munkamenetben mérésből: ugyanezen eszköz `find_duplicates()` függvényét a 1500 soros `simple_qa` + `step_by_step` + `deepseek` részhalmazon lefuttattam (`dd_crosscheck.py`), ez **2333 másodpercig (kb. 39 perc)** tartott. A páronkénti költség négyzetes, így a 4400–4500 soros korpuszra ez nagyságrendileg 5–6 óra. A 11+ órás futás ennél is hosszabb volt, az ok (például a gép alvó állapota) nincs kivizsgálva. **A leállított futás eredményt nem adott, a megszakadt futásból nincs használt eredmény.**
- A megszakított futást **nem indítottam újra változtatás nélkül** (a kérésnek megfelelően).

### 1.2 Milyen célzott ellenőrzés fejeződött be a 0801–0900 batch idején

- Eszköz: scratchpad `usr_check9.py` (a repón kívül).
- Mit vetett össze: a batch 100 új sorát (raw fájl) a **többi 4300 clean sorral** (a batch saját clean fájlja kihagyva), 5 mezőpárra: `instruction||input`, `output–output`, `instruction–instruction`, `instruction–input(zajos)`, `output–input(zajos)`.
- Módszer: `difflib.SequenceMatcher(None, a, b).ratio()`, **küszöb 0,9**, normalizálás nélkül (`strip` csak), a szűrők (hossz-arány, `real_quick_ratio`, `quick_ratio`) csak kizáró, felső korlát-jellegű elő-szűrők.
- Eredmény: mind az 5 irányban 0 találat 0,9 fölött.
- **Amit ez nem fedett le:** a később javított korábbi sorokat (`0518`, `0708`), a régi–régi párokat, és a később szerkesztett sorokat. A „0 találat” tehát csak az akkori hatókörre (100 új sor × 4300 meglévő sor) érvényes volt.

### 1.3 Az új, szakaszolt és mérhető ellenőrzés (jelen munkamenet)

Rövid próbafutás előbb (`dd_full.py trial`): 10 késői sor 0,2 mp (0,017 mp/sor), ebből a teljes futás ~75 mp-re volt becsülhető. Ezután szakaszolt futás (`dd_full.py run 200`): 200 soros szakaszok, látható előrehaladással, minden szakasz részeredménye külön JSON fájlba mentve, újraindításkor a kész szakaszok kihagyva.

- **Módszer azonossága az eredeti eszközzel** (a küszöb és a minőségi követelmény változatlan, 0,9): ugyanaz a `difflib.SequenceMatcher(None, későbbi, korábbi).ratio()`, ugyanazok a mezők (`instruction || input`, `output`, `id`), ugyanaz a szöveg-előkészítés (`strip`). A gyorsítás kizárólag matematikailag pontos elő-szűrés: a `ratio() ≥ 0,9` feltételhez szükséges, hogy a hossz-arány (`2·min/(la+lb)`) és a karakter-multihalmaz-metszet arány is ≥ 0,9; ezeken elbukó párok ratio()-ja nem érheti el a küszöböt.
- **Igazolás:** (a) az eredeti eszköz a 1500 soros részhalmazon 39 perc alatt pontosan azt a 6 „későbbi sor → korábbi sor” találatot adta, amit az új módszer (`simple_qa_0857/0851`, `0859/0851`, `0914/0671`, `1081/0734`, `step_by_step_0229/0227`, `simple_qa_0489/0915`); az új módszer ezen felül a `0859/0857` párt is jelzi, mert nem áll meg az első találatnál; (b) egy 71 soros mintán (a 11 ismert találat + 60 véletlen sor) az eredeti eszköz és az új módszer azonos halmazt adott 0,9-nél (6/6, output 0/0) és 0,8-nál is (8/8, output 0/0) (`dd_verify.py`).
- **Hatókör:** a teljes, végleges **4500 soros** `data/clean/` korpusz **minden sora minden korábbi sorral** szemben (N×N), minden szakasz lefutott (23/23), 27 másodperc alatt. A futás **a végső, javított adatverzión** történt (minden most javított sort is beleértve).
- **Eredmény:** `id`-duplikátum 0; `output`-hasonlóság ≥ 0,9: 0; `instruction||input` hasonlóság ≥ 0,9: 7 pár, **mind a `simple_qa` és `step_by_step` csomagokban** (`simple_qa_0857/0851` 0,904; `0859/0851` 0,919; `0859/0857` 0,904; `0914/0671` 0,919; `1081/0734` 0,918; `0489/0915` 0,921; `step_by_step_0229/0227` 0,900). Az `uncertainty_source_request` csomag egyetlen sora sem érintett. Ezek a más csomagok korábbi, a progressz-fájlban részben már dokumentált jelzései (rövid, sablonos kérdések), a jelen munka hatókörén kívül esnek, tartalmi értékelésüket nem végeztem el (lásd nyitott tételek).
- **Csomag-szintű 5 irányú ellenőrzés** (`audit_pkg.py pairs`, szakaszolt, 10×100 soros részeredmények mentve): az 1000 sor belül (1000×1000) és a többi 3500 sorral szemben, mind az 5 mezőpárra: **0 találat 0,9 fölött**. A 0,8–0,9 közötti tájékoztató találatok tartalmi értékelése az audit riportban.
- **Ami nem fedett le:** az `input–output`, `input–input` és `quality_notes` mezők páronkénti összevetése (a `dataset_dedupe.py` sem vizsgálja ezeket); a 0,9-es küszöb alatti, de tartalmilag ismétlődő sorok általános felderítése (ezt a 0,8-as tájékoztató lista és a kézi olvasás fedte).

---

## 2. Az utolsó 100 példa

### 2.1 Témaválasztás — a korábbi 900 sor átnézése alapján

Előzetesen mind a 900 sor `tags[6]` témacímkéit módonként kigyűjtöttem, és a lefedettséget elemeztem. Feltűnő aránytalanságok: a személyes, az időben változó (ár, menetrend) és a csalásfelismerési helyzetek dominálnak; kevés a **tudásbeli határ** (történelmi, tudományos kérdés, aminek nincs pontos válasza), a **technikai/informatikai ellenőrzés**, a **mértékegység- és jelentés-többértelműség**, a **háztartási és kerti gyakorlati ajánlás** és a **nem csalás jellegű ellenőrzési helyzet**. Ezekre építettem.

Módonkénti elosztás (86 sor a hat módra, a cél a csomagszintű kiegyenlítés: a csomag végén 144/144/144/144/147/152 + 125 kontraszt):

| Mód | Db | Miért ennyi |
|---|---|---|
| `kontraszt_magabiztos` | 14 | előírás |
| `kitalalas_elutasitasa` | 16 | a 128-as állásról 144-re |
| `forras_nelkul_nem_tudhato` | 16 | 128 → 144 |
| `pontositas_kell` | 15 | 129 → 144 |
| `altalanos_valasz_ellenorzessel` | 15 | 129 → 144 |
| `ellenorzesi_ut` | 12 | 135 → 147 (a mód eleve az egyik legtöbbet lefedett) |
| `valtozo_adat` | 12 | 140 → 152 |
| **Összesen** | **100** | |

Nehézség: easy 46, medium 49, hard 5. Inputos sor: 1 (`0942`).

### 2.2 `ellenorzesi_ut` — a legutóbbi 15 csalásfelismerési példa után 12 más jellegű helyzet

Egyik sem csalásfelismerési: letöltött fájl épsége (ellenőrző összeg), gépi fordítás átnézése, Wikipédia-adat felhasználása dolgozatban, konyhai mérleg pontossága, csomagolt élelmiszer allergénjelölése, biztonsági mentés visszaállíthatósága, füstjelző működése, gyógyszertárban kapott más nevű készítmény, internetes kód futtatása előtt, hosszabbító terhelhetősége, táblázatos végösszeg ellenőrzése, két könyv eltérő évszáma (azonosítók: `0902 0903 0904 0909 0920 0934 0935 0956 0957 0978 0982 0992`). Az egészség- és biztonságközeli sorok (`0920`, `0956`, `0978`) a döntést szakemberre (allergológus, gyógyszerész, villanyszerelő) bízzák.

### 2.3 A 14 kontraszt-sor — altípusok és kérdésforma

Az „ugye?” és az „Igaz, hogy…?” **eldöntendő (zárt)** kérdésnek számít; ezt alkalmaztam. Összesen 12/14 nyitott (minimum 8), 2/14 zárt.

| ID | Altípus (plusz-címke) | kind | Forma |
|---|---|---|---|
| 0968 | `hibas_elofeltevesjavitas` | `fp_villam_ketszer_fa_alatt` | állító kijelentés – nyitott |
| 0971 | `hibas_elofeltevesjavitas` | `fp_nagy_fal_urbol` | „ugye?” – **zárt** |
| 0939 | `hibas_elofeltevesjavitas` | `fp_denever_vak` | WH-kérdés téves előfeltevéssel – nyitott |
| 0999 | `hibas_elofeltevesjavitas` | `fp_nyelvterkep` | állító kijelentés – nyitott |
| 0905 | `igaz_elofeltevesmegerosites` | `tp_vesebab_nyersen` | állító kijelentés – nyitott |
| 0914 | `igaz_elofeltevesmegerosites` | `tp_meh_csipes_tobbseg` | állító kijelentés – nyitott |
| 0918 | `igaz_elofeltevesmegerosites` | `tp_tengervizivas` | „Igaz, hogy…?” – **zárt** |
| 0947 | `igaz_elofeltevesmegerosites` | `tp_tengervizfagyaspont` | állító kijelentés – nyitott |
| 0926 | `reszben_igaz_elofeltevespontositas` | `rp_elektromos_auto_kibocsatas` | állító kijelentés – nyitott |
| 0946 | `reszben_igaz_elofeltevespontositas` | `rp_mez_eltarthatosag` | „Mennyire igaz…?” – nyitott |
| 0967 | `reszben_igaz_elofeltevespontositas` | `rp_haz_vihar_biztonsag` | állító kijelentés – nyitott |
| 0919 | egyértelműen megoldható (nincs plusz-címke) | `ct_autofogyasztas_250km` | WH-feladatkérdés – nyitott |
| 0928 | egyértelműen megoldható (nincs plusz-címke) | `ct_tizedes_sorrend` | felszólító önálló feladat – nyitott |
| 0980 | egyértelműen megoldható (nincs plusz-címke) | `ct_cipo_kedvezmeny` | WH-feladatkérdés – nyitott |

4 hibás előfeltevés, 4 igaz előfeltevés, 3 részben igaz, 3 megoldható feladat. A helyzetek és a válaszok tartalma is változatos (világűr, időjárás-biztonság, állattan, élettan, tengerek fizikája, élelmiszerbiztonság, rovarok, ételtárolás, közlekedési környezetvédelem, viharbiztonság, hétköznapi számolás).

### 2.4 Új tényállítások forrásellenőrzése (a clean elfogadás előtt)

A „közvetlenül olvastam” azt jelenti, hogy a forrás oldalát ebben a munkamenetben `WebFetch`-csel vagy a beépített böngészővel megnyitottam és a releváns szöveget elolvastam; a „keresési összefoglaló” azt, hogy csak a `WebSearch` találatból következtetek a forrás tartalmára, a forrást magát nem nyitottam meg.

| Sor | Állítás | Forrás | Ellenőrzés módja |
|---|---|---|---|
| `0971` Nagy Fal az űrből | Holdról nem látható, Föld körüli pályáról nehéz vagy lehetetlen szabad szemmel; nagy teljesítményű teleobjektívvel fényképezhető | NASA „Great Wall” képcikk | közvetlenül olvastam (böngésző). A „keskeny, színe a tájéhoz hasonló” rész: BBC Sky at Night / Britannica keresési összefoglaló |
| `0968` villám | gyakran ugyanoda csap; Empire State Building átlag évi 23; fa alatt állni a villámbalesetek második leggyakoribb oka; szilárd épület vagy fémtetős autó a menedék | Nemzeti Meteorológiai Szolgálat „lightning myths” | közvetlenül olvastam |
| `0939` denevér | nem vak, kis szeme nagyon érzékeny, sötétben lát | USGS „Are bats blind?” | közvetlenül olvastam; az echolokáció kiegészítő szerepe közismert, külön forrás nélkül |
| `0999` nyelvtérkép | nincs szétválasztott ízzóna, minden ízlelőbimbós rész érzékeny minden ízre; Hänig 1901 | Smithsonian Magazine | közvetlenül olvastam |
| `0947` tengervíz fagyáspont | édesvíz 32 °F, tengervíz kb. 28,4 °F | NOAA Ocean Service „Can the ocean freeze?” | közvetlenül olvastam |
| `0918` tengervíz ivása | ivása akár halálos, a vese csak a tengervíznél kevésbé sós vizeletet termel | NOAA „Can you drink seawater?” | közvetlenül olvastam |
| `0905` vörös vesebab | fitohemagglutinin; 4-5 nyers szem tüneteket okozhat; 1-3 órán belül; 12 óra áztatás, legalább 10 perc forralás; lassúfőző nem elég; konzerv biztonságos | hongkongi Centre for Food Safety | közvetlenül olvastam; az FDA hosszabb forralást ajánl: keresési összefoglaló, nem szerepel a válaszban |
| `0914` méhcsípés | ~21 ezer fajból 8 pusztul el csípés után; mézelő méh szemcsés szúrója; többi faj szúrója sima | The Conversation cikk | közvetlenül olvastam; a poszméhek sima szúrója: Britannica keresési összefoglaló |
| `0946` méz | lezárva évtizedekig-évszázadokig stabil, de sötétedhet, ízét vesztheti, kristályosodhat; gyakorlati eltarthatóság gyakran 2 év | National Honey Board GYIK | közvetlenül olvastam (böngésző) |
| `0926` elektromos autó | nincs kipufogógáz-kibocsátás; áramtermelés és akkumulátorgyártás kibocsátással jár; életciklusra jellemzően alacsonyabb, mint a benzinesé | EPA „Electric Vehicle Myths” | közvetlenül olvastam |
| `0967` lakás vihar alatt | szilárd épület menedék, de a ház sem 100%-os; vezetékes telefon, készülékek, vezetékek, kábelek, számítógép, vízvezeték, fém ajtók-ablakok kerülendők | Nemzeti Meteorológiai Szolgálat „lightning myths” | közvetlenül olvastam |
| `0919`, `0928`, `0980` | százalék-, arány-, tizedes összehasonlító számolás | (számolás) | kézzel ellenőrizve: 6·2,5 = 15; 0,05 < 0,45 < 0,5 < 0,506; 15 000·0,8 = 12 000 |

A nem kontraszt módok tényszerű, számszerű állításai is forrásellenőrzést kaptak: WHO felnőtt mozgási ajánlás (`0929`), NIST jelszócsere-ajánlás (`0984`), NFPA füstjelző (`0935`), USDA nyers csirke 1-2 nap (`0994`), tulipánhagyma ültetési mélység (`0922`), tengeri/szárazföldi mérföld (`0988`) — ezekhez **keresési összefoglaló** alapján jutottam, a forrást nem nyitottam meg, ezt a sorok `quality_notes` mezője is jelzi. Az audit közben (lásd 6. szakasz) hat ilyen tartalmú sor pontosítására került sor.

---

## 3. Ellenőrzések és eredmények (a 0901–1000 batch)

### 3.1 Automatikus ellenőrzések

| Ellenőrzés | Parancs | Eredmény |
|---|---|---|
| Generálás | `python gen_usr10.py` (scratchpad) | 100 sor, mód-eloszlás a 2.1 szerint, 100 egyedi instruction+input / output / quality_notes |
| Séma | `python tools/dataset_validate.py data/clean/claude_uncertainty_source_request_0901_1000_clean.jsonl` | 100 beolvasott, **100 érvényes, 0 elutasított** |
| Pontozás | `python tools/dataset_score.py <clean>` | átlag **100.0/100** |
| Batchen belüli dedupe | `python tools/dataset_dedupe.py <clean>` | id 0, instruction 0, output 0 |
| Saját ellenőrző | `python usr_check10.py <raw> <out>` (scratchpad) | email / URL / telefon / IBAN / MF-AI-említés: mind üres; identity bleed: üres; erős káromkodás: üres; az „angol szó” jelzés 3 sorban az angol forráscímek miatt (pl. „Can you drink seawater?” a `quality_notes` mezőben), tartalmi angol keveredés nincs |
| Keresztduplikáció a 4400 meglévő sorral | `usr_check10.py` (5 mezőpár, 0,9) | **0 találat mind az 5 irányban**; id-ütközés 0 |
| Regresszió | `python -m unittest tests.test_v1_7_4_dataset_foundation` | **minden teszt sikeres, STÁTUSZ: STABIL** |
| Topic report | `python tools/dataset_topic_report.py data/clean` | 49 fájl, 4500 sor, `uncertainty_source_request` 1000 |

Az `usr_check10` *tájékoztató* hasonlósági listája (0,7 fölött az instructionben) 10 párt jelzett a meglévő korpusszal; ezeket az 3.3 szakaszban tartalmilag értékeltem.

### 3.2 Kézi ellenőrzés — mind a 100 új sor teljes átolvasása

Minden sort egyenként elolvastam (kérdés, input, válasz). A generálás előtt/után javított tételek:

- **Tartalmi ismétlés a meglévő korpusszal:** a `biblia_szoszam_kiadas` sor (Pontosan hány szó van a Bibliában magyarul?) lényegében megismételte a `0029` sort (0,883 instruction-hasonlóság **és** azonos válaszelv: kiadásfüggő, szószámlálóval megszámolható). Ez tartalmi, nem csak formai ismétlés volt, ezért **kicseréltem** egy valóban új helyzetre (`sorozat_kovetkezo_resz_cselekmenye`: még be nem mutatott rész tartalma).
- Sablonos nyitások szétszórása: 3 `Milyen gyakran…`, 3 `Mondd meg pontosan…`, 1 `Mennyi ideig…` nyitó instruction átfogalmazva (a `Milyen gyakran kell…` sablon a korpuszban már így is gyakori).
- Nyelvi javítások: `vagy a halál körülményeire vagy kíváncsi` (kétszeres „vagy”) átírva; a jelszócsere-sor vesszős mondattoldása két mondatra bontva; az internetes kód sor nehézkes nyitómondata (`Elolvasva sorról sorra…`) átírva; egy `quality_notes` elgépelés (`GY.I.K.` → `GYIK`).
- A tag-ellenőrzés (ASCII snake_case, egyedi kind) a generálás előtt lefutott, hibát nem adott; a `quality_notes` mezők a batchen belül 100/100 egyediek.
- **A kézi átolvasás nem talált** diagnózist, személyes jogi verdiktet, befektetési tanácsot vagy adagolást; az egészség- és biztonságközeli sorok (`0908` gomba, `0920` allergén, `0956` gyógyszer, `0978` hosszabbító, `0930` elhunyt rokon, `0987` élettartam, `0979` szülési nap) mind szakemberhez irányítanak.

### 3.3 A hasonlósági találatok tartalmi értékelése (megtartva vagy cserélve)

| Új sor ↔ meglévő | Hasonlóság | Tartalmi értékelés | Döntés |
|---|---|---|---|
| `0941` (sorozat következő rész **cselekménye**) ↔ `0097` (következő rész **megjelenési dátuma**) | 0,82 | más információtípus (tartalom vs. időpont), más mód (`forras_nelkul` vs. `valtozo_adat`), eltérő válasz | megtartva |
| `0933` ágynemű, `0993` porszívószűrő, `0898` fékbetét ↔ `0818` fogkefe, `0076` olaj | 0,76–0,86 | azonos **sablon** („mennyi időnként cserélendő”), de más tárgy, más tényanyag és más ellenőrzési út; a mód lényege az általános érték + saját ellenőrzés | megtartva |
| `0949` római utazás költsége ↔ `0059` jegyár, `0843` javítás | 0,70–0,74 | mind pontosításkérés hiányzó feltételek miatt, de más feltételkészletet kérnek (indulás/időpont/szállás vs. útvonal/kedvezmény vs. hiba/eszköz) | megtartva |
| `0950` első tűzgyújtó ↔ `0044` első villámfénykép | 0,74 | mindkét „első” kérdés, más témakör, más régészeti/fotótörténeti forráshoz irányít | megtartva |
| `0953` törölköző mosási hőfok ↔ `0809` hűtő hőfoka | 0,72 | csak a „Hány fokon…” nyitás közös | megtartva |
| `0969` autó meghibásodása ↔ `0591` futár érkezése | 0,73 | csak a „Mondd meg pontosan” nyitás közös | megtartva (az instruction később is átfogalmazva) |
| `0983` dal játszása ↔ `0399` folt kimosása | 0,73 | csak a „Hogyan…, ezt” nyitás közös | megtartva |
| `0842` mai lépésszám ↔ `0174` „Hány lépést tettem ma?” | **0,88 / 0,90** | **tartalmilag ismétlés** (ugyanaz a kérdés, ugyanaz az elv: nincs hozzáférés a lépésszámlálóhoz) | **kicserélve** az audit során `Melyik napon vásároltam a mosógépemet?` sorra (lásd 6. szakasz) |

---

## 4. Manuális vs. automatikus — összefoglaló szétválasztás

- **Automatikus (séma, dedupe, pontozás, regresszió, PII/URL/identity-bleed szűrők):** mind sikeres, ez nem bizonyítja a tartalmi helyességet.
- **Manuális/forrás-alapú (külön elvégezve):** mind a 100 sor teljes átolvasása; a kontraszt-sorok tényállításainak forrásellenőrzése (2.4, ebből 11/11 közvetlenül elolvasva a magyarul megfogalmazott fő állításokhoz, a részletek egy része másodlagos összefoglaló); a hasonlósági találatok tartalmi értékelése (3.3).
- **Nem történt meg:** független emberi (más személy általi) átolvasás; szakértői (orvosi, jogi, pénzügyi) átnézés.

---

## 5. Végállapot és fájlok

- `uncertainty_source_request`: **1000 / 1000**; teljes clean korpusz: **4500 sor** (1000 simple_qa + 1000 explanation + 500 step_by_step + 500 summary + 500 noisy_input + 1000 uncertainty_source_request).
- Új fájlok: `data/raw/claude_uncertainty_source_request_0901_1000_raw.jsonl` (100 sor; a raw a **generáláskori szöveg**, a 6. szakasz javításai után a clean tőle egy sorban eltér: `0842`), `data/clean/…_0901_1000_clean.jsonl` (100 sor), `data/rejected/…_0901_1000_rejected.jsonl` (0 sor, üres fájl a konvenció szerint), ez a riport.
- Scratchpad segédszkriptek (a repón kívül, **nem** emelve a `tools/` alá): `usr10_part1.py`–`usr10_part4.py`, `gen_usr10.py`, `usr_check10.py`, `fix10_a.py`, `dd_full.py`, `dd_verify.py`, `dd_crosscheck.py`, `audit_pkg.py`.
- Topic report kivétel: a négy csomagjelölő címke (`instruction_core`, `bizonytalansag`, `forraskeres`, `nem_kamuzik`) a 4500 soros korpuszban egyenként 1000 sor (22,2%), `[FIGYELEM]` jelzéssel; a felhasználó által jóváhagyott, dokumentált csomagjelölő-kivétel. A `zajos bemenet` és `összefoglalás` címkék (11,1%) más csomagok jelölői. A küszöböt és a validátort nem módosítottam.

---

## 6. Az audit közben talált tartalmi javítások (külön commit)

A batch checkjeitől független, a csomagszintű audit közben talált, **már commitolt clean sorokra** vonatkozó javításokat külön commit tartalmazza (`v1.13.12-dataset-fix`), csak a clean fájlokban, a raw fájlok érintetlenek. Részletek, régi és új szöveggel, forrással: az audit riportban (5. szakasz). Érintett sorok: `0317` (quality_notes egyedisítés), `0641` (tartalmi ismétlés a `0404`-gyel), `0782` (quality_notes egyedisítés), `0787`, `0816`, `0829`, `0842`, `0849`, `0864`, `0898`.

## 7. Nyitott tételek

- A 100 sor nem esett át független emberi vagy szakértői átnézésen.
- A keresési összefoglaló alapján forrásolt állítások (WHO, NIST, NFPA, USDA, mérföld, tulipán, FDA-forralás) közvetlen elsődleges forrásból való újraolvasása.
- A csomag válaszsablonjai és instruction-nyitásai (lásd audit): nem blokkoló, de nyitott minőségi tétel.
