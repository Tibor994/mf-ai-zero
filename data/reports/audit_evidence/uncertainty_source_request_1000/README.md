# Audit-bizonyítékok — `uncertainty_source_request` 1000 soros csomag (2. audit-kör)

Ez a mappa **bizonyíték, nem eszköz**: a `tools/` könyvtár és a repó validátorai/küszöbei változatlanok, ezek a szkriptek nem a projekt eszközei. A szkriptek a session scratchpad-jéből lettek átmásolva, **változtatás nélkül** (sha256 lent).

## Tartalom

| Fájl | Mit tartalmaz |
|---|---|
| `code/dd_full.py` | a teljes korpuszos, szakaszolt, újraindítható duplikáció-ellenőrzés (a végleges futás ezzel készült) |
| `code/dd_verify.py` | ekvivalencia-teszt: eredeti `find_duplicates()` vs. elő-szűrt módszer, 71 soros részhalmazon, 0,9 és 0,8 küszöbön |
| `code/dd_crosscheck.py` | ekvivalencia-teszt: eredeti `find_duplicates()` 1500 soron (simple_qa + step_by_step + deepseek) |
| `code/audit_pkg.py` | a csomag-audit szakaszai (szerkezet, stílus, 5 mezős hasonlósági párkeresés belső/külső) |
| `data_version.txt` | a végleges futás adatverziója: szülő commit, fájlonkénti sha256 és sorszám |
| `results/dd_full_final_report.txt`, `results/dd_full_final_run.log` | a végleges futás kimenete |
| `results/flagged_123_ids.json`, `results/flagged_123_rows_text.txt` | a 0001–0700 batchek kulcsszavas, nem hard sorai (123 azonosító) és szövegük az átnézéskor |
| `row_changes_sources.json` | a forrás-igazítás sorai: régi és új `output` |
| `contrast_125_table.md` | a 125 kontraszt-sor soronkénti, kizáró forrás-besorolása |
| `training_exclusion_pending_review.txt` | a felülvizsgálatig a tanítási halmazból kizárandó sorok |

## Reprodukálás

A szkriptek a `REPO` útvonalat (`C:\Users\Lenovo\OneDrive\Dokumentumok\MF-AI-Zero`) kódolva tartalmazzák, és a részeredményeket a **szkript melletti** `dd_parts/` könyvtárba írják, ezért a repón kívüli másolatból futtasd (különben a repóban jönne létre `dd_parts/`):

```bash
mkdir -p /tmp/ddrun && cp code/dd_full.py /tmp/ddrun/ && cd /tmp/ddrun
PYTHONIOENCODING=utf-8 PYTHONUTF8=1 python dd_full.py run 200     # 4500 sor, 23 chunk, ~30 mp / 8 mag
PYTHONIOENCODING=utf-8 PYTHONUTF8=1 python dd_full.py report
```

Az adatverziót a `data_version.txt` rögzíti (a futás a v1.13.15 fix commit (24094fd) tartalmán történt; a fájlok sha256-ja ott van). Az ekvivalencia-tesztek (`dd_verify.py`, `dd_crosscheck.py`) a v1.13.14-es (72b0130) adaton futottak; a 1500 soros részhalmaz (simple_qa, step_by_step, deepseek fájlok) a fix commitban **nem változott**, a 71 soros minta fix seedű (`20260925`), és 60 véletlen sora között lehetett uncertainty-sor is (ezek a fix commit előtti szövegen futottak).

## Mezők, normalizálás, összehasonlítás (a `tools/dataset_dedupe.py` viselkedésének másolata)

* **Feladat-mező:** `instruction.strip() + " || " + input.strip()` (üres input esetén is a ` || ` elválasztóval; ha a teljes szöveg üres, kihagyva). **Kimenet-mező:** `output.strip()`. **Azonosító:** `id` egyezés. Más normalizálás nincs (nincs kisbetűsítés, nincs írásjel-eltávolítás), a `.strip()` kivételével.
* **Hasonlóság:** `difflib.SequenceMatcher(None, kesobbi, korabbi).ratio()` (`autojunk` alapérték). A sorok a fájlnév szerinti ábécésorrendben, fájlon belül sorrendben vannak; minden sort az **összes korábbival** hasonlít.
* **Küszöb:** találat, ha `ratio >= 0.9` (nagyobb-egyenlő, a toolban is). Az elő-szűrők kizáró feltétele szigorúan `< 0.9`, tehát pontosan a küszöbön lévő pár (pl. `step_by_step_0229 ↔ 0227` = 0,9000) nem szűrhető ki, és találatként szerepel.
* **A tool „első találat soronként” jelentést ad**, a `dd_full.py` **minden** ≥ 0,9 párt listáz; ezért a szkript 7 párt ad, a 1500 soros eredeti tool 6-ot (a `0859 ↔ 0857` pár a `0859 ↔ 0851` mögött másodikként szerepel).

## Miért nem hagyhat ki az elő-szűrés küszöböt elérő párt

Legyen `M` a `SequenceMatcher` által talált egyező karakterek száma, `la`, `lb` a hosszak. `ratio = 2M/(la+lb)`.

1. **Hossz-szűrő.** Az egyező karakterek közös részsorozatot alkotnak, ezért `M ≤ min(la, lb)`, így `ratio ≤ 2·min(la,lb)/(la+lb)`. Ha ez `< 0,9`, a `ratio < 0,9` is.
2. **Karakter-multiset szűrő.** Egy közös részsorozat minden karaktere mindkét sztringben szerepel, legalább annyiszor, ahányszor a részsorozatban, tehát `M ≤ Σ min(Ca[c], Cb[c])` (a két `Counter` metszetének összege). Ha `2·Σ/(la+lb) < 0,9`, akkor `ratio < 0,9`.
3. **`autojunk`** csak csökkentheti az egyezések számát (egyes gyakori karaktereket kihagy a keresésből), tehát a valós `ratio` legfeljebb kisebb, mint a fenti korlátok; a korlátok tehát a toolban használt `SequenceMatcher` esetén is érvényesek.
4. **Lebegőpontos pontosság.** A szűrő és a `ratio()` ugyanazt a `2.0*x/(la+lb)` alakú kifejezést használja, és a hányados monoton az `x`-ben, ezért a `M ≤ x` egyenlőtlenségből a lebegőpontos érték is `≤`.

Az elő-szűrt ágon csak a valódi `SequenceMatcher(None, kesobbi, korabbi).ratio() >= 0.9` dönt, a szűrők csak a *biztosan* küszöb alatti párokat hagyják ki. (Számok a végleges futásból: 2 mező × 10 122 750 pár = 20 245 500 összehasonlítás; a hossz-szűrő után 4 016 754 maradt, a multiset-szűrő után **2769** pár jutott a valódi `difflib` számításig.)

## Teszteredmények (az algoritmus-ekvivalencia érvétől külön)

Ezek **empirikus egyezések**, nem bizonyítékok az algoritmus-ekvivalenciára:

* `dd_crosscheck.py`: az eredeti `find_duplicates()` 1500 soron (simple_qa + step_by_step + deepseek) 2333 mp alatt ugyanazt a 6 első-találat párt adta (0,900–0,921), 0 output-találattal és 0 id-egyezéssel, mint a szakaszolt módszer.
* `dd_verify.py`: 71 soros részhalmazon (a 11 ismert soron + 60 véletlen soron) 0,9 és 0,8 küszöbön is azonos találathalmaz (0,9: task 6 / output 0; 0,8: task 8 / output 0).

## `audit_pkg.py` megjegyzés

A `pair_ratio()` függvény kihagyja a 6 karakternél rövidebb sztringeket. A végleges korpuszban a legrövidebb feladat-szöveg (`instruction || input`) 14, a legrövidebb `output` 30 karakter, ezért az `instruction||input` és `output~output` vizsgálatoknál ez a szűrő soha nem lépett életbe (a `dd_full.py`-ban nincs ilyen szűrő). A zajos (`instruction~input`, `output~input`) összevetéseknél a szűrő üres `input` esetén érvényes, ott a találat definíció szerint nincs.
