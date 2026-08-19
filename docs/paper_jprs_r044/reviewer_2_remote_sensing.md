# Independent red-team review 2: remote-sensing significance

**Frozen manuscript SHA-256:** `e23077a080af8c3f3ad70606b83bf8d4491503be60d4e442f8c725e13f445317`

**Recommendation tendency:** Weak reject

## Summary

The manuscript is relevant to remote sensing because oriented boxes are often consumed as measurements rather than only as detection envelopes. The study covers four named aerial-image benchmarks, uses more than one detector family, and treats dense images as the statistical unit. The human disagreement analysis is particularly useful for readers who might otherwise interpret degree thresholds as physical truth.

The paper is nevertheless closer to a rigorous evaluation framework than to a demonstrated remote-sensing advance. The motivating applications (ship alignment, aircraft arrangement, bridge direction) are plausible, but none is quantitatively evaluated. The DOTA evidence uses a local train/validation protocol, and no geographic or sensor-transfer study tests whether a calibrated risk statement remains meaningful outside the evaluation distribution. The absence of a deployable repair is acceptable for a measurement paper, but it increases the burden on application validation.

## Scores

| Criterion | Score (1--5) | Rationale |
|---|---:|---|
| Novelty | 3 | The integration is useful, but the paper needs a remote-sensing decision study to rise above a benchmark-metric critique. |
| Technical soundness | 4 | Strong protocol separation, exact provenance, and explicit limitations. |
| Evidence breadth | 4 | Four datasets and several hosts are substantial; held-out geographic/sensor transfer and operational tasks are absent. |
| Presentation | 4 | Complete manuscript, tables, figures, supplement, and references; final journal formatting remains. |
| JPRS fit | 4 | Directly relevant to trustworthy geometric interpretation of aerial detections. |

## Strongest rejection reasons

1. **Remote-sensing value is asserted rather than measured.** The paper does not quantify how orientation-risk selection affects a mapping, monitoring, alignment, or scene-understanding decision.
2. **No prospective shift validation.** Image-level guarantees are evaluated within frozen dataset splits. Remote-sensing deployment commonly changes geography, season, platform, and ground sampling distance, precisely where reliability claims are most vulnerable.
3. **No surviving deployment mechanism.** The study can diagnose and calibrate with labeled target images, but it cannot provide a target-label-free score or repair. This is not fatal by itself, but it makes the current contribution less actionable.

## Required scientific revision

The smallest convincing addition is one prospectively held-out remote-sensing case study, selected before outcome inspection, that compares AP-based and orientation-risk-based model or threshold choices and measures an external orientation-sensitive endpoint. A sensor/geography transfer split with image-level risk verification would address both significance and robustness. Pure rewriting or an additional in-distribution detector row would not close this gap.

## Positive assessment

The paper avoids public DOTA-test comparisons, does not claim broad state of the art, separates human disagreement from annotation truth, and records failed repair routes as limitations. These choices make the current negative recommendation remediable rather than a rejection for scientific overclaiming.
