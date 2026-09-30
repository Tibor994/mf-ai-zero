# -*- coding: utf-8 -*-
"""MT-5 méretbeli mérés (bizonyíték, nem eszköz): 1000 MESTERSÉGES beszélgetés -> MT-3 (a valódi TE-1
exporttal szemben) -> MT-2 -> MT-4 -> MT-5 száraz futás.

A beszélgetések a tests/test_multiturn_split.py generátorával készülnek (valós szavakból összeállított
értelmetlen mondatok, `mtfx_syn_NNNN` azonosítóval, fixture móddal): NEM valódi beszélgetések, az 1000
beszélgetéses csomagba nem számítanak, tanításra nem használhatók. A száraz futás `fixture_` előtagú
mappába kerül. A valódi adatot (data/clean, a TE-1 export) a mérés csak olvassa.

Használat: python benchmark_train.py <eredmény.json> [n=1000]
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
sys.path.insert(0, os.path.join(REPO, "src"))
import dataset_export_train as te1  # noqa: E402
import multiturn_dedupe as dd  # noqa: E402
import multiturn_export as mx  # noqa: E402
import multiturn_split as ms  # noqa: E402
import train_multiturn as mt5  # noqa: E402
import test_multiturn_split as T  # noqa: E402


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def main():
    out_json = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 1000
    tmp = tempfile.mkdtemp(prefix="mt5bench_")
    res = {"records_requested": n}
    try:
        recs = T.corpus(n, seed=2027)
        os.makedirs(os.path.join(tmp, "convs"))
        conv = os.path.join(tmp, "convs", "corpus.jsonl")
        T.write_jsonl(conv, recs)
        res["records_total"] = len(recs)
        t = time.time()
        te1_dir = te1.run_export(os.path.join(tmp, "te1"), run_name="real")["run_dir"]  # a valódi data/clean csak olvasva
        res["te1_export_seconds"] = round(time.time() - t, 2)
        t = time.time()
        rep = dd.run_from_files([conv], os.path.join(tmp, "mt3"), "fixture", te1_export=te1_dir, run_name="r")
        res["mt3_seconds"] = round(time.time() - t, 2)
        report = os.path.join(rep["run_dir"], "dedupe_report.json")
        t = time.time()
        man2 = ms.run_from_files([conv], os.path.join(tmp, "mt2"), "fixture", report, te1_export=te1_dir,
                                 targets=ms.DEFAULT_TARGETS, run_name="s")
        res["mt2_seconds"] = round(time.time() - t, 2)
        mt2_path = os.path.join(man2["run_dir"], "split_manifest.json")
        t = time.time()
        man4 = mx.run_export(mt2_path, os.path.join(tmp, "mt4"), "fixture", run_name="fixture_bench")
        res["mt4_seconds"] = round(time.time() - t, 2)
        export_manifest = os.path.join(man4["run_dir"], "export_manifest.json")

        t = time.time()
        man5 = mt5.run_dry_run(export_manifest, "fixture", os.path.join(tmp, "mt5"), run_name="fixture_bench")
        res["mt5_seconds_total"] = round(time.time() - t, 2)
        res["mt5_timing_seconds"] = man5["timing_seconds"]
        res["mt5_vocab"] = man5["vocab"]
        res["mt5_counts"] = man5["counts"]
        res["mt5_warnings"] = man5["warnings"]
        res["mt5_splits"] = man5["splits"]

        # ismételhetőség + visszaolvasásos önellenőrzés
        t = time.time()
        man5b = mt5.run_dry_run(export_manifest, "fixture", os.path.join(tmp, "mt5"), run_name="fixture_bench2")
        res["mt5_repeat_seconds"] = round(time.time() - t, 2)
        drop = ("created_utc", "run_dir", "outputs", "timing_seconds")
        d1 = {k: v for k, v in man5.items() if k not in drop}
        d2 = {k: v for k, v in man5b.items() if k not in drop}
        res["mt5_repeat_deterministic"] = json.dumps(d1, sort_keys=True) == json.dumps(d2, sort_keys=True)
        res["mt5_verify_report"] = mt5.verify_dry_run_report(os.path.join(man5["run_dir"], mt5.REPORT_FILE))

        # kisebb --max-chars: néhány minta visszatartása (nem csendes csonkítás)
        manifest, run_dir, _s = mt5.load_export(export_manifest, "fixture")
        all_lengths = sorted(len(r["text"]) for s in mt5.SPLITS for md in mt5.DEFAULT_MODES for r in mt5.load_samples(manifest, run_dir, s, md))
        cutoff = all_lengths[int(len(all_lengths) * 0.7)]
        man5c = mt5.run_dry_run(export_manifest, "fixture", os.path.join(tmp, "mt5"), max_chars=cutoff, run_name="fixture_bench_limit")
        res["mt5_small_limit"] = {"max_chars": cutoff, "withheld_oversized_total": man5c["counts"]["withheld_oversized_total"],
                                  "warnings": man5c["warnings"]}

        # a felsőbb export/felosztás/jelentés érintetlen marad
        before = {p: sha(os.path.join(man4["run_dir"], p)) for p in man4["outputs"]}
        mt5.run_dry_run(export_manifest, "fixture", os.path.join(tmp, "mt5"), run_name="fixture_bench_untouched")
        after = {p: sha(os.path.join(man4["run_dir"], p)) for p in man4["outputs"]}
        res["mt4_export_untouched"] = before == after
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    with open(out_json, "w", encoding="utf-8", newline="\n") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(json.dumps({k: res[k] for k in ("records_total", "mt3_seconds", "mt2_seconds", "mt4_seconds", "mt5_seconds_total",
                                          "mt5_repeat_deterministic", "mt5_verify_report", "mt4_export_untouched", "mt5_small_limit")},
                     ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
