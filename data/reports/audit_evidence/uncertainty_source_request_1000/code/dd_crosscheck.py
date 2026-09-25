# -*- coding: utf-8 -*-
"""Az elo-szuresek helyessegenek igazolasa: az EREDETI tools/dataset_dedupe.find_duplicates() (szuretlen difflib) futtatasa egy reszhalmazon
(osszes simple_qa + step_by_step sor, ahol az ismert talalatok vannak) es az eredmeny osszevetese a szakaszolt modszer talalataival."""
import glob, json, os, sys, time
REPO = r"C:\Users\Lenovo\OneDrive\Dokumentumok\MF-AI-Zero"
sys.path.insert(0, os.path.join(REPO, "tools"))
from dataset_dedupe import find_duplicates
sub = []
for f in sorted(glob.glob(os.path.join(REPO, "data", "clean", "*.jsonl"))):
    b = os.path.basename(f)
    if "simple_qa" in b or "step_by_step" in b or "deepseek" in b:
        for l in open(f, encoding="utf-8"):
            if l.strip():
                sub.append(json.loads(l))
print("reszhalmaz sorok:", len(sub), flush=True)
ent = [{"row_number": i + 1, "row": r} for i, r in enumerate(sub)]
t0 = time.time()
rep = find_duplicates(ent)
print("eredeti tool futasido: %.0fs" % (time.time() - t0))
print("id:", len(rep["id_duplicates"]), "| task:", [(sub[d["duplicate"] - 1]["id"], sub[d["kept"] - 1]["id"], d["similarity"]) for d in rep["instruction_duplicates"]],
      "| output:", [(sub[d["duplicate"] - 1]["id"], sub[d["kept"] - 1]["id"], d["similarity"]) for d in rep["output_duplicates"]])
