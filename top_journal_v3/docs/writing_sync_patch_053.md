# Writing sync patch 053

- Abstract wording: replace independent-of-accuracy phrasing with `mAP未能充分刻画的 orientation reliability signal`.
- Evidence wording: replace proof language with `supports / indicates that gains cannot be explained by box-size priors alone`.
- Scope and Claims: move forbidden claims and claim ledger to appendix; do not repeat `cannot support` in every main table.
- NRC schematic: use `top_journal_v3/figures/nrc_interpretation_schematic.md` and `.csv`.
- Related work patch: replace placeholder references with the following real sources:
  - Selective prediction: Geifman and El-Yaniv, `Selective Classification for Deep Neural Networks`, arXiv:1705.08500; Geifman and El-Yaniv, `SelectiveNet: A Deep Neural Network with an Integrated Reject Option`, ICML/PMLR 2019.
  - Conformal risk control: Angelopoulos, Bates, Fisch, Lei, and Schuster, `Conformal Risk Control`, arXiv:2208.02814 / ICLR 2024; distinguish this guarantee layer from a ranking score.
  - Detector calibration / D-ECE: Kuppers, Kronenberger, Shantia, and Haselhoff, `Multivariate Confidence Calibration for Object Detection`, CVPR Workshops 2020; Pathiraja et al., `Multiclass Confidence and Localization Calibration for Object Detection`, CVPR 2023.
  - OBB square-like and angle periodicity: Yang and Yan, `Arbitrary-Oriented Object Detection with Circular Smooth Label`, ECCV 2020; Yang et al., `Dense Label Encoding for Boundary Discontinuity Free Rotation Detection`, CVPR 2021.
  - PSC mechanism context: Yu and Da, `Phase-Shifting Coder: Predicting Accurate Orientation in Oriented Object Detection`, CVPR 2023.
  - Distribution-aware OBB losses: Yang et al., `Rethinking Rotated Object Detection with Gaussian Wasserstein Distance Loss`, ICML 2021; Yang et al., `Learning High-Precision Bounding Box for Rotated Object Detection via Kullback-Leibler Divergence`, NeurIPS 2021.
  - Uncertainty estimation: Gal and Ghahramani, `Dropout as a Bayesian Approximation: Representing Model Uncertainty in Deep Learning`, ICML 2016; Lakshminarayanan, Pritzel, and Blundell, `Simple and Scalable Predictive Uncertainty Estimation using Deep Ensembles`, NeurIPS 2017.
- Claim ledger / forbidden claims: appendix only; no TPAMI/CVPR-ready wording.
