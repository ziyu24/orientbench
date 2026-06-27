# SODA-A Status 022

> 2026-06-27 23:48:21 CST

- **present=True**（/home/rspip/cqc/data/dataset/SODA-A）；不再 missing_dataset。
- OBB format: dota_format_tiled_ss/val_tiled DOTA-poly8 txt（+ Annotations/*.json 源）。parser=parse_dota_txt ready。
- baseline: oriented_rcnn #4 valid（mr_dev1x reuse）；lsknet #11/psc #23 也可用；arsdetr #17 blocked。
- status=**present_parser_ready_inference_done**；val_tiled subset 408 img/15187 obj；exploratory NRC 0.84。
