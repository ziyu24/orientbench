# M4 optional third-dataset extension (Command 070, frozen before pilots)

- `selected_dataset`: FAIR1M-v1.0. The local `FAIRDataset` XML reader, all 37 classes, train/validation images, OBB annotations, evaluator, PSC/CSL/DCL coders, and native-signal instrumentation are available and preflight-readable. Therefore the DOTA-v1.0 fallback is not activated.
- `split`: frozen local train_80 -> val_20 (`18505`/`4362` complete images); no D_cal/D_audit file is changed.
- `class_list`: Passenger Ship, Liquid Cargo Ship, Dry Cargo Ship, Motorboat, Fishing Boat, Warship, Engineering Ship, other-ship, Tugboat, Small Car, Cargo Truck, Van, Trailer, other-vehicle, Dump Truck, Bus, Tractor, Excavator, Truck Tractor, Boeing737, Boeing747, Boeing777, Boeing787, other-airplane, C919, A220, A321, A330, A350, ARJ21, Tennis Court, Football Field, Basketball Court, Baseball Field, Intersection, Bridge, Roundabout.
- `backbone`: ResNet-50 + FPN, frozen stage 1, BN in eval mode; identical RetinaNet geometry/class branches across the three heads.
- `schedule_family`: 1x, 12 epochs, validation every epoch, SGD momentum 0.9, weight decay 1e-4, linear warm-up 500 iterations, MultiStep milestones 8/11, global batch 4 (one image per GPU).
- `augmentation`: resize 1024x1024 with aspect ratio preserved; horizontal/vertical/diagonal random flip, total probability 0.75; no additional augmentation.
- `evaluator`: class-aware rotated-IoU greedy matching; VOC-11 AP50 and AP75; full val_20; le90 long-axis angle error.
- `main_mask`: matched-GT aspect ratio >=2.1 and valid le90 long-axis orientation.
- `primary_risk_event`: angle_error_le90 > delta_theta_0.75(matched_GT_aspect_ratio), using frozen concentric same-scale geometry and 0.001-degree solver contract.
- `pilot_lr_budget`: equal 3x3 grid, heads PSC/CSL/DCL, seed0, 3 epochs, LR candidates 0.0025/0.005/0.010. Select by AP50, then AP75, then lower mean angle error; reliability metrics never select LR.
- `final_seeds`: seed0, seed1, seed2; 12 epochs each. All three seed0 runs are trained and evaluated before seed1/seed2 are launched.
- `native_uncertainty`: PSC=`phase_mod` (squared decoded phase-vector magnitude); CSL=`softmax_margin` (top1-top2; entropy/max probability may be appendix diagnostics); DCL=`bit_margin` (mean absolute sigmoid-bit distance from 0.5, identical to the K2 frozen native definition).
- `early_stop`: stop an attempt only for sustained NaN/Inf, empty predictions, abnormal-loss AP50 collapse, evaluator/data-protocol error, or process failure. Poor scientific outcome is not an early-stop reason and cannot alter the LR budget or seed matrix.
- `AMP_FP32_fallback`: attempt frozen AMP first. On AMP incompatibility, sustained NaN/Inf, divergence, or invalid empty prediction, retry the identical configuration in FP32. A genuine OOM waits 1200 seconds and retries the same four-GPU/batch configuration; GPU count and batch size never change.
- `scheduling`: every training task uses GPUs 0,1,2,3; at most two tasks run concurrently and both see all four GPUs. Other users' processes are not killed.
- `scope_exclusions`: no direct regression, KLD, second dataset, detector matrix, K1/K2/M1/M2/M3/PSC rerun, Deployable gate, or new mechanism hypothesis.

This protocol was frozen before the first Command-070 pilot launch.

## Final frozen result

- Third-dataset decision: **REPLICATES_A**.
- PSC: mean NRC=1.1222; all seeds CI lower >1: True.
- CSL: mean NRC=0.9740; stable reverse: False.
- DCL: mean NRC=0.5507; all seeds NRC<1: True.
- PSC support spans 3 fixed size groups and 2 exclusive aspect-ratio groups; it is not attributed to one such layer.
- Historical K2 outcome A is not modified; this extension only changes its cross-dataset scope.
