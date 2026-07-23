_base_ = ['./fair1m_psc.py']

model = dict(
    bbox_head=dict(
        angle_coder=dict(_delete_=True, type='CSLCoder', angle_version='le90',
                         omega=4, window='gaussian', radius=3),
        loss_angle=dict(_delete_=True, type='SmoothFocalLoss', gamma=2.0,
                        alpha=0.25, loss_weight=0.8),
        use_normalized_angle_feat=False))
