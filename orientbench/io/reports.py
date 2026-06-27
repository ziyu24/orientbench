"""Small IO helpers for report/CSV/JSONL writing."""
from __future__ import annotations

import csv
import json
import os
from typing import Any, Dict, Iterable, List, Optional


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def write_jsonl(path: str, records: Iterable[Dict[str, Any]]) -> int:
    n = 0
    with open(path, "w", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
            n += 1
    return n


def read_jsonl(path: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if not os.path.isfile(path):
        return out
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def write_csv(path: str, records: List[Dict[str, Any]], columns: Optional[List[str]] = None) -> int:
    if columns is None:
        columns = list(records[0].keys()) if records else []
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=columns, extrasaction="ignore")
        w.writeheader()
        for r in records:
            row = {}
            for k in columns:
                v = r.get(k)
                if isinstance(v, (list, dict)):
                    v = " | ".join(map(str, v)) if isinstance(v, list) else json.dumps(v, ensure_ascii=False)
                row[k] = "" if v is None else v
            w.writerow(row)
    return len(records)


def write_json(path: str, obj: Any) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=2)
