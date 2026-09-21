# Harmadik uncertainty_source_request batch - uncertainty_source_request_0201-0300

**Verdikt: STABIL.** 100 sor, **100 clean / 0 rejected**, `category: uncertainty_source_request`, a **6. csomag (Bizonytalanság / forráskérés)** harmadik batchje az új, bővített 17 000 soros `instruction_core`-ban. A csomag célmérete **1000 sor**, ezzel **300 / 1000** kész.
A batch célja: a modell ne találjon ki választ, ha nem biztos (jelezze a bizonytalanságot, kérjen forrást vagy pontosítást, mondja meg, mit és hol lehet ellenőrizni), **de ne is legyen feleslegesen félős**. Új ebben a batchben: (1) **14 kontraszt-sor**, ebből 13 összetettebb (többmondatos ok-okozati magyarázat, lépéses tanács, vagy bemásolt adatot magabiztosan feldolgozó válasz), (2) új tématerületek (oktatás, iskola/kollégium, háztartás, közösségi média, utazás, időjárás, sport, telefon/app, ügyintézés, vásárlás), (3) sokkal kevesebb ár/jegy/nyitvatartás/bankkártya téma.

> **Számozás**: 6. csomag = Bizonytalanság / forráskérés, cél 1000 sor; a régi 4900 soros roadmap számozása nem irányadó. Állás a batch után: **300 / 1000**.

## 0. A kérés követelményei és teljesülésük

| Követelmény | Teljesülés |
|---|---|
| 100 sor, magyar, `uncertainty_source_request`, id `0201`-`0300` | 100 sor, folytonos id-k, `source: synthetic_claude_magyar`, a meglévő 9 mezős séma |
| 100/100 valid, 100/100 clean, 0 rejected | **100 / 100 valid, 100 clean, 0 rejected** |
| 0 batchen belüli duplikátum, 0 kereszt-dedupe találat | 0 / 0 (2. fejezet); az első futás **2 azonos instruction-t** talált a 2. batchhel, ezeket clean előtt javítottam (4. fejezet, 1. pont) |
| 0 PII/URL/e-mail/telefonszám, 0 MF-AI/Nextora, 0 identity bleed, 0 erős káromkodás | mind 0 (3. fejezet 5. pont) |
| Regressziós teszt STABIL | minden teszt sikeres, **STÁTUSZ: STABIL** |
| Maradjon 10-15% kontraszt-sor | **14 sor = 14%** (`kontraszt_magabiztos`) |
| A kontraszt-sorok legyenek összetettebbek is | **13 / 14 összetettebb** (11 sor >= 40 szó többmondatos magyarázat vagy lépéssor, 2 sor bemásolt adatot értékel/számol); 1 rövid fogalommagyarázat (*hotspot*) |
| Életszerű, magabiztosan megválaszolható hétköznapi kérdések a kontraszt-sorok között | iskolatáska este, vásárlási lista, bőrönd bepakolása, futás hidegben, kollégiumi konyha, napirend értékelése, kosár végösszege, jelszó-ismétlés, értesítések tanuláskor stb. (1.3) |
| A kontraszt-soroknál ne bizonytalankodjon feleslegesen | a 14 sorban 0 fenntartó/bizonytalanságot jelző kifejezés (az egyetlen kulcsszó-találat az *összefüggően* szó, téves illesztés) |
| A többi sor bizonytalanság / forráskérés (változó adat, friss info, forrás nélkül nem tudható, ár/jegy/nyitvatartás/termékadat/menetrend, egészség/jog/pénz, pontosítás, ellenőrzési út, kitalálás elutasítása) | 86 sor, 6 mód (15 / 14 / 14 / 14 / 14 / 15) |
| Kevesebb ismétlés ár/jegy/nyitvatartás/bankkártya témából | **0** bankkártya, **0** nyitvatartás, **0** jegyár sor; ár/vásárlás jellegű összesen 6 sor (cipőkészlet, akció, poggyász-súly, kosár-végösszeg, kamatmentes részlet, webshop-szabályzat) |
| Új területek: oktatás, háztartás, közösségi média, utazás, időjárás, sport, ügyintézés, telefon/app, vásárlás, iskola/kollégium | mind szerepel (1.2) |
| Ne legyen sok „általában” és „nézd meg”; ne kezdődjön sok válasz ugyanúgy | *általában* **1** sor (26 -> 5 -> 1), *nézd meg* **3** sor (35 -> 5 -> 3); kétszavas nyitás legfeljebb 2 sornál azonos; *Ezt nem* kezdet 1, *Nem tudom biztosan* 0 |
| Természetes magyar, ne kamuzzon, ne legyen félős | mind a 100 sor kézzel végigolvasva, két javítási kör (4. fejezet) |
| Egészség/jog/pénz: külön óvatosság, diagnózis/jogi állásfoglalás/pénzügyi tanács nélkül | 16 `hard` sor, kézzel átnézve, mind tanács nélküli (3. fejezet 5. pont) |

## 1. Felépítés

### 1.1. A hét mód (`tags[5]`)

| Mód-címke | Sor | Mit tanít |
|---|---|---|
| `valtozo_adat` | 15 | éves/napi változó dátum és adat (tanév, ponthatár, frissítés, akció, vízum, poggyászszabály, élő üzemállapot): számot nem mond, megmondja, mitől változik és hol nézhető meg |
| `forras_nelkul_nem_tudhato` | 14 | hozzáférés nélküli, magánjellegű vagy jövőbeli tény (tanár véleménye, követők száma, dolgozat jegye, menza-étlap): nem talál ki választ |
| `pontositas_kell` | 14 | hiányos kérdés (*Miért nem működik?*, *Mit vigyek magammal?*, *Elég lesz erre a pénz?*): rákérdez, és megmondja, mitől függ a válasz |
| `altalanos_valasz_ellenorzessel` | 14 | érdemi általános válasz (szülői felügyelet, telefonváltás, repülő lekésése, mosógép, szédülés), de kimondja, mit kell szakemberrel vagy típusspecifikus forrással tisztázni |
| `kitalalas_elutasitasa` | 14 | kitalálást kér a felhasználó (kitalált interjú, meccs-végeredmény, hamis igazolás, diagnózis, adó egy számban): udvariasan elutasít, és valódi utat kínál |
| `ellenorzesi_ut` | 15 | konkrét ellenőrzési lépések (oklevél, hamis profil, alkalmazás, utazási iroda, csoportchat-hír, adathalász e-mail, háztartási tipp) |
| **`kontraszt_magabiztos`** | **14** | stabil, hétköznapi tudás vagy a megadott adatból biztosan levezethető válasz: magabiztos, nem túl hosszú, nincs fenntartás |

### 1.2. Bizonytalansági típusok és témák eloszlása

A `tags[6]` mind a 100 sorban **egyedi** (100 különböző téma-címke). Tematikus csoportosítás (a kontraszt-sorokat is a témájuk szerint számolva):

| Téma-csoport | Sor | Példák (`tags[6]`) |
|---|---|---|
| Oktatás, iskola, kollégium | 35 | `tanev_kezdes`, `felveteli_ponthatar`, `kollegiumi_ferohely`, `dolgozat_elso_feladat`, `menza_etlap`, `tanulmanyi_osztondij`, `kollegiumi_jelentkezes`, `kollegium_hamis_igazolas`, `pihenes_tanulas`, `iskolataska_este` |
| Telefon, app, közösségi média | 19 | `telefon_frissites`, `adatvedelmi_menupont`, `szuloi_felugyelet`, `uj_telefon_adatok`, `hamis_profil`, `zaklatas_kozossegi`, `jelszo_ujrahasznositas`, `hotspot_fogalma` |
| Időjárás, sport | 15 | `tabella_allas`, `uv_index`, `bajnoki_szezon_rajt`, `futott_kilometer`, `fogadas_vegeredmeny`, `edzesterv_megbizhatosag`, `futas_hidegben`, `idojaras_elorejelzes_valasztas` |
| Ügyintézés, jog, pénz, egészség | 12 | `eleg_a_penz`, `kell_engedely`, `kamatmentes_reszlet`, `szedules_allaskor`, `diakmunka`, `ado_egy_szam`, `torokfajas_diagnozis`, `meddig_ervenyes` |
| Háztartás, vásárlás | 11 | `lakcimkartya_csere`, `cipo_szinkeszlet`, `nagy_akcio_idopont`, `mosogep_tisztitas`, `maradek_etel`, `fa_padlo_apolasa`, `haztartasi_tipp_ecet`, `kosar_vegosszeg` |
| Utazás | 8 | `vizum_torokorszag`, `kezipoggyasz_suly`, `lekestem_a_repulot`, `utazasi_iroda`, `beutazasi_szabaly_frissesseg`, `borond_pakolas` |

A 2. batchhez képest eltűnt a jegy-, nyitvatartás- és bankkártya-téma, a közlekedés/menetrend helyett az utazás és az iskolai/kollégiumi ügyek kerültek előtérbe.

### 1.3. A kontraszt-sorok (14 sor, 14%)

| id | Kérdés | Típus |
|---|---|---|
| `0232` | Miért nem jó, ha ugyanazt a jelszót használom mindenhol? | összetettebb: ok-okozat + megoldás |
| `0286` | Mit érdemes csinálni, ha este elfelejtem bepakolni az iskolatáskámat? | összetettebb: életszerű helyzet, lépések |
| `0246` | Miért jobb listát írni vásárlás előtt? | összetettebb: három indok + trükk |
| `0224` | Miért kell pihenni tanulás közben? | összetettebb: magyarázat + példa |
| `0229` | Miért nem jó ötlet mindent az utolsó pillanatra hagyni? | összetettebb: következmények + megoldás |
| `0231` | Hogyan álljak neki, ha egy tananyag túl nehéznek tűnik? | összetettebb: többlépéses tanács |
| `0209` | Hogyan pakoljak be egy bőröndöt, hogy ne gyűrődjön össze minden? | összetettebb: utazási praktika |
| `0275` | Miért jó, ha tanuláskor kikapcsolom az értesítéseket a telefonomon? | összetettebb: ok + beállítási tipp |
| `0288` | Miért fontos, hogy a kollégiumi közös konyha tiszta legyen? | összetettebb: közösségi helyzet |
| `0208` | Miért jó, ha nem osztok meg mindent magamról a közösségi oldalakon? | összetettebb: ok-okozat + próbakérdés |
| `0251` | Mit vegyek fel futáshoz, ha hideg van? | összetettebb: konkrét tanács indoklással |
| `0217` | Szerinted jó ez a napirend? (bemásolt napirend) | összetettebb: magabiztos értékelés + építő javaslat |
| `0211` | Mennyi lesz a végösszeg? (bemásolt kosár) | összetettebb: a megadott számokból biztosan kiszámolható (3 780 Ft) |
| `0201` | Mi az a hotspot a telefonon? | rövid fogalommagyarázat |

Szabályok: (a) csak stabil, közismert tény, józan gyakorlati tanács vagy a megadott adatból levezethető válasz; (b) hétköznapi, életszerű helyzetek (iskola, vásárlás, utazás, kollégium, telefon), nem csak definíciók; (c) 0 fenntartás (*általában*, *függ*, *nem tudom*, *ellenőrizd*, forráskérés): a modell itt tudja a választ; (d) 28-55 szó (átlag 43.6), természetes hang; (e) egészségügyi, jogi, pénzügyi tanácsot a kontraszt-sorok nem adnak; a `0251` futás-tanács ruházati kérdés, a `0217` napirend-értékelés nem orvosi. A kontraszt-sorok a kérés szerint megkapták a `bizonytalansag`, `forraskeres`, `nem_kamuzik` címkét is; a megkülönböztetés a `kontraszt_magabiztos` mód-címkével történik (lásd 6. fejezet, 2. pont).

### 1.4. Formai döntések

- **`input`**: 94 sorban üres, **6 sorban** a felhasználó által bemásolt szöveg (napirend, kosár, csoportchat-hír, telefontöltés-mítosz, adathalász-gyanús iskolai e-mail, ecetes mosási tipp). Két kontraszt-sor tartalmaz bemásolt adatot (napirend, kosár), ott a modell magabiztosan válaszol; a másik négy inputos sor `ellenorzesi_ut` mód: a bemásolt szöveg igazságát nem ítéli meg, hanem ellenőrzési utat ad.
- **`difficulty`**: easy 49 / medium 35 / hard 16. A *hard* a jogi, pénzügyi, egészségügyi, biztonsági érintettségű sorok, mind a nem-kontraszt sorok között; a kontraszt-sorok mind *easy*.
- **`quality_notes`**: soronként egyedi, megmondja, mit nem állít a modell (kontraszt-sornál miért nem kell bizonytalankodnia).
- **Sorrend**: deterministikus keverés (seed 20260929), a kontraszt-sorok szétszórva.

## 2. Számok

| Mérőszám | Érték |
|---|---|
| Raw sorok | 100 |
| Schema validáció (`dataset_validate.py`) | 100 / 100 valid |
| **Végleges clean** | **100** (100%) |
| **Rejected** | **0** (0%, üres fájl) |
| Batchen belüli dedupe (id / instruction / output, 0.9) | 0 / 0 / 0 |
| Egyedi instruction+input / output / quality_notes | 100 / 100 / 100 |
| Kereszt-dedupe a meglévő **3700** clean sor ellen (id-ütközés; instruction+input, output, instruction-instruction, instruction-input, output-input >= 0.9) | 0 / 0 / 0 / 0 / 0 / 0 (az 1. és a 2. batch sorai is benne vannak) |
| Instruction-hasonlóság a korpusszal >= 0.7 (tájékoztató) | csak sablon-hasonlóság (*Hogyan tisztítsam a mosógépet?* ~ *Hogyan tisztítsam a mikrót?*), tartalmi ütközés 0 |
| `input` != `output`, `instruction` != `output` | 100 / 100 |
| Átlagos quality score | **100.0 / 100** (minden sor 100) |
| Regressziós teszt (`tests.test_v1_7_4_dataset_foundation`) | minden teszt sikeres, **STÁTUSZ: STABIL** |
| Output szószám (min / medián / átlag / max) | 26 / 41 / 41.7 / 58 (nem-kontraszt átlag 40.9, kontraszt 43.6); legfeljebb 376 karakter |
| Instruction átlagos szószáma | 6.7 |
| Összes szó (instruction + input + output) | 4878 (33 195 karakter) |
| Topic report (3800 soros korpusz) | a négy címke (`instruction_core`, `bizonytalansag`, `forraskeres`, `nem_kamuzik`) egyenként 300 sor = **7.9%**, épp a 8%-os küszöb alatt (lásd 6. fejezet, 3. pont) |
| Teljes clean korpusz | **3800 sor** (1000 simple_qa, 1000 explanation, 500 step_by_step, 500 summary, 500 noisy_input, 300 uncertainty_source_request) |

## 3. Ellenőrzési lépések

1. **Generálás**: 100 sor négy részben, soronként kézzel megírt kérdés-válasz párokkal (nincs szabály- vagy sablongenerátor); a válaszokat a „ne kamuzzon” szabály szerint írtam, a kontraszt-sorokat szándékosan fenntartás nélkül.
2. **Schema**: `dataset_validate.py` 100/100; saját ellenőrzés az id-folytonosságra, a kötelező tagekre, az ASCII snake_case tag-formára, a difficulty-értékekre, az egyediségre és a mód-eloszlásra.
3. **Dedupe**: `dataset_dedupe.py`: id 0, instruction-hasonlóság 0, output-hasonlóság 0; páronkénti összevetés a batchen belül: 9 pár >= 0.6, legnagyobb 0.76 (`0222`/`0256`: *Mikor kezdődik a jövő tanév?* / *Mikor kezdődik az óra?*, két különböző kérdés), >= 0.9: 0.
4. **Kereszt-dedupe** a 3700 meglévő clean sorral szemben, 5 összevetésben (`real_quick_ratio`/`quick_ratio` előszűréssel): a végleges állapotban 0 találat, 0 id-ütközés.
5. **Safety/PII/identity bleed**: e-mail, URL, telefonszám-, azonosító-/IBAN-minta 0; MF-AI/Nextora/Nexora említés 0; `guard.looks_like_identity_bleed` 0; önbemutatkozás-jel 0; angol stopword 0; erős káromkodás/gyűlölet 0. A számjegyet tartalmazó outputok: kettő a *112* segélyhívó (`0263` szédülés, `0267` zaklatás), egy a kontraszt `0211` (a megadott számokból kiszámolt végösszeg); telefonszám 0.
   Érzékeny területek: a kulcsszavas unió 23 sor; a 16 `hard` sor mind kézzel átnézve. Ezekben a modell **nem ad diagnózist, jogi állásfoglalást vagy pénzügyi tanácsot**: `0271` (torokfájás) kimondja, hogy diagnózist nem tud adni, riasztó tünetnél orvost jelöl; `0263` (szédülés) általános első lépéseket és 112-t ad, okot nem; `0278` (adó) számot nem mond, forrást és szakértőt nevez meg; `0283` (fogadás) tippet nem ad, a kockázatra és segítő szolgálatra utal; `0287` (kamatmentes részlet) általános szempontokat ad, ajánlatot nem minősít; `0254` (diákmunka) és `0273` (hiteles fordítás) általános szempontok, jogi tanács nélkül; `0227` (*Elég lesz erre a pénz?*) rákérdez, pénzügyi tanácsot kifejezetten nem ad; `0299` (maradék étel) napokat nem mond, a hivatalos élelmiszerbiztonsági ajánlásra utal, és kétség esetén a kidobást javasolja.
6. **„Ne kamuzzon” audit**: (a) az automata kulcsszavas ellenőrzés a 86 nem-kontraszt sorból 12-t jelzett fenntartás-jel nélkülinek; kézzel átnézve mindegyikben van tartalmi jel (elutasítás, pontosító kérdés, hozzáférés hiánya, típusfüggés, ellenőrzési lépés), a kulcsszólista volt szűk; (b) a bizonyosságot jelző szavak (*biztosan, mindig, soha, garantál, egyértelműen, nyilván*) találatai kézzel átnézve tagadók (*Biztosat nem mondhatok*, *nem jósolható*), biztonsági figyelmeztetések (*különböző tisztítószereket soha ne keverj*) vagy téves illesztések (*nyilvántartás*, *nyilvános*); (c) egyik nem-kontraszt sor sem állít konkrét árat, dátumot, eredményt, ponthatárt, jogszabály-tartalmat vagy adatvédelmi állapotot; (d) a fenntartással kezelt elterjedt állítások (`0230` éjszakai töltés, `0210` ecetes mosás) nem mondanak igent vagy nemet, hanem forrást és ellenőrzési utat adnak.
7. **Kontraszt-ellenőrzés**: mind a 14 sor stabil közismeret, józan gyakorlati tanács vagy a megadott számokból levezethető válasz; fenntartó kifejezés 0; a `0211` számítás ellenőrizve (2 x 450 + 1 990 + 890 = 3 780).
8. **Nyitások és stílus**: kétszavas nyitás legfeljebb 2 sornál azonos (*Keresd meg*, *Ez az*, *Nézd meg*, *Biztosat nem*, *Mit szeretnél*); leggyakoribb első szó *a* 21 (névelős, természetes), *az* 8, *ez* 7, *ezt* 5, *mert* 3, *mi* 3, *mit* 3; *Ezt nem* 1, *Nem tudom biztosan* 0, *Nem tudom* 0. Fenntartó/sablonos fordulatok a 2. batch végállapotához képest: *általában* 5 -> 1, *nézd meg* 5 -> 3, *érdemes* 6 -> 5, *segítek* 12 -> 3, *ha megírod* 8 -> 3, *függ* 19 -> 15; a *hivatalos* 5 -> 14 (az iskolai/utazási ügyekben természetes, lásd 6. fejezet, 5. pont).
9. **Quality score**: `dataset_score.py` 100.0 / 100.
10. **Regressziós teszt**: STABIL.
11. **Kézi átolvasás**: mind a 100 sor (kérdés, input és válasz) egymás mellett végigolvasva a második javítási kör előtt.

## 4. Milyen hibákat javítottam clean előtt

| # | Hiba / kockázat | Javítás |
|---|---|---|
| 1 | **Kereszt-dedupe: két instruction betűre azonos a 2. batch soraival** (*Mit kellene ellenőriznem ezzel kapcsolatban?*, *Igaz ez? Hogyan tudom ellenőrizni?*); az `instruction+input` egyezés nem jelzett, mert az inputok eltérnek, de az instruction-instruction összevetés 1.0-t adott | átfogalmazva: *Mit érdemes leellenőrizni ebben a hírben?*, *Van ebben igazság, és honnan derül ki?* |
| 2 | Kontraszt-sor sablonhasonlósága: *Mit tegyek, ha nem értem a tananyagot?* 0.85 a `simple_qa_0164` sorhoz (*Mit tegyek, ha nem értem a matekot?*) | *Hogyan álljak neki, ha egy tananyag túl nehéznek tűnik?* |
| 3 | Kontraszt-sor tartalmi átfedése: *Miért fontos bemelegíteni edzés előtt?* 0.78 az `explanation_0441` és 0.77 a `simple_qa_0186` sorhoz | lecserélve egy új, összetettebb sorra: *Mit vegyek fel futáshoz, ha hideg van?* |
| 4 | **Nyitás-koncentráció** az első vázlatban: *Mert…* 7 (mind kontraszt), *Ezt nem…* 4 | 4 *Mert*-nyitás és 3 *Ezt nem*-nyitás átfogalmazva (pl. *Elég egyetlen oldalról kiszivárgó jelszó…*, *A lista megmutatja…*, *Az ételmérgezést nem írom bele…*, *Menesztést nem állíthatok…*); végül *Mert* 3, *Ezt nem* 1 |
| 5 | Ismétlődő fordulatok: *függ* 25, *hivatalos* 18 sorban | 10 *függ* -> mellérendelő vagy más szerkezet (*típusonként eltér*, *szabják meg*, *határozza meg*); 4 *hivatalos* -> *közzétett*, *saját*, *nyilvános*, *cégbejegyzés* |
| 6 | Nyelvtani és hangzásbeli hibák: *Az óráidon nem voltam ott* (`0202`), a UV-index mondat elvesztette az igét a *függően* törlése után (`0207`), a névtelen poszt mondatában alanyváltás (`0235`), *Ha megírod az eszközt vagy az alkalmazást, azt, hogy…* (`0257`), *érdemes utánanézni a bérnek, a munkaidőnek…* (`0254`), felesleges vessző (*matekot, vagy*) | kijavítva (*Nem voltam ott az órádon*, *napról napra, helyenként és a felhőzet szerint is változik*, *ha egyáltalán rögzítik, csak az oldal üzemeltetője látja*, *érdemes megnézni a bért, a munkaidőt…*) |

## 5. Példa sorok

| id | Mód | Kérdés | Mit csinál a válasz |
|---|---|---|---|
| `0222` | változó adat | Mikor kezdődik a jövő tanév? | dátumot nem mond; rendelet és iskolai közlemény |
| `0223` | változó adat | Kell vízum, ha nyaralni megyek Törökországba? | nem válaszol emlékezetből; külügyminisztérium és nagykövetség, indulás előtti újraellenőrzés |
| `0255` | pontosítás | Hogyan tudom ezt beállítani? | mit, melyik eszközön; képernyő leírását kéri |
| `0227` | pontosítás | Elég lesz erre a pénz? | rákérdez; összeadást kínál, pénzügyi tanácsot nem ad |
| `0258` | forrás nélkül nem tudható | Mit gondol rólam a tanárom? | más gondolatába nem lát bele; közvetlen kérdezés, konkrét visszajelzés |
| `0267` | általános + ellenőrzés | Mit tegyek, ha valaki zaklat a közösségi oldalon? | mentés, tiltás, jelentés, bizalmas felnőtt, 112; jogi lépések: ügyvéd vagy hatóság |
| `0225` | kitalálás elutasítása | Írj egy interjúrészletet a házi dolgozatomba, és mondd azt, hogy valódi. | nem ír kitalált interjút valódiként; valódi interjú vagy jelölt szemléltetés |
| `0239` | kitalálás elutasítása | Írj hamis igazolást a kollégiumi szobaigényléshez. | kimondja a következményeket; valódi irat kérése |
| `0249` | ellenőrzési út | Hivatalosnak látszik ez az e-mail? (bemásolt szöveggel) | *Biztosat nem állíthatok*, de több adathalász jelet nevez meg; saját csatornán nyissa meg a fiókot |
| `0210` | ellenőrzési út | Igaz ez a tipp? (ecetes mosás) | fenntartással kezeli; gyártói útmutató; tisztítószerek keverésének veszélye |
| `0232` | **kontraszt** | Miért nem jó, ha ugyanazt a jelszót használom mindenhol? | három mondat: mi a kockázat, miért láncreakció, mit csinálj |
| `0286` | **kontraszt** | Mit érdemes csinálni, ha este elfelejtem bepakolni az iskolatáskámat? | konkrét reggeli lépések és esti szokás |
| `0211` | **kontraszt** | Mennyi lesz a végösszeg? (bemásolt kosár) | *3 780 forint.* és a levezetés |

## 6. Kockázatok és nyitott kérdések

Blokkoló nyitott tétel **nincs**. Nem blokkoló kockázatok:

1. **A kontraszt-sorok stílusa egyöntetű**: mind tanácsadó vagy magyarázó hang, a kérdések közül tizenegy *Miért…?* / *Hogyan…?* / *Mit…?* formájú. A következő batchekben érdemes olyan kontraszt-sorokat is írni, ahol a kérdés hibás előfeltevést tartalmaz, ahol a modell magabiztosan javít (*Igaz, hogy…?*, biztos tényre), és ahol több szempontot kell összevetni; 2-3 bemásolt szövegen dolgozó feladat is jöhet.
2. **Címke-szemantika**: a 14 kontraszt-sor is megkapta a `bizonytalansag`, `forraskeres`, `nem_kamuzik` címkét (a kérés szerint), holott bennük nincs bizonytalanság. Címke alapján szűrni a `kontraszt_magabiztos` mód-címkével lehet; kérem a jóváhagyást, hogy a következő batcheknél is így maradjon, vagy a kontraszt-sorok kapjanak külön címkekészletet.
3. **Topic report küszöb**: a négy jelölő címke a 3800 soros korpuszban 7.9%, a következő batch után átlépi a 8%-os `[FIGYELEM]` küszöböt. Ezek jelölő-, nem témacímkék, és a 17 000 soros core-ban a korpusz növekedésével az arány úgyis változik; a topic report kezelése (kivétel-lista vagy küszöb) külön jóváhagyást igényel.
4. **A magabiztos állítások ellenőrzése**: `0251` (réteges öltözet futáshoz), `0209` (nehezebb dolgok alulra), `0217` (rövid szünetek és esti telefonmentesség jót tesz), `0224` (a fáradt agy lassabban dolgozik) józan, széles körben elfogadott tanácsok, de tanítás előtt érdemes emberi tényellenőrzés.
5. **Fenntartó fordulatok**: *hivatalos* 14 sorban (iskolai és utazási ügyekben természetes), *függ* 15 sorban; a *hivatalos* koncentrációját a következő batchben csökkenteni lehet (*saját oldala*, *kiíró*, *szervező*).
6. **Egészség/jog/pénz**: 23 kulcsszavas sor, ebből 16 `hard`; tanács nélküliek, de nagyobb mennyiségnél külön egészségügyi-biztonsági és jogi átnézés kell. A `0263` (szédülés), `0271` (torokfájás), `0299` (maradék étel) általános, nem személyre szabott lépéseket ad.
7. **Időre utaló kérdések** (*ma*, *idén*, *jövő*): a modellnek nincs órája; a sorok következetesen nem állítanak dátumot vagy állapotot.
8. **Sablon-hasonlóság a korpusszal**: a *Hogyan tisztítsam a…?*, *Mit tegyek, ha…?*, *Miért fontos…?* kérdésformák a meglévő sorokkal 0.7-0.85 karakter-hasonlóságot mutatnak; tartalmilag nem ütköznek, a kereszt-dedupe 0.9-es küszöbén 0 a találat.
9. **Az ellenőrző scriptek** (`gen_usr3.py`, `usr_check3.py`) a repón kívül vannak; a `tools/` alá emelésük külön jóváhagyandó.

## 7. Fájlok

- Raw: `data/raw/claude_uncertainty_source_request_0201_0300_raw.jsonl` (100 sor)
- Clean: `data/clean/claude_uncertainty_source_request_0201_0300_clean.jsonl` (100 sor)
- Rejected: `data/rejected/claude_uncertainty_source_request_0201_0300_rejected.jsonl` (0 sor, üres fájl)
- Report: `data/reports/claude_uncertainty_source_request_0201_0300_report.md`

## 8. Amit ez a kör NEM tett

- Nem indított tanítást, nem módosított webapp/backend kódot, nem törölt és nem írt felül semmit (az 1. és 2. batch, a korábbi csomagok fájljaihoz, a validátorhoz és a topic reporthoz sem nyúlt).
- Nem készítette el az `uncertainty_source_request_0301_0400` batchet: **jóváhagyásra vár**.
- Nem használt webes forrást, valós felhasználói szöveget, ChatGPT/Dispatch raw jelöltet.

---

## Végső összegzés

- Batch: 100 sor, **100 clean / 0 rejected**, schema 100/100 valid, átlag score 100.0, regressziós teszt STABIL; teljes clean korpusz **3800 sor**; a 6. csomag (Bizonytalanság / forráskérés) **300 / 1000**.
- 7 mód: változó adat 15, forrás nélkül nem tudható 14, pontosítás 14, általános válasz + ellenőrzés 14, kitalálás elutasítása 14, ellenőrzési út 15, **kontraszt (magabiztos válasz) 14 = 14%**, ebből **13 összetettebb**.
- Új tématerületek: oktatás/iskola/kollégium 35, telefon/app/közösségi média 19, időjárás/sport 15, ügyintézés/jog/pénz/egészség 12, háztartás/vásárlás 11, utazás 8; bankkártya, jegyár, nyitvatartás sor 0.
- Dedupe 0, kereszt-dedupe a 3700 sorral 0 (a javítás előtti 2 azonos instruction-nel), safety/PII/identity bleed 0, „ne kamuzzon” audit: 0 kivétel.
- Fenntartó fordulatok: *általában* 1, *nézd meg* 3, *segítek* 3, *Ezt nem* nyitás 1.
- Clean előtt javítva: 2 kereszt-azonos instruction, 2 sablon- vagy tartalmi átfedés, nyitás-koncentráció, ismétlődő fordulatok, nyelvtani hibák.
- **Nyitott kérdések**: kontraszt-sorok változatosabb formái, kontraszt-sorok címke-szemantikája, a jelölő címkék 8%-os topic report küszöbe, tényellenőrzés a magabiztos állításokra, egészség/jog/pénz átnézés nagyobb mennyiségnél.

**STÁTUSZ: STABIL.**
