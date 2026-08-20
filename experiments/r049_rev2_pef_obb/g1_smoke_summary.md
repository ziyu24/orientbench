# G1 implementation and four-GPU smoke summary

- Historical pre-geometry smoke is retained only as engineering evidence: its
  grid did not encode candidate box width/height and is not admissible for G2.
- Geometry-repaired `PeriodicEvidenceField` has 12 `theta mod pi` candidates;
  each candidate rotates fixed fractions of the same FPN anchor candidate
  box's width/height before the shared scorer sees visual evidence.  It emits
  normalized `q`, axial refined angle, and fixed tail-mass risk.
- `pytest -q experiments/r049_rev2_pef_obb/test_pef_field.py`: 5 passed.
- Repaired PEF: DOTA/PSC four-A30 500-iteration all-parameter smoke completed
  normally at `outputs/persistent_artifacts/orientbench_r049_rev2_pef_obb_20260819/g1/dota_psc_pef_geometry_smoke_500/train.log`.
  Final validation and checkpoint completed; the recorded `loss_pef` and
  post-AMP global gradient norm were finite.
- DIRECT_DIST and SCALAR_QUALITY: each four-A30 20-iteration integration smoke
  completed normally before full validation.  Their zero-initialization mAP is
  expected and is not used as a science result.
- All G1 outputs use DOTA-v1.0 train/val only.  No forbidden endpoint or GT
  inference input was used in the repaired PEF forward path.
