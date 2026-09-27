# MT-3 — többfordulós duplikáció-ellenőrző és csoportképzés — jelentés

> **REVÍZIÓ (2026-09-27): ez a jelentés az mt3-1.0 állapotot írja le. A 3. és a 6. szakasz megfeleltetéseit (`>=` alap, triviális minta `review`, névsemlegesített döntés, deklarált változat lefokozása, „jóváhagyásra vár”) a felhasználó döntései felülírták; az eszköz mt3-2.0-ra módosult. A jelenlegi viselkedést és mérést lásd: `data/reports/mt2_report.md` A. rész és `docs/MULTITURN_DEDUPE.md`. A 4. szakasz mérései (59 teszt, 46 mutáns, 60,1 mp) az mt3-1.0-ra vonatkoznak.**

Dátum: 2026-09-26. Eszköz: `tools/multiturn_dedupe.py` (mt3-1.0). Tesztek: `tests/test_multiturn_dedupe.py`. Dokumentáció: `docs/MULTITURN_DEDUPE.md`. Bizonyítékok: `data/reports/audit_evidence/mt3_dedupe/`.

Nem történt tanítás, valódi tanítóadat-generálás; a tanító- és chat kód, a webapp/backend és a meglévő validátorok/eszközök **nem módosultak** (csak új fájlok és riportok). A hat kizárás érvényben maradt (a TE-1 export továbbra is 4500 sorból 6-ot kizár, 4494-et exportál). A tesztadat mesterséges és elkülönített (`mtfx_` azonosító, `meta.fixture: true`); az 1000 beszélgetéses csomagba nem számít, valódi többfordulós adat továbbra sincs. Semmilyen adat nem lett training-ready.

## 1. A kiinduló állapot ellenőrzése a tényleges repóval

| Állítás | Ellenőrzés | Eredmény |
|---|---|---|
| a legutóbbi commit `068e1b5` | `git log`, `git rev-parse HEAD origin/main` | egyezik (HEAD = origin/main = `068e1b5de82e…`), a munkafa tiszta (csak a két helyi, követetlen riport) |
| 4500 clean sor | a `data/clean/*.jsonl` sorainak megszámolása | **4500** (explanation 1000, noisy_input 500, simple_qa 1000, step_by_step 500, summary 500, uncertainty_source_request 1000) |
| 6 kizárt, 4494 exportált | a TE-1 exportáló kétszeri futtatása | **4500 beolvasva, 6 kizárva, 4494 exportálva**, mindkétszer |
| valódi többfordulós adat nincs | `data/raw|clean|rejected|inbox` alatt `*multiturn*` | **nincs** (a `tests/fixtures/multiturn/` 5 fixture-je tesztadat) |
| TE-1, TE-2, MT-0, MT-1 kész | a tesztkészletek futtatása a munka végén | 100 teszt OK (35 + 36 + 29) |
| 17 000 példás terv | összevetés a `multiturn_package7_plan.md` 1. szakaszával | egyezik (3000/3000/2000/2000/2000/1000/1000/1000/1000/1000); a régi 4900-as cél a tervben elavultként szerepel |

**Eltérések (dokumentálva):**
1. A projektet a kérésben „Nextora Zero”-ként említed; a repó (kód, dokumentáció, az MT-1 azonosság-szűrő) „Nexora”/„MF-AI-Zero” néven szerepel. Az MT-1 mindkét írásmódot elutasítja a beszélgetés-szövegben; a repó elnevezésein nem változtattam.
2. Az előző jelentésem „következő lépés” szakaszában elgépeltem az eszköz nevét egy félmondatban; a tervben és a kódban mindenhol `tools/multiturn_dedupe.py` szerepel, tehát a repó és a terv között nincs eltérés.
3. További eltérést nem találtam.

## 2. Mi készült, mely fájlok változtak

Minden fájl **új** (a meglévő fájlok közül csak a terv- és a haladási riport frissült):

| Fájl | Szerep |
|---|---|
| `tools/multiturn_dedupe.py` | az MT-3 eszköz |
| `tests/test_multiturn_dedupe.py` | 59 teszt |
| `docs/MULTITURN_DEDUPE.md` | módszer, normalizálás, pontszám-jelentés, küszöb-megfeleltetés, csoportosítás, kivételek, korlátok |
| `data/reports/mt3_report.md` | ez a jelentés |
| `data/reports/audit_evidence/mt3_dedupe/` | mérés, mutációs vizsgálat, bemutató- és valós-export futás (README a mappában) |
| `data/reports/multiturn_package7_plan.md` | frissítve (MT-3 kész, állapotok) |

**Mit vet össze:** azonosítók ismétlődését (fájlon belül, fájlok között, a TE-1 export azonosítóival); teljes beszélgetések pontos, normalizálás utáni és közeli egyezését (szerep- és pozíció-őrzően); a tanítási mintákat (releváns előzmény + kérdés + válasz) csomagon belül, csomagok (fájlok) között és a 4494 exportált példával; közeli változatokat csoportosít (`mtg_…` csoportazonosító, egyszeres kötés, tranzitív lezárás). A részleges szövegegyezést (`info`) külön jelzi a valóban ismétlődő tanítási mintától (`sample_exact`/`sample_near`). Minden találat rögzíti a rekordot és a fordulót (fájl, sor), az egyezés típusát, a pontszámot és a módszert, a döntési státuszt és az indokot, a csoportazonosítót (rekord- és csoportszinten); a futás a bemeneti fájlok ellenőrzőösszegéhez kötött (`--verify-report`).

## 3. A kézikönyvi szabályok alkalmazása — és ami nem értelmezhető magyarázat nélkül

A kézikönyvi számokat (0,90 → felülvizsgálat, 0,95 → alapból elutasítás, pontos ismétlődés → elutasítás/javítás) **nem módosítottam**, és parancssorból nem is módosíthatók. A választott mérőszám: `difflib.SequenceMatcher(None, a, b, autojunk=False)` egyező-karakter arány (`2·M/(|a|+|b|)`) normalizált szövegen; beszélgetés-szinten szerep- és pozíció-őrző összevont arány, minta-szinten `min(kérdés, válasz, előzmény)`. Ez **szöveges átfedés, nem bizonyított jelentésazonosság**. A részletek a `docs/MULTITURN_DEDUPE.md` 2–4. szakaszában.

A határok az alábbi helyeken nem értelmezhetők magyarázat nélkül; ezek **jóváhagyást kérő megfeleltetések**, nem csendes szabálymódosítások:

| Kérdés | Mért eltérés | Az eszköz viselkedése | Jóváhagyandó |
|---|---|---|---|
| a kézikönyv „fölött”-je: `>` vagy `>=` | a meglévő eszközök `>=`-t használnak | alapból `>=`, a pontos 0,90/0,95 `at_boundary` jelzést kap; `--handbook-strict` a szó szerinti `>` | melyik legyen az alap |
| rövid szövegek | két rövid kérdés („hány nap van egy hétben/évben”) 0,933 | rövid mintánál (kérdés+válasz < 60 karakter) a hasonlóság nem dönt, csak a pontos egyezés jelez | a 60 karakteres kapu és a triviális minta = `review` (nem `reject`) |
| átfogalmazás | a kézzel átfogalmazott változat összevont karakter-aránya 0,634, a tartalmi szó-átfedése 0,429 (nem rokon fixture-párok: ≤ 0,074) | a 0,90/0,95 nem értelmezhető; külön heurisztika (`review`, küszöb 0,35, ideiglenes kalibráció 15 fixture-páron és 1 kézi átfogalmazáson) | a heurisztika és a küszöb; valódi adaton újrakalibrálni |
| névcsere | névsemlegesítés nélkül 0,9747, névsemlegesítéssel 1,0 | alapból névsemlegesítés (MT-0 névtár); a névcserés másolat `reject` | a névsemlegesítés alapértelmezése |
| deklarált változat | tervezett változat (közös `split_group`) is ≥ 0,95 lehet | legfeljebb `review` (nyers pontos másolat mindig `reject`); dokumentált kivétel: `--exceptions` | a kivétel-mechanizmus szabályai |

**Egy közös köszönés, rövid válasz vagy azonos kérdés eltérő előzményben önmagában nem minősít duplikáltnak egy beszélgetést** (tesztelt): a beszélgetés-szintű arány az egész beszélgetésen számít; az azonos kérdés eltérő előzménnyel `info`; a triviális, pontosan ismétlődő első-forduló minta mintaszinten `review`, de a beszélgetés `conversation_decision` mezője nem `blocked`. Az elutasítás **haladási tiltás** (`progression: blocked`), nem forrásadat-törlés; a bemeneti fájlok bájtra változatlanok maradnak (tesztelt).

**Láncolt hasonlóság:** ha A hasonlít B-re és B C-re, egy csoport lesz (egyszeres kötés, tranzitív lezárás), mert a közvetítő taggal átszivárogna a tartalom a felosztás határán; 5 tag fölött `group_too_large` (`review`) és a leggyengébb élek jelölése véd a túlzottan nagy csoport ellen. A csoportazonosító `mtg_<a legkisebb rekordazonosító>`: a bemeneti sorrendtől és a fájlfelosztástól független; kisebb azonosítójú tag csatlakozásakor változik, ezért az MT-2 felosztás előtt a végleges bemenetre kell futtatni, és a jelentés ellenőrzőösszegéhez kötni.

## 4. Tesztek és mérések

**Tesztek:** `tests.test_multiturn_dedupe`: **59 teszt OK** (~60–90 mp). A célzott esetek: pontos másolat; ismétlődő azonosító (fájlon belül, fájlok között, az exporttal); névcserés változat (névsemlegesítéssel és anélkül); átfogalmazás; közös köszönés eltérő feladattal; azonos kérdés eltérő előzménnyel és azonos előzménnyel; felcserélt szerepek és felcserélt/eltolt üzenetsorrend; láncolt csoportképzés (egységteszt + valós rekordok), reprodukálható és stabil csoportazonosítók, túl nagy csoport, persona/deklarált csoport; egyezés a TE-1 exporttal (pontos, közeli 0,90–0,95 és ≥ 0,95, előzményes fordulat, válasz-egyezés); sérült/hamisított/hibás TE-1 export; hibás JSON, nem turns-validált rekord, hiányzó és üres bemenet; a bemenet futás **közben** és **után** megváltozik (`--verify-report`); kimeneti útvonal-védelem, felülírás tilalma; határértékek 0,90/0,95 pontosan (`>=` és `--handbook-strict`), rövid szövegek; kivételek (elfogadott, felmentés típusonként, érvénytelen/elavult/nem felmenthető); a jelentés kötelező mezői; determinizmus; parancssori kilépési kódok, és hogy a küszöbök nem módosíthatók; valós TE-1 exporttal: a beültetett, valódi exportált példával azonos első forduló megtalálása fájl:sor hellyel, a tesztfixture-ök egyezés nélkül, a `data/` érintetlen.

**Teljes regresszió (a munka végén):** `tests.test_multiturn_dedupe` + `test_multiturn_validate` + `test_te1_dataset_export` + `test_te2_chat_text`: **159 teszt OK** (`-W error::ResourceWarning` mellett is); `tests.test_v1_7_4_dataset_foundation`: STABIL.

**Mutációs vizsgálat** (a tesztek erejére): 46 szándékos hibamutáns (küszöbök, döntési szabályok, deklarált változat, szerep-őrzés, csoportosítás, kivételek, bemenet-védelem, előszűrés-korlát elrontása, autojunk, haladási állapot, `training_ready`…). Első futás: 41 elbukott, 5 túlélt; a túlélők miatt új tesztek készültek, az újrafuttatás után **46/46 elbukik** (`mutation_results.txt`). Két mutáns szándékosan **nem pontos** előszűrő-korlát volt (túl kicsi hossz-korlát, túl szűk hossz-ablak): ezeket az előszűrt és a teljes összehasonlítást összevető tesztek bukatják el.

**Előszűrés vs. teljes összehasonlítás (garantált, nem közelítő):** a hossz- és karakter-multiset felső korlát bizonyítottan pontos (`M ≤ min(|a|,|b|)`, `M ≤` a multisetek metszete); a szűrő csak a küszöb alatti párokat hagyja ki. Mérés (90 szintetikus beszélgetés, 250 export-példa): a két mód **azonos** találat-halmazt ad (235 = 235, azonos JSON: találatok, csoportok, rekordállapotok); az előszűrt futás 1,39 mp, a teljes összehasonlítás 754,4 mp (~540-szeres különbség); a szűrők az összehasonlításra kijelölt beszélgetés-párok 99,96%-át (a teljes méretű futásban), a minta-párok 99,99%-át szűrték ki a drága összevetés előtt. A tesztek szintetikus korpuszokon (a 0,90/0,95 határra tervezett párokkal) mindkét módban azonos eredményt mutatnak.

**Futásidő (szintetikus terhelés, a valódi 4494 példás exporttal szemben; egy folyamat, ez a gép):** 1050 beszélgetés, 5207 minta: **60,1 mp** (beszélgetés-szint 12,8 mp, minta-szint 29,4 mp, válasz-egyezés 17,5 mp). Összehasonlított párok: 550 705 beszélgetés-pár → 243 teljes összevetés; 9,43 M minta-pár → 383; 5,31 M válasz-pár → 162. Beültetett esetek: pontos másolat 10/10, normalizálás utáni másolat 10/10, közeli változat (3–5% szócsere) 10/10, exportált példával azonos első forduló 10/10, átfogalmazás-szerű változat (35% szócsere) **8/10** (a heurisztika nem teljes). Kézi futás a 12 bemutató-beszélgetésen 0,6 mp. A szintetikus terhelés **nem** valódi beszélgetés; a valódi adat statisztikája más lehet.

## 5. Milyen bemeneten történt az ellenőrzés

* Mesterséges tesztadat: 5 fixture + átalakított változataik (pontos másolat, névcsere, átfogalmazás, lánc, szerepcsere, sorrendcsere, köszönés, azonos kérdés), ideiglenes mappákban, MT-1-validálva fixture módban.
* A **valódi TE-1 export** (4494 példa, manifest és ellenőrzőösszegek ellenőrizve) mint referencia: az 5 fixture ellen 0 találat; egy beültetett, valódi exportált példa első fordulóként megtalálva.
* Szintetikus terhelés (~1050 beszélgetés) csak a futásidő és az előszűrés mérésére, a belső API-n át (nem MT-1-validált, nem került fájlba a datasetben).
* **Valódi többfordulós adaton nem futott**, mert nincs.

## 6. Ami bizonytalan vagy nyitott

* A kézikönyvi küszöbök megfeleltetése (3. szakasz táblázata) **jóváhagyásra vár**, különösen `>=` vs `>`, a rövid minta kapuja és a paraphrase-heurisztika.
* A paraphrase-küszöb (0,35) ideiglenes, nagyon kis mintán kalibrált; az átfogalmazás nagyrészt észrevétlen marad (8/10 a szintetikus 35% szócserénél). Valódi adaton újrakalibrálandó, és a heurisztika csak `review`-t ad.
* A pozíció-őrző arány beszúrt/törölt váltásnál alacsony lehet; az üzenet-átfedés részben pótolja (`messages_reordered`, eltolt helyre is).
* A `meta.depends` annotáció helyességét az eszköz nem ellenőrzi; a releváns előzmény az annotáción és az előző váltáson alapul.
* Nem ítéli meg, hogy két minta tartalmilag eltérő képességet tanít-e: ezt a `review` és a dokumentált kivétel dönti el (kézi, nem független).
* Az eszköz csak a beszélgetés-adatot és az 1 kanonikus TE-1 exportot veti össze; az 1–6. csomag egyfordulós sorainak egymás közti duplikációját a meglévő eszközök kezelik.
* Egy pontos másolat beszélgetés- és minta-szinten is jelentkezik (több találat ugyanarra a párra); ez a jelentés olvashatóságát rontja, a döntést nem.

## 7. Pontosan mire vonatkozik a STABIL minősítés

**STABIL** = a `tools/multiturn_dedupe.py` **működése** a fenti, mesterséges és szintetikus bemeneteken és a valódi TE-1 exporttal szemben: a tesztek (59 új; az összes új tesztkészlet 159; a regresszió STABIL) sikeresek, a mutációs vizsgálat 46/46, az előszűrés a teljes összehasonlítással azonos eredményt ad, a bemenet-védelmek és a kimenet visszakövethetősége működnek. **Nem vonatkozik** valódi többfordulós adat minőségére, tartalmi helyességre, természetességre, a kézikönyvi megfeleltetések jóváhagyására, az 1000 beszélgetés bármelyikének elfogadására vagy training-ready állapotra. A `clear_of_duplicate_findings` sem elfogadás.

## 8. Az első 100 valódi beszélgetés következő lépése

Az MT-6 kapu feltételei (MT-0 formátum, MT-1 validátor, MT-3 duplikáció) **technikailag teljesültek**; a generálás **nem indult**, kifejezett jóváhagyás kell. Konkrét következő lépés:

1. **Jóváhagyás** a 3. szakasz megfeleltetéseire (`>=`/`>`, rövid minta, paraphrase-heurisztika, névsemlegesítés, kivétel-mechanizmus), mert ezek az első batch kapuját határozzák meg.
2. **Az első 50 beszélgetés** (`claude_multiturn_0001_0050`) elkészítése a terv 7. szakasza szerinti összetétellel (család-kvóták, hossz, téma, 3 tervezett változat-pár) — csak jóváhagyás után.
3. Kapu-lánc a batch után: MT-1 `--mode dataset` (0 hiba) → MT-3 (a 4494 exporttal és az előző batchekkel; nincs blokkoló találat vagy dokumentált kivétel) → **teljes kézi átolvasás** (kérdés, válasz és előzmény együtt; a `depends` ellenőrzése) → jelentés a beszélgetés-, üzenet- és mintaszámmal külön → jóváhagyás a második 50 előtt.
4. A 100 után: felülvizsgálat és jóváhagyás; addig nincs `training-ready`.

## 9. A tanítás előtt még hiányzó feladatok

* **MT-2** — csoport-tudatos, determinisztikus 800/100/100 felosztás (az MT-3 számított csoportjaira építve, a jelentés ellenőrzőösszegéhez kötve).
* **MT-4** — renderelés (R1/R3/R2) és exportálás kizárási szűrővel; a képzett minták száma; a csoport egy részbe kerül.
* **MT-5** — többfordulós tanító betöltő (csak betöltés és száraz futás), mintánkénti kódolás, veszteség-maszk; a v0.7 tanító érintetlen.
* **TE-3** — az 1–6. csomag egyfordulós adatának globális, csoport-/közeli-változat-tudatos train/validation/test felosztása (a TE-2 export nem oszt fel).
* **Nyitott tartalmi ellenőrzések:** a 6. csomag korlátozott lezárása (6 kizárt sor: `0220`, `0829`, `0849`, `0864` jogi átnézésre, `0602`, `0898` forrásra vár); 10 nem forrásolt E-sor; 7 hedge-elt, forrás nélküli szám; 39 előtag nélküli kontraszt-sor újracímkézése; 14 ismétlődő `kind` címke; **független emberi/szakértői átolvasás** az egész korpuszra; az 1–5. csomag kibővített céljának tartalmi lefedettségi auditja; a 7–10. csomag (és az 1–5. csomag hiányzó adatának) generálása külön jóváhagyással.
* **D-1** — a futásidejű előzmény-mélység (1 váltás) és az R3 „arany összefoglaló” döntése (webapp/backend módosítás csak külön jóváhagyással).
* A tanítás megindításának kifejezett engedélye.
