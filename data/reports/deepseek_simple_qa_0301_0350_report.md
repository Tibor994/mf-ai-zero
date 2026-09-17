# DeepSeek simple_qa_0301-0350 import report
- Forrás: `data/raw/deepseek_simple_qa_0301_0350_raw.jsonl` (DeepSeek generálta, `raw` batch)
- Beolvasott sorok: 50
- Validáláson elfogadva: 50
- Validáláson elutasítva: 0
- Kereszt-batch/batchon belüli duplikátumként kiszűrve: 4
- Végleges clean sorok: 46
- Átlag quality_score: 100.0

## Automatikusan javított apróságok
- sor 3: **dugohuzo_to_lefolyotisztito** - 'használj dugóhúzót vagy hívj szakembert' -> 'használj lefolyótisztító pumpát vagy hívj szakembert'.
- sor 9: **sutotisztitas_ovatosabb** - 'Használj sütőtisztítót vagy készíts szódabikarbónából és ecetből keveréket.' -> 'Használj kímélő sütőtisztítót, VAGY - külön ettől, a kettőt ne kombináld - készíts szódabikarbónából és ecetből keveréket.'.
- sor 55: **wifi_spelling** - 'a wifis és a mobilnet' -> 'a Wi-Fi-s és a mobilnet'.
- sor 55: **wifi_spelling** - 'A wifi egy helyi hálózathoz' -> 'A Wi-Fi egy helyi hálózathoz'.
- sor 55: **wifi_spelling** - 'A wifi általában gyorsabb' -> 'A Wi-Fi általában gyorsabb'.
- sor 61: **telefont_nyomkodjad_natural** - 'ne a telefont nyomkodjad' -> 'ne a telefonodat böngészd'.
- sor 99: **nexora_zero_accent** - 'fejlesztik tovább a Nexora Zerot?' -> 'fejlesztik tovább a Nexora Zerót?'.

## Validáláson elutasított sorok
- (nem volt elutasított sor a javítás után)

## Kereszt-batch duplikátumok (data/clean/deepseek_simple_qa_0151_0200/0201_0250/0251_0300 ellen ellenőrizve, küszöb=0.9)
| új id | egyezés típusa | egyező korábbi id | forrás | hasonlóság |
|---|---|---|---|---|
| simple_qa_0344 | instruction_duplicates | simple_qa_0192 | deepseek_simple_qa_0151_0200_clean.jsonl | 1.0 |
| simple_qa_0347 | instruction_duplicates | simple_qa_0244 | deepseek_simple_qa_0201_0250_clean.jsonl | 0.921 |
| simple_qa_0345 | output_duplicates | simple_qa_0297 | deepseek_simple_qa_0251_0300_clean.jsonl | 0.982 |
| simple_qa_0347 | output_duplicates | simple_qa_0244 | deepseek_simple_qa_0201_0250_clean.jsonl | 1.0 |
| simple_qa_0349 | output_duplicates | simple_qa_0248 | deepseek_simple_qa_0201_0250_clean.jsonl | 1.0 |

## Kimeneti fájlok
- Clean: `data/clean/deepseek_simple_qa_0301_0350_clean.jsonl` (46 sor)
- Rejected: `data/rejected/deepseek_simple_qa_0301_0350_rejected.jsonl` (4 sor)

**FONTOS: ez a csomag NEM lett tanításra használva - a nyers és a clean adat is csak a `data/` mappában, ellenőrzésre vár.**
