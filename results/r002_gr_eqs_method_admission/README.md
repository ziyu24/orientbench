# r002 GR-EQS method admission — G1 result

Decision: `KILL_GR_EQS_METHOD`.

G1 completed normally over the three leave-one-dataset-out held-outs, six
evaluation units, and three fixed training seeds.  The independent verifier
recomputed all 18 unit/seed NRC deltas and checked 180,000 synchronized
cluster-bootstrap replicates.  The conjunctive gate failed, so G2 was not
started, as required by the active plan.

The compact result reference contains the decision, per-unit gate metrics,
independent-verification result, AP outcomes, frozen nested-LODO choices,
AP-parity summaries, path-free forward/checkpoint registries, data-split
digests, and a SHA-256 manifest for the complete internal evidence store.
The manifest's logical paths identify raw prediction tables, feature and label
tables, sealed scores, bootstrap replicates, generated configs, checkpoints,
run specifications, and the producing/independent-recomputation code without
placing local machine paths or bulky regenerable artifacts in Git.
