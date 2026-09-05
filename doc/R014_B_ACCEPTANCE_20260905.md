# r014：B 独立数值复核与剩余验收

后续说明：本报告是首批证据复核，原件公开缺口等不是最新终态。
用户授权直连26后的实际核查与r014科学收口见`doc/R014_HOST_REAUDIT_20260905.md`；
原校准manifest已经找到，“缺失不可恢复”已撤销，数值表不变。

日期：2026-09-05。主线代码基线：`8687d2e5de9eff12c27272f9290ee613f1b99500`。
实际读取的证据提交：`bead82282b100ec89f7b58f50f5a32b2d6c2bf0e`
（`origin/exec/r014-source-identity-correction`）。

## 结论：数值已复现，执行有效性尚未闭合

这次确实发布了完整修正概率与同步抽样，不再是“只有摘要、B无法复算”。
B从发布端读取六个raw表，未导入生产或SERVER验证代码，独立完成错误、分母、风险、
50,000抽样、六格同时区间、功效及clean utility复算，结果一致。

但`mutations.py`没有真实执行其声称的反例检验，全部calibration像素的第二路径覆盖
仅2,385/7,416，原输入/模型绑定所需小型记录未随证据发布。故不接受
`final.json`的`valid=true`或“输入/实现问题已经完全关闭”。
正式状态仍为`INCONCLUSIVE_R013_H1A`，当前优先原因是剩余实现/证据有效性；
POWER是**给定已发布概率且其执行来源成立**时可独立复现的条件诊断，不是已验收终态。

当前唯一SERVER任务仍是r014的剩余验收，不新增r015，不重训、不重新模型前向、不打开test。
不可恢复的原记录应明确终结为inconclusive，不能无限追加repair或追认历史。

## 1. 已独立复现的具体数字

风险为class-balanced × component-equal，先计算逐seed风险再平均；
效应是±10°平均风险减clean风险。表中效应与区间单位均为百分点，不是相对改善率。
区间是原六维同步max-abs-studentized 95%同时区间。

| 架构 | 属性 | Delta（pp） | 同时区间（pp） | 原合同功效诊断 |
| --- | --- | ---: | --- | ---: |
| ResNet-50 | wing | +0.5070 | [-2.4254, 3.4394] | 0.20396 |
| ResNet-50 | engine | +0.5082 | [-1.3435, 2.3599] | 0.58606 |
| ResNet-50 | propulsion | +2.1439 | [0.2817, 4.0060] | 0.56040 |
| ViT-B/16 | wing | -0.0307 | [-3.9275, 3.8661] | 0.08280 |
| ViT-B/16 | engine | +0.9485 | [-1.4973, 3.3944] | 0.31648 |
| ViT-B/16 | propulsion | -1.4622 | [-5.7042, 2.7798] | 0.07378 |

注意：不是“六格区间都跨零”，ResNet propulsion的下界为正；但单格不满足整个原合取协议。
全部upper仍大于2pp，不能依据上界门KILL；六格功效全部低于0.80，故身份/实现若最终有效，
且预测不变，原顺序裁决仍是POWER。平移bootstrap功效是冻结设计诊断，不是后验效应存在概率，
也不据此自动追加来源或seed。负点估计不能外推为“方向无用”。

本地复核事实：

- 7,416对象ID唯一、25 components；六模型对象/标签/component完全同序同值。
- 完整二类概率有限且在[0,1]；二类概率和最大偏差1.1920928955078125e-7。
  两视图平均与存储均值逐值相等；按完整二类argmax重算所有错误，与发布错误逐值相等。
- 主程序单列概率>0.5与合同argmax在本数据上没有任何分类差异；仍应修复一般性定义。
- PCG64(12012)产生的50,000×25抽样矩阵与发布draws逐值相等。
  本数据实际无零类别分母draw、六格实际无零方差；生产者未实现这些分支没有污染本次数字，
  但不能用“本次没触发”代替合同中的真实退化测试。
- 全部bootstrap逐seed/属性/三臂风险最大差2.220446049250313e-16。
  Delta最大差2.7755575615628914e-17，sd最大差6.938893903907228e-18，
  效应上下界最大差6.245004513516506e-17，q差3.1086244689504383e-15，
  功效差0；clean upper最大差1.1102230246251565e-16。
- clean同时upper最大0.39233191488314<0.5，18个clean head均非恒定。
- 依发布来源标记划分的5,098个未受影响对象，六模型三臂三属性相对旧概率的分类翻转均为0；
  最大概率差为4.875063896179199e-4。数值差来源未凭输出单独证明，不能仅称机器精度误差；
  但本批未受影响对象的分类风险没有改变。

## 2. 已读取记录与“原始像素已独立证明”要分开

发布的source_records含4,065训练行、7,416校准行；所有行image_id与其记录的
g0_source_cog一致。记录声明训练旧/新像素差0，校准2,318行像素改变。这是B逐行读取与计数，
**不是B从原始COG独立读取全部像素**。训练227行affected只是CAT-only映射的假想碰撞标记，
不能当作227个训练样本错图。

原报告称calibration排除9082、10788，但“未进入frozen eligible manifest”尚未解释原资格原因。
证据树未包含G0/共同eligible及旧train/calibration原始manifest，也未包含六模型初始化、
完成训练和原输入绑定记录。raw中的模型摘要不能独自补上这条来源链。

证据README称含旧—修正比较，实际树有old_reproduction而没有compare_old输出；
B本地已直接比较发布raw得到上面的未受影响分类翻转数，SERVER仍须让交付清单与实际内容一致。
大影像和模型不要求塞入普通Git；缺的是原有可公开小型记录与真实核验结果。

## 3. 阻止最终验收的明确代码证据

| 文件 | 实际做了什么 | 不能据此声称什么 |
| --- | --- | --- |
| mutations.py | identity两次调用自己的同一grid；angle仅比较坐标grid | 没有对照实际生产render，也没验证实际像素响应 |
| mutations.py | theta180比较(p0+p1)/2与(p1+p0)/2 | 加法交换律不能证明实际theta+180输入及视图配对正确 |
| mutations.py | 错源检查两个ID不等、错行检查逆序不等、NaN有限性、文件数减一 | 没有把坏输入交给真实验证器/裁决器并观察拒绝 |
| mutations.py | 零方差区间直接赋(0,0) | 没有执行退化统计；度弧度、零分母、正确共同重排也未检验 |
| geometry_reference.py | 第二路径像素仅2,385行；来源image_id来自主审计表；缺记录continue | 未完成原合同7,416全canvas第二路径和独立来源绑定 |
| verify.py | 核对Delta/sd/q，信任原source表；未完整核对区间/功效/clean/裁决 | SERVER的“独立验证通过”比实际覆盖范围更大；B已另行补做数值复算 |
| stats.py | 无效draw数硬写0、无零方差处理、只以正类概率>0.5判类 | 当前真实数据数字可用，不代表边界分支按合同正确 |
| evaluate_corrected.py | 只比较磁盘模型文件评估前后内容 | 不等于验证内存参数/所有buffer不变或原训练来源 |
| finalize.py | 将2318硬编码为通过条件，消费all_pass；未用test/未重训写常量 | 不能用预期计数或自述追认原执行；utility与输入无效原因也需分开 |

这些是可定位的验收缺口，不是对执行者意图的判断，也不表明所有修正数字错误。
应真实执行原合同要求的检验，不叠加新治理结构。
如果原模型或输入身份不可恢复，或者发现现有render语义不成立，本次停止并保留明确缺口；
不以再次训练/推理制造一套新历史。

## 4. 当前创新与期刊定位

本次仍判断为**JSTARS类领域测量论文候选，未达到可自洽主张的TGRS/JPRS创新水平**。
这是依据实际贡献的研究判断，不是分区查询、期刊打分或录用承诺，也不是沿用历史标签。

保留的科学素材包括：六单元完整方向评价对照、矩形几何风险边界及600个人工目标；
其中AP50严格不变是GT约束构造，非oracle固定15°扰动实际使AP50下降2.88–9.51pp、
AP75下降3.74–17.20pp。人工450个双人数值对的2.3112°是条件标注分歧，不是GT噪声地板。
原六单元LTT全部coverage=1，只覆盖matched high-AR风险，不能当作完整系统非平凡控制。
这些限制见全项目创新重评及结果总账，而非用最新r014代表全部项目。

为什么没有升档：

1. 新的修正恢复的是可信度，不是新机制。严谨必要，但纠错和更多抽样不会自动增加科学新意。
2. H1a仅考察无旋转增强的固定规范化分类流程对角参数的响应，包含采样与背景支持变化；
   不是可部署检测角改进的收益。即使六格通过，也未超越已知飞机方向规范化与不变表征解释。
3. 目前没有证明一个能预测“何时方向测量值得成本、何时应绕开”的可迁移机制，更未战胜
   同信息/资源预算下完整支持+旋转增强/强不变基线。不能把小分数、重命名head或追加数据补作创新。

直接近邻已重新核对：[IGARSS 2023飞机细粒度识别的作者机构摘要](https://athene-forschung.unibw.de/?change_language=en&id=154661)
明确使用机头方向规范化并报告FAIR1M识别改善；
[ReDet作者论文](https://arxiv.org/abs/2103.07733)已结合旋转等变特征与旋转不变RoI表示。
前者在此仅依据可读取的机构摘要，不声称已取得付费全文。这些近邻不等于已经完成本项目全部
控制实验，但足以反对“只要再证明规范化分类器怕角扰动就有顶刊新意”的推论。

因此不签新训练命令来维持顶刊叙事。r014结束后只保留前次报告中“有限资源下方向测量相对
强不变决策的增量价值与可预测边界”这一未成熟候选；其机制、真实用途和来源独立确认设计
未成立前，不启动H1b/H2或预算实验。若不能提出超越已有解释的可否证预测，应收敛测量稿，
而不是重复同一属性角扰动。

## 附录：B 本地只读复算代码

以下程序从固定证据提交读取blob到内存；不读取服务器磁盘、不导入项目生产/验证模块、
不运行模型、不写数据文件。输入代码和数值摘要的范围是已发布概率表，不能替代原COG/训练来源证明。

```python
import io,json,subprocess
import numpy as np
ref='bead82282b100ec89f7b58f50f5a32b2d6c2bf0e'
def blob(name): return subprocess.check_output(['git','show',ref+':evidence/'+name])
def js(name): return json.loads(blob(name))
models=[k+'_'+str(s) for k in ('resnet50','vit_b16') for s in (1201,1202,1203)]
raw=[np.load(io.BytesIO(blob('r014/raw_'+n+'.npz'))) for n in models]
records=[json.loads(line) for line in blob('r014/source_records.jsonl').splitlines()]
y=raw[0]['labels']; oid=raw[0]['object_id']; co=raw[0]['component']
p=np.stack([z['p_avg'] for z in raw]).reshape(2,3,3,len(oid),3,2)
error=p.argmax(-1)!=y[None,None,None]
alt=(p[...,1]>.5)!=y[None,None,None]
present=np.zeros((3,25,2),bool); v=np.zeros((2,3,3,3,25,2))
for k in range(3):
 for j in range(25):
  for c in range(2):
   mask=(co==j)&(y[:,k]==c);present[k,j,c]=mask.any()
   if mask.any():v[:,:,:,k,j,c]=error[:,:,:,mask,k].mean(-1)
rng=np.random.Generator(np.random.PCG64(12012))
draw=rng.integers(0,25,(50000,25))
w=np.zeros((50000,25),np.float64)
np.add.at(w,(np.arange(50000)[:,None],draw),1)
den=np.einsum('bj,kjc->bkc',w,present)
valid=np.all(den>0,axis=(1,2))
def aggregate(weights):
 out=np.empty((len(weights),2,3,3,3))
 for k in range(3):
  for arm in range(3):
   a=np.einsum('bj,msj->bms',weights,v[:,:,arm,k,:,0])/(weights@present[k,:,0])[:,None,None]
   b=np.einsum('bj,msj->bms',weights,v[:,:,arm,k,:,1])/(weights@present[k,:,1])[:,None,None]
   out[:,:,:,k,arm]=.5*(a+b)
 return out
R=aggregate(w); point=aggregate(np.ones((1,25)))[0]
rep=((R[...,1]+R[...,2])*.5-R[...,0]).mean(2).reshape(-1,6)
delta=((point[...,1]+point[...,2])*.5-point[...,0]).mean(1).reshape(6)
def interval(values,pt):
 sd=values.std(0,ddof=1);active=sd>0
 q=float(np.quantile(np.max(np.abs((values[:,active]-pt[active])/sd[active]),axis=1),.95,method='linear')) if active.any() else 0.
 return sd,q,pt-q*sd,pt+q*sd
sd,q,lo,hi=interval(rep,delta)
power=(.02+rep-delta-q*sd>0).mean(0)
clean=R[...,0].mean(2).reshape(-1,6); cp=point[...,0].mean(1).reshape(6)
cs,cq,clo,chi=interval(clean,cp)
summary=js('r014/summary.json')
fields={'delta':delta,'sd':sd,'simultaneous_lower':lo,'simultaneous_upper':hi,'power':power,'clean_risk':cp,'clean_sd':cs,'clean_simultaneous_upper':chi}
diff={k:float(np.max(np.abs(val-np.asarray(summary[k]).reshape(-1)))) for k,val in fields.items()}
diff['q']=abs(q-summary['q']);diff['clean_q']=abs(cq-summary['clean_q'])
rr=np.load(io.BytesIO(blob('r014/bootstrap_replicates.npz')))
stored=np.load(io.BytesIO(blob('r014/bootstrap_draws.npy')))
nonsingle=[len(np.unique(z['p_avg'][0].argmax(-1)[:,k]))==2 for z in raw for k in range(3)]
changed={}
for part in ('train','calibration'):
 r=[x for x in records if x['partition']==part]
 changed[part]={'rows':len(r),'declared_affected':sum(x['affected'] for x in r),'pixel_changed':sum(x['pixel_different'] for x in r),'source_matches_g0':all(x['image_id']==x['g0_source_cog'] for x in r)}
out={'objects':len(oid),'components':len(np.unique(co)),'ids_unique':len(set(oid.tolist()))==len(oid),'all_raw_identity_equal':all(np.array_equal(z['object_id'],oid) and np.array_equal(z['labels'],y) and np.array_equal(z['component'],co) for z in raw),'prob_valid':all(np.isfinite(z['p_view']).all() and (z['p_view']>=0).all() and (z['p_view']<=1).all() for z in raw),'p_avg_exact':all(np.array_equal(z['p_avg'],z['p_view'].mean(1)) for z in raw),'stored_errors_exact':all(np.array_equal(z['error'],(z['p_avg'].argmax(-1)!=z['labels'][None])) for z in raw),'argmax_vs_half_differences':int(np.sum(error!=alt)),'draws_exact':bool(np.array_equal(draw,stored)),'invalid_denominator_draws':int((~valid).sum()),'zero_sd_cells':int((sd==0).sum()),'risk_replicate_maxdiff':float(np.max(np.abs(R-rr['risk']))),'statistics_maxdiff':diff,'delta_pp':(delta*100).tolist(),'simultaneous_lower_pp':(lo*100).tolist(),'simultaneous_upper_pp':(hi*100).tolist(),'power':power.tolist(),'clean_upper_max':float(chi.max()),'clean_heads_nonconstant':all(nonsingle),'source_records':changed,'final':js('r014/final.json'),'mutation_report':js('r014/mutations.json')}

out['prob_sum_maxdiff']=max(float(np.max(np.abs(z['p_view'].sum(-1)-1))) for z in raw)
comparisons={}
for n,z in zip(models,raw):
 old=np.load(io.BytesIO(blob('r013/raw_'+n+'.npz')))
 affected_ids={x['object_id'] for x in records if x['partition']=='calibration' and x['affected']}
 mask=np.array([int(x) in affected_ids for x in oid])
 oldp=old['p_avg'] if 'p_avg' in old.files else old['prob']
 if oldp.ndim==3:oldp=np.stack([1-oldp,oldp],axis=-1)
 comparisons[n]={'old_keys':old.files, 'new_old_maxdiff_unaffected':float(np.max(np.abs(z['p_avg'][:,~mask]-oldp[:,~mask]))),'prediction_flips_unaffected':int(np.sum(z['p_avg'][:,~mask].argmax(-1)!=oldp[:,~mask].argmax(-1)))}
out['old_new']=comparisons
print(json.dumps(out,indent=2))
```
