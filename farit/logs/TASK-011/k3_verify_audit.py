#!/usr/bin/env python3
"""K3 verification of TASK-011 (annotation audit), independent recompute.

Checks:
  W1. Every verdict quote in farit/results/annotation_audit.json occurs verbatim on
      the cited page of units_native.jsonl (independent of apply_verdicts.py).
  W2. Broken-evidence-ref recount: every gold evidence_set fragment of the audited
      instances resolves verbatim at its cited page -> recount the "0/49" claim.
  W3. Sample composition: A=8, B=8, C=4, D=10 (N/A 5, NOT_STATED 3, NO_DATA 2), E=10;
      unique instances = 38; verdict counts 34/2/4.
  W4. Dev-only: no locked document (sds_21+) anywhere in the sample.
Run from repo root: ~/ds_env/bin/python farit/logs/TASK-011/k3_verify_audit.py
"""
import json
from collections import Counter

PAGE_UNPATCHED = "\n".join  # placeholder to avoid empty-line artifacts? no—use raw text

units = {}
for line in open("farit/data/corpus/units_native.jsonl"):
    u = json.loads(line)
    units[(u["document"], u["page"])] = u

recs = json.load(open("farit/results/annotation_audit.json"))
assert len(recs) == 40

# ---- W4: dev-only
locked = [r["document"] for r in recs if int(r["document"].split("_")[1].split(".")[0]) >= 21]
print(f"[W4] locked documents in sample: {locked or 'none'}")

# ---- W1: verbatim quote check
fails = 0
nq = 0
for r in recs:
    for q in r["quotes"]:
        nq += 1
        u = units.get((r["document"], q["page"]))
        if u is None:
            print(f"  MISSING PAGE {r['document']} p{q['page']}")
            fails += 1
            continue
        if q["text"] not in u["text"]:
            print(f"  NOT VERBATIM {r['document']} p{q['page']}: {q['text'][:60]!r}")
            fails += 1
print(f"[W1] quotes: {nq} checked, {fails} failures")

# ---- W2: gold evidence_set fragments of the audited instances
gold = {}
for line in open("farit/data/corpus/gold_evidence.jsonl"):
    g = json.loads(line)
    gold[(g["document"], g["field"])] = g

insts = {(r["document"], r["field"]) for r in recs}
frag_fail = 0
nfrag = 0
for key in sorted(insts):
    g = gold.get(key)
    if g is None:
        print(f"  INSTANCE NOT IN gold_evidence.jsonl: {key}")
        continue
    for ev in g.get("evidence_set", []):
        nfrag += 1
        u = units.get((g["document"], ev["page"]))
        if u is None or ev["text"] not in u["text"]:
            print(f"  BROKEN FRAGMENT {key} p{ev['page']}: {ev['text'][:60]!r}")
            frag_fail += 1
print(f"[W2] gold evidence fragments over audited instances: {nfrag}, broken: {frag_fail}")

# ---- W3: composition
groups = Counter(r["group"] for r in recs)
verdicts = Counter(r["verdict"] for r in recs)
d_states = Counter(r["state"] for r in recs if r["group"] == "D")
uniq = len(insts)
e_set = {(r["document"], r["field"]) for r in recs if r["group"] == "E"}
a_set = {(r["document"], r["field"]) for r in recs if r["group"] == "A"}
print(f"[W3] groups: {dict(sorted(groups.items()))}")
print(f"[W3] D states: {dict(d_states)}")
print(f"[W3] verdicts: {dict(verdicts)}, unique instances: {uniq}, E∩A: {len(e_set & a_set)}")
