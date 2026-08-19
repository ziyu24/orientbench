# Native-risk export check

The four-GPU DIOR inference export wrote `11738` prediction rows. Its first
image contains `43` decoded detections and exactly `43` `cora_native_risk`
values (range `0.448987`–`0.487288`). The risk values are attached to the
post-NMS detections and are not detection-score transforms.

Evidence: `outputs/persistent_artifacts/orientbench_cora_obb_r049_20260819/g1/native_risk_export_test/predictions.pkl`.
