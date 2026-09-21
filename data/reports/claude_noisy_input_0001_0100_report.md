# Első noisy_input batch - noisy_input_0001-0100

Az 5. csomag (**Hibás user szöveg -> javított szöveg**, cél: 500 clean sor) **első 100 sora**. Kitalált, hétköznapi, magyar felhasználói
üzenetek (elírt, ékezet nélküli, beszélt nyelvű, rövidítéses, szóközhibás, hibás ragos, telefonon gyorsan gépelt, indulatos, szleng, kusza), és
ezek természetes, érthető javított változata. Nincs valós személy/magánadat, URL, e-mail, telefonszám, cím, projektadat, tanács vagy megválaszolt kérdés:
az output mindig a felhasználó **saját üzenetének tisztább változata**, nem válasz rá.

## ⚠ Sémadöntés, ami a jóváhagyásodra vár

A megadott mezőlistában nincs `instruction`, a repó validátora (`tools/dataset_validate.py`, `REQUIRED_FIELDS`) viszont kötelezően kéri, és üres értéket elutasít.
A validátor módosítása nem ennek a batchnek a hatóköre, ezért **megtartottam a 9 mezős repó-sémát**, és az `instruction` mezőbe rövid, kézzel írt,
**nem helyesírás-javító jellegű** feladatmegfogalmazás került (*"Értsd meg, mit szeretne mondani a felhasználó..."*, *"Mit akart írni a felhasználó?..."*),
összesen 29 különböző szöveg (11 típus-specifikus + 18 általános, egy szöveg legfeljebb 4 sorban). A többi mező pontosan az általad megadott: `category: noisy_input`,
`input` (zajos), `output` (javított), `tags`, `difficulty`, `source: synthetic_claude_magyar`, egyedi `quality_notes`. Ha az `instruction` nem kell, azt a
következő batch előtt külön jóváhagyással a validátorral együtt kell eltávolítani; addig az 5. csomag minden batchén ugyanez a séma marad.

## 0. A kérés követelményei és teljesülésük

| Követelmény | Teljesülés |
|---|---|
| 100 clean sor, `category: noisy_input`, `source: synthetic_claude_magyar`, egyedi `quality_notes` | **100 clean / 0 rejected**, 100 / 100 egyedi quality_notes |
| Vegyes zajtípusok (elgépelés, ékezet nélkül, beszélt nyelv, rövidítés, szóköz, hibás rag, telefonos, indulatos, kérdés félreütéssel, kusza mondat, szleng) | mind a 11 típus, 8-10 sor típusonként (1. fejezet); az id-k a típusokat vegyesen kapják |
| Ne csak helyesírás-javítás legyen, a felhasználói stílus értése a cél | az output **megtartja a hangot** (*haverom*, *meg*, *tesóm*, *jó fej*, *kaja*, *a franc*, *hát*, *izé*), csak érthetővé teszi; 9 sor kizárólag formai (8 szóköz-típus + 1 nagybetűs indulatos), a többi 91 szóalak-szintű zajt is tartalmaz |
| Az output ne legyen túljavított, hivatalos szöveg | az output szószáma az inputéhoz közeli (arány 0.81-1.25, átlag 1.00, medián 14 szó), szleng csak ott cserélődött, ahol az érthetőséghez kellett (*beparáztam* -> *megijedtem*, *tök* -> *nagyon*); szó-szintű szándékmegőrzés: input->output 0.84, output->input 0.82 |
| Kerülendők (PII, szidalom, gyűlölet, szexuális/veszélyes, politika, orvosi/jogi/pénzügyi konkrét tanács, MF-AI/Nextora adat, URL) | egyik sem szerepel (3. fejezet, 8. pont); 6 sor tartalmaz enyhe indulatszót (*a franc*, *a fenébe*, *úristen*, *hülyeség*, *para*), erős káromkodás 0 |
| Ugyanaz a sablon ne ismétlődjön | 100 / 100 egyedi input, output; 50 különböző téma; input-párok >= 0.7 hasonlóságú: 0; a leggyakoribb input-nyitó szó (*a*) 11 sor; output-nyitó szópár legfeljebb 2 |

## 1. Felépítés

| Zajtípus (`tags[2]`) | Sor | Mi a zaj |
|---|---|---|
| elgépelés | 9 | felcserélt/hiányzó betűk (*holnpa*, *gtiározni*) |
| ékezet nélkül | 9 | teljes ékezethiány (*fuszerekkel*, *hetvegen*) |
| beszélt nyelv | 9 | *hát*, *izé*, *asszem*, *figyu*, *mittomén*, *szval*, hiányos szerkezet |
| rövidítés | 9 | *vmi*, *vki*, *kb*, *pl*, *h*, *v*, *akk*, *tel.* |
| szóköz- és írásjelhiba | 8 | összeragadt szavak, kettős szóköz, szóköz a vessző előtt |
| hibás ragozás | 9 | rossz rag vagy szám (*boltba vagyok*, *két gyerekek*, *Debrecenre megyünk*) |
| telefonos gyors gépelés | 9 | kisbetűs, ékezet- és írásjel nélküli, sietős üzenet |
| indulatos, laza stílus | 9 | csupa nagybetű, felkiáltójel-halmozás, kifakadás |
| kérdés félreütésekkel | 9 | félreütött kérdőszó vagy szó egy egyébként tiszta kérdésben |
| hosszabb kusza mondat | 10 | írásjel nélküli, egymásba folyó 30-40 szavas mondat |
| enyhe szleng | 10 | *tuti*, *király*, *suli*, *para*, *meló*, *csaj*, *kamu* |

`tags` = `["magyar", "zajos bemenet", <zajtípus>, <téma>]`, 50 különböző téma (főzés, közlekedés, lakóközösség, telefon, háztartási gép, utazás, bevásárlás...).
`difficulty` a bemenet és a javított változat karakter-eltérése és a bemenet hossza szerinti rang: legnagyobb 20 = hard, következő 35 = medium, a többi 45 easy.
Az id-k deterministikus keverés (seed 20260922) után lettek kiosztva, így nincs típus-blokk.

## 2. Számok

| Mérőszám | Érték |
|---|---|
| Raw sorok | 100 |
| Schema validáció (`dataset_validate.py`, raw és clean is) | 100 / 100 valid |
| `input` == `output` | 0 sor |
| Batchen belüli dedupe (id / instruction+input / output, 0.9) | 0 / 0 / 0 |
| Kereszt-dedupe a 3000 meglévő clean sor ellen (id; instruction+input, output, input-vs-input, input-vs-output >= 0.9, minden találat) | 0 / 0 / 0 / 0 / 0 |
| **Végleges clean** | **100** |
| **Rejected** | **0** |
| Átlag quality_score | **100.0 / 100** |
| Difficulty | easy 45, medium 35, hard 20 |
| Egyedi input / output / quality_notes / instruction | 100 / 100 / 100 / 29 |
| Output szószám (min / medián / max) | 6 / 14 / 39 |
| Output / input szóhossz-arány (min / átlag / max) | 0.81 / 1.00 / 1.25 |
| Karakter-szintű változás (1 - hasonlóság, min / medián / max) | 0.010 / 0.061 / 0.238 |
| Ismeretlen szavak aránya a korpusz-szókincshez képest (input -> output átlag) | **0.266 -> 0.175** |
| Szándékmegőrzés (5 betűs tőszavak lefedettsége, input->output / output->input átlag) | 0.84 / 0.82 |
| Formai zajmarker az outputban (kisbetűs kezdés, hiányzó záró írásjel, dupla szóköz, szóköz írásjel előtt, betűhalmozás, csupa nagybetű, rövidítések) | **0 sor** (az inputban 77 sor tartalmaz legalább egyet) |
| Identity bleed / saját projekt-említés / URL / e-mail / telefon- és cím-minta | 0 / 0 / 0 / 0 / 0 |
| Erős káromkodás, gyűlölet, érzékeny téma kulcsszó (orvos, jog, pénzügy, politika, szex, fegyver...) | 0 |
| Topic report (3100 soros korpusz) | `összefoglalás` 16.1% (500 sor, dokumentált), `zajos bemenet` 3.2% (100 sor, az új csomag jelölő címkéje); más túlreprezentált téma-tag nincs |
| Teljes clean korpusz | **3100 sor** (1000 simple_qa, 1000 explanation, 500 step_by_step, 500 summary, 100 noisy_input) |

## 3. Ellenőrzési lépések (a kért pipeline szerint)

1. **Generálás**: 100 sor 3 részben, soronként kézzel megírt input-output párokkal (nincs szabály- vagy sablongenerátor); az outputot mindig a saját inputjából
   levezetve írtam.
2. **Schema**: `dataset_validate.py` 100/100; saját ellenőrzés a 9 kötelező mezőre, `category`, `source`, `difficulty`, a `tags` fejlécre és a tag-hosszra.
3. **Input != output**: 0 azonos sor; minden sorban valódi tartalmi változás van (lásd 4. fejezet).
4. **Valóban javítottabb-e**: (a) ismeretlen-szó arány a 3100 sor szókincséhez képest, sorpáronként; (b) formai zajmarkerek az outputban (0 sor); (c) az outputban nincs
   rövidítés (*vmi*, *vki*, *kb*, *pl*, *h*, *v*, *akk*, *pls*, *tel.*), nincs betűhalmozás és nincs írásjel-halmozás. A (a) pont 12 sort jelzett, ahol az output ismeretlen-szó aránya
   nagyobb az inputénál; mind a 12 kézzel átnézve: ritka, de helyes szóalak (pl. *bérletemet*, *vasútállomásra*, *sétaútvonalak*), nem hiba.
5. **Szándékmegőrzés**: az input és az output 5 betűs tőszavainak átfedése; 2 sor <0.5 (`0030`, `0038`), mindkettő ékezet nélküli/szlenges input, amelynek a tőszavai az ékezetek miatt
   nem egyeznek, kézzel átnézve rendben.
6. **Batch dedupe**: id 0, instruction+input 0, output 0.
7. **Kereszt-dedupe a teljes korpusz ellen**: az új 100 sor a 3000 meglévő clean sorral szemben (minden találat, `quick_ratio` előszűréssel), több szempontból is: instruction+input, output,
   input-vs-input, input-vs-output; 0 találat, 0 id-ütközés.
8. **Safety/PII/identity bleed**: e-mail, URL, telefon/azonosító-, irányítószám- és címminta 0; MF-AI/Nextora említés 0; `guard.looks_like_identity_bleed` 0 az összes mezőn; erős káromkodás/gyűlölet
   szókészlet 0; érzékeny témák (orvos, gyógyszer, ügyvéd, adó, hitel, szavazás, párt, szex, fegyver, drog, alkohol) 0 találat. A kérdések (pl. tejföl lefagyasztása, matrac, kávé) az inputban
   maradnak, és az outputban **nincs rájuk válasz vagy tanács**.
9. **Quality score**: 100.0 / 100, minden sor 100.
10. **Regressziós teszt**: `tests/test_v1_7_4_dataset_foundation.py` - minden teszt sikeres, **STÁTUSZ: STABIL**.
11. **Manuális átolvasás és mintavétel**: mind a 100 sor input és output egymás mellett elolvasva; formális minta 40 sor (6. fejezet).
12. **Clean/rejected/report**: clean 100, rejected 0 (üres fájl), ez a report; **progress** frissítve (helyi fájl).

## 4. Mi számít javításnak (és mi nem)

- **Javítás**: szóalak-szintű zaj (elgépelés, hiányzó ékezet, hibás rag/szám, rövidítés kibontása, az összeragadt szavak szétválasztása), az írásjelek és a mondatkezdés rendbetétele,
  a kusza mondat tagolása. A **sorrend és a tartalom** megmarad.
- **Nem javítás (szándékosan)**: a user hangját adó fordulatok maradnak (*haverom*, *tesóm*, *meg* mint kötőszó, *a franc*, *a fenébe is*, *jó fej*, *kaja*, *hát*, *izé*, *amúgy*, *vagy mi*),
  a bizonytalanság és az indulat jelzése, a kérdés kérdés marad. Slang csak ott cserélődik, ahol az érthetőséghez kell (*beparáztam*, *király*, *tök para*, *szabi*, *telója*, *csaj*).
- **9 kizárólag formai sor** (`0006`, `0022`, `0023`, `0031`, `0037`, `0047`, `0053`, `0069`, `0071`): a szóköz- és írásjelhiba típus 8 sora + a csupa nagybetűs `0006`; itt maga a zaj formai.
- **Ami nincs benne**: helyesírási szabály megválaszolása, tanács, magyarázat, hivatalosabb átfogalmazás, új tartalom.

## 5. Önkorrekciók a teljes átolvasás során (mind clean előtt, 7 sor)

- **Gyenge zajú sorok (4)**: `0013`, `0043`, `0055` csak nagybetű/írásjel-változtatást tartalmazott (nem volt szóalak-szintű zaj), `0063`-ban csak a tagolás. Újraírtam az inputot valós zajjal
  (*véletlen*/*mer*, *fözni*/*vmi*, *szval*/*vmit*, ö/ő és o/ó felcserélések a *hütö*, *fagyaszto*, *szerelöt* szavakban); az outputok változatlanok.
- **Szándék-eltolódás az outputban (3)**: `0015` (*vagy mi* -> *hogy vissza lehet-e állítani*: a felhasználó "nem tudom visszaállítani" kijelentéséből kérdés lett -> a *vagy mi* lezárás megmaradt),
  `0049` (betoldott *csak* a *holnap ér rá* elé), `0067` (*zsebe maradt* -> *hagytam*: az ige megváltozott, majd az első javításban a tárgyeset is rossz maradt -> *a kulcsom ... zsebében maradt*).
- A 12 ismeretlen-szó jelzés és a 2 alacsony szándékmegőrzési jelzés kézi átnézése módosítást nem igényelt.

## 6. Manuális mintavétel (formális 40 sor)

A minta rögzített szabály szerint készült (az id sorszáma 5-tel osztva 1 vagy 3 maradékot ad: 40 sor), nem válogatott. Mind a 100 sort elolvastam, a minta ennek a dokumentált része. A minta soraiban a fenti önkorrekciók közül a `0013`, `0043`, `0063` szerepel (a javítás után értékelve).

| id | Zajtípus | Konkrét javítások (szó-szintű különbség; a nagybetű- és írásjel-változás nem szerepel) | Értékelés |
|---|---|---|---|
| 0001 | beszélt nyelv | oda -> fél nyolcra; jutni -> odaérni; - fél nyolcra | OK |
| 0003 | beszélt nyelv | - kérik; + kérik | OK |
| 0006 | indulatos, laza stílus | csak szóköz/írásjel/nagybetű | OK |
| 0008 | rövidítés | pl -> Például; vmi -> valami | OK |
| 0011 | kérdés félreütésekkel | Hogyna -> Hogyan | OK |
| 0013 | beszélt nyelv | véletlen -> véletlenül; mer -> Mert | OK (javított: valós szóalak-zaj hozzáadva) |
| 0016 | telefonos gyors gépelés | nettom es -> netem és; feltolteni -> feltölteni | OK |
| 0018 | beszélt nyelv | akarok -> szeretnék; - valamit; + valamit; + a gond | OK |
| 0021 | kérdés félreütésekkel | Mnnyi -> Mennyi; folyon -> folyjon | OK |
| 0023 | szóköz- és írásjelhiba | csak szóköz/írásjel/nagybetű | OK |
| 0026 | telefonos gyors gépelés | jon -> jön; kovetkezo -> következő; + a; talalom -> találom | OK |
| 0028 | hosszabb kusza mondat | meg -> és; - és | OK |
| 0031 | szóköz- és írásjelhiba | csak szóköz/írásjel/nagybetű | OK |
| 0033 | elgépelés | paradicsomlvelek -> paradicsomlevelek; kertbe -> kertben | OK |
| 0036 | hosszabb kusza mondat | mikor -> amikor; kérni -> megkérni; bikázzon -> segítsen bikázni; - és | OK |
| 0038 | indulatos, laza stílus | hulyeseg mar -> hülyeség már; jegyar emeles -> jegyár emelés; meg -> még; mar -> már; fenebe -> fenébe | OK |
| 0041 | hibás ragozás | + éjszaka; - éjszaka; nem -> ne; konfliktus -> konfliktusba | OK |
| 0043 | enyhe szleng | fözni -> főzni; vmi -> valami | OK (javított: valós szóalak-zaj hozzáadva) |
| 0046 | rövidítés | kb -> körülbelül | OK |
| 0048 | hibás ragozás | Debrecenre -> Debrecenbe | OK |
| 0051 | elgépelés | akrok -> akarok; megazni -> megázni | OK |
| 0053 | szóköz- és írásjelhiba | csak szóköz/írásjel/nagybetű | OK |
| 0056 | hibás ragozás | telefonomnak a -> telefonom | OK |
| 0058 | ékezet nélkül | Segitsetek otletet -> Segítsetek ötletet; unokahugom szuletesnapjara tiz eves -> az unokahúgom születésnapjára tíz éves; es -> és | OK |
| 0061 | kérdés félreütésekkel | lefagyaszatni -> lefagyasztani | OK |
| 0063 | hosszabb kusza mondat | hütö -> hűtő; fagyaszto -> fagyasztó; hütö -> hűtő; szerelöt -> szerelőt | OK (javított: ö/ő, o/ó zaj hozzáadva) |
| 0066 | hibás ragozás | + átmentünk; barátomnál mentünk át -> barátomhoz | OK |
| 0068 | ékezet nélkül | edzes kozben -> edzés közben; lendulets zenet szeretnek -> lendületes zenét szeretnék; tul -> túl | OK |
| 0071 | szóköz- és írásjelhiba | akövetkező -> a következő; Ittvárok -> Itt várok | OK |
| 0073 | hibás ragozás | hivatalba -> hivatalban | OK |
| 0076 | enyhe szleng | beparáztam h -> Megijedtem hogy; tök -> nagyon | OK |
| 0078 | indulatos, laza stílus | + mellette; - mellette | OK |
| 0081 | kérdés félreütésekkel | trukköt -> trükköt; sütőpapirhoz -> sütőpapírhoz; odraagad -> odaragad | OK |
| 0083 | elgépelés | hsszú -> hosszú | OK |
| 0086 | kérdés félreütésekkel | elkzedeni -> elkezdeni; munkat -> munkát; szeszéyes -> szeszélyes | OK |
| 0088 | elgépelés | + a; feladatábn -> feladatában; hogy -> hogyan | OK |
| 0091 | indulatos, laza stílus | ebbol -> ebből; eleg holnaptol kerekpárral -> elég Holnaptól kerékpárral; megbizhatatlan -> megbízhatatlan | OK |
| 0093 | indulatos, laza stílus | kenyerböl -> kenyérből; hazban -> házban | OK |
| 0096 | ékezet nélkül | szomszedok -> szomszédok; furnak hetvegen -> fúrnak hétvégén; mod -> mód; szoljak -> szóljak | OK |
| 0098 | enyhe szleng | király -> fantasztikus; tuti -> biztosan | OK |

**Eredmény: 40 / 40 megfelelt** (a három korábban gyenge zajú sor a javítás után). Az egész batchben 7 sort kellett javítani a clean előtt (5. fejezet), a hibaarány 7 / 100, a mintában 3 / 40;
mivel a hibák a minta olvasása előtt kiderültek és javultak, 40 soros minta elég volt, és nem kellett bővíteni.

## 7. Megfigyelések és korlátok (őszinte értékelés)

- **`instruction` mező**: lásd az elején; jóváhagyást igényel. A 29 különböző instruction-szöveg és a 4-es maximális ismétlés kicsi, de nem dedupe-kockázat.
- **A zaj szintetikus**: kézzel írt, de a valódi felhasználói zaj (pl. billentyűzet-szomszédság, autokorrektúra) szórása nagyobb; a következő batchekben érdemes több hibakombinációt (ékezet nélkül + rövidítés + szleng)
  és több témát bevinni. Ebben a batchben főleg egy dominánsan egy típusú zaj szerepel soronként (11 típus), keveset kevert.
- **Témaszórás**: 50 különböző téma 100 sorban, de a *főzés* (9 sor) és a *közlekedés* (6 sor) enyhén előre tör.
- **A validátor csak az outputot vizsgálja** torz tokenekre és angol keveredésre; az input szándékosan zajos, ezért az inputra ezek a szabályok nem vonatkoznak.
- **Az ismeretlen-szó arány heurisztika** (a 3100 sor szókincse magyar ragozás miatt hiányos), csak sorpáronkénti összevetésre jó.
- **`zajos bemenet` tag 3.2%**: az új csomagot jelölő tag, nem témaszaturáció.
- **Az ellenőrző scriptek** (`noisy_check.py`, `gen_noisy_batch1.py`) a repón kívül vannak; a `tools/` alá emelésük külön jóváhagyandó.

## 8. Fájlok

- Raw: `data/raw/claude_noisy_input_0001_0100_raw.jsonl` (100 sor)
- Clean: `data/clean/claude_noisy_input_0001_0100_clean.jsonl` (100 sor)
- Rejected: `data/rejected/claude_noisy_input_0001_0100_rejected.jsonl` (0 sor, üres fájl)
- Report: `data/reports/claude_noisy_input_0001_0100_report.md`

## 9. Amit ez a kör NEM tett

- Nem indított tanítást, nem módosított webapp/backend kódot, nem törölt és nem írt felül semmit (a validátorhoz sem nyúlt).
- Nem készítette el a `noisy_input_0101-0500` sorokat (külön jóváhagyásra várnak).
- Nem használt webes forrást, valós felhasználói szöveget, ChatGPT/Dispatch raw jelöltet.
- Nem módosította a topic report tag-kezelését, és nem emelte a scripteket a repóba.

---

## Végső összegzés

- Batch: 100 sor, **100 clean / 0 rejected**, átlag score 100.0, regressziós teszt STABIL.
- Zajtípusok: 11 típus (8-10 sor), 50 téma; az output megtartja a felhasználó hangját és szándékát, nem hivatalos, nem válasz.
- Ellenőrzések: 100/100 valid, input != output, 0 duplikátum és 0 kereszt-találat a 3000 sor ellen, 0 PII/URL/identity bleed/káromkodás; ismeretlen-szó arány 0.266 -> 0.175.
- Manuális: mind a 100 sor elolvasva, formális minta 40/40 megfelelt; 7 sor javítva clean előtt.
- **Jóváhagyás kell**: az `instruction` mező (a repó sémája kéri, a megadott listában nem szerepelt).
- Teljes clean korpusz: **3100 sor**.

**STÁTUSZ: STABIL.**
