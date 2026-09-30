# MT-5 — többfordulós tanító BETÖLTŐ (kísérleti, elkülönített) — csak betöltés és száraz futás

Modul: `src/train_multiturn.py` (mt5-1.0). Tesztek: `tests/test_train_multiturn.py`. Bemenet: egy MT-4 `export_manifest.json` és a hozzá tartozó `samples_<rész>_<mód>.jsonl` fájlok (`tools/multiturn_export.py`, mt4-1.x).

**Ez a modul NEM tanít.** Nincs optimalizáló lépés, gradiens-visszaterjesztés, paraméterfrissítés vagy betanított checkpoint mentése — a modul forrása nem is tartalmaz ilyen kódágat (a `--dry-run` kapcsoló kötelező; nincs `--train` opció). A tényleges tanítás külön feladat és külön jóváhagyás. A `split_approved`/`content_verified`/`training_ready` állapotokat a forrás-exportból veszi át változatlanul (mind `false`), és sosem állítja igazra.

**Elkülönített, kísérleti megvalósítás.** A meglévő v0.7 `train_chat.py`, a `chat.py`/`guard.py`/`router.py` stabil lánc, a `src/memory.py` (futásidejű előzmény) és a webapp/backend **nem módosul**; ezeket a modul nem is importálja. A `config.py`-t és a `model.py` `CharLSTM` osztályát csak olvassa (megosztott architektúra, nem "a tanító" maga). A `tools/` alatti MT-1..MT-4 eszközöket nem importálja: az MT-4 export érvényességét önállóan, saját (célzott, nem az MT-4 teljes logikáját megkettőző) ellenőrzéssel vizsgálja.

## 1. A három döntés a megvalósításban

| Döntés | Megvalósítás |
|---|---|
| **R2 elsődleges, R1 összehasonlító próba, R3 nincs** | mindkét mód (alapból `--modes R2,R1`) betöltődik, kódolódik, kötegelődik és előrefutási próbán megy át; a szótár kizárólag az R2 train mintákból épül (R1 ugyanezt a szótárat használja); a jelentés külön mezőben jelzi, melyik az elsődleges (`config.primary_mode`); egyik mód sikeres betöltése sem jelent jóváhagyást. R3 kérése `RefusedError` (18-as kód), a manifestben `config.unsupported_modes` is dokumentálja. |
| **Nincs véletlen ablakolás, a mintahatár megőrzött** | a meglévő `train_chat.get_batch()` a teljes szöveget összefűzi és `config.seq_length` (64) karakteres véletlen ablakokat vág ki, beszélgetéshatáron át is. Ez a modul minden mintát (MT-4 `text` mezője) egyben, a saját határain belül kódol; egy köteg-sor mindig **pontosan egy minta**, sosem két minta összefűzve. |
| **Fixture export kizárólag kifejezett tesztmódban** | a `--mode` kifejezett és egyeznie kell az export `data_kind`/`fixture` jelölésével mindkét irányban (`load_export`); a jelentés futás-mappája fixture esetén `fixture_` előtagú. Egy manifest-szintű hamisítás (a `data_kind` mező meghamisítása) sem marad észrevétlen: a mintafájlok SOROK szintjén tárolt `fixture` jelölését a `load_samples` külön, függetlenül ellenőrzi. |

## 2. Bemenet-ellenőrzés (`load_export`, `load_samples`)

Sorrendben: mód-választás érvényessége → a manifest létezik és olvasható JSON → kötelező kulcsok megvannak → nincs `FAILED.txt`/`.partial` maradék → `tool`/`tool_version` MT-4-re mutat → `status: completed` → `training_ready`/`content_verified`/`split_approved` (a manifestben ÉS a `statuses` blokkban is) mind `false` → a kért `--mode` egyezik az export `data_kind`/`fixture` jelölésével → a hat TE-1 kizárás ellenőrzése megtörtént (`exclusion_guard.performed`), különben csak kifejezett `--allow-no-te1-comparison` mellett → minden `outputs`-ban felsorolt fájl megvan és az ellenőrzőösszege/mérete egyezik → fixture exportnál megvan a tesztadat-jelölő fájl → a `conversations` lista darabszáma és azonosító-egyedisége részenként egyezik a `splits` összegzéssel.

Ezután **mintafájlonként** (`load_samples`): a fájl sorainak száma egyezik a manifesttel → minden sor `split`/`mode`/`data_kind`/`fixture` mezője egyezik a fájllal és az exporttal → a `conversation_id` ismert és a megfelelő részhez tartozik → a `sample_id` `<beszélgetés>#<mód>#<célforduló>` alakú és egyedi → a `target` karaktertartomány érvényes (`0 <= start < end <= len(text)`) → beszélgetésenként a minták száma egyezik a manifest `exchanges` mezőjével.

Bármelyik lépés hibája `InvalidExportError` (sérült/elavult export, 11-es kód) vagy `StaleExportError` (elavult eszköz/verzió/státusz/kizárás, 12-es kód); a mód/fixture ütközés `RefusedError` (15-ös kód). Egyik sem ír vagy módosít semmit a forrás-exportban.

## 3. Célmaszk

A veszteség-maszk **kizárólag** az MT-4 minta `target` mezőjéből (a célválasz karaktertartománya a renderelt szövegben) származik, nem heurisztikából. A (bemenet=`ids[:-1]`, cél=`ids[1:]`) eltolt párra: `mask[i] = 1,0`, ha az `i`. cél-pozíció (amely az eredeti szöveg `(i+1)`. karakterét jósolja) a `[target_start, target_end)` tartományba esik. Az előzmény, az aktuális kérdés és a (kötegeléskor hozzáadott) kitöltés emiatt sosem kap `1,0`-t. Egy **független** önellenőrzés (`verify_mask_alignment`, nem a maszkképző függvény belső logikáját ismétli meg) a maszk `1,0` pozícióiból visszaszámolja a jósolt karaktereket és összeveti a tényleges célválasz-szöveggel; ez minden minta előkészítésekor lefut (`prepare_sample`), hiba esetén `VerificationError`.

## 4. Kódolás, szótár, ismeretlen karakterek

A szótár **kizárólag** a train rész elsődleges (R2) mintáinak renderelt szövegéből épül (a teljes, címkékkel együtt renderelt szöveg karakterei — ugyanaz az elv, mint a meglévő `train_chat.build_vocab()`). Két **fenntartott** azonosító kerül a szótár mögé (nem a megfigyelt karakterek közé, tehát nem "bővíti" a train-szótárat utólag): `UNK` az ismeretlen (validation/test, esetleg R1-only) karakterekhez, `PAD` a kötegelési kitöltéshez.

A kódolás **pozíciótartó**: minden karakter pontosan egy id-t kap (a meglévő `tokenizer.CharTokenizer.encode` ezzel szemben **kihagyja** az ismeretlen karaktereket, ami eltolná a célmaszk pozícióit — ezért ez a modul saját kódolást használ, nem a `tokenizer.py`-t). Az ismeretlen karakterek `unk_id`-t kapnak és számolva vannak (`unknown_chars_total_occurrences`, `unknown_chars_distinct`), a szótár nem bővül miattuk. A train/R2 rész emiatt garantáltan 0 ismeretlen karaktert mutat; a train/R1 (a csonkolás miatt, elméletileg) és a validation/test részek nem feltétlenül.

## 5. Hosszkorlát és kompatibilitási korlát — két külön dolog

* **Hosszkorlát (`--max-chars`, explicit, alapból `DEFAULT_MAX_CHARS` = 4096):** a fölötte lévő mintát a betöltő **nem csonkítja csendben**: kihagyja a kötegelésből, és okkal, a mért hosszal együtt jelenti (`splits.<rész>.<mód>.withheld_oversized`/`withheld_reasons`, `sample_lengths.tsv`). Ez **kísérleti**, technikai védőkorlát, nem tartalmi ítélet; az alapérték nem kalibrált valódi többfordulós adaton (mert még nincs).
* **Kompatibilitási korlát (a betanított modell tapasztalata):** a `CharLSTM` (LSTM) architektúra elméletileg tetszőleges hosszú sorozatot fogad (nincs rögzített kontextusablak, mint egy Transformernél) — ezt egy **friss, véletlen inicializált, tanítatlan** próba-modellel, tényleges előrefutással és veszteség-számítással ellenőrzi a modul (`forward_check`, `torch.no_grad()`, nincs `.backward()`). A jelenleg **betanított** v0.7 modell viszont mindvégig `config.seq_length` (64) karakteres véletlen ablakokon tanult, folytonos állapotátvitel nélkül: tényleges, **tanult** tapasztalata ennél hosszabb, összefüggő kontextusra nincs. A jelentés ezt a két dolgot külön mezőben mutatja (`splits.<rész>.<mód>.samples_over_trained_context_pct` a hosszkorlát alatt maradt, de 64 karakternél hosszabb bemenetű minták aránya), és **a sikeres betöltés/előrefutás önmagában NEM bizonyítja a hosszú kontextus tényleges megtanulását**.

## 6. Kötegelés és állapot-elkülönítés

Egy köteg sora mindig **pontosan egy minta** (a fájlban szereplő sorrendben, `--batch-size` méretű csoportokban) — sosem fűz össze két beszélgetést. A rövidebb sorok jobbról `pad_id`-vel (bemenet/cél) és `0,0`-val (maszk) vannak kitöltve a köteg leghosszabb mintájáig; a kitöltés emiatt sosem kap célmaszkot (tesztelve). Minden előrefutás **nulla kezdő rejtett állapottal** indul (`hidden=None`); a modul sosem ad tovább rejtett állapotot sem a kötegen belüli sorok között (az LSTM batch-dimenziója eleve független), sem kötegek **között** (nincs olyan kód, amely egy köteg végállapotát átadná a következőnek) — ezt közvetlen teszt igazolja (egy köteg B önmagában és egy A köteg után futtatva ugyanazt az eredményt adja).

## 7. Kimenet és önellenőrzés

Új futás-mappa (`<out-dir>/<fixture_>mt5_<időbélyeg vagy --run-name>/`), soha nem ír felül és nem lehet az MT-4 export saját mappája alatt, sem `data/clean|raw|rejected|inbox` alatt. Kimenet: `dryrun_report.json` (bemenetek, beállítások, szótár, részenkénti/módonkénti statisztika, kihagyott minták oka és hossza, kompatibilitási arány, időzítés, figyelmeztetések, korlátok, `training_ready`/`content_verified`/`split_approved: false`) és `sample_lengths.tsv` (mintánként: rész, mód, azonosító, beszélgetés, hossz, megtartva/visszatartva, ok, ismeretlen karakter). A jelentés a lemezről visszaolvasva önellenőrzött, mielőtt véglegesedik (`verify_dry_run_report`, a `--verify-report` kapcsolóval utólag is újrafuttatható); hiba esetén `FAILED.txt` marad, a `dryrun_report.json` nem jön létre.

## 8. Reprodukálhatóság

A jelentés (az időzítésen kívül) **determinisztikus**: a próba-modell súlyait `torch.manual_seed(config.seed)` rögzíti közvetlenül a modell létrehozása előtt, a kötegelés a fájlbeli sorrendet követi (nincs véletlen keverés). Két azonos bemeneten futtatott száraz futás — a `created_utc`/`run_dir`/`outputs`/`timing_seconds` mezőktől eltekintve — bájtra azonos jelentést ad (tesztelve).

## 9. Korlátok

* A célmaszk az MT-4 `target` mezőjéből származik: ha az MT-4 renderelése hibás lenne, ez a modul azt nem tudja észrevenni (csak a saját, belső illeszkedését ellenőrzi, nem a renderelés tartalmi helyességét).
* A hosszkorlát fölötti minták visszatartása kísérleti, technikai védőkorlát; az alapérték nem kalibrált valódi adaton.
* Az előrefutási ellenőrzés egy friss, véletlen inicializált próba-modellel történik, NEM a betanított v0.7 checkpointtal: a kiszámított veszteség-érték tartalmilag értelmezhetetlen, csak alak-/futás-ellenőrzésre szolgál.
* A `CharLSTM` architektúra tetszőleges hosszú sorozatot elméletileg elfogad; ez nem jelenti, hogy egy ténylegesen tanított modell meg is tanulja használni a hosszú kontextust.
* Az erőforrás-mérés a kódolt tenzorok becsült mérete és a mért futásidő (ezen a gépen, egyszeri futás), nem profilozott csúcsmemória.
* Az ismeretlen karakterek kezelése a train-szótárhoz képest történik; ha a train rész maga sem fedi le a nyelv teljes karakterkészletét, ez sok ismeretlen karaktert eredményezhet.
* Valódi többfordulós adaton (a fixture teszteken túl) ez a modul nem futott, mert ilyen adat még nem létezik.

## 10. Használat és kilépési kódok

```bash
python src/train_multiturn.py --export-manifest <export_manifest.json> --mode dataset|fixture \
    --out-dir <mappa> --dry-run [--modes R2,R1] [--max-chars 4096] [--batch-size 16] \
    [--allow-no-te1-comparison] [--run-name <név>]
python src/train_multiturn.py --verify-report <dryrun_report.json>
```

`0` kész, nincs visszatartott/hibás minta; `1` kész, de figyelmet kér (visszatartott (túl hosszú) minta, ismeretlen karakter, előrefutási hiba); `2` argumentumhiba; `10` bemeneti fájl hiba; `11` sérült/ellenőrzőösszeg-eltérő export; `12` elavult/nem megfelelő export (eszköz, verzió, státusz, mód/fixture eltérés, hiányzó kizárás-ellenőrzés); `13` kimeneti útvonal hiba; `14` belső önellenőrzés hibát talált (nincs véglegesített jelentés); `15` elutasított kérés (hiányzó `--dry-run`, ismeretlen renderelési mód, R3 kérése).
