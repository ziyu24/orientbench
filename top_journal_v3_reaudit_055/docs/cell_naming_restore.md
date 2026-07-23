# 单元命名还原（066）

主稿去匿名化：正文表间不应让读者猜"单元 A–F"对应关系。还原为 dataset + detector：

| 匿名 | 单元 | 数据集 | 检测器 | full-val AP50 |
|---|---|---|---|---|
| 单元 A | DIOR#22 | DIOR-R | 相位编码 RetinaNet (PSC) | 0.5368 |
| 单元 B | DIOR#3 | DIOR-R | Oriented R-CNN | 0.6448 |
| 单元 C | DIOR#61 | DIOR-R | Rotated RTMDet-s | 0.6462 |
| 单元 D | FAIR1M#24 | FAIR1M | 相位编码 RetinaNet (PSC) | 0.3462 |
| 单元 E | SODA#23 | SODA-A | 相位编码 RetinaNet (PSC) | 0.5991 |
| 单元 F | SODA#4 | SODA-A | Oriented R-CNN | 0.7295 |
| (新, K4b) | DOTA(ORCNN) | DOTA-v1.0 | Oriented R-CNN | 见 K4b |
| (新, K4b) | DOTA(RTMDet) | DOTA-v1.0 | Rotated RTMDet-m | 0.7161 |

要求：主稿所有表统一用"数据集 + 检测器"命名（如"DIOR-R / PSC"），去掉 A–F 匿名；表间映射一目了然。
本 doc 为主稿修订依据，本轮不改主稿正文（第二层留待 K1/K3/K4 硬事实同步时统一处理）。
