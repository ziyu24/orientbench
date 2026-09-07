import numpy as np
import pytest
from orientbench.r020.metrics import measure, summarise


def test_assignment_loss_is_not_a_four_forward_probability_ensemble():
    p=np.full((2,4,2,3),.5)
    p[0,0],p[1,3]=.9,.9
    p[1,0],p[0,3]=.1,.1
    y=np.ones((2,3),bool)
    row=measure(p,y,y,.5)
    expected=(-np.log(.9)-np.log(.1))/2
    assert row['loss_av']==pytest.approx(expected)
    assert row['loss_av']!=pytest.approx(-np.log(.5))
    assert row['gain_a']==pytest.approx(-np.log(.5)-expected)


def test_swapping_model_names_changes_no_action_risk_and_rejects_broadcast_maps():
    rng=np.random.default_rng(20)
    p=rng.random((2,4,5,7))
    y=rng.random((5,7))<.2
    a,b=[measure(q,y,np.ones_like(y),.2) for q in (p,p[::-1])]
    for k in ('gain_a','gain_b','crossed_i','loss_av','loss_bu'):
        assert a[k]==pytest.approx(b[k])
    assert a['loss_av_12']==pytest.approx(b['loss_av_21'])
    with pytest.raises(ValueError,match='complete maps'):
        measure(p[:,:,:,0],y,np.ones_like(y),.2)


def test_blocks_are_equal_and_two_primary_intervals_are_explicit():
    tiles=['0_0','450_0','2700_0']
    rows=[{'tile':t,'gain_a':0 if i<2 else 10,'gain_b':2.,'crossed_i':1.} for i,t in enumerate(tiles)]
    result=summarise(rows,tiles)
    assert result['means']['gain_a']==5
    assert result['two_primary_bonferroni_97_5_intervals']['gain_b']==[2.,2.]
    with pytest.raises(ValueError,match='complete unique'):
        summarise(rows[:-1],tiles)


def test_assignment_iou_is_averaged_after_ratios_not_by_pooled_counts():
    rows=[{'tile':'0_0','gain_a':1.,'gain_b':1.,'iou_av_12_intersection':1,
           'iou_av_12_union':1,'iou_av_21_intersection':1,'iou_av_21_union':9}]
    value=summarise(rows,['0_0'])['iou']['av_assignment_average']
    assert value==pytest.approx((1+1/9)/2)
    assert value!=pytest.approx(2/10)
