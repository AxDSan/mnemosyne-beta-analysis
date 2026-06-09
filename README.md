# Mnemosyne Beta Analysis v2 — Independent Reproduction

**Date:** 2026-06-09

On June 7, 2026, Sibyl Labs published a blog post comparing four memory engines (Sibyl, Hindsight, Mem0, Mnemosyne) on a 500-company, 365-day business-memory benchmark. Mnemosyne's published result was **5/350 retrieval**.

We reproduced the benchmark independently. Our result: **317/350 (90.6%)**.

## Our Results

| Category | Correct | Total | Rate |
|----------|---------|-------|------|
| status | 41 | 50 | 82.0% |
| context_stat | 38 | 50 | 76.0% |
| marker | 50 | 50 | 100% |
| milestone | 50 | 50 | 100% |
| role | 50 | 50 | 100% |
| temporal_topic | 38 | 50 | 76.0% |
| negative_trap | 50 | 50 | 100% |
| **Overall** | **317** | **350** | **90.6%** |
| **Ex-trap** | **267** | **300** | **89.0%** |

**Time:** 373 seconds | **Cost:** $0 (local embeddings)

## What We Did

1. **Generated a matching corpus** — 500 companies, 365 days of activity, 236,658 records total
2. **Ingested into Mnemosyne** — direct SQLite batch insert into BEAM working_memory, 236K records in 40 seconds
3. **Ran retrieval-only benchmark** — hybrid recall (FTS5 + sqlite-vec embeddings via fastembed), checking if exact answer appears in top-10 results
4. **Trap questions** — 50 fake company names, all correctly refused (0 results returned)

## Reproducing

```bash
# Generate corpus
python3 generate_corpus.py

# Ingest into Mnemosyne
python3 fast_ingest.py

# Run benchmark
python3 hybrid_bench.py
```

**Prerequisites:** Mnemosyne (pip install mnemosyne-memory[embeddings]), sqlite-vec, fastembed.

## Files

| File | Description |
|------|-------------|
| `corpus.json` | 236,658 business records across 500 companies (365 days) |
| `questions.json` | 350 questions (50 per category + 50 traps) |
| `generate_corpus.py` | Corpus and question generator |
| `fast_ingest.py` | Bulk SQLite batch ingest |
| `hybrid_bench.py` | Hybrid recall benchmark runner |
| `hybrid_results.json` | Raw per-question results |
| `scores.json` | Aggregated scores |

## Notes

The original blog post's Mnemosyne score of 5/350 had no reproducible artifact ("figures from tester's report only"). Our reproduction uses the full hybrid recall pipeline — FTS5 text search + vector embeddings — which the default config may not have enabled. Current-state queries (status, context_stat) are the weakest category because the foundation record has higher keyword density than the latest status checkin. A temporal recency boost would close most of that gap.

## License

MIT
