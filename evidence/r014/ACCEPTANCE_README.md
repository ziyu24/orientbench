# r014 remaining acceptance evidence

This supplement records the read-only remaining-acceptance checks performed after
the corrected raw probabilities and statistics already present in this ref.

- `acceptance_pixel_records.jsonl`: one independently selected official source and
  pixel comparison for each of the 7,416 calibration objects.
- `acceptance_summary.json`: full-source and old-canvas counts plus the available
  (and unavailable) original execution records.
- `render_acceptance_raw.json` and `render_acceptance_decision.json`: production
  renderer versus independent-reference results for every calibration source,
  including all 20 affected loc--CAT keys.  The 5e-5 tolerance is explicitly a
  post-hoc reconstruction-precision check, not a preregistered scientific gate.
- `independent_acceptance.json`: no-producer-import statistical recomputation and
  actual input-mutation rejection results.

No model was trained or evaluated, and no test pixel or test metric was opened.
Missing original r013 fit and calibration manifests keep the final status at
`INCONCLUSIVE_R013_H1A / INPUT_OR_IMPLEMENTATION`.
