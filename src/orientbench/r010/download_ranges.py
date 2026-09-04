"""Bounded ranged downloader for the two explicitly-listed official S3 objects."""
from __future__ import annotations
import argparse
import concurrent.futures
import os
import urllib.request
from pathlib import Path

def fetch(url: str, target: Path, expected: int, workers: int, block: int, restart: bool) -> None:
    partial = target.with_name(target.name + ".r010.partial")
    if restart:
        partial.unlink(missing_ok=True)
        target.unlink(missing_ok=True)
    if partial.exists() and partial.stat().st_size != expected:
        partial.unlink()
    if not partial.exists():
        with partial.open("wb") as f: f.truncate(expected)
    spans = [(start, min(expected - 1, start + block - 1)) for start in range(0, expected, block)]
    fd = os.open(partial, os.O_WRONLY)
    def one(span):
        start, end = span
        request = urllib.request.Request(url, headers={"Range": f"bytes={start}-{end}"})
        with urllib.request.urlopen(request, timeout=180) as response:
            data = response.read()
            received = response.headers.get("Content-Range", "")
        if len(data) != end - start + 1 or not received.startswith(f"bytes {start}-{end}/"):
            raise RuntimeError(f"range validation failed {start}-{end}: {received}, {len(data)} bytes")
        offset = 0
        while offset < len(data): offset += os.pwrite(fd, data[offset:], start + offset)
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
            list(pool.map(one, spans))
    finally: os.close(fd)
    if partial.stat().st_size != expected: raise RuntimeError("local length mismatch")
    os.replace(partial, target)

def main():
    p = argparse.ArgumentParser(); p.add_argument("--url", required=True); p.add_argument("--out", type=Path, required=True); p.add_argument("--bytes", type=int, required=True); p.add_argument("--workers", type=int, default=16); p.add_argument("--block-mib", type=int, default=16); p.add_argument("--restart", action="store_true"); a = p.parse_args()
    a.out.parent.mkdir(parents=True, exist_ok=True)
    fetch(a.url, a.out, a.bytes, a.workers, a.block_mib * 1024 * 1024, a.restart)
if __name__ == '__main__': main()
