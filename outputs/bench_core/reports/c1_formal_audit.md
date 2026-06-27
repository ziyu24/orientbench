# C1 Formal Audit — D_audit (augmentation-view consistency)

> RHINO frozen sha256 55a90abbace42927…; frozen thresholds applied (NOT mutated); D_audit holdout.
> **scope: augmentation-view only — NOT genuine physical multi-view evidence.**

## VERDICT: **formal_pass** (within augmentation-view scope only; not genuine physical multi-view)

- view-consistency p90 = **3.489°** (threshold <= 5.04; bootstrap CI [3.409,3.577])
- DropRate across views = **0.1364** (threshold <= 0.184)
- OT dustbin mass mean = 0.1162; OT vs GT-identity reldiff = 0.0
- both-views responsible = 9042; near-square masked = 86
- failure taxonomy: {'dropped_both_views': 755, 'high_view_inconsistency': 62, 'dropped_near_square': 1}
- per-class median view-consistency err (deg): {'baseball-diamond': 18.965, 'basketball-court': 1.878, 'ground-track-field': 3.067, 'harbor': 1.669, 'large-vehicle': 0.567, 'plane': 1.908, 'roundabout': 53.19, 'ship': 1.23, 'small-vehicle': 1.375, 'soccer-ball-field': 4.352, 'swimming-pool': 1.637, 'tennis-court': 0.482}

## 边界
- formal_pass 仅在 augmentation-view scope；**不是** genuine physical multi-view 证据；DOTA partial；阈值未调。
