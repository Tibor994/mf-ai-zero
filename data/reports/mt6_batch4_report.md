# MT-6 — a negyedik 50 valódi többfordulós beszélgetés (`claude_multiturn_0151_0200`) — jelentés

Dátum: 2026-10-15 (a batch 2026-10-07–09 között készült, a lezárás és a dokumentáció 2026-10-15). Fájlok:
`data/raw/claude_multiturn_0151_0200_raw.jsonl`, `data/clean/claude_multiturn_0151_0200_clean.jsonl` (azonos tartalom, sha256
`72a9d7f8e2de2768374ddb26c1ff8ebaded20a1db878b5d6f36d43a57d9f4033`). Bizonyítékok: `data/reports/audit_evidence/mt6_batch4/`.

**Ez adat-előkészítés, nem tanítás.** A munka a felhasználó 2026-10-04-i jóváhagyott tervmódosítására épül: a független, emberi
tartalmi átolvasás **nyitott, kötelező tanítás előtti feltétel marad**, de nem akadályozza további tanítóadatok előkészítését.
Tanítás, modellmódosítás és ötödik batch nem indult. `split_approved` / `content_verified` / `training_ready`: **változatlanul `false`**.
Minden felülvizsgálat **AI-alapú** (Claude-alügynökök + saját közvetlen ellenőrzés); **nem független, nem emberi audit**.

## 0. Kiindulás, sorrend és a harmadik batch utóellenőrzése

* Kiindulás: `2134ab2` (a harmadik batch). Ezután, a negyedik batch megkezdése előtt, két commit készült:
  * `2ae9a95` (`v1.13.31-mt6-batch3-postfix`): a harmadik batch 3. körében javított 10 rekord **javítás utáni célzott tartalmi
    ellenőrzése** (AI-alapú), a `0120` állításonkénti (díj-/ügyintézési) táblázata, és 5 igazolt szövegjavítás (`0115`, `0117`,
    `0120`, `0127`, `0147`; ezt a lezárásnál a commit tartalmából újra ellenőriztem: mind az öt módosított szöveg benne van).
    A `0120` régi lakcím sorsáról szóló mondata kikerült, mert elsődleges jogszövegből nem tudtam megerősíteni; a lakcímkártya
    díjáról/kiállításáról a rekord továbbra sem állít semmit.
  * `69ea889` (`v1.13.32-mt6-batch4-targets`): a negyedik batch célértékei a terv új **7/c** szakaszában.
* **Ismert sorrendi eltérés.** A célértékeket a szövegírás előtt a terv fájljába felírtam, de külön commitba csak az F1 első
  szövegvázlata (`b4_f1.py`, munkamappa, nem a repóban) megírása **után** kerültek (`69ea889`). A célszámok a felírás és a commit
  között nem változtak; a célokat később sem igazítottam az elkészült adathoz. Ezt ezért **nem tekintem teljesen előzetesen, külön
  commitban rögzített célnak**; az adat commitja mindenképp a célok commitja után készült.

## 1. Mennyiség

| Mennyiség | Batch4 (`0151`–`0200`) | Kombinált 200 |
|---|---|---|
| Beszélgetés | **50** | **200** |
| Üzenet | **470** (235 user + 235 assistant) | **1876** |
| Váltás / tanítási minta | **235** (50 első fordulós, 185 előzmény-függő) | **938** |

A kombinált 200 a teljes csomagcél (4690 váltás) 20%-a szerinti kumulatív érték (938, pontosan). Az eredeti `0001`–`0150` fájlokhoz
a lezárás során semmi változás nem történt a harmadik batch fent említett 5 javításán kívül.

## 2. Tervezett és tényleges összetétel

A „Cél” az előre (a szövegírás előtt a tervbe, majd `69ea889`-ben commitolva) rögzített 7/c érték; a „Tény” a végleges adat mérése
(`composition_actual.json`).

| Szempont | Rögzített cél (7/c) | Batch4 tény | Kumulatív 200: cél → tény |
|---|---|---|---|
| Család | F1 7, F2 7, F3 6, F4 7, F5 5, F6 5, F7 5, F8 6, F9 2 | **pontosan egyezik** | F1 30, F2 26, F3 26, F4 26, F5 22, F6 18, F7 20, F8 22, F9 10 — **egyezik** |
| F4 téves felhasználói javítás | 1 | 1 (`0174`) | 5 |
| Hossz (váltás) | 3:10, 4:15, 5:12, 6:8, 7:3, 8:2 | **pontosan egyezik** | 3:40, 4:60, 5:50, 6:30, 7:12, 8:8 — **egyezik** |
| Tématerület | 5 × 10 | **5 × 10** | 20 × 10 — **egyezik** |
| Nehézség | easy 15 / medium 25 / hard 10 | **pontosan egyezik** | 60 / 100 / 40 — **egyezik** |
| Register | tegező 42 / magázó 8 | **pontosan egyezik** | 170 / 30 — **egyezik** |
| Elírás a felhasználónál | 5 | **5** (`0153`, `0163`, `0172`, `0181`, `0195`) | 20 — **egyezik** |
| Érzékeny terület | legfeljebb 4 | **4** (`0157`, `0176`, `0194`, `0200`) | 16 (korlát ≤ 16) — **a korláton** |
| Mélység ≥ 2 | legalább 13 | 38 | 149 |
| ≥ 2 készség kombinálása | legalább 20 | 34 | 129 |
| Tervezett változat-pár | 1 | 1 (`0166`/`0196`, `g0166`) | 5 pár, változat-részesedés 0,05 (korlát 0,15) |
| Név nélküli beszélgetés | 22 | **22** | 36 |
| Megnevezett rekordok | 28; ebből legalább 14 még soha nem használt név, a többinél legfeljebb egy ismétlés | 28: **14 új**, 14 újrahasznált (egyszer) | egy név legfeljebb kétszer szerepel (mért maximum: 2) |
| „Szia! X vagyok,” kezdetek | legfeljebb 11 | 6 | — |
| Asszisztens nyitószó | ≤ 8% | legfeljebb 7,7% („ha”) a batchen; 6,8% („a”) a kombinált 200-on | — |
| Váltás / üzenet / minta | 235 / 470 / 235 | **235 / 470 / 235** | 938 / 1876 / 938 |

A célok az átolvasás és javítás során **nem változtak**. A `sensitive_area` címkét a tartalom szerint adtam (egészség: `0157`,
`0176`; jogi/eljárási jogok: `0194`, `0200`); az általános főzés/vásárlás/fogyasztói szerződés-segítség (`0153`, `0163`, `0168`,
`0182`) nem érzékeny, akkor sem, ha orvosra/hatóságra utal.

## 3. A tervezett változat-pár

| Pár | Azonosítók | Közös mag | Eltérés | Csoport |
|---|---|---|---|---|
| 5. pár | `multiturn_0166` / `multiturn_0196` | gyerekzsúr szervezése, költségkeret elosztása | 0166 F3: 6 éves kislány, 8 gyerek, otthon, 30 000 Ft, kétórás zsúr; 0196 F8: 10 éves fiú, 12 gyerek, szabadtér, 60 000 Ft, délutáni időbeosztás és előkészítő teendők; más család, hossz, számok és kérés | közös `split_group: g0166` |

Az MT-3 a párt kizárólag a deklarált csoport alapján kapcsolja (a végső futásban 0 találat); a deklaráció nem írta felül az MT-3 döntését,
és a próbafelosztásban a pár egy részbe került.

## 4. AI-alapú felülvizsgálat: találatok, javítások, javítás utáni ellenőrzés

**Nem független, nem emberi audit.** Részletes, rekordszintű napló: `audit_evidence/mt6_batch4/review_log.md`; az alügynökök teljes
jelentései nem kerültek a repóba, a napló azok kivonata és a verziók tényleges különbsége.

| Kör | Olvasott állapot | Hatókör | OK | NEEDS_FIX | Javítás utána |
|---|---|---|---|---|---|
| 1. | eredeti piszkozat | mind az 50, 4 friss alügynök | 16 | 34 | A: 43 rekord / 87 üzenet / 26 `depends`-módosítás |
| 2. | A után | a 43 módosult rekord, 4 friss alügynök | 25 | 18 | B: 32 rekord / 49 üzenet / 11 `depends` |
| 3. | B után | a 32 módosult rekord, 2 friss alügynök | 21 | 11 (3 ERROR) | C: 13 rekord / 18 üzenet / 1 `depends`; D (MT-3 `info`): 2 üzenet |
| 4. (végső, célzott) | C+D után | 13 rekord teljes kontextussal (20 üzenet + 1 `depends`), a `0198`, a `0196` és a `0200` kiemelve; 1 friss alügynök | 9 | 4 (csak MINOR, **0 ERROR**) | E: 4 rekord / 4 üzenet (saját újraolvasás) |

* **Fő hibatípusok:** téves vagy felfújt `meta.depends` (a legtöbb jelzés: fölösleges index, a válasz az őt megelőző kérdésből is megírható;
  vagy hiányzó bejegyzés), belső ellentmondás (`0176` összegzés, `0195` feladatok és családi összegzés, `0198` tempó), néhány tényszerű
  vagy félrevezető állítás (`0153` tojáshelyettesítés, `0158` park mosdója/játszótere, `0169` csíkok oka, `0191` turmixgép-folyadék,
  `0200` „magánszféra”), nem teljesített kérés (`0194`: „rendben van?”; `0193`: „óránkénti” beosztás).
* **Saját hibám, javítva:** a 2. kör utáni javításomban a `0198` 7. üzenete állítmány nélküli mondat lett; ezt a 3. kör jelezte, a
  4. kör már rendben találta. A 3. körös javításom a `0200`-ban „magánszféra” szót írt (téves, „versenyszféra” kell); szintén a 3. kör találta meg.
* **A `0198`** rekordot a 4. kör kiemelten, teljes egészében (terv, tempó, csomagolás, összegzés, minden `depends` bejegyzés)
  vizsgálta: nincs ERROR; a kérések teljesültek.
* **A `0196` 8. és `0200` 2. üzenetének MT-3-vezérelt átfogalmazása** (az MT-3 két `info` jelzése: azonos kérdés eltérő előzménnyel)
  **a 3. körös ellenőrzésekben még nem szerepelt**; csak MT-1/MT-3 futott rajta. Ezt a 4. kör pótolta: mindkettő illeszkedik az utána
  következő válaszhoz és a `depends` bejegyzésekhez.
* **A 4. kör utáni 4 javítás** (`0157` 13., `0164` 11., `0168` 3., `0193` 9. üzenet; nyelvtani/pontossági): igazolt, apró hibák;
  javítás utáni ellenőrzésük **saját közvetlen újraolvasás + MT-1 + a teljes lánc újrafuttatása** — erre újabb alügynök nem olvasta.
  A 4. kör opcionális, nem hibának ítélt javaslatait nem alkalmaztam.
* A 0001–0150 beszélgetésekhez a lezárás során nem nyúltam (a harmadik batch 5 javítása a `2ae9a95` commitban külön igazolt).

## 5. Technikai ellenőrzések (a végleges adaton)

| Lépés | Eredmény |
|---|---|
| Friss TE-1 export (`export_20261007_fresh`) | 4500 beolvasva, **6 kizárva** (`0220`, `0602`, `0829`, `0849`, `0864`, `0898`), 4494 exportálva; a `train_candidates.jsonl` sha256 egyezik a korábbi exportokéval |
| MT-1, batch4 önmagában | 50/50 `turns-validált`, **0 hibás**, 121 figyelmeztetés (mind `capitalized_token_review`; ebből 85 a természetes „Ft” rövidítés, a többi mértékegység/ritka szó/szoftvernév/magázó névmás) |
| MT-1, kombinált 200 | **0 hibás**, 5 + 13 + 48 + 121 = 187 figyelmeztetés, mind ilyen típusú |
| MT-3 (`mt3-2.0`), kombinált 200 + friss TE-1 export | **0 találat**, 0 blokkolt rekord, 195 csoport (5 deklarált pár), változat-részesedés 0,05 |
| MT-2 próbafelosztás (160/20/20) | pontosan 160/20/20, 0 visszatartott, 0 szétvágott csoport, 0 részek közötti átfedés; **nem a végleges 800/100/100, nem jóváhagyott** |
| MT-4 export (R1 + R2, dataset) | R2: 747 + 96 + 95 minta 100% veszteségmentes; R1: 266 + 31 + 33 veszteségmentes (a csonkolás miatti, dokumentált különbség); 0 visszatartott |
| MT-5 `--dry-run` (R2 elsődleges, R1 összehasonlító) | minden minta betöltve / kódolva / kötegelve / előrefutva (47/47, 6/6, 6/6 köteg), 0 hiba, 0 visszatartott |

Az MT-3 egy korábbi futása a végleges előtti állapoton 2 `info` jelzést adott (`0048`/`0200` és `0166`/`0196` hasonló kérdése); a két
felhasználói kérdést átfogalmaztam (lásd fent, D), a végső futás 0 találatot ad. Az MT-1 → MT-5 láncot a végleges
szövegre **újra futtattam** (a 4. kör utáni javítások miatt), az eszközök kódját és küszöbeit nem módosítottam, a lezárt eszközök
mutációs vizsgálatát nem futtattam újra. A futások bemeneti ellenőrzőösszegei egyeznek a végleges fájlokéval (README).

## 6. Hossz, szótár, ismeretlen karakterek, nyitott korlátok

* Szótár: **102 karakter** (+UNK+PAD), **kizárólag a train/R2 részből**; új a korábbi 150-es futáshoz képest: `"` `%` `&` `+` `0` `1` `2` `6` `7` `9`
  `<` `=` `>` `|` `²` `×` `–` `−` `≈` (a természetes számjegy- és írásjel-használat miatt).
* **Ismeretlen karakter: 0 előfordulás** train / validation / test × R2 / R1 (azaz hat helyen mind 0): nincs érintett karakter és
  nincs érintett rekord (`mt5_unknown_chars_by_split.json`). A szótárat nem bővítettem validation/test adatból, a tartalmat nem
  írtam át emiatt. Megfigyelés: hat karakter a train részben egyetlen beszélgetéstől függ (`<`, `>`, `&`, `"` — `0177`; `²` — `0156`;
  `|` — `0195`); más felosztásban ezek ismeretlenként jelennének meg a validation/test részben.
* Minta-hossz: train R2 130–3122 karakter (átlag 743), R1 130–900 (átlag 393). A minták **100%-a** meghaladja a jelenlegi betanított modell
  64 karakteres kontextusát — a beszélgetéseket **nem rövidítettem**. A 64 karakteres ablak kérdése változatlanul nyitott.
* **Nyitott:** (1) a független, emberi tartalmi átolvasás (kötelező tanítás előtti feltétel); (2) nem igazolt tények (a napló végén felsorolva:
  jogi/fogyasztóvédelmi részletek, sütési/főzési arányok, edzés- és tempóbecslések, kávé-/koffeinhatárok, háztartási és utazási
  ökölszabályok); (3) a végleges felosztás jóváhagyása; (4) a 64 karakteres modell-kontextus kérdése; (5) a 4. kör utáni 4 apró javításra
  (lásd 4.) nem készült újabb alügynöki ellenőrzés, csak saját újraolvasás és a technikai lánc.

## 7. Fájlok és commit

* `data/raw|clean/claude_multiturn_0151_0200_*.jsonl` (új, 50 beszélgetés; a raw/clean `.gitignore`-ban van, ezért a korábbiakhoz hasonlóan kényszerített hozzáadással kerül a commitba).
* `data/reports/audit_evidence/mt6_batch4/` (README, `review_log.md`, `composition_actual.json`, MT-1/MT-3/MT-2/MT-4/MT-5, ismeretlen karakterek, TE-1 manifest).
* `data/reports/mt6_batch4_report.md` (ez a jelentés); `data/reports/multiturn_package7_plan.md`, `data/reports/dataset_autopilot_progress.md` (haladás-rögzítés; a 7/c célok nem módosultak).
* Célok commitja: `69ea889`; a harmadik batch javításai: `2ae9a95`; az adat commitja: lásd a `git log`-ban (`v1.13.33-mt6-batch4`).
* `data/train/…` futás-mappák: munkamappák, nem verziókövetettek.

## 8. Következő lépés

Az ötödik batch (`0201–0250`) vagy a független, emberi átolvasás külön, kifejezett jóváhagyást igényel. A független átolvasás halmaza immár a
kész 200 beszélgetés; ez marad a tanítás előtti kötelező feltétel. Tanítás és `training-ready` minősítés továbbra sem engedélyezett.
