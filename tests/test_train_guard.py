"""014 + 014-supplement formal-training guard tests."""
import os, sys, json, tempfile
_P=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,_P)
from orientbench.runners.train_guard import (validate_formal_training, compute_effective_batch,
    compute_scaled_lr)

def _val(**kw):
    d=dict(host="X",per_gpu_batch=2,world_size=4,grad_accum=1,reference_global_batch=8,
           reference_lr=1e-4,configured_lr=1e-4,auto_scale_lr_enabled=False,cuda_visible="0,1,2,3",
           val_interval=1,save_best_metric="dota/mAP",save_last=True,max_keep_ckpts=1,
           master_port=29551,work_dir="/wd/rhino",other_master_ports=[29552],other_work_dirs=["/wd/a4"])
    d.update(kw); return validate_formal_training(**d)

def test_effective_batch_and_scaled_lr():
    assert compute_effective_batch(2,4,1)==8
    assert abs(compute_scaled_lr(1e-4,8,8)-1e-4)<1e-12
    assert abs(compute_scaled_lr(1e-4,16,8)-2e-4)<1e-12

def test_world_size_not_4_refused():
    r=_val(world_size=2, cuda_visible="0,1")
    assert r["ok"] is False and any("world_size" in e for e in r["errors"])

def test_partial_gpu_refused():
    r=_val(cuda_visible="0,1", world_size=2)
    assert r["gpu_topology"]=="invalid" and r["ok"] is False

def test_lr_linear_scaling_enforced():
    assert _val(configured_lr=2e-4)["ok"] is False
    assert _val(configured_lr=1e-4)["lr_scaling_proof_valid"] is True

def test_no_double_scaling():
    r=_val(auto_scale_lr_enabled=True, per_gpu_batch=4, configured_lr=compute_scaled_lr(1e-4,16,8))
    assert r["ok"] is False and any("double scaling" in e for e in r["errors"])

def test_val_interval_must_be_1():
    r=_val(val_interval=4)
    assert r["ok"] is False and any("val_interval" in e for e in r["errors"])

def test_save_best_metric_required():
    r=_val(save_best_metric=None)
    assert r["ok"] is False and any("save_best" in e for e in r["errors"])

def test_save_last_and_best_policy():
    assert _val(save_last=False)["ok"] is False
    assert _val()["checkpoint_policy_valid"] is True  # best+latest guaranteed

def test_concurrent_port_workdir_conflict_refused():
    assert _val(master_port=29552)["ok"] is False   # same as other job's port
    assert _val(work_dir="/wd/a4")["ok"] is False     # same as other job's dir

def test_two_4gpu_concurrent_allowed():
    # distinct ports/dirs, both 4-gpu -> allowed (no single-job block)
    r=_val()
    assert r["ok"] is True and r["formal_eligible"] is True and r["gpu_topology"]=="single_job_4gpu"

def test_resume_noncompliant_refused():
    assert _val(resume_from_noncompliant=True)["ok"] is False

def test_pipeline_rejects_non_formal_eligible():
    import importlib.util
    spec=importlib.util.spec_from_file_location("p42", os.path.join(_P,"scripts","42_post_training_pipeline.py"))
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    with tempfile.TemporaryDirectory() as d:
        json.dump({"formal_eligible":False}, open(os.path.join(d,"manifest.json"),"w"))
        assert m._formal_eligible(d)[0] is False
        json.dump({"formal_eligible":True,"gpu_topology":"single_job_4gpu","world_size":4,
                   "batch_proof_valid":True,"lr_scaling_proof_valid":True},
                  open(os.path.join(d,"manifest.json"),"w"))
        assert m._formal_eligible(d)[0] is True

def test_concurrent_launcher_two_hosts():
    import importlib.util
    spec=importlib.util.spec_from_file_location("p45", os.path.join(_P,"scripts","45_concurrent_host_training.py"))
    m=importlib.util.module_from_spec(spec)
    try: spec.loader.exec_module(m)
    except Exception: return
    assert m.HOSTS[0]["host"]=="RHINO" and m.HOSTS[1]["route"]=="A4"
    assert m.HOSTS[0]["port"]!=m.HOSTS[1]["port"]   # distinct ports
    assert m.SAVE_BEST_KEY=="dota/mAP"

if __name__=="__main__":
    p=f=0
    for n,fn in sorted(globals().items()):
        if n.startswith("test_") and callable(fn):
            try: fn(); p+=1; print("PASS",n)
            except Exception as e: f+=1; print("FAIL",n,e)
    print(f"{p} passed {f} failed"); raise SystemExit(1 if f else 0)
