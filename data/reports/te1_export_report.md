# TE-1 — kizárás-érvényesítő, visszakövethető clean-export

Dátum: 2026-09-25. Eszköz: `tools/dataset_export_train.py` (te1-1.0). Tesztek: `tests/test_te1_dataset_export.py`. Bizonyíték: `audit_evidence/te1_export/manifest_real_run_1.json`.

**Az export NEM tartalmi ellenőrzés és NEM training-ready állapot.** Azt igazolja, hogy a kizárási lista érvényesült, és hogy az exportált adat forrásfájlokig, azonosítókig és darabszámokig visszakövethető.

## Mit tesz és mit nem

| Követelmény | Megoldás |
|---|---|
| Olvassa és ténylegesen érvényesítse a listát | a lista minden bejegyzése pontosan egy clean sorra kell mutasson; a kimenetből lemezről visszaolvasva ellenőrzi, hogy nincs benne kizárt azonosító |
| A kizárt sorokat ne törölje | csak olvassa a clean fájlokat; a forrásfájlok sha256-ját a futás előtt és után is összeveti (eltérés → hiba); a kimenet kizárólag új futás-mappába kerül, védett `data/clean|raw|rejected|inbox` és a bemeneti mappa alá nem írhat, meglévő futás-mappát nem ír felül |
| Hiányzó/hibás lista, nem egyértelmű azonosító → hiba | 10-es kilépési kód és magyar hibaüzenet: lista hiányzik / nem olvasható / üres / hibás formátumú sor / üres mező / wildcard, előtag, tartomány, nagybetű, szóköz az azonosítóban / duplikált azonosító / azonosító nincs a clean sorok között / azonosító több sorban szerepel |
| A hibás beállítás ne kerülhető meg észrevétlenül | nincs kizárás-kikapcsoló kapcsoló; **kétirányú konzisztencia:** ha egy clean sor `quality_notes` mezője kizárás-jelölést („a tanítási halmazból kizárandó”) hordoz, de az azonosítója nincs a listán, az export megáll (így egy bejegyzés kivétele vagy az üres lista sem oldja fel a kizárást); az üres listához kifejezett `--allow-empty-exclusions` kell, és az a jelölés-ellenőrzést sem kerüli meg |
| Visszakövethető export | `manifest.json`: forrásfájlok (elérési út, sha256, bájt, CRLF-sorok, beolvasott/exportált/kizárt sorok), a lista sha256-ja és bejegyzései, a kizárt sorok fájl+sor+sor-sha256, darabszámok kategóriánként, ellenőrzések, git commit, figyelmeztetések; `export_index.tsv`: azonosító, forrásfájl, forrássor, sor-sha256; `train_candidates.jsonl`: az engedélyezett sorok **bájt-hűen** |
| Ne állítson többet | a manifest `content_verified: false`, `training_ready: false`, és `scope_disclaimer` mezőt tartalmaz; a parancssori kimenet is kiírja |

Nem csinál: nem tanít; nem érinti a `src/` tanító- és chat kódját; nem konvertál chat-szöveggé (TE-2); nem olvas raw/rejected mappát.

## Használat

```bash
python tools/dataset_export_train.py --out-dir data/train/te1_export
```

Kilépési kódok: 0 sikeres; 2 argumentumhiba; 10 kizárási lista hiba; 11 forrásadat-hiba; 12 kimeneti ellenőrzés sikertelen; 13 kimeneti útvonal hiba. Hiba után nem marad érvényesnek látszó export: a kimeneti ellenőrzés hibája `.partial` fájlokat és `FAILED.txt`-t hagy, manifest nélkül (a hiányzó manifest = érvénytelen export); a lista- és forráshibák előtt semmilyen futás-mappa nem jön létre.

## Ellenőrzések

**1) Egységtesztek** — `python -m unittest tests.test_te1_dataset_export`: **35 teszt, OK** (`-W error::ResourceWarning` mellett is). Fő területek:
* boldog út: a kizárt sorok kimaradnak, az engedélyezettek megmaradnak és bájt-hűek (CRLF forrásnál is), a források bájtra azonosak, a kizárt sor a clean fájlban megvan; a manifest tartalma (sorok, sha256, kategóriák);
* lista-hibák: hiányzó, üres (jelölés nélküli corpuszon is), hibás sorok (5 változat), nem szabályos azonosítók (7 változat), duplikált, elgépelt, több sorban szereplő, kivett bejegyzés (jelölt sor a listán kívül), az üres-lista kapcsoló nem kerüli meg a jelölés-ellenőrzést;
* forrás/útvonal: nem-clean mappa, hibás JSON sor (fájl:sor a hibaüzenetben), duplikált azonosító, védett kimeneti mappák, felülírás, érvénytelen futásnév;
* kimeneti ellenőrzés: kizárt sor szivárgása (kiegyenlített és nem kiegyenlített darabszámmal), szűretlen export, futás közben módosuló forrás, a kimeneti sor és a forrás eltérése — mindegyiknél `VerificationError`, `FAILED.txt`, manifest és végleges export nélkül;
* parancssor: kilépési kódok, és hogy `--no-exclusions`, `--skip-exclusions`, `--ignore-exclusions` ismeretlen kapcsoló;
* **valós adat** (csak olvasás): pontosan a hat kizárt sor marad ki (4500 → 6 + 4494), az engedélyezett azonosítók halmaza pontosan az összes azonosító mínusz a hat, a 49 clean fájl sha256-ja a futás előtt és után azonos, a hat sor a clean fájlokban megvan, egy kivett bejegyzésű lista, egy üres lista (kapcsolóval is) és egy elgépelt azonosítójú lista hibával megáll, a tényleges lista pontosan a hat azonosítót tartalmazza (a teszt rögzíti; a lista szándékos módosításakor a tesztet is tudatosan frissíteni kell).

**2) Mutációs vizsgálat** (a tesztek erejére): 11 szándékos hibamutánsból (szűrés kikapcsolva, jelölés-ellenőrzés ki, nem létező azonosító nem hiba, kimeneti szivárgás-/index-ellenőrzés ki, üres lista engedett, duplikált azonosító engedett, forrás-változás nem ellenőrzött, nem-clean mappa engedett, szabálytalan azonosító engedett, futás-mappa felülírható) **9-et a tesztek elbuktatnak**; **2 mutáns túlélt**, mert a védelem más rétegen is fennáll (a kimeneti szivárgás-ellenőrzés akkor is elbukik az indexen és a darabszámon; a szabálytalan azonosító a clean sorokban való kereséskor hibázik). Mindkettő védelmi redundancia, nem hiányzó védelem; a párhuzamos kikapcsolásuk (kimenet+index) elbukik.

**3) Valós futás** (`manifest_real_run_1.json`): 49 clean fájl, **4500 sor beolvasva, 6 kizárva, 4494 exportálva**; kategóriánként: explanation 1000, noisy_input 500, simple_qa 1000, step_by_step 500, summary 500, uncertainty_source_request 994 (6 kizárva). Kizárva: `uncertainty_source_request_0220` (`…0201_0300…:20`), `0829` (`…0801_0900…:29`), `0849` (`:49`), `0864` (`:64`), `0602` (`…0601_0700…:2`), `0898` (`…0801_0900…:98`). Ellenőrzések mind igazak, figyelmeztetés nincs; független (a szkripttől külön írt) összevetés: az export pontosan a forrássorok mínusz a hat sor (4494 = 4494).

**4) Regresszió:** `python -m unittest tests.test_v1_7_4_dataset_foundation` — minden teszt sikeres, STÁTUSZ: STABIL. A meglévő eszközök, a tanító és a chat kód nem módosultak (csak két új fájl jött létre).

## Korlátok

* A manifest `git_commit` mezője a futás idején érvényes HEAD; a sor-szintű `row_sha256` platformfüggetlen, a fájl-szintű sha256 viszont a sorvégektől (LF/CRLF) függ (a clean fájlok egy része a munkakönyvtárban CRLF sorvégű).
* Az export egyfordulós (9 mezős) sorokra készült; a többfordulós `turns` formátum ellenőrzése külön feladat (MT-1…MT-4), lásd a `multiturn_package7_plan.md` 8. szakaszát.
* A jelenlegi `train_chat.py` nem olvassa az exportot: a TE-2 (tanítószöveg-konverzió) hiányzik, ezért a tanítás továbbra sem indítható.
* Az export tartalmi helyességet nem állít: a nyitott tartalmi tételek a 6. csomag jelentéseiben követhetők.
