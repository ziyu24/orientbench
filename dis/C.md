# OrientBench C：r017 服务器终判与 r018 终结型静态裁决

- review date: `2026-08-08`
- r017 server head: `b349dcbd44685eae66bdabbdf7a795493ccdc08e`
- execution base: `942a5a2cb7e78e8b8ef9d447a6bcd449c590c017`
- r017 report: [`orientbench-c-r017-20260808.md`](server_reports/orientbench-c-r017-20260808.md)
- archived r017 instruction: [`orientbench-c-r017-20260808-server-returned.md`](sug/orientbench-c-r017-20260808-server-returned.md)
- current instruction: [`sug.md`](sug.md)
- next report: `dis/server_reports/orientbench-c-r018-20260808.md`
- overall r017 acceptance: **`PROTOCOL_DRIFT_R017 / FAIL_AUDIT_IMPLEMENTATION_R017`；数值与合格稿件索引部分继续采纳**
- current venue ceiling: **strong-JSTARS potential、尚未 ready；TGRS/ISPRS JPRS 仍需完成 r018 终结收据与一次投稿级贡献攻击；CVPR/ICCV 不成立**
- `cc_recommendation: no`：当前缺口是可直接验证的静态验收器实现问题；新的服务器证据出现前不重复调用 CC。

## 1. 回答“服务器到底搞完还是早停”

服务器确实把 r017 脚本、产物、commit 和 push 做完了，远端 `main` 已到 `b349dcbd...`；它**不是早停**，也没有发生 EQS 性能失败。

但“脚本跑完”不等于“完成 `dis/sug.md` 的全部必做验证”。r017 在缺少若干强制验证的情况下仍报告 `ALL_REQUIRED_PHASES_COMPLETED/FULL_COMPLETION/PASS_STATIC_RECEIPT_R017`。按任务预注册语义，这必须记为 `PROTOCOL_DRIFT_R017`，底层为 `FAIL_AUDIT_IMPLEMENTATION_R017`。因此：

- execution trace：确实跑完并推送；
- contract fulfillment：未完成；
- early stop：否；
- scientific performance failure：否；
- numeric status：仍为 `EXPLORATORY_CORE_SUPPORT_R015`。

## 2. 可采纳证据

1. Git：r017 是 `942a5a2...` 后恰好一个 commit，精确 13 条授权路径；`dis/B.md` 两端 blob 均为 `3181a862137918f1dd41677893937c12b3c39c28`；工作树与 `git diff --check` 通过。12 个非自引用输出及 15 个 tracked inputs 的 bytes/SHA 与 Git blob 匹配。
2. 数值：C 从现有 unit/dataset 字段独立按 `Delta_NRC>=0.02`、CI lower>0、Holm<0.05 重算，六个 unit 与三个 dataset 均支持；覆盖三数据集、三 detector families，FAIR unit D 支持。该结果只支持高置信探索性 Core 证据，不修复揭盲前 seal，也不升级为 confirmatory/deployable。
3. zero sets：六个 zero-eligible 集合均非空，count 与 sorted SHA 已生成，SODA 按 mother scene；canonical split 的历史 SHA256/实际 MD5 parity 差异已披露。
4. 稿件索引：claim ledger 8/8 SHA、唯一命中和标题绑定通过；O2-DFINE、Fourier Angle Alignment 及其它弱根页已标 `UNKNOWN_EXCLUDED`；正文 exploratory、HRSC 跨零、leave-dataset 0/6、fixed-dose descriptive-only、旧 CI/UCB 排除和核心引用扫描通过。

## 3. 拒绝 PASS 的决定性证据

### 3.1 gate 与 summary 没有按合约独立验证

- validator 只检查 `(level,key)`，未检查 bootstrap 的 `(level,key,dataset)` 三元域。
- 它只比较 point/CI/p/Holm/support；r017 要求的 audit rows、cluster count/SHA、bootstrap reps、身份和 detector family 没有从 r016 summary 逐字段比较。r016 summary 本身没有其中多数字段，r017 却没有写 `SOURCE_FIELD_ABSENT`。
- gate 直接筛选 r015 的旧 `supported=True` 后计数，而不是从 Delta/CI/Holm 重新判 support。当前数值恰好通过只能保留探索性事实，不能挽救 validator 的独立性。

### 3.2 feature witness 自相矛盾

冻结 sentinel 契约是 `(u_axis,IoU_loss,center,wdisp,hdisp,score_disp,margin)=(3,1,3,3,3,10,0)`；源码逐值实现了该向量，r017 JSON 却把 sentinel 写成 `false/IMPLEMENTATION_DEVIATION`，validator 又把该 false 硬编码为“预期偏差”并据此通过。w/h swap 只引用 `pred_ar=max/min`，没有行为微测试；0/90 boundary、schema prefix/contains 与逐文件 seal 也未充分验证。

### 3.3 manifest 的 exact closure 为假

`validate_r016_receipt_r017.py` 第 335 行直接 `manifest_path.read_text()`，绕过统一 access wrapper；第 337 行仅比较 path set 与空 runtime，不比较 bytes/SHA/schema，却签发 `manifest_access_exact=true`。报告据此宣称 exact access closure 和 FULL_COMPLETION，直接触发协议漂移。

## 4. 科学与投稿裁决

- r014 正式状态继续是 `FAIL_PROTOCOL_R014`；r015/r016/r017 不能追认 deployable PASS。
- `EXPLORATORY_CORE_SUPPORT_R015` 是当前最强正证据，但 HRSC `0.0602` 的 CI `[-0.0143,0.1438]` 跨零，leave-dataset 仍为 0/6，fixed-dose 仅描述性。CVPR/ICCV 线不成立。
- strong-JSTARS potential 仍可信但未 ready。TGRS/ISPRS JPRS 不能靠换 gate 或修辞升级；先把最后一轮静态裁决诚实闭合，再做投稿级贡献/相关工作/可证伪性攻击。

## 5. 唯一下一步

执行 r018 **static final adjudication**：不重跑 bootstrap、不训练、不推理、不改稿，只修复三元 key、support/gate、source metadata 缺失语义、canonical set witness、feature 微测试和 full-record provenance。r018 成功 token 只表示“裁决收据有效”，可以伴随对 r017 的负裁决；不得再伪装为科学或 venue PASS，也不得自行生成 r019。

## 6. 决策台账

| item | decision | confidence | falsifier / next action |
|---|---|---:|---|
| r017 Git scope | adopt | high | 任一非授权路径或 B blob 变化会推翻；当前未见 |
| r017 FULL_COMPLETION/PASS | reject as protocol drift | high | 只有逐项实现缺失验证且证据一致才可另立新收据，不能回改历史 |
| exploratory numeric core | adopt | high | 三元 key、独立 support/gate 或原始数值复核出现不一致则降级 |
| claim/novelty/manuscript index | adopt | high | r018 动态复核发现 hash、弱来源或边界回归则推翻 |
| early stop / performance | neither | high | r017 已运行和推送；缺陷属于 audit implementation |
| next work | r018 final static adjudication | high | 只允许 `dis/sug.md` 的 10 条写入路径 |
