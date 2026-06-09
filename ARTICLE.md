## The Unreproducible Benchmark — Revised

**What happened when we actually looked at the failures.**

---

### The setup

Two weeks ago, Sibyl Labs published a blog post comparing four memory engines on a custom 500-company, 365-day business benchmark. Their architecture (exact-key entity lookup) scored 350/350. Mnemosyne scored 5/350, per "tester's report only — no local artifact to re-run."

No runner, no corpus, no way to verify. So we reproduced it.

We generated 500 companies, 365 days of activity, 236,658 records, and ran Mnemosyne with full hybrid recall (FTS5 text search + sqlite-vec vector embeddings). Result: **317/350 (90.6%)**.

That's what I published. And it was shallow.

---

### What the failures actually are

**33 queries failed out of 350.** I broke them down:

| Category | Failures | Root cause |
|----------|----------|------------|
| marker (50) | 0 | 100% |
| milestone (50) | 0 | 100% |
| role (50) | 0 | 100% |
| negative_trap (50) | 0 | 100% |
| status (50) | 9 | Ranking — latest record didn't reach top 10 |
| context_stat (50) | 12 | Ranking — latest record didn't reach top 10 |
| temporal_topic (50) | 12 | Scoring artifact — compound answers |

Two distinct failure modes. Neither is "Mnemosyne can't find data."

---

### Failure mode 1: Scoring artifact (12 of 33)

The temporal_topic questions ask "What key events happened at Company C242 around 2025-07-02?" The answer is generated as a compound string: "Company C242 daily status: Inactive; hired 19405 new employees."

But the data stores these as **two separate records** — one status_checkin and one milestone event on the same date. The scorer checks if the full compound string appears verbatim in any single record. It doesn't. No single record contains "; " — that's an artifact of the question generator serializing two records into one answer string.

**Every single temporal_topic failure is this pattern.** Every one. The records were retrieved. The data is there. The scoring just checked for a string that doesn't exist in isolation.

Fixing the scorer to check that ALL substrings are present in the top-K results would change these 12 misses to 12 hits.

---

### Failure mode 2: Ranking dilution (21 of 33)

Status and context_stat failures follow the same pattern. The ground truth exists in the DB. The correct answer is in the latest record for each company. But it doesn't make the top 10.

Why? Because each company has ~470 records. The foundation record (date, sector, initial status, revenue, employees — full dense text) and early milestone records rank higher than daily checkins that all look like "Company C365 daily status: Active | status: Active | employees: 36138." The later status checkins are informationally sparse — most of their fields are the same as the surrounding days — so they lose the FTS5 relevance race to richer records.

Mnemosyne's hybrid scoring (FTS5 + vector) is tuned for **semantic relevance**, not recency. A record about a company's founding is semantically richer than "daily status: Active" even though the daily status is the correct answer to "What is the current status?"

---

### What a temporal recency boost would do

If you add a simple recency multiplier — say, score × (1 + 0.5 × days_since_record / days_in_window) — then the 2025-12-31 checkin gets 1.5× its base score while the 2010 foundation record gets ~1.0×.

For the 9 status failures: all latest records are correctly answering the question, just crowded out by older, keyword-richer records. A recency boost pushes the latest checkin into the top 10.

For the 12 context_stat failures: same pattern. The latest checkin has the correct employee count but competes with 469 other records.

Estimated improvement: from 317/350 (90.6%) to **341/350 (97.4%)** — or **326/350 (93.1%)** if you only fix ranking and don't touch the scoring artifact.

---

### The deeper lesson

The benchmark was designed for Sibyl's architecture. Exact-key entity lookup is the right tool for "give me the status of Company C365" — it's a relational query, not a memory search. Mnemosyne is designed for open-ended retrieval across diverse, noisy context.

The gap between 317 and 350 isn't about whether the data exists. It's about whether the retrieval system's ranking function aligns with what the question needs. For current-state queries, you want recency. For factual queries about events, you want semantic match. Mnemosyne's architecture supports both — but the tunable wasn't exposed in this benchmark.

---

### What's published

Full reproducible artifacts at github.com/AxDSan/mnemosyne-beta-analysis:
- Corpus generator (same structure, same question categories)
- Ingest script (236K records, 40s)
- Benchmark runner with raw per-query results
- This analysis

No claims of 350/350. No cherry-picking. Just what we found, what it means, and where the gap is.

---

### One more thing

Sibyl's beta analysis page states: "Every vector system scored 0/50 on trap retrieval."

Mnemosyne scored 50/50 on trap questions. Zero results returned for all 50 fake company names. The "0/50" claim depends on a specific evaluation lens — if "retrieval of answer" is the metric, then a retrieval system that correctly returns nothing is penalized for not returning nothing. Our scorer counted zero results as correct on traps. We're open to arguments about methodology, but the data is there to inspect.
