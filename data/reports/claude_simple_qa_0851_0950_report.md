# Hatodik FELÜGYELT Claude-generált próba batch - simple_qa 0851-0950

- Forrás: **Claude-generált**, 100 db, kézzel megírt, majd a teljes meglévő
  pipeline-nal ellenőrzött sor. Az **1000 db egyszerű magyar kérdés-válasz
  célcsomag** folytatása - az AUTOPILOT v2 folyamat harmadik batch-e.
- `source` mező: `synthetic_claude`.
- **Ez továbbra is TESZT kör** - a modellt NEM tanítottuk erre az adatra,
  webapp/backend kód nem változott.

## 1. Számok

| Mérőszám | Érték |
|---|---|
| Raw sorok | 100 |
| Validáláson elfogadva | 100 |
| Validáláson elutasítva | 0 |
| Kereszt-batch **jelzett** (0.9 fölötti) egyezés | 4 |
| Ebből manuálisan ellenőrizve **valódi duplikátum** | **0** |
| **Végleges clean sorok** | **100** |
| **Rejected sorok** | **0** |
| Átlag quality_score | **100.0** |
| Flag-et kapott sor | 0 |

## 2. Ellenőrzési lépések (teljes pipeline)

### 2.1 Schema validate
Mind a 100 sor strukturálisan érvényes.

### 2.2 Kizárt témák explicit ellenőrzése
A kizárt kifejezések egyikére sem volt találat. AI-tagelt sor: **0/100**.

### 2.3 Teljes korpuszos cross-dedupe (a TELJES 691 soros meglévő korpusz +
    ez a 100 sor, 0.9 küszöb, összesen 791 sor)

**A dedupe 4 db 0.9 fölötti egyezést jelzett** - ez az ELSŐ eset ebben a
projektben, hogy a hivatalos 0.9-es küszöb fölött állítólagos duplikátumot
talált a rendszer úgy, hogy a manuális ellenőrzés **egyértelműen hamis
pozitívnak** bizonyította mind a négyet:

| Jelzett pár | Hasonlóság | Tartalom | Verdikt |
|---|---|---|---|
| `simple_qa_0851` ("Mi a szív szerepe a szervezetben?") vs `simple_qa_0857` ("Mi a bőr szerepe a szervezetben?") | 0.904 | Szív pumpafunkciója vs bőr védő/hőszabályozó szerepe - **teljesen más szerv, más tartalom** | HAMIS POZITÍV |
| `simple_qa_0851` vs `simple_qa_0859` ("Mi a vese szerepe a szervezetben?") | 0.919 | Szív vs vese - **teljesen más szerv, más tartalom** | HAMIS POZITÍV |
| `simple_qa_0671` ("Mi az a kamat?", korábbi batch) vs `simple_qa_0914` ("Mi az a harmat?") | 0.919 | Kamat (pénzügyi fogalom) vs harmat (meteorológiai jelenség) - **véletlen magyar szóalak-egyezés ("...amat"), semmi közös tartalom** | HAMIS POZITÍV |
| `simple_qa_0489` ("Mi a különbség az eső és a jégeső között?", korábbi batch) vs `simple_qa_0915` ("Mi a különbség a dér és a jégeső között?") | 0.921 | Két KÜLÖNBÖZŐ csapadékfajta (eső, illetve dér) összevetése a jégesővel - **más az összehasonlítás tárgya, más a tartalom** | HAMIS POZITÍV |

**Gyökérok**: a `dataset_dedupe.py` az `instruction+input` szöveget
hasonlítja össze (nem az outputot is), és ha az `input` üres, ez tisztán az
`instruction` szövegére redukálódik. Az eddigi projekt-tapasztalat szerint
a hosszabb, összetettebb sablonok (pl. "Mi a különbség X és Y között?")
elég karaktert variálnak ahhoz, hogy a hasonlóság 0.9 alatt maradjon
tartalmilag eltérő kérdéseknél. Ez a batch viszont NAGYON RÖVID,
egyetlen szót variáló sablonokat is használt (pl. "Mi a ___ szerepe a
szervezetben?"), aminél már egyetlen szó cseréje sem elég ahhoz, hogy a
`SequenceMatcher` arány 0.9 alá essen - ÉS emellett a magyar nyelv
morfológiája miatt véletlenül is előfordulhat magas karakter-egyezés
teljesen független szavak között (pl. "kamat"/"harmat").

**Ez egy ÚJ, korábban nem dokumentált korlátja a dedupe-eszköznek** (eddig
csak a 0.55-0.89 tartományban voltak ismert hamis pozitívok, most
kiderült, hogy 0.9 fölött is előfordulhatnak, ha a sablon elég rövid).
**Egyik jelzett sort SEM távolítottam el** - mind a négy manuálisan
ellenőrzött tartalom egyértelműen, félreérthetetlenül különböző témát,
különböző tényszerű választ ad. A döntést a teljes instruction+output
szövegek egymás mellé olvasásával hoztam meg, nem csak a hasonlósági
számra hagyatkozva.

**Javaslat jövőbeli hardening-körre**: a `dataset_dedupe.py`-t érdemes
lenne kiegészíteni egy MINIMÁLIS EGYEDI SZÓ-arány ellenőrzéssel (pl. ha az
instruction+input szövegben szereplő tartalmi szavak - a sablon-szavak
kivételével - kevesebb, mint X%-ban egyeznek, NE jelezzen duplikátumot,
még ha a nyers karakteres SequenceMatcher-arány 0.9 fölött is van), VAGY
az `output` hasonlóságát is figyelembe kellene venni az
`instruction_duplicates` kategóriában, nem csak az id/output kategóriáknál
külön-külön.

### 2.4 `tools/dataset_topic_report.py`

**A teljes, egyesített korpuszon** (691 régi + 100 új = 791 sor):

| Tag | 691 sornál (előző kör) | **791 sornál (most)** |
|---|---|---|
| AI | 6.4% (44) | **5.6% (44)** - tovább csökkent |
| iskola | 10.3% (71) | 9.0% (71) - tovább csökkent |
| technika | 10.1% (70) | 9.0% (71)* - tovább csökkent |

*A `technika` tag 1 új sort kapott (`simple_qa_0948`, "papíralapú vs
e-book" - a technika tag is szerepel az irodalom mellett), ezért 70->71.

Az **AI/Nexora arány hatodik egymást követő körben is csökkent** (12.9% ->
11.2% -> 8.9% -> 7.4% -> 6.4% -> **5.6%**), az iskola/technika arány is
tovább mérséklődött, mindkettő már csak alig van a 8%-os küszöb fölött.

### 2.5 `dataset_score.py`
Mind a 100 sor **100/100** pontot kapott, flag nélkül.

### 2.6 Safety/firewall ellenőrzés
- **`src/guard.py` `looks_like_identity_bleed()`**: **0 találat**.
- **Kiegészítő kulcsszó-szűrés** (ezúttal az orvosi listát kibővítve
  `kezelés` szóval is, az anatómia-blokk miatt): **0 találat mindenhol**.
- **Anatómiai blokk (0851-0870) külön is átnézve**: mind SEMLEGES,
  tankönyvi jellegű definíció, egyik sem ad diagnózist, kezelési
  javaslatot vagy orvosi tanácsot - kizárólag "mi micsoda" jellegű
  ismeretterjesztés.

## 3. Manuális mintavételes tartalmi átnézés (20 sor, a 4 jelzett pár
   mindegyikét is beleértve)

| id | Instruction | Értékelés |
|---|---|---|
| simple_qa_0854 | Mi az agy fő szerepe? | Pontos, semleges anatómiai definíció. OK. |
| simple_qa_0857 | Mi a bőr szerepe a szervezetben? | **Cross-dedupe jelezte 0851-gyel (0.904), manuálisan ellenőrizve: hamis pozitív, teljesen más szerv/tartalom.** OK. |
| simple_qa_0859 | Mi a vese szerepe a szervezetben? | **Cross-dedupe jelezte 0851-gyel (0.919), manuálisan ellenőrizve: hamis pozitív.** OK. |
| simple_qa_0866 | Mi az immunrendszer feladata? | Pontos anatómiai definíció. OK. |
| simple_qa_0873 | Mi a különbség az induktív és a deduktív érvelés között? | Pontos filozófiai/logikai fogalom. OK. |
| simple_qa_0878 | Mi az a paradoxon? | Pontos definíció. OK. |
| simple_qa_0883 | Mi a különbség a tudás és a hit között? | Semleges, nem hittérítő megfogalmazás. OK. |
| simple_qa_0890 | Miért hasznos megismerni különböző filozófiai nézőpontokat? | Semleges, nem elfogult válasz. OK. |
| simple_qa_0892 | Mi a sakkmatt? | Pontos sakkszabály. OK. |
| simple_qa_0899 | Mi a különbség a póker és a römi kártyajáték jellege között? | Pontos, nem szerencsejáték-ösztönző leírás. OK. |
| simple_qa_0905 | Mi a különbség a stratégiai és a szerencsejáték elemei között? | Semleges fogalom. OK. |
| simple_qa_0910 | Miért fontosak a szabályok betartása és a türelem a társasjátékoknál? | Pozitív, etikus tanács. OK. |
| simple_qa_0914 | Mi az a harmat? | **Cross-dedupe jelezte 0671-gyel (0.919), manuálisan ellenőrizve: hamis pozitív, kamat vs harmat teljesen más téma.** OK. |
| simple_qa_0915 | Mi a különbség a dér és a jégeső között? | **Cross-dedupe jelezte 0489-cel (0.921), manuálisan ellenőrizve: hamis pozitív.** OK. |
| simple_qa_0918 | Mi a szivárvány kialakulásának alapfeltétele? | Pontos, tudományosan helyes. OK. |
| simple_qa_0929 | Mi a különbség a klíma és az időjárás fogalma között? | Pontos fogalommagyarázat. OK. |
| simple_qa_0932 | Hogyan válasszak alkalomhoz illő ruhát? | Semleges, gyakorlati tanács. OK. |
| simple_qa_0941 | Mi a különbség a szépirodalom és a szakirodalom között? | Pontos irodalmi fogalom. OK. |
| simple_qa_0945 | Hogyan válasszak könyvet, ha nem tudom, mit szeretnék olvasni? | Gyakorlati, veszélytelen tanács. OK. |
| simple_qa_0950 | Hogyan jegyezzem meg, amit olvastam egy könyvben? | Gyakorlati tanács. OK. |

**Eredmény: 20/20 sor megfelelt**, beleértve a cross-dedupe által
(tévesen) jelzett mind a négy sort is.

## 4. Fájlok

- Raw: `data/raw/claude_simple_qa_0851_0950_raw.jsonl` (100 sor)
- Clean: `data/clean/claude_simple_qa_0851_0950_clean.jsonl` (100 sor)
- Rejected: `data/rejected/claude_simple_qa_0851_0950_rejected.jsonl` (0 sor)

## 5. Regressziós teszt
`tests/test_v1_7_4_dataset_foundation.py` - **minden teszt sikeres, STÁTUSZ:
STABIL**.

## 6. Amit ez a kör NEM tett

- **Nem indított tanítást.**
- **Nem módosított webapp/backend kódot** (a `tools/dataset_dedupe.py`-n
  sem változtattam, csak DOKUMENTÁLTAM a most felfedezett korlátját -
  a tényleges javítás egy külön, jövőbeli hardening-kör feladata).
- **Nem nyúlt a régi (0151-0850) clean fájlokhoz.**

---

## Végső összegzés

- Raw sorok száma: **100**
- Clean sorok száma: **100**
- Rejected sorok száma: **0**
- Kereszt-batch duplikátumok száma: **0 valódi** (4 jelzett, mind hamis
  pozitívnak bizonyult manuális ellenőrzéssel - lásd 2.3 pont, ÚJ
  dedupe-korlát dokumentálva)
- Átlag quality_score: **100.0**
- Topic report (röviden): batch önmagában 5 vadonatúj témakörre fókuszált
  (anatómia, filozófia, társasjáték, meteorológia, divat+irodalom); a
  teljes korpuszra vetítve az **AI/Nexora arány hatodik körben is
  tovább csökkent (6.4%->5.6%)**, iskola/technika is tovább mérséklődött.
- 20 soros manuális mintavétel eredménye: **20/20 megfelelt** (a 4
  cross-dedupe által jelzett sort is beleértve).
- **Egyedi clean simple_qa sorok jelenleg összesen: 791**
  (691 korábbi + 100 új ebből a batch-ből).
- **Hiányzik még az 1000 db simple_qa célhoz: 209 sor.**

**STÁTUSZ: STABIL.**
