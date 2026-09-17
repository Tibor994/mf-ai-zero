"""
MF-AI-Zero - dataset pipeline hardening: témakör- és arányriport.

CÉL: egy .jsonl könyvtár (pl. data/clean/) TELJES tartalmán megszámolja a
tag- és category-előfordulásokat, és jelzi, ha valamelyik tag aránytalanul
felül van reprezentálva a teljes korpuszhoz képest.

Ezt egy 2026-09-i audit (data/reports/dataset_audit_0151_0500.md, 2.3 pont)
javasolta: kimutatta, hogy az 'AI' tag a korpusz 12.8%-át teszi ki, és ezen
belül is egy szűk, önreferenciális kérdéskört (pl. "mi a Nexora Zero célja")
ismétel batch-ről batch-re, apró átfogalmazásokkal - korábban ezt semmilyen
automata eszköz nem mérte, csak alkalmi, kézzel írt Counter-elemzés az
audit-körökben. Ez a modul ezt formalizálja, és egy KONFIGURÁLHATÓ
küszöbbel automatikusan jelzi a túlreprezentált tageket.

Ez a modul SOHA nem törli/módosítja a forrásfájlokat - csak REPORTOL.

Használat parancssorból:
    python tools/dataset_topic_report.py data/clean
    python tools/dataset_topic_report.py data/clean --threshold 0.08 --keyword nexora

Használat modulként:
    from dataset_topic_report import topic_report
"""

import argparse
import glob
import json
import os
from collections import Counter

# Az audit (2.3 pont) kb. 8-10%-os arányt javasolt riasztási küszöbként -
# ennél magasabb tag-arány valószínűleg tartalmi túlismétlést jelez.
DEFAULT_OVERREPRESENTATION_THRESHOLD = 0.08

# A 'magyar' tag minden sorban jelen van (nyelvjelző, nem témakör) - a
# téma-eloszlásból szándékosan kihagyjuk, mert torzítaná a képet.
EXCLUDED_TAGS = {"magyar"}


def _load_rows(clean_dir):
    files = sorted(glob.glob(os.path.join(clean_dir, "*.jsonl")))
    rows = []
    for path in files:
        with open(path, "r", encoding="utf-8") as f:
            for raw_line in f:
                stripped = raw_line.strip()
                if not stripped:
                    continue
                rows.append(json.loads(stripped))
    return rows, [os.path.basename(p) for p in files]


def topic_report(rows, overrepresentation_threshold=DEFAULT_OVERREPRESENTATION_THRESHOLD,
                  keyword_watchlist=None):
    """rows: [{"tags": [...], "category": ..., "instruction": ..., "output": ...}, ...].

    Visszaad egy dict-et: {"total_rows", "tag_counts", "category_counts",
    "overrepresented_tags": [{"tag", "count", "ratio"}, ...],
    "keyword_counts": {kulcsszó: darab}}."""
    total = len(rows)
    tag_counter = Counter()
    category_counter = Counter()
    for row in rows:
        category_counter[row.get("category") or "(nincs)"] += 1
        for tag in row.get("tags") or []:
            if tag not in EXCLUDED_TAGS:
                tag_counter[tag] += 1

    overrepresented = []
    if total:
        for tag, count in tag_counter.items():
            ratio = count / total
            if ratio > overrepresentation_threshold:
                overrepresented.append({"tag": tag, "count": count, "ratio": round(ratio, 4)})
    overrepresented.sort(key=lambda x: x["ratio"], reverse=True)

    keyword_counts = {}
    if keyword_watchlist:
        for keyword in keyword_watchlist:
            low_keyword = keyword.lower()
            keyword_counts[keyword] = sum(
                1 for row in rows
                if low_keyword in ((row.get("instruction") or "") + " " + (row.get("output") or "")).lower()
            )

    return {
        "total_rows": total,
        "tag_counts": dict(tag_counter.most_common()),
        "category_counts": dict(category_counter.most_common()),
        "overrepresented_tags": overrepresented,
        "keyword_counts": keyword_counts,
    }


def _main():
    parser = argparse.ArgumentParser(description="MF-AI-Zero témakör- és arányriport.")
    parser.add_argument("clean_dir", help="A vizsgálandó könyvtár (pl. data/clean).")
    parser.add_argument("--threshold", type=float, default=DEFAULT_OVERREPRESENTATION_THRESHOLD,
                         help=f"Túlreprezentáltsági küszöb (0-1, alapértelmezés: {DEFAULT_OVERREPRESENTATION_THRESHOLD}).")
    parser.add_argument("--keyword", action="append", default=[],
                         help="Kulcsszó, amit külön is számolni kell (instruction+output szövegben, "
                              "kis/nagybetű-független). Többször megadható.")
    args = parser.parse_args()

    rows, files = _load_rows(args.clean_dir)
    result = topic_report(rows, args.threshold, args.keyword)

    print(f"Vizsgált fájlok: {len(files)}")
    print(f"Összes sor: {result['total_rows']}")
    print("\nCategory eloszlás:")
    for cat, cnt in result["category_counts"].items():
        print(f"  {cat}: {cnt}")
    print("\nTag eloszlás (top 15):")
    for tag, cnt in list(result["tag_counts"].items())[:15]:
        ratio = cnt / result["total_rows"] if result["total_rows"] else 0
        print(f"  {tag}: {cnt} ({ratio:.1%})")
    print(f"\nTúlreprezentált tagek (küszöb: {args.threshold:.0%}):")
    if result["overrepresented_tags"]:
        for item in result["overrepresented_tags"]:
            print(f"  [FIGYELEM] {item['tag']}: {item['count']} sor ({item['ratio']:.1%})")
    else:
        print("  (nincs túlreprezentált tag)")
    if result["keyword_counts"]:
        print("\nKulcsszó-előfordulások:")
        for kw, cnt in result["keyword_counts"].items():
            print(f"  '{kw}': {cnt} sor")


if __name__ == "__main__":
    _main()
