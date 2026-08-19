# Large-candidate deletion dossier

No target in this dossier has been deleted.  SHA-256 equality was checked
before listing exact duplicates.

## Group D — exact duplicate copies: 2.5 GiB reclaimable

Delete only the listed redundant copies, retaining their canonical twins.

| Redundant copy | Canonical retained copy | SHA-256 equality | Recovery |
|---|---|---|---|
| `orientbench_r010/{unit_FAIR1M-v1.0_24.json,details_SODA-A_4.pkl,unit_DIOR-R_22.json,unit_DIOR-R_61.json,unit_DIOR-R_3.json,unit_SODA-A_4.json}` | identical file under `orientbench_r011/` | verified | copy the r011 twin back to r010 |
| four mutation copies of `track_m_risk_coverage.csv` | `orientbench_topjournal_feasibility_receipt3_20260811/track_m_risk_coverage.csv` | verified | copy the canonical CSV back into each mutation evidence directory |
| `orientbench_v2_047/track_a_dumps/SODA-A_23.pkl` | `orientbench_v2_047/tta_preds/SODA-A_23/identity.pkl` | verified | copy the retained identity pickle back |

## Group E — materialized DIOR flip images: 5.3 GiB reclaimable

Delete only `input_views/dior_hflip_jpg/`, `input_views/dior_hflip_png/`,
`input_views/dior_vflip_jpg/`, and `input_views/dior_vflip_png/`.  Retain
`dior_png_aliases/`, the generated source script, normalized matched rows and
prediction dumps.

Exact rebuild commands, run from the project root:

```bash
PYTHONNOUSERSITE=1 conda run --no-capture-output -n pcp-obb python \
  outputs/persistent_artifacts/orientbench_panorama_r041_20260817/code/materialize_dior_lsknet_views.py hflip --workers 40
PYTHONNOUSERSITE=1 conda run --no-capture-output -n pcp-obb python \
  outputs/persistent_artifacts/orientbench_panorama_r041_20260817/code/materialize_dior_lsknet_views.py vflip --workers 40
```

The scripts deterministically rebuild 11,738 JPEG flips at quality 95 from
the retained PNG aliases and recreate the PNG symlinks.

## Still under audit

Do not delete `m069_psc_phase1` (5.7 GiB), `work_dirs/k2` (3.5 GiB),
`orientbench_v2` (3.9 GiB), r040/r041 predictions, or the r032 historical
worktree without separate lineage verification.  They may be publication
evidence, checkpoints or current historical provenance rather than disposable
runtime products.
