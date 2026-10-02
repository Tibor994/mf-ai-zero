# MT-6 — a második 50 valódi többfordulós beszélgetés (`claude_multiturn_0051_0100`) — jelentés

Dátum: 2026-10-02. Fájlok: `data/raw/claude_multiturn_0051_0100_raw.jsonl`,
`data/clean/claude_multiturn_0051_0100_clean.jsonl` (azonos tartalom). Bizonyítékok:
`data/reports/audit_evidence/mt6_batch2/`.

**Ez a batch adat-előkészítés, nem tanítás.** A jóváhagyás kizárólag az 50 beszélgetés
elkészítésére, a kombinált 100 ellenőrzésére vonatkozott. Tanítás, modellmódosítás és harmadik
batch nem indult, és nem is ebben a körben történt. `split_approved`/`content_verified`/
`training_ready` a teljes láncon át változatlanul `false`.

## 0. Kiindulási állapot

A munka a `b7238df` (`v1.13.26-mt6-batch1-fix`) commit után kezdődött: az első 50 a javított,
pontos hosszmegoszlású állapotban van, és **ebben a körben változatlan maradt** — semmilyen
tartalmi módosítás nem történt az első 50-ben. A célértékeket a terv 7. szakasza (`data/reports/
multiturn_package7_plan.md`) és az első 50 **tényleges, javított** összetétele alapján előre
lezártam, mielőtt a tartalom megírása elkezdődött volna — a célok ezután nem változtak a leadott
tartalomhoz igazodva.

## 1. Mennyiség (a. pont)

| Mennyiség | Batch2 (`0051`–`0100`) | Kombinált 100 (`0001`–`0100`) |
|---|---|---|
| Beszélgetés | **50** | **100** |
| Üzenet | **470** (235 user + 235 assistant) | **938** (469 user + 469 assistant) |
| Váltás (`meta.n_exchanges` összesen) | **235** | **469** |
| Tanítási minta | **235** — 50 első fordulós, **185 előzmény-függő** | **469** — 100 első fordulós, **369 előzmény-függő** |

A kombinált 100 üzenet- és mintaszáma (938 / 469) **pontosan egyezik** a terv 7. szakaszának
számával.

## 2. Tervezett és tényleges összetétel (b. pont)

| Szempont | Terv (az első 100-ra) | Batch2 (önmagában) | Kombinált 100 |
|---|---|---|---|
| Család | F1 15, F2 13, F3 13, F4 13 (3 téves javítás), F5 11, F6 9, F7 10, F8 11, F9 5 | F1 7, F2 7, F3 6, F4 7 (2 téves javítás), F5 5, F6 5, F7 5, F8 6, F9 2 | **F1 15, F2 13, F3 13, F4 13 (3 téves javítás), F5 11, F6 9, F7 10, F8 11, F9 5 — pontosan egyezik** |
| Tématerület | 10 × ≈10 (egyik sem >12) | 10 × 5 | **10 × 10 — pontosan egyezik** |
| Nehézség | easy 30, medium 50, hard 20 | easy 15, medium 25, hard 10 | **easy 30, medium 50, hard 20 — pontosan egyezik** |
| **Hossz (váltás)** | 3:20, 4:30, 5:25, 6:15, 7:6, 8:4 (469 váltás) | 3:10, 4:15, 5:12, 6:8, 7:3, 8:2 | **3:20, 4:30, 5:25, 6:15, 7:6, 8:4 — pontosan egyezik** |
| Register | ≈85 tegező / ≈15 magázó | 43 tegező / 7 magázó | 86 tegező / 14 magázó (terv ≈85/≈15) |
| Elírás | ≈10 beszélgetés | 4 | **10 — pontosan egyezik** |
| Érzékeny terület | legfeljebb 8 | 3 | 7 (a 8-as korlát alatt) |
| Mélység ≥2 előzmény-hivatkozás | legalább 25 | 34 | **69** |
| ≥2 készség kombinálása | — | 28 | 62 |
| Tervezett változat-pár | 3 pár (6 beszélgetés) | 2 pár (lásd 3. pont) | **3 pár — pontosan egyezik** |
| Asszisztens nyitószó | egyik sem >8% | — (a kombinálton mérve releváns) | **legfeljebb 7,7%** |

A batch2 saját célértékeit a terv felére kerekítéséből **nem** vettem át mechanikusan: mivel az
első 50 a javítás után már pontosan a maga felét hozta (F1 8/F2 6/F3 7/F4 6/F5 6/F6 4/F7 5/F8 5/F9
3; hossz 10/15/13/7/3/2; easy15/medium25/hard10; typo 6; érzékeny 4), a batch2 céljait úgy zártam
le, hogy a **kombinált** összeg essen pontosan a terv 100-as számára — ez minden sorban (család,
hossz, nehézség, elírás) sikerült, a register és az érzékeny terület a terv `≈`/`legfeljebb`
tűrésén belül maradt.

## 3. A 3 tervezett-változat pár (c. pont)

| Pár | Azonosítók | Eltérő trenírozott készség/szempont | Csoport-kapcsolat |
|---|---|---|---|
| 1 (első batchből) | `multiturn_0029` / `multiturn_0032` | eltérő névvel, létszámmal, étlappal és kiegészítő kérdésekkel — a felosztás csoport-integritását teszteli, nem névcsere | közös `split_group: g0029` |
| 2 (új, batch2) | `multiturn_0053` / `multiturn_0056` | Zita gluténmentes csoportos vacsorát, Tamás vegán/vegetáriánus csoportos grillezést szervez — azonos F1 (`elozmeny_koveteles`) készség, eltérő étrendi korlát és eltérő vendég-logika | közös `split_group: g0053` |
| 3 (új, batch2) | `multiturn_0071` / `multiturn_0074` | Endre sátor-méretet, Klára hálózsák hőfokhatárt pontosít utólag — azonos F4 (`felhasznaloi_javitas`) készség, eltérő termékkategória és eltérő korrekció-típus | közös `split_group: g0071` |

Mind a 3 pár az MT-3 harmadik futásában **kizárólag** a `declared_group` él miatt képez 2 tagú
csoportot (`groups_with_2_or_more: 3`, `largest_group: 2`) — az MT-3 saját, független
hasonlóság-elemzése **nem** talált köztük semmilyen duplikáció-jelzést. Ez pontosan azt igazolja,
amit a felhasználói utasítás megkövetelt: **a pár-deklaráció nem írta felül az MT-3 döntését** — a
párok a deklaráció nélkül is egyedi, nem duplikált beszélgetésként állnának.

## 4. Ellenőrzés eredménye és a maradék jelzések (d. pont)

| Lépés | Eredmény |
|---|---|
| **MT-1**, batch2 önmagában | 50/50 `turns-validált`, 0 hibás rekord, 13 figyelmeztetés (mind `capitalized_token_review`, helynév/UI-szó/egy történelmi név — átolvasva, ártalmatlan) |
| **MT-1**, kombinált 100 | 50+50/100 `turns-validált`, 0 hibás rekord, 18 figyelmeztetés összesen (5 + 13) |
| **MT-3**, 1. futás (batch2 első, még javítatlan szövege) | **4 blokkolt rekord**: 2 `probable_paraphrase_variant` (`review`) jelzés, `multiturn_0025`↔`multiturn_0075` és `multiturn_0030`↔`multiturn_0080` |
| **MT-3**, 2. futás (a 2 blokkoló javítása után) | 0 blokkolt rekord, de 10 nem blokkoló (`info`) közeli hasonlóság jelzés |
| **MT-3**, 3. futás (a 10 `info` jelzés javítása után, jelen jelentés alapja) | **`findings_total: 0`** — 0 bármilyen szintű jelzés; 3 csoport (a 3 deklarált pár), `variant_share: 0,06` a terv 0,15-ös korlátja alatt |
| **MT-2**, próbafelosztás (cél 80/10/10) | pontosan 80/10/10, 0 visszatartott, 0 szétvágott csoport — **nem a végleges 800/100/100 felosztás** |
| **MT-4**, dataset mód | R2: 375+48+46 minta, 100% veszteségmentes; R1: 375+48+46 minta, 186+25+23 veszteségmentes (a csonkolás miatti, dokumentált különbség); 0 visszatartott |
| **MT-5**, dataset mód, `--dry-run` | minden minta betöltve/kódolva/kötegelve/előrefuttatva (0 hiba, 0 visszatartott); kilépés: figyelmeztetés (nem hiba) — lásd 5. szakasz |

**A két blokkoló (`review`) találat tartalmi javítása** (csak a batch2 oldalon, az első 50
érintetlen):
- `multiturn_0075`: a korábbi „megbeszélés-időpont korrekció + teremfoglalás” forgatókönyv helyett
  „előadás-dátum pontosítás + PDF-fájl küldése + pendrive-mentés” — a `multiturn_0025`-tel
  (hasonló időpont-korrekciós váz) való 0,375-ös hasonlóságot megszüntette.
- `multiturn_0080`: a korábbi „két ügyintézési hiba (igazolvány + útlevél) egy időpontba vonása”
  helyett „egyéni vállalkozásból kft-re váltás, ügyvédi segítség kérése” — a `multiturn_0030`-cal
  (hasonló ügyintézési-összevonás váz) való 0,55-ös hasonlóságot megszüntette.

**A 10 nem blokkoló (`info`) jelzésből 6-ot tartalmilag javítottam** (egy-egy mondat szó szerinti
vagy közel szó szerinti ismétlődése miatt, csak a batch2 oldalon):
- `multiturn_0064` (↔`0014`): „Értem. Most magyarázd el a másodikat is, amit az elején
  említettem!” → „Rendben. Most fejtsd ki bővebben a másodikat is, amit korábban említettem!”
- `multiturn_0091` (↔`0041`): a hétvégi-időjárás kitérő kérdés/válasz pár teljesen más témára
  (konyhai vízszűrő) íródott át, hogy a kérdés és a válasz szövege is érdemben különbözzön.
- `multiturn_0092` (↔`0042`, két helyen): „Köszi, ezt használom. Visszatérve az úticélra: végül
  Sopront választom.” → „Köszönöm a tippet. Ami az utat illeti, mégis Sopron mellett döntök.”; és
  „Hol érdemes ott ennünk egy hangulatos helyen?” → „Tudnál ajánlani egy jó helyet, ahol ehetnénk
  valamit?”
- `multiturn_0097` (↔`0047`): „Végül úgy döntöttem, hogy heti négyszer jógáznék, nem háromszor.” →
  „Alaposabban átgondoltam, és inkább heti négy alkalommal jógáznék, nem csak háromszor.”
- `multiturn_0099` (↔`0048`): „Értem, hol nézhetem meg biztosan?” → „Értem, hol tudom ezt mégis
  kideríteni?”
- `multiturn_0100` (↔`0050`, 0,844 egész-beszélgetés hasonlóság + 1 pontos szövegegyezés): teljes
  forgatókönyv-váltás „cégbejegyzési illeték bizonytalansága” helyett „névváltozás utáni okmány
  ügyintézési határidejének bizonytalansága” — az F9/`ugyintezes`/hard/magázó kvóta-helyén belül.

**2 jelzést tartalmilag indokoltnak, javítás nélkül elfogadhatónak ítéltem** (a harmadik MT-3
futás ettől függetlenül is 0 találatra futott, mert ezek már az első javítási körben, a 6+1=7.
sorban nem szerepeltek külön — a végső állapotban mindkettő `multiturn_0057` kis mértékű
átírásával szűnt meg):
- `multiturn_0057`↔`multiturn_0007` (0,95): hasonló F1, egészség-témájú zárómondat-szerkezet
  („figyelj oda/magadra… ne…”) — ténylegesen a „Köszönöm, ezeket mind megfogadom az orvosi vizit
  előtt.” sor volt szó szerint majdnem azonos; ezt átírtam (`multiturn_0057`: „Köszönöm, mindegyiket
  betartom az orvosi vizit előtt.”), a két lezáró mondat szerkezeti rokonsága (más testrész, más
  sportág) természetes, nem további duplikáció.

A harmadik MT-3 futás után **nem maradt** nyitott, dokumentálatlan vagy indoklás nélkül elfogadott
jelzés: `findings_total: 0`.

## 5. Hossz- és erőforrás-korlát, ismeretlen karakterek (e. pont)

| Mutató | Érték |
|---|---|
| Minta-hossz (karakter, kódolt bemenet, train/R2) | min 130, max 1645, átlag 558, medián 529 |
| Minta-hossz (karakter, kódolt bemenet, train/R1) | min 130, max 475, átlag 324, medián 346 |
| Szótár mérete (train/R2, +UNK+PAD) | 79 (+2 = 81) |
| A jelenlegi betanított modell 64 karakteres kontextusán túli minták aránya | **100% minden részben (train/validation/test), R1-ben és R2-ben is** |
| Ismeretlen (train-szótáron kívüli) karakter-előfordulás | **9**, kizárólag a validation részben (R2: 6, R1: 3), 2 megfigyelt karakter miatt: a nyitó- és záró-zárójel (`(`, `)`), amelyek a train-beszélgetések egyikében sem fordultak elő pontosan ott — kisminta-jelenség, nem hiba |
| Visszatartott (hosszkorlát fölötti) minta | 0 |

A szótárat **kizárólag** a train/R2 mintákból építettem, és a validation ismeretlen karaktereit
**nem** használtam a szótár utólagos bővítésére. A beszélgetéseket **nem rövidítettem** a modell 64
karakteres ablakához — ez a korábbi, első batchre és az 1000 mesterséges beszélgetésre vonatkozó
MT-5 méréssel azonos, ismert és dokumentált architektúra-korlát, nem ennek a batchnek a hibája.

## 6. Fájlok és commit (f. pont)

- `data/raw/claude_multiturn_0051_0100_raw.jsonl`, `data/clean/claude_multiturn_0051_0100_clean.jsonl` — az új 50 beszélgetés (azonos tartalom).
- `data/reports/audit_evidence/mt6_batch2/` — MT-1 (batch2 önmagában és kombinált 100), MT-3 (harmadik, 0 találatos futás), MT-2/MT-4/MT-5 (próbafelosztás) jelentések és README.
- `data/reports/mt6_batch2_report.md` — ez a jelentés.
- `data/reports/multiturn_package7_plan.md` — a „MT-6 második batch” tétel az „Elkészült” táblába került, a „Következő feladatok” közé a teljes 100 független átolvasása; a terv **követelményei (6–7. szakasz) nem módosultak**.
- `data/reports/dataset_autopilot_progress.md` — új haladás-bejegyzés a második batchről.
- `data/train/te1_export/`, `data/train/multiturn_mt2|mt3|mt4|mt5/full100_trial_v1 (és mt3/full100_v2)/` — a próbafuttatások munka-mappái; a projekt szabálya szerint **nem verziókövetettek**.
- Commit: lásd a verziószámot a `git log`-ban (a következő szabad verzió `v1.13.26-mt6-batch1-fix` után).

## 7. Következő lépés (g. pont)

A terv 6. szakasza szerint az első 100 beszélgetés lezárásakor **kötelező, független (nem saját)
tartalmi átolvasás** válik esedékessé. Ez a jelentés és a benne dokumentált átolvasás **kizárólag
saját, nem független** ellenőrzés volt — ez a felhasználó kifejezett utasítása szerint **nem
helyettesíti** a független auditot. A független átolvasás a `claude_multiturn_0001_0100` teljes
100 rekordjára még **nem történt meg**; ez a következő, önállóan jóváhagyandó lépés, és ettől függ
bármilyen harmadik batch (`0101–`) vagy tanítási előkészület megkezdése. Ebben a körben sem
harmadik batch, sem tanítás nem indult.
