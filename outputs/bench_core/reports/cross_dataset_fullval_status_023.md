# Cross-Dataset Full-Val Status 023

> 2026-06-28 00:12:08 CST

- DIOR-R/FAIR1M/SODA-A 当前用受控 subset（DIOR 600 / FAIR1M 521 / SODA 408 img），**非静默截断**（明确记录）。
- 原因: exploratory 吞吐 + 多 detector 扩展优先；full val 留待（4-GPU 不变 batch）。
- HRSC2016 用 test split（mmrotate HRSCDataset）。
- 下一步: 如需 full val，同 4-GPU 配置去 SUBSET cap 重跑。
