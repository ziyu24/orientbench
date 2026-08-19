# Independent red-team review 1: measurement and statistics

**Frozen manuscript SHA-256:** `e23077a080af8c3f3ad70606b83bf8d4491503be60d4e442f8c725e13f445317`

**Recommendation tendency:** Weak reject

## Summary

The manuscript argues that detection AP and orientation reliability are distinct estimands, introduces an aspect-ratio-dependent severe event, reports risk--coverage diagnostics, and uses complete images in a finite-sample risk-control procedure. The controlled perturbation is cleanly stated, and the explicit separation of matching, eligibility, risk, and statistical unit is a strength. The human annotation component materially improves threshold interpretation.

The main concern is not numerical provenance; the exact checker closes the reported values. The concern is whether the scientific novelty and validation of the combined estimand are sufficient for a top remote-sensing journal. The perturbation is constructed to preserve IoU 0.5, the severe event is itself derived from rectangle IoU geometry, and the LTT result selects full coverage because the event is rare. These components are coherent, but the manuscript does not yet show that the proposed evaluation changes a consequential real-world model-selection or risk-management decision prospectively.

## Scores

| Criterion | Score (1--5) | Rationale |
|---|---:|---|
| Novelty | 3 | Careful synthesis and protocol design, but the core AP50 counterexample and rectangle geometry are conceptually expected; the operational novelty needs stronger prospective demonstration. |
| Technical soundness | 4 | Definitions, matching, image-level unit, and source closure are strong; construct circularity and the rare-event/full-coverage outcome remain interpretive weaknesses rather than implementation failures. |
| Evidence breadth | 4 | Multiple datasets and detector families plus human labels; not a full matrix, and some claims remain detector/dataset-level. |
| Presentation | 4 | Complete and unusually explicit, though dense and longer than necessary. |
| JPRS fit | 4 | Relevant to reliable aerial-image interpretation and evaluation methodology. |

## Strongest rejection reasons

1. **Estimand circularity and AR-only definition.** The severe event is defined through the same rectangle-overlap geometry used to motivate the AP limitation. The paper needs a stronger demonstration that this event predicts an application-relevant orientation failure beyond restating aspect-ratio-dependent IoU sensitivity.
2. **Finite-sample result is statistically valid but empirically weak.** At alpha 0.03 every unit selects full coverage. This verifies low mean severe risk under the chosen event but does not demonstrate a nontrivial abstention decision or superior risk management.
3. **Multiplicity and generalization remain partly descriptive.** The six perturbation directions are consistent, but the ranking results are heterogeneous and some evidence identities are post-outcome or descriptive. A prospective held-out validation would materially strengthen the central protocol claim.

## Required scientific revision

The minimum nonlinguistic addition is a prospective, preregistered external evaluation in which the protocol changes a model or threshold choice under held-out geography, sensor, or acquisition conditions, followed by image-level verification of the declared risk. The external test should include an application-facing orientation consequence not algebraically defined by the same rectangle-IoU curve. No new detector is required, but a real decision must become testable.

## Claims that are appropriately bounded

- NRC is not called independent of AP.
- The phase result is not generalized to every PSC angle head.
- Human disagreement is not called ground-truth error.
- Target-ground-truth-fitted geometry scores are not presented as deployable.
- Failed correction attempts are not positive contributions.
