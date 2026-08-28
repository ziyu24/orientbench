# 给服务器的业务 052 续执行指令

请完整执行以下指令，不要只回复解释：

## 1. 身份与精确任务

1. 在 `/home/rspip/cqc/pro/study/orientbench` 执行 `git pull --ff-only origin main`，确认 `git config --local paper.worker-id` 为 `server-primary`。
2. 继续**同一业务 052**，不得新建业务编号，不得启动其它科学路线。
3. 精确绑定保持为：
   - dispatch id：`orientbench-b-r052-cmr-functional-admission-20260828`
   - plan path：`dis/plans/B/b-r052-cmr-functional-admission-20260828/sug.md`
   - dispatch commit：`85d076b853b394db60d57571bcaffc693af33adf`
   - plan SHA-256：`6c7e122e5d9ff3d4993e7e4e92f4ef2708259be45e6b7a17e8bbead2177fae2d`
4. 必读 B 终验：`dis/reviews/B/orientbench-r052-postexecution-review-20260828.md`。此前 `KILL_CMR_IMPLEMENTATION_PRINCIPLE` token 已被 B 判为无效，因为它绑定错 dispatch commit，且只证明核心路径尚未实现，不是方法原理失败。
5. 不覆盖或删除旧 `STARTED.json`、旧 token、旧报告和旧产物。新增 `audit_bundles/r052/STARTED_CORRECTION.json`，如实记录原 STARTED 误写 plan commit、现在按上述精确三元组续执行，以及用户已明确要求继续业务 052。

## 2. 已完成内容与必须重做内容

可直接复用，不要浪费时间重跑：

- G0 baseline asset identity；
- DOTA-v1.0 identity parity `mAP/AP50=0.7061/0.7060`；
- G0 delta-collision audit；
- 已验证可运行的四卡环境与基础 20-iteration smoke 框架。

必须重做：

- 旧 1,024 manifest 来自最终 `pred_instances`，不是 pre-NMS decoded proposals，因此不得作为正式 G1 universe；
- 旧 formal runner 只是源码/字段静态检查，不是正式 G1；
- 旧 G1 token 与 `执行完毕` 回执均不得复用。

## 3. 先完成真实 detector-native 实现

### 3.1 pre-NMS proposal 与 UID

1. 在 Oriented RPN 产生 decoded proposal 后、ROI class expansion 与最终 NMS 前立即分配 immutable `proposal_uid`，建议格式为 `image_id:rpn_proposal_index`，并保存原 decoded box、proposal score 与 batch/image identity。
2. ROI class expansion 后生成 `class_uid=proposal_uid:class_id`；K=12 候选生成 `candidate_uid=class_uid:k`。
3. 三类 UID 必须随 loss、joint output、box decode、class marginalization、NMS keep index 与 raw export 传递；禁止在 NMS 后按 box 几何反猜来源。
4. 用该真实 pre-NMS universe 重新按冻结规则选择恰好 1,024 个 train-only positives：class match、rotated IoU `>=0.5`、每图最多四个、SHA256(image_id) 顺序。保存新 manifest 和 SHA-256，旧 manifest 标记 superseded 但不得删除。

### 3.2 修正 joint likelihood 与 no-GT inference

1. 保留训练 joint NLL：
   `-logsumexp_k(log q_k + log p_class,k(y) + log p_box,k(t) + log p_angle,k(theta))`。
2. box target 使用相对 decoded proposal 的标准归一化 residual，四个 arms 完全一致；推断时解码回 `cx,cy,w,h`。
3. 训练责任可以使用 GT likelihood，但**推断和 native risk 禁止使用任何 GT target**。推断冻结为：
   - `log P(c)=logsumexp_k(log q_k + log P_k(c))`；
   - 对最终候选类 `c*`，`w_k=softmax(log q_k + log P_k(c*))`；
   - `cx,cy,logw,logh` 用 `w_k` 加权并解码；
   - theta 用 `w_k` 的 axial circular mean；
   - native risk 用同一 `w_k` 的冻结 axial tail expectation。
4. 修复现有错误公式 `logsumexp(resp + class_ll)`；不得把 probability 直接加到 log-probability，必须使用 `log q/log w + log probability`。
5. `JointOutput` 明确区分 train-only target-conditioned quantities 与 inference quantities，并携带 proposal/class/candidate UID。

### 3.3 接入实际推断路径

1. 在 r052 新目录内实现 `R052JointRoIHead.predict_bbox` 或等价真实 override；不得修改 third_party。
2. CMR 的 K=12 个候选必须各自执行真实 7x7 Rotated RoIAlign；DIRECT_DIST_V2 与 SINGLE_ROI_JOINT 使用冻结的单观察定义。
3. marginal class score、完整 box、theta 与 native risk 必须进入真实 decode/NMS/final `pred_instances` 和 raw export，不能只在 `bbox_loss` 中存在。
4. CONT、DIRECT_DIST_V2、SINGLE_ROI_JOINT、CMR_FULL 共用同一 integration、decode、NMS、risk 与 UID 路径；新增参数量差 `<=5%`。
5. 先做四卡 smoke。路径、AMP、batch、gradient accumulation、worker 和兼容性问题可在 r052 新目录内自主修复；四卡 OOM 时串行 arms 或降低 per-GPU batch并保持 global batch，不得降为少于四卡。

## 4. 真正执行完整 G1

正式 G1 必须在新的 1,024 个 pre-NMS proposal universe 上动态运行 detector，不得用 grep、`inspect.getsource`、类方法身份或 dataclass 字段检查代替。必须逐项保存数值与逐 proposal pass mask：

1. DIRECT_DIST_V2：至少 95% proposal 的相对 log-q feature gradient `>1e-6`，feature permutation median posterior L1 `>0.05`。
2. CMR candidate-feature across-k variance：至少 95% `>1e-6`。
3. candidate 顺序 cyclic roll 一格后 q 对应 roll，median aligned L1 `<=0.05`。
4. 图像与 proposal 同步旋转一格：proposal-relative q 保持索引，median aligned L1 `<=0.05`；global theta 同步旋转一格。
5. 至少 95% proposal 的 final class likelihood、至少一个非 theta box 分量与 theta 对 candidate evidence 的 autograd norm 各 `>1e-6`。
6. detach(q)：前向 loss 数值不变；正常 evidence gradient `>1e-6`，detach 后 `<=1e-12`。
7. 跨 proposal shuffle q：至少 95% proposal 的 total loss、class likelihood、至少一个非 theta box posterior 绝对变化各 `>1e-6`。
8. 删除/交换/重复 proposal/class/candidate UID、篡改 NMS keep mapping 的真实 mutations 全部非零拒绝。
9. 全部关键 loss/posterior/risk/gradient finite；候选 scorer 与四个非角度分量收到非零梯度；参数差 `<=5%`。

在上述实现与动态测试全部完成前，**禁止提交新的 formal token**。工程缺失只能报告未完成，不能再包装为 `KILL_CMR_IMPLEMENTATION_PRINCIPLE`。

全部通过后，保存新的唯一有效 G1 token、独立 validator、mutation outputs、manifest 与 SHA-256，再进入 G2。若完整实现后的真实动态 G1 数值合取失败，才允许按冻结计划正常 `KILL_CMR_IMPLEMENTATION_PRINCIPLE`。

## 5. G2 与回执

1. 仅新的有效 G1 全过后，才运行冻结四卡三 epoch的 CONT、DIRECT_DIST_V2、SINGLE_ROI_JOINT、CMR_FULL。
2. 每 epoch full DOTA val，最终 epoch 一次裁决；CMR 必须分别打赢两个 joint controls 的全部冻结条件。
3. 禁止打开 DOTA-v2.0、SODA official test、HRSC 或新数据，禁止改 K/loss/threshold/risk/control，禁止把失败结果写入稿件。
4. 若工程仍未完成，回执首行必须是 `未执行完毕`；只有完整 G1 后的正常科学 kill，或 G1 通过并完成 G2 后，才可写 `执行完毕`。
5. 最终仍严格两行：第一行 `执行完毕` 或 `未执行完毕`；第二行唯一报告路径 `dis/server_reports/orientbench-b-r052-cmr-functional-admission-20260828/SERVER_EXECUTION_REPORT.md`。
