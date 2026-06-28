# Adapter Manifest 024

> 2026-06-28 10:58:48 CST

- `configs/_adapters/fv_b3_DIOR-R.py`: _base_ pth_data config + scratch farm + DumpDetResults
- `configs/_adapters/fv_b4_SODA.py`: _base_ pth_data config + scratch farm + DumpDetResults
- `configs/_adapters/fv_b5_FAIR1M.py`: _base_ pth_data config + scratch farm + DumpDetResults
- 仅改 test data path + evaluator(DumpDetResults)；不改 model/batch/lr/schedule。
