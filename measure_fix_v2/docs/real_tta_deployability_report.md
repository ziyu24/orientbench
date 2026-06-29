# Real-TTA Deployability Proof 报告 (042)

> SUPERVISOR_APPROVED_042_REAL_TTA_DEPLOYABILITY_PROOF · measure_fix_v2/ 独立 · 原始 dataset **未修改** · 未改 thresholds(b7c4e649)/D_cal-D_audit · 未训练 detector · 未补 full matrix · 未恢复 P2 · 未启动 Track A · DOTA #20 未调参。
> 唯一人读主报告。real TTA = 真实 flip 推理（区别于 041 offline proxy）。

## 1. 041 回顾
- Route-C GT-free offline consistency proxy = STABLE-PASS（non-DOTA 10/10 优于 size-linear，retained 0.718）；但最大缺口 = real TTA 未跑通（041 blocked by empty annfile）。本轮做 **real TTA deployability proof**。

## 2. real TTA blocker 如何修复
- 041 blocker：DIOR `annfiles_dotaformat/test/` 为空，populate 会改 read-only dataset。
- **修复 = shadow farm**（不改原 dataset）：在 `/dev/shm/cqc/orientbench/measure_fix_v2_tta/DIOR-R/` 用 **image symlink（5863）+ 由 GT 生成 annfiles（5863）**，adapter 指向 farm。验证：原 dataset 0 文件被修改（find -newer = 0）。

## 3. shadow farm 方案
- images/：symlink → `/home/rspip/cqc/data/dataset/DIOR/images/trainval/*.jpg`。
- annfiles/：DOTA poly8（由 DIOR-R fullval GT 生成，class=GT class_name）。
- manifest：dior_farm_manifest_042.json（source path、count、original_dataset_modified=false）。

## 4. transform sanity
- GT OBB round-trip（transform forward+inverse）：**hflip / vflip / rot90 IoU=1.0000**（center err 0px、angle err 0°）→ inverse 几何可靠。实用 hflip+vflip（θ→−θ 最稳）；rot90 几何可靠但 near-square 长短边交换在 le90 仍歧义，作可选。详见 tta_transform_sanity_042.{md,csv}。

## 5. real TTA cells
- **成功（real flip 推理，4-GPU world_size=4，DumpDetResults→scratch）**：DIOR ORCNN #3、DIOR PSC #22（各 identity+hflip+vflip）。
- 坐标约定（经验确认）：mmrotate dump 的 flip 预测在 **flipped 帧**，离线 un-flip（cx→W−cx, θ→−θ）后与 base 对齐；残差即 TTA 不一致信号。real TTA consistency：match_frac 0.99-1.00，mean disagreement ~1.4-2°。
- **未成功**：DIOR LSKNet #10（OrientedRCNN 在 adapter 继承下未注册到 mmengine registry，3 次尝试，next-step）；SODA/FAIR1M real-TTA（同 shadow-farm pattern，本轮未建 = next-step coverage）。详见 real_tta_inference_manifest_042.json。

## 6. selector 对比（leave-detector within DIOR，无目标 GT）
| target | score | sizelin | geo | **realTTA** | beats_sz | beats_geo | retained |
|---|---|---|---|---|---|---|---|
| DIOR #3 (ORCNN) | 0.704 | 0.638 | 0.438 | **0.391** | True | True | 0.772 |
| DIOR #22 (PSC) | 0.563 | 0.568 | 0.422 | **0.419** | True | False(marginal) | 0.661 |
- **real TTA Route-C 2/2 显著优于 score+ar+size linear**（deployable）；real_tta_consistency 在 ORCNN #3 优于 geometry-only，PSC #22 与 geometry 相当；mean retained 0.717。

## 7. bootstrap CI
- paired bootstrap 400×。DELTA(sizelin − realTTA) 两 cell CI>0（realTTA_beats_sizelin=True）。DELTA(geo − realTTA)：#3 CI>0，#22 跨 0。详见 results csv。

## 8. DOTA #20 negative control
- 本轮 real TTA 未跑 DOTA #20（DOTA 为 weak-structure negative control，**不调参**）；其状态延续 040/041 诊断（oracle_gain 0.155，未显著反校准）。

## 9. real TTA 裁决：**STABLE-PASS（on tested cells；coverage limited）**
- real TTA Route-C 在测试的 2 个 non-DOTA cells 上**全部显著优于 score+ar+size linear**（无目标 GT），mean retained 0.717，**方向与 041 offline proxy 一致** → **real TTA 证实 offline proxy 结论，deployable 信号真实**。
- **诚实边界**：coverage 限于 2 个 DIOR cells（#10 lsknet config-registry 阻塞、SODA/FAIR1M real-TTA 未建 farm = documented next-step）；real_tta_consistency 在 PSC #22 相对 geometry 增益边际。**不是** full deployability 完成。

## 10. 是否允许 Track A
- **前置满足，可有条件准备**；本轮未启动，待监督员批准作机制支线（非阻塞）。

## 11. 是否允许 P3 method development 继续
- **支持继续**：real TTA 已跑通并证实 deployable 信号（区别于 offline proxy）。
- **不得逾越**：未声称 P3 最终完成 / 顶会 ready；real TTA coverage 仍限 2 cells；selector 训练仍用 source GT（calibration），target 无 GT（deployable 方向）。

## 12. 下一步建议
- 扩 real TTA coverage：修 lsknet registry（custom_imports/scope）、为 SODA/FAIR1M 建 shadow farm → real TTA 跨 dataset/detector 全覆盖。
- few-shot calibration 对比；（待批准）Track A forward dump 机制支线。venue 交合作者。
