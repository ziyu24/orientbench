#!/usr/bin/env python3
"""Exact path/key validator for r044. No fuzzy or nearest-value matching."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "audit_bundles/r044/claim_spec.csv"
OUT = ROOT / "audit_bundles/r044/claim_check.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def exact_csv(path, key):
    selector, field = key.split("|", 1)
    conditions = []
    for term in selector.split("&"):
        column, value = term.split("=", 1)
        conditions.append((column, value))
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    matches = [r for r in rows if all(r.get(c) == v for c, v in conditions)]
    if len(matches) != 1:
        raise ValueError(f"exact selector matched {len(matches)} rows: {key}")
    if field not in matches[0]:
        raise KeyError(field)
    return matches[0][field]


def transform(value, op):
    if op == "identity": return value
    if op == "float": return float(value)
    if op == "abs": return abs(float(value))
    if op.startswith("round:"): return round(float(value), int(op.split(":", 1)[1]))
    raise ValueError(f"unknown transform {op}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--override", action="append", default=[], help="source_path=replacement_path")
    ap.add_argument("--output", default=str(OUT))
    args = ap.parse_args()
    overrides = dict(x.split("=", 1) for x in args.override)
    failures, inputs = [], {}
    with SPEC.open(newline="", encoding="utf-8") as f:
        specs = list(csv.DictReader(f))
    manuscript = (ROOT / "docs/paper_jprs_r044/orientation_reliability_jprs.md").read_text(encoding="utf-8")
    for s in specs:
        rel = s["source_path"]
        path = Path(overrides.get(rel, str(ROOT / rel)))
        try:
            inputs[rel] = sha(path)
            raw = inputs[rel] if s["source_key"] == "__sha256__" else exact_csv(path, s["source_key"])
            actual = transform(raw, s["transform"])
            if s["transform"] == "identity":
                ok = actual == s["expected"]
            else:
                ok = abs(float(actual) - float(s["expected"])) <= float(s["atol"])
            if not ok:
                failures.append({"claim_id":s["claim_id"], "reason":"value_mismatch", "expected":s["expected"], "actual":actual})
            if ok and s["manuscript_location"].startswith("section:"):
                number = re.escape(s["manuscript_location"].split(":", 1)[1])
                hit = re.search(rf"^### {number}\b", manuscript, flags=re.M)
                if not hit:
                    failures.append({"claim_id":s["claim_id"], "reason":"missing_manuscript_section"})
                else:
                    tail = manuscript[hit.start():]
                    end = re.search(r"^#{2,3} ", tail[len(tail.splitlines()[0])+1:], flags=re.M)
                    section = tail if not end else tail[:len(tail.splitlines()[0])+1+end.start()]
                    if s["expected"] not in section:
                        failures.append({"claim_id":s["claim_id"], "reason":"expected_literal_absent_from_section", "expected":s["expected"], "section":s["manuscript_location"]})
        except Exception as e:
            failures.append({"claim_id":s["claim_id"], "reason":"lookup_error", "detail":str(e)})

    cited = sorted(set(re.findall(r"@([A-Za-z][A-Za-z0-9_]+)", manuscript)))
    bib = (ROOT / "docs/paper_jprs_r044/references.bib").read_text(encoding="utf-8")
    bibkeys = sorted(set(re.findall(r"@[A-Za-z]+\{([^,]+),", bib)))
    with (ROOT / "docs/paper_jprs_r044/reference_audit.csv").open(newline="", encoding="utf-8") as f:
        auditkeys = sorted(r["citation_key"] for r in csv.DictReader(f))
    missing_bib = sorted(set(cited)-set(bibkeys)); missing_audit = sorted(set(cited)-set(auditkeys))
    if missing_bib: failures.append({"claim_id":"CITATIONS", "reason":"missing_bib", "keys":missing_bib})
    if missing_audit: failures.append({"claim_id":"CITATIONS", "reason":"missing_reference_audit", "keys":missing_audit})
    report = {
        "schema_version": 1,
        "status": "PASS" if not failures else "FAIL",
        "total": len(specs),
        "passed": len(specs)-len([x for x in failures if x["claim_id"] != "CITATIONS"]),
        "failed": len(failures),
        "failures": failures,
        "input_sha256": dict(sorted(inputs.items())),
        "citation_audit": {"cited":len(cited), "bib_records":len(bibkeys), "audit_records":len(auditkeys), "missing_bib":missing_bib, "missing_audit":missing_audit},
        "exact_lookup_only": True,
        "nearest_value_matching": False,
    }
    out = Path(args.output); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status":report["status"], "total":report["total"], "failed":report["failed"]}))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
