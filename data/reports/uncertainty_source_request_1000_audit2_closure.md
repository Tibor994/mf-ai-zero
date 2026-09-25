# 6. csomag — `uncertainty_source_request` — 2. audit-kör: a nyitott tételek célzott lezárása

Dátum: 2026-09-25. Előzmény: az első completion audit (`uncertainty_source_request_1000_completion_audit.md`, commit `72b0130`). Fix commit: `24094fd` (`v1.13.15-dataset-fix`). Bizonyítékok: `audit_evidence/uncertainty_source_request_1000/`.

Új adatcsomag és tanítás nem indult; a webapp/backend kód, a `tools/` és a validátorok/küszöbök változatlanok; a raw fájlok változatlanok.

## Végső státusz

**KORLÁTOZOTT LEZÁRÁS (audit 2).** Az adatbázis szerkezetileg és duplikáció szempontjából teljes; a nyitott audittételek nagy része lezárult, de **nem minden**: 6 sor felülvizsgálatig kizárt, 10 kontraszt-sor forrásellenőrzése nem történt meg, független emberi/szakértői átnézés nem volt. A „teljes lezárás” nem adható meg.

## 1. Kiinduló állapot (fájlokból ellenőrizve)

* `claude_uncertainty_source_request_*_clean.jsonl`: 10 fájl × 100 = **1000 sor**; teljes clean korpusz: **4500 sor** (49 fájl). HEAD = `72b0130` a munka elején.
* A sorok száma a munka végén is 1000 / 4500: **egyetlen sor sem került törlésre vagy hozzáadásra**, csak 33 sor szövege/jegyzete változott.

## 2. Feladatlista sorazonosítókkal és végállapot

| # | Tétel | Sorok / azonosítók | Végállapot |
|---|---|---|---|
| 1 | 125 kontraszt-sor soronkénti besorolása; „124 vs 125” | mind a 125 | **ZÁRVA** (`contrast_125_table.md`) |
| 2 | 24 „csak keresési összefoglaló” (Ö) sor eredeti forrásának elolvasása | 2.–6. és 9. batch Ö-sorai | **ZÁRVA** (a források megnyitva; a szövegmódosítások a 3. szakaszban) |
| 3 | 28 „korábbi riportra támaszkodó” (R) sor visszavezetése | 0602 … 0700, 0704 … 0799 (28 sor) | **ZÁRVA 27 sorra; NYITOTT: `0602`** (forrás nem nyitható meg) |
| 4 | 59 „forrást nem igénylő” sor indoklása | lásd a táblázat C/D/E osztályai | **ZÁRVA** indoklással; **10 sor (E) forrásellenőrzése nem történt meg → NYITOTT, alacsony kockázat** |
| 5 | A 0001–0700 batchek kulcsszavas, nem hard soraira kimaradt átnézés | 123 sor (`flagged_123_ids.json`) | **ZÁRVA** (mind a 123 sor teljes szöveggel elolvasva, 8 javítva, 115 megtartva); szakértői átnézés: `0220`, `0602` |
| 6 | `0506` | `0506` | **ZÁRVA** dokumentálva (lásd 4.) |
| 7 | 7 hasonlósági pár tartalmi értékelése | 7 pár, 8 egyedi sor | **ZÁRVA** (mind megtartva, indoklással) |
| 8 | Gyorsított ellenőrzés reprodukálhatósága | `dd_full.py` stb. | **ZÁRVA** (`README.md`, `data_version.txt`, `code/`) |
| 9 | Válaszsablonok: 49 „…és azt sem tudom, melyik…” és 29(30) „Hogyan ellenőrizzem…” | 49 + 30 sor | **ZÁRVA** (mind megtartva, nem üres/félrevezető/érdemben egységesítő) |
| 10 | Jogi számok (magyar) szakértői ellenőrzése | `0829`, `0849`, `0864`, `0220` | **NYITOTT** (kizárva a tanításból) |
| 11 | `0898` fékbetét-forrás | `0898` | **NYITOTT** (szám kikerült, kizárva) |
| 12 | 39 előtag nélküli kontraszt-sor újracímkézése | 2.–3. batch | **NYITOTT** (nem kért, külön jóváhagyás kell) |
| 13 | 14 ismétlődő `kind` címke | lásd 1. audit | **NYITOTT** (nem kért) |
| 14 | Nem kontraszt-módok hedge-elt, forrás nélküli számai | `0809`, `0840`, `0844`, `0876`, `0953`, `0974`, `0991` | **NYITOTT**, alacsony kockázat, nem blokkoló |
| 15 | Független emberi átolvasás | teljes csomag | **NYITOTT** (nem végezhető el általam) |
| 16 | A scratch szkriptek `tools/` alá emelése | – | **Nem történt meg** (kérésre); a szkriptek bizonyítékként a `audit_evidence/…/code/` alatt |

## 3. 125 kontraszt-sor forráslefedettsége

**A 124 vs 125 eltérés oka:** az első audit „13 K + 24 Ö + 28 R + 59 A/D = 124” összegzése kihagyta az 1 „közvetett” sort (`0453`, a batch 7 forrásán át); a helyes összeg 13+24+1+28+59 = 125. Ezen felül az első audit **hibásan** állította, hogy a batch 7 (0601–0700) kontraszt-sorai „R: a riportban dokumentáltak”, mert a batch 7 riport ezekhez forrást nem dokumentált, és a batch 8 riport táblája keresés-alapú volt (a `0726` sorban belső ellentmondással). Ezért a régi K/Ö/R besorolást **soronkénti, kizáró** besorolás váltotta fel; a részletes táblázat: `audit_evidence/…/contrast_125_table.md`.

| Osztály | Sorok |
|---|---|
| **P** – elsődleges/hivatalos/szakmai forrás megnyitva és elolvasva, a szöveg megfelel | 36 |
| **P\*** – forrás megnyitva, a szöveg ebben a körben a forráshoz igazítva | 18 |
| **N / N\*** – csak másodlagos (szerkesztőségi/vállalati) forrás nyitható meg (Serious Eats, Wine Spectator, CommScope, Sleep Foundation, Battery University, SLR Lounge) | 4 + 2 |
| **O** – forrás nem nyitható meg (`0602`) | 1 |
| **C** – számolás/naptári definíció, újraellenőrizve | 15 |
| **D** – definíció / logika / általános tanács, külső szám- vagy jogi állítás nélkül | 39 |
| **E** – köznapi empirikus állítás, forrás nem megnyitva | 10 |
| **Összesen** | **125** |

Megjegyzések:
* A 24 Ö sor: a keresési összefoglaló helyett az eredeti oldalt (CDC, AASM/Sleep Foundation, CISA, Cleveland Clinic, Whirlpool, AAOS, UBA, McGill OSS, Let's Encrypt, UMaine, Serious Eats, Chrome Súgó, PMC-cikkek, Cornell, Stanford Children's, Rutgers, UGA, Cochrane, Harvard Health stb.) megnyitottam és elolvastam (böngészőn át, illetve Europe PMC kivonat). A korábbi „keresési összefoglaló elegendő” feltevés több helyen **hibásnak** bizonyult, ezek a sorok módosultak (P\*): pl. `0801` („egy-két nap” → 8%/14%), `0830` (kekszmorzsa → gumicukor), `0819` (inzulin kikerült), `0841`, `0859`, `0835`, `0303`, `0425`, `0687`, `0732`, `0726` (a „felére-harmadára” szám nem szerepelt a forrásban), `0698`, `0419`, `0642`, `0669`, `0453`, `0707`, `0708`, `0364`, `0275`.
* A 28 R sor (batch 7–8): a `0602` kivételével mind közvetlen forrással ellenőrizve. **A `0602` (fűtéscsökkentés) elsődleges forrása nem nyitható meg** (a hivatalos energetikai oldal blokkolt), ezért a szöveg minőségi állításra szűkült, a sor NYITOTT és a tanításból kizárt.
* A korábbi „59 A/D sor” a soronkénti táblázatban **nem reprodukálható azonosító szerint**, felváltja az új C+D+E = 64 sor. Az eltérés oka: a batch 7–8 hat számolási sora korábban R-ként szerepelt (most C), és néhány korábbi A/D sor tényállítást tartalmazott, ezért P/P\* lett (pl. `0275`). Az új osztályok: **C** (15): a számolást újra elvégeztem (a megadott adatból, külső forrás nem kell); **D** (39): definíció, logikai megjegyzés vagy hétköznapi tanács, szám- vagy jogi állítás nélkül; **E** (10: `0169`, `0170`, `0195`, `0319`, `0347`, `0543`, `0568`, `0569`, `0845`, `0895`): tényállítás-jellegű köznapi mondat, nem számszerű és hedge-elt, de **forrásból nem ellenőriztem** — a „közismertnek tűnik” itt nem zárja a tételt, ezért nyitott marad (nem blokkoló). A C/D/E besorolás az én besorolásom, nem független ellenőrzés.

## 4. Kimaradt tartalmi átnézés (0001–0700, kulcsszavas nem hard sorok) és a `0506`

* **Azonosítás:** az első audit kulcsszavas (egészség/jog/pénz/biztonság) szűrője a 0001–0700 batchek nem hard soraira 123 azonosítót adott (`results/flagged_123_ids.json`, szöveggel: `flagged_123_rows_text.txt`). (A „körülbelül 120” tehát pontosan 123.)
* **Átnézés:** mind a 123 sort a kérdéssel, bemenettel és válasszal együtt újraolvastam; a számokat, határidőket és szabályokat forrásokhoz vetettem, kitérve az érvényességi körre.
* **Eredmény:** 115 sor változatlan; **8 sor módosult** (`0181` EFSA: 2,0/2,5 liter *teljes* vízbevitel; `0210` a reakciótermékek; `0220` vagyoni biztosíték; `0275`; `0303`; `0453`; `0602`; `0687`); szakértői átnézést igényel `0220` (jogi) és `0602` (forrás hiányos).
* **Nem független ellenőrzés:** ez az én átnézésem volt, **nem** független emberi vagy szakértői ellenőrzés.
* **`0506` (nyújtás edzés előtt):** azért maradt nyitva, mert az első audit csak „árnyalás” tételként jelölte (a „nem bizonyítottan véd” megfogalmazás lehet-e túl erős). A kérdéses állítást megnyitott forrás támogatja (PMC12034053 áttekintés; PMID 18785063: a statikus nyújtás edzés előtt nem csökkenti bizonyítottan a sérülés kockázatát; a dinamikus bemelegítés igen). **Szükséges javítás nincs** → lezárva dokumentációval, a szöveg változatlan. **Opcionális árnyalás** (nem alkalmazva): kimondhatná, hogy rövid statikus nyújtás nem káros.

## 5. A 7 hasonlósági pár (tartalmi értékelés)

Az összehasonlított tartalom: `instruction.strip() + " || " + input.strip()` (a tool szerint; az input mindegyiknél üres). Küszöb: `>= 0,9`. „Kimenet” = az `output` mezők hasonlósága.

| Pár (későbbi ↔ korábbi) | Csomag | Feladat-hasonlóság | Csak instrukció | Kimenet | Tanulási cél | Döntés |
|---|---|---|---|---|---|---|
| `simple_qa_0857` ↔ `0851` | `claude_simple_qa_0851_0950` | 0,9041 | 0,8923 | 0,2449 | bőr funkciói ↔ szív keringtető szerepe | **megtartva** |
| `simple_qa_0859` ↔ `0851` | ugyanaz | 0,9189 | 0,9091 | 0,2479 | vese szűrő/vízháztartás ↔ szív keringtető szerepe | **megtartva** |
| `simple_qa_0859` ↔ `0857` | ugyanaz | 0,9041 | 0,8923 | 0,0730 | vese ↔ bőr | **megtartva** |
| `simple_qa_0914` ↔ `0671` | `claude_simple_qa_0851_0950` ↔ `_0651_0750` | 0,9189 | 0,8966 | 0,1923 | harmat (meteorológia) ↔ kamat (közgazdaság) | **megtartva** |
| `simple_qa_1081` ↔ `0734` | `_1051_1159` ↔ `_0651_0750` | 0,9184 | 0,9111 | 0,2725 | elem ↔ vegyület (atom szintje) vs. keverék ↔ vegyület (szétválaszthatóság) | **megtartva** |
| `simple_qa_0489` ↔ `0915` | `deepseek_simple_qa_0451_0500` ↔ `claude_simple_qa_0851_0950` | 0,9213 | 0,9136 | 0,2047 | eső ↔ jégeső (halmazállapot) vs. dér ↔ jégeső (lecsapódás vs. felhőben képződő jég) | **megtartva** |
| `step_by_step_0229` ↔ `0227` | `claude_step_by_step_0201_0300` | 0,9000 (határeset) | 0,8947 | 0,0204 | kerékpár *felkészítése* túrára ↔ *tisztítása* túra után | **megtartva** |

Indoklás (közös): a magas feladat-hasonlóságot a **rövid, sablonos kérdésforma** okozza (`Mi a X szerepe a szervezetben?`, `Mi a különbség a X és a Y között?`, `Írd le lépésekben, hogyan …`) és a hozzáfűzött ` || ` elválasztó (18–82 karakteres szövegekben 3–4 karakter eltérés is ≥ 0,9-et ad); a **tartalom** nem ismétlődik: a kimenetek hasonlósága 0,02–0,27, a tanulási célok különbözők (más szerv, más jelenség, más folyamat). A `0851/0857/0859` egy szándékos anatómiai sorozat, három külön szerv. Az `1081↔0734` és `0489↔0915` párokban egy közös fogalom (vegyület, jégeső) szerepel, de más megkülönböztetés tanítására; a `0229↔0227` egy közös lépése (lánc kenése) mind a két folyamatban logikailag indokolt. Szinonimacsere-jellegű átírás nem történt. **Sorszám-változás: 0** (4500 → 4500, a raw változatlan). A teljes korpuszos futás a végső adatokon ugyanazt a 7 párot adja.

## 6. A gyorsított ellenőrzés reprodukálhatósága

* Megőrzött, **változatlan** kód: `audit_evidence/…/code/dd_full.py` (sha256 `58fe5adf…816aa`), `dd_verify.py`, `dd_crosscheck.py`, `audit_pkg.py`; futtatási parancsok, mezők, normalizálás, a `>=` összehasonlítás és az adatverzió: `README.md` és `data_version.txt` (fájlonkénti sha256, 4500 sor; szülő commit `72b0130`, a futás a `24094fd` tartalmán).
* **Az elő-szűrés nem hagyhat ki küszöböt elérő párt:** a `ratio = 2M/(la+lb)` és `M ≤ min(la,lb)`, valamint `M ≤ Σ min(Ca[c],Cb[c])` (az egyező karakterek közös részsorozatot alkotnak); az `autojunk` csak csökkenthet; a szűrők szigorúan `<` 0,9-cel zárnak ki, a találat `>=` 0,9 — a pontosan 0,9000-es pár (`0229↔0227`) nem szűrhető ki. Részletes levezetés a `README.md`-ben.
* **Külön, empirikus tesztek (nem az algoritmus-ekvivalencia érve):** az eredeti tool 1500 soron (2333 mp) ugyanazt a 6 első-találat párt adta; egy 71 soros mintán 0,9 és 0,8 küszöbön is azonos találathalmaz. A végleges futás: 4500/4500 „későbbi” sor lefedve, 20 245 500 mezőpár-összehasonlításból 2769 jutott a valódi `difflib` számításig; **7 feladat-találat, 0 kimenet-találat, 0 id-egyezés**.
* A `audit_pkg.py` <6 karakteres szűrője a végleges korpuszban nem lép életbe (legrövidebb feladat-szöveg 14, legrövidebb kimenet 30 karakter).

## 7. Válaszsablonok

* **49 sor „…és azt sem tudom, melyik…”** (a `és azt sem tudom` 4-gram az outputban): mind a 49 esetben a bemenetből valóban hiányzik a hivatkozási alap („a falumban”, „ez a bolt”, „a kedvenc appom”), tehát a mondat nem üres és nem félrevezető; a sorok további tartalma (források, visszakérdezés) különböző. 49 / 1000 = 4,9%. **Egyetlen sor sem változott** (természetes ismétlés, szó-kvóta nélkül).
* **„Hogyan ellenőrizzem…” nyitás:** 30 sor (29 `ellenorzesi_ut` + a `0460` gumiabroncs-nyomás, `altalanos_valasz_ellenorzessel`; az első audit 29-et számolt csak az `ellenorzesi_ut` módban). Mind más ellenőrzendő dolgot (számla, csomagértesítés, alapítvány, foglalás, hangszer…) és más ellenőrzési utat tartalmaz. **Nem változott.**

## 8. Ellenőrzés a végső adatokon

| Ellenőrzés | Eredmény |
|---|---|
| Módosított 8 fájl: `dataset_validate` | 100/100 érvényes, 0 elutasított, id-duplikátum 0 |
| Módosított 8 fájl: pontszám | 100,0/100 (100 sor) — **nem a tartalmi helyesség bizonyítéka** |
| Módosított 8 fájl: `dataset_dedupe` | 0 instruction-, 0 output-hasonlóság |
| Minden clean fájl (49): `dataset_validate` | 0 elutasított sor |
| `python -m unittest tests.test_v1_7_4_dataset_foundation` | minden teszt sikeres, STÁTUSZ: STABIL |
| Teljes korpusz N×N (`dd_full.py`, 4500/4500 sor) a végső adaton | 7 feladat-pár (lásd 5.), 0 kimenet, 0 id |
| `dataset_topic_report` | a négy csomagjelölő címke 22,2% `[FIGYELEM]` — a korábban dokumentált kivétel (eszköz, küszöb változatlan) |
| Sorszám | 1000 / 4500, változatlan |

## 9. Összesítés

* **Kész sorok:** 1000/1000 (uncertainty csomag), 4500 (teljes clean korpusz).
* **Ellenőrzött sorok és állítások:** 125 kontraszt-sor osztályozva (60 sor forrásmegnyitással: 54 P/P\*, 6 N/N\*; 15 számolás újraellenőrizve; 39 D; 10 E ellenőrzés nélkül; 1 O); 123 kulcsszavas sor elolvasva; 7 pár tartalmilag értékelve; 49+30 sablon-sor átnézve; a `0181`, `0816`, `0891`, `0898`, `0922`, `0929`, `0965`, `0210` nem kontraszt-sorok számai/állításai forráshoz igazítva. A megnyitott forrásoldalak pontos számát nem számoltam (nagyságrendileg 60); minden sor forrása a táblázatban név szerint szerepel.
* **Megtartott / javított / kizárt:** javítva 30 sor (szöveg + jegyzet, `row_changes_sources.json`); 3 további sor (`0829`, `0849`, `0864`) csak jegyzet-kiegészítést kapott; 4467 sor változatlanul megtartva (4500 − 33); **kizárva 6 sor**.
* **Nyitott szakértői/forrás-felülvizsgálatok:** jogi: `0220`, `0829`, `0849`, `0864`; forrás: `0602`, `0898`.
* **A tanításra elfogadott halmaz pontos köre:** a 4500 clean sorból **4494** sor (az uncertainty csomagból **994**); kizárási módszer: `audit_evidence/…/training_exclusion_pending_review.txt` id-listája (a sorok a fájlokban maradnak, a `quality_notes` jelzi a státuszt). A 4494 sor tartalmazza a fenti 10 E-sort és az 1. audit nyitott, nem blokkoló tételeit (12–15); ezek forrás-ellenőrzése vagy független átnézése hiányzik, ezért az elfogadás **automatikus ellenőrzésekre és az én tartalmi átnézésemre** épül, **nem** független emberi/szakértői ellenőrzésre.
