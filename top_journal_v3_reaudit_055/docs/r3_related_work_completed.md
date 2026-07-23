# R3 —— 相关工作（真实文献）

> 真实存在的论文/官方资料；不虚构引用。少数条目的精确书目字段（页码/卷期）待相机就绪前最终核对，集中列于末尾 blocker 小节；不在此以占位符伪造。核心条目已联网核验（附 URL）。

## 1. 选择性预测与风险-覆盖
- Geifman, El-Yaniv. **Selective Classification for Deep Neural Networks.** NeurIPS 2017.
- Geifman, El-Yaniv. **SelectiveNet: A Deep Neural Network with an Integrated Reject Option.** ICML 2019.
- El-Yaniv, Wiener. **On the Foundations of Noise-free Selective Classification.** JMLR 2010.（risk-coverage 基础）

## 2. 保形预测与保形风险控制
- Vovk, Gammerman, Shafer. **Algorithmic Learning in a Random World.** Springer 2005.
- Angelopoulos, Bates. **A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification.** arXiv:2107.07511（综述）。
- **Conformal Risk Control.** Angelopoulos, Bates, Fisch, Lei, Schuster. ICLR 2024（arXiv:2208.02814）。控制任意单调损失期望，含分布迁移扩展。〔已核验〕
- **Distribution-Free, Risk-Controlling Prediction Sets (RCPS).** Bates, Angelopoulos, Lei, Malik, Jordan. JACM 2021。
- **Learn then Test: Calibrating Predictive Algorithms to Achieve Risk Control (LTT).** Angelopoulos, Bates, Candès, Jordan, Lei. arXiv:2110.01052；Annals of Applied Statistics 2025。以多重假设检验框架控制风险、控 FWER。〔已核验〕

## 3. 分布迁移下的保形
- Tibshirani, Foygel Barber, Candès, Ramdas. **Conformal Prediction Under Covariate Shift.** NeurIPS 2019。
- Gibbs, Candès. **Adaptive Conformal Inference Under Distribution Shift.** NeurIPS 2021。
- Vovk 等. **Mondrian confidence machine.** 2003（分层/条件保形，对应本文按长宽比分层）。

## 4. 检测器校准
- Küppers, Kronenberger, Bär, Haselhoff. **Multivariate Confidence Calibration for Object Detection (D-ECE).** CVPR Workshops 2020。
- Guo, Pleiss, Sun, Weinberger. **On Calibration of Modern Neural Networks.** ICML 2017（ECE 基础）。

## 5. 角度编码与旋转框回归
- **CSL：Arbitrary-Oriented Object Detection with Circular Smooth Label.** Yang, Yan. ECCV 2020。
- **DCL：Dense Label Encoding for Boundary Discontinuity Free Rotation Detection.** Yang, Yang, Yan 等. CVPR 2021。
- **PSC：Phase-Shifting Coder: Predicting Accurate Orientation in Oriented Object Detection.** Yu, Da. CVPR 2023（arXiv:2211.06368）。以不同频率相位统一处理边界不连续与 **square-like（近方形）** 模糊。〔已核验；与本文近方形口径直接相关〕
- **GWD：Rethinking Rotated Object Detection with Gaussian Wasserstein Distance Loss.** Yang, Yan, Feng, He 等. ICML 2021。
- **KLD：Learning High-Precision Bounding Box for Rotated Object Detection via Kullback-Leibler Divergence.** Yang, Yang, Yang, Ming, Wang, Tian, Yan. NeurIPS 2021（arXiv:2106.01883）。KLD **按长宽比调整角度参数的重要性**——与本文几何门控命题（第 §theory）直接呼应。〔已核验〕

## 6. square-like / near-square OBB 问题
- CSL（Yang, Yan, ECCV 2020）与 PSC（Yu, Da, CVPR 2023）均显式讨论旋转对称导致的角度周期模糊与近方形不可辨。
- Qian, Zhang 等. **Learning Modulated Loss for Rotated Object Detection (RSDet).** AAAI 2021（角度边界/近方形损失）。
- Xu, Fu, Wu 等. **Gliding Vertex on the Horizontal Bounding Box for Multi-Oriented Object Detection.** TPAMI 2021。

## 7. 测试时增强与不确定性
- Ayhan, Berens. **Test-time Data Augmentation for Estimation of Heteroscedastic Aleatoric Uncertainty.** MIDL 2018。
- Gal, Ghahramani. **Dropout as a Bayesian Approximation.** ICML 2016（不确定度背景）。

## 8. 旋转检测器与数据集
- 检测器：Oriented R-CNN（Xie, Wang 等, ICCV 2021）；RTMDet（Lyu 等, arXiv:2212.07784）；LSKNet（Li, Wang 等, ICCV 2023）；ARS-DETR（Zeng 等, arXiv:2303.04989）。
- 数据集：DOTA（Xia 等, CVPR 2018）；DIOR-R（Cheng 等, TGRS 2022；原 DIOR：Li 等, ISPRS J. 2020）；FAIR1M（Sun 等, ISPRS J. 2022）；**SODA-A：Towards Large-Scale Small Object Detection: Survey and Benchmarks.** Cheng, Yuan, Yao, Yan, Zeng, Xie, Han. TPAMI 2023（arXiv:2207.14096）〔已核验〕；HRSC2016（Liu 等, ICPRAM 2017）。

## Blocker（相机就绪前需最终核对的精确书目字段）
以下条目为真实工作，但其**精确页码/卷期/确切会议年**需在定稿前对官方出处最终核对（本轮未逐一联网核验，不据记忆伪造精确字段）：CSL、DCL、GWD、RSDet、Gliding Vertex、RCPS、Mondrian、D-ECE、Oriented R-CNN、RTMDet、LSKNet、ARS-DETR、DOTA、DIOR-R、FAIR1M、HRSC2016、Ayhan-Berens、Geifman-El-Yaniv。已联网核验：PSC、KLD、SODA-A、Conformal Risk Control、Learn-Then-Test。

**Sources（已核验）**：
- PSC: https://openaccess.thecvf.com/content/CVPR2023/html/Yu_Phase-Shifting_Coder_Predicting_Accurate_Orientation_in_Oriented_Object_Detection_CVPR_2023_paper.html ；arXiv:2211.06368
- SODA-A: https://arxiv.org/abs/2207.14096 ；TPAMI 10.1109/TPAMI.2023.3290594
- KLD: https://arxiv.org/abs/2106.01883 ；NeurIPS 2021
- Conformal Risk Control: https://openreview.net/ (ICLR 2024) ；arXiv:2208.02814
- Learn then Test: https://arxiv.org/abs/2110.01052
