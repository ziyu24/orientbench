# License & Reproducibility Notes

> 2026-06-29 15:18:48 CST

## License
- 代码：项目内 orientbench/ + scripts/（随项目 license）。
- 第三方：mmrotate / ai4rs / ARS-DETR / LSKNet / Strip-RCNN 等遵循各自 license（third_party/、隔离 clone）。
- 数据：DOTA / DIOR-R / FAIR1M / SODA-A / HRSC2016 遵循各自数据集 license；本项目**未改原始 dataset**。
- 模型：pth_data baseline 只读未改；trained_by_027_replicate 等本项目产物明确标注，不冒充 readme checkpoint。

## Reproducibility
- envs：mr_dev1x (mmrotate 1.x) / ai4rs_train (+ai4rs_clone) / arsdetr (mmrotate 0.1.0) / mr (0.3.4)。详见 final_reproducibility_guide.md。
- 大文件：raw/schema 在 /dev/shm（非持久）；key cells 持久化 outputs/persistent_artifacts/orientbench_v2/（gitignored）+ manifest(sha256+生成命令+can_recompute)。
- thresholds.yaml FROZEN sha256 b7c4e649…；D_cal/D_audit 确定性 md5 split 未变。
- 复算：按 reproducibility guide 重跑 adapter inference + 离线 metrics 脚本（61/65/71/72/73），不重训。
