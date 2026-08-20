# G0 asset and baseline freeze

The required DOTA-v1.0 PSC primary asset is present.  Its train and validation
image counts are 15,749 and 5,297; the paired annotation directories have the
same counts.  The resolved image storage is an existing historical `/dev/shm`
link, so it is treated as an external dataset dependency, not an output
artifact.  No dataset material was written there.

The valid archived PSC checkpoint replayed on four A30 GPUs with the frozen
12-epoch, global-batch-4, SGD-0.005, AMP/BN recipe.  Replay mAP/AP50 was
`0.5562/0.5560`, matching the archived `0.5562` within zero decimal drift.
The only repair was replacing a retired data-root alias in a project-local
adapter; detector, evaluator and checkpoint were unchanged.

DIOR-R has registered converted trainval/test annotations under the project
read set and valid PSC/Oriented-RCNN checkpoints.  SODA-A's registered tiled
train/val asset and both baseline families are available.  The registered
FAIR1M transformed split is absent, so that optional expansion cell is frozen
as `SKIP_EXTENSION`; raw FAIR1M is not substituted.  DOTA-v2.0, SODA official
test and old audit semantics were not accessed.

G0 result: **PASS for the DOTA/PSC primary cell**.  Proceed to G1.
