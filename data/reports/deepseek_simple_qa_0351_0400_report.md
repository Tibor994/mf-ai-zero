# DeepSeek simple_qa_0351-0400 import report
- Forrás: `data/raw/deepseek_simple_qa_0351_0400_raw.jsonl` (DeepSeek generálta, `raw` batch)
- Beolvasott sorok: 50
- Validáláson elfogadva: 50
- Validáláson elutasítva: 0
- Kereszt-batch duplikátumként kiszűrve: 2
- Végleges clean sorok: 48
- Átlag quality_score: 100.0

## Automatikusan javított apróságok
- sor 3: **valtas_ruhat_to_valtoruhat** - 'Vigyél váltás ruhát' -> 'Vigyél váltóruhát'.
- sor 51: **sejtszam_pontositas** - 'A testünk sok millió sejtből épül fel.' -> 'A testünk emberi sejtek billióiból épül fel.'.
- sor 99: **nexora_zero_accent** - 'fejlesztik tovább a Nexora Zerot?' -> 'fejlesztik tovább a Nexora Zerót?'.

## Átnézve, de változtatás nélkül hagyva
- `simple_qa_0394`, `simple_qa_0399` (AI-biztonság/etika említések) és `simple_qa_0395` (Nexora Zero) - már eleve óvatos, hedge-elt megfogalmazás ("arra törekszünk", "erre is figyelünk"), nem talált túlzó állítást.

## Validáláson elutasított sorok
- (nem volt elutasított sor a javítás után)

## Kereszt-batch duplikátumok (data/clean/deepseek_simple_qa_0151_0200/0201_0250/0251_0300/0301_0350 ellen ellenőrizve, küszöb=0.9)
| új id | egyezés típusa | egyező korábbi id | forrás | hasonlóság |
|---|---|---|---|---|
| simple_qa_0395 | instruction_duplicates | simple_qa_0196 | deepseek_simple_qa_0151_0200_clean.jsonl | 1.0 |
| simple_qa_0400 | instruction_duplicates | simple_qa_0350 | deepseek_simple_qa_0301_0350_clean.jsonl | 1.0 |

## Kimeneti fájlok
- Clean: `data/clean/deepseek_simple_qa_0351_0400_clean.jsonl` (48 sor)
- Rejected: `data/rejected/deepseek_simple_qa_0351_0400_rejected.jsonl` (2 sor)

**FONTOS: ez a csomag NEM lett tanításra használva - a nyers és a clean adat is csak a `data/` mappában, ellenőrzésre vár.**
