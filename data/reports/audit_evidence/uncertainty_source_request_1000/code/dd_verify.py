# -*- coding: utf-8 -*-
"""Az elo-szurt modszer ekvivalenciajanak igazolasa: eredeti tools/dataset_dedupe.find_duplicates() vs. elo-szurt modszer
ugyanazon a reszhalmazon (a 7 ismert >=0.9 talalat soraibol + 400 veletlen sor, fix seed), tobb kuszobon (0.9 es 0.8)."""
import collections, difflib, glob, json, os, random, sys, time
REPO = r"C:\Users\Lenovo\OneDrive\Dokumentumok\MF-AI-Zero"
sys.path.insert(0, os.path.join(REPO, "tools"))
from dataset_dedupe import find_duplicates
allr = []
for f in sorted(glob.glob(os.path.join(REPO, "data", "clean", "*.jsonl"))):
    for l in open(f, encoding="utf-8"):
        if l.strip():
            allr.append(json.loads(l))
idx = {r["id"]: i for i, r in enumerate(allr)}
known = ["simple_qa_0857", "simple_qa_0851", "simple_qa_0859", "simple_qa_0914", "simple_qa_0671", "simple_qa_1081", "simple_qa_0734", "step_by_step_0229", "step_by_step_0227", "simple_qa_0489", "simple_qa_0915"]
rng = random.Random(20260925)
pick = set(idx[k] for k in known) | set(rng.sample(range(len(allr)), 60))
sub = [allr[i] for i in sorted(pick)]
print("reszhalmaz:", len(sub), flush=True)


def T(r):
    ins = (r.get("instruction") or "").strip()
    inp = (r.get("input") or "").strip() if isinstance(r.get("input"), str) else ""
    t = "%s || %s" % (ins, inp)
    return t if t.strip(" |") else ""


def fast(sub, th):
    out = {"task": set(), "output": set()}
    for name, get in (("task", T), ("output", lambda r: (r.get("output") or "").strip())):
        txt = [get(r) for r in sub]
        cnt = [collections.Counter(t) for t in txt]
        for j in range(len(sub)):
            a = txt[j]
            if not a:
                continue
            for i in range(j):
                b = txt[i]
                if not b:
                    continue
                if 2.0 * min(len(a), len(b)) / (len(a) + len(b)) < th:
                    continue
                if 2.0 * sum((cnt[j] & cnt[i]).values()) / (len(a) + len(b)) < th:
                    continue
                if difflib.SequenceMatcher(None, a, b).ratio() >= th:
                    out[name].add(j)
    return out


for th in (0.9, 0.8):
    t0 = time.time()
    ent = [{"row_number": i, "row": r} for i, r in enumerate(sub)]
    rep = find_duplicates(ent, th)
    orig = {"task": {d["duplicate"] for d in rep["instruction_duplicates"]}, "output": {d["duplicate"] for d in rep["output_duplicates"]}}
    t1 = time.time()
    fa = fast(sub, th)
    t2 = time.time()
    print("kuszob %.1f | eredeti: task %d, output %d (%.0fs) | elo-szurt: task %d, output %d (%.0fs) | azonos halmaz: task %s, output %s" % (
        th, len(orig["task"]), len(orig["output"]), t1 - t0, len(fa["task"]), len(fa["output"]), t2 - t1, orig["task"] == fa["task"], orig["output"] == fa["output"]), flush=True)
