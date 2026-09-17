# DeepSeek simple_qa_0401-0450 import report
- Forrás: `data/raw/deepseek_simple_qa_0401_0450_raw.jsonl` (DeepSeek generálta, `raw` batch)
- Beolvasott sorok: 50
- Validáláson elfogadva: 50
- Validáláson elutasítva: 0
- Kereszt-batch duplikátumként kiszűrve: 1
- Végleges clean sorok: 49
- Átlag quality_score: 100.0

## Automatikusan javított apróságok
- sor 35: **zarjad_el_to_zard_el** - 'Zárjad el a csapot' -> 'Zárd el a csapot'.

## Átnézve, de változtatás nélkül hagyva
- `simple_qa_0421`, `simple_qa_0425`, `simple_qa_0426`, `simple_qa_0428` (jogi/társadalmi fogalmak) - mindegyik tiszta, semleges definíció, egyik sem ad jogi/politikai tanácsot.

## Validáláson elutasított sorok
- (nem volt elutasított sor a javítás után)

## Kereszt-batch duplikátum-ellenőrzés
A hivatalos dedupe-eszközzel (0.9 küszöb) a TELJES eddigi korpuszon (0151-0400 clean, 246 sor), PLUSZ egy kiegészítő, célzott, 0.55-ös küszöbű ellenőrzéssel kifejezetten az időbeosztás/feladatbeosztás, naplóírás, üvegházhatás és célkitűzés/önfejlesztés témájú új sorokra.

| új id | egyezés típusa | egyező korábbi id | forrás | hasonlóság |
|---|---|---|---|---|
| simple_qa_0446 | instruction_duplicates | simple_qa_0370 | deepseek_simple_qa_0351_0400_clean.jsonl | 1.0 |

A kiegészítő, alacsonyabb küszöbű ellenőrzés megerősítette, hogy a 0.55-0.89 tartományban talált egyezések (pl. "Mit tegyek, ha...", "Mi az...?" sablonok) mind csak közös mondatszerkezetet osztanak, NEM valódi tartalmi duplikátumot - ezeket nem vettem ki.

## Kimeneti fájlok
- Clean: `data/clean/deepseek_simple_qa_0401_0450_clean.jsonl` (49 sor)
- Rejected: `data/rejected/deepseek_simple_qa_0401_0450_rejected.jsonl` (1 sor)

**FONTOS: ez a csomag NEM lett tanításra használva - a nyers és a clean adat is csak a `data/` mappában, ellenőrzésre vár.**
