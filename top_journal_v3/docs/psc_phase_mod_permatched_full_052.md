# PSC phase_mod per-matched full table 052

Generated: 2026-07-02 21:45:06 CST

The CSV aligns instrumented PSC phase_mod predictions to matched GT OBBs by same-image/same-class greedy rIoU matching. It uses the newly generated DOTA #20 forward dump plus persistent DIOR/FAIR/SODA Track A dumps; no aggregate proxy is used.

- DOTA-v1.0/20: complete_full_real, predictions=69668, matched=17960
- DIOR-R/22: complete_full_real, predictions=212448, matched=29994
- FAIR1M-v1.0/24: complete_full_real, predictions=484332, matched=54768
- SODA-A/23: complete_full_real, predictions=1663631, matched=309218

Output: `top_journal_v3/reports/psc_phase_mod_permatched_full_052.csv`
