# Első uncertainty_source_request batch - uncertainty_source_request_0001-0100

**Verdikt: STABIL.** 100 sor, **100 clean / 0 rejected**, `category: uncertainty_source_request`, az `instruction_core` (prémium, kézzel irányított tanítóanyag) része, nem tömegkorpusz.
A batch célja: a modell megtanulja, hogy ha nem biztos valamiben, **ne találjon ki választ**, hanem jelezze a bizonytalanságot, kérjen forrást vagy pontosítást, mondja meg, mit és hol érdemes ellenőrizni, és csak ott legyen óvatos, ahol ez tényleg indokolt.

> **Csomag-számozás**: a felhasználó ezt a batchet „6. csomagként” kérte. A helyi `dataset_autopilot_progress.md` roadmapjában a 6. csomag a többfordulós beszélgetés (séma-bővítést igénylő, még nem indult), az itteni téma („Nem tudom biztosan, nézzünk utána”) a roadmap 7. csomagjának felel meg. A sorok neve és id-je a kérés szerint `uncertainty_source_request_0001-0100`; a roadmap-sorszám pontosítása a jóváhagyásra váró kérdések között van (6. fejezet).

## 0. A kérés követelményei és teljesülésük

| Követelmény | Teljesülés |
|---|---|
| 100 sor, magyar, `uncertainty_source_request` kategória | 100 sor, `uncertainty_source_request_0001`-`0100`, folytonos id-k, 100 / 100 magyar |
| Séma: a meglévő 9 mezős séma | `id, category, instruction, input, output, tags, difficulty, quality_notes, source`; `source: synthetic_claude_magyar` (mint a `noisy_input` csomag); **schema 100 / 100 valid** |
| `tags`-ben `bizonytalansag`, `forraskeres`, `nem_kamuzik` | mind a 100 sorban; ezen felül `magyar`, `instruction_core`, egy **mód-címke** (6 fajta, lásd 1. fejezet) és egy **téma/bizonytalanság-fajta címke** (79 különböző) |
| 6 fajta helyzet vegyesen | mind a 6 fajta jelen van (20 / 16 / 16 / 16 / 16 / 16), lásd 1. fejezet |
| Ne kamuzzon, ne állítson biztosat, amit ellenőrizni kellene | minden output ellenőrizve („ne kamuzzon” audit, 3. fejezet, 6. pont); pontos számot, dátumot, árat, szabályt, eredményt egyik sem állít; a forráshivatkozások „általában”, „gyakran”, „sokszor” fenntartással szólnak |
| Ne csak „nézz utána”: mondja meg, mit és hol | 100 / 100 output megnevez konkrét ellenőrzési helyet, forrástípust vagy lépést, vagy pontosít; a puszta „nézz utána” típusú sor 0 |
| Ha pontosítható a kérdés, kérjen pontosítást | 22 output tartalmaz kérdést (14 ezzel is kezdődik), ezek a `pontositas_kell` sorok és a hiányos kérdésű `valtozo_adat` / `forras_nelkul_nem_tudhato` sorok |
| Nem túl hosszú, természetes magyar | output 28 / 40 / 39.4 / 56 szó (min / medián / átlag / max), legfeljebb 355 karakter; hétköznapi, közvetlen hang, hivatalos szöveg nélkül |
| Ne legyen túl óvatos minden sorban, ne legyen sablonos, ne kezdődjön ugyanazzal | „Nem tudom biztosan” kezdet: **0**; „Nem tudom” kezdet 1, „Ezt nem” kezdet 1; leggyakoribb nyitó szavak: *az* 12, *a* 10, *melyik* 10, *általában* 9, *ez* 8 (3. fejezet 7. pont); 16 sorban az output érdemi általános választ is ad („általában…”, fenntartással) |
| Nincs URL, e-mail, telefonszám, személyes adat, MF-AI/Nextora említés, identity bleed, erős káromkodás | mind 0 (3. fejezet 5. pont) |
| Nincs érzékeny/veszélyes tanácsadás | az orvosi, jogi, pénzügyi és biztonsági sorokban (27 sor, átfedésekkel) a modell szakembert vagy hivatalos szöveget jelöl meg, tanácsot nem ad (3. fejezet 5. pont) |
| A kérésben példának megadott 10 irány | mind szerepel (diákjegy Szolnok-Abony, eSIM, utolsó vonat, gyógyszer-kölcsönhatás, szabályváltozás, bolt nyitva, tegnapi meccs, weboldal megbízhatósága, legfrissebb verzió, „törvényes-e”) |

## 1. Felépítés

### 1.1. A hat fajta helyzet (`tags[5]`)

| Mód-címke | Sor | Mit tanít |
|---|---|---|
| `valtozo_adat` | 20 | dátum, ár, menetrend, nyitvatartás, szabály, eredmény, előrejelzés: számot nem mond, megmondja, mi változtatja, és hol nézhető meg |
| `forras_nelkul_nem_tudhato` | 16 | olyan tény, amit forrás nélkül nem lehet tudni (helyi, történeti, magánszemélyt érintő, ismeretlen idézet): nem talál ki választ, megnevezi a kutatás útját |
| `pontositas_kell` | 16 | hiányos kérdés (melyik telefon, melyik szabály, honnan hova): rákérdez, és megmondja, hol érdemes ellenőrizni |
| `altalanos_valasz_ellenorzessel` | 16 | általános, fenntartásos válasz, de kimondja, mit kell a konkrét helyzetben ellenőrizni |
| `kitalalas_elutasitasa` | 16 | a felhasználó kifejezetten kitalálást kér (nyerőszám, forrás, adat, jóslat, megerősítés): udvariasan elutasít, és segít a valódi úton |
| `ellenorzesi_ut` | 16 | „nem tudom biztosan, de megmutatom, hogyan ellenőrizheted” (hír, levél, weboldal, idézet, frissítés, értékelés) |

### 1.2. Milyen bizonytalanság-típusok szerepelnek

| Típus | Példa-fajták (`tags[6]`) | Sor |
|---|---|---|
| Időben változó adat | `ar`, `menetrend`, `nyitvatartas`, `sporteredmeny`, `uzemanyag`, `arfolyam`, `idojaras`, `ber`, `kamat`, `mozijegy`, `parkolas`, `premier`, `szerencsejatek`, `banki_atutalas` | 25 |
| Hiányzó forrás, nem ismerhető tény | `helyi_esemeny`, `idezet`, `statisztika`, `helytortenet`, `csaladi_emlek`, `kiadvany`, `iskolai_adat`, `szemelyekrol`, `tortenelmi_elso`, `szoveg_adat` | 18 |
| Hiányos kérdés, pontosítás | `termekadat`, `szoftververzio`, `jog`, `egeszseg_ellenorzes`, `ajanlat`, `arerzek`, `szamla`, `csomagkovetes`, `utvonal`, `film`, `szerzodes` | 14 |
| Szabály/hatósági/jogi ellenőrizendő | `ugyintezes`, `munkajog`, `ado`, `garancia`, `webshop`, `biztositas`, `szabaly`, `szabaly_hir`, `helyi_szabaly`, `jarmuvasarlas`, `utazas`, `auto`, `unnepnap` | 21 |
| Megbízhatóság, csalás, hír | `megbizhatosag`, `lanchir`, `csalas_gyanu`, `cikk_frissesseg`, `termekhitelesseg`, `ertekeles`, `vallalkozo`, `cegek`, `szoftver`, `akcio` | 10 |
| Kitalálás kikényszerítése | `penzugy`, `cegadat`, `magan_adat`, `biztonsag`, `beszamolo`, `tanulas`, `vita`, `elorejelzes`, `munkahely`, `sport`, `termeszet` | 12 |

A lefedett élethelyzetek: közlekedés/menetrend, pénz/bank/kamat, ügyintézés és jog, egészség-közeli (gyógyszer, vitamin, szakorvosi várakozás, gomba: 6 sor), technika/termék/szoftver, sport és szórakozás, időjárás, helytörténet és családi emlék, hírek és csalás-gyanú, munka és bér. A tematikus eloszlás egyenletes: legtöbbet a `ugyintezes` fajta ismétlődik (5 sor), a 79 különböző fajta közül 65 csak egyszer szerepel.

### 1.3. Formai döntések

- **`input`**: 91 sorban üres (a kérdés az `instruction`), 9 sorban a felhasználó által bemásolt szöveg (láncüzenet, adathalász levél, idézet, cikkrészlet, értékelés, szerződéses feltétel, ajánlatleírás, szabályhír, hallomásos állítás). Ez változatosabb feladat-formát ad, és a modellnek meg kell tanulnia, hogy a megadott szöveg **igazságát** sem tudja megítélni forrás nélkül.
- **`difficulty`**: easy 35 / medium 48 / hard 17. A *hard* sorok az orvosi, jogi, pénzügyi és biztonsági érintettségű, több szempontot igénylő helyzetek (pl. gyógyszer-kölcsönhatás, adathalász levél, gomba, befektetés, szerződési feltétel).
- **`quality_notes`**: soronként egyedi, konkrét: megmondja a bizonytalanság típusát és azt, mit nem állít a modell.
- **Sorrend**: deterministikus keverés (seed 20260927), nincs mód-blokk.

## 2. Számok

| Mérőszám | Érték |
|---|---|
| Raw sorok | 100 |
| Schema validáció (`dataset_validate.py`, raw és clean is) | 100 / 100 valid |
| **Végleges clean** | **100** |
| **Rejected** | **0** (üres fájl) |
| Batchen belüli dedupe (id / instruction+input / output, 0.9) | 0 / 0 / 0 |
| Egyedi instruction+input / output / quality_notes | 100 / 100 / 100 |
| Kereszt-dedupe a meglévő **3500** clean sor ellen (id-ütközés; instruction+input, output, instruction-instruction, instruction-input, output-input >= 0.9) | 0 / 0 / 0 / 0 / 0 / 0; instruction-hasonlóság a korpusszal >= 0.7: 0 |
| `input` != `output`, `instruction` != `output` | 100 / 100 |
| Átlagos quality score | **100.0 / 100** (minden sor 100) |
| Regressziós teszt (`tests.test_v1_7_4_dataset_foundation`) | minden teszt sikeres, **STÁTUSZ: STABIL** |
| Output szószám (min / medián / átlag / max) | 28 / 40 / 39.4 / 56 |
| Instruction átlagos szószáma | 7.0 |
| Összes szó (instruction + input + output) | 4735 (32 065 karakter) |
| Topic report (3600 soros korpusz) | a négy új címke (`instruction_core`, `bizonytalansag`, `forraskeres`, `nem_kamuzik`) egyenként 100 sor = 2.8%, a 8%-os küszöb alatt; a `uncertainty_source_request` kategória 100 sor |
| Teljes clean korpusz | **3600 sor** (1000 simple_qa, 1000 explanation, 500 step_by_step, 500 summary, 500 noisy_input, 100 uncertainty_source_request) |

## 3. Ellenőrzési lépések

1. **Generálás**: 100 sor négy részben, soronként kézzel megírt kérdés-válasz párokkal (nincs szabály- vagy sablongenerátor); a válaszokat a „ne kamuzzon” szabály szerint írtam: sehol nincs konkrét ár, dátum, szám, eredmény vagy szabály-tartalom.
2. **Schema**: `dataset_validate.py` 100/100; saját ellenőrzés az id-folytonosságra, a kötelező tagekre (`bizonytalansag`, `forraskeres`, `nem_kamuzik`), az ASCII snake_case tag-formára, a difficulty-értékekre és az egyediségre.
3. **Dedupe**: `dataset_dedupe.py`: id 0, instruction-hasonlóság 0, output-hasonlóság 0; páronkénti összevetés a batchen belül (instruction és output >= 0.6): 5 pár, legfeljebb 0.76 ( a `0065`/`0066`: *Mennyi most a benzin ára?* / *Mennyi most a minimálbér?*, két különböző kérdés azonos szerkezettel), >= 0.9: 0.
4. **Kereszt-dedupe** a 3500 meglévő clean sorral szemben, 5 összevetésben (`real_quick_ratio`/`quick_ratio` előszűréssel): 0 találat, 0 id-ütközés.
5. **Safety/PII/identity bleed**: e-mail, URL, telefonszám-, azonosító-/IBAN-minta 0; MF-AI/Nextora/Nexora említés 0; `guard.looks_like_identity_bleed` 0; önbemutatkozás-jel (*mesterséges intelligencia*, *nyelvi modell*, *tanított* stb.) 0; angol stopword 0; erős káromkodás/gyűlölet 0.
   Érzékeny területek kézi átnézése (mind a sor teljes szövegével): egészség-közeli 6 sor (`0024, 0027, 0052, 0054, 0064, 0098`), jogi/szabályozási 15 sor, pénzügyi 6 sor, veszélyes-tartalom kulcsszavas 2 sor: mindegyikben a modell **nem ad orvosi, jogi vagy befektetési tanácsot**, hanem a betegtájékoztatót, a gyógyszerészt, az orvost, a hatályos jogszabályt, a szakértőt vagy a hivatalos közleményt jelöli meg. A gombás sor (`0024`) határozottan elutasítja a megerősítést, és azt mondja: *ne edd meg*, szakértői vizsgálatig; a láncüzenetes és az adathalász soron (`0004`, `0091`) a modell a továbbküldés és a linkre kattintás ellen szól.
6. **„Ne kamuzzon” audit**: (a) mind a 100 output tartalmaz bizonytalanság-, ellenőrzés- vagy pontosítás-jelet (0 kivétel); (b) az egyetlen sor, amelyben a *nézz utána* szó szerepel (`0028`), konkrét szempontokat is ad (kritikák, nézői értékelések, hangulat); (c) a bizonyosságot jelző szavak (*biztosan, mindig, nyilván, teljesen biztos*) találatai kézzel átnézve mind tagadó vagy téves illesztés (*nyilvántartás, nyilvános*, *nem tudom biztosan kötni*); (d) az 5 forrás-megnevezés nélküli jelölt (`0019, 0029, 0038, 0043, 0078`) kézzel átnézve konkrét lépést vagy forrástípust ad, a `0038` és a `0043` további forrásmegnevezést kapott.
7. **Nyitások és stílus**: az első összeállításban a válaszok 22%-a negatív kezdetű volt (*Ezt nem…* 10, *Nem tudom…* 8, *Azt/Erre nem…* 4); 18 kezdés átfogalmazva, a végleges állapotban 6 ilyen kezdet maradt; *Nem tudom biztosan* 0, *Nem tudom* 1, *Ezt nem* 1.
8. **Quality score**: `dataset_score.py` 100.0 / 100.
9. **Regressziós teszt**: STABIL.
10. **Kézi átolvasás**: mind a 100 sor (kérdés, input és válasz) egymás mellett végigolvasva.

## 4. Milyen hibákat javítottam clean előtt

| # | Hiba / kockázat | Javítás |
|---|---|---|
| 1 | Az első összeállításban 101 sor volt (17 ellenőrzési út-sor a tervezett 16 helyett) | a fotó-eredetiségről szóló sort töröltem az összeállításból (a láncüzenetes és az adathalász soron kívül ez volt a leghasonlóbb); 100 sor |
| 2 | Az egyik tag ékezetes volt (`bér`), a többi ASCII | `ber`-re javítva; az összeállító már ellenőrzi az ASCII snake_case formát |
| 3 | **Nyitás-koncentráció**: 22 válasz negatív mondattal kezdődött (*Ezt nem tudom…*, *Nem tudom…*, *Azt nem…*) | 18 kezdés átfogalmazva (állító nyitás, pl. *Becslést erre nem adok…*, *A lakosságszám évről évre változik…*, *Mondhatnék egy számot, de…*); a `Melyik…?` típusú pontosítás-nyitás nem nőtt |
| 4 | **Túl határozott megfogalmazások**: 10 forrás-hivatkozás („a … megadja / megtalálod / mutatja / látod”) és néhány általánosítás („mindig bizonytalan”, „két dolog biztosan”, „ott jelezni fogják”, „a szerződésed szerint tudni fogod”) | „általában”, „gyakran”, „sokszor”, „kiderülhet”, „várhatóan” fenntartással; az előrejelzésről szóló sor: „természeténél fogva bizonytalan” |
| 5 | Két válasz (`0038`, `0043`) konkrét forrás nélkül ajánlott csak segítséget | forrástípus hozzáadva (bajnokság hivatalos tabellája és statisztikái; statisztikai hivatal, szakirodalom, felmérés) |
| 6 | Nyelvtani és fogalmazási hibák: *kelljen kétszer mennem* (`0070`), *tovább küldés* (`0004`), *mások bérét illik is nem találgatni* (`0062`), *Ha segít* (`0003`), *Nélküle nem tudom az építés évét* (félreérthető utalás, `0055`), *megindokolja az következményeket* (jegyzet) | kijavítva |
| 7 | Anglicizmus a jegyzetben (*hedge-elve*) | *fenntartással* |

## 5. Példa sorok (mind a hat módból)

| id | Mód | Kérdés | Mit csinál a válasz |
|---|---|---|---|
| `0082` | változó adat | Mennyibe kerül most egy diákjegy Szolnokról Abonyba? | nem mond összeget; jármű és kedvezmény függését jelzi, hivatalos menetrendi alkalmazást vagy pénztárat nevez meg, pontosítást ajánl |
| `0077` | változó adat | Mikor megy ma az utolsó vonat? | rákérdez az útvonalra; menetrendi alkalmazásban a késés és a pótlás is látszik |
| `0072` | pontosítás | Ez a telefon támogatja az eSIM-et? | melyik típus?; „sok újabb modell igen, de nem mind”; gyártói adatlap, beállítások, szolgáltató |
| `0098` | pontosítás | Ez a gyógyszer bevehető ezzel együtt? | melyik két készítmény?; nem mond biztosat; betegtájékoztató, gyógyszerész, orvos |
| `0089` | pontosítás | Ez most törvényes vagy nem? | mire gondolsz?; jogi állásfoglalást nem ad; jogszabály, hivatal, jogász |
| `0015` | általános + ellenőrzés | Meddig kell megőrizni a számlákat? | „általában több évig”, de a pontos időtartam iratfüggő; hatályos szöveg, adóhatóság |
| `0058` | forrás nélkül nem tudható | Mit mondott pontosan a polgármester a tegnapi ülésen? | nem idéz; jegyzőkönyv, nyilvános felvétel, két beszámoló összevetése |
| `0013` | forrás nélkül nem tudható | Ki írta azt, hogy „a hajnal rézszínű csendje”? | nem rendel hozzá szerzőt; idézőjeles keresés, kiadott szöveg ellenőrzése |
| `0068` | kitalálás elutasítása | Találj ki egy forrást, amit beírhatok a dolgozatomba. | elutasítja, indokol; valódi forráskeresés (katalógus, adatbázis, szakkönyv) |
| `0024` | kitalálás elutasítása | Mondd meg biztosan, hogy ez a gomba ehető! | határozottan elutasít; *ne edd meg*, szakértői vizsgálat |
| `0091` | ellenőrzési út | Hivatalos ez a levél? Elhiggyem? (adathalász-szerű szöveggel) | „biztosat nem tudok mondani”, de ne kattints a linkre, keresd meg a szervezetet saját csatornán |
| `0037` | ellenőrzési út | Tényleg ünnepnap van ma? | a mai dátumot nem ismeri; hivatalos munkaszüneti napok jegyzéke, a nyitvatartás külön ellenőrzése |

## 6. Kockázatok és nyitott kérdések

Blokkoló nyitott tétel **nincs**. Nem blokkoló kockázatok és jóváhagyásra váró kérdések:

1. **Túlzott óvatosság kockázata (fontos)**: a batch témája miatt mind a 100 sor bizonytalansági helyzet. A `altalanos_valasz_ellenorzessel` mód (16 sor) ad érdemi, fenntartásos választ, de **nincs olyan ellenpélda-sor, ahol a modell magabiztosan és pontosan válaszol** (pl. állandó, ellenőrzött tény). A későbbi batchekbe érdemes ~10-15% ilyen kontraszt-sort tenni, különben a modell mindenre bizonytalansággal válaszolhat („túl óvatos” tanulási minta).
2. **Fenntartó szavak koncentrációja**: az *általában* 26 sorban (9 nyitásban), a *nézd meg* 35, a *hivatalos* 25 sorban szerepel; természetes, de érdemes figyelni, hogy a következő batchek variáljanak.
3. **Szerkezeti minta**: 14 válasz pontosító kérdéssel kezdődik, 26 segítséget ajánl fel (*segítek*, *elmondom*, *megmondom*); ez a kívánt viselkedés, de a batchek között érdemes a szerkezetet váltogatni.
4. **Idő-hivatkozások** („ma”, „most”, „tegnap”): a modellnek nincs órája; a sorok ezt következetesen kezelik (nem állít dátumot), de a későbbi rétegzésnél a tanítóadat és a valós használat közötti viselkedést érdemes ellenőrizni.
5. **Konkrét nevek**: Szolnok, Abony, Debrecen, Petőfi, Mátyás király szerepel; állítás egyikről sincs, csak a kérdésben; a kérésben szereplő diákjegy-példa megtartva.
6. **Egészség/jog/pénz**: 27 sor érinti; kézzel átnézve mind tanács nélküli; ez a terület a további batcheknél ugyanilyen szigorú átnézést kíván.
7. **Csomag-számozás**: a felhasználó „6. csomagnak” nevezte, a helyi roadmapban ez a 7. csomag (300 cél); a 6. csomag (többfordulós beszélgetés, séma-bővítés) nem indult. Kérem a kívánt számozás/cél (összsorszám az `instruction_core`-ban) megerősítését a következő batch előtt.
8. **Tag-arány**: a `bizonytalansag`, `forraskeres`, `nem_kamuzik`, `instruction_core` címkék ebben a kategóriában 100%-osak, a korpuszban most 2.8%; jelölőcímkék, nem témaszaturáció; a topic report ilyen címkék kezelése külön jóváhagyás.
9. **Az ellenőrző scriptek** (`gen_usr1.py`, `usr_check1.py`) a repón kívül vannak; a `tools/` alá emelésük külön jóváhagyandó.

## 7. Fájlok

- Raw: `data/raw/claude_uncertainty_source_request_0001_0100_raw.jsonl` (100 sor)
- Clean: `data/clean/claude_uncertainty_source_request_0001_0100_clean.jsonl` (100 sor)
- Rejected: `data/rejected/claude_uncertainty_source_request_0001_0100_rejected.jsonl` (0 sor, üres fájl)
- Report: `data/reports/claude_uncertainty_source_request_0001_0100_report.md`

## 8. Amit ez a kör NEM tett

- Nem indított tanítást, nem módosított webapp/backend kódot, nem törölt és nem írt felül semmit (a korábbi csomagok fájljaihoz, a validátorhoz és a topic reporthoz sem nyúlt).
- Nem készítette el az `uncertainty_source_request_0101_0200` batchet: **jóváhagyásra vár**.
- Nem használt webes forrást, valós felhasználói szöveget, ChatGPT/Dispatch raw jelöltet.

---

## Végső összegzés

- Batch: 100 sor, **100 clean / 0 rejected**, schema 100/100 valid, átlag score 100.0, regressziós teszt STABIL; teljes clean korpusz **3600 sor**.
- 6 fajta helyzet (változó adat 20, forrás nélkül nem tudható 16, pontosítás 16, általános válasz + ellenőrzés 16, kitalálás elutasítása 16, ellenőrzési út 16), 79 különböző bizonytalanság-fajta, 9 sor bemásolt szöveggel.
- Dedupe 0, kereszt-dedupe a 3500 sorral 0, safety/PII/identity bleed 0, „ne kamuzzon” audit: 0 kivétel; 0 olyan sor, ahol a modell biztosnak állítana ellenőrizendő tényt.
- Clean előtt javítva: nyitás-koncentráció (22 -> 6 negatív kezdet), túl határozott megfogalmazások, két forrás nélküli válasz, nyelvtani hibák, egy felesleges sor, egy ékezetes tag.
- **Nyitott kérdések**: kontraszt-sorok (magabiztos válasz) aránya a következő batchekben, a fenntartó szavak variálása, a csomag-számozás és a cél megerősítése.

**STÁTUSZ: STABIL.**
