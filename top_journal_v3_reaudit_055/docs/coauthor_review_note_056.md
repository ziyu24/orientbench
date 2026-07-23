# 合作者审稿说明（一页）

## 论文现在的身份
**Orientation Reliability Measurement Protocol + Finite-Sample Conformal Risk Control**。
不是 full benchmark；不是 detector SOTA；不是可部署方法胜利；不是顶会 ready。最稳正贡献 = 测量协议（第 3–4 节）+ 有限样本保形朝向风险控制（第 6 节）。

## 相对前稿修正了什么
1. **协议漂移更正（核心）**：前稿把 unmasked NRC>1 解释为“检测置信度反校准”。在冻结 masked 口径（ar≥1.6）+ 同一权威匹配表上重算，检测置信度 4/4 PSC cell 显著校准（0.542/0.885/0.914）；unmasked NRC>1 是近方形 pooling artifact（每个 ar 分层 NRC 都 <1，pooled 却 >1）。该反校准结论 **作废**。
2. **P1 由 partial 升为 precise-pass**：约束扰动（保持 rIoU>0.5）下 mAP@0.5 各 ar-bin Δ=0，朝向误差 +约30°、AP75 塌陷。替换前稿无效的均匀 30° 扰动。
3. **P2 由“空洞保证”升为有效贡献**：在严格风险预算（优于平均可靠性）下给出带弃权、带 Hoeffding 界的尾部保证；打分菜单确立“保形层 + 几何选择器”默认。
4. **机制信号迁移**：反校准从 detection-score（作废）迁到 intrinsic phase_mod（masked 下幸存，机制候选）。
5. **DOTA#20 排除主表**（19 图子集残缺 dump，invalid_pending）。

## 哪些结论可以审（已有真实证据支撑）
- P1 precise-pass 的表述与 ar 门控（表 3 / 3b + 理论曲线）。
- P2 保形的 alpha 扫描、尾部保证、打分菜单、shift 审计（表 4–7）。
- masked 口径 detection 校准 vs phase_mod 反校准的 CI（表 8）。
- 证据 retained/superseded 归类（附录 E）。

## 哪些结论不能再争（已定，请勿回退）
- 不得再用 unmasked NRC>1 作为“检测置信度反校准”headline。
- 不得把 DOTA#20 当有效单元或 validation。
- 不得把 phase_mod 写成机制定论。
- 不得把 P5 写成下游 utility 成功。
- 不得声称 full benchmark / detector SOTA / 顶会 ready。

## 还缺什么
- 更多 cell 在冻结 masked 口径 + provenance-clean 下重算（当前 7 full-val + 2 masked-only）。
- 受控 angle-coder 实验以把 phase_mod 升为机制证据（涉及训练，需另行决定）。
- 角度真正主导的下游任务（如舰船 heading 选择性预测）以支撑 utility。
- 更紧的有限样本/迁移保证；DOTA full-val provenance dump。

## 请重点审的地方
1. **第 6 节 P2 的保证表述**：均值版“近似保证”与尾部版“Hoeffding 界”的措辞是否足够克制、是否会被读者读成严格保证。
2. **第 8 节机制候选的语气**：phase_mod 反校准是否被明确限定为 candidate。
3. **第 5 节 P1 precise-pass 的边界**：是否清楚区分“mAP@0.5 结构性弱敏感”与“mAP 完全看不见角度”。
4. **附录 E supersede 记录**：pooling artifact 的解释是否让审稿人信服。
5. **相关工作**：占位文献需补真实出处（勿编造）。
