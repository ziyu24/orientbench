from pathlib import Path
import numpy as np
import pytest
from orientbench.r022.support import sampling_support,inspect_support
from orientbench.r022 import run
from orientbench.r021.forecast import Transport,features
from orientbench.r018.evaluate import digest,write,read


def test_native_border_missingness_is_disclosed_while_fixed_core_is_retained():
    valid=np.ones((900,900),bool);valid[:22]=False
    info=inspect_support(valid,[{'dy':-4,'dx':-2},{'dy':0,'dx':0}])
    assert info['native_invalid']==22*900
    assert info['resized_invalid']>0
    assert info['core_invalid']==[0,0,0]


def test_single_missing_sample_inside_shifted_core_rejects_without_shrinking():
    valid=np.ones((900,900),bool)
    y=int(np.floor((28+.5)*900/448-.5))
    x=int(np.floor((32+.5)*900/448-.5))
    valid[y,x]=False
    assert inspect_support(valid,[])['core_invalid']==[0]
    with pytest.raises(ValueError,match='no cropping'):
        inspect_support(valid,[{'dy':-4,'dx':0}])


def test_sampling_support_checks_all_four_positive_bilinear_contributors():
    for dy in (0,1):
        for dx in (0,1):
            valid=np.ones((900,900),bool)
            source=(100+.5)*900/448-.5
            lo=int(np.floor(source))
            valid[lo+dy,lo+dx]=False
            assert not sampling_support(valid)[100,100]


def test_frozen_model_load_reproduces_query_without_refitting(tmp_path):
    geometry=np.array([[.1,.2],[.3,.1]])
    model=Transport(geometry,np.ones((4,80,2,16)),np.array([.1,.2,.3,.4]),.2)
    p=np.full((32,32),.3)
    x=np.stack([features(p,*geometry),features(p,*geometry[::-1])])
    model.fit_ridge(x,np.array([.2,-.1]))
    model.bias.update(transport=.02,ridge=-.01)
    path=tmp_path/'model.npz';model.save(path)
    cal={'bias':model.bias,'forecaster_sha256':digest(path)}
    loaded=run.load_frozen(path,cal)
    assert loaded.predict(p,*geometry)==model.predict(p,*geometry)
    with pytest.raises(ValueError):
        run.load_frozen(path,{**cal,'bias':{}})


def test_frozen_held_execution_orders_decisions_before_outcomes(monkeypatch,tmp_path):
    events=[]
    class Fake:
        def acquire_images(self,splits):events.append('support')
        def forward(self,splits,seeds):events.append(seeds[0])
        def acquire_held_labels(self):events.append('labels')
        def budget(self):pass
        def save_evidence(self):return {'new_forward_images':512}
    monkeypatch.setattr(run,'freeze_decisions',lambda *a:events.append('decisions'))
    monkeypatch.setattr(run,'measure_held',lambda *a:{'actual_labels':{'intervals_97_5':{'policy_gain':[-1,1],'mae_gain':[-1,1]}}})
    manifest={'geometry':{'v':{'look_xy':[.1,.2]}},'held_views':['v'],'held_tiles':[]}
    run.execute(Fake(),manifest,{'foreground_fraction':.2,'scope':'test','support_amendment':'test'},tmp_path,None,{'selected_baseline':'max_separation'},[])
    assert events==['support',1701,'decisions',1702,'labels']
    assert not read(tmp_path/'summary.json')['both_coprimary_lower_bounds_positive']


def test_failed_label_transfer_preserves_received_bytes(monkeypatch,tmp_path):
    assets=run.HeldAssets.__new__(run.HeldAssets)
    assets.out=tmp_path/'out';assets.out.mkdir()
    write(assets.out/'decisions.json',{})
    assets.dataset=tmp_path/'data';assets.manifest={'held_tiles':['x']}
    assets.labels={'x':{'key':'spacenet/SN4_buildings/train/AOI_6_Atlanta/labels/x.json','bytes':10}}
    assets.cfg={'download_bytes_limit':20};assets.budget=lambda:None
    class Response:
        headers={'Content-Length':'10'}
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def read(self,n):
            if not hasattr(self,'sent'):
                self.sent=True;return b'123'
            return b''
    monkeypatch.setattr(run.urllib.request,'urlopen',lambda *a,**k:Response())
    with pytest.raises(ValueError,match='short label'):
        assets.acquire_held_labels()
    ledger=read(assets.out/'download_ledger.json')
    assert ledger[0]['received_bytes']==3
    assert ledger[0]['status']=='failed'


def test_fixed_r022_sources_and_cohort_are_bound():
    root=Path(__file__).resolve().parents[2]
    cfg=read(root/'configs/r022/protocol.json')
    audit=read(root/'doc/R021_B_REVIEW_20260907.json')
    assert cfg['data_manifest_sha256']==digest(root/'configs/r021/data_manifest.json')
    assert all(sha==audit['source_files'][name]['sha256'] for name,sha in cfg['frozen_source_sha256'].items())
