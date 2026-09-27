# MT-2 bizonyítékok (nem eszköz, nem adat)

Ez a mappa **bizonyíték**: nem része a projekt eszközeinek és nem tanítóadat. Minden itt szereplő beszélgetés **mesterséges**: a `tests/test_multiturn_split.py` generátorával, valós magyar szavakból (`tests/fixtures/multiturn/synthetic_vocabulary.txt`) összeállított **értelmetlen mondatok**, `mtfx_syn_NNNN` azonosítóval, `meta.fixture: true`; az 1000 beszélgetéses csomagba **nem számítanak**, tanításra nem használhatók, valódi többfordulós adat továbbra sincs. A valódi adatot (`data/clean`, a TE-1 export) a mérés csak olvassa.

| Fájl | Mi ez |
|---|---|
| `benchmark_split.py` | a méréshez használt szkript: 1000 mesterséges beszélgetés (tervezett változat-csoportokkal, persona-hármasokkal) → MT-3 a valódi 4494 példás TE-1 exporttal szemben → MT-2. A `REPO` útvonal a szerző gépére van rögzítve. Használat: `python benchmark_split.py <eredmény.json> [n] [--blocked]` (a `--blocked` 12 beültetett pontos másolatot és 6 kizárt beszélgetést ad a visszatartás méréséhez) |
| `benchmark_results_1000.json` | a mérés eredménye (tiszta 1000 beszélgetés): futásidők (MT-3, MT-2), a kijelölés részenkénti darabszámai (beszélgetés, üzenet, minta), eltérés a céltól, rétegzés, független csoport-ellenőrzés, ismételhetőség és manifest-ellenőrzés |
| `benchmark_results_1000_blocked.json` | ugyanaz beültetett blokkolt másolatokkal és kizárt beszélgetésekkel: a visszatartás okai, a kijelölhető darabszám és az arányosan skálázott cél |
| `mutation_results.txt` | a mutációs vizsgálat eredménye (MT-2 mutánsok; mind elbukik a tesztekkel) |

A `mutation_results.txt` az eszköz teljes forrására készült mutánsokat mutatja: minden mutáns egy szándékosan elrontott szabály (csoport-integritás, visszatartás, az MT-3 jelentés aktualitása, darabszám-optimalizálás, rétegzés, ellenőrzés, kimenetek).
