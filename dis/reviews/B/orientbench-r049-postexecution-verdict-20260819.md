# B post-execution verdict — r049

## Verdict

- Execution: `ACCEPT_COMPLETED_GATED_EARLY_STOP`.
- B scientific verdict: `REJECT_EXECUTED_CORA_V1`.
- Joint scientific state: `PENDING` until a traceable C verdict exists; B does not unilaterally write `KILLED`.

## Evidence accepted

G0 reproduced both registered PSC hosts within the frozen AP tolerance. After a source-preserving invalid-box filter and a common FP32 wrapper, the three DIOR-R seed-0 arms completed the same three-epoch/four-GPU budget and produced full-val AP plus detector-native risk exports. DIOR-R alone validly triggered the frozen early stop:

| arm | AP50 | AP75 | AUGRC | Risk@70 | mean angle error |
|---|---:|---:|---:|---:|---:|
| CONT | 0.496 | 0.275 | 0.009783 | 0.020114 | 2.1050° |
| VM-NLL | 0.485 | 0.265 | 0.008165 | 0.015910 | 2.0260° |
| CORA | 0.491 | 0.248 | 0.007761 | 0.015687 | 1.9475° |

CORA loses 2.7 AP75 points relative to the stronger accuracy control. Its risk gains over VM-NLL are only 0.000404 AUGRC (4.95% relative) and 0.000223 Risk@70 (1.40% relative). These effect sizes are too small to justify more seeds or SODA-A. Stopping before SODA-A, extra seeds, ablations, Stage B, DOTA-v2.0, SODA official test, and old clean endpoints is therefore accepted.

## Scope correction and owner self-audit

The result rejects the executed CORA-v1 parameterization, not every possible detector-native orientation-risk method. Two frozen-design weaknesses matter:

1. The absolute `AUGRC >= 0.01` improvement gate was poorly scaled: the strongest control AUGRC itself is only 0.008165, so that particular inequality was unattainable on this normalized-harm scale. This does not rescue r049 because AP75 fails decisively and both relative risk gains are negligible.
2. `counterfactual_harm_logits = base_logits + slope * delta` is affine in signed angle intervention. It cannot represent the periodic/V-shaped harm landscape expected around a correct orientation, and the tests verify mutation/finite gradients but not recovery of that landscape. The implementation is a real native branch, but it is not a strong realization of the scientific idea.

Accordingly, r049 may not support a deployable-method, TGRS, or JPRS claim. No threshold reinterpretation or CORA-v1 rerun is authorized.

## Venue assessment

After r049, the defensible level remains `STRONG_JSTARS_OR_REMOTE_SENSING`; this is below the project's legal TGRS-or-better target. The existing measurement manuscript remains useful evidence but has no surviving method-level contribution strong enough for JPRS/TGRS.

