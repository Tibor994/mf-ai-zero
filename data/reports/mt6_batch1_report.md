# MT-6 — az első 50 valódi többfordulós beszélgetés (`claude_multiturn_0001_0050`) — jelentés (javított kiadás)

Dátum: 2026-10-02. Fájlok: `data/raw/claude_multiturn_0001_0050_raw.jsonl`, `data/clean/claude_multiturn_0001_0050_clean.jsonl` (azonos tartalom). Bizonyítékok: `data/reports/audit_evidence/mt6_batch1/`.

**Ez a javított kiadás** a 2026-09-30-i első kiadás (`v1.13.25-mt6-batch1`, commit `2f295b6`) hosszmegoszlási hiányosságát orvosolja a felhasználó kifejezett kérése alapján. **Ez a batch adat-előkészítés, nem tanítás.** A jóváhagyás kizárólag az 50 beszélgetés elkészítésére, javítására és technikai ellenőrzésére vonatkozott; tanítás, modellmódosítás és a második 50 generálása nem indult, és nem is ebben a körben történt.

## 0. A kiindulási állapot ellenőrzése

A `git diff 1a368e2 2f295b6 -- data/reports/multiturn_package7_plan.md` megerősíti: az MT-6 első kiadásakor a terv **6. szakaszában (az ellenőrzések listája) és a 7. szakaszában (az első 100 beszélgetés tervezett összetétele)** semmi nem módosult — ezek a felhasználó korábban jóváhagyott **követelményei**, a jelentésemben idézett 3/4/5/6/7/8 váltásos (10/15/13/7/3/2) célszámok is ebből a változatlan táblázatból lettek levezetve. Amit az előző commit módosított, az kizárólag **haladás-rögzítés** volt: a terv–tény táblázat „tény” oszlopa, az „Elkészült”/„Következő feladatok” táblák, és a „Döntések” szakasz nyitott pontjainak listája. A követelmények tehát nem lettek az elkészült (akkor még hiányos) adathoz igazítva; az eltérést az első jelentésben magam jeleztem eltérésként, és ezt a javított kiadás most megszünteti.

A „váltás” fogalmát a meglévő MT-0 formátum szerint használom: egy váltás = egy user + egy assistant üzenet (`meta.n_exchanges`); ez **nem azonos** az üzenetszámmal (ami a váltásszám kétszerese).

## 1. Mennyiség

| Mennyiség | Érték |
|---|---|
| Beszélgetés | **50** (`multiturn_0001`–`multiturn_0050`) |
| Üzenet | **468** (234 user + 234 assistant) |
| Váltás (`meta.n_exchanges` összesen) | **234** |
| Tanítási minta (egy assistant-fordulóra adott cél, előzménnyel) | **234** — ebből 50 első fordulós (előzmény nélkül), **184 előzmény-függő** |

## 2. Tervezett és tényleges összetétel (egymás mellett)

A terv (`data/reports/multiturn_package7_plan.md` 7. szakasza, változatlan) az **első 100** beszélgetésre ad konkrét arányokat; az első 50 célszámait ebből a **felére kerekítve** vezettem le (páratlan sorszámú tétel — család F1/F3/F5/F7/F9, váltásszám 3/5/7 — felfelé, páros lefelé, hogy az összeg pontosan 50 maradjon).

| Szempont | Terv (100 fele, kerekítve) | Tényleges (50, javított) |
|---|---|---|
| Család | F1 8, F2 6, F3 7, F4 6, F5 6, F6 4, F7 5, F8 5, F9 3 | **pontosan egyezik** |
| Tématerület | 10 × 5 | **pontosan egyezik** |
| Nehézség | easy 15, medium 25, hard 10 | **pontosan egyezik** |
| Register | tegező 43, magázó 7 | **pontosan egyezik** |
| **Hossz (váltás)** | **3: 10, 4: 15, 5: 13, 6: 7, 7: 3, 8: 2** | **3: 10, 4: 15, 5: 13, 6: 7, 7: 3, 8: 2 — pontosan egyezik** |
| Elírás a felhasználói üzenetben | ≈5 (10%) | 6 |
| Érzékeny terület | ≤4 | 4 |
| Mélység ≥2 előzmény-hivatkozás | ≥13 (fele a 100-as ≥25-nek) | **35** |
| ≥2 készség kombinálása | ≥20 (40%) | **34 (68%)** |
| Tervezett változat-pár | arányos rész a 100-as terv 3 párjából | 1 pár (`multiturn_0029`/`_0032`, közös `split_group`, eltérő névvel/létszámmal/étlappal, nem névcsere) |
| Asszisztens nyitószó | egyik sem >8% | **legfeljebb 7,7%** |

Minden korábbi eltérés megszűnt. A nehézség és a register pontos egyezéséhez két, tartalmilag indokolt
módosítás kellett (lásd 3. szakasz): `multiturn_0042` easy→medium (a bővített tartalom valódi, nagyobb
összetettséget kapott) és `multiturn_0030` tegező→magazo (a hivatalos ügyintézési téma a batch többi,
ügyintézés-témájú magázó rekordjával összhangban formálisabb regisztert indokol).

## 3. Módosított rekordok és az ok

**39 rekord** `turns` tartalma bővült 1–4 új, **valódi feladatot végző** fordulóval — pontosítás, korábbi
feltétel/adat felhasználása, javítás utáni további lépés, többlépéses feladat folytatása, vagy a család
szerinti más releváns készség. Nem üres köszönésekkel, ismétléssel vagy töltelékkel történt a bővítés. A
teljes lista és az egyes bővítések tartalmi jellege: lásd `data/reports/audit_evidence/mt6_batch1/README.md`
(„Módosított rekordok” táblázat). Összesen 71 új váltás (142 új üzenet) került be. A `meta.depends` minden
érintett rekordnál újraszámolt, a módosított hivatkozásokat külön átnéztem (lásd 4. szakasz).

**11 rekord változatlan maradt** (`multiturn_0005, 0016, 0018, 0019, 0021, 0034, 0036, 0037, 0048, 0049, 0050`):
ezek már a tervezett hosszon voltak, vagy a család definíciója szerint helyesen rövidek, teljes ívű
beszélgetések (pl. F9 bizonytalanság-mintázat, F6 pure témaváltás).

**Az első kiadás óta javított technikai hibák (a jelen, javított adatba már nem kerültek bele változatlanul):**
- Az előző kiadás `meta.depends` mezőit (ahol a hossz változott) teljesen újraszámoltam a tényleges, végleges `turns` tartalomhoz; egy önálló tartomány-ellenőrzés (`build_batch1.py`-ban) minden bejegyzést a saját, a `multiturn_validate.py`-val megegyező képlettel validált, mielőtt a fájl elkészült.
- Az asszisztens-válasz nyitószó-eloszlást a bővítés után újra megmértem: a sok új válasz miatt az „egy” (11,1%) és az „a” (10,3%) szó átlépte a 8%-os korlátot; 14 választ átfogalmaztam, amíg mindegyik nyitószó 7,7% alá került.

**Visszatartott vagy review-státuszban maradt eset: nincs.** Mind az 50 (javított) beszélgetés átment az
MT-1-en elsőre, az MT-3-on 0 találattal, az MT-2 próbafelosztáson 0 visszatartással, az MT-4-en 0 nem
ábrázolható rekorddal.

**Fennmaradó, review-t igénylő (de nem blokkoló) MT-1 figyelmeztetés: 2 db, mindkettő átolvasva és
ártalmatlannak minősítve** (ugyanaz, mint az első kiadásban): a „Bécsbe” városnév (nincs a névtár
engedélyezett listáján, de nem személynév) és az „Ön” formális névmás (a magázó regiszter szabályos,
nagybetűs formája). **Ez a saját, nem független átolvasásom minősítése**, nem helyettesíti a 6. szakasz
szerinti független/kiterjedt emberi átolvasást, ami az első 100 lezárásakor válik esedékessé.

## 4. Tartalmi és technikai ellenőrzés eredménye

A teljes, módosított tartalmat sorról sorra átolvastam, különös figyelemmel a módosított
`meta.depends` hivatkozásokra (minden bejegyzés `turn`/`on`/`depth` értékét kézzel visszakövettem a
tényleges szövegig, hogy valóban az ott hivatkozott korábbi fordulóra épül-e a válasz). Ez **saját,
nem független** átolvasás, nem helyettesíti a független auditot.

| Lépés | Eredmény |
|---|---|
| **MT-1** (`multiturn_validate.py`, dataset mód) | 50/50 `turns-validált`, 0 hibás rekord, 5 figyelmeztetés (2 egyedi, mindkettő átolvasva) |
| **MT-3** (`multiturn_dedupe.py`, a mind az 50 beszélgetés + a friss, valódi TE-1 export — 4500 sor beolvasva, 6 kizárva, 4494 exportálva — ellen) | 0 duplikáció-találat, 0 blokkolt rekord, 49 csoport (1 kettes, a tervezett-változat pár) |
| **MT-2** (`multiturn_split.py`, **próbafelosztás**, cél 40/5/5) | pontosan 40/5/5, 0 visszatartott, 0 szétvágott csoport — **nem a végleges 800/100/100 felosztás** |
| **MT-4** (`multiturn_export.py`, dataset mód) | R2: 185+22+27 minta, 100% veszteségmentes; R1: 185+22+27 minta, 85+10+10 veszteségmentes (a csonkolás miatti, dokumentált különbség); 0 visszatartott |
| **MT-5** (`train_multiturn.py`, dataset mód, `--dry-run`) | minden minta sikeresen betöltve/kódolva/kötegelve/előrefuttatva (0 hiba); kilépési kód 1 (**figyelmet kér**, nem hiba) — lásd az 5. szakaszt |

A javítás **egyetlen lezárt eszköz validátorát vagy küszöbét sem lazította**: az MT-1/MT-3/MT-2/MT-4/MT-5
kódja (és a hozzájuk tartozó, korábban lezárt mutációs vizsgálat) változatlan maradt, az adatot a
változatlan eszközökön futtattam újra. A lezárt eszközök teljes mutációs vizsgálatát nem ismételtem meg
(ez adatjavítás, nem eszközváltozás). Az ellenőrzés **új, visszakövethető kimenetbe** került: a korábbi
(`b1` nevű) próbafutás-mappákat törölve, a teljes MT-3→MT-2→MT-4→MT-5 láncot újra lefuttattam a javított
adaton, és a friss jelentéseket mentettem az `audit_evidence/mt6_batch1/` alá (a régi, első kiadáshoz
tartozó jelentéseket felülírva — a `data/train/` munka-mappák a projekt szabálya szerint amúgy sem
verziókövetettek).

A `split_approved`, `content_verified` és `training_ready` mezők a forrás-exportban és minden jelentésben
**változatlanul `false`** maradtak a teljes láncon át.

## 5. Hossz- és erőforrás-korlát

| Mutató | Érték |
|---|---|
| Minta-hossz (karakter, kódolt bemenet) | R2: kb. 128–900 (átlag ~400); R1: kb. 128–460 (átlag ~310) |
| Szótár mérete (train/R2, +UNK+PAD) | 72 (+2 = 74) |
| A jelenlegi betanított modell 64 karakteres kontextusán túli minták aránya | **100% minden részben, R1-ben és R2-ben is** |
| Ismeretlen (train-szótáron kívüli) karakter-előfordulás validation/test mintákban | 39, 4 megfigyelt karakter miatt: nagybetűs **Á**, **Ö**, illetve a **0**, **1** számjegy (lásd a README részletes magyarázatát) — kisminta-jelenség, nem hiba |
| Visszatartott (hosszkorlát fölötti) minta | 0 |

**A 100%-os arány ugyanazt a korlátot igazolja valódi adaton, amit az MT-5 1000 mesterséges beszélgetéses
mérése is mutatott**: a legrövidebb minta is kétszerese a jelenlegi betanított modell 64 karakteres tanult
kontextusának. Ez a betöltőtől független, a modell architektúrájának/tanításának korlátja (lásd
`mt5_report.md`); a sikeres betöltés/előrefutás itt sem bizonyítja a hosszú kontextus tényleges
megtanulását. A beszélgetéseket **nem rövidítettem** ehhez a korláthoz — a hosszmegoszlás-javítás
kifejezetten a terv szerinti, hosszabb beszélgetések megírásáról szólt, a 64 karakteres ablak kérdése
továbbra is külön, a tanítás megindítása előtt megoldandó probléma.

## 6. Fájlok és commit

- `data/raw/claude_multiturn_0001_0050_raw.jsonl`, `data/clean/claude_multiturn_0001_0050_clean.jsonl` — a javított 50 beszélgetés (azonos tartalom), **felülírva** az első kiadás tartalmát, azonos azonosítókkal.
- `data/reports/audit_evidence/mt6_batch1/` — frissített MT-1/MT-3/MT-2/MT-4/MT-5 jelentések és README (a 2. változat jelzéssel).
- `data/reports/mt6_batch1_report.md` — ez a jelentés (javított kiadás).
- `data/train/te1_export/`, `data/train/multiturn_mt2|mt3|mt4|mt5/b1/` — a próbafuttatások munka-mappái; a projekt szabálya szerint **nem verziókövetettek**.
- Terv/haladás-dokumentumok: `data/reports/multiturn_package7_plan.md`, `data/reports/dataset_autopilot_progress.md` — a hosszmegoszlás-javítás tényét rögzítik, a **követelményeket (6–7. szakasz) nem módosítják**.
- Commit: lásd a verziószámot a `git log`-ban (a következő szabad verzió az előző `v1.13.25-mt6-batch1` után).

## 7. Fennmaradó korlátok

- A jelen batch **nem független emberi/szakértői átolvasáson** esett át — ez a terv 6. szakasza szerint az első 100 lezárásakor válik esedékessé.
- A 64 karakteres tanítási ablak korlátja (5. szakasz) továbbra is fennáll; a tényleges tanítás bemenetének kérdése (R1/R2, a modell kontextushossza) változatlanul nyitott, a korábbi MT-5 jelentésben leírtak szerint.
- A tervezett-változat párok száma (1 db) a 100-as terv 3 párjának csak egy részét fedi — ez a második 50 tervezésénél pótolható.
- A második 50 (`multiturn_0051`–`_0100`) és a tanítás megindítása ebben a körben **nem indult**, külön, kifejezett jóváhagyást igényel.
