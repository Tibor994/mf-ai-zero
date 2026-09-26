# MT-3 — többfordulós duplikáció-ellenőrzés és csoportosítás

Eszköz: `tools/multiturn_dedupe.py` (mt3-1.0). Tesztek: `tests/test_multiturn_dedupe.py`. Bemenet: az `docs/MULTITURN_FORMAT.md` szerinti, az MT-1 által **turns-validált** beszélgetés-rekordok. Az eszköz **csak olvas**; a forrásadatot nem módosítja és nem törli.

**Alapelv (kézikönyvi döntési elv): ugyanaz a téma megengedett, ugyanaz a tanítási minta nem.**

| Kézikönyvi szabály | Az eszközben |
|---|---|
| pontosan ismétlődő tanítási minta: elutasítás vagy javítás szükséges | `reject` |
| 0,90 fölötti hasonlóság: felülvizsgálat | `review` |
| 0,95 fölötti hasonlóság: alapból elutasítás, kivéve dokumentáltan eltérő képességet tanítót | `reject`; deklarált változatnál (közös `split_group`) `review`; dokumentált kivétel: `--exceptions` |
| bizonytalan eset | `review` (nem megy automatikusan tovább) |

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
2. **névsemlegesítés** (alapból): az MT-0 névtár (`approved_given_names`, `blocked_given_names`) keresztnevei, ragozott alakjukkal (a MT-1 illesztő szerint) `NÉV` tokenre cserélve; így a névcserés másolat normalizálás után azonos. `--no-name-normalization` kikapcsolja;
3. listajelölők (`1.`, `2)`, `-`, `•`, `*`) eltávolítása;
4. kisbetű (`casefold`); írásjelek szóközre; szóközök összevonása.

A **számok és az ékezetek megmaradnak** (a `kér` és a `ker` különbözik). A normalizálás nem ismeri fel az átfogalmazást vagy a szinonimát.

## 3. Pontszám — mi mit jelent

**Hasonlóság.** `difflib.SequenceMatcher(None, a, b, autojunk=False)` egyező-karakter arányából: `2·M/(|a|+|b|)`, ahol `M` az egyező blokkok karaktereinek összege, `a` a korábbi rekord/minta. Ez **szöveges átfedés**, nem jelentés-azonosság. A meglévő `dataset_dedupe` alapértelmezett `autojunk`-ot használ; az MT-3 `autojunk=False`-ot, mert 200 karakter fölött az alapértelmezés a gyakori karaktereket kihagyná, és a hosszabb szövegek hasonlóságát alulbecsülné.

**Beszélgetés-szint (összevont, szerep- és pozíció-őrző arány).** `2·ΣM_i / Σ(|a_i|+|b_i|)`, ahol `i` az azonos indexű, azonos szerepű üzenetpárokon fut; a párosítatlan üzenetek hossza a nevezőben szerepel (`M=0`). Az azonos szöveg **másik szerepben** vagy **másik helyen** nem ad egyezést: a szerepek és az üzenetsorrend jelentősége megmarad. Az arány a beszélgetés összes karakterére vonatkozik, így egy rövid közös köszönés vagy rövid válasz önmagában nem viszi a beszélgetést a határok közelébe.

**Minta-szint.** A minta három része külön arány: `q` (kérdés), `a` (válasz), `c` (releváns előzmény). **Pontszám = min(q, a, c)**: a minta csak akkor ismétlődő, ha a kérdés, a válasz és az előzmény is ismétlődik. Releváns előzmény = az előző váltás (`t-3`, `t-2`) **és** a `meta.depends` által megjelölt üzenetek (a kérdés, `t-1`, nem része). Két üres előzmény `c = 1,0`; az egyik üres → `c = 0,0`; nem üres előzményeket jobbra igazítva, szerepőrzően hasonlítunk. Az annotáció helyességét az eszköz nem ellenőrzi.

**Export-szint.** A TE-1 példa mint minta: kérdés = `instruction` + input, válasz = `output`, előzmény nélkül. Előzményes fordulat így nem lehet duplikátum, csak részleges egyezés.

**Pontos egyezés.** A normalizált szöveg, a szerepek és a sorrend azonos. A **nyers** pontos egyezés (`exact_conversation`) és az azonosító-ütközés (`duplicate_id`) **nem menthető fel** kivétellel.

**Határeset (`>=` vagy `>`).** A kézikönyv „fölött” szava szó szerint `>`; a meglévő eszközök (`dataset_dedupe`) `>=`-t használnak. Az MT-3 alapból a konzervatív `>=`-t alkalmazza, és a pontosan 0,90/0,95 értéket `at_boundary: true` jelzéssel látja el; `--handbook-strict` a szó szerinti `>` értelmezést használja. Az érték a jelentés `config.decision_rules` részében szerepel. **Jóváhagyást kérő eltérés/megfeleltetés, nem csendes módosítás.**

## 4. A 0,90/0,95 határok értelmezhetősége — mért eltérések és javasolt megfeleltetés

A határokat a karakter-arányra alkalmazzuk; ott ez értelmezhető. Ahol nem, azt itt mutatjuk be (mért értékek: a 5 tesztfixture és kézzel készült változatai, lásd `tests/test_multiturn_dedupe.py`):

| Eset | Mért érték | Következmény |
|---|---|---|
| névcserés másolat, névsemlegesítés nélkül | 0,9747 | ≥ 0,95 → `reject` |
| névcserés másolat, névsemlegesítéssel | 1,0 | normalizálás után pontos → `reject` |
| kézzel átfogalmazott változat (ugyanaz a forgatókönyv) | összevont 0,634 | a 0,90/0,95 határ **nem értelmezhető** átfogalmazásra: a karakter-arány nem látja meg |
| ugyanaz + szó-átfedés (Jaccard, 4 karakteres tövek) | 0,429 (nem rokon fixture-párok: ≤ 0,074) | külön heurisztika: `probable_paraphrase_variant` → `review`, küszöb 0,35 (**ideiglenes**, 15 fixture-pár és 1 kézi átfogalmazás alapján kalibrált) |
| szerepcserés másolat | összevont 0,266 | nem azonos beszélgetés; az üzenet-átfedés `roles_swapped_messages` → `review` |
| a user-üzenetek sorrendje felcserélve | összevont 0,8005 | `near_variant` (info) + `messages_reordered` → `review` |
| rövid kérdések („hány nap van egy hétben” / „…évben”) | 0,933 | rövid szövegnél 1–2 karakter is a 0,9 fölé visz: **a küszöb nem értelmezhető** |
| lánc: A–B 0,815, B–C 0,849, A–C 0,672 | — | csak a szomszédok közeli változatok; a csoport tranzitív (6. szakasz) |

**Javasolt megfeleltetés (a kézikönyv számait nem módosítottuk; jóváhagyást kérünk):**
1. A 0,90/0,95 a fenti **karakter-arányra** vonatkozik, beszélgetés- és minta-szinten.
2. **Rövid minta** (kérdés+válasz < 60 normalizált karakter): a hasonlóság nem dönt; csak a **pontos** egyezés jelez, `review` szinten (`sample_exact_trivial`), mert egy közös köszönés ismétlődése tervezett lehet, de automatikusan nem mehet tovább. Nem-triviális pontos minta: `reject`.
3. **Átfogalmazás:** külön heurisztika (`review`), sosem dönt automatikusan.
4. **Határeset:** `>=` (alap) és `--handbook-strict` (`>`) — a jóváhagyandó döntés.

## 5. Találat-típusok és döntések

| Típus | Szint | Státusz | Megjegyzés |
|---|---|---|---|
| `duplicate_id` | azonosító | `reject` | nem menthető fel |
| `exact_conversation` | beszélgetés | `reject` | nyers azonosság; nem menthető fel; deklarált változatnál is |
| `exact_after_normalization` | beszélgetés | `reject` (deklarált változat: `review`) | pl. névcserés másolat |
| `near_conversation` | beszélgetés | `reject` ≥ 0,95, `review` ≥ 0,90 (deklarált változat: legfeljebb `review`) | összevont arány |
| `near_variant` | beszélgetés | `info` | 0,80–0,90: csak csoportosítás |
| `probable_paraphrase_variant` | beszélgetés | `review` | heurisztika (szó-átfedés ≥ 0,35) |
| `roles_swapped_messages`, `messages_reordered` | beszélgetés | `review` | azonos üzenetek másik szerepben; másik helyen (más sorrendben vagy eltolva, pl. beszúrt váltás után) |
| `sample_exact`, `sample_near` | minta / export | `reject` / `review` a fenti szabály szerint | min(q, a, c) |
| `sample_exact_trivial` | minta / export | `review` | rövid, pontosan ismétlődő minta |
| `same_qa_different_context`, `same_question_different_context`, `same_question_context_different_answer`, `shared_answer_different_question` | minta / export | `info` | **részleges szövegegyezés**, nem ismétlődő tanítási minta |
| `persona_reuse_exceeds_limit`, `declared_group_too_large`, `group_too_large` | csoport | `review` | terv 4.3; csoportméret |
| `declared_groups_merged` | csoport | `info` | a számított csoport a mérvadó |

Minden találat rögzíti: az érintett rekordot és fordulót (`turn`, fájl, sor), az egyezés típusát, a pontszámot és a módszert, a döntési státuszt és indokot, valamint (a rekordokhoz és a csoportokhoz) a csoportazonosítót. **Külön** szerepel a részleges szövegegyezés (`info`) és a valóban ismétlődő tanítási minta (`sample_exact`/`sample_near`).

**Egy közös köszönés, rövid válasz vagy azonos kérdés eltérő előzményben önmagában nem minősíti duplikáltnak a beszélgetést:** a beszélgetés-szintű arány az egész beszélgetésen számít; az azonos kérdés eltérő előzménnyel `info`, a triviális pontos első-forduló ismétlés mintaszinten `review`, a beszélgetés `conversation_decision` mezője viszont nem `blocked`.

## 6. Csoportosítás (MT-2 előkészítése)

**Élek** (a csoport a rekordok összefüggő halmaza): pontos vagy normalizálás utáni azonosság; összevont hasonlóság ≥ 0,80 (`near_conversation`/`near_variant`); `probable_paraphrase_variant`; szerepcsere/sorrendcsere; nem-triviális ismétlődő minta (`sample_overlap`, ≥ 0,90); azonos `persona`; azonos deklarált `split_group`. Nem él: az `info` részleges egyezés (azonos kérdés eltérő előzménnyel), a triviális köszönés, a TE-1 export találatai (más adatcsomag).

**Láncolt hasonlóság szabálya (egyszeres kötés, tranzitív lezárás):** ha A hasonlít B-re és B C-re, akkor A, B és C **egy csoport**, akkor is, ha A és C közvetlenül nem hasonlít. Indok: ha egy tag a tanító-, egy másik a teszthalmazba kerülne, a közvetítő tagon át a tartalom átszivárogna. A csoportosítás így konzervatív; a láncnak van ára: hosszú lánc nagy csoportot adhat. Védelem: `group_too_large` (`review`) 5 tag fölött, a leggyengébb élekkel; a felülvizsgáló dönt, mely élek nem valódi változat-kapcsolatok.

**Csoportazonosító:** `mtg_<a csoport lexikografikusan legkisebb rekordazonosítója>`. Ugyanarra a bemeneti halmazra mindig ugyanaz (a bemeneti sorrend és a fájlfelosztás nem számít); nagyobb azonosítójú tag csatlakozásakor nem változik; **kisebb azonosítójú tag csatlakozásakor változik** (ezért a felosztás előtt a végleges bemenetre kell futtatni, és az eredmény a bemeneti fájlok ellenőrzőösszegéhez kötött).

**Deklarált és számított csoport:** a rekordok `meta.split_group` mezője a szerzői szándék; az MT-2 felosztás a **számított** csoportot használja (a `groups.json`), amely a deklaráltak fölé is összevonhat (`declared_groups_merged`). Egy csoport minden tagja (és mintája) csak **egy** részbe kerülhet: a tanító-, validációs és tesztadatba együtt nem.

**Tervezett változat-arány:** a többtagú csoportokba tartozó rekordok aránya (`variant_share`); a terv szerinti 15% fölött a `variant_share_over_plan` jelzi (nem blokkol).

## 7. Kivételek (dokumentált eltérő képesség)

`--exceptions <json>`: lista, elemei `{"a": id, "b": id, "waive": ["<típus>", ...] | ["*"], "reason": "…≥ 15 karakter…", "reviewer": "…"}`. A megnevezett pár megnevezett típusú **blokkoló** találatait `accepted_with_exception` státuszra állítja (az eredeti státusz a `status_before_exception` mezőben marad; az indok a jelentésben). `"*"` a pár összes felmenthető találata. **Nem menthető fel:** `duplicate_id`, `exact_conversation`. Ismeretlen azonosító, nem létező találat, rövid indok, ismeretlen kulcs → hiba (elavult vagy téves kivétel nem maradhat észrevétlen). A kivétel a csoportosítást nem szünteti meg, és a fájl ellenőrzőösszege a jelentés része.

## 8. Reprodukálhatóság és a bemenet védelme

* A jelentés rögzíti a bemeneti fájlok (beszélgetés-fájlok, TE-1 export manifest/export/index, névtár, kivétel-fájl) ellenőrzőösszegét; a TE-1 export a `te2.load_te1_export` ellenőrzésével jön be (manifest, ellenőrzőösszegek, index).
* A bemenet a futás **közben** megváltozott → hiba (16-os kód, jelentés nélkül). A futás **után** megváltozott bemenetet a `--verify-report <jelentés>` mutatja (15-ös kód).
* Csak turns-validált rekord (MT-1, a megfelelő móddal) fogadható; egyébként 11-es kód és a hibás rekordok felsorolása.
* Az új futás-mappa soha nem ír felül semmit; nem lehet a bemeneti mappa alatt, sem `data/clean|raw|rejected|inbox` alatt.
* Kimenet: `dedupe_report.json` (konfiguráció, bemenetek, időmérés, számlálók, összegzés, találatok, csoportok, rekordállapotok, korlátok), `findings.tsv`, `groups.json`, `record_status.tsv`.

## 9. Gyorsítás — garantált, nem közelítő

A hossz- és karakter-multiset felső korlát **bizonyítottan pontos**: az egyező karakterek közös részsorozatot alkotnak, ezért `M ≤ min(|a|,|b|)` és `M ≤ Σ_c min(a_c, b_c)` (a két karakter-multiset metszete); a szűrő csak azt a párt hagyja ki, amelynek aránya biztosan a vizsgált küszöb alatt van (beszélgetés-szinten a súlyozott összeg felső korlátja, minta-szinten a `q`/`a` külön). Ritka karaktereket egy vödörbe vonva a korlát csak lazább lesz, nem érvénytelen. A minta-szintű kérdés-hossz ablak (`2·min/(a+b) ≥ küszöb`) ugyanezt az elvet követi. Az eredmény a teljes összehasonlítással (`--no-prefilter`) **azonos**; ezt a tesztek (szintetikus korpusz, a 0,90/0,95 határra tervezett párokkal, mindkét mód összevetése) és a szintetikus méréseink igazolják. A paraphrase-heurisztika nem szűrő: minden párra fut.

## 10. Mért futásidő (szintetikus terhelés, a valódi TE-1 exporttal)

Lásd `data/reports/mt3_report.md` és a `data/reports/audit_evidence/mt3_dedupe/` mappa: az 1000 beszélgetés méretű szintetikus terhelés (a valódi 4494 példás exporttal szemben) futásideje, a szűrők hatékonysága és a teljes összehasonlítással való egyezés.

## 11. Korlátok

* A hasonlóság karakter-alapú átfedés, nem jelentés-azonosság; az átfogalmazás nagyrészt észrevétlen marad (a heurisztika ideiglenesen kalibrált, valódi adaton újrakalibrálandó).
* A pozíció-őrző arány beszúrt/törölt váltás után alacsony lehet; a minta-szintű és az üzenet-átfedéses ellenőrzés ezt részben pótolja.
* Rövid szövegnél a küszöb nem értelmezhető (lásd 4. szakasz).
* A névsemlegesítés a névtárra épül; a névtárban nem szereplő név különbség.
* A csoportosítás egyszeres kötésű: lánc nagy csoportot adhat.
* A `meta.depends` annotáció helyességét az eszköz nem ellenőrzi.
* Az eszköz nem ítéli meg, hogy két tanítási minta **tartalmilag** tanít-e eltérő képességet: ezt a kézi felülvizsgálat (`review`) és a dokumentált kivétel dönti el.
* A `clear_of_duplicate_findings` nem elfogadás és nem training-ready.

## 12. Használat és kilépési kódok

```bash
python tools/multiturn_dedupe.py --mode dataset --conversations <f1.jsonl> [<f2.jsonl> ...] --out-dir <mappa> [--te1-export <TE-1 futás-mappa>] [--exceptions <json>]
python tools/multiturn_dedupe.py --verify-report <dedupe_report.json>
```

`0` lefutott, nincs blokkoló találat; `1` lefutott, van `reject`/`review`; `2` argumentumhiba; `10` bemeneti fájl hiba; `11` nem turns-validált rekord; `12` TE-1 export hiba; `13` kivétel-fájl hiba; `14` kimeneti útvonal hiba; `15` a bemenet megváltozott a jelentés óta; `16` a bemenet a futás közben megváltozott. A küszöbök (0,90/0,95) parancssorból **nem** módosíthatók.
