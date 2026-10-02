# MT-6 — az első 100 beszélgetés teljes tartalmi felülvizsgálata (2. kör, AI-alapú) — jelentés

Dátum: 2026-10-02. Érintett fájlok: `data/raw|clean/claude_multiturn_0001_0050_*.jsonl`,
`data/raw|clean/claude_multiturn_0051_0100_*.jsonl` (mindkét pár azonos tartalmú). Bizonyítékok:
`data/reports/audit_evidence/mt6_batch2/` (az `*_audit2_*` jelölésű fájlok ebből a körből).

**Ez a kör tartalmi hibákat javított mindkét batchben, a felhasználó kifejezett engedélyével.**
Tanítás, modellmódosítás, split jóváhagyás és harmadik batch nem indult.

## 1. Ki és hogyan végezte az ellenőrzést

Két friss, erre a célra indított Claude-alügynök (`general-purpose`) vizsgálta át a 100 beszélgetés
minden üzenetét — egyik az első 50-et, másik a második 50-et —, a terv követelményeivel, a
formátum-specifikációval és a névtárral felszerelve, saját, a generálástól független kontextusban
(nem látták, hogyan készült a tartalom, és nem fogadták el a korábbi „megfelelt” jelzést
bizonyításként). Emellett én magam is közvetlenül átnéztem és leellenőriztem minden jelentett
találatot a tényleges, aktuális fájltartalom alapján, mielőtt bármit javítottam volna — ez
kiszűrt egy hamis találatot is (lásd 4. szakasz).

**Fontos pontosítás, a felhasználó kifejezett kérése szerint: ez AI-alapú, ismételt önellenőrzés,
nem független és nem emberi audit.** A két alügynök és én is ugyanaz a modellcsalád vagyunk
(Claude), csak külön kontextusban futva. A terv 6. szakasza szerinti **független/emberi** átolvasás
ettől továbbra is elkülönül, és **nem történt meg** — ez a következő, önállóan jóváhagyandó lépés
(lásd 7. szakasz).

## 2. Találatok száma

| | Batch1 (0001–0050) | Batch2 (0051–0100) | Összesen |
|---|---|---|---|
| Átnézett beszélgetés | 50/50 | 50/50 | **100/100** |
| `OK` (nem igényelt javítást) | 24 | 25 | 49 |
| `NEEDS_FIX` (javítást igényelt) | 26 | 25 | 51 |
| `WITHHELD` (visszatartott) | 0 | 0 | **0** |

A `NEEDS_FIX` 51 esete **egyetlen, rendszerszintű hibatípusra** vezethető vissza túlnyomó
többségében (lásd 3. szakasz): 23+19 = **42 eset** (82%) ugyanaz a hiba volt, nem 42 független
probléma. A fennmaradó 9 eset (5 batch1-ben, 4 batch2-ben) egyedi tartalmi/jelölési hiba volt,
mindegyiket külön dokumentálom (4. szakasz). **Visszatartott (rendezetlenül maradt) eset nincs** —
minden jelentett találatot megvizsgáltam, és vagy javítottam, vagy (egy esetben) a vizsgálat után
elvetettem mint téves jelzést.

## 3. A rendszerszintű hiba: az asszisztens a felhasználó be nem mutatott nevét használja

42 beszélgetésben (23 az első, 19 a második batchből) az asszisztens válasza már az **első**
(néhány esetben egy későbbi) fordulóban megszólítja a felhasználót a keresztnevén, miközben a
felhasználó **sehol** a beszélgetésben nem mutatkozik be („X vagyok”). A modell számára ez
kitalálható, forrás nélküli tudás lenne — pontosan az a hiba, amit a terv 4.3 szakasza explicit
tilt („a modell nem állíthatja, hogy előző beszélgetésre emlékszik; csak a beszélgetésen belüli
adatot használja”). A hiba nem egyetlen családra korlátozódik, de főleg F2/F3-ban (ahol a nyitó
sor egyenesen a kérdésbe ugrik, bemutatkozás nélkül) halmozódott.

**Gyökér-ok, amit a korábbi munkafolyamatban magam is megerősítettem:** a `multiturn_0063`
rekordnál a jelen kör előtt egy korábbi javítás (az „deklarált név nem használt” szkript-ellenőrzés
kielégítésére) egyszerűen hozzáfűzte a nevet az asszisztens válaszához, anélkül hogy ellenőrizte
volna, a felhasználó valaha bemutatkozott-e — ez pontosan ezt a hibamintát hozta létre, és jelzi,
hogy a hiba generálás közben szisztematikusan, nem véletlenül keletkezett több helyen.

**Javítás mind a 42 esetben:** a felhasználó nyitó sorához hozzáadtam a bemutatkozást („Szia! X
vagyok, ...” vagy „Jó napot! X vagyok, ...”), a beszélgetés további részét érintetlenül hagyva.
Ahol egy korábbi javítás (`multiturn_0063`) emiatt mesterkélt módon illesztette be a nevet egy
assistant-válasz végére, azt a természetesebb, önmagában is helyes mondatra visszaalakítottam.

## 4. Egyedi találatok (9 eset) — mindegyik javítva

| Azonosító | Hiba | Javítás |
|---|---|---|
| `multiturn_0003` | `meta.depends` turn7 téves hivatkozása (a stock-választásra [turn4] hivatkozott, miközben a szöveg a zabtejszín-választásra [turn2] utal) | `on` listát [0,4]→[0,2]-re javítottam |
| `multiturn_0023` | `meta.depends` turn9 hivatkozása alaptalan volt (a tészta pihenőideje nem függ a tejmennyiségtől) | a hivatkozás törölve |
| `multiturn_0027` | F4 (felhasználói javítás) címke alatt valójában F5-mintázat (változó kérés, „mégis inkább”/„végül úgy döntöttem” megfogalmazással, nem tényleges korrekcióval) | a két kiváltó mondatot „bocsánat, elírtam: nem X, hanem Y” típusú, valódi korrekcióra írtam át, a család- és nehézségi kvóta megmaradt |
| `multiturn_0035` | `meta.depends` turn7 hivatkozása alaptalan volt (a duplex nyomtatás nem függ a papírtípustól) | a hivatkozás törölve (a rekordnak F6-ként nem is szükséges `depends` bejegyzése) |
| `multiturn_0040` | (1) `meta.depends` turn7 téves hivatkozása (bevásárlólistára mutatott egy adóügyi kérdés helyett); (2) két, túl magabiztos adóügyi kijelentés egy „ügyintézés/pénzügy — nincs tanács” tématerületen; (3) `sensitive_area` hiányosan `false` | (1) a hivatkozás törölve; (2) mindkét mondatot átírtam, hogy NAV/adószakértőhöz irányítson, ne állítson magabiztos szabályt; (3) `sensitive_area: true` |
| `multiturn_0051` | „új **foteled** keresek” nyelvtani hiba (birtokos rag helyett tárgyeset kellene); `meta.depends` turn5 alaptalan hivatkozása | „fotelt”-re javítva; a hivatkozás törölve (a színválasz valójában az azonnal megelőző, nem egy korábbi fordulóra épül) |
| `multiturn_0056` | `meta.depends` záró turn téves hivatkozása (a vegán-fordulatra [turn8] hivatkozott, miközben a záró mondat a létszámra [turn2] utal) | `on` listát [0,8]→[0,2]-re javítottam |
| `multiturn_0060` | Ténybeli hiba: „az orvosi alkalmassági igazolás jellemzően néhány hónapig érvényes” — ellenőrizve (WebSearch, 13/1992. NM rendelet): a valóságban életkor szerint 2–10 **évig** érvényes | a mondatot a valós, életkor-függő, éves időtartamra javítottam |
| `multiturn_0073` | Logikai ellentmondás: a felhasználó első állítása (só lassítja a forrást) valójában a fizikailag **helyes** állítás volt, az asszisztens mégis korrekcióként kezelte, majd a felhasználó második állítása ennek az ellentettjére váltott indoklás nélkül | a nyitó mondatot átírtam, hogy a felhasználó a kezdetektől a téves mítoszt (a só gyorsítja a forrást) állítsa, így a teljes beszélgetés egy, következetes téves hiedelem körül forog, az F4 „téves javítás” mintának megfelelően |
| `multiturn_0077` | Ugyanaz a F4/F5 mintázat-keveredés, mint `0027`-nél | ugyanúgy „bocsánat, elírtam/pontosítanom kell: nem X, hanem Y” típusú korrekcióra írtam át |

**Egy jelentett találatot a saját, közvetlen ellenőrzésem után elvetettem:** a batch2-ellenőrző
alügynök `multiturn_0091` turn13 `depends`-bejegyzését hibásnak jelezte, de a tényleges, aktuális
szöveg közvetlen elolvasása azt mutatta, hogy a bejegyzés helyes (a záró mondat valóban mindkét
korábbi témára — sütő és vízszűrő — utal). Ezt nem javítottam, és itt dokumentálom, hogy a döntés
visszakövethető legyen.

**Két találatot megvizsgáltam, de indokolt, nem javítandó természetes hasonlóságnak ítéltem:**
`multiturn_0099`↔korábban már javított `multiturn_0048` mintázat (ez a korábbi, első auditkörben
már javítva lett) és a két változat-pár (`0053`/`0056`, `0071`/`0074`) szándékos, de nem túlzott
hasonlósága — ezekről lásd a 6. szakaszt.

## 5. Mi NEM változott

- A beszélgetések **azonosítói** (`multiturn_0001`–`0100`) és a tervezett **összetétel** (család,
  tématerület, nehézség, hossz, register, elírás) **pontosan** ugyanaz maradt, mint a javítás előtt
  — lásd a 6. szakasz táblázatát. A javítás kizárólag szöveget és (egy esetben) a `sensitive_area`
  jelzőt módosított, kvótát sosem.
- Semmilyen validátor, küszöb vagy a lezárt eszközök (MT-1/MT-3/MT-2/MT-4/MT-5) kódja nem változott;
  ezek mutációs vizsgálatát **nem** futtattam újra (ez tartalomjavítás, nem eszközváltozás).
- A 3 tervezett-változat pár és a 6 korábban azonosított, nem blokkoló MT-3 `info`-jelzés közül a
  már egyszer lezárt ügyek érintetlenek maradtak.

## 6. Összetétel a javítás után (változatlan a javítás előttihez képest)

| Szempont | Érték |
|---|---|
| Beszélgetés / üzenet / minta | 100 / **938** / **469** |
| Család | F1 15, F2 13, F3 13, F4 13, F5 11, F6 9, F7 10, F8 11, F9 5 — **pontosan a terv szerint** |
| Tématerület | mind a 10 tématerület pontosan 10-10 |
| Nehézség | easy 30, medium 50, hard 20 — **pontosan a terv szerint** |
| Register | tegező 86, magázó 14 (terv ≈85/≈15) |
| Elírás | 10 beszélgetés — **pontosan a terv szerint** |
| Érzékeny terület | **8** (a `multiturn_0040` javítás miatt 7-ről 8-ra nőtt) — pontosan a terv ≤8-as korlátján |
| Hossz (váltás) | 3:20, 4:30, 5:25, 6:15, 7:6, 8:4 — **pontosan a terv szerint** |
| Asszisztens-válasz nyitószó | legfeljebb 7,7% (a javítás két `multiturn_0040`-beli válasz nyitószavát is módosította, hogy az „a” szó a javítás után is 8% alatt maradjon) |
| Tervezett-változat pár | 3 (`g0029`, `g0053`, `g0071`), érintetlen, mindhárom tartalmilag megerősítve eltérő (lásd alább) |

A 3 változat-pár tartalmát ismét, közvetlenül elolvastam: mindhárom más ételt/eszközt, más
létszámot/korrekciót és más záró kérdést használ, nem névcsere — ez megegyezik a korábbi,
batch2-jelentésben leírtakkal, és a két ellenőrző alügynök is függetlenül megerősítette, hogy a
hasonlóságuk a szándékos mértéken belül marad.

## 7. Technikai ellenőrzés (új, visszakövethető kimenet)

| Lépés | Eredmény |
|---|---|
| **MT-1**, mindkét fájl külön | 0 hibás rekord mindkettőben, 5+13=18 figyelmeztetés — **ugyanazok**, mint a javítás előtt (a javítások nem érintették az ott jelzett szavakat) |
| **MT-1**, kombinált 100 | 0 hibás rekord, 18 figyelmeztetés |
| **MT-3**, harmadik-utáni (negyedik) futás, a kombinált 100 + a valódi 4494 soros TE-1 export ellen | **`findings_total: 0`** (nem csak 0 blokkolás); 3 csoport (a 3 deklarált pár), a 6 korábbi kizárás érvényben |
| **MT-2**, próbafelosztás (cél 80/10/10) | pontosan 80/10/10, 0 visszatartott, 0 szétvágott csoport |
| **MT-4**, dataset mód | R2: 375+48+46 minta, **100% veszteségmentes**; R1: 375+48+46 minta, 173+23+21 veszteségmentes (a csonkolás miatti, dokumentált különbség — a konkrét szám a tartalom-javítás miatt kissé eltér a korábbi 186+25+23-tól, de a mintaszám és a veszteségmentesség logikája változatlan); 0 visszatartott |
| **MT-5**, dataset mód, `--dry-run` | minden minta betöltve/kódolva/kötegelve/előrefuttatva (0 hiba, 0 visszatartott) |

Az eredmények a `data/reports/audit_evidence/mt6_batch2/` mappában az `*_audit2_*` jelölésű
fájlokban vannak (az eredeti, javítás előtti jelentések is megmaradtak, a nyomonkövethetőség
miatt).

## 8. Hossz- és szótárkorlát

- A szótár **kizárólag** a train/R2 mintákból épült: **79** megfigyelt karakter (+UNK+PAD=81),
  **ugyanannyi**, mint a javítás előtt.
- Ismeretlen (train-szótáron kívüli) karakter-előfordulás: **9**, kizárólag a validation részben,
  csak a nyitó/záró zárójel (`(`, `)`) miatt — **megegyezik** a javítás előtti állapottal, a
  szótárat nem bővítettem visszamenőleg.
- A minták **100%-a** (minden részben, R1-ben és R2-ben is) **továbbra is** meghaladja a jelenlegi
  betanított modell 64 karakteres kontextusát — ezt a korlátot a javítás során **nem** használtam
  fel a beszélgetések rövidítésére; minden javítás tartalmi, nem hosszcsökkentő volt.

## 9. Jóváhagyási állapotok

`split_approved`, `content_verified`, `training_ready`: **változatlanul `false`** a teljes
láncon át, minden jelentésben. Ez a feladat AI-alapú tartalmi ellenőrzést és javítást engedélyezett
— tanítást, modellmódosítást vagy új beszélgetéscsomag generálását **nem**.

## 10. Következő lépés

A terv 6. szakasza szerinti **független (nem AI, lehetőleg emberi) tartalmi átolvasás** az első
100 beszélgetésre **még nem történt meg** — ez a soron következő, önállóan jóváhagyandó feladat,
és erre épül a felosztás elfogadása, a harmadik batch és bármilyen tanítási előkészület. A jelen
kör (két friss AI-alügynök + saját közvetlen ellenőrzés) **nem helyettesíti** ezt, csak csökkenti a
független átolvasás során várhatóan talált hibák számát.
