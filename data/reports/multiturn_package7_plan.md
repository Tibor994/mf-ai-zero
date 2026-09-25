# 7. csomag — 1000 többfordulós beszélgetés (`multiturn`) — előkészítő terv

Dátum: 2026-09-25. **Ez csak terv.** Új adat, kódmódosítás és tanítás nem indult; a webapp/backend, a `tools/`, a validátorok és a tanító kód változatlanok.

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
| N-8 | **A kizárás technikai kikényszerítése** | lásd 2. szakasz | **kötelező tanítás előtti feladat (TE-1)** |

## 1. Terv–tény táblázat (tíz csomag)

Forrás: a tényleges fájlok (`data/raw|clean|rejected/*.jsonl`) soronkénti megszámolása (kategória a fájlnév szerint, a `category` mező a clean/raw fájlokban egyezik). **Fontos:** a 17 000 soros terv csomagonkénti céltáblája a repóban és a beszélgetésben **nem található meg** (csak a régi 9 csomagos, 4900 soros roadmap a haladási fájlban, illetve az egyes riportok „17 000 soros instruction core” említése). Az 1–7. sor célja a haladási fájlból/kérésekből származik; a **8–10. csomag célja ismeretlen**, azt nem találtam ki.

| # | Csomag | Terv | Raw (érvényes JSON sor) | **Clean (tény)** | Rejected | Eltérés | Státusz |
|---|---|---|---|---|---|---|---|
| 1 | simple_qa | 1000 | 1007 (ebből 2 nem parse-olható sor a `deepseek_simple_qa_0151_0200` és `_0201_0250` raw fájlban, változatlanul) | **1000** | 9 | 0 | kész, auditált |
| 2 | explanation | 1000 | 1003 | **1000** | 3 | 0 | kész, auditált |
| 3 | step_by_step | 500 | 500 | **500** | 402 (a `chatgpt` inbox importok, séma-hibás sorok) | 0 | kész, auditált |
| 4 | summary | 500 | 500 | **500** | 0 | 0 | kész, auditált |
| 5 | noisy_input | 500 | 500 | **500** | 0 | 0 | kész, auditált |
| 6 | uncertainty_source_request | 1000 | 1000 | **1000** (ebből 6 kizárt) | 0 | 0 | **korlátozott lezárás** |
| 7 | multiturn | 1000 | 0 | **0** | 0 | −1000 | ez a terv |
| 8 | ? | ? (a terv nem elérhető) | 0 | 0 | 0 | ? | nem kezdődött |
| 9 | ? | ? | 0 | 0 | 0 | ? | nem kezdődött |
| 10 | ? | ? | 0 | 0 | 0 | ? | nem kezdődött |
| | **Összesen** | 5500 az 1–7. csomagra; 17 000 a teljes terv → a 8–10. csomagra összesen **11 500** jutna (ez pusztán kivonás, nem terv) | 4510 sor (2 hibás) | **4500** | 414 | | |

Megjegyzés: a régi (9 csomagos) roadmapban a többfordulós csomag 6. sorszámú és 300 db volt (`multiturn_*` kategória, séma-bővítést igényel); az új terv szerint 7. csomag, 1000 beszélgetés.

## 2. A hat kizárt sor kihagyása: tényleg biztosított?

**NEM. Jelenleg csak dokumentálva van.**

Bizonyíték (fájlokból ellenőrizve):
* A hat sor (`uncertainty_source_request_0220 0602 0829 0849 0864 0898`) benne van a `data/clean/*.jsonl` fájlokban, `quality_notes`-uk jelzi a státuszt.
* A `training_exclusion_pending_review.txt` listát **semmilyen kód nem olvassa** (`.py`/`.json` fájlokban nincs rá hivatkozás, csak riportokban).
* **Nincs olyan kód, amely a `data/clean` JSONL-t tanítóadattá alakítja.** A tanító szkript (`src/train_chat.py`) kizárólag a kézzel írt `data/chat_train*.txt` fájlokat olvassa (`User: …\nAI: …` blokkok); a `data/train/` mappa üres. A `tools/dataset_split.py` nem szűr, és csak tesztből hívódik.
* Ezért ma sem a kizárás, sem a JSONL→tanítóadat út nem létezik; ha valaki a `data/clean` tartalmát kézzel tanítóadattá alakítaná, a hat sor bekerülne.

**TE-1 (KÖTELEZŐ tanítás előtti feladat):** a kizárást technikailag ki kell kényszeríteni. Javasolt: új exportáló eszköz, amely (a) beolvassa a kizárási listát, (b) kihagyja a listázott azonosítókat, (c) megáll hibával, ha a lista nem olvasható vagy egy kizárt azonosító mégis a kimenetben lenne, (d) manifesztet ír (sorszámok, sha256, kizárt azonosítók), (e) egységteszttel bizonyítja a hat sor hiányát. A kódigényt a 8. szakasz részletezi. Amíg TE-1 nincs kész és tesztelve, **tanítás nem indítható** ezekkel az adatokkal.

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

### 3.2 Javasolt formátum: egy rekord = egy beszélgetés

**Kanonikus tárolás:** soronként egy beszélgetés, a 9 meglévő mező megtartásával + új mezők:

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

### 3.3 Mi számít egy „példának” az 1000-es célban?

**Egy példa = egy teljes beszélgetés** (egy `multiturn_NNNN` rekord). A cél tehát **1000 beszélgetés**. Külön jelentendő mennyiségek (a terv szerint):

| Mennyiség | Terv | Levezetés |
|---|---|---|
| **Beszélgetés** | **1000** | a cél |
| Váltások (user+assistant pár) | **4690** | 3 váltás: 200 beszélgetés, 4: 300, 5: 250, 6: 150, 7: 60, 8: 40 → 600+1200+1250+900+420+320 |
| **Üzenetek** | **9380** | 4690 user + 4690 assistant |
| **Tanítási minták** (egy minta = egy assistant-fordulóra adott cél, előzménnyel) | **4690** | ebből 1000 az első fordulóé (előzmény nélkül, a meglévő egyfordulós adathoz hasonló), **3690 előzmény-függő** |
| Előzmény-függő minták mélysége | kb. 70% mélység-1 (≈2600, R1-gyel tanítható), kb. 30% mélység ≥2 (≈1090, R3 vagy R2 kell) | tervezett arány; a `meta.depends` annotációval mérendő |
| Becsült szöveghossz | kb. 1,2–1,5 millió karakter (kanonikus) | 4690 váltás × (≈70 + ≈220 karakter) |

Az „1000 példa” mindig a beszélgetésekre vonatkozik; a mintaszám nem számít bele a célba, és a jelentésekben mindig külön szerepel.

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

* **Felosztási egység a csoport** (`meta.split_group`), nem a rekord és nem a minta. Egy beszélgetés **összes** váltása/mintája, valamint közeli változatai mindig ugyanabba a részbe kerülnek.
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

## 8. Kódigény (NEM végrehajtva; jóváhagyást igényel)

| # | Igény | Fájl (javasolt) | Miért |
|---|---|---|---|
| **TE-1** | JSONL → tanítóadat exportáló **kizárási szűrővel**, manifesztel, teszttel | új: `tools/dataset_export_train.py` (+ teszt) | ma nincs export, és a kizárás nincs kikényszerítve (2. szakasz); az 1–6. csomagra is kell |
| K2 | beszélgetés-validátor (minden fordulóra PII/veszély/torzítás/angol keveredés, szerepek, hossz, `depends`, névtár) — a `dataset_validate.validate_row` **importálásával**, annak módosítása nélkül | új: `tools/multiturn_validate.py` | a régi validátor a `turns`-t nem látja |
| K3 | csoport-tudatos felosztó, rétegzett, determinisztikus, manifesztet ír | új: `tools/multiturn_split.py` | a `dataset_split.py` sorszintű és kategóriánként véletlen |
| K4 | beszélgetés-szintű duplikáció/szivárgás (a gyorsított, pontos szűrőmódszerrel), változat-csoportosítás (union-find) | új: `tools/multiturn_dedupe.py` | a régi eszközök csak az `instruction||input` és `output` mezőt hasonlítják |
| K5 | import-útvonal az új kategóriához (`data/raw|clean|rejected/claude_multiturn_*`) és riport | új: `tools/multiturn_import.py` vagy a `dataset_import.py` bővítése (**döntés kell**) | a mostani import a 9 mezős sorokra épül |
| K6 | **tanító betöltő**: teljes minták (R1/R3/R2) egyenkénti kódolása, veszteség-maszk az assistant-tokenekre, előre felosztott `--train-path/--val-path` (csoport-tudatos), a `seq_length` (jelenleg 64) és a mintahossz összehangolása | új: `src/train_multiturn.py` (a v0.7 `train_chat.py` érintetlen marad) | jelenleg a modell 64 karakternél régebbi előzményt nem tanul, a blokk-felosztás szétvágná a beszélgetést |
| K7 | tesztek: export (6 kizárt sor hiánya), validátor, csoport-integritás, determinizmus, R1 formátum a `memory.py` konstansaival (importálva, nem másolva) | `tests/…` | regresszió |
| — | **Nem kell** kód az adatgenerálás előtt: a kanonikus JSONL kézzel/szkripttel a scratchpadben építhető, majd K2–K4 futtatható | | |
| — | Futásidejű mélyebb előzmény (jelenleg 1 váltás): **webapp/backend módosítás**, csak külön jóváhagyással; nélküle a mélység ≥2 minták R3-mal vagy csak értékelésre használhatók | `src/memory.py`, `web/app.py` | döntés kell |

Kockázat: a karakter-LSTM (hidden 128, 2 réteg) hosszú, többfordulós kontextus használatára való képessége nem bizonyított; javasolt egy kis, korlátozott előpróba a K6 kész után — **most nem indul tanítás**.

## 9. Jóváhagyásra váró döntések

1. A 17 000 soros terv csomagonkénti céljai (különösen 8–10.) — a táblázat kitöltéséhez.
2. „1 példa = 1 beszélgetés”, a mintaszám külön jelentéssel (3.3).
3. Kanonikus formátum (`turns` tömb, új `multiturn` kategória) vs. a soronkénti tartalék.
4. K1–K7 közül a jóváhagyott kör; TE-1 mindenképpen a tanítás előtt.
5. Futásidejű előzmény-mélység (1 váltás) és az R3 „arany összefoglaló” használata.
6. 800/100/100 arány és a globális (1–6. csomagot is érintő) felosztási stratégia.
7. Az első 100 beszélgetés elindítása (`claude_multiturn_0001_0050`).
