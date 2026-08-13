---
schema_version: 1
review_id: c-review-r022-r027-postpull-20260813
actor: C
review_mode: open_postpull_evidence_check
evidence_head: a4f59f5bcdd44aa596b0a76db080276d20a75ebd
targets:
  - orientbench-b-r022-measurement-validity-20260813
  - orientbench-b-r023-measurement-validity-20260813
  - orientbench-b-r026-dota-external-confirmation-20260813
  - orientbench-b-r027-jprs-paper-package-20260813
verdict: CONTESTED_REVISE
created_at: 2026-08-13T09:37:00-07:00
---

# C post-pull evidence review: r022--r027

## Verdict

`CONTESTED_REVISE`。r022 早停合规；r023 的 DIOR 数值方向可信但完整 runtime 未跨机交付；r026 的 DOTA 数值可作为强描述性外部复现，但其 formal confirmation、validator 和 mutation 闭包不合格；r027 草稿不得以当前措辞投稿。

## 决定性证据

1. r026 `validator_r026.py` 从最终 summary 输入开始，未读取 raw/bootstrap，且没有重算 p/Holm/CI/epsilon/swap。
2. r026 `mutations_r026.py` 直接硬编码 `pristine_exit=0`、`mutated_exit=2`，没有执行验证器。
3. r026 implementation A raw 与 r025 代码 blob 相同；r026 是结果揭示后的审计，不是独立前瞻确认。
4. 当前 Git clone 不含 r023/r026 runtime，无法完成 B/C post-pull 独立重放。
5. r027 的 r026 claim audit 是 summary-to-copy comparison；package manifest 自引用且实际 hash/bytes 不匹配。
6. r027 DOTA `tta_localization` 描述性实现遗漏 `missing_fraction`。

## Scientific reading

保留的结论：AR eligibility domain 是 OBB orientation-reliability estimand 的一部分；DIOR 有正式内部效应，DOTA 显示同向强数值，FAIR1M/SODA-A 不复现界定适用范围。

不接受的结论：`preregistered independent external confirmation`、`CONFIRMED_EXTERNAL_STRONG` 已获 B/C 双方接受、JPRS ready。

## Required resolution

执行一次不改变科学 gate 的 corrective audit，交付最小跨机 raw/replicate bundle，使用 raw-based validator 和真实 mutation；随后修稿并由 C 重放。没有该证据时保持 `CONTESTED`。
