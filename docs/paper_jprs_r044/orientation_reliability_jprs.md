# Orientation Reliability in Oriented Object Detection: Geometry-Aware Measurement and Image-Level Risk Control

**Authors:** [AUTHOR NAMES TO BE COMPLETED BY THE OWNERS]

**Affiliations:** [AFFILIATIONS TO BE COMPLETED BY THE OWNERS]

**Corresponding author:** [NAME AND CONTACT TO BE COMPLETED BY THE OWNERS]

## Abstract

Average precision summarizes classification, localization, and confidence ordering, but it does not directly answer whether the reported orientation of a detected remote-sensing object is trustworthy. This distinction matters for ships, aircraft, vehicles, bridges, and elongated infrastructure, where heading or long-axis direction may drive downstream interpretation even when a detection overlaps its target. We present an architecture-independent measurement and risk-control framework for orientation reliability in oriented object detection. First, a controlled full-evaluator intervention rotates matched predictions as far as possible while preserving their pairwise intersection-over-union above 0.5. Across six complete validation units, AP50 is unchanged, whereas AP75 falls by 0.1731--0.6166 and mean long-axis error increases by 29.186--31.886 degrees. Second, we derive an aspect-ratio-dependent angular tolerance from concentric, congruent rectangles and define a well-specified reporting domain and geometry-normalized severe event. Third, normalized risk--coverage (NRC), area under the risk--coverage curve, and fixed-coverage risks measure how any confidence score orders orientation error without conflating ordering with probability calibration. Fourth, we use complete images as exchangeable units in a fixed-sequence Learn-Then-Test procedure with Hoeffding--Bentkus upper bounds. At a nominal risk budget of 0.03, selected detection-score rules have calibration upper bounds from 0.003008 to 0.025875 across six units. Finally, 600 independently and blindly double-annotated targets yield 450 numeric angle pairs with mean circular disagreement 2.3112 degrees (image-cluster 95% interval 1.9970--2.7854); disagreement exceeds 5 degrees in 8.00% of pairs and 10 degrees in 0.8889%. Experiments span DIOR-R, FAIR1M-v1.0, SODA-A, and a local DOTA-v1.0 train/validation protocol. The contribution is a measurement, diagnostic, and finite-sample control framework, not a new detector or a deployable orientation-correction method.

**Keywords:** oriented object detection; remote sensing; orientation reliability; selective prediction; risk--coverage; geometric identifiability; finite-sample risk control

## 1. Introduction

Oriented object detection is a basic component of modern remote-sensing interpretation. Compared with horizontal boxes, an oriented bounding box (OBB) records not only object presence and approximate extent but also a long-axis direction. That direction supports tasks such as estimating vessel alignment at berths, organizing aircraft on aprons, characterizing road and bridge orientation, monitoring parking patterns, and measuring the layout of elongated facilities. A model can therefore be useful as a detector while being unreliable as an orientation sensor. Standard benchmark reporting rarely makes this distinction explicit.

Average precision (AP) is indispensable, but its scientific target is broad. AP combines confidence ordering, class correctness, geometric matching, duplicate suppression, and a chosen overlap threshold. A prediction may have enough overlap to count as correct at IoU 0.5 while its long-axis direction is poor for a downstream heading-sensitive operation. Conversely, AP can change because the center or scale changes even when the angle is held fixed. Reporting AP50 or even AP75 alone consequently does not identify the reliability of the angle coordinate. This is not an argument against AP; it is an argument that detection quality and orientation reliability are different estimands.

The distinction is especially important in aerial imagery. Object sizes, aspect ratios, acquisition conditions, and annotation conventions vary substantially across datasets. Near-square objects have weak or undefined long-axis identity, while slender objects can lose overlap after a small angular rotation. A fixed 5-degree error does not have the same geometric meaning for a nearly square storage tank and a long ship. Moreover, remote-sensing images often contain many spatially and semantically related instances. Treating thousands of objects within the same image as independent replicates produces uncertainty estimates that can be much too optimistic. A defensible orientation-reliability protocol must therefore state the angular equivalence, the eligible geometry, the severity event, the score direction, the matching population, and the statistical unit.

This study develops such a protocol and tests the measurement problem directly. Its starting question is deliberately simple: can AP50 remain unchanged while orientation quality becomes much worse? We answer using a controlled intervention on complete prediction sets rather than a matched-only proxy. For each eligible true-positive prediction, we rotate the box away from its reference orientation while keeping its center, dimensions, class, and confidence fixed and preserving pairwise IoU above 0.5. The entire evaluator is then rerun. Across six detector--dataset units, AP50 is exactly unchanged, yet AP75 and mean angle error deteriorate strongly. A reverse control changes center or scale without touching angle and changes AP, confirming that AP movement need not imply angular movement. Together these controls provide an operational separation between the two quantities.

We next address geometry. Let two rectangles be concentric, congruent, and equal in scale, with aspect ratio (a\geq1). Their IoU as a function of relative rotation gives a tolerance curve (\delta_\tau(a)): the smallest angle at which IoU falls below (\tau). At IoU 0.75, the tolerance at (a=2.1) is 15.3297 degrees and decreases rapidly with aspect ratio. We use this model to define a well-specified reporting region and a severe orientation event. The construction does not claim that an observed prediction--ground-truth pair falls below IoU 0.75 because of angle alone. It instead expresses error in relation to a controlled same-shape geometric reference, while explicitly excluding weakly identifiable near-square cases from the principal interpretation.

Orientation reliability also requires a way to assess ranking. If a detector supplies a confidence score, a user may retain only the highest-scoring detections. A good orientation-reliability score should order low-angle-error instances before high-error instances. Risk--coverage curves describe this behavior across retention levels. We report the area under this curve (AURC), fixed-coverage risks, and NRC, which normalizes observed AURC between oracle and random-ranking baselines. NRC is not an expected calibration error, a probability, or a claim of statistical independence from AP. It is a within-setting ordering diagnostic. This careful interpretation is important because native angle-head signals and detection scores can behave differently across detector and dataset combinations.

Finally, we formulate finite-sample risk control at the image level. The complete evaluation image, including an image with no retained eligible prediction, is the exchangeable unit. Calibration images are separated from images used to define score thresholds, and the final evaluation images do not participate in selection. A bounded per-image loss is controlled through fixed-sequence Learn-Then-Test (LTT) with a Hoeffding--Bentkus bound. This design respects within-image dependence and prevents the number of detections in a dense image from masquerading as the number of independent observations. An instance-independent calculation is retained only as a labeled counterfactual to show how the statistical unit affects the reported bound.

The empirical evidence spans three large remote-sensing test protocols and one local DOTA-v1.0 train/validation protocol, with phase-coded RetinaNet, Oriented R-CNN, and rotated RTMDet families represented. A separate human study supplies a semantic anchor: two annotators independently and blindly labeled the long-axis angle of 600 targets, 200 from each of DIOR-R, FAIR1M-v1.0, and SODA-A. The result clarifies why 5 degrees is a meaningful but annotation-sensitive threshold, whereas 10 degrees has a clearer severe-error margin. Human disagreement is not treated as ground-truth error and is never subtracted from model error.

The contributions are:

1. **A direct validity test for orientation measurement.** A controlled full-evaluator intervention shows that AP50 can be invariant while AP75 and long-axis error deteriorate sharply in six complete validation units.
2. **A geometry-aware estimand.** An explicit rectangle-rotation tolerance curve defines the relation among aspect ratio, angular identifiability, a principal reporting domain, and a normalized severe-orientation event.
3. **A selective reliability protocol.** NRC, AURC, and fixed-coverage risks evaluate whether arbitrary confidence signals rank orientation error, with score direction and population made explicit.
4. **Image-level finite-sample control.** A fixed-sequence LTT procedure controls a bounded per-image severe-risk loss without assuming that detections within the same image are independent.
5. **A cross-dataset evidence base with a human anchor.** Results across multiple OBB detector families and datasets are interpreted together with 600 independent double annotations and explicit negative boundaries.

The scope is intentionally measurement-diagnostic. We do not introduce a new detection head, claim state-of-the-art detection accuracy, or claim that a surviving deployable correction has been established. Evaluated repair attempts did not provide a stable positive method contribution. This limitation sharpens the intended use of the framework: diagnosing when an existing detector's angle output is reliable enough to report or retain, and exposing when a conventional detection metric cannot answer that question.

## 2. Related work

### 2.1 Oriented object detection in remote sensing

Remote-sensing detection datasets established the need to localize objects with arbitrary orientation and extreme scale variation. DOTA introduced a large aerial-image benchmark with quadrilateral annotations and diverse categories [@xia2018dota]. DIOR supplied a broad optical remote-sensing benchmark, and DIOR-R extended its use to oriented detection settings [@li2020dior]. FAIR1M emphasizes fine-grained recognition in high-resolution imagery [@sun2022fair1m], while SODA-A focuses on small objects in aerial scenes [@cheng2023soda]. These benchmarks differ in object density, class granularity, imaging conditions, and annotation semantics. Such diversity motivates cross-setting evaluation, but it also makes pooled claims hazardous: an apparent score behavior can reflect population geometry or annotation conventions rather than a detector-wide law.

Modern OBB detectors differ in proposal design, assignment, regression, and angle representation. Oriented R-CNN adapts a two-stage architecture with oriented proposals and aligned features [@xie2021orientedrcnn]. Real-time one-stage designs such as RTMDet provide a contrasting family [@lyu2022rtmdet]. The present work does not seek to rank these architectures. They are used as heterogeneous hosts for asking whether a metric and risk protocol behave consistently when the detection machinery changes.

### 2.2 Angular periodicity, boundary discontinuity, and square-like ambiguity

Angle regression is complicated by periodic equivalence and parameterization boundaries. Under a long-edge 90-degree convention, adding 180 degrees represents the same physical axis, but a 90-degree change generally swaps the long and short axes rather than preserving the same box semantics. Circular Smooth Label (CSL) recasts angle prediction as circular classification to reduce boundary discontinuity [@yang2020csl]. Dense Label Encoding (DCL) uses a compact coded representation for the same broad problem [@yang2021dcl]. Phase-Shifting Coder (PSC) represents orientation through periodic phase signals [@yu2023psc]. These approaches are valuable for learning, but an angle representation does not by itself provide a calibrated or properly ordered confidence score for downstream selective use.

Distribution-aware losses address another aspect of OBB geometry. Gaussian Wasserstein Distance treats a box through a Gaussian representation and supplies a continuous distance for rotated regression [@yang2021gwd]. Kullback--Leibler-divergence-based regression similarly relates oriented boxes through distributions and adapts sensitivity to object scale and shape [@yang2021kld]. Probabilistic box representations can reduce discontinuities and improve optimization, yet they do not remove the semantic ambiguity of assigning a long-axis angle to a square-like object. The distinction between optimization geometry and evaluation identifiability is central here.

The square-like problem has been recognized in angle coding and OBB evaluation: when width and height are nearly equal, small perturbations of corners or side ordering can produce large changes in the reported long-axis angle without a comparably large change in occupied area. Aspect-ratio-sensitive designs explicitly use shape information [@zeng2024arsdetr]. Our use of aspect ratio is different. We do not propose an aspect-ratio-dependent detector module. We define the domain in which a long-axis angle has a stable geometric interpretation and normalize severe error by a deterministic same-shape tolerance. Ground-truth geometry defines the evaluation estimand; predicted geometry remains distinct from it.

### 2.3 Calibration and uncertainty for object detection

Confidence calibration asks whether scores agree with empirical correctness frequencies. Temperature scaling and expected calibration error are widely used for classification [@guo2017calibration]. Object detection adds localization, class imbalance, duplicate predictions, background false positives, and spatially structured errors. Detection-specific calibration work therefore studies multivariate confidence, class and localization calibration, or joint reliability summaries [@kuppers2020multivariate; @pathiraja2023multiclass]. Self-aware detection further asks whether a detector recognizes its own errors [@oksuz2023selfaware].

Orientation reliability overlaps with this literature but is not identical to it. A detection score can be calibrated for an IoU-defined correctness event while being a poor ordering signal for long-axis error among matched detections. Conversely, a score can rank angle error well without being a calibrated probability of any event. Detection expected calibration error (D-ECE), localization-aware calibration, and NRC answer different questions. Our protocol treats them as complementary. We do not rename NRC as calibration, and we do not infer angle-head uncertainty merely from the behavior of the final detection score.

### 2.4 Selective prediction and risk--coverage evaluation

Selective prediction permits a model to abstain on uncertain examples. Classical selective classification characterizes coverage and conditional risk under a reject option [@elyaniv2010foundations]. Deep selective classification and SelectiveNet demonstrate how confidence and abstention can be evaluated or learned [@geifman2017selective; @geifman2019selectivenet]. More recent work highlights common flaws in selective-system evaluation, including metric choices and the interpretation of AURC [@traub2024flaws].

In OBB evaluation, the corresponding question is operational: if only a fraction of detected objects can be trusted for orientation-sensitive interpretation, does the score retain low-error angles first? A risk--coverage curve exposes the answer over all retention levels rather than at one hand-picked threshold. Oracle and random rankings provide interpretable anchors. Our NRC normalizes AURC between those anchors within the same evaluation population. Because oracle and random baselines depend on the error distribution, NRC comparisons are safest within the same dataset, detector, matching rule, and eligibility definition. We therefore avoid a headline correlation across incomparable datasets.

### 2.5 Conformal prediction and finite-sample risk control

Conformal prediction provides distribution-free coverage statements under exchangeability [@vovk2005algorithmic]. Conformal risk control extends this idea from set coverage to more general bounded losses [@angelopoulos2024crc]. Learn-Then-Test calibrates predictive algorithms through hypothesis testing and multiple-testing control [@angelopoulos2021ltt]. Related work has adapted conformal reasoning to object detection [@andeol2023conformal].

Our finite-sample component is a fixed-sequence LTT procedure for a bounded image-level loss. It is not a guarantee about raw instances, and it is not a proof under arbitrary dataset shift. Exchangeability is assumed at the image level. The method separates a score-fitting subset, a calibration subset that selects a threshold, and a held-out reporting subset. This separation is particularly important in dense aerial imagery, where one image can contribute hundreds of correlated objects. The result is a conditional statement tied to the declared population and risk event, not a universal safety certification.

## 3. Problem formulation and geometry-aware estimand

### 3.1 Canonical long-axis error

An oriented rectangle is represented as (b=(x,y,w,h,\theta)), where ((x,y)) is its center, (w\geq h>0) are long- and short-side lengths after canonicalization, and (\theta) is the long-axis angle. We use the `le90` convention and a 180-degree axial period. For prediction (p) and ground truth (g), the canonical error in degrees is

\[
e(p,g)=\min_{k\in\mathbb Z}|\theta_p-\theta_g+180k|,
\qquad e\in[0,90].
\]

This definition regards antiparallel directions as the same axis. It does not infer a directed heading: bow versus stern, or forward versus backward, is outside the information encoded by an ordinary OBB. It also does not identify orthogonal axes. If a dataset or application provides a directed heading, a different 360-degree event is required.

The error is defined only for an eligible, deterministic prediction--ground-truth pair. Predictions are sorted by the evaluator's confidence rule and matched one-to-one to an unmatched ground-truth object of the same class when rotated IoU is at least 0.5. Unmatched predictions do not have a meaningful ground-truth angle error. They remain part of full AP computation, but they do not enter matched-pair orientation risk. This separation prevents false positives from being assigned an artificial angle of zero or 90 degrees.

### 3.2 Rotation tolerance of a rectangle

Let (R(a,0)) be a rectangle of unit area, aspect ratio (a\geq1), centered at the origin, and aligned with angle zero. Let (R(a,\delta)) be the same rectangle rotated by (\delta\in[0,90]) degrees. Define

\[
J(\delta;a)=\operatorname{IoU}\big(R(a,0),R(a,\delta)\big)
\]

and the first strict tolerance crossing

\[
\delta_\tau(a)=\inf\{\delta\in[0,90]:J(\delta;a)<\tau\}.
\]

The curve is computed by deterministic polygon intersection and bisection to a 0.001-degree solve tolerance. At (a=1), the IoU-0.5 curve does not cross within the first lobe, while (\delta_{0.75}(1)=25.5285\) degrees. At (a=1.6), the 0.5 and 0.75 tolerances are 69.6358 and 19.6727 degrees. At (a=2.1), (\delta_{0.75}(2.1)=15.3297\) degrees; at (a=4), it is 8.1577 degrees; and at (a=8), it is 4.0893 degrees. Thus the same absolute angular error has sharply different overlap consequences as shape changes.

The principal reporting boundary is (a\geq2.1). It approximates the aspect ratio at which a 15-degree rotation crosses below IoU 0.75; the direct inverse is near 2.15. The rounded boundary is an engineering reporting convention, not an estimate fitted to maximize a result. Lower boundaries of 1.3 and 1.6 are sensitivity analyses only. The main mask also excludes prediction or ground-truth boxes that are flagged as near-square under the numerical canonicalization checks. The aspect ratio used in the mask is always taken from the matched ground-truth box.

This construction clarifies the role of geometry without pretending that aspect ratio alone determines uncertainty. Texture, resolution, occlusion, class symmetry, labeling policy, and the angle head all matter. The curve isolates one definitional component: how much angular rotation a congruent rectangle of a given shape can absorb before a reference IoU threshold is crossed. It is useful for defining an estimand, but it is not a learned confidence score and must not be described as a correction method.

### 3.3 Geometry-normalized severe orientation event

For eligible match (i), let (a_i) be the ground-truth aspect ratio and (e_i) the canonical angle error. The primary severe event is

\[
Y_i=\mathbf 1\{e_i>\delta_{0.75}(a_i)\}.
\]

The event says that the angle error exceeds the rotation required to push a same-center, same-scale, congruent reference rectangle below IoU 0.75. It does **not** say that the observed prediction pair has IoU below 0.75, because an observed pair can also differ in center and scale. This distinction prevents a geometric normalization from being confused with a decomposition of observed IoU.

For continuous ranking analyses, we additionally use canonical error (e_i) directly. A clipped geometry-normalized continuous risk may be written as

\[
r_i^{\mathrm{geo}}=\frac{1}{3}\operatorname{clip}\!\left(
\frac{e_i}{\max(\delta_{0.75}(a_i),1^\circ)},0,3\right),
\]

which lies in ([0,1]). Fixed-angle events (e_i>5^\circ), (e_i>10^\circ), and (e_i>15^\circ) are retained as sensitivity endpoints. The human study below shows why 5 degrees should be labeled noise-sensitive, especially on SODA-A, whereas 10 degrees has a clearer severe-tail interpretation. The geometry-normalized event remains primary because it explicitly accounts for shape.

### 3.4 Risk--coverage and normalized ranking quality

Let (s_i) be any scalar score declared such that larger values mean greater trust. Sort eligible matches in descending score order, with deterministic stable handling of ties. At coverage (c\in(0,1]), retain the first (k(c)=\lceil cn\rceil) instances. For continuous angular risk,

\[
R_s(c)=\frac{1}{k(c)}\sum_{j=1}^{k(c)}e_{(j)}.
\]

The area under the risk--coverage curve is computed on the fixed coverage grid (\mathcal C):

\[
\operatorname{AURC}(s)=\frac{1}{|\mathcal C|}\sum_{c\in\mathcal C}R_s(c).
\]

We also report Risk@70 and Risk@90. These quantities answer a concrete deployment-style question: among the retained 70% or 90% of matched detections, what is the average orientation error? They are empirical summaries unless paired with an explicit finite-sample procedure.

To make ranking quality interpretable relative to the error distribution, define an oracle ordering (s^\star) that sorts by increasing error and a random-ranking expectation (s^{\mathrm{rnd}}). NRC is

\[
\operatorname{NRC}(s)=
\frac{\operatorname{AURC}(s)-\operatorname{AURC}(s^\star)}
{\operatorname{AURC}(s^{\mathrm{rnd}})-\operatorname{AURC}(s^\star)}.
\]

An NRC of zero corresponds to oracle ordering, one to random ordering in expectation, and a value above one to reverse ordering relative to random. Values below one are informative within the declared population. NRC should not be pooled as though its denominator were invariant across datasets. It is not a probability calibration score and does not prove independence from AP.

### 3.5 Image-level risk and finite-sample threshold selection

Selective reporting introduces a second objective: choose a threshold on (s) such that retained orientations have bounded severe-event risk. Let (\mathcal I) be the complete evaluation-image universe. For image (I\), threshold (t), and retained eligible set (S_I(t)=\{i\in I:s_i\geq t\}), define

\[
L_I(t)=
\begin{cases}
|S_I(t)|^{-1}\sum_{i\in S_I(t)}Y_i,& |S_I(t)|>0,\\
0,& |S_I(t)|=0.
\end{cases}
\]

This bounded loss gives every image one contribution regardless of object density. An image with no eligible or retained prediction remains in the universe with loss zero; silently dropping it would change the estimand. A secondary image event,

\[
Z_I(t)=\mathbf1\{\exists i\in S_I(t):Y_i=1\},
\]

records whether any retained severe error occurs in the image. Exact Clopper--Pearson bounds are reserved for this binary secondary endpoint. They are not applied to the bounded average (L_I(t)).

The outer calibration set is deterministically split into (D_{\mathrm{fit}}) and (D_{\mathrm{cal}}). The fit subset defines a fixed menu of candidate thresholds corresponding to target coverages. It does not certify them. On (D_{\mathrm{cal}}), the method computes a one-sided Hoeffding--Bentkus upper confidence bound (U_{HB}(t;\delta)) for (\mathbb E[L_I(t)]). Candidate coverages are tested in a fixed sequence, from conservative to permissive, for risk budgets (\alpha\in\{0.03,0.05,0.10\}) and failure probability (\delta=0.10). Testing stops at the first candidate that cannot be certified. The most permissive previously certified candidate is selected. The held-out (D_{\mathrm{audit}}) subset reports realized coverage and risk and never changes the selected threshold.

The guarantee depends on exchangeability of complete images within the target population and on the fixed procedure. It does not survive arbitrary covariate shift automatically. It also does not guarantee the angle of an unmatched prediction, since angle error is undefined without a match. The benefit of the design is more modest and concrete: within the declared evaluation distribution, it does not count correlated detections in a single dense aerial image as independent trials.

## 4. Experimental design

### 4.1 Datasets and detector families

The evidence covers DIOR-R, FAIR1M-v1.0, SODA-A, and DOTA-v1.0. DIOR-R contains diverse optical remote-sensing categories and provides three full-validation detector units. FAIR1M-v1.0 contributes a fine-grained phase-coded RetinaNet unit. SODA-A contributes phase-coded RetinaNet and Oriented R-CNN units under its project evaluation split. DOTA-v1.0 contributes two additional detector families under a local train/validation protocol. No public DOTA trainval/test comparison is made, and no public-test state-of-the-art claim is inferred.

The six principal units are: a phase-coded rotated RetinaNet, Oriented R-CNN, and rotated RTMDet-S on DIOR-R; phase-coded rotated RetinaNet on FAIR1M-v1.0; and phase-coded rotated RetinaNet plus Oriented R-CNN on SODA-A. The geometry-normalized descriptive table additionally contains local DOTA-v1.0 Oriented R-CNN and rotated RTMDet-M units. This composition gives variation in one-stage versus two-stage designs and angle-head type, but it is not a complete factorial detector matrix.

For non-DOTA datasets, the established project split follows trainval for training and test for evaluation. DOTA uses train for training and val for evaluation. The present study performs no training or inference; all results are derived from frozen, tracked prediction and evaluation artifacts. Dataset names are therefore shorthand for these exact project protocols rather than claims about every public benchmark configuration.

### 4.2 Matching and eligible population

Full AP is computed on the entire post-NMS prediction set using rotated polygon IoU, classwise confidence sorting, one-to-one greedy matching, and the declared interpolation convention. Orientation analyses use deterministic class-constrained matches at IoU at least 0.5. The main geometry-aware population requires matched ground-truth aspect ratio (a_i\geq2.1) and excludes canonicalization-unstable near-square boxes. Matching, eligibility, and risk are separate operations: matching determines whether angle error is defined; eligibility determines whether long-axis interpretation is strong enough for the principal report; risk evaluates the error among eligible matches.

The ground-truth aspect ratio defines the evaluation population and severe-event threshold. A model-side score may use only variables actually available on the prediction side unless explicitly labeled as a target-ground-truth-fitted upper bound. This separation is essential. If ground-truth geometry both defines the event and is used as an input to a purported deployable confidence score, the result becomes circular. We report geometry-dependent fitted scores, where referenced, only as analysis upper bounds.

### 4.3 Controlled angle intervention

The primary validity experiment begins with complete predictions, complete ground truth, and the post-NMS identity of every prediction. Eligible matched true positives are rotated away from their reference angle while keeping center, width, height, class score, class label, and all unmatched predictions fixed. The maximum perturbation is constrained so that the prediction's pairwise rotated IoU with its original matched ground truth remains above 0.5. A small numerical margin prevents boundary ambiguity.

After perturbation, the full evaluator rematches predictions and recomputes AP50 and AP75. This is not a matched-only AP surrogate: false positives, classwise score ordering, and rematching remain active. The protocol also verifies that the number of false positives at IoU 0.5 is unchanged. Mean canonical angle error is recomputed on the resulting matched population. Because the intervention is explicitly designed to preserve the 0.5 match condition while worsening orientation, it is a stress test of what AP50 can detect, not a natural corruption model.

The reverse control holds angle fixed and changes either center or scale. Center shifts of 0.1 or 0.2 times the square root of box area, and a uniform scale factor of 0.85, reduce AP50 and AP75 for representative DIOR-R units while angle error is unchanged. This control shows the opposite dissociation: AP can move without angle moving. The two interventions therefore bracket the measurement distinction.

### 4.4 Ranking scores and statistical summaries

Detection score is the principal broadly available ranking signal. For phase-coded units, the native phase magnitude is included as a detector/dataset diagnostic where available. Test-time augmentation circular variance and other native signals appear only within their predefined score menus. Larger-is-more-trustworthy direction is declared before curve computation; a score is never silently negated after observing the result.

For representative NRC estimates, uncertainty is obtained by resampling complete images and keeping all their matched detections together. The intervals therefore reflect image-level clustering. We do not headline cross-dataset Spearman correlations between NRC and AP. Detector family, error distribution, aspect-ratio mix, and random-oracle denominator all differ across settings, so within-setting comparisons are more defensible.

### 4.5 Human double-annotation protocol

Two distinct annotators independently labeled the long-axis orientation of the same 600 canonical targets, 200 each from DIOR-R, FAIR1M-v1.0, and SODA-A. Task order was independently randomized, and neither annotator saw the other annotation, model angle, or ground-truth angle. A target could receive a numeric axial angle, an ambiguous decision, or a skip decision. The primary endpoint preserves all original decisions rather than converting nonnumeric decisions to zero disagreement.

Among the 600 targets, 450 received numeric angles from both annotators. Circular disagreement uses the same 180-degree axial period as the model metric. Uncertainty is estimated by clustering on source image with 10,000 bootstrap replicates. A secondary blinded recheck examined 29 one-sided nonnumeric cases; 27 yielded a numeric pair and two remained ambiguous. These rechecks do not overwrite primary outcomes. The study supports aggregate and broad dataset-level interpretation, not precise rare-class or extreme-tail rates.

### 4.6 Multiplicity and evidence identity

The controlled perturbation is interpreted as a repeated directional result across six units rather than six unrelated discoveries. NRC intervals are descriptive within settings. Image-level LTT controls its threshold family through the fixed sequence. Human intervals use source-image clusters. Geometry curves are deterministic numerical calculations and do not receive sampling intervals.

Evidence identities are kept separate. The principal full-validation perturbation, geometry event, and image-level risk-control outputs are formal results. Some ranking and reverse-control summaries are descriptive. Human annotation is a separate study. DOTA evidence follows the local train/validation protocol and includes a post-outcome independently checked component; it is not described as a pristine prospective public-test confirmation. These labels prevent a coherent-looking table from erasing differences in how and when evidence was obtained.

## 5. Results

### 5.1 AP50 does not identify orientation reliability

Table 1 reports the complete controlled-intervention result. Every unit has (\Delta\mathrm{AP50}=0.0000), and the number of false positives at IoU 0.5 is unchanged. The result is exact to the persisted reporting precision rather than merely statistically nonsignificant. In contrast, AP75 decreases in every unit, by 0.4953, 0.4226, and 0.6166 on the three DIOR-R units; 0.1731 on FAIR1M-v1.0; and 0.2144 and 0.3413 on the two SODA-A units. Mean angle error increases by 30.838, 30.116, 31.535, 31.886, 29.186, and 30.745 degrees, respectively. Across all units, the AP75 loss spans 0.1731--0.6166 and the angular increase spans 29.186--31.886 degrees.

| Dataset / unit | Detector | AP50 original | AP50 perturbed | AP75 original | AP75 perturbed | Mean error original | Mean error perturbed |
|---|---|---:|---:|---:|---:|---:|---:|
| DIOR-R/3 | Oriented R-CNN | 0.7999 | 0.7999 | 0.5850 | 0.0897 | 4.593° | 35.431° |
| DIOR-R/22 | Rotated RetinaNet-PSC | 0.6964 | 0.6964 | 0.4980 | 0.0753 | 4.758° | 34.874° |
| DIOR-R/61 | Rotated RTMDet-S | 0.8866 | 0.8866 | 0.7148 | 0.0982 | 4.375° | 35.910° |
| FAIR1M-v1.0/24 | Rotated RetinaNet-PSC | 0.3452 | 0.3452 | 0.2369 | 0.0638 | 4.631° | 36.516° |
| SODA-A/23 | Rotated RetinaNet-PSC | 0.6119 | 0.6119 | 0.2349 | 0.0205 | 5.230° | 34.416° |
| SODA-A/4 | Oriented R-CNN | 0.7592 | 0.7592 | 0.3627 | 0.0214 | 5.148° | 35.893° |

The intervention's mean allowable rotation is approximately 33.65--35.41 degrees across units. This confirms that the construction exploits the tolerance of the IoU-0.5 decision boundary rather than a bookkeeping artifact. The full evaluator is rerun, so the result does not arise from computing AP on only the preselected matches. Figure 1 visualizes the separation, and Figure 2 shows the original and perturbed AP75 and angle-error values.

The reverse control reinforces the interpretation. On DIOR-R/3, a center shift of (0.1\sqrt{\text{area}}) reduces AP50 from 0.7999 to 0.7683 and AP75 from 0.5850 to 0.2062 while leaving angle untouched. A 0.85 scale factor reduces AP50 to 0.7615 and AP75 to 0.0843, again with no angular change. Corresponding controls on DIOR-R/22 reduce AP50 and AP75 without changing angle. AP is therefore sensitive to multiple box components, and AP50 can be deliberately insensitive to large angle changes within its match tolerance. A separate orientation report is justified.

This finding should not be overstated. The intervention is constructed, not sampled from a natural sensor degradation. It proves non-identification: AP50 alone cannot rule out large orientation deterioration. It does not estimate how often such deterioration occurs in deployment, nor does it imply that AP75 is an angle metric. AP75 is more sensitive in this intervention but still mixes center, scale, class, duplicates, and confidence ordering.

### 5.2 Geometry changes the meaning of an angular error

Figure 3 shows the deterministic tolerance curves. The (\delta_{0.75}(a)) curve falls monotonically over the displayed range: 25.5285 degrees at aspect ratio 1, 19.6727 at 1.6, 16.0548 at 2.0, 15.3297 at 2.1, 12.9594 at 2.5, 8.1577 at 4, and 4.0893 at 8. The IoU-0.5 tolerance is infinite within the first 90-degree lobe for sufficiently square rectangles, is 69.6358 degrees at 1.6, 47.4084 at 2.0, 19.9234 at 4, and 9.6457 at 8. These numbers explain why a permissive overlap threshold can hide a large angular change and why a fixed degree threshold does not have uniform geometric severity.

Within the (a\geq2.1) principal domain, retained matched counts are 49,502, 54,297, and 53,671 for the DIOR-R units; 31,801 for FAIR1M-v1.0; 197,529 and 235,428 for SODA-A; and 33,029 and 34,383 for the two local DOTA-v1.0 units. Geometry-normalized severe-event rates are 0.0081, 0.0082, 0.0167, 0.0052, 0.0036, 0.0053, 0.0019, and 0.0029, spanning 0.0019--0.0167. Mean angle error ranges from 1.719 to 2.280 degrees, while p90 ranges from 3.930 to 5.172 degrees.

These rates are descriptive properties of matched, well-defined orientations. They should not be read as end-to-end failure probabilities for all detections: false positives and false negatives are outside the matched-angle denominator. Nor are lower rates automatically better detector scores across datasets, because object composition and annotation differ. Their purpose is to show that the event can be computed consistently and that its prevalence is nonzero but relatively rare under the frozen matching rule.

The use of matched-ground-truth aspect ratio is deliberate. It gives the event a stable evaluation meaning, independent of whether a detector predicts width and height accurately. The cost is that the event cannot be computed for unlabeled deployment data. It is an evaluation target, analogous to class correctness or IoU, rather than an inference-time signal. Predicted aspect ratio can be used by a score, but it must not silently replace ground-truth aspect ratio in the definition of success.

### 5.3 Confidence ranking is setting dependent

Figure 4 reports representative masked NRC values with image-cluster intervals. Detection score is informative in all four displayed PSC settings: NRC is 0.6926 [0.6718, 0.7111] on DOTA-v1.0/20, 0.5424 [0.5292, 0.5562] on DIOR-R/22, 0.8848 [0.8649, 0.9074] on FAIR1M-v1.0/24, and 0.9138 [0.9028, 0.9257] on SODA-A/23. The intrinsic phase magnitude differs: 0.9638 [0.9292, 0.9980] on DOTA, 1.1286 [1.0984, 1.1596] on DIOR-R, 1.1009 [1.0767, 1.1206] on FAIR1M, and 1.0902 [1.0806, 1.1003] on SODA-A.

The correct inference unit is detector/dataset/score. Detection score ranks continuous angle error better than random in these comparable masked populations. The native phase magnitude is near random but slightly informative on the displayed DOTA unit and reverse-ordered on the other three. This pattern does not prove that a PSC angle head is generally anti-calibrated. Phase magnitude is not necessarily designed as a confidence probability, the displayed units do not cover every PSC implementation, and score behavior can change with the population definition. The result supports a narrower diagnostic statement: a native angle signal and the final detection score can carry different orientation-risk ordering information.

The masked and unmasked analyses further warn against population drift. When near-square and lower-aspect-ratio objects are included, apparent ordering can change because the angle itself becomes less identifiable and the oracle--random normalization changes. We therefore do not treat a sign flip across aspect-ratio populations as evidence that a learned selector repaired a detector. Later controlled work found that the dominant component of an earlier geometry-selector gain was definitional. The positive contribution here is the explicit estimand and diagnostic, not a nonlinear score.

### 5.4 Image-level risk control avoids pseudo-replication

For the principal detection score at (\alpha=0.03), all six units select the full target-coverage candidate under the image-level procedure. Calibration Hoeffding--Bentkus upper bounds are 0.0153817, 0.0161449, and 0.0258754 for the DIOR-R units; 0.00536176 for FAIR1M-v1.0; and 0.00307779 and 0.00300844 for the SODA-A units. These values span 0.003008--0.025875 and lie below the 0.03 target risk. Held-out mean image risks are 0.0120770, 0.0132485, 0.0215337, 0.00349409, 0.00163027, and 0.00223282.

| Unit | Calibration images | Held-out images | Selected target coverage | Calibration HB UCB | Held-out mean image risk | Held-out instance coverage |
|---|---:|---:|---:|---:|---:|---:|
| A | 3,003 | 5,900 | 1.0 | 0.0153817 | 0.0120770 | 1.000000 |
| B | 3,003 | 5,900 | 1.0 | 0.0161449 | 0.0132485 | 0.999928 |
| C | 3,003 | 5,900 | 1.0 | 0.0258754 | 0.0215337 | 0.999927 |
| D | 1,076 | 2,142 | 1.0 | 0.00536176 | 0.00349409 | 1.000000 |
| E | 5,717 | 11,522 | 1.0 | 0.00307779 | 0.00163027 | 0.999990 |
| F | 5,717 | 11,522 | 1.0 | 0.00300844 | 0.00223282 | 0.999983 |

Full selected coverage is not evidence that thresholding is unnecessary in general. It reflects the low prevalence of the primary severe event and the declared 0.03 mean-image budget in these particular units. More stringent budgets, a different event, dataset shift, or a population including unmatched outcomes could require abstention. The table is valuable because it shows the entire selection result, including nonempty-image proportions and realized coverage in the machine-readable supplement, rather than reporting only a favorable retained subset.

Figure 5 compares the formal image-level upper bound with an invalid instance-independent counterfactual. On unit A, the image-level bound is 0.0153817 while the instance-iid exact-binomial value is 0.00865956; the retained-instance count is 4.425 times the number of calibration images. On unit B, the corresponding values are 0.0161449 and 0.00733765 with a 4.740 inflation ratio. Dense SODA-A units have 7.737 and 9.250 retained instances per calibration image. The direction is not uniformly conservative for every cell because the image loss weights images equally while instance risk weights objects equally, but the comparison shows that the two analyses estimate different quantities. The instance-iid value is never presented as a valid guarantee.

The procedure also separates empirical instance risk from image risk. For example, held-out empirical instance severe-risk is 0.008378 on A, versus mean image risk 0.012077; on F it is 0.005805, versus mean image risk 0.002233. Differences can go either way because dense images receive more weight in the instance estimand. Declaring the unit is therefore not a cosmetic variance adjustment; it defines the population average.

### 5.5 Human disagreement anchors threshold semantics

The 600-target human protocol yields 450 primary numeric pairs: 122 from DIOR-R, 169 from FAIR1M-v1.0, and 159 from SODA-A. Overall mean 180-degree circular disagreement is 2.3112 degrees, with an image-cluster 95% interval of 1.9970--2.7854. The median is 1.6359 degrees, p90 is 4.4220 degrees, and p95 is 5.9359 degrees. The probability of disagreement above 5 degrees is 0.0800 [0.055679, 0.105621], and above 10 degrees is 0.008889 [0.002208, 0.017897]. Figure 6 summarizes these quantities.

Dataset-level means are 1.6725 degrees for DIOR-R, 2.0655 for FAIR1M-v1.0, and 3.0623 for SODA-A. SODA-A also has the heavier tail: p90 5.1520 degrees, p95 8.0200 degrees, (P(>5^\circ)=0.113208), and (P(>10^\circ)=0.025157). DIOR-R and FAIR1M have no observed disagreement above 10 degrees among their numeric pairs, but finite sample size prevents interpreting zero events as a zero population rate.

The (a\geq2.1) subset contains 308 pairs. Its mean is 2.2823 degrees, median 1.6130, p90 4.1978, p95 5.5860, (P(>5^\circ)=0.068182), and (P(>10^\circ)=0.006494). The similar mean in the well-defined region indicates that excluding square-like cases does not eliminate human disagreement. It does, however, provide a clearer long-axis semantic target.

These results constrain language around risk budgets. Mean-risk budgets near 1.5--2 degrees approach the scale of inter-annotator disagreement and should be described as label-noise-aware rather than as physical heading guarantees. A 5-degree event is meaningful but annotation-sensitive: 8.00% of numeric pairs cross it. A 10-degree event has substantially more separation from typical disagreement, although SODA-A retains a non-negligible tail. Human disagreement is not an estimate of dataset ground-truth error, because neither annotator is an oracle and the sampled task differs from the annotation production process. We therefore use it only as a semantic anchor.

### 5.6 Cross-dataset boundaries and negative method evidence

The measurement-validity intervention is directionally consistent across all six principal units. The geometry event is computable across eight units, and image-level risk control closes for the six principal units under the stated budget. Ranking behavior, however, is heterogeneous. This combination supports a general measurement warning and a reusable protocol, but not a universal claim that one score is always reliable.

Several evaluated correction routes did not survive their prespecified tests. An earlier nonlinear geometry selector's apparent reversal was largely attributable to the aspect-ratio-defined component of the estimand; target-domain ground-truth fitting remains an upper bound. A set-valued coverage-transfer route did not establish transferable benefit. Two orientation-error ranking variants showed no positive generalized risk--coverage improvement across their evaluated matrix. A symmetric angular head configuration caused large AP50 and AP75 regressions on DIOR-R and SODA-A. Because that implementation differed from its frozen formula, it rejects only the evaluated configuration and cannot prove that the broader method class is impossible.

These negative results are not presented as contributions or hidden behind the measurement paper. They define the present boundary: there is no surviving deployable repair that can be recommended without target-domain angle labels. The framework can measure, diagnose, and control reported risk under an evaluation distribution; it does not fix the detector.

## 6. Discussion

### 6.1 What AP and orientation reliability each measure

AP remains the primary metric for end-to-end detection. It penalizes missed objects, false positives, duplicate predictions, poor localization, and confidence ranking. Orientation reliability is conditional on an eligible matched detection and asks whether its long-axis estimate is accurate and appropriately ordered by a trust score. Neither subsumes the other. A detector with excellent angle estimates on its true positives can still have poor AP because it misses many objects; a detector with strong AP50 can still supply unreliable angles among its matches.

The controlled intervention makes this distinction visible without relying on correlation. Correlations between AP and NRC across datasets would mix different populations and denominators. The intervention holds most prediction properties fixed and selectively worsens orientation while preserving the AP50 match condition. The reverse control holds orientation fixed while changing localization. This pair of manipulations provides clearer construct-validity evidence than a cross-model scatter plot.

AP75 is more sensitive than AP50 to the controlled angle changes, but it is not a substitute for angle error. Its sensitivity depends on aspect ratio and on center and scale quality. The proposed geometry curve helps explain this dependence. In practice, we recommend reporting AP50/AP75 together with mean or quantile long-axis error in a declared well-defined domain, a severe-event rate, and a risk--coverage summary for the intended confidence score.

### 6.2 Safe use of reliability scores

A reliability score is useful only after its direction, population, and target risk are specified. Detection score is attractive because it is universally available, but it is trained for class and objectness objectives rather than directly for angular accuracy. Native angle-head quantities may contain orientation information, yet their numerical scale need not have an uncertainty interpretation. A score that works on one dataset can reverse on another because the mapping among texture, shape, detection confidence, and angle error changes.

Risk--coverage curves should therefore be treated as diagnostic objects. When a score is intended for operational selection, threshold calibration must be separated from final assessment. If target-domain angle labels are used to fit the score, the result is a target-calibrated analysis upper bound, not a label-free deployment method. Test-time augmentation consistency can be computed without target labels, but it still requires prospective validation under the exact augmentation and matching policy.

The image-level LTT component provides one route for selecting thresholds when labeled calibration images are available. It does not eliminate the need for monitoring under shift. A deployment could maintain a calibration stream of representative labeled scenes, certify a threshold for a bounded per-image risk, and abstain or flag orientations below the threshold. When the acquisition platform, geography, season, resolution, or class mixture changes, the exchangeability assumption should be revisited.

### 6.3 Remote-sensing relevance

Orientation is not equally important for every category. For circular storage tanks, square sports courts, or visually symmetric objects, long-axis angle may have little semantic meaning. For ships, aircraft, bridges, wind turbines, long vehicles, and runways, it can be important for alignment, movement inference, map updating, or spatial organization. The well-defined domain prevents the evaluation from rewarding a method for predicting an arbitrary angle on near-square objects.

Dense aerial scenes make statistical unit choice consequential. A port image containing hundreds of ships is not hundreds of independent acquisitions. Atmospheric conditions, sensor blur, sun angle, annotation style, and detector feature maps create shared dependence. Image-level loss gives such a scene one exchangeable contribution. This choice corresponds naturally to a use case in which a scene-level batch is the unit on which risk is managed.

The human anchor further connects geometric metrics to interpretation. A numerical threshold far below ordinary inter-annotator disagreement risks giving a false impression of physical precision. The heavier SODA-A tail demonstrates that annotation difficulty itself is dataset dependent. Reporting a single universal 5-degree accuracy figure without annotation context would therefore be misleading.

### 6.4 Relation to detector calibration

Probability calibration and selective ordering should be reported separately. D-ECE asks whether detections with a given confidence have an observed correctness frequency after conditioning or binning choices. NRC asks how the score orders a continuous angle loss among matched eligible detections. A monotone transformation can preserve NRC while changing calibration; a nonmonotone recalibration can change ordering. Likewise, a score can be calibrated for IoU-0.5 correctness yet fail to rank angular error.

A complete reliability study could report class calibration, localization calibration, orientation-event calibration, and risk--coverage together. The current evidence is strongest for the orientation measurement and ranking components. We do not claim that the severe-event score is a calibrated probability. The LTT threshold certifies a bounded mean image loss under exchangeability; it does not calibrate each individual score value.

## 7. Limitations

First, the main orientation analysis is conditional on class-correct matches at rotated IoU at least 0.5. It does not assign angle risk to false positives or missed objects, so it must accompany rather than replace AP. An end-to-end operational loss could combine detection and angle consequences, but that requires application-specific costs not defined here.

Second, the geometry model uses concentric, same-scale, congruent rectangles. Real prediction errors combine translation, scale, aspect-ratio, and rotation. The tolerance curve is an estimand-normalization device, not a causal decomposition of observed IoU. Its (a\geq2.1) boundary is interpretable and frozen, but alternative applications may choose a different overlap threshold or semantic boundary.

Third, near-square and symmetric objects do not have a uniquely stable long-axis orientation. Excluding them improves interpretability but narrows the population. Results for lower aspect ratios remain sensitivity analyses. Category semantics can also override rectangular geometry: an object may have a meaningful directed heading even when its box is nearly square, or no meaningful heading despite being elongated.

Fourth, score results are partly at the detector/dataset level. The phase-magnitude observations do not prove that the PSC angle head is universally anti-calibrated. DOTA uses a local train/validation protocol and is not compared with published trainval/test numbers. The detector coverage is heterogeneous but not a complete architecture-by-dataset matrix.

Fifth, the finite-sample guarantee assumes exchangeable images from the declared population. It does not guarantee performance after geographic, temporal, sensor, or resolution shift. The selected full-coverage thresholds reflect a relatively rare severe event and the chosen 0.03 mean-image budget. Different risks can lead to different decisions.

Sixth, the human study measures disagreement, not truth. It contains 600 primary decisions and 450 numeric pairs, enough for aggregate and broad dataset comparisons but not for precise rare-class, size-bin, or extreme-tail inference. A directed-heading study would require additional semantic labels and expertise.

Seventh, no evaluated correction method produced a stable, deployable repair. Target-domain ground-truth-fitted scores are only upper bounds. Failed geometry selection, set-valued transfer, orientation-ranking, and symmetric-head experiments are not positive method evidence. Consequently, this paper provides measurement, diagnosis, and risk control rather than a model that improves angle predictions.

Finally, the study uses frozen project artifacts and does not claim that every result has been reproduced in an independent external codebase. Machine-readable tables, exact claim checks, and deterministic figure scripts improve inspectability, but broader community replication remains necessary.

## 8. Conclusion

High detection AP does not answer when an oriented box's angle is trustworthy. Across six complete validation units, a controlled angle intervention leaves AP50 unchanged while sharply reducing AP75 and increasing long-axis error by roughly 29--32 degrees. A deterministic rectangle-rotation model explains why angular meaning depends on aspect ratio and supports a well-defined orientation domain and geometry-normalized severe event. NRC and risk--coverage curves evaluate confidence ordering, while an image-level fixed-sequence LTT procedure controls bounded severe risk without treating correlated detections as independent. Independent double annotations show that 5-degree claims are annotation-sensitive and that 10 degrees has a clearer severe-risk interpretation.

The resulting framework is deliberately modular: full AP measures detection; canonical angle error measures orientation; geometry declares where that angle is identifiable; risk--coverage measures score ordering; and image-level bounds govern finite-sample selection. This separation makes reliability claims more precise and exposes unsupported extrapolations. The current evidence supports measurement and diagnosis across several remote-sensing settings, with explicit dataset and method boundaries. It does not establish a deployable correction or state-of-the-art detector.

## Data and code availability

The project repository contains the tracked derived evidence tables, deterministic plotting scripts, claim specifications, validation outputs, and machine-readable manuscript tables used in this study. Raw datasets are governed by their original licenses and are not redistributed through the manuscript package. Availability is limited to the artifacts explicitly listed in the accompanying manifest; no guarantee about external dataset hosting or future maintenance is implied.

## Ethics and annotation note

The human task involved orientation annotation of remote-sensing object crops and did not collect sensitive personal attributes. Annotator identities are represented only through nonreversible study identifiers in the analysis artifacts. The final submission must include the authors' institution-specific ethics or exemption statement if required. Human disagreement is reported as annotation uncertainty and is not used to label either annotator as erroneous.

## Author contributions

[TO BE COMPLETED BY THE AUTHORS USING THE JOURNAL'S CONTRIBUTOR-TAXONOMY REQUIREMENTS.]

## Funding

[FUNDING INFORMATION TO BE COMPLETED BY THE AUTHORS; NO FUNDING SOURCE IS ASSERTED HERE.]

## Declaration of competing interests

[TO BE COMPLETED BY THE AUTHORS.]

## Acknowledgements

[TO BE COMPLETED BY THE AUTHORS; NO PERSON OR ORGANIZATION IS NAMED WITHOUT OWNER CONFIRMATION.]

## References

References are maintained in `references.bib`; each cited record is paired with a verification entry in `reference_audit.csv`.

## Figure captions

**Figure 1. Accuracy--orientation separation.** Changes in AP50, AP75, and mean long-axis error under the controlled full-evaluator perturbation. All plotted values come from the six frozen complete-validation rows.

**Figure 2. Controlled perturbation by unit.** Original and perturbed AP75 and mean angle error for DIOR-R, FAIR1M-v1.0, and SODA-A units. The intervention does not alter center, scale, class, or confidence.

**Figure 3. Geometry-dependent rotation tolerance.** The smallest relative angle at which concentric, same-scale, congruent rectangles cross below IoU 0.50 or 0.75. The vertical line shows the principal reporting boundary (a=2.1).

**Figure 4. Representative NRC results.** Within-setting continuous angle-error NRC and image-cluster 95% intervals for detection score and intrinsic phase magnitude. Lower is better; one is random-ranking expectation.

**Figure 5. Statistical-unit comparison.** Formal image-level Hoeffding--Bentkus calibration upper bounds versus explicitly invalid instance-independent exact-binomial counterfactuals at (\alpha=0.03).

**Figure 6. Human long-axis disagreement.** Mean circular disagreement with source-image-cluster 95% intervals and p90 values for the overall sample, each dataset, and the (a\geq2.1) subset.
