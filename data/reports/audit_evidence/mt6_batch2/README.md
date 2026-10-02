# MT-6 második batch (claude_multiturn_0051_0100) — bizonyítékok

**2. kör (2026-10-02, AI-alapú teljes tartalmi felülvizsgálat, mindkét batch):** a `*_audit2_*`
jelölésű fájlok ennek a körnek az eredményei, a kombinált 100 + a valódi TE-1 export ellen. A
teljes jelentés: `data/reports/mt6_batch_audit2_report.md`. A jelen README és az alábbi 1. kör
leírása az eredeti (2026-10-02 korábbi, első) batch2-jelentés állapotát dokumentálja; a tartalom
(mindkét batchben) azóta tartalmilag javult, lásd az audit2-jelentést a pontos változásokért.

Ez a mappa a 7. csomag (`multiturn`) **második, valódi, datasetbe szánt** 50 beszélgetésének
(`multiturn_0051`–`0100`) teljes technikai ellenőrzési láncát dokumentálja, a kombinált 100
(`multiturn_0001`–`0100`) ellen is: MT-1 (formátum-/szűrő-ellenőrzés, batch2 önmagában és a
kombinált 100-on) → MT-3 (duplikáció, a kombinált 100 + a valódi 4494 soros TE-1 export ellen,
harmadik, javított futás) → MT-2 (próbafelosztás) → MT-4 (renderelés és export) → MT-5 (betöltési
száraz futás). A `data/train/` alatti tényleges futás-mappák (munka-könyvtárak, a projekt szabálya
szerint nem verziókövetettek) ide másolt jelentései adják a végleges, megőrzött bizonyítékot.

| Fájl | Mi ez |
|---|---|
| `mt1_validate_batch2only_report.json` | MT-1 riport: csak a `claude_multiturn_0051_0100_clean.jsonl`, 0 hibás, 13 figyelmeztetés |
| `mt1_validate_combined100_report.json` | MT-1 riport: a kombinált 100 (mindkét clean fájl), 0 hibás, 18 figyelmeztetés összesen |
| `mt3_dedupe_combined100_report.json` | MT-3 riport (`full100_v2` futás): a kombinált 100 + a valódi TE-1 export ellen, **0 találat** |
| `mt2_split_trial_manifest.json` | MT-2 **próbafelosztás** (80/10/10 cél, nem a végleges 800/100/100) manifestje a kombinált 100-on |
| `mt4_export_trial_manifest.json` | MT-4 export manifest (`data_kind: dataset`, `fixture: false`, R1+R2 renderelés) a próbafelosztásra |
| `mt5_dryrun_trial_report.json` | MT-5 száraz futás riportja a próbafelosztás exportjára |

## Miért egy harmadik MT-3 futás

Az első MT-3 futás (a batch2 első, még nem javított tartalmára) **4 blokkolt rekordot** adott: két
`probable_paraphrase_variant` (`review`) jelzés `multiturn_0025`↔`multiturn_0075` és
`multiturn_0030`↔`multiturn_0080` között, mindkét oldali rekordot blokkolva. Ennek oka: a batch2
két rekordja túl hasonló forgatókönyv-vázat használt az első batch megfelelő rekordjaihoz
(időpont-korrekció utáni logisztika; két ügyintézési hiba egy időpontba vonása). A felhasználó
kifejezett szabálya szerint az első 50 **nem módosítható** — ezért `multiturn_0075`-öt (új
forgatókönyv: előadás-dátum pontosítás + PDF-fájl + pendrive-mentés) és `multiturn_0080`-at (új
forgatókönyv: egyéni vállalkozásból kft-re váltás, ügyvédi segítség) **csak a batch2 oldalon**
teljesen átírtam.

A második MT-3 futás így 0 blokkolt rekordot adott, de 10, nem blokkoló (`info`) közeli hasonlóságot
jelzett a kombinált 100-on. Ebből 6-ot (`multiturn_0064`, `multiturn_0091`, `multiturn_0092` két
helyen, `multiturn_0097`, `multiturn_0099`) tartalmilag indokoltnak ítéltem a javításra (egy-egy
mondat szó szerinti vagy közel szó szerinti ismétlődése a megfelelő batch1-rekordhoz képest), és
átírtam — mind csak a batch2 oldalon. `multiturn_0100` a `multiturn_0050`-hez képest egész
beszélgetés szintű `near_variant` jelzést kapott (0,844, plusz egy pontos szövegegyezés egy
mondatban); ezt a rekordot teljesen új forgatókönyvre (hivatali határidő-bizonytalanság a
cégbejegyzési illeték helyett) írtam át, az F9/ugyintezes/hard/magázó kvóta-helyén belül.
`multiturn_0057`↔`multiturn_0007` (0,95, hasonló zárómondat-szerkezet) és `multiturn_0099`↔`0048`
(0,90, azonos follow-up kérdés egy szó eltéréssel) is ebbe a körbe tartozott.

A harmadik, jelen mappában dokumentált futás: **`findings_total: 0`** — nem csak 0 blokkolás, hanem
0 bármilyen szintű jelzés. 3 csoport maradt 2 tagú (a 3 szándékosan deklarált változat-pár), mindegyik
kizárólag a `declared_group` él miatt, az MT-3 saját hasonlóság-elemzése **nem** talált köztük
semmilyen duplikáció-jelzést — ez igazolja, hogy a pár-deklaráció nem írta felül az MT-3 döntését,
hanem a párok valóban, függetlenül is különböznek. `variant_share: 0.06`, a terv 0,15-ös korlátja
alatt.

## Legfontosabb számok

- Batch2 önmagában: **50 beszélgetés, 470 üzenet, 235 tanítási minta** (50 első fordulós, 185
  előzmény-függő).
- Kombinált 100: **938 üzenet, 469 tanítási minta** — pontosan a terv 7. szakaszának száma.
- Család (kombinált): F1 15, F2 13, F3 13, F4 13 (3 téves javítás), F5 11, F6 9, F7 10, F8 11, F9 5
  — **pontosan** a terv szerint.
- Tématerület (kombinált): mind a 10 tématerület **pontosan** 10-10 beszélgetéssel.
- Nehézség (kombinált): easy 30, medium 50, hard 20 — **pontosan** a terv szerint.
- Register (kombinált): tegező 86, magázó 14 (terv: ≈85/≈15).
- Elírás (kombinált): 10 beszélgetés (terv: ≈10). Érzékeny terület (kombinált): 7 (terv: legfeljebb 8).
- Hossz (váltás, kombinált): 3 váltás 20, 4 váltás 30, 5 váltás 25, 6 váltás 15, 7 váltás 6, 8 váltás 4
  — **pontosan** a terv szerinti 469 váltás.
- 3 tervezett-változat pár (`g0029`, `g0053`, `g0071`), mindegyik eltérő trenírozott készséggel és
  témával, nem névcsere.
- Asszisztens-válasz nyitószavak (kombinált 100): egyik sem haladja meg a 7,7%-ot.

## MT-1 — 18 figyelmeztetés a kombinált 100-on, mind átolvasva

Mind a 18 figyelmeztetés `capitalized_token_review` kód: mondat közbeni nagybetűs szó, amely vagy
helynév (Bécs, Visegrád, London, Róma, Kékes), vagy márka/UI-elem (Album, Indítás, Tűztorony), vagy
egy történelmi személy neve (Newton, egy mértékegység-eredet-kérdésben). Egyik sem személyes adat,
egyik sem a névtár által tiltott név. Átolvasva, ártalmatlan.

## MT-2 — próbafelosztás (NEM a végleges 800/100/100)

80/10/10 cél, pontosan teljesítve: 80/10/10 beszélgetés, 0 visszatartott, 0 szétvágott csoport (a 3
deklarált pár egyben maradt).

## MT-4 — export (dataset mód, valódi adat)

R2 (teljes előzmény): 375+48+46 minta, **100% veszteségmentes** minden részben. R1 (futásidő-hű):
375+48+46 minta, ebből 186+25+23 veszteségmentes — a többinél az R1 csonkolása miatt korábbi
előzmény vész el (dokumentált, várt különbség). 0 visszatartott.

## MT-5 — száraz futás (dataset mód)

Minden minta sikeresen betöltődött, kódolódott, kötegelődött és előrefutott (0 hiba, 0 visszatartott).
Szótár: 79 megfigyelt karakter (+UNK+PAD=81), kizárólag a train/R2 mintákból. **A minták 100%-a —
R1-ben és R2-ben is, minden részben — meghaladja a jelenlegi betanított modell 64 karakteres
kontextusát.** 9 ismeretlen (train-szótáron kívüli) karakter-előfordulás, kizárólag a validation
részben, két karakter miatt: a nyitó- és záró-zárójel (`(`, `)`), amelyek a train-beszélgetések
egyikében sem fordultak elő. Kisminta-jelenség, nem hiba; a szótár nem bővült visszamenőleg. A
`training_ready`/`content_verified`/`split_approved` mezők változatlanul `false`.
