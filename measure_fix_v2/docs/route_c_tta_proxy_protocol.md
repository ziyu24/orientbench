# Route-C TTA Proxy 协议（跑前冻结，041）

> SUPERVISOR_APPROVED_041_ROUTE_C_TTA_PROXY_DEPLOYABLE_CHECK · measure_fix_v2/ 独立 · P1 frozen 只读 · 未改 thresholds/split · 不训练 detector · 不补 full matrix · 不恢复 P2 · 不启动 Track A · DOTA #20 不作调参目标。

## 0. 核心问题
TTA / augmentation consistency proxy 能否在**不使用目标域 GT angle-error 标定**下支撑 deployable reliability-aware selector？

## 1. TTA transforms
- identity（base，已有）。
- **horizontal flip（hflip）**：几何逆映射 cx→W−cx, cy→cy, w→w, h→h, θ→−θ（le90），逆映射可靠 → 主用。
- vertical flip：θ→−θ, cy→H−cy（与 hflip 同理，可靠）→ 视成本可加。
- 90° rotation：le90 下 (w,h,θ)→(h,w,θ±90°) 映射对近方形不稳 → 若不可靠标 unsupported，不硬用。
- **不使用任何目标域 GT angle-error**。

## 2. 训练源 / 测试目标
- source-trained selector：在 source cells 的 D_cal 用 source GT 学（calibration setting）；**target D_audit 只评估**，不调参、不用 target GT。
- leave-dataset + leave-detector，与 040 一致。

## 3. features（全部 GT-free 可部署）
- score；box geometry（log_ar, log_sqrt_area, w, h）；GV-obliquity。
- **TTA hflip angle consistency**：base θ 与 un-flip 后匹配 TTA pred 的 canonical 角度差（小=可靠）。
- **offline GT-free local-angle-consistency**（augmentation-free 备选/补充）：同图邻近预测角度离散度。
- 可加 TTA score stability / box IoU stability。
- detector/class features 仅作分析。

## 4. selector 对照
- baseline1 score-only；baseline2 score+ar+size linear；baseline3 = 039/040 source-trained geometry-aware selector；**Route-C = source-trained geometry + TTA/consistency proxy selector**。

## 5. cells
- 真实 hflip TTA：DIOR ORCNN #3、FAIR1M PSC #24（较小，逆映射可靠）。
- offline GT-free consistency（覆盖更广）：+ DIOR PSC #22、SODA PSC #23、LSKNet #10、**DOTA PSC #20（negative control）**。
- 大文件（TTA 预测）放 /dev/shm scratch；features/manifest 放 measure_fix_v2。

## 6. metrics（D_audit）
- NRC-AUC、AURC、Risk@70/90、p90/p95/p99 after selection、bootstrap CI(400×)、oracle gain retained、per-cell、non-DOTA summary、DOTA negative-control summary。

## 7. 判定（跑前冻结）
- **stable-pass**：Route-C 在 non-DOTA majority cells 显著优于 score+ar+size linear；保留 source-trained/oracle gain 主要部分；DOTA #20 作 documented negative control；无需目标域 GT。
- **partial-pass**：有改善但不稳定 → P3 continue 但仅 deployable candidate。
- **fail**：无法稳定优于 score+ar+size → P3 降级 upper-bound/analysis，不启动 Track A / detector 训练。

## 8. DOTA #20 negative-control 处理
- DOTA #20 = low-oracle-gain / weak-structure negative control；其无明显提升**不计入 fail**，标 documented limitation；**不为其调参**。

## 9. 停止条件
- fail → 停手回报，P3 降级。想改 frozen thresholds/split、训练 detector、启动 Track A、恢复 P2、为 DOTA 调参 → 停手回报。
