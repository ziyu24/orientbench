# Remaining Detector Blockers 021 (read-only; no install/download)

> 2026-06-27 22:34:45 CST

## ARS-DETR
- needs: mmrotate 0.1.0 fork (third_party/ARS-DETR) + matching torch/mmcv env
- isolated create possible: yes (new conda env, mmrotate 0.1.0 + old mmcv/torch)
- create risk: high: old pinned deps (mmcv-full 1.x, torch<1.10 likely), CUDA build fragile; could fail
- **confusable_with_RHINO: NO — ARS-DETR is a distinct archetype; RHINO host is locked (55a90abb); never substitute**
- network_download: no
- nonformal: no (would be formal_capable once env built)
- min unblock: create isolated mmrotate-0.1.0 env (approval); load #14 ckpt; verify build+ckpt; 4-GPU infer

## point2rbox_v2
- needs: offline pretrained weights for its generator init (currently urllib download in __init__)
- isolated create possible: env ok (ai4rs_train); blocker is runtime network fetch
- create risk: low env / blocked by no-download policy
- **confusable_with_RHINO: NO**
- network_download: YES — model __init__ calls urllib (forbidden)
- nonformal: YES — weak/pseudo-label generator (not formal angle gate)
- min unblock: provide offline cached weight + patch __init__ to skip download (isolated clone, recorded diff); still nonformal
