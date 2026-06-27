#!/usr/bin/env python3
"""25_collaborator_form.py — emit collaborator decision form (all items pending)."""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from orientbench.reports.readiness import build_collaborator_form  # noqa: E402

REPORT_DIR = os.path.join(_PROJECT_ROOT, "outputs", "bench_core", "reports")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--timestamp", default=None)
    args = ap.parse_args(argv)
    ts = args.timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S (local)")
    os.makedirs(REPORT_DIR, exist_ok=True)
    with open(os.path.join(REPORT_DIR, "collaborator_decision_form.md"), "w", encoding="utf-8") as fh:
        fh.write(build_collaborator_form(ts))
    print("[ok] wrote collaborator_decision_form.md (all items pending)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
