_base_ = ['./fair1m_psc.py']

custom_imports = dict(imports=['orientbench_ext.dcl_coder'],
                      allow_failed_imports=False)
model = dict(
    bbox_head=dict(
        angle_coder=dict(_delete_=True, type='DCLCoder', angle_version='le90', omega=1),
        loss_angle=dict(_delete_=True, type='mmdet.CrossEntropyLoss',
                        use_sigmoid=True, loss_weight=0.8),
        use_normalized_angle_feat=False))
