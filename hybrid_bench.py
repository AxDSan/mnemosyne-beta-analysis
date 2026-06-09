#!/usr/bin/env python3
"""Full hybrid recall benchmark. Writes to dedicated file."""
import json, os, sys, time
from collections import defaultdict

BANK_DB = "/tmp/mnemosyne-beta-benchmark/mnemosyne_data/banks/beta_bench_6/mnemosyne.db"
OUT = "/tmp/mnemosyne-beta-benchmark"
sys.path.insert(0, "/root/.hermes/projects/mnemosyne")
from mnemosyne.core.beam import BeamMemory

beam = BeamMemory(session_id="bench", db_path=str(BANK_DB))

with open(os.path.join(OUT, "questions.json")) as f:
    questions = json.load(f)

from mnemosyne.core import embeddings as _embeddings
_embeddings.embed_query("warmup")
print("Warmup done", flush=True)

results = []
by_cat = defaultdict(list)
start = time.time()

for idx, q in enumerate(questions):
    cat = q["category"]
    qid = q["id"]
    answer = q.get("answer")
    answer_str = str(answer) if answer else ""
    
    recalled = beam.recall(q["question"], top_k=10)
    
    if cat == "negative_trap":
        correct = len(recalled) == 0
    else:
        correct = any(answer_str in r.get("content", "") for r in recalled) if answer else False
    
    results.append({"id": qid, "category": cat, "retrieval": correct, "num_results": len(recalled)})
    by_cat[cat].append(correct)
    
    if (idx + 1) % 50 == 0:
        oc = sum(1 for r in results if r["retrieval"])
        elapsed = time.time() - start
        print(f"  {idx+1}/350 - {oc}/{idx+1} ({oc/(idx+1)*100:.1f}%) - {elapsed:.0f}s", flush=True)

elapsed = time.time() - start

oc = ot = 0
for cat in sorted(by_cat.keys()):
    items = by_cat[cat]
    c = sum(1 for x in items if x)
    t = len(items)
    p = round(c/t*100, 1) if t else 0
    oc += c; ot += t
    print(f"{cat:<20} {c:>8} {t:>8} {p:>7.1f}%")

ex_trap = [r for r in results if r["category"] != "negative_trap"]
etc = sum(1 for r in ex_trap if r["retrieval"])
ett = len(ex_trap)
etp = round(etc/ett*100, 1) if ett else 0

print("-"*48)
print(f"{'OVERALL':<20} {oc:>8} {ot:>8} {round(oc/ot*100,1):>7.1f}%")
print(f"{'OVERALL (ex-trap)':<20} {etc:>8} {ett:>8} {etp:>7.1f}%")

with open(os.path.join(OUT, "hybrid_results.json"), "w") as f:
    json.dump({"elapsed": round(elapsed,1), "overall": oc, "total": ot, "pct": round(oc/ot*100,1), "ex_trap_pct": etp, "results": results}, f)
