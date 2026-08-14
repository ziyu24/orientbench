---
schema_version: 2
dispatch_id: orientbench-b-r029-bundle-closure-20260813
execution_status: complete
completion_mode: PURE_BUNDLE_CLOSURE
---

# r029 服务器执行报告

补交并 Git force-add 两个原字节 bundle 对象：

- `dota/bootstrap.npy`：1,280,128 bytes，`6b2e0178ff2ec8507289aa9ede02fef65a7f69d36d3de33b78c6f224e48e8d30`。
- `dota/dota_gt_fresh.pkl`：2,680,160 bytes，`3baa2ca8d2d80c7994db371ff8828a77e90c53521e4c2c187e6f61ee46e0beff`。

以 staged Git canonical blob 实测重新核验 `bundle_manifest.csv` 的 20 个无自引用对象：20/20 bytes 与 SHA-256 一致；manifest 内容没有数值差异，故重建结果为零行 diff。未读取科学输入、未重算或修改科学数值/gate/冻结表，也未更改 bundle 其余对象。
