# Negyedik noisy_input batch - noisy_input_0301-0400

Az 5. csomag (**Hibás user szöveg -> javított szöveg**, cél: 500 clean sor) **negyedik 100 sora** (összesen 400 / 500). Kitalált, hétköznapi, magyar felhasználói üzenetek és ezek természetes, érthető javított változata.
Nincs valós személy/magánadat, URL, e-mail, telefonszám, cím, projektadat, tanács vagy megválaszolt kérdés: az output mindig a felhasználó **saját üzenetének tisztább változata**, nem válasz rá, és nem hivatalosabb nála.

A 3. batch jó irányát tartja (rendesen tagolt, de hibás chat-üzenetek, magas szándékmegőrzés, kevés teljesen szétesett input), és **négy típust erősít**, amelyekből a 3. batchben kevés volt: *indulatos*, *hosszabb kusza mondat*, *enyhe szleng* és *kérdés félreütésekkel* (3. batch: 5 / 4 / 4 / 3 sor; itt 16 / 17 / 28 / 28).

**Séma**: a 9 mezős repó-séma marad (`id, category, instruction, input, output, tags, difficulty, quality_notes, source`), az `instruction` mező megtartása jóváhagyott. 30 különböző, kézzel írt, nem helyesírás-javító jellegű feladatmegfogalmazás (típus-specifikus és általános), egy szöveg legfeljebb 4 sorban;
az 1-3. batch 90 instruction-szövegével egyik sem egyezik (az összeállító szkript ezt minden futáskor ellenőrzi).

## 0. A kérés követelményei és teljesülésük

| Követelmény | Teljesülés |
|---|---|
| 100 clean sor, `noisy_input_0301`-`0400`, `category: noisy_input`, `source: synthetic_claude_magyar`, egyedi `quality_notes` | **100 clean / 0 rejected**, 100 / 100 egyedi quality_notes, az id-k folytonosak |
| Magas szándékmegőrzés | tőszó-átfedés input->output / output->input **0.93 / 0.91** (3. batch: 0.91 / 0.88); egyetlen sor sem esik 0.5 alá; output / input szószám 0.92 / 1.00 / 1.00 (min / átlag / max) |
| Természetes magyar chat-stílus | 84 sor nagybetűvel kezdődik, 37 sor teljes mondatokkal és záró írásjellel; köszöntés, megszólítás, kérdés a közönséghez (*Srácok, …*, *Sziasztok!*, *Ti is úgy vagytok vele, hogy…?*, *Ismertek valami tök jó helyet…?*); megtartott hétköznapi szavak: *tök* (25 sor), *szóval*, *suli*, *haver*, *tesó*, *pulcsi*, *meló*, *sajna*, *anyu*, *persze*, *király*, *ciki*, *para*, *a fene*, *hülye* |
| Kevesebb teljesen szétesett, ékezet nélküli input | kisbetűs kezdés és írásjel nélküli vég **16 sorban** (3. batch: 34; 2. batch: 81); ≥ 15 szavas, kisbetűs, írásjel nélküli **11 sor** (3. batch: 15); ékezet-javítás összesen 20 sorban (3. batch: 42), az *ékezet nélkül* címke 18 sorban (elsődleges: 1) |
| Több normálisan tagolt, de hibás user üzenet | **86 sorban legfeljebb 2, 94 sorban legfeljebb 3 szóalak-szintű javítás** (3. batch: 75 / 83); nagybetűs kezdés és legfeljebb 3 javítás: 84 sor (3. batch: 62); javított szóalak / input szó arány 0.094 (3. batch: 0.124) |
| Az output javítson, de tartsa meg a user hangját | a teljes átolvasás szerint nincs sor, ahol az output hivatalosabbra váltana; a szleng és a beszélt szavak megmaradnak (*tök jó*, *ciki*, *király ötlet*, *tuti*), csak a hibás alak javul (*szval* -> *szóval*, *cikki* -> *ciki*, *akksi* -> *akku*) |
| Minden sorban valódi szóalak-szintű javítás | **100 / 100 sor**; csak nagybetű/írásjel/szóköz-változású sor: 0 (az összeállítás közben talált 5 ilyen gyenge sort javítottam, lásd 5. fejezet) |
| 2-3 zajtípus soronként | 87 sor 3, 13 sor 2 típussal |
| Több indulatos, kusza mondat, enyhe szleng, kérdés-félreütés | összes címke: *kérdés félreütésekkel* 28, *enyhe szleng* 28, *hosszabb kusza mondat* 17, *indulatos, laza stílus* 16 (3. batch: 3 / 4 / 4 / 5) |
| Változatos téma | **100 különböző téma**, egyik sem szerepelt az 1-3. batch 247 témája között; közlekedési téma 0, főzés/háztartás 3 sor |
| Kerülendők (PII, URL, e-mail, telefon, MF-AI/Nextora, erős káromkodás, érzékeny téma) | egyik sem szerepel (3. fejezet, 9. pont); enyhe indulatszó: *a fene*, *hülye program*, *tényleg lehetetlen* |
| Input != output | 0 azonos sor; ismeretlen-szó arány 0.148 -> 0.116 (3. fejezet, 4. pont) |

## 1. Felépítés

A négy csoport az összeállítás négy részét jelöli; a típusok átfedik egymást (pl. az 1. részben is van szleng és kérdés).

| Csoport | Sor | Jellemző |
|---|---|---|
| Indulatos és kusza mondatok, tagolt, de hibás | 25 | kettős felkiáltójel, számonkérő hang, vessző nélküli, egymásba fonódó mondatok, 1-2 elütés |
| Félreütött kérdések és enyhe szleng | 25 | hiányzó betű a kérdésben, hiányzó kérdőjel; *tök*, *ciki*, *para*, *menő*, *cuki*, *király*; *szval* |
| Vegyes chat-üzenetek (szleng, kérdés, kusza, rövidítés) | 25 | kisbetűs, félig tagolt üzenetek, *pl/kb/vki/vmi/h*, 1-3 hiba |
| 8 erősen zajos + 17 vegyes | 25 | 8 kisbetűs, ékezet- és írásjel nélküli üzenet (indulatos, kusza, kérdés, szleng is), 17 rendesen tagolt, hibás üzenet |

| Zajtípus | Elsődleges (`tags[2]`) | Összes címke | Mi a zaj |
|---|---|---|---|
| elgépelés | 8 | 72 | hiányzó/dupla/felcserélt betű (*szürkr, jétszanak, minőségt, letnni, elaudtam*) |
| szóköz- és írásjelhiba | 1 | 50 | hiányzó vessző és záró írásjel, kettős felkiáltójel/kérdőjel, *e* kötőjel nélkül |
| beszélt nyelv | 0 | 30 | *szval*, *szóval*, *persze*, *Nem baj, majd…*, beszélt szerkezet |
| kérdés félreütésekkel | 24 | 28 | elütés egy kérdésben, hiányzó kérdőjel |
| enyhe szleng | 24 | 28 | *tök jó, tök ciki, tök para, tuti, király* |
| ékezet nélkül | 1 | 18 | teljes vagy részleges ékezethiány |
| hosszabb kusza mondat | 16 | 17 | vessző nélküli, 25-40 szavas, több tagmondatos mondat |
| indulatos, laza stílus | 16 | 16 | kettős felkiáltójel, *a fene*, *hülye*, *ez már elég*, türelmetlen hang |
| telefonos gyors gépelés | 5 | 11 | kisbetűs kezdés, hiányzó záró írásjel, sietős elütés |
| rövidítés | 3 | 11 | *kb, pl, vki, vkinek, vmi, h, 5kor* |
| hibás ragozás | 2 | 6 | *A előadás -> Az előadás, bankem -> bankom, barátomnál -> barátomtól, szomszédot -> szomszédnak* |

`tags` = `["magyar", "zajos bemenet"] + 2-3 zajtípus + [téma]` (5-6 elem). A zajcímkéket kézzel adtam és szkripttel ellenőriztem, lásd 3. fejezet, 5. pont.
`difficulty`: a bemenet és a javított változat karakter-eltérése, a bemenet hossza és a zajtípusok száma szerinti rang: legnagyobb 20 = hard, következő 35 = medium, a többi 45 easy.
Az id-k deterministikus keverés (seed 20260925) után lettek kiosztva, nincs típus- vagy csoportblokk.

## 2. Számok

| Mérőszám | Érték |
|---|---|
| Raw sorok | 100 |
| Schema validáció (`dataset_validate.py`, raw és clean is) | 100 / 100 valid |
| `input` == `output` | 0 sor |
| Batchen belüli dedupe (id / instruction+input / output, 0.9) | 0 / 0 / 0 |
| Kereszt-dedupe a **3300** meglévő clean sor ellen, beleértve az 1-3. noisy batchet (id; instruction+input, output, input-vs-input, input-vs-output >= 0.9) | 0 / 0 / 0 / 0 / 0 |
| **Végleges clean** | **100** |
| **Rejected** | **0** |
| Átlag quality_score | **100.0 / 100** (minden sor 100) |
| Difficulty | easy 45, medium 35, hard 20 |
| Egyedi input / output / quality_notes / instruction | 100 / 100 / 100 / 30 (egy instruction legfeljebb 4 sorban) |
| Zajtípus soronként | 3 típus: 87 sor, 2 típus: 13 sor |
| Output szószám (min / medián / max) | 9 / 18 / 39 |
| Output / input szóhossz-arány (min / átlag / max) | 0.92 / 1.00 / 1.00 |
| Karakter-szintű változás (1 - hasonlóság, min / medián / max) | 0.004 / 0.019 / 0.350 (szándékosan kicsi: a legtöbb sorban 1-2 szót kell javítani) |
| Javított szóalakok soronként (min / átlag / medián / max) | 1 / 1.7 / 1 / 11 (3. batch: 1 / 2.5 / 2 / 10) |
| Szóalak-szintű javítás nélküli sor / csak formai sor | **0 / 0** |
| Ismeretlen szavak aránya a korpusz-szókincshez képest (input -> output átlag) | **0.148 -> 0.116** (3. batch: 0.187 -> 0.151) |
| Szándékmegőrzés (5 betűs tőszavak lefedettsége, input->output / output->input átlag) | **0.93 / 0.91** |
| Formai zajmarker az outputban | **0 sor** (az inputban 69 sor tartalmaz legalább egyet) |
| Identity bleed / saját projekt-említés / URL / e-mail / telefon- és cím-minta | 0 / 0 / 0 / 0 / 0 |
| Erős káromkodás, gyűlölet, érzékeny téma kulcsszó | 0 |
| Topic report (3400 soros korpusz) | `zajos bemenet` **11.8%** (400 sor; a csomag jelölő címkéje, a küszöb 8%, lásd 7. fejezet), `összefoglalás` 14.7% (500 sor, dokumentált), `ékezet nélkül` 4.4% |
| Teljes clean korpusz | **3400 sor** (1000 simple_qa, 1000 explanation, 500 step_by_step, 500 summary, 400 noisy_input) |

### A négy noisy batch összevetése (ugyanazokkal az ellenőrzőkkel mérve)

| Mutató | 1. batch | 2. batch | 3. batch | 4. batch |
|---|---|---|---|---|
| Zajtípus soronként | 1 | 2-3 (76 sor 3) | 2-3 (60 sor 3) | 2-3 (87 sor 3) |
| Nagybetűs kezdés | 69 | 17 | 63 | 84 |
| Írásjellel záródó input | 31 | 6 | 43 | 37 |
| Sem kezdő nagybetű, sem záró írásjel | 25 | 81 | 34 | 16 |
| Legfeljebb 3 javított szóalak | 63 | 14 | 83 | 94 |
| Javított szóalak / input szó | 0.209 | 0.347 | 0.124 | 0.094 |
| Szándékmegőrzés (input->output) | 0.84 | 0.67 | 0.91 | 0.93 |
| Indulatos / kusza / szleng / félreütött kérdés címke | - | - | 5 / 4 / 4 / 3 | 16 / 17 / 28 / 28 |
| Különböző téma | 50 | 100 | 100 | 100 |

## 3. Ellenőrzési lépések

1. **Generálás**: 100 sor négy részben, soronként kézzel megírt input-output párokkal (nincs szabály- vagy sablongenerátor); az outputot mindig a saját inputjából levezetve írtam.
2. **Schema**: `dataset_validate.py` 100/100; saját ellenőrzés a 9 kötelező mezőre, `category`, `source`, `difficulty`, a `tags` fejlécre és az 5-6 tag-hosszra; téma-egyediség a batchen belül és az 1-3. batch 247 témájával szemben; instruction-szövegek eltérése az előző 90-től.
3. **Input != output**: 0 azonos sor; minden sorban szóalak-szintű változás van (0 csak formai sor).
4. **Valóban javítottabb-e**: (a) ismeretlen-szó arány a korpusz szókincséhez képest, sorpáronként (a batch saját fájlját a szókincsből kihagyva): 0.148 -> 0.116; egyetlen sor emelkedik (`0397`: 0.06 -> 0.07, ritka, de helyes szóalak miatt);
   (b) formai zajmarkerek az outputban: 0 (az első futáson az *akksi* jelzett, lásd 5. fejezet); (c) nincs rövidítés, betűhalmozás és írásjel-halmozás az outputban.
5. **Zajcímkék bizonyítéka**: külön szkript minden sorra ellenőrzi, hogy a címkéhez tartozik-e szóalak-szintű nyom. Első futás 14 sort jelzett; javítva: `0342`, `0344`, `0399` (*elgépelés* -> *ékezet nélkül*, mert tiszta ékezethiány volt).
   A maradék 11 jelzés kézzel átnézve: `0302` (*melég*) és `0341` (*mielött*) rossz ékezetű elütés, az *elgépelés* címke jogos; `0380` (*vkinek*) és `0314`, `0393` (*szoval*) téves jelzés (a szkript szótára nem ismeri az ékezet nélküli alakot);
   `0391` határeset a *hosszabb kusza mondat* címkénél (22 szavas, vessző nélküli mondat); a *beszélt nyelv* címke az `0317, 0318, 0345, 0350, 0357` sorokban gyenge bizonyítékú (a fordulat megmaradt, nem javítás tárgya), ezeket nem vettem le, de a korlátoknál (7. fejezet) jelzem.
6. **Szándékmegőrzés**: tőszó-átfedés 0.93 / 0.91 (egyetlen sor sem < 0.5) + kézi olvasás.
7. **Batch dedupe**: id 0, instruction+input 0, output 0. Input-párok >= 0.7 hasonlóság: 0.
8. **Kereszt-dedupe a teljes korpusz ellen**: az új 100 sor a **3300** meglévő clean sorral szemben (az 1-3. noisy batch is benne van; `real_quick_ratio`/`quick_ratio` előszűréssel), 4 összevetésben; 0 találat, 0 id-ütközés.
9. **Safety/PII/identity bleed**: e-mail, URL, telefon/azonosító, irányítószám- és címminta 0; MF-AI/Nextora említés 0; `guard.looks_like_identity_bleed` 0; erős káromkodás 0; érzékeny téma kulcsszó 0. Enyhe indulatszó: *a fene* (`0331`), *hülye program* (`0394`), *ez már elég* (`0301`), *tényleg lehetetlen* (`0335`).
   A kérdések (pl. függönyszín, filctoll-folt, játékhely, pulcsi-méret, podcast) az inputban maradnak, az outputban **nincs rájuk válasz vagy tanács**. Az egyetlen „hogyan” jellegű tanácskérés (`0318`, filctoll-folt) háztartási, nem orvosi, jogi vagy pénzügyi.
10. **Quality score**: 100.0 / 100.
11. **Regressziós teszt**: `tests/test_v1_7_4_dataset_foundation.py` - minden teszt sikeres, **STÁTUSZ: STABIL**.
12. **Manuális átolvasás és mintavétel**: mind a 100 sor input és output egymás mellett végigolvasva; formális minta 40 sor (6. fejezet).
13. **Clean/rejected/report**: clean 100, rejected 0 (üres fájl), ez a report; **progress** frissítve (helyi fájl, szándékosan nincs commitolva).

## 4. Mi számít javításnak (és mi nem)

- **Javítás**: elgépelés (*szürkr -> szürke*), hiányzó ékezet (*hiányzo -> hiányzó*), rövidítések kibontása (*vki, vkinek, kb, pl, h, szval*), hibás rag/névelő (*A előadás -> Az előadás, ablak alá áll -> ablak alatt áll*), hiányzó vesszők és záró írásjel, a kettős felkiáltójel/kérdőjel egyre csökkentése, a kérdőjel pótlása ott, ahol az input maga kérdés.
  A **sorrend és a tartalom** megmarad.
- **Nem javítás (szándékosan)**: a felhasználó hangját adó szavak és szerkezetek maradnak (*tök, ciki, para, tuti, király, meló, suli, pulcsi, anyu, sajna, hülye program, a fene*), az indulat (*ez már tényleg nem normális*), a bizonytalanság (*lehet, hogy*, *azt hiszem*), a kérdés kérdés marad.
  Nem került be új szó, tanács vagy magyarázat.
- **Ami nincs benne**: helyesírási szabály, tanács, válasz a kérdésre, hivatalosabb átfogalmazás, új tartalom.

## 5. Önkorrekciók az összeállítás és a teljes átolvasás során (mind clean előtt)

- **Csak formai vagy gyenge sor (5)**: az első változatban `bezárt ajtó`, `szülői értekezlet ideje`, `prezentáció előtt` és `új poszter` sorban a kért szóalak-szintű hiba hiányzott (csak vessző/kérdőjel), a `csöpögő hang` sor pedig hibás volt: az output egy mondatot **elhagyott** (tartalomvesztés), a jegyzet pedig zavaros volt. Mindegyikbe valódi elütés került (*mielött, értekelet, prezetálnom, poszrert, fürdőbn*), és a `csöpögő hang` sor input-output párja rendbe lett téve.
- **Jegyzet-hiba (5)**: az előző pontbeli sorok és a `kölcsönkapott hosszabbító` quality_notes-ában zárójeles, homályos kitétel (pl. „a sor másik hibája…”) maradt; kicseréltem konkrét, sorra szóló megfogalmazásra.
- **Címkék (3)**: `0342`, `0344`, `0399`, lásd 3. fejezet, 5. pont.
- **Ellenőrzőt kiváltó szó (1)**: az `új okosóra` sor outputjában az *akksi* formai markerként jelzett; *akku* lett, a szleng *tök menő* megmaradt.
- **Félreérthető input/output (1)**: a `közös ebéd` sor első változata (*vki nem ér rá esetleg*) az outputban értelmetlen mondattá vált (*valaki nem ér rá esetleg?*); a szándékolt jelentés (*vki ráérne esetleg*) lett az input és az output.
- **Jegyzet-tartalom (1)**: a `csapatterv leadása` jegyzet olyan idézetet említett, ami nem volt a sorban; kijavítva.
- A 11 címke-jelzés és az 1 OOV-emelkedés kézi átnézése további módosítást nem igényelt.

## 6. Manuális mintavétel (formális 40 sor)

A minta rögzített szabály szerint készült (az id sorszáma 5-tel osztva 1 vagy 3 maradékot ad: 40 sor), nem válogatott. Mind a 100 sort elolvastam, a minta ennek a dokumentált része. Az értékelés az 5. fejezetben leírt javítások után történt.

| id | Zajtípusok (`tags`) | Konkrét javítások (szó-szintű különbség; a nagybetű- és írásjel-változás nem szerepel) | Értékelés |
|---|---|---|---|
| 0301 | indulatos, laza stílus + ékezet nélkül + szóköz- és írásjelhiba | zarva es -> zárva és; mondtak -> mondták; mar eleg -> már elég | OK |
| 0303 | hosszabb kusza mondat + szóköz- és írásjelhiba + elgépelés | kapkdni -> kapkodni | OK |
| 0306 | elgépelés + beszélt nyelv + szóköz- és írásjelhiba | hazajöon -> hazajön; szval -> szóval | OK |
| 0308 | enyhe szleng + elgépelés + beszélt nyelv | megengdte -> megengedte; szval -> szóval | OK |
| 0311 | kérdés félreütésekkel + elgépelés + szóköz- és írásjelhiba | szombtra -> szombatra | OK |
| 0313 | hosszabb kusza mondat + szóköz- és írásjelhiba + elgépelés | pótlni -> pótolni | OK |
| 0316 | enyhe szleng + elgépelés + beszélt nyelv | szürkke -> szürke; szval -> szóval | OK |
| 0318 | kérdés félreütésekkel + elgépelés + beszélt nyelv | filctolat -> filctollat | OK |
| 0321 | kérdés félreütésekkel + telefonos gyors gépelés + elgépelés | értekelet -> értekezlet | OK |
| 0323 | elgépelés + szóköz- és írásjelhiba | elszaporotak -> elszaporodtak | OK |
| 0326 | kérdés félreütésekkel + ékezet nélkül + telefonos gyors gépelés | szinu fuggonyt -> színű függönyt; szobamba -> szobámba; vilagoszold -> világoszöld | OK |
| 0328 | hosszabb kusza mondat + elgépelés + szóköz- és írásjelhiba | felejthtett -> felejthetett | OK |
| 0331 | indulatos, laza stílus + kérdés félreütésekkel + elgépelés | srozat -> sorozat | OK |
| 0333 | indulatos, laza stílus + elgépelés + szóköz- és írásjelhiba | minőségt -> minőséget | OK |
| 0336 | indulatos, laza stílus + kérdés félreütésekkel + elgépelés | értsítést -> értesítést | OK |
| 0338 | hosszabb kusza mondat + szóköz- és írásjelhiba + elgépelés | elhalaszttam -> elhalasztottam | OK |
| 0341 | kérdés félreütésekkel + elgépelés + szóköz- és írásjelhiba | mielött -> mielőtt | OK |
| 0343 | rövidítés + szóköz- és írásjelhiba + beszélt nyelv | vki -> valaki; kb -> körülbelül; szval -> szóval | OK |
| 0346 | elgépelés + hibás ragozás | Átrendztem -> Átrendeztem; alá -> alatt | OK |
| 0348 | indulatos, laza stílus + elgépelés + szóköz- és írásjelhiba | Egysszer -> Egyszer | OK |
| 0351 | elgépelés + szóköz- és írásjelhiba | elfelejtete -> elfelejtette | OK |
| 0353 | enyhe szleng + rövidítés + elgépelés | pl -> például; vmi -> valami; érr -> ér | OK |
| 0356 | enyhe szleng + rövidítés + beszélt nyelv | akksi kb -> akku körülbelül; szval -> szóval | OK |
| 0358 | indulatos, laza stílus + ékezet nélkül + szóköz- és írásjelhiba | müködik -> működik | OK |
| 0361 | hosszabb kusza mondat + ékezet nélkül + szóköz- és írásjelhiba | mar -> már; kiderult -> kiderült; foglalas kesz -> foglalás kész; fizetes -> fizetés; ezert -> ezért | OK |
| 0363 | rövidítés + telefonos gyors gépelés + beszélt nyelv | kb -> körülbelül; szval -> szóval; pl -> például | OK |
| 0366 | indulatos, laza stílus + elgépelés + szóköz- és írásjelhiba | pillantban -> pillanatban | OK |
| 0368 | kérdés félreütésekkel + elgépelés | dmoinót -> dominót | OK |
| 0371 | kérdés félreütésekkel + elgépelés + beszélt nyelv | Elküldtd -> Elküldted | OK |
| 0373 | kérdés félreütésekkel + telefonos gyors gépelés + elgépelés | megkérdzhetem -> Megkérdezhetem | OK |
| 0376 | kérdés félreütésekkel + elgépelés + szóköz- és írásjelhiba | tegnp -> tegnap | OK |
| 0378 | kérdés félreütésekkel + elgépelés + szóköz- és írásjelhiba | könyvesboltt -> könyvesbolt | OK |
| 0381 | kérdés félreütésekkel + enyhe szleng + elgépelés | kényelmse -> kényelmes | OK |
| 0383 | enyhe szleng + elgépelés + szóköz- és írásjelhiba | letnni -> letenni | OK |
| 0386 | kérdés félreütésekkel + ékezet nélkül + elgépelés | kodom -> kódom; ellenörztem -> ellenőriztem | OK |
| 0388 | indulatos, laza stílus + elgépelés + szóköz- és írásjelhiba | annyra -> annyira | OK |
| 0391 | enyhe szleng + hosszabb kusza mondat + elgépelés | elaudtam -> elaludtam | OK |
| 0393 | enyhe szleng + ékezet nélkül + beszélt nyelv | vegre elkeszult -> Végre elkészült; es tok jo -> és tök jó; szoval -> szóval; lassa -> lássa | OK |
| 0396 | enyhe szleng + elgépelés + szóköz- és írásjelhiba | fürdőbn -> fürdőben | OK |
| 0398 | elgépelés + szóköz- és írásjelhiba + beszélt nyelv | kimentnk -> kimentünk | OK |

**Eredmény: 40 / 40 megfelelt** (szempontok: az input és az output jelentése azonos, nincs új tartalom, a hang megmaradt, nem hivatalos, az output valóban tisztább). A teljes 100 soros olvasásból a 3. és 5. fejezetben leírt tételek javultak; a mintában maradt hiba nem volt.

## 7. Megfigyelések és korlátok (őszinte értékelés)

- **`zajos bemenet` tag 11.8%**: a topic report ezt túlreprezentáltnak jelzi (küszöb 8%). Ez a csomag jelölő címkéje, nem témaszaturáció, és a csomag végére (500 sor) kb. 15%-ra nő. A `tools/dataset_topic_report.py` kezelése külön jóváhagyandó, ebben a körben nem módosítottam.
- **A zajcímkék részben stílust jelölnek, nem külön javítást**: 87 sor kap 3 címkét, de a sorok átlagosan csak 1.7 szóalak-javítást tartalmaznak (86 sorban legfeljebb 2). Az *indulatos*, *enyhe szleng*, *kérdés félreütésekkel* és *hosszabb kusza mondat* címke gyakran a szöveg hangját vagy szerkezetét írja le (kettős felkiáltójel, *tök*, kérdés, vessző nélküli hosszú mondat), amelyhez a javítás a vessző/írásjel vagy egy elütés.
  A címkét ne tekintsük pontos, hibánként adott annotációnak; a *beszélt nyelv* címke 5 sorban (`0317, 0318, 0345, 0350, 0357`) különösen gyenge.
- **A javítások kis száma szándékos, de van ára**: a modell így kevés „nagy javítás” példát lát (medián karakter-változás 0.019); a 3. batch óta a nagy hibaszórású (erősen zajos) sorok száma 16 (3. batch: 34), ezt az 5. batchben érdemes kiegyensúlyozni, ha a csomagban szükség van rá.
- **Rövidítés, telefonos gépelés, hibás ragozás ritka**: a 4 hangsúlyos típus mellett ezekből kevés van (11 / 11 / 6 címke); az 1-3. batch bőven tartalmaz belőlük.
- **A hibaszórás keskeny**: az elgépelés főként hiányzó/dupla betű; billentyű-szomszédos betűhiba (*hpgy, nrm*), *õ*/*û* betű és összeírt szavak (*nemtom*) ebben a batchben nincsenek.
- **Közlekedési téma 0**: szándékos (a 2. batchben sok volt), de a tematikus szórás így kicsit a hétköznapi otthoni és iskolai témák felé tolódik.
- **A szándékmegőrzés-mutató** az ékezet nélküli sorokat továbbra is torzítja; mivel ebben a batchben kevés ilyen sor van, magasabb az átlag (0.93), mint a 2. batchben (0.67). A kézi olvasás a tartalmi egyezést megerősítette.
- **Az ismeretlen-szó arány heurisztika**: a korpusz szókincse magyar ragozás miatt hiányos, csak sorpáronkénti összevetésre jó.
- **Az ellenőrző scriptek** (`noisy_check4.py`, `noisy_extra.py`, `noisy_light3.py`, `verify_labels4.py`, `gen_noisy_batch4.py`) a repón kívül vannak; a `tools/` alá emelésük külön jóváhagyandó.
- **A validátor csak az outputot vizsgálja** torz tokenekre és angol keveredésre; az input szándékosan zajos.

## 8. Fájlok

- Raw: `data/raw/claude_noisy_input_0301_0400_raw.jsonl` (100 sor)
- Clean: `data/clean/claude_noisy_input_0301_0400_clean.jsonl` (100 sor)
- Rejected: `data/rejected/claude_noisy_input_0301_0400_rejected.jsonl` (0 sor, üres fájl)
- Report: `data/reports/claude_noisy_input_0301_0400_report.md`

## 9. Amit ez a kör NEM tett

- Nem indított tanítást, nem módosított webapp/backend kódot, nem törölt és nem írt felül semmit (az 1-3. batch fájljaihoz és a validátorhoz sem nyúlt).
- Nem készítette el a `noisy_input_0401-0500` sorokat (külön jóváhagyásra várnak).
- Nem használt webes forrást, valós felhasználói szöveget, ChatGPT/Dispatch raw jelöltet.
- Nem módosította a topic report tag-kezelését, és nem emelte a scripteket a repóba.

---

## Végső összegzés

- Batch: 100 sor, **100 clean / 0 rejected**, átlag score 100.0, regressziós teszt STABIL.
- A kért irány: szándékmegőrzés 0.93 / 0.91, a formátlan input 34 -> 16 sor, 94 sorban legfeljebb 3 javított szóalak, 84 nagybetűs kezdésű üzenet, minden sorban valódi szóalak-szintű javítás (0 csak formai sor), 2-3 zajtípus (87 sor 3).
- Erősített típusok (összes címke, 3. batch -> 4. batch): indulatos 5 -> 16, kusza mondat 4 -> 17, enyhe szleng 4 -> 28, félreütött kérdés 3 -> 28. 100 új téma (közlekedés 0, főzés/háztartás 3).
- Ellenőrzések: 100/100 valid, input != output, 0 duplikátum és 0 kereszt-találat a 3300 sor ellen (az 1-3. batchet is beleértve), 0 PII/URL/identity bleed/erős káromkodás/érzékeny kulcsszó; ismeretlen-szó arány 0.148 -> 0.116.
- Manuális: mind a 100 sor elolvasva, formális minta 40/40 megfelelt; az összeállítás közben javított hibák az 5. fejezetben.
- Korlát: a zajcímkék részben stílust jelölnek (átlag 1.7 javított szóalak / sor), a *beszélt nyelv* címke 5 sorban gyenge; a `zajos bemenet` tag a topic reportban 11.8%.
- Teljes clean korpusz: **3400 sor**; 5. csomag: 400 / 500.

**STÁTUSZ: STABIL.**
