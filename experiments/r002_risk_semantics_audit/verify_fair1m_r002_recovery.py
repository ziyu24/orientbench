#!/usr/bin/env python3
"""Independently verify the recovered FAIR1M r002 DOTA annotation contract."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def tree_digest(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in paths:
        digest.update(path.name.encode("utf-8"))
        digest.update(file_sha256(path).encode("ascii"))
    return digest.hexdigest()


def inspect(path: Path) -> tuple[int, int, int]:
    objects = difficulty_zero = difficulty_one = 0
    for line in path.read_text(encoding="utf-8", errors="strict").splitlines():
        fields = line.split()
        if len(fields) < 10:
            raise ValueError(f"malformed DOTA row in {path.name}")
        try:
            [float(value) for value in fields[:8]]
            difficulty = int(fields[-1])
        except ValueError as exc:
            raise ValueError(f"malformed DOTA row in {path.name}") from exc
        if difficulty not in (0, 1):
            raise ValueError(f"unexpected difficulty {difficulty} in {path.name}")
        objects += 1
        difficulty_zero += difficulty == 0
        difficulty_one += difficulty == 1
    return objects, difficulty_zero, difficulty_one


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--annotation-dir", required=True, type=Path)
    parser.add_argument("--expected-files", type=int, default=4362)
    parser.add_argument("--expected-tree-sha256", required=True)
    args = parser.parse_args()
    paths = sorted(args.annotation_dir.glob("*.txt"))
    counts = [inspect(path) for path in paths]
    report = {
        "annotation_files": len(paths),
        "annotation_objects": sum(row[0] for row in counts),
        "difficulty_zero_objects": sum(row[1] for row in counts),
        "difficulty_one_objects": sum(row[2] for row in counts),
        "observed_tree_sha256": tree_digest(paths),
        "expected_tree_sha256": args.expected_tree_sha256,
    }
    report["ok"] = bool(
        len(paths) == args.expected_files
        and report["observed_tree_sha256"] == args.expected_tree_sha256
    )
    print(json.dumps(report, sort_keys=True))
    if not report["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
