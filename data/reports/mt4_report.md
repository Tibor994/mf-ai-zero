# MT-4 — a felosztott beszélgetések renderelése és exportálása kizárási szűrővel — jelentés

Dátum: 2026-09-27. Eszköz: `tools/multiturn_export.py` (**mt4-1.0**, új). Tesztek: `tests/test_multiturn_export.py` (**70**). Dokumentáció: `docs/MULTITURN_EXPORT.md`. Bizonyítékok: `data/reports/audit_evidence/mt4_export/`.

Nem történt tanítás és nem készült valódi tanítóadat vagy valódi többfordulós beszélgetés. A tanító-, chat-, webapp/backend-kód, a `src/` (köztük a `src/memory.py`) és a korábbi eszközök (`tools/dataset_*.py`, TE-1, TE-2, MT-1, MT-2, MT-3) **nem módosultak**; az MT-4 fájlok újak. A hat kizárás érvényben maradt (a TE-1 export továbbra is 4500 sorból 6-ot kizár, 4494-et exportál). Semmilyen adat nem lett training-ready; az export sikere a `split_approved`, `content_verified`, `training_ready` állapotokat nem változtatja (mind `false`, a felsőbb manifestek bájtra érintetlenek).

## 0. A kiinduló állapot ellenőrzése a tényleges repóval

| Állítás | Ellenőrzés | Eredmény |
|---|---|---|
| a legutóbbi commit `07881cd` (`v1.13.22-mt2-split`) | `git log`, `git rev-parse HEAD origin/main` | egyezik (HEAD = origin/main) |
| 4500 clean sor, 6 kizárt, 4494 exportált | a valódi TE-1 export a valós-adatos teszten és a méréseken | **4500 beolvasva, 6 kizárva, 4494 exportálva**; az MT-4 manifest a hat azonosítót és a 12 kizárt szöveg ellenőrzőösszegét rögzíti |
| valódi többfordulós adat nincs | `data/raw|clean|rejected|inbox` alatt `*multiturn*` | **nincs** (tesztelt) |
| a korábbi eszközök működése | TE-1 35, TE-2 36, MT-1 29, MT-3 75, MT-2 70 teszt; `tests.test_v1_7_4_dataset_foundation` | mind OK, STABIL |

## 1. Mi készült

| Fájl | Szerep |
|---|---|
| `tools/multiturn_export.py` | az MT-4 eszköz (bemenet: az MT-2 manifest) |
| `tests/test_multiturn_export.py` | 70 teszt |
| `docs/MULTITURN_EXPORT.md` | módszer, kimenet, renderelés, veszteség, ellenőrzések, kilépési kódok |
| `data/reports/audit_evidence/mt4_export/` | 1000 beszélgetéses méréseket futtató szkript és eredmények, mutációs vizsgálat |
| `data/reports/multiturn_package7_plan.md` | frissítve (MT-4 kész) |

Kimenet egy új futás-mappában: részenként (train / validation / test) a **bájt-pontos kanonikus beszélgetések**, az **R1 és R2 renderelt minták**, a `export_index.tsv` és a `conversation_index.tsv` (visszakövetés), a `withheld.tsv`, és az `export_manifest.json`.

## 2. A kéréseid pontjai

| A kérésed | Megvalósítás | Teszt |
|---|---|---|
| az MT-2 manifest és a bemenetek ellenőrzése; elavult, hiányos, megváltozott bemenetnél egyértelmű hiba | `verify_manifest` (bemenetek, kimenetek, MT-3 jelentés, a kijelölés újraszámolása) + az MT-4 saját ellenőrzése a manifest belső egységéről (kijelölés- és csoport-ellenőrzőösszeg a manifest saját listáiból, egység-integritás, darabszámok, státuszok `false`) + a forrássorok bájt-pontos ellenőrzőösszege; hibánál **15-ös kód**, nincs futás-mappa | hiányzó/sérült manifest; hiányzó kulcsok; áthelyezett beszélgetés a manifestben; módosított csoport-tagság, darabszám, státusz, ellenőrzés; jóváhagyást állító manifest; megváltozott beszélgetés-fájl, MT-3 jelentés, kizárási lista, TE-1 export, MT-2 kimenet; forrássor-eltérés; futás **közben** és **kiírás közben** megváltozó bemenet |
| a beszélgetések sorrendje, szerepek, teljes tartalom, azonosítók, felosztás megőrzése; a részek elkülönítése | a kanonikus másolat a forrássor bájtjai, forrássorrendben, részenként külön fájl; a minták beszélgetésenként, célforduló szerint rendezve | a kanonikus sor bájt-azonos a forrássorral; a JSON-objektum azonos; a szerepek váltakoznak; azonosítók; minden beszélgetés pontosan egy részben; a csoportok nem szakadnak szét; a részek beszélgetés-halmaza egyezik az MT-2 kijelöléssel |
| kizárt, elutasított és fel nem oldott rekord ne kerüljön az exportba; a hat kizárás maradjon érvényben | az MT-2 visszatartási listáján túl **függetlenül**: kizárási lista, `quality_notes` jelölés, MT-3 jelentés (nincs blokkolt rekord vagy csoport); a hat TE-1 kizárt sor azonosítója nem ütközhet, **szövege** (instruction, input, output, nyírva) egyetlen üzenetben sem szerepelhet | mind az öt rekord-osztály elutasítva akkor is, ha a manifest kijelölte volna; a hat valódi kizárt sor **mind a 12 szövege** (kérdés és válasz) elutasítva, a hibaüzenet megnevezi a sort és a mezőt; szóközös változat; azonosító-ütközés; TE-1 nélküli bemenet csak kifejezett kapcsolóval, figyelmeztetéssel |
| nincs csendes átírás vagy csonkolás; ami nem ábrázolható veszteségmentesen, azt indoklással jelezze | a kanonikus másolat nem átírt; a renderelt minták üzenetenként jelölt szegmensei (`complete`), a csonkolás (`original/rendered/lost_chars`) és a nem ábrázolható előzmény-függés mintánként és összesítve; a nem ábrázolható beszélgetés **visszatartva** (`withheld.tsv`), nem átírva; az R3 nem készül, indoklással | R1 határértékek (80/81, 120/121, `rstrip`), csonkolás- és függés-jelölés; sortörő/vezérlő/üres/szóközös üzenet; üres előtag a futásidő-függvényből; ellentmondó renderelés (önellenőrzés) |
| visszaolvasási teszt igazolja a tartalmat, a szerepeket és a beszélgetéshatárokat | a kiírt fájlokat az eszköz a lemezről, a renderertől független darabolással visszaolvassa a manifest véglegesítése előtt (`verify_export`), és a `--verify-export` utólag újra elvégzi | a teszt saját, független visszaolvasása; 40+ szándékos elrontás (tartalom, szerep, határ, sorrend, hiányzó/áthelyezett/kettőzött rekord, státusz, jelölő, ellenőrzőösszeg) **akkor is** észrevétlen marad-e, ha a manifest ellenőrzőösszege újra van írva; renderer-hiba észlelése |
| új kimeneti mappa; forrásadat és korábbi export nem íródik felül; visszakövethetőség | a futás-mappa új, létező nem írható felül, nem lehet a bemenetek mappája alatt sem `data/clean\|raw\|rejected\|inbox` alatt; minden minta rögzíti a forrásfájlt, sort, sor-ellenőrzőösszeget, beszélgetést, csoportot és a célfordulót | kimeneti útvonal-védelem, felülírás tilalma; a felsőbb fájlok ellenőrzőösszege a kiírás előtt és után azonos; minden index-sor a forrássorra és fordulóra visszavezethető |
| a technikai próba elkülönített tesztadaton; tesztadat ne exportálódjon észrevétlenül valódi adatként; az export ne változtassa a státuszokat | kifejezett `--mode`, egyeznie kell az MT-2 manifest módjával; fixture: `fixture_` előtagú futás-mappa, jelölő fájl, minden minta `fixture: true` és `data_kind: fixture`, `training_data: false`; a státuszok átvétele (mind `false`), jóváhagyást állító bemenet elutasítva | mód-eltérés, rossz futásnév, rekord-jelölés eltérés, jelölő fájl és előtag utólagos ellenőrzése, státuszok |
| csak MT-4; háttérparancsok folyamatállapot és kilépési kód alapján | nincs adatgenerálás, tanítás, módosított tanító-/chat-/webapp-kód; a háttérben futó mérések és mutációs szeletek egy vezérlő szkripttel futottak, amely a szeletek **kilépési kódját** és időkorlátot használ (nem naplószöveget) | lásd a 5. szakaszt |

## 3. A renderelés — és amit tudni kell

* **R1 (futásidő-hű):** az előtag a `src/memory.py` `build_prompt_context` **importált** függvényének kimenete (nem másolat; a teszt igazolja: a függvény lecserélésekor az R1 a lecserélt kimenetet adja). Az előtag a cél előtti **utolsó** váltás, `User ≤ 80 / AI ≤ 120` karakterre vágva; az aktuális kérés és a cél **teljes**. A vágás a futásidő viselkedése, de **veszteség**: mintánként jelölt.
* **R2 (teljes előzmény):** a teljes beszélgetés a célig, veszteségmentes (csak címkék és elválasztók kerülnek hozzá).
* **R3 nem készül:** kézi „arany” összefoglalót igényel, és külön döntés kell (terv 3.2, D-1); kérése hiba (18-as kód), a manifest indokolja.
* **Az R1 csonkolásának mértéke** (1000 mesterséges beszélgetés; az én generátorom üzenet-hosszaival, valódi adaton más lehet): a train rész 4243 R1-mintájából **3031 (71%)** csonkolt előzményű, **607 (14%)** mélyebb előzmény-függése R1-gyel nem ábrázolható, csak **1137 (27%)** veszteségmentes; összesen 127 994 karakter marad ki az előzményekből. Ugyanez az R2-ben 0. Az R1 tehát futásidő-hű, de a többfordulós előzmény jelentős részét nem adja át; az MT-5 előtt el kell dönteni, melyik módot használja a tanítás.
* A minta-rekord tartalmazza a `target` karaktertartományt (a cél szövegének helye a mintában): az MT-5 veszteség-maszkja erre épülhet.

## 4. Tesztek és mérések

**Tesztek:** `tests.test_multiturn_export`: **70 teszt OK** (~70 mp). Osztályok: renderelés (tiszta függvények, 12), az export tartalma és szerkezete (14), elavult/hiányos/megváltozott bemenet (8), kizárások (6), veszteségmentesség és nem ábrázolható esetek (4), tesztadat-védelem és kimeneti mappa (4), visszaolvasás elrontott exporton (8), **minden ellenőrzés a saját üzenetével** (9), parancssor (2), valós TE-1 export a hat kizárással (3).

**Mérés (1000 mesterséges beszélgetés, a valódi 4494 példás TE-1 exporttal szemben; `audit_evidence/mt4_export/`):**

| Mutató | Tiszta korpusz | 12 beültetett blokkolt másolattal és 6 kizárt beszélgetéssel |
|---|---|---|
| MT-2 kijelölés | 1000 / 0 visszatartott | 970 / 42 visszatartott |
| export (beszélgetés, train / val / test) | 800 / 100 / 100 | 776 / 97 / 97 |
| üzenet | 8486 / 1074 / 1052 | 8214 / 1032 / 1032 |
| minta módonként (R1 = R2 darabszám), első fordulós + előzmény-függő | 4243 / 537 / 526 (800+3443, 100+437, 100+426) | 4107 / 516 / 516 |
| az MT-2 manifest darabszámaival egyezik | igen (0 visszatartott) | igen |
| kimenet mérete | R1: 6,7 + 0,85 + 0,83 MB; R2: 9,4 + 1,2 + 1,2 MB; kanonikus: 2,1 + 0,27 + 0,26 MB | hasonló |
| MT-4 futásidő (a manifest-ellenőrzés újraszámolásával együtt) | **14,8 mp** (ebből render+írás 1,1 mp, a visszaolvasás 1,3 mp) | 15,8 mp |
| második export bájtra azonos; felsőbb fájlok érintetlenek; visszatartottak hiányoznak; részek szétválasztva | igen / igen / igen / igen | igen / igen / igen (mind a 12 másolat, a persona-társaik és a 6 kizárt hiányzik) / igen |

**Mutációs vizsgálat:** **114 mutáns, mind elbukik.** Az első futásban 113-ból 77 bukott el, **36 túlélt**. Ennek oka nem egyetlen hiányzó teszt volt: a visszaolvasás és a bemenet-ellenőrzések egymást átfedő ellenőrzéseket tartalmaznak (mélységi védelem), ezért egy ellenőrzés kihagyását egy másik is jelezte, és a teszt csak „valamilyen” hibát talált. Javítás: minden ellenőrzéshez olyan teszt készült, amely a **saját, egyedi üzenetét** kéri, a bemenet-oldali ellenőrzéseket egységszinten hívja; új teszt, hogy a renderer-hibát a független visszaolvasás akkor is észreveszi, ha az export és az ellenőrzés ugyanazt a renderert használja, és hogy az ellentmondó renderelést az önellenőrzés visszatartja. Az újrafuttatásban a 36 túlélő és egy új mutáns közül 1 túlélt (a mód-választás saját üzenetét a manifest-egyezés üzenete is tartalmazta), ez a teszt szigorításával elbukott. **Egy megjegyzés:** az 1. futás szelet-naplóit egy fájl-törlési hiba miatt nem őriztem meg; a végeredményt a vezérlő összegző fájlja adja (a `mutation_results.txt` ezt jelzi).

**Regresszió:** `tests.test_multiturn_export` + `test_multiturn_split` + `test_multiturn_dedupe` + `test_multiturn_validate` + `test_te1_dataset_export` + `test_te2_chat_text`: **315 teszt OK** (`-W error::ResourceWarning` mellett is, kilépési kód 0); `tests.test_v1_7_4_dataset_foundation`: STABIL (a modul saját futtatóval fut: a szkript kilépési kódja 0; a `python -m unittest` burkoló 5-ös kódja csak azt jelzi, hogy unittest-teszt nincs benne, ez a korábbi állapottal azonos).

## 5. Háttérfolyamatok kezelése

Az előző munkából két várakozó parancs bennragadt (naplószövegre vártak, amely a kódolás miatt sosem egyezett). Ezt te észrevetted; a két parancsot leállítottam. Ebben a munkában a háttérben futó parancsok (tesztfutások, mérések, mutációs szeletek) **folyamatállapotra és kilépési kódra** épültek: a tesztfutás a kilépési kódját a napló végére írta, a mérések ugyanígy; a mutációs szeleteket egy vezérlő szkript részfolyamatként indította, `wait`-tel (időkorláttal) várta és a kilépési kódokat, valamint az összegzést fájlba írta; a hosszú várakozások korlátos, folyamatállapotot ellenőrző ciklusok voltak. A munka végén nem maradt futó `python` vagy várakozó `sleep` folyamat, és nem maradt függő háttér-feladat.

## 6. Milyen bemeneten történt az ellenőrzés

* **Mesterséges tesztadat** (a valódi 1000 beszélgetés nem létezik): a `tests/test_multiturn_split.py` generátora — valós magyar szavakból összeállított **értelmetlen mondatok** (`mtfx_syn_NNNN`, `meta.fixture: true`), MT-1-validálva fixture módban. Szerkezetileg érvényesek, de tartalmilag nem beszélgetések; az 1000 beszélgetéses csomagba nem számítanak, tanításra nem használhatók.
* A **valódi TE-1 export** (4494 példa, a hat kizárás érvényesítve) mint referencia és a hat kizárt sor forrásszövege, csak olvasva; a `data/` a tesztek előtt és után bájtra azonos, `*multiturn*` fájl nincs.
* **Valódi többfordulós adaton nem futott**, mert nincs.

## 7. Pontosan mire vonatkozik a STABIL minősítés

**STABIL** = a `tools/multiturn_export.py` (mt4-1.0) **működése** a fenti mesterséges és szintetikus bemeneteken és a valódi TE-1 exporttal szemben: a 70 teszt, a 114/114 mutáns, a mérések (visszaolvasás, ismételhetőség, felsőbb fájlok érintetlensége) és a regresszió (315 teszt + foundation) sikeres. **Nem vonatkozik** valódi többfordulós adat minőségére, tartalmi helyességre, természetességre, a felosztás vagy az export jóváhagyására, arra, hogy az R1 vagy az R2 alkalmas-e tanításra, vagy training-ready állapotra.

## 8. Ami bizonytalan vagy nyitott

* **R1 vagy R2:** az R1 futásidő-hű, de a mintáknak csak ~27%-a veszteségmentes (mesterséges hosszakkal); az R2 veszteségmentes, de hosszú, és a jelenlegi futásidő nem ad ekkora előzményt (D-1). A karakter-LSTM tanítási ablaka (`seq_length = 64`) mindkettőnél sokkal rövidebb a mintánál: a mintánkénti kódolás, az ablakolás és a veszteség-maszk az MT-5 feladata és külön döntés.
* **R3** nem készül: „arany” összefoglaló és döntés kell.
* A kizárt TE-1 sorok elleni védelem pontos (nyírt) szövegegyezésre vonatkozik; átfogalmazást vagy részleges átfedést nem talál.
* A visszaolvasás a formátumot és a forrás-megfelelést igazolja, nem a tartalom minőségét; az MT-3 „tiszta” állapota és a felosztás sem tartalmi ellenőrzés.
* Az MT-4 a felosztás manifestjét a `verify_manifest` újraszámolásával ellenőrzi: ez 1000 beszélgetésnél ~8–10 mp, de minden export előtt lefut (szándékos, nem kihagyható).
* A mutációs vizsgálat 1. futásának szelet-naplói elvesztek (lásd 4. szakasz); az eredmény a vezérlő összegzésén és az újrafuttatásokon alapul.

## 9. Következő konkrét lépés (MT-5) és a tanítás előtt még hiányzó feladatok

**Az MT-5 (`src/train_multiturn.py`, csak betöltés és száraz futás) jóváhagyása előtt / mellett dönteni kell:**
1. **melyik renderelés** a tanítás bemenete (R1, R2, vagy külön kísérlet mindkettővel);
2. az **ablak/szekvencia-hossz** kezelése (a jelenlegi 64 karakter és a mintahossz viszonya), és hogy a v0.7 tanító érintetlensége mellett hogyan olvasható a többfordulós minta;
3. hogy az MT-5 a tesztadat-exportot (`data_kind: fixture`) csak kifejezett tesztmódban fogadja el.

Az MT-5 betöltő bemenete az MT-4 export (`export_manifest.json`, `samples_<rész>_<mód>.jsonl`; a `target` tartomány adja a veszteség-maszkot); a szótár csak a train részből épül; a bemeneti manifest ellenőrzése (hiány/sha256-eltérés → hiba); `--dry-run` statisztikával, tanítás nélkül.

**A tanítás előtt még hiányzik:**
* **MT-5** — többfordulós tanító betöltő (csak betöltés és száraz futás), mintánkénti kódolás, veszteség-maszk; a v0.7 tanító érintetlen.
* **TE-3** — az 1–6. csomag egyfordulós adatának globális, csoport-/közeli-változat-tudatos felosztása (a TE-2 export nem oszt fel); az MT-2 `export_links.json` kapcsolatait figyelembe véve.
* **Nyitott tartalmi ellenőrzések:** a 6. csomag korlátozott lezárása (6 kizárt sor: `0220`, `0829`, `0849`, `0864` jogi átnézésre, `0602`, `0898` forrásra vár); 10 nem forrásolt E-sor; 7 hedge-elt, forrás nélküli szám; 39 előtag nélküli kontraszt-sor újracímkézése; 14 ismétlődő `kind` címke; **független emberi/szakértői átolvasás** az egész korpuszra; az 1–5. csomag kibővített céljának tartalmi lefedettségi auditja; a 7–10. csomag (és az 1–5. csomag hiányzó adatának) generálása külön jóváhagyással.
* **D-1** — a futásidejű előzmény-mélység (1 váltás) és az R3 „arany összefoglaló” döntése (webapp/backend módosítás csak külön jóváhagyással).
* Az első 50 beszélgetés generálása (MT-6 kapu) kifejezett jóváhagyással — a nyitó váltásokat változtatni kell (azonos nyitó minta `reject`).
* A felosztás és az export jóváhagyása, és a tanítás megindításának kifejezett engedélye.
