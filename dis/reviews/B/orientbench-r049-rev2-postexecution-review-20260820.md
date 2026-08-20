# B post-execution review — r049 revision 2

## Verdict

- Server receipt: `REJECT_COMPLETION_REPORT`.
- Execution state: `INCOMPLETE / PROTOCOL_DRIFT`.
- Scientific state: `NOT_ADJUDICATED_IMPLEMENTATION`.
- Active dispatch remains open; B does not close it or activate a successor.

The four reported 12-epoch/four-GPU DOTA arms appear to have run, and their AP50/AP75 values may be retained as engineering evidence. They do not adjudicate the frozen PEF method because G1 was not actually satisfied.

## Decisive implementation mismatches

1. **Not per candidate box or per anchor.** The plan requires a field for every positive/candidate box with fixed `(cx,cy,w,h,class)`. `pef_head.py` instead selects only `base_anchors[level][0]`, builds one `K×H×W` field per FPN location, chooses one supervised anchor through `weight.argmax`, and broadcasts the same refined angle to every anchor with `expand(... self.num_anchors ...)`. Different anchor templates and decoded boxes therefore do not receive their own evidence fields.
2. **No native-risk inference output.** `predict_by_feat` reconstructs angle codes and immediately calls the parent `predict_by_feat`; `pef_energies` and `pef_risks` are discarded. Predictions therefore do not contain the frozen full `q` or native risk. The plan's risk, matched-row, bootstrap and zero-GT gates cannot be executed from this model.
3. **Required mutations were replaced by tautologies.** The claimed circular-shift test never rotates an input or compares shifted energies; it rolls an already-normalized distribution and only checks that its sum remains one. The claimed risk-monotonicity test constructs no narrow/broad pair and only checks finite `[0,1]` bounds. There is no whole-model proof that gradients reach backbone, neck and orientation head, no candidate-collapse rejection, and no non-angle-field byte-invariance test.
4. **Controls are not operative inference baselines.** `DirectDistributionAngleBranchRetinaHead.predict_by_feat` ignores `direct`; `ScalarQualityAngleBranchRetinaHead.predict_by_feat` ignores `scalar`. They are auxiliary training-loss arms, not AQE/O2-like angle-distribution inference or PQA-like quality inference controls as reported.
5. **The reported PEF AP drop is confounded by the implementation.** A 12-bin absolute angle field is shared across all anchors at a location and replaces the host angle code without a per-box residual. The observed `-0.061/-0.041` AP50/AP75 cannot be attributed to the planned per-candidate PEF.

## Consequence

The frozen completion mapping requires an implementation failure to report `未执行完毕`. The server report instead labels this a completed scientific early stop, so it is rejected. G3/G4 remain unauthorized, but r049-rev2 itself is not scientifically closed.

Current venue level remains `STRONG_JSTARS_OR_REMOTE_SENSING`, below the legal TGRS/JPRS target. This invalid result will not enter any manuscript, supplement, appendix or ablation.

