# MT-6 harmadik batch (claude_multiturn_0101_0150) — bizonyítékok

Ez a mappa a 7. csomag (`multiturn`) harmadik, valódi, datasetbe szánt 50 beszélgetésének (`multiturn_0101`–`0150`)
technikai ellenőrzési láncát és az AI-alapú felülvizsgálat naplóját tartalmazza, a kombinált 150 beszélgetésre is.
A célértékeket a szövegírás előtt, külön commitban rögzítettem (`b54ca82`, a terv 7/b szakasza).

| Fájl | Mi ez |
|---|---|
| `review_log.md` | rekordszintű AI-felülvizsgálati napló (3 kör, minden rekord eredménye és a javítás) — **AI-alapú, nem független/emberi audit** |
| `mt1_validate_batch3only_report.json` | MT-1: csak a `0101–0150`, 50/50 turns-validált, 0 hibás, 49 figyelmeztetés |
| `mt1_validate_combined150_report.json` | MT-1: mindhárom clean fájl (a kombinált 150), 0 hibás, 5 + 13 + 49 = 67 figyelmeztetés |
| `mt3_dedupe_combined150_report.json` | MT-3 (`full150_v1`): a kombinált 150 + a friss TE-1 export ellen, **0 találat**, 0 blokkolt rekord, 4 csoport (a 4 deklarált pár) |
| `mt2_split_trial_manifest.json` | MT-2 **próbafelosztás** (120/15/15), nem a végleges 800/100/100 és nem jóváhagyott |
| `mt4_export_trial_manifest.json` | MT-4 export manifest (`data_kind: dataset`, `fixture: false`, R1 + R2) a próbafelosztásra |
| `mt5_dryrun_trial_report.json` | MT-5 száraz futás (`--dry-run`), R2 elsődleges, R1 összehasonlító; tanítás nem történt |
| `te1_export_fresh_manifest.json` | a friss TE-1 export manifestje (4500 beolvasva, 6 kizárva, 4494 exportálva) |

## A friss TE-1 export

A TE-1 eszköz csak `clean` nevű mappából exportál és minden `data/clean/*.jsonl` fájlt beolvas; a `data/clean`
mappa mostanra a többfordulós fájlokat is tartalmazza, amelyeket a TE-1 exportba nem szabad belekeverni (egyfordulós
export). Ezért az export bemenete a `data/clean` egyfordulós (nem `multiturn`) fájljainak **bájt-azonos másolata**
egy `clean` nevű ideiglenes mappában (49 fájl), az eszköz változatlan, a hat kizárás érvényben (`0220 0602 0829 0849 0864 0898`).
Az eredmény `export_20261004_fresh`: a `train_candidates.jsonl` sha256-ja **megegyezik** a korábbi
(`export_20260930T143131Z`) exportéval, vagyis az 1–6. csomag clean adata nem változott. Az export mappái
(`data/train/…`) a projekt szabálya szerint nem verziókövetettek.

## Hosszúsági és szótár-adatok (MT-5, kombinált 150, trial split)

* Szótár: 83 megfigyelt karakter (+UNK+PAD = 85), **kizárólag a train/R2 mintákból**.
* Ismeretlen (train-szótáron kívüli) karakter: 15 előfordulás, **kizárólag a validation részben** (R2: 9, R1: 6), a `0` és `1` számjegy
  miatt. Forrás: a korábbi `multiturn_0014` „1830-tól … 1848-ig” szövege, amely a próbafelosztásban a validation részbe
  került; az új batch szövegében **nincs számjegy**. A szótárat nem bővítettem a validation/test adatából.
* Minta-hossz (karakter): train R2 130–2840 (átlag 653, medián 581), train R1 130–745 (átlag 360); validation R2 150–1559, R1 150–546; test R2 146–1950, R1 146–594.
* A minták **100%-a** (minden részben, R1-ben és R2-ben is) meghaladja a jelenlegi betanított modell 64 karakteres kontextusát; **nem rövidítettem** a beszélgetéseket ehhez.
* Visszatartott (hosszkorlát fölötti) minta: 0; előrefutási hiba: 0.
* R2: 564 + 73 + 66 minta 100% veszteségmentes; R1: 226 + 28 + 23 veszteségmentes (a csonkolás miatti, dokumentált különbség).

`split_approved`, `content_verified`, `training_ready`: **változatlanul `false`** minden jelentésben.
