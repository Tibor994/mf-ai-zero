# -*- coding: utf-8 -*-
"""6. csomag (uncertainty_source_request) teljes completion audit-futtato. Csak olvas, nem ir a repoba.
Hasznalat: python audit_pkg.py <fazis>   fazis: struct | pairs | style | all
Kimenet: audit_out/<fazis>.txt (+ audit_out/pairs.json). A pairs fazis szakaszolt (chunkonkent ment, ujrainditasnal kihagyja a keszeket)."""
import collections, difflib, glob, json, multiprocessing as mp, os, re, sys, time

REPO = r"C:\Users\Lenovo\OneDrive\Dokumentumok\MF-AI-Zero"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "audit_out")
PART = os.path.join(OUT, "pair_parts")
os.makedirs(PART, exist_ok=True)
sys.path.insert(0, os.path.join(REPO, "src"))
sys.path.insert(0, os.path.join(REPO, "tools"))
PKG = "uncertainty_source_request"
MODES = ["valtozo_adat", "forras_nelkul_nem_tudhato", "pontositas_kell", "altalanos_valasz_ellenorzessel", "kitalalas_elutasitasa", "ellenorzesi_ut", "kontraszt_magabiztos"]
PLUS = {"hibas_elofeltevesjavitas", "igaz_elofeltevesmegerosites", "reszben_igaz_elofeltevespontositas"}
MARK = ["magyar", "instruction_core", "bizonytalansag", "forraskeres", "nem_kamuzik"]
FIELDS9 = ["id", "category", "instruction", "input", "output", "tags", "difficulty", "quality_notes", "source"]


def load_all():
    rows = []
    for f in sorted(glob.glob(os.path.join(REPO, "data", "clean", "*.jsonl"))):
        for n, l in enumerate(open(f, encoding="utf-8"), 1):
            if l.strip():
                r = json.loads(l)
                rows.append((os.path.basename(f), n, r))
    return rows


def T(r):
    ins = (r.get("instruction") or "").strip()
    inp = (r.get("input") or "").strip() if isinstance(r.get("input"), str) else ""
    t = "%s || %s" % (ins, inp)
    return t if t.strip(" |") else ""


GETTERS = {
    "instruction||input": lambda r: T(r),
    "output~output": lambda r: (r.get("output") or "").strip(),
    "instruction~instruction": lambda r: (r.get("instruction") or "").strip(),
    "instruction~input": lambda r: (r.get("instruction") or "").strip(),   # A oldal
    "output~input": lambda r: (r.get("output") or "").strip(),             # A oldal
}
GETTERS_B = dict(GETTERS)
GETTERS_B["instruction~input"] = lambda r: (r.get("input") or "").strip() if isinstance(r.get("input"), str) else ""
GETTERS_B["output~input"] = GETTERS_B["instruction~input"]

G = {}


def init():
    allr = load_all()
    G["all"] = allr
    G["pkg"] = [i for i, (fn, n, r) in enumerate(allr) if r.get("category") == PKG]
    G["txt"] = {}
    G["cnt"] = {}
    for k in GETTERS:
        A = [GETTERS[k](r) for _, _, r in allr]
        B = [GETTERS_B[k](r) for _, _, r in allr]
        G["txt"][k] = (A, B)
        G["cnt"][k] = ([collections.Counter(x) for x in A], [collections.Counter(x) for x in B])


def pair_ratio(a, b, ca, cb, th):
    la, lb = len(a), len(b)
    if la < 6 or lb < 6:
        return None
    if 2.0 * min(la, lb) / (la + lb) < th:
        return None
    if 2.0 * sum((ca & cb).values()) / (la + lb) < th:
        return None
    r = difflib.SequenceMatcher(None, a, b).ratio()
    return r if r >= th else None


def do_chunk(args):
    scope, s, e, th = args
    out = os.path.join(PART, "%s_%s_%05d_%05d.json" % (scope, str(th).replace(".", ""), s, e))
    if os.path.exists(out):
        return out, True
    pk = G["pkg"][s:e]
    n = len(G["all"])
    is_pkg = set(G["pkg"])
    hits = collections.defaultdict(list)
    for j in pk:                       # "kesobbi" oldal = csomag sor
        for k in GETTERS:
            A, B = G["txt"][k]
            CA, CB = G["cnt"][k]
            a, ca = A[j], CA[j]
            if not a:
                continue
            if scope == "internal":
                cand = [i for i in G["pkg"] if i < j]
            else:  # other: a csomagon kivuli sorok
                cand = [i for i in range(n) if i not in is_pkg]
            for i in cand:
                b = B[i]
                if not b:
                    continue
                r = pair_ratio(a, b, ca, CB[i], th)
                if r is not None:
                    hits[k].append([G["all"][j][2]["id"], G["all"][i][2]["id"], round(r, 4)])
    json.dump(hits, open(out, "w", encoding="utf-8"), ensure_ascii=False)
    return out, False


def run_pairs(scope, th, cs=100):
    init()
    m = len(G["pkg"])
    chunks = [(scope, s, min(s + cs, m), th) for s in range(0, m, cs)]
    t0 = time.time()
    with mp.Pool(max(1, mp.cpu_count() - 1), initializer=init) as pool:
        for i, (out, skipped) in enumerate(pool.imap_unordered(do_chunk, chunks), 1):
            print("[%s th=%s %d/%d] %s %s %.0fs" % (scope, th, i, len(chunks), os.path.basename(out), "(kesz volt)" if skipped else "", time.time() - t0), flush=True)


def collect(scope, th):
    res = collections.defaultdict(list)
    for f in sorted(glob.glob(os.path.join(PART, "%s_%s_*.json" % (scope, str(th).replace(".", ""))))):
        for k, v in json.load(open(f, encoding="utf-8")).items():
            res[k] += v
    return res


def struct():
    allr = load_all()
    P = [(fn, n, r) for fn, n, r in allr if r.get("category") == PKG]
    o = open(os.path.join(OUT, "struct.txt"), "w", encoding="utf-8")
    W = lambda *a: print(*a, file=o, flush=True)
    W("KORPUSZ osszes sor:", len(allr), "| kategoria:", dict(collections.Counter(r["category"] for _, _, r in allr)))
    W("CSOMAG sorok:", len(P), "| fajlok:", dict(collections.Counter(fn for fn, _, _ in P)))
    ids = [r["id"] for _, _, r in P]
    exp = ["%s_%04d" % (PKG, i) for i in range(1, 1001)]
    W("azonositok 0001-1000 folytonos es egyedi, fajl-sorrendben:", ids == exp, "| egyedi:", len(set(ids)), "| hianyzo:", sorted(set(exp) - set(ids))[:5], "| extra:", sorted(set(ids) - set(exp))[:5])
    bad = []
    for fn, n, r in P:
        ok = list(r.keys()) == FIELDS9 and all(isinstance(r[k], str) for k in ("id", "category", "instruction", "input", "output", "difficulty", "quality_notes", "source")) and isinstance(r["tags"], list) and all(isinstance(t, str) for t in r["tags"])
        if not ok or r["source"] != "synthetic_claude_magyar" or r["difficulty"] not in ("easy", "medium", "hard"):
            bad.append(r["id"])
    W("9 mezos sema (mezosorrend, tipusok, source, difficulty enum) hibas sorok:", bad)
    W("kotelezo 5 jelolo-tag az elso 5 helyen minden sorban:", all(r["tags"][:5] == MARK for _, _, r in P))
    W("tags[5] mod ervenyes:", all(r["tags"][5] in MODES for _, _, r in P), "| mod-eloszlas:", dict(collections.Counter(r["tags"][5] for _, _, r in P)))
    W("tags[6] ASCII snake_case:", all(re.fullmatch(r"[a-z0-9_]+", r["tags"][6]) for _, _, r in P))
    kinds = collections.Counter(r["tags"][6] for _, _, r in P)
    W("tags[6] egyedi ertekek:", len(kinds), "/ 1000 | ismetlodok:", {k: v for k, v in kinds.items() if v > 1})
    extra = collections.Counter(t for _, _, r in P for t in r["tags"][7:])
    W("tags[7:] (plusz-cimkek):", dict(extra), "| nem engedelyezett plusz-cimke:", [t for t in extra if t not in PLUS])
    W("plusz-cimke csak kontraszt-soron:", all((not r["tags"][7:]) or r["tags"][5] == "kontraszt_magabiztos" for _, _, r in P))
    W("nehezseg:", dict(collections.Counter(r["difficulty"] for _, _, r in P)), "| inputos sorok:", sum(1 for _, _, r in P if r["input"]))
    W("egyedi instruction+input / output / quality_notes:", len({T(r) for _, _, r in P}), len({r["output"] for _, _, r in P}), len({r["quality_notes"] for _, _, r in P}))
    # per-batch
    W("\n== BATCHENKENT (fajl): sorok / mod-eloszlas / kontraszt / plusz-cimkek")
    for fn in sorted({fn for fn, _, _ in P}):
        rr = [r for f, _, r in P if f == fn]
        W(fn.replace("claude_uncertainty_source_request_", "").replace("_clean.jsonl", ""), len(rr), dict(collections.Counter(r["tags"][5] for r in rr)),
          "| kontraszt:", sum(1 for r in rr if r["tags"][5] == "kontraszt_magabiztos"), "| plusz:", dict(collections.Counter(t for r in rr for t in r["tags"][7:])))
    # kontraszt reszletes
    C = [r for _, _, r in P if r["tags"][5] == "kontraszt_magabiztos"]
    W("\n== KONTRASZT: osszes:", len(C), "| arany:", "%.1f%%" % (100 * len(C) / len(P)))
    pref = collections.Counter(re.match(r"(fp|tp|rp|ct|ip)_", r["tags"][6]).group(1) if re.match(r"(fp|tp|rp|ct|ip)_", r["tags"][6]) else "elotag_nelkuli" for r in C)
    W("kind-elotag szerint:", dict(pref), "| plusz-cimke szerint:", dict(collections.Counter(t for r in C for t in r["tags"][7:])))
    W("plusz-cimke vs kind-elotag egyezes (fp->hibas, tp->igaz, rp->reszben):",
      dict(collections.Counter((r["tags"][6][:2], tuple(r["tags"][7:])) for r in C if r["tags"][6][:3] in ("fp_", "tp_", "rp_"))))
    W("elotag nelkuli kontraszt-kindek (nincs plusz-cimke):", sorted(r["tags"][6] for r in C if not re.match(r"(fp|tp|rp|ct|ip)_", r["tags"][6])))
    # biztonsag
    W("\n== BIZTONSAG / PII (instruction, input, output, quality_notes, tags)")
    from guard import looks_like_identity_bleed
    chk = {"email": r"[\w.+-]+@[\w-]+\.[\w.-]+", "url": r"https?://|www\.|\.(hu|com|org|net|eu)\b", "telefon": r"(?:\+?36|06)[\s/-]?\d{1,2}[\s/-]?\d{3}[\s/-]?\d{3,4}|\b\d{2,4}[\s-]\d{3}[\s-]\d{3,4}\b|\b\d{9,}\b",
           "IBAN/adoazonosito": r"\bIBAN\b|\b[A-Z]{2}\d{6}\b|\b\d{8}-\d{8}", "MF-AI/Nextora/Nexora": r"MF[- ]?AI|Nexora|Nextora|Nexor"}
    allt = lambda r: " || ".join([r["instruction"], r["input"], r["output"], r["quality_notes"]] + r["tags"])
    for k, rx in chk.items():
        W("%-22s" % k, [r["id"][-4:] for _, _, r in P if re.search(rx, allt(r), re.I)])
    W("identity bleed (guard):", [r["id"][-4:] for _, _, r in P if looks_like_identity_bleed(r["category"], r["output"]) or looks_like_identity_bleed(r["category"], r["instruction"])])
    PROF = ["kurva", "fasz", "geci", "picsa", "bazd", "baszd", "köcsög", "buzi", "rohadt", "anyád"]
    W("eros karomkodas/gyuloletbeszed:", [(r["id"][-4:], w) for _, _, r in P for w in PROF if w in allt(r).lower()])
    W("onbemutatkozas-jel az outputban:", [(r["id"][-4:], w) for _, _, r in P for w in ["mesterséges intelligencia", "nyelvi modell", "chatbot", "asszisztens vagyok", "én egy ai", "program vagyok"] if w in r["output"].lower()])
    # ervenyes: tool validator mind a 10 fajlra kulon
    W("\n== SENSITIVE KULCSSZAVAS (output+mezok) BATCHENKENT")
    SENS = {"egeszseg": r"gyógyszer|vitamin|orvos|betegség|tünet|adag|kölcsönhat|gomba", "jog": r"törvény|jogász|jogi|szerződés|felmond|adó", "penz": r"befektet|kamat|nyeresé|bank", "veszely": r"ehető|veszélyes|mérgez"}
    for fn in sorted({fn for fn, _, _ in P}):
        rr = [r for f, _, r in P if f == fn]
        fl = {r["id"][-4:] for r in rr if any(re.search(rx, " ".join([r["instruction"], r["input"], r["output"], r["quality_notes"]]), re.I) for rx in SENS.values())}
        fo = {r["id"][-4:] for r in rr if any(re.search(rx, r["output"], re.I) for rx in SENS.values())}
        hard = {r["id"][-4:] for r in rr if r["difficulty"] == "hard"}
        W(fn.split("_")[-3] + "_" + fn.split("_")[-2], "| hard osszesen:", len(hard), "| kulcsszavas(output):", len(fo), "| kulcsszavas(mind a 4 mezo):", len(fl), "| hard a kulcsszavasban(output/4mezo):", len(hard & fo), "/", len(hard & fl), "| hard kulcsszo nelkul(4mezo):", sorted(hard - fl))


def style():
    allr = load_all()
    P = [r for _, _, r in allr if r.get("category") == PKG]
    o = open(os.path.join(OUT, "style.txt"), "w", encoding="utf-8")
    W = lambda *a: print(*a, file=o, flush=True)
    TK = lambda t: re.findall(r"[^\W_]+", t)
    W("== NYITASOK (instruction elso 2 szo, top 15):", collections.Counter(" ".join(TK(r["instruction"])[:2]).lower() for r in P).most_common(15))
    W("== NYITASOK (output elso 2 szo, top 20):", collections.Counter(" ".join(TK(r["output"])[:2]).lower() for r in P).most_common(20))
    W("== NYITASOK (output elso szo, top 15):", collections.Counter(TK(r["output"])[0].lower() for r in P).most_common(15))
    W("== mod szerint output elso 2 szo (top 5):")
    for m in MODES:
        W("  ", m, collections.Counter(" ".join(TK(r["output"])[:2]).lower() for r in P if r["tags"][5] == m).most_common(5))
    W("== mod szerint instruction elso 2 szo (top 5):")
    for m in MODES:
        W("  ", m, collections.Counter(" ".join(TK(r["instruction"])[:2]).lower() for r in P if r["tags"][5] == m).most_common(5))
    W("== ISMETLODO KIFEJEZESEK (a sorok %-a, ahol az output tartalmazza):")
    for w in ["nem tudom", "nem tudhatom", "ehhez pontosítás kell", "általában", "függ", "érdemes", "nézd meg", "hivatalos", "ellenőrizd", "segítek", "ezért", "szolgáltató", "kérdezd", "ha megírod", "ha megadod", "kitalál", "pontos", "orvos", "szakember"]:
        c = sum(1 for r in P if w in r["output"].lower())
        W("  %-24s %4d sor (%.1f%%)" % (w, c, 100 * c / len(P)))
    # n-gram
    def ngr(n):
        c = collections.Counter()
        for r in P:
            t = [x.lower() for x in TK(r["output"])]
            seen = {" ".join(t[i:i + n]) for i in range(len(t) - n + 1)}
            c.update(seen)
        return c
    for n in (4, 5, 6):
        W("== leggyakoribb %d-gramok (hany kulonbozo sor outputjaban van meg):" % n, ngr(n).most_common(12))
    W("== output hossz szavakban modonkent (min/median/atlag/max):")
    for m in MODES:
        L = sorted(len(TK(r["output"])) for r in P if r["tags"][5] == m)
        W("  ", m, len(L), L[0], L[len(L) // 2], round(sum(L) / len(L), 1), L[-1])
    W("== instruction forma: kerdojeles / nem:", sum(1 for r in P if "?" in r["instruction"]), "/", sum(1 for r in P if "?" not in r["instruction"]))
    W("== instruction 'Mondd meg'/'Találd ki'/'Írd' kezdet:", collections.Counter(TK(r["instruction"])[0].lower() for r in P if TK(r["instruction"])[0].lower() in ("mondd", "találd", "írd", "írj", "számold", "idézd")))
    # kind fogalmi tema (tags[6] tokenek)
    W("== leggyakoribb kind-token (tags[6] szavai):", collections.Counter(w for r in P for w in r["tags"][6].split("_") if len(w) > 3).most_common(25))


if __name__ == "__main__":
    mp.freeze_support()
    ph = sys.argv[1]
    if ph in ("struct", "all"):
        struct()
    if ph in ("style", "all"):
        style()
    if ph in ("pairs", "all"):
        for scope in ("internal", "other"):
            run_pairs(scope, 0.9)
        for scope in ("internal", "other"):
            run_pairs(scope, 0.8)
    if ph == "report":
        for th in (0.9, 0.8):
            for scope in ("internal", "other"):
                res = collect(scope, th)
                print("scope=%s th=%s" % (scope, th), {k: len(v) for k, v in res.items()})
                if th == 0.9:
                    for k, v in res.items():
                        for h in v:
                            print("   ", k, h)
                else:
                    for k, v in res.items():
                        if k in ("instruction||input", "output~output", "instruction~instruction"):
                            for h in sorted(v, key=lambda x: -x[2])[:25]:
                                if h[2] < 0.9:
                                    print("   ~", k, h)
