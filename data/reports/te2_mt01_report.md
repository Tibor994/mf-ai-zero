# TE-2, MT-0 és MT-1 — jelentés

Dátum: 2026-09-26. Kód: `tools/dataset_export_chat_text.py`, `tools/multiturn_validate.py`, `tools/multiturn_name_bank.json`; tesztek: `tests/test_te2_chat_text.py`, `tests/test_multiturn_validate.py`; specifikáció: `docs/MULTITURN_FORMAT.md`; tesztadat: `tests/fixtures/multiturn/valid_conversations.jsonl`; bizonyíték: `audit_evidence/te2_export/manifest_te2_real_run_1.json`.

Új adat nem készült, tanítás nem indult; a `src/` (tanító, chat), a `web/`, a meglévő `tools/` és a validátorok **nem módosultak** (a `git status` szerint csak új fájlok és riportok).

## Három külön állapot

| Kérdés | Állapot |
|---|---|
| **Technikai kompatibilitás** (a régi betöltő feldolgozza-e a kiírt fájlt) | **igazolt** az egyfordulós exportra (TE-2, a tényleges `src/train_chat.py` függvényeivel, tanítás nélkül). A többfordulós adatra még nem (MT-4/MT-5). |
| **Tartalmi ellenőrzés** | **nincs lezárva**: a 6. csomag korlátozott lezárással áll (6 kizárt sor, 10 nem forrásolt E-sor, független átolvasás nincs); a TE-2 és az MT-1 nem tartalmi ellenőrzés. |
| **A tanítás megindításának engedélye** | **nincs**: kifejezett felhasználói döntés kell; a manifestek `training_ready: false`. |

## TE-2 — előkészítő `User:/AI:` szövegexport

**Bemenet:** kizárólag sikeres TE-1 export. Ellenőrzi a manifestet (`status: ok`, TE-1 eszköz és verzió, `training_ready`/`content_verified` false, minden ellenőrzés igaz), hogy nincs `FAILED.txt`/`.partial` fájl, az export- és indexfájl sha256-ja és sorszáma egyezik, az indexsorok azonosítója és sor-sha256-ja egyezik az exporttal, a darabszámok egyensúlyban vannak.

**Kizárás újraellenőrzése (a hat sor nem kerülhet bele):** a kizárt azonosítók és a kizárás-jelölésű sorok nincsenek az exportban; a kizárási lista jelenlegi tartalma egyezik a TE-1 manifestben rögzítettel (különben „elavult export”, hiba); a forrásfájlok sha256-ja és a kizárt sorok forrássora (fájl, sor, sor-sha256, azonosító) egyezik; a kizárt sorok blokkja nincs a kimenetben.

**Blokkformátum:**
```
User: <instruction>
<input>          <- csak ha nem üres, új sorban, többsoros is lehet
AI: <output>
<üres sor>
```
Minden blokkot üres sor zár le (az utolsót is): így a régi betöltő `text.split("\n\n")` felbontása pontosan a blokkokat adja, és a fájl más blokkfájllal való összefűzése sem olvaszt blokkokat. UTF-8, LF.

**Veszteségmentesség — nincs csendes levágás vagy átírás.** A mezők szövege bájtra azonosan kerül a blokkba, és a kiírt szöveget lemezről visszaolvasva blokkra bontva, visszaparse-olva pontosan az eredeti instruction/input/output mezők jönnek ki. Amit a formátum nem tud egyértelműen hordozni, azt a sort **nem írja ki**, hanem a `withheld_rows.tsv` fájlban és a manifestben okkal felsorolja (`--fail-on-withheld` hibával megállít):

| Ok | Miért nem adható át veszteség nélkül |
|---|---|
| `empty_instruction`, `empty_output`, `whitespace_only_input`, `field_not_string:*` | nincs mit/nem szöveg |
| `carriage_return:*`, `control_character:*` | a régi betöltő olvasáskor átalakítaná / vezérlőkarakter |
| `multiline_instruction` | összemosódna az input sorával (a két eset nem különböztethető meg) |
| `blank_line:*` | a régi betöltő az üres sornál blokkot vágna |
| `edge_newline:*` | a blokk szélén álló újsor a blokkhatárral keveredne |
| `role_label_at_line_start:*` | sor elején álló `User:`/`AI:` (behúzva vagy `AI :` alakban is) téves szerephatár lenne |

A sor **közben** szereplő `User:`/`AI:` említés nem okoz határt, ezért átmegy, de `inline_role_label` jelzést kap az indexben és a manifestben (és a régi betöltő `User: ` számlálója eltér a blokkszámtól — ez figyelmeztetés). Az input többsorossága (`multiline_input`) is jelölt.

**Régi betöltővel végzett ellenőrzés (tanítás nélkül):** a `train_chat.load_text`, `split_train_val`, `build_vocab` és `encode` függvényeket a kiírt fájlra hívja: a betöltő blokkfelbontása és a felosztás utáni blokkok megegyeznek a kiírtakkal, minden karakter kódolható. **A betöltő felosztása csak diagnosztika, eldobva; NEM a train/validation/test felosztás.** A manifest `split_assigned: false`, a kimenetben nincs train/val fájl.

**Visszakövethetőség:** `block_index.tsv` (blokk-sorszám, azonosító, kategória, forrásfájl, forrássor, sor-sha256, blokk-sha256, blokkhossz, jelzések), `manifest_te2.json` (a TE-1 manifest sha256-ja, verziója és git commitja, ellenőrzött összegek, kizárások, darabszámok, ellenőrzések, a régi betöltős eredmény, figyelmeztetések).

**Valós adaton** (`manifest_te2_real_run_1.json`): TE-1 4494 sor → **4494 blokk, 0 visszatartott**; 1046 blokkban van input (500 `noisy_input`, 500 `summary`, 46 `uncertainty_source_request`), ebből 50 többsoros; 0 sor közbeni felirat-említés; kategóriánként explanation 1000, noisy_input 500, simple_qa 1000, step_by_step 500, summary 500, uncertainty_source_request 994. Régi betöltő: 1 804 884 karakter, szótár 104 karakter, `User: ` számláló 4494 = blokkszám, blokkok sértetlenek. Egy külön írt újraszámlálás (a tesztben) szerint a szöveg pontosan 4494 üres sort és 4494 `User: `/`\nAI: ` előfordulást tartalmaz, a hat kizárt sor blokkja egyik sincs benne. (A manifest `git_commit` mezője a futáskor érvényes HEAD, ekkor a TE-2 kód még nem volt commitolva.)

**Korlát:** a TE-2 az egyfordulós sorokat alakítja át; az input megjelenítési szabálya (új sorban az instruction után) a modell számára új felület, hatását nem mértük; a régi betöltő továbbra is véletlen 64 karakteres ablakokat vesz (`seq_length = 64`), ezen az export nem változtat.

## MT-0 — formátum, névtár, tesztadat

* `docs/MULTITURN_FORMAT.md`: a rekord (a 9 régi mező származtatott + `turns` + `meta`), a `turns` szabályai (felváltó szerepek, 3–8 váltás, egysoros, nyírt üzenetek, hosszkorlát), a `meta` mezői és a `depends` (mélység = `t//2 − min(i//2)`, legalább 1), a 9 család és 10 domain, a `dataset`/`fixture` mód, a számolás (beszélgetés / üzenet / tanítási minta külön), az állapotszótár, az MT-1 szabálykódok, a névtár-szabályok és korlátai.
* `tools/multiturn_name_bank.json`: 150 jóváhagyott keresztnév, tiltott keresztnevek és vezetéknevek, engedélyezett helynevek (átfedés nélkül, tesztelve).
* `tests/fixtures/multiturn/valid_conversations.jsonl`: **5 mesterséges tesztbeszélgetés** (`mtfx_valid_001…005`, F1/F3/F4/F5/F7, tegező és magázó, 3–4 váltás; összesen 36 üzenet, 18 tanítási minta, ebből 5 első fordulós és 13 előzmény-függő). **Nem részei az 1000 beszélgetéses csomagnak**: `meta.fixture: true`, `source: test_fixture`, dataset módban elutasítottak, `data/` alatt nincs multiturn fájl (tesztelve). A szövegeket én írtam, ellenőrzött magyar nyelvi lektor nélkül.

## MT-1 — beszélgetés-validátor

**Minden üzenetet vizsgál, a közbenső fordulókat is:** szerepek és sorrend, kötelező és ismeretlen mezők, `meta`/`depends`, származtatott mezők, üzenet-szöveg szabályok, a projekt meglévő tartalmi szűrései **üzenetenként** (a `dataset_validate.validate_row` importálásával, módosítás nélkül: személyes adat, veszélyes tartalom, angol keveredés, torz szó, ismétlődő karakter, túlállítás, assistant-üzenet legalább 3 szó), saját szabályok (MF-AI/Nexora említés, URL/domain, 8+ jegyű szám, `User:`/`AI:` felirat, névtár: nem jóváhagyott keresztnév, teljes név-minta, nem deklarált név), a `quality_notes` mezőre is. A kimenet **külön** mutatja a `legacy_validator_compatible` és a `turns_validated` állapotot, és külön számolja a beszélgetéseket, üzeneteket és tanítási mintákat (csak a turns-validált rekordokra).

**A kérés kulcsesete — hiba/személyes adat kizárólag egy közbenső üzenetben:** 9 tesztesetben (e-mail közbenső user-üzenetben; telefonszám közbenső assistant-üzenetben; jelszó- és kulcs-minta; angol keveredés; torz szó; ismétlődő karakter; túlállítás; 3 szó alatti assistant-válasz) a rekordot **a régi validátor hibátlannak tartja** (`validate_row` üres, `validate_file` 1 érvényes/0 elutasított sor), az **MT-1 elutasítja**, a pontos üzenetre (`turns[i].text`) mutatva. Kontraszt: ugyanaz a hiba az első user- vagy az utolsó assistant-üzenetben már a régi validátoron is elbukik.

**Tesztek:** 29 teszt sikeres (fixture-ök, 65 szerkezeti szabály-eset egy változtatásonként, 19 tartalmi/név-eset pontos útvonallal, névtár és ragozott nevek, fájl-szint és számlálás, parancssor).

## Ellenőrzések

| Ellenőrzés | Eredmény |
|---|---|
| `tests.test_te2_chat_text` | 36 teszt OK (`-W error::ResourceWarning` mellett is), valós adaton is |
| `tests.test_multiturn_validate` | 29 teszt OK |
| `tests.test_te1_dataset_export` | 35 teszt OK (a TE-1 változatlan) |
| `tests.test_v1_7_4_dataset_foundation` | minden teszt sikeres, STÁTUSZ: STABIL |
| **Mutációs vizsgálat MT-1** | 33 szándékos hibamutáns (pl. „csak az első és az utolsó üzenetet vizsgálja”, felhasználói/assistant-tartalom kihagyása, névellenőrzés, depends-mélység, fixture-védelem, hamis `turns_validated`, számlálás érvénytelen rekordokkal): **33/33-at a tesztek elbuktatnak** |
| **Mutációs vizsgálat TE-2** | 32 egyedi mutáns + 1 kombinált: a kizárás-, lista-, forrás-, manifest-, ellenőrzőösszeg-, kimeneti-út-, visszaparse-, veszteségmentesség-, formátum- és felirat-védelmek mind elbuktak; 2 egyedi mutáns (`a régi betöltő blokkfelbontása` és `a felosztás utáni blokkok`) túlélt, mert a két ellenőrzés egymást fedi — együtt kikapcsolva a teszt elbukik. Egy kiegyensúlyozott, de hamis darabszámú manifest-eset hiányát a vizsgálat találta meg, ezért új teszt készült |

## Korlátok

* Az MT-1 nem tartalmi ellenőrzés: nem ítéli meg, hogy a válasz helyes, természetes vagy előzmény-hű; a `depends` annotáció valódiságát kézi átolvasás ellenőrzi. A névfelismerés lista- és mintaalapú biztonsági háló (ragozott alakok szűk végződéslistával), nem bizonyíték arra, hogy nincs valós személy neve a szövegben.
* Nincs beszélgetés-szintű duplikáció-ellenőrzés és csoportképzés (MT-3), csoport-tudatos felosztás (MT-2), többfordulós renderelés/export (MT-4) és többfordulós tanító betöltő (MT-5). A karakter-LSTM képessége hosszú kontextus használatára nem bizonyított.
* Az egyfordulós adat train/validation/test felosztása (TE-3) még nincs; a TE-2 semmit nem oszt fel.
* A 6. csomag tartalmi lezárása nyitott (lásd `multiturn_package7_plan.md` 0. szakasz).

## Következő konkrét lépés

**MT-3** (`tools/multiturn_dedupe.py` + tesztek): beszélgetés- és fordulószintű duplikáció-ellenőrzés, a 4494 exportált sor elleni szivárgás-vizsgálat és közeli-változat csoportképzés (`groups.json`). Ez az utolsó kapu, amely az első 100 valódi beszélgetés generálása (MT-6) előtt hiányzik: az MT-0 (formátum) és az MT-1 (validátor) kész. Elfogadási feltételei a tervben (8. szakasz). Az adatgenerálás és a tanítás továbbra is külön jóváhagyást kér.
