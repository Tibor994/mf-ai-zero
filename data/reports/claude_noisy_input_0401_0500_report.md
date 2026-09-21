# Ötödik, záró noisy_input batch - noisy_input_0401-0500

Az 5. csomag (**Hibás user szöveg -> javított szöveg**, cél: 500 clean sor) **záró, ötödik 100 sora**: ezzel a csomag **500 / 500**. Kitalált, hétköznapi, magyar felhasználói üzenetek és ezek természetes, érthető javított változata.
Nincs valós személy/magánadat, URL, e-mail, telefonszám, cím, projektadat, tanács vagy megválaszolt kérdés: az output mindig a felhasználó **saját üzenetének tisztább változata**, nem válasz rá, és nem hivatalosabb nála.

A 4. batch stabil irányát tartja (magas szándékmegőrzés, természetes chat-stílus, a felhasználó hangjának megtartása, minden sorban valódi szóalak-szintű javítás), és a **kért új zajfajtákat** hozza: billentyű-szomszédos elütést, *o*/*0* karaktertévesztést és összeírt/szétírt szavakat.
Az indulatos, kusza, enyhe szlenges és félreütött kérdéses sorok aránya megmarad; a teljesen szétesett input kevés.

**Séma**: a 9 mezős repó-séma marad (`id, category, instruction, input, output, tags, difficulty, quality_notes, source`), az `instruction` mező megtartása jóváhagyott. 29 különböző, kézzel írt, nem helyesírás-javító jellegű feladatmegfogalmazás, egy szöveg legfeljebb 4 sorban;
az 1-4. batch 120 instruction-szövegével egyik sem egyezik (az összeállító szkript ezt minden futáskor ellenőrzi).

## 0. A kérés követelményei és teljesülésük

| Követelmény | Teljesülés |
|---|---|
| 100 clean sor, `noisy_input_0401`-`0500`, `category: noisy_input`, `source: synthetic_claude_magyar`, egyedi `quality_notes` | **100 clean / 0 rejected**, 100 / 100 egyedi quality_notes, az id-k folytonosak |
| Magas szándékmegőrzés | tőszó-átfedés input->output / output->input **0.91 / 0.91** (4. batch: 0.93 / 0.91); egyetlen sor sem esik 0.5 alá |
| Természetes magyar chat-stílus | 89 sor nagybetűvel kezdődik; megszólítás, köszönés, kérdés a közönséghez (*Figyi, hogy vagy?*, *Ti mit gondoltok?*, *Köszi mindenkinek…*, *Ki tud jönni holnap…?*); megtartott hétköznapi szavak: *tök* (27 sor), *szóval*, *haver*, *cuki*, *gáz*, *persze*, *ciki*, *tulaj*, *pléd*, *nem tom* |
| Output javít, de megtartja a user hangját, nem hivatalosít | a teljes átolvasás szerint nincs sor, ahol az output hivatalosabbra váltana; a szleng, a beszélt fordulatok és az indulat megmarad (*tök gáz*, *tök cuki*, *Ez így nem fair*, *Mit tudom én*), csak a hibás alak javul |
| Minden sorban valódi szóalak-szintű javítás | **100 / 100 sor**; csak nagybetű/írásjel-változású sor 0. Hat sorban a javítás nem betűcsere, hanem szóhatár- vagy számjegy-javítás (lásd 7. fejezet): `0402, 0407, 0450` (*vala mi*, *el kezdtem*, *mivan*, *nemtudom*) és `0404, 0457, 0472` (*5o*, *2ooo*, *1o*) |
| Több billentyű-szomszédos elütés | **80 sor** legalább egy, a magyar QWERTZ-kiosztás szerint szomszédos billentyűre cserélt betűvel (összesen 82 elütés: *nrm, hpgy, veke, tegnao, ninden, skkora, kspcsoló, fitós, dolgoznpm, szomszéf, éjfék*), további 35 sor hiányzó/felesleges betűvel; a 4. batchben ez a mérőszám nem volt külön vizsgálva |
| *o*/*0* vagy hasonló karaktertévesztés, csak természetesen | **7 sor, 8 token**: kisbetűs *o* a nulla helyett számokban (*1o perc, 3o gyerek, 5o kilométer, 2ooo forint, 3o%-os*); szavakban nincs *0*, mert az nem természetes |
| Néhány összeírt szó (*nemtom / mivan / valahogy* jellegű) | **12 sor összeírt** (*nemtom, nemtudom, mivan, mittudom, hogyvagy, Nemis, Szerintemnem, Mostmár, Aztmondta, azthiszem, Nemhiszem, Csakmert, Nemtudjátok, vagymi*) és **4 sor szétírt** (*vala mi, Vala hogy, ki csit, el kezdtem*) szó |
| Maradjon több indulatos, kusza mondat, enyhe szleng, félreütött kérdés | összes címke: *enyhe szleng* 25, *kérdés félreütésekkel* 23, *indulatos, laza stílus* 21, *hosszabb kusza mondat* 16 (4. batch: 28 / 28 / 16 / 17) |
| Ne legyen túl sok teljesen szétesett, ékezet nélküli input | kisbetűs kezdés és írásjel nélküli vég **11 sorban** (4. batch: 16); ≥ 15 szavas, kisbetűs, írásjel nélküli **4 sor**; az *ékezet nélkül* címke 3 sorban szerepel |
| Változatos téma | **100 különböző téma**, egyik sem szerepelt az 1-4. batch 347 témája között; közlekedési téma 0, főzés/háztartás 3 sor |
| 2-3 zajtípus soronként | 93 sor 3, 7 sor 2 típussal |
| Kerülendők (PII, URL, e-mail, telefon, MF-AI/Nextora, erős káromkodás, érzékeny téma) | egyik sem szerepel (3. fejezet, 9. pont); enyhe indulatszó: *tök gáz*, *ez tök idegesítő*, *Mit tudom én*, *nekem elegem van belőle* |
| Input != output | 0 azonos sor; ismeretlen-szó arány 0.154 -> 0.112 (3. fejezet, 4. pont) |

## 1. Felépítés

A négy csoport az összeállítás négy részét jelöli; a típusok átfedik egymást.

| Csoport | Sor | Jellemző |
|---|---|---|
| Billentyű-szomszédos elütések, tagolt üzenetek (indulatos, kusza, szleng, kérdés) | 25 | 1-2 szomszédos-billentyűs betűcsere (*hpgy, nrm, tegnao*), többnyire nagybetűvel kezdve, a vesszők hiányoznak |
| Összeírt/szétírt szavak és *o*/*0* tévesztés | 25 | *nemtom, mivan, Nemis, vala mi, ki csit*; *1o perc, 3o gyerek, 2ooo forint* |
| Indulatos, kusza, szlenges és félreütött kérdéses üzenetek | 25 | *!!*, *??*, hosszú, vessző nélküli mondatok, *tök*, kérdés hiányzó betűvel |
| 5 kisbetűs, írásjel nélküli + 20 vegyes | 25 | 2 ékezetes és 3 ékezet nélküli, kisbetűs, írásjel nélküli üzenet; 20 rendesen tagolt, hibás üzenet |

| Zajtípus | Elsődleges (`tags[2]`) | Összes címke | Mi a zaj |
|---|---|---|---|
| elgépelés | 6 | 85 | szomszédos billentyű (*veke, milyrn*), hiányzó/felesleges betű, *o*/*0* számokban |
| szóköz- és írásjelhiba | 14 | 45 | összeírt/szétírt szavak, hiányzó vessző és záró írásjel, kettős felkiáltójel/kérdőjel |
| telefonos gyors gépelés | 11 | 41 | szomszédos billentyű, kisbetűs kezdés, hiányzó záró írásjel |
| beszélt nyelv | 4 | 33 | *szval*, *nem tom*, *persze*, beszélt szerkezet |
| enyhe szleng | 16 | 25 | *tök jó, tök gáz, tök cuki, ciki* |
| kérdés félreütésekkel | 18 | 23 | elütés egy kérdésben, hiányzó kérdőjel |
| indulatos, laza stílus | 16 | 21 | kettős felkiáltójel, *elegem van*, *ez már nem vicces*, türelmetlen hang |
| hosszabb kusza mondat | 14 | 16 | vessző nélküli, 25-40 szavas, többtagmondatos mondat |
| ékezet nélkül | 0 | 3 | teljes ékezethiány (a kérésnek megfelelően minimális) |
| hibás ragozás | 1 | 1 | *a igazgatóhoz -> az igazgatóhoz* |

`tags` = `["magyar", "zajos bemenet"] + 2-3 zajtípus + [téma]` (5-6 elem). A zajcímkéket kézzel adtam és szkripttel ellenőriztem, lásd 3. fejezet, 5. pont.
`difficulty`: a bemenet és a javított változat karakter-eltérése, a bemenet hossza és a zajtípusok száma szerinti rang: legnagyobb 20 = hard, következő 35 = medium, a többi 45 easy.
Az id-k deterministikus keverés (seed 20260926) után lettek kiosztva, nincs típus- vagy csoportblokk.

## 2. Számok

| Mérőszám | Érték |
|---|---|
| Raw sorok | 100 |
| Schema validáció (`dataset_validate.py`, raw és clean is) | 100 / 100 valid |
| `input` == `output` | 0 sor |
| Batchen belüli dedupe (id / instruction+input / output, 0.9) | 0 / 0 / 0 |
| Kereszt-dedupe a **3400** meglévő clean sor ellen, beleértve az 1-4. noisy batchet (id; instruction+input, output, input-vs-input, input-vs-output >= 0.9) | 0 / 0 / 0 / 0 / 0 |
| **Végleges clean** | **100** |
| **Rejected** | **0** |
| Átlag quality_score | **100.0 / 100** (minden sor 100) |
| Difficulty | easy 45, medium 35, hard 20 |
| Egyedi input / output / quality_notes / instruction | 100 / 100 / 100 / 29 (egy instruction legfeljebb 4 sorban) |
| Zajtípus soronként | 3 típus: 93 sor, 2 típus: 7 sor |
| Output szószám (min / medián / max) | 10 / 18 / 36 |
| Output / input szóhossz-arány (min / átlag / max) | 0.92 / 1.01 / 1.15 (a szétválasztott összeírt szavak növelik a szószámot) |
| Karakter-szintű változás (1 - hasonlóság, min / medián / max) | 0.007 / 0.023 / 0.272 (szándékosan kicsi) |
| Javított szóalakok soronként (min / átlag / medián / max) | 1 / 1.9 / 2 / 9 (4. batch: 1 / 1.7 / 1 / 11); legfeljebb 2 javítás: 81 sor, legfeljebb 3: 91 sor |
| Ismeretlen szavak aránya a korpusz-szókincshez képest (input -> output átlag) | **0.154 -> 0.112** (5 sorban az output aránya kicsit nagyobb: `0405, 0407, 0425, 0472, 0483`; a javított *10*, *30* számtokenek ismeretlennek számítanak, nem hiba) |
| Szándékmegőrzés (5 betűs tőszavak lefedettsége, input->output / output->input átlag) | **0.91 / 0.91** |
| Formai zajmarker az outputban | **0 valódi sor** (az inputban 83 sor tartalmaz legalább egyet); az ellenőrző egy téves jelzést adott a `0457`-en: a *2000* három nullája „betűhalmozásnak” számít |
| Identity bleed / saját projekt-említés / URL / e-mail / telefon- és cím-minta | 0 / 0 / 0 / 0 / 0 |
| Erős káromkodás, gyűlölet, érzékeny téma kulcsszó | 0 |
| Topic report (3500 soros korpusz) | `zajos bemenet` **14.3%** (500 sor; a csomag jelölő címkéje, a küszöb 8%, lásd 7. fejezet), `összefoglalás` 14.3% (500 sor, dokumentált), `ékezet nélkül` 4.3% |
| Teljes clean korpusz | **3500 sor** (1000 simple_qa, 1000 explanation, 500 step_by_step, 500 summary, 500 noisy_input) |

### Az ötödik batch új zajfajtái (`noisy_special5.py` mérése)

| Mérőszám | Érték |
|---|---|
| Sor legalább egy szomszédos-billentyűs elütéssel (magyar QWERTZ; vízszintes és függőleges szomszédok) | **80** (82 elütés) |
| Sor hiányzó/felesleges betűs elütéssel | 35 |
| Sor *o*/*0* tévesztéssel | 7 (8 token; `0404, 0405, 0410, 0425, 0457, 0472, 0483`) |
| Sor összeírt szóval / szétírt szóval | 12 / 4 |
| Sor legalább egy a három új fajtából | **93** (a maradék 7 sor más elütést tartalmaz) |

### Az öt noisy batch összevetése (ugyanazokkal az ellenőrzőkkel mérve)

| Mutató | 1. | 2. | 3. | 4. | 5. batch |
|---|---|---|---|---|---|
| Zajtípus soronként | 1 | 2-3 | 2-3 | 2-3 | 2-3 (93 sor 3) |
| Nagybetűs kezdés | 69 | 17 | 63 | 84 | 89 |
| Írásjellel záródó input | 31 | 6 | 43 | 37 | 22 |
| Sem kezdő nagybetű, sem záró írásjel | 25 | 81 | 34 | 16 | 11 |
| Legfeljebb 3 javított szóalak | 63 | 14 | 83 | 94 | 91 |
| Javított szóalak / input szó | 0.209 | 0.347 | 0.124 | 0.094 | 0.113 |
| Szándékmegőrzés (input->output) | 0.84 | 0.67 | 0.91 | 0.93 | 0.91 |
| Különböző téma | 50 | 100 | 100 | 100 | 100 |

## 3. Ellenőrzési lépések

1. **Generálás**: 100 sor négy részben, soronként kézzel megírt input-output párokkal (nincs szabály- vagy sablongenerátor); az outputot mindig a saját inputjából levezetve írtam.
2. **Schema**: `dataset_validate.py` 100/100; saját ellenőrzés a 9 kötelező mezőre, `category`, `source`, `difficulty`, a `tags` fejlécre és az 5-6 tag-hosszra; téma-egyediség a batchen belül és az 1-4. batch 347 témájával szemben; instruction-szövegek eltérése az előző 120-tól.
3. **Input != output**: 0 azonos sor; minden sorban szóalak-szintű változás van; csak nagybetű/írásjel-változású sor 0 (3 sorban - `0402, 0407, 0450` - a javítás kizárólag szóhatár-javítás, lásd 7. fejezet).
4. **Valóban javítottabb-e**: (a) ismeretlen-szó arány a korpusz szókincséhez képest, sorpáronként (a batch saját fájlját a szókincsből kihagyva): 0.154 -> 0.112; öt sorban minimálisan nagyobb, lásd 2. fejezet; (b) formai zajmarkerek az outputban: 0 valódi; (c) nincs rövidítés, betűhalmozás és írásjel-halmozás az outputban.
5. **Zajcímkék bizonyítéka**: külön szkript minden sorra ellenőrzi, hogy a címkéhez tartozik-e szóalak-szintű nyom. Első futás 9 sort jelzett; javítva a `legókészlet` (*beszélt nyelv* kivéve) és a `kimondatlan gondolat` (*beszélt nyelv* kivéve), mert nem volt bizonyíték.
   A maradék 8 jelzés kézzel átnézve: `0404, 0457, 0472` (*o*/*0* tévesztés, a szkript szótára nem kezeli), `0488` (*kényelnes*, szomszédos billentyű) és `0470` (*ténykeg*) valódi elütés, az *elgépelés* címke jogos; `0402`, `0495` határeset a *hosszabb kusza mondat* címkénél (19-24 szavas, vessző nélküli mondat); `0407` (*nem tom*) beszélt szerkezet.
6. **Szándékmegőrzés**: tőszó-átfedés 0.91 / 0.91 (egyetlen sor sem < 0.5) + kézi olvasás.
7. **Batch dedupe**: id 0, instruction+input 0, output 0. Input-párok >= 0.7 hasonlóság: 0.
8. **Kereszt-dedupe a teljes korpusz ellen**: az új 100 sor a **3400** meglévő clean sorral szemben (az 1-4. noisy batch is benne van; `real_quick_ratio`/`quick_ratio` előszűréssel), 4 összevetésben; 0 találat, 0 id-ütközés.
9. **Safety/PII/identity bleed**: e-mail, URL, telefon/azonosító, irányítószám- és címminta 0; MF-AI/Nextora említés 0; `guard.looks_like_identity_bleed` 0; erős káromkodás 0; érzékeny téma kulcsszó 0. Enyhe indulatszó: *tök gáz*, *tök idegesítő*, *Mit tudom én*, *elegem van belőle*.
   A kérdések (pl. madáreleség, e-könyv olvasó, falióra elemcsere, 3D puzzle, esőcsatorna) az inputban maradnak, az outputban **nincs rájuk válasz vagy tanács**. Az egyetlen érzelmi hangvételű sor a `kimondatlan gondolat` (`0402`): semleges, tanács és személyes adat nélkül.
10. **Quality score**: 100.0 / 100.
11. **Regressziós teszt**: `tests/test_v1_7_4_dataset_foundation.py` - minden teszt sikeres, **STÁTUSZ: STABIL**.
12. **Manuális átolvasás és mintavétel**: mind a 100 sor input és output egymás mellett végigolvasva; formális minta 40 sor (6. fejezet).
13. **Clean/rejected/report**: clean 100, rejected 0 (üres fájl), ez a report; **progress** frissítve (helyi fájl, szándékosan nincs commitolva).
14. **Csomag-szintű ellenőrzés (mind az 500 noisy_input sor együtt; csak ellenőrzés, a korábbi batchek módosítása nélkül)**: `dataset_validate.py` 500 / 500 valid; `dataset_dedupe.py` id 0 / instruction+input 0 / output 0; saját páronkénti összevetés (input-input, output-output, instruction+input >= 0.9): 0 találat;
    az id-k `noisy_input_0001`-`0500` hézag nélkül; 500 egyedi input, output és quality_notes; input == output: 0; átlag quality_score 100.0 (az egyetlen 100 alatti sor a `0114`, 90: `low_instruction_overlap`); 447 különböző téma (az 1. batch 50 témát használt 100 sorra), 149 különböző instruction;
    difficulty easy 225 / medium 175 / hard 100; zajtípus soronként: 1 típus 100 sor (1. batch), 2 típus 84 sor, 3 típus 316 sor. A csomag-szintű minta- és arányvizsgálat (címke-egyensúly, ismétlődő fordulatok, pl. *szval* 60 inputban, *tök* 63 outputban) a záró audit/fix kör tárgya.

## 4. Mi számít javításnak (és mi nem)

- **Javítás**: billentyű-szomszédos elütés (*nrm -> nem, veke -> vele*), *o*/*0* tévesztés számokban (*1o -> 10*), összeírt szó szétválasztása (*nemtom -> nem tudom, mivan -> mi van*), szétírt szó összeírása (*ki csit -> kicsit, vala mi -> valami*),
  rövidítés/beszélt alak (*szval -> szóval*), hibás névelő (*a igazgatóhoz -> az igazgatóhoz*), hiányzó vesszők és záró írásjel, a kettős felkiáltójel/kérdőjel egyre csökkentése. A **sorrend és a tartalom** megmarad.
- **Nem javítás (szándékosan)**: a felhasználó hangját adó szavak és szerkezetek maradnak (*tök, gáz, cuki, ciki, pléd, tulaj, nem tom, persze, Figyi, haver*), az indulat (*ez már nem vicces*), a bizonytalanság (*azt hiszem*, *szerintem*, *lehet, hogy*), a kérdés kérdés marad.
  Nem került be új szó, tanács vagy magyarázat.
- **Ami nincs benne**: helyesírási szabály, tanács, válasz a kérdésre, hivatalosabb átfogalmazás, új tartalom.

## 5. Önkorrekciók az összeállítás és a teljes átolvasás során (mind clean előtt)

- **Csak formai vagy gyenge sor (3)**: `kisebb szülinapi terv`, `elmaradt visszahívás` és `időhúzó megbeszélés` első változatában nem volt szóalak-szintű hiba (csak vessző/pont); valódi elütés került beléjük (*szunte, visszahívnsk, döntöttünj*), és a quality_notes-ban lévő zárójeles, kitérő magyarázat konkrét jegyzetre lett cserélve.
- **Címkék (2)**: `legókészlet` és `kimondatlan gondolat`, lásd 3. fejezet, 5. pont.
- A 8 címke-jelzés és az 5 OOV-emelkedés kézi átnézése további módosítást nem igényelt.

## 6. Manuális mintavétel (formális 40 sor)

A minta rögzített szabály szerint készült (az id sorszáma 5-tel osztva 1 vagy 3 maradékot ad: 40 sor), nem válogatott. Mind a 100 sort elolvastam, a minta ennek a dokumentált része. Az értékelés az 5. fejezetben leírt javítások után történt.

| id | Zajtípusok (`tags`) | Konkrét javítások (szó-szintű különbség; a nagybetű- és írásjel-változás nem szerepel) | Értékelés |
|---|---|---|---|
| 0401 | enyhe szleng + elgépelés + beszélt nyelv | pizsanát -> pizsamát; szval -> szóval | OK |
| 0403 | telefonos gyors gépelés + elgépelés + szóköz- és írásjelhiba | kinyitpm -> kinyitom | OK |
| 0406 | kérdés félreütésekkel + elgépelés + beszélt nyelv | reggwl -> reggel; szval -> szóval | OK |
| 0408 | kérdés félreütésekkel + elgépelés + telefonos gyors gépelés | falióea -> falióra | OK |
| 0411 | enyhe szleng + elgépelés + beszélt nyelv | rohsnni -> rohanni | OK |
| 0413 | indulatos, laza stílus + kérdés félreütésekkel + elgépelés | dolgoznpm -> dolgoznom | OK |
| 0416 | enyhe szleng + szóköz- és írásjelhiba + elgépelés | szval -> szóval; nappalibsn -> nappaliban | OK |
| 0418 | enyhe szleng + szóköz- és írásjelhiba + elgépelés | alnát -> almát | OK |
| 0421 | kérdés félreütésekkel + elgépelés + telefonos gyors gépelés | ötdzör -> ötször | OK |
| 0423 | enyhe szleng + elgépelés + beszélt nyelv | szsbadnapom -> szabadnapom; szval -> szóval | OK |
| 0426 | szóköz- és írásjelhiba + telefonos gyors gépelés + beszélt nyelv | ki csit -> Kicsit; szval -> szóval | OK |
| 0428 | hosszabb kusza mondat + szóköz- és írásjelhiba + elgépelés | unslmas -> unalmas | OK |
| 0431 | enyhe szleng + telefonos gyors gépelés + beszélt nyelv | elestwm szval -> elestem szóval | OK |
| 0433 | beszélt nyelv + elgépelés + szóköz- és írásjelhiba | vidámparkbs -> vidámparkba; szval -> szóval | OK |
| 0436 | kérdés félreütésekkel + telefonos gyors gépelés + elgépelés | tegnao -> tegnap; ninden -> minden | OK |
| 0438 | enyhe szleng + elgépelés + beszélt nyelv | bögrér -> bögrét; szval -> szóval | OK |
| 0441 | hosszabb kusza mondat + indulatos, laza stílus + elgépelés | közelrg -> közeleg | OK |
| 0443 | telefonos gyors gépelés + elgépelés + beszélt nyelv | Szimbaton -> Szombaton; szval -> szóval | OK |
| 0446 | telefonos gyors gépelés + beszélt nyelv + elgépelés | szval -> szóval; hozpk -> hozok | OK |
| 0448 | hosszabb kusza mondat + indulatos, laza stílus + elgépelés | döntöttünj -> döntöttünk | OK |
| 0451 | telefonos gyors gépelés + ékezet nélkül + szóköz- és írásjelhiba | fenyoben -> fenyőben; talaltam -> találtam; kek pillangot es -> kék pillangót és; megorultem -> megörültem | OK |
| 0453 | enyhe szleng + elgépelés + beszélt nyelv | szval -> szóval; szomszédmak -> szomszédnak | OK |
| 0456 | kérdés félreütésekkel + elgépelés + telefonos gyors gépelés | mindenhil -> mindenhol | OK |
| 0458 | kérdés félreütésekkel + telefonos gyors gépelés + elgépelés | holnsp -> holnap; fitós -> fotós | OK |
| 0461 | kérdés félreütésekkel + elgépelés + telefonos gyors gépelés | csal -> csak | OK |
| 0463 | kérdés félreütésekkel + elgépelés + beszélt nyelv | elzárídott -> elzáródott | OK |
| 0466 | hosszabb kusza mondat + indulatos, laza stílus + elgépelés | rendeltrm -> rendeltem | OK |
| 0468 | kérdés félreütésekkel + szóköz- és írásjelhiba + elgépelés | Mivan -> Mi van; minfenki -> mindenki | OK |
| 0471 | szóköz- és írásjelhiba + telefonos gyors gépelés + elgépelés | azthiszem -> Azt hiszem; fáradr -> fáradt | OK |
| 0473 | hibás ragozás + szóköz- és írásjelhiba + elgépelés | leveler -> levelet; a -> az | OK |
| 0476 | enyhe szleng + elgépelés + beszélt nyelv | szval -> szóval; mrccset -> meccset | OK |
| 0478 | telefonos gyors gépelés + enyhe szleng + elgépelés | szépwt -> szépet; szval -> szóval | OK |
| 0481 | telefonos gyors gépelés + ékezet nélkül + beszélt nyelv | edzes szoval -> edzés szóval; es -> és; koran lefeknem -> korán lefeküdnöm | OK |
| 0483 | elgépelés + beszélt nyelv + szóköz- és írásjelhiba | 3o -> 30; szval -> szóval | OK |
| 0486 | enyhe szleng + telefonos gyors gépelés + beszélt nyelv | hörcsögön -> hörcsögöm; szval -> szóval | OK |
| 0488 | szóköz- és írásjelhiba + elgépelés + beszélt nyelv | Szerintemnem -> Szerintem nem; kényelnes szval nemtudom -> kényelmes szóval nem tudom | OK |
| 0491 | kérdés félreütésekkel + elgépelés + telefonos gyors gépelés | lejátszpm -> lejátszom | OK |
| 0493 | indulatos, laza stílus + elgépelés + szóköz- és írásjelhiba | visszahívnsk -> visszahívnak | OK |
| 0496 | szóköz- és írásjelhiba + beszélt nyelv | hogyvagy -> hogy vagy; szval -> szóval | OK |
| 0498 | indulatos, laza stílus + telefonos gyors gépelés + szóköz- és írásjelhiba | veke -> vele | OK |

**Eredmény: 40 / 40 megfelelt** (szempontok: az input és az output jelentése azonos, nincs új tartalom, a hang megmaradt, nem hivatalos, az output valóban tisztább). A teljes 100 soros olvasásból a 3. és 5. fejezetben leírt tételek javultak; a mintában maradt hiba nem volt.

## 7. Megfigyelések és korlátok (őszinte értékelés)

- **`zajos bemenet` tag 14.3%**: a topic report ezt túlreprezentáltnak jelzi (küszöb 8%). Ez a csomag jelölő címkéje, nem témaszaturáció, a csomag lezárásával már nem nő tovább. A `tools/dataset_topic_report.py` kezelése külön jóváhagyandó, ebben a körben nem módosítottam.
- **A „minden sorban szóalak-szintű javítás” hat sorban tágabb értelmezésű**: a `0404, 0457, 0472` javítása *o*/*0* számtévesztés (*5o -> 50*), a `0402, 0407, 0450` javítása szóhatár (*vala mi*, *el kezdtem*, *mivan*, *nemtudom*). Ezek valódi szóalak-javítások, de az automatikus „javított szóalak” mérőszám nem számolja őket (ez a `noisy_extra.py` szerint hat „csak formai” sornak tűnik). Ha a csomag audit során szigorúbb definíciót kell, ezt a hat sort érdemes újrafogalmazni.
- **A zajcímkék részben stílust jelölnek, nem külön javítást**: 93 sor kap 3 címkét, de a sorok átlagosan 1.9 szóalak-javítást tartalmaznak. Az *indulatos*, *enyhe szleng*, *kérdés félreütésekkel* és *hosszabb kusza mondat* címke gyakran a szöveg hangját vagy szerkezetét írja le. A címkét ne tekintsük pontos, hibánként adott annotációnak.
- **Az *ékezet nélkül* típus csak 3 sorban szerepel a batchben** (a kérés szerint kevés szétesett input); a csomag egészében az 1-4. batch fedi. A *hibás ragozás* és *rövidítés* címke ebben a batchben szinte hiányzik (1 / 0 sor).
- **Az *o*/*0* tévesztés csak számokban van** (természetesség miatt); nincs *0* betűként szavakban, és nincs *l*/*1*, *I*/*l* tévesztés.
- **Tagolás**: csak 22 input kezdődik nagybetűvel és zárul írásjellel; a többi hiányzó záró írásjelet is tartalmaz, ez a telefonos gépelés része, de az 5. csomag egészének tanításakor érdemes ügyelni a mintaarányra (lásd a záró audit javaslatot).
- **Az ismeretlen-szó arány heurisztika**: a korpusz szókincse magyar ragozás miatt hiányos, a *10*, *30* jellegű számtokenek is ismeretlenek; csak sorpáronkénti összevetésre jó.
- **Az ellenőrző scriptek** (`noisy_check5.py`, `noisy_extra.py`, `noisy_light3.py`, `noisy_special5.py`, `verify_labels5.py`, `gen_noisy_batch5.py`) a repón kívül vannak; a `tools/` alá emelésük külön jóváhagyandó.
- **A validátor csak az outputot vizsgálja** torz tokenekre és angol keveredésre; az input szándékosan zajos.

## 8. Fájlok

- Raw: `data/raw/claude_noisy_input_0401_0500_raw.jsonl` (100 sor)
- Clean: `data/clean/claude_noisy_input_0401_0500_clean.jsonl` (100 sor)
- Rejected: `data/rejected/claude_noisy_input_0401_0500_rejected.jsonl` (0 sor, üres fájl)
- Report: `data/reports/claude_noisy_input_0401_0500_report.md`

## 9. Amit ez a kör NEM tett

- Nem indított tanítást, nem módosított webapp/backend kódot, nem törölt és nem írt felül semmit (az 1-4. batch fájljaihoz és a validátorhoz sem nyúlt).
- Nem futtatott záró audit/fix kört az 5. csomagon (külön jóváhagyásra vár, lásd az összegzés javaslatát).
- Nem használt webes forrást, valós felhasználói szöveget, ChatGPT/Dispatch raw jelöltet.
- Nem módosította a topic report tag-kezelését, és nem emelte a scripteket a repóba.

---

## Végső összegzés

- Batch: 100 sor, **100 clean / 0 rejected**, átlag score 100.0, regressziós teszt STABIL.
- A kért új zajfajták: 80 sorban billentyű-szomszédos elütés (82 db), 7 sorban *o*/*0* tévesztés számokban, 12 összeírt és 4 szétírt szó (*nemtom, mivan, nemis, vala mi, ki csit*); 93 sor legalább egyet tartalmaz.
- A stabil irány: szándékmegőrzés 0.91 / 0.91, 89 nagybetűs kezdésű üzenet, csak 11 formátlan (kisbetűs, írásjel nélküli) sor, 91 sorban legfeljebb 3 javított szóalak, 0 csak nagybetű/írásjel-változású sor, 2-3 zajtípus (93 sor 3), 100 új téma.
- Megmaradt hangsúlyok (összes címke): enyhe szleng 25, félreütött kérdés 23, indulatos 21, kusza mondat 16.
- Ellenőrzések: 100/100 valid, input != output, 0 duplikátum és 0 kereszt-találat a 3400 sor ellen (az 1-4. batchet is beleértve), 0 PII/URL/identity bleed/erős káromkodás/érzékeny kulcsszó; ismeretlen-szó arány 0.154 -> 0.112.
- Manuális: mind a 100 sor elolvasva, formális minta 40/40 megfelelt; az összeállítás közben javított hibák az 5. fejezetben.
- **5. csomag: 500 / 500 noisy_input clean**, 0 rejected; teljes clean korpusz: **3500 sor**. Záró audit/fix kör: **javasolt** (csomag-szintű ellenőrzések, címke- és arány-egyensúly, lásd a válasz összegzését).

**STÁTUSZ: STABIL.**
