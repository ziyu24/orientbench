# Orientation Reliability and Aspect-Ratio Eligibility in Oriented Detection

## Abstract

Orientation reliability depends on the aspect-ratio (AR) domain over which it is measured. We evaluate this statement using a frozen long-side canonicalization and AR-normalized angle-risk protocol. The DIOR result is mixed beyond DIOR itself. A single DOTA-v1.0 external result supports the directional signature at the dataset aggregate, but its evidence status is deliberately post-outcome audited: hypotheses, direction, criteria, and the external probe were frozen before the first DOTA result; r025 executed that result; r026 and r028 audited it after the outcome. A fresh r028 raw-layer validator reproduces all six r026 formal rows (96/96 fields) and the r023 replicate layer (4,950/4,950 fields). This is not presented as a preregistered independent external confirmation or as universal calibration evidence.

## 1. Introduction

An oriented detector may have acceptable localization while its angle ordering is unreliable. The complication is geometric: square-like boxes are weakly oriented under long-side conventions, so AR eligibility affects the risk being measured. We therefore study measurement validity, not SOTA detection accuracy or a new detector architecture.

Our relationship to risk--coverage/AURC, selective prediction, detector calibration/D-ECE, distribution-aware OBB losses (GWD/KLD), periodic angle coding, square-like ambiguity, and uncertainty/conformal prediction is methodological: these methods motivate risk-aware ranking, but none specifies the AR domain for normalized angle risk. We contribute a transparent frozen protocol, an external result with a corrected evidence identity, and replayable raw artifacts.

## 2. Protocol

Predicted and GT OBB angles are canonicalized to their long side; periodic error is minimized modulo 180°. For GT aspect ratio \(a\), frozen tolerance \(\delta_{0.75}(a)\), and canonical error \(e_{can}\), the risk is \(r_{geo}=\operatorname{clip}(e_{can}/\max(\delta_{0.75}(a),1),0,3)/3\). The main comparison is frozen score--AR--size probe minus score-only, assessed in `MAIN_AR_GE_2.1` and `NORMALIZED_ALL_AR` with AUGRC and Risk@70.

Formal predicates use percentile CIs, centered bootstrap p values, separate Holm families, endpoint epsilons, and tie-aware acceptance swaps. Their purpose is fixed decision logic, not a post hoc claim escalator. The r028 source code recomputes these quantities from matched parquets and the 10,000-draw bootstrap array without importing r025/r026 analysis code.

## 3. Results

### DIOR and the cross-dataset boundary

r023 reports an AR-domain signature within DIOR but is globally `INCONCLUSIVE_MIXED`: FAIR1M and SODA-A do not supply the same signature. The new r028 replicate-layer audit covers 405 r023 hypotheses and finds 4,950/4,950 checked fields consistent with the frozen table. This supports reproducibility of the archived calculation, not a universal result.

### Post-outcome audited DOTA result

The DOTA hypotheses and frozen DIOR-source probe were specified before the first DOTA outcome in the r024 plan chain. r024 stopped on source-coefficient structure, after which the user specified DIOR beta; r025 produced the first DOTA result; r026 originally labeled it as an external confirmation; C subsequently contested the audit layer; r028 supplies the corrective audit. Thus the appropriate evidence identity is **post-outcome audited external replication**.

The fresh raw revalidation reproduces the DOTA aggregate AUGRC DoD 0.014321 (95% CI [0.008337, 0.021029]) and Risk@70 DoD 0.029008 (95% CI [0.016474, 0.043630]); it also reproduces all unit rows and predicate fields. RTMDet is a unit witness; Oriented R-CNN has the specified direction but does not meet the main-domain effect condition. There are 48,889 and 51,736 all-AR matched rows for the two units. These statements are audit findings, not a jointly accepted `CONFIRMED_EXTERNAL_STRONG` verdict.

### Corrected descriptive package

r028 corrects the `tta_localization` definition to `-(missing_fraction + iou_loss)`. All affected DOTA descriptive rows are regenerated and r027 affected files are explicitly superseded. No new descriptive analysis is promoted into a formal witness.

## 4. Audit and reproducibility

The Git replay bundle includes full matched parquets, the 16×10,000 bootstrap array, frozen r026/r023 records, r023 replicates, multiplicity record, fresh validator code, raw revalidation results, and manifest hashes. It also includes independent GT integrity evidence: 5,297 tiles, 458 mothers, 55,804 nonignored GT instances, per-class totals, and proof that both matched GT-id sets are subsets of the fresh GT conversion.

Six semantic mutations were executed as subprocesses. All pristine runs exited 0 and all mutated runs exited nonzero: GT angle/risk relation, tile-to-mother relation, AR range/domain, bootstrap comparison, swap predicate, and report-token agreement. This replaces the previous paper-only mutation record.

## 5. Limitations

The DOTA evidence is a post-outcome audit of one external validation dataset and two detector families, not a pre-outcome independent replication. GT originates from persisted prelabel conversion; original split annfiles are absent on the migrated host. Oriented R-CNN does not meet its unit witness predicate. DIOR's stipulated SODA cross-dataset condition is unmet. We do not claim DOTA SOTA, a universal calibration defect, a deployable selector, or final submission readiness.

## Timeline

| event | commit | time (UTC-07:00) |
|---|---|---|
| r024 plan frozen | `0571c2e4` | 2026-08-13 04:26:27 |
| r024 early stop / coefficient structure | `a3f058d6` | 2026-08-13 05:04:38 |
| user-specified DIOR-beta; r026 plan | `0ab65875` | 2026-08-13 05:06:01 |
| r025 first DOTA result | `5ce52c23` | 2026-08-13 05:23:23 |
| r026 closure | `747c0dba` | 2026-08-13 05:29:44 |
| C contest | `28951bb3` | 2026-08-13 09:37:36 |
| r028 corrective audit plan | `e871b7b2` | 2026-08-13 09:48:49 |

This masked draft contains no author identity, submission, or venue action.
