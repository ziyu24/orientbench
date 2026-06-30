# D_cal-only Predictor Sanity (047, low-priority, time-boxed)

> 2026-06-30 17:40:18 CST。低优先、半天上限。**不得用 oracle_gain/retained 代数耦合指标制造伪相关**（046 已证循环）。

## 状态：**partial / inconclusive（time-boxed，未深入）**
- 046 已证明 oracle_gain↔retained 循环、非循环检验无预测力。本轮主线为 non-PSC deployable leave-*（已完成），D_cal-only predictor 为低优先。
- 设计（未跑全）：以 **D_cal 内 score-NRC / 退化比例**（source-side，非 D_audit）预测 **unseen-target 绝对 gain**，leave-one-cell-out + permutation。
- **结论**：本轮**未得清晰结果即停止**（按指令 "若无清晰结果立即停止写 partial"），**不消耗主线**。predictive boundary 仍按 046 判定 = 未成立，measure→diagnose→fix 写并列结构，DOTA #20 = limitation。
- next-step：单独低成本实验构造干净 D_cal-only predictor。
