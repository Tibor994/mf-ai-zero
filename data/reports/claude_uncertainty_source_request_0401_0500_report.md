# Ötödik uncertainty_source_request batch - uncertainty_source_request_0401-0500

**Verdikt: STABIL.** 100 sor, **100 clean / 0 rejected**, `category: uncertainty_source_request`, a **6. csomag (Bizonytalanság / forráskérés)** ötödik batchje az új, bővített 17 000 soros `instruction_core`-ban. A csomag célmérete **1000 sor**, ezzel **500 / 1000** kész, vagyis a csomag fele megvan.
A batch célja: a modell ne találjon ki választ, ha nem biztos, **de ne is legyen feleslegesen félős**. Új ebben a batchben: (1) **14 kontraszt-sor, ebből 10 előfeltevéses**: **6 hibás előfeltevést javító** és **4 igaz előfeltevést megerősítő** (a modell nem csak cáfol, hanem tud határozott igent is mondani), 4 hétköznapi tanács; (2) konkrétabb, életszerűbb helyzetek az általános `Mit tegyek, ha…?` típusú, `simple_qa`-szerű kérdések helyett; (3) telefon/app/technika, háztartás, utazás, sport, közösségi média, vásárlás, ügyintézés és hétköznapi félreértések.

> **Számozás**: 6. csomag = Bizonytalanság / forráskérés, cél 1000 sor; a régi 4900 soros roadmap számozása nem irányadó. Állás a batch után: **500 / 1000**.
> **Címkék**: a fő mód a korábbi batchekkel egyezően **`kontraszt_magabiztos`** (a kérésben `contrast_magabiztos` szerepelt; a már commitolt címkét tartottam meg). A `hibas_elofeltevesjavitas` plusz címke maradt, és **nem külön fő mód**. Az igaz előfeltevést megerősítő sorokon új, szintén plusz címke van: **`igaz_elofeltevesmegerosites`** (a szűrhetőség kedvéért; lásd 6. fejezet, 3. pont).

## 0. A kérés követelményei és teljesülésük

| Követelmény | Teljesülés |
|---|---|
| 100 sor, magyar, `uncertainty_source_request`, id `0401`-`0500` | 100 sor, folytonos id-k, `source: synthetic_claude_magyar`, a meglévő 9 mezős séma |
| 100/100 valid, 100/100 clean, 0 rejected | **100 / 100 valid, 100 clean, 0 rejected**; a validátor az első futásban 1 sort elutasított (`0439`), ezt clean előtt javítottam (4. fejezet, 2. pont) |
| 0 batchen belüli duplikátum, 0 kereszt-dedupe találat | 0 / 0 (2. fejezet); a saját összevetés egy batchen belüli azonos instruction-t talált (`0412`/`0416`), ezt javítottam (4. fejezet, 1. pont); kereszt-dedupe a korpusszal az első futástól 0 |
| 0 PII/URL/e-mail/telefonszám, 0 MF-AI/Nextora, 0 identity bleed, 0 erős káromkodás | mind 0 (3. fejezet 5. pont) |
| Regressziós teszt STABIL | minden teszt sikeres, **STÁTUSZ: STABIL** |
| Címkézés: `hibas_elofeltevesjavitas` marad, nem külön fő mód; a fő mód a kontraszt mód-címke | mind a 6 javító soron plusz címke; fő mód `kontraszt_magabiztos` |
| 10-15% kontraszt-sor | **14 sor = 14%** |
| 8-12 előfeltevéses kontraszt-sor | **10 sor** (6 javító + 4 megerősítő) |
| Ne legyenek mind cáfolósak: kb. 5-6 hibás előfeltevést javító, kb. 3-5 igaz előfeltevést megerősítő | **6 javító**, **4 megerősítő** (1.3) |
| Nem félős kontraszt-sorok | 0 fenntartó kifejezés a 14 sorban (az egyetlen kulcsszó-találat az *előfordulhat, hogy semmit nem érzel* a `0472`-ben, ténymegállapítás, nem fenntartás) |
| A többi sor bizonytalanság / forráskérés | 86 sor, 6 mód (15 / 14 / 14 / 14 / 14 / 15) |
| Kerüld az általános `Mit tegyek, ha…?` `simple_qa`-szerű kérdéseket; életszerűbb szituációk | **0** `Mit tegyek, ha…?` instruction; a kérdések konkrét helyzetekre szólnak (*Kell autópálya-matrica a holnapi útvonalunkon?*, *Meddig érvényes a gázkészülékem felülvizsgálata?*, *Miért nem jelent meg a posztom a követőim hírfolyamában?*); kereszt-dedupe találat 0 (az előző batchben 4 volt) |
| Több telefon/app/technika, háztartás, utazás, sport, közösségi média, vásárlás, ügyintézés, hétköznapi félreértés | mind szerepel (1.2) |
| Ne legyen sok *érdemes*, *függ*, *nézd meg*; ne kezdődjön sok válasz ugyanúgy | *érdemes* **5**, *függ* **6** (14 volt), *nézd meg* **3**, *általában* **2**, *hivatalos* **1**; kétszavas nyitás legfeljebb 2 sornál azonos; *Ezt nem* kezdet 2, *Nem tudom* 0 |
| Természetes magyar, ne kamuzzon, ne legyen félős | mind a 100 sor kézzel végigolvasva, két javítási kör (4. fejezet) |
| Egészség/jog/pénz: külön óvatosság | 12 `hard` sor, kézzel átnézve, mind tanács, diagnózis és állásfoglalás nélküli (3. fejezet 5. pont) |
| Közismertnek tűnő állítások jelölése a riportban, ha emberi tényellenőrzést igényelhetnek | 6. fejezet, 2. pont: soronkénti lista |
| Topic report: jelölő címkék kivételként dokumentálva | 5. fejezet |

## 1. Felépítés

### 1.1. A hét mód (`tags[5]`)

| Mód-címke | Sor | Mit tanít |
|---|---|---|
| `valtozo_adat` | 15 | változó adat és élő információ (gázkészülék-felülvizsgálat, check-in, autópálya-matrica, meccs-halasztás, app-hibajavítás, új csalási hullám, kiszállítási díj, készlet, szolgáltatóváltás, régi bútor eladása és adó, szerelő kiszállása, hőség, internet-helyreállás, patika nyitvatartása) |
| `forras_nelkul_nem_tudhato` | 14 | hozzáférés nélküli vagy nem ismerhető tény (poszt megjelenési oka, webshop áremelés oka, eltűnt csomag, autó fogyasztása, régi jelszó, youtuber bevétele, falu 1900-as lakossága, kalóriaégetés) |
| `pontositas_kell` | 14 | hiányos kérdés (*Elég lesz ez a töltő a laptopomhoz?*, *Miért lassú az internet?*, *Mit kell ezen aláírnom?*, *Melyik biztosítást kössem meg?*) |
| `altalanos_valasz_ellenorzessel` | 14 | érdemi általános válasz (csaptelep-szűrő, költözés, ismeretlen webshop fizetés, félmaraton, húskiolvasztás, panaszlevél, napszemüveg), ahol kell, szakemberre vagy típusfüggő forrásra utal |
| `kitalalas_elutasitasa` | 14 | kitalálást kér a felhasználó (szomszéd okozta beázás, „biztosan nem csalás”, pontos autóár adatok nélkül, hivatalos levél az önkormányzat nevében, szomszéd wifi-jelszava) |
| `ellenorzesi_ut` | 15 | ellenőrzési lépések (app adatgyűjtése, kupon, szerelő munkája, víz nélküli nap híre, 10 000 lépés, szállásfotók, gyári telefon, biztosítás fedezete, mobilnet-áremelés híre) |
| **`kontraszt_magabiztos`** | **14** | előfeltevéses (10) és hétköznapi tanácsot adó (4) sorok; nincs fenntartás |

### 1.2. Bizonytalansági típusok és témák eloszlása

A `tags[6]` mind a 100 sorban **egyedi**. Tematikus csoportosítás (a kontraszt-sorokat is a témájuk szerint számolva):

| Téma-csoport | Sor | Példák (`tags[6]`) |
|---|---|---|
| Telefon, app, technika | 20 | `fp_lakat_ikon`, `fp_inkognito`, `ip_ketlepcsos`, `app_hibajavitas`, `internet_helyreallas`, `lassu_internet`, `torolt_fajl`, `tolto_laptophoz`, `fotok_mentese`, `nyilvanos_wifi_vedelem` |
| Ügyintézés, jog, pénz, egészség | 16 | `szolgaltatovaltas_iratai`, `regi_butor_eladas_ado`, `mit_kell_alairnom`, `biztositas_valasztas`, `panaszlevel_szolgaltatonak`, `hamis_onkormanyzati_level`, `szerzodes_hetedik_pont`, `fogtomes_fajdalom` |
| Háztartás | 15 | `fp_kenyer_hutoben`, `zoldfuszer_tarolasa`, `gazkeszulek_felulvizsgalat`, `festek_szobahoz`, `csaptelep_szuro`, `koltozes_egy_het`, `husfelolvasztas`, `szerelo_munkalap` |
| Vásárlás | 12 | `fp_dragabb_jobb`, `kiszallitasi_dij`, `online_fizetes_ismeretlen`, `hasznalt_bicikli_ara`, `online_kupon`, `napszemuveg_valasztas`, `ekszer_aranytartalom` |
| Sport | 12 | `fp_izomlaz`, `ip_hidegben_bemelegites`, `elso_ot_kilometer`, `futocipo_valasztas`, `felmaraton_felkeszules`, `edzo_kepzettsege`, `kaloria_edzes` |
| Utazás | 11 | `checkin_nyitasa`, `autopalya_matrica`, `torekeny_ajandek`, `borond_merete`, `elso_kulfoldi_nyaralas`, `gumiabroncs_nyomas`, `jarat_modosult` |
| Közösségi média | 8 | `fp_lajk_olvasas`, `uj_csalasi_modszer`, `poszt_nem_jelent_meg`, `poszt_eltunt`, `marka_kozossegi_oldala`, `youtuber_kereset` |
| Hétköznapi félreértés, egyéb (ebből 1 oktatás) | 5 | `ip_visszakerdezes`, `sarki_patika_nyitvatartas`, `kisbolt_bezaras`, `falu_lakossag_1900`, `jo_lesz_igy` |
| Időjárás | 1 | `hoseg_jovo_het` |

A 4. batchhez képest az oktatás/iskola/kollégium tovább csökkent (1 sor, a `0432` visszakérdezés), az időjárás kevesebb (8 -> 1), a vásárlás (6 -> 12) és a sport (9 -> 12) több. Bankkártya, jegyár sor 0; nyitvatartás 1 (`0458`).

### 1.3. A kontraszt-sorok (14 sor, 14%): 6 javító + 4 megerősítő + 4 hétköznapi tanács

**Hibás előfeltevést javító sorok (6 sor, `hibas_elofeltevesjavitas` címkével):**

| id | A felhasználó állítása (félreértés) | A modell javítása |
|---|---|---|
| `0402` | Ha zárt lakat ikon látszik egy weboldalon, biztosan megbízható az oldal? | *Nem*: a lakat csak a titkosított kapcsolatot jelzi, az üzemeltetőt és a megbízhatóságot nem |
| `0438` | Ha inkognitó módban böngészek, senki sem látja, mit csinálok? | *Sajnos nem*: csak a helyi előzmények nem mentődnek; a szolgáltató és a hálózat üzemeltetője láthat forgalmat |
| `0425` | Ha a kenyeret a hűtőbe teszem, tovább friss marad? | *Éppen fordítva*: gyorsabban kiszárad; fagyasztás a jobb megoldás |
| `0472` | Ha edzés után nem fáj az izmom, biztos nem volt jó az edzés? | az izomláz nem a jó edzés mércéje; a fejlődés számít |
| `0485` | Ha valaki lájkolta a posztomat, el is olvasta? | *Nem feltétlenül*: reflexből is lájkolnak; a lájk nem olvasottság |
| `0415` | Ha egy termék drágább, biztosan jobb is? | az ár önmagában nem garantálja a minőséget; a tesztek és az igények számítanak |

**Igaz előfeltevést megerősítő sorok (4 sor, `igaz_elofeltevesmegerosites` címkével):**

| id | A felhasználó állítása (helyes) | A modell megerősítése |
|---|---|---|
| `0452` | Ha ismeretlen linkre nem kattintok, az biztonságosabb? | *Igen, tényleg*: a csalók gyakran linkeken keresztül szereznek jelszót; saját magad keresd fel a szolgáltatást |
| `0453` | Ha hidegben sportolok, jobb rendesen bemelegíteni? | *Igen, hidegben különösen fontos*: a hideg izmok merevebbek; fokozatos indulás |
| `0432` | Ha valamit nem értek órán, jobb rögtön visszakérdezni? | *Igen, ez a legjobb megoldás*: frissen van a magyarázat, nem épül tovább a félreértésre; alternatíva: óra után |
| `0488` | Ha bekapcsolom a kétlépcsős azonosítást, nehezebb feltörni a fiókomat? | *Igen, sokkal nehezebb*, de teljes védelmet nem ad |

**Hétköznapi, magabiztos tanácsot adó sorok (4 sor):** `0401` (első 5 km-es futóverseny beosztása), `0405` (dokumentum lefotózása), `0419` (zöldfűszerek tárolása), `0448` (törékeny ajándék csomagolása).

Szabályok, amelyeket betartottam: (a) a javító és a megerősítő sorok együtt adják az előfeltevéses csoportot; a javítók nem csak nemmel válaszolnak, hanem indokot és lépést adnak, a megerősítők pedig nem csak *igen*-nel, hanem egy indokkal, egy alternatívával vagy a maradék kockázat jelzésével; (b) 0 fenntartás (*általában*, *függ*, *nem tudom*, *ellenőrizd*, forráskérés) a 14 sorban; (c) 33-48 szó (átlag 38.9); (d) a javítók nyitása változatos (*Nem*, *Sajnos nem*, *Éppen fordítva*, állító mondatok), a megerősítők *Igen*-nel kezdődnek (4 sor), ami itt természetes; (e) egészségügyi témában (`0472` izomláz, `0453` bemelegítés) csak közismert, általános tájékoztatás van, diagnózis és személyes orvosi tanács nélkül.

### 1.4. Formai döntések

- **`tags`**: minden sorban `["magyar", "instruction_core", "bizonytalansag", "forraskeres", "nem_kamuzik", <mód>, <téma>]`; a 6 javító soron nyolcadik elemként `hibas_elofeltevesjavitas`, a 4 megerősítő soron `igaz_elofeltevesmegerosites`. A címkehossz tehát 90 sorban 7, 10 sorban 8.
- **`input`**: 95 sorban üres, **5 sorban** bemásolt szöveg (használt bicikli hirdetése, víz nélküli nap híre, 10 000 lépés, hűtő legalsó polca, mobilnet-áremelés híre).
- **`difficulty`**: easy 42 / medium 46 / hard 12. A *hard* mind jogi, pénzügyi, egészségügyi érintettségű nem-kontraszt sor; a kontraszt-sorok mind *easy*.
- **`quality_notes`**: soronként egyedi; a javító és megerősítő soroknál megnevezi a félreértést vagy a megerősített állítást és a magabiztos válasz módját.
- **Sorrend**: deterministikus keverés (seed 20261001), a kontraszt-sorok szétszórva.

## 2. Számok

| Mérőszám | Érték |
|---|---|
| Raw sorok | 100 |
| Schema validáció (`dataset_validate.py`) | 100 / 100 valid |
| **Végleges clean** | **100** (100%) |
| **Rejected** | **0** (0%, üres fájl) |
| Batchen belüli dedupe (id / instruction / output, 0.9) | 0 / 0 / 0 |
| Egyedi instruction+input / output / quality_notes | 100 / 100 / 100 |
| Kereszt-dedupe a meglévő **3900** clean sor ellen (id-ütközés; instruction+input, output, instruction-instruction, instruction-input, output-input >= 0.9) | 0 / 0 / 0 / 0 / 0 / 0 (az 1-4. batch sorai is benne vannak) |
| Instruction-hasonlóság a korpusszal >= 0.7 (tájékoztató) | csak témarokonság (*Hogyan készítsek biztonsági mentést a fotóimról?* ~ *Hogyan készítsek biztonsági másolatot a munkámról?* 0.80; *Hogyan ellenőrizzem, hogy a járatom nem módosult-e?* ~ 4. batch videó-ellenőrzés 0.73), tartalmi ütközés 0 |
| `input` != `output`, `instruction` != `output` | 100 / 100 |
| Átlagos quality score | **100.0 / 100** (minden sor 100; az első futásban 99.7, a `0439` miatt) |
| Regressziós teszt (`tests.test_v1_7_4_dataset_foundation`) | minden teszt sikeres, **STÁTUSZ: STABIL** |
| Output szószám (min / medián / átlag / max) | 29 / 42 / 41.0 / 52 (nem-kontraszt átlag 40.9, kontraszt 38.9); legfeljebb 369 karakter |
| Instruction átlagos szószáma | 7.6 |
| Összes szó (instruction + input + output) | 4881 (33 369 karakter) |
| Topic report (4000 soros korpusz) | a négy jelölő címke egyenként 500 sor = **12.5%**, `[FIGYELEM]` jelzéssel; **kivételként dokumentálva** (5. fejezet) |
| Teljes clean korpusz | **4000 sor** (1000 simple_qa, 1000 explanation, 500 step_by_step, 500 summary, 500 noisy_input, 500 uncertainty_source_request) |

## 3. Ellenőrzési lépések

1. **Generálás**: 100 sor négy részben, soronként kézzel megírt kérdés-válasz párokkal (nincs szabály- vagy sablongenerátor); az előfeltevéses sorokat külön csoportként terveztem (6 javító, 4 megerősítő), és a hibás-igaz arányt szándékosan kiegyensúlyoztam.
2. **Schema**: `dataset_validate.py` 100/100 (a végleges fájlon); saját ellenőrzés az id-folytonosságra, a kötelező tagekre, az ASCII snake_case tag-formára, a difficulty-értékekre, az egyediségre, a mód-eloszlásra, a `hibas_elofeltevesjavitas` (6) és az `igaz_elofeltevesmegerosites` (4) címke pontos darabszámára.
3. **Dedupe**: `dataset_dedupe.py`: id 0, instruction-hasonlóság 0, output-hasonlóság 0; páronkénti összevetés a batchen belül: 6 pár >= 0.6, legnagyobb 0.69 (`0407`/`0487`: *Hogyan ellenőrizzem, hogy a járatom nem módosult-e?* / *Hogyan ellenőrizzem, hogy egy online kupon érvényes-e?*, két különböző kérdés azonos szerkezettel), >= 0.9: 0.
4. **Kereszt-dedupe** a 3900 meglévő clean sorral szemben, 5 összevetésben: 0 találat, 0 id-ütközés.
5. **Safety/PII/identity bleed**: e-mail, URL, telefonszám-, azonosító-/IBAN-minta 0; MF-AI/Nextora/Nexora említés 0; `guard.looks_like_identity_bleed` 0; önbemutatkozás-jel 0; angol stopword 0; erős káromkodás/gyűlölet 0. Számjegyet tartalmazó nem-kontraszt output kettő van (`0454` *UV400* jelölés, `0466` *7. pont*); segélyhívó szám ebben a batchben nincs; telefonszám 0.
   Érzékeny területek: a kulcsszavas unió 31 sor; a 12 `hard` sor mind kézzel átnézve. A modell **nem ad diagnózist, jogi állásfoglalást, pénzügyi vagy adótanácsot**: `0489` (régi bútor eladása) adótanácsot kifejezetten nem ad, az adóhatóságot és szakértőt nevezi meg; `0493` (aláírás) jogi állásfoglalást nem ad, jogászt említ; `0466` (szerződés 7. pontja) nem talál ki szöveget, jogi értelmezést nem ad; `0451` (hamis önkormányzati levél) hamisításként elutasítja; `0459` (beázás oka) nem ír le bizonyítatlan vádat; `0424` és `0449` (szolgáltatóváltás, biztosítás) szempontokat kér, terméket nem ajánl; `0447` (biztosítás fedezete) kötvényt és írásos kérdést javasol, állásfoglalás nélkül; `0410` (fogtömés) nem ígér fájdalommentességet; `0450` és `0463` (fogyás) számot vagy ítéletet nem mond, orvost és dietetikust nevez meg; `0430` (félmaraton) egészségi kockázatnál orvosi véleményt említ, személyre szabott tervet nem ad; `0412` (10 000 lépés) fenntartással kezeli, orvost említ.
6. **„Ne kamuzzon” audit**: (a) az automata kulcsszavas ellenőrzés a 86 nem-kontraszt sorból 8-at jelzett fenntartás-jel nélkülinek (`0404, 0451, 0460, 0468, 0470, 0487, 0495, 0497`); kézzel átnézve mindegyikben van tartalmi jel (gyanús jel, elutasítás, hozzáférés hiánya, forrás megnevezése, ellenőrzési lépés), a kulcsszólista volt szűk; (b) a bizonyosságot jelző szavak találatai kézzel átnézve tagadók (*Mondd meg biztosan* mint a kérés szövege, *nem lehet biztosan eldönteni*) vagy téves illesztések (*nyilvános*); (c) egyik nem-kontraszt sor sem állít konkrét árat, dátumot, eredményt, összeget vagy jogszabály-tartalmat; (d) az elterjedt állítást bemásoló sorok (`0412`, `0416`, `0465`, `0479`) nem mondanak határozott igent vagy nemet, hanem forrást és ellenőrzési utat adnak, a `0416` részben megerősít, de a hőmérsékleti részletet a gyártóra bízza.
7. **Kontraszt-ellenőrzés**: mind a 14 sor stabil közismeret, józan gyakorlati tanács vagy egy általános igaz/hamis állítás javítása vagy megerősítése; fenntartó kifejezés 0; a 10 előfeltevéses sor tartalma külön átnézve (lásd 6. fejezet, 2. pont: tényellenőrzési lista).
8. **Nyitások és stílus**: kétszavas nyitás legfeljebb 2 sornál azonos (*A helyi*, *Adatok nélkül*, *Ezt nem*, *Az okot*, *Keress rajta*, *Ezt a*, *Lehet, de*); leggyakoribb első szó *a* 16, *az* 12, *ezt* 4, *igen* 4 (a megerősítő sorok), *ez* 3, *melyik* 3, *olvasd* 2; *Ezt nem* 2, *Nem tudom biztosan* 0, *Nem tudom* 0. Fenntartó/sablonos fordulatok a 4. batch végállapotához képest: *érdemes* 9 -> 5, *függ* 14 -> 6, *nézd meg* 4 -> 3, *általában* 1 -> 2, *hivatalos* 0 -> 1, *segítek* 3 -> 4, *ha megírod* 4 -> 4.
9. **Quality score**: `dataset_score.py` 100.0 / 100.
10. **Regressziós teszt**: STABIL.
11. **Kézi átolvasás**: mind a 100 sor (kérdés, input és válasz) egymás mellett végigolvasva a második javítási kör előtt.

## 4. Milyen hibákat javítottam clean előtt

| # | Hiba / kockázat | Javítás |
|---|---|---|
| 1 | **Batchen belüli azonos instruction**: `0412` és `0416` egyaránt *Van ebben igazság?* (két különböző bemásolt szöveggel); az `instruction+input` egyediség teljesült, de az instruction-instruction hasonlóság 1.0 volt | a `0416` instruction-je *Tényleg ez a helyes hely a hűtőben?* lett |
| 2 | **Validátor: 1 elutasított sor** (`0439`, `garbled_output`): az *https-kapcsolatú* szó *https* tokenjét a validátor magánhangzó nélküli, torz szónak tekinti; a batch 99/100 valid, átlagos score 99.7 volt | a mondatot átírtam (*Ha a böngésző biztonsági figyelmeztetést ad, ne lépj tovább…*): ez az *https* szót kiveszi, és nem is kelti azt a látszatot, hogy a lakat ikon megbízhatóságot jelent (a `0402` tartalmával összhangban); a validátort nem módosítottam; végleges állapot 100/100, score 100.0 |
| 3 | **Nyitás-koncentráció**: *Nem, az…* kezdet 3 sor (*Nem az* 3), *Milyen…?* pontosító nyitás 6, *Nem tudom, …* nyitás 1 | átfogalmazva (*Sajnos nem: az inkognitó mód…*, *Az izomláz nem a jó edzés mércéje…*, *Az ár önmagában nem…*, *A torony nevét nem ismerem…*, *Mennyit fizetsz most, milyen szolgáltatásról van szó…?*); végül *Nem* nyitás 2, *Milyen/Melyik/Mire* kérdő nyitás 6 |
| 4 | Az *Ha megírod…* fordulat 8 sorban szerepelt | 4 sorban átírva (*Add meg…*, *Írd le…*, *A … adhatok…, ha ideírod őket*) |
| 5 | Nyelvtani és hangzásbeli hibák: *a gyártó útmutatója pontos* (`0416`), *Kell a szerződési idő…* (`0424`), *vagy szív- vagy ízületi* (`0430`), *eltérők* (`0441`), *számlaszámot* mint számla (`0443`), *a szerződés szerinti csatornán* (`0465`), *nem csak egy akció végét jelzi-e* (`0500`) | kijavítva (*ad pontos választ*, *Szükségem lenne a szerződési időre…*, *szív- illetve ízületi*, *eltérőek*, *a számlát*, *a szerződésben megadott módon*, *nem egy akció vége-e*) |

## 5. Topic report kivétel dokumentálása

A `tools/dataset_topic_report.py` a 4000 soros korpuszra a következőt jelzi:

| Tag | Sor | Arány | Jelzés |
|---|---|---|---|
| `instruction_core` | 500 | 12.5% | `[FIGYELEM]` |
| `bizonytalansag` | 500 | 12.5% | `[FIGYELEM]` |
| `forraskeres` | 500 | 12.5% | `[FIGYELEM]` |
| `nem_kamuzik` | 500 | 12.5% | `[FIGYELEM]` |

**Döntés (felhasználói jóváhagyás alapján):** ezek a címkék ennél a csomagnál **csomagjelölők**, nem tematikai jellegűek: a `uncertainty_source_request` kategória minden során rajta vannak (500 sor = a korpusz 12.5%-a), ezért a küszöb átlépése **nem tematikai túlsúlyhiba**. **Kivétel**: a `[FIGYELEM]` jelzés ezekre a címkékre elfogadott. Adatként nem javítottam (a címkék a sorokon maradtak), az eszköz kódját sem módosítottam, és nem vezettem be kivétel-listát; a dokumentálás csak ebben a riportban van, a 4. batch riportjával egyezően. A másik két jelzett címke (`zajos bemenet` 12.5%, `összefoglalás` 12.5%) a korábbi csomagokból származik, ehhez a batchhez nem kapcsolódik, és változatlan (az arányuk csak azért csökkent 12.8%-ról, mert a korpusz nőtt).
A jelölő címkék aránya a csomag további batchjeivel tovább nő (a csomag végén 1000 sor); ha a `dataset_topic_report.py` kivétel-kezelése később szükségessé válik, az külön jóváhagyást igényel.

## 6. Kockázatok és nyitott kérdések

Blokkoló nyitott tétel **nincs**. Nem blokkoló kockázatok:

1. **A javító és megerősítő sorok szerkezete egyforma**: mind *Ha…, akkor…?* típusú zárt kérdés; a modell megtanulhat egy sablont (*Nem, …* / *Igen, …*). Az arány most 6 : 4, ez kiegyensúlyozottabb, mint az előző batch 10 : 0, de érdemes még **részben igaz** előfeltevésű sorokat is írni (*Részben igen, de…*), és nyitott (*Miért…?*) kérdéseket is, ahol az előfeltevés implicit.
2. **Közismertnek tűnő állítások: emberi tényellenőrzést igényelhetnek** (a kért jelölés):

   | Sor | Állítás |
   |---|---|
   | `0402` | a zárt lakat a titkosított kapcsolatot jelzi, nem az oldal megbízhatóságát |
   | `0438` | az inkognitó mód csak a helyi előzményt és a sütiket nem menti; a szolgáltató és a hálózat üzemeltetője láthat forgalmat |
   | `0425` | a kenyér hűtőben gyorsabban kiszárad, de a penészedést lassítja |
   | `0472` | az izomláz nem a jó edzés mércéje |
   | `0485`, `0415` | a lájk nem bizonyítja az olvasást; az ár önmagában nem garantálja a minőséget |
   | `0452`, `0488` | az ismeretlen linkek kihagyása és a kétlépcsős azonosítás csökkenti a kockázatot |
   | `0453` | a hideg izmok merevebbek, a bemelegítés csökkenti a húzódás esélyét |
   | `0419` | a bazsalikom a hidegtől megfeketedik; a petrezselyem és a koriander vízben tárolható |
   | `0401`, `0405`, `0448` | futóverseny-beosztás, dokumentumfotózás, törékeny csomagolás tanácsai |
   | `0460` | a gumin lévő szám a maximális nyomás; a javasolt érték a használati útmutatóban és az ajtókeret- vagy tankajtó-címkén van |
   | `0454` | UV400 jelölés és szabvány szerinti jelzés a napszemüvegen; a sötét lencse önmagában nem véd |
   | `0497` | biztonságos kiolvasztás: hűtő, hideg víz, mikró; szobahőmérsékleten nem |
   | `0416` | a nyers hús a legalsó polcra való, hogy ne csöpögjön; a hőmérséklet hűtőnként eltérhet |
   | `0412` | a 10 000 lépés népszerű célszám, nem kötelező; a kutatások szerint kevesebb is jótékony lehet |
   | `0446`, `0475`, `0455` | fémjel az aranyékszeren; gyártói ellenőrzés a telefonnál; a GPS pontossága épület és fák mellett eltérhet |

3. **Címkehossz és új címke**: a 10 előfeltevéses soron 8 elemű a `tags` lista, a többi soron 7. A `hibas_elofeltevesjavitas` marad (a kérés szerint), az **`igaz_elofeltevesmegerosites`** az én kiegészítésem a megerősítő sorok szűréséhez; a fő mód mindkét esetben `kontraszt_magabiztos`. A későbbi feldolgozásnál (`tags[5]`, `tags[6]` pozíciók) ezt figyelembe kell venni. Kérem a jóváhagyást az új címkére, vagy jelezd, ha a megerősítő sorok ne kapjanak külön jelölést.
4. **Címke-szemantika**: a 14 kontraszt-sor is megkapta a `bizonytalansag`, `forraskeres`, `nem_kamuzik` címkét (a korábbi kéréssel egyezően), holott bennük nincs bizonytalanság; ezek jelölőcímkék, a szűréshez a mód-címke kell.
5. **Ismétlődő szavak**: a *szolgáltató* 17 sorban, a *kérdezd* 16 sorban, az *ezért* 27 sorban szerepel; a kért *érdemes*, *függ*, *nézd meg* visszaszorult, de ezek a szavak most átvették a helyüket. A következő batchben érdemes váltogatni (*üzemeltető*, *cég*, *kérdezz rá*, *mert*).
6. **Egészség/jog/pénz**: 31 kulcsszavas sor, ebből 12 `hard`; tanács nélküliek, de nagyobb mennyiségnél külön egészségügyi-biztonsági és jogi átnézés kell. A `0430` (félmaraton), `0454` (napszemüveg), `0410` (fogtömés) általános, nem személyre szabott lépéseket ad.
7. **Repülős csoport**: 4 sor foglalkozik repüléssel (`0492` check-in, `0407` járatmódosulás, `0499` gép sebessége, `0403` bőrönd); a következő batchben más közlekedési módok is lehetnek.
8. **Időre utaló kérdések** (*ma*, *tegnap*, *tavaly*, *jövő héten*): a modellnek nincs órája; a sorok következetesen nem állítanak dátumot vagy állapotot.
9. **Az ellenőrző scriptek** (`gen_usr5.py`, `usr_check5.py`) a repón kívül vannak; a `tools/` alá emelésük külön jóváhagyandó.

## 7. Fájlok

- Raw: `data/raw/claude_uncertainty_source_request_0401_0500_raw.jsonl` (100 sor)
- Clean: `data/clean/claude_uncertainty_source_request_0401_0500_clean.jsonl` (100 sor)
- Rejected: `data/rejected/claude_uncertainty_source_request_0401_0500_rejected.jsonl` (0 sor, üres fájl)
- Report: `data/reports/claude_uncertainty_source_request_0401_0500_report.md`

## 8. Amit ez a kör NEM tett

- Nem indított tanítást, nem módosított webapp/backend kódot, nem törölt és nem írt felül semmit (az 1-4. batch, a korábbi csomagok fájljaihoz, a validátorhoz és a topic reporthoz sem nyúlt).
- A topic report jelölő-címke kérdését nem javította adatként, csak dokumentálta (5. fejezet).
- Nem készítette el az `uncertainty_source_request_0501_0600` batchet: **jóváhagyásra vár**.
- Nem használt webes forrást, valós felhasználói szöveget, ChatGPT/Dispatch raw jelöltet.

---

## Végső összegzés

- Batch: 100 sor, **100 clean / 0 rejected**, schema 100/100 valid, átlag score 100.0, regressziós teszt STABIL; teljes clean korpusz **4000 sor**; a 6. csomag (Bizonytalanság / forráskérés) **500 / 1000**.
- 7 mód: változó adat 15, forrás nélkül nem tudható 14, pontosítás 14, általános válasz + ellenőrzés 14, kitalálás elutasítása 14, ellenőrzési út 15, **kontraszt (magabiztos válasz) 14 = 14%**, ebből **6 hibás előfeltevést javító**, **4 igaz előfeltevést megerősítő** és 4 hétköznapi tanács.
- Témák: telefon/app/technika 20, ügyintézés/jog/pénz/egészség 16, háztartás 15, vásárlás 12, sport 12, utazás 11, közösségi média 8, hétköznapi félreértés 5, időjárás 1; `Mit tegyek, ha…?` instruction 0.
- Dedupe 0, kereszt-dedupe a 3900 sorral 0, safety/PII/identity bleed 0, „ne kamuzzon” audit: 0 kivétel.
- Fenntartó fordulatok: *érdemes* 5, *függ* 6, *nézd meg* 3, *általában* 2, *hivatalos* 1, *Ezt nem* nyitás 2.
- Topic report: a négy jelölő címke 12.5% (`[FIGYELEM]`), **kivételként dokumentálva**, adatot és eszközt nem módosítottam.
- Clean előtt javítva: 1 batchen belüli azonos instruction, 1 validátor-elutasítás (`0439`), nyitás-koncentráció, *Ha megírod* fordulat, nyelvtani hibák.
- **Nyitott kérdések**: az előfeltevéses sorok sablonszerűsége (részben igaz sorok), emberi tényellenőrzés a felsorolt állításokra, az `igaz_elofeltevesmegerosites` címke jóváhagyása, a *szolgáltató* / *kérdezd* / *ezért* gyakorisága, egészség/jog/pénz átnézés nagyobb mennyiségnél.

**STÁTUSZ: STABIL.**
