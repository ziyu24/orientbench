# Orientation Reliability Depends on the Aspect-Ratio Eligibility Domain

## Abstract

Oriented detectors can localize an object successfully while their angle is unreliable. We study whether this reliability conclusion is stable under changes to the aspect-ratio (AR) eligibility domain. Our frozen protocol canonicalizes each OBB to its long side, normalizes periodic angle error by a frozen AR-dependent tolerance, and compares score-only with a frozen score--AR--size probe under cluster bootstrap, Holm correction, effect bands, and acceptance-set swaps. In the formal DIOR analysis, the AR-domain signature is present but does not satisfy the cross-dataset gate [L1]. A preregistered DOTA-v1.0 confirmation with two detector families yields dataset witnesses for AUGRC and Risk@70, with RTMDet unit witnesses and AP parity checks passed [L2, L3]. The resulting claim is deliberately bounded: the measurement conclusion depends on the AR eligibility domain and is externally supported on DOTA for the DIOR-source frozen probe; it is not claimed universal across all datasets.

## 1. Introduction

Angle quality is not determined solely by detection confidence. Near-square OBBs are intrinsically ambiguous under long-side orientation conventions, so changing the AR domain can change which reliability conclusion a score ranking appears to support. We frame this as measurement validity, rather than as a new detector or a claim of DOTA SOTA.

Our contributions are:

1. A frozen orientation-reliability protocol based on long-side canonical angle error and AR-dependent geometric normalization.
2. Formal DIOR evidence that the score--AR--size comparison reverses between `AR>=2.1` and the full AR domain [L1].
3. An external DOTA confirmation with independent raw reruns, full witness predicates, and AP parity [L2, L3].
4. An evidence ledger and reproducibility map for every numerical claim [L5].

## 2. Methods

For predicted and GT OBB angles, we canonicalize the angle of the longer side and take the minimum difference modulo 180 degrees. With AR defined from GT width and height, the normalized risk is `clip(e_can/max(delta_0.75(AR),1),0,3)/3`. The principal comparison is `linear_source_frozen - raw_confidence`; the frozen DIOR-source linear probe is documented in the r026 report [L2].

We compare the main domain `AR>=2.1` to `NORMALIZED_ALL_AR`. The endpoints are AUGRC and selective Risk@70. A witness requires reversed directional confidence intervals beyond endpoint-specific epsilons, a Holm-adjusted centered-bootstrap p-value below .05, a nonzero DoD CI, sufficient effect magnitude, and—at Risk@70—whole-tie acceptance-set swaps of at least .05.

## 3. Results

### DIOR formal finding

The r023 formal rerun contains five unit and two dataset witnesses, all within the AR-domain / normalized-all-AR signature. Its global state is `INCONCLUSIVE_MIXED`, because FAIR1M and SODA do not provide the same cross-dataset signature [L1]. This is a boundary, not a negative result to hide.

### DOTA external confirmation

On DOTA-v1.0 val, Oriented R-CNN AP50/AP75 are 0.706069/0.451742 and RTMDet are 0.716127/0.486848, each within the frozen parity tolerance [L3]. The equal-unit DOTA aggregate has an AUGRC DoD of 0.014321 (95% CI [0.008337, 0.021029]) and a Risk@70 DoD of 0.029008 (95% CI [0.016474, 0.043630]); both are witnesses after Holm adjustment [L2]. RTMDet is a unit witness for both endpoints; Oriented R-CNN has the prescribed direction but does not clear its main-domain effect band [L2].

## 4. Discussion and limitations

The evidence supports a conditional measurement statement: selecting the AR domain selects the reliability conclusion. It does not establish a universal property of every dataset or detector. The DOTA probe is explicitly DIOR-source frozen; no DOTA fitting was used. The migrated host retains the DOTA tile-level GT conversion but not the 5297 split annfiles, a limitation documented in the execution record. External confirmation covers one validation split and two detector families.

## Data and reproducibility

The evidence ledger links all claims to immutable artifacts and hashes [L5]. The current draft is not a submission and contains no author identity or submission action.
