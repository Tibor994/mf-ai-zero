# 6. csomag — `uncertainty_source_request` (Bizonytalanság / forráskérés) — 1000 soros completion audit

> **Javítás (2. audit-kör, `v1.13.16`):** a 6. szakasz forrás-lefedettségi táblája és az „összesített kép” **helyesbítve és felváltva** a `uncertainty_source_request_1000_audit2_closure.md` soronkénti táblázatával (a batch 7 kontraszt-sorai *nem* voltak dokumentáltan forrásolva; a 13+24+28+59 összeg az 1 „közvetett” sort kihagyta). A 12. szakasz nyitott tételeinek állapota a 2. audit-kör jelentésében van.


Dátum: 2026-09-25
Auditált adatverzió: a `data/clean/claude_uncertainty_source_request_0001_0100_clean.jsonl` … `_0901_1000_clean.jsonl` (10 fájl, 1000 sor) **végleges állapota**, a jelen audit közben végzett tartalmi javításokkal együtt (a javítások commitja a 9. szakaszban). A vizsgált teljes clean korpusz: 4500 sor (49 fájl).

## Verdikt

**A csomag darabszáma és szerkezete teljes (1000/1000, hibátlan séma, folytonos azonosítók, 0 duplikáció 0,9 fölött), és blokkoló hiba nem maradt. Az „auditált, lezárt” minősítést azonban csak korlátozottan adom meg**, mert a lefedettség nem egyenletes: a szerkezeti, duplikációs, biztonsági és „kemény” (hard) soros tartalmi átnézés a teljes csomagra elvégzett, a tényállítások forrásellenőrzése viszont csak részben közvetlen (lásd 6. szakasz), a nem-hard sorok többségének utólagos újraolvasása pedig a batchek saját átolvasására támaszkodik. A nem blokkoló, nyitva maradt tételek a 12. szakaszban vannak. A 100-as automatikus pontszám önmagában nem bizonyít tartalmi hibátlanságot.

Korábbi auditfutások/riportok eredményét **nem használtam fel** bizonyítékként: minden itt szereplő szám az itt leírt módszerrel, a végleges adatverzión lett újraszámolva; a korábbi batch riportokból csak a *forrásjegyzékeket* és a *nyitott tételek listáját* vettem át, külön megjelölve.

---

## 1. Darabszám, azonosítók, folytonosság, séma

Eszköz: `audit_pkg.py struct` (scratchpad, a repón kívül) + `tools/dataset_validate.py`, `dataset_score.py`, `dataset_dedupe.py` fájlonként.

| Ellenőrzés | Eredmény |
|---|---|
| Sorok | 1000 (10 × 100) |
| Azonosítók | `uncertainty_source_request_0001` … `_1000`, fájlsorrendben folytonos, 1000 egyedi, hiányzó 0, extra 0 |
| 9 mezős séma | mezősorrend, típusok, `source` = `synthetic_claude_magyar`, `difficulty` ∈ {easy, medium, hard}: hibás sor 0 |
| `tools/dataset_validate.py` fájlonként | 10/10 fájl: 100 érvényes, 0 elutasított |
| `tools/dataset_score.py` fájlonként | 10/10 fájl: átlag 100.0/100 |
| `tools/dataset_dedupe.py` fájlonként | 10/10 fájl: id 0, instruction 0, output 0 |
| Egyedi `instruction+input` / `output` / `quality_notes` | 1000 / 1000 / 1000 (az audit előtt `quality_notes` 998 volt, két sor azonos jegyzetet viselt, javítva) |
| Nehézség | easy 495, medium 378, hard 127; inputos sor 46 |

## 2. Módok, címkék, kontrasztpéldák tényleges aránya

| Mód (`tags[5]`) | Db |
|---|---|
| `valtozo_adat` | 152 |
| `ellenorzesi_ut` | 147 |
| `kitalalas_elutasitasa` | 144 |
| `forras_nelkul_nem_tudhato` | 144 |
| `pontositas_kell` | 144 |
| `altalanos_valasz_ellenorzessel` | 144 |
| `kontraszt_magabiztos` | **125 (12,5%)** |

- Minden sorban az első 5 tag a csomagjelölő (`magyar`, `instruction_core`, `bizonytalansag`, `forraskeres`, `nem_kamuzik`), a 6. tag érvényes mód, a 7. tag ASCII snake_case téma (kind). **Csak jóváhagyott plusz-címkék** szerepelnek (`hibas_elofeltevesjavitas` 36, `igaz_elofeltevesmegerosites` 23, `reszben_igaz_elofeltevespontositas` 15), kizárólag kontraszt-soron, és a `fp_`/`tp_`/`rp_` kind-előtag mindig a megfelelő plusz-címkével jár együtt.
- **A kind-címkék 979/1000 egyediek.** 14 címke ismétlődik (`ugyintezes` 5×, `idezet`, `nyitvatartas`, `termekadat`, `szerencsejatek` 3–3×, további 9 címke 2×): ezek az 1–2. batch tág témacímkéi, a sorok tartalma eltér (1000 egyedi instruction+input). Nem hiba, de a címke kevéssé informatív.
- **A kontraszt-sorok tényleges összetétele** (a 125 sor): hibás előfeltevés javítása 36, igaz előfeltevés megerősítése 23, részben igaz pontosítása 15 — **összesen 74 (59%) valódi előfeltevés-alapú kontraszt** —, egyértelműen megoldható feladat (`ct_`) 12, és **39 előtag nélküli, plusz-címke nélküli sor** (főként a 2.–3. batchből: fogalommagyarázat, hétköznapi tanács, pl. `het_napjai`, `menetrend_fogalma`, `jelszo_szerepe`). Ez az utóbbi 39 sor az előfeltevés-altípusok bevezetése előtt készült, „magabiztos válasz” jellegű; a csomag terve szerinti 14 kontraszt-sorból álló, altípusonként elosztott szerkezet a 4. batchtől (0301–0400) egységes. Nyitott tétel: a 39 sor újracímkézése vagy átdolgozása külön jóváhagyással.
- Batchenként (kontraszt / plusz-címkék): 0001–0100: 0; 0101–0200: 13 (nincs plusz-címke); 0201–0300: 14; 0301–0400: 14 (10 hibás); 0401–0500: 14 (6 hibás, 4 igaz); 0501–0600: 14 (3/3/4); 0601–0700: 14 (4/4/3); 0701–0800: 14 (5/4/2); 0801–0900: 14 (4/4/3); 0901–1000: 14 (4/4/3).

## 3. Biztonság és személyes adat (mind az 1000 sor, minden szöveges mező + tagek)

| Szűrő | Találat |
|---|---|
| e-mail, URL/domén, telefonszám-szerű, IBAN/adóazonosító, MF-AI/Nextora/Nexora említés | 0 (az audit közben egy `quality_notes` mezőben talált domén-szöveget eltávolítottam, lásd 9. szakasz) |
| identitás-átszivárgás (`src/guard.py: looks_like_identity_bleed`) | 0 |
| önbemutatkozás-jelek az outputban | 0 |
| erős káromkodás / gyűlöletbeszéd kulcsszó | 0 |
| a tiltott, előíró jellegű minták keresése az outputban (adagolás, diagnózis-állítás, befektetési ajánlás, jogi verdikt, adókulcs) | 4 kulcsszavas találat (`0086`, `0291`, `0525`, `0956`), mind álpozitív (általános ellenőrzési lépés, nem előírás) |

## 4. Belső ismétlések és átfedések a többi csomaggal

### 4.1 Módszer és hatókör

- **Végső, teljes korpuszos futás** (`dd_full.py`, 4500 sor, N×N, `instruction||input`, `output`, `id`, küszöb 0,9, szakaszolt, 23/23 szakasz, 27 mp): id 0; output ≥ 0,9: 0; instruction||input ≥ 0,9: 7 pár, **mind a `simple_qa` és `step_by_step` csomagokban** (lista a batch riportban, 1.3 szakasz). Az `uncertainty_source_request` csomag egyetlen sora sem érintett.
- **Csomag-szintű 5 irányú futás** (`audit_pkg.py pairs`, szakaszolt, 10×100 soros részeredmények mentve): `instruction||input`, `output–output`, `instruction–instruction`, `instruction–input(zajos)`, `output–input(zajos)`; belül (1000×1000) és a többi 3500 sorral szemben. **0,9 fölött 0 találat mind az 5 mezőpárra, mindkét hatókörben.**
- A módszer az eredeti `tools/dataset_dedupe.py` `find_duplicates()` szemantikájával azonos (bizonyítás: a batch riport 1.3 szakasza), a küszöb és a minőségi követelmény nem lett gyengítve; az elő-szűrők matematikailag pontos felső korlátok.
- **A jelen audit előtt megszakadt teljes korpuszos futás** (`tools/dataset_cross_dedupe.py`, 11+ óra, kimenet nélkül, leállítva) eredményét nem használtam. Lásd a batch riport 1. szakaszát.
- Nem volt a hatókörben: `input–output`, `input–input`, `quality_notes` páronkénti összevetés (a repó eszközei sem vizsgálják).

### 4.2 A 0,8–0,9 közötti (küszöb alatti) találatok tartalmi értékelése

Csomagon belül 12 pár (`instruction||input` ≥ 0,8), a többi csomaggal szemben 27 pár. Mindegyiket megnéztem (kérdés és válasz). **Kiemelten:**

| Pár | Hasonlóság | Tartalmi értékelés | Döntés |
|---|---|---|---|
| `0842` ↔ `0174` (mai lépésszám) | 0,88–0,90 | tartalmi ismétlés | **cserélve** (9. szakasz) |
| `0641` ↔ `0404` (kvíz-app vs. app adatgyűjtése) | 0,81 | a válasz is tartalmilag ismételt (engedélyek, adatkezelési tájékoztató) | **válasz átírva** a kvízekre jellemző szempontokra (9. szakasz) |
| `0933` ↔ `0818`, `0898` ↔ `0818`/`0076` (Milyen gyakran kell cserélni…) | 0,80–0,86 | azonos sablon, más tárgy, más tényanyag | megtartva; a mód lényege az „átlag + saját ellenőrzés” |
| `0135` ↔ `0065` (áfa vs. benzinár), `0843` ↔ `0059` (javítás vs. jegyár), `0941` ↔ `0097` (sorozat: cselekmény vs. megjelenés), `0680` ↔ `0487` (árverés vs. kupon), `0837` ↔ `0084` (melyik verzióra frissítsek vs. melyik a legfrissebb), `0169` ↔ `0021`, `0259` ↔ `0137`, `0498` ↔ `0362`, `0898` ↔ `0076` | 0,80–0,84 | eltérő tárgy vagy információtípus, azonos kérdéssablon | megtartva |
| Más csomagokkal: `0419`↔`simple_qa_0201`, `0252`↔`simple_qa_0203`/`0305`, `0170`↔`simple_qa_0988` stb. (27 pár, 0,80–0,89) | 0,80–0,89 | rövid „Hogyan tisztítsam/válasszak…”, „Mi az a…” kérdéssablonok különböző tárgyakra; a `simple_qa` válaszok 1–2 mondatosak | megtartva |
| `0277` (szülői felügyelet gyerek telefonján) ↔ `simple_qa_0271` (szülői felügyelet) | 0,80 | témaazonos, de az `uncertainty` válasz típusfüggő menüpontokra és ellenőrzésre hivatkozik | megtartva, **megfigyelés** (nyitott, nem blokkoló) |

## 5. Témaváltozatosság, nyitások, visszatérő válaszsablonok (mind az 1000 sor)

Eszköz: `audit_pkg.py style`.

- **Instruction-nyitás** (első két szó): `mondd meg` 36 (3,6%, döntően a `kitalalas_elutasitasa` módban, ahol a kérés természete ez), `hogyan ellenőrizzem` 30 (**az `ellenorzesi_ut` mód 147 sorának 20%-a**), `találd ki` 21, `mennyi most` 14, `mennyibe kerül` 13, `honnan tudom` 13, `hogyan derítsem` 13, `mire figyeljek` 13. A 818 kérdőjeles / 182 kérdőjel nélküli instruction.
- **Válasz-nyitás:** `ezt nem` 20, `erről nincs` 14, `nézd meg` 12, `igen ez` 11 (a kontraszt-módban ez a várt megerősítő nyitás), `a pontos` 9, `a mai` 8.
- **Visszatérő válaszsablon (valódi megfigyelés):** a „…és azt sem tudom, melyik …” szerkezet **49 sor** outputjában szerepel (4,9%); a „nem ismerem, és azt sem tudom”, „nem látom, és azt sem tudom” háromszavas variánsai együtt 30+ sor. Ezek főként a `pontositas_kell` és `forras_nelkul_nem_tudhato` módokban vannak, és a korábbi batchek (kb. 1–8.) terméke; a 9–10. batch tudatosan más szerkezeteket használ. **Nem blokkoló, de valós minőségi tétel**, amit a jelen audit nem javított (a korábbi batchek több tucat sorát érintené).
- **Visszatérő szavak (a sorok %-a az outputban):** `ezért` 24,8%, `pontos` 17,9%, `függ` 13,9%, `érdemes` 13,7%, `nem tudom` 13,3%, `hivatalos` 8,8%, `nézd meg` 8,4%, `orvos` 7,0%. `ehhez pontosítás kell` 0,4% (4 sor).
- **Output-hossz** (szó, min/medián/átlag/max): módonként 33–46 átlag; a kontraszt-módban 10–103.
- **Témák:** a `tags[6]` szavai szerint a leggyakoribb tematikus tokenek: `elso` (22), `regi` (20), `telefon` (16), `helyi`, `hamis` (13–13), `szomszed` (12). A témák a személyes-fogyasztói életterületek mellett a 10. batchben új területekkel (tudásbeli határ, mértékegység, informatikai ellenőrzés, háztartás) bővültek; a korábbi 900 sor tartalmi térképét a 10. batch tervezésekor átnéztem (batch riport 2.1). **Hiányosság:** az első 8 batch témái a személyes és fogyasztói helyzetekre koncentrálnak, tudományos/történelmi ismeret-határ kérdésből csak a 9–10. batchben van érdemi mennyiség.

## 6. Forrásellenőrzések — lefedettségi táblázat

Jelölés: **K** = a forrást ebben az auditban/batchben közvetlenül megnyitottam és elolvastam; **Ö** = csak keresési összefoglaló alapján; **A** = nem tartalmaz forrásfüggő tényállítást (definíció, számolás, logika); **D** = általános hétköznapi tanács vagy vélemény, forrás nélkül; **R** = a batch riportja szerint forrásolt, ebben az auditban nem ellenőriztem újra.

| Batch | Kontraszt-sorok | Forrásellenőrzés |
|---|---|---|
| 0101–0200 | 13 | 2 sor tényállítással: `0102` kézmosás 20 mp (CDC, **Ö**), `0167` alvás (AASM/CDC „legalább 7 óra” **Ö**; a „hét-kilenc” felső határ **nem forrásolt**, a válasz így is helyes irányú); 11 sor **A/D** |
| 0201–0300 | 14 | `0232` jelszó-újrahasználat (CISA-találat cím szintjén, **Ö**, gyenge); 13 sor **A/D** |
| 0301–0400 | 14 | 5 sor **Ö** (`0303` mosogatószer, `0328` hideg és megfázás [Cleveland Clinic/Harvard], `0364` cipő délután [APMA-jellegű összefoglaló], `0379` szellőztetés [Umweltbundesamt], `0388` felhők és UV [CDC/Skin Cancer Foundation]); 9 sor **A/D** |
| 0401–0500 | 14 | 6 sor **Ö** (`0402` lakat-ikon, `0419` zöldfűszer, `0425` kenyér a hűtőben, `0438` inkognitó [Google Chrome Súgó], `0472` izomláz, `0488` kétlépcsős azonosítás [CISA]); `0453` a batch 7 forrása (PMC12034053) által közvetve; 7 sor **A/D** |
| 0501–0600 | 14 | `0574` fém a mikróban [USDA FSIS], `0583` megapixel **Ö**; `0506`, `0518` **K** (Mayo Clinic, batch 7 és a 0801–0900 batch javítása); 10 sor **A/D** |
| 0601–0700 | 14 | **R** (batch 7 riport) |
| 0701–0800 | 14 | **R** (batch 8 riport); a `0708` a 0801–0900 batchben forrással újraírva (Google Play Console, Statista) |
| 0801–0900 | 14 | 8 sor **Ö** (`balkezesség`, `kávépörkölés`, `gyümölcslé`, `alma-etilén`, `kézírás`, `kék fény`, `C-vitamin`, `5 másodperces szabály`; a batch riportja szerint keresési összefoglalók: Cornell/ScienceDaily, McGill, kávépörkölő cikkek, Stanford/Cleveland Clinic, Mueller & Oppenheimer, Harvard Health/Sleep Foundation, Cochrane, Rutgers/Scientific American); 6 sor **A/D** (zár, fogászati szűrés, otthoni edzés, 3 számolás) |
| 0901–1000 | 14 | **K** a 11 fő állításra (NASA, NWS, USGS, NOAA×2, Smithsonian, EPA, hongkongi CFS, The Conversation, National Honey Board), másodlagos összefoglalók a részletekre; 3 sor számolás **A** |

**Összesített kép a 125 kontraszt-sorra:** közvetlenül olvasott forrás (K) 13 sor (`0506`, `0518` és a 0901–1000 batch 11 sora), keresési összefoglaló (Ö) 24 sor (2–6. és 9. batch), közvetett (a batch 7 forrásán át) 1 sor (`0453`), korábbi riportra támaszkodó (R) 28 sor (batch 7–8), forrást nem igénylő vagy általános tanács (A/D) 59 sor. **Az A/D besorolások az én besorolásaim, független emberi ellenőrzés nem történt.**

**A nem kontraszt módok számszerű állításai** (32 sor tartalmaz számjegyet, továbbá a betűvel írt számok): a 9–10. batch számszerű állításait az audit során ellenőriztem: WHO 150/300 perc (`0929`, **Ö**), WHO <5 g só (`0878`, **Ö**), ADA fogkefe 3–4 hónap (`0818`, **Ö**), NIST jelszócsere (`0984`, **Ö**), NFPA füstjelző (`0935`, **Ö**), USDA nyers csirke 1–2 nap (`0994`, **Ö**), OSHA monitor-távolság (`0965`, a „50–70 cm” az OSHA 50–100 cm tartományán belül, **Ö**), olajcsere (`0891`, a keresési összefoglalókban 5–10 ezer mérföld hagyományos, 7,5–15 ezer szintetikus olajnál, **Ö**), tulipánhagyma (`0922`, **Ö**), mérföld (`0988`), a magyar jogi számok (`0829`, `0849`, `0864` — lásd 9. szakasz), a fékbetét (`0898`, javítva), a tej (`0816`, javítva). **Nem forrásolt** (közismert, hedge-elt általános érték): `0809` hűtő 0–5 °C, `0840` ágyméret, `0844` garanciaidő, `0974` tészta főzési idő, `0991` kelesztés, `0953` törölköző mosási hőfok, `0876` alvás 7–9 óra (a 9 órás határ).

## 7. A korábban nyitott tartalmi tételek státusza

| Tétel (a progressz-fájl és a batch riportok szerint) | Státusz |
|---|---|
| `0518` első és második pontosítás (Mayo Clinic) | lezárva (`bad81c1`, `e97ba92`), a végső adatban szerepel |
| `0506` „rövid, rutinba ágyazott nyújtás” árnyalás | **nyitva maradt** (nem módosítottam új tartalmi indok nélkül) |
| `0541`, `0542`, `0545` tényellenőrzés | lezárva a batch 7-ben (Red Cross, CDC, Mayo Clinic, PMC) |
| `fp_ingyenes_app_haszna` (`0708`) forrás | lezárva (`e97ba92`) |
| `0743` ↔ `0663` tartalmi összehasonlítás | lezárva a 0801–0900 riportban: mindkettő megtartva, `0663` a 0601–0700 batchben van |
| batch-hivatkozás hibája (`0663`) | javítva a 0801–0900 riportban |
| a 34 egészség-közeli sor és a „9 hard” | tisztázva a 8. szakaszban |
| igaz előfeltevésű sorok, tényellenőrzés a magabiztos állításokra (0301–0500 nyitott) | a 0601–1000 batchekre teljesült; a 2–6. batchre ebben az auditban részlegesen pótolva (6. szakasz) |
| az `ellenorzesi_ut` mód sablon-ismétlődése | 8. batchtől javított; a korábbi batchek 29 `Hogyan ellenőrizzem…` nyitása megmaradt (5. szakasz) |
| a teljes korpuszos cross-dedupe | pótolva (4. szakasz) |
| scratchpad szkriptek `tools/` alá emelése | **nem történt meg** (kifejezetten nem kellett) |

## 8. Érzékeny (egészség-közeli, jogi, pénzügyi) sorok — a „34 sor / 9 hard → 8” eltérés tisztázása

**Az eltérés oka.** A 0701–0800 batch riportja két, egymástól független számot említett: (a) a batch egészének nehézségi eloszlását (`easy 56 / medium 35 / hard 9`), és (b) a „34 kulcsszavas sor, ebből 9 hard” mondatot a nyitott tételek között. A (b) mondat a (a) szám átvétele volt, tévesen a kulcsszavas részhalmazra vonatkoztatva. Az én korábbi újraszámolásom „8 hard” értéke a kulcsszavas halmazon *belüli* hard sorok száma volt egy szélesebb, mind a négy mezőre kiterjedő kulcsszókeresés mellett. **A két szám más mennyiségre vonatkozott; a fájl nem változott.** Tényleges adatok (a `80c87c1` commitban és most is azonosak):

- A 0701–0800 batch **9 hard sora:** `0701, 0714, 0724, 0731, 0735, 0743, 0759, 0778, 0786`.
- Kulcsszavas keresés az **output** mezőn: 25 sor, ebből hard 7 (`0701, 0714, 0724, 0735, 0743, 0759, 0778`); mind a négy szöveges mezőn: 29 sor, ebből hard 8 (a `0786` is bekerül); a `0731`-ben egyik módszerrel sincs kulcsszó.
- A „34” szám **nem reprodukálható**: az eredeti `usr_check8.py` a committált állapoton 27 találatot ad a négy lista összegeként (25 egyedi sor). A 34 forrása ismeretlen; a **sorazonosítók és besorolások az irányadók**, nem a 34-es szám.

**Tartalmi átnézés lefedettsége (teljes szövegű olvasás):**

| Halmaz | Sorok | Olvasás |
|---|---|---|
| 0701–0800: a 9 hard sor és a kulcsszavas sorok uniója | 30 | mind a 30 sor teljes szövege elolvasva az auditban |
| 0001–0700 batchek összes **hard** sora | 110 | mind a 110 sor teljes szövege elolvasva az auditban |
| 0801–0900 és 0901–1000 batchek hard sorai, illetve az összes sora | 3 + 5 hard; 200 sor | mind a 200 sor elolvasva a batch készítésekor |
| A 0001–0700 batchek kulcsszavas (egészség/jog/pénz/veszély), nem hard sorai | ~120 | **nem olvastam újra** az auditban (a batchek saját átolvasására támaszkodik); helyette mintaszerű, előíró jellegű kifejezésekre szűrtem (3. szakasz) |

**Eredmény:** a 127 hard sor egyike sem ad diagnózist, személyes jogi verdiktet, befektetési tanácsot vagy adagolást; mind elutasítja a találgatást, vagy szakemberhez/hivatalos szervhez irányít. Egy finom megjegyzés: `0663` (laboreredmény) a „gyulladásra utalhatnak” mondattal óvatos értelmezést ad, de kifejezetten diagnózis nélkül; ezt megtartottam.

Kulcsszavas és hard sorok batchenként (az 4 szöveges mező alapján): 0001–0100: 30/17, 0101–0200: 41/24, 0201–0300: 23/16, 0301–0400: 28/14, 0401–0500: 32/12, 0501–0600: 36/20, 0601–0700: 24/7, 0701–0800: 29/9, 0801–0900: 39/3, 0901–1000: 25/5 (kulcsszavas / hard).

## 9. Az audit közben végzett javítások (`v1.13.12-dataset-fix`)

Csak a clean fájlokban; a raw fájlok érintetlenek. A commit előtt mind a négy érintett fájl újra 100/100 valid, 100.0 pontszámú, 0 dedupe. A `git diff` pontosan 10 sort érint.

| Sor | Mi volt a baj | Régi → új (rövidítve) | Forrás / indok |
|---|---|---|---|
| `0787` (0701–0800) | „érvényes tartalomszolgáltatási engedély” nem ellenőrizhető szempont | „…van-e az oldalnak érvényes tartalomszolgáltatási engedélye” → „…elérhető-e átlátható cégadat, impresszum és adatkezelési tájékoztató” | tartalmi pontosítás, a többi mondat változatlan |
| `0816` (0801–0900) | a kérdés a lejárat *után* kérdez, a válasz a lejárat *előtti* felbontás utáni időt adta; a „3–5 nap” szűkebb volt a forrásokhoz képest | „…szavatossági időn belül… 3-5 napig” → „a lejárta utáni fogyasztás nem javasolt… felbontás után a tej hűtve jellemzően nagyjából 5–7 napig tartható el” | USDA-jellegű keresési összefoglalók (**Ö**) |
| `0829` | „általában 5 évig” pontatlan | → „az adómegállapítás elévülése alapesetben a bevallási év utolsó napjától számított öt év; a számviteli törvény hatálya alá tartozó vállalkozásoknál legalább nyolc év” | Art. és Sztv. 169. § keresési összefoglalók (**Ö**, magyar nyelvű szakoldalak) |
| `0849` | „legalább 3 év” hiányos, a 2025-ös szabályváltozás nélkül | → „általában az általános hároméves munkajogi elévülési időig, a könyvviteli bizonylatnak minősülőket legalább nyolc évig; a nyugdíjjal összefüggő iratok szabályai 2025 elejétől módosultak” | jogi szakoldalak keresési összefoglalói (**Ö**) |
| `0864` | „jellemzően 2 év” **félrevezető**: az alapszabály 6 hónap, a 2 év a megszakításokkal együtt a felső korlát | → „az elkövetéstől számított hat hónap után elévül, az eljárási cselekmények megszakítják, legfeljebb két évig lehetséges (szabálysértési törvény 6. §); a közlekedési igazgatási bírságokra külön szabályok is vonatkozhatnak” | a 2012. évi II. törvény szövege **K** (Nemzeti Jogszabálytár); a bírságokról egy szaklap cikke **K** |
| `0898` | „30–70 ezer km” alacsonyabb volt a forrásokban mérföldben megadott 25–65 ezer mérföldes (kb. 40–105 ezer km) tartománynál | → „több tízezer kilométer, jellemzően nagyjából 40–100 ezer km” | keresési összefoglalók (**Ö**) |
| `0842` | tartalmi ismétlés a `0174` sorral | `Hány lépést tettem ma eddig?` → `Melyik napon vásároltam a mosógépemet?` (kind: `mosogep_vasarlas_datuma`) | tartalmi cseréje egy új, forrás nélkül nem tudható helyzetre |
| `0641` | a válasz tartalmilag ismételte a `0404` sort | engedélyek/adatkezelési tájékoztató → a kvízekre jellemző szempontok (közösségi belépés, megosztás, névjegyzék-kérés) | tartalmi egyedisítés |
| `0317`, `0782` | azonos `quality_notes` a `0252`, illetve `0659` sorral | egyedi megfogalmazás | metaadat |
| `0864` `quality_notes` | domén-szöveg szerepelt a jegyzetben | domén nélküli forrásmegnevezés | URL-mentességi szabály |

A `0842` javítása miatt a `raw` és a `clean` egy sorban eltér (a 0801–0900 raw a generáláskori szöveg). A `0518` és `0708` korábbi javításai (commit `e97ba92`) a végső adatban benne vannak és a teljes korpuszos futásban szerepeltek.

## 10. Automatikus ellenőrzések — összesítés

| Ellenőrzés | Parancs | Eredmény |
|---|---|---|
| Séma, pontozás, dedupe fájlonként (10 fájl) | `tools/dataset_validate.py`, `dataset_score.py`, `dataset_dedupe.py` | 10/10: 100 érvényes, 0 elutasított, 100.0, 0/0/0 |
| Regresszió | `python -m unittest tests.test_v1_7_4_dataset_foundation` | minden teszt sikeres, STÁTUSZ: STABIL |
| Topic report | `python tools/dataset_topic_report.py data/clean` | 49 fájl, 4500 sor; a négy csomagjelölő címke (`instruction_core`, `bizonytalansag`, `forraskeres`, `nem_kamuzik`) egyenként 1000 sor, 22,2%, `[FIGYELEM]` |
| Teljes korpuszos duplikáció (N×N, 4500 sor) | `dd_full.py run 200` | id 0, output 0, task 7 (mind `simple_qa`/`step_by_step`) |
| Csomag-szintű 5 irányú (belül és a többivel) | `audit_pkg.py pairs` | 0 találat 0,9 fölött |
| Szerkezet, címkék, biztonság | `audit_pkg.py struct` | lásd 1–3. szakasz |

**Topic-report kivétel:** a négy csomagjelölő címke a 8%-os küszöb fölött van (22,2%), ez a felhasználó által jóváhagyott, dokumentált csomagjelölő-kivétel; az eszközt és a küszöböt nem módosítottam. A `zajos bemenet` és `összefoglalás` (11,1%) más csomagok jelölő-címkéi.

## 11. A csomag lefedettsége táblázatban

| Terület | Hatókör | Módszer | Státusz |
|---|---|---|---|
| Darabszám, azonosító, séma | 1000/1000 | automatikus + saját szerkezeti audit | **Kész** |
| Módok, címkék, kontraszt-arány | 1000/1000 | automatikus | **Kész** (a 39 előtag nélküli kontraszt-sor nyitott tétel) |
| Belső duplikáció ≥ 0,9 | 1000×1000, 5 mezőpár | szakaszolt, pontos elő-szűrt difflib | **Kész**, 0 találat |
| Átfedés más csomagokkal ≥ 0,9 | 1000×3500, 5 mezőpár | ugyanaz | **Kész**, 0 találat |
| Teljes korpusz N×N | 4500×4500, 3 mező | `dd_full.py` | **Kész**; 7 más-csomagi pár tartalmi értékelése nem történt meg |
| Küszöb alatti (0,8–0,9) tartalmi átfedés | 39 pár | kézi tartalmi összevetés | **Kész**, 2 sor javítva |
| Biztonság/PII, identity bleed | 1000/1000 | automatikus | **Kész** |
| Hard sorok tartalmi átnézése | 127/127 | teljes szövegű olvasás | **Kész** |
| Kulcsszavas nem-hard sorok újraolvasása (0001–0700) | ~120 sor | — | **Nem történt meg** (batch-átolvasásra támaszkodik) |
| Kontraszt-sorok tényforrás-ellenőrzése | 125 | K 13 / Ö 24 / közvetett 1 / R 28 / A-D 59 | **Részleges** |
| Számszerű állítások forrásellenőrzése (nem kontraszt) | a 9–10. batch és a jogi számok | Ö/K | **Részleges** |
| Független emberi/szakértői átnézés | 1000 | — | **Nem történt meg** |
| Nyitás- és sablonelemzés | 1000/1000 | automatikus + értékelés | **Kész** (a sablonok nem javítva) |

## 12. Megszakadt, hiányzó ellenőrzések és nyitott tartalmi kérdések

**Megszakadt:** a `tools/dataset_cross_dedupe.py` teljes korpuszos futása 2026-09-23-án 11+ óra után, kimenet nélkül leállítva. Helyette a szakaszolt, azonos szemantikájú módszer futott le, és a teljes 4500 soros korpuszra befejeződött.

**Hiányzó:** független emberi átolvasás; szakértői (orvosi, jogi, pénzügyi) átnézés; a 2–6. batch kontraszt-sorainak teljes közvetlen forrásellenőrzése; a kulcsszavas nem-hard sorok újraolvasása a 0001–0700 batchekben.

**Nyitott tartalmi kérdések (nem blokkolók):**
1. A „…és azt sem tudom, melyik…” válaszsablon 49 sorban; az `ellenorzesi_ut` mód `Hogyan ellenőrizzem…` nyitása 29 sorban — érdemes lenne külön, jóváhagyott átdolgozási körben szétszórni.
2. 39 előtag nélküli, plusz-címke nélküli kontraszt-sor (2.–3. batch) újracímkézése vagy átdolgozása.
3. `0506` (rövid, rutinba ágyazott nyújtás) tudományos árnyalása.
4. A keresési összefoglaló alapján forrásolt (Ö) állítások (24 kontraszt-sor, a WHO/NIST/NFPA/USDA/ADA/OSHA számok, a magyar jogi számok) közvetlen elsődleges forrásból való újraolvasása; a jogi számoknál (`0829`, `0849`, `0864`) jogász általi ellenőrzés.
5. A 14 ismétlődő kind-címke egyediesítése (informatívabb témacímkék).
6. A 7 nem `uncertainty` csomagi (`simple_qa`, `step_by_step`) ≥ 0,9 hasonlósági pár tartalmi értékelése (más csomag hatóköre).
7. A `0277` ↔ `simple_qa_0271` témaátfedés megfigyelése.
8. Scratchpad szkriptek (`gen_usr*.py`, `usr_check*.py`, `dd_full.py`, `audit_pkg.py`) `tools/` alá emelése csak külön jóváhagyással.

## 13. Commitok

- `e97ba92` — `v1.13.10-dataset-fix` (0518 második javítás, 0708 forrás)
- `a066b3c` — `v1.13.11-dataset-generation` (0801–0900 batch)
- `cc9be38` — `v1.13.12-dataset-fix` (az audit közben talált tartalmi javítások, 9. szakasz)
- `d398f86` — `v1.13.13-dataset-generation` (0901–1000 batch és riportja)
- `v1.13.14-dataset-audit` — ez a riport (azonosítója a lezáró jelentésben, mert a saját commitját nem tudja tartalmazni)

A javítás- és a batch-commit **után** a végleges adatverzióra a teljes korpuszos N×N futást és a szerkezeti auditot újra lefuttattam: a `git status` a clean/raw/rejected fájlokra tiszta, az eredmények megegyeznek a fentiekkel.
