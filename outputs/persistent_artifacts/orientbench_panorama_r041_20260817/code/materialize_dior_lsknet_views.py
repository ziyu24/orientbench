#!/usr/bin/env python3
"""Materialize output-local DIOR flips for a detector without aug_test."""
from __future__ import annotations

import argparse
import multiprocessing as mp
import os
from pathlib import Path

import cv2

ROOT = Path('/home/rspip/cqc/pro/study/orientbench/outputs/persistent_artifacts/orientbench_panorama_r041_20260817/input_views')
SOURCE = ROOT / 'dior_png_aliases'


def materialize(job: tuple[str, str]) -> str:
    source_text, direction = job
    source = Path(source_text)
    name = source.stem
    jpg_dir = ROOT / f'dior_{direction}_jpg'
    png_dir = ROOT / f'dior_{direction}_png'
    jpg = jpg_dir / f'{name}.jpg'
    alias = png_dir / f'{name}.png'
    if not jpg.exists():
        image = cv2.imread(str(source), cv2.IMREAD_COLOR)
        if image is None:
            raise RuntimeError(f'unreadable input: {source}')
        code = 1 if direction == 'hflip' else 0
        ok, encoded = cv2.imencode('.jpg', cv2.flip(image, code), [cv2.IMWRITE_JPEG_QUALITY, 95])
        if not ok:
            raise RuntimeError(f'encode failed: {source}')
        temporary = jpg.with_suffix('.tmp')
        temporary.write_bytes(encoded.tobytes())
        os.replace(temporary, jpg)
    if not alias.exists():
        alias.symlink_to(Path('..') / jpg_dir.name / jpg.name)
    return name


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('direction', choices=('hflip', 'vflip'))
    parser.add_argument('--workers', type=int, default=40)
    args = parser.parse_args()
    jpg_dir = ROOT / f'dior_{args.direction}_jpg'
    png_dir = ROOT / f'dior_{args.direction}_png'
    jpg_dir.mkdir(parents=True, exist_ok=True)
    png_dir.mkdir(parents=True, exist_ok=True)
    sources = sorted(SOURCE.glob('*.png'))
    if len(sources) != 11738:
        raise RuntimeError(f'expected 11738 source aliases, found {len(sources)}')
    with mp.Pool(processes=args.workers) as pool:
        jobs = ((str(p), args.direction) for p in sources)
        for index, _ in enumerate(pool.imap_unordered(materialize, jobs, chunksize=16), 1):
            if index % 500 == 0 or index == len(sources):
                print(f'{args.direction} {index}/{len(sources)}', flush=True)


if __name__ == '__main__':
    main()
