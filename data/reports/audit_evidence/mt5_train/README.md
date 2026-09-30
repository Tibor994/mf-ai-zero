# MT-5 bizonyítékok (nem eszköz, nem adat)

Ez a mappa **bizonyíték**: nem része a projekt eszközeinek és nem tanítóadat. A benchmark 1000 **mesterséges**
beszélgetést használ: a `tests/test_multiturn_split.py` generátorával, valós magyar szavakból összeállított
**értelmetlen mondatokat**, `mtfx_syn_NNNN` azonosítóval, `meta.fixture: true`; az 1000 beszélgetéses csomagba
**nem számítanak**, tanításra nem használhatók, valódi többfordulós adat továbbra sincs. A száraz futás
`fixture_` előtagú mappába kerül. A valódi adatot (`data/clean`, a TE-1 export) a mérés csak olvassa.

| Fájl | Mi ez |
|---|---|
| `benchmark_train.py` | a méréshez használt szkript: 1000 mesterséges beszélgetés → MT-3 (a valódi TE-1 exporttal szemben) → MT-2 → MT-4 → **MT-5 száraz futás**; méri az időket, a szótárat, a hossz-/erőforrás-statisztikákat, az ismételhetőséget, a visszaolvasásos önellenőrzést, egy kisebb `--max-chars` melletti visszatartást és a felsőbb export érintetlenségét. A `REPO` útvonal a szerző gépére van rögzítve. Használat: `python benchmark_train.py <eredmény.json> [n=1000]` |
| `bench_result_1000.json` | a mérés teljes eredménye (lásd alább a legfontosabb számokat) |
| `bench_run.log` | a mérés futásának nyers kimenete |
| `mutation_results.txt` | a mutációs vizsgálat eredménye (az MT-5 mutánsok; a végleges állapot: 75 mutánsból 74 elbukik, 1 indokolt, dokumentált ekvivalens túlélő) |

## A benchmark legfontosabb számai (1000 mesterséges beszélgetés)

- Teljes csővezeték: TE-1 export 0,64 mp, MT-3 186,75 mp, MT-2 12,92 mp, MT-4 27,81 mp, **MT-5 száraz futás 158,45 mp**.
- Szótár: 68 megfigyelt karakter (+UNK +PAD = 70), kizárólag a train/R2 mintákból.
- Alapértelmezett `--max-chars 4096` mellett: 0 visszatartott, 0 ismeretlen karakter, 0 előrefutási hiba, 0 figyelmeztetés.
- Megismételt futás **bájtra azonos** jelentést adott (`mt5_repeat_deterministic: true`); a visszaolvasásos önellenőrzés tiszta (`mt5_verify_report: []`); az MT-4 export fájljai a MT-5 futás után is érintetlenek (`mt4_export_untouched: true`).
- Kisebb `--max-chars` (641, a hosszak 70. percentilise) mellett 3178 minta lett **jelentve visszatartva** (nem csendben csonkítva).

### Kiemelt korlát: a jelenlegi betanított modell kontextushossza

`samples_over_trained_context_pct` = **100,0%** MINDEN felosztásban ÉS MINDKÉT módban (R2 és R1 is) - vagyis
ezen a méreten (1000 beszélgetés) EGYETLEN egy minta bemenete sem fér bele a jelenlegi modell tanított
kontextusába (`config.seq_length = 64` karakter); még a legrövidebb, futásidő-hű (R1) minták is legalább 160
karakter hosszúak. Az előrefutási próba mindegyik kötegen technikailag "sikeres" volt (0 hiba) - de ez egy
FRISS, TANÍTATLAN próba-modellel történt, aminek az LSTM-architektúrája nem korlátozza keményen a bemenet
hosszát; ez **nem** bizonyítja, hogy a valódi, betanított ellenőrzőpont ilyen hosszon jó minőségű választ adna.
Ez a betöltőtől független, a modell architektúrájával/tanításával összefüggő KOMPATIBILITÁSI korlát, amit a
tényleges tanítás megkezdése előtt külön kell kezelni (lásd a fő MT-5 jelentést).

A mutációs vizsgálat az eszköz teljes forrására készült mutánsokat mutatja: minden mutáns egy szándékosan
elrontott szabály (célmaszk-illesztés, szótárépítés, kódolás, kötegelés, előrefutási próba, hossz-/
visszatartás-jelentés, figyelmeztetések, visszaolvasásos önellenőrzés, kimeneti mappa-védelem, parancssor). A
szeleteket egy folyamat-állapotra váró (a héj saját `timeout` parancsával korlátozott) vezérlő futtatta - a
naplók szövege sosem volt várakozási feltétel.
