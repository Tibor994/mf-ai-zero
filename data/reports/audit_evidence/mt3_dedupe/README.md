# MT-3 bizonyítékok (nem eszköz, nem adat)

Ez a mappa **bizonyíték**: nem része a projekt eszközeinek és nem tanítóadat. Minden itt szereplő beszélgetés **mesterséges**, a tesztfixture-ökből (`tests/fixtures/multiturn/`) átalakított vagy szintetikusan generált; `mtfx_` azonosítójú, `meta.fixture: true`, az 1000 beszélgetéses csomagba **nem számít bele**, tanításra nem használható.

**Verziók:** a mappa fájljai két eszközverzióhoz tartoznak. Az **mt3-2.0** (a felhasználó döntései szerint revideált eszköz) fájljai: `benchmark_results_1000_mt3v2.json`, `benchmark_results_1000_mt3v1_same_session.json` (kontroll: az mt3-1.0 ugyanabban a munkamenetben mérve), `mutation_results_mt3_v2.txt`, `demo_scenarios.jsonl`, `demo_scenarios_report.json`, `fixtures_vs_real_export_report.json`. Az **mt3-1.0** (a revízió előtti eszköz) fájljai: `benchmark_results_1000.json`, `mutation_results.txt`.

| Fájl | Mi ez |
|---|---|
| `benchmark_synthetic.py` | a méréshez használt szintetikus terhelés-generátor és időmérő. A valódi TE-1 exportból (csak olvasva) és véletlen szó-cserékből épít ~1000 beszélgetést; a `multiturn_dedupe.run_dedupe` belső API-ját hívja (a parancssori eszköz mindig MT-1-validált bemenetet kér), ezért a szintetikus beszélgetések nem MT-1-validáltak. Beültetett esetek: 10 pontos másolat, 10 normalizálás utáni másolat, 10 közeli változat (3-5% szócsere), 10 átfogalmazás-szerű változat (35% szócsere), 10 exportált példával azonos első forduló. A `--names` kapcsoló a kiegészítő névsemleges menetet is futtatja. A `REPO` útvonal a szerző gépére van rögzítve. Használat: `python benchmark_synthetic.py <TE-1 futás-mappa> <eredmény.json> 1000 [--equivalence] [--names]` |
| `benchmark_results_1000_mt3v2.json` | az mt3-2.0 mérése (`--names`): futásidők fázisonként, számlálók (összehasonlított/kiszűrt/teljesen összevetett párok, a névsemleges menet külön), találatok típusonként, beültetett esetek felismerése |
| `benchmark_results_1000_mt3v1_same_session.json` | ugyanez az mt3-1.0 eszközzel (a `d252935` commit állapota), ugyanazon a gépen egymás után mérve: 89,0 mp (az mt3-2.0: 97,9 mp, +10%) |
| `benchmark_results_1000.json` | az mt3-1.0 első mérése (60,1 mp; más géphelyzetben készült, az mt3-2.0-val nem összehasonlítható) |
| `mutation_results_mt3_v2.txt` | az mt3-2.0 mutációs vizsgálata: 82 mutáns, mind elbukik (első futás 77/81, a 4 túlélő miatt 4 új teszt) |
| `mutation_results.txt` | az mt3-1.0 mutációs vizsgálata (46 mutáns) |
| `demo_scenarios.jsonl` | 15 mesterséges bemutató-beszélgetés (pontos másolat, névcserés másolat, átfogalmazás, lánc, szerepcsere, közös köszönés, azonos kérdés eltérő előzménnyel, névlistás pár, deklarált változat) |
| `demo_scenarios_report.json` | ezek mt3-2.0 jelentése a valódi TE-1 exporttal összevetve (a jelentés formátumának bemutatása: reject/review/info találatok, csoportok, rekordállapotok). A TE-1 export útvonala a szerző ideiglenes mappájára mutat, ezért a `--verify-report` ezen a fájlon nem futtatható újra |
| `fixtures_vs_real_export_report.json` | az 5 tesztfixture és a valódi TE-1 export (4494 példa) összevetése: 0 találat, 0 blokkolt rekord |

A `--verify-report` a jelentésekben rögzített bemeneti ellenőrzőösszegeket ellenőrzi újra. A jelentések `tool_sha256` mezője az MT-3 eszköz futáskori fájljának ellenőrzőösszege.
