# Top journal evidence decision 049

Generated: 2026-07-02 18:47:16 CST

Decision: broader top-tier claim insufficient in this run.

- P1 constructive decoupling: partial. Raw perturbation and rematching pipeline completed on available proxy/synthetic raw predictions; final claim requires non-synthetic detector predictions and mAP join.
- P2 conformal risk control: partial. Within-cell empirical risk-control thresholds were produced; formal finite-sample theorem text and non-proxy rerun remain required.
- P3 PSC mechanism: fail/blocked for 049 criteria. DOTA #20 phase_mod and per-instance aliasing/confounding artifacts were not available, so fewer than two free tests support mechanism escalation.
- P4 uncertainty baselines: partial. Circular-statistics requirement documented; strong baselines not recomputed.
- P5 downstream task: partial. angle-induced rIoU drop task completed on proxy/synthetic predictions, not final detector evidence.

top_journal_discussion_level = false
remote_sensing_journal_ready = possible only after P1/P2/P4 are rerun on non-synthetic detector assets
broader top-tier claim insufficient
