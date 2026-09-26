# MT-3 bizonyítékok (nem eszköz, nem adat)

Ez a mappa **bizonyíték**: nem része a projekt eszközeinek és nem tanítóadat. Minden itt szereplő beszélgetés **mesterséges**, a tesztfixture-ökből (`tests/fixtures/multiturn/`) átalakított vagy szintetikusan generált; `mtfx_` azonosítójú, `meta.fixture: true`, az 1000 beszélgetéses csomagba **nem számít bele**, tanításra nem használható.

| Fájl | Mi ez |
|---|---|
| `benchmark_synthetic.py` | a méréshez használt szintetikus terhelés-generátor és időmérő. A valódi TE-1 exportból (csak olvasva) és véletlen szó-cserékből épít ~1000 beszélgetést; a `multiturn_dedupe.run_dedupe` belső API-ját hívja (a parancssori eszköz mindig MT-1-validált bemenetet kér), ezért a szintetikus beszélgetések nem MT-1-validáltak. Beültetett esetek: 10 pontos másolat, 10 normalizálás utáni másolat, 10 közeli változat (3-5% szócsere), 10 átfogalmazás-szerű változat (35% szócsere), 10 exportált példával azonos első forduló. A `REPO` útvonal a szerző gépére van rögzítve. Használat: `python benchmark_synthetic.py <TE-1 futás-mappa> <eredmény.json> 1000 --equivalence` |
| `benchmark_results_1000.json` | a mérés eredménye: futásidők fázisonként, számlálók (összehasonlított/kiszűrt/teljesen összevetett párok), találatok típusonként, beültetett esetek felismerése, az előszűrt és a teljes összehasonlítás egyezése |
| `mutation_results.txt` | a mutációs vizsgálat eredménye (46 mutáns, mind elbukik a tesztekkel) |
| `demo_scenarios.jsonl` | 12 mesterséges bemutató-beszélgetés (pontos másolat, névcserés másolat, átfogalmazás, lánc, szerepcsere, közös köszönés, azonos kérdés eltérő előzménnyel) |
| `demo_scenarios_report.json` | ezek MT-3 jelentése a valódi TE-1 exporttal összevetve (a jelentés formátumának bemutatása: 22 találat, csoportok, rekordállapotok). A TE-1 export útvonala a szerző ideiglenes mappájára mutat, ezért a `--verify-report` ezen a fájlon nem futtatható újra |
| `fixtures_vs_real_export_report.json` | az 5 tesztfixture és a valódi TE-1 export (4494 példa) összevetése: 0 találat, 0 blokkolt rekord |

A `--verify-report` a jelentésekben rögzített bemeneti ellenőrzőösszegeket ellenőrzi újra. Az itt tárolt jelentések git commitja a futáskor érvényes HEAD (`068e1b5`), a `tools/multiturn_dedupe.py` ekkor még nem volt commitolva.
