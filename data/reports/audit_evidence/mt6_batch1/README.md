# MT-6 első batch (claude_multiturn_0001_0050) — bizonyítékok

Ez a mappa a 7. csomag (`multiturn`) **első, valódi, datasetbe szánt** 50 beszélgetésének teljes
technikai ellenőrzési láncát dokumentálja: MT-1 (formátum-/szűrő-ellenőrzés) → MT-3 (duplikáció, a
valódi 4494 soros TE-1 export ellen) → MT-2 (próbafelosztás) → MT-4 (renderelés és export) → MT-5
(betöltési száraz futás). A `data/train/` alatti tényleges futás-mappák (munka-könyvtárak, a projekt
szabálya szerint nem verziókövetettek) ide másolt jelentései adják a végleges, megőrzött bizonyítékot.

| Fájl | Mi ez |
|---|---|
| `mt1_validate_report.json` | MT-1 teljes riport: 50/50 rekord `turns-validált`, 0 hibás, 5 figyelmeztetés (lásd lent) |
| `mt3_dedupe_report.json` | MT-3 riport: a batch önmagában és a valódi TE-1 export (4494 sor) ellen, 0 találat |
| `mt2_split_manifest.json` | MT-2 **próbafelosztás** (40/5/5 cél, nem a végleges 800/100/100) manifestje |
| `mt4_export_manifest.json` | MT-4 export manifest (`data_kind: dataset`, `fixture: false`, R1+R2 renderelés) |
| `mt5_dryrun_report.json` | MT-5 száraz futás riportja (betöltés, kódolás, kötegelés, előrefutás, hosszstatisztika) |

## Legfontosabb számok

- **50 beszélgetés, 326 üzenet, 163 tanítási minta** (50 első fordulós, 113 előzmény-függő).
- Család: F1 8, F2 6, F3 7, F4 6, F5 6, F6 4, F7 5, F8 5, F9 3 (pontosan a tervezett arány, lásd a fő jelentést).
- Tématerület: mind a 10 tématerület pontosan 5-5 beszélgetéssel.
- Nehézség: easy 16, medium 24, hard 10.
- Register: tegező 44, magázó 6.
- Hossz (váltás): 3 váltás 39, 4 váltás 9, 5 váltás 2 (a terv szerinti hosszabb eloszlástól eltér, dokumentálva a fő jelentésben).
- 27 beszélgetésben van legalább egy ≥2 mélységű előzmény-hivatkozás; 34 beszélgetés kombinál legalább két készséget.
- 1 tervezett-változat pár (`multiturn_0029` és `multiturn_0032`, közös `split_group: g0029`, eltérő névvel/számokkal).
- Asszisztens-válasz nyitószavak: egyik sem haladja meg a 7,4%-ot (a terv szerinti ≤8% korlát teljesül).

## MT-1 — 5 figyelmeztetés, mind átolvasva

A névfelismerés **biztonsági háló, nem bizonyíték** (lásd `docs/MULTITURN_FORMAT.md` 9. szakasz): mondat
közbeni, nem jóváhagyott/tiltott listás nagybetűs szavakat jelez át olvasásra.
- `multiturn_0022`: **„Bécsbe”** (2×) — a Bécs városnév nincs a névtár `allowed_proper_nouns` listáján
  (csak magyar városok szerepelnek ott); nem személy neve, nem érzékeny adat. **Átolvasva, ártalmatlan.**
- `multiturn_0025`: **„Ön”** (3×) — a magázó regiszter kötelező, nagybetűs formális névmása, nem személynév.
  **Átolvasva, ártalmatlan.**

## MT-3 — 0 találat a batchen belül és a valódi korpusz ellen

A friss TE-1 export (`data/train/te1_export/export_20260930T143131Z`, 4500 sor beolvasva, 6 kizárva, 4494
exportálva) ellen és a batch 50 rekordja egymás között: **0 duplikáció-jelzés, 0 blokkolt rekord**, 49
csoport (1 kettes létszámú — a tervezett változat-pár —, a többi egyedi). Ez **nem** bizonyítja tartalmi
egyediséget, csak azt, hogy az ellenőrző nem talált blokkoló jelzést (lásd az eszköz saját figyelmeztetését
a riportokban).

## MT-2 — próbafelosztás (NEM a végleges 800/100/100)

40/5/5 cél (a végleges 1000-es csomag 800/100/100 arányával egyező, 50-re vetítve), pontosan teljesítve:
40/5/5 beszélgetés, 0 visszatartott, 0 szétvágott csoport (a tervezett-változat pár együtt maradt a
train részben). **Ez technikai próba, nem a csomag végleges felosztása.**

## MT-4 — export (dataset mód, valódi adat)

R2 (teljes előzmény): 131+16+16 minta, **100% veszteségmentes** minden részben. R1 (futásidő-hű, a
`memory.build_prompt_context` szerint csak 1 előző váltás): 131+16+16 minta, ebből 81+10+10 veszteségmentes
— a többi mintánál az R1 csonkolása miatt korábbi előzmény vész el (ez **dokumentált, várt** különbség
R1 és R2 között, nem hiba). 0 visszatartott, nem ábrázolható rekord.

## MT-5 — száraz futás (dataset mód, betöltés/kódolás/kötegelés/előrefutás, NEM tanítás)

Minden minta (train/validation/test, R1 és R2 is) sikeresen betöltődött, kódolódott, kötegelődött és
előrefutott egy friss, tanítatlan próba-modellel (0 hiba). Szótár: 70 megfigyelt karakter (+UNK+PAD=72),
kizárólag a train/R2 mintákból. **A minták 100%-a — R1-ben és R2-ben is, minden részben — meghaladja a
jelenlegi betanított modell 64 karakteres kontextusát**; a legrövidebb minta is 128 karakter (lásd a fő
jelentés hossz-/kompatibilitási szakaszát). 6 ismeretlen (train-szótáron kívüli) karakter-előfordulás a
validation/test mintákban — egy nagybetűs „Ö” (a `multiturn_0025` „Ön” szavából, ami a próbafelosztásban
a test részbe került, és a 40 train-beszélgetés egyikében sem fordult elő nagybetűsen) — dokumentált,
kisminta-jelenség, nem hiba. Kilépési kód 1 (**EXIT_ATTENTION** — figyelmet kér, nem hiba) pontosan emiatt
a figyelmeztetés miatt. A `training_ready`/`content_verified`/`split_approved` mezők a jelentésben és a
forrás-exportban is változatlanul `false`.
