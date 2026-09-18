# Második FELÜGYELT step_by_step batch - step_by_step 0101-0200

## 0. A ChatGPT raw candidate fájl ellenőrzésének eredménye (második pilot próbálkozás)

A `data/inbox/chatgpt/chatgpt_step_by_step_0101_0200_raw.jsonl` fájlt
**RAW CANDIDATE** státuszban kezeltük, a teljes kötelező pipeline-nal
ellenőrizve, a producer önellenőrzési állításától függetlenül.

### Schema validáció eredménye
- **Valid sorok**: 0 / 100
- **Ok**: minden sorból hiányzott a kötelező `source` mező. Az `input`
  mezőt a producer az első pilot óta technikailag stringgé alakította,
  de az **érték** továbbra sem felelt meg a konvenciónak: minden sor
  `input` értéke a szó szerinti `"{\"Current\":null}"` szöveg volt az
  elvárt üres string (`""`) helyett.
- **Ellentmondás a beküldött állítással**: a beküldő ismét azt
  állította, hogy "kötelező mezők megvannak: igen" - ez ismét **téves**
  volt.

### Súlyosabb, tartalmi probléma: a batch nem tartalmazott új tartalmat
A validáláson túl egy **sokkal komolyabb probléma** is kiderült: a
`chatgpt_step_by_step_0101_0200_raw.jsonl` mind a 100 sorának
`instruction` és `output` mezője **szó szerint megegyezik** az első,
korábban elutasított `chatgpt_step_by_step_0001_0100_raw.jsonl` batch
100 sorával - csak az `id` mezők lettek átszámozva (0001→0101, stb.),
és hozzáadódott egy minden sorban **azonos, generikus boilerplate**
`quality_notes` szöveg ("Egyedi, hétköznapi, lépésenkénti magyar
példa."). Ez azt jelenti, hogy a második batch **valójában nem
tartalmazott egyetlen genuinly új példát sem** - technikailag "javított"
mezőkkel újraküldött, de tartalmilag azonos anyag volt.

### Döntés
Mind a 100 sor **elutasításra került**, `reason:
"schema_invalid_missing_fields_and_duplicate_content"` jelöléssel, a
teljes eredeti sor megőrzésével:
`data/rejected/chatgpt_step_by_step_0101_0200_rejected.jsonl`.
**Egyik sor sem lett automatikusan javítva vagy elfogadva.**

### Visszajelzés a ChatGPT/Dispatch producer felé (második, súlyosabb kör)
1. A `source` mező **továbbra is hiányzik** minden sorból - ez már a
   második egymást követő batch, ahol ez a probléma fennáll.
2. Az `input` mező most már string típusú, de az **értéke** helytelen -
   üres stringnek (`""`) kell lennie, nem a `{"Current": null}` szöveg
   szó szerinti string-reprezentációjának.
3. **A legsúlyosabb probléma**: a második batch tartalma szó szerint
   megegyezik az elsőével. Egy valódi "második batch"-nek **genuinly új,
   különböző instrukció-output párokat** kell tartalmaznia, nem a
   korábbi (már elutasított) tartalom újraszámozott másolatát.
4. A `quality_notes` mezőnek **egyedi, az adott sor tartalmára
   vonatkozó, rövid leírásnak** kell lennie minden sornál, nem azonos
   boilerplate szövegnek.

## 1. A pótló Claude-generált batch

Mivel a ChatGPT raw candidate ismét 0 clean sort eredményezett (és ami
benne volt, az sem lett volna új tartalom), a teljes 100 soros célt
**genuinly új témakörökkel rendelkező Claude-generált tartalommal**
pótoltuk, tudatosan elkerülve az első Claude batch (0001-0100)
témaköreit is.

- Forrás: **Claude-generált**, 100 db, kézzel megírt, majd a teljes
  meglévő pipeline-nal ellenőrzött sor.
- `category`: `step_by_step`, `source`: `synthetic_claude`.
- 10 vadonatúj témablokk (alvás/pihenés, digitális jólét, új hobbi
  kezdése, lakásköltözés, kisállattartás, vendéglátás/házibuli,
  önkéntesség, digitális biztonság, karrier/önéletrajz, stresszkezelés)
  - egyik sem ismétli az első batch témáit (háztartás, konyha, utazás,
    tanulás, ügyintézés, kertészet, sport, munka, pénzügy, etikett).

### 1.1 Számok

| Mérőszám | Érték |
|---|---|
| Raw sorok (Claude-generált) | 100 |
| Validáláson elfogadva | 100 |
| Validáláson elutasítva | 0 |
| Batchen belüli dedupe (id/instruction/output) | 0 találat |
| Kereszt-batch **jelzett** (0.9 fölötti) egyezés (teljes 2100 soros korpuszon) | 5 |
| Ebből az ÚJ step_by_step batch-et érintő | **0** |
| **Végleges clean sorok** | **100** |
| **Rejected sorok** (Claude batch-en belül, tartalmi ok miatt) | **2** (lásd 1.3) |
| Átlag quality_score | **100.0** |
| Flag-et kapott sor | 0 |
| Difficulty eloszlás | easy: 62, medium: 33, hard: 5 |
| Formátum-ellenőrzés (számozott lépések, egyedi quality_notes) | 100/100 megfelelt |

### 1.2 Ellenőrzési lépések (teljes pipeline)

#### Schema validate
Mind a 100 sor strukturálisan érvényes.

#### Magyar nyelvi/formátum ellenőrzés
Minden output 4-6 számozott lépést tartalmaz, "1."-gyel kezdődik,
100-700 karakter hosszú, minden instrukció tartalmazza a "lépés" szót,
és - a ChatGPT batch-csel ellentétben - **minden sor egyedi
quality_notes szöveggel rendelkezik**. **100/100 sor megfelelt.**

#### Batchen belüli dedupe
`tools/dataset_dedupe.find_duplicates()` a 100 soron belül: **0 id-,
0 instruction-, 0 output-duplikátum.**

#### Kizárt témák explicit ellenőrzése ÉS a felfedezett, kezelt probléma
Az első keresztfutás **2 találatot** adott a "wifi" kizárt kulcsszóra
(`step_by_step_0174`: "hogyan védd meg az otthoni wifi hálózatodat",
`step_by_step_0176`: "nyilvános wifi hálózatok biztonságos használata").
**Ez esetben - a korábbi batch-ekben tapasztalt rövid-sablon hamis
pozitívoktól eltérően - ez egy VALÓDI, szándékos kizárt téma találat
volt**, nem véletlen szövegegyezés: a "wifi" szó explicit szerepel az
AUTOPILOT kizárt témalistáján. **Mindkét sort eltávolítottuk**, és két
alternatív digitális biztonsági témával pótoltuk (régi eszköz
biztonságos törlése, böngésző adatvédelmi beállításai), amik nem
érintik a kizárt témát. A két eredeti (wifi témájú) sor dokumentálva
lett a rejected fájlban, `reason: "excluded_topic_wifi"` jelöléssel,
jelezve, hogy más szempontból (schema, score) megfeleltek volna, de a
kizárt téma miatt nem kerülhettek clean-be.

AI-tagelt sor: **0/100**.

#### Teljes korpuszos cross-dedupe (a TELJES 2100 soros meglévő korpusz +
    ez a 100 sor - a patchelt verzióval -, 0.9 küszöb, összesen 2200 sor)

A dedupe **5 db 0.9 fölötti instruction-hasonlósági egyezést** jelzett,
mind az öt a **korábban már dokumentált, megtartott simple_qa hamis
pozitívok pontos megismétlődése**:

| kept | duplicate | similarity |
|---|---|---|
| simple_qa_0851 | simple_qa_0857 | 0.904 |
| simple_qa_0851 | simple_qa_0859 | 0.919 |
| simple_qa_0671 | simple_qa_0914 | 0.919 |
| simple_qa_0734 | simple_qa_1081 | 0.918 |
| simple_qa_0915 | simple_qa_0489 | 0.921 |

**Az ÚJ step_by_step_0101-0200 batch egyik sora sem szerepel egyik
jelzésben sem** - fontos megerősítés, hogy annak ellenére, hogy ez a
batch is életszerű, hétköznapi témákat érint, mint az első Claude batch,
a konkrét instrukciók és megfogalmazások nem ütköznek egymással.

#### `tools/dataset_topic_report.py`

**A teljes, egyesített korpuszon** (1000 simple_qa + 1000 explanation +
200 step_by_step = 2200 sor): legmagasabb tag fizika 5.1%. **Túl-
reprezentált tagek: NINCS.**

#### `dataset_score.py`
Mind a 100 sor **100/100** pontot kapott, flag nélkül.

#### Safety/firewall ellenőrzés
- **`src/guard.py` `looks_like_identity_bleed()`**: **0 találat**.
- **Kiegészítő kulcsszó-szűrés (a wifi-témát leszámítva, lásd fent)**:
  **4 további nyers találat**, mind manuálisan ellenőrizve és **hamis
  pozitívnak** bizonyult:
  - "gyógyszertár" (`step_by_step_0139`: költözés utáni környékismerkedés,
    "bolt vagy gyógyszertár" - helymeghatározási landmark, nem
    gyógyszerhasználat).
  - "adag" (`step_by_step_0142`: "kövesd az állatorvos által javasolt
    adagolást" - háziállat-etetés, nem emberi gyógyszeradag).
  - "mérgez" és "vegyszer" (`step_by_step_0150`: "zárd el a mérgező
    növényeket és vegyszereket" - háziállat-biztonsági, védekező
    jellegű tanács, nem károkozásra buzdítás).
- **Digitális biztonság blokk (171-180, a patchelt 174/176-tal együtt)
  külön is átnézve**: minden sor általános, védekező jellegű digitális
  biztonsági gyakorlati tanács, egyik sem ad konkrét feltörési vagy
  visszaélési útmutatást.

### 1.3 Manuális mintavételes tartalmi átnézés (20 sor, minden témablokkból 2)

| id | Instruction | Értékelés |
|---|---|---|
| step_by_step_0101 | Írd le lépésekben, hogyan alakíts ki nyugodt esti lefekvési rutint. | Gyakorlati, veszélytelen. OK. |
| step_by_step_0106 | Írd lépésekben, hogyan csökkentsd a koffein alvásra gyakorolt hatását. | Általános, nem orvosi tanács. OK. |
| step_by_step_0111 | Írd le lépésekben, hogyan csökkentsd a napi képernyőidődet tudatosan. | Semleges digitális jólét. OK. |
| step_by_step_0118 | Írd lépésekben, hogyan mérd fel a digitális eszközhasználat hatását a közérzetedre. | Elvontabb, önreflexiós. OK. |
| step_by_step_0121 | Írd le lépésekben, hogyan kezdj el egy teljesen új hobbit felnőttként. | Semleges, gyakorlati. OK. |
| step_by_step_0126 | Írd lépésekben, hogyan tervezz meg egy kezdő költségvetést egy új hobbihoz. | Felelős, nem konkrét pénzügyi tanács. OK. |
| step_by_step_0131 | Írd le lépésekben, hogyan tervezz meg egy lakásköltözést időben. | Gyakorlati, veszélytelen. OK. |
| step_by_step_0137 | Írd le lépésekben, hogyan csökkentsd a költözéssel járó stresszt. | Semleges pszichológiai tanács. OK. |
| step_by_step_0141 | Írd le lépésekben, hogyan készülj fel egy új kisállat érkezésére. | Gyakorlati, felelős. OK. |
| step_by_step_0147 | Írd le lépésekben, hogyan válassz megfelelő állatorvost. | Gyakorlati, nem orvosi diagnózis. OK. |
| step_by_step_0154 | Írd lépésekben, hogyan tervezz meg egy allergiákra is figyelő vendéglátást. | Felelős, biztonságtudatos. OK. |
| step_by_step_0161 | Írd le lépésekben, hogyan kezdj el önkénteskedni. | Semleges, közösségi. OK. |
| step_by_step_0171 | Írd le lépésekben, hogyan hozz létre erős, biztonságos jelszót. | Gyakorlati digitális biztonság. OK. |
| step_by_step_0178 | Írd lépésekben, hogyan járj el gyanús fiókaktivitás esetén. | Védekező, felelős tanács. OK. |
| step_by_step_0181 | Írd le lépésekben, hogyan írj meg egy hatékony önéletrajzot. | Gyakorlati karriertanács. OK. |
| step_by_step_0189 | Írd le lépésekben, hogyan mondj fel elegánsan egy munkahelyen. | Semleges, professzionális. OK. |
| step_by_step_0191 | Írd le lépésekben, hogyan végezz egy egyszerű légzőgyakorlatot. | Általános, nem klinikai. OK. |
| step_by_step_0195 | Írd le lépésekben, hogyan kezelj egy hirtelen szorongásos pillanatot. | Felelősen megfogalmazott, szakemberhez irányít, ha tartós. OK. |
| step_by_step_0199 | Írd le lépésekben, hogyan kérj segítséget tartós túlterhelés esetén. | Felelős, szakemberhez irányító tanács. OK. |
| step_by_step_0200 | Írd lépésekben, hogyan tarts fenn hosszú távú egyensúlyt munka és pihenés között. | Semleges, összegző. OK. |

**Eredmény: 20/20 sor megfelelt.**

## 2. Fájlok

- ChatGPT raw candidate (megőrizve, forrásként): `data/inbox/chatgpt/chatgpt_step_by_step_0101_0200_raw.jsonl` (100 sor, NEM clean)
- ChatGPT candidate rejected: `data/rejected/chatgpt_step_by_step_0101_0200_rejected.jsonl` (100 sor, schema hiba + duplikált tartalom miatt)
- Claude raw (pótlás, patchelt verzió): `data/raw/claude_step_by_step_0101_0200_raw.jsonl` (100 sor)
- Clean: `data/clean/claude_step_by_step_0101_0200_clean.jsonl` (100 sor)
- Rejected (Claude batch, kizárt téma miatt, dokumentációs céllal): `data/rejected/claude_step_by_step_0101_0200_rejected.jsonl` (2 sor, eredeti wifi-témájú változatok, pótolva)

## 3. Regressziós teszt
`tests/test_v1_7_4_dataset_foundation.py` - **minden teszt sikeres, STÁTUSZ:
STABIL**.

## 4. Amit ez a kör NEM tett

- **Nem indított tanítást.**
- **Nem módosított webapp/backend kódot.**
- **Nem nyúlt a régi clean fájlokhoz.**
- **Nem bízott meg automatikusan a ChatGPT raw candidate-ban.**
- **Nem javította automatikusan a ChatGPT raw candidate strukturális
  hibáit.**
- **Nem hagyott clean-be kerülni kizárt témájú (wifi) tartalmat**, még
  akkor sem, amikor az a saját, Claude-generált tartalmában bukkant fel
  - a validator szerep saját generálásra is ugyanolyan szigorral
    vonatkozik.

---

## Végső összegzés

- ChatGPT raw candidate (2. próbálkozás): 100 sor beküldve, **0 clean**
  (100% schema elutasítás - hiányzó `source` mező, hibás `input` érték
  -, ÉS a tartalom 100%-ban megegyezett a korábban már elutasított első
  batch-csel, csak átszámozva).
- Claude pótló generálás: 100 raw → **100 clean** (2 saját sor is
  kizárásra került és pótlásra a wifi kizárt téma miatt, ez
  dokumentálva).
- Kereszt-batch duplikátumok száma: **0** (mind az öt jelzés a korábbi
  simple_qa hamis pozitívok megismétlődése).
- Átlag quality_score: **100.0**.
- Safety: 0 identity-bleed, 1 valódi kizárt-téma találat (kezelve,
  pótolva), 4 hamis pozitív kulcsszótalálat (mind ellenőrizve).
- 20 soros manuális mintavétel eredménye: **20/20 megfelelt**.
- **Egyedi clean step_by_step sorok jelenleg összesen: 200 / 500.**
- **Hiányzik még a 3. csomag céljához: 300 sor.**

**STÁTUSZ: STABIL.**

**Súlyosabb visszajelzés a ChatGPT/Dispatch producer felé**: a második
pilot batch nem csupán ismét séma-hibás volt (hiányzó `source` mező),
hanem **tartalmilag is azonos volt az elsővel** - ez arra utal, hogy a
producer jelenleg nem genuinly új tartalmat generál batch-enként, hanem
ugyanazt a mintakészletet küldi be újraszámozva. Mielőtt egy harmadik
próbálkozás érdemi lenne, ezt a mögöttes problémát (nem a séma-formátumot,
hanem magát a tartalomgenerálási folyamatot) kell orvosolni a producer
oldalán.
