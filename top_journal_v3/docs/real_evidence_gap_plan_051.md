# Real evidence gap plan 051

Generated: 2026-07-02 21:02:02 CST

## Concrete gaps

- DOTA #20 Track A phase_mod is absent from both persistent artifacts and /dev/shm Track A dumps. Existing DOTA #20 has real raw/schema and matched features, but no instrumented phase_mod forward dump.
- DIOR #22 / FAIR1M #24 / SODA #23 persistent Track A pkl files contain phase_mod, but older 050 did not persist exact pred_id-to-matched-GT alignment. 051 attempts offline rematching from the pkl predictions to recover that alignment; any missing DOTA row remains unavailable_with_evidence.
- Existing features_v2 matched tables contain score, theta/geometry-derived fields, error and split, but not full 17-field matched rows with pred OBB, GT OBB, match IoU and GT id. 051 writes recovered matched subsets under outputs/persistent_artifacts/orientbench_real_051/.
- DIOR #61, DIOR #10, FAIR1M #5/#12, SODA #4/#11 and HRSC #13 have schema/raw material partly only in outputs/predictions or /dev/shm, not fully in persistent_artifacts. These need persistence or rerun before final evidence.
- TTA pkl files exist for several key cells, but circular variance was not previously persisted as a first-class table. 051 writes tta_circular_variance_051.csv from available TTA pkls.

## Directly reusable

- Persistent raw/schema: DOTA #20, DIOR #22/#3, FAIR1M #24, SODA #23.
- Persistent features_v2: DOTA #20, DIOR #22/#3/#10/#61, FAIR1M #24/#5/#12, SODA #23/#4/#11.
- Persistent Track A pkl: DIOR #22, FAIR1M #24, SODA #23.
- Persistent TTA pkl: DIOR #3/#22/#61, FAIR1M #5/#24, SODA #4/#23.

## Must rerun or rebuild

- DOTA #20 instrumented Track A forward dump with phase_mod, using a shadow farm and no detector training.
- Full persistent raw/schema for scratch-only cells needed in final tables.
- Full-cell matched 17-field tables if 052 decides to run final P1/P2/P4/P5 evidence, because 051 uses capped offline recovery for handoff.

DOTA #20 current status row: `match_iou_missing;phase_mod_missing;tta_missing;circular_variance_missing`.
