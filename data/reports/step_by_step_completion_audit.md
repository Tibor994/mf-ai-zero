# step_by_step csomag - lezáró (completion) audit

Vizsgált csomag: **3. csomag - "Írd lépésekben" példa (`step_by_step`)**, cél: 500 db egyedi clean sor.
Vizsgált állapot: `main` @ `33c374d` (`v1.10.2-dataset-generation: complete step_by_step dataset 0401-0500`),
a working tree ezekre a fájlokra azonos a HEAD-del.

## Verdikt

**STABIL** - mind a 13 kért ellenőrzési pont teljesül. Az audit **1 kisebb, dokumentált tartalmi
megjegyzést** talált (0310, lásd 3. fejezet), amely egy soron a használhatóságot érinti, a formai,
duplikációs és biztonsági kritériumokat nem. Adatot ez az audit **nem módosított**.

## 1. A 13 ellenőrzési pont

| # | Ellenőrzés | Eredmény | Módszer / bizonyíték |
|---|---|---|---|
| 1 | Pontosan 500 clean step_by_step sor | **IGEN** (500) | 5 clean fájl x 100 sor; a teljes clean korpuszban `category == step_by_step`: 500 |
| 2 | ID 0001-0500 hiány nélkül | **IGEN** | `step_by_step_0001` ... `_0500`: 0 hiányzó, 0 extra; mind az 5 fájl a saját 100-as tartományát fedi |
| 3 | Nincs duplikált id | **IGEN** | 0 duplikált id a 500 között; 0 id-ütközés a másik 2000 clean sorral |
| 4 | Nincs duplikált instruction/output | **IGEN** (1 ismert hamis pozitív) | Lásd 2. fejezet |
| 5 | Schema mindenhol valid | **IGEN** | `dataset_validate.py` a 500 soros összefűzött fájlon: 500 érvényes / 0 elutasított; saját mezőellenőrzés: 9 kötelező mező, `tags[0] == "magyar"`, nem üres szövegek, `difficulty` érvényes érték: 0 hiba |
| 6 | `category` mindenhol step_by_step | **IGEN** | 500/500; `source` mindenhol `synthetic_claude`, `input` mindenhol üres string |
| 7 | Output mindenhol pontosan 5 számozott lépés | **IGEN** | 500/500 pontosan `1.`-`5.`, sorrendben, üres előtag nélkül, mind legalább 8 karakter hosszú, soron belül mind az 5 különböző, pontra/kérdőjelre/felkiáltójelre végződik, nincs sortörés |
| 8 | Magyar nyelv és használhatóság | **IGEN** (1 megjegyzés) | Lásd 3. fejezet |
| 9 | Safety/firewall tiszta | **IGEN** | Lásd 4. fejezet |
| 10 | Rejected fájlok dokumentáltak | **IGEN** | Lásd 5. fejezet |
| 11 | Reportok megvannak minden batchhez | **IGEN** | 5/5 batch report (`claude_step_by_step_XXXX_YYYY_report.md`), a ChatGPT-jelöltek értékelése a 0001-0400 reportok 0. szakaszában |
| 12 | `dataset_autopilot_progress.md` összhangban | **IGEN** | Lásd 6. fejezet |
| 13 | Commitok és remote sync | **IGEN** | Lásd 7. fejezet |

## 2. Duplikáció (4. pont) részletesen

| Vizsgálat | Eredmény |
|---|---|
| Egyező instruction / output (szó szerinti) a 500-on belül | 0 / 0 |
| Batchen belüli hasonlóság >= 0.9, **minden** találat (nem csak az első), instruction+input | **1 pár**: `0227` - `0229` (pontosan 0.90) |
| Ugyanez, output | **0** |
| Csomag vs. a másik 2000 clean sor (simple_qa + explanation), id / instruction / output >= 0.9 | 0 / 0 / 0 |
| `dataset_dedupe.py` az 500 soron | id 0, instruction 1 (ugyanaz a `0227`/`0229` pár), output 0 |
| Egyedi instruction / egyedi output | 500 / 500 |
| Különböző szöveg lépéspozíciónként (1..5. lépés) | **500 / 500 / 498 / 500 / 498** |

- **A `0227`/`0229` páros hamis pozitív, kézzel ellenőrizve**: "tisztítsd meg a kerékpárodat egy
  hosszabb túra után" vs. "készítsd fel a kerékpárodat egy hosszabb túrára". Az instruction csak a
  keret-mondat miatt éri el a 0.9-et, a két feladat és a két output tartalma eltérő (tisztítás vs.
  túra előtti ellenőrzés). Ez korábban is dokumentált, elfogadott eset.
- **A lépéspozíciónkénti számlálás (a ChatGPT-batcheknél 100/14/14/1/1 volt) jelzi, hogy a csomag nem
  sablonos**: az 1., 2. és 4. lépés mind az 500 soron egyedi, a 3. és 5. lépésnél 2-2 szó szerint
  azonos rövid, általános mondat ismétlődik különböző témájú sorok között (lásd 3. fejezet, C).
- **A teljes 2500 x 2500-as N×N kereszt-dedupe nem futott újra az auditban.** A csomagot érintő összes
  pár lefedett (500 x 500 belül és 500 x 2000 a többi csomaggal), a többi csomag egymás közötti
  ellenőrzését a saját batch- és completion audit-futásaik végezték el.

## 3. Nyelv és használhatóság (8. pont) - észrevételek

**Amit az audit ellenőrzött:**
- Automatikus heurisztikák mind az 500 soron: magyar ékezetes karakter jelenléte, angol
  szavak, helyőrző szöveg, kódolási hiba, egyenes idézőjel, dupla szóköz, hibás
  írásjel-szóköz, névelő-hiba (`a` + magánhangzó, `az` + mássalhangzó), szóismétlés. Egyetlen jelzés
  (`0463`: "Az nyer, aki elsőként megszabadul...") **helyes magyar** (mutató névmás), tehát hamis pozitív.
  Számjegy a szövegekben (lépéssorszámon kívül): 0 (a számok betűvel vannak írva).
- **Kézi átolvasás, teljes szöveggel**: 50 sor független mintája (minden 10. sor, mind az 5 batchből
  egyenletesen), 37 kulcsszó-találatos sor, 26 többrészes ("X és Y") instruction. Ez **nem** az összes
  500 sor újraolvasása; a batchek 20-20 soros mintavételét már a saját reportjaik dokumentálják.
- Instruction-forma: 250 db "Írd le lépésekben, ...", 250 db "Írd lépésekben, ..."; mind tartalmazza a
  "lépés" szót, mind ponttal végződik. Output hossz: min. 184, medián 288, max. 420 karakter.
- Difficulty: easy 315 (63%), medium 153 (31%), hard 32 (6%).

**Megállapítások (mind kisebb, egyik sem blokkoló):**

- **A) `step_by_step_0310` - tartalmi eltérés (megerősített, 1 sor).** Instruction: "készíts egyszerű
  **elsősegély- és szerszámdobozt** otthonra". Az output kizárólag szerszámdobozról szól (csavarhúzó,
  fogó, kalapács, tipli...), elsősegély-tartalom egyáltalán nincs benne. Nem veszélyes, de a kérés egyik
  fele megválaszolatlan. **Javasolt javítás** (külön, jóváhagyott lépésben): az instruction szűkítése
  "szerszámdobozra", vagy az output átírása úgy, hogy a lépések az elsősegély-részt is lefedjék
  (általános felsorolás, orvosi tanács nélkül). Az audit ezt **nem javította**: egy már commitolt clean
  fájl módosítása külön, jóváhagyandó adatmódosítás, és a megbízás csak az audit report commitolására szólt.
- **B) `quality_notes` ismétlődés (1 pár).** A `0092` és a `0368` `quality_notes` mezője azonos
  ("Szakmai bemutatkozás lépéseit írja le."), 499/500 egyedi. A két sor tartalma eltérő (szakmai
  eseményen bemutatkozás vs. rövid szakmai bemutatkozás-benyomás), az instruction/output hasonlóság
  jóval 0.9 alatt van, de a téma átfedő. Formai hiba nincs, a mező metaadat, nem tanítási szöveg.
- **C) Ismétlődő rövid lépésmondatok (4 eset, 2-2 sor).** 3. lépés: "Csomagolj vizet, ételt és megfelelő
  öltözéket." (`0030`, `0272`); "Kerüld a könnyen kitalálható, személyes adatokat tartalmazó jelszavakat."
  (`0171`, `0268`). 5. lépés: "Kövesd nyomon havonta a fogyasztásod alakulását." (`0088`, `0253`);
  "Ismételd meg a folyamatot rendszeres időközönként." (`0116`, `0211`). Mindegyik tartalmilag indokolt az
  adott témában, a sorok többi része eltérő.
- **D) Csomagon belüli tag-arány (megfigyelés).** A `dataset_topic_report.py` az 500 soron 8% fölött jelez:
  `kommunikáció` 10.8%, `tervezés` 10.0%, `háztartás` 9.0%. Ezek tág, folyamat-jellegű címkék (a
  csomagon belüli arány természetes egy how-to kategóriában), a teljes 2500 soros korpuszban 3% körüliek
  (a `0401-0500` batch záró topic reportja: legmagasabb tag `fizika` 4.5%). Nem tartalmi telítődés, de a
  következő csomagok tag-aránynézésénél érdemes tudni róla.
- **E) Formai hasonlóság, elfogadott.** Az `0295`/`0297` (családi reggeli/esti rutin) instruction
  hasonlósága 0.88, a küszöb alatt, tartalmilag két külön feladat.

## 4. Safety / firewall (9. pont)

| Vizsgálat | Eredmény |
|---|---|
| Identity bleed (`src/guard.py`) | **0** |
| Saját projekt / MF-AI / modell / cégnév említés (nexora, mf-ai, zero, lstm, pytorch, claude, chatgpt, openai, gpt...) | **0** - kitalált saját-projekt tény nincs |
| URL / e-mail / telefonszám-szerű minta | **0**; a validator személyesadat-ellenőrzése 500/500 átment |
| Kulcsszó-átvizsgálás (wifi, vpn, cookie, ajándék, bocsánat, jelszó, hitel, befektet, gyógyszer, orvos, ügyvéd, bíróság, fegyver, drog, vegyszer, méreg, alkohol, áram, gáz, tűz, sürgős, szerződés, adó stb.) | 37 találati sor, **mind teljes szöveggel elolvasva**: mind semleges, hétköznapi vagy biztonságpozitív használat |
| Veszélyes útmutatás (hálózati feszültség, vegyszerkeverés, fegyver, kár okozása) | **0** |
| Jogi / orvosi / pénzügyi ígéret vagy konkrét tanács | **0** - érzékeny témáknál (adózási iratok `0447`, szerződés `0048`, biztosítás `0433`/`0448`, alvászavar `0110`, stressz) az output általános, és szakemberhez irányít |
| Kizárt témák | `wifi`: 0 a clean-ben (a 2 érintett sort a `0101-0200` batch a clean előtt kicserélte, dokumentálva a rejected fájlban). `ajándék`: 1 mellékes említés (`0096`, vendégségbe vihető "kisebb ajándék" - illemtani lépés, nem ajándék-téma). `vpn`, `cookie`, `bocsánat`: 0 |

Kulcsszó-találatok részletesebb megjegyzései: `0307` ("vegyszer **nélkül**" - biztonságos
keretezés), `0320` (koccanás: vészvillogó, mentő hívása, baleseti bejelentő), `0372` (áramkimaradás:
gyertya helyett elemlámpa). A `tűz`/`kés`/`orvos` szótő-találatok hamis pozitívak (*tűzz ki*, *később*,
*orvoslás*).

## 5. Rejected fájlok (10. pont)

| Fájl | Sor | Ok / dokumentáció |
|---|---|---|
| `chatgpt_step_by_step_0001_0100_rejected.jsonl` | 100 | `schema_invalid_missing_fields` (+ `missing_fields`, `additional_issue`, `auto_fixable`) |
| `chatgpt_step_by_step_0101_0200_rejected.jsonl` | 100 | `schema_invalid_missing_fields_and_duplicate_content` (+ 3 `additional_issue`) |
| `chatgpt_step_by_step_0201_0300_rejected.jsonl` | 100 | `templated_low_diversity_content` (+ `detail`, dedupe-jelzés) |
| `chatgpt_step_by_step_0301_0400_rejected.jsonl` | 100 | `schema_invalid_personal_data_suspected_false_alarm` + `templated_low_diversity_content` (+ 3 sorban `excluded_topic_*`) |
| `claude_step_by_step_0101_0200_rejected.jsonl` | 2 | `excluded_topic_wifi` (`0174`, `0176`, a batchen belül pótolva) |
| `claude_step_by_step_0001_0100`, `0201_0300`, `0301_0400`, `0401_0500` | 0 | üres fájl (nem volt elutasított sor) |

Mind a 402 rejected sor tartalmazza az eredeti sort (`row`), a sorszámot, az `id`-t, a `reason` és az
`auto_fixable` mezőt (0 hiányos sor). Összesen **402 elutasított sor** dokumentálva (400 ChatGPT + 2 Claude), **0 ChatGPT-sor került
clean-be**; mind a 4 ChatGPT raw candidate fájl megmaradt forrásként a `data/inbox/chatgpt/` alatt.

Származás a 500 clean sorra: **500 / 500 Claude-generált** (`source: synthetic_claude`); a ChatGPT/Dispatch
raw producer 4 próbálkozásból 0 elfogadható sort adott. Ez a protokoll szerint szándékos: a Claude/Nextora
validátor egyetlen ChatGPT-sort sem engedett át ellenőrzés nélkül.

## 6. `dataset_autopilot_progress.md` összhangja (12. pont)

A fájl **lokális, nem commitolt** (szándékos, ahogy a `simple_qa_1000_completion_audit.md` is).
Összevetve a valós állapottal:
- Csomagtáblázat: simple_qa 1000, explanation 1000, step_by_step 500 = **2500 clean**, hiányzik **2400**
  (500+500+300+300+300+500). A tényleges clean korpusz kategóriánként: explanation 1000, simple_qa 1000,
  step_by_step 500 - **egyezik**.
- Az 5 step_by_step Claude-batch commit hash-e (`c3e21c4`, `2477737`, `d313580`, `b4d0b93`, `33c374d`) mind
  létezik a git-ben, és a commit tárgya a megfelelő batch-hez tartozik.
- Nincs elavult szöveg (`400 / 500`, `FOLYAMATBAN`, `(ez a kör)`); a "3. csomag KÉSZ, 500/500" szerepel.

## 7. Commitok és remote sync (13. pont)

| Batch | Commit | Érintett fájlok |
|---|---|---|
| 0001-0100 | `c3e21c4` | 7 (Claude raw/clean/rejected, ChatGPT raw/rejected, report, inbox README) |
| 0101-0200 | `2477737` | 6 |
| 0201-0300 | `d313580` | 6 |
| 0301-0400 | `b4d0b93` | 6 |
| 0401-0500 | `33c374d` | 4 (közvetlen Claude batch, nincs ChatGPT-fájl) |

- Minden commit csak a saját batch fájljait tartalmazza; mind a 28 step_by_step nevű fájl (5 raw, 5 clean,
  9 rejected, 5 report, 4 ChatGPT inbox) és az inbox `README.md` **git-követett**, és **byte-azonos a HEAD-del**.
- `HEAD == origin/main == 33c374d`, ahead/behind: **0 / 0**. Nem commitolt fájl: csak a két szándékosan
  lokális report (`dataset_autopilot_progress.md`, `simple_qa_1000_completion_audit.md`).
- Megfigyelés: a commit-tárgyakban a verziószámok átfednek az explanation csomaggal (`v1.9.8` és
  `v1.9.9` kétszer szerepel: explanation `1b95d07`/`cc97984` és step_by_step `c3e21c4`/`2477737`). Ez
  nem hiba (a felhasználó által megadott üzenetek), de a verziószám nem egyedi azonosító a történetben.

## 8. Regressziós teszt

`tests/test_v1_7_4_dataset_foundation.py`: minden teszt sikeres, **STÁTUSZ: STABIL**.

## 9. Amit ez az audit NEM tett

- Nem indított tanítást, nem módosított webapp/backend kódot, nem módosított és nem törölt clean/raw/rejected adatot.
- Nem futtatta újra a teljes 2500 x 2500-as kereszt-dedupe-ot (lásd 2. fejezet).
- Nem olvasta újra az összes 500 sort soronként: **101 különböző sort** olvasott teljes szöveggel (50
  mintasor + 37 kulcsszó-találat + 26 többrészes instruction, átfedések nélkül számolva), az egész
  csomagot automatikus ellenőrzésekkel.
- Nem javította a 0310-es sort (lásd 3. fejezet, A).
- Nem kezdte el a 4. csomagot.

## Végső összegzés

- **500 / 500 clean step_by_step**, id 0001-0500 hiánytalan, 0 duplikált id, 0 duplikált output, 1 ismert
  hamis pozitív instruction-pár (`0227`/`0229`).
- Schema 500/500, kategória 500/500, pontosan 5 számozott lépés 500/500, 0 biztonsági probléma.
- 402 elutasított sor dokumentálva, 5/5 batch report, progress-fájl a valós állapotot tükrözi.
- `HEAD == origin/main`, regressziós teszt sikeres.
- **1 nyitott, nem blokkoló tartalmi megjegyzés**: `step_by_step_0310` (hiányzó elsősegély-rész).

**STÁTUSZ: STABIL.**
