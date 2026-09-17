# DeepSeek simple_qa_0451-0500 import report
- Forrás: `data/raw/deepseek_simple_qa_0451_0500_raw.jsonl` (DeepSeek generálta, `raw` batch)
- Beolvasott sorok: 50
- Validáláson elfogadva: 50
- Validáláson elutasítva: 0
- Kereszt-batch duplikátumként kiszűrve: 0
- Végleges clean sorok: 50
- Átlag quality_score: 100.0

## Automatikusan javított apróságok
- sor 19: **hitel_alany_allitmany_egyeztetes** - 'A hitel pénzt kérsz kölcsön, amit vissza kell fizetni, a megtakarítás pedig a saját pénzed félretétele.' -> 'A hitel azt jelenti, hogy pénzt kérsz kölcsön, amit vissza kell fizetni, a megtakarítás pedig a saját pénzed félretétele.'.
- sor 27: **olajtuz_biztonsagosabb_tanacs** - 'Soha ne önts rá vizet, hanem takard le egy fedővel vagy nedves ruhával.' -> 'Soha ne önts rá vizet, hanem takard le egy fedővel vagy tűzoltó takaróval - nedves ruhát SOSE használj, mert a forró olajjal érintkezve az is veszélyes gőzképződést/lángfellobbanást okozhat.'.
- sor 69: **mennydorges_pontositas** - 'A hirtelen áramlás fényt és hangot, azaz mennydörgést okoz.' -> 'A villám hirtelen rendkívül felforrósítja a körülötte lévő levegőt, ami robbanásszerűen kitágul - ez a lökéshullám okozza a mennydörgés hangját.'.

## Kifejezetten ellenőrzött, de NEM duplikátumnak talált sor
- `simple_qa_0496` ("Mit tegyek, ha megbántottam valakit?") vs. a korábbi `simple_qa_0363` ("Hogyan kérjek bocsánatot?", batch 5) - közvetlen hasonlóság-számítás: task_sim=0.464, out_sim=0.442, messze a 0.9-es küszöb alatt. Rokon témájú, de tartalmilag és szövegezésében is különböző - NEM duplikátum, bent maradt a clean fájlban.

## Validáláson elutasított sorok
- (nem volt elutasított sor a javítás után)

## Kereszt-batch duplikátumok (data/clean/deepseek_simple_qa_0151_0200...0401_0450 ellen ellenőrizve, küszöb=0.9)
- (nem volt kereszt-batch duplikátum)

## Kimeneti fájlok
- Clean: `data/clean/deepseek_simple_qa_0451_0500_clean.jsonl` (50 sor)
- Rejected: `data/rejected/deepseek_simple_qa_0451_0500_rejected.jsonl` (0 sor)

**FONTOS: ez a csomag NEM lett tanításra használva - a nyers és a clean adat is csak a `data/` mappában, ellenőrzésre vár.**
