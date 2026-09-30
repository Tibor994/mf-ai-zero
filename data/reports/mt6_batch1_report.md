# MT-6 — az első 50 valódi többfordulós beszélgetés (`claude_multiturn_0001_0050`) — jelentés

Dátum: 2026-09-30. Fájlok: `data/raw/claude_multiturn_0001_0050_raw.jsonl`, `data/clean/claude_multiturn_0001_0050_clean.jsonl` (azonos tartalom — a batch minden rekordja elsőre átment az MT-1-en, nem volt tartalmi javítást igénylő elutasítás). Bizonyítékok: `data/reports/audit_evidence/mt6_batch1/`.

**Ez a batch adat-előkészítés, nem tanítás.** A jóváhagyás kizárólag az 50 beszélgetés elkészítésére és technikai ellenőrzésére vonatkozott; tanítás, modellmódosítás és a második 50 generálása nem indult, és nem is ebben a körben történik.

## 1. Mennyiség

| Mennyiség | Érték |
|---|---|
| Beszélgetés | **50** (`multiturn_0001`–`multiturn_0050`) |
| Üzenet | **326** (163 user + 163 assistant) |
| Tanítási minta (egy assistant-fordulóra adott cél, előzménnyel) | **163** — ebből 50 első fordulós (előzmény nélkül), **113 előzmény-függő** |

## 2. Tervezett és tényleges összetétel

A terv (`data/reports/multiturn_package7_plan.md` 7. szakasza) az **első 100** beszélgetésre ad konkrét arányokat, két 50-es alegységre bontva; mivel a szakasz nem bont tovább külön az első és második 50-re, az első 50 célszámait a 100-as arányok **felére kerekítve** vezettem le. A kerekítési szabály: páratlan sorszámú tétel (család: F1, F3, F5, F7, F9; hossz: 3, 5, 7 váltás) felfelé, páros lefelé kerekítve, hogy az összeg pontosan 50 maradjon.

| Szempont | Terv (100 fele, kerekítve) | Tényleges (50) | Megjegyzés |
|---|---|---|---|
| Család | F1 8, F2 6, F3 7, F4 6, F5 6, F6 4, F7 5, F8 5, F9 3 | **pontosan egyezik** | — |
| Tématerület | 10 × 5 | **pontosan egyezik** | — |
| Nehézség | easy 15, medium 25, hard 10 | easy 16, medium 24, hard 10 | ±1 easy/medium, elhanyagolható |
| Register | tegező 43, magázó 7 | tegező 44, magázó 6 | ±1, elhanyagolható |
| Hossz (váltás) | 3: 10, 4: 15, 5: 13, 6: 7, 7: 3, 8: 2 | 3: 39, 4: 9, 5: 2, 6–8: 0 | **jelentősen eltér, lásd alább** |
| Elírás a felhasználói üzenetben | ≈5 (10%) | 6 | teljesül |
| Érzékeny terület | ≤4 | 4 | pontosan a felső korláton |
| Mélység ≥2 előzmény-hivatkozás | ≥13 (fele a 100-as ≥25-nek) | **27** | jelentősen meghaladja |
| ≥2 készség kombinálása | ≥20 (40%) | **34 (68%)** | jelentősen meghaladja |
| Tervezett változat-pár | 1–2 (a 100-as terv 3 párjának arányos része) | 1 pár (`multiturn_0029`/`_0032`, közös `split_group`) | teljesül |
| Asszisztens nyitószó | egyik sem >8% | **legfeljebb 7,4%** | teljesül (lásd 3. szakasz) |

**A hosszeloszlás eltérésének oka és értékelése:** az eredeti terv az első 100-ra még 6–8 váltásos beszélgetéseket is előírt jelentős arányban; írás közben minden beszélgetést a saját, természetes lezárási pontjáig írtam meg (nem toldottam meg mesterségesen egy előre rögzített váltásszámra), és a család mintázatai (F3 pontosítás, F6 témaváltás) többségében már 3 váltás alatt teljesen, hitelesen lezárhatók voltak. Az eredmény: több rövidebb (3–4 váltásos), de **mindegyik teljes ívű, természetes** beszélgetés, kevesebb hosszú. Ez **nem a minőség rovására** történt — ellenkezőleg, a mesterséges megnyújtás sablonos, ismétlődő fordulókhoz vezetett volna, amit a jóváhagyás kifejezetten tiltott. Az F7 (témaváltás-visszatérés) és F8 (többlépéses feladat) családok hosszabbak (4 váltás átlagosan), mert a mintázatuk ezt igényli; a leghosszabb, 8 váltásos tervezett tétel jelenleg nincs a batchben — ez a második 50 tervezésénél pótolható, ha szükséges.

## 3. Írás közben javított hibák

**Nem tartalmi (technikai) hibák, mind az írás közben, a commitolt tartalomba kerülés ELŐTT javítva:**
- **`meta.depends` index-hibák (32 rekord):** a beszélgetések hosszának írás közbeni finomítása miatt több `depends` bejegyzés hibás (nem létező) fordulóra mutatott. Mindegyiket a tényleges, végleges `turns` tartalomhoz igazítva javítottam, és egy önálló ellenőrző szkript (`build_batch1.py`) minden bejegyzést a saját, a `multiturn_validate.py`-val megegyező képlettel újraszámolt — ez az MT-1 saját, független ellenőrzésén is átment.
- **`content_overclaiming` (1 rekord, `multiturn_0003`):** egy felhasználói üzenet szó szerint tartalmazta a tiltólistás „mindent tudok” kifejezést (ártalmatlan összefüggésben: „most már megvan minden, amire szükségem van a leveshez”); átfogalmaztam.
- **`meta.fixture` hiánya:** az MT-1 ezt opcionálisnak tekinti, de az MT-4 exportáló szigorúbb, kifejezett `false` értéket vár `dataset` módban; minden rekordhoz hozzáadtam.
- **Egy F6 (témaváltás) rekord (`multiturn_0035`) tévesen visszatért az eredeti témára** (ami F7 mintázat, nem F6) — a záró fordulót átírtam, hogy valóban új témán maradjon, a család definíciójával összhangban.
- **Asszisztens-válasz nyitószó-eloszlás:** az első teljes átolvasáskor a „Szia” szó 25,8%-ban nyitotta a válaszokat (a terv ≤8%-os korlátja fölött); 32 választ átfogalmaztam (más köszönés, vagy a névvel/tartalommal induló mondat), majd a második átolvasáskor kiderült, hogy az „egy” és az „akkor” szavak vették át a túlreprezentált szerepet (14,7%, illetve 11,7%) — ezeket is átfogalmaztam (19 további válasz), amíg egyetlen nyitószó sem haladta meg a 7,4%-ot.

**Visszatartott vagy review-státuszban maradt eset: nincs.** Mind az 50 beszélgetés átment az MT-1-en elsőre (a fenti javítások az írás közbeni, commit előtti iteráció részei voltak, nem az MT-1 elutasításai), az MT-3-on 0 találattal, az MT-2 próbafelosztáson 0 visszatartással, az MT-4-en 0 nem ábrázolható rekorddal.

**Fennmaradó, review-t igénylő (de nem blokkoló) MT-1 figyelmeztetés: 2 db, mindkettő átolvasva és ártalmatlannak minősítve** (lásd `data/reports/audit_evidence/mt6_batch1/README.md`): a „Bécsbe” városnév (nincs a névtár engedélyezett listáján, de nem személynév) és az „Ön” formális névmás (a magázó regiszter szabályos, nagybetűs formája).

## 4. Az ellenőrzések eredménye

| Lépés | Eredmény |
|---|---|
| **MT-1** (`multiturn_validate.py`, dataset mód) | 50/50 `turns-validált`, 0 hibás rekord, 5 figyelmeztetés (2 egyedi, mindkettő átolvasva) |
| **MT-3** (`multiturn_dedupe.py`, a batch + a friss, valódi TE-1 export — 4500 sor beolvasva, 6 kizárva, 4494 exportálva — ellen) | 0 duplikáció-találat, 0 blokkolt rekord, 49 csoport (1 kettes, a tervezett-változat pár) |
| **MT-2** (`multiturn_split.py`, **próbafelosztás**, cél 40/5/5) | pontosan 40/5/5, 0 visszatartott, 0 szétvágott csoport — **nem a végleges 800/100/100 felosztás** |
| **MT-4** (`multiturn_export.py`, dataset mód) | R2: 131+16+16 minta, 100% veszteségmentes; R1: 131+16+16 minta, 81+10+10 veszteségmentes (a csonkolás miatti, dokumentált különbség); 0 visszatartott |
| **MT-5** (`train_multiturn.py`, dataset mód, `--dry-run`) | minden minta sikeresen betöltve/kódolva/kötegelve/előrefuttatva (0 hiba); kilépési kód 1 (**figyelmet kér**, nem hiba) — lásd az 5. szakaszt |
| Regresszió | ehhez a batchhez külön regressziós futtatás nem volt szükséges (a meglévő eszközök saját, lezárt tesztkészletét nem módosítottam); a batch az eszközök **változatlan, már tesztelt** kódján futott végig |

A `split_approved`, `content_verified` és `training_ready` mezők a forrás-exportban és minden jelentésben **változatlanul `false`** maradtak a teljes láncon át.

## 5. Hossz- és erőforrás-korlát

| Mutató | Érték |
|---|---|
| Minta-hossz (karakter, kódolt bemenet) | R2: 128–897 (átlag ~396, medián ~380); R1: 128–459 (átlag ~308, medián ~336) |
| Szótár mérete (train/R2, +UNK+PAD) | 70 (+2 = 72) |
| A jelenlegi betanított modell 64 karakteres kontextusán túli minták aránya | **100% minden részben, R1-ben és R2-ben is** |
| Ismeretlen (train-szótáron kívüli) karakter-előfordulás validation/test mintákban | 6 (egyetlen ok: a nagybetűs „Ö” az „Ön” szóból, ami csak a próbafelosztás test részébe került beszélgetésben fordul elő — kisminta-jelenség, nem hiba) |
| Visszatartott (hosszkorlát fölötti) minta | 0 |

**A 100%-os arány ugyanazt a korlátot igazolja valódi adaton, amit az MT-5 1000 mesterséges beszélgetéses mérése is mutatott**: a legrövidebb minta (128 karakter) is kétszerese a jelenlegi betanított modell 64 karakteres tanult kontextusának. Ez a betöltőtől független, a modell architektúrájának/tanításának korlátja (lásd `mt5_report.md`); a sikeres betöltés/előrefutás itt sem bizonyítja a hosszú kontextus tényleges megtanulását.

## 6. Fájlok és commit

- `data/raw/claude_multiturn_0001_0050_raw.jsonl`, `data/clean/claude_multiturn_0001_0050_clean.jsonl` — a 50 beszélgetés (azonos tartalom).
- `data/reports/audit_evidence/mt6_batch1/` — MT-1/MT-3/MT-2/MT-4/MT-5 jelentések és README.
- `data/reports/mt6_batch1_report.md` — ez a jelentés.
- `data/train/te1_export/`, `data/train/multiturn_mt2|mt3|mt4|mt5/b1/` — a próbafuttatások munka-mappái; a projekt szabálya szerint **nem verziókövetettek** (`.gitignore`), a végleges bizonyítékot az `audit_evidence/mt6_batch1/` másolatai őrzik.
- Terv/haladás-dokumentumok frissítve: `data/reports/multiturn_package7_plan.md`, `data/reports/dataset_autopilot_progress.md`.
- Commit: lásd a verziószámot a `git log`-ban (`v1.13.25` vagy a következő szabad verzió).

## 7. Mi szükséges a második 50 előtt

- **Kifejezett jóváhagyás** a második 50 (`multiturn_0051`–`_0100`) elkészítésére — ez a jelentés csak az elsőt zárja le.
- Érdemes a második 50-nél **hosszabb (6–8 váltásos) beszélgetésekre nagyobb súlyt helyezni**, mivel az első 50 ezekből keveset tartalmazott (lásd 2. szakasz) — így a teljes első 100 közelebb kerül a terv szerinti hosszeloszláshoz.
- A tervezett-változat párok száma is pótolható: a terv 3 párt irányoz elő az első 100-ra, eddig 1 készült el.
- A jelen batch **nem független emberi/szakértői átolvasáson** esett át (csak a saját, az MT-0 dokumentáció szerint dokumentáltan nem független átolvasásomon) — ez a 6. szakasz szerint az első 100 lezárásakor válik esedékessé.
- A tényleges tanítás bemenetének kérdése (R1/R2, a modell kontextushossza) továbbra is nyitott, változatlanul a korábbi MT-5 jelentésben leírtak szerint.
