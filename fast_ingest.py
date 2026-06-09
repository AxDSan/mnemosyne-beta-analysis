#!/usr/bin/env python3
"""Fast direct-ingest for beta benchmark. Batch INSERT into working_memory."""
import json, os, sys, time, hashlib, shutil
from datetime import datetime

OUT = "/tmp/mnemosyne-beta-benchmark"
BENCH_BANK = "beta_bench_6"
DATA_DIR = os.path.join(OUT, "mnemosyne_data")
os.environ["MNEMOSYNE_DATA_DIR"] = DATA_DIR

from mnemosyne.core.banks import BankManager
from mnemosyne.core.beam import init_beam
from mnemosyne.core.memory import _get_connection

for d in [os.path.join(DATA_DIR, "banks"), os.path.join(DATA_DIR, "mnemosyne.db")]:
    if os.path.exists(d):
        if os.path.isdir(d): shutil.rmtree(d)
        else: os.remove(d)

bm = BankManager()
try: bm.create_bank(BENCH_BANK)
except: pass
BANK_DB = bm.get_bank_db_path(BENCH_BANK)
init_beam(BANK_DB)
conn = _get_connection(BANK_DB)
cursor = conn.cursor()

with open(os.path.join(OUT, "corpus.json")) as f:
    records = json.load(f)["records"]
print(f"Loaded {len(records)} records")

SAMPLE = None
for i, arg in enumerate(sys.argv):
    if arg == "--sample" and i+1 < len(sys.argv):
        SAMPLE = int(sys.argv[i+1])
if SAMPLE:
    records = records[:SAMPLE]
    print(f"Sample: {SAMPLE}")

start = time.time()
batch = []
BATCH_SIZE = 2500

COLUMNS = "id, content, source, timestamp, session_id, importance, veracity, scope, consolidated_at, event_date"
PLACEHOLDERS = "?, ?, ?, ?, ?, ?, ?, ?, 0, ?"

for i, rec in enumerate(records):
    parts = [f"[{rec['company_id']}] {rec['company_name']}"]
    for field in ["date","event_type","detail","status","stakeholder","role"]:
        if rec.get(field): parts.append(f"| {field}: {rec[field]}")
    if rec.get("employees") is not None: parts.append(f"| employees: {rec['employees']}")
    if rec.get("revenue") is not None: parts.append(f"| revenue: {rec['revenue']}")
    content = " ".join(parts)
    
    mid = hashlib.sha256(f"{content}{i}".encode()).hexdigest()[:16]
    ts = datetime.now().isoformat()
    event_date = rec.get("date", "2000-01-01")
    
    batch.append((mid, content, "benchmark_ingest", ts, "bench", 0.8, "tool", "session", event_date))
    
    if len(batch) >= BATCH_SIZE:
        cursor.executemany(f"INSERT OR IGNORE INTO working_memory ({COLUMNS}) VALUES ({PLACEHOLDERS})", batch)
        conn.commit()
        batch = []
    
    if (i+1) % 100000 == 0:
        elapsed = time.time() - start
        print(f"  {i+1}/{len(records)} ({elapsed:.1f}s, {(i+1)/elapsed:.0f}/s)")

if batch:
    cursor.executemany(f"INSERT OR IGNORE INTO working_memory ({COLUMNS}) VALUES ({PLACEHOLDERS})", batch)
    conn.commit()

elapsed = time.time() - start
cursor.execute("SELECT COUNT(*) FROM working_memory")
wm = cursor.fetchone()[0]
print(f"\nDone: {wm} rows in {elapsed:.1f}s ({wm/elapsed:.0f}/s)")
print(f"DB: {BANK_DB}")

with open(os.path.join(OUT, "bank_path.txt"), "w") as f:
    f.write(BANK_DB)
