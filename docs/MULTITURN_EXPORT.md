# MT-4 — felosztott többfordulós beszélgetések renderelése és exportálása kizárási szűrővel

Eszköz: `tools/multiturn_export.py` (mt4-1.0). Tesztek: `tests/test_multiturn_export.py`. Bemenet: az MT-2 `split_manifest.json` és az általa rögzített, MT-1-validált, MT-3-ellenőrzött bemenetek. Az eszköz **csak olvas**: forrásadatot, a felsőbb manifesteket és korábbi exportot nem módosít, nem töröl, és mindig **új** kimeneti mappába dolgozik. Nem tanít, nem generál adatot.

**Az export technikai előkészítés, nem tanítási engedély.** A manifest `split_approved`, `content_verified` és `training_ready` értéke `false`, és az export sikere ezeket nem változtatja (a felsőbb manifestek bájtra érintetlenek; tesztelt).

## 1. Alapelvek

| Elv | Megvalósítás |
|---|---|
| csak aktuális, teljes, érintetlen bemenet | az MT-2 manifestet a `multiturn_split.verify_manifest` ellenőrzi (bemenetek, kimenetek, MT-3 jelentés aktualitása, a kijelölés újraszámolása); ezen felül az MT-4 külön ellenőrzi a manifest **belső egységességét** (a kijelölés-lista és a csoport-tagság ellenőrzőösszege, egység-integritás, darabszámok, státusz-mezők); elavult, hiányos vagy megváltozott bemenetnél a **15-ös kóddal** megáll |
| a felosztás és a sorrend megmarad | a kijelölés az MT-2 `assignment` listája; részenként külön fájl; a beszélgetések a forrásfájlok MT-2 szerinti sorrendjében és sorrendjében; az üzenetek sorrendje és szerepe változatlan |
| kizárt, elutasított, fel nem oldott rekord nincs az exportban | az MT-2 visszatartási listáján túl **függetlenül** ellenőrzi: kizárási lista, `quality_notes` kizárás-jelölés, az MT-3 jelentés (nincs `blocked` rekord, nincs blokkolt tagot tartalmazó csoport); találat esetén 13-as kód, export nem jön létre |
| a hat TE-1 kizárás érvényben marad | a TE-1 export kizárt sorait (`te2.check_exclusions`: kizárási lista változatlan, forrássorok ellenőrzőösszege) betölti; a kizárt sorok azonosítója nem ütközhet, **szövegük** (instruction, input, output, nyírva) egyetlen exportált üzenetben sem szerepelhet (a hibaüzenet megnevezi a sort és a mezőt); az azonosítók és a szöveg-ellenőrzőösszegek a manifestben |
| nincs csendes átírás vagy csonkolás | a kanonikus másolat a forrássor **bájtjai**; a renderelt minta minden üzenete szegmensként jelölt (`complete`), a csonkolás és a nem ábrázolható előzmény-függés mintánként és összesítve, indoklással szerepel; ami veszteségmentesen nem ábrázolható, az **visszatartva**, nem átírva (`withheld.tsv`) |
| visszakövethető | minden minta rögzíti a forrásfájlt, sort, sor-ellenőrzőösszeget, beszélgetést, csoportot és a célfordulót; `export_index.tsv`, `conversation_index.tsv` |
| visszaolvasással ellenőrzött | a kiírt fájlokat az eszköz a lemezről visszaolvassa, mielőtt a manifest véglegesedik (`--verify-export` utólag újra elvégzi) |
| a tesztadat nem exportálható észrevétlenül valódi adatként | lásd 6. szakasz |

## 2. Kimenet (`<out-dir>/<futás>/`)

| Fájl | Tartalom |
|---|---|
| `canonical_train.jsonl`, `canonical_validation.jsonl`, `canonical_test.jsonl` | a beszélgetések **bájt-pontos forrássorai** részenként, forrássorrendben (egy sor = egy teljes beszélgetés: azonosítók, szerepek, teljes szöveg, `meta`) |
| `samples_<rész>_R1.jsonl`, `samples_<rész>_R2.jsonl` | a renderelt tanítási minták (assistant-fordulónként egy) az R1 és R2 módban; a két mód **ugyanazon minták alternatív renderelése**, nem összeadandó |
| `export_index.tsv`, `conversation_index.tsv` | soronként a minta/beszélgetés → forrás, forduló, ellenőrzőösszeg |
| `withheld.tsv` | a veszteségmentesen nem ábrázolható beszélgetések és az ok (üres, ha nincs) |
| `export_manifest.json` | bemenetek ellenőrzőösszegei, beállítások, darabszámok részenként és módonként, veszteség-jelölések összesítése, kizárás-védelem, státuszok, kimeneti fájlok ellenőrzőösszege, korlátok. **Csak ez jelzi a lezárt exportot**; `.partial` vagy `FAILED.txt` = nem használható |
| `FIXTURE_TEST_DATA_NOT_FOR_TRAINING.txt` | csak tesztadat (fixture) exportban |

## 3. Renderelés

Egy **minta** egy assistant-fordulóra adott cél. A beszélgetés-, az üzenet- és a mintaszám külön szerepel (a mintaszám = az assistant-fordulók száma; beszélgetésenként 1 első fordulós, a többi előzmény-függő). Az üzenetek egysorosak (MT-1), a címkék `User: ` / `AI: `, a blokkok között `\n\n`. A minta azonosítója: `<beszélgetés>#<mód>#<célforduló>`.

| Mód | Tartalom | Veszteség |
|---|---|---|
| **R1** (futásidő-hű) | a cél előtti **utolsó** váltás **a `src/memory.py` `build_prompt_context` szerint** (importált függvény, nem másolt; `User ≤ 80` / `AI ≤ 120` karakterre vágva), majd a **teljes** aktuális kérés és a **teljes** cél | az előzmény csonkolt lehet (`...` jelölővel); a mélység ≥ 2 előzmény-függés R1-gyel nem ábrázolható |
| **R2** (teljes előzmény) | a teljes beszélgetés a célig | nincs (csak a címkék és elválasztók kerülnek hozzá) |
| **R3** (összefoglaló-előzmény) | — | **nem készül**: kézi „arany” összefoglaló és külön döntés kell (terv 3.2, D-1); kérése hiba (18-as kód) |

**Minta-rekord (főbb mezők):** `text` (a renderelt szöveg), `messages` (szegmensek: `role`, `turn`, `kind` = `context`/`current`/`target`, `start`, `end`, `complete`), `target` (a cél szövegének karakter-tartománya a `text`-ben — a későbbi MT-5 veszteség-maszkjához), `content_complete`, `dependency` (`on`, `depth`, `covered`, `missing`), `lossless` (= `content_complete` és a függés lefedett), `history_truncation` (üzenetenként `original_chars`, `rendered_chars`, `lost_chars`), `family`, `domain`, `data_kind`, `fixture`, `source` (`file`, `line`, `line_sha256`).

**Az R1 előtag bájt-pontos:** a teszt a `src/memory.py` külön betöltött példányával, valamint a dokumentált szabály betű szerinti alkalmazásával (80/81, 120/121 karakteres határ, `rstrip`) veti össze; a `memory.build_prompt_context` lecserélése esetén az R1 a lecserélt kimenetet adja (bizonyíték az importálásra). A `src/memory.py` ellenőrzőösszege a manifestben.

## 4. Veszteség és amit nem ábrázol

* **R1 csonkolás:** a valódi beszélgetésekben az asszisztens-üzenetek átlagosan hosszabbak 120 karakternél (terv: medián ≈ 200), így az R1 előzménye többnyire csonkolt. Ez a futásidő-hűség ára, nem hiba: **mintánként jelölt**, összesítve a manifestben (`content_truncated`, `messages_truncated`, `history_chars_lost`).
* **Mélyebb előzmény-függés:** ha a `meta.depends` bejegyzés olyan üzenetre hivatkozik, amely nincs az R1 mintában (mélység ≥ 2), a minta `dependency.covered: false`, `lossless: false`; az R1 ezt nem tudja tanítani, az R2 igen.
* **Nem ábrázolható beszélgetés:** üres, széleiben szóközös, sortörő vagy vezérlő karaktert tartalmazó üzenet, vagy a futásidő-függvény üres előtagot adna: a beszélgetés **visszatartva** (nem javítva), indokkal; a kimenet ekkor a 1-es kilépési kóddal figyelmeztet, és a darabszám eltér az MT-2-től (a manifest jelzi). MT-1-validált bemenetnél ez védekező ellenőrzés.
* **R2 hossza:** a teljes előzményes minta akár néhány ezer karakter; a karakter-LSTM tanításkori ablaka (`seq_length = 64`) ennél sokkal rövidebb — a használatáról az MT-5 és a külön jóváhagyás dönt.

## 5. Ellenőrzések sorrendje

1. mód és renderelés-lista (R3/ismeretlen → 18);
2. MT-2 manifest: olvasható, belső egység, státuszok `false`, `verify_manifest` (15);
3. a kért mód egyezik a manifest módjával (18); a futás-mappa neve: fixture → `fixture_` előtag, valódi adat → nem `fixture…` (18);
4. források: a kijelölt sorok bájt-pontosan egyeznek a manifest sor-ellenőrzőösszegével, MT-1-érvényesek (11/15);
5. kizárások: visszatartott, kizárási listás, kizárás-jelölt rekord; a hat TE-1 kizárás (azonosító és szöveg); az MT-3 jelentés függetlenül (13);
6. kimeneti útvonal: nem lehet a bemenetek mappája alatt, sem `data/clean|raw|rejected|inbox` alatt, nem írhat felül (14);
7. renderelés, kiírás, **visszaolvasás** (17): kanonikus sorok = forrássorok; a minták független visszaparse-olása a beszélgetésekkel; szegmens-határok; részenkénti szétválasztás, sorrend; szerepek; `lossless`/függés jelölések; kizárt szöveg hiánya; indexek; darabszámok az MT-2-vel és a képlettel; státuszok és tesztadat-jelölés;
8. a bemenetek sha256-a a futás előtt és után azonos (16).

## 6. Tesztadat-védelem és státuszok

* A `--mode dataset|fixture` **kifejezett**, és egyeznie kell az MT-2 manifest módjával; a tesztadat (fixture) és a valódi adat nem keverhető.
* Fixture exportban: a futás-mappa neve `fixture_` előtagú, minden minta `fixture: true` és `data_kind: fixture`, a manifest `training_data: false` és `purpose: technikai próba…`, a mappában jelölő fájl van, a kanonikus rekordok `meta.fixture: true`. A visszaolvasás mindezt ellenőrzi.
* Az MT-1 dataset módja elutasítja a tesztadatot, így az nem is kerülhet valódi exportba.
* Az export a `split_approved`, `content_verified`, `training_ready` értékét csak **átveszi** (mind `false`), nem állítja át; ha az MT-2 manifest bármelyiket igazra állítaná, az MT-4 elutasítja a bemenetet.

## 7. Korlátok

* Az R1 futásidő-hű, de csonkolt; az R3 nem készül. A tényleges tanítási formátum (melyik mód, ablakhossz, veszteség-maszk) az MT-5 és a külön jóváhagyás kérdése.
* A kizárt TE-1 sorok elleni védelem pontos (nyírt) szövegegyezésre vonatkozik; átfogalmazott vagy részleges átfedést nem talál.
* A visszaolvasásos ellenőrzés a formátum és a forrás megfelelését igazolja, nem a tartalom minőségét; a `clear` MT-3 állapot és a felosztás sem tartalmi ellenőrzés.
* Az export felhasználható-e tanításra, külön kifejezett felhasználói döntés; a manifestek ezt sosem állítják.

## 8. Használat és kilépési kódok

```bash
python tools/multiturn_export.py --mode dataset|fixture --mt2-manifest <split_manifest.json> --out-dir <mappa> [--modes R1,R2] [--allow-no-te1-comparison] [--run-name <név>]
python tools/multiturn_export.py --verify-export <export_manifest.json>
```

`0` kész, teljes; `1` kész, de figyelmet kér (visszatartott beszélgetés, TE-1 összevetés nélküli bemenet); `2` argumentumhiba; `10` bemeneti fájl hiba; `11` nem turns-validált rekord; `12` TE-1 export hiba; `13` kizárás megsértése; `14` kimeneti útvonal hiba; `15` elavult/hiányos/megváltozott bemenet; `16` a bemenet a futás közben megváltozott; `17` a visszaolvasásos ellenőrzés hibát talált (nincs véglegesített export); `18` elutasított kérés (mód, nem támogatott renderelés, tesztadat-védelem).
