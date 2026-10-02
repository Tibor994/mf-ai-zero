# 7. csomag — 1000 többfordulós beszélgetés (`multiturn`) — előkészítő terv

Dátum: 2026-10-02. 9. változat (TE-2, MT-0, MT-1, MT-3 [revideálva: mt3-2.0], MT-2, MT-4, MT-5 elkészült; **MT-6 első batch (50 beszélgetés) elkészült, a hosszmegoszlás javított kiadásban pontosan a 7. szakasz szerinti**; a felhasználó jóváhagyásai és a teljes 17 000 soros terv beépítve; a 7. szakasz tervezett arányai a javítás során sem módosultak).

**Állapot:** elkészült és tesztelt a TE-1 (kizáró exportáló), a TE-2 (előkészítő `User:/AI:` szövegexport), az MT-0 (formátum-specifikáció, névtár, tesztfixture), az MT-1 (beszélgetés-validátor), az MT-3 (beszélgetés-szintű duplikáció-ellenőrzés és csoportképzés, `tools/multiturn_dedupe.py`, a felhasználó döntései szerint revideálva), az MT-2 (csoport-tudatos, reprodukálható felosztás, `tools/multiturn_split.py`), az MT-4 (a felosztott beszélgetések renderelése és exportálása kizárási szűrővel, `tools/multiturn_export.py`) és az MT-5 (elkülönített, tanítás nélküli betöltő és száraz futás, `src/train_multiturn.py`). **Az első 50 valódi, datasetbe szánt beszélgetés (`claude_multiturn_0001_0050`) elkészült és a teljes MT-1→MT-3→MT-2 (próbafelosztás)→MT-4→MT-5 láncon átment** (lásd `data/reports/mt6_batch1_report.md`). A meglévő validátorok, tanító és chat kód, valamint a webapp/backend változatlanok. Tanítás nem indult; a 7. csomag adatai 50/1000-nél tartanak, **nem training-ready**. **Három külön állapot:** technikai kompatibilitás (TE-2 a régi betöltővel, MT-5 a betöltés/kódolás/kötegelés/előrefutás szintjén — most már az első 50 valódi beszélgetésen is igazolva), tartalmi ellenőrzés (csak saját, nem független átolvasás történt), a tanítás megindításának engedélye (nincs) — egyik sem következik a másikból.

## 0. A 6. csomag (uncertainty_source_request) rögzített állapota

**KORLÁTOZOTT LEZÁRÁS.** A csomag nem teljesen ellenőrzött és **nem training-ready**. (A korábbi jelentésekben szereplő „tanításra elfogadott halmaz 4494/4500” megfogalmazást ezért „tanításra jelölt (nem training-ready)” megfogalmazásra javítottam.)

| Követő | Nyitott tétel | Sorok / hatókör | Hol követhető |
|---|---|---|---|
| N-1 | Kizárt sorok: jogi átnézés | `0220`, `0829`, `0849`, `0864` | `audit_evidence/uncertainty_source_request_1000/training_exclusion_pending_review.txt` |
| N-2 | Kizárt sorok: forrás nem nyitható meg | `0602`, `0898` | ugyanott |
| N-3 | Köznapi állítás, forrás nem ellenőrizve (E) | `0169 0170 0195 0319 0347 0543 0568 0569 0845 0895` | `contrast_125_table.md` |
| N-4 | Hedge-elt, forrás nélküli számok (nem kontraszt) | `0809 0840 0844 0876 0953 0974 0991` | 1. audit 6. szakasz |
| N-5 | 39 előtag nélküli kontraszt-sor újracímkézése | 2.–3. batch | 1. audit 12. szakasz |
| N-6 | 14 ismétlődő `kind` címke | 1. audit | 1. audit 12. szakasz |
| N-7 | Független emberi/szakértői átolvasás | teljes csomag | nem végzett |
| N-8 | A kizárás technikai kikényszerítése | lásd 2. szakasz | **TE-1 kész** (exportálón át kikényszerítve); a tanító oldali betöltés is kész (TE-2, MT-5), a tényleges tanítás megindítása még nincs |

## 1. Terv–tény táblázat (a teljes, érvényes 17 000 soros terv szerint)

Forrás: a tényleges fájlok (`data/raw|clean|rejected/*.jsonl`) soronkénti megszámolása; a tervoszlop a felhasználó által jóváhagyott, teljes adatterv. **A korábbi csomagok kezdő adagjainak elkészülte nem jelenti a kibővített céljuk teljesülését.**

| # | Csomag | Terv | Clean (tény) | Teljesítés | Hiányzik | Raw (érvényes JSON sor) | Rejected | Státusz |
|---|---|---|---|---|---|---|---|---|
| 1 | Magyar hétköznapi tudás (`simple_qa`) | 3000 | 1000 | 33,3% | 2000 | 1007 (2 nem parse-olható sor a `deepseek_simple_qa_0151_0200` és `_0201_0250` raw fájlban, változatlanul) | 9 | **kezdő adag kész, auditált; a cél NEM teljesült** |
| 2 | Magyarázós/tanítós válaszok (`explanation`) | 3000 | 1000 | 33,3% | 2000 | 1003 | 3 | **kezdő adag kész; a cél NEM teljesült** |
| 3 | Lépésenkénti feladatmegoldás (`step_by_step`) | 2000 | 500 | 25,0% | 1500 | 500 | 402 (`chatgpt` inbox importok, séma-hibás sorok) | **kezdő adag kész; a cél NEM teljesült** |
| 4 | Összegzés és átfogalmazás (`summary`) | 2000 | 500 | 25,0% | 1500 | 500 | 0 | **kezdő adag kész; a cél NEM teljesült** (a 500 sor összegzés; az átfogalmazás-jellegű tartalom külön nincs mérve) |
| 5 | Hibás felhasználói szöveg értése (`noisy_input`) | 2000 | 500 | 25,0% | 1500 | 500 | 0 | **kezdő adag kész; a cél NEM teljesült** |
| 6 | Bizonytalanság / forráskérés (`uncertainty_source_request`) | 1000 | 1000 (ebből 6 kizárt) | 100% a darabszámra | 0 | 1000 | 0 | **korlátozott lezárás**, nem training-ready |
| 7 | Többfordulós beszélgetés (`multiturn`) | 1000 | 50 | 5,0% | 950 | 50 | 0 | **első batch (0001–0050) kész, technikailag ellenőrzött; nem training-ready** |
| 8 | Személyiség/stílus adaptáció | 1000 | 0 | 0% | 1000 | 0 | 0 | nem kezdődött |
| 9 | Safety/határok | 1000 | 0 | 0% | 1000 | 0 | 0 | nem kezdődött (a 6. csomag „nem kamuzik” sorai nem safety-csomag) |
| 10 | Nextora saját tudás | 1000 | 0 | 0% | 1000 | 0 | 0 | nem kezdődött (csak repo/dokumentum alapján, kitalálás tilos) |
| | **Összesen** | **17 000** | **4550** | **26,8%** | **12 450** | 4560 (2 hibás) | 414 | |

Ellenőrzés: 3000+3000+2000+2000+2000+1000×5 = 17 000; hiányzó: 2000+2000+1500+1500+1500+950+1000×3 = 12 450. A tényleges fájlokból a clean összeg 1000+1000+500+500+500+1000+50 = 4550 (a 7. csomag 50 sora még **nem** training-ready, lásd 5-ös lábjegyzet fent).

Megjegyzések:
* A régi 9 csomagos roadmap (4900 sor) és annak „webes összefoglaló” (300) csomagja ebben a tervben már nem szerepel; a régi roadmap számozása nem irányadó.
* A haladási fájl korábbi „KÉSZ” jelölései az 1–5. csomag **kezdő adagjára** vonatkoztak; a fenti táblázat felülírja őket.
* A 4. csomag „átfogalmazás” és az 5. csomag „értés” jellegű része a meglévő adatban csak részben mérhető (összegzés, illetve hibás → javított szöveg): tartalmi lefedettségi audit szükséges, mielőtt a kibővített cél kiosztásra kerül.

## 2. A hat kizárt sor kihagyása: TE-1

**Kiindulás (ellenőrizve a fájlokból, a TE-1 előtt):** a kizárás csak dokumentálva volt; a listát semmilyen kód nem olvasta, és nem létezett JSONL→tanítóadat út (`src/train_chat.py` csak a kézzel írt `data/chat_train*.txt` fájlokat olvassa, `data/train/` üres).

**TE-1 (kész, elkülönített eszköz):** `tools/dataset_export_train.py`, tesztek: `tests/test_te1_dataset_export.py` (35 teszt). A meglévő tanító és chat kód nem módosult.
* A listát szigorúan beolvassa, és **egyértelmű hibával megáll** (10-es kilépési kód), ha a lista hiányzik, üres (kifejezett `--allow-empty-exclusions` nélkül), hibás formátumú sort vagy nem szabályos/duplikált azonosítót tartalmaz, egy azonosító nem szerepel a clean sorok között, vagy nem egyértelmű (több sor).
* **Kétirányú konzisztencia:** ha egy clean sor `quality_notes` mezője kizárás-jelölést hordoz, de az azonosítója nincs a listán, az export megáll → egy sor észrevétlen kivétele a listából, vagy az üres lista sem oldja fel a kizárást. Nincs olyan kapcsoló, amely kikapcsolná a kizárást.
* A kizárt sorokat **nem törli és nem módosítja** a clean fájlokban; a forrásfájlok sha256-ját a futás előtt és után is összeveti.
* **Visszakövethető export** új futás-mappába (soha nem ír felül): `train_candidates.jsonl` (a nem kizárt sorok, bájt-hűen), `export_index.tsv` (azonosító, forrásfájl, forrássor, sor-sha256), `manifest.json` (forrásfájlok sha256/sorszám/CRLF, lista sha256, kizárt sorok fájl+sor+sha256, darabszámok kategóriánként, ellenőrzések, git commit). A kimenetet lemezről visszaolvasva ellenőrzi (nincs kizárt azonosító, darabszámok egyeznek, sor-sha256 egyezik); hiba esetén `.partial` fájlok és `FAILED.txt` marad, manifest nélkül.
* **Valós adaton:** 4500 sor beolvasva, **6 kizárva** (`uncertainty_source_request_0220 0602 0829 0849 0864 0898`), **4494 exportálva**; a tesztek külön, független összevetéssel is egyeznek; a clean fájlok sha256-ja a futás előtt és után azonos. Az export **nem** tartalmi ellenőrzés és **nem** training-ready állapot (a manifest `content_verified: false`, `training_ready: false`).

**Ami még hiányzik a tanítás előtt (követő):**
* **TE-2 kész** (`tools/dataset_export_chat_text.py`): a TE-1 exportból előkészítő `User:/AI:` szöveg, a régi betöltővel (tanítás nélkül) igazolt technikai kompatibilitással; **nem** felosztás, nem tartalmi ellenőrzés, nem training-ready. A jelenlegi `train_chat.py` továbbra sem olvassa a JSONL-t: adat **csak a TE-1/TE-2 exporton át** kerülhet tanítóadatnak.
* Hiányzik: a train/validation/test felosztás (külön követelmény), a tartalmi lezárás (6. csomag nyitott tételei), és a tanítás megindításának kifejezett engedélye.

## 3. Többfordulós formátum

### 3.1 A meglévő formátum és a betöltő ténylegesen

| Elem | Tény | Következmény a többfordulós adatra |
|---|---|---|
| JSONL séma | 9 kötelező mező (`id, category, instruction, input, output, tags, difficulty, quality_notes, source`); a validátor **nem utasítja el** az extra mezőket, nincs kategória-fehérlista, és csak a 9 mezőt vizsgálja → egy `multiturn` fájl a régi validátoron **átmenne**, ami hamis biztonságot adna | egy `turns` tömb a régi validátorral nem ellenőrződik (PII, veszélyes tartalom, torz szöveg a közbenső fordulókban észrevétlen maradna) |
| Kimenet-korlát | `output` 3–1500 karakter, `difficulty` easy/medium/hard | asszisztens-fordulók ennél rövidebbek lesznek |
| Tanító szkript | `train_chat.py`: `User:/AI:` szöveg, blokkok elválasztása üres sorral (`\n\n`), a train/val felosztás **véletlenszerű blokkonként** (`val_split=0,1`, seed 1337) | ha egy beszélgetésben `\n\n` van, a betöltő szétvágja, és a darabok különböző (train/val) részbe kerülhetnek → **szivárgás**; csoport-tudatos felosztás nincs |
| Minta-vétel | `get_batch`: véletlen ablakok, **`seq_length = 64` karakter**, állapot-átvitel nélkül | a modell a tanításkor legfeljebb 64 karakternyi kontextust lát; ennél régebbi előzményt **nem tanul meg használni** |
| Futásidejű előzmény | `memory.build_prompt_context`: **csak a legutolsó egy váltás**, `User: ≤80 kar.\nAI: ≤120 kar.\n\n`; `conversation_manager`: rövid (≤200 kar.) összefoglaló `User: Miről beszélgettünk eddig?\nAI: …` alakban, csak kifejezett utalásnál („folytasd”, „az előző”, „ezt javítsd”…) | a modell ma legfeljebb 1 korábbi váltást, vagy rövid összefoglalót kap; mélyebb előzmény futásidőben **nem érhető el** (ennek módosítása webapp/backend-kód → külön jóváhagyás) |
| Karakteres szótár | a szótár a tanítószövegből épül | új karakter (pl. ritka írásjel) a szótárt változtatja |

### 3.2 Formátum: egy rekord = egy beszélgetés (ELFOGADVA)

**Kanonikus tárolás (elfogadva):** soronként egy beszélgetés, a 9 meglévő mező megtartásával + új mezők; **az üzenetek sorrendjét és szerepeit a `turns` tömb őrzi meg**:

```json
{"id": "multiturn_0001", "category": "multiturn",
 "instruction": "<az első felhasználói üzenet>", "input": "", "output": "<az utolsó asszisztens-üzenet>",
 "tags": ["magyar", "instruction_core", "tobbfordulos", "<csalad-slug>"],
 "difficulty": "medium", "quality_notes": "...", "source": "claude_generated",
 "turns": [{"role": "user", "text": "..."}, {"role": "assistant", "text": "..."}, ...],
 "meta": {"family": "F5", "skills": ["valtozo_keres", "elozmeny_koveteles"], "n_exchanges": 4,
          "split_group": "g0001", "persona": "p017", "domain": "vasarlas",
          "depends": [{"turn": 4, "on": [1, 3], "depth": 2}]}}
```

* A 9 régi mező **származtatott** (első user / utolsó assistant), hogy a régi eszközök ne omoljanak össze; **a régi eszközök eredménye a közbenső fordulókra nem bizonyíték** (ezért kell új ellenőrzés, lásd 6. szakasz).
* Miért nem „egy fordulóra egy sor” (`instruction`=aktuális üzenet, `input`=előzmény)? Az működne a jelenlegi eszközökkel kódmódosítás nélkül, de: (1) a beszélgetés nem atomi → a felosztás/szivárgás nehezebben védhető, (2) az előzmény minden sorban ismétlődik (négyzetes redundancia), (3) a „példa” fogalma szétesik, (4) a beszélgetés-szintű duplikáció nem látszik. Ezért ez csak tartalék változat marad.
* Rendszer-üzenet nincs (a jelenlegi modell sem használ).

**Három renderelés (az exportáló készíti, a kanonikus adatot nem módosítja):**

| Mód | Tartalom | Cél |
|---|---|---|
| **R1** (futásidő-hű) | a cél előtti **1** utolsó váltás, `User ≤80 / AI ≤120` karakterre vágva, `\n\n`-nel, majd `User: <aktuális>\nAI: <cél>` | ezt a promptot adja ma a `memory.py`; ez a közvetlenül tanítható minta |
| **R3** (összefoglaló) | `User: Miről beszélgettünk eddig?\nAI: <arany összefoglaló ≤200 kar.>\n\n` + aktuális kérés | a `conversation_manager` prompt-alakja; mély visszautalásoknál (téma-visszatérés). **Döntés kell**, mert kézi „arany” összefoglalót igényel |
| **R2** (teljes előzmény) | a teljes beszélgetés a célig | értékeléshez és egy későbbi, hosszabb kontextust használó betöltőhöz; a jelenlegi futásidő ezt nem adja |

### 3.3 Mi számít egy „példának” az 1000-es célban? (ELFOGADVA)

**Egy példa = egy teljes beszélgetés** (egy `multiturn_NNNN` rekord). A cél tehát **1000 beszélgetés**. Külön jelentendő mennyiségek (a terv szerint):

| Mennyiség | Terv | Levezetés |
|---|---|---|
| **Beszélgetés** | **1000** | a cél |
| Váltások (user+assistant pár) | **4690** | 3 váltás: 200 beszélgetés, 4: 300, 5: 250, 6: 150, 7: 60, 8: 40 → 600+1200+1250+900+420+320 |
| **Üzenetek** | **9380** | 4690 user + 4690 assistant |
| **Tanítási minták** (egy minta = egy assistant-fordulóra adott cél, előzménnyel) | **4690** | ebből 1000 az első fordulóé (előzmény nélkül, a meglévő egyfordulós adathoz hasonló), **3690 előzmény-függő** |
| Előzmény-függő minták mélysége | kb. 70% mélység-1 (≈2600, R1-gyel tanítható), kb. 30% mélység ≥2 (≈1090, R3 vagy R2 kell) | tervezett arány; a `meta.depends` annotációval mérendő |
| Becsült szöveghossz | kb. 1,2–1,5 millió karakter (kanonikus) | 4690 váltás × (≈70 + ≈220 karakter) |

Az „1000 példa” mindig a beszélgetésekre vonatkozik; **a beszélgetések, az üzenetek és az ezekből később képzett tanítási minták száma minden jelentésben külön szerepel**, a mintaszám nem számít bele a célba.

Hosszkorlátok: user-üzenet ≤300 karakter; assistant-üzenet 1–4 mondat, ≤600 karakter (javasolt medián ≈200); beszélgetés 3–8 váltás.

## 4. Lefedettség és tartalmi irányelvek

### 4.1 Forgatókönyv-családok (elsődleges család, összesen 1000)

| Család | Mit tanít | Cél (db) |
|---|---|---|
| F1 Előzmény követése | korábban megadott adat (kitalált név, összeg, időpont, preferencia) helyes használata több fordulóval később | 150 |
| F2 Visszautalás | „az”, „ezt”, „a másodikat”, „amit az előbb mondtam” feloldása | 130 |
| F3 Pontosítás | a modell visszakérdez, a felhasználó válaszol, a modell ennek megfelelően fejezi be | 130 |
| F4 Felhasználói javítás | a felhasználó javítja a modellt vagy önmagát („nem 5, hanem 6 fő”); a modell javít, **nem** hízelgő; ebből 25 olyan, ahol a felhasználó javítása téves, és a modell udvariasan kitart a helyes állítás mellett | 130 |
| F5 Változó kérés | a feltétel menet közben változik („mégis inkább olcsóbb”), a modell a legfrissebbet használja | 110 |
| F6 Témaváltás | hirtelen új téma, a régi téma nem szivárog át | 90 |
| F7 Témaváltás és visszatérés | A → B → vissza A-ra a korábbi részletekkel | 100 |
| F8 Több lépésben befejezett feladat | terv → lista → piszkozat → módosítás → végleges | 110 |
| F9 Bizonytalanság többfordulóban | a modell nem tudja, forrást kér / pontosít; a 6. csomag elveivel (nem kamuzik), előzményekkel | 50 |
| | **Összesen** | **1000** |

Keresztmetszeti követelmény: a beszélgetések legalább 40%-a legalább két készséget kombinál (`meta.skills`).

### 4.2 Természetes, változatos magyar nyelv

* Többnyire tegező, kb. 15% magázó; a felhasználói üzenetek hossza, hangneme, kérdés-/kijelentő formája vegyes (a 6. csomag tapasztalata: zárt „ugye?” forma is számít).
* Felhasználói üzenetek legfeljebb 10%-a könnyű elírással/ékezet nélkül (természetesség; a `noisy_input` csomaggal nem ismétlő), az asszisztens mindig helyesen ír.
* Asszisztens: nem kezdődhet minden válasz ugyanúgy (egy nyitó szó ≤ 8%), nincs sablonismétlés; nem túl óvatos, csak ahol kell.
* Tématerületek (10, egyenként legfeljebb ≈10%): vásárlás/árak; utazás/közlekedés; főzés; tanulás/iskola; munka/levelezés; otthon/barkács; általános egészség/sport (diagnózis nélkül); technológia/telefon; szabadidő/kultúra; ügyintézés/általános pénzügy (nincs tanács).
* Érzékeny területek (egészség/jog/pénz) ≤ 8%, csak szakemberhez irányítással.

### 4.3 Kitalált személyes adatok

* Minden személyes adat **kitalált és nem azonosítható**: keresztnév (előre rögzített ≈150 nevű névtárból, néha általános vezetéknévvel), életkor, foglalkozás, háziállat neve, kitalált cégnév, a beszélgetésen belül adott számok.
* Tilos: valós közszereplő, valós kisvállalkozás, teljes cím, telefonszám, e-mail, azonosító, bankszámla, 8+ jegyű számsor, URL, MF-AI/Nexora említés, identitás-szivárgás.
* Egy „persona” legfeljebb 3 beszélgetésben szerepelhet, és ezek egy felosztási csoportba tartoznak.
* A modell nem állíthatja, hogy előző beszélgetésre emlékszik; csak a beszélgetésen belüli adatot használja.
* A külvilági tényállítás vagy stabil köztudás, vagy a 6. csomag módszerével (bizonytalanság jelzése, forrás) kezelt; friss adatot (dátum, ár, nyitvatartás) a modell nem talál ki.

## 5. Felosztás (train / validation / test)

* **Felosztás: 800 / 100 / 100 beszélgetés (ELFOGADVA).** **Felosztási egység a csoport** (az MT-3 **számított** csoportja, amely a deklarált `meta.split_group` és a `persona` kapcsolatot is tartalmazza), nem a rekord és nem a minta. Egy beszélgetés **összes** váltása/mintája, valamint közeli változatai mindig ugyanabba a részbe kerülnek.
* **Közeli változat:** (a) tervezett változat: ugyanaz a forgatókönyv-mag más névvel/számokkal/megfogalmazással (megengedett arány ≤15%, 2–3 elemű csoportok); (b) ugyanaz a persona; (c) automatikusan talált: a teljes átirat vagy a felhasználói üzenetek sorozatának hasonlósága ≥ 0,8 → egy csoportba (union-find); ≥ 0,9 → duplikátum, elutasítva (a korpusz szabályával egyezően).
* Arány: **800 / 100 / 100 beszélgetés** (kb. 3750 / 470 / 470 minta), csoportszinten, család és hosszsáv szerint rétegezve; determinisztikus (rögzített seed + csoportazonosító). A csoportméret miatt ±2% eltérés megengedett.
* A teszthalmazba legalább 30 „nehéz” beszélgetés kerül (mélység ≥2 utalás, javítás, visszatérés).
* Kereszt-csomag szivárgás: a beszélgetések fordulói nem lehetnek ≥ 0,9-es hasonlóságúak az 1–6. csomag 4500 sorával.
* Nyitott: az 1–6. csomagnak jelenleg nincs rögzített train/val/test felosztása (a `dataset_split.py` csak kategóriánként véletlenszerűen oszt, és nem használt); globális felosztási stratégia külön döntést kér.

## 6. Ellenőrzések (kapuk a batchekre)

| Terület | Ellenőrzés | Küszöb |
|---|---|---|
| Szerkezet | séma (9 mező + `turns`), szerepek váltakozása user→assistant, utolsó = assistant, 3–8 váltás, nincs üres fordulat, hosszkorlátok, származtatott mezők egyezése, egyedi id | 100% |
| Biztonság / PII | a meglévő `validate_row` logika **minden fordulóra** (lapított sorokon), + névtár-ellenőrzés (csak a rögzített kitalált nevek), MF-AI/Nexora, URL/e-mail/telefon | 0 találat |
| Tartalom | minden beszélgetés teljes elolvasása (kérdés, válasz, előzmény együtt) az első 100-nál; ezután batchenként ≥ 20% + minden jelzett | az én átolvasásom, **nem független** |
| Előzmény-függés | a `meta.depends` minden bejegyzésénél a cél-válasz tényleg az előzményre épül (ablációs olvasás: az előzmény nélküli válasz nem lenne helyes); a mélység-mező igaz | 100% az első 100-nál, ≥ 20% utána |
| Viselkedés | javítás-sorok: a modell nem hízeleg, téves felhasználói javításnál kitart; nincs kitalált külső tény; nincs „emlékszem korábbról” | 0 hiba |
| Duplikáció | batchen belüli és teljes korpuszos (beszélgetés-szintű átirat + fordulónkénti üzenet) a gyorsított, bizonyítottan pontos módszerrel; a 4500 sor ellen | 0 találat ≥ 0,9 |
| Felosztás | csoport-integritás (0 csoport lép át részt), determinizmus (kétszeri futás azonos), arányok, persona nem lép át, részek közti max hasonlóság jelentése | 0 megsértés |
| Eloszlás | család-kvóta (±2 db az első 100-ban), hosszeloszlás, téma ≤ 12% (első 100), asszisztens nyitó szó ≤ 8%, 4-gram ismétlés riport, `dataset_topic_report` (a csomagjelölő címkék dokumentált kivétele) | lásd 7. |
| Regresszió | `python -m unittest tests.test_v1_7_4_dataset_foundation` és az új eszközök tesztjei | STABIL |
| Kizárás | a kimeneti manifeszt tartalmazza a 6 kizárt id hiányát (TE-1) | kötelező |

Az automatikus pontszám itt sem bizonyítja a tartalmi helyességet.

## 7. Az első 100 beszélgetés tervezett összetétele

Két 50-es alegységben (`claude_multiturn_0001_0050`, `_0051_0100`; a korábbi szabály szerint 25–50 példa/batch), a 100 után **kötelező felhasználói jóváhagyás**.

| Szempont | Terv az első 100-ban |
|---|---|
| Család | F1 15, F2 13, F3 13, F4 13 (ebből 3 téves felhasználói javítás), F5 11, F6 9, F7 10, F8 11, F9 5 |
| Hossz (váltás) | 3: 20, 4: 30, 5: 25, 6: 15, 7: 6, 8: 4 → 469 váltás, 938 üzenet, 469 minta (100 első fordulós + 369 előzmény-függő) |
| Téma | 10 tématerület × ≈10 (egy sem > 12) |
| Nehézség | easy 30, medium 50, hard 20 |
| Tervezett változat-csoport | 3 pár (6 beszélgetés) — a csoportos felosztás tesztelésére; a többi egyedi |
| Register | ≈85 tegező, ≈15 magázó; ≈10 beszélgetésben könnyű elírás a felhasználónál |
| Érzékeny terület | legfeljebb 8 |
| Mélység ≥2 utalás | legalább 25 beszélgetésben (F7, F1, F8), R3-hoz „arany összefoglaló” csak jóváhagyás után |
| Elfogadási kapu | a 6. szakasz minden sora teljesül; a jelentés külön mutatja: kész beszélgetés, üzenet, minta, ellenőrzött és nyitott tételek; nincs „training-ready” minősítés |

## 8. Kódfeladatok

**Alapelv az új formátum ellenőrzéséről.** A régi `dataset_validate.py` sikere **nem** minősíti ellenőrzöttnek a `turns` formátumot: nincs kategória-fehérlista, extra mezőt nem utasít el, és csak a 9 régi mezőt látja, vagyis egy közbenső fordulóban lévő PII/veszélyes/torz szöveg észrevétlen maradna. (Ezt az MT-1 tesztjei bizonyítják: közbenső üzenetben lévő hibánál a régi validátor a rekordot és a fájlt átengedi, az MT-1 elutasítja.) Az állapotok külön szótárral szerepelnek a jelentésekben:

| Állapot | Mit jelent | Ki adja |
|---|---|---|
| `régi-validátor-kompatibilis` | a 9 régi mezőre a régi validátor átengedi | `dataset_validate.py` (csak szerkezeti kompatibilitás) |
| `turns-validált` | minden üzenetre lefutott az új validátor (MT-1) hibátlanul | `multiturn_validate.py` |
| `duplikáció-ellenőrzött` | beszélgetés- és fordulószintű, korpuszos ellenőrzés (MT-3) | `multiturn_dedupe.py` |
| `tartalmilag átolvasott` | a teljes beszélgetés elolvasva (nem független) | jelentésben, kézi |
| `exportálható` | a kizárási lista érvényesült, az export visszakövethető | TE-1 / TE-2 / MT-4 manifest |
| `technikailag kompatibilis` | a régi betöltő a kiírt fájlt blokkhatár-hiba és tanítás nélkül feldolgozza | TE-2 (egyfordulós, a régi betöltővel); MT-5 (többfordulós, saját, elkülönített betöltővel — az MT-5 önálló loader, nem a régi `train_chat.py`-t bővíti) |
| `training-ready` | **csak** kifejezett felhasználói döntéssel; a manifestek ezt sosem állítják | felhasználó |

### Elkészült
| # | Feladat | Fájlok | Elfogadási feltétel és bizonyíték | Állapot |
|---|---|---|---|---|
| **TE-1** | kizárás-érvényesítő, visszakövethető export (egyfordulós clean sorok) | `tools/dataset_export_train.py`, `tests/test_te1_dataset_export.py` | mind a 6 kizárt sor kimarad, az engedélyezettek megmaradnak; a clean sorok nem törlődnek/módosulnak; hibás lista/azonosító egyértelmű hibával megáll; manifest nem állít tartalmi ellenőrzést | **KÉSZ** (35 teszt) |
| **TE-2** | TE-1 exportból előkészítő `User:/AI:` szöveg, veszteségmentesség-őrzéssel, régi betöltős kompatibilitás-ellenőrzéssel | `tools/dataset_export_chat_text.py`, `tests/test_te2_chat_text.py`, `data/reports/te2_mt01_report.md` | csak sikeres TE-1 exportot fogad (manifest + ellenőrzőösszegek); az input az instruction után új sorban; nincs csendes átírás (nem átadható sor visszatartva, okkal); hat kizárt sor és blokkjuk hiányzik; visszaolvasás/visszaparse-olás bájt-pontos; a valódi `train_chat` függvényekkel tanítás nélkül feldolgozva; nincs felosztás; blokk-index visszakövethető | **KÉSZ** (36 teszt; valós adaton 4494 blokk, 0 visszatartott) |
| **MT-0** | formátum-specifikáció, névtár, tesztfixture | `docs/MULTITURN_FORMAT.md`, `tools/multiturn_name_bank.json`, `tests/fixtures/multiturn/valid_conversations.jsonl` | minden mező és szabály leírva; ≥150 jóváhagyott keresztnév + tiltólisták, átfedés nélkül; a fixture-ök `mtfx_` azonosítójúak, `meta.fixture: true`, dataset módban elutasítottak, `data/` alatt nincs multiturn fájl | **KÉSZ** |
| **MT-1** | beszélgetés-validátor | `tools/multiturn_validate.py`, `tests/test_multiturn_validate.py` | minden üzenet vizsgált; szabályonként elbukó teszt; közbenső üzenetben lévő hiba/PII → a régi validátor átengedi, az MT-1 elutasítja; a régi-validátor-kompatibilis és a turns-validált állapot külön; a beszélgetés-, üzenet- és mintaszám külön | **KÉSZ** (29 teszt) |
| **MT-3** | beszélgetés-szintű duplikáció-ellenőrzés és közeli-változat csoportosítás (mt3-2.0) | `tools/multiturn_dedupe.py`, `tests/test_multiturn_dedupe.py`, `docs/MULTITURN_DEDUPE.md`, `data/reports/mt3_report.md`, `data/reports/mt2_report.md` | azonosító-, beszélgetés- (pontos, normalizált, közeli, szerep- és pozíció-őrző), minta- (előzménnyel) és TE-1 export elleni ellenőrzés; **szigorú `>` határ alapból** (0,90 fölött review, 0,95 fölött reject; `--inclusive-boundaries`: `>=`); a pontos ismétlődő minta rövidségtől függetlenül reject; a rövid szöveg hasonlósági kivétele és a paraphrase-heurisztika **kísérleti** review-jelzés; a névsemlegesített egyezés **kiegészítő** review-jelzés (az eredeti szöveg megőrzésével); a közös `split_group` nem írja felül a döntést; kivétel reject-szinten dokumentált `capability` nélkül nem adható; a jelentés az eszköz fájljának és a forrássorok ellenőrzőösszegét rögzíti | **KÉSZ** (75 teszt, 82/82 mutáns elbukik; a döntéseket a felhasználó jóváhagyta; nem training-ready) |
| **MT-2** | csoport-tudatos, reprodukálható felosztás (train/validation/test) | `tools/multiturn_split.py`, `tests/test_multiturn_split.py`, `tests/fixtures/multiturn/synthetic_vocabulary.txt`, `docs/MULTITURN_SPLIT.md`, `data/reports/mt2_report.md`, `data/reports/audit_evidence/mt2_split/` | az MT-3 **számított** csoportjaira és aktuális jelentésére épül (verzió, eszköz-ellenőrzőösszeg, bemenetek, rekord-sorellenőrzőösszegek egyeznek; elavult jelentés hibával megáll); egy csoport egy részbe kerül (független ellenőrzéssel, ellenséges esetekkel: közös persona, deklarált csoport, láncolt kapcsolat, kivétellel felmentett pár); fel nem oldott MT-3 reject/review, blokkolt tagot tartalmazó csoport és kizárt rekord nem kerül kijelölésre; a cél-darabszám pontos optimalizálása (DP + pontos töltelék), nem elérhető cél esetén az eltérés jelentve, csoportot nem vág szét; sha256-alapú, sorrendtől független determinizmus; a TE-1 exporttal talált kapcsolatok (`export_links.json`, a TE-3-hoz) és a részek közötti átfedések listázva; manifest a bemenetek, beállítások, csoport-tagság és kijelölés ellenőrzőösszegével; `--verify-manifest` újraszámolással | **KÉSZ** (70 teszt, 83/83 mutáns elbukik; a kijelölés nem jóváhagyott, nem training-ready) |
| **MT-4** | a felosztott beszélgetések renderelése (R1/R2) és exportálása kizárási szűrővel | `tools/multiturn_export.py`, `tests/test_multiturn_export.py`, `docs/MULTITURN_EXPORT.md`, `data/reports/mt4_report.md`, `data/reports/audit_evidence/mt4_export/` | az MT-2 manifestet és bemeneteit ellenőrzi (`verify_manifest`, belső egység, státuszok), elavult/hiányos/megváltozott bemenetnél hibával megáll; a kanonikus beszélgetések bájt-pontos másolata részenként, forrássorrendben; R1 = a `src/memory.build_prompt_context` importált függvényének kimenete + teljes aktuális kérés és cél (a csonkolás és a nem ábrázolható előzmény-függés mintánként jelölve), R2 = teljes előzmény (veszteségmentes), R3 nem készül (arany összefoglaló és döntés kell); visszakövethetőség fájl/sor/forduló szintig; a kizárt, visszatartott, blokkolt rekordok és a hat TE-1 kizárás (azonosító és szöveg) függetlenül ellenőrzött; a lemezről visszaolvasás igazolja a tartalmat, a szerepeket és a beszélgetéshatárokat; tesztadat `fixture_` előtaggal, jelölővel és `training_data: false`-szal; a `split_approved`/`content_verified`/`training_ready` státuszokat nem változtatja | **KÉSZ** (70 teszt, 114/114 mutáns elbukik; az export nem jóváhagyott, nem training-ready) |
| **MT-5** | többfordulós tanító BETÖLTŐ (**csak betöltés és száraz futás**, tanítás nem) | `src/train_multiturn.py`, `tests/test_train_multiturn.py`, `docs/MULTITURN_TRAIN.md`, `data/reports/mt5_report.md`, `data/reports/audit_evidence/mt5_train/` | bemenete kizárólag az MT-4 export (`export_manifest.json` + mintafájlok; elavult/hiányos/megváltozott bemenetnél hibával megáll); R2 (teljes előzmény) az elsődleges, R1 (futásidő-hű, csonkolás-jelöléssel) külön összehasonlító próba, R3 nem készül; nincs véletlen ablakolás, egy köteg-sor egy minta-határ, beszélgetések nem folynak össze, rejtett állapot nem öröklődik; a célmaszk a `target` karaktertartományból, két független módon ellenőrizve; a szótár kizárólag a train/R2 részből épül, a validation/test ismeretlen karakterei dokumentáltan (utólagos bővítés nélkül) kezelve; explicit `--max-chars` fölötti minta visszatartva jelentéssel, nem csonkítva; egy FRISS, tanítatlan próba-modellel csak alak-/futás-ellenőrzés (`--dry-run` kötelező, nincs `.backward()`/`.step()`/`torch.save`); a fixture export kizárólag kifejezett tesztmódban fogadható el; a `split_approved`/`content_verified`/`training_ready` státuszokat nem változtatja | **KÉSZ** (83 teszt, 75 mutánsból 74 elbukik + 1 dokumentált, indokolt ekvivalens; **kiemelt korlát**: 1000 mesterséges beszélgetésen a minták 100%-a — R1-ben és R2-ben is — meghaladja a jelenlegi betanított modell 64 karakteres kontextusát, lásd `mt5_report.md`; a betöltés nem jóváhagyott, nem training-ready, tanítás nem indult) |
| **MT-6 első batch** | az első 50 valódi, datasetbe szánt beszélgetés (`claude_multiturn_0001_0050`) | `data/raw\|clean/claude_multiturn_0001_0050_*.jsonl`, `data/reports/mt6_batch1_report.md`, `data/reports/audit_evidence/mt6_batch1/` | a jóváhagyott formátum és a tervezett család/tématerület/nehézség/register/**hossz**-arányok szerint (a 100-as terv arányos, dokumentált felére kerekítve, **a hossz-eloszlás a javított kiadásban pontosan**: 3 váltás 10, 4 váltás 15, 5 váltás 13, 6 váltás 7, 7 váltás 3, 8 váltás 2); tényleges, egymásra épülő fordulók (pontosítás, korábbi feltétel/javítás/többlépés/más készség — nem összefűzött, független kérdés-válasz, nem üres köszönés/ismétlés); tartalmilag változatos nyitások és nyitószavak (asszisztens-válasz nyitószó ≤7,7%); a hat TE-1 kizárás érvényben; saját (nem független) teljes átolvasás; MT-1 (50/50 turns-validált) → MT-3 (0 találat a batch + a valódi 4494 soros TE-1 export ellen) → MT-2 (**próbafelosztás**, 40/5/5, nem a végleges 800/100/100) → MT-4 (dataset módú export) → MT-5 (dataset módú dry-run) lánc hibátlan; `split_approved`/`content_verified`/`training_ready` változatlanul false | **KÉSZ, javított kiadás** (lásd `mt6_batch1_report.md`; az első kiadás — `v1.13.25-mt6-batch1` — hossz-eloszlása jelentősen eltért a tervtől, 39 rekord tartalmi bővítésével javítva; a 7. csomag adatai 50/1000-nél; nem training-ready, tartalmilag nem független átolvasott) |
| **MT-6 második batch** | a második 50 valódi, datasetbe szánt beszélgetés (`claude_multiturn_0051_0100`), az első 100 lezárása | `data/raw\|clean/claude_multiturn_0051_0100_*.jsonl`, `data/reports/mt6_batch2_report.md`, `data/reports/audit_evidence/mt6_batch2/` | a célértékek a terv 7. szakasza és a javított első 50 tényleges összetétele alapján előre lezárva, utána a tartalom ezekre írva; a kombinált 100 a 7. szakasz minden kötött számát pontosan teljesíti (család F1 15/F2 13/F3 13/F4 13 [3 téves javítás]/F5 11/F6 9/F7 10/F8 11/F9 5; hossz 3:20/4:30/5:25/6:15/7:6/8:4; nehézség easy30/medium50/hard20; register tegező 86/magázó 14; 938 üzenet, 469 minta); a terv 3 változat-párjából mind a 3 kész (`0029`/`0032`, `0053`/`0056`, `0071`/`0074`), a pár-deklaráció nem írta felül az MT-3 saját döntését; az első 50 változatlan maradt; saját (nem független) teljes átolvasás; MT-1 (batch2 önmagában és a kombinált 100-on is, 0 hibás) → MT-3 (harmadik futás, 0 találat — nem csak 0 blokkolás — a kombinált 100 + a valódi 4494 soros TE-1 export ellen) → MT-2 (**próbafelosztás**, 80/10/10, nem a végleges 800/100/100) → MT-4 (dataset módú export) → MT-5 (dataset módú dry-run) lánc hibátlan; `split_approved`/`content_verified`/`training_ready` változatlanul false | **KÉSZ** (lásd `mt6_batch2_report.md`; a 7. csomag adatai 100/1000-nél; nem training-ready, tartalmilag nem független átolvasott — a teljes 100 független átolvasása még nyitott feladat) |

### Következő feladatok (javasolt sorrend és függőség)
| # | Feladat | Fájlok (új) | Elfogadási feltételek | Függ |
|---|---|---|---|---|
| **MT-6, teljes 100 független átolvasása** | a `claude_multiturn_0001_0100` teljes tartalmának **független** (nem AI, lehetőleg emberi) ellenőrzése | — | a plan 6. szakasza szerint az első 100-nál kötelező; a saját átolvasás és a 2026-10-02-i AI-alapú második ellenőrzési kör (`mt6_batch_audit2_report.md`, két friss Claude-alügynök + saját közvetlen ellenőrzés, 51 tartalmi hiba javítva) ezt **nem helyettesíti**; eddig nem történt meg; a harmadik batch (`0101–`) és bármilyen tanítási előkészület ettől függ | MT-6 második batch, AI-audit 2. kör |
| **TE-3** | globális train/validation/test felosztás az 1–6. csomagra (egyfordulós adat) | `tools/dataset_split_groups.py` (javasolt), tesztek | külön követelmény: a TE-2 exportot NEM osztja fel automatikusan; determinisztikus, csoport-/közeli-változat-tudatos, manifesztet ír; a felosztás jóváhagyása külön | TE-2 |
| **D-1** | futásidejű előzmény-mélység (jelenleg 1 váltás, `src/memory.py`) | (webapp/backend) | **külön jóváhagyás nélkül nem érintjük**; addig a mélység ≥2 minták R3-mal vagy csak értékelésre használhatók | – |

Kockázat (**az MT-5 méréssel megerősítve, nem csak feltételezve**): 1000 mesterséges beszélgetésen a `train_multiturn.py` száraz futása azt mutatta, hogy a minták 100%-a — R1-ben (futásidő-hű, csonkolt) ÉS R2-ben (teljes előzmény) is — meghaladja a jelenlegi betanított modell (karakter-LSTM, hidden 128, 2 réteg, `seq_length=64`) tanított kontextusát; a legrövidebb R1-minta is legalább 160 karakter. Ez nem a betöltő hibája (a betöltés/kódolás/kötegelés/előrefutás technikailag sikeres), hanem a modell architektúrájának/tanításának KORLÁTA: a sikeres betöltés NEM bizonyítja, hogy a valódi checkpoint ezen a hosszon jó minőségű választ adna. Ezért a tényleges tanítás megkezdése előtt a modell kontextushosszának (vagy egyenértékű architektúra-változtatásnak) a kérdését külön kell kezelni; ezután is csak kis, korlátozott előpróba javasolt, **kifejezett jóváhagyással**.

## 9. Döntések

**Elfogadva (a felhasználó jóváhagyása):** a teljes 17 000 soros terv csomagonkénti célja; egy példa = egy teljes beszélgetés; a `turns` tömb őrzi az üzenetek sorrendjét és szerepeit; 800/100/100 beszélgetés összetartozó változatok közös részbe sorolásával; a beszélgetések, üzenetek és tanítási minták külön számolása; a TE-1 elkészítése elkülönített eszközként.

**Jóváhagyva és elkészült:** TE-2 (az `input` az instruction után új sorban), MT-0, MT-1.

**Még nyitott:**
1. Az MT-4 és az MT-5 is elkészült (a felhasználó jóváhagyta és megkapta a jelentést mindkettőhöz). (Az MT-3 kézikönyvi megfeleltetéseit a felhasználó az MT-3 jelentés áttekintése után döntötte el; a revideált eszköz `mt3-2.0`, lásd `mt2_report.md` A. rész. A felosztás kijelölése technikai, jóváhagyása külön.) Nyitva marad: a tényleges tanítás bemenetének kiválasztása (R1/R2, ablak-/szekvenciahossz-kezelés, a modell kontextushosszának kérdése) és a tanítás megindításának kifejezett engedélye — ez MAGA a tanítás, külön feladat és jóváhagyás.
2. Az R3 „arany összefoglaló” használata és a futásidejű előzmény-mélység (D-1).
3. Az 1–6. csomag globális train/validation/test felosztása (TE-3) — a TE-2 export nem oszt fel semmit.
4. A 6. csomag nyitott tartalmi tételei (jogi/forrás felülvizsgálat, E-sorok, független átolvasás) — a tartalmi lezárás nélkül a `training-ready` nem adható.
5. A 4. és 5. csomag kibővített céljának tartalmi lefedettségi auditja (átfogalmazás / hibás szöveg értése).
6. Az első 100 beszélgetés lezárása: az első 50 (`0001–0050`) elkészült és technikailag ellenőrzött (lásd `mt6_batch1_report.md`); a második 50 kifejezett jóváhagyást kell, majd a 100 elkészülte után kötelező, külön (lehetőleg független) átolvasás.
7. A tanítás megindításának engedélye: külön, kifejezett döntés.

