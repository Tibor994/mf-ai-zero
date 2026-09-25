# 7. csomag — 1000 többfordulós beszélgetés (`multiturn`) — előkészítő terv

Dátum: 2026-09-25. 2. változat (a felhasználó jóváhagyásai és a teljes 17 000 soros terv beépítve).

**Állapot:** a TE-1 exportáló elkészült és tesztelt (`tools/dataset_export_train.py`, `tests/test_te1_dataset_export.py`); a meglévő validátorok, tanító és chat kód, valamint a webapp/backend változatlanok. Új adatgenerálás és tanítás nem indult; a 7. csomag adatai még nem léteznek.

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
| N-8 | A kizárás technikai kikényszerítése | lásd 2. szakasz | **TE-1 kész** (exportálón át kikényszerítve); a tanító oldali bekötés még nincs (TE-2, MT-5) |

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
| 7 | Többfordulós beszélgetés (`multiturn`) | 1000 | 0 | 0% | 1000 | 0 | 0 | **ez a terv; nem kezdődött** |
| 8 | Személyiség/stílus adaptáció | 1000 | 0 | 0% | 1000 | 0 | 0 | nem kezdődött |
| 9 | Safety/határok | 1000 | 0 | 0% | 1000 | 0 | 0 | nem kezdődött (a 6. csomag „nem kamuzik” sorai nem safety-csomag) |
| 10 | Nextora saját tudás | 1000 | 0 | 0% | 1000 | 0 | 0 | nem kezdődött (csak repo/dokumentum alapján, kitalálás tilos) |
| | **Összesen** | **17 000** | **4500** | **26,5%** | **12 500** | 4510 (2 hibás) | 414 | |

Ellenőrzés: 3000+3000+2000+2000+2000+1000×5 = 17 000; hiányzó: 2000+2000+1500+1500+1500+1000×4 = 12 500. A tényleges fájlokból a clean összeg 1000+1000+500+500+500+1000 = 4500.

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
* **TE-2** — a TE-1 exportból a jelenlegi betöltő (`User:/AI:` blokkok) formátumú szöveg készítése az egyfordulós sorokra (lásd 8. szakasz); a jelenlegi `train_chat.py` továbbra sem olvassa a JSONL-t, ezért **csak a TE-1/TE-2 exporton át** szabad adatot tanítóadatnak használni.
* A tanítás indítása külön, kifejezett jóváhagyás.

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

* **Felosztás: 800 / 100 / 100 beszélgetés (ELFOGADVA).** **Felosztási egység a csoport** (`meta.split_group`), nem a rekord és nem a minta. Egy beszélgetés **összes** váltása/mintája, valamint közeli változatai mindig ugyanabba a részbe kerülnek.
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

## 8. Kódfeladatok (NEM végrehajtva, kivéve TE-1; minden további külön jóváhagyást kér)

**Alapelv az új formátum ellenőrzéséről.** A régi `dataset_validate.py` sikere **nem** minősíti ellenőrzöttnek a `turns` formátumot: nincs kategória-fehérlista, extra mezőt nem utasít el, és csak a 9 régi mezőt látja, vagyis egy közbenső fordulóban lévő PII/veszélyes/torz szöveg észrevétlen maradna. Az állapotok külön szótárral szerepelnek a jelentésekben:

| Állapot | Mit jelent | Ki adja |
|---|---|---|
| `régi-validátor-kompatibilis` | a 9 régi mezőre a régi validátor átengedi | `dataset_validate.py` (csak szerkezeti kompatibilitás) |
| `turns-validált` | minden fordulóra lefutott az új validátor (MT-1) hibátlanul | `multiturn_validate.py` |
| `duplikáció-ellenőrzött` | beszélgetés- és fordulószintű, korpuszos ellenőrzés (MT-3) | `multiturn_dedupe.py` |
| `tartalmilag átolvasott` | a teljes beszélgetés elolvasva (nem független) | jelentésben, kézi |
| `exportálható` | a kizárási lista érvényesült, az export visszakövethető | TE-1/MT-4 manifest |
| `training-ready` | **csak** kifejezett felhasználói döntéssel, minden fenti teljesülése után; a manifest ezt sosem állítja | felhasználó |

### Elkészült
| # | Feladat | Fájlok | Elfogadási feltétel | Állapot |
|---|---|---|---|---|
| **TE-1** | kizárás-érvényesítő, visszakövethető export (egyfordulós clean sorok) | `tools/dataset_export_train.py`, `tests/test_te1_dataset_export.py` | mind a 6 kizárt sor kimarad, az engedélyezettek megmaradnak és bájt-hűek; kizárt sor nincs törölve/módosítva a clean fájlokban; hiányzó/üres/hibás/duplikált/nem egyértelmű/elgépelt/hiányos lista egyértelmű hibával megáll; kimenet visszaolvasásos ellenőrzése; manifest nem állít tartalmi ellenőrzést | **KÉSZ** (35 teszt; 11 szándékos hibamutánsból 9-et a tesztek elbuktatnak, 2 (a kimeneti szivárgás-ellenőrzés és a szabálytalan-azonosító-minta) más védelmi rétegekkel is fedett, redundáns) |

### Következő feladatok (javasolt sorrend és függőség)
| # | Feladat | Fájlok (új) | Elfogadási feltételek | Függ |
|---|---|---|---|---|
| **TE-2** | egyfordulós export → tanítószöveg (`User:/AI:` blokkok) a TE-1 manifest alapján | `tools/dataset_export_chat_text.py`, `tests/test_te2_chat_text.py` | csak TE-1 exportot fogad (a `manifest.json` `status: ok` és a fájl-sha256 egyezik, különben hiba); a blokkokban nincs üres sor; az `input` megjelenítési szabálya dokumentált és tesztelt; az index (blokk → azonosító) megvan, kizárt azonosító nincs; a jelenlegi `train_chat.split_train_val` blokkszáma egyezik a várttal | TE-1 |
| **MT-0** | formátum-specifikáció, névtár (≈150 kitalált keresztnév), tiltólista, minta-beszélgetések **csak tesztfixture-nek** | `docs/MULTITURN_FORMAT.md`, `tests/fixtures/multiturn/*.jsonl` | minden mező és szabály leírva (szerepek, 3–8 váltás, hosszkorlátok, `meta`, `depends`); minden érvényes és minden hibás fixture pontosan egy szabályt szemléltet; a fixture NEM kerül `data/` alá és nem számít adatnak | – |
| **MT-1** | beszélgetés-validátor | `tools/multiturn_validate.py`, `tests/test_multiturn_validate.py` | szabályonként legalább egy elbukó teszt (szerepváltás, első=user, utolsó=assistant, 3–8 váltás, üres fordulat, hosszkorlát, származtatott mezők egyezése, `depends` érvényessége és mélysége, névtár-ellenőrzés, MF-AI/Nexora, URL/e-mail/telefon, 8+ jegyű szám); a `dataset_validate.validate_row` **importálva** fordulónként, módosítás nélkül; **bizonyítja a hiányt**: olyan fixture, amely PII-t tartalmaz egy közbenső fordulóban, a régi validátoron átmegy, az MT-1-en elbukik; a kimenet külön jelzi a `régi-validátor-kompatibilis` és a `turns-validált` állapotot | MT-0 |
| **MT-3** | beszélgetés-szintű duplikáció és csoportképzés | `tools/multiturn_dedupe.py`, `tests/test_multiturn_dedupe.py` | teljes átirat, felhasználói üzenetsorozat és fordulónkénti összevetés; a 4494 exportált sor ellen is; `>= 0,9` duplikátum, `>= 0,8` közeli változat → `groups.json` (union-find, persona-kapcsolattal); a gyors elő-szűrés (a `dd_full` módszer másolata) egyezését a nem szűrt `difflib`-bel véletlen részhalmazokon és a pontosan 0,9-es határesetnél teszt igazolja; beültetett duplikátumok 100%-ban megtalálva | MT-0 |
| **MT-2** | csoport-tudatos felosztás | `tools/multiturn_split.py`, `tests/test_multiturn_split.py` | 800/100/100 beszélgetés (±2%), család és hosszsáv szerint rétegezve; 0 csoport lép át részt (ellenséges fixture-rel is: közös persona, közös csoportazonosító, láncszerűen összekapcsolt csoportok); determinizmus (kétszeri futás, más sorrend → azonos kiosztás); csoport nélküli beszélgetésre hibával áll meg; a manifest külön mutatja a beszélgetés-, üzenet- és mintaszámot minden részre | MT-3 |
| **MT-4** | renderelés (R1/R3/R2) és exportálás kizárási szűrővel | `tools/multiturn_export.py`, `tests/test_multiturn_export.py` | csak `turns-validált`, `duplikáció-ellenőrzött`, felosztott bemenetet fogad; az R1 előtag bájt-pontosan egyezik a `src/memory.build_prompt_context` kimenetével ugyanarra az előzményre (importálva, nem másolva; a `src/memory.py` nem módosul); a TE-1 kizárási mechanizmus újrahasznosítva; a képzett minták száma a képlettel egyezik (váltások száma; első fordulós és előzmény-függő külön); egy csoport minden mintája ugyanabban a részben; a manifest nem állít training-ready állapotot | MT-1, MT-2, MT-3, TE-1 |
| **MT-5** | többfordulós tanító betöltő (**csak betöltés és száraz futás**, tanítás nem) | `src/train_multiturn.py`, `tests/test_train_multiturn.py` | a v0.7 `train_chat.py` és a chat kód érintetlen; mintánkénti kódolás, veszteség-maszk az assistant-tokenekre (a maszk-pozíciókat teszt igazolja), egyetlen ablak sem lép át minta-határt; előre felosztott `--train-path/--val-path`; a szótár csak a train részből épül, a val ismeretlen karaktereit jelzi; a bemeneti manifest ellenőrzése (hiány/sha256-eltérés → hiba); `--dry-run` statisztikával (mintaszám, hossz-eloszlás), tényleges tanítás nélkül; tanítás csak külön jóváhagyással | MT-4 |
| **MT-6** | első 100 beszélgetés generálási kapuja | (nem kód) | csak MT-0, MT-1, MT-3 elfogadása után; a 100 elkészülte után kötelező jóváhagyás; a jelentés külön mutatja a beszélgetés-, üzenet- és mintaszámot; nincs „training-ready” | MT-0, MT-1, MT-3 |
| **D-1** | futásidejű előzmény-mélység (jelenleg 1 váltás, `src/memory.py`) | (webapp/backend) | **külön jóváhagyás nélkül nem érintjük**; addig a mélység ≥2 minták R3-mal vagy csak értékelésre használhatók | – |

Kockázat (nem bizonyított): a karakter-LSTM (hidden 128, 2 réteg) képessége hosszú, többfordulós kontextus használatára; ezért az MT-5 után is csak kis, korlátozott előpróba javasolt, **kifejezett jóváhagyással**.

## 9. Döntések

**Elfogadva (a felhasználó jóváhagyása):** a teljes 17 000 soros terv csomagonkénti célja; egy példa = egy teljes beszélgetés; a `turns` tömb őrzi az üzenetek sorrendjét és szerepeit; 800/100/100 beszélgetés összetartozó változatok közös részbe sorolásával; a beszélgetések, üzenetek és tanítási minták külön számolása; a TE-1 elkészítése elkülönített eszközként.

**Még nyitott:**
1. A TE-2 (egyfordulós sorok tanítószöveggé alakítása, az `input` megjelenítése) jóváhagyása — enélkül a 4494 exportált sor nem használható a jelenlegi betöltővel.
2. Az MT-0…MT-5 feladatok jóváhagyása (sorrend fent), külön-külön kérhető.
3. Az R3 „arany összefoglaló” használata és a futásidejű előzmény-mélység (D-1).
4. Globális train/val/test stratégia az 1–6. csomagra.
5. A 4. és 5. csomag kibővített céljának tartalmi lefedettségi auditja (átfogalmazás / hibás szöveg értése).
6. Az első 100 beszélgetés elindítása csak az MT-6 kapu után.

