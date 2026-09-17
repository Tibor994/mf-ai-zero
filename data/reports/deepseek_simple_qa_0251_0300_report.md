# DeepSeek simple_qa_0251-0300 import report
- Forrás: `data/raw/deepseek_simple_qa_0251_0300_raw.jsonl` (DeepSeek generálta, `raw` batch)
- Beolvasott sorok: 50
- Validáláson elfogadva: 50
- Validáláson elutasítva: 0
- Duplikátumként kiszűrve: 0
- Végleges clean sorok: 50
- Átlag quality_score: 100.0

## Automatikusan javított apróságok
- sor 23: **ervelhez_to_ervhez** - 'Minden érvelhez tartozzon' -> 'Minden érvhez tartozzon'.
- sor 51: **gyari_visszaallitas_vegso_esetkent** - 'Ha ez sem segít, állítsd vissza a gyári beállításokat, de előtte mentsd az adataidat.' -> 'Ha ez sem segít, csak végső esetben állítsd vissza a gyári beállításokat, és előtte mindenképp mentsd az adataidat.'.
- sor 59: **wifi_spelling** - 'elveszett a wifi jelszó' -> 'elveszett a Wi-Fi jelszó'.
- sor 59: **gyari_visszaallitas_vegso_esetkent** - 'Ha nem megy, állítsd vissza a gyári beállításokat, de utána újra be kell állítani.' -> 'Ha nem megy, csak végső esetben állítsd vissza a gyári beállításokat, mert utána mindent újra be kell állítani.'.

## Átnézve, de változtatás nélkül hagyva
- `simple_qa_0294`, `simple_qa_0300` (Nexora Zero említések) - már eleve óvatos, hedge-elt megfogalmazás ("a célja, hogy...", "a cél, hogy..."), nem talált túlzó állítást.
- Ügyintézés-kategóriájú sorok (0251/0253/0254/0255/0256/0257) - már eleve "lehet"/"általában"/"szükség lehet" jellegű, nem-túl-magabiztos megfogalmazást használnak.

## Validáláson elutasított sorok
- (nem volt elutasított sor a javítás után)

## Duplikátumok
- (nem volt duplikátum)

## Kimeneti fájlok
- Clean: `data/clean/deepseek_simple_qa_0251_0300_clean.jsonl` (50 sor)
- Rejected: `data/rejected/deepseek_simple_qa_0251_0300_rejected.jsonl` (0 sor)

**FONTOS: ez a csomag NEM lett tanításra használva - a nyers és a clean adat is csak a `data/` mappában, ellenőrzésre vár.**
