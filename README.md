# MF-AI-Zero

Egy saját, **nulláról tanított**, kicsi, karakter-alapú nyelvi modell magyar szövegen.
Nincs benne semmilyen külső AI API (OpenAI, Claude, Gemini stb.) és nincs
letöltött, előre betanított modell sem — mindent te tanítasz be a saját
gépeden, CPU-n is.

## Mi ez a projekt?

A MF-AI-Zero egy egyszerű **karakter-alapú LSTM nyelvi modell**. Ez azt
jelenti, hogy a modell nem szavakban, hanem egyes karakterekben gondolkodik:
megtanulja, hogy egy adott karaktersorozat után statisztikailag milyen
karakter szokott következni magyar szövegben. Ha elég szöveget adsz neki, és
elég ideig tanítod, egyre valósághűbb magyar szövegrészleteket tud generálni.

Ez a v0.1 verzió szándékosan **egyszerű és kicsi**:
- könnyen átlátható a kód (nincsenek bonyolult trükkök),
- gyorsan fut CPU-n is,
- jól mutatja, hogyan épül fel egy nyelvi modell az alapoktól.

Nem versenyez ChatGPT-vel vagy hasonló nagy modellekkel — ez egy **tanulási
és kísérletezési célú, saját mini-AI**.

## Projektstruktúra

```
MF-AI-Zero/
├── README.md
├── requirements.txt
├── render.yaml              # Render "Blueprint" - lásd "Deploy Renderre" szakasz
├── Dockerfile                # Hugging Face Spaces / Docker deployhoz
├── .dockerignore
├── data/
│   ├── train.txt            # önálló mondatok (v0.1-v0.4 modellekhez)
│   ├── chat_train.txt        # User:/AI: kérdés-válasz párok (v0.7 chat-modellhez)
│   ├── chat_train_v07c.txt    # a fentihez fűzött, 3x súlyozott instrukciós kísérlet (v0.7c)
│   └── chat_train_v07d.txt    # ugyanaz, de 1x súlyozással (v0.7d)
├── models/
│   ├── mf_ai_zero_best.pt   # a jelenlegi legjobb "sima" (nem chat) modell
│   ├── mf_ai_zero_chat_v0_7.pt   # általános chat modell (a router ezt hívja general_chat/greeting/goodbye/command esetén)
│   ├── mf_ai_zero_chat_v0_7c.pt  # mondatszám-kérésekre specializált modell (a router ezt hívja sentence_request esetén)
│   └── mf_ai_zero_chat_v0_7d.pt  # kísérleti modell - lásd "v0.7d kísérlet" szakasz (NEM használja a router)
├── conversations/           # a chat.py / web/app.py itt menti a beszélgetéseket (.txt)
├── learning_log/            # v0.8: feedback.jsonl - kiértékelt válaszok naplója
├── tests/
│   ├── golden_chat_tests.json    # 50 rögzített regressziós teszteset (v0.7e)
│   ├── test_v07e_router.py        # futtatható router-teszt, STABIL/NEM STABIL státusszal
│   └── test_v08_learning_log.py    # futtatható teszt az evaluator.py / learning_log.py-hoz
├── src/
│   ├── config.py            # beállítások (modell méret, tanítási paraméterek)
│   ├── model.py              # a modell architektúrája (CharLSTM)
│   ├── train.py               # tanító szkript (önálló mondatokhoz)
│   ├── train_chat.py           # tanító szkript (User:/AI: kérdés-válasz párokhoz)
│   ├── generate.py            # szöveggeneráló szkript
│   ├── chat.py                # terminálos beszélgetős (chat) mód
│   ├── router.py               # v0.7e: intent-felismerés + modell-útválasztás
│   ├── evaluator.py             # v0.8: szabályalapú válaszértékelés
│   └── learning_log.py           # v0.8: feedback.jsonl naplózás
└── web/                     # v0.6: helyi webes chat felület
    ├── app.py                # Flask backend
    ├── templates/
    │   └── index.html         # az oldal HTML váza
    └── static/
        ├── style.css           # sötét, "Mental Fuerza" hangulatú kinézet
        └── script.js            # chat logika a böngészőben
```

## Telepítés

Szükséged lesz Python 3.9+ verzióra. Ajánlott egy virtuális környezet
használata, de nem kötelező.

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Ez telepíti a PyTorch-ot, ami a modell tanításához és futtatásához kell.
(CPU-n is működik, nincs szükség videokártyára.)

## Tanítás

A modell a `data/train.txt` fájlban lévő magyar mondatokból tanul. A fájl
már tartalmaz néhány tucat próbamondatot, hogy azonnal kipróbálható legyen a
projekt — de bátran bővítsd sok más magyar szöveggel is, minél többel, annál
jobb eredményt kapsz.

Tanítás indítása:

```bash
python src/train.py
```

A szkript:
1. beolvassa és karakterekre bontja a szöveget, majd a mondatokat
   train (90%) és validation (10%) részre osztja (lásd `config.val_split`),
2. felépíti a karakter-szótárat,
3. végigmegy a beállított epoch-számon (lásd `src/config.py`), és minden
   epoch után kiírja mind a train, mind a validation loss-t — a validation
   loss azt mutatja, hogy a modell mennyire boldogul olyan mondatokkal,
   amelyeket tanítás közben nem látott,
4. mindig elmenti a modellt ide: `models/mf_ai_zero_best.pt` (ez a
   "jelenlegi legjobb modell" fájlneve, ezt tölti be alapból a
   `generate.py` is), amikor a validation loss javul — így a végén nem
   feltétlenül az utolsó epoch, hanem a legjobban általánosító állapot
   marad meg (ez védekezés a túltanulás, azaz overfitting ellen).

A `--model-path` és `--epochs` kapcsolókkal külön névre is tudsz tanítani
(pl. kísérletezéshez, anélkül hogy a jelenlegi legjobb modellt felülírnád),
a `--patience` kapcsolóval pedig early stoppingot kapcsolhatsz be:

```bash
python src/train.py --epochs 200 --patience 15 --model-path models/mf_ai_zero_kiserlet.pt
```

## Szöveggenerálás

Miután lefutott a tanítás, kipróbálhatod a modellt egy kezdő mondattal:

```bash
python src/generate.py --prompt "Az erő bennem"
```

Opcionális paraméterek:

```bash
python src/generate.py --prompt "Az erő bennem" --length 300 --temperature 0.7
```

- `--length`: hány karaktert generáljon a prompt után (alapértelmezett: 200)
- `--temperature`: mennyire legyen "kreatív" a modell. Alacsonyabb érték
  (pl. 0.5) óvatosabb, kiszámíthatóbb szöveget ad; magasabb érték (pl. 1.2)
  változatosabb, de kockázatosabb (esetleg értelmetlenebb) szöveget.
- `--seed`: ha megadod (pl. `--seed 42`), a generálás determinisztikussá
  válik — ugyanaz a seed, prompt és a többi paraméter mindig ugyanazt a
  szöveget adja vissza. Seed nélkül minden futás más eredményt ad.
- `--sentences`: ha megadod (pl. `--sentences 3`), a generálás leáll,
  amint ennyi teljes mondatot (`.`, `!` vagy `?` után) legenerált, még
  a `--length` határ elérése előtt.
- `--model-path`: melyik mentett modellfájlt töltse be (alapértelmezés:
  `models/mf_ai_zero_best.pt`).

Minden generálás végén megjelenik egy sor is, ami megmutatja, hogy a
generált mondatok hány százaléka egyezik szó szerint a `data/train.txt`
valamelyik sorával — ez egy egyszerű mérőszám arra, hogy a modell mennyire
"magol be" szó szerint, ahelyett hogy valódi új mondatokat alkotna.

## Beszélgetős (chat) mód - terminál (v0.5)

A v0.5-től kezdve a betanított modell köré egy egyszerű, terminálos
beszélgetős felület is tartozik. Indítása:

```bash
python src/chat.py
```

A v0.7-től kezdve alapból a chat-formátumra tanított modellt
(`models/mf_ai_zero_chat_v0_7.pt`, lásd lentebb) tölti be, és egy
`User: ` promptot mutat, ahova beírhatod az üzenetedet — ez a modell
ténylegesen megpróbál válaszolni a kérdésedre, 3-6 mondatos válasszal.

Opcionálisan megadható a kezdő temperature és egy másik modellfájl is -
például, ha összehasonlításként ki akarod próbálni egy korábbi (v0.1-v0.4),
nem chat-formátumra tanított modellt:

```bash
python src/chat.py --temperature 0.6 --model-path models/mf_ai_zero_v0_4.pt
```

Parancsok a beszélgetés közben:

| Parancs | Hatás |
|---|---|
| `/exit` | kilépés a chatből (a beszélgetés mentve marad) |
| `/reset` | a beszélgetés-memória törlése |
| `/temp 0.6` | a temperature (kreativitás) átállítása menet közben |
| `/help` | a parancsok kiírása |

A program megjegyzi az utolsó 5 user/AI váltást (ez a "memória"), és a
beszélgetés végén (`/exit` vagy Ctrl+C) automatikusan elmenti egy
időbélyeges `.txt` fájlba a `conversations/` mappában, `User: ...` /
`AI: ...` formátumban.

**Fontos korlát**: ez továbbra is egy kicsi, karakter-alapú LSTM, nem egy
igazi chatbot. A v0.7 chat-modell a jól lefedett kérdéstípusokra (pl.
bemutatkozás, célok) megbízhatóan jó választ ad, de nem tökéletesen
konzisztens, és néhány kérésformát (pl. "Írj N mondatot X-ről") még nem
kezel jól — részletek a "Chat-formátumra tanítás (v0.7)" szakaszban. Ez
egy működő prototípus, ne várj tőle ChatGPT-szintű társalgást — a
beszélgetés-memória is inkább a naplózást és a `/reset`-et szolgálja, nem
azt, hogy a modell ténylegesen
"emlékezne" a korábbi mondatokra.

## Beszélgetős (chat) mód - böngészőben (v0.6)

A v0.6 ugyanazt a válaszgenerálási logikát egy kényelmesebb, böngészős
felület mögé teszi. Nem tanít és nem módosít semmilyen modellt — csak egy
webes felületet ad a meglévő modell köré. A v0.7-től alapból a
chat-formátumra tanított modellt (`models/mf_ai_zero_chat_v0_7.pt`) tölti be.

Telepítés után (a `requirements.txt` már tartalmazza a Flask-et is)
indítsd el a szervert:

```bash
python web/app.py
```

Ha egy másik modellt szeretnél kipróbálni (pl. összehasonlításként a
korábbi v0.4-et), vagy más porton indítanád:

```bash
python web/app.py --model-path models/mf_ai_zero_v0_4.pt --port 8000
```

A konzol kiírja, amikor a modell betöltődött, majd nyisd meg a böngészőben:

```
http://localhost:8000
```

A felület:
- sötét, "Mental Fuerza" hangulatú kinézet (fekete alap, arany/kék kiemelés),
- a beszélgetés buborékokban jelenik meg — a te üzeneteid jobbra (kék), az
  AI válaszai balra (arany szegélyű, sötét) buborékban,
- alul szövegmező és **Küldés** gomb — Enterrel is elküldhető az üzenet,
- **Temperature** választó (0.5 / 0.6 / 0.7) és **Mondatok** választó
  (3 / 4 / 5 / 6), amivel közvetlenül szabályozható a válasz kreativitása
  és hossza,
- **Törlés** gomb, ami kiüríti a beszélgetést a felületen.

A háttérben egy Flask szerver fut (`web/app.py`), ami induláskor egyszer
tölti be a modellt, és egy `/api/chat` végponton keresztül szolgálja ki a
böngésző kéréseit (a felhasználó üzenetét, a választott temperature-t és
mondatszámot JSON-ként kapja, és JSON-ben adja vissza a választ). Minden
webes beszélgetés is automatikusan mentődik egy `web_conversation_*.txt`
fájlba a `conversations/` mappában, ugyanabban a `User: ...` / `AI: ...`
formátumban, mint a terminálos chat.

Ugyanaz a **fontos korlát** érvényes, mint a terminálos módnál: ez egy
kicsi, karakter-alapú modell - ne várj tőle ChatGPT-szintű társalgást.

## Chat-formátumra tanítás (v0.7)

A v0.1-v0.4 modellek (a `data/train.txt`-en tanítva) önálló, motivációs
mondatokat írtak — kérdésre nem tudtak érdemben válaszolni, mert sosem
láttak kérdés-válasz párokat. A v0.7 ezt oldja meg egy új tanító adattal
és egy új tanító szkripttel:

- **`data/chat_train.txt`**: több száz kézzel írt magyar kérdés-válasz pár
  (`User: <kérdés>` / `AI: <válasz>` formátumban, üres sorral elválasztva),
  kiegészítve témasablonokból generált további párokkal. A témák: bemutatkozás,
  célok, tanulás, saját AI-fejlődés, erő és kitartás, hétköznapi beszélgetés,
  rövid és hosszabb (3-6 mondatos) válaszok, félreértések kezelése, és
  "nem tudom még, de tanulom" jellegű őszinte válaszok.
- **`src/train_chat.py`**: ugyanazt a modellarchitektúrát tanítja, mint a
  `train.py`, csak ezen az adaton, és a checkpointba elmenti, hogy ez egy
  `"chat"` formátumú modell — ez alapján tudja a `chat.py` / `web/app.py`,
  hogy a promptot `"User: <üzenet>\nAI:"` alakra kell csomagolnia, hogy a
  modell tényleg a kérdésre válaszoljon, ne csak egy önálló mondatot írjon.

Tanítás indítása (nem írja felül a régi modelleket):

```bash
python src/train_chat.py --epochs 200 --patience 15
```

Az eredmény: `models/mf_ai_zero_chat_v0_7.pt` — ez lett a `chat.py` és a
`web/app.py` új alapértelmezett modellje. A korábbi (v0.1-v0.4) modellek
összehasonlításként bármikor betölthetők a `--model-path` kapcsolóval.

**Korlát, amit érdemes tudni**: a chat-modell a leggyakoribb, jól
lefedett kérdéstípusokra (bemutatkozás, célok, önreflexió) megbízhatóan jó
választ ad, de nem 100%-osan konzisztens — ugyanarra a kérdésre más-más
véletlen indítás mellett néha eltérő minőségű választ ad, és bizonyos
kérésformákat (pl. "Írj N mondatot X-ről") még nem kezel megbízhatóan.
Ez egy kicsi, karakter-alapú modell korlátja, nem hiba.

## Mondatszám-felismerés (v0.7b)

A v0.7 modell magától nem vette mindig figyelembe, ha a kérdésben konkrét
mondatszám szerepelt (pl. "Írj 5 mondatot az erőről."). A v0.7b **nem
tanított új modellt** - ehelyett a `src/chat.py`-ban (amit a `web/app.py`
is használ) egyszerű, kód szintű felismerést épített be:

- Ha az üzenetedben ilyesmi szerepel: `"írj 5 mondatot"`, `"4 mondatban"`,
  `"mondj 6 mondatot"` (szám számjeggyel vagy kiírva, "mondat" szó előtt),
  a program automatikusan ennyire állítja a generálandó mondatok számát -
  felülírva a felületen kiválasztott értéket is.
- Ha nincs ilyen kérés a szövegben, minden marad a régiben: a webes
  felület legördülője, vagy a terminálos chat véletlen 3-6 közötti
  választása dönt.
- A felismerés csak *olvassa* az üzenetet, nem módosítja azt, így a téma
  (pl. "az erőről", "a fejlődésről") mindig megmarad a modellnek küldött
  promptban.
- Mivel a modell (mérete miatt) néha idő előtt "befejezettnek" érzi a
  választ egy hosszabb, N-mondatos kérésnél, konkrét mondatszám-kérés
  esetén a program több (max. 8) generálási próbálkozásból választja a
  legtöbb tényleges mondatot tartalmazó változatot - ez segít, de a kis
  modell miatt nem garantálja, hogy mindig pontosan N mondat készül.

## v0.7c kísérlet: instrukciós adat bővítése — STÁTUSZ: NEM STABIL

A v0.7b után is bizonytalan maradt az "Írj N mondatot X-ről" típusú
kérések kezelése, ezért készült egy célzott kísérlet: **348 új, kézzel
írt kérdés-válasz pár** (`data/chat_train_v07c.txt`), ahol minden válasz
garantáltan *pontosan* annyi mondatból áll, amennyit a kérdés kért -
ezt kódban ellenőriztük generálás közben. A témák: erő, fejlődés, célok,
tanulás, kitartás, saját AI, memória, tudásbázis, webkutatás, programozás,
bemutatkozás és hétköznapi beszélgetés. Ezt a v0.7 adatához fűzve (3x
súlyozva) egy külön modellt tanítottunk: **`models/mf_ai_zero_chat_v0_7c.pt`**
(a v0.7 modell és adatai nem változtak).

**Eredmény, 20 tesztkérdésen:**
- ✅ **Mondatszám-pontosság: 20/20** - minden kért N-mondatos válasz
  pontosan N mondatból állt. Ez a v0.7-hez képest drámai javulás.
- ⚠️ De két új probléma jelentkezett:
  1. **Téma-tévesztés**: az N-mondatos válaszok kb. felében a modell más
     témájú mondatokat kevert bele (pl. "Írj 4 mondatot a memóriáról"
     kérdésre kitartással kapcsolatos mondatokat adott).
  2. **Általános beszélgetési minőség visszaesett**: az instrukciós
     példák nagy aránya (a végleges adat ~47%-a) miatt a modell az
     egyszerű, nem-instrukciós kérdésekre is rosszabbul válaszol, mint a
     v0.7. Például "Mi a célod?" és "Hogyan leszel okosabb?" - amikre a
     v0.7 korábban pontosan válaszolt - a v0.7c-nél irreleváns vagy rossz
     témájú választ kaptak.

**Emiatt a v0.7c NEM lett az alapértelmezett modell** - a `chat.py` és a
`web/app.py` továbbra is a `models/mf_ai_zero_chat_v0_7.pt`-ot (v0.7)
tölti be alapból, mert összességében megbízhatóbb. A v0.7c
kísérletképpen, összehasonlításra bármikor kipróbálható:

```bash
python src/chat.py --model-path models/mf_ai_zero_chat_v0_7c.pt
python web/app.py --model-path models/mf_ai_zero_chat_v0_7c.pt
```

**Tanulság**: a v0.7c felvetette, hogy talán elég lenne kisebb súllyal
bevonni az instrukciós példákat - ezt a v0.7d kísérlet tesztelte (lásd
lent), és megcáfolta ezt a feltételezést.

## v0.7d kísérlet: mérsékeltebb súlyozás — STÁTUSZ: NEM STABIL

A v0.7c után felmerült, hogy a probléma oka az instrukciós példák túl
nagy aránya (3x súlyozással ~47%) lehetett. A v0.7d ugyanazt a 348
instrukciós példát **súlyozás nélkül (1x)** fűzte a v0.7 adatához, így
azok a végső adatnak csak ~22,6%-át tették ki. Ez egy külön modellt
eredményezett: **`models/mf_ai_zero_chat_v0_7d.pt`** (a v0.7 és v0.7c
modellek és adatai nem változtak).

**Side-by-side teszt eredménye** (20 általános + 20 "Írj N mondatot"
kérdés, kulcsszó-alapú automatikus kiértékeléssel):

| Modell | Általános kérdések | Instrukciós (pontos mondatszám) |
|---|---|---|
| **v0.7** | **15/20** | 4/20 |
| v0.7c | 5/20 | **20/20** |
| v0.7d | 6/20 | 19/20 |

**Következtetés**: a súly csökkentése (3x → 1x) gyakorlatilag nem javított
az általános beszélgetés minőségén (5/20 → 6/20, a v0.7 15/20-hoz képest
továbbra is súlyos regresszió), miközben az instrukció-követés majdnem
ugyanolyan jó maradt (19/20). Ez azt mutatja, hogy **a probléma nem
elsősorban az instrukciós példák arányából fakad**, hanem valószínűleg
abból, hogy az új témák (különösen a "saját AI" és "bemutatkozás"
instrukciós bankjai) tartalmilag túl közel esnek a v0.7 már jól működő,
egymondatos bemutatkozás/cél-válaszaihoz, és a modell a kettő között
"összezavarodik" (pl. a "Viszlát!"-ra a v0.7d egyszer egy kitalált
instrukciós kérdést, "Mesélj a tudás kapcsán egy gondolatot!"-et
generált válaszként).

**Emiatt a v0.7d SEM lett az alapértelmezett modell** - a `chat.py` és a
`web/app.py` továbbra is a `models/mf_ai_zero_chat_v0_7.pt`-ot (v0.7)
tölti be. A v0.7c-hez hasonlóan a v0.7d is kísérletként bármikor
kipróbálható:

```bash
python src/chat.py --model-path models/mf_ai_zero_chat_v0_7d.pt
python web/app.py --model-path models/mf_ai_zero_chat_v0_7d.pt
```

**Tanulság**: sem a v0.7c, sem a v0.7d nem oldotta meg a problémát ÚGY,
hogy egyetlen modellbe próbálta belegyömöszölni mindkét képességet
(általános chat + pontos mondatszám). Ez vezetett a v0.7e-hez.

## v0.7e: intent router — STÁTUSZ: STABIL ✅ (ÉLES, ez az alapértelmezett)

A v0.7e **nem tanított új modellt**. Ehelyett felismerte, hogy a
probléma strukturális: egy kis karakter-alapú modell nem tud egyszerre
jó lenni kétféle, eltérő stílusú feladatban. A megoldás egy egyszerű,
szabályalapú **router**, ami minden üzenetnél eldönti, melyik *meglévő*
modell válaszoljon:

- **`src/router.py`** — `detect_intent(text)` öt kategóriába sorolja az
  üzenetet: `command`, `sentence_request`, `goodbye`, `greeting`,
  `general_chat`. Csak `sentence_request` esetén válaszol a **v0.7c**
  modell (explicit mondatszám-kéréseknél, pl. "Írj 5 mondatot...") —
  minden más esetben (általános kérdés, köszönés, búcsú, parancs)
  mindig a **v0.7** modell válaszol, változatlanul.
- **Determinisztikus utófeldolgozás** (`enforce_sentence_count()`):
  mondatszám-kérésnél a `respond()` már eddig is 8x próbálkozott a
  pontos N mondat eltalálására (lásd v0.7b) - ha ez a 8 próbálkozás sem
  hozott pontos találatot, a router már NEM generál újra, hanem
  determinisztikusan vágja (ha túl sok mondat lett) vagy a meglévő
  mondatokat ismételve egészíti ki (ha túl kevés lett) pontosan N-re.
  Ez garantálja, hogy a végeredmény MINDIG pontosan N mondatból áll.
- **`tests/golden_chat_tests.json`** — 50 rögzített teszteset (20
  általános, 20 mondatszám-kérés, 10 parancs/köszönés/búcsú), amik
  mostantól a projekt "golden" regressziós tesztkészlete: minden
  jövőbeli modell- vagy router-változtatásnak ezen kell megfelelnie.
- **`tests/test_v07e_router.py`** — futtatható teszt, ami a fenti
  készleten méri az intent-felismerés pontosságát, az általános chat és
  a mondatszám-pontosság sikerarányát, és STABIL/NEM STABIL státuszt ad.

Futtatás:

```bash
python tests/test_v07e_router.py
```

**Mért eredmény** (2026-09-15):

| Metrika | Eredmény | Elvárt | Állapot |
|---|---|---|---|
| Intent-felismerés pontossága | 50/50 (100%) | ≥ 95% | ✅ |
| Általános chat sikerarány | 15/20 | ≥ 15/20 | ✅ |
| Mondatszám pontosság | 20/20 | ≥ 19/20 | ✅ |
| Parancs/köszönés/búcsú | 10/10 | ≥ 9/10 | ✅ |
| v0.7c válaszolt-e általános kérdésre | 0 eset | 0 | ✅ |

Mind az öt feltétel teljesült, **nincs regresszió** a v0.7 önmagában
mért 15/20-as általános teljesítményéhez képest, és a mondatszám-
pontosság a korábbi ~0-4/20-ról 20/20-ra javult. **Ezért a v0.7e router
lett az éles alapértelmezett viselkedés**: a `chat.py` és a
`web/app.py` mostantól induláskor **mindkét** modellt betölti (v0.7 -
általános, v0.7c - mondatszám), és a routeren keresztül válaszol.
Sem a v0.7, sem a v0.7c modellfájl nem változott - csak a köréjük épülő
logika. A `--no-router` kapcsolóval a régi, egy-modelles viselkedés is
visszakapcsolható, ha csak egy adott modellt akarsz kipróbálni:

```bash
python src/chat.py --no-router --model-path models/mf_ai_zero_chat_v0_7d.pt
python web/app.py --no-router --model-path models/mf_ai_zero_v0_4.pt
```

**Ismert, megmaradt korlát**: a v0.7c önmagában (a `sentence_request`
ágon) néha ismétel egy mondatot ugyanazon a válaszon belül, vagy nem
mindig tökéletesen témahű (lásd a v0.7c szakaszt) - ezt a router nem
oldja meg, csak a MONDATSZÁMOT garantálja pontosan. Ez egy jövőbeli
finomítási irány, nem blokkolja a jelenlegi STABIL státuszt, mert a
kért elfogadási feltételek (pontos darabszám, nem feltétlenül tartalmi
tökély) mind teljesülnek.

## Barátnak megosztás ideiglenesen

Ez **nem éles/végleges deploy** - egy egyszerű, ideiglenes módja annak,
hogy valaki más gépről, más wifiről is kipróbálhassa a webes chatet,
amíg a saját géped fut és a szervert nem állítod le. Két opció van.

### A) Helyi teszt (csak a te géped éri el)

```bash
python web/app.py
```

Nyisd meg te magad: **http://localhost:8000**

Ez ugyanaz, mint eddig - senki más nem éri el, mert a szerver csak a
saját gépedről elérhető címen (`127.0.0.1`) figyel.

### B) Ideiglenes külső teszt (a barátod is eléri)

Ehhez két dolog kell: (1) a szerver "kifelé" is figyeljen, (2) legyen
rajta jelszó, hogy ne legyen bárki számára nyitott a neten.

**1. lépés - jelszó beállítása és a szerver indítása külső hoston**

PowerShellben:

```powershell
$env:TEST_PASSWORD = "valami-nehezen-kitalalhato-jelszo"
python web/app.py --host 0.0.0.0
```

A konzol kiírja, hogy "Jelszavas védelem: BEKAPCSOLVA", és a helyi
hálózati IP-címedet is (pl. `http://192.168.1.75:8000`) - ez már önmagában
elég lenne, ha a barátod ugyanazon a wifin van, de a feladat szerint más
wifiről szeretné elérni, ezért kell egy tunnel (lásd 2. lépés).

Ha a portot is meg akarod adni (pl. mert a 8000 foglalt):

```powershell
$env:PORT = "8080"
python web/app.py --host 0.0.0.0
```

**2. lépés - tunnel indítása, hogy más wifiről is elérhető legyen**

A saját géped `http://localhost:8000` címét egy tunnel-szolgáltatás
teszi ideiglenesen elérhetővé egy publikus URL-en keresztül, anélkül
hogy router-portot kellene nyitnod. Két jó, ingyenes opció - válaszd az
egyiket, amelyik neked telepítve van vagy amelyiket szívesebben
telepítenéd:

**Cloudflare Tunnel (`cloudflared`)**

```powershell
winget install --id Cloudflare.cloudflared
cloudflared tunnel --url http://localhost:8000
```

**vagy ngrok**

```powershell
winget install --id ngrok.ngrok
ngrok http 8000
```

Mindkettő kiír egy publikus URL-t (pl. `https://valami-random-nev.trycloudflare.com`
vagy `https://valami-random-nev.ngrok-free.app`) - **ezt az URL-t küldheted el
a barátodnak**, a jelszóval együtt (felhasználónév mindig `friend`, a
jelszó az, amit a `TEST_PASSWORD`-ba írtál).

A barátod a linkre kattintva egy böngészős jelszó-bekérő ablakot lát
majd (HTTP Basic Auth) - ott adja meg a `friend` felhasználónevet és a
jelszót, utána ugyanazt a chat felületet látja, amit te.

**Fontos, mert ez ideiglenes megoldás:**
- Amíg a `cloudflared`/`ngrok` és a `python web/app.py` fut a gépeden,
  a link él. Ha bármelyiket bezárod, a link azonnal megszűnik.
- A tunnel URL-je minden indításkor más (ingyenes csomagnál) - ha
  újraindítod, új linket kell küldened.
- Ne oszd meg a linket nyilvánosan (pl. közösségi médiában) - ez egy
  ideiglenes, egy baráti tesztre szánt megoldás, nem egy publikus,
  skálázható szolgáltatás.

### Leállítás

Bármelyik opciót választottad, a megosztás azonnal megszűnik, ha:
1. leállítod a `python web/app.py`-t (a terminálban `Ctrl+C`), **és**
2. (ha tunnelt használtál) leállítod a `cloudflared`/`ngrok` folyamatot is
   (szintén `Ctrl+C` abban a terminálban).

Ha csak a tunnelt állítod le, de a `python web/app.py` fut tovább, a
géped `localhost:8000`-je magadnak továbbra is elérhető marad, csak a
barátod linkje szűnik meg - ez a biztonságos, javasolt sorrend.

## Deploy Renderre vagy Hugging Face Spacesre

A fenti tunnel-megoldás egyetlen hátránya, hogy a **te gépednek futnia
kell** hozzá. Ha azt szeretnéd, hogy a link akkor is éljen, ha a géped ki
van kapcsolva, a projektet feltöltheted egy ingyenes felhő-szolgáltatásra.
Ez sem "éles" deploy - egy kis, ingyenes teszt-szolgáltatás -, de a
géped futása nélkül is elérhető marad.

**Ehhez a projekt már fel van készítve**: a `web/app.py` mostantól
gunicorn alatt (`gunicorn web.app:app`) is fut, minden beállítás
(modell-elérési utak, host, port, `TEST_PASSWORD`) környezeti
változóból jön, a `requirements.txt` CPU-only PyTorch-ot kér (sokkal
gyorsabb telepítés), és van hozzá `render.yaml` (Renderhez) és
`Dockerfile` (Hugging Face Spaces-hez). **A v0.7e router-logika nem
változott** - csak a köré épülő indítási/konfigurációs réteg.

### Előfeltétel mindkét opcióhoz: a projekt git repóban legyen

```bash
cd MF-AI-Zero
git init
git add .
git commit -m "MF-AI-Zero - deploy előkészítés"
```

Utána hozz létre egy repót GitHubon (Renderhez) vagy egy Space-et
Hugging Face-en (ahogy lent), és told fel oda.

### Mit kell feltölteni

**A teljes projektet** (nincs értelme kihagyni semmit, összesen ~11 MB):
`web/`, `src/`, `models/`, `data/`, `templates`/`static` (a `web/`
alatt), `requirements.txt`, `render.yaml`, `Dockerfile`. A futáshoz
ténylegesen csak két modellfájl **kötelező**:
`models/mf_ai_zero_chat_v0_7.pt` (általános chat) és
`models/mf_ai_zero_chat_v0_7c.pt` (mondatszám-kérések) - a többi
(`mf_ai_zero_v0_4.pt`, `mf_ai_zero_best.pt`, `mf_ai_zero_chat_v0_7d.pt`)
csak akkor kell, ha összehasonlításként őket is ki akarod próbálni
deploy után a `MODEL_PATH` env-változóval.

### Mit kell beállítani (mindkét platformon ugyanaz az elv)

| Környezeti változó | Érték | Miért |
|---|---|---|
| `TEST_PASSWORD` | egy általad kitalált jelszó | enélkül a link bárkinek nyitott a neten! |
| `HOST` | `0.0.0.0` | hogy a platform elérje kívülről (Renderen kötelező beállítani; a Dockerfile ezt már tartalmazza) |

A `PORT`-ot mindkét platform saját maga állítja be automatikusan (Render
a `$PORT`-ot, Spaces a `7860`-at) - ezzel nincs teendőd.

### A) Render (ajánlott - lásd az indoklást a szakasz végén)

1. Told fel a repót GitHubra (`git remote add origin ...`, `git push`).
2. Menj a [render.com](https://render.com)-ra, jelentkezz be (ingyenes
   fiók GitHub-bal is mehet), majd **New +** → **Blueprint**.
3. Válaszd ki a GitHub repódat - Render automatikusan megtalálja a
   `render.yaml`-t, és felkínálja a `mf-ai-zero-chat` szolgáltatást.
4. Kattints **Apply**-ra. Render elindítja az első buildet
   (`pip install -r requirements.txt`, kb. 3-5 perc a torch letöltése
   miatt).
5. Amint kész a build, menj a szolgáltatás **Environment** fülére, és
   add hozzá a `TEST_PASSWORD` változót (a `render.yaml` szándékosan nem
   tartalmazza az értékét, hogy ne kerüljön be a git repóba). Mentés
   után Render automatikusan újraindítja a szolgáltatást.
6. A szolgáltatás tetején megjelenik a publikus URL, valami ilyesmi:
   `https://mf-ai-zero-chat.onrender.com` - **ezt küldheted el a
   barátodnak**, a `TEST_PASSWORD`-dal együtt (felhasználónév: `friend`).

*Ha nem akarsz `render.yaml`-t használni, kézzel is beállítható: New + →
Web Service → a repód kiválasztása → Runtime: Python 3 → Build Command:
`pip install -r requirements.txt` → Start Command:
`gunicorn --bind 0.0.0.0:$PORT web.app:app` → majd a fenti env-változók
hozzáadása.*

**Ingyenes csomag korlátai**: 15 perc inaktivitás után "elalszik" a
szolgáltatás, a következő kérésre ~30-50 másodperc alatt ébred fel újra
- ez normális, nem hiba, és baráti tesztelésre bőven elég.

### B) Hugging Face Spaces (Docker SDK)

1. Told fel a repót GitHubra (mint fent), VAGY told fel közvetlenül a
   Space saját git repójába (lásd 3. lépés).
2. Menj a [huggingface.co/new-space](https://huggingface.co/new-space)
   oldalra, jelentkezz be, adj nevet a Space-nek, és az **SDK**
   választásnál válaszd a **Docker**-t (nem Gradio/Streamlit!), a
   láthatóságnál pedig azt, amit szeretnél (Public, hogy a barátod is
   elérje link nélküli belépés próbálgatása nélkül).
3. A Space létrehozása után az egy git repó - told fel bele a projekt
   tartalmát:
   ```bash
   git remote add hf https://huggingface.co/spaces/FELHASZNALONEVED/SPACE-NEVED
   git push hf main
   ```
4. Menj a Space **Settings** fülére, **Repository secrets** alatt add
   hozzá a `TEST_PASSWORD`-ot (ez a HF megfelelője a Render env
   változóinak - titkosítva tárolja, nem látszik a Space kódjában).
5. A Space automatikusan build-eli a `Dockerfile`-t, és pár perc után
   fut. A publikus URL a Space oldalán jelenik meg, valami ilyesmi:
   `https://huggingface.co/spaces/FELHASZNALONEVED/SPACE-NEVED` - **ezt
   küldheted el a barátodnak**, a `TEST_PASSWORD`-dal együtt.

**Ingyenes csomag korlátai**: a Space is elalszik inaktivitás után
(alapból), és a saját HF felhasználói fiókodhoz kötött nyilvános
URL-mintát kapja - ez baráti tesztelésre szintén bőven elég.

### Melyik a jobb ehhez a célhoz? **Render.**

Mindkettő működik, de Renderhez **nem kell Docker-fájlt írnod és
érteni** - a `requirements.txt` + `render.yaml` elég, Render natívan
futtatja a Python kódot. A Hugging Face Spaces Docker SDK-ja extra
réteg (Dockerfile, a 7860-as port konvenció, "Repository secrets" vs.
sima env változók közti különbség), ami ehhez az egyszerű,
ideiglenes-teszt célhoz felesleges bonyodalom. Render dashboardja is
egyszerűbb egy sima webalkalmazáshoz (Hugging Face Spaces inkább ML
*demókhoz*, Gradio/Streamlit-hez van optimalizálva). A Dockerfile-t
azért meghagytam a projektben, mert (a) így HF Spaces is egy az egyben
működik, ha mégis azt választanád, és (b) bármilyen más Docker-alapú
hoszthoz is azonnal használható.

## Válaszértékelés és tanulási napló (v0.8)

A v0.8 **nem tanít és nem módosít semmilyen modellt** - egy megfigyelő
réteget ad a v0.7e router fölé, ami minden AI-választ automatikusan
kiértékel és naplóz, hogy később (külön lépésben, emberi átnézéssel)
ebből javító tanítóadatot lehessen válogatni.

- **`src/evaluator.py`** - `evaluate_reply()`: egyszerű, szabályalapú
  pontozás (0-100), ami konkrét, a projekt korábbi fejlesztése során
  ténylegesen megfigyelt hibamintákat keres: üres/placeholder válasz,
  kiszivárgott `User:`/`AI:` címke, ismétlődő mondat egy válaszon belül,
  túl rövid válasz, és (mondatszám-kéréseknél) eltérő mondatszám a
  kérttől. Nem gépi tanulás - csak konkrét, ellenőrizhető szabályok.
- **`src/learning_log.py`** - `log_feedback()`: minden választ egy sorba
  ment (JSONL formátum) a `learning_log/feedback.jsonl` fájlba: user
  üzenet, AI válasz, intent, melyik modell válaszolt, a válasz hossza
  (karakter és szó), a minőségi pontszám és a talált problémák.
- A `chat.py` és a `web/app.py` mindegyik válasz után automatikusan
  meghívja mindkettőt - ez egy **tisztán additív, a válasz generálása
  UTÁN lefutó lépés**, ami nem változtatja meg, mit kapsz vissza a
  chatben, csak naplózza azt.

Példa egy naplósorra:

```json
{"timestamp": "2026-09-16T16:22:05", "user_message": "Írj 4 mondatot a tanulásról.", "ai_reply": "...", "intent": "sentence_request", "model_used": "v0.7c", "reply_length_chars": 274, "reply_length_words": 42, "quality_score": 100, "quality_flags": [], "sentence_requested": 4, "sentence_actual": 4, "sentence_fixed": false}
```

Teszt:

```bash
python tests/test_v08_learning_log.py
```

**Fontos, amit szándékosan NEM csinál a v0.8**: nem indít el semmilyen
automatikus tanítást, nem válogat ki "jó" vagy "rossz" példákat, és nem
nyúl egyetlen modellhez sem. Ez egy jövőbeli lépés (pl. v0.9) lehetne -
egy külön szkript, ami a `learning_log/feedback.jsonl`-t átnézi (esetleg
emberi jóváhagyással), és ebből épít egy új tanító adatfájlt.

## Miért csak v0.1?

Ez egy indulási alap, nem egy kész, "okos" nyelvi modell. Ennyi tanító
mondatból és ekkora modellméretből még nem várható folyékony,
nyelvtanilag mindig helyes szöveg — inkább azt láthatod, hogy a modell
kezdi felismerni a magyar szavak és mondatok jellegzetes mintázatait
(betűkapcsolatok, ékezetek, szóhosszúságok stb.).

A cél az volt, hogy legyen egy **egyszerű, működő, teljesen saját**
alaprendszer, amit utána szabadon lehet fejleszteni.

## Hogyan lehet később okosítani?

Néhány irány, amerre a projektet tovább lehet fejleszteni:

1. **Több és jobb tanító szöveg**: minél több és változatosabb magyar szöveget
   adsz a `data/train.txt`-hez (vagy több fájlhoz), annál jobb mintázatokat
   tud tanulni a modell.
2. **Nagyobb modell**: a `src/config.py`-ban növelheted az `embedding_dim`,
   `hidden_size` és `num_layers` értékeket — ez erősebb, de lassabb tanítást
   eredményez.
3. **Hosszabb tanítás**: a `num_epochs` növelésével tovább tanulhat a modell
   ugyanazon az adaton.
4. **Szó-alapú tanítás**: karakterek helyett szavakra (vagy "subword" token-ekre)
   való áttérés gyorsabb, koherensebb szöveggenerálást tesz lehetővé.
5. **Transformer architektúra**: az LSTM helyett egy egyszerű, saját
   Transformer (pl. egy mini GPT-stílusú modell) építése további
   tanulási lehetőség, és jellemzően jobb eredményt ad.
6. **Validációs adat és korai leállás**: külön validációs szöveggel mérve
   elkerülhető a túltanulás (overfitting).

## Mit futtass a kipróbáláshoz?

```bash
pip install -r requirements.txt
python src/train.py
python src/generate.py --prompt "Az erő bennem"
python src/train_chat.py --epochs 200 --patience 15
python tests/test_v07e_router.py
python src/chat.py
python web/app.py
```

Az utolsó sor után nyisd meg a böngészőben: `http://localhost:8000`
