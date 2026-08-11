# r020 measurement-validity pragmatic recovery report

## Status

- user authorization: proceed pragmatically after formal preflight stop
- candidate scientific state: `INCONCLUSIVE_MIXED`
- formal cross-machine state: `NOT_ADJUDICATED_PENDING_SUPERVISOR`
- recovery completion: `FULL_RECOVERY_ANALYSIS`
- formal r020 receipt: remains consumed and non-reusable
- GPU/training/forward/inference: none

This recovery preserves the published preflight failure instead of rewriting it. It is decision-grade recovery evidence, not a retroactive claim that the original r020 audit contract closed.

## Execution

- environment: existing `/home/rspip/cqc/data/install/yes/envs/pcp-obb`
- job affinity: logical CPUs `0-47`
- bootstrap workers: 39
- bootstrap seed: 20260809
- bootstrap replicates: 10,000
- elapsed time: 581.30 seconds
- persistent runtime: `outputs/persistent_artifacts/orientbench_measurement_validity_r020_20260811/recovery_full_r10000`
- smoke runtime: `outputs/persistent_artifacts/orientbench_measurement_validity_r020_20260811/recovery_smoke_r20` (engineering validation only)

The job used a 48-CPU task affinity on the migrated 112-logical-CPU host, so 39 workers consumed approximately 81.25% of the authorized job CPU set without changing scientific thresholds, splits, eligibility definitions or bootstrap identities.

## Input and cohort closure

All 26 frozen input byte counts and SHA-256 identities matched the dispatch table. Learned EQS values were never requested from Parquet. All six matched D_audit base cohorts joined features and scores one-to-one with missing=0 and drop=0. Legal right-hand-side extras were counted and excluded.

Base D_audit row counts were A=43,848, B=47,887, C=47,881, D=26,108, E=157,586 and F=192,249. Main AR>=2.1 row counts were A=25,080, B=27,682, C=27,410, D=15,132, E=101,160 and F=120,947. DIOR A/B/C shared the same D_audit image universe; SODA E/F shared the same mother-scene universe.

## Fixed families and validation

- unit hypotheses: 270
- dataset hypotheses: 135
- endpoints: continuous-loss AUGRC, Risk@70, Risk@90
- contrasts: linear source-frozen, TTA angle and TTA localization versus raw confidence
- ablations: the five frozen geometry/AR ablations
- multiplicity: separate Holm correction for the complete 270 and 135 families
- independent validator: `PASS`

The independent validator recomputed all unit and equal-unit dataset point endpoints from `rows.parquet`, reconstructed centered-bootstrap p values from all 4,050,000 hypothesis replicates, independently recalculated both Holm families and every witness predicate, and rehashed the runtime manifest.

## Decision evidence

Seven formal-shape recovery witnesses survived the frozen CI, effect-size, swap and Holm predicates:

- five unit witnesses: A AUGRC, A Risk@70, B AUGRC, C AUGRC and C Risk@70;
- two dataset witnesses: DIOR-R AUGRC and DIOR-R Risk@70.

All seven use the same structure: `AR_DOMAIN / NORMALIZED_ALL_AR / linear_source_frozen / RAW_BETTER_MAIN__PROBE_BETTER_ABLATION`. In plain language, raw confidence is better on the preregistered AR>=2.1 main domain, but the frozen score+AR+size linear probe becomes better when all aspect ratios are admitted.

No FAIR1M or SODA-A dataset witness survived. The AUGRC signature covers only three units (A/B/C) and one dataset; the Risk@70 signature covers only two units (A/C) and one dataset. Neither signature reaches the required >=2 datasets, >=4/6 units and SODA dataset+unit support. `passing_signatures` is therefore empty.

The candidate state is consequently `INCONCLUSIVE_MIXED`, not `PASS_TO_EXTERNAL_CONFIRMATION` and not `FAIL_GENERIC_OR_NULL`. The evidence identifies a DIOR-specific AR-domain sensitivity but does not establish a reproducible cross-dataset OBB measurement-validity witness.

## Scientific implication

The result does not justify reopening the top-journal experimental loop or claiming a cross-dataset measurement contribution. It also prevents a clean null claim because DIOR contains multiplicity-corrected witnesses. The defensible interpretation is: orientation-reliability conclusions can be AR-domain-sensitive in DIOR, but the effect did not replicate on FAIR1M or SODA-A under the frozen family.

This recovery should be submitted to C/supervisor for independent post-pull review. Until that review, the repository's formal state remains `NOT_ADJUDICATED_PENDING_SUPERVISOR`.

## Follow-up independent closure

After the initial recovery result, a second implementation B independently reopened the 26 raw inputs, rebuilt membership, long-side angles, risks, strict joins, all five ablations, point metrics and the complete 10,000-replicate bootstrap. B did not import implementation A or read A rows/runtime before sealing its own output.

Comparator C then compared both sealed bundles. All 4,320,000 unit metric cells and 2,160,000 dataset metric cells were exactly equal; maximum absolute difference was 0. The 405 point hypotheses, CI, centered p, Holm, swap, witness identities and gate were also exactly equal. B independently returned the same 5 unit witnesses, 2 dataset witnesses, empty passing-signature set and `INCONCLUSIVE_MIXED` candidate state.

The pinned fd-shifts reference was fetched once from the exact official HTTPS repository at commit `c4467aec134e99691359da209f811d91283fc1e3`. Both required Git blob and raw SHA identities matched. Full import failed only because the existing environment lacks `loguru`; a traceable AST exact-function-span adapter dynamically read `AUC_DISPLAY_SCALE=1000` and matched tie, binary, continuous and boundary generalized-risk/AUGRC vectors at `atol=1e-12, rtol=0`.

Six isolated recovery mutations passed pristine and were rejected after mutation: D_audit raw theta, SODA tile-to-mother identity, AUGRC origin, two-dataset gate count, 26-input inventory and report candidate-state token. Every pristine validator exited 0 and every mutated validator exited 2.

These follow-up checks materially strengthen the scientific recovery. They cannot retroactively recreate a pre-data code seal, the original live application hash-chain, the original strace bidirectional closure or the original single-commit/postseal receipt. Those historical formal blockers remain explicit and are the only reason this report does not upgrade the old r020 receipt.

## Evidence identities

- `gate.json`: SHA-256 `bdc4bdaefb912d82ed08cfb78499eaf50d14e08c2a963455bec0f8cf44808abd`
- `hypotheses.csv`: SHA-256 `1d1104cae6ed8927d404705956d25b2aba8efc246595700166594a3adb00f3a3`
- `witnesses.csv`: SHA-256 `3e9a0a4129a7b046b83eb3e2a6c944a94df46e98dc1f596ec2669a8c83e29223`
- `hypothesis_replicates.parquet`: SHA-256 `525c3dcaba7f661445963a2cfc107b394a55a41beccdd973e43b4a3f90f004de`
- `manifest.csv`: SHA-256 `6b2022041f0c05200adeebfb8598b6eac995ad57618316268ceb343edb982e93`
- implementation B `manifest.csv`: SHA-256 `cf36d96d25429f268290392ffb089debd52cf1e114ae7ba5380f32a955b73b6a`
- Comparator C `comparator.json`: SHA-256 `6d76827a8970f0f4a1e542789565a29dcad0805d3a1901a1c78655119bb03113`
- pinned reference `recovery_reference_probe.json`: SHA-256 `d989c16ddc9b5dc1638e528c4efc22ed6092f253c082266925e9f63aef6d7865`
- mutation index `mutation_index.json`: SHA-256 `1622f62128e03322bb96f0f890f9f86a268a568626f26c0ea8e8e434218f40ae`
