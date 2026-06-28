# Final Reproducibility Guide

> 2026-06-28 22:14:10 CST | git a54d5364597b

## envs
- mr_dev1x (mmrotate 1.0.0rc1, torch 2.4) — onedl/unknown configs inference.
- ai4rs_train (+ ai4rs_clone projects) — RHINO/A4 host, LSKNet/Strip cross-dataset.
- arsdetr (python3.8, torch1.9.0+cu111, mmcv-full1.5.0, mmdet2.25.1, mmrotate0.1.0, e2cnn) — ARS-DETR.
- mr (mmrotate 0.3.4) — legacy.

## key scripts
- host train: scripts/44/45; freeze: 40/54; formal audit: 41/55/56.
- cross-dataset GT: 64/70 (parsers in scripts/_cross_dataset_parsers.py).
- inference adapters: configs/_adapters/*.py; metrics: 61/65/71/72/73.
- consolidation: 74_final_matrix_summary.py.

## storage
- raw pkl + schema jsonl: /dev/shm/cqc/orientbench/predictions/ (scratch, non-persistent).
- project: per-cell manifest.json (sha256 + scratch path + metrics) + aggregate metrics CSVs.

## thresholds
- configs/thresholds.yaml FROZEN sha256 b7c4e649b1a3de6d…; DO NOT edit.

## verification
- scripts/90-101 + pytest; all green at git a54d5364597b.
