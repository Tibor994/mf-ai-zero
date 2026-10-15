# MT-6 negyedik batch (`claude_multiturn_0151_0200`) — bizonyítékok

Ez a mappa a 7. csomag (`multiturn`) negyedik, valódi, datasetbe szánt 50 beszélgetésének (`multiturn_0151`–`0200`)
technikai ellenőrzési láncát és az AI-alapú felülvizsgálat naplóját tartalmazza, a kombinált 200 beszélgetésre is.
**Ez adat-előkészítés, nem tanítás.** A `split_approved`, `content_verified` és `training_ready` minden fájlban `false`.
A független, emberi tartalmi átolvasás nyitott, kötelező tanítás előtti feltétel.

A célértékeket a terv 7/c szakasza rögzíti (`data/reports/multiturn_package7_plan.md`, commit `69ea889`). A rögzítés sorrendi
eltérése (az F1 első szövegvázlata a célok commitja előtt a munkamappában már létezett) a `review_log.md`-ben szerepel.

| Fájl | Mi ez |
|---|---|
| `review_log.md` | rekordszintű AI-felülvizsgálati napló (4 kör + a javítás utáni lépések): az eredeti találatok, a mért javítások és a javítás utáni ellenőrzés külön oszlopban — **AI-alapú, nem független/emberi audit** |
| `composition_actual.json` | a tényleges összetétel (batch4 és kombinált 200), a célokkal való egyeztetéshez |
| `mt1_validate_batch4only_report.json` | MT-1: csak a `0151–0200`; 50/50 turns-validált, 0 hibás, 121 figyelmeztetés (mind `capitalized_token_review`) |
| `mt1_validate_combined200_report.json` | MT-1: mind a négy clean fájl; 0 hibás, 5 + 13 + 48 + 121 = 187 figyelmeztetés, mind `capitalized_token_review` |
| `mt3_dedupe_combined200_report.json` | MT-3 (`mt3-2.0`): a kombinált 200 + a friss TE-1 export ellen; **0 találat**, 0 blokkolt rekord, 195 csoport (5 deklarált pár), változat-részesedés 0,05 |
| `mt2_split_trial_manifest.json` | MT-2 **próbafelosztás** (160/20/20), nem a végleges 800/100/100 és nem jóváhagyott; 0 visszatartott, 0 szétvágott csoport, 0 részek közötti átfedés-jelzés |
| `mt4_export_trial_manifest.json` | MT-4 export manifest (`data_kind: dataset`, `fixture: false`, R1 + R2) |
| `mt5_dryrun_trial_report.json` | MT-5 száraz futás (`--dry-run`), R2 elsődleges, R1 összehasonlító; tanítás nem történt |
| `mt5_unknown_chars_by_split.json` | ismeretlen karakterek felosztásonként és módonként (független újraszámolás a minta-fájlokból) |
| `te1_export_fresh_manifest.json` | a friss TE-1 export manifestje (4500 beolvasva, 6 kizárva, 4494 exportálva) |

## A futások és a végleges adat összetartozása

A végleges clean fájl sha256-ja: `72a9d7f8e2de2768374ddb26c1ff8ebaded20a1db878b5d6f36d43a57d9f4033`
(`data/clean/claude_multiturn_0151_0200_clean.jsonl`, a `data/raw/…_raw.jsonl` bájt-azonos). A batch3 (`0101_0150`): `65cf0ff4…`,
az első kettő: `8cfe645d…`, `1f9f0e3a…`. Ellenőrzés: az MT-3, MT-2 jelentés/manifest `inputs.conversation_files[*].sha256` mezői
mind a négy aktuális fájléval egyeznek; az MT-2 manifest az MT-3 jelentés sha256-ját, az MT-4 az MT-2 manifestét, az MT-5 az
MT-4 manifestét tartalmazza, mindegyik egyezik. Ennek kedvéért a futásokat a **végleges** szövegre (a 4. kör utáni javítások után)
futtattam, az előző (el nem fogadott) futások mappáit töröltem.

A manifestekben a `git_commit` mező a futás idején érvényes HEAD-et (`69ea889…`, a célok commitja) mutatja, mert az adatfájlok
még nem voltak commitolva; az adat commitja a futások utáni. A TE-1 manifest `source_file` mezői a munkamappában lévő bájt-azonos
másolatra mutatnak (lásd lent).

Futtatási parancsok (az eszközök kódja és küszöbei változatlanok; az MT-1 → MT-3 → MT-2 → MT-4 → MT-5 sorrendben):

* MT-1: `python tools/multiturn_validate.py <clean fájl(ok)> --mode dataset --json <jelentés>`
* MT-3: `python tools/multiturn_dedupe.py --mode dataset --conversations <4 clean fájl> --out-dir data/train/multiturn_mt3 --te1-export data/train/te1_export/export_20261007_fresh --run-name full200_v1`
* MT-2: `python tools/multiturn_split.py --mode dataset --conversations <4 clean fájl> --mt3-report …/full200_v1/dedupe_report.json --out-dir data/train/multiturn_mt2 --te1-export data/train/te1_export/export_20261007_fresh --targets 160,20,20 --seed 42 --run-name full200_trial_v1`
* MT-4: `python tools/multiturn_export.py --mode dataset --mt2-manifest …/split_manifest.json --out-dir data/train/multiturn_mt4 --modes R1,R2 --run-name full200_trial_v1`
* MT-5: `python src/train_multiturn.py --export-manifest …/export_manifest.json --mode dataset --out-dir data/train/multiturn_mt5 --run-name full200_trial_v1 --dry-run --modes R2,R1`

## A friss TE-1 export

A TE-1 eszköz csak `clean` nevű mappából exportál és minden `*.jsonl` fájlt beolvas; a `data/clean` mappa mostanra a
többfordulós fájlokat is tartalmazza, amelyeket az egyfordulós exportba nem szabad belekeverni. Ezért az export bemenete a
`data/clean` egyfordulós (nem `multiturn`) fájljainak **bájt-azonos másolata** egy `clean` nevű ideiglenes mappában (49 fájl,
az ellenőrzés a futás előtt `cmp`-pel megtörtént), az eszköz és a kizárási lista változatlan. A hat kizárás érvényben:
`uncertainty_source_request_0220`, `0602`, `0829`, `0849`, `0864`, `0898`. Eredmény: `export_20261007_fresh`; 4500 beolvasva,
**6 kizárva**, 4494 exportálva; a `train_candidates.jsonl` sha256-ja (`a0fd747e…`) **azonos** a korábbi
(`export_20260930T143131Z`, `export_20261004_fresh`) exportéval, vagyis az 1–6. csomag clean adata nem változott. Az export
mappái (`data/train/…`) nem verziókövetettek.

## Szótár, ismeretlen karakterek és hosszak (MT-5, trial split, kombinált 200)

* Szótár: **102 megfigyelt karakter** (+UNK+PAD = 104), **kizárólag a train/R2 mintákból** (a korábbi 150-es futásban 83 volt;
  az új karakterek: `"` `%` `&` `+` `0` `1` `2` `6` `7` `9` `<` `=` `>` `|` `²` `×` `–` `−` `≈`).
* **Ismeretlen karakter: 0 előfordulás mind a hat részben** (train/validation/test × R2/R1), a minta-fájlokból független
  számítással és az MT-5 jelentés `unknown_char_occurrences_total = 0` értékével egyezően. A szótárat nem bővítettem
  validation/test adatból, és a tartalmat nem írtam át ismeretlen karakterek eltüntetésére.
* Törékenységi megfigyelés (nem hiba): hat karakter a train részben **egyetlen beszélgetésből** származik — `<`, `>`, `&`, `"`
  a `0177` (Excel-képletek), `²` a `0156`, `|` a `0195` (soron belüli táblázat). Ha ezek a beszélgetések a validation/test
  részbe kerültek volna, ismeretlen karakterként jelentek volna meg; a jelenlegi próbafelosztásban mind a train részben van.
* Minta-hossz (karakter, kept): train R2 130–3122 (átlag 743, medián 649), train R1 130–900 (átlag 393); validation R2 143–2453,
  R1 143–724; test R2 130–2840, R1 130–745. A minták **100%-a** (minden részben, R1-ben és R2-ben is) meghaladja a jelenlegi
  betanított modell 64 karakteres kontextusát; **nem rövidítettem** a beszélgetéseket ehhez, a kérdés nyitott.
* Visszatartott (hosszkorlát fölötti) minta: 0; előrefutási hiba: 0 (R2: 747 + 96 + 95 minta 100% veszteségmentes; R1: 266 + 31 + 33
  veszteségmentes, a többi a dokumentált csonkolás miatt tér el).
