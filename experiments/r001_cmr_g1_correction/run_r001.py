#!/usr/bin/env python3
"""r001: live 1024-row global-q and affine-geometry correction evidence."""
from __future__ import annotations
import copy, hashlib, json, math
from collections import defaultdict
from pathlib import Path

import cv2
import torch
from mmcv.transforms import Compose
from mmdet.apis import init_detector
from mmdet.utils import get_test_pipeline_cfg

from experiments.r052_cmr_admission.joint_api import K, ProposalObservationArms, axial_delta, joint_loss
from experiments.r052_cmr_admission.joint_roi_head import _box_residual

ROOT=Path('/home/rspip/cqc/pro/study/orientbench')
OLD=ROOT/'outputs/persistent_artifacts/orientbench_r052_cmr_admission_20260828/g1'
MANIFEST=OLD/'correction_pre_nms_export_6000_uid_v3_rpn_provenance/frozen_1024_pre_nms_positive_proposals.json'
CFG=ROOT/'configs/r052_cmr_admission/dota_orcnn_joint_cmr_smoke_correction.py'
CKPT=OLD/'correction_cmr_joint_smoke_5/epoch_1.pth'
OUT=ROOT/'coordination/instructions/r001/evidence'

def feature(model,pipeline,path,boxes,image=None):
    item={'img_path':path,'img_id':'r001'} if image is None else {'img':image,'img_id':'r001'}
    data=pipeline(item); data=model.data_preprocessor({'inputs':[data['inputs']], 'data_samples':[data['data_samples']]},False)
    with torch.no_grad(): x=model.extract_feat(data['inputs'])
    priors=torch.tensor(boxes,device=data['inputs'].device,dtype=torch.float32); ids=torch.zeros(len(priors),device=priors.device,dtype=torch.long)
    return model.roi_head._r052_features(x,priors,ids),priors

def corners(box):
    x,y,w,h,t=box; c,s=math.cos(t),math.sin(t); pts=[]
    for dx,dy in ((-w/2,-h/2),(w/2,-h/2),(w/2,h/2),(-w/2,h/2)):
        pts.append((x+c*dx-s*dy,y+s*dx+c*dy))
    return pts

def affine_box(box,m):
    pts=torch.tensor(corners(box),dtype=torch.float64); a=torch.tensor(m,dtype=torch.float64)
    q=torch.cat((pts,torch.ones((4,1),dtype=torch.float64)),1)@a.T
    center=q.mean(0); edge=q[1]-q[0]; w=float(torch.linalg.vector_norm(edge)); h=float(torch.linalg.vector_norm(q[3]-q[0]))
    return [float(center[0]),float(center[1]),w,h,float(math.atan2(float(edge[1]),float(edge[0])))],q.tolist()

def main():
    OUT.mkdir(parents=True,exist_ok=True); manifest=json.loads(MANIFEST.read_text()); rows=manifest['proposals']
    assert len(rows)==1024 and len({r['proposal_uid'] for r in rows})==1024
    groups=defaultdict(list)
    for r in rows: groups[r['image_path']].append(r)
    device='cuda:0'; model=init_detector(str(CFG),str(CKPT),device=device); model.eval(); pipe=Compose(get_test_pipeline_cfg(model.cfg))
    acfg=copy.deepcopy(get_test_pipeline_cfg(model.cfg)); acfg[0]['type']='mmdet.LoadImageFromNDArray'; apipe=Compose(acfg)
    arm=model.roi_head.r052_joint; direct=ProposalObservationArms(arm.channels,arm.joint.num_classes,'direct').to(device); direct.load_state_dict(arm.state_dict()); saved=[]; geometry=[]
    for path,rs in sorted(groups.items()):
        boxes=[r['rpn_decoded_box'] for r in rs]; f,priors=feature(model,pipe,path,boxes); f=f.detach().requires_grad_(True)
        labels=torch.tensor([r['class_id'] for r in rs],device=device); gt=torch.tensor([r['matched_gt_box'] for r in rs],device=device); target=_box_residual(gt,priors); source=priors[:,4]; uids=[r['proposal_uid'] for r in rs]
        out=arm(f,labels,target,gt[:,4],source,uids); inf=arm.infer(f,source,uids); emb=arm.candidate_embeddings(f)
        d=f[:,0].detach().requires_grad_(True); dout=direct(d,labels,target,gt[:,4],source,uids); dg=torch.autograd.grad((dout.q[:,1].log()-dout.q[:,0].log()).sum(),d)[0].norm(dim=1)
        cyc=arm.infer(f.detach().roll(1,1),source,uids); cyc_l1=(cyc.q-inf.q.detach().roll(1,1)).abs().sum(-1)
        ix=torch.arange(len(rs),device=device); cls=inf.marginal_class_log_probs[ix,labels]; box=inf.box_residuals[ix,labels,0]; theta=inf.angles[ix,labels]
        cg=torch.autograd.grad(cls.sum(),f,retain_graph=True)[0].norm(dim=(1,2)); bg=torch.autograd.grad(box.sum(),f,retain_graph=True)[0].norm(dim=(1,2)); tg=torch.autograd.grad(theta.sum(),f,retain_graph=True)[0].norm(dim=(1,2))
        normal=joint_loss(out); arm.zero_grad(set_to_none=True); normal.backward(retain_graph=True); evidence=float(arm.joint.posterior.weight.grad.norm()); boxg=[float(x) for x in arm.joint.box_loc_head.weight.grad.norm(dim=1)]; arm.zero_grad(set_to_none=True)
        detached=-torch.logsumexp(out.q.detach().clamp_min(1e-12).log()+out.class_log_likelihood+out.box_log_likelihood+out.angle_log_likelihood,-1).mean(); detached.backward(retain_graph=True); de=0. if arm.joint.posterior.weight.grad is None else float(arm.joint.posterior.weight.grad.norm())
        image=cv2.imread(path); step=float(torch.pi/K); m=cv2.getRotationMatrix2D((image.shape[1]/2,image.shape[0]/2),-step*180/math.pi,1.)
        rb=[]; transforms=[]
        for b in boxes:
            q,pts=affine_box(b,m); inv=cv2.invertAffineTransform(m); back,bpts=affine_box(q,inv); rb.append(q); transforms.append({'matrix':m.tolist(),'original_box':b,'rotated_box':q,'rotated_corners':pts,'inverse_box':back,'inverse_corners':bpts,'analytic_theta_error':float(axial_delta(torch.tensor(back[4]-b[4])))})
        rim=cv2.warpAffine(image,m,(image.shape[1],image.shape[0]),flags=cv2.INTER_LINEAR); rf,rp=feature(model,apipe,path,rb,image=rim); ri=arm.infer(rf,rp[:,4],uids); qerr=(ri.q-inf.q.detach()).abs().sum(-1)
        expected=torch.tensor([x['rotated_box'][4]-x['original_box'][4] for x in transforms],device=device); terr=axial_delta(ri.angles[ix,labels]-(inf.angles.detach()[ix,labels]+expected))
        for i,r in enumerate(rs):
            saved.append({'uid':r['proposal_uid'],'emb':emb[i].detach().cpu(),'label':int(labels[i]),'target':target[i].detach().cpu(),'angle':float(gt[i,4]),'source':float(source[i]),'q':inf.q[i].detach().cpu(),'direct_feature':d[i].detach().cpu(),'base':{'direct_grad':float(dg[i]),'candidate_var':float(f[i].var(0).mean()),'cyclic_l1':float(cyc_l1[i]),'cls_grad':float(cg[i]),'box_grad':float(bg[i]),'theta_grad':float(tg[i]),'normal_loss':float(normal.detach()),'detached_loss':float(detached.detach()),'evidence_grad':evidence,'detached_evidence_grad':de,'box_component_grads':boxg,'geometry_q_l1':float(qerr[i]),'geometry_theta':float(terr[i]),'finite':bool(torch.isfinite(inf.q[i]).all() and torch.isfinite(inf.native_risk[i]).all())}}); geometry.append({'proposal_uid':r['proposal_uid'],**transforms[i],'relative_q_l1':float(qerr[i]),'theta_error':float(terr[i])})
    n=len(saved); perm=list(range(1,n))+[0]; records=[]; dfeat=torch.stack([x['direct_feature'] for x in saved]).to(device); src=torch.tensor([x['source'] for x in saved],device=device); uid=[x['uid'] for x in saved]
    bq=direct.infer(dfeat,src,uid).q; pq=direct.infer(dfeat[perm],src,uid).q; dl1=(bq-pq).abs().sum(-1)
    for start in range(0,n,64):
        s=saved[start:start+64]; foreign=[saved[perm[start+i]] for i in range(len(s))]; emb=torch.stack([x['emb'] for x in s]).to(device); labels=torch.tensor([x['label'] for x in s],device=device); target=torch.stack([x['target'] for x in s]).to(device); angle=torch.tensor([x['angle'] for x in s],device=device); source=torch.tensor([x['source'] for x in s],device=device); u=[x['uid'] for x in s]
        local=arm.joint(emb,labels,target,angle,source,proposal_uids=u); fq=torch.stack([x['q'] for x in foreign]).to(device).clamp_min(1e-12).log(); sh=arm.joint(emb,labels,target,angle,source,fq,u); ix=torch.arange(len(s),device=device)
        for i,x in enumerate(s):
            base=x['base']; records.append({'proposal_uid':x['uid'],'foreign_q_source_uid':foreign[i]['uid'],'direct_grad':base['direct_grad'],'direct_l1':float(dl1[start+i]),'candidate_var':base['candidate_var'],'cyclic_l1':base['cyclic_l1'],'geometry_q_l1':base['geometry_q_l1'],'geometry_theta':base['geometry_theta'],'cls_grad':base['cls_grad'],'box_grad':base['box_grad'],'theta_grad':base['theta_grad'],'normal_loss':base['normal_loss'],'detached_loss':base['detached_loss'],'evidence_grad':base['evidence_grad'],'detached_evidence_grad':base['detached_evidence_grad'],'box_component_grads':base['box_component_grads'],'shuffle_loss':float((local.joint_log_likelihood[i]-sh.joint_log_likelihood[i]).abs()),'shuffle_class':float((local.class_log_likelihood[i]-sh.class_log_likelihood[i]).abs()),'shuffle_box':float((local.box_log_likelihood[i]-sh.box_log_likelihood[i]).abs()),'finite':base['finite']})
    assert len(records)==1024 and all(x['proposal_uid']!=x['foreign_q_source_uid'] for x in records)
    (OUT/'g1_rows.json').write_text(json.dumps(records)+'\n'); (OUT/'geometry_controls.json').write_text(json.dumps(geometry)+'\n')
    def frac(k): return sum(x[k]>1e-6 for x in records)/n
    import statistics
    med=lambda k:float(statistics.median(x[k] for x in records))
    analytic=max(x['analytic_theta_error'] for x in geometry)<=1e-6
    checks={'direct_gradient_95pct':frac('direct_grad')>=.95,'direct_permutation':med('direct_l1')>.05,'candidate_variance_95pct':frac('candidate_var')>=.95,'cyclic':med('cyclic_l1')<=.05,'geometry_relative_q':med('geometry_q_l1')<=.05,'geometry_theta':med('geometry_theta')<=.05,'analytic_affine_inverse':analytic,'class_gradient_95pct':frac('cls_grad')>=.95,'box_gradient_95pct':frac('box_grad')>=.95,'theta_gradient_95pct':frac('theta_grad')>=.95,'detach_forward':max(abs(x['normal_loss']-x['detached_loss']) for x in records)<=1e-6,'detach_gradient':min(x['evidence_grad'] for x in records)>1e-6 and max(x['detached_evidence_grad'] for x in records)<=1e-12,'shuffle_loss_95pct':frac('shuffle_loss')>=.95,'shuffle_class_95pct':frac('shuffle_class')>=.95,'shuffle_box_95pct':frac('shuffle_box')>=.95,'finite':all(x['finite'] for x in records),'box_components':all(min(x['box_component_grads'])>1e-6 for x in records)}
    conclusion='PASS_G1_CORRECTION' if all(checks.values()) else ('INCONCLUSIVE_GEOMETRY_HARNESS' if not analytic else 'KILL_CMR_IMPLEMENTATION_PRINCIPLE')
    result={'schema_version':1,'instruction_id':'r001','count':n,'manifest_sha256':hashlib.sha256(MANIFEST.read_bytes()).hexdigest(),'checks':checks,'metrics':{k:med(k) for k in ('direct_l1','candidate_var','cyclic_l1','geometry_q_l1','geometry_theta','shuffle_loss','shuffle_class','shuffle_box')},'conclusion':conclusion}
    import yaml; (OUT/'G1_RESULT.yaml').write_text(yaml.safe_dump(result,sort_keys=True,allow_unicode=True))
    hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (OUT/'G1_RESULT.yaml',OUT/'g1_rows.json',OUT/'geometry_controls.json')}; (OUT/'artifact_manifest.yaml').write_text(yaml.safe_dump({'schema_version':1,'command':'bash experiments/r001_cmr_g1_correction/run_r001.sh','can_recompute':True,'artifacts':hashes},sort_keys=True))
if __name__=='__main__': main()
