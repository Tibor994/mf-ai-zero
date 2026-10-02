# MT-6 első batch (claude_multiturn_0001_0050) — bizonyítékok (2. változat, a hosszmegoszlás javítása után)

Ez a mappa a 7. csomag (`multiturn`) **első, valódi, datasetbe szánt** 50 beszélgetésének teljes
technikai ellenőrzési láncát dokumentálja: MT-1 (formátum-/szűrő-ellenőrzés) → MT-3 (duplikáció, a
valódi 4494 soros TE-1 export ellen) → MT-2 (próbafelosztás) → MT-4 (renderelés és export) → MT-5
(betöltési száraz futás). A `data/train/` alatti tényleges futás-mappák (munka-könyvtárak, a projekt
szabálya szerint nem verziókövetettek) ide másolt jelentései adják a végleges, megőrzött bizonyítékot.

**Ez a verzió a felhasználó 2026-10-02-i javítási kérésére készült**: az első kiadás (lásd a `git log`-ban
`v1.13.25-mt6-batch1`) hosszmegoszlása (váltásszám: 39/9/2/0/0/0) jelentősen eltért a tervezett
3/4/5/6/7/8 váltásos arányoktól (10/15/13/7/3/2, az első 100-as terv dokumentáltan felére kerekítve). A
javítás **tartalmilag, valódi többlépéses/pontosító/korrekciós/előzmény-használó fordulókkal** bővítette
39 rekordot — nem üres köszönésekkel vagy ismétléssel.

| Fájl | Mi ez |
|---|---|
| `mt1_validate_report.json` | MT-1 teljes riport: 50/50 rekord `turns-validált`, 0 hibás, 5 figyelmeztetés (lásd lent) |
| `mt3_dedupe_report.json` | MT-3 riport: a batch önmagában és a valódi TE-1 export (4494 sor) ellen, 0 találat |
| `mt2_split_manifest.json` | MT-2 **próbafelosztás** (40/5/5 cél, nem a végleges 800/100/100) manifestje |
| `mt4_export_manifest.json` | MT-4 export manifest (`data_kind: dataset`, `fixture: false`, R1+R2 renderelés) |
| `mt5_dryrun_report.json` | MT-5 száraz futás riportja (betöltés, kódolás, kötegelés, előrefutás, hosszstatisztika) |

## Legfontosabb számok (a javítás után)

- **50 beszélgetés, 468 üzenet, 234 tanítási minta** (50 első fordulós, 184 előzmény-függő).
- Család: F1 8, F2 6, F3 7, F4 6, F5 6, F6 4, F7 5, F8 5, F9 3 (**pontosan** a terv szerint).
- Tématerület: mind a 10 tématerület **pontosan** 5-5 beszélgetéssel.
- Nehézség: easy 15, medium 25, hard 10 (**pontosan** a terv szerint — `multiturn_0042` easy→medium, mert a kibővített tartalom valódi, nagyobb összetettséget kapott).
- Register: tegező 43, magázó 7 (**pontosan** a terv szerint — `multiturn_0030` tegező→magazo, mert a hivatalos ügyintézési téma a batch többi magázó, ügyintézés-témájú rekordjával összhangban formálisabb regisztert indokol).
- **Hossz (váltás): 3 váltás 10, 4 váltás 15, 5 váltás 13, 6 váltás 7, 7 váltás 3, 8 váltás 2 — pontosan a kért megoszlás.**
- 35 beszélgetésben van legalább egy ≥2 mélységű előzmény-hivatkozás; 34 beszélgetés kombinál legalább két készséget.
- 1 tervezett-változat pár (`multiturn_0029` és `multiturn_0032`, közös `split_group: g0029`, eltérő névvel, létszámmal, étlappal és kiegészítő kérdésekkel — nem puszta névcsere).
- Asszisztens-válasz nyitószavak: egyik sem haladja meg a 7,7%-ot (a terv szerinti ≤8% korlát a bővítés után is teljesül, egy második átdolgozási kör után).

## Módosított rekordok (39 db) és az ok

A javítás **39 rekord** `turns` tartalmát bővítette 1–4 új, valódi feladatot végző fordulóval (pontosítás,
korábbi feltétel/adat felhasználása, javítás utáni további lépés, többlépéses feladat folytatása, vagy a
család szerinti más releváns készség), és ennek megfelelően a `meta.depends` mezőt is újraszámolta. A
pontos azonosítók és a hozzáadott váltások száma:

| Azonosító | Hozzáadott váltás | Azonosító | Hozzáadott váltás | Azonosító | Hozzáadott váltás |
|---|---|---|---|---|---|
| multiturn_0001 | +1 | multiturn_0017 | +2 | multiturn_0033 | +1 |
| multiturn_0002 | +1 | multiturn_0020 | +1 | multiturn_0035 | +1 |
| multiturn_0003 | +1 | multiturn_0022 | +1 | multiturn_0038 | +3 |
| multiturn_0004 | +2 | multiturn_0023 | +2 | multiturn_0039 | +3 |
| multiturn_0006 | +1 | multiturn_0024 | +2 | multiturn_0040 | +3 |
| multiturn_0007 | +2 | multiturn_0025 | +1 | multiturn_0041 | +2 |
| multiturn_0008 | +1 | multiturn_0026 | +1 | multiturn_0042 | +4 (+ nehézség easy→medium) |
| multiturn_0009 | +1 | multiturn_0027 | +4 | multiturn_0043 | +1 |
| multiturn_0010 | +2 | multiturn_0028 | +1 | multiturn_0044 | +2 |
| multiturn_0011 | +1 | multiturn_0029 | +2 | multiturn_0045 | +4 |
| multiturn_0012 | +2 | multiturn_0030 | +1 (+ register tegező→magazo) | multiturn_0046 | +2 |
| multiturn_0013 | +1 | multiturn_0031 | +2 | multiturn_0047 | +3 |
| multiturn_0014 | +3 | multiturn_0032 | +2 | | |
| multiturn_0015 | +1 | | | | |

(11 rekord — `multiturn_0005, 0016, 0018, 0019, 0021, 0034, 0036, 0037, 0048, 0049, 0050` — **változatlan**
maradt: ezek már a tervezett hosszon voltak, vagy a család definíciója szerint helyesen rövidek, teljes
ívű beszélgetések.) Minden módosított rekord **azonosítója megmaradt** (`multiturn_0001`–`0050`,
folytonosan), a tartalom bővült, nem íródott át gyökeresen.

## MT-1 — 5 figyelmeztetés, mind átolvasva (ugyanaz, mint az első kiadásban)

- `multiturn_0022`: **„Bécsbe”** (2×) — a Bécs városnév nincs a névtár `allowed_proper_nouns` listáján; nem személy neve. **Átolvasva, ártalmatlan.**
- `multiturn_0025`: **„Ön”** (3×) — a magázó regiszter kötelező, nagybetűs formális névmása. **Átolvasva, ártalmatlan.**

## MT-3 — 0 találat a batchen belül és a valódi korpusz ellen

A friss TE-1 export (4500 sor beolvasva, 6 kizárva, 4494 exportálva) ellen és a batch 50 rekordja egymás
között: **0 duplikáció-jelzés, 0 blokkolt rekord**, 49 csoport (1 kettes létszámú — a tervezett
változat-pár —, a többi egyedi).

## MT-2 — próbafelosztás (NEM a végleges 800/100/100)

40/5/5 cél, pontosan teljesítve: 40/5/5 beszélgetés, 0 visszatartott, 0 szétvágott csoport.

## MT-4 — export (dataset mód, valódi adat)

R2 (teljes előzmény): 185+22+27 minta, **100% veszteségmentes** minden részben. R1 (futásidő-hű): 185+22+27
minta, ebből 85+10+10 veszteségmentes — a többinél az R1 csonkolása miatt korábbi előzmény vész el
(dokumentált, várt különbség). 0 visszatartott.

## MT-5 — száraz futás (dataset mód)

Minden minta sikeresen betöltődött, kódolódott, kötegelődött és előrefutott (0 hiba). Szótár: 72 megfigyelt
karakter (+UNK+PAD=74), kizárólag a train/R2 mintákból. **A minták 100%-a — R1-ben és R2-ben is, minden
részben — meghaladja a jelenlegi betanított modell 64 karakteres kontextusát.** 39 ismeretlen
(train-szótáron kívüli) karakter-előfordulás a validation/test mintákban, 4 megfigyelt karakter miatt:
nagybetűs **Á** és **Ö** (olyan szavak eleje, amelyek a 40 train-beszélgetés egyikében sem fordultak elő
pontosan ott, nagybetűsen), illetve a **0** és **1** számjegy (a validation/test részbe került egy-két
olyan beszélgetés — pl. évszámot vagy méretet tartalmazó —, amelynek számjegyei a train-mintákban nem
pontosan ugyanazok). Mind kisminta-jelenség, nem hiba. Kilépési kód 1 (**EXIT_ATTENTION**) pontosan emiatt
a figyelmeztetés miatt. A `training_ready`/`content_verified`/`split_approved` mezők változatlanul `false`.
