# Dataset roadmap - jövőbeli nagy csomagok (0501-tól)

**Ez a dokumentum kizárólag TERV - egyik itt felsorolt csomag generálása sem
történt meg, és ez a kör nem is indított el ilyet.** A terv a
`data/reports/dataset_audit_0151_0500.md` (4. pont) és a
`data/reports/dataset_pipeline_hardening_0151_0500.md` tanulságaira épül,
különös tekintettel arra, hogy a 0151-0500 korpuszban feltárt két fő
probléma (kereszt-batch duplikátum, AI/Nexora témakör túlismétlése) a
jövőbeli csomagoknál strukturálisan ne ismétlődhessen meg.

## 1. A 9 tervezett csomag

| # | Csomag | Db | Fájlnév-prefix | `category` mező | Megjegyzés |
|---|---|---|---|---|---|
| 1 | Egyszerű magyar kérdés-válasz | 1000 | `simple_qa_batch2_*` | `simple_qa` | Folytatás 0501-től; AI/Nexora arány ≤5% a csomagon belül (lásd 3. pont) |
| 2 | Magyarázós példa | 1000 | `explanation_*` | `explanation` | Fogalom-magyarázatok, "hogyan működik X" jellegű |
| 3 | "Írd lépésekben" példa | 500 | `stepwise_*` | `stepwise` (ÚJ kategória) | Számozott lépéslistát váró instrukciók |
| 4 | Összegzés példa | 500 | `summary_*` | `summary` | Hosszabb bemenet -> tömör kivonat |
| 5 | Hibás user szöveg -> javított szöveg | 500 | `typo_correction_batch2_*` | `typo_correction` | A meglévő `sample_pack_v1.jsonl` sémáját követve |
| 6 | Hosszabb, többfordulós beszélgetés | 300 | `multiturn_*` | `multiturn` (ÚJ kategória, séma-bővítést igényel) | Lásd 4. pont - séma-tervezés ELŐBB szükséges |
| 7 | "Nem tudom biztosan, nézzünk utána" példa | 300 | `uncertain_lookup_batch2_*` | `uncertain_lookup` | Épít a meglévő minta-csomagra; a `generic_template` szűrő már erre hangolva van |
| 8 | Webes forrásból készült összefoglaló | 300 | `web_summary_*` | `web_summary` (ÚJ kategória) | Forrás-attribúció kötelező (`source` mező) - lásd 4. pont |
| 9 | Saját projekt/MF-AI témájú tudásanyag | 500 | `project_knowledge_*` | `project_knowledge` (ÚJ kategória) | Ez lényegében az AI/Nexora témakör folytatása - KÜLÖN, korlátozott helyen kapjon teret (lásd 3. pont) |

**Összesen: 5200 tervezett sor** (a jelenlegi 342 fölé).

## 2. Miért ebben a sorrendben érdemes haladni

Javasolt prioritás - a kockázat/megvalósíthatóság alapján, NEM a listában
szereplő sorrend szerint:

1. **1-2-5-7. csomag először** (simple_qa, explanation, typo_correction,
   uncertain_lookup) - ezek a meglévő séma egyszerű bővítései, a pipeline
   ezekre már bizonyítottan (350+ sornyi tapasztalattal) jól működik.
2. **3-4. csomag** (stepwise, summary) - új `category` érték, de a JSONL
   séma (egy instruction+egy output) változatlan marad, csak a validátor
   `ALLOWED_DIFFICULTIES`-hez hasonló, `category`-specifikus tartalmi
   elvárásokat érdemes hozzáadni (pl. stepwise-nál számozott lista
   ellenőrzése) - kis bővítés.
3. **9. csomag** (saját projekt/MF-AI tudás) - CSAK a 3. pontban leírt
   arány-korlátozással, és csak miután a `dataset_topic_report.py`
   rutinszerűen fut minden importnál.
4. **6. és 8. csomag utoljára** (multiturn, web_summary) - ezek séma-
   bővítést és/vagy forrás-hitelesség kérdést vetnek fel, ezért csak azután
   induljanak, hogy ezeket a nyitott kérdéseket (4. pont) a felhasználó
   jóváhagyta.

## 3. Az AI/Nexora túlismétlés strukturális megelőzése

A 0151-0500 korpusz legnagyobb minőségi problémája az volt, hogy az `AI` tag
aránytalanul (12.9%) és tartalmilag ismétlődően (23/44 sor egy szűk, 9
alapfogalmú klaszter átfogalmazása) volt jelen, és ezt SEMMI nem akadályozta
meg importáláskor. A jövőbeli csomagoknál:

- **9. csomag (`project_knowledge`) kapja meg kizárólag** az AI/Nexora/saját
  projekt témát - a többi 8 csomagban (1-8) ez a témakör **explicit tiltott
  vagy erősen korlátozott** (pl. csomagonként max 2-3 sor, ha egyáltalán
  releváns az adott kategóriához).
- A 9. csomagon BELÜL is kötelező a `dataset_topic_report.py` futtatása
  minden 50-100 soros sub-batch után, 8%-os küszöbbel per-alfogalom (nem
  csak a `AI` tag szintjén, hanem pl. "modell tesztelés", "Nexora cél",
  "adatminőség" al-témánként is) - ez jelenleg KÉZI felügyeletet igényel,
  mert a `dataset_topic_report.py` csak tag-szinten, nem al-téma-szinten
  riaszt (lásd a hardening-riport 5. pontját, "tartalmi hasonlóságot is néző
  túlismétlés-detektor" javaslat - ha ez elkészül, ez a lépés automatizálható).

## 4. Nyitott kérdések, amiket jóvá kell hagyatni, MIELŐTT az adott csomag
   elindul

### 6. csomag (multiturn)
A jelenlegi JSONL séma (`id, category, instruction, input, output, tags,
difficulty, quality_notes, source`) EGY fordulót ír le. Egy többfordulós
beszélgetéshez vagy (a) egy `turns: [{"role": ..., "text": ...}, ...]` tömb
mező bevezetése szükséges a séma bővítéseként, vagy (b) minden fordulót
külön soron, egy közös `conversation_id` mezővel összekapcsolva. Mindkettő
érinti a `tools/dataset_validate.py` `REQUIRED_FIELDS`/`validate_row()`
logikáját - ÚJ, explicit jóváhagyást igénylő kódmódosítás, ami jelenleg NEM
történt meg.

### 8. csomag (web_summary)
Ha a forrás valós webes tartalom, két kérdés nyitott: (a) **szerzői jog** -
mennyi/milyen formában idézhető/összefoglalható egy külső forrás anélkül,
hogy másolásnak minősülne, (b) **forrás-hitelesség** - a `source` mezőnek
ellenőrizhető URL-t vagy hivatkozást kell tartalmaznia, ami jelenleg nincs
kikényszerítve a validátorban. Mindkettő a felhasználó explicit
döntését igényli, mielőtt bármilyen tartalom készülne.

### 9. csomag (project_knowledge)
Lásd 3. pont - a korlátozás MÓDJÁT (pontos kvóta, al-téma lista) a
felhasználónak kell jóváhagynia, mielőtt a csomag elindul, mert ez direkt
folytatása annak a témakörnek, amit a hardening-kör most éppen korlátozott.

## 5. Folyamat-ajánlás minden jövőbeli csomaghoz

Az audit és a hardening-kör konkrét, bizonyított tanulságai alapján:

1. **Minden import kösse be a `tools/dataset_cross_dedupe.py`-t** a TELJES,
   akkor aktuális `data/clean/` állomány ellen - ne csak "az eddigi
   batch-ek ellen", ahogy korábban ad hoc módon történt. Ez már bizonyítottan
   elérhető és működik (lásd hardening-riport 2.1 pont).
2. **Minden import UTÁN futtasd a `tools/dataset_topic_report.py`-t** 8%-os
   küszöbbel, és nézd át kézzel a riasztott tageket (lásd hardening-riport
   2.2 pont - a puszta arány önmagában nem elég, tartalmi átvizsgálás is
   kell).
3. **Kisebb sub-batch-ekben generálni** (50-100 soros egységek), hogy egy
   hibás köteg felfedezése ne 500-1000 sort érintsen egyszerre - ez már a
   0301-0450 batch-eknél is bevált gyakorlat volt.
4. **`topic_flags` mechanizmus alkalmazása** azonnal, importáláskor, ha egy
   csomagon belül tartalmi ismétlődés gyanúja merül fel - nem utólag, egy
   külön hardening-körben, ahogy most történt.
5. **A 6. és 8. csomagnál NE induljon generálás**, amíg a 4. pontban leírt
   séma-/forrás-kérdéseket a felhasználó explicit jóvá nem hagyja.

---

**FONTOS: ez a dokumentum kizárólag TERV. Egyik csomag generálása sem
történt meg, és ez a kör nem indított tanítást, nem módosított webapp/
backend kódot, és nem commitolt/pusholt semmit.**
