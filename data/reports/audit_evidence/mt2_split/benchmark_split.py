# -*- coding: utf-8 -*-
"""MT-2 méretbeli mérés (bizonyíték, nem eszköz): 1000 MESTERSÉGES beszélgetés -> MT-3 (a valódi TE-1 exporttal szemben) -> MT-2.

A beszélgetések a tests/test_multiturn_split.py generátorával készülnek (valós szavakból összeállított értelmetlen mondatok,
`mtfx_syn_NNNN` azonosítóval, fixture móddal): NEM valódi beszélgetések, az 1000 beszélgetéses csomagba nem számítanak,
tanításra nem használhatók. A valódi adatot (data/clean, TE-1 export) csak olvassa.

Használat: python benchmark_split.py <eredmény.json> [n=1000] [--blocked]
  --blocked: 12 beültetett pontos másolat (blokkolt rekord) és 6 kizárt beszélgetés a visszatartás mérésére.
"""
import json
import os
import shutil
import sys
import tempfile
import time

REPO = r"C:\Users\Lenovo\OneDrive\Dokumentumok\MF-AI-Zero"
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "tools"))
import dataset_export_train as te1  # noqa: E402
import multiturn_dedupe as dd  # noqa: E402
import multiturn_split as ms  # noqa: E402
from tests import test_multiturn_split as T  # noqa: E402


def main():
    out_json = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 1000
    with_blocked = "--blocked" in sys.argv
    tmp = tempfile.mkdtemp(prefix="mt2bench_")
    res = {"records_requested": n, "with_blocked_scenario": with_blocked}
    try:
        recs = T.corpus(n, seed=2026)
        # tervezett változatok: ~15%-nyi többtagú csoport (deklarált párok/hármasok), és láncolt persona-kapcsolatok
        k = 0
        groups = 0
        while k + 3 < n * 0.15 * 2:
            size = 2 + (groups % 2)
            for j in range(size):
                T.link(recs[k + j], group="g%04d" % (5000 + groups))
            k += size + 1
            groups += 1
        for j in range(0, 30, 3):                                        # 10 persona-hármas (a persona legfeljebb 3 beszélgetésben szerepelhet)
            for t in (1, 2):
                T.link(recs[600 + j + t], persona=recs[600 + j]["meta"]["persona"])
        expected_excluded = []
        if with_blocked:
            for c in range(12):
                dup = T.copy_of(recs[700 + c], "mtfx_syn_%04d" % (9000 + c))
                T.link(dup, group="g%04d" % (9000 + c), persona="p%03d" % (950 + c))
                recs.append(dup)
            expected_excluded = ["mtfx_syn_%04d" % i for i in range(800, 806)]
        os.makedirs(os.path.join(tmp, "convs"))
        conv = os.path.join(tmp, "convs", "corpus.jsonl")
        T.write_jsonl(conv, recs)
        res["records_total"] = len(recs)
        t = time.time()
        export = te1.run_export(os.path.join(tmp, "te1"), run_name="real")["run_dir"]     # a valódi data/clean csak olvasva
        res["te1_export_seconds"] = round(time.time() - t, 2)
        t = time.time()
        rep = dd.run_from_files([conv], os.path.join(tmp, "mt3"), "fixture", te1_export=export, run_name="r")
        res["mt3_seconds"] = round(time.time() - t, 2)
        res["mt3_summary"] = {k2: rep["summary"][k2] for k2 in ("records", "findings_by_status", "blocked_records", "groups", "groups_with_2_or_more",
                                                                  "largest_group", "variant_share", "experimental_signals")}
        report = os.path.join(rep["run_dir"], "dedupe_report.json")
        T.Base.ensure_tool_sha(report)
        excl = None
        if expected_excluded:
            excl = os.path.join(tmp, "excl.txt")
            with open(excl, "w", encoding="utf-8") as f:
                for rid in expected_excluded:
                    f.write(f"{rid} | tartalmi kifogás | felülvizsgálat\n")
        t = time.time()
        man = ms.run_from_files([conv], os.path.join(tmp, "mt2"), "fixture", report, te1_export=export, exclusions_path=excl,
                                targets=ms.DEFAULT_TARGETS, run_name="s")
        res["mt2_seconds"] = round(time.time() - t, 2)
        res["mt2_compute_seconds"] = man["timing_seconds"]["compute"]
        for key in ("counts", "splits", "deviation", "hard_test", "cross_split", "export_links", "verification", "warnings"):
            res["mt2_" + key] = man[key]
        res["mt2_stratification"] = man["stratification"]["result"]
        res["mt2_dp_choice"] = man["stratification"]["dp_choice"]
        res["mt2_assignment_sha256"] = man["assignment_sha256"]
        # reprodukálhatóság: második futás és manifest-ellenőrzés újraszámolással
        t = time.time()
        man2 = ms.run_from_files([conv], os.path.join(tmp, "mt2"), "fixture", report, te1_export=export, exclusions_path=excl,
                                 targets=ms.DEFAULT_TARGETS, run_name="s2")
        res["mt2_repeat_identical"] = man2["assignment_sha256"] == man["assignment_sha256"]
        res["mt2_verify_manifest"] = ms.verify_manifest(os.path.join(man["run_dir"], "split_manifest.json"))
        res["mt2_repeat_and_verify_seconds"] = round(time.time() - t, 2)
        # más seed, más kijelölés (a darabszám ugyanaz)
        man3 = ms.run_from_files([conv], os.path.join(tmp, "mt2"), "fixture", report, te1_export=export, exclusions_path=excl,
                                 targets=ms.DEFAULT_TARGETS, seed="masik", run_name="s3")
        res["mt2_other_seed"] = {"assignment_differs": man3["assignment_sha256"] != man["assignment_sha256"],
                                 "same_counts": man3["deviation"]["achieved"] == man["deviation"]["achieved"]}
        # független ellenőrzés a kimeneti fájlból
        by_unit = {}
        for a in man["assignment"]:
            by_unit.setdefault(a["unit"], set()).add(a["split"])
        res["independent_check"] = {"units": len(by_unit), "units_split_across_parts": sum(1 for v in by_unit.values() if len(v) > 1)}
        held = {h["id"]: h["reasons"] for h in man["held_back"]}
        res["held_back_ids"] = held
        if with_blocked:
            res["excluded_ids_held_back"] = all("excluded_list" in held.get(i, []) for i in expected_excluded)
            res["planted_duplicates_held_back"] = sum(1 for i in held if i.startswith("mtfx_syn_90"))
        res["real_data_untouched_note"] = "a data/clean csak olvasva (a TE-1 exporttal); a kimenetek ideiglenes mappában voltak és törölve"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    with open(out_json, "w", encoding="utf-8", newline="\n") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(json.dumps({k: res[k] for k in ("records_total", "mt3_seconds", "mt2_seconds", "mt2_compute_seconds", "mt2_deviation", "independent_check")}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
