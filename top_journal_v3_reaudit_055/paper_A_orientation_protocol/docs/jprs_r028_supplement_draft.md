# Supplement: r028 Corrective Audit and Replay Materials

## S1. Evidence identity

The DOTA result is a **post-outcome audited external replication**. The protocol direction, witness criteria, and frozen external probe predate the first DOTA result; the audit and its final framing do not. r025 is the first-result execution, and r026/r028 are result-after audit rounds. This language replaces “preregistered independent external confirmation” and does not assert that B and C have jointly accepted a final scientific state.

## S2. Fresh revalidation

`revalidate_r026_raw.py` reads only matched DOTA parquets, bootstrap array, frozen tolerance source, and tile-to-mother map during calculation. It recomputes points, epsilons, CIs, DoD, centered p, Holm, tie-aware swaps, witnesses, and a four-state gate. Only then is it compared with r026's frozen table. Result: 96/96 field checks match.

`revalidate_r023_raw.py` independently reads r020/r023 runtime rows and 4.05m persisted hypothesis replicate values. It recomputes 405 hypothesis CIs, p values, Holm values, witnesses, and primary point values. Result: 4,950/4,950 field checks match.

## S3. Mutation evidence

The six mutations are true subprocess calls to the r028 validator. Their `mutation_index.json` records returned exit codes and captured stdout/stderr hashes. Each pristine process exits 0; each mutation exits nonzero. The tested semantic surfaces are GT theta/risk, tile→mother mapping, AR range/domain, bootstrap-cell evidence versus frozen comparison, swap gate, and declared report token versus recomputed state.

## S4. Replay bundle and GT integrity

`audit_bundles/r028/` is a Git-tracked, manifest-hashed replay bundle. It contains full DOTA matched columns, the 16×10,000 bootstrap array, frozen r026 hypothesis/gate copies, r023 hypotheses/witnesses/gate/replicates/multiplicity record, fresh validator code, revalidation records, and DOTA GT conversion. Its manifest has no self entry.

`gt_integrity.json` records `dota_gt_fresh.pkl` bytes/SHA, 5,297 tiles, 458 mothers, 55,804 GT instances, 15 class counts, and matched GT-id subset checks for both detector units. It is a completeness audit of the conversion object, not a claim that original migration-host annfiles are present.

## S5. Corrected r027 descriptive material

The prior r027 `tta_localization` implementation was incorrect. r028 defines it exactly as `-(missing_fraction + iou_loss)`, emits corrected DOTA unit and class tables, and marks the affected r027 descriptive artifacts `SUPERSEDED_BY_R028`. Formal r023/r026 witness tables are unchanged. The rebuilt r027 package manifest is non-self-referential and records only actual hashes/bytes.
