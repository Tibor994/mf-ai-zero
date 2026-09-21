# Hatodik uncertainty_source_request batch - uncertainty_source_request_0501-0600

**Verdikt: STABIL.** 100 sor, **100 clean / 0 rejected**, `category: uncertainty_source_request`, a **6. csomag (Bizonytalanság / forráskérés)** hatodik batchje az új, bővített 17 000 soros `instruction_core`-ban. A csomag célmérete **1000 sor**, ezzel **600 / 1000** kész; a clean korpusz **4100 sor**.
A batch célja: a modell ne találjon ki választ, ha nem biztos, **de ne is legyen feleslegesen félős**. Új ebben a batchben: (1) **részben igaz előfeltevésű kontraszt-sorok** (a felhasználó félig jól gondolja, a modell pontosít), (2) **nyitottabb, természetesebb kérdésformák** a zárt *Ha…, akkor…?* helyett (*Jól értem, hogy…?*, *Akkor ez azt jelenti, hogy…?*, *Ebből következik, hogy…?*, *Ez alapján csinálhatom úgy, hogy…?*), (3) a túl gyakori szavak (*szolgáltató*, *kérdezd*, *ezért*, *érdemes*, *függ*) visszaszorítása, (4) konkrét hétköznapi helyzetek, `Mit tegyek, ha…?` instruction nélkül.

> **Számozás**: 6. csomag = Bizonytalanság / forráskérés, cél 1000 sor; a régi 4900 soros roadmap számozása nem irányadó. Állás a batch után: **600 / 1000**.
> **Címkék**: a fő mód a korábbi batchekkel egyezően **`kontraszt_magabiztos`**. Plusz címkék (nem fő módok): `hibas_elofeltevesjavitas` (3 sor), `igaz_elofeltevesmegerosites` (3 sor) és az ebben a batchben új **`reszben_igaz_elofeltevespontositas`** (4 sor; lásd 6. fejezet, 3. pont).

## 0. A kérés követelményei és teljesülésük

| Követelmény | Teljesülés |
|---|---|
| 100 új sor, id `0501`-`0600`, magyar, `uncertainty_source_request`, 600/1000, clean 4100 | 100 sor, folytonos id-k, `source: synthetic_claude_magyar`; csomag **600 / 1000**, korpusz **4100** |
| STABIL, 0 rejected, 0 dedupe, safety tiszta, quality score 100 | **100 / 100 valid, 100 clean, 0 rejected**, dedupe 0, kereszt-dedupe 0, safety 0, score **100.0**, regressziós teszt STABIL |
| Részben igaz előfeltevésű kontraszt-sorok | **4 sor** (`0506`, `0512`, `0568`, `0569`), plusz címkével |
| A kontraszt-sorok ne csak zárt *Ha…, akkor…?* szerkezetűek legyenek; nyitottabb kérdések | a 14 kontraszt-sorban **0 zárt *Ha…, akkor…?*** forma: *Jól értem, hogy…?* 3, *Ebből következik, hogy…?* 3, *Akkor ez azt jelenti, hogy…?* 2, *Ez alapján csinálhatom úgy, hogy…?* 2, nyitott *Hogyan… / Miért… / Mit…?* 4 |
| `igaz_elofeltevesmegerosites` plusz címke marad, nem fő mód | 3 sor (`0518`, `0523`, `0548`); fő mód `kontraszt_magabiztos` |
| `hibas_elofeltevesjavitas` plusz címke marad | 3 sor (`0543`, `0574`, `0583`) |
| Kontraszt-sorok száma 10-15% (a korábbi kérésből) | **14 sor = 14%**; ebből 10 előfeltevéses (3 javító + 3 megerősítő + 4 részben igaz) és 4 hétköznapi tanács |
| Ne legyen sok *szolgáltató*, *kérdezd*, *ezért*, *érdemes*, *függ* | *szolgáltató* **0** (17 volt), *kérdezd* **0** (16), *ezért* **6** (27), *érdemes* **4** (5), *függ* **6** (6) sor |
| Egészség/jog/pénz: nincs diagnózis, jogi állásfoglalás, adótanács, pénzügyi tanács | 20 `hard` sor, kézzel átnézve, mind tanács- és állásfoglalás nélküli (3. fejezet 5. pont) |
| Kerüld az általános `Mit tegyek, ha…?` instructionöket; konkrét hétköznapi helyzetek | **0** `Mit tegyek, ha…?` instruction; kereszt-dedupe találat a `simple_qa`-val 0 |
| Fact-check gyanús, közismertnek tűnő állítások külön jelölése emberi átnézésre; validátor és eszközök változatlanok | 6. fejezet, 2. pont: soronkénti lista; a validátort és az eszközöket nem módosítottam |
| A végén megáll, nem kezdi el a `0601_0700` batchet | igen |
| 0 PII/URL/e-mail/telefonszám, 0 MF-AI/Nextora, 0 identity bleed, 0 erős káromkodás | mind 0 (3. fejezet 5. pont) |

## 1. Felépítés

### 1.1. A hét mód (`tags[5]`)

| Mód-címke | Sor | Mit tanít |
|---|---|---|
| `valtozo_adat` | 15 | változó adat és élő információ (első fagy, éjszakai vonat, app nyelvi támogatása, uszoda vasárnapi nyitvatartása, jelentkezési határidő, vízkorlátozás, festék száradása, új okosóra, bolti visszavétel, késedelmi kamat, Balaton vízhőmérséklete, ünnepnapi piac) |
| `forras_nelkul_nem_tudhato` | 14 | hozzáférés nélküli vagy nem ismerhető tény (lépcsőházi rajz, tavalyi kiadás, lift karbantartása, alvás, jövő évi lakbér, használt kerékpár kilométere, hűtő áramfogyasztása, első mobiltelefon) |
| `pontositas_kell` | 14 | hiányos kérdés (*Lehet ezt kicserélni másikra?*, *Mennyi idő alatt készül el?*, *Ez a levél nekem szól?*, *Kell ehhez külön biztosítás?*, *Hány adag lesz ebből?*) |
| `altalanos_valasz_ellenorzessel` | 14 | érdemi általános válasz (lánc rozsda ellen, bukósisak, laptop törlése eladás előtt, repülőn fülfájás, kerékpárbelső foltozása, erkélyi kert, rosszullét az utcán, hőség klíma nélkül), ahol kell, szakemberre vagy típusfüggő forrásra utal |
| `kitalalas_elutasitasa` | 14 | kitalálást kér a felhasználó (PIN-kód, ajánlólevél mások nevében, anyajegy, balesetért felelős, nyugdíj adatok nélkül, parkolóhely-garancia, „a tej még jó”, futár pontos érkezése) |
| `ellenorzesi_ut` | 15 | ellenőrzési lépések (banki app, hamis sportcipő, paradicsom-tanács, mobilhálózat-leállás híre, napelem télen, kilométeróra, gyerekjáték biztonsága, utalás megérkezése, sportóra pulzusa) |
| **`kontraszt_magabiztos`** | **14** | előfeltevéses (10) és hétköznapi tanácsot adó (4) sorok; nincs fenntartás |

### 1.2. Bizonytalansági típusok és témák eloszlása

A `tags[6]` mind a 100 sorban **egyedi**. Tematikus csoportosítás (a kontraszt-sorokat is a témájuk szerint számolva):

| Téma-csoport | Sor | Példák (`tags[6]`) |
|---|---|---|
| Telefon, app, technika | 21 | `fp_hatterben_futas`, `fp_megapixel`, `ip_jelszokezelo`, `rp_router_ujrainditas`, `ketto_mentes`, `magyar_nyelvu_app`, `regi_laptop_torlese`, `telefon_vizallosag`, `napelem_telen` |
| Háztartás | 17 | `fp_mikro_femedeny`, `ip_elsore_lejarat`, `feher_ruha_mosasa`, `festek_szaradas`, `gepi_mosogato_tisztitasa`, `erkelyi_zoldsegeskert`, `paradicsom_hutoben`, `vizszuro_betet_csere` |
| Ügyintézés, jog, pénz, egészség | 15 | `idopontfoglalas_valtozas`, `keseldelmi_kamat_csekk`, `kell_hozza_biztositas`, `ismeretlennek_utalas`, `baleset_felelossege`, `szomszed_fa_telekhatar`, `anyajegy_veszelyes`, `banki_app_valodi` |
| Utazás, közlekedés | 12 | `kezipoggyasz_hosszu_ut`, `ejszakai_vonat_tengerpart`, `borravalo_merteke`, `repulon_ful`, `szallodai_szolgaltatasok`, `parkolohely_garancia`, `kmora_allas_valodi` |
| Sport | 11 | `rp_nyujtas_edzes_elott`, `ip_futas_elott_etel`, `tura_cipo`, `sportora_pulzus`, `lanc_rozsda`, `kerekpar_belso_foltozas`, `uszoda_vasarnap` |
| Vásárlás | 11 | `rp_nagyobb_kiszereles`, `hasznalt_konyv_allapota`, `kibontott_termek_visszavetele`, `hamis_sportcipo`, `kornyezetbarat_jeloles`, `bukosisak_merete`, `hasznalt_kerekpar_vasarlas` |
| Közösségi média és értékelés | 5 | `rp_privat_fiok`, `lajkok_elrejtese`, `korrekt_ertekeles`, `enekes_valasa`, `weboldal_frissessege` |
| Hétköznapi félreértés, egyéb | 4 | `kutya_nem_harap`, `kollega_ellopta_otletet`, `mennyi_ido_alatt_keszul`, `piac_unnepnap` |
| Időjárás | 4 | `elso_fagy`, `balaton_vizhomerseklet`, `hoseg_klima_nelkul`, `nedves_haj_megfazas` |

Az oktatás/iskola/kollégium sor ebben a batchben 0. Bankkártya, jegyár sor 0.

### 1.3. A kontraszt-sorok (14 sor, 14%): 3 javító + 3 megerősítő + 4 részben igaz + 4 hétköznapi tanács

A kontraszt-sorok mind természetesebb, nyitottabb szerkezetűek. Ahol a *Akkor ez azt jelenti…?* / *Ebből következik…?* / *Ez alapján csinálhatom úgy…?* forma előzményt feltételez, a sor `input` mezője tartalmazza a felhasználó által idézett mondatot (5 sor), így nem marad kontextus nélküli a kérdés.

**Hibás előfeltevést javító sorok (3 sor, `hibas_elofeltevesjavitas` címkével):**

| id | Kérdésforma | A felhasználó állítása (félreértés) | A modell javítása |
|---|---|---|---|
| `0543` | *Jól értem, hogy…?* | ha lezárom a telefon képernyőjét, semmi sem fut a háttérben | *Nem egészen*: üzenetküldők, levelezés, zene, frissítések futnak tovább; a háttér korlátozható |
| `0583` | *Ebből következik, hogy…?* | a több megapixel mindig jobb képet ad | *Nem*: a megapixel csak a felbontás; érzékelő, lencse, képfeldolgozás számít |
| `0574` | *Ez alapján csinálhatom úgy, hogy…?* | a mikróban rövid ideig fémedényben is melegíthetek | *Nem*: a fém szikrázhat, tüzet is okozhat; üveg, kerámia, mikrózható műanyag |

**Igaz előfeltevést megerősítő sorok (3 sor, `igaz_elofeltevesmegerosites` címkével):**

| id | Kérdésforma | A felhasználó állítása (helyes) | A modell megerősítése |
|---|---|---|---|
| `0548` | *Akkor ez most azt jelenti, hogy…?* (bemásolt kontextussal) | jelszókezelővel egyszerűbb a különböző jelszavak kezelése | *Igen, pontosan ezt jelenti*; erős főjelszó és kétlépcsős azonosítás |
| `0518` | *Jól értem, hogy…?* | futás előtt jobb nem nehéz étellel indulni | *Igen, ez így van*; egy-két óra várakozás nagyobb étkezés után, könnyű harapnivaló |
| `0523` | *Ebből következik, hogy…?* (bemásolt kontextussal) | otthon is a régebbi élelmiszert kell előre tenni | *Igen*, ugyanaz a szabály; kevesebb romlik meg |

**Részben igaz előfeltevést pontosító sorok (4 sor, `reszben_igaz_elofeltevespontositas` címkével):**

| id | Kérdésforma | A felhasználó állítása | A modell pontosítása |
|---|---|---|---|
| `0568` | *Jól értem, hogy…?* | az újraindítástól gyorsabb lesz az internet | *Részben*: átmeneti hibán segít, a tartós lassúságon és az előfizetett sebességen nem |
| `0506` | *Ebből következik, hogy…?* (bemásolt cikkrészlet) | edzés előtt mindenképp nyújtani kell, különben sérülés | *Ez túlzás, de van benne igazság*: a bemelegítés fontos, a hosszú nyújtás edzés előtt nem bizonyítottan véd |
| `0512` | *Akkor ez azt jelenti, hogy…?* (bemásolt tényadat) | a nagyobb kiszerelés mindig olcsóbb | *Ebben az esetben igen, de általánosítani nem lehet*; az egységárat kell összevetni |
| `0569` | *Ez alapján csinálhatom úgy, hogy…?* (bemásolt szabály) | a privát fiókomat senki idegen nem láthatja | *Nagyrészt igen, de nem teljesen*: képernyőkép, látható név és profilkép |

**Hétköznapi, magabiztos tanácsot adó sorok (4 sor):** `0577` (fehér ruha mosása), `0592` (kézipoggyász hosszú útra), `0549` (két helyre mentés), `0526` (használt könyv állapota).

Szabályok, amelyeket betartottam: (a) a javító, megerősítő és részben igaz sorok együtt képezik az előfeltevéses csoportot (3 : 3 : 4), így a modell nem csak *Nem*-mel és *Igen*-nel, hanem *Részben*, *Nagyrészt igen*, *Ez túlzás, de…* típusú válaszokkal is találkozik; (b) mindegyik válasz indokol, és ad egy gyakorlati lépést vagy kiegészítést; (c) 0 fenntartó kifejezés (*általában*, *függ*, *nem tudom*, *ellenőrizd*, *forrás*) a 14 sorban; a részben igaz sorokban a pontosítás a válasz **tartalma**, nem bizonytalankodás; (d) 35-47 szó (átlag 42.1), természetes hang; (e) egészségügyi témában (`0518` futás előtti étkezés, `0506` nyújtás) csak közismert, általános tájékoztatás van, diagnózis és személyes tanács nélkül.

### 1.4. Formai döntések

- **`tags`**: minden sorban `["magyar", "instruction_core", "bizonytalansag", "forraskeres", "nem_kamuzik", <mód>, <téma>]`; a 10 előfeltevéses soron nyolcadik elemként a megfelelő plusz címke. A címkehossz tehát 90 sorban 7, 10 sorban 8.
- **`input`**: 91 sorban üres, **9 sorban** bemásolt szöveg: 5 kontraszt-sor (jelszókezelő, régebbi élelmiszer előre, nyújtás cikk, nagyobb kiszerelés, privát fiók), a `0530` (recept adagszámítás), a `0527` (mobilhálózat híre), a `0584` (paradicsom) és a `0552` (napelem).
- **`difficulty`**: easy 54 / medium 26 / hard 20. A *hard* mind jogi, pénzügyi, egészségügyi vagy biztonsági érintettségű nem-kontraszt sor; a kontraszt-sorok mind *easy*.
- **`quality_notes`**: soronként egyedi; az előfeltevéses soroknál megnevezi a kérdésformát, a félreértést vagy a megerősített állítást és a magabiztos válasz módját.
- **Sorrend**: deterministikus keverés (seed 20261002), a kontraszt-sorok szétszórva.

## 2. Számok

| Mérőszám | Érték |
|---|---|
| Raw sorok | 100 |
| Schema validáció (`dataset_validate.py`) | 100 / 100 valid (már a nyers fájlon is; a végleges clean fájlon is) |
| **Végleges clean** | **100** (100%) |
| **Rejected** | **0** (0%, üres fájl) |
| Batchen belüli dedupe (id / instruction / output, 0.9) | 0 / 0 / 0 |
| Egyedi instruction+input / output / quality_notes | 100 / 100 / 100 |
| Kereszt-dedupe a meglévő **4000** clean sor ellen (id-ütközés; instruction+input, output, instruction-instruction, instruction-input, output-input >= 0.9) | 0 / 0 / 0 / 0 / 0 / 0 (az 1-5. batch sorai is benne vannak); az első futásban 2 instruction-instruction találat volt (4. fejezet, 1. pont) |
| Instruction-hasonlóság a korpusszal >= 0.7 (tájékoztató) | csak sablon- és témarokonság (*Hogyan tisztítsam a gépi mosogatót?* ~ *Hogyan tisztítsam a mosógépet?* 0.80; *Mondd meg biztosan, hogy a szomszéd kutyája nem harap.* ~ *Mondd meg biztosan, hogy ez a link nem csalás.* 0.70), tartalmi ütközés 0 |
| `input` != `output`, `instruction` != `output` | 100 / 100 |
| Átlagos quality score | **100.0 / 100** (minden sor 100) |
| Regressziós teszt (`tests.test_v1_7_4_dataset_foundation`) | minden teszt sikeres, **STÁTUSZ: STABIL** |
| Output szószám (min / medián / átlag / max) | 28 / 41 / 41.3 / 54 (nem-kontraszt átlag 40.9, kontraszt 42.1); legfeljebb 349 karakter |
| Instruction átlagos szószáma | 8.0 |
| Összes szó (instruction + input + output) | 5007 (33 695 karakter) |
| Topic report (4100 soros korpusz) | a négy jelölő címke egyenként 600 sor = **14.6%**, `[FIGYELEM]` jelzéssel; **kivételként dokumentálva** (5. fejezet) |
| Teljes clean korpusz | **4100 sor** (1000 simple_qa, 1000 explanation, 500 step_by_step, 500 summary, 500 noisy_input, 600 uncertainty_source_request) |

## 3. Ellenőrzési lépések

1. **Generálás**: 100 sor négy részben, soronként kézzel megírt kérdés-válasz párokkal (nincs szabály- vagy sablongenerátor); az előfeltevéses sorokat külön csoportként terveztem, a kérdésformákat előre elosztottam.
2. **Schema**: `dataset_validate.py` 100/100 a nyers és a végleges fájlon is; saját ellenőrzés az id-folytonosságra, a kötelező tagekre, az ASCII snake_case tag-formára, a difficulty-értékekre, az egyediségre, a mód-eloszlásra, és a plusz címkék pontos darabszámára (3 / 3 / 4).
3. **Dedupe**: `dataset_dedupe.py`: id 0, instruction-hasonlóság 0, output-hasonlóság 0; páronkénti összevetés a batchen belül: 6 pár >= 0.6, legnagyobb 0.71 (`0517`/`0519`: *Hogyan ellenőrizzem, hogy a telefonomon lévő banki alkalmazás valódi-e?* / *…a telefonom valóban vízálló-e?*, két különböző kérdés azonos szerkezettel), >= 0.9: 0.
4. **Kereszt-dedupe** a 4000 meglévő clean sorral szemben, 5 összevetésben: a végleges állapotban 0 találat, 0 id-ütközés.
5. **Safety/PII/identity bleed**: e-mail, URL, telefonszám-, azonosító-/IBAN-minta 0; MF-AI/Nextora/Nexora említés 0; `guard.looks_like_identity_bleed` 0; önbemutatkozás-jel 0; angol stopword 0; erős káromkodás/gyűlölet 0. Számjegyet tartalmazó nem-kontraszt output egy van (`0541` *112* segélyhívó); telefonszám 0.
   Érzékeny területek: a kulcsszavas unió 32 sor; a 20 `hard` sor mind kézzel átnézve. A modell **nem ad diagnózist, jogi állásfoglalást, adótanácsot vagy pénzügyi tanácsot**: `0539` (anyajegy) kimondja, hogy nem tudja megítélni, riasztó jelekre bőrgyógyászati vizsgálatot javasol; `0537` (megfázás) nem ígér védettséget, orvost és gyógyszerészt nevez meg; `0545` (fülfájás repülőn) és `0542` (hőség) közismert általános fogásokat ad, betegségnél orvosi tanács, személyre szabott tanács nélkül; `0541` (rosszullét) a 112-t és a kiérkező segítség utasításainak követését nevezi meg, tanfolyamot ajánl; `0572` (baleset felelőse) felelősséget nem állapít meg, tényszerű összefoglalót kínál; `0546` (edzői vád) nem állít okot, orvost említ; `0531` (nyugdíj) számot nem mond, pénzügyi és jogi tanácsot nem ad; `0551` (késedelmi kamat) számot nem mond, pénzügyi tanácsot nem ad; `0557` (tavalyi kiadások) hozzáférés nélkül összeget nem talál ki; `0578` (utalás ismeretlennek) pénzügyi tanácsot nem ad, gyanús jeleket sorol; `0580` (lakbér) jogi kérdésben szakembert nevez meg; `0565` (biztosítás), `0595` (levél), `0567` (telekhatár) jogi állásfoglalást nem ad; `0517` és `0529` (banki alkalmazás, utalás megérkezése) ellenőrzési utat ad, pénzügyi tanács nélkül; `0562` (sportóra pulzusa) az órán mért értéket egészségügyi döntéshez nem tartja használhatónak, orvosra utal; `0550` (vízszűrő) egészségi aggálynál szakembert nevez meg.
6. **„Ne kamuzzon” audit**: (a) az automata kulcsszavas ellenőrzés a 86 nem-kontraszt sorból 16-ot jelzett fenntartás-jel nélkülinek (`0503, 0507, 0509, 0510, 0517, 0519, 0525, 0537, 0552, 0580, 0582, 0584, 0590, 0594, 0597, 0599`); kézzel átnézve mindegyikben van tartalmi jel (nincs adat, gyanús jel, elutasítás, típusfüggés, *Részben*, *Ez így nem pontos*, ellenőrzési lépés), a kulcsszólista volt szűk; (b) a bizonyosságot jelző szavak találatai kézzel átnézve tagadók (*Biztosat nem mondhatok*, *nem lehet előre biztosan megmondani*), a kérés szövegéből átvettek (*Mondd meg biztosan…*) vagy téves illesztések (*nyilvános*, *mindig* mint *nem mindig árul el mindent*); (c) egyik nem-kontraszt sor sem állít konkrét árat, dátumot, eredményt, összeget vagy jogszabály-tartalmat; (d) az elterjedt állítást bemásoló sorok (`0527`, `0552`, `0584`) nem mondanak határozott igent vagy nemet, hanem pontosítanak és forrást adnak, a `0552` (*Ez így nem pontos*) és a `0584` (*Részben*) közismert tényre támaszkodik, ezért szerepel a tényellenőrzési listán (6. fejezet, 2. pont).
7. **Kontraszt-ellenőrzés**: mind a 14 sor stabil közismeret, józan gyakorlati tanács vagy egy általános állítás javítása, megerősítése vagy pontosítása; fenntartó kifejezés 0; kérdésforma-eloszlás lásd 0. fejezet.
8. **Nyitások és stílus**: kétszavas nyitás legfeljebb 2 sornál azonos (*Erről nincs*, *Vedd ki*, *Ezt előre*, *Olvasd el*, *Ezt nem*, *Nem a*); leggyakoribb első szó *a* 16, *ezt* 7, *az* 5, *milyen* 4, *erről* 3, *ez* 3, *keresd* 3, *igen* 3 (a megerősítő sorok); *Ezt nem* 2, *Nem tudom biztosan* 0, *Nem tudom* 0. Gyakori szavak az 5. batch végállapotához képest: *szolgáltató* 17 -> 0, *kérdezd* 16 -> 0, *ezért* 27 -> 6, *érdemes* 5 -> 4, *függ* 6 -> 6, *nézd meg* 3 -> 1, *általában* 2 -> 2, *hivatalos* 1 -> 0, *segítek* 4 -> 4, *ha megírod* 4 -> 2. Új kiugrás: *pontos* 19 sorban (*pontos lépések*, *pontos időpont*), *ellenőrizd* 7, *rákérdez-* 5.
9. **Quality score**: `dataset_score.py` 100.0 / 100.
10. **Regressziós teszt**: STABIL.
11. **Kézi átolvasás**: mind a 100 sor (kérdés, input és válasz) egymás mellett végigolvasva a második javítási kör előtt.

## 4. Milyen hibákat javítottam clean előtt

| # | Hiba / kockázat | Javítás |
|---|---|---|
| 1 | **Azonos instruction**: a paradicsomos és a napelemes sor is *Van ebben igazság?* volt (két különböző bemásolt szöveggel), ami egyezik az 5. batch `0412` sorának instruction-jével is; az `instruction+input` egyediség teljesült, de az instruction-instruction összevetés 1.0-t adott (2 kereszt- és 1 batchen belüli találat) | *Mennyire igaz ez a konyhai tanács?*, illetve *Mi igaz ebből a napelemes állításból?* |
| 2 | **Gyakori szó: *ezért*** az első vázlatban 20 sorban | 14 sorban átfogalmazva (mellérendelő vagy más szerkezet: *így*, *tehát*, elhagyás); végül 6 sor |
| 3 | **Gyakori kifejezés: *nézd meg*** az első vázlatban 5 sorban | 4 sorban cserélve (*Figyeld meg*, *Vizsgáld meg*, *Ellenőrizd*, *Olvasd el*); végül 1 sor |
| 4 | Nyelvtani és hangzásbeli hibák: *a kézzel megnyomott, nyikorgó vázat hagyd ki* (`0590`), és az *ezért* elhagyása utáni rövid mondatkapcsolatok (*nem ismerem, évszámot nem mondok*) | a `0590` kijavítva (*a nyikorgó vagy laza vázú darabot hagyd ki*); a rövid, vesszős mondatkapcsolatok szándékosan maradtak, lásd 6. fejezet, 6. pont |
| 5 | A validátor a nyers fájlon már az első futásban 100/100 volt (az 5. batch 1 elutasított sora nem ismétlődött): előzetes ellenőrzés a nyers fájlon, torz-token kockázat (*https*, rövidítések) kerülve | megelőző lépés, javítás nem kellett |

## 5. Topic report kivétel dokumentálása

A `tools/dataset_topic_report.py` a 4100 soros korpuszra a következőt jelzi:

| Tag | Sor | Arány | Jelzés |
|---|---|---|---|
| `instruction_core` | 600 | 14.6% | `[FIGYELEM]` |
| `bizonytalansag` | 600 | 14.6% | `[FIGYELEM]` |
| `forraskeres` | 600 | 14.6% | `[FIGYELEM]` |
| `nem_kamuzik` | 600 | 14.6% | `[FIGYELEM]` |

**Döntés (a korábbi felhasználói jóváhagyás alapján):** ezek a címkék ennél a csomagnál **csomagjelölők**, nem tematikai jellegűek: a `uncertainty_source_request` kategória minden során rajta vannak (600 sor = a korpusz 14.6%-a), ezért a küszöb átlépése **nem tematikai túlsúlyhiba**. **Kivétel**: a `[FIGYELEM]` jelzés ezekre a címkékre elfogadott. Adatként nem javítottam, az eszköz kódját nem módosítottam, és nem vezettem be kivétel-listát; a dokumentálás csak a riportban van, a 4. és az 5. batch riportjával egyezően. A másik két jelzett címke (`zajos bemenet` 12.2%, `összefoglalás` 12.2%) a korábbi csomagokból származik, ehhez a batchhez nem kapcsolódik, és változatlan (az arányuk csak a korpusz növekedése miatt csökkent).
A jelölő címkék aránya a csomag további batchjeivel tovább nő (a csomag végén 1000 sor); ha a `dataset_topic_report.py` kivétel-kezelése később szükségessé válik, az külön jóváhagyást igényel.

## 6. Kockázatok és nyitott kérdések

Blokkoló nyitott tétel **nincs**. Nem blokkoló kockázatok:

1. **Az előfeltevéses sorok kérdésformái még mindig zártak**: mindegyik állítást ellenőrizteti (*Jól értem, hogy…?*, stb.); a modell megtanulhatja, hogy minden ilyen kérdésre *Igen/Nem/Részben* nyitással válaszoljon. Következő batchekben érdemes olyan kontraszt-sorokat is írni, ahol az előfeltevés csak implicit, például *Miért…?* vagy *Hogyan…?* kérdésben, és ahol a felhasználó több állítást keverve mond.
2. **Közismertnek tűnő állítások: emberi tényellenőrzést igényelhetnek** (a kért jelölés; a validátor és az eszközök nem módosultak):

   | Sor | Állítás |
   |---|---|
   | `0543` | a lezárt képernyő mellett az üzenetküldők, levelezés, zene, navigáció és frissítések tovább futhatnak, és fogyasztják az akkumulátort |
   | `0583` | a megapixel csak a felbontást mutatja; a képminőséget az érzékelő, a lencse és a képfeldolgozás is befolyásolja |
   | `0574` | fémedény a mikróban szikrázhat, tüzet is okozhat |
   | `0568` | a router újraindítása átmeneti hibán segíthet, az előfizetett sebességen nem |
   | `0506` | edzés előtt a hosszú, statikus nyújtás nem bizonyítottan véd a sérüléstől; a dinamikus bemelegítés jobb (**sportegészségügyi állítás, külön óvatos átnézést kér**) |
   | `0512`, `0569` | egységár és kiszerelés; privát fiók: a jóváhagyott követők képernyőképet készíthetnek, a név és a profilkép sokszor látszik |
   | `0518` | futás előtt nagyobb étkezés után egy-két óra várakozás; könnyű harapnivaló (**egészségi jellegű, általános**) |
   | `0523`, `0548` | az elsőként lejáró élelmiszer előre tétele; a jelszókezelő előnyei |
   | `0577`, `0592`, `0549`, `0526` | fehér ruha mosása (szín szerinti válogatás, túlterhelés), kézipoggyász-lista, két helyre mentés, használt könyv állapota |
   | `0584` | a paradicsom hűtőbe tétele ízt és állagot ronthat, de biztonsági kockázatot nem jelent |
   | `0552` | a napelem télen kevesebbet, borús időben is valamennyi áramot termel |
   | `0527` | tervezett, országos mobilhálózat-leállásról hatósági és üzemeltetői közlemény lenne |
   | `0545`, `0542`, `0541` | fülnyomás-kiegyenlítés repülőn, hőség elleni lépések, rosszullét: 112 (**egészségi jellegűek, általános tájékoztatás**) |
   | `0566`, `0590`, `0582`, `0587`, `0508` | bukósisak méretezése (a szíj alatt két ujj), szélálló esernyő jellemzői, lánckenés, belső foltozása, gépi mosogató tisztítása |
   | `0509`, `0519` | a CE jelölés nem garantálja a gyerekjáték biztonságát; IP kód és a vízállóság romlása |
   | `0525` | a kopásjelek (pedál, kormány, ülés) magas futásra utalhatnak |
   | `0538` | a szag nem mindig árulja el a tej romlását |

3. **Címkehossz és új címke**: a 10 előfeltevéses soron 8 elemű a `tags` lista, a többi soron 7. A `hibas_elofeltevesjavitas` és az `igaz_elofeltevesmegerosites` marad (a kérés szerint plusz címkék); a **`reszben_igaz_elofeltevespontositas`** az én kiegészítésem a részben igaz sorok szűréséhez, a fő mód mindhárom esetben `kontraszt_magabiztos`. Kérem a jóváhagyást az új címkére, vagy jelezd, ha a részben igaz sorok ne kapjanak külön jelölést.
4. **Címke-szemantika**: a 14 kontraszt-sor is megkapta a `bizonytalansag`, `forraskeres`, `nem_kamuzik` címkét (a korábbi kéréssel egyezően), holott bennük nincs bizonytalanság; ezek jelölőcímkék, a szűréshez a mód-címke kell.
5. **Egészség/jog/pénz**: 32 kulcsszavas sor, ebből 20 `hard` (az 5. batchben 12); tanács nélküliek, de nagyobb mennyiségnél külön egészségügyi-biztonsági és jogi átnézés kell. A `0541` (rosszullét), `0545` (fülfájás), `0542` (hőség) és `0562` (sportóra pulzusa) egészségi jellegű, általános tájékoztatást adnak.
6. **Stílus**: a *ezért* visszaszorítása után 6 sorban rövid, vesszővel tagolt mondatkapcsolat maradt (*A kiadásaidhoz nincs hozzáférésem, összeget nem tudok mondani.*, `0557`, `0520`, `0521`, `0561`, `0588`, `0589`); magyarul elfogadható, de a következő batchben érdemes természetesebb kötőszót vagy két mondatot használni. Új kiugró szavak: *pontos* 19 sorban, *ellenőrizd* 7, *rákérdez-* 5.
7. **`simple_qa`-rokonság**: a *Hogyan tisztítsam a…?* típusú kérdések (`0508`) témaközel vannak a `simple_qa` sorokhoz (0.77-0.80 karakter-hasonlóság); tartalmilag nem ütköznek, de az általános tisztítási kérdések további kerülendők.
8. **Időre utaló kérdések** (*tegnap*, *tavaly*, *holnap*, *idén*, *hétvégén*): a modellnek nincs órája; a sorok következetesen nem állítanak dátumot vagy állapotot.
9. **Az ellenőrző scriptek** (`gen_usr6.py`, `usr_check6.py`) a repón kívül vannak; a `tools/` alá emelésük külön jóváhagyandó.

## 7. Fájlok

- Raw: `data/raw/claude_uncertainty_source_request_0501_0600_raw.jsonl` (100 sor)
- Clean: `data/clean/claude_uncertainty_source_request_0501_0600_clean.jsonl` (100 sor)
- Rejected: `data/rejected/claude_uncertainty_source_request_0501_0600_rejected.jsonl` (0 sor, üres fájl)
- Report: `data/reports/claude_uncertainty_source_request_0501_0600_report.md`

## 8. Amit ez a kör NEM tett

- Nem indított tanítást, nem módosított webapp/backend kódot, nem törölt és nem írt felül semmit (az 1-5. batch, a korábbi csomagok fájljaihoz, a validátorhoz, a scoring és dedupe eszközökhöz és a topic reporthoz sem nyúlt).
- A topic report jelölő-címke kérdését nem javította adatként, csak dokumentálta (5. fejezet).
- Nem készítette el az `uncertainty_source_request_0601_0700` batchet: **jóváhagyásra vár**.
- Nem használt webes forrást, valós felhasználói szöveget, ChatGPT/Dispatch raw jelöltet.

---

## Végső összegzés

- Batch: 100 sor, **100 clean / 0 rejected**, schema 100/100 valid, átlag score 100.0, regressziós teszt STABIL; teljes clean korpusz **4100 sor**; a 6. csomag (Bizonytalanság / forráskérés) **600 / 1000**.
- 7 mód: változó adat 15, forrás nélkül nem tudható 14, pontosítás 14, általános válasz + ellenőrzés 14, kitalálás elutasítása 14, ellenőrzési út 15, **kontraszt (magabiztos válasz) 14 = 14%**, ebből **3 hibás előfeltevést javító**, **3 igaz előfeltevést megerősítő**, **4 részben igaz előfeltevést pontosító** és 4 hétköznapi tanács; kérdésformák: *Jól értem* 3, *Ebből következik* 3, *Akkor ez azt jelenti* 2, *Ez alapján csinálhatom úgy* 2, nyitott 4, zárt *Ha…, akkor…?* 0.
- Témák: telefon/app/technika 21, háztartás 17, ügyintézés/jog/pénz/egészség 15, utazás/közlekedés 12, sport 11, vásárlás 11, közösségi média 5, hétköznapi félreértés 4, időjárás 4; oktatás/iskola 0; `Mit tegyek, ha…?` instruction 0.
- Dedupe 0, kereszt-dedupe a 4000 sorral 0 (a javítás előtti 2 instruction-egyezéssel), safety/PII/identity bleed 0, „ne kamuzzon” audit: 0 kivétel.
- Gyakori szavak: *szolgáltató* 0, *kérdezd* 0, *ezért* 6, *érdemes* 4, *függ* 6, *nézd meg* 1.
- Topic report: a négy jelölő címke 14.6% (`[FIGYELEM]`), **kivételként dokumentálva**, adatot és eszközt nem módosítottam.
- Clean előtt javítva: 2+1 azonos instruction, *ezért* 20 -> 6, *nézd meg* 5 -> 1, nyelvtani hibák.
- **Nyitott kérdések**: az előfeltevéses kérdések zárt jellege, emberi tényellenőrzés a felsorolt állításokra (különösen a `0506`, `0518`, `0541`, `0542`, `0545`), az új `reszben_igaz_elofeltevespontositas` címke jóváhagyása, egészség/jog/pénz átnézés nagyobb mennyiségnél, a *pontos* / *ellenőrizd* gyakorisága.

**STÁTUSZ: STABIL.**
