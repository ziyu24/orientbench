# DOTA #20 Negative-Control 收口 (041)

> 2026-06-29 21:42:47 CST

- **DOTA #20 PSC masked NRC = 0.84（CI[0.79,0.90]，未显著反校准）**；是唯一未显著反校准的 PSC cell。
- **within-target oracle_gain = 0.155（四 PSC cell 最低**；DIOR 0.207/FAIR1M 0.378/SODA 0.593）→ 本身可学习 orientation-reliability 结构最弱。
- **method 在 DOTA #20 无大幅提升 ≠ P3 fail**：DOTA #20 = low-gain / weak-structure **negative control**。一个可靠性方法在"几乎没有可靠性结构可学"的 cell 上提升有限，是预期且正确的行为（否则反而说明过拟合/泄漏）。
- 041 观察：加入 GT-free consistency feature 后，DOTA #20 **leave-dataset 由 fail 转 pass（routeC 0.59 beats sizelin）**，leave-detector 仍弱 → 与"弱结构"一致。
- **不为 DOTA #20 调参**（监督员明令）。DOTA #20 标为 **documented negative control / weak-structure limitation**，非主失败。
