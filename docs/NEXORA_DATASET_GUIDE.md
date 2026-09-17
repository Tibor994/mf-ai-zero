# Nexora Zero - Dataset Foundation útmutató (v1.7.4)

Ez a dokumentum a `tools/dataset_*.py` eszközökkel épített tanítóadat-
előkészítő rendszert írja le. **Ez a rendszer önmagában NEM tanít
semmit** - kizárólag arra való, hogy külső forrásból (Gemini/ChatGPT/
Claude generálta, vagy kézzel írt) JSONL adatot **biztonságosan
betegyünk, ellenőrizzünk, tisztítsunk**, mielőtt bármi később, egy
KÜLÖN, explicit döntéssel ténylegesen tanításra kerülne.

---

## 1. Mire való ez a rendszer

A Nexora Zero (MF-AI-Zero) modellje eddig kézzel írt, kis mennyiségű
szöveg alapján lett tanítva. A cél egy **megbízható csatorna** kiépítése
ahhoz, hogy nagyobb, AI-asszisztensekkel (Gemini, ChatGPT, Claude)
generált JSONL adatcsomagokat is be lehessen vonni - de csak úgy, hogy
minden sor átmegy egy **szerkezeti és biztonsági ellenőrzésen**, mielőtt
bármi "élesnek" számítana.

A rendszer NEM dönt automatikusan arról, hogy egy adatcsomag jó-e
tanításra - csak **objektív jelzéseket** ad (validálás, duplikátum-
keresés, minőségpontszám), a végső döntés mindig emberi.

---

## 2. Hogyan kell egy Gemini/ChatGPT/Claude outputot bemásolni

1. Kérd meg a modellt, hogy **JSONL formátumban**, **soronként EGY JSON
   objektumban** adja a válaszokat, pontosan a 3. pontban leírt séma
   szerint.
2. Mentsd a nyers kimenetet egy `.jsonl` fájlba a `data/raw/` mappába,
   pl. `data/raw/gemini_batch1.jsonl`.
3. **Ne módosítsd kézzel a nyers fájlt** - ha valami hibás benne, azt a
   validátor úgyis jelezni fogja, és a `data/rejected/` mappában
   megkapod pontosan, hogy melyik sor mivel hibás.
4. Futtasd le rajta az import-folyamatot (lásd 4. pont).

---

## 3. Elvárt JSONL séma

Minden sor egy önálló, valid JSON objektum, pontosan ezekkel a
mezőkkel:

```json
{
  "id": "egyedi-string-azonosito",
  "category": "simple_qa",
  "instruction": "A feladat vagy kérdés szövege.",
  "input": "Opcionális kiegészítő szöveg (lehet üres string, DE a mezőnek léteznie kell).",
  "output": "Az elvárt, helyes válasz szövege.",
  "tags": ["cimke1", "cimke2"],
  "difficulty": "easy",
  "quality_notes": "Szabad szöveges megjegyzés (lehet üres string).",
  "source": "gemini"
}
```

**Kötelező mezők:** `id`, `category`, `instruction`, `input`, `output`,
`tags`, `difficulty`, `quality_notes`, `source` - MINDEGYIKNEK léteznie
kell, még ha `input`/`quality_notes` üres string is.

**`difficulty`** csak ez a három érték lehet: `easy`, `medium`, `hard`.

**`tags`** mindig lista (akár üres lista is lehet: `[]`).

**Gyakori hiba, amire figyelj:** ha a category vagy bármely mező nevében
aláhúzás van (pl. `simple_qa`), a generátor modell néha véletlenül
escape-eli: `simple\_qa`. Ez **érvénytelen JSON escape** - a validátor
ezt pontosan jelzi, de a legjobb, ha eleve figyelmezteted a generátor
modellt, hogy ne tegyen backslash-t aláhúzás elé.

---

## 4. Hogyan fut a validátor

```bash
python tools/dataset_validate.py data/raw/gemini_batch1.jsonl
```

Soronként ellenőriz:
- valid JSON-e a sor (és külön, pontosabb üzenetet ad, ha a hiba egy
  érvénytelen escape-szekvencia, pl. `simple\_qa`)
- minden kötelező mező megvan-e
- `id`/`category`/`instruction`/`output`/`source` nem üres
- `tags` lista
- `difficulty` csak easy/medium/hard
- nincs duplikált `id` a fájlon belül
- az `output` nem túl rövid (min. 3 szó) és nem túl hosszú (max. 1500
  karakter)
- nincs zagyva, ismétlődő karaktersorozat (pl. "aaaaa")
- nincs torz/értelmetlen szó (magánhangzó nélküli, 5+ betűs token)
- nincs nyilvánvaló angol keveredés (technikai szavak, pl. "python",
  "api", "html", kivételt kapnak)
- nincs feltűnő, személyes adatra utaló minta (email, telefonszám-szerű)
- nincs feltűnő, veszélyes tartalomra utaló minta (kulcs/jelszó-szerű)
- nincs túl magabiztos, valótlan Nexora-állítás (pl. "olyan okos vagyok,
  mint a ChatGPT")

**Korlátok, amiket érdemes tudni:** ezek mind determinisztikus,
szabályalapú (NEM szótár/ML-alapú) ellenőrzések - a "torz szó"
felismerés csak a legdurvább eseteket (magánhangzó nélküli token) kapja
el, egy valós szóhoz HASONLÓ, de téves szót (pl. "szavem" a "szívem"
helyett) nem lehet dictionary nélkül megbízhatóan elkapni. Az angol-
keveredés és a személyes adat/veszélyes tartalom felismerés is
konzervatív, kézzel karbantartott mintalistákra épül - nem helyettesíti
a kézi átnézést.

A hibás sorok **SOSEM törlődnek** - a validálás csak REPORTOL.

---

## 5. Hogyan fut a deduplikáló

```bash
python tools/dataset_dedupe.py data/clean/batch1.jsonl
```

Három szempont szerint keres duplikátumot:
1. **`id` alapján** - pontos egyezés.
2. **"feladat" (instruction+input) hasonlóság alapján** - `difflib`
   alapú szöveg-hasonlóság, alapértelmezett küszöb 0.9 (90%). FONTOS: az
   `instruction` ÖNMAGÁBAN szándékosan NEM elég - sok kategóriánál (pl.
   `typo_correction`, `summary`) ugyanaz az instruction-sablon
   ismétlődik, és csak az `input` hordozza a ténylegesen eltérő
   feladatot, ezért a hasonlóságot az `instruction`+`input` PÁRJÁRA
   számoljuk.
3. **`output` hasonlóság alapján** - ugyanaz a módszer az `output`
   mezőre.

A talált duplikátumokat **külön reportolja** (megtartandó sor / duplikátum
sor / hasonlósági érték) - nem dönt automatikusan, a `dedupe_rows()`
függvény ad egy JAVASOLT, duplikátum-mentes listát, de a forrásfájlt nem
módosítja.

---

## 6. Hogyan fut a minőségpontozó

```bash
python tools/dataset_score.py data/clean/batch1.jsonl
```

Minden sorra egy 0-100 közötti `quality_score`-t számol, 100-ból
levonva a talált problémákért (torz szó, ismétlődő karakter, túl rövid/
hosszú, angol keveredés, túlzó Nexora-állítás, hiányzó záró írásjel,
ismert sablonos "kitérő" válasz, gyanúsan alacsony instruction/output
szó-átfedés). A pontszám **NEM dönt automatikusan** semmiről - csak
segít rangsorolni/válogatni.

---

## 7. Hogyan készül a train/eval split

```bash
python tools/dataset_split.py data/clean/batch1.jsonl --train-ratio 0.9 --seed 42 \
    --train-out data/train/batch1.jsonl --eval-out data/eval/batch1.jsonl
```

- Alapértelmezés: 90% train / 10% eval.
- **Kategóriánként arányosan** oszt (minden `category` külön kerül
  megkeverésre és vágásra), hogy egy kis kategória se maradjon eval
  nélkül, és egy nagy kategória se dominálja el az eval részt.
- **Determinisztikus** - fix `seed` (alapértelmezés: 42) mellett mindig
  UGYANAZT a felosztást adja ugyanarra a bemenetre.

---

## 8. Teljes import-folyamat egy paranccsal

```bash
python tools/dataset_import.py data/raw/gemini_batch1.jsonl
```

Ez validál → deduplikál → pontoz, és kiírja:
- `data/clean/gemini_batch1.jsonl` - elfogadott, deduplikált,
  `quality_score`-ral kiegészített sorok
- `data/rejected/gemini_batch1.jsonl` - a validáláson elbukott NYERS
  sorok (a hívó fél, azaz TE, kézzel átnézheted)
- `data/rejected/gemini_batch1_report.json` - részletes report:
  sorszám, id, hiba oka, és hogy elvileg auto-javítható-e (pl. egy
  escape-hiba) vagy kézi ellenőrzést igényel
- `data/reports/gemini_batch1_summary.json` - összefoglaló számok

**A train/eval split NEM fut le automatikusan importáláskor** - ez egy
külön, tudatos lépés (lásd 7. pont), miután már átnézted a `clean/`
eredményt.

---

## 9. Minta-csomag

A `data/samples/sample_pack_v1.jsonl` egy kézzel írt, 16 soros,
**csak mintának/tesztadatnak szánt** csomag, 5 kategóriával
(`simple_qa`, `explanation`, `typo_correction`, `summary`,
`uncertain_lookup`). Ez **NEM valódi tanítóadat mennyiség** - kizárólag
arra való, hogy a validátor/dedupe/scorer/split eszközöket ellenőrizni
lehessen rajta (lásd `tests/test_v1_7_4_dataset_foundation.py`), és
mintaként szolgáljon ahhoz, milyen formátumú/minőségű sorokat várunk egy
külső generátortól.

---

## 10. Mikor szabad az adatot ténylegesen tanításra használni

**Soha automatikusan.** Mielőtt bármilyen `data/clean/` vagy
`data/train/` tartalom ténylegesen egy tanítási körbe kerülne:

1. Fusson le rajta a teljes lánc (validate → dedupe → score → split).
2. Egy ember (nem az AI) NÉZZE ÁT legalább a `data/rejected/` reportot
   és egy mintát a `data/clean/` eredményből.
3. Legyen egy **külön, explicit user-döntés** arról, hogy "ez a csomag
   mehet tanításra" - ez a projekt eddigi minden körének szabálya
   (lásd pl. a v1.7-es köröket: "ne kezdj v1.8-at", "ne taníts még
   modellt" stb. explicit korlátozások) is ezt az elvet követi.
4. A tanítás maga továbbra is egy KÜLÖN kör/szkript (`train.py`-szerű),
   amit ez a dataset-foundation rendszer NEM indít el és NEM is tud
   elindítani - a kettő szándékosan el van választva.
