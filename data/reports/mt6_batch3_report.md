# MT-6 — a harmadik 50 valódi többfordulós beszélgetés (`claude_multiturn_0101_0150`) — jelentés

Dátum: 2026-10-07. Fájlok: `data/raw/claude_multiturn_0101_0150_raw.jsonl`, `data/clean/claude_multiturn_0101_0150_clean.jsonl`
(azonos tartalom). Bizonyítékok: `data/reports/audit_evidence/mt6_batch3/`.

**Ez adat-előkészítés, nem tanítás.** A munka a felhasználó 2026-10-04-i jóváhagyott tervmódosítására épül: a független,
emberi tartalmi átolvasás **nyitott, kötelező tanítás előtti feltétel marad**, de nem akadályozza további tanítóadatok
előkészítését. Tanítás, modellmódosítás és negyedik batch nem indult. `split_approved` / `content_verified` /
`training_ready`: **változatlanul `false`**.

## 0. Kiindulás és célértékek

* Kiindulás: `2da70e8` (`v1.13.28-mt6-audit2`). A tervmódosítást és a batch **célértékeit a szövegírás előtt, külön
  commitban rögzítettem** (`b54ca82`, `v1.13.29-mt6-batch3-targets`; a terv új 7/b szakasza): a teljes csomag célszámainak
  15%-a (150/1000) mínusz a kész, javított 100 tényleges összetétele; a célok utólag nem módosultak.
* A korábbi 100 beszélgetéshez **nem nyúltam**. Közben a `b54ca82` commitban pontosítottam az előző auditjelentés
  számolási hibáit (50 rekord módosult, 1 jelzés elvetve, a `0089` javítása hiányzott a táblázatból) — ez csak dokumentáció.
* Az előző felülvizsgálat tanulságai kötelezően érvényesültek: a felhasználó **bemutatkozik, mielőtt az asszisztens a nevét
  használná** (a generátor ezt szkriptben ellenőrzi); 14 beszélgetés név nélküli; a bemutatkozási formák változatosak;
  a `meta.depends` csak valódi, korábbi váltásra épülő válasznál szerepel; címkék a tényleges tartalmat követik.

## 1. Mennyiség

| Mennyiség | Batch3 (`0101`–`0150`) | Kombinált 150 |
|---|---|---|
| Beszélgetés | **50** | **150** |
| Üzenet | **468** (234 user + 234 assistant) | **1406** |
| Váltás / tanítási minta | **234** (50 első fordulós, 184 előzmény-függő) | **703** |

A kombinált 150 üzenet- és mintaszáma a teljes csomagcél (4690 váltás) 15%-a (703,5) szerinti kumulatív érték.

## 2. Tervezett és tényleges összetétel

| Szempont | Rögzített cél (7/b) | Batch3 tény | Kumulatív 150 cél → tény |
|---|---|---|---|
| Család | F1 8, F2 6, F3 7, F4 6, F5 6, F6 4, F7 5, F8 5, F9 3 | **pontosan egyezik** | F1 23, F2 19, F3 20, F4 19, F5 17, F6 13, F7 15, F8 16, F9 8 — **egyezik** |
| F4 téves felhasználói javítás | 1 | 1 (`0124`) | 4 |
| Hossz (váltás) | 3:10, 4:15, 5:13, 6:7, 7:3, 8:2 | **pontosan egyezik** | 3:30, 4:45, 5:38, 6:22, 7:9, 8:6 — **egyezik** |
| Tématerület | 5 × 10 | **5 × 10** | 15 × 10 — **egyezik** |
| Nehézség | easy 15 / medium 25 / hard 10 | **pontosan egyezik** | 45 / 75 / 30 — **egyezik** |
| Register | tegező 42 / magázó 8 | **pontosan egyezik** | 128 / 22 — **egyezik** |
| Elírás | 5 | **5** | 15 — **egyezik** |
| Érzékeny terület | legfeljebb 4 | **4** (`0107`, `0117`, `0130`, `0150`) | 12 (korlát ≤ 12) — **a korláton** |
| Mélység ≥ 2 | legalább 13 | 42 | — |
| ≥ 2 készség kombinálása | legalább 20 | 33 | — |
| Tervezett változat-pár | 1 | 1 (`0104`/`0144`, `g0104`) | 4 pár, változat-részesedés 0,053 (korlát 0,15) |
| Név nélküli beszélgetés | 14 | **14** | — |
| „Szia! X vagyok,” kezdetek | legfeljebb 18 | 15 | — |
| Asszisztens nyitószó | ≤ 8% | legfeljebb 6,0% (batchen); 7,1% (kombinált 150) | — |

A célok az átolvasás és javítás során **nem változtak**; a fenti táblázat a végső adatot méri. Két kvótasemleges
címkecsere történt tartalmi indokkal (`0114` hard→medium, `0133` medium→hard), és `0130` `sensitive_area` false→true
(ezért az érzékeny terület a 4-es korláton áll).

## 3. A tervezett változat-pár

| Pár | Azonosítók | Közös mag | Eltérés | Csoport |
|---|---|---|---|---|
| 4. pár | `multiturn_0104` / `multiturn_0144` | dolgozatra készülés időbeosztása (N hét, négy tétel, napi idő) | 0104 F1: irodalom, három hátralévő regény, oldalszám/nap, egy kieső hét átosztása; 0144 F8: biológia, négy témakör, óra/nap, a genetika átsúlyozása, napi beosztás; más név, szám, kérés és család | közös `split_group: g0104` |

Az MT-3 a párt kizárólag a deklarált csoport-él alapján kapcsolja (az önálló hasonlóság-elemzése nem talált köztük
jelzést), vagyis a deklaráció nem írta felül az MT-3 döntését; a próbafelosztásban mind a négy pár egy részbe került.

## 4. Feltárt és javított hibák (AI-alapú felülvizsgálat, 3 kör)

**Ez AI-alapú felülvizsgálat, nem független, nem emberi audit.** Részletes, rekordszintű napló: `audit_evidence/mt6_batch3/review_log.md`.

* 3 kör, friss kontextusú Claude-alügynökökkel (egy tartomány elakadt, kisebb részekre bontva újra futott), minden jelzést
  én is a tényleges szövegen ellenőriztem javítás előtt. Eredmény: 1. kör 13 OK / 37 javítandó; 2. kör (teljes újraolvasás)
  19 / 31; 3. kör (célzott, 12 rekord) 2 / 10; WITHHELD egyik körben sem.
* Az eredeti piszkozathoz képest **46 rekord módosult** (44-ben szöveg, 128 üzenet; 37-ben `meta.depends`), **4 változatlan** (`0105`, `0136`, `0143`, `0148`).
* Fő hibatípusok: tartalmilag téves vagy azonos váltáson belüli kontextusra épülő `depends` (~30 rekord); szolgáltatófüggő vagy
  volatilis állítás általános tényként (`0110`, `0111`, `0120`, `0130`, `0133`); kitalált vagy feltételezett információ
  (`0122`, `0127`, `0142`, `0147`); elhagyott vagy be nem teljesített kérés (`0139`, `0145`, `0146`, `0147`, `0149`); nyelvtan/természetesség.
* Ténybeli kérdésben egy esetben az alügynökök ellentmondtak egymásnak (`0120`, lakcímkártya 2025 utáni kiállítása és díja);
  két külön keresés is ellentmondó másodlagos forrást adott, ezért a rekord **semmit nem állít** a díjról és az automatizmusról,
  az ügyintézőhöz utal. Az ilyen pont **nem tekinthető igazoltnak**.
* A korábbi 100-hoz konkrét igazolt hiba hiányában nem nyúltam.

## 5. Technikai ellenőrzések

| Lépés | Eredmény |
|---|---|
| Friss TE-1 export | 4500 beolvasva, **6 kizárva**, 4494 exportálva; a `train_candidates.jsonl` sha256 egyezik a korábbival |
| MT-1, batch3 önmagában | 50/50 `turns-validált`, **0 hibás**, 49 figyelmeztetés (mind `capitalized_token_review`: bolygó- és égitest-nevek, `Nap`/`Föld`, `Önnek`/`Önnel`, `Nézet`, `Üdvözlettel`, regénycímek, `Ausztriába`) |
| MT-1, kombinált 150 | **0 hibás**, 5 + 13 + 49 = 67 figyelmeztetés, mind ilyen típusú és átolvasott (hely- és égitest-nevek, magázó névmás, felületi feliratok) |
| MT-3 (`full150_v1`) a kombinált 150 + a friss TE-1 export ellen | **0 találat**, 0 blokkolt rekord, 4 csoport (4 deklarált pár), változat-részesedés 0,053 |
| MT-2 próbafelosztás (120/15/15) | pontosan 120/15/15, 0 visszatartott, 0 szétvágott csoport; **nem a végleges 800/100/100, nem jóváhagyott** |
| MT-4 export (R1 + R2, dataset) | R2: 564 + 73 + 66 minta 100% veszteségmentes; R1: 226 + 28 + 23 veszteségmentes (a csonkolás miatti, dokumentált különbség); 0 visszatartott |
| MT-5 `--dry-run` (R2 elsődleges, R1 összehasonlító) | minden minta betöltve / kódolva / kötegelve / előrefuttatva, 0 hiba, 0 visszatartott |

Az eszközök kódját és küszöbeit nem módosítottam; a lezárt eszközök mutációs vizsgálatát **nem** futtattam újra. Az MT-3
korábbi piszkozat-futásai 3 `info` jelzést adtak (a `0134` kérdése a `simple_qa_0951` kérdésével, a `0108` kérdése a
`simple_qa_0223`-mal, a `0114` egyik kérdése a `0064`-gyel azonos); ezeket tartalmilag átfogalmaztam, az utolsó futás 0 találatot ad.

## 6. Hossz, szótár, nyitott korlátok

* Szótár: 83 karakter (+UNK+PAD), **kizárólag a train/R2 részből**. Ismeretlen karakter: 15 előfordulás, csak a validation részben,
  a `0` és `1` számjegy miatt (a korábbi `0014` „1830-tól … 1848-ig” szövege került a validation részbe; az új batchben nincs számjegy).
  A szótárat nem bővítettem a validation/test adatából.
* Minta-hossz: train R2 130–2840 karakter (átlag 653), R1 130–745 (átlag 360); a minták **100%-a** meghaladja a jelenlegi modell
  64 karakteres kontextusát — a beszélgetéseket **nem rövidítettem**. A 64 karakteres ablak kérdése változatlanul nyitott.
* **Nyitott:** (1) a független, emberi tartalmi átolvasás (kötelező tanítás előtti feltétel); (2) nem igazolt tények:
  lakcímkártya díja és kiállítása, egészségügyi általános tanácsok, sütési idők és mennyiségek, árszint-állítások, festék-fedés, vázméret;
  (3) a végleges felosztás jóváhagyása; (4) a 64 karakteres modell-kontextus kérdése; (5) a harmadik kör után újabb teljes AI-kör nem futott.

## 7. Fájlok és commit

* `data/raw|clean/claude_multiturn_0101_0150_*.jsonl` (új, 50 beszélgetés).
* `data/reports/audit_evidence/mt6_batch3/` (README, `review_log.md`, MT-1/MT-3/MT-2/MT-4/MT-5 és a friss TE-1 manifest).
* `data/reports/mt6_batch3_report.md` (ez a jelentés); `data/reports/multiturn_package7_plan.md`, `data/reports/dataset_autopilot_progress.md` (haladás-rögzítés; a 6–7. szakasz követelményei nem változtak).
* A célértékek commitja: `b54ca82`; az adat commitja: lásd a `git log`-ban (`v1.13.30-mt6-batch3`).
* `data/train/…` futás-mappák: munkamappák, nem verziókövetettek.

## 8. Következő lépés

A negyedik batch (`0151–0200`) vagy a független, emberi átolvasás külön, kifejezett jóváhagyást igényel. A független átolvasás
halmaza immár a kész 150 beszélgetés; ez marad a tanítás előtti kötelező feltétel. Tanítás és `training-ready` minősítés
továbbra sem engedélyezett.
