# B 对 r043 SAUR-OBB Stage A 的执行验收与科学 verdict

- actor: B (`peer-b-primary`)
- dispatch: `orientbench-b-r043-saur-obb-stagea-20260818`
- evidence cutoff: 2026-08-18T18:38:00-07:00

## Verdict

**ACCEPT_EXECUTION / REJECT_SAUR_METHOD / DO_NOT_EXPAND**。

DIOR-R 与 SODA-A 的 BASE identity parity 均通过；CONT 与 SAUR 使用同一宿主、追加预算和四卡训练。修正初始化后，SAUR 在 step zero 保持 PSC identity，但第一轮分别得到：DIOR-R AP50 `0.3340`（BASE `0.5370`，差 `-0.2030`），SODA-A AP50 `0.4320`（BASE `0.5990`，差 `-0.1670`）。二者都远低于冻结 survival floor `-0.0020`，按首轮明显偏低规则停止正确；风险指标不可能挽救独立失败的 AP50 合取门。

用户对 DIOR-R `trainval -> test` 的明确 amendment 已持久化，故该 split 不再构成本轮违规。服务器无 OOM、无未处理异常，SODA-A official test 与 DOTA-v2.0 未触碰。

边界：实现将计划正文的无阈值 `g=(w-h)^2/(w^2+h^2+eps)` 改为带 slope/center 的 sigmoid gate，且缺少计划要求的完整 no-GT-inference 单测；因此本轮只否决已执行的 SAUR 配置，不宣称所有 symmetry-aware distribution head 在理论上均失败。该偏差不构成重跑理由：两数据集的实际退化远超门槛，且继续调 gate/LR/冻结层会成为新的方法与新协议。旧 SAUR 路线停止，不进入 Stage B。

期刊判断：方法贡献未存活，当前科学资产仍只支持 strong-JSTARS/Remote-Sensing 档；这低于项目合法目标。下一合法动作是把已有正向测量、几何诊断、图像级有限样本控制和人工复核重构为 JPRS measurement-diagnostic 完整稿，而不是继续追加 detector head。

