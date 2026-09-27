# MT-4 bizonyítékok (nem eszköz, nem adat)

Ez a mappa **bizonyíték**: nem része a projekt eszközeinek és nem tanítóadat. Minden itt szereplő beszélgetés **mesterséges**: a `tests/test_multiturn_split.py` generátorával, valós magyar szavakból (`tests/fixtures/multiturn/synthetic_vocabulary.txt`) összeállított **értelmetlen mondatok**, `mtfx_syn_NNNN` azonosítóval, `meta.fixture: true`; az 1000 beszélgetéses csomagba **nem számítanak**, tanításra nem használhatók, valódi többfordulós adat továbbra sincs. Az export ezért `fixture_` előtagú mappába, jelölő fájllal és `training_data: false` jelöléssel készült. A valódi adatot (`data/clean`, a TE-1 export) a mérés csak olvassa.

| Fájl | Mi ez |
|---|---|
| `benchmark_export.py` | a méréshez használt szkript: 1000 mesterséges beszélgetés (tervezett változat-csoportokkal, persona-hármasokkal) → MT-3 a valódi 4494 példás TE-1 exporttal szemben → MT-2 → **MT-4**; méri az időket, a részenkénti darabszámokat (beszélgetés, üzenet, minta módonként), a veszteség-jelöléseket, az ismételhetőséget és a felsőbb fájlok érintetlenségét. A `REPO` útvonal a szerző gépére van rögzítve. Használat: `python benchmark_export.py <eredmény.json> [n] [--blocked]` |
| `benchmark_results_1000.json` | a mérés eredménye (tiszta 1000 beszélgetés): export 800/100/100, R1 és R2 mintaszámok, csonkolás és nem ábrázolható előzmény-függés az R1-ben, a kimeneti fájlok mérete, visszaolvasás, második export bájtra azonos, felsőbb fájlok érintetlenek |
| `benchmark_results_1000_blocked.json` | ugyanez 12 beültetett blokkolt másolattal (és azok persona-társaival) és 6 kizárási listás beszélgetéssel: az MT-2 970 beszélgetést jelöl ki, az export pontosan azokat tartalmazza, a visszatartottak egyike sincs benne |
| `mutation_results.txt` | a mutációs vizsgálat eredménye (az MT-4 mutánsok; mind elbukik a tesztekkel) |

A mutációs vizsgálat az eszköz teljes forrására készült mutánsokat mutatja: minden mutáns egy szándékosan elrontott szabály (renderelés, szegmens-határok, bemenet- és elavultság-ellenőrzés, kizárások, tesztadat-védelem, kiírás, státuszok, visszaolvasás). A szeleteket egy folyamat-állapotra váró vezérlő futtatta (a naplók szövege nem várakozási feltétel).
