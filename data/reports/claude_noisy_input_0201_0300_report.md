# Harmadik noisy_input batch - noisy_input_0201-0300

Az 5. csomag (**Hibás user szöveg -> javított szöveg**, cél: 500 clean sor) **harmadik 100 sora** (összesen 300 / 500). Kitalált, hétköznapi, magyar felhasználói üzenetek és ezek természetes, érthető javított változata.
Nincs valós személy/magánadat, URL, e-mail, telefonszám, cím, projektadat, tanács vagy megválaszolt kérdés: az output mindig a felhasználó **saját üzenetének tisztább változata**, nem válasz rá, és nem hivatalosabb nála.

A 2. batch (`0101-0200`) inputjai többségükben nagyon szétesettek voltak (81 sor: kisbetűs kezdés és írásjel nélküli vég, átlag 5.9 javított szóalak soronként). Ez a batch **szándékosan a másik végletet is lefedi**:
sok a rendesen tagolt, nagybetűs, vesszős, chat-stílusú üzenet, amelyben csak pár elütés, rövidítés, rossz rag vagy beszélt nyelvi botlás van; a nagyon szétesett, ékezet nélküli inputok aránya csökken (15 sor), de nem tűnik el.

**Séma**: a 9 mezős repó-séma marad (`id, category, instruction, input, output, tags, difficulty, quality_notes, source`), az `instruction` mező megtartása jóváhagyott. 31 különböző, kézzel írt, nem helyesírás-javító jellegű feladatmegfogalmazás
(11 típus-specifikus + 20 általános, ezek között „csak a pár hibát javítsd…”, „ne hivatalosítsd…” jellegűek), egy szöveg legfeljebb 4 sorban; az 1. és 2. batch instruction-szövegeivel egyik sem egyezik.

## 0. A kérés követelményei és teljesülésük

| Követelmény | Teljesülés |
|---|---|
| 100 clean sor, `noisy_input_0201`-`0300`, `category: noisy_input`, `source: synthetic_claude_magyar`, egyedi `quality_notes` | **100 clean / 0 rejected**, 100 / 100 egyedi quality_notes, az id-k folytonosak |
| 2-3 zajtípus soronként, természetesebb keverék | 60 sor 3, 40 sor 2 típussal; a keverék már a valós együttjárásokat követi (elgépelés + rag, telefonos gépelés + ékezethiány, rövidítés + telefonos, elgépelés + írásjel; 1. fejezet), nem csak a 2. batch „telefonos + beszélt + ékezet nélkül” mintáját ismétli |
| Több valós chat-stílusú magyar user szöveg | 63 sor nagybetűvel kezdődik, 83 sorban van vessző (61-ben legalább 2), köszöntés/megszólítás (*Sziasztok!*, *Figyi*, *Figyu*, *Na*, *Ja, igen*), kérdések a közönséghez (*Ti mit szoktatok…?*, *Nem jönnél el?*, *…, nem?*) |
| Kevesebb teljesen formátlan input | kisbetűs kezdés és írásjel nélküli vég **34 sorban** (2. batch: 81; 1. batch: 25); ≥ 15 szavas, kisbetűs, írásjel nélküli **15 sor** (2. batch: 61, 1. batch: 8) |
| Több sor, ahol csak pár elütés / rövidítés / rossz rag / beszélt nyelvi zavar van | **83 sorban legfeljebb 3 szóalak-szintű javítás** (2. batch: 14), 62 sorban nagybetűs kezdés és legfeljebb 3 javítás (2. batch: 3); javított szóalak / input szó arány: 0.124 (2. batch: 0.347, 1. batch: 0.209) |
| Az output javítson, de tartsa meg a user hangját, ne hivatalosítsa túl | output / input szószám 0.94 / 1.00 / 1.04 (min / átlag / max); megtartott hétköznapi szavak: *kéne* (12 sor), *tök* (8), *suli* (7), *vagy mi* (5), *hisz* (5), *hát*, *figyi*, *figyu*, *haver*, *tesó*, *cucc*; szándékmegőrzés (tőszó-átfedés) 0.91 / 0.88 |
| Kerülendők (PII, URL, e-mail, telefon, MF-AI/Nextora, erős káromkodás, érzékeny téma) | egyik sem szerepel (3. fejezet, 8. pont); erős káromkodás 0, érzékeny téma kulcsszó 0 |
| Input != output, valóban javított | 0 azonos sor; minden sorban legalább egy szóalak-szintű javítás; ismeretlen-szó arány 0.187 -> 0.151 (3. fejezet, 4. pont) |
| Témaszórás | **100 különböző téma**, egyik sem szerepelt az 1. és 2. batch 147 témája között; közlekedési téma 1, főzés/háztartás 1 sor |

## 1. Felépítés

| Csoport | Sor | Jellemző |
|---|---|---|
| Rendesen tagolt, kevés hibás üzenet | 24 | nagybetűs kezdés, vesszők és pont többnyire rendben, 1-3 hiba (elgépelés, rossz rag, *pl*/*kb*/*vki*, hiányzó vessző, 1-2 ékezet) |
| Chat-stílusú, félig tagolt üzenet | 26 | köszöntéssel, kisbetűs kezdéssel vagy hiányzó záró írásjellel, beszélt fordulatokkal, 1-3 hiba |
| Közepes zajszintű üzenet | 25 | részleges ékezethiány, hiányzó vesszők, rövidítések, 2-5 javítás |
| Erősen zajos üzenet | 15 | kisbetűs, ékezet nélküli, írásjel nélküli, hosszabb mondat |
| Vegyes (indulatos, kusza, szleng, kérdés, üzenet-műfajok) | 10 | indulatos kifakadás, egymásba fonódó mondat, szleng, gratuláció, névnapi köszöntő |

| Zajtípus | Elsődleges (`tags[2]`) | Összes címke | Mi a zaj |
|---|---|---|---|
| szóköz- és írásjelhiba | 2 | 48 | hiányzó vessző, hiányzó záró írásjel, *van e*, *be pakolni*, kettős felkiáltójel |
| elgépelés | 15 | 43 | hiányzó/dupla/felcserélt betű (*megöntöznni, beragdt, vrebek, pingpongversney, dipoplomádhoz*) |
| ékezet nélkül | 25 | 39 | teljes vagy részleges ékezethiány (*mar, latszik, napszemuvegem, honapja*) |
| beszélt nyelv | 9 | 37 | *mer, szval, figyu, vagy mi, na meg*, tagolatlan beszélt szerkezet |
| telefonos gyors gépelés | 18 | 32 | kisbetűs kezdés, hiányzó záró írásjel, sietős elütés |
| rövidítés | 12 | 29 | *kb, pl, vki, vmi, h, ok, köv.* |
| hibás ragozás | 8 | 16 | *táborban -> táborba, színpadnál -> színpadtól, megtart -> megtartja, két hette -> két hete, sok emberek* |
| indulatos, laza stílus | 5 | 5 | kettős felkiáltójel, csupa nagybetűs kiáltás, türelmetlen hang |
| enyhe szleng | 1 | 4 | *tök jó, tök menő, tök hülyeség* |
| hosszabb kusza mondat | 2 | 4 | egymásba fonódó, 25-40 szavas mondat vessző nélkül |
| kérdés félreütésekkel | 3 | 3 | elütés egy egyébként kérdő mondatban |

`tags` = `["magyar", "zajos bemenet"] + 2-3 zajtípus + [téma]` (5-6 elem). A zajcímkéket kézzel adtam, és egy külön szkripttel minden sorra ellenőriztem, hogy a címkének van-e nyoma a szóalak-különbségben (lásd 3. fejezet, 5. pont); a 2. batchtől eltérően **nincs automatikus címke-kiegészítés**.
`difficulty`: a bemenet és a javított változat karakter-eltérése, a bemenet hossza és a zajtípusok száma szerinti rang: legnagyobb 20 = hard, következő 35 = medium, a többi 45 easy. Mivel a batch sok enyhén hibás sort tartalmaz, a *hard* sorok nagyrészt az erősen zajos csoportból kerülnek ki.
Az id-k deterministikus keverés (seed 20260924) után lettek kiosztva, nincs típus- vagy csoportblokk.

## 2. Számok

| Mérőszám | Érték |
|---|---|
| Raw sorok | 100 |
| Schema validáció (`dataset_validate.py`, raw és clean is) | 100 / 100 valid |
| `input` == `output` | 0 sor |
| Batchen belüli dedupe (id / instruction+input / output, 0.9) | 0 / 0 / 0 |
| Kereszt-dedupe a **3200** meglévő clean sor ellen, beleértve az 1. és 2. noisy batchet (id; instruction+input, output, input-vs-input, input-vs-output >= 0.9) | 0 / 0 / 0 / 0 / 0 |
| **Végleges clean** | **100** |
| **Rejected** | **0** |
| Átlag quality_score | **100.0 / 100** (minden sor 100) |
| Difficulty | easy 45, medium 35, hard 20 |
| Egyedi input / output / quality_notes / instruction | 100 / 100 / 100 / 31 (egy instruction legfeljebb 4 sorban) |
| Zajtípus soronként | 3 típus: 60 sor, 2 típus: 40 sor |
| Output szószám (min / medián / max) | 12 / 21 / 43 |
| Output / input szóhossz-arány (min / átlag / max) | 0.94 / 1.00 / 1.04 |
| Karakter-szintű változás (1 - hasonlóság, min / medián / max) | 0.004 / 0.023 / 0.130 (szándékosan kicsi: sok sorban csak pár betű változik) |
| Javított szóalakok soronként (min / átlag / medián / max) | 1 / 2.5 / 2 / 10 (2. batch: 1 / 5.9 / 6 / 16) |
| Szóalak-szintű javítás nélküli sor / csak formai sor | **0 / 0** |
| Ismeretlen szavak aránya a korpusz-szókincshez képest (input -> output átlag) | **0.187 -> 0.151** (2. batch: 0.284 -> 0.143) |
| Szándékmegőrzés (5 betűs tőszavak lefedettsége, input->output / output->input átlag) | **0.91 / 0.88** (2. batch: 0.67 / 0.67); 4 sor < 0.5, mind erősen ékezet nélküli input, kézzel átnézve rendben |
| Formai zajmarker az outputban | **0 valódi sor** (az inputban 63 sor tartalmaz legalább egyet); az ellenőrző egy téves jelzést adott a `0210`-en: az *1000* három nullája „betűhalmozásnak” számít |
| Identity bleed / saját projekt-említés / URL / e-mail / telefon- és cím-minta | 0 / 0 / 0 / 0 / 0 |
| Erős káromkodás, gyűlölet, érzékeny téma kulcsszó | 0 |
| Topic report (3300 soros korpusz) | `zajos bemenet` **9.1%** (300 sor; a csomag jelölő címkéje, a küszöb 8%, lásd 7. fejezet), `összefoglalás` 15.2% (500 sor, dokumentált), `ékezet nélkül` 4.0% |
| Teljes clean korpusz | **3300 sor** (1000 simple_qa, 1000 explanation, 500 step_by_step, 500 summary, 300 noisy_input) |

### A három noisy batch összevetése (ugyanazokkal az ellenőrzőkkel mérve)

| Mutató | 1. batch (0001-0100) | 2. batch (0101-0200) | 3. batch (0201-0300) |
|---|---|---|---|
| Zajtípus soronként | 1 | 2-3 (76 sor 3) | 2-3 (60 sor 3) |
| Nagybetűs kezdés | 69 | 17 | 63 |
| Írásjellel záródó input | 31 | 6 | 43 |
| Sem kezdő nagybetű, sem záró írásjel | 25 | 81 | 34 |
| Legfeljebb 3 javított szóalak | 63 | 14 | 83 |
| Javított szóalak / input szó | 0.209 | 0.347 | 0.124 |
| Különböző téma | 50 | 100 | 100 |

## 3. Ellenőrzési lépések

1. **Generálás**: 100 sor négy részben, soronként kézzel megírt input-output párokkal (nincs szabály- vagy sablongenerátor); az outputot mindig a saját inputjából levezetve írtam.
2. **Schema**: `dataset_validate.py` 100/100; saját ellenőrzés a 9 kötelező mezőre, `category`, `source`, `difficulty`, a `tags` fejlécre és az 5-6 tag-hosszra; téma-egyediség a batchen belül és az 1-2. batch 147 témájával szemben; instruction-szövegek eltérése az előző batchekétől.
3. **Input != output**: 0 azonos sor; minden sorban szóalak-szintű változás van (0 csak formai sor).
4. **Valóban javítottabb-e**: (a) ismeretlen-szó arány a korpusz szókincséhez képest, sorpáronként (a batch saját fájlját a szókincsből kihagyva): 0.187 -> 0.151; két sor emelkedik (`0203`: *kinél*, `0294`: *keressek*), mindkettő ritka, de helyes szóalak; (b) formai zajmarkerek az outputban: 0 valódi;
   (c) nincs rövidítés, betűhalmozás és írásjel-halmozás az outputban.
5. **Zajcímkék bizonyítéka**: külön szkript minden sorra ellenőrzi, hogy a címkéhez tartozik-e szóalak-szintű nyom (ékezet-javítás, elgépelés, rag-csere, rövidítés, írásjel-változás, szleng-/beszélt szó). Első futás 12 sort jelzett; javítva: `0217` (*elgépelés* -> *ékezet nélkül* + *szóköz- és írásjelhiba*), `0270` (nem volt benne elgépelés, csak ékezethiba -> valódi elütés, *hogyna*, került bele).
   A maradék 10 jelzés kézzel átnézve: `0246` (*tok jo* = *tök jó*, ékezet nélkül a szleng-szó), `0261` (*oontozom* valódi elütés) téves jelzés; a *beszélt nyelv* címke `0204, 0226, 0299` (*szoval*), `0207, 0240, 0245, 0259, 0272` (*Nem baj ha kihagyom?*, *vmi biztos nem jó vele*, *suli*, *az is bejött*, *Majd holnap, vagy holnapután, talán*) sorokban beszélt fordulatra épül, de az ötben (`0207, 0240, 0245, 0259, 0272`) gyenge bizonyítékkal, mert a fordulat nem hiba, csak megmaradt: ezeket a címkéket **nem** vettem le, de a korlátoknál (7. fejezet) jelzem.
6. **Szándékmegőrzés**: tőszó-átfedés 0.91 / 0.88 + kézi olvasás.
7. **Batch dedupe**: id 0, instruction+input 0, output 0. Input-párok >= 0.7 hasonlóság: 0.
8. **Kereszt-dedupe a teljes korpusz ellen**: az új 100 sor a **3200** meglévő clean sorral szemben (az 1. és 2. noisy batch is benne van; `real_quick_ratio`/`quick_ratio` előszűréssel), 4 összevetésben; 0 találat, 0 id-ütközés.
   **Javítás a 2. batch reportjához**: az akkori ellenőrző a `noisy_input` nevű fájlokat mind kihagyta, így a 2. batch a „3000 sor” ellen lett összevetve, az 1. batch (100 sor) ellen nem. Utólag újrafuttattam a 2. batchet a **3100** sor ellen (az 1. batchet is beleértve): 0 találat. A commitolt 2. batch report számadata tehát pontosítandó, a tartalom nem érintett.
9. **Safety/PII/identity bleed**: e-mail, URL, telefon/azonosító, irányítószám- és címminta 0; MF-AI/Nextora említés 0; `guard.looks_like_identity_bleed` 0; erős káromkodás 0; érzékeny téma kulcsszó 0 (egy első futáskor jelzett *beteg* szó a `0225`-ös sorból kikerült, lásd 5. fejezet).
   A kérdések (pl. szemüvegkeret, hangszerválasztás, szelektív gyűjtés, kutyaiskola) az inputban maradnak, az outputban **nincs rájuk válasz vagy tanács**.
10. **Quality score**: 100.0 / 100.
11. **Regressziós teszt**: `tests/test_v1_7_4_dataset_foundation.py` - minden teszt sikeres, **STÁTUSZ: STABIL**.
12. **Manuális átolvasás és mintavétel**: mind a 100 sor input és output egymás mellett végigolvasva; formális minta 40 sor (6. fejezet).
13. **Clean/rejected/report**: clean 100, rejected 0 (üres fájl), ez a report; **progress** frissítve (helyi fájl, szándékosan nincs commitolva).

## 4. Mi számít javításnak (és mi nem)

- **Javítás**: elgépelés, hiányzó ékezet, rövidítések kibontása (*vmi, vki, kb, pl, h, ok, köv.*), hibás rag/vonzat (*táborban -> táborba, kihez érdeklődnöm -> kinél érdeklődnöm, rajzversenyre vesz részt -> rajzversenyen*), az összeírt/szétírt szavak rendbetétele (*be pakolni -> bepakolni, mostmar -> most már*),
  hiányzó vesszők és záró írásjel, kis kezdőbetű. A **sorrend és a tartalom** megmarad.
- **Nem javítás (szándékosan)**: a felhasználó hangját adó szavak és szerkezetek maradnak (*kéne, tök, suli, figyi, figyu, haverom, tesóm, cucc, vagy mi, hisz, na meg, hát*), a bizonytalanság (*szerintem, azt hiszem, lehet, hogy*), az indulat, a kérdés kérdés marad, a kijelentés kijelentés.
  Ha az input már helyes volt, nem írtam át (pl. a *vegyem-e meg* szórend). Nem került be új szó, tanács vagy magyarázat.
- **Ami nincs benne**: helyesírási szabály, tanács, válasz a kérdésre, hivatalosabb átfogalmazás, új tartalom.

## 5. Önkorrekciók az összeállítás és a teljes átolvasás során (mind clean előtt)

- **Csak formai sor (1)**: a `lépcsőház-felújítás` sor eredetileg csak vesszőket/pontot igényelt, szóalak-hiba nélkül -> valódi hiba (*furnak* -> *fúrnak*) került bele, a címke *ékezet nélkül*-lel bővült.
- **Címkék (2)**: `0217` és `0270`, lásd 3. fejezet, 5. pont.
- **Érzékeny kulcsszó (1)**: a `0225` input eredetileg „a tanár beteg lett”; ez egészséggel kapcsolatos kulcsszó volt, ezért „a tanár nem tud bejönni” lett az input és az output is (a jelentés: elmarad az óra, változatlan).
- **Hibás javítás az outputban (2)**: a `csónakázás` sorban a *elazott* első outputja *eláztott* volt (átható ige), a helyes **elázott**; a `bolhapiaci számológép` sorban az output átírta a *vegyem-e meg* szórendet *megvegyem-e*-re, ami felesleges változtatás volt -> a bemeneti szórend maradt.
- **Jegyzet-hiba (1)**: a `hőmérő az erkélyen` quality_notes-ban elírt névelő javítva.
- **Ellenőrző hibája (2)**: (a) az OOV-mérés első futásán a batch saját sorai a szókincsben voltak (0.0 / 0.0), ezért a saját fájlt kihagyom; (b) a kereszt-dedupe az 1-2. batchet nem hasonlította a 3. batchhez, lásd 3. fejezet, 8. pont.
- A 4 alacsony szándékmegőrzési sor és a 2 OOV-emelkedés kézi átnézése módosítást nem igényelt.

## 6. Manuális mintavétel (formális 40 sor)

A minta rögzített szabály szerint készült (az id sorszáma 5-tel osztva 1 vagy 3 maradékot ad: 40 sor), nem válogatott. Mind a 100 sort elolvastam, a minta ennek a dokumentált része. Az értékelés az 5. fejezetben leírt javítások után történt.

| id | Zajtípusok (`tags`) | Konkrét javítások (szó-szintű különbség; a nagybetű- és írásjel-változás nem szerepel) | Értékelés |
|---|---|---|---|
| 0201 | telefonos gyors gépelés + elgépelés + enyhe szleng | fejhalgatóm -> fejhallgatóm | OK |
| 0203 | elgépelés + hibás ragozás | Elvesztetem -> Elvesztettem; kihez -> kinél | OK |
| 0206 | ékezet nélkül + hibás ragozás | mar -> már; emberek -> ember | OK |
| 0208 | hibás ragozás + elgépelés | színpadnál -> színpadtól; lessz -> lesz | OK |
| 0211 | rövidítés + szóköz- és írásjelhiba + beszélt nyelv | Vki -> Valaki | OK |
| 0213 | elgépelés + hibás ragozás | fogot -> fogott; megtart -> megtartja | OK |
| 0216 | elgépelés + rövidítés + ékezet nélkül | akcizik es pl -> akciózik és például | OK |
| 0218 | beszélt nyelv + szóköz- és írásjelhiba + elgépelés | hangoskönyeket -> hangoskönyveket | OK |
| 0221 | ékezet nélkül + telefonos gyors gépelés + beszélt nyelv | nagymamam mostmar -> nagymamám most már; videohivast inditani -> videóhívást indítani; meg -> még; szoval -> szóval; oran at -> órán át; kepernyot -> képernyőt | OK |
| 0223 | elgépelés + szóköz- és írásjelhiba | beragdt -> beragadt | OK |
| 0226 | telefonos gyors gépelés + ékezet nélkül + beszélt nyelv | sunt lattam -> sünt láttam; es -> és; megorultem -> megörültem; szoval -> szóval | OK |
| 0228 | ékezet nélkül + szóköz- és írásjelhiba | nevnapot -> névnapot | OK |
| 0231 | elgépelés + szóköz- és írásjelhiba | válaztani -> választani | OK |
| 0233 | elgépelés + szóköz- és írásjelhiba + beszélt nyelv | válassam -> válasszam | OK |
| 0236 | telefonos gyors gépelés + hosszabb kusza mondat + elgépelés | átjoött -> átjött | OK |
| 0238 | rövidítés + elgépelés | gyereekkel -> gyerekekkel; h -> hogy; vmi -> valami | OK |
| 0241 | elgépelés + rövidítés | felejtetem -> felejtettem; vmi -> valami | OK |
| 0243 | telefonos gyors gépelés + beszélt nyelv | szoval -> szóval | OK |
| 0246 | ékezet nélkül + telefonos gyors gépelés + enyhe szleng | vasarnap csonakaztunk -> Vasárnap csónakáztunk; es tok jo -> és tök jó; vegen -> végén; elazott -> elázott; jott -> jött; hullam -> hullám | OK |
| 0248 | indulatos, laza stílus + ékezet nélkül + szóköz- és írásjelhiba | MAR -> Már; levo lakasban es -> lévő lakásban és; koran -> korán | OK |
| 0251 | indulatos, laza stílus + szóköz- és írásjelhiba + ékezet nélkül | idöpontot -> időpontot | OK |
| 0253 | telefonos gyors gépelés + rövidítés + enyhe szleng | kb -> körülbelül | OK |
| 0256 | indulatos, laza stílus + hibás ragozás + elgépelés | pénzem -> pénzemet; alkalomal -> alkalommal | OK |
| 0258 | beszélt nyelv + hibás ragozás | hétvégén -> hétvégére; mer -> mert | OK |
| 0261 | ékezet nélkül + elgépelés + telefonos gyors gépelés | muskatlik -> muskátlik; erkelyen -> erkélyen; elszaradni -> elszáradni; oontozom oket -> öntözöm őket; ertem -> értem | OK |
| 0263 | kérdés félreütésekkel + elgépelés | elküldenii -> elküldeni; egészböl -> egészből | OK |
| 0266 | ékezet nélkül + szóköz- és írásjelhiba + beszélt nyelv | birja -> bírja; be pakolni -> bepakolni | OK |
| 0268 | beszélt nyelv + rövidítés + szóköz- és írásjelhiba | vmi -> valami | OK |
| 0271 | elgépelés + hibás ragozás | uszodabérltet -> uszodabérletet; sávba -> sávban | OK |
| 0273 | telefonos gyors gépelés + szóköz- és írásjelhiba + elgépelés | kinyitvva -> kinyitva | OK |
| 0276 | beszélt nyelv + rövidítés + szóköz- és írásjelhiba | kb -> körülbelül | OK |
| 0278 | beszélt nyelv + hibás ragozás + szóköz- és írásjelhiba | pakolásba -> pakolásban | OK |
| 0281 | beszélt nyelv + elgépelés | jétszanak -> játszanak; szval -> szóval | OK |
| 0283 | ékezet nélkül + telefonos gyors gépelés + szóköz- és írásjelhiba | negykor felebredtem es -> négykor felébredtem és; szoval -> szóval; es kavet fottem -> és kávét főztem; mar -> már; faradt -> fáradt | OK |
| 0286 | telefonos gyors gépelés + elgépelés + beszélt nyelv | kertbn -> kertben | OK |
| 0288 | ékezet nélkül + hosszabb kusza mondat + telefonos gyors gépelés | vettunk uj -> vettünk új; szomszed -> szomszéd; tul -> túl; es -> és; kilatast -> kilátást; jo -> jó; csinalnom -> csinálnom | OK |
| 0291 | szóköz- és írásjelhiba + elgépelés | vesenek -> vesszenek | OK |
| 0293 | telefonos gyors gépelés + rövidítés + szóköz- és írásjelhiba | kb -> körülbelül; pl -> például | OK |
| 0296 | ékezet nélkül + telefonos gyors gépelés + szóköz- és írásjelhiba | talaltam -> találtam; regi szamologepet -> régi számológépet; ert es -> ért és; mukodik -> működik | OK |
| 0298 | ékezet nélkül + beszélt nyelv + szóköz- és írásjelhiba | szinész -> színész | OK |

**Eredmény: 40 / 40 megfelelt** (szempontok: az input és az output jelentése azonos, nincs új tartalom, a hang megmaradt, nem hivatalos, az output valóban tisztább). A teljes 100 soros olvasásból a 3. és 5. fejezetben leírt tételek javultak; a mintában maradt hiba nem volt.

## 7. Megfigyelések és korlátok (őszinte értékelés)

- **`zajos bemenet` tag 9.1%**: a topic report ezt túlreprezentáltnak jelzi (küszöb 8%). Ez a csomag jelölő címkéje, nem témaszaturáció, és a csomag végére (500 sor) kb. 15%-ra nő. A `tools/dataset_topic_report.py` kezelése külön jóváhagyandó, ebben a körben nem módosítottam.
- **A zajcímkék heurisztikusak**: a címkéket kézzel adtam, szkripttel ellenőriztem, de a *beszélt nyelv* címke 5 sorban (`0207, 0240, 0245, 0259, 0272`) gyenge bizonyítékú (a fordulat megmaradt, nem javítás tárgya). A címkét a modell szempontjából ne tekintsük pontos annotációnak.
- **A típuseloszlás eltolódott**: az *indulatos* (5), *kusza mondat* (4), *enyhe szleng* (4) és *kérdés félreütésekkel* (3) sorok száma kicsi, mert a batch célja a természetes, enyhén hibás üzenet volt. Az 1-2. batch bőven tartalmaz ilyen sorokat; az *ékezet nélkül* címke 39 sorban szerepel (részleges ékezethiánnyal együtt).
- **Billentyű-szomszédos betűhiba (pl. *hpgy, nrm*) és *õ*/*û* betű ebben a batchben nincs** (0 sor); ezeket a 2. batch hozta, itt a hiányzó/dupla/felcserélt betű az elütés fő formája.
- **A hibaarány a valóságosnál szelídebb lehet**: 83 sorban legfeljebb 3 javított szóalak van. Ez a kért irány, de a valódi felhasználói zaj szórása nagyobb; a 4. batchben érdemes újra bevinni erősebb, kevert zajú, hosszabb szöveget és több tagolatlan, több gondolatú üzenetet.
- **A szándékmegőrzés-mutató** (0.91) az ékezet nélküli sorokat továbbra is torzítja (4 sor < 0.5).
- **A javított output kis eltérése** (medián karakter-változás 0.023) azt jelenti, hogy a sorok nagy részében egy-két szót kell javítani; a modellnek így nehezebb rosszul tanulnia „mindent átírok” szokást, de kevesebb a „nagy javítás” példa; ezt a 4. batchben ki lehet egyensúlyozni.
- **Az ismeretlen-szó arány heurisztika**: a korpusz szókincse magyar ragozás miatt hiányos, csak sorpáronkénti összevetésre jó.
- **Az ellenőrző scriptek** (`noisy_check3.py`, `noisy_extra.py`, `noisy_light3.py`, `verify_labels3.py`, `gen_noisy_batch3.py`) a repón kívül vannak; a `tools/` alá emelésük külön jóváhagyandó.
- **A validátor csak az outputot vizsgálja** torz tokenekre és angol keveredésre; az input szándékosan zajos.

## 8. Fájlok

- Raw: `data/raw/claude_noisy_input_0201_0300_raw.jsonl` (100 sor)
- Clean: `data/clean/claude_noisy_input_0201_0300_clean.jsonl` (100 sor)
- Rejected: `data/rejected/claude_noisy_input_0201_0300_rejected.jsonl` (0 sor, üres fájl)
- Report: `data/reports/claude_noisy_input_0201_0300_report.md`

## 9. Amit ez a kör NEM tett

- Nem indított tanítást, nem módosított webapp/backend kódot, nem törölt és nem írt felül semmit (az 1-2. batch fájljaihoz és a validátorhoz sem nyúlt; a 2. batch reportját sem javítottam utólag, a pontosítás ebben a reportban van).
- Nem készítette el a `noisy_input_0301-0500` sorokat (külön jóváhagyásra várnak).
- Nem használt webes forrást, valós felhasználói szöveget, ChatGPT/Dispatch raw jelöltet.
- Nem módosította a topic report tag-kezelését, és nem emelte a scripteket a repóba.

---

## Végső összegzés

- Batch: 100 sor, **100 clean / 0 rejected**, átlag score 100.0, regressziós teszt STABIL.
- Az igényelt irány: 2-3 zajtípus soronként (60 sor 3), a formátlan input aránya 81 -> 34 sor, 83 sorban legfeljebb 3 javított szóalak, 62 sor rendesen tagolt és enyhén hibás, 100 új téma (közlekedés 1, főzés/háztartás 1).
- Ellenőrzések: 100/100 valid, input != output, 0 duplikátum és 0 kereszt-találat a 3200 sor ellen (az 1-2. batchet is beleértve), 0 PII/URL/identity bleed/erős káromkodás/érzékeny kulcsszó; ismeretlen-szó arány 0.187 -> 0.151, szándékmegőrzés 0.91 / 0.88.
- Manuális: mind a 100 sor elolvasva, formális minta 40/40 megfelelt; az összeállítás közben javított hibák az 5. fejezetben.
- Pontosítás: a 2. batch kereszt-dedupe-ja az 1. batchet nem tartalmazta, utólag lefuttatva 0 találat (3. fejezet, 8. pont).
- Teljes clean korpusz: **3300 sor**; 5. csomag: 300 / 500. A topic report a `zajos bemenet` tagre 9.1%-ot jelez (a csomag jelölő címkéje).

**STÁTUSZ: STABIL.**
