# r051 G0 primary prior-art collision audit

Audit window: 2019-01 through 2026-08. Scope is the frozen conjunction: the same decoded OBB proposal, K-way periodic candidate angles that each change a 7x7 rotated-RoI observation, a shared scorer forming a cyclic posterior, likelihood marginalization into the detector, and a no-GT posterior-tail orientation-risk output bound through NMS.

| Primary source | What it establishes | Collision result |
| --- | --- | --- |
| Ding et al., [RoI Transformer (CVPR 2019)](https://openaccess.thecvf.com/content_CVPR_2019/papers/Ding_Learning_RoI_Transformer_for_Oriented_Object_Detection_in_Aerial_Images_CVPR_2019_paper.pdf) | Learns one oriented RoI transformation from a horizontal RoI. | No cyclic candidate likelihood, marginalization, or native risk. |
| Xie et al., [Oriented R-CNN (ICCV 2021)](https://openaccess.thecvf.com/content/ICCV2021/papers/Xie_Oriented_R-CNN_for_Object_Detection_ICCV_2021_paper.pdf) | Oriented RPN and a conventional oriented RoI refinement head. | No K-way observation intervention or proposal posterior/risk. |
| Han et al., [ReDet (CVPR 2021)](https://openaccess.thecvf.com/content/CVPR2021/papers/Han_ReDet_A_Rotation-Equivariant_Detector_for_Aerial_Object_Detection_CVPR_2021_paper.pdf) | Rotation-equivariant features and rotation-invariant RoI alignment. | Single canonical/invariant feature path, not decoded-proposal cyclic marginalization. |
| Yu and Da, [PSC (CVPR 2023)](https://openaccess.thecvf.com/content/CVPR2023/papers/Yu_Phase-Shifting_Coder_Predicting_Accurate_Orientation_in_Oriented_Object_Detection_CVPR_2023_paper.pdf) | Periodic angle coding to resolve boundary/square ambiguity. | Coder only; no candidate-conditioned RoI observation or posterior risk. |
| Wang et al., [AQE (TGRS 2023)](https://doi.org/10.1109/TGRS.2023.3292111) | Direct angle distribution estimation and angle-quality assessment. | Distribution/quality control, not cyclic visual intervention on one decoded proposal. |
| Ding et al., [O2-RT-DETR (2026)](https://arxiv.org/abs/2603.15497) | Decoder-layer angle-distribution refinement. | Query distribution refinement; no rotated-RoI candidate likelihood or NMS-bound native risk. |
| Zhu and Huang, [PQA (AAAI 2026)](https://ojs.aaai.org/index.php/AAAI/article/view/38411) | Pixel-level scalar localization quality. | Scalar quality output, not complete periodic posterior/marginal likelihood. |
| Gu et al., [FAA (CVPR 2026)](https://arxiv.org/abs/2602.23790) | Frequency-domain direction estimation and canonical RoI feature alignment. | One canonical-angle alignment, not K candidate observations or posterior tail risk. |

## Decision

**PASS_G0_NO_EXACT_COLLISION.** The audit found components and close controls, but no primary source in scope that states or implements the complete frozen conjunction above. This is only a novelty-collision screen, not a claim of publication novelty or a scientific result. All listed methods remain explicit nearest-neighbor controls/boundaries; the planned CMR implementation must still pass the exact provenance and G1 empirical gates.
