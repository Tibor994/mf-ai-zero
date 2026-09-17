# DeepSeek simple_qa_0201-0250 import report
- Forrás: `data/raw/deepseek_simple_qa_0201_0250_raw.jsonl` (DeepSeek generálta, `raw` batch)
- Beolvasott sorok (javítás után): 50
- Validáláson elfogadva: 50
- Validáláson elutasítva: 0
- Duplikátumként kiszűrve: 0
- Végleges clean sorok: 50
- Átlag quality_score: 100.0

## Automatikusan javított apróságok
- sor 25: **missing_separator_split** - Két JSON rekord egy fizikai sorra keveredett (elválasztó/sortörés nélkül) - kettébontva.
- sor 10: **a_az_hangzoilleszkedes** - 'a apró szilánkokat' -> 'az apró szilánkokat'.
- sor 10: **zuzodott_to_torott** - 'A zúzódott üveget' -> 'A törött üveget'.
- sor 15: **osszad_to_oszd** - 'Osszad részekre' -> 'Oszd részekre'.
- sor 30: **wifi_spelling** - 'ha lassú a wifi?' -> 'ha lassú a Wi-Fi?'.
- sor 30: **wifi_spelling** - 'Wifi lassulásra' -> 'Wi-Fi lassulásra'.
- sor 46: **nexora_zero_accent** - 'Nexora Zerot' -> 'Nexora Zerót'.

## Validáláson elutasított sorok
- (nem volt elutasított sor a javítás után)

## Duplikátumok
- (nem volt duplikátum)

## Kimeneti fájlok
- Clean: `data/clean/deepseek_simple_qa_0201_0250_clean.jsonl` (50 sor)
- Rejected: `data/rejected/deepseek_simple_qa_0201_0250_rejected.jsonl` (0 sor)

**FONTOS: ez a csomag NEM lett tanításra használva - a nyers és a clean adat is csak a `data/` mappában, ellenőrzésre vár.**
