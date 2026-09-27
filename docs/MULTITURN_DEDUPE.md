# MT-3 — többfordulós duplikáció-ellenőrzés és csoportosítás

Eszköz: `tools/multiturn_dedupe.py` (mt3-2.0). Tesztek: `tests/test_multiturn_dedupe.py`. Bemenet: az `docs/MULTITURN_FORMAT.md` szerinti, az MT-1 által **turns-validált** beszélgetés-rekordok. Az eszköz **csak olvas**; a forrásadatot nem módosítja és nem törli. A felosztás (MT-2, `docs/MULTITURN_SPLIT.md`) erre a jelentésre épül.

**Alapelv (kézikönyvi döntési elv): ugyanaz a téma megengedett, ugyanaz a tanítási minta nem.**

A revideált (mt3-2.0) döntések a felhasználó jóváhagyott szabályai; a korábbi (mt3-1.0) megfeleltetések (`>=` alap, deklarált változat lefokozása, névsemlegesített döntés, triviális minta `review`) **megszűntek**.

| Kézikönyvi szabály | Az eszközben |
|---|---|
| pontosan ismétlődő tanítási minta (előzménnyel együtt, **rövidségtől függetlenül**): elutasítás vagy javítás | `reject` (`sample_exact`, `exact_conversation`, `exact_after_normalization`) — külön szabály, nem menthető fel |
| **0,90 fölötti** hasonlóság: felülvizsgálat | `review` — szigorú `>`; pontosan 0,90: nem fölötte |
| **0,95 fölötti** hasonlóság: alapból elutasítás, kivéve dokumentáltan eltérő képességet tanítót | `reject` — szigorú `>`; kivétel csak dokumentált tartalmi indokkal (`--exceptions`, kötelező `capability` mező); a közös `split_group` **nem** indok |
| bizonytalan eset | `review` (haladási tiltás) |

**Az elutasítás státusz és haladási tiltás, nem törlés.** A `reject` és a `review` a rekordot `blocked` (haladás tiltva) állapotba teszi; a bemeneti fájlok érintetlenek. A `clear_of_duplicate_findings` állapot **nem** elfogadás, **nem** tartalmi ellenőrzés és **nem** training-ready; a szöveges hasonlóság **nem** bizonyított jelentésazonosság.

## 1. Mit vet össze

| Szint | Egység | Összehasonlítás |
|---|---|---|
| azonosító | rekord-`id` | fájlon belül, fájlok között és a TE-1 exportált példák azonosítóival: mindig `reject` |
| beszélgetés | teljes beszélgetés | pontos (nyers), normalizálás utáni pontos és közeli egyezés; a hasonlítás szerep- és pozíció-őrző |
| minta | egy **assistant-fordulóra adott tanítási minta** = (releváns előzmény, kérdés, válasz) | csomagon belül, csomagok (fájlok) között és a TE-1 export példáival |
| üzenet-átfedés | azonos hosszabb (≥ 20 normalizált karakter) üzenetek másik szerepben vagy másik helyen | szerepcsere, sorrendcsere jelzése |
| csoport | összetartozó változatok | egyszeres kötésű csoportosítás, reprodukálható azonosító |

Csomagon belüli és csomagok közötti ismétlődés: a `--conversations` több fájlt is fogad; minden fájl egy csomag/batch. A találat `duplicate_id` esetén jelzi, hogy `same_file` vagy `across_files`; a beszélgetés- és minta-találatnál a `file`/`line` mező mutatja a forrást. A **TE-1 export** (a 4494 egyfordulós példa) külön referencia: mintaszinten hasonlítjuk (előzmény nélküli minta).

## 2. Normalizálás

Az összehasonlítás normalizált szövegen történik, üzenetenként (a `User:`/`AI:` címkék, elválasztók és sorszámok nem részei az összehasonlított szövegnek, ezért nem torzítják a hasonlóságot):

1. NFC; tipográfiai idézőjelek és gondolatjelek egységesítése;
2. listajelölők (`1.`, `2)`, `-`, `•`, `*`) eltávolítása;
3. kisbetű (`casefold`); írásjelek szóközre; szóközök összevonása.

A **döntések az eredeti, névvel együtti normalizált szövegen születnek.** A **névsemlegesítés** (az MT-0 névtár keresztnevei, ragozott alakjukkal, `NÉV` tokenre cserélve) **kiegészítő jelzés** (lásd 5. szakasz): a rekord mindkét nézetet megőrzi, az eredeti szöveg sosem módosul, a jelentés az eredeti üzeneteket idézi. `--no-name-normalization` kikapcsolja a kiegészítő jelzést.

A **számok és az ékezetek megmaradnak** (a `kér` és a `ker` különbözik). A normalizálás nem ismeri fel az átfogalmazást vagy a szinonimát.

## 3. Pontszám — mi mit jelent

**Hasonlóság.** `difflib.SequenceMatcher(None, a, b, autojunk=False)` egyező-karakter arányából: `2·M/(|a|+|b|)`, ahol `M` az egyező blokkok karaktereinek összege, `a` a korábbi rekord/minta. Ez **szöveges átfedés**, nem jelentés-azonosság. A meglévő `dataset_dedupe` alapértelmezett `autojunk`-ot használ; az MT-3 `autojunk=False`-ot, mert 200 karakter fölött az alapértelmezés a gyakori karaktereket kihagyná, és a hosszabb szövegek hasonlóságát alulbecsülné.

**Beszélgetés-szint (összevont, szerep- és pozíció-őrző arány).** `2·ΣM_i / Σ(|a_i|+|b_i|)`, ahol `i` az azonos indexű, azonos szerepű üzenetpárokon fut; a párosítatlan üzenetek hossza a nevezőben szerepel (`M=0`). Az azonos szöveg **másik szerepben** vagy **másik helyen** nem ad egyezést: a szerepek és az üzenetsorrend jelentősége megmarad. Az arány a beszélgetés összes karakterére vonatkozik, így egy rövid közös köszönés vagy rövid válasz önmagában nem teszi duplikálttá a beszélgetést.

**Minta-szint.** A minta három része külön arány: `q` (kérdés), `a` (válasz), `c` (releváns előzmény). **Pontszám = min(q, a, c)**: a minta csak akkor ismétlődő, ha a kérdés, a válasz és az előzmény is ismétlődik. Releváns előzmény = az előző váltás (`t-3`, `t-2`) **és** a `meta.depends` által megjelölt üzenetek (a kérdés, `t-1`, nem része). Két üres előzmény `c = 1,0`; az egyik üres → `c = 0,0`; nem üres előzményeket jobbra igazítva, szerepőrzően hasonlítunk. Az annotáció helyességét az eszköz nem ellenőrzi.

**Export-szint.** A TE-1 példa mint minta: kérdés = `instruction` + input, válasz = `output`, előzmény nélkül. Előzményes fordulat így nem lehet duplikátum, csak részleges egyezés.

**Pontos egyezés (külön szabály).** A kérdés, a válasz és az előzmény azonos (minta), illetve a szerepek, a sorrend és a normalizált szöveg azonos (beszélgetés): `reject`, a hasonlósági küszöböktől és a **szöveg hosszától függetlenül**. A teljes, előzménnyel együtt azonos tanítási minta rövid (pl. köszönés) is elutasítandó vagy javítandó — ez azt jelenti, hogy két beszélgetés azonos „Szia!” / „Szia! Miben segíthetek?” nyitó váltása mintaszinten `reject`; javítás: a nyitó váltás változtatása. A beszélgetés-szint ettől független: a közös köszönés a beszélgetést nem teszi duplikálttá (`conversation_decision` nem `blocked`), és a rövid minta nem köt csoportot.

**Határértékek (`>` alapból, `>=` opcionálisan).** A kézikönyv „fölött” szava szó szerint `>`: az MT-3 alapból ezt alkalmazza (**0,90 fölött `review`, 0,95 fölött `reject`**), a pontosan 0,90 érték csak közeli változat (`near_variant`, beszélgetés-szint) vagy `sample_at_boundary` (`info`, minta-szint), a pontosan 0,95 érték `review`. A pontosan a határon lévő találat `at_boundary: true` jelzést kap. A régi eszközök `>=` határát a `--inclusive-boundaries` adja (a jelentés `config.decision_rules.comparison` értéke `>` vagy `>=`). Az előszűrt és a teljes összehasonlítás a határértékeken is azonos (tesztelt).

## 4. Kísérleti jelzések és amit nem bizonyítanak

Három jelzés dokumentáltan **kísérleti**. Egyik sem bizonyít jelentésbeli egyediséget, **a találat hiánya sem**, és egyik sem helyettesíti a tartalmi átolvasást. A jelentés `summary.experimental_signals` mezője számolja őket, a `config.experimental` rögzíti a beállításukat.

| Jelzés | Szabály | Megjegyzés |
|---|---|---|
| **rövid szöveg** (`sample_near_short`) | ha a kérdés+válasz < 60 normalizált karakter, a hasonlóság **nem utasít el automatikusan és nem fogad el**: `review` (haladási tiltás); pontosan 0,90 → `info` | 1–2 karakter eltérés is 0,9 fölé visz (pl. „hány nap van egy hétben/évben”: 0,933), ezért a küszöb itt nem értelmezhető; a **pontos** egyezés rövid szövegnél is `reject` |
| **átfogalmazás** (`probable_paraphrase_variant`) | tartalmi szó-átfedés (Jaccard, 4 karakteres tövek) ≥ 0,35, legalább 15 tartalmi szó → `review` | a küszöb kis mintán kalibrált; **a szintetikus terhelés 8/10 felismerési eredménye csak arra a konkrét tesztkészletre vonatkozik**. Szűk szókincsű, véletlenszerű szövegen hamis pozitív is előfordul (lásd `data/reports/mt2_report.md`), ezért felülvizsgálatot kér, nem dönt |
| **névsemlegesített egyezés** (`name_swapped_match`, `sample_name_swapped`) | lásd 5. szakasz | kiegészítő jelzés |

## 5. Névcsere: kiegészítő jelzés, az eredeti szöveg megőrzésével

* A döntés az **eredeti (névvel együtti)** szövegen történik. Egy névcserés másolat, amelynek nyers hasonlósága 0,95 fölött van, ezért a nyers nézeten `reject` (0,90–0,95: `review`); külön névcsere-jelzés nem keletkezik, mert a döntés már megszületett.
* Ha a nyers nézeten **nincs döntési szintű találat**, de a névsemlegesített szöveg azonos vagy a határok fölötti hasonlóságú (pl. sok név a szövegben: nyersen 0,84, névsemlegesítve 1,0), a jelentés kiegészítő `review` jelzést ad: **`name_swapped_match`** (beszélgetés) vagy **`sample_name_swapped`** (minta/export). Ez sosem `reject`, és sosem fogad el.
* A jelzés csak azokra a párokra fut, ahol legalább az egyik oldalon szerepel névtár-név; név nélküli párokon a kiegészítő menet nem fut.
* A találat rögzíti: `raw_score`, `masked_score`, a két oldal nevei (`names_a`, `names_b`), és az **eredeti** üzeneteket (`differing_original_messages`, illetve `original_a`/`original_b` a mintáknál), `experimental_supplementary: true`.
* **A puszta névcsere nem új képesség.** A felülvizsgáló dönt: javítás (a beszélgetés érdemi változtatása), vagy dokumentált indok `--exceptions` bejegyzéssel, ha a szereplők vagy kapcsolataik változása miatt a feladat eltérő (pl. más kapcsolat, más szerep a történetben). Az eszköz ezt nem tudja megítélni.

## 6. Találat-típusok és döntések

| Típus | Szint | Státusz | Megjegyzés |
|---|---|---|---|
| `duplicate_id` | azonosító | `reject` | nem menthető fel |
| `exact_conversation` | beszélgetés | `reject` | nyers azonosság; nem menthető fel; közös `split_group` mellett is |
| `exact_after_normalization` | beszélgetés | `reject` | csak írásjelben/kis-nagybetűben/listajelölőben tér el (a nevek megmaradnak); nem menthető fel |
| `near_conversation` | beszélgetés | `reject` > 0,95, `review` > 0,90 | összevont arány; közös `split_group` mellett is; `details.declared_variant` csak tájékoztató |
| `near_variant` | beszélgetés | `info` | 0,80–0,90 (a pontosan 0,90 is): csak csoportosítás |
| `probable_paraphrase_variant` | beszélgetés | `review` | **kísérleti** (szó-átfedés ≥ 0,35) |
| `name_swapped_match` | beszélgetés | `review` | **kiegészítő** (5. szakasz) |
| `roles_swapped_messages`, `messages_reordered` | beszélgetés | `review` | azonos üzenetek másik szerepben; másik helyen (más sorrendben vagy eltolva, pl. beszúrt váltás után) |
| `sample_exact` | minta / export | `reject` | előzménnyel együtt azonos minta, **hossztól függetlenül**; nem menthető fel |
| `sample_near` | minta / export | `reject` > 0,95, `review` > 0,90 | min(q, a, c) |
| `sample_near_short` | minta / export | `review` | **kísérleti** rövid-szöveg kivétel (4. szakasz) |
| `sample_at_boundary` | minta / export | `info` | pontosan 0,90 (szigorú `>` mellett nem fölötte) |
| `sample_name_swapped` | minta / export | `review` | **kiegészítő** (5. szakasz) |
| `same_qa_different_context`, `same_question_different_context`, `same_question_context_different_answer`, `shared_answer_different_question` | minta / export | `info` | **részleges szövegegyezés**, nem ismétlődő tanítási minta |
| `persona_reuse_exceeds_limit`, `declared_group_too_large`, `group_too_large` | csoport | `review` | terv 4.3; csoportméret (csoport-szintű: rekordot nem blokkol) |
| `declared_groups_merged` | csoport | `info` | a számított csoport a mérvadó |

Minden találat rögzíti: az érintett rekordot és fordulót (`turn`, fájl, sor), az egyezés típusát, a pontszámot és a módszert, a döntési státuszt és indokot, valamint (a rekordokhoz és a csoportokhoz) a csoportazonosítót. **Külön** szerepel a részleges szövegegyezés (`info`) és a valóban ismétlődő tanítási minta (`sample_exact`/`sample_near`).

**A közös `split_group` nem írja felül a duplikációs döntést.** A tervezett változat (közös `split_group`) is `reject`, ha 0,95 fölötti, és az azonos szövegű nyers másolat mindig `reject`. A csoportazonosító a felosztást segíti, nem minőségi felmentés. A 0,95 fölötti egyezés csak dokumentált tartalmi indokkal kaphat kivételt (7. szakasz).

## 7. Csoportosítás (az MT-2 alapja)

**Élek** (a csoport a rekordok összefüggő halmaza): pontos vagy normalizálás utáni azonosság; összevont hasonlóság ≥ 0,80 (`near_conversation`/`near_variant`); `probable_paraphrase_variant`; `name_swapped_match`/`sample_name_swapped`; szerepcsere/sorrendcsere; nem rövid ismétlődő minta (`sample_overlap`, > 0,90 vagy pontos); azonos `persona`; azonos deklarált `split_group`. Nem él: az `info` részleges egyezés, a **rövid** (< 60 karakteres) minták találatai (`sample_exact` és `sample_near_short` egyaránt), a TE-1 export találatai (más adatcsomag).

**Láncolt hasonlóság szabálya (egyszeres kötés, tranzitív lezárás):** ha A hasonlít B-re és B C-re, akkor A, B és C **egy csoport**, akkor is, ha A és C közvetlenül nem hasonlít. Indok: ha egy tag a tanító-, egy másik a teszthalmazba kerülne, a közvetítő tagon át a tartalom átszivárogna. A csoportosítás így konzervatív; a láncnak van ára: hosszú lánc nagy csoportot adhat. Védelem: `group_too_large` (`review`) 5 tag fölött, a leggyengébb élekkel; a felülvizsgáló dönt, mely élek nem valódi változat-kapcsolatok.

**Csoportazonosító:** `mtg_<a csoport lexikografikusan legkisebb rekordazonosítója>`. Ugyanarra a bemeneti halmazra mindig ugyanaz (a bemeneti sorrend és a fájlfelosztás nem számít); nagyobb azonosítójú tag csatlakozásakor nem változik; **kisebb azonosítójú tag csatlakozásakor változik** (ezért a felosztás előtt a végleges bemenetre kell futtatni, és az eredmény a bemeneti fájlok ellenőrzőösszegéhez kötött).

**Deklarált és számított csoport:** a rekordok `meta.split_group` mezője a szerzői szándék; az MT-2 felosztás a **számított** csoportot használja, amely a deklaráltak fölé is összevonhat (`declared_groups_merged`). Egy csoport minden tagja (és mintája) csak **egy** részbe kerülhet.

**Tervezett változat-arány:** a többtagú csoportokba tartozó rekordok aránya (`variant_share`); a terv szerinti 15% fölött a `variant_share_over_plan` jelzi (nem blokkol).

## 8. Kivételek (dokumentált eltérő képesség)

`--exceptions <json>`: lista, elemei `{"a": id, "b": id, "waive": ["<típus>", ...] | ["*"], "reason": "…≥ 15 karakter…", "capability": "…≥ 15 karakter…", "reviewer": "…"}`. A megnevezett pár megnevezett típusú **blokkoló** találatait `accepted_with_exception` státuszra állítja (az eredeti státusz a `status_before_exception` mezőben marad; az indok és a `capability` a találatban és a jelentésben). `"*"` a pár összes **felmenthető** találata.

* **Reject-szintű (0,95 fölötti) találat felmentéséhez a `capability` mező kötelező**: a dokumentált tartalmi indok arról, hogy a két minta mit tanít eltérően. A közös `split_group` vagy a puszta névcsere nem indok. Review-szintű találathoz elég a `reason`.
* **Nem menthető fel:** `duplicate_id`, `exact_conversation`, `exact_after_normalization`, `sample_exact` (a pontos ismétlődés „elutasítás vagy javítás”). A `"*"` ezeket nem érinti.
* Ismeretlen azonosító, nem létező találat, rövid indok vagy `capability`, ismeretlen kulcs → hiba (elavult vagy téves kivétel nem maradhat észrevétlen). A kivétel a csoportosítást nem szünteti meg (az MT-2 a felmentett párt még egy egységbe is vonja), és a fájl ellenőrzőösszege a jelentés része.

## 9. Reprodukálhatóság és a bemenet védelme

* A jelentés rögzíti a bemeneti fájlok (beszélgetés-fájlok, TE-1 export manifest/export/index, névtár, kivétel-fájl) ellenőrzőösszegét, **az MT-3 eszköz fájljának ellenőrzőösszegét** (`tool_sha256`) és rekordonként a forrássor ellenőrzőösszegét (`line_sha256`); az MT-2 ezekre támaszkodva ismeri fel az elavult jelentést. A TE-1 export a `te2.load_te1_export` ellenőrzésével jön be (manifest, ellenőrzőösszegek, index).
* A bemenet a futás **közben** megváltozott → hiba (16-os kód, jelentés nélkül). A futás **után** megváltozott bemenetet a `--verify-report <jelentés>` mutatja (15-ös kód).
* Csak turns-validált rekord (MT-1, a megfelelő móddal) fogadható; egyébként 11-es kód és a hibás rekordok felsorolása.
* Az új futás-mappa soha nem ír felül semmit; nem lehet a bemeneti mappa alatt, sem `data/clean|raw|rejected|inbox` alatt.
* Kimenet: `dedupe_report.json` (konfiguráció, bemenetek, időmérés, számlálók, összegzés, találatok, csoportok, rekordállapotok, korlátok), `findings.tsv`, `groups.json`, `record_status.tsv`.

## 10. Gyorsítás — garantált, nem közelítő

A hossz- és karakter-multiset felső korlát **bizonyítottan pontos**: az egyező karakterek közös részsorozatot alkotnak, ezért `M ≤ min(|a|,|b|)` és `M ≤ Σ_c min(a_c, b_c)` (a két karakter-multiset metszete); a szűrő csak azt a párt hagyja ki, amelynek aránya biztosan a vizsgált küszöb alatt van. Ritka karaktereket egy vödörbe vonva a korlát csak lazább lesz, nem érvénytelen. A minta-szintű kérdés-hossz ablak (`2·min/(a+b) ≥ küszöb`) ugyanezt az elvet követi. A küszöb az **inkluzív** érték (≥ 0,90): a szigorú `>` szabály így is teljes: a határon lévő párok is átmennek az előszűrőn, és csak a döntés dönt. Az eredmény a teljes összehasonlítással (`--no-prefilter`) **azonos**, mindkét határ-értelmezésben és a névsemleges kiegészítő menetben is; ezt a tesztek (szintetikus korpusz, a 0,90/0,95 határra tervezett párokkal, névlistás párral és export-sorral) igazolják. A paraphrase-heurisztika nem szűrő: minden párra fut.

## 11. Mért futásidő

Ugyanazon a gépen, egymás után mérve (1050 szintetikus beszélgetés a valódi 4494 példás exporttal szemben, egy folyamat): mt3-1.0 **89,0 mp**, mt3-2.0 **97,9 mp** (+10%; ebből a kiegészítő névsemleges menet 4,4 mp: 31 034 beszélgetés-pár és 411 107 minta-pár). Az összehasonlított párok száma azonos. Részletek: `data/reports/mt2_report.md` A. rész és `data/reports/audit_evidence/mt3_dedupe/` (`benchmark_results_1000_mt3v2.json`, `benchmark_results_1000_mt3v1_same_session.json`). A régi jelentésben szereplő ~60 mp más géphelyzetben készült.

## 12. Korlátok

* A hasonlóság karakter-alapú átfedés, nem jelentés-azonosság; az átfogalmazás nagyrészt észrevétlen marad, és a kísérleti heurisztika hiánya sem bizonyít egyediséget.
* A pozíció-őrző arány beszúrt/törölt váltás után alacsony lehet; a minta-szintű és az üzenet-átfedéses ellenőrzés ezt részben pótolja.
* Rövid szövegnél a küszöb nem értelmezhető (4. szakasz); csak a pontos egyezés dönt.
* A névsemlegesítés a névtárra épül; a névtárban nem szereplő név különbség. A kiegészítő jelzés nem tudja megítélni, hogy a névcsere mellett a szereplők kapcsolata is változott-e.
* A csoportosítás egyszeres kötésű: lánc nagy csoportot adhat.
* A `meta.depends` annotáció helyességét az eszköz nem ellenőrzi.
* Az eszköz nem ítéli meg, hogy két tanítási minta **tartalmilag** tanít-e eltérő képességet: ezt a kézi felülvizsgálat (`review`) és a dokumentált kivétel (`capability`) dönti el.
* A `clear_of_duplicate_findings` nem elfogadás és nem training-ready.

## 13. Használat és kilépési kódok

```bash
python tools/multiturn_dedupe.py --mode dataset --conversations <f1.jsonl> [<f2.jsonl> ...] --out-dir <mappa> [--te1-export <TE-1 futás-mappa>] [--exceptions <json>] [--inclusive-boundaries]
python tools/multiturn_dedupe.py --verify-report <dedupe_report.json>
```

`0` lefutott, nincs blokkoló találat; `1` lefutott, van `reject`/`review`; `2` argumentumhiba; `10` bemeneti fájl hiba; `11` nem turns-validált rekord; `12` TE-1 export hiba; `13` kivétel-fájl hiba; `14` kimeneti útvonal hiba; `15` a bemenet megváltozott a jelentés óta; `16` a bemenet a futás közben megváltozott. A küszöbök (0,90/0,95) parancssorból **nem** módosíthatók; a `--inclusive-boundaries` csak a határ értelmezését (`>` helyett `>=`) váltja.
