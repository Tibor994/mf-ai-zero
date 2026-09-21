# Második uncertainty_source_request batch - uncertainty_source_request_0101-0200

**Verdikt: STABIL.** 100 sor, **100 clean / 0 rejected**, `category: uncertainty_source_request`, a **6. csomag (Bizonytalanság / forráskérés)** második batchje az új, bővített 17 000 soros `instruction_core`-ban. A csomag célmérete **1000 sor**, ezzel **200 / 1000** kész.
A batch célja: a modell ne találjon ki választ, ha nem biztos (jelezze a bizonytalanságot, kérjen forrást vagy pontosítást, mondja meg, mit és hol lehet ellenőrizni), **de ne is legyen feleslegesen félős**: ezért ebben a batchben **13 kontraszt-sor** is van, ahol a modell magabiztosan válaszol.

> **Számozás**: a felhasználó pontosítása szerint ez az új `instruction_core` 6. csomagja (Bizonytalanság / forráskérés, cél 1000 sor). A régi, 4900 soros roadmap számozását ennél a csomagnál nem tekintem irányadónak; a helyi `dataset_autopilot_progress.md` ennek megfelelően frissült (nem commitolt fájl).

## 0. A kérés követelményei és teljesülésük

| Követelmény | Teljesülés |
|---|---|
| 100 sor, magyar, `uncertainty_source_request` kategória, id `0101`-`0200` | 100 sor, folytonos id-k, `source: synthetic_claude_magyar`, a meglévő 9 mezős séma |
| A tartott szigor: 100/100 valid, 100/100 clean, 0 rejected | **100 / 100 valid, 100 clean, 0 rejected** |
| 0 batchen belüli duplikátum, 0 kereszt-dedupe találat a meglévő clean korpusz ellen | 0 / 0 (lásd 2. fejezet); a kereszt-dedupe az első futásban **1 pontos egyezést** talált, ezt clean előtt javítottam (4. fejezet, 1. pont) |
| 0 PII/URL/e-mail/telefonszám, 0 MF-AI/Nextora, 0 identity bleed, 0 erős káromkodás | mind 0 (3. fejezet 5. pont) |
| Regressziós teszt STABIL | minden teszt sikeres, **STÁTUSZ: STABIL** |
| A batch 10-15%-a kontraszt-sor | **13 sor = 13%** (`kontraszt_magabiztos`), lásd 1.3 |
| Kontraszt: általános, stabil tudás, magabiztos, nem túl hosszú válasz | 10-32 szó, **0 fenntartó/bizonytalanságot jelző kifejezés** a 13 sorban |
| A többi sor bizonytalanság / forráskérés (változó adat, friss info, ár/menetrend/nyitvatartás/eredmény, egészség/jog/pénz, pontosítás, forrás nélkül nem tudható, ellenőrzési út) | 87 sor, 6 mód (16 / 14 / 14 / 15 / 14 / 14) |
| Ne kezdődjön sok válasz ugyanúgy | leggyakoribb kétszavas nyitás 3 sor (*Ezt a*); *Ezt nem* kezdet 1 (első vázlatban 7), *Nem tudom biztosan* 0, *Nem tudom* 0 |
| Kevesebb „általában” és „nézd meg” | *általában* 26 -> **5** sor, *nézd meg* 35 -> **5** sor (az 1. batchhez képest) |
| Természetes, magyaros, nem sablonos válaszok | mind a 100 sor kézzel végigolvasva, két javítási kör (4. fejezet) |
| Ne kamuzzon, de ne is legyen félős | „ne kamuzzon” audit a 3. fejezet 6. pontja; a kontraszt-sorok és az ellenőrzési út sorai magabiztos, konkrét választ adnak |

## 1. Felépítés

### 1.1. A hét mód (`tags[5]`)

| Mód-címke | Sor | Mit tanít |
|---|---|---|
| `valtozo_adat` | 16 | ár, menetrend, nyitvatartás, eredmény, előrejelzés, jogszabályi összeg, élő adat: számot nem mond, megmondja, mitől változik és hol nézhető meg |
| `forras_nelkul_nem_tudhato` | 14 | hozzáférés nélküli vagy nem ismerhető tény (helyi múlt, magánadat, elemzőadat, becsült érték): nem talál ki választ, megnevezi a kutatás útját |
| `pontositas_kell` | 14 | hiányos kérdés (*Mennyi ideig tart az út?*, *Melyik a jobb?*): rákérdez, és megmondja, mitől függ a válasz |
| `altalanos_valasz_ellenorzessel` | 15 | érdemi általános válasz (bérlés, hitel, láz, véradás), de kimondja, mit kell szakemberrel vagy hivatalos forrással tisztázni |
| `kitalalas_elutasitasa` | 14 | kitalálást kér a felhasználó (jóslat, hamis igazolás, kitalált idézet vagy telefonszám): udvariasan elutasít, és valódi utat kínál |
| `ellenorzesi_ut` | 14 | konkrét ellenőrzési lépések (hír, fotó, bankhívás, albérlet-hirdetés, statisztika, alapítvány) |
| **`kontraszt_magabiztos`** | **13** | stabil, hétköznapi tudás: magabiztos, rövid válasz, nincs fenntartás |

### 1.2. Bizonytalansági típusok és témák eloszlása

A `tags[6]` mind a 100 sorban **egyedi** (100 különböző téma-címke). Durva tematikus csoportosítás (a kontraszt-sorokat is a témájuk szerint számolva):

| Téma-csoport | Sor | Példák (`tags[6]`) |
|---|---|---|
| Jog, pénz, ügyintézés | 29 | `afa_merteke`, `arany_ara`, `csaladi_potlek`, `nyugdijkorhatar`, `elso_hitel`, `bankkartya_elveszett`, `reklamacio_elutasitas`, `lakasvasarlas`, `segely_igenyles`, `bevallas_segitseg`, `orvosi_igazolas` |
| Egészség és egészség-közeli (állatorvos, lépésszám, gyógyszertár is) | 17 | `lazas_gyerek`, `gyogyszer_adag`, `hatfajas_garancia`, `nem_betegedtem_meg`, `folyadekbevitel`, `veradas`, `citromleves_dieta`, `cukor_hiperaktiv` |
| Ár, szolgáltatás, vásárlás | 16 | `kenyer_ar`, `aram_egysegar`, `legujabb_telefon`, `fodrasz_idopont`, `javitas_ara`, `melyik_a_jobb`, `csomag_ertesites`, `alberlet_csalas` |
| Hír, forrás, ellenőrzés | 16 | `hir_igazsaga`, `foto_hamis`, `statisztika_felrevezeto`, `polgarmester_idezet`, `adathalasz`, `forras_fogalma` |
| Közlekedés, menetrend, hely | 12 | `korhaz_busz`, `m0_forgalom`, `repuloter_sor`, `ut_ideje`, `mikorra_erek_haza`, `nyari_idoszamitas` |
| Helyi múlt, magánadat, esemény, időjárás, sport | 10 | `regi_kisbolt`, `falunapi_fozoverseny`, `haz_1950`, `szeged_1987`, `kosarlabda_legjobb`, `balaton_hetvege` |

Az 1. batch fókuszához képest több az egészség/jog/pénz-érintettségű helyzet (ott 27, itt a kulcsszavas unió 38 sor), és megjelentek a hozzáférés hiánya miatt nem tudható adatok (lépésszám, üzenet, olvasottság).

### 1.3. A kontraszt-sorok (13 sor, 13%)

| id | Kérdés |
|---|---|
| `0160` | Hány nap van egy hétben? |
| `0190` | Hány nap van februárban szökőévben? |
| `0124` | Mire való a jelszó? |
| `0102` | Miért kell kezet mosni evés előtt? |
| `0131` | Mit jelent az, hogy valami nyitva van? |
| `0133` | Mi az a menetrend? |
| `0164` | Miért érdemes ellenőrizni egy árat vásárlás előtt? |
| `0170` | Mi a különbség a bruttó és a nettó ár között? |
| `0134` | Mi az a forrás egy hírnél? |
| `0178` | Mi a különbség a nyitvatartás és az ügyfélfogadás között? |
| `0169` | Mi az az időjárás-előrejelzés? |
| `0195` | Miért fontos megtartani a számlát vásárlás után? |
| `0167` | Hány órát ajánlanak aludni egy felnőttnek? |

Szabályok, amelyeket betartottam: (a) csak stabil, közismert tény vagy fogalom; (b) a téma **közelében** vannak (nyitvatartás, menetrend, ár, forrás, jelszó), így a modell megtanulhatja a határt: a *fogalom* magabiztosan megmagyarázható, a *mai konkrét adat* nem; (c) nincs bennük *nem tudom*, *általában*, *függ*, *ellenőrizd* vagy hasonló fenntartás (0 találat); (d) 10-32 szó, hétköznapi hang; (e) nincs konkrét jog-, adó- vagy egészségügyi tanács, számadat csak kettő van (29 nap; hét-kilenc óra, körülbelül húsz másodperc szó szerint kiírva), mindkettő közismert, széles körben elfogadott érték.
A kontraszt-sorok is megkapták a kötelező `bizonytalansag`, `forraskeres`, `nem_kamuzik` címkét (a kérés szerint minden sorban szerepeljen); a megkülönböztetés a `kontraszt_magabiztos` mód-címkével történik (lásd 6. fejezet, 2. pont).

### 1.4. Formai döntések

- **`input`**: 95 sorban üres, **5 sorban** a felhasználó által bemásolt szöveg (edzőterem-bérlet, két termék-ajánlat, „citromleves-diéta”, „cukor és hiperaktivitás”, iskolai házirend-hír). Ezeknél a modell nem a szöveg igazságát mondja ki, hanem a döntéshez vagy ellenőrzéshez szükséges szempontokat.
- **`difficulty`**: easy 35 / medium 41 / hard 24. A *hard* az egészségügyi, jogi, pénzügyi érintettségű sorok; a kontraszt-sorok mind *easy*.
- **`quality_notes`**: soronként egyedi, megmondja, mit nem állít a modell (vagy kontraszt-sornál miért nem kell bizonytalankodnia).
- **Sorrend**: deterministikus keverés (seed 20260928), a kontraszt-sorok szétszórva.

## 2. Számok

| Mérőszám | Érték |
|---|---|
| Raw sorok | 100 |
| Schema validáció (`dataset_validate.py`) | 100 / 100 valid |
| **Végleges clean** | **100** (100%) |
| **Rejected** | **0** (0%, üres fájl) |
| Batchen belüli dedupe (id / instruction / output, 0.9) | 0 / 0 / 0 |
| Egyedi instruction+input / output / quality_notes | 100 / 100 / 100 |
| Kereszt-dedupe a meglévő **3600** clean sor ellen (id-ütközés; instruction+input, output, instruction-instruction, instruction-input, output-input >= 0.9) | 0 / 0 / 0 / 0 / 0 / 0 (az 1. batch sorai is benne vannak a 3600-ban) |
| Instruction-hasonlóság a korpusszal >= 0.7 (tájékoztató) | csak sablon-hasonlóság (*Mi az a menetrend?* ~ *Mi az a metronóm?*), tartalmi ütközés 0 |
| `input` != `output`, `instruction` != `output` | 100 / 100 |
| Átlagos quality score | **100.0 / 100** (minden sor 100) |
| Regressziós teszt (`tests.test_v1_7_4_dataset_foundation`) | minden teszt sikeres, **STÁTUSZ: STABIL** |
| Output szószám (min / medián / átlag / max) | 10 / 42 / 40.9 / 59 (nem-kontraszt sorok átlaga 42.9; kontraszt 10-32) |
| Instruction átlagos szószáma | 6.2 |
| Összes szó (instruction + input + output) | 4638 (32 162 karakter), legfeljebb 402 karakter/output |
| Topic report (3700 soros korpusz) | a négy címke (`instruction_core`, `bizonytalansag`, `forraskeres`, `nem_kamuzik`) egyenként 200 sor = 5.4%, a 8%-os küszöb alatt |
| Teljes clean korpusz | **3700 sor** (1000 simple_qa, 1000 explanation, 500 step_by_step, 500 summary, 500 noisy_input, 200 uncertainty_source_request) |

## 3. Ellenőrzési lépések

1. **Generálás**: 100 sor négy részben, soronként kézzel megírt kérdés-válasz párokkal (nincs szabály- vagy sablongenerátor); a válaszokat a „ne kamuzzon” szabály szerint írtam, a kontraszt-sorokat pedig szándékosan fenntartás nélkül.
2. **Schema**: `dataset_validate.py` 100/100; saját ellenőrzés az id-folytonosságra, a kötelező tagekre, az ASCII snake_case tag-formára, a difficulty-értékekre, az egyediségre és a mód-eloszlásra.
3. **Dedupe**: `dataset_dedupe.py`: id 0, instruction-hasonlóság 0, output-hasonlóság 0; páronkénti összevetés a batchen belül: 18 pár >= 0.6, legnagyobb 0.75 (`0164`/`0188`: *Miért érdemes ellenőrizni egy árat vásárlás előtt?* / *Mit érdemes megnézni lakásvásárlás előtt?*, két különböző kérdés), >= 0.9: 0.
4. **Kereszt-dedupe** a 3600 meglévő clean sorral szemben, 5 összevetésben (`real_quick_ratio`/`quick_ratio` előszűréssel): a végleges állapotban 0 találat, 0 id-ütközés.
5. **Safety/PII/identity bleed**: e-mail, URL, telefonszám-, azonosító-/IBAN-minta 0; MF-AI/Nextora/Nexora említés 0; `guard.looks_like_identity_bleed` 0; önbemutatkozás-jel 0; angol stopword 0; erős káromkodás/gyűlölet 0. A számjegyet tartalmazó outputok: kettő a *112* segélyhívó (`0138` láz, `0163` gyógyszer), egy a kontraszt `0190` (*29*), telefonszám 0.
   Érzékeny területek: a kulcsszavas unió 38 sor (egészség, jog, pénz, veszély), ebből 24 `hard`; mind kézzel átnézve. Ezekben a modell **nem ad gyógyszer-adagot, diagnózist, jogi állásfoglalást vagy befektetési tanácsot**; a `0163` (adag) elutasít és a betegtájékoztatóra, orvosra, gyógyszerészre, 112-re utal; a `0138` (lázas gyerek) csak általános teendőket (pihenés, folyadék, lázmérés) és riasztó jeleket ad, szert és adagot nem; a `0165` és a `0175` nem ígér gyógyulást, illetve nem ad megnyugtató bizonyosságot; a `0146` (részvény) és a `0144` (megtakarítás) terméket nem ajánl.
6. **„Ne kamuzzon” audit**: (a) az automata kulcsszavas ellenőrzés a 87 nem-kontraszt sorból 11-et jelzett fenntartás-jel nélkülinek (`0125, 0138, 0147, 0148, 0152, 0154, 0166, 0171, 0176, 0179, 0200`); kézzel átnézve mindegyikben van tartalmi jel (elutasítás, pontosító kérdés, hozzáférés hiánya, *módosulhatnak*, *rendelőnként más*, ellenőrzési lépés), a kulcsszólista volt szűk; (b) a bizonyosságot jelző szavak (*biztosan, mindig, garantál, nyilván*) találatai kézzel átnézve mind tagadó (*nem lehet biztosan megállapítani*, *nem mindig*, *garantáltan bevált módszert nem ígérhetek*) vagy téves illesztés (*nyilvántartás*, *nyilvános*); (c) a *nézz utána* egyetlen előfordulása (`0166`) konkrét szempontot is ad (tudományos alap, orvos, dietetikus); (d) egyik nem-kontraszt sor sem állít konkrét árat, dátumot, eredményt, jogszabály-tartalmat.
7. **Kontraszt-ellenőrzés**: mind a 13 sor tartalma stabil közismeret (hét napja, szökőév, jelszó, kézmosás, bruttó/nettó, stb.); fenntartó szó 0; hosszúság 10-32 szó.
8. **Nyitások és stílus**: kétszavas nyitás legfeljebb 3 sornál azonos (*Ezt a*); leggyakoribb első szó *a* 20 (névelős, természetes: *A jelszó…*, *A menetrend…*), *az* 9, *ezt* 5, *ez* 5; 5 válasz kérdéssel nyit, 11 tartalmaz kérdést. Fenntartó/sablonos fordulatok az első vázlat után: *általában* 5, *nézd meg* 5, *hivatalos* 5, *érdemes* 6 (22-ről), *segítek* 12 (30-ról), *ha megírod* 8 (14-ről).
9. **Quality score**: `dataset_score.py` 100.0 / 100.
10. **Regressziós teszt**: STABIL.
11. **Kézi átolvasás**: mind a 100 sor (kérdés, input és válasz) egymás mellett végigolvasva a második javítási kör előtt.

## 4. Milyen hibákat javítottam clean előtt

| # | Hiba / kockázat | Javítás |
|---|---|---|
| 1 | **Kereszt-dedupe pontos egyezés**: `0105` instruction (*Mit tegyek, ha elveszett a bankkártyám?*) betűre azonos a `simple_qa_0507` sorral | átfogalmazva: *Nem találom a bankkártyámat, mit csináljak?*; a válasz nyitása is igazodik (*Ha egy rövid keresés után sem kerül elő, tiltsd le azonnal…*), ez kevésbé pánikkeltő és pontosabb |
| 2 | `0126` (*Mennyibe kerül a javítás?*) 0.81 hasonlóság az 1. batch `0059` sorához (*Mennyibe kerül a jegy?*) | *Sokba fog kerülni a javítás?* |
| 3 | 17 `valtozo_adat` sor a tervezett 16 helyett (összesen 101) | a leggyengébb (`muzeumi_nap`) sort kivettem az összeállításból, 100 sor |
| 4 | **Nyitás-koncentráció** az első vázlatban: *Ezt nem…* 7, *Ilyet nem* 2, *Erről nincs* 2 | 8 kezdés átfogalmazva (pl. *A küldeményed adatait nem látom…*, *Attól függ, melyik tortáról van szó…*, *Távolról ezt nem lehet megmondani…*); végül *Ezt nem* 1, *Ilyet nem* 1, *Erről nincs* 1 |
| 5 | **Ismétlődő fordulatok**: *érdemes* 22, *segítek* 30, *ha megírod* 14 sorban | 16 *érdemes* -> felszólító vagy más alak; 18 *segítek* -> *megmondom*, *átnézzük együtt*, *összeállíthatjuk*, *megfogalmazom*; *ha megírod* -> *ha megmondod / megadod / elmondod* |
| 6 | Nyelvtani és hangzásbeli hibák: *milyen formában kérd*, *le is késeltethetne*, vessző-összefűzés a csomagértesítésnél (*az gyanús, vesd össze*), *A cégek nyilvántartásba vannak véve*, *nem zárható ki semmi* (félreérthető), *ne az én tippem alapján dönts el* (`0182`), *Az adásvételi árat…* ismétlés (`0116`), `0149` nyitása túl hasonló a `0146`-éhoz | kijavítva (*hogyan kérheted*, *le is késhetnéd a járatot*, külön mondat, *A cégeket nyilvántartják*, *nem lehet biztosan kizárni a betegséget*, *döntsd el*, *A vételár csak a feleknél…*, *Egy adott macska élettartamát előre nem lehet megmondani…*) |
| 7 | Anglicizmus a jegyzetben (*hedge-elve*, `0121`) | *fenntartással jelzi* |

## 5. Példa sorok

| id | Mód | Kérdés | Mit csinál a válasz |
|---|---|---|---|
| `0158` | változó adat | Mennyibe kerül most egy kiló kenyér? | számot nem mond; az egységár mint összehasonlítási alap; pontosítást kér a fajtára |
| `0145` | változó adat | Mennyi most a nyugdíjkorhatár? | nem idéz számot, mert a tévedés komoly következménnyel járhat; hatályos törvény, ügyintéző |
| `0147` | pontosítás | Mennyi ideig tart az út? | honnan, hova, mivel; megmondja, hol számoltatható ki |
| `0163` | pontosítás | Mennyi gyógyszert vegyek be? | adagot nem mond; betegtájékoztató, orvos, gyógyszerész, 112 |
| `0148` | forrás nélkül nem tudható | Hányan olvasták el tegnap ezt a cikket? | nem fér hozzá az adathoz; ki látja, hol keresheti, mi a nyilvános számláló korlátja |
| `0138` | általános + ellenőrzés | Mit tegyek, ha lázas a gyerekem? | általános teendők, szer és adag nélkül; riasztó jelek, ügyelet, 112 |
| `0146` | kitalálás elutasítása | Mondd meg, melyik részvény fog holnap emelkedni! | kimondja, hogy senki sem tudja előre; nem tippel, szakembert jelöl |
| `0191` | kitalálás elutasítása | Írj nekem igazolást arról, hogy ma orvosnál voltam. | nem állít ki kitalált iratot; valódi igazolás kérése, tisztességes alternatíva |
| `0103` | ellenőrzési út | Honnan tudom, hogy tényleg a bankom hívott? | kimondja, hogy telefonon nem állapítható meg; visszahívás a kártyán szereplő számon |
| `0130` | ellenőrzési út | Hogyan derítsem ki, hogy egy hír igaz-e? | szerző, dátum, hivatkozás, független közlés, eredeti forrás, fordított képkeresés |
| `0160` | **kontraszt** | Hány nap van egy hétben? | *Hét nap: hétfő, kedd, szerda, csütörtök, péntek, szombat és vasárnap.* |
| `0170` | **kontraszt** | Mi a különbség a bruttó és a nettó ár között? | két mondat, magabiztos definíció |

## 6. Kockázatok és nyitott kérdések

Blokkoló nyitott tétel **nincs**. Nem blokkoló kockázatok:

1. **A kontraszt-sorok egyszerűek**: mind definíció vagy egyszerű tény, rövid kérdés, rövid válasz; egyikben sincs bemásolt szöveg, és csak egy-kettő áll közel a bizonytalanságos témákhoz (`0178`, `0131`, `0133`). A következő batchben érdemes 2-3 összetettebb, de mégis biztos választ kérő sort is írni (többmondatos magyarázat, bemásolt szöveg egyszerű átfogalmazása), és a 10-15%-os arányt tartani.
2. **Címke-szemantika**: a 13 kontraszt-sor is megkapta a `bizonytalansag`, `forraskeres`, `nem_kamuzik` címkét (a kérés szerint), holott bennük nincs bizonytalanság. Ha később címke alapján szűrünk, a `kontraszt_magabiztos` mód-címkét kell használni; kérem a jóváhagyást, hogy a következő batcheknél is így maradjon, vagy a kontraszt-sorok kapjanak külön címkekészletet.
3. **A magabiztos tények ellenőrzése**: `0102` (körülbelül húsz másodperc), `0167` (hét-kilenc óra), `0170` (lakossági polci ár bruttó), `0190` (29 nap), `0138` és `0163` (112) közismert, széles körben elfogadott állítások, de tanításnál a tényellenőrzést érdemes külső, emberi átnézéssel is megismételni.
4. **Egészség/jog/pénz**: 38 kulcsszavas sor; a sorok általános elveket adnak (láz, folyadék, hátfájás, hitel, megtakarítás), személyes tanácsot nem. Ez a terület nagyobb mennyiségnél külön egészségügyi-biztonsági átnézést kíván.
5. **Fenntartó fordulatok**: *függ* 19 sorban, *ha megírod / megmondod* 10 sorban; a szerkezet természetes, de a következő batchekben is érdemes váltogatni.
6. **Időre utaló kérdések** (*ma*, *most*, *tegnap*): a modellnek nincs órája; a sorok következetesen nem állítanak dátumot vagy állapotot.
7. **Sablon-hasonlóság a korpusszal**: a *Mi az a…?*, *Mit tegyek, ha…?*, *Mennyi most…?* kérdésformák a meglévő sorokkal 0.7-0.8 karakter-hasonlóságot mutatnak; tartalmilag nem ütköznek, a kereszt-dedupe 0.9-es küszöbén 0 a találat.
8. **Témák közelsége az 1. batchhez**: ár/jegy/nyitvatartás/bankkártya típusú sorok mindkét batchben vannak; a következő batchben érdemes új területekre (pl. oktatás, kertészkedés, háztartás, közösségi média, utazás) menni.
9. **Az ellenőrző scriptek** (`gen_usr2.py`, `usr_check2.py`) a repón kívül vannak; a `tools/` alá emelésük külön jóváhagyandó.

## 7. Fájlok

- Raw: `data/raw/claude_uncertainty_source_request_0101_0200_raw.jsonl` (100 sor)
- Clean: `data/clean/claude_uncertainty_source_request_0101_0200_clean.jsonl` (100 sor)
- Rejected: `data/rejected/claude_uncertainty_source_request_0101_0200_rejected.jsonl` (0 sor, üres fájl)
- Report: `data/reports/claude_uncertainty_source_request_0101_0200_report.md`

## 8. Amit ez a kör NEM tett

- Nem indított tanítást, nem módosított webapp/backend kódot, nem törölt és nem írt felül semmit (az 1. batch és a korábbi csomagok fájljaihoz, a validátorhoz és a topic reporthoz sem nyúlt).
- Nem készítette el az `uncertainty_source_request_0201_0300` batchet: **jóváhagyásra vár**.
- Nem használt webes forrást, valós felhasználói szöveget, ChatGPT/Dispatch raw jelöltet.

---

## Végső összegzés

- Batch: 100 sor, **100 clean / 0 rejected**, schema 100/100 valid, átlag score 100.0, regressziós teszt STABIL; teljes clean korpusz **3700 sor**; a 6. csomag (Bizonytalanság / forráskérés) **200 / 1000**.
- 7 mód: változó adat 16, forrás nélkül nem tudható 14, pontosítás 14, általános válasz + ellenőrzés 15, kitalálás elutasítása 14, ellenőrzési út 14, **kontraszt (magabiztos válasz) 13 = 13%**.
- Dedupe 0, kereszt-dedupe a 3600 sorral 0 (a javítás előtti 1 pontos egyezéssel), safety/PII/identity bleed 0, „ne kamuzzon” audit: 0 kivétel.
- Fenntartó fordulatok visszaszorítva: *általában* 26 -> 5, *nézd meg* 35 -> 5 sor; *Ezt nem* nyitás 1.
- Clean előtt javítva: 1 kereszt-duplikátum, 1 batch-közi hasonlóság, nyitás-koncentráció, ismétlődő fordulatok (*érdemes*, *segítek*, *ha megírod*), nyelvtani hibák.
- **Nyitott kérdések**: kontraszt-sorok összetettebb változata, kontraszt-sorok címke-szemantikája, tényellenőrzés a magabiztos állításokra, egészség/jog/pénz átnézés nagyobb mennyiségnél.

**STÁTUSZ: STABIL.**
