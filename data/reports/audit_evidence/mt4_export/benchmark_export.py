# -*- coding: utf-8 -*-
"""MT-4 méretbeli mérés (bizonyíték, nem eszköz): 1000 MESTERSÉGES beszélgetés -> MT-3 (a valódi TE-1 exporttal szemben) -> MT-2 -> MT-4.

A beszélgetések a tests/test_multiturn_split.py generátorával készülnek (valós szavakból összeállított értelmetlen mondatok,
`mtfx_syn_NNNN` azonosítóval, fixture móddal): NEM valódi beszélgetések, az 1000 beszélgetéses csomagba nem számítanak, tanításra
nem használhatók; az export `fixture_` előtagú mappába kerül. A valódi adatot (data/clean, TE-1 export) csak olvassa.

Használat: python benchmark_export.py <eredmény.json> [n=1000] [--blocked]
  --blocked: 12 beültetett pontos másolat (blokkolt rekord + csoporttárs) és 6 kizárási listás beszélgetés a visszatartás méréséhez.
"""
import hashlib
import json
import os
import shutil
import sys
import tempfile
import time

REPO = r"C:\Users\Lenovo\OneDrive\Dokumentumok\MF-AI-Zero"
sys.path.insert(0, os.path.join(REPO, "tests"))
sys.path.insert(0, os.path.join(REPO, "tools"))
import dataset_export_train as te1  # noqa: E402
import multiturn_dedupe as dd  # noqa: E402
import multiturn_export as mx  # noqa: E402
import multiturn_split as ms  # noqa: E402
import test_multiturn_split as T  # noqa: E402


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def main():
    out_json = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 1000
    with_blocked = "--blocked" in sys.argv
    tmp = tempfile.mkdtemp(prefix="mt4bench_")
    res = {"records_requested": n, "with_blocked_scenario": with_blocked}
    try:
        recs = T.corpus(n, seed=2026)
        k = groups = 0
        while k + 3 < n * 0.15 * 2:                                       # tervezett változat-csoportok (2-3 tagú)
            size = 2 + (groups % 2)
            for j in range(size):
                T.link(recs[k + j], group="g%04d" % (5000 + groups))
            k += size + 1
            groups += 1
        for j in range(0, 30, 3):                                          # persona-hármasok
            for t in (1, 2):
                T.link(recs[600 + j + t], persona=recs[600 + j]["meta"]["persona"])
        excluded = []
        if with_blocked:
            for c in range(12):
                dup = T.copy_of(recs[700 + c], "mtfx_syn_%04d" % (9000 + c))
                T.link(dup, group="g%04d" % (9000 + c), persona="p%03d" % (950 + c))
                recs.append(dup)
            excluded = ["mtfx_syn_%04d" % i for i in range(800, 806)]
        os.makedirs(os.path.join(tmp, "convs"))
        conv = os.path.join(tmp, "convs", "corpus.jsonl")
        T.write_jsonl(conv, recs)
        res["records_total"] = len(recs)
        te1_dir = te1.run_export(os.path.join(tmp, "te1"), run_name="real")["run_dir"]         # a valódi data/clean csak olvasva
        t = time.time()
        rep = dd.run_from_files([conv], os.path.join(tmp, "mt3"), "fixture", te1_export=te1_dir, run_name="r")
        res["mt3_seconds"] = round(time.time() - t, 2)
        report = os.path.join(rep["run_dir"], "dedupe_report.json")
        excl = None
        if excluded:
            excl = os.path.join(tmp, "excl.txt")
            with open(excl, "w", encoding="utf-8") as f:
                for rid in excluded:
                    f.write(f"{rid} | tartalmi kifogás | felülvizsgálat\n")
        t = time.time()
        man2 = ms.run_from_files([conv], os.path.join(tmp, "mt2"), "fixture", report, te1_export=te1_dir, exclusions_path=excl,
                                 targets=ms.DEFAULT_TARGETS, run_name="s")
        res["mt2_seconds"] = round(time.time() - t, 2)
        mt2_path = os.path.join(man2["run_dir"], "split_manifest.json")
        ups = [mt2_path, conv, report] + [os.path.join(man2["run_dir"], n2) for n2 in man2["outputs"]] + \
              [os.path.join(te1_dir, n2) for n2 in os.listdir(te1_dir)] + ([excl] if excl else [])
        before = {p: sha(p) for p in ups}
        t = time.time()
        man4 = mx.run_export(mt2_path, os.path.join(tmp, "mt4"), "fixture", run_name="fixture_bench")
        res["mt4_seconds_total"] = round(time.time() - t, 2)
        res["mt4_render_and_write_seconds"] = man4["timing_seconds"]["render_and_write"]
        res["mt2_counts"] = {"assigned": man2["counts"]["assigned"], "held_back": man2["counts"]["held_back"], "by_reason": man2["counts"]["held_back_by_reason"]}
        res["export_counts"] = {s: {"conversations": man4["splits"][s]["conversations"], "messages": man4["splits"][s]["messages"],
                                    "R1": {k: man4["splits"][s]["samples"]["R1"][k] for k in ("total", "first_turn", "history_dependent", "lossless", "content_truncated",
                                                                                              "dependency_not_covered", "history_chars_lost")},
                                    "R2": {k: man4["splits"][s]["samples"]["R2"][k] for k in ("total", "first_turn", "history_dependent", "lossless")}}
                                for s in mx.SPLITS}
        res["expected_from_mt2"] = man4["expected_from_mt2"]
        res["withheld"] = len(man4["withheld"])
        res["warnings"] = man4["warnings"]
        res["statuses"] = man4["statuses"]
        res["output_files"] = {k: v["bytes"] for k, v in man4["outputs"].items()}
        t = time.time()
        problems = mx.verify_export(os.path.join(man4["run_dir"], mx.MANIFEST_FILE))
        res["verify_export_seconds"] = round(time.time() - t, 2)
        res["verify_export_problems"] = problems
        man4b = mx.run_export(mt2_path, os.path.join(tmp, "mt4"), "fixture", run_name="fixture_bench2")
        res["repeat_byte_identical"] = all(open(os.path.join(man4["run_dir"], k), "rb").read() == open(os.path.join(man4b["run_dir"], k), "rb").read()
                                           for k in man4["outputs"])
        res["upstream_untouched"] = {p: sha(p) for p in ups} == before
        held = {h["id"] for h in man2["held_back"]}
        exported = {c["id"] for c in man4["conversations"]}
        res["held_back_absent_from_export"] = not (held & exported)
        res["parts_disjoint"] = len(exported) == sum(man4["splits"][s]["conversations"] for s in mx.SPLITS)
        res["fixture_marked"] = {"dir_prefix": os.path.basename(man4["run_dir"]).startswith("fixture_"), "marker_file": os.path.isfile(os.path.join(man4["run_dir"], mx.FIXTURE_MARKER_FILE)),
                                 "training_data": man4["training_data"]}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    with open(out_json, "w", encoding="utf-8", newline="\n") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(json.dumps({k: res[k] for k in ("records_total", "mt3_seconds", "mt2_seconds", "mt4_seconds_total", "verify_export_seconds", "withheld",
                                          "repeat_byte_identical", "upstream_untouched", "verify_export_problems")}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
