# DeepSeek simple_qa_0151-0200 import report
- Forrás: `data/raw/deepseek_simple_qa_0151_0200_raw.jsonl` (DeepSeek generálta, `raw` batch)
- Beolvasott sorok (a hiányzó-elválasztó javítás UTÁN): 50
- Validáláson elfogadva: 50
- Validáláson elutasítva: 0
- Duplikátumként kiszűrve: 0
- Végleges clean sorok: 50
- Átlag quality_score: 100.0

## Automatikusan javított apróságok
- sor 10: **missing_separator_split** - Két JSON rekord egy fizikai sorra keveredett (hiányzó sortörés) - kettébontva.
- sor 25: **wifi_spelling** - 'wifira' -> 'Wi-Fi-re' (instruction mező).
- sor 25: **wifi_spelling** - 'Wifi használat' -> 'Wi-Fi használat' (quality_notes mező).
- sor 44: **nexora_zero_accent** - 'Nexora Zeroból' -> 'Nexora Zeróból' (hiányzó ékezet).

## Validáláson elutasított sorok
- (nem volt elutasított sor a javítás után)

## Duplikátumok
- (nem volt duplikátum)

## Kimeneti fájlok
- Clean: `data/clean/deepseek_simple_qa_0151_0200_clean.jsonl` (50 sor)
- Rejected: `data/rejected/deepseek_simple_qa_0151_0200_rejected.jsonl` (0 sor)

**FONTOS: ez a csomag NEM lett tanításra használva - a nyers és a clean adat is csak a `data/` mappában, ellenőrzésre vár.**
