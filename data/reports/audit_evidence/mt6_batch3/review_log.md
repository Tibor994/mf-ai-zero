# MT-6 harmadik batch (`multiturn_0101`–`0150`) — rekordszintű AI-felülvizsgálati napló

**Ez AI-alapú felülvizsgálat (Claude-alügynökök + saját közvetlen ellenőrzés), NEM független és NEM emberi audit.**

Menete: 3 kör. Mindegyik alügynök a generálástól független, friss kontextusban, a tényleges szöveget olvasta; minden
jelzést a szerző (én) a tényleges szövegen közvetlenül megvizsgált, és csak akkor javított, ha a jelzés igaz volt.
Az alügynökök üzenetenként átnézték a rekordokat (nyelv, tartalom, számítás, név-szabály, `meta.depends` tartalmi
helyessége, címke-illeszkedés, forrásigény). Egy alügynök (0126–0150) az első körben elakadt, ezt két kisebb
tartományra bontva újra futtattam.

| Kör | Hatókör | OK | NEEDS_FIX | WITHHELD |
|---|---|---|---|---|
| 1. (az eredeti piszkozat) | mind az 50 | 13 | 37 | 0 |
| 2. (az 1. kör javításai után, teljes újraolvasás) | mind az 50 | 19 | 31 | 0 |
| 3. (célzott, a legtöbbet átírt rekordokon) | 12 rekord | 2 | 10 | 0 |

A 2. és 3. körben a jelzések java már kisebb (hivatkozás-finomítás, megfogalmazás), de volt érdemi is (lásd lent). A
3. kör után **újabb teljes kör nem futott**: a maradék, ismert nyitott pontokat a jelentés 6. szakasza sorolja fel.
Az eredeti piszkozathoz képest **46 rekord módosult** (44 rekordban szöveg, összesen 128 üzenet; 37 rekordban
`meta.depends`), **változatlan maradt 4**: `0105`, `0136`, `0143`, `0148`. Címke-változás 3 rekordnál: `0114`
nehézség hard→medium és `0133` medium→hard (kvóta-semleges csere, a tartalmi összetettségnek megfelelően), `0130`
`sensitive_area` false→true (jogi határidő-tájékoztatás). Család, tématerület, hossz, register, azonosító és a
tervezett változat-pár nem változott.

## Jelzés-típusok (az 1. körből, a javítás előtti állapotról)

* `meta.depends` tartalmilag téves vagy azonos váltáson belüli kontextusra épülő hivatkozás: a leggyakoribb (kb. 30 rekord).
* Ténybeli / elavult / szolgáltatófüggő állítás általános tényként: `0110`, `0111`, `0120`, `0130`, `0133`.
* Kitalált vagy feltételezett információ: `0122` (kitalált tó), `0127` (a felhasználó be nem mondott célja), `0142`/`0147` (a javaslat döntésként kezelve).
* Be nem teljesített kérés vagy elhagyott elem: `0139` (típus), `0145` (két mondat), `0146` (közműszolgáltatók), `0147` (belefér-e?), `0149`.
* Nyelvtan / természetesség: `0101`, `0102`, `0111`, `0113`, `0114`, `0128`, `0129`, `0131`, `0132`.
* Címke: `0102` (elírás, `user_typos=false`), `0128` („mégis inkább” előzmény nélkül), `0130` (`sensitive_area`).

## Rekordok

R1/R2/R3 = az adott kör ítélete (OK = megfelelt, NF = javítandó). „–” = abban a körben nem vizsgált.

| Azonosító | R1 | R2 | R3 | Fő jelzések és javítás |
|---|---|---|---|---|
| 0101 | NF | OK | – | „hány könyvet”; „üresen sem lóg le” logikai hiba → „teli sem lóg a dereka alá”; a merevített hátrész visszakerült az összegzésbe |
| 0102 | NF | OK | – | „a páromal” elírás a `user_typos=false` rekordban → „a párommal”; „beleférnek”; „jó eséllyel belefértek”; `depends` finomítva |
| 0103 | NF | NF | – | `depends` t7 nem valódi (a felhasználó újra megnevezte) → kérdés átfogalmazva; lazanya-lap darabszám nélkül, kirakásos módszerrel; sajt: 30–40 dkg |
| 0104 | NF | NF | – | `depends` t9 téves hivatkozás javítva; t5, t7 bővítve; „Melyek a regények” |
| 0105 | OK | OK | – | változatlan |
| 0106 | NF | NF | – | `depends` t5/t7/t9; 7 literes festékdoboz nem szabványos → 5 + 2,5 literes doboz; egyetlen vásárlási javaslat |
| 0107 | NF | NF | – | `depends` t11 téves, t7/t9 gyenge; az „első lépcső” árnyalás a fél tizenkettes lefekvésnél |
| 0108 | NF | NF | – | gyenge `depends` törölve/javítva; „SMS-kód”, „hitelesítő alkalmazás”, „jelszókezelő” |
| 0109 | OK | OK | – | apró: „hétvégén korán”, „nyitvatartási időben” |
| 0110 | NF | NF | – | szolgáltatófüggő eljárás általános tényként (a személyes óraállás-bejelentés egyes szolgáltatóknál megszűnt) → forgatókönyv átírva: online vagy telefon, a szolgáltatófüggés jelezve; azonosító: „a számlán szereplő” |
| 0111 | NF | NF | – | „neki nem lehet feladni”, hiányzó ige; a tartály ürítésének gyakorisága ténybeli hiba; „a robot jobb a szőr ellen”; `depends` |
| 0112 | OK | NF | – | `depends` t7; „Tisza-parti sétány”; „fő látnivalókat” |
| 0113 | NF | OK | – | „hűlve szépen szeletelhető”; `depends`; kérdés pontosítva |
| 0114 | NF | NF | – | `depends` t7; „méter per másodperces sebességet”; „nulláról indulva”; nehézség hard→medium |
| 0115 | OK | NF | NF | a zárómondat félreérthető volt → „a levél végén az Üdvözlettel elé teheti”; „Üdvözlettel, László”; „együtt Önnel” |
| 0116 | OK | NF | NF | „mosva” → teljesen száraz ruha, nedvszívó zacskó; „ha van hely a szekrényedben”; `depends` t3 valódivá téve („nyárra”) |
| 0117 | OK | NF | NF | egészségügyi sürgősségi szintek 3 lépcsőre bontva (háziorvos / aznap-másnap / azonnal sürgősségi); „erősödik vagy kisugárzik, hagyd abba”; `depends` t7 valódivá téve („már két hete tart”) |
| 0118 | NF | NF | NF | `depends`; nincs operációs rendszer-feltételezés; fájlok és mappák méret szerinti rendezése pontosítva |
| 0119 | NF | OK | – | `depends` t7 törölve |
| 0120 | NF | NF | NF | a lakcímkártya-kiállításról szóló állítás volatilis és a források ellentmondtak (egyik: külön ügymenet, díjas; másik: a bejelentéssel együtt kiállítják) → **nem állít se díjat, se automatizmust**, az ügyintézőhöz utal; a régi/új lakcím (állandó vs tartózkodási hely) pontosítva; 3 munkanapos határidő „általában” jelzéssel; `depends` |
| 0121 | NF | OK | – | `depends`; „érdemes olyan gépet keresnie” (nem állítja, hogy belefér) |
| 0122 | NF | OK | – | kitalált tó („belvárostól vagy a tótól”) → látnivalók / tömegközlekedés; „dátumokat add meg” |
| 0123 | NF | OK | – | `depends` t7 |
| 0124 | NF | OK | – | `depends` (téves javítás: az asszisztens kitart, helyesen) |
| 0125 | NF | OK | – | `depends`; kérdés átfogalmazva („résztvevőkre”) |
| 0126 | NF | NF | – | `depends` t3/t5/t9; „szélesebb” (nem „kicsit”); a karnis hajlik, nem a függöny |
| 0127 | NF | NF | NF | az asszisztens a felhasználó be nem mondott fogyás-célját feltételezte → forgatókönyv átírva: súlyzós feltételezés, „nincs súlyzóm” (valódi javítás); plank vs ismétlés → csípőemelés; pihenőnapok pontosítva; összegzés felsorolja a gyakorlatokat |
| 0128 | NF | NF | – | „mégis inkább” előzmény nélkül → a nyitó célt (lépésszámlálás) ad; piaci állítás „általában”; ötven méteres vízállóság |
| 0129 | NF | NF | – | `depends`; vetítés-időpont megnevezve (öt óra körül), reklámokkal; „mozira” |
| 0130 | NF | OK | – | a határidő-szabály hiányos volt (feladás vs kézbesítés napja) → szabály- és eljárásfüggés jelezve; `sensitive_area=true`; `depends` |
| 0131 | NF | NF | – | `depends`; „költségkeret”; „városi kerékpárból”; piaci állítások hedge-elve |
| 0132 | NF | NF | – | `depends`; kérdéses költség-állítás hedge-elve; parkolás / nyitvatartás; „három főre”; látogatási sorrend |
| 0133 | NF | NF | NF | nem kivitelezhető sütési terv (héjas krumpli a hús mellett) → cikkekre vágva, korábban betéve; hús és hal külön tepsiben; csirke belső hőmérséklete; `depends`; nehézség medium→hard |
| 0134 | OK | OK | – | apró: „A fehér pólót a színes ruháktól külön” |
| 0135 | NF | NF | – | „alatt és attól jobbra, majd az ablaktáblák rögzítése parancs”; tárgysor-példa; `depends` |
| 0136 | OK | OK | – | változatlan |
| 0137 | NF | OK | – | „először sétálj, utána nyújts”; kérdés („az első végösszeg”) |
| 0138 | NF | NF | OK | `depends` t7/t9; „forrásban lévő víz”; „adatkábel”; a téglafal megfogalmazása |
| 0139 | NF | NF | – | `depends` t7 törölve; az összegzés megnevezi a játék típusát; „leütve”; „játékosonként” |
| 0140 | OK | OK | – | apró: pénznem elhagyva a százalékszámításnál; „Összefoglalva vigye magával” |
| 0141 | OK | NF | NF | a feltételezett kedvezmény biztos tényként szerepelt → feltételes megfogalmazás; `depends` |
| 0142 | NF | NF | NF | a hipotetikus hatvanezer „javasoltként”; „szűkös” → „valószínűleg kevés”; feltételes éjszakaszám; `depends` |
| 0143 | OK | OK | – | változatlan |
| 0144 | OK | NF | – | `depends`; a napok felsorolva („kedd, szerda, csütörtök és péntek”) — a tervezett változat-pár 0104-gyel, mindhárom kör tartalmilag különbözőnek találta |
| 0145 | NF | NF | – | „két mondat” kérés nem teljesült → két mondat; a fel nem kért kötelezettség (dobozok neve) törölve; `depends` |
| 0146 | NF | NF | OK | elhagyott teendő (közműszolgáltatók) pótolva; hivatalos lakcímbejelentés a beköltözés után; egyes szám |
| 0147 | NF | NF | NF | a „belefér?” kérdésre válasz; a hétfő/csütörtök „például”; tejtermék-ellentmondás feloldva; étkezések az összegzésben; edzés utáni fehérje időzítése „egy-két óra”; `depends` |
| 0148 | OK | OK | – | változatlan |
| 0149 | NF | OK | – | a válasz nem illett a kérdéshez („bajnokság neve”) → magyar válogatott; `depends` |
| 0150 | NF | NF | – | `depends`; a garantált bérminimum pontosítva; „könyvelő vagy munkajogi szakember” |

## A forrásigényes állítások ellenőrzése

Ellenőrzött (keresővel / hivatalos vagy másodlagos forrással, a rekord szövegében óvatosan, szükség esetén
hedge-elve): a regények szerzői (`0104`), a perihélium januárban és a ~3% távolságváltozás (`0124`), a sakk-alaphelyzet
(`0139`), az Ausztriába autóval utazás kötelező felszerelései és az EU-n belüli igazolvány (`0140`), a Vasi Skanzen
nyitva tartása idényfüggő (`0132`), az ajánlott küldemény feladási napjának szabálya az Ákr.-ban általában, de
eljárásfüggően (`0130`), az Excel ablaktábla-rögzítés (`0135`), a lakcím-bejelentés 3 munkanapos határideje
(`0120`, óvatosan megfogalmazva), a garantált bérminimum és a minimálbér kormányrendeleti szabályozása (`0150`).

**Nem igazolt maradt (nem tekinthető igazoltnak):** a lakcímkártya díja és automatikus kiállítása 2025 február után
(a források ellentmondtak, ezért a rekord nem állít semmit — `0120`); egészségügyi általános tanácsok (`0107`, `0117`,
`0127`, `0137`); sütési idők, belső hőmérséklet, mennyiségek (`0103`, `0113`, `0123`, `0133`); árszint-állítások
(`0102`, `0119`, `0121`, `0128`, `0131`, `0141`, `0142`, `0147`); festék-fedés 10 m²/liter (`0106`);
a kerékpár-vázméret (`0131`); a gyorsulás/sebesség és százalékszámítások pontosan újraszámoltak (nem forrásigényesek).

## 4. lépés — a 3. kör utáni, javítás utáni célzott tartalmi ellenőrzés (2026-10-07)

A 3. kör javításai (`0115`, `0116`, `0117`, `0118`, `0120`, `0127`, `0133`, `0141`, `0142`, `0147`) után a fenti naplóban
**nem szerepelt** javítás utáni tartalmi ellenőrzés (a 3. kör végén „újabb teljes kör nem futott”). Ezt a negyedik batch
megkezdése előtt, célzottan pótoltam: egy friss kontextusú Claude-alügynök (**AI-alapú, nem független, nem emberi**) a
10 rekord *jelenlegi* szövegét olvasta (nyelv, számítás, felhasználói feltételek, `depends`, név-szabály, címkék,
forrásigényes állítások); minden jelzést én is a tényleges szövegen ellenőriztem. Teljes újraaudit és mutációs vizsgálat
nem futott.

Eredmény: **9 OK, 1 NEEDS_FIX** (`0115`). A korábbi 10 jelzés mindegyike megoldottnak bizonyult, új hibát a javítások nem
vittek be; számolás, `n_exchanges`, név-szabály, register és címkék mindenhol rendben.

| Rekord | Eredmény a javítás után | Közvetlenül ellenőrzött teendő | Utóellenőrzés |
|---|---|---|---|
| 0115 | NEEDS_FIX | az „az Üdvözlettel elé” **nyelvtanilag hibás** (a „-vel” esetű szó nem kap „elé” névutót; „a levél végén … elé teheti” helyhatározó + irány keveredik) → „a levél végére, az „Üdvözlettel” zárás elé teheti:” | a módosított üzenet újraolvasva, MT-1 0 hiba |
| 0116 | OK | – | – |
| 0117 | OK | stiláris: „aznap-másnap” → „aznap vagy másnap” (helyesírás) | újraolvasva |
| 0118 | OK | – | – |
| 0120 | OK (alügynök) — lásd lent a szigorúbb saját megítélést | a régi lakcím sorsáról szóló állítás kicserélve (nem igazolt automatizmus kikerült); `depends` a 9. üzenetnél kiegészítve a 7. üzenettel | újraolvasva, MT-1 0 hiba |
| 0127 | OK | lógó határozói igenév („eszköz nélkül kezdve”) → „eszköz nélkül, a saját testsúlyoddal kezdj” | újraolvasva |
| 0133 | OK | nem blokkoló megjegyzés (három tepsi, nyers hús ellenőrzése) — nem volt hiba, nem módosítottam | – |
| 0141 | OK | megjegyzés: 55″ vs 65″ ülőtávolságra vitatott, a szöveg csak „illik”-et mond és az eredeti kínálat 55/65 volt — nem módosítottam | – |
| 0142 | OK | – | – |
| 0147 | OK | hiányzó záró vessző („például hétfőn és csütörtökön,”); az összegzés elhagyta a sajt mérséklését, amelyet a 11. üzenet kimondott → „mérsékelt joghurttal, túróval és sajttal” | újraolvasva |

A kérdéses 5 rekord (`0115`, `0117`, `0120`, `0127`, `0147`) a 3. körben már módosult rekord volt, így a „46 módosult
rekord / 4 változatlan” összesítés nem változik; a 4. lépés összesen 6 üzenetet és 1 `depends`-bejegyzést (`0120`) érint.
A harmadik batch végső `sha256`-ja a 4. lépés után: `65cf0ff4f76bce5e40a545508ae86d23971cf6b6f7d6c6b860b8a8af7fc6e38c`
(előtte `f00884176b589f4059044d71dc7aa496ec40763df06f4cd39430fea796f55cbd`). Az MT-1 a javított fájlon: 50/50
turns-validált, 0 hibás, 48 figyelmeztetés (a korábbi 49-ből egy `capitalized_token_review` megszűnt a `0115` átírásával).

### `0120` — állításonkénti ellenőrzés (díj- és ügyintézési állítások)

A kérdés: maradt-e a rekordban nem igazolt díj- vagy ügyintézési állítás. Az alügynök *másodlagos* forrásokból (hírek,
ingatlan-útmutatók, kormányhivatali összefoglalók) dolgozott, és a régi lakcímről szóló állítást „igazoltnak” minősítette. Én
ugyanezt a **jogszabályszövegből (Nytv., 1992. évi LXVI. tv., njt.jog.gov.hu)** is ellenőriztem, és ott ezt a pontot **nem**
tudtam megerősíteni, ezért a szigorúbb mércét alkalmaztam: bizonytalan tényt nem hagyok a szövegben tényként.

| Állítás a rekordban | Forrás / státusz | Lépés |
|---|---|---|
| Az új lakcímet a kormányablakban kell bejelenteni (3. üzenet) | másodlagos forrásokból igazolt (2025. 02. 01-től kormányablak; online is); elsődleges szöveget ennél a pontnál nem olvastam | marad; a szöveg a pontos eljárást a kormányablaknál való megerősítésre bízza |
| általában a beköltözéstől számított 3 munkanapon belül (3., 9.) | **elsődlegesen igazolt** (Nytv. 26. §) + másodlagos | marad („általában”, plusz megerősítés kérése) |
| bérlőként a bérleti szerződés és a bérbeadó nyilatkozata „kellhet” (3., 9.) | **elsődlegesen igazolt** (Nytv. 27/A. § (3): szállásadó hozzájárulása / teljes bizonyító erejű okirat) | marad („kellhet”, „szükség esetén”) |
| a tartózkodási hely bejelentése nem jelenti az eddigi lakóhely feladását (5.) | **elsődlegesen igazolt** (Nytv. 5. § (3)) | új szövegben szerepel |
| lakóhelyként bejelentve „a régi lakcím megszűnik” (5., régi szöveg) | az elsődleges szövegben nem találtam megerősítve; az alügynök másodlagos alapon igazoltnak vette | **kivéve**: a szöveg csak annyit mond, hogy ez attól függ, lakóhelyként vagy tartózkodási helyként jelenti-e be, és a régi cím külön jelentéséről az ügyintézőt kell kérdezni |
| lakcímkártya kiállítása / díja 2025 február után (7., 9.) | **ellentmondó források** (egyik szerint nem automatikus és díjköteles, másik szerint díjmentes), elsődleges szöveg nincs | a rekord **semmit nem állít**: „változhat … kérdezze meg az ügyintézőt”; **nem igazolt**, nem is jelölöm annak |

Következtetés: a rekordban nem maradt igazolatlan díj- vagy ügyintézési *állítás*; a lakcímkártyáról és a régi cím sorsáról
a szöveg szándékosan csak az ügyintézőhöz irányít. A felhasználó lakcímkártya-cserére vonatkozó kérdésére így nincs
közvetlen igen/nem válasz — ez tudatos, a tényszabály miatti kompromisszum. Az érzékeny-terület címke (`false`) a korábbi
döntés szerint marad (közigazgatási tájékoztatás, nem egészségügyi/jogi tanácsadás).
