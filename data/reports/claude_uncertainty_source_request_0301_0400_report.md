# Negyedik uncertainty_source_request batch - uncertainty_source_request_0301-0400

**Verdikt: STABIL.** 100 sor, **100 clean / 0 rejected**, `category: uncertainty_source_request`, a **6. csomag (Bizonytalanság / forráskérés)** negyedik batchje az új, bővített 17 000 soros `instruction_core`-ban. A csomag célmérete **1000 sor**, ezzel **400 / 1000** kész.
A batch célja: a modell ne találjon ki választ, ha nem biztos, **de ne is legyen feleslegesen félős**. Új ebben a batchben: (1) **14 kontraszt-sor, ebből 10 hibás előfeltevést javító** (a felhasználó egy valószínű félreértést állít, a modell magabiztosan és udvariasan javítja), (2) sokkal kevesebb oktatási/iskolai téma (35 -> 1), (3) új és bővített tématerületek: háztartás, utazás, időjárás, sport, telefon/app, közösségi média, vásárlás, ügyintézés, hétköznapi félreértések, egyszerű technikai kérdések.

> **Számozás**: 6. csomag = Bizonytalanság / forráskérés, cél 1000 sor; a régi 4900 soros roadmap számozása nem irányadó. Állás a batch után: **400 / 1000**.
> **Mód-címke**: a kontraszt-sorok szűrő-címkéje a korábbi batchekkel egyezően **`kontraszt_magabiztos`** (a kérésben `contrast_magabiztos` szerepelt; a meglévő, már commitolt címkét tartottam meg, hogy a szűrés az 1-3. batchre is egységes maradjon).

## 0. A kérés követelményei és teljesülésük

| Követelmény | Teljesülés |
|---|---|
| 100 sor, magyar, `uncertainty_source_request`, id `0301`-`0400` | 100 sor, folytonos id-k, `source: synthetic_claude_magyar`, a meglévő 9 mezős séma |
| 100/100 valid, 100/100 clean, 0 rejected | **100 / 100 valid, 100 clean, 0 rejected** |
| 0 batchen belüli duplikátum, 0 kereszt-dedupe találat | 0 / 0 (2. fejezet); az első futás **4 találatot** adott a `simple_qa` sorokkal (2 pontos egyezés, 2 >= 0.9), ezeket clean előtt javítottam (4. fejezet, 1. pont) |
| 0 PII/URL/e-mail/telefonszám, 0 MF-AI/Nextora, 0 identity bleed, 0 erős káromkodás | mind 0 (3. fejezet 5. pont) |
| Regressziós teszt STABIL | minden teszt sikeres, **STÁTUSZ: STABIL** |
| 10-15% kontraszt-sor | **14 sor = 14%** (`kontraszt_magabiztos`) |
| 8-12 hibás előfeltevést javító kontraszt-sor | **10 sor** (a `tags` végén `hibas_elofeltevesjavitas` címkével, 1.3) |
| A hibás előfeltevésnél magabiztos, udvarias javítás, nincs felesleges bizonytalanság | mind a 10 sor kimondja a helyes választ (*Dehogy*, *De lehet*, vagy állító mondat), 0 fenntartó kifejezés a 14 kontraszt-sorban |
| A többi sor bizonytalanság / forráskérés | 86 sor, 6 mód (15 / 14 / 14 / 14 / 14 / 15) |
| Kevesebb oktatás/iskola/kollégium | **1 sor** (`0389`, tanulási nap; az előző batchben 35), iskolai/kollégiumi ügy 0 |
| Új témák: háztartás, utazás, időjárás, sport, telefon/app, közösségi média, vásárlás, ügyintézés, hétköznapi félreértések, egyszerű technikai kérdések | mind szerepel (1.2) |
| Ne legyen sok *hivatalos*, *általában*, *nézd meg*; ne kezdődjön sok válasz ugyanúgy | *hivatalos* **0** (14 -> 0), *általában* **1**, *nézd meg* **4**; kétszavas nyitás legfeljebb 2 sornál azonos; *Ezt nem* kezdet 1, *Nem tudom biztosan* 0 |
| Természetes magyar, ne kamuzzon, ne legyen félős | mind a 100 sor kézzel végigolvasva, két javítási kör (4. fejezet) |
| Egészség/jog/pénz: külön óvatosság | 14 `hard` sor, kézzel átnézve, mind tanács, diagnózis és állásfoglalás nélküli (3. fejezet 5. pont) |
| Topic report 8%-os kérdés: jelölő címkék, kivételként dokumentálni, adatot nem javítani | 5. fejezet: **kivételként dokumentálva**, az adat és az eszköz változatlan |

## 1. Felépítés

### 1.1. A hét mód (`tags[5]`)

| Mód-címke | Sor | Mit tanít |
|---|---|---|
| `valtozo_adat` | 15 | változó adat (kéményseprő, vízdíj, oltás, komp, hidegfront, pollen, futóverseny, meccsközvetítés, új funkció, app-árazás, felhasználási feltételek, törzsvásárlói kedvezmény, szemétdíj-határidő, gépjárműadó, telefon-támogatás) |
| `forras_nelkul_nem_tudhato` | 14 | hozzáférés nélküli, magánjellegű vagy jövőbeli tény (profillátogatók, törölt üzenet, számla, akkumulátor élettartama, lakáseladás időzítése) |
| `pontositas_kell` | 14 | hiányos kérdés (*Hogyan telepítsem ezt a programot?*, *Milyen az idő ott?*, *Jó lesz így?*, *Hogyan spóroljak többet?*) |
| `altalanos_valasz_ellenorzessel` | 14 | érdemi általános válasz (vízkő, csöpögő csap, vihar, futás kezdése, elázott telefon, kölcsön barátnak), ahol kell, szakemberre vagy típusfüggő forrásra utal |
| `kitalalas_elutasitasa` | 14 | kitalálást kér a felhasználó (mm-pontos csapadék, alaptalan vád, hibakód, pénz megduplázása, diagnózis, jogi bizonyosság) |
| `ellenorzesi_ut` | 15 | ellenőrzési lépések (telefonvírus, nyereményjáték, használt telefon, szállásfoglalás, vihar-hír, étrend-kiegészítő, akciós ár, videó, tartozás-állítás, kávé-tévhit) |
| **`kontraszt_magabiztos`** | **14** | stabil tudás vagy hibás előfeltevés magabiztos javítása; nincs fenntartás |

### 1.2. Bizonytalansági típusok és témák eloszlása

A `tags[6]` mind a 100 sorban **egyedi**. Tematikus csoportosítás (a kontraszt-sorokat is a témájuk szerint számolva):

| Téma-csoport | Sor | Példák (`tags[6]`) |
|---|---|---|
| Telefon, app, egyszerű technikai kérdések | 20 | `uj_funkcio_frissites`, `telefon_tamogatas_ideje`, `fp_app_torles`, `fp_lemerult_kepek`, `fp_wifi_internet`, `lefagy_a_szamitogep`, `elazott_telefon`, `melyik_kabel`, `wifi_masok_hasznaljak` |
| Háztartás | 17 | `kemenysepro_idopont`, `vizdij_telepules`, `vizko_eltavolitas`, `csepeg_a_csap`, `penesz_megelozese`, `fp_tobb_mosogatoszer`, `szellozes_telen`, `folt_kimosasa` |
| Ügyintézés, jog, pénz, egészség | 15 | `gepjarmuado_osszeg`, `hova_kell_beadni`, `jogilag_nekem_igazam`, `kolcson_baratnak`, `megdupla_penz`, `kiutes_allergia`, `etrend_kiegeszito`, `tartozas_lakas_elvitel` |
| Utazás | 11 | `utazasi_oltas`, `komp_menetrend`, `gyogyszer_kulfoldre`, `hosszu_autout`, `fp_kulfoldi_wifi`, `szallasfoglalas_megvan`, `autokolcsonzo_megbizhatosag` |
| Sport | 9 | `futoverseny_varos`, `meccs_kozvetites_kezdes`, `jatekos_golok`, `fp_futas_hideg`, `futas_kezdes`, `sportcipo_probalas` |
| Időjárás | 8 | `hidegfront_erkezes`, `pollenszam_ma`, `vihar_szabadban`, `fp_felhos_leegeses`, `eso_millimeter`, `vihar_hir_tuloz` |
| Közösségi média | 8 | `felhasznalasi_feltetelek`, `profilnezok`, `atvett_kozossegi_fiok`, `nyeremenyjatek`, `video_atszerkesztve` |
| Vásárlás | 6 | `torzsvasarloi_kedvezmeny`, `matrac_valasztas`, `erdemes_megvenni_vizforralo`, `akcios_ar_valodi` |
| Hétköznapi félreértések és egyéb | 5 | `fp_valasz_haragszik`, `sok_feladat`, `jo_lesz_igy`, `recept_megbizhatosag`, `foter_tervezoje` |
| Oktatás | 1 | `fp_elrontott_nap` |

Az 1-3. batchhez képest eltűnt az iskolai/kollégiumi ügyek dominanciája (35 -> 1), és megjelent a háztartás, a technikai hibák és az utazás. Bankkártya, jegyár, nyitvatartás sor 0.

### 1.3. A kontraszt-sorok (14 sor, 14%), ebből 10 hibás előfeltevést javító

**Hibás előfeltevést javító kontraszt-sorok (10 sor, `hibas_elofeltevesjavitas` címkével):**

| id | A felhasználó állítása (félreértés) | A modell javítása |
|---|---|---|
| `0368` | Ha kikapcsolom a wifit, az internet is megszűnik a világon? | *Dehogy*: csak a saját eszköz veszíti el a helyi kapcsolatot; a mobiladat működik |
| `0319` | Ha törlök egy appot, a telefonom is elromlik? | nem romlik el, helyet szabadít fel; kivétel: a rendszeralkalmazások |
| `0389` | Ha elrontok egy tanulási napot, már nincs értelme folytatni? | *Dehogynem*: egy nap semmit sem dönt el; kisebb feladat másnapra |
| `0382` | Ha valaki nem válaszol azonnal, biztos haragszik? | ebből még nem következik; hétköznapi okok, barátságos üzenet |
| `0328` | Ha hidegben futok, biztosan beteg leszek? | a hideg önmagában nem tesz beteggé, a megfázást vírusok okozzák; réteges ruha, kihűlés esetén melegre menni |
| `0381` | Ha lemerül a telefonom, a képeim is eltűnnek? | a fotók a tárhelyen maradnak; időnkénti mentés mint plusz biztonság |
| `0388` | Ha felhős az ég, nem lehet leégni? | *De lehet*: a felhők az UV-sugárzás jelentős részét átengedik |
| `0303` | Ha több mosogatószert teszek a gépbe, tisztább lesz az edény? | nem, lerakódás és foltok; a csomagolás szerinti adag |
| `0372` | Ha elfelejtettem a jelszavamat, új fiókot kell csinálnom? | nem, jelszó-visszaállítás van; a régi adatok megmaradnak |
| `0375` | Ha külföldön vagyok, a telefonom nem tud wifire csatlakozni? | *Dehogynem*: wifihez nem kell hazai hálózat; a mobiladat és a hívás díja más lehet |

**Hétköznapi, magabiztos tanácsot adó kontraszt-sorok (4 sor):** `0379` (téli szellőztetés), `0347` (hűtő ajtaja), `0364` (sportcipő próbálása), `0324` (sok feladat egyszerre).

Szabályok, amelyeket betartottam: (a) csak stabil, közismert tényről vagy józan gyakorlati tanácsról van szó; (b) a javítás udvarias és magyarázó (*Dehogy…*, *Ebből még nem következik…*, *De lehet…*), nem kioktató; (c) a válasz nem marad a puszta tagadásnál, mindig ad egy indokot és egy gyakorlati lépést vagy megjegyzést; (d) 0 fenntartás (*általában*, *függ*, *nem tudom*, *ellenőrizd*, forráskérés); (e) 30-49 szó (átlag 39.1), mind összetettebb, mint egy rövid definíció; (f) egészségügyi témában (`0328` hideg, `0388` UV) csak közismert, általános tájékoztatás van, diagnózis és személyes orvosi tanács nélkül, a `0328` kihűlés esetén melegre menést javasol.

### 1.4. Formai döntések

- **`tags`**: minden sorban `["magyar", "instruction_core", "bizonytalansag", "forraskeres", "nem_kamuzik", <mód>, <téma>]`; a 10 hibás előfeltevést javító soron egy nyolcadik elem: `hibas_elofeltevesjavitas`. (A címkehossz tehát 90 sorban 7, 10 sorban 8; a validátor és a topic report mindkettőt kezeli.)
- **`input`**: 95 sorban üres, **5 sorban** bemásolt szöveg (vízforraló-ajánlat, nyereményjáték, vihar-hír, tartozás-állítás, kávé-tévhit); kontraszt-sorban most nincs bemásolt szöveg.
- **`difficulty`**: easy 50 / medium 36 / hard 14. A *hard* mind a jogi, pénzügyi, egészségügyi érintettségű nem-kontraszt sor; a kontraszt-sorok mind *easy*.
- **`quality_notes`**: soronként egyedi; a hibás előfeltevés soroknál megnevezi a félreértést és a javítás módját.
- **Sorrend**: deterministikus keverés (seed 20260930), a kontraszt-sorok szétszórva.

## 2. Számok

| Mérőszám | Érték |
|---|---|
| Raw sorok | 100 |
| Schema validáció (`dataset_validate.py`) | 100 / 100 valid |
| **Végleges clean** | **100** (100%) |
| **Rejected** | **0** (0%, üres fájl) |
| Batchen belüli dedupe (id / instruction / output, 0.9) | 0 / 0 / 0 |
| Egyedi instruction+input / output / quality_notes | 100 / 100 / 100 |
| Kereszt-dedupe a meglévő **3800** clean sor ellen (id-ütközés; instruction+input, output, instruction-instruction, instruction-input, output-input >= 0.9) | 0 / 0 / 0 / 0 / 0 / 0 (az 1-3. batch sorai is benne vannak) |
| Instruction-hasonlóság a korpusszal >= 0.7 (tájékoztató) | csak sablon-hasonlóság (*Mit tegyek, ha elázott a telefonom?* ~ *Mit tegyek, ha lassú a telefon?*), tartalmi ütközés 0 |
| `input` != `output`, `instruction` != `output` | 100 / 100 |
| Átlagos quality score | **100.0 / 100** (minden sor 100) |
| Regressziós teszt (`tests.test_v1_7_4_dataset_foundation`) | minden teszt sikeres, **STÁTUSZ: STABIL** |
| Output szószám (min / medián / átlag / max) | 25 / 40 / 40.4 / 58 (nem-kontraszt átlag 40.0, kontraszt 39.1); legfeljebb 409 karakter |
| Instruction átlagos szószáma | 7.3 |
| Összes szó (instruction + input + output) | 4785 (32 240 karakter) |
| Topic report (3900 soros korpusz) | a négy jelölő címke egyenként 400 sor = **10.3%**, `[FIGYELEM]` jelzéssel; **kivételként dokumentálva** (5. fejezet) |
| Teljes clean korpusz | **3900 sor** (1000 simple_qa, 1000 explanation, 500 step_by_step, 500 summary, 500 noisy_input, 400 uncertainty_source_request) |

## 3. Ellenőrzési lépések

1. **Generálás**: 100 sor négy részben, soronként kézzel megírt kérdés-válasz párokkal (nincs szabály- vagy sablongenerátor); a hibás előfeltevés sorokat külön csoportként terveztem és írtam meg.
2. **Schema**: `dataset_validate.py` 100/100; saját ellenőrzés az id-folytonosságra, a kötelező tagekre, az ASCII snake_case tag-formára, a difficulty-értékekre, az egyediségre, a mód-eloszlásra és a `hibas_elofeltevesjavitas` címke pontosan 10 sorra.
3. **Dedupe**: `dataset_dedupe.py`: id 0, instruction-hasonlóság 0, output-hasonlóság 0; páronkénti összevetés a batchen belül: 13 pár >= 0.6, legnagyobb 0.71 (`0318`/`0362`: *Melyik nyaralóhelyet válasszam?* / *Melyik sportot válasszam?*, két különböző kérdés azonos szerkezettel), >= 0.9: 0.
4. **Kereszt-dedupe** a 3800 meglévő clean sorral szemben, 5 összevetésben: a végleges állapotban 0 találat, 0 id-ütközés.
5. **Safety/PII/identity bleed**: e-mail, URL, telefonszám-, azonosító-/IBAN-minta 0; MF-AI/Nextora/Nexora említés 0; `guard.looks_like_identity_bleed` 0; önbemutatkozás-jel 0; angol stopword 0; erős káromkodás/gyűlölet 0. Számjegyet tartalmazó output kettő van (*112* a `0358` viharnál és a `0398` kiütésnél); telefonszám 0.
   Érzékeny területek: a kulcsszavas unió 28 sor; a 14 `hard` sor mind kézzel átnézve. A modell **nem ad diagnózist, jogi állásfoglalást, pénzügyi tanácsot vagy adagolást**: `0398` (kiütés) kimondja, hogy az okot innen nem tudja megállapítani, riasztó jelekre orvost és 112-t nevez meg; `0304` (*jogilag biztosan nekem van igazam*) jogi bizonyosságot nem állít, jogászt és kérdéslistát ajánl; `0363` (pénz megduplázása) kimondja, hogy nincs ilyen biztos mód, a csalás kockázatára figyelmeztet; `0308` (lakáseladás időzítése) nem jósol, szakértőt jelöl; `0330` (kölcsön barátnak) általános elvek jogi és adózási tanács nélkül; `0390` (spórolás) rákérdez, személyre szabott pénzügyi tanácsot kifejezetten nem ad; `0371` (tartozás) nem erősít meg és nem cáfol, jogi segítséget és írásos tájékoztatót ajánl; `0349` (étrend-kiegészítő) szempontokat ad, biztonságosságot nem állít, kölcsönhatásnál orvost és gyógyszerészt említ; `0400` (gyógyszer külföldre) nem mond szabályt, az orvost és a célország előírásait nevezi meg; `0339` (utazási oltás) nem nevez meg oltást, szakembert és hatósági tájékoztatót jelöl; `0334` (futás kezdése) és `0362` (sportválasztás) egészségi kockázatnál orvost említ.
6. **„Ne kamuzzon” audit**: (a) az automata kulcsszavas ellenőrzés a 86 nem-kontraszt sorból 12-t jelzett fenntartás-jel nélkülinek (`0306, 0307, 0313, 0337, 0342, 0346, 0353, 0358, 0366, 0386, 0387, 0393`); kézzel átnézve mindegyikben van tartalmi jel (elutasítás, hozzáférés hiánya, típusfüggés, gyanús jel, ellenőrzési lépés), a kulcsszólista volt szűk; (b) a bizonyosságot jelző szavak találatai kézzel átnézve tagadók vagy téves illesztések (*nyilvános*, *mindig* mint *nem mindig pontosak*); (c) egyik nem-kontraszt sor sem állít konkrét árat, dátumot, eredményt, összeget vagy jogszabály-tartalmat; (d) a fenntartással kezelt elterjedt állítás (`0385` kávé) nem mond igent vagy nemet, hanem forrástípust ad, a `0371` pedig nem erősíti meg a tartozás-állítást.
7. **Kontraszt-ellenőrzés**: mind a 14 sor stabil közismeret vagy józan gyakorlati tanács; fenntartó kifejezés 0; a 10 hibás előfeltevés helyes javítása külön átnézve (lásd 6. fejezet, 2. pont: tényellenőrzés).
8. **Nyitások és stílus**: kétszavas nyitás legfeljebb 2 sornál azonos (*Kérd el*, *Erről nincs*, *A mai*, *Nézd át*, *Azt nem*); leggyakoribb első szó *a* 16, *az* 7, *mit* 4, *ez* 4, *ezt* 3, *melyik* 3, *olvasd* 3; *Ezt nem* 1 (első vázlatban 7), *Nem tudom biztosan* 0, *Nem tudom* 0. A hibás előfeltevés sorok nyitása változatos (*Dehogy…*, *Dehogynem…*, *De lehet…*, *Nem, a legtöbb…*, állító mondatok). Fenntartó/sablonos fordulatok a 3. batch végállapotához képest: *általában* 1 -> 1, *nézd meg* 3 -> 4, *hivatalos* 14 -> 0, *érdemes* 5 -> 9, *segítek* 3 -> 3, *függ* 15 -> 14.
9. **Quality score**: `dataset_score.py` 100.0 / 100.
10. **Regressziós teszt**: STABIL.
11. **Kézi átolvasás**: mind a 100 sor (kérdés, input és válasz) egymás mellett végigolvasva a második javítási kör előtt.

## 4. Milyen hibákat javítottam clean előtt

| # | Hiba / kockázat | Javítás |
|---|---|---|
| 1 | **Kereszt-dedupe: 4 találat a `simple_qa` sorokkal**: *Hogyan kezdjek el futni?* (`simple_qa_0281`, 1.0), *Mit tegyek, ha csöpög a csap?* (`simple_qa_0206`, 1.0), *Hogyan készüljek fel egy hosszú autóútra?* (`simple_qa_0353`, 0.94), *Mit tegyek, ha lefagy a számítógép?* (`simple_qa_0172`, 0.91) | átfogalmazva, konkrétabban: *Hogyan kezdjek futni, ha hosszú ideje nem mozogtam?*, *Csöpög a fürdőszobai csap, mit lehet vele kezdeni?*, *Mire készüljek fel egy hosszabb autós utazás előtt?*, *Lefagyott a gépem, mit lehet ilyenkor csinálni?* |
| 2 | **Nyitás-koncentráció** az első vázlatban: *Ezt nem…* 7 sor, a hibás előfeltevés sorok közül 7 kezdődött *Nem, …*-mel | 7 *Ezt nem* nyitás átfogalmazva (pl. *A profilod látogatóit én nem látom…*, *Az akkumulátor élettartamát előre nem lehet megmondani…*, *Megerősíteni nem tudom…*); a hibás előfeltevés sorok nyitása változatossá téve (*Dehogy*, *Dehogynem*, *De lehet*, állító mondatok); végül *Ezt nem* 1, *Nem, …* 1 |
| 3 | Nyelvtani és hangzásbeli hibák: *Nem látok a lakásodba* (`0348`), *más forrásokat is átolvashatsz* (`0314`), *Azt nem látom, ami a képernyődön van* (`0357`), *Ezt nem írom le, mert nem tudom igazolni…* (kényszeredett szerkezet, `0384`) | kijavítva (*Nem látok be a lakásodba*, *még más forrásokat is érdemes átnézni*, *mi van a képernyődön*, *Tartósságot nem tudok igazolni, ezért nem írom le a hirdetésbe: a megalapozatlan ígéret megtévesztheti a vevőt.*) |
| 4 | A **`hivatalos`** szó az előző batchben 14 sorban szerepelt | 0 sorra visszaszorítva (saját oldala, szolgáltató, hatóság, kiíró, közzétett) |
| 5 | Az *érdemes* szó 9 sorban maradt (5-ről nőtt) | a szó eloszlásából adódik (tanácsadó sorok); nem javítottam tovább, a nyitott kockázatok között szerepel |

## 5. Topic report kivétel dokumentálása

A `tools/dataset_topic_report.py` a 3900 soros korpuszra a következőt jelzi:

| Tag | Sor | Arány | Jelzés |
|---|---|---|---|
| `instruction_core` | 400 | 10.3% | `[FIGYELEM]` |
| `bizonytalansag` | 400 | 10.3% | `[FIGYELEM]` |
| `forraskeres` | 400 | 10.3% | `[FIGYELEM]` |
| `nem_kamuzik` | 400 | 10.3% | `[FIGYELEM]` |

**Döntés (felhasználói jóváhagyás alapján):** ezek a címkék ennél a csomagnál **csomagjelölők**, nem tematikai jellegűek: a `uncertainty_source_request` kategória minden során rajta vannak (400 sor = a korpusz 10.3%-a), ezért a küszöb átlépése **nem tematikai túlsúlyhiba**. **Kivétel**: a `[FIGYELEM]` jelzés ezekre a címkékre elfogadott. Adatként nem javítottam (a címkék a sorokon maradtak), az eszköz kódját sem módosítottam, és nem vezettem be kivétel-listát; a dokumentálás csak ebben a riportban van. A két másik jelzett címke (`zajos bemenet` 12.8%, `összefoglalás` 12.8%) a korábbi csomagokból származik, ehhez a batchhez nem kapcsolódik, és változatlan.
A jelölő címkék aránya a korpusz növekedésével a 17 000 soros core végén is a csomag méretétől függ; ha a `dataset_topic_report.py` kivétel-kezelése később szükségessé válik (például címkefelsorolás a küszöb alól), az külön jóváhagyást igényel.

## 6. Kockázatok és nyitott kérdések

Blokkoló nyitott tétel **nincs**. Nem blokkoló kockázatok:

1. **A javító-jellegű sorok „mindig nemet mond” kockázata**: a 10 hibás előfeltevés sor mindegyike a felhasználó állítását cáfolja; a modell megtanulhatja, hogy egy *Ha…, akkor…?* típusú kérdésre alapból nemmel válaszol. Következő batchekben érdemes 2-3 olyan sort is írni, ahol az előfeltevés **igaz** (*Igen, …*), és a modell magabiztosan megerősíti, illetve olyat, ahol részben igaz.
2. **Tényellenőrzés a magabiztos állításokra**: `0328` (a hideg önmagában nem okoz betegséget; a megfázást vírusok okozzák), `0388` (a felhők az UV-sugárzás jelentős részét átengedik), `0303` (mosogatószer-túladagolás, a gépbe való só), `0347` (hűtő ajtaja, szellőzés), `0364` (délutáni cipőpróba, hüvelykujjnyi hely), `0379` (rövid, erős szellőztetés) közismert, széles körben elfogadott állítások, de tanítás előtt érdemes emberi tényellenőrzés.
3. **Címkehossz**: a 10 hibás előfeltevés soron 8 elemű a `tags` lista, a többi soron 7; ez a saját kiegészítésem (a szűréshez), a séma nem tiltja, de a későbbi feldolgozásnál (`tags[5]`, `tags[6]` pozíciók) érdemes figyelembe venni. A `kontraszt_magabiztos` mód-címke továbbra is a szűrőcímke; kérem a jóváhagyást, hogy a `hibas_elofeltevesjavitas` marad-e, vagy a hibás előfeltevés soroknak külön mód-címkét adjunk.
4. **Címke-szemantika**: a 14 kontraszt-sor is megkapta a `bizonytalansag`, `forraskeres`, `nem_kamuzik` címkét (a kérés szerint), holott bennük nincs bizonytalanság; ezek jelölőcímkék, a szűréshez a mód-címke kell.
5. **Egészség/jog/pénz**: 28 kulcsszavas sor, ebből 14 `hard`; tanács nélküliek, de nagyobb mennyiségnél külön egészségügyi-biztonsági és jogi átnézés kell. A `0358` (vihar), `0334` (futás kezdése), `0313` (elázott telefon), `0400` (gyógyszer külföldre) általános, nem személyre szabott lépéseket adnak.
6. **Fenntartó fordulatok**: *érdemes* 9 sorban, *függ* 14 sorban, *nézd meg* 4 sorban; a *hivatalos* 0 sorra csökkent, ami lehet túlkorrekció (a hatóság közleménye néha valóban *hivatalos*); a következő batchben természetes mértékben lehet újra.
7. **Kereszt-dedupe a `simple_qa` sablonjaival**: a 4 pontos vagy közel pontos egyezés arra utal, hogy az általános *Mit tegyek, ha…?* / *Hogyan kezdjek…?* típusú hétköznapi kérdéseket a `simple_qa` már sokat lefedi; a következő batchek előtt érdemes a tervezett instructionöket a korpusszal előre összevetni, mielőtt megírom a választ.
8. **Időre utaló kérdések** (*ma*, *tegnap*, *tavaly*, *most*): a modellnek nincs órája; a sorok következetesen nem állítanak dátumot vagy állapotot.
9. **Az ellenőrző scriptek** (`gen_usr4.py`, `usr_check4.py`) a repón kívül vannak; a `tools/` alá emelésük külön jóváhagyandó.

## 7. Fájlok

- Raw: `data/raw/claude_uncertainty_source_request_0301_0400_raw.jsonl` (100 sor)
- Clean: `data/clean/claude_uncertainty_source_request_0301_0400_clean.jsonl` (100 sor)
- Rejected: `data/rejected/claude_uncertainty_source_request_0301_0400_rejected.jsonl` (0 sor, üres fájl)
- Report: `data/reports/claude_uncertainty_source_request_0301_0400_report.md`

## 8. Amit ez a kör NEM tett

- Nem indított tanítást, nem módosított webapp/backend kódot, nem törölt és nem írt felül semmit (az 1-3. batch, a korábbi csomagok fájljaihoz, a validátorhoz és a topic reporthoz sem nyúlt).
- A topic report jelölő-címke kérdését nem javította adatként, csak dokumentálta (5. fejezet).
- Nem készítette el az `uncertainty_source_request_0401_0500` batchet: **jóváhagyásra vár**.
- Nem használt webes forrást, valós felhasználói szöveget, ChatGPT/Dispatch raw jelöltet.

---

## Végső összegzés

- Batch: 100 sor, **100 clean / 0 rejected**, schema 100/100 valid, átlag score 100.0, regressziós teszt STABIL; teljes clean korpusz **3900 sor**; a 6. csomag (Bizonytalanság / forráskérés) **400 / 1000**.
- 7 mód: változó adat 15, forrás nélkül nem tudható 14, pontosítás 14, általános válasz + ellenőrzés 14, kitalálás elutasítása 14, ellenőrzési út 15, **kontraszt (magabiztos válasz) 14 = 14%**, ebből **10 hibás előfeltevést javító**.
- Témák: telefon/app/technika 20, háztartás 17, ügyintézés/jog/pénz/egészség 15, utazás 11, sport 9, időjárás 8, közösségi média 8, vásárlás 6, hétköznapi félreértések 5, oktatás 1 (35 volt); bankkártya, jegyár, nyitvatartás sor 0.
- Dedupe 0, kereszt-dedupe a 3800 sorral 0 (a javítás előtti 4 találattal), safety/PII/identity bleed 0, „ne kamuzzon” audit: 0 kivétel.
- Fenntartó fordulatok: *hivatalos* 0, *általában* 1, *nézd meg* 4, *Ezt nem* nyitás 1.
- Topic report: a négy jelölő címke 10.3% (`[FIGYELEM]`), **kivételként dokumentálva**, adatot és eszközt nem módosítottam.
- Clean előtt javítva: 4 kereszt-dedupe találat, nyitás-koncentráció, nyelvtani hibák, a *hivatalos* visszaszorítása.
- **Nyitott kérdések**: igaz előfeltevésű (megerősítő) kontraszt-sorok, tényellenőrzés a magabiztos állításokra, a `hibas_elofeltevesjavitas` címke jövője, egészség/jog/pénz átnézés nagyobb mennyiségnél, *érdemes* és *függ* gyakorisága, a `simple_qa` sablonokkal való előzetes összevetés.

**STÁTUSZ: STABIL.**
