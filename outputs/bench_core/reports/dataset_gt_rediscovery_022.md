# Dataset GT Rediscovery 022 (recursive rescan)

> 2026-06-27 23:48:21 CST
> 监督员裁示纠正: DIOR-R/FAIR1M/SODA-A 均有 OBB 标签；不得因空 annfiles/错 split/错路径判 missing。

| dataset | chosen_ann_dir | split | format | non_empty | obb_sample | parser | why_021_wrong | status |
|---|---|---|---|---|---|---|---|---|
| DIOR-R | annfiles/obb (robndbox 8-corner XML) | splits/val.txt | DIOR robndbox XML (8 corners) | 23463 | 4065 | parse_dior | 021 searched annfiles/obb with *.txt only; real files are *.xml -> false 'empty' | **OBB_FOUND** |
| FAIR1M-v1.0 | split/val_20/annfiles (points XML) | split/val_20 | FAIR1M points/quad XML | 4362 | 10408 | parse_fair1m | 021 find -size precedence bug + assumed split_ss path; val_20/annfiles non-empty XML present | **OBB_FOUND** |
| SODA-A | dota_format_tiled_ss/val_tiled/annfiles (DOTA poly8 txt) | val_tiled | DOTA poly8 txt (+ Annotations/*.json source) | 12832 | 15187 | parse_dota_txt | 021 marked SODA-A missing_dataset; it is PRESENT with dota_format_tiled_ss | **PRESENT_OBB_FOUND** |
| HRSC2016 | annfiles (mbox XML) | splits/test.txt | HRSC mbox XML | 1681 | 1228 | HRSCDataset(mmrotate) | 021 correct; angle uncertain | **OBB_FOUND_angle_uncertain** |

## 021 错误根因
- 递归扫描不足 + 文件扩展名假设错误（DIOR obb 是 .xml 非 .txt）+ find -size 优先级 bug + 未递归发现 SODA-A 的 dota_format_tiled_ss。
- 已全部纠正：真实 OBB GT 解析成功，nonzero。
