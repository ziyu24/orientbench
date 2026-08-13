# Orientation Reliability Depends on the Aspect-Ratio Eligibility Domain

## Abstract

An oriented detector can localize an object successfully while its reported orientation remains unreliable. We study the measurement validity of that statement: whether it is stable when the aspect-ratio (AR) eligibility domain changes. A frozen protocol canonicalizes each oriented box to its long side, normalizes periodic angle error by an AR-dependent tolerance, and evaluates score rankings by AUGRC and selective risks. The formal DIOR analysis identifies an AR-domain signature but is globally mixed: it is supported within DIOR and not reproduced on FAIR1M or SODA-A [L1, L2]. A preregistered external DOTA-v1.0 validation, using a DIOR-source frozen score--AR--size probe, confirms the signature at the equal-detector aggregate for AUGRC and Risk@70 [L3]. Descriptive cluster-bootstrap scans show how the contrast varies across AR cutoffs [L9]. The claim is deliberately conditional: AR eligibility is part of the reliability estimand, not a harmless reporting choice.

## 1. Introduction

Oriented object detection must estimate both location and angle. The latter is convention-sensitive for square-like boxes: a small perturbation in a nearly symmetric shape can change the long-side representation without changing the semantic object. Consequently, a detector-confidence ranking can be adequate for detection while being poorly aligned with normalized orientation risk.

We frame this as measurement validity. Rather than assert a universal calibration defect, we ask whether a frozen comparison between score-only and a score--AR--size probe changes across an explicitly declared AR eligibility domain. This question is related to selective prediction and risk--coverage evaluation, including AURC/AUGRC, but its target is normalized OBB angle risk. It is also related to detector calibration (including detection ECE), distribution-aware OBB losses such as GWD/KLD, square-like OBB ambiguity, periodic angle coders, and uncertainty/conformal approaches. Those literatures motivate reliable ranking; they do not remove the need to define the angle-risk domain.

Our contributions are:

1. A frozen orientation-reliability measurement protocol that makes long-side canonicalization, periodicity, geometric normalization, AR eligibility, cluster bootstrap, multiplicity control, and tie-aware swaps explicit.
2. Formal DIOR evidence for an AR-domain signature, together with the important boundary that it is not a cross-dataset universal result [L1, L2].
3. A preregistered DOTA external confirmation with two detector families, independent hypothesis records, matched-count checks, and AP-parity checks [L3, L4].
4. A descriptive paper package: AR scans with cluster CIs, Risk@90, class decomposition, source-probe sensitivity, full unit tables, uncertainty disclosure, and a hash-linked evidence ledger [L7-L14].

## 2. Frozen measurement protocol

### 2.1 Canonical orientation risk

For a prediction and its matched ground truth, we first represent both OBBs by their longer side. The canonical angle error is the minimum angular difference modulo 180 degrees, denoted \(e_{can}\). Let \(a=\max(w,h)/\min(w,h)\) be the ground-truth AR and let \(\delta_{0.75}(a)\) be the frozen tolerance lookup/interpolation rule. The geometric risk used throughout is

\[
r_{geo}=\operatorname{clip}\{e_{can}/\max(\delta_{0.75}(a),1),0,3\}/3.
\]

This definition makes the square-like degeneracy explicit: AR is not merely a covariate, but affects the scale used to interpret periodic angle error. The principal domains are `MAIN_AR_GE_2.1` and `NORMALIZED_ALL_AR`.

### 2.2 Probes, endpoints, and formal decision rule

The primary formal contrast is `linear_source_frozen - raw_confidence`. The linear probe was fit on its declared source only and held frozen for external DOTA use; it combines detection score, log predicted AR, and log predicted area. The descriptive total table additionally reports two frozen proxy probes (`tta_angle`, `tta_localization`) [L13].

We report AUGRC, Risk@70, and, descriptively, Risk@90. Formal witnesses require directional main and ablation confidence intervals beyond frozen endpoint-specific \(\epsilon\), a nonzero difference-of-differences CI, centered-bootstrap Holm-adjusted significance, effect-band conditions, and whole-tie acceptance-set swaps for Risk@70. Images/mothers are the resampling clusters. The protocol, source inputs, and formal results remain frozen in r023/r026 [L1, L3]. The two implementation/audit route is a reproducibility safeguard, not a claim of a new detector method.

## 3. Results

### 3.1 DIOR formal finding and boundary

The r023 formal rerun contains five unit witnesses and two dataset witnesses in the `NORMALIZED_ALL_AR` signature [L1]. Its global state is `INCONCLUSIVE_MIXED`: FAIR1M and SODA-A do not satisfy the same cross-dataset signature [L2]. This boundary is substantive. It prevents interpreting the DIOR result as a universal detector property.

### 3.2 Preregistered DOTA external confirmation

On DOTA-v1.0 validation, the equal-detector formal aggregate has AUGRC DoD 0.014321 (95% CI [0.008337, 0.021029]) and Risk@70 DoD 0.029008 (95% CI [0.016474, 0.043630]); both are formal witnesses after Holm adjustment [L3]. RTMDet is a unit witness for both endpoints. Oriented R-CNN has the prescribed direction but does not meet the main-domain effect band, and is reported as such rather than discarded [L3].

The matched all-AR counts are 48,889 for Oriented R-CNN and 51,736 for RTMDet [L3]. Their AP50/AP75 parity values are 0.706069/0.451742 and 0.716127/0.486848, respectively [L4]. A field-level independent recomputation verifies all seven r023 witness rows and all r026 hypothesis, swap, count, and parity values in this draft [L8].

### 3.3 Descriptive AR-domain map

Figure-ready data comprise cutoff scans from AR 1.0 to 3.0 for DIOR A/B/C, DOTA Oriented R-CNN and RTMDet, and two DOTA aggregates. Each point has a 200-draw cluster-bootstrap CI, and all rows are marked `DESCRIPTIVE` [L9]. The scan is an interpretive map, not a replacement formal gate. DOTA Risk@90 is likewise shown for main and all-AR domains at unit and aggregate levels [L10].

The remaining reviewer-facing detail is available without elevating new claims: DOTA 15-class decomposition flags classes with fewer than 500 rows [L11]; FAIR1M-source and SODA-A-source frozen-probe variants retain their own cluster CIs [L12]; and the complete eight-unit, four-probe, three-endpoint, two-domain table records the row count for every estimate [L13]. Dataset-level cluster counts, eligible clusters, bootstrap SEs, and descriptive MDE80 values disclose precision [L14].

## 4. Discussion

The central conclusion is conditional and operational: choosing an AR eligibility domain changes the orientation-reliability conclusion. A deployment should therefore declare its reliability domain rather than infer that a full-AR score ranking answers a well-defined angle question. The DOTA result shows external support for one frozen DIOR-source probe, not that a DOTA-trained selector is deployable or that every detector has a miscalibrated intrinsic angle head.

The per-source probe analyses explain why transfer must be named: source coefficients and their DOTA consequences are sensitivity evidence, not refitted DOTA performance [L12]. Historical learned-EQS work is retained as an appendix/negative route; it is not used to promote a method claim [L5, L6].

## 5. Limitations

The migrated host retains DOTA tile-level ground-truth conversion but not the 5,297 split annfiles. External confirmation covers one validation split and two detector families. The DIOR formal gate does not satisfy the stipulated SODA cross-dataset condition. DOTA Risk@90 and the AR scans are descriptive, and their CIs do not create new formal witnesses. We do not claim DOTA SOTA, universal calibration failure, or a deployable selector.

## Data availability and reproducibility

Every substantive statement is linked to the evidence ledger [L1-L14]. The package contains the generator and independent claim-recomputation scripts, frozen-input paths, and SHA-256 values. This is a masked draft only: author identities, acknowledgements, final venue formatting, and submission action remain for user and B/C review.
