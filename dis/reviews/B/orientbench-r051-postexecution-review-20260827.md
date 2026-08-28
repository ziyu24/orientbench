# B post-execution review — r051 CMR-OBB

## Verdict

- Server receipt: `REJECT_COMPLETION_REPORT`.
- Execution state: `INCOMPLETE / PROTOCOL_DRIFT`.
- Scientific state: `NOT_ADJUDICATED_IMPLEMENTATION`.
- Active dispatch remains open; B does not close it or activate a successor.

The four-GPU smoke, exact proposal/class UID propagation, three serially completed frozen-host arms, raw exports and metric packaging are real engineering progress. The parallel OOM attempts were recovered under the unchanged four-GPU protocol and are not the reason for rejection. The decisive problem is that the executed model and strongest control do not implement the frozen G1 scientific contract.

## Decisive mismatches

### 1. The planned likelihood marginalization is not integrated into the detector

The plan defines CMR as a cyclic proposal likelihood whose posterior is marginalized into refined angle, box and class likelihood. `CMRRoIEvidence.forward_from_features` computes `log_marginal_likelihood`, but no training or inference call consumes it. Training uses only cross-entropy on the angle-bin logits. Inference copies `active_boxes`, changes only column 4 (`theta`), and calls NMS with the untouched host classification scores. Centre, size and class likelihood are not marginalized or refined.

Consequently the executed arm is an angle-only candidate-RoI auxiliary refiner, not the frozen `cyclic likelihood marginalization into the detector` method. Its AP/angle failure cannot adjudicate the planned CMR contribution.

### 2. DIRECT_DIST is not instance-conditioned

The declared strongest control constructs

`logit[n,k] = evidence(encoded[n] + phase[k])`.

Because `evidence` is a single linear scalar head, this equals

`w^T encoded[n] + w^T phase[k] + b`.

The instance-dependent term is identical for every `k` and therefore cancels exactly under the softmax. The resulting K-way posterior is a single global residual distribution shared by every proposal, regardless of image, RoI feature or class. The existing test checks only output shape and finite gradients; it never requires two different proposal features to produce different posteriors.

This is not the plan's equal-budget direct angle distribution conditioned on the same proposal feature, so selecting it as the strongest control does not form the registered comparison.

### 3. The completed metric gate therefore addresses the wrong estimand

The reported CMR values (`AP50=0.6490`, `AP75=0.3820`) are worse than the reported DIRECT_DIST values (`0.6650/0.4010`), and the angle/risk statistics also move in the wrong direction. Those values may be retained as engineering evidence for the executed angle-only head. They do not yield `REJECT_CMR_CHEAP_SIGNAL` for the frozen method because G1 implementation admission was not satisfied.

## Consequence

The completion mapping requires implementation failure to return `未执行完毕`. The two-line server receipt says `执行完毕`, so it is rejected. G2/G3/G4 correctly remain unexecuted, but r051 is not scientifically closed.

Current venue level remains `STRONG_JSTARS_OR_REMOTE_SENSING`, below the legal TGRS/JPRS target. The invalid negative result must not enter the manuscript, supplement, appendix or ablation.
