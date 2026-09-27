# -*- coding: utf-8 -*-
"""MT-3 méréshez használt SZINTETIKUS terhelés-generátor és időmérő (bizonyíték, NEM a projekt eszköze, NEM adatgenerálás).

Ez a szkript a valódi TE-1 exportból (csak olvasva) és véletlenszerű szó-cserékből építi az "1000 beszélgetés"
méretű terhelést a futásidő mérésére; a szintetikus beszélgetések NEM MT-1-validáltak, nem kerülnek fájlba a
datasetben, és nem tanítási adatok. A `multiturn_dedupe.run_dedupe` belső API-ját hívja (a parancssori eszköz
mindig MT-1-validált bemenetet kér).

Használat: python benchmark_synthetic.py <te1_export_run_dir> <eredmény.json> [beszélgetésszám] [--equivalence] [--names]
  --names: a kiegészítő névsemleges menet (mt3-2.0) is fut (a rekordok a névtár-illesztővel épülnek); nélküle a menet kimarad.
"""
import json, os, random, sys, time

REPO = r"C:\Users\Lenovo\OneDrive\Dokumentumok\MF-AI-Zero"
sys.path.insert(0, os.path.join(REPO, "tools"))
import dataset_export_chat_text as te2  # noqa: E402
import multiturn_dedupe as dd  # noqa: E402
import multiturn_validate as mt1  # noqa: E402

MASKER = dd.NameMasker(mt1.load_name_bank()) if "--names" in sys.argv else None


def load_export(run_dir):
    manifest, msha, rows = te2.load_te1_export(run_dir)
    return manifest, msha, rows


def build(rows, n_conv, seed):
    rng = random.Random(seed)
    vocab = sorted({w for r in rows for w in r["obj"]["output"].split() if 4 <= len(w) <= 12})
    short = [r for r in rows if len(r["obj"]["output"]) <= 350 and len(r["obj"]["instruction"]) <= 200]

    def perturb(text, frac):
        w = text.split()
        for _ in range(int(len(w) * frac)):
            w[rng.randrange(len(w))] = rng.choice(vocab)
        return " ".join(w)

    def new_conv(cid, n_ex):
        turns = []
        for _ in range(n_ex):
            r = rng.choice(short)["obj"]
            turns.append(perturb(r["instruction"], 0.5))
            turns.append(perturb(r["output"], 0.5))
        return turns

    def rec(idx, cid, texts, group=None, persona=None):
        obj = {"id": cid, "turns": [{"role": "user" if i % 2 == 0 else "assistant", "text": t} for i, t in enumerate(texts)],
               "meta": {"split_group": group or f"g{idx:04d}", "persona": persona or f"p{idx % 1000:03d}", "depends": []}}
        return dd.make_rec(idx, obj, "synthetic", 0, idx + 1, "x", MASKER)

    base_texts = [new_conv(i, rng.choice((3, 4, 4, 5, 5, 6, 8))) for i in range(n_conv)]
    planted = {"exact": [], "normalized": [], "near": [], "paraphrase_like": [], "first_turn_export_copy": []}
    recs = [rec(i, f"synthetic_{i:04d}", t) for i, t in enumerate(base_texts)]
    k = len(recs)
    for i in range(10):                                          # pontos másolat
        recs.append(rec(k, f"synthetic_dup_exact_{i:02d}", list(base_texts[i])))
        planted["exact"].append(recs[-1].id); k += 1
    for i in range(10, 20):                                      # normalizálás után azonos (nagybetű + írásjel)
        recs.append(rec(k, f"synthetic_dup_norm_{i:02d}", [t.upper() + "!!" for t in base_texts[i]]))
        planted["normalized"].append(recs[-1].id); k += 1
    for i in range(20, 30):                                      # közeli változat (kb. 3-6% szócsere)
        recs.append(rec(k, f"synthetic_dup_near_{i:02d}", [perturb(t, rng.choice((0.03, 0.05))) for t in base_texts[i]]))
        planted["near"].append(recs[-1].id); k += 1
    for i in range(30, 40):                                      # átfogalmazás-szerű (kb. 35% szócsere)
        recs.append(rec(k, f"synthetic_dup_para_{i:02d}", [perturb(t, 0.35) for t in base_texts[i]]))
        planted["paraphrase_like"].append(recs[-1].id); k += 1
    export_copy_rows = rng.sample([r for r in short if r["obj"]["input"] == ""], 10)
    for i, r in enumerate(export_copy_rows):                     # első forduló pontos másolata egy exportált példának
        texts = [r["obj"]["instruction"], r["obj"]["output"]] + new_conv(k, 2)
        recs.append(rec(k, f"synthetic_export_copy_{i:02d}", texts))
        planted["first_turn_export_copy"].append(recs[-1].id); k += 1
    return recs, planted


def summarize(res, planted):
    by = {}
    for f in res["findings"]:
        by.setdefault(f["type"] + "/" + f["status"], 0)
        by[f["type"] + "/" + f["status"]] += 1
    found = {}
    for kind, ids in planted.items():
        hit = 0
        for rid in ids:
            if any(rid in (f["a"]["record"], f["b"]["record"]) and f["status"] in ("reject", "review") for f in res["findings"]):
                hit += 1
        found[kind] = f"{hit}/{len(ids)}"
    return by, found


def main():
    run_dir, out = sys.argv[1], sys.argv[2]
    n_conv = int(sys.argv[3]) if len(sys.argv) > 3 and not sys.argv[3].startswith("--") else 1000
    manifest, msha, rows = load_export(run_dir)
    result = {"tool_version": dd.TOOL_VERSION, "names_pass": MASKER is not None, "te1_export_manifest_sha256": msha, "export_rows": len(rows),
              "conversations_base": n_conv, "runs": {}}
    if "--equivalence" in sys.argv:
        sub_conv = min(n_conv, 40)
        recs, planted = build(rows, sub_conv, 1)
        rows_small = rows[:250]
        t = time.perf_counter(); fast = dd.run_dedupe(recs, rows_small, prefilter=True, masker=MASKER); tf = time.perf_counter() - t
        recs2, _ = build(rows, sub_conv, 1)
        t = time.perf_counter(); full = dd.run_dedupe(recs2, rows_small, prefilter=False, masker=MASKER); tu = time.perf_counter() - t
        sig = lambda r: json.dumps([r["findings"], r["groups"], r["records"]], ensure_ascii=False, sort_keys=True)
        result["equivalence"] = {"conversations": len(recs), "export_rows": len(rows_small), "findings_prefilter": len(fast["findings"]),
                                 "findings_full": len(full["findings"]), "identical": sig(fast) == sig(full),
                                 "seconds_prefilter": round(tf, 2), "seconds_full": round(tu, 2),
                                 "counters_prefilter": fast["counters"], "counters_full": full["counters"]}
    recs, planted = build(rows, n_conv, 1)
    result["conversations_total"] = len(recs)
    for workers in (1,):
        recs_w, _ = build(rows, n_conv, 1)
        t = time.perf_counter()
        res = dd.run_dedupe(recs_w, rows, prefilter=True, masker=MASKER)
        el = time.perf_counter() - t
        by, found = summarize(res, planted)
        result["runs"][f"workers_{workers}"] = {"seconds_total": round(el, 2), "timing_seconds": res["timing_seconds"],
                                                 "counters": res["counters"], "findings_by_type_status": dict(sorted(by.items())),
                                                 "planted_detected": found, "summary": {k: v for k, v in res["summary"].items()
                                                                                      if k not in ("findings_by_type_status",)}}
        print(workers, round(el, 2), found, flush=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
