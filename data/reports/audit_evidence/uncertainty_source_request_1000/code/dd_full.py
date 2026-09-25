# -*- coding: utf-8 -*-
"""Teljes korpuszos, SZAKASZOLT, ujraindithato duplikacio-ellenorzes.
Modszer = tools/dataset_dedupe.py find_duplicates() (difflib.SequenceMatcher(None, kesobbi, korabbi).ratio(), kuszob 0.9,
mezok: 'instruction || input' es 'output', + id-egyezes). CSAK matematikailag pontos elo-szuresek (hossz-arany es karakter-multiset felso korlat):
ezek soha nem szurnek ki olyan part, aminek a ratio()-ja >= 0.9, tehat az eredmeny azonos a tool eredmenyevel, csak gyorsabb.
Hasznalat:
  python dd_full.py trial <j_start> <j_end>            (idomeres, nem ment)
  python dd_full.py run <chunk_size> [--only-new-from N]  (chunkonkent ment: dd_parts/*.json, ujrainditasnal a kesz chunkokat kihagyja)
  python dd_full.py report                                (osszegzes)
"""
import collections, difflib, glob, json, multiprocessing as mp, os, sys, time

REPO = r"C:\Users\Lenovo\OneDrive\Dokumentumok\MF-AI-Zero"
HERE = os.path.dirname(os.path.abspath(__file__))
PARTS = os.path.join(HERE, "dd_parts")
TH = 0.9


def load():
    ent = []
    for f in sorted(glob.glob(os.path.join(REPO, "data", "clean", "*.jsonl"))):
        for n, l in enumerate(open(f, encoding="utf-8"), 1):
            if l.strip():
                r = json.loads(l)
                ent.append((os.path.basename(f), n, r))
    return ent


def prep(ent):
    T, O, ID = [], [], []
    for fn, n, r in ent:
        ins = (r.get("instruction") or "").strip()
        inp = (r.get("input") or "").strip() if isinstance(r.get("input"), str) else ""
        T.append("%s || %s" % (ins, inp) if ("%s || %s" % (ins, inp)).strip(" |") else "")
        O.append((r.get("output") or "").strip())
        ID.append(r.get("id"))
    CT = [collections.Counter(t) for t in T]
    CO = [collections.Counter(o) for o in O]
    return T, O, ID, CT, CO


G = {}


def init():
    ent = load()
    G["ent"] = ent
    G["T"], G["O"], G["ID"], G["CT"], G["CO"] = prep(ent)


def cmp_field(texts, cnts, j, i_range):
    a = texts[j]
    if not a:
        return []
    la, ca = len(a), cnts[j]
    hits, checked, exact = [], 0, 0
    for i in i_range:
        b = texts[i]
        if not b:
            continue
        lb = len(b)
        if 2.0 * min(la, lb) / (la + lb) < TH:
            continue
        checked += 1
        inter = sum((ca & cnts[i]).values())
        if 2.0 * inter / (la + lb) < TH:
            continue
        exact += 1
        r = difflib.SequenceMatcher(None, a, b).ratio()   # a = kesobbi sor, b = korabbi (mint a toolban)
        if r >= TH:
            hits.append((i, round(r, 4)))
    return hits, checked, exact


def do_chunk(args):
    js, je, min_i_new = args
    out = os.path.join(PARTS, "chunk_%05d_%05d.json" % (js, je))
    if os.path.exists(out):
        return out, 0.0, True
    t0 = time.time()
    res = {"js": js, "je": je, "task": [], "output": [], "id": [], "stats": {"pairs_len_ok": 0, "pairs_exact": 0}}
    ids_first = {}
    for j in range(js, je):
        for name, texts, cnts in (("task", G["T"], G["CT"]), ("output", G["O"], G["CO"])):
            r = cmp_field(texts, cnts, j, range(0, j))
            if r:
                h, c, e = r
                res["stats"]["pairs_len_ok"] += c
                res["stats"]["pairs_exact"] += e
                for i, s in h:
                    res[name].append({"later": j, "earlier": i, "sim": s})
        for i in range(0, j):
            if G["ID"][i] is not None and G["ID"][i] == G["ID"][j]:
                res["id"].append({"later": j, "earlier": i})
    os.makedirs(PARTS, exist_ok=True)
    json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False)
    return out, time.time() - t0, False


def main():
    mode = sys.argv[1]
    os.makedirs(PARTS, exist_ok=True)
    if mode == "trial":
        js, je = int(sys.argv[2]), int(sys.argv[3])
        init()
        t0 = time.time()
        for j in range(js, je):
            for texts, cnts in ((G["T"], G["CT"]), (G["O"], G["CO"])):
                cmp_field(texts, cnts, j, range(0, j))
        dt = time.time() - t0
        print("trial rows %d..%d of %d: %.1fs (%.3fs/row)" % (js, je, len(G["ent"]), dt, dt / (je - js)))
    elif mode == "run":
        cs = int(sys.argv[2])
        start = int(sys.argv[3]) if len(sys.argv) > 3 else 0
        ent = load()
        n = len(ent)
        chunks = [(s, min(s + cs, n), 0) for s in range(start, n, cs)]
        print("rows:", n, "chunks:", len(chunks), "cpu:", mp.cpu_count(), flush=True)
        t0 = time.time()
        done = 0
        with mp.Pool(max(1, mp.cpu_count() - 1), initializer=init) as pool:
            for out, dt, skipped in pool.imap_unordered(do_chunk, chunks):
                done += 1
                print("[%d/%d] %s %s %.0fs elapsed" % (done, len(chunks), os.path.basename(out), "(kihagyva, mar kesz)" if skipped else "%.0fs" % dt, time.time() - t0), flush=True)
        print("RUN_DONE", flush=True)
    elif mode == "report":
        ent = load()
        hits = {"task": [], "output": [], "id": []}
        covered = 0
        for f in sorted(glob.glob(os.path.join(PARTS, "chunk_*.json"))):
            d = json.load(open(f, encoding="utf-8"))
            covered += d["je"] - d["js"]
            for k in hits:
                hits[k] += d[k]
        print("lefedett 'kesobbi' sorok:", covered, "/", len(ent))
        for k, v in hits.items():
            print(k, len(v))
            for h in v:
                a, b = ent[h["later"]], ent[h["earlier"]]
                print("  ", a[2]["id"], "<->", b[2]["id"], h.get("sim"))


if __name__ == "__main__":
    mp.freeze_support()
    main()
