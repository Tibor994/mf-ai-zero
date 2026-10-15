# MT-6 negyedik batch (`multiturn_0151`–`0200`) — rekordszintű AI-felülvizsgálati napló

**Ez AI-alapú felülvizsgálat (Claude-alügynökök + saját közvetlen ellenőrzés), NEM független és NEM emberi audit.**
A független, emberi tartalmi átolvasás továbbra is nyitott, kötelező tanítás előtti feltétel.

A napló három dolgot különít el: (1) az **eredeti találatokat** (mit jelzett a felülvizsgálat az adott állapotban),
(2) a **javításokat** (mi változott ténylegesen, a verziók bájt-szintű különbségéből számolva), és (3) a **javítás utáni
ellenőrzést** (melyik állapotot ki olvasta újra). Csak ténylegesen megtörtént ellenőrzés szerepel benne.

## Menete, verziók és kezelés

Minden alügynök friss kontextusú Claude-példány volt, **csak olvasási megbízással** (fájlt módosítani nem kérték; a repó állapota ezt nem cáfolta); a jelzéseket a szerző (én)
közvetlenül a tényleges szövegen ellenőriztem, és csak a valóban hibás vagy bizonyíthatóan gyenge pontot javítottam.
Az alügynökök teljes jelentései **nem** kerültek a repóba; a jelen napló azok kivonata és a tényleges
adatkülönbségek. Az ellenőrzési szempontok: `meta.depends` szigorú teszt (a válasz megírható-e az őt közvetlenül megelőző
felhasználói üzenetből előzmény nélkül? — ha igen, a bejegyzés fölösleges; a `depth` számítása), a felhasználói feltételek
betartása (az összegzésekben is), forrásigényes állítások (volatilis vagy szolgáltatófüggő adat általános tényként),
számítások újraszámolása, név- és személyes adat szabály, címke–tartalom illeszkedés, nyelvtan és természetesség.

| Állapot | Mit jelent | sha256 (a nyers fájlé) |
|---|---|---|
| `draft1` | az eredeti piszkozat, az 1. kör ezt olvasta (4 alügynök, 50 rekord) | `c653e1dd6762efd685e17aab3bcad8fb9597f0c78aafa1f82df5fea201459c9d` |
| `draft2` | az 1. kör javításai (A) után; a 2. kör ezt olvasta újra (4 alügynök, a 43 módosult rekord) | `d7d736d5493d5f44cedb93ac13fd5e9148c10ca6ebf680628a89914eca034f0b` |
| `draft3` | a 2. kör javításai (B) után; a 3. kör ezt olvasta újra (2 alügynök, a 32 újra módosult rekord) | `94791301133ffa87703618a1a4a825d55241808fd0f1fdea8ce9267d28ee9f3b` |
| `draft4` | a 3. kör javításai (C) után (18 üzenet + 1 `depends`); saját közvetlen újraolvasás | `6086591b82677e83b131b906c32e89f283f3650033f5a232fdbddf6a7060892f` |
| `draft5` | a `draft4` + az MT-3 két `info` jelzése miatti átfogalmazás (D: `0196` 8. és `0200` 2. üzenet); **a 4. (végső) célzott kör ezt az állapotot olvasta** | `98fa81f429a0117e3858027cce4d81a3b18ae64ac5c09d69f12099fe155e6c27` |
| **végső** | a `draft5` + a 4. kör 4 igazolt, apró nyelvtani/pontossági javítása (E: `0157` 13., `0164` 11., `0168` 3., `0193` 9. üzenet); ez a repóban lévő fájl, erre futott az MT-1 → MT-5 lánc | `72a9d7f8e2de2768374ddb26c1ff8ebaded20a1db878b5d6f36d43a57d9f4033` |

| Kör | Olvasott állapot | Hatókör | OK | NEEDS_FIX | Megjegyzés |
|---|---|---|---|---|---|
| 1. | `draft1` | mind az 50 | 16 | 34 | a jelzések többsége `depends`-hiba; tényszerű vagy belső ellentmondás: `0153`, `0158`, `0169`, `0176`, `0191`, `0195`, `0198` |
| 2. | `draft2` | az 1. kör után módosult 43 | 25 | 18 | főleg `depends` (hiányzó/fölösleges); egy nyelvi hiba (`0193` „helyet foglalni”), a többi megfogalmazás |
| 3. | `draft3` | a 2. kör után módosult 32 | 21 | 11 | 3 ERROR: `0195` összegzés (te/férjed), `0198` 7. üzenet (állítmány nélküli mondat — az előző javításom hibája), `0200` 3. üzenet („magánszféra”) |
| 4. (végső, célzott) | `draft5` | a 3. kör utáni (C+D) 20 üzenet és 1 `depends`, 13 rekord teljes kontextussal; minden rekord `depends`-e | 9 | 4 (csak MINOR; 0 ERROR) | kiemelt vizsgálat: `0198`; a `0196` és `0200` MT-3-vezérelt átfogalmazása **eddig egyik alügynöki körben sem szerepelt** (csak MT-1/MT-3 futott rajta), ezt a 4. kör pótolta; az alügynök a 0198 teljes rekordját is átnézte: nincs ERROR |

A 7 érintetlen rekordot (`0165`, `0167`, `0170`, `0175`, `0183`, `0186`, `0187`) az 1. kör találta rendben, utána nem módosultak.
A 2. és 3. körben OK-nak értékelt, azóta nem módosult rekordok végső állapota megegyezik az utoljára olvasott állapottal.

**Ismert, dokumentált sorrendi eltérés.** A negyedik batch célértékei a terv új 7/c szakaszában a szövegírás előtt, a terv
fájljában rögzültek, külön commitban (`69ea889`, `v1.13.32-mt6-batch4-targets`) viszont csak az F1 első szövegvázlatának
(`b4_f1.py`, a munkamappában, nem a repóban) megírása **után** kerültek be. A célszámok a rögzítés és a commit között nem
változtak, de ezt **nem tekintem teljesen előzetes, külön commitban rögzített célnak**; az adatot és a jelentést tartalmazó
commit viszont mindenképp a célok commitja után készült.

## Rekordszintű napló

Jelölések: „üz. N” = a javítás után az adott sorszámú üzenet szövege megváltozott (0 = első felhasználói üzenet, páratlan = asszisztens);
„depends tN: régi→új” = az N. (asszisztens) üzenet `depends` bejegyzésének `on` listája. A „Javítás (minőségi leírás)” a szerző
összefoglalója, a „változott” oszlopok a ténylegesen mért különbségek.


| Rekord | Család / hossz | 1. kör (eredeti piszkozat) | Eredeti találatok (fő pontok) | Javítás (minőségi leírás) | A. javítás után változott | 2. kör | B. javítás után változott | 3. kör | C. javítás után változott | D. (MT-3-vezérelt) átfogalmazás | 4. (végső) célzott kör | E. a 4. kör után változott (saját újraolvasás) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0151 | F1 / 4 váltás | OK | stilizált megfogalmazás; címke: a felhasználó kétszer változtat az elosztáson | szöveg; skills: valtozo_keres | skills | OK | üz. 3 | OK | – | – | – | – |
| 0152 | F1 / 4 váltás | NEEDS_FIX | „egyszerű terepű” nem természetes; a 3 órás idő összetétele nem világos | szöveg (a 3. körben az autózás kizárása pontosítva) | üz. 3,7 | OK | üz. 7 | NEEDS_FIX(MINOR) | üz. 7 | – | OK | – |
| 0153 | F1 / 5 váltás | NEEDS_FIX | ERROR: az ecet/szódabikarbóna mennyiség félrevezető; depends t5 [0] téves (a kérés újra szerepel) | lazítás: extra sütőpor; depends t5 → [2] | üz. 3; depends t5: [0]→[2] | OK | – | – | – | – | – | – |
| 0154 | F1 / 5 váltás | OK | nyelvtan („az 42 nap”, saját olvasat); 2. kör: depends t5 index 3 fölösleges | szöveg; depends t5 → [2] | üz. 1 | NEEDS_FIX | depends t5: [2, 3]→[2] | OK | – | – | – | – |
| 0155 | F1 / 6 váltás | NEEDS_FIX | depends t5/t7 indexek; „15 percben” kétértelmű; címke | szöveg; depends t5 → [3], t7 → [0,2]; skills + valtozo_keres | üz. 0; depends t5: [2, 3]→[3]; t7: [0, 3]→[0, 2]; skills | OK | – | – | – | – | – | – |
| 0156 | F1 / 6 váltás | NEEDS_FIX | 32–50 palánta (nem 30–45); a „hetente hányszor” kérdésre nem volt heti szám | szöveg; 3. kör: „kb. kétnaponta” | üz. 7,9,11 | OK | üz. 9 | OK | – | – | – | – |
| 0157 | F1 / 7 váltás | NEEDS_FIX | belső ellentmondás („ismételd az előzőt”); biztonsági megfogalmazás; a 3–5 km túlbecsült; depends t11 gyenge | szöveg ×több üzenet; 3–4. kör: 5 km a 9–10. hétre, 7. hét, tagolás, helyesírás | üz. 3,5,11,13 | OK | üz. 5,9,11,13 | NEEDS_FIX(MINOR) | üz. 5,9,11,13 | – | NEEDS_FIX(MINOR) | üz. 13 |
| 0158 | F2 / 3 váltás | NEEDS_FIX | ERROR: a park mosdója/játszótere helyfüggő tény általános állításként | hedge („nézzétek meg…”) | üz. 3 | OK | – | – | – | – | – | – |
| 0159 | F2 / 3 váltás | NEEDS_FIX | ERROR (depends): t5 [0,2] → a válasz csak a 2. üzenet adatait használja; 2. kör is jelezte | válasz átírva (fiók, havi mentés), depends t5 → [2]; „felhőtárhely” | üz. 5 | NEEDS_FIX | üz. 5; depends t5: [0, 2]→[2] | OK | – | – | – | – |
| 0160 | F2 / 4 váltás | NEEDS_FIX | depends t5 [2,3] → [3]; „mit együnk” | depends, user üzenet | depends t5: [2, 3]→[3] | OK | üz. 6 | OK | – | – | – | – |
| 0161 | F2 / 4 váltás | NEEDS_FIX | ERROR (depends): t5 [1,2] → [2]; szellőzés/mélység hiányzott; 2. kör: t3 [0,1] → [0] | szöveg, depends, „inkább … illik” | üz. 3; depends t5: [1, 2]→[2] | NEEDS_FIX | üz. 3; depends t3: [0, 1]→[0] | OK | – | – | – | – |
| 0162 | F2 / 4 váltás | NEEDS_FIX | ERROR (depends): t5, t7 téves indexek; a beszedés/átutalás különbség pontatlan | szöveg; depends t5 → [2], t7 → [2] | üz. 3,5; depends t5: [3]→[2]; t7: [0, 2]→[2] | OK | – | – | – | – | – | – |
| 0163 | F2 / 5 váltás | NEEDS_FIX | liszt 150–190 g; cukrozatlan növényi ital (a legkisebb nem szereti az édeset); „adag” → „gofri” | szöveg; 3. kör: gofrisütő, „ha te is eszel” | üz. 1,5,7,9 | OK | üz. 5 | OK | – | – | – | – |
| 0164 | F2 / 6 váltás | NEEDS_FIX | ERROR (depends): t5 [0,3] felfújt → [3]; kétértelmű kifejezések | depends, szöveg | üz. 3,11; depends t5: [0, 3]→[3] | NEEDS_FIX | üz. 11 | OK | üz. 11 | – | NEEDS_FIX(MINOR) | üz. 11 |
| 0165 | F3 / 3 váltás | OK | nincs jelzés | nem módosult | – | – | – | – | – | – | – | – |
| 0166 | F3 / 3 váltás | OK | opcionális megfogalmazás (a 2. körben OK); MT-3 info: 0196 hasonló kérdése | szöveg | üz. 3 | OK | – | – | – | – | – | – |
| 0167 | F3 / 4 váltás | OK | nincs jelzés | nem módosult | – | – | – | – | – | – | – | – |
| 0168 | F3 / 4 váltás | NEEDS_FIX | a 3. üzenet nem használta a felhasználó adatait (8 hónap, online); 2. kör: hiányzó depends t3, „Ott” hivatkozás; 3. kör: elállási logika | szöveg (NMHH, 16 hónap hátra, 14 napos elállás hedge-elve); depends t3 → [0] | üz. 3,7 | NEEDS_FIX | üz. 3; depends t3: –→[0] | NEEDS_FIX(MINOR) | üz. 3 | – | NEEDS_FIX(MINOR) | üz. 3 |
| 0169 | F3 / 5 váltás | NEEDS_FIX | ERROR: depends t5 fölösleges; a „sötét csíkok” okai tévesek; 2. kör: „ezt válaszd” homályos | szöveg; depends t5 → [2] | üz. 5,9; depends t5: [3]→[2] | NEEDS_FIX | üz. 5,9 | OK | – | – | – | – |
| 0170 | F3 / 5 váltás | OK | nincs jelzés | nem módosult | – | – | – | – | – | – | – | – |
| 0171 | F4 / 3 váltás | OK | opcionális: víz/rizs tömegarány pontosítása | szöveg | üz. 1 | OK | üz. 1 | OK | – | – | – | – |
| 0172 | F4 / 3 váltás | NEEDS_FIX | depends t5 hiányos [0,3]; fogalmazás (a 3. üzenet két körben pontosítva) | szöveg; depends t5 → [0,3] | üz. 3; depends t5: [3]→[0, 3] | OK | üz. 3 | OK | üz. 3 | – | OK | – |
| 0173 | F4 / 3 váltás | OK | nyelvtan/módbeli keveredés („végig kell gondolnia”) | szöveg (2. és 3. kör) | üz. 3,5 | NEEDS_FIX | üz. 3 | OK | – | – | – | – |
| 0174 | F4 / 4 váltás | NEEDS_FIX | ERROR (depends): t5 [1] fölösleges; „csak egész számokkal” pontosítás; F4 (téves felhasználói javítás) tartalmilag megtartva | szöveg; depends t5 → [1]; t7 → [5] | üz. 3,5,7 | OK | – | – | – | – | – | – |
| 0175 | F4 / 4 váltás | OK | nincs jelzés | nem módosult | – | – | – | – | – | – | – | – |
| 0176 | F4 / 5 váltás | NEEDS_FIX | ERROR: a végső összegzés „hetente” vs. korábbi „1–2 hetente”; elhagyott feltétel (nagyobb bögre); „fölött lehet” gyenge | szöveg; depends t5 → [3] | üz. 3,9; depends t5: [2]→[3] | NEEDS_FIX | üz. 3,7 | OK | – | – | – | – |
| 0177 | F4 / 5 váltás | NEEDS_FIX | a hónap-oszlop feltételezése, az évszám, „Két feltételhez” megnevezés | szöveg (C oszlop, évszám, megnevezés) | üz. 5,7,9 | OK | – | – | – | – | – | – |
| 0178 | F5 / 3 váltás | NEEDS_FIX | depends t5 [0,3] → [0]; „futásokra jár” | szöveg, depends | üz. 5; depends t5: [0, 3]→[0] | OK | – | – | – | – | – | – |
| 0179 | F5 / 4 váltás | NEEDS_FIX | ERROR (depends): t5 [3] fölösleges; a Perseidák többsége éjfél után látszik; 2–3. kör: hiányzó depends t3, t5 → [0,3] | szöveg; depends t3, t5 | üz. 3,5 | NEEDS_FIX | üz. 3,5; depends t3: –→[0] | NEEDS_FIX(MINOR) | üz. 5; depends t5: [3]→[0, 3] | – | OK | – |
| 0180 | F5 / 4 váltás | NEEDS_FIX | ERROR (depends): t5 fölösleges (u4 átfogalmazva); „napi kirándulás”; „két felnőttel” kétértelmű (ketten) | szöveg; depends t7 → [1,5] | üz. 1,4,5; depends t7: [1]→[1, 5] | OK | üz. 0 | OK | – | – | – | – |
| 0181 | F5 / 5 váltás | NEEDS_FIX | depends t5; az első nap ismétlése; „kisebb államok” | szöveg; depends t5 → [3] | üz. 5,7,9; depends t5: [2, 3]→[3] | NEEDS_FIX | üz. 7 | OK | – | – | – | – |
| 0182 | F5 / 6 váltás | NEEDS_FIX | ERROR (depends): t3, t5 fölösleges; „összehasonlítani az ajánlatokat” | válaszok átírva, depends t7 → [2] | üz. 3,5,11; depends t7: [2, 3]→[2] | OK | – | – | – | – | – | – |
| 0183 | F6 / 3 váltás | OK | nincs jelzés | nem módosult | – | – | – | – | – | – | – | – |
| 0184 | F6 / 3 váltás | NEEDS_FIX | depends: a név a 0. üzenetből (t5 → [0,2,3]); tárgysor; 3. kör: az engedélyezés kérése hiányzott a mintából | szöveg | üz. 5; depends t5: [2, 3]→[0, 2, 3] | OK | üz. 5 | NEEDS_FIX(MINOR) | üz. 5 | – | OK | – |
| 0185 | F6 / 4 váltás | NEEDS_FIX | hiányzó depends t5; lepedő-összehajtás pontatlan; „agyonnyom” | szöveg; depends t5 → [3] | üz. 5,7; depends t5: –→[3] | OK | üz. 5,7 | OK | – | – | – | – |
| 0186 | F6 / 4 váltás | OK | nincs jelzés | nem módosult | – | – | – | – | – | – | – | – |
| 0187 | F6 / 5 váltás | OK | nincs jelzés | nem módosult | – | – | – | – | – | – | – | – |
| 0188 | F7 / 4 váltás | OK | opcionális: depends t5 → [0,1] | depends | depends t5: [1]→[0, 1] | OK | – | – | – | – | – | – |
| 0189 | F7 / 5 váltás | OK | opcionális: „A többi szónál gyakoribb a j”, önfelolvasás; 2. kör: t5 depends gyenge | szöveg (ly-os szólista visszahivatkozás) | üz. 1,5,9 | OK | üz. 5,9 | OK | – | – | – | – |
| 0190 | F7 / 5 váltás | OK | opcionális: „tehát”; depends t9 kiegészítése | szöveg, depends t9 → [1,5,7] | üz. 9; depends t9: [1, 5]→[1, 5, 7] | OK | – | – | – | – | – | – |
| 0191 | F7 / 6 váltás | NEEDS_FIX | ERROR (tény): „400 W … kevés folyadékkal” fordított tanács; 2. kör: hiányzó depends t3, t9 → [2] | szöveg; depends | üz. 7,9,11; depends t9: [3]→[2, 3] | NEEDS_FIX | depends t3: –→[0]; t9: [2, 3]→[2] | OK | – | – | – | – |
| 0192 | F7 / 7 váltás | NEEDS_FIX | ERROR (depends): t11 [3] fölösleges (a válasz a HDMI kábelre hivatkozik); USB-C kábel pontosítás | szöveg | üz. 3,11 | OK | üz. 3,7 | OK | – | – | – | – |
| 0193 | F8 / 6 váltás | NEEDS_FIX | ERROR (depends): t5 [3] → [0]; „óránkénti” beosztás; 2–3. kör: „helyet foglalni”, „15:00-s”, „a mentor” | szöveg; depends t5 → [0] | üz. 3,5,9,11; depends t5: [3]→[0] | NEEDS_FIX | üz. 3,5,9,11 | NEEDS_FIX(MINOR) | üz. 9,11 | – | NEEDS_FIX(MINOR) | üz. 9 |
| 0194 | F8 / 6 váltás | NEEDS_FIX | ERROR (depends): t5 [2,3] → [0,2]; a „rendben van?” kérdésre nem felelt; jegyzőkönyv/írásbeli válasz pontosítás | szöveg; depends t5 | üz. 7; depends t5: [2, 3]→[0, 2] | OK | üz. 9 | NEEDS_FIX(MINOR) | üz. 9 | – | OK | – |
| 0195 | F8 / 6 váltás | NEEDS_FIX | ERROR: 9/12 éves feladat-ellentmondás; depends t11, t9; „ágyat húzni”; 3. kör: a családi összegzés „te/férjed” | szöveg; depends t9 → [7], t11 → [3,7,9] | üz. 5,7,11; depends t11: [3, 5, 9]→[3, 7, 9] | NEEDS_FIX | üz. 5,7,9,11; depends t9: [5]→[7] | NEEDS_FIX(ERROR) | üz. 7,11 | – | OK | – |
| 0196 | F8 / 7 váltás | OK | depends t9/t7/t11; csapat többes szám; a lista prózában; MT-3 info: u8 hasonló a 0166-hoz | szöveg; depends; u8 átfogalmazva | üz. 5; depends t9: [0, 2]→[0] | NEEDS_FIX | üz. 13; depends t7: [2, 5]→[5]; t11: [2, 3]→[3, 4]; t13: [2, 5, 9, 11]→[2, 4, 5, 6, 9, 11] | NEEDS_FIX(MINOR) | üz. 13 | üz. 8 | OK | – |
| 0197 | F8 / 8 váltás | NEEDS_FIX | ERROR (depends): t5, t7, t11, t13 és hiányzó t3; hat vendég/hat fő; ital/alkohol; ár-becslés módszer | szöveg; depends | üz. 0,7,9,11,15; depends t5: [0, 3]→[3]; t7: [2, 5]→[5]; t11: [0, 2]→[0]; t13: [2, 3]→[3] | NEEDS_FIX | üz. 7,9,15; depends t3: –→[0] | OK | – | – | – | – |
| 0198 | F8 / 8 váltás | NEEDS_FIX | ERROR: tempó-ellentmondás (6 km 45 perc); depends t5 hiányzik, t7 általános; cipő „bejárt”; a 3. körben a 7. üzenet javított mondata állítmány nélküli lett | szöveg; depends t5, t13; a 7. üzenet állítmánnyal javítva | üz. 3,5,7,13,15; depends t13: [3]→[0, 3] | NEEDS_FIX | üz. 7,13; depends t5: –→[0]; t13: [0, 3]→[0] | NEEDS_FIX(ERROR) | üz. 7 | – | OK | – |
| 0199 | F9 / 4 váltás | NEEDS_FIX | ERROR (depends): t7 [4,5] → [0]; „átvehető a jegy” | depends; szöveg | üz. 7; depends t5: [3]→[0, 3]; t7: [4, 5]→[0] | NEEDS_FIX | üz. 7 | OK | – | – | – | – |
| 0200 | F9 / 5 váltás | NEEDS_FIX | ERROR (depends): t7, t9, hiányzó t3; „Nemzeti Jogszabálytár”; 3. kör: „magánszféra” téves szó; MT-3 info: u2 hasonló a 0048-hoz | szöveg; depends; u2 átfogalmazva | üz. 3,7,9; depends t7: [3, 5]→[0, 1, 5]; t9: [0, 3, 5, 7]→[0, 1, 3, 7] | NEEDS_FIX | üz. 3,7; depends t3: –→[0, 1] | NEEDS_FIX(ERROR) | üz. 3 | üz. 2 | OK | – |

## A 4. kör után (E)

A 4. kör 0 ERROR-t jelzett; 4 rekordban javasolt apró nyelvtani/pontossági javítást (`0157` 13., `0164` 11., `0168` 3., `0193` 9. üzenet).
Ezeket a szövegen közvetlenül ellenőriztem (egy hiányzó toldalék/ige, kétértelmű „15 órás”), és javítottam. A javított négy
üzenetet **újabb alügynök nem olvasta**: a javítás utáni ellenőrzés itt saját közvetlen újraolvasás, az MT-1 (0 hiba) és a
teljes lánc újrafuttatása (MT-3: 0 találat; MT-2/MT-4/MT-5 lefutott). A 4. kör opcionális, nem hibának ítélt javaslatait
(`0157` 5. és 9., `0194` 9., `0195` 11., `0198` 7./13./15., `0200` 9. üzenet, valamint a `0157` 7., `0164` 7., `0196` 7./11.
`depends` határeseteit) **nem alkalmaztam**: igazolt hibát nem jelentettek, így a szöveg nem változott. A `0198` rekord
`depends` bejegyzéseit (t3, t5, t7, t11, t13, t15) a 4. kör külön végigvizsgálta: mind helyes.

## Összesített változások (mért, rekordszám / üzenetszám)

| Javítás | Rekord | Üzenet | `depends` módosítás |
|---|---|---|---|
| A (1. kör után) | 43 | 87 | 26 rekord |
| B (2. kör után) | 32 | 49 | 11 rekord |
| C (3. kör után) | 13 | 18 | 1 rekord (`0179`) |
| D (MT-3 `info` miatt) | 2 | 2 | 0 |
| E (4. kör után) | 4 | 4 | 0 |

Az eredeti piszkozathoz képest összesen **a 7 érintetlen rekord kivételével mind a 43 rekord módosult**; a 7 érintetlen:
`0165`, `0167`, `0170`, `0175`, `0183`, `0186`, `0187`.

## Ellenőrizetlen / nem igazolt pontok (nem tekintendők igazoltnak)

Ezeket az alügynökök sem keresővel, sem hivatalos forrásból nem erősítették meg, vagy csak másodlagos forrást találtak;
a szövegek általános megfogalmazásúak vagy a hivatalos forrásra/ügyintézőre utalnak:

* `0168`, `0194`, `0200`: fogyasztóvédelmi és munkajogi részletek (14 napos elállás, szóbeli/írásbeli panasz kezelése, az NMHH
  hatásköre, a pótszabadság jogszabályi háttere, versenyszféra/közszféra) — hivatalos jogszabályszöveggel nem ellenőriztem.
* `0153`, `0157`, `0171`, `0176`, `0197`, `0198`: sütési/főzési arányok és idők, edzés- és tempóbecslések, kávé- és
  koffeinhatárok (400/200 mg, EFSA-ajánlás alügynöki kereséssel megerősítve, de nem hivatalos forrásból olvasva).
* `0161`, `0163`, `0172`, `0180`: háztartási/utazási ökölszabályok (hűtő-űrtartalom, gofri-hozam, a Pécs állomás–belváros séta,
  a Budapest–Pozsony autóút ideje).
* Az AI-átolvasás nem talált olyan helyet, ahol a volatilis adat (ár, díj, menetrend, nyitvatartás) általános tényként szerepelne; ez az átolvasás eredménye, nem bizonyítás.
