# Nexora Zero - UI/UX redesign backlog

Ez a dokumentum a **jövőbeli, még nem elkezdett** UI/UX redesign
követelményeit gyűjti össze. Nem terv, nem ütemezés - egy jegyzék arról,
mit kell figyelembe venni, amikor egyszer, egy KÜLÖN kör keretében sor
kerül a felület újratervezésére.

**Ez a dokumentum önmagában nem indít, nem engedélyez és nem ütemez be
semmilyen kódmódosítást.** Amíg egy jövőbeli kör kifejezetten nem
hivatkozik rá és nem kér munkát rá, a benne felsorolt pontok csak
jegyzett szándékok, nem feladatok.

---

## 1. Alapállítás

A jelenlegi (v1.7.2-ig kialakult) webes felület **fejlesztői/prototípus
felület**, NEM végleges termék-UI. Funkcionálisan stabil és tesztelt
(lásd a v0.8-v1.7 regressziós láncot), de a vizuális/UX kialakítás
ideiglenes, gyors iterációkból nőtt ki - nem egy tudatos design-rendszer
eredménye.

---

## 2. Célkép: ChatGPT-szerű elrendezés

A későbbi redesign célja egy ismerős, modern chat-app elrendezés:

- **Bal oldali sidebar**, benne:
  - "Új csevegés" indítása
  - **Képek** (feltöltés/kezelés - lásd v1.7.2 "+" menü "hamarosan"
    placeholdere, ez lenne a végleges hely)
  - **Fájlok** (a jelenlegi "Fájlok (részletes)" panel ide költözne)
  - **Bővítmények**
  - **Később**: videó, kép-szerkesztő, videó-szerkesztő modulok
- **Középen**: önálló, fókuszált beszélgetési ablak (a chat-box a mai
  formájánál nagyobb hangsúlyt kapna, kevesebb elterelő elem mellette)

---

## 3. A felső gombsor (Memória / Tudásbázis / Fájlok) nem végleges

A jelenlegi fejléc-gombsor ("🧠 Memória", "📚 Tudásbázis", "📎 Fájlok
(részletes)") egy ideiglenes, funkcionális megoldás. A redesign során
ezeknek a sidebar-ba vagy egy beállítások/panel-rendszerbe kell
költözniük - a jelenlegi vízszintes gombsor-elrendezés nem cél.

---

## 4. "Fájl-kontextus" jelzés - túl nagy, feltűnő buborékok

A jelenlegi indikátor-chipek (pl. "📎 fájl-kontextus", "📄 fájl-alapú
válasz", "🧠 rövid memória" stb.) nagy, jól látható buborékokként
jelennek meg minden AI-válasz alatt. Ez működik, de vizuálisan
túlsúlyos. A redesign céja:

- **Kicsi, diszkrét ikonok** vagy egy apró állapotsáv, nem teljes méretű
  buborékok
- Esetleg hover/tooltip-alapú részletezés a jelenlegi mindig-látható
  szöveg helyett

---

## 5. Vizuális nyelv (szín/tipográfia/fejléc) nem végleges

A jelenlegi fekete/kék/arany színvilág, a buborék-stílus (`.bubble`,
`.message.ai`/`.message.user`), a betűtípus-választás, és a "Nexora
Zero" fejléc-elrendezés mind **ideiglenes**, gyors iterációként
alakultak ki (lásd v1.5 és v1.7.2 körök). Egyik elem sem tekintendő
végleges márka-/design-döntésnek.

---

## 6. Célkitűzés

A redesign végső célja egy **letisztult, prémium, modern AI-app
megjelenés** - összemérhető minőségben a piacon megszokott AI-chat
felületekkel (elrendezés, tipográfia, szín- és térhasználat
tekintetében), a projekt saját, nulláról tanított karakter-alapú modell
jellegét (kis, kísérleti, nem ChatGPT-szintű) őszintén kommunikálva.

---

## 7. Sorrend: funkcionalitás előbb, UI-redesign külön körben

**Fontos, végrehajtási szabály:** amíg ez a dokumentum érvényben van,
a funkcionalitás (biztonság, stabilitás, új képességek - pl. a
tervezett v1.8 Nexora Build System) élvez elsőbbséget. A UI-redesign
NEM ezekkel párhuzamosan, hanem egy **külön, kifejezetten erre
dedikált körben** történjen, csak azután, hogy a mögöttes
funkcionalitás már stabil.

---

*Ez a dokumentum jegyzék, nem munkaterv. Létrehozásának oka: a v1.7.2
"user-test fixes" kör során világossá vált, hogy a jelenlegi UI csak
átmeneti megoldás - ezt itt rögzítjük, hogy a döntés és az indoklás ne
vesszen el, de a tényleges redesign-munka ütemezése egy későbbi,
explicit user-döntés.*
