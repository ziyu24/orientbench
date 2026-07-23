# Related work references patch

Replace placeholder [R1]-[R7] with real references covering these areas:

1. Selective prediction: Geifman and El-Yaniv, Selective Classification for Deep Neural Networks, NeurIPS 2017, https://papers.neurips.cc/paper/7073-selective-classification-for-deep-neural-networks ; Geifman and El-Yaniv, SelectiveNet, ICML 2019, https://proceedings.mlr.press/v97/geifman19a.html .
2. Conformal/risk control: Bates, Angelopoulos, Lei, Malik, and Jordan, Distribution-Free, Risk-Controlling Prediction Sets, JACM 2021, https://arxiv.org/abs/2101.02703 .
3. Detector calibration / D-ECE: Kueppers et al., Multivariate Confidence Calibration for Object Detection, CVPR Workshops 2020, https://arxiv.org/abs/2004.13546 ; Pathiraja et al., Multiclass Confidence and Localization Calibration for Object Detection, CVPR 2023, https://openaccess.thecvf.com/content/CVPR2023/papers/Pathiraja_Multiclass_Confidence_and_Localization_Calibration_for_Object_Detection_CVPR_2023_paper.pdf .
4. OBB square-like problem and angle periodicity: Yang and Yan, Arbitrary-Oriented Object Detection with Circular Smooth Label, ECCV 2020, https://www.ecva.net/papers/eccv_2020/papers_ECCV/html/666_ECCV_2020_paper.php .
5. CSL / DCL / PSC angle coding: Yang et al., Dense Label Encoding for Boundary Discontinuity Free Rotation Detection, CVPR 2021, https://openaccess.thecvf.com/content/CVPR2021/html/Yang_Dense_Label_Encoding_for_Boundary_Discontinuity_Free_Rotation_Detection_CVPR_2021_paper.html ; Yu and Da, Phase-Shifting Coder: Predicting Accurate Orientation in Oriented Object Detection, CVPR 2023, https://arxiv.org/abs/2211.06368 .
6. GWD / KLD losses: Yang et al., Rethinking Rotated Object Detection with Gaussian Wasserstein Distance Loss, ICML 2021, https://arxiv.org/abs/2101.11952 ; Yang et al., Learning High-Precision Bounding Box for Rotated Object Detection via Kullback-Leibler Divergence, NeurIPS 2021, https://proceedings.neurips.cc/paper/2021/hash/98f13708210194c475687be6106a3b84-Abstract.html .
7. Uncertainty estimation: Gal and Ghahramani, Dropout as a Bayesian Approximation, ICML 2016, https://proceedings.mlr.press/v48/gal16.html ; Lakshminarayanan et al., Simple and Scalable Predictive Uncertainty Estimation using Deep Ensembles, NeurIPS 2017, https://papers.neurips.cc/paper/7219-simple-and-scalable-predictive-uncertainty-estimation-using-deep-ensembles .

Writing edits:

- Abstract: replace 'independent of accuracy signal' with 'an orientation reliability signal not sufficiently characterized by mAP'.
- Selector claim: replace 'proves gains are not box-size prior' with 'supports that gains cannot be explained by box-size priors alone'.
- Add a Scope and Claims subsection in the main text; move claim ledger / forbidden claims to appendix.
