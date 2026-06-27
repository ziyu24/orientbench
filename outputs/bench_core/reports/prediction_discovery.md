# Real Prediction Discovery

> 生成时间: 2026-06-25 18:21:48 CST
> 只读扫描；未推理/生成 prediction；未修改 pth_data。

- scan roots: ['/home/rspip/cqc/pro/study/pth_data', '/home/rspip/cqc/pro/study/orientbench/outputs', '/home/rspip/cqc/pro/study/orientbench/pth_data']
- candidates: 92 (capped=False); external=19
- real prediction-ish: 19; coco-style needs_conversion: 2; ready schema: 0
- **no_real_prediction_found (ready-schema): True**

## External prediction-ish candidates
| baseline_id | dataset | file_type | size_bytes | parse_status | schema_status | needs_conversion |
|---|---|---|---|---|---|---|
| None | None | json | 17785 | parseable_json | unknown_needs_conversion | True |
| None | None | json | 2 | parseable_json | unknown_needs_conversion | True |
| 26 | DOTA-v1.0 | json | 160845 | parse_error | unknown_needs_conversion | True |
| 26 | DOTA-v1.0 | json | 160845 | parse_error | unknown_needs_conversion | True |
| 27 | DOTA-v1.0 | json | 363899 | parse_error | unknown_needs_conversion | True |
| 27 | DOTA-v1.0 | json | 363899 | parse_error | unknown_needs_conversion | True |
| 64 | DOTA-v1.0 | json | 32438408 | sniffed_large_json | coco_style_needs_conversion | True |
| 13 | HRSC2016 | json | 24876 | parse_error | unknown_needs_conversion | True |
| None | None | json | 32438408 | sniffed_large_json | coco_style_needs_conversion | True |
| 70 | DOTA-v1.0 | json | 104605 | parse_error | unknown_needs_conversion | True |
| 70 | DOTA-v1.0 | json | 104605 | parse_error | unknown_needs_conversion | True |
| 7 | DOTA-v1.0 | json | 88758 | parse_error | unknown_needs_conversion | True |
| 8 | DOTA-v1.5 | json | 93266 | parse_error | unknown_needs_conversion | True |
| 6 | HRSC2016 | json | 18089 | parse_error | unknown_needs_conversion | True |
| 6 | HRSC2016 | json | 18089 | parse_error | unknown_needs_conversion | True |
| 3 | DIOR-R | json | 131334 | parse_error | unknown_needs_conversion | True |
| 3 | DIOR-R | json | 131334 | parse_error | unknown_needs_conversion | True |
| 69 | DOTA-v1.5 | json | 94778 | parse_error | unknown_needs_conversion | True |
| 69 | DOTA-v1.5 | json | 94778 | parse_error | unknown_needs_conversion | True |

说明：coco_style_needs_conversion 表示文件含 image_id/bbox/score/category_id，需转换为 prediction schema（obb_cx/cy/w/h/theta + class_name）后方可正式接入。training_log_not_prediction 为训练日志标量，非 prediction。完整见 prediction_discovery.csv。
