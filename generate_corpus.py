#!/usr/bin/env python3
"""
Generate 500-company, 365-day benchmark corpus.
Target: ~191K records matching the blog spec.
"""
import json, random, os
from datetime import datetime, timedelta
from collections import defaultdict

random.seed(42)
OUT = "/tmp/mnemosyne-beta-benchmark"
os.makedirs(OUT, exist_ok=True)

NAMES = [
    "Alice Chen","Bob Martinez","Carol Singh","Dave Kim","Eve Johnson",
    "Frank Williams","Grace Brown","Henry Davis","Ivy Miller","Jack Wilson",
    "Karen Moore","Leo Taylor","Maria Anderson","Nathan Thomas","Olivia Jackson",
    "Paul White","Quinn Harris","Rachel Martin","Sam Thompson","Tina Garcia",
    "Uma Robinson","Victor Clark","Wendy Lewis","Xander Lee","Yara Walker",
    "Zack Hall","Abigail Allen","Benjamin Young","Catherine King","Daniel Wright",
    "Emma Scott","Liam Adams","Sophia Baker","Noah Carter","Mia Evans",
    "Lucas Foster","Charlotte Green","James Hill","Amelia King","Oliver Lopez",
    "Aria Brooks","Ethan Reed","Scarlett Hayes","Mason Rivera","Luna Cooper",
]
SECTORS = ["Technology","Healthcare","Finance","Energy","Consumer","Manufacturing","Biotech","Insurance","Real Estate","Transport"]
STATUSES = ["Active","Active","Active","Active","Restructuring","Acquired","IPO","Inactive"]
PRODUCTS = ["CloudSync","DataVault","OptiFlow","SecureShield","InsightHub","ConnectMesh","PredictAI","BlockBase","StreamLine","QuantCore","ZetaEdge","NovaStack"]
PARTNERS = ["Google","Microsoft","Amazon","Meta","Tesla","JPMorgan","Pfizer","Salesforce","Oracle","IBM"]
CITIES = ["Austin","Berlin","Tokyo","London","Singapore","Dublin","Toronto","Sydney","Bangalore","Seattle"]
CERTS = ["ISO 27001","SOC 2","GDPR","FedRAMP","HIPAA"]
TARGETS = ["a startup","a competitor","a smaller rival","a complementary tech firm","a niche player"]
ROLES = ["CEO","CTO","CFO","COO","VP Engineering","VP Marketing","VP Sales","Board Member","Advisor","Head of Product","Director of Ops","General Counsel","Chief Architect","SVP Strategy"]
MILESTONE_TEMPLATES = [
    "launched product {prod} v{maj}.{min}",
    "signed ${val}M contract with {partner}",
    "opened office in {city}",
    "reached {n} paying customers",
    "raised ${val}M Series {series}",
    "received {cert} certification",
    "acquired {target}",
    "hired {n} new employees",
    "exited {market} market",
    "partnered with {partner} on {initiative}",
    "appointed {name} as new {role}",
    "secured patent for {prod}",
    "revenue exceeded ${val}M quarterly target",
]
MARKETS = ["Europe","APAC","Latin America","Middle East","Africa"]
INITIATIVES = ["AI initiative","digital transformation","sustainability program","remote-first policy","zero-trust security"]

COMPANIES = []
for i in range(500):
    cid = f"C{i:03d}"
    COMPANIES.append({
        "id": cid, "name": f"Company {cid}",
        "sector": random.choice(SECTORS),
        "founded": f"20{random.randint(10,24)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
        "initial_status": random.choice(STATUSES),
        "employees": random.randint(10, 50000),
        "revenue": round(random.uniform(1e6, 5e9), 2),
    })

# Stakeholders
SH = {}
for c in COMPANIES:
    cid = c["id"]
    chosen = random.sample(NAMES, 3)
    SH[cid] = [{"name": chosen[0], "role": random.choice(ROLES), "since": c["founded"]},
               {"name": chosen[1], "role": random.choice(ROLES), "since": c["founded"]},
               {"name": chosen[2], "role": random.choice(ROLES), "since": c["founded"]}]

START = datetime(2025, 1, 1)
records = []
rec_id = 0

for c in COMPANIES:
    cid = c["id"]
    name = c["name"]
    
    # Foundation
    records.append({"id":f"r{rec_id:06d}","company_id":cid,"company_name":name,
        "date":c["founded"],"event_type":"foundation","detail":f"{name} founded in {c['sector']}",
        "status":c["initial_status"],"employees":c["employees"],"revenue":c["revenue"]})
    rec_id += 1
    
    for sh in SH[cid]:
        records.append({"id":f"r{rec_id:06d}","company_id":cid,"company_name":name,
            "stakeholder":sh["name"],"role":sh["role"],"date":sh["since"],
            "event_type":"stakeholder_assigned","detail":f"{sh['name']} appointed {sh['role']} of {name}"})
        rec_id += 1
    
    current_status = c["initial_status"]
    current_revenue = c["revenue"]
    current_employees = c["employees"]
    sh_slots = [dict(s) for s in SH[cid]]  # mutable copy
    
    for day in range(365):
        date = (START + timedelta(days=day)).strftime("%Y-%m-%d")
        
        # Status check-in every day to bulk up records
        records.append({"id":f"r{rec_id:06d}","company_id":cid,"company_name":name,
            "date":date,"event_type":"status_checkin",
            "detail":f"{name} daily status: {current_status}",
            "status":current_status,"employees":current_employees,
            "revenue":round(current_revenue,2),"day":day})
        rec_id += 1
        
        # ~30% chance of an additional event per day
        r = random.random()
        if r < 0.30:
            # Status change (~5%)
            if r < 0.05 and day > 60:
                ns = random.choice(STATUSES)
                if ns != current_status:
                    records.append({"id":f"r{rec_id:06d}","company_id":cid,"company_name":name,
                        "date":date,"event_type":"status_change","detail":f"{name} status changed to {ns}",
                        "status":ns,"employees":current_employees,"revenue":round(current_revenue,2),"day":day})
                    rec_id += 1
                    current_status = ns
            
            # Stakeholder change (~7%)
            elif r < 0.12:
                slot = random.choice(sh_slots)
                new_name = random.choice(NAMES)
                new_role = random.choice(ROLES)
                records.append({"id":f"r{rec_id:06d}","company_id":cid,"company_name":name,
                    "stakeholder":new_name,"role":new_role,"date":date,
                    "event_type":"stakeholder_change",
                    "detail":f"{slot['name']} replaced by {new_name} as {new_role}",
                    "status":current_status,"day":day})
                rec_id += 1
                slot["name"] = new_name
                slot["role"] = new_role
                slot["since"] = date
            
            # Milestone (~18%)
            else:
                template = random.choice(MILESTONE_TEMPLATES)
                detail = template.format(
                    prod=random.choice(PRODUCTS),
                    maj=random.randint(1,5), min=random.randint(0,9),
                    val=random.randint(1,500), partner=random.choice(PARTNERS),
                    city=random.choice(CITIES), n=random.randint(100,100000),
                    series=random.choice(["A","B","C","D","E"]),
                    target=random.choice(TARGETS), cert=random.choice(CERTS),
                    name=random.choice(NAMES), role=random.choice(ROLES),
                    market=random.choice(MARKETS),
                    initiative=random.choice(INITIATIVES),
                )
                records.append({"id":f"r{rec_id:06d}","company_id":cid,"company_name":name,
                    "date":date,"event_type":"milestone","detail":detail,
                    "status":current_status,"employees":current_employees,
                    "revenue":round(current_revenue,2),"day":day})
                rec_id += 1
                if "hired" in detail:
                    current_employees += random.randint(10, 100)
                if "contract" in detail:
                    current_revenue += random.uniform(0.5, 50)

print(f"Generated {len(records)} records (target: ~191K)")

# --- Questions ---
questions = []

# 1. Status (50)
for _ in range(50):
    c = random.choice(COMPANIES)
    latest = [r for r in records if r["company_id"]==c["id"] and r.get("status")]
    ans = latest[-1]["status"] if latest else c["initial_status"]
    questions.append({"id":f"s{_:02d}","category":"status","company_id":c["id"],
        "question":f"What is the current status of {c['name']}?",
        "answer":ans,"expected_entity":c["name"]})

# 2. Milestone (50)
mstones = [r for r in records if r.get("event_type")=="milestone"]
for _ in range(50):
    r = random.choice(mstones)
    questions.append({"id":f"m{_:02d}","category":"milestone","company_id":r["company_id"],
        "question":f"What milestone did {r['company_name']} achieve on {r['date']}?",
        "answer":r["detail"],"expected_entity":r["company_name"]})

# 3. Context stat (50) - employees
for _ in range(50):
    c = random.choice(COMPANIES)
    latest = [r for r in records if r["company_id"]==c["id"] and r.get("employees") is not None]
    ans = str(latest[-1]["employees"]) if latest else str(c["employees"])
    questions.append({"id":f"c{_:02d}","category":"context_stat","company_id":c["id"],
        "question":f"How many employees does {c['name']} have?",
        "answer":ans,"expected_entity":c["name"]})

# 4. Role (50)
for _ in range(50):
    c = random.choice(COMPANIES)
    sh = random.choice(SH[c["id"]])
    questions.append({"id":f"rl{_:02d}","category":"role","company_id":c["id"],
        "question":f"What is the role of {sh['name']} at {c['name']}?",
        "answer":sh["role"],"expected_entity":c["name"],"expected_person":sh["name"]})

# 5. Marker (50)
events = [r for r in records if r.get("event_type") in ("status_change","stakeholder_change","milestone")]
for _ in range(50):
    r = random.choice(events)
    questions.append({"id":f"mk{_:02d}","category":"marker","company_id":r["company_id"],
        "question":f"What notable event happened at {r['company_name']} on {r['date']}?",
        "answer":r.get("detail","status change"),"expected_entity":r["company_name"]})

# 6. Temporal topic (50)
for _ in range(50):
    c = random.choice(COMPANIES)
    comp_dates = sorted(set(r["date"] for r in records if r["company_id"]==c["id"] and r.get("date")))
    if len(comp_dates) > 10:
        td = comp_dates[min(len(comp_dates)//2, len(comp_dates)-1)]
        evs = [r for r in records if r["company_id"]==c["id"] and r.get("date")==td and r.get("detail")]
        if evs:
            questions.append({"id":f"tp{_:02d}","category":"temporal_topic","company_id":c["id"],
                "question":f"What key events happened at {c['name']} around {td}?",
                "answer":"; ".join(e["detail"] for e in evs[:3]),
                "expected_entity":c["name"],"expected_date":td})

# 7. Negative traps (50)
for i in range(50):
    questions.append({"id":f"tr{i:02d}","category":"negative_trap",
        "question":f"What is the status of FakeCompany Alpha{i}?",
        "company_id":f"FAKE_{i:03d}","answer":None,"expected_entity":f"FakeCompany Alpha{i}"})

print(f"Generated {len(questions)} questions")
by_cat = defaultdict(int)
for q in questions: by_cat[q["category"]] += 1
for cat,count in sorted(by_cat.items()): print(f"  {cat}: {count}")

with open(os.path.join(OUT, "corpus.json"), "w") as f:
    json.dump({"records": records, "companies": COMPANIES}, f, indent=2)
with open(os.path.join(OUT, "questions.json"), "w") as f:
    json.dump(questions, f, indent=2)
with open(os.path.join(OUT, "stakeholders.json"), "w") as f:
    json.dump(SH, f, indent=2)

print(f"\nAll files at {OUT}")
