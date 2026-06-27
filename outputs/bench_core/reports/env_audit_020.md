# Env Audit 020

> 2026-06-27 22:11:26 CST
> reuse-first: existing conda envs probed before any create.

| family | existing_env | repo_path | import_ok | config_build_ok | ckpt_compatible | needs_create | needs_install | blocker |
|---|---|---|---|---|---|---|---|---|
| LSKNet | ai4rs_train | ai4rs_clone/projects/LSKNet | True | True | True (missing=0/406) | False | False | none -> UNBLOCKED via reuse |
| Strip_RCNN | ai4rs_train | ai4rs_clone/projects/Strip_RCNN | True | True | True (missing=2/384 negligible) | False | False | none -> UNBLOCKED via reuse |
| h2rbox_v2 | ai4rs_train | ai4rs_clone/configs/h2rbox_v2 | True | True | True | False | False | none -> UNBLOCKED via reuse (weakly-supervised) |
| point2rbox_v2 | ai4rs_train | ai4rs_clone/projects/Point2Rbox_v2 | True | False | untested | False | False | blocked: model __init__ performs network download (urllib) -> forbidden no-download; also weak/pseudo generator -> nonformal |
| ARS-DETR | none (needs mmrotate 0.1.0) | third_party/ARS-DETR | False | False | untested | True | True | blocked_dependency: mmrotate 0.1.0 fork; no matching env; no ai4rs reuse code; NOT a RHINO substitute |

## 结论
- **3 family 经 reuse(ai4rs_train + ai4rs_clone projects)解锁: LSKNet, Strip_RCNN, h2rbox_v2**（0.3.4 ckpt 完整加载入 ai4rs 1.x 模型）。
- point2rbox_v2: blocked（model __init__ 触发网络下载，禁止；weak/pseudo nonformal）。
- ARS-DETR: blocked_dependency（mmrotate 0.1.0，无匹配 env / 无 ai4rs reuse code；不替代 RHINO）。
- **未创建任何新 env**（reuse 满足）；未安装新依赖；未改 base/已有 env。
