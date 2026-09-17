"""
MF-AI-Zero - v1.7.4 dataset foundation: train/eval split.

CÉL: egy MÁR validált/deduplikált JSONL sor-listát determinisztikusan
train/eval részre osztani - kategóriánként ARÁNYOSAN (ha egy kategóriából
csak kevés sor van, akkor is próbál mindkét részbe jutattni belőle, ha a
mennyiség engedi), FIX seed-del, hogy a split mindig ugyanaz legyen
ugyanarra a bemenetre.

FONTOS: ez a modul NEM ír fájlt magától - visszaadja a két listát
(train_rows, eval_rows), a hívó (pl. dataset_import.py vagy egy teszt)
dönti el, hova menti.

Használat parancssorból:
    python tools/dataset_split.py data/clean/batch1.jsonl --train-ratio 0.9 --seed 42

Használat modulként:
    from dataset_split import split_rows
"""

import argparse
import json
import random
from collections import defaultdict

DEFAULT_TRAIN_RATIO = 0.9
DEFAULT_SEED = 42


def split_rows(rows, train_ratio=DEFAULT_TRAIN_RATIO, seed=DEFAULT_SEED):
    """rows: dict-ek listája (minden elem legalább 'category' kulccsal
    rendelkezik). Visszaad egy (train_rows, eval_rows) párt.

    Kategóriánként KÜLÖN determinisztikus keverés (random.Random(seed) -
    SOSEM a globális random modul, hogy más, egyidejű kód ne
    befolyásolja/módosítsa a kimenetet), majd arányos vágás - így minden
    kategória train/eval aránya kb. ugyanaz, mint a globális train_ratio,
    még ha a kategóriák mérete nagyon eltérő is."""
    if not 0.0 < train_ratio < 1.0:
        raise ValueError("train_ratio-nak 0 és 1 között kell lennie.")

    by_category = defaultdict(list)
    for row in rows:
        by_category[row.get("category") or "ismeretlen"].append(row)

    rng = random.Random(seed)
    train_rows = []
    eval_rows = []

    for category in sorted(by_category.keys()):
        category_rows = list(by_category[category])
        rng.shuffle(category_rows)
        n = len(category_rows)
        # legalább 1 sor eval-ba kerüljön, ha van elég (>=2) sor abból a
        # kategóriából - így egy kis kategória se maradjon eval nélkül,
        # de 1 elemű kategóriánál nincs mit osztani, az train-be megy.
        if n >= 2:
            train_count = max(1, round(n * train_ratio))
            train_count = min(train_count, n - 1)
        else:
            train_count = n
        train_rows.extend(category_rows[:train_count])
        eval_rows.extend(category_rows[train_count:])

    return train_rows, eval_rows


def _load_rows(path):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for raw_line in f:
            stripped = raw_line.strip()
            if not stripped:
                continue
            try:
                row = json.loads(stripped)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                rows.append(row)
    return rows


def _write_jsonl(rows, path):
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _main():
    parser = argparse.ArgumentParser(description="MF-AI-Zero dataset train/eval split.")
    parser.add_argument("path", help="A felosztandó .jsonl fájl elérési útja.")
    parser.add_argument("--train-ratio", type=float, default=DEFAULT_TRAIN_RATIO)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--train-out", default=None, help="Opcionális kimeneti .jsonl a train résznek.")
    parser.add_argument("--eval-out", default=None, help="Opcionális kimeneti .jsonl az eval résznek.")
    args = parser.parse_args()

    rows = _load_rows(args.path)
    train_rows, eval_rows = split_rows(rows, args.train_ratio, args.seed)

    print(f"Beolvasott sorok: {len(rows)}")
    print(f"Train: {len(train_rows)}, Eval: {len(eval_rows)} (seed={args.seed}, arány={args.train_ratio})")

    if args.train_out:
        _write_jsonl(train_rows, args.train_out)
        print(f"Train fájl kiírva: {args.train_out}")
    if args.eval_out:
        _write_jsonl(eval_rows, args.eval_out)
        print(f"Eval fájl kiírva: {args.eval_out}")


if __name__ == "__main__":
    _main()
