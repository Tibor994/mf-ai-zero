# Második noisy_input batch - noisy_input_0101-0200

Az 5. csomag (**Hibás user szöveg -> javított szöveg**, cél: 500 clean sor) **második 100 sora** (összesen 200 / 500). Kitalált, hétköznapi, magyar felhasználói
üzenetek és ezek természetes, érthető javított változata. Nincs valós személy/magánadat, URL, e-mail, telefonszám, cím, projektadat, tanács vagy megválaszolt kérdés:
az output mindig a felhasználó **saját üzenetének tisztább változata**, nem válasz rá, és nem hivatalosabb nála.

A batch az 1. batch korlátait célzottan javítja (lásd 0. fejezet): soronként több zajtípus keveredik, több a valódi telefonos gyorsgépelés-jellegű hiba, nincs „csak formai” sor,
100 különböző téma (a főzés/háztartás alig van jelen), és több a természetes, beszélt nyelvű szerkezet.

**Séma**: a 9 mezős repó-séma marad (`id, category, instruction, input, output, tags, difficulty, quality_notes, source`); az `instruction` mező megtartását **jóváhagytad** az 1. batch után.
30 különböző, kézzel írt, nem helyesírás-javító jellegű feladatmegfogalmazás (10 típus-specifikus + 20 általános), egy szöveg legfeljebb 4 sorban.

## 0. A kérés követelményei és teljesülésük

| Követelmény | Teljesülés |
|---|---|
| 100 clean sor, `noisy_input_0101`-`0200`, `category: noisy_input`, `source: synthetic_claude_magyar`, egyedi `quality_notes` | **100 clean / 0 rejected**, 100 / 100 egyedi quality_notes, az id-k folytonosak |
| Több vegyes zaj egy soron belül | **minden sor legalább 2, 76 sor 3 zajtípust kapott** (1. batch: 1 típus / sor); az összes zajcímke 276 |
| Több valódi telefonos gyorsgépelés-jellegű hiba | 44 sor telefonos címkével (27 elsődleges); billentyű-szomszédos/felcserélt/hiányos betűk (*hpgy, nrm, nert, vaty, elkzedtem, minig, mliyen, hogyna*), összeírt szavak (*nemtom, nemtudom, acsaladbol*), fél-ékezetes *õ*/*û* betűk, 83 kisbetűs kezdésű és 94 írásjel nélkül végződő input |
| Kevesebb csak formai zaj | **0 sor** kizárólag nagybetű/írásjel/szóköz-változással (1. batch: 9); minden sorban szóalak-szintű javítás van: 1-16, átlag 4.9 javított szóalak soronként |
| Több téma, ne a főzés/háztartás dominálja | **100 különböző téma** 100 sorban (1. batch: 50); főző/háztartási témájú sor 3, közlekedési 12 (1. batch: 9 + 6) |
| Természetesebb hétköznapi mondatok, több beszélt nyelvi szerkezet | 43 sorban van *beszélt nyelv* címke (*hát, izé, asszem, figyu, ja, szóval, mondjuk, ugye, vagy mi, meg*), 12 kusza, hosszabb mondat; a kifejezések 26 sorban az outputban is megmaradnak (ahol a jelölő kifejezés volt) |
| Az output ne legyen hivatalos, szándék és hang maradjon | output szószám / input szószám: 0.83 / 1.00 / 1.15 (min / átlag / max), medián 17 szó; szándékos megtartott hétköznapi szavak: *a fene, izé, figyu, figyi, pulcsi, suli, app, nasi, kaja, haver, kéne* |
| Kerülendők (PII, URL, e-mail, telefon, MF-AI/Nextora, erős káromkodás, érzékeny téma) | egyik sem szerepel (3. fejezet, 8. pont); erős káromkodás 0 (az egyetlen találat a *szarkasztikus* szó a `quality_notes`-ban: téves egyezés) |
| Input != output, valóban javított | 0 azonos sor; ismeretlen-szó arány 0.284 -> 0.143 (3. fejezet, 4. pont) |

## 1. Felépítés

| Zajtípus | Elsődleges (`tags[2]`) | Összes címke | Mi a zaj |
|---|---|---|---|
| telefonos gyors gépelés | 27 | 44 | kisbetűs, írásjel nélküli, sietős üzenet; szomszédos/felcserélt betűk (*hpgy, nrm, vaty*), összeírt szavak, *õ*/*û* |
| beszélt nyelv | 26 | 43 | *hát, izé, asszem, figyu, ja, ugye, mondjuk*, félbehagyott, hiányos szerkezet |
| hosszabb kusza mondat | 10 | 12 | egymásba folyó 25-35 szavas, írásjel nélküli mondat, több gondolat |
| indulatos, laza stílus | 8 | 12 | csupa nagybetű, felkiáltójel-halmozás, türelmetlen kifakadás |
| ékezet nélkül | 8 | 83 | teljes vagy részleges ékezethiány (*hetvegen, tortenelembol, kesek*) |
| rövidítés | 7 | 21 | *vmi, vki, vhol, kb, pl, h, kszi, nemtom, tel., akksi* |
| kérdés félreütésekkel | 6 | 27 | félreütött kérdés, hiányzó kérdőjel |
| elgépelés | 4 | 17 | felcserélt/hiányzó/dupla betű (*elkzedtem, minig, mliyen*) |
| hibás ragozás | 3 | 5 | rossz rag, egyeztetés (*nem passzoltak nekem senki*, *a lányának a suliba*) |
| szóköz- és írásjelhiba | 1 | 11 | összeragadt/széthúzott szavak, kettős szóköz, szóköz írásjel előtt |
| enyhe szleng | 0 | 1 | egyetlen másodlagos címke (a szleng-szavak a *beszélt nyelv* alatt szerepelnek) |

`tags` = `["magyar", "zajos bemenet"] + 2-3 zajtípus + [téma]` (5-6 elem; az 1. batch pontosan 4). 100 különböző téma (sorozatnézés, telefonfólia, röplabdaedzés, ajtócsengő,
elveszett sapka, első tájképrajz, billentyűzet, társasjáték-est, ügyfélszolgálat stb.). A zajtípus-címkék egy része automatikusan a szóalak-különbségből is kiegészült (ha egy sorban legalább 3 ékezetjavítás, kibontott rövidítés,
szóköz-/írásjelhiba vagy elgépelt szóalak van, a hiányzó címke fel lett véve, sorban legfeljebb 3-ig).
`difficulty`: a bemenet és a javított változat karakter-eltérése, a bemenet hossza és a zajtípusok száma szerinti rang: legnagyobb 20 = hard, következő 35 = medium, a többi 45 easy.
Az id-k deterministikus keverés (seed 20260923) után lettek kiosztva, nincs típus-blokk.

## 2. Számok

| Mérőszám | Érték |
|---|---|
| Raw sorok | 100 |
| Schema validáció (`dataset_validate.py`, raw és clean is) | 100 / 100 valid |
| `input` == `output` | 0 sor |
| Batchen belüli dedupe (id / instruction+input / output, 0.9) | 0 / 0 / 0 |
| Kereszt-dedupe a 3000 meglévő clean sor ellen (id; instruction+input, output, input-vs-input, input-vs-output >= 0.9) | 0 / 0 / 0 / 0 / 0 |
| **Végleges clean** | **100** |
| **Rejected** | **0** |
| Átlag quality_score | **99.9 / 100** (99 sor 100; a `noisy_input_0114` 90, ok: `low_instruction_overlap`, lásd 7. fejezet) |
| Difficulty | easy 45, medium 35, hard 20 |
| Egyedi input / output / quality_notes / instruction | 100 / 100 / 100 / 30 (egy instruction legfeljebb 4 sorban) |
| Zajtípus soronként | 3 típus: 76 sor, 2 típus: 24 sor |
| Output szószám (min / medián / max) | 5 / 17 / 32 |
| Output / input szóhossz-arány (min / átlag / max) | 0.83 / 1.00 / 1.15 |
| Karakter-szintű változás (1 - hasonlóság, min / medián / max) | 0.043 / 0.092 / 0.528 |
| Javított szóalakok soronként (elgépelés + ékezet + szétválasztás; min / átlag / max) | 1 / 4.9 / 16 |
| Szóalak-szintű javítás nélküli sor | **0** (28 sorban elgépelt szó, 100-ban ékezetjavítás, 4-ben összeírt szó szétválasztása, 23-ban rövidítés) |
| Ismeretlen szavak aránya a korpusz-szókincshez képest (input -> output átlag) | **0.284 -> 0.143** |
| Szándékmegőrzés (5 betűs tőszavak lefedettsége, input->output / output->input átlag) | 0.67 / 0.67 (az ékezet nélküli inputok tőszavai az ékezetek miatt nem egyeznek; 10 sor <0.5, mind kézzel átnézve, rendben) |
| Formai zajmarker az outputban | **0 sor** (az inputban 97 sor tartalmaz legalább egyet) |
| Identity bleed / saját projekt-említés / URL / e-mail / telefon- és cím-minta | 0 / 0 / 0 / 0 / 0 |
| Erős káromkodás, gyűlölet, érzékeny téma kulcsszó | 0 (*szarkasztikus* a `quality_notes`-ban: téves találat) |
| Topic report (3200 soros korpusz) | `összefoglalás` 15.6% (500 sor, dokumentált), `zajos bemenet` 6.2% (200 sor, a csomag jelölő címkéje); `ékezet nélkül` 2.9%; más túlreprezentált tag nincs |
| Teljes clean korpusz | **3200 sor** (1000 simple_qa, 1000 explanation, 500 step_by_step, 500 summary, 200 noisy_input) |

## 3. Ellenőrzési lépések

1. **Generálás**: 100 sor négy részben, soronként kézzel megírt input-output párokkal (nincs szabály- vagy sablongenerátor); az outputot mindig a saját inputjából levezetve írtam.
   Csoportok: 25 telefonos gyorsgépelés, 20 beszélt nyelvű, 10 kusza mondat, 8 indulatos, 8 félreütött kérdés, 8 részleges ékezethiány, 8 rövidítéses, 7 hibás ragos, 4 elgépelés, 2 szóköz-hibás.
2. **Schema**: `dataset_validate.py` 100/100; saját ellenőrzés a 9 kötelező mezőre, `category`, `source`, `difficulty`, a `tags` fejlécre és a 5-6 tag-hosszra.
3. **Input != output**: 0 azonos sor; minden sorban szóalak-szintű változás van.
4. **Valóban javítottabb-e**: (a) ismeretlen-szó arány a korpusz szókincséhez képest, sorpáronként (a batch saját fájlját a szókincsből kihagyva): 0.284 -> 0.143; egyetlen sor
   emelkedik (`0120`: *6kor* -> *6-kor*, a kötőjeles szám tokenje ismeretlen, nem hiba); (b) formai zajmarkerek az outputban: 0 sor; (c) nincs rövidítés, betűhalmozás és írásjel-halmozás az outputban.
5. **Szándékmegőrzés**: tőszó-átfedés + kézi olvasás; a 10 alacsony fedettségű sor (`0104, 0114, 0134, 0150, 0155, 0170, 0175, 0180, 0188, 0195`) mind ékezet nélküli/rövidítéses input, kézzel átnézve rendben.
6. **Batch dedupe**: id 0, instruction+input 0, output 0. Input-párok >= 0.7 hasonlóság: 0.
7. **Kereszt-dedupe a teljes korpusz ellen**: az új 100 sor a 3000 meglévő clean sorral szemben (`real_quick_ratio`/`quick_ratio` előszűréssel), 4 összevetésben; 0 találat, 0 id-ütközés.
8. **Safety/PII/identity bleed**: e-mail, URL, telefon/azonosító, irányítószám- és címminta 0; MF-AI/Nextora említés 0; `guard.looks_like_identity_bleed` 0; érzékeny témák
   (orvos, gyógyszer, ügyvéd, adó, hitel, szavazás, párt, szex, fegyver, drog, alkohol) 0 találat. A kérdések (pl. telefonfólia, szülinapi hely) az inputban maradnak, az outputban **nincs rájuk válasz vagy tanács**.
9. **Quality score**: 99.9 / 100.
10. **Regressziós teszt**: `tests/test_v1_7_4_dataset_foundation.py` - minden teszt sikeres, **STÁTUSZ: STABIL**.
11. **Manuális átolvasás és mintavétel**: mind a 100 sor input és output egymás mellett végigolvasva; formális minta 40 sor (6. fejezet).
12. **Clean/rejected/report**: clean 100, rejected 0 (üres fájl), ez a report; **progress** frissítve (helyi fájl, szándékosan nincs commitolva).

## 4. Mi számít javításnak (és mi nem)

- **Javítás**: elgépelés, hiányzó ékezet, rövidítések kibontása (*vmi, vki, kb, pl, h, nemtom, kszi -> köszi*), az összeragadt vagy széthúzott szavak rendbetétele, hibás rag/egyeztetés, a kérdőjel pótlása ott,
  ahol az input maga kérdés, a kusza mondat tagolása. A **sorrend és a tartalom** megmarad.
- **Nem javítás (szándékosan)**: a felhasználó hangját adó szavak maradnak (*a fene, izé, figyu/figyi, pulcsi, suli, app, nasi, kaja, haver, kéne, ugye, vagy mi, mint egy szobor, mint egy kutya*),
  a bizonytalanság és az indulat, a kérdés kérdés marad, a kijelentés kijelentés. Nem került be új szó, tanács vagy magyarázat.
- **Ami nincs benne**: helyesírási szabály, tanács, válasz a kérdésre, hivatalosabb átfogalmazás, új tartalom.

## 5. Önkorrekciók az összeállítás és a teljes átolvasás során (mind clean előtt)

- **Téma-túlsúly**: az első összeállításban a sorok 21%-a közlekedési témájú volt (busz, vonat, menetrend, megálló); **9 sort lecseréltem** más témájú, új sorra (sorozatnézés, röplabdaedzés, társasjáték-est, hó és 15 fok, történelemdolgozat,
  szomszéd néni kérése, elveszett sapka, első tájképrajz, billentyűzet) -> közlekedés 12 sor, főzés/háztartás 3 sor.
- **Közel-duplikátum input**: a `0144`/`0193` ("kocsival vagy vonattal...") párt a lecserélés megszüntette; input-pár >= 0.7: 0.
- **Ismétlődő instruction**: az első összeállításban egy típus-specifikus instruction 9 sorban szerepelt -> legfeljebb 4 ismétlés / szöveg (30 különböző szöveg).
- **Formai jelölő az outputban**: 2 outputban *?!* maradt -> egyetlen írásjelre (*?*) cserélve.
- **Címkék (7)**: hibás vagy pontatlan zajcímkék javítva: *kevert kérdés* (nem létező típus) -> *kérdés félreütésekkel*; az ügyfélszolgálat, gyerekprogram, levél a tanárnak, késő vonat sorok *hibás ragozás*/*kérdés félreütésekkel*
  címkéje (nincs rag-hiba / kérdés az inputban) -> *szóköz- és írásjelhiba*; telefonfólia (*hibás ragozás* -> *ékezet nélkül*); esti program (*elgépelés* -> *ékezet nélkül*).
- **Szándék/hang az outputban (3)**: a `0193` sorban az output elhagyta a *ja* töltelékszót (*na ja szóval* -> *Na, szóval*), most *Na, ja, szóval*; a kirándulási sorban az input már helyes *kiránduláshoz* szóalakját nem írtam át *kirándulásra*-ra (felesleges változtatás); a *kszi* outputja *kösz* helyett **köszi** lett (a hangnem hű megtartása).
- A 10 alacsony fedettségű sor és az egyetlen OOV-emelkedés (`0120`) kézi átnézése módosítást nem igényelt.

## 6. Manuális mintavétel (formális 40 sor)

A minta rögzített szabály szerint készült (az id sorszáma 5-tel osztva 1 vagy 3 maradékot ad: 40 sor), nem válogatott. Mind a 100 sort elolvastam, a minta ennek a dokumentált része. Az értékelés a fenti javítások után történt.

| id | Zajtípusok (`tags`) | Konkrét javítások (szó-szintű különbség; a nagybetű- és írásjel-változás nem szerepel) | Értékelés |
|---|---|---|---|
| 0101 | indulatos, laza stílus + szóköz- és írásjelhiba + ékezet nélkül | egyszeruen -> Egyszerűen; ertem -> értem; miert -> miért; normalis valaszt -> normális választ; ugyfelszolgalattol -> ügyfélszolgálattól; mondjak -> mondják; visszahiv... | OK |
| 0103 | rövidítés + ékezet nélkül + elgépelés | en pl -> Én például; zenet -> zenét; tel akksija -> telefon akkuja; lemerul -> lemerül; ugy 5re -> úgy 5 re; erek -> érek | OK |
| 0106 | beszélt nyelv + telefonos gyors gépelés + ékezet nélkül | dicser -> dicsér; allitolag -> állítólag; resz utan -> rész után; jo -> jó | OK |
| 0108 | hosszabb kusza mondat + telefonos gyors gépelés + ékezet nélkül | szallast -> szállást; odaertunk kiderult -> odaértünk kiderült; szomszedban -> szomszédban; es -> és; szomszed -> szomszéd; szoval fel oraig varakoztunk -> Szóval fél... | OK |
| 0111 | ékezet nélkül + kérdés félreütésekkel | jo -> jó; cipo meretben -> cipő méretben; mar -> már; lakasban -> lakásban | OK |
| 0113 | telefonos gyors gépelés + beszélt nyelv + rövidítés | hazibuli -> házibuli; nalunk es nemtom hany -> nálunk és nem tudom hány; hivjak -> hívjak | OK |
| 0116 | telefonos gyors gépelés + indulatos, laza stílus + ékezet nélkül | billentyuzetemen nehany -> billentyűzetemen néhány; mukodik es mar -> működik és már; ujra -> újra; inditani -> indítani; gepet -> gépet | OK |
| 0118 | telefonos gyors gépelés + ékezet nélkül + elgépelés | sziaa -> Szia; kezdodik -> kezdődik; nert -> Mert; kesek szoljatok -> késem szóljatok; mar elkezdtek -> már elkezdtétek | OK |
| 0121 | beszélt nyelv + ékezet nélkül | agyra es mar -> ágyra és már; merges -> mérges; sarral -> sárral | OK |
| 0123 | elgépelés + beszélt nyelv | Elkzedtem -> Elkezdtem; minig -> mindig; szinket -> színeket; ugy nez -> úgy néz | OK |
| 0126 | hosszabb kusza mondat + szóköz- és írásjelhiba + ékezet nélkül | ket muszakot -> két műszakot; vallalnom -> vállalnom; kollega -> kolléga; mondtak -> mondták; pentekre -> péntekre; igy -> így | OK |
| 0128 | rövidítés + telefonos gyors gépelés + ékezet nélkül | mar -> már; ido -> idő; bejarathoz -> bejárathoz | OK |
| 0131 | telefonos gyors gépelés + kérdés félreütésekkel + ékezet nélkül | jatek -> játék; ota lassu -> óta lassú; mar -> már; toltodik -> töltődik; csinalnom -> csinálnom | OK |
| 0133 | szóköz- és írásjelhiba + telefonos gyors gépelés | eső kabat -> esőkabát; kabat -> kabát | OK |
| 0136 | beszélt nyelv + hibás ragozás + elgépelés | roplabda edzesen -> röplabdaedzésen; + senki; passzoltak -> passzolt; senki es mar -> és már; nezek -> nézek | OK |
| 0138 | kérdés félreütésekkel + beszélt nyelv + ékezet nélkül | jo konyv -> jó könyv; hetvegen -> hétvégén; tul vekony es -> túl vékony és; tul hosszu -> túl hosszú | OK |
| 0141 | beszélt nyelv + elgépelés + ékezet nélkül | furcsan zorog -> furcsán zörög; kanyaridok -> kanyarodom; szerelöhöz -> szerelőhöz; mar -> már | OK |
| 0143 | telefonos gyors gépelés + rövidítés + ékezet nélkül | hetvegen koltozom es meg -> Hétvégén költözöm és még; 9kor jon -> 9 kor jön | OK |
| 0146 | beszélt nyelv + telefonos gyors gépelés + ékezet nélkül | szoval -> Szóval; hirek -> hírek; lat esot -> látok esőt; ki ne -> kinek | OK |
| 0148 | beszélt nyelv + rövidítés + ékezet nélkül | Hat en nemtom -> Hát én nem tudom; jo otlet -> jó ötlet; inkabb -> inkább; mar -> már | OK |
| 0151 | beszélt nyelv + szóköz- és írásjelhiba + ékezet nélkül | raj zoltam eloszor tajkepet es -> rajzoltam először tájképet és; tul jo -> túl jó; legalabb -> legalább; szamit -> számít | OK |
| 0153 | beszélt nyelv + ékezet nélkül + kérdés félreütésekkel | mondtak -> mondták; en -> én | OK |
| 0156 | telefonos gyors gépelés + kérdés félreütésekkel + ékezet nélkül | jatszoterrol es mar mindjart -> játszótérről és már mindjárt; csalljam -> csaljam | OK |
| 0158 | ékezet nélkül + beszélt nyelv | radioban -> rádióban; szamot -> számot; cimet -> címét; lassu -> lassú; es -> és; enekes -> énekes | OK |
| 0161 | ékezet nélkül + elgépelés | kiránduni -> kirándulni; utvonal -> útvonal; orank -> óránk | OK |
| 0163 | hosszabb kusza mondat + szóköz- és írásjelhiba + ékezet nélkül | irnom -> írnom; tanarnak -> tanárnak; lanyom pentektol -> lányom péntektől; csaladi -> családi; igy elhuzunk -> úgy elhúzunk | OK |
| 0166 | telefonos gyors gépelés + beszélt nyelv + ékezet nélkül | baratom eskuvojere -> barátom esküvőjére; es nemtom -> és nem tudom; fiuk -> Fiúk | OK |
| 0168 | telefonos gyors gépelés + beszélt nyelv + ékezet nélkül | idom orara jarni -> időm órára járni; ra idom -> rá időm | OK |
| 0171 | kérdés félreütésekkel + telefonos gyors gépelés + ékezet nélkül | hany -> Hány; tenyleg erezzem -> tényleg érezzem; kulonbseget -> különbséget; ketszer -> kétszer | OK |
| 0173 | ékezet nélkül + rövidítés | fesztivalra -> fesztiválra; jo cipo -> jó cipő; sar -> sár | OK |
| 0176 | beszélt nyelv + kérdés félreütésekkel + ékezet nélkül | macskam mostanaban -> macskám mostanában; szekreny tetejen -> szekrény tetején; es -> és; lejonni asszem -> lejönni Azt hiszem; igy -> így | OK |
| 0178 | ékezet nélkül + kérdés félreütésekkel | ajanlani -> ajánlani; jo -> jó; hetvegere -> hétvégére; szeretnenk -> szeretnénk; baratokkal -> barátokkal | OK |
| 0181 | beszélt nyelv + szóköz- és írásjelhiba + ékezet nélkül | kavezoban vart -> kávézóban várt; es -> és; beallni -> beálljak; inkabb -> inkább; tovabb -> tovább | OK |
| 0183 | telefonos gyors gépelés + beszélt nyelv + ékezet nélkül | szomszed -> szomszéd; kutyamat amig -> kutyámat amíg; kene megirnom -> kéne megírnom | OK |
| 0186 | ékezet nélkül + beszélt nyelv | tanarno -> tanárnő; kerte -> kérte; kiserlethez -> kísérlethez; meretut -> méretűt; tudjatok -> tudjátok | OK |
| 0188 | hibás ragozás + beszélt nyelv | kollegam -> kollégám; jonni -> jönni; lanyanak a suliba szuloi ertekezlet -> lánya sulijában szülői értekezlet | OK |
| 0191 | rövidítés + kérdés félreütésekkel + elgépelés | vki -> Valaki; h -> hogy; konyvtar -> könyvtár; kb -> körülbelül; oraig -> óráig | OK |
| 0193 | beszélt nyelv + hibás ragozás + elgépelés | szoval -> szóval; elmegyunk -> elmegyünk; vonatnal -> vonattal | OK |
| 0196 | telefonos gyors gépelés + kérdés félreütésekkel + ékezet nélkül | latta -> látta; kek sapkamat -> kék sapkámat; bejaratnal -> bejáratnál; mar -> már; emlekszem -> emlékszem | OK |
| 0198 | beszélt nyelv + indulatos, laza stílus + ékezet nélkül | csinalni -> csinálni; csoportmunkaban -> csoportmunkában; tobbiek -> többiek; nezik -> nézik; dolgozok ugy -> dolgozom úgy | OK |

**Eredmény: 40 / 40 megfelelt** (a minta szempontjai: input és output jelentése azonos, nincs új tartalom, hang megmaradt, nem hivatalos, az output valóban tisztább). A teljes 100 soros olvasásból a 7. és 5. fejezetben leírtak
javultak; a mintában maradt hiba nem volt.

## 7. Megfigyelések és korlátok (őszinte értékelés)

- **Az `ékezet nélkül` címke soronként szinte mindenhol szerepel (83 sor)**: a telefonos gyors gépelés hétköznapi velejárója, ezért a címke a soroknak szinte mindegyikén rajta van; a típusonkénti elsődleges eloszlás
  (`tags[2]`) kiegyensúlyozottabb. A `topic_report` szerint az `ékezet nélkül` tag a teljes korpusz 2.9%-a, nem túlreprezentált.
- **Alacsony szándékmegőrzési mutató (0.67, 1. batch: 0.84)**: az 5 betűs tőszó-átfedés az ékezet nélküli inputoknál a hiányzó ékezetek miatt eleve nem egyezik; ez a mérőszám torzítása, nem tartalmi eltérés, a 10 alacsony sort kézzel átnéztem.
- **`noisy_input_0114` score 90**: a `low_instruction_overlap` szabály az 5 szavas output és az instruction rövid átfedését jelzi; a sor tartalma rendben van, az instruction-t nem írtam át csak a pontszám miatt.
- **A zaj szintetikus**: kézzel írt, de a valódi felhasználói zaj (autokorrektúra, valódi billentyűzet-szomszédság) szórása nagyobb; billentyű-szomszédos betűhiba kb. 11 sorban van, *õ*/*û* csak 1 sorban (`0104`).
- **Tömör, kisbetűs inputok magas aránya (83 kisbetűs kezdés, 94 írásjel nélküli vég)**: szándékos (telefonos gépelés), de a 3. batchben érdemes több rendesen tagolt, csak 1-2 szóalak-hibás üzenetet is bevinni, hogy az arány ne torzuljon.
- **Az ismeretlen-szó arány heurisztika**: a korpusz szókincse magyar ragozás miatt hiányos, csak sorpáronkénti összevetésre jó (a kötőjeles szám-ragok, pl. *6-kor*, ismeretlen tokenek).
- **Az ellenőrző scriptek** (`noisy_check2.py`, `noisy_extra.py`, `gen_noisy_batch2.py`) a repón kívül vannak; a `tools/` alá emelésük külön jóváhagyandó. A keresztdedupe-szűrő és az OOV-mérés a batch saját fájlját kihagyja.
- **A validátor csak az outputot vizsgálja** torz tokenekre és angol keveredésre; az input szándékosan zajos.

## 8. Fájlok

- Raw: `data/raw/claude_noisy_input_0101_0200_raw.jsonl` (100 sor)
- Clean: `data/clean/claude_noisy_input_0101_0200_clean.jsonl` (100 sor)
- Rejected: `data/rejected/claude_noisy_input_0101_0200_rejected.jsonl` (0 sor, üres fájl)
- Report: `data/reports/claude_noisy_input_0101_0200_report.md`

## 9. Amit ez a kör NEM tett

- Nem indított tanítást, nem módosított webapp/backend kódot, nem törölt és nem írt felül semmit (az 1. batch fájljaihoz és a validátorhoz sem nyúlt).
- Nem készítette el a `noisy_input_0201-0500` sorokat (külön jóváhagyásra várnak).
- Nem használt webes forrást, valós felhasználói szöveget, ChatGPT/Dispatch raw jelöltet.
- Nem módosította a topic report tag-kezelését, és nem emelte a scripteket a repóba.

---

## Végső összegzés

- Batch: 100 sor, **100 clean / 0 rejected**, átlag score 99.9, regressziós teszt STABIL.
- Az 1. batch korlátainak javítása: 2-3 zajtípus minden soron (76 sor 3), 0 csak formai sor, 100 különböző téma (közlekedés 12, főzés/háztartás 3), több telefonos gyorsgépelés és beszélt nyelvű üzenet.
- Ellenőrzések: 100/100 valid, input != output, 0 duplikátum és 0 kereszt-találat a 3000 sor ellen, 0 PII/URL/identity bleed/erős káromkodás; ismeretlen-szó arány 0.284 -> 0.143.
- Manuális: mind a 100 sor elolvasva, formális minta 40/40 megfelelt; az összeállítás közben javított hibák az 5. fejezetben.
- Teljes clean korpusz: **3200 sor**; 5. csomag: 200 / 500.

**STÁTUSZ: STABIL.**
