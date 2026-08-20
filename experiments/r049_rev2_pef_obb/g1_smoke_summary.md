# G1 implementation and four-GPU smoke summary

- `PeriodicEvidenceField` has 12 `theta mod pi` candidates; each candidate
  rotates the FPN `grid_sample` offsets before the shared scorer sees them.
  It emits a normalized `q`, axial refined angle, and fixed tail-mass risk.
- `pytest -q experiments/r049_rev2_pef_obb/test_pef_field.py`: 4 passed.
- PEF: DOTA/PSC four-A30 500 iteration all-parameter smoke completed normally.
  Final logged `loss_pef=0.6180`, total gradient norm `3.1332`; full-val ran.
- DIRECT_DIST and SCALAR_QUALITY: each four-A30 20-iteration integration smoke
  completed normally before full validation.  Their zero-initialization mAP is
  expected and is not used as a science result.
- All G1 outputs use DOTA-v1.0 train/val only.  No forbidden endpoint or GT
  inference input was used in the PEF forward path.
