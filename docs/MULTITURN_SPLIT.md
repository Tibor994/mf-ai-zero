# MT-2 — csoport-tudatos, reprodukálható felosztás (train / validation / test)

Eszköz: `tools/multiturn_split.py` (mt2-1.0). Tesztek: `tests/test_multiturn_split.py`. Bemenet: az `docs/MULTITURN_FORMAT.md` szerinti, az MT-1 által **turns-validált** beszélgetés-rekordok és az **aktuális MT-3 jelentés** (`tools/multiturn_dedupe.py`, mt3-2.x). Az eszköz **csak olvas**: forrásadatot nem módosít, nem töröl, és új adatot nem generál.

**Az eredmény technikai kijelölés, nem jóváhagyott felosztás:** a manifest `split_approved: false`, `training_ready: false`, `content_verified: false`. A felosztás és a tartalmi ellenőrzés jóváhagyása külön felhasználói döntés.

## 1. Alapelvek

| Elv | Megvalósítás |
|---|---|
| A felosztási egység a csoport, nem a rekord és nem a minta | egy beszélgetés **összes** váltása/mintája, és az MT-3 szerint hozzá kötött összes változat **egy** részbe kerül |
| A számított csoport a mérvadó | az egység az MT-3 **számított** csoportja (`mtg_…`), nem a deklarált `meta.split_group`; az MT-3 csoportjai már tartalmazzák a közös `split_group` és `persona` kapcsolatokat, ezt az MT-2 külön ellenőrzi |
| A dokumentált kivétel nem választja szét a párt | a kivétellel felmentett (`accepted_with_exception`) párt az MT-2 **egy egységbe vonja**, akkor is, ha az MT-3 nem kötötte össze (pl. `sample_near_short`): a szöveges közelség tudott, ezért egy részben marad |
| A csoport-integritás előbbre való a pontos darabszámnál | ha a cél nem érhető el, az eszköz **jelenti az eltérést**, csoportot nem vág szét |
| Fel nem oldott döntés nem kerül kijelölésre | MT-3 `reject`/`review` (haladási tiltás), az ilyen tagot tartalmazó csoport, kizárási listás rekord, kizárás-jelölésű rekord: `held_back`, okkal |
| A kizárások érvényesek maradnak | a TE-1 exportból hiányzó hat sor azonosítója a manifestben szerepel; ha egy beszélgetés azonosítója egy TE-1 kizárt sor azonosítójával egyezne, visszatartva |
| Elavult eredmény nem használható csendben | az MT-3 jelentés aktualitását az eszköz ellenőrzi (lásd 3. szakasz); eltérés esetén hibával (15-ös kód) áll meg |
| Reprodukálható | az eredmény csak a bemenetektől, a beállításoktól és a `--seed` értéktől függ; nem függ a rekordok/fájlok sorrendjétől; nincs Python `random`, nincs hash-véletlenítés: minden „véletlen” sha256-ból számolt |

## 2. Az algoritmus

1. **Egységek.** Az MT-3 csoportjai + a kivétellel felmentett párok egyesítése (egyszeres kötés). Egység-azonosító: a benne lévő legkisebb MT-3 csoportazonosító.
2. **Visszatartások.**
   * `mt3_blocked`: a rekord MT-3 haladása `blocked` → **az egész egység** visszatartva; a csoporttársak oka `group_has_blocked_member` (a fel nem oldott változat-probléma miatt a csoport összetétele bizonytalan);
   * `excluded_list` (a `--exclusions` lista), `excluded_marker` (a `quality_notes`-ban a TE-1 kizárás-jelölés), `id_collides_with_te1_excluded_row`: csak **a rekord** marad ki; a csoporttársai kijelölhetők, a visszatartott rekord pedig `reserved_split` értéket kap (abba a részbe kerülne, ha később felszabadul).
3. **Cél-darabszámok.** `--targets train,validation,test` (alap `800,100,100`). Ha a kijelölhető darabszám eltér a terv összegétől (pl. visszatartások, vagy az első 100 beszélgetés), a célt legnagyobb maradékos módszerrel arányosan skálázza (`ideal_counts`); a jelentés mindkettőtől (terv és ideális) mutatja az eltérést, és külön jelzi a skálázást (`scaled_from_planned`).
4. **Darabszám-optimalizálás (pontos).** A 2+ tagú egységekre bitkészletes dinamikus programozás: az összes elérhető (validation, test) darabszám-pár közül a legkisebb összeltérésű (|train−cél| + |validation−cél| + |test−cél|); az 1 tagú egységek (töltelék) kitöltése konvex, szakaszonként lineáris célfüggvény pontos minimumával (`best_fill`). Döntetlennél a kisebb legnagyobb eltérés, majd a **többtagú egységek arányos részesedése** nyer (különben a csoportok mind a train részbe kerülnének). A nagy csoport a train részbe kerül, ha nem fér a kisebb részbe.
5. **Konkrét kijelölés.** Az egységek sha256(`seed|egység-azonosító`) szerinti, a bemeneti sorrendtől független sorrendben, súlyozott bejárással (csak olyan választás, amelyből a DP célállapota még elérhető).
6. **Rétegzés.** Azonos méretű egységek cseréje a részek között (a darabszám és az egységek érintetlenek) a család, hosszsáv (váltásszám: 3–4 / 5–6 / 7–8), domain és „nehéz” jelző arányosabb eloszlásáért (χ²-szerű veszteség, determinisztikus lokális keresés). „Nehéz” = előzmény-mélység ≥ 2 **vagy** család F4 (felhasználói javítás) / F7 (témavisszatérés). A terv „legalább 30 nehéz a 100 teszt-beszélgetésből” minimuma a `--min-hard-test` (alap `auto`: a teszt-darabszám 30%-a, legfeljebb a kijelölhető nehéz beszélgetések száma), büntetőtagként; nem teljesíthető minimumot a jelentés jelzi.
7. **Független ellenőrzés** (a nyers adaton, nem az algoritmus köztes szerkezetein): minden rekord pontosan egyszer kijelölt vagy visszatartott; egység, MT-3 csoport, deklarált `split_group`, `persona`, MT-3 él és kivétellel felmentett pár nem szakad szét; nincs kijelölt blokkolt rekord vagy blokkolt tagot tartalmazó csoport; nincs kijelölt kizárt rekord; nincs részek között megosztott, fel nem oldott (`reject`/`review`) MT-3 páros. Hiba esetén 17-es kód, kimenet nélkül.

## 3. Az MT-3 jelentés aktualitása (elavult eredmény nem használható)

Az eszköz csak akkor fogad el MT-3 jelentést, ha **mind** teljesül:

* `tool == tools/multiturn_dedupe.py`, `status == completed`, `training_ready` és `content_verified` `false`;
* `tool_version` egyezik az MT-3 eszköz jelenlegi verziójával (a `mt3-1.x` jelentések a felülvizsgált döntési szabályok előttiek: elutasítva), és a jelentés `tool_sha256` mezője az MT-3 **jelenlegi fájljának** ellenőrzőösszegével egyezik (más kóddal készült eredmény nem használható);
* a 0,90/0,95/0,80 küszöbök egyeznek, és a jelentés rögzíti, hogy a közös `split_group` nem írja felül a döntést;
* a jelentés összes bemenete (beszélgetés-fájlok, TE-1 export manifest/export/index, névtár, kivétel-fájl) ellenőrzőösszege **változatlan** (`dedupe --verify-report` logika);
* a jelentés beszélgetés-fájljai (útvonal és ellenőrzőösszeg) és rekordjai (`fájl:sor`, azonosító, **sor-ellenőrzőösszeg**) **pontosan egyeznek** a felosztás bemenetével; nincs csoport nélküli rekord;
* a jelentés csoport-tagsága önkonzisztens, és tartalmazza a deklarált `split_group`/`persona` kapcsolatokat;
* a jelentés tartalmaz TE-1 export összevetést (különben csak kifejezett `--allow-no-te1-comparison` mellett, figyelmeztetéssel: a részek közötti átfedés az egyfordulós adattal szemben ilyenkor nem vizsgált), és ha `--te1-export` adott, az ugyanaz, amellyel az MT-3 készült.

A futás közben megváltozó bemenet 16-os kódú hiba. A kész manifest bemeneteit és kimeneteit a `--verify-manifest` ellenőrzi, **majd a kijelölést újraszámolja** ugyanazokból a bemenetekből és beállításokból, és összeveti a rögzítettel (15: megváltozott bemenet/kimenet; 18: nem reprodukálható).

## 4. Kimenetek (`<out-dir>/<futás>/`)

| Fájl | Tartalom |
|---|---|
| `split_manifest.json` | a teljes feljegyzés: bemenetek ellenőrzőösszegei (beszélgetés-fájlok, MT-3 jelentés és eszköz, TE-1 export, kizárási lista, névtár), beállítások (seed, célok, ideális darabszámok, rétegzés), egységek és tagságuk, a rekordonkénti kijelölés (`fájl`, `sor`, `sor-ellenőrzőösszeg`, egység, rész), visszatartások okkal, részenkénti darabszámok (beszélgetés, üzenet, minta — első fordulós és előzmény-függő külön), eloszlások, eltérések, „nehéz” minimum, rétegzési eredmény, részek közötti átfedések és TE-1 kapcsolatok összegzése, ellenőrzési eredmények, kimeneti fájlok ellenőrzőösszege, figyelmeztetések, korlátok |
| `assignment.tsv`, `groups.tsv`, `ids_train.txt`, `ids_validation.txt`, `ids_test.txt` | a kijelölés olvasható alakja (az id-listák csak azonosítókat tartalmaznak, adatot nem másolnak) |
| `held_back.tsv` | visszatartott rekordok, okok, MT-3 találat-azonosítók, `reserved_split` |
| `cross_split_overlaps.tsv` | az MT-3 által jelzett, **részek között** megosztott rekordpárok (csoportot nem kötő, információ-szintű átfedések is) |
| `export_links.json` | a TE-1 exporttal talált kapcsolatok a **későbbi TE-3** egyeztetéshez |

**TE-3 egyeztetés.** A TE-3 (az 1–6. csomag egyfordulós adatának felosztása) még nem létezik. A `duplicate_like` kapcsolatú TE-1 sort (`sample_exact/near/near_short/name_swapped/at_boundary`) a TE-3-nak abba a részbe kell tennie, amelybe a kapcsolódó beszélgetés-csoport került (`required_split`), különben a közeli másolat részek között oszlik meg; a `partial_overlap` csak tájékoztató. Két különböző részbe került csoporthoz kötött sor `conflict`; a visszatartott beszélgetéshez kötött sor függőben van (`pending_units`).

## 5. Számlálás — három külön szám

Minden részre külön: **beszélgetés** (a felosztás egysége a csoport, de a darabszám beszélgetés), **üzenet** (2 / váltás), **minta** (assistant-fordulónként egy; első fordulós = beszélgetésenként 1, előzmény-függő = a többi). Terv: 800/100/100 beszélgetés ≈ 3750/470/470 minta; a tényleges érték a beszélgetések hosszától függ.

## 6. Korlátok

* A csoportok az MT-3 **szöveges** hasonlóságán és a deklarált kapcsolatokon alapulnak: a jelentésben azonos, de szövegben eltérő beszélgetések (a kísérleti heurisztikán kívül) külön csoportba, így külön részbe kerülhetnek.
* A részek közötti információ-szintű átfedések nem kötnek csoportot: listázva vannak, de a kijelölés nem próbálja minimalizálni őket.
* A rétegzés legjobb szándékú lokális keresés (azonos méretű egységek cseréje): kis mintán vagy sok nagy csoportnál a részek összetétele eltérhet az arányostól; a csoport-integritás előbbre való.
* Egy blokkolt rekord az egész csoportját visszatartja; sok blokkolt rekordnál a kijelölhető darabszám jelentősen csökkenhet (ilyenkor a cél arányosan skálázott, és a jelentés jelzi).
* A TE-1 kizárt sorok tartalma a hasonlósági összevetés referenciájából hiányzik; az MT-2 csak azonosító-ütközést vizsgál.
* A kijelölés technikai előkészítés: nem tartalmi ellenőrzés és nem training-ready.

## 7. Használat és kilépési kódok

```bash
python tools/multiturn_split.py --mode dataset --conversations <f1.jsonl> [<f2.jsonl> ...] --mt3-report <dedupe_report.json> --out-dir <mappa> [--te1-export <TE-1 futás-mappa>] [--exclusions <lista>] [--targets 800,100,100] [--seed <szöveg>]
python tools/multiturn_split.py --verify-manifest <split_manifest.json>
```

Kizárási lista: soronként `azonosító | ok | szükséges felülvizsgálat` (mint a TE-1-nél), csak pontos azonosító; ismeretlen vagy duplikált azonosító hiba.

`0` kész, teljes és pontos; `1` kész, de figyelmet kér (visszatartott rekord, eltérés a célszámtól, teljesületlen „nehéz” minimum, döntési szintű részek közötti páros, TE-1 összevetés nélküli MT-3 jelentés); `2` argumentumhiba; `10` bemeneti fájl hiba; `11` nem turns-validált rekord; `12` TE-1 export hiba; `13` kizárási lista hiba; `14` kimeneti útvonal hiba; `15` elavult/nem egyező MT-3 jelentés vagy megváltozott bemenet/kimenet; `16` a bemenet a futás közben megváltozott; `17` a belső ellenőrzés hibát talált; `18` a manifest újraszámolással nem reprodukálható.
