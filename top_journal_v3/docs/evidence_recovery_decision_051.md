# Evidence recovery decision 051

Generated: 2026-07-02 21:03:02 CST

- P1 rerun readiness: yes; recovered matched tables are capped at 300 images/cell and need full-cell rerun for final P1.
- P2 conformal readiness: yes for feature-table empirical rerun; final CRC should use full persistent matched rows.
- P3 PSC free mechanism readiness: no; DOTA #20 phase_mod remains missing unless rerun with instrumented forward dump.
- P4 uncertainty readiness: partial; TTA circular variance table exists for available pkls, but MC/dropout/ensemble/native/GWD-KLD are still absent.
- P5 downstream readiness: partial; matched rows are real but capped/offline, suitable for 052 smoke before final full-cell.

Recommendation: do not rewrite science conclusions yet. Start 052 only after either accepting capped real recovery as smoke input or rerunning full-cell DOTA #20 Track A plus full matched 17-field persistence for the seven key cells.
